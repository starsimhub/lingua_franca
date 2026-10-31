"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np
import pandas as pd
import sciris as sc

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim

example = here
ref = pd.read_csv(os.path.join(example, 'reference', 'results.csv'))
n_runs = 50
tolerance = dict(total=0.02, yearly=0.2, correlation=0.98, region=0.2, stock=0.03) # With 50 runs against 50: see the README


def monthly(res, key):
    """ A daily flow summed by month (a flow at index k is the number during the step ending on day k, so during day k-1) """
    months = [str(t)[:7] for t in res.timevec[:-1]]
    return pd.Series(res[key].values[1:], index=months).groupby(level=0, sort=False).sum()


def run(seed):
    res = sim.new(verbose=0, rand_seed=seed, results=['onset']).run().results.measles # Onsets by district every day
    by_district = res.onset.by('district')
    after = np.array([str(t)[:4] >= '2020' for t in res.timevec[:-1]]) # By the day each step starts on, as in monthly()
    regions = pd.Series(by_district.values[1:][after].sum(axis=0), index=[col.split(':')[0] for col in by_district.columns]).groupby(level=0).sum()
    end = [str(t)[:10] for t in res.timevec].index('2025-12-01') # The original's last value is at the start of the last month
    return sc.objdict(infections=monthly(res, 'onset'), cases=monthly(res, 'cases'), regions=regions, S=res.S.values[end], R=res.R.values[end])


if __name__ == '__main__':
    runs = sc.parallelize(run, iterarg=range(n_runs), ncpus=2)
    for key in ['infections', 'cases']:
        ours = pd.concat([r[key] for r in runs], axis=1).mean(axis=1)
        theirs = ref[ref.series == f'monthly_{key}'].set_index('time')['value']
        ours, theirs = ours.loc[theirs.index], theirs
        yearly = lambda s: s.groupby(s.index.str[:4]).sum()
        total, by_year, corr = abs(ours.sum()/theirs.sum() - 1), (yearly(ours)/yearly(theirs) - 1).abs().max(), np.corrcoef(ours, theirs)[0, 1]
        print(f'{key}: total {ours.sum():,.0f} (original {theirs.sum():,.0f}); by year, largest difference {by_year:.1%}; correlation of monthly means {corr:.3f}')
        assert total < tolerance['total'] and by_year < tolerance['yearly'] and corr > tolerance['correlation'], f'{key} disagree'
    ours = pd.concat([r.regions for r in runs], axis=1).mean(axis=1)
    theirs = ref[ref.series.str.startswith('region_')].set_index('series')['value'].rename(lambda s: s[7:])
    worst = (ours/theirs.loc[ours.index] - 1).abs().max()
    print(f'infections from 2020 by region: largest difference {worst:.1%}')
    assert worst < tolerance['region'], 'the regions disagree'
    last = ref[ref.series.isin(['national_S', 'national_R'])].groupby('series')['value'].last()
    S, R = np.mean([r.S for r in runs]), np.mean([r.R for r in runs])
    print(f'susceptible at the end {S:,.0f} (original {last.national_S:,.0f}); immune {R:,.0f} ({last.national_R:,.0f})')
    assert abs(S/last.national_S - 1) < tolerance['stock'] and abs(R/last.national_R - 1) < tolerance['stock'], 'the stocks disagree'


"""
Compare the Starsim version with the reference results of the original

    python compare.py

The original draws R0 and the share of cases detected afresh for each run, without a seed, so its
reference keeps the values it drew (`reference/draws.csv`). Starsim is run with the same values, so
the mean and range of its ten runs of each scenario should match the original's exactly; it is then
run with its own draws, which should match only in distribution.

Raises an error if, with the original's draws, any series differs by more than 1e-9 of its largest value,
or if, with Starsim's own draws, a mean peak of more than one person or mean deaths differ by more than 30%.
"""
import os
import sys
import numpy as np
import pandas as pd
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))
sys.path.insert(0, os.path.join(root, 'docs', 'models'))
import tools
from model import sim, pop, scenarios

example = os.path.join(root, 'docs', 'models', 'flepimop', 'vaccine_scenarios')
ref = pd.read_csv(os.path.join(example, 'reference', 'results.csv'))
ref_draws = pd.read_csv(os.path.join(example, 'reference', 'draws.csv'))
flows = dict(S='waning', E='infection', I='onset', R='recovery', V='vaccination') # The flow into each state
outcomes = dict(incidCase='cases', incidHosp='hosp', incidDeath='deaths', currHosp='n_hosp')
tol_same = 1e-9 # With the same draws, as a share of each series' largest value
tol_own = 0.3 # With different draws: the original has ten runs of each scenario, so its own means are uncertain
stocks = [f'{place}_{state}' for place in pop for state in flows] # The number in each state


def ours(sims):
    """ Each series of the original, from the runs of one scenario, as an array of runs by days

    A stock at index k is the number at the start of day k, in both. A flow (and an outcome) at index k is the number during
    the step ending on day k, so its first value, at the start, is 0; the original's on day k is the number during day k, so
    ours from index 1 match the original's from day 0 """
    out = dict()
    res = [sim.results.seir for sim in sims]
    for place in pop:
        for state,flow in flows.items():
            out[f'{place}_{state}'] = np.array([r[state].select(patch=place).values for r in res])
            out[f'{place}_incidence_{state}'] = np.array([r[flow].select(patch=place).values[1:] for r in res])
        for name,key in outcomes.items():
            out[f'{place}_{name}'] = np.array([r[key].select(patch=place).values[1:] for r in res])
    return out


def theirs(scen, name, col='value'):
    """ A series of the original; deaths are summed over the provinces, and a flow leaves out its last day, the stop, which ours does not reach """
    names = [f'{place}_{name}' for place in pop] if name in outcomes else [name]
    vals = sum(ref[ref.series == f'{scen}_{n}'].sort_values('time')[col].values for n in names)
    return vals if name in stocks else vals[:-1]


def summary(arr):
    """ The mean, 5%, and 95% of the runs, as run.py works them out """
    ordered = np.sort(arr, axis=0)
    n = len(arr)
    return dict(value=arr.mean(axis=0), low=ordered[int(0.05*(n - 1))], high=ordered[int(0.95*(n - 1))])


def same_draws():
    """ Each scenario, run with the values the original drew for it """
    sims = [sim.new(label=row.scenario, pars=dict(Ro=row.Ro, p_case=row.p_case), interventions=scenarios[row.scenario], verbose=0) for row in ref_draws.itertuples()]
    msim = ss.parallel(sims, parallel=False)
    print('With the values the original drew: the largest difference in the mean, 5%, and 95% of each series, as a share of its largest value')
    for scen in scenarios:
        series = ours([s for s in msim.sims if s.label == scen])
        diffs = dict()
        for name,arr in series.items():
            stats = summary(arr)
            diffs[name] = max(np.abs(stats[col] - theirs(scen, name, col)).max()/max(np.abs(theirs(scen, name, col)).max(), 1e-12) for col in ['value', 'low', 'high'])
        exact = [name for name,diff in diffs.items() if diff < 1e-9]
        print(f'  {scen:8s}: {len(exact)} of {len(diffs)} series within 1e-9; ' + ', '.join(f'{name} {diff:.1e}' for name,diff in diffs.items() if name not in exact))
        assert max(diffs.values()) < tol_same, f'{scen}: a series differs by {max(diffs.values()):.1e} of its largest value'
    return


def own_draws(n_runs=100):
    """ Each scenario, run with values Starsim draws, against the original's ten runs """
    msim = ss.parallel([sim.new(label=name, interventions=mods, verbose=0) for name,mods in scenarios.items()], n_runs=n_runs, priors=True, parallel=False)
    print(f'\nWith {n_runs} runs of each scenario, drawn by Starsim (the original has 10): the peak of the mean, 5%, and 95% series, and the deaths')
    for scen in scenarios:
        series = ours([s for s in msim.sims if s.label == scen])
        for name in ['large_province_I', 'small_province_I']:
            stats = summary(series[name])
            peaks = [f'{stats[col].max():6.1f} ({theirs(scen, name, col).max():6.1f})' for col in ['value', 'low', 'high']]
            print(f'  {scen:8s} {name:16s} peak: mean {peaks[0]}, 5% {peaks[1]}, 95% {peaks[2]}; original in brackets')
            assert theirs(scen, name).max() < 1 or abs(stats['value'].max()/theirs(scen, name).max() - 1) < tol_own, f'{scen}: the mean peak of {name} differs by more than {tol_own:.0%}'
        deaths = (series['large_province_incidDeath'] + series['small_province_incidDeath']).sum(axis=1)
        print(f'  {scen:8s} {"deaths":16s} mean {deaths.mean():5.1f} ({theirs(scen, "incidDeath").sum():5.1f})')
        assert abs(deaths.mean()/theirs(scen, 'incidDeath').sum() - 1) < tol_own, f'{scen}: mean deaths differ by more than {tol_own:.0%}'
    return


if __name__ == '__main__':
    same_draws()
    own_draws()

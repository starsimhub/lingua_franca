"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim, scenarios

ref = tools.read_results(here)
comps = ['sus', 'undx', 'dx', 'linked', 'tx', 'lost', 'vs', 'dead_hiv', 'dead_other']
cascade = dict(plhiv='all_people', diagnosed='all_dx', treated='all_tx')
tolerance = 1e-12 # Of the largest value in each series


def worst(res, scen):
    """ The largest difference in any compartment of either sex, and in the cascade, as a share of the largest value of each """
    # A stock at index k is the number in year k after the start, in both: compare from 2016 to 2035
    out = {}
    for comp in comps:
        for sex in ['females', 'males']:
            ours, theirs = res[comp].select(sex=sex).values, np.array(ref[f'{scen}_{sex}_{comp}'][1])
            out[f'{sex}_{comp}'] = np.abs(ours - theirs).max()/theirs.max()
    for ours,theirs in cascade.items():
        for sex in ['females', 'males']:
            vals = np.array(ref[f'{scen}_{sex}_{theirs}'][1])
            out[f'{sex}_{ours}'] = np.abs(res[ours].select(sex=sex).values - vals).max()/vals.max()
    return out


if __name__ == '__main__':
    for scen,pars in dict(baseline={}, **scenarios).items():
        res = sim.new(verbose=0, pars=pars).run().results.hiv
        diffs = worst(res, scen)
        key = max(diffs, key=diffs.get)
        vs = {sex: (res.vs.select(sex=sex)[-1], ref[f'{scen}_{sex}_vs'][1][-1]) for sex in ['females', 'males']}
        print(f'{scen:15s} largest difference {diffs[key]:.2g} ({key}); virally suppressed in 2035: ' + ', '.join(f'{k} {a:,.0f} (original {b:,.0f})' for k,(a,b) in vs.items()))
        assert diffs[key] < tolerance, f'{scen}: {key} differs by {diffs[key]:.2g}'

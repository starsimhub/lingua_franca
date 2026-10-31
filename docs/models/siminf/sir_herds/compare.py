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
from model import sim

n_runs = 100 # The 7% of runs where the infection dies out early move the means a lot
tolerance = 3 # Standard errors of the mean of the runs
times = [100, 200, 365, 500, 700, 1000, 1460]


def one(seed):
    """ One run: the series the reference has, by day (a count at index t is the number on day t, with the transitions of SimInf's day t and, as in SimInf, that day's scheduled events) """
    res = sim.new(rand_seed=seed, verbose=0).run().results.sir
    out = {key:res[key].values for key in 'SIR'}
    I = res.I.strata # By herd
    out['nodes_infected'] = (I > 0).sum(axis=1)
    for node in [1, 2, 3]:
        for key in 'SIR':
            out[f'node{node}_{key}'] = res[key].select(herd=str(node)).values
    return out


if __name__ == '__main__':
    ref = tools.read_results(here)
    runs = [one(seed) for seed in range(n_runs)]
    worst = 0
    for key in ['S', 'I', 'R', 'nodes_infected', 'node1_I']:
        rt, rv = ref[key]
        vals = np.array([run[key] for run in runs])
        print(f'{key}:')
        for t in times:
            i = rt.index(float(t))
            mean, se = vals[:, t].mean(), vals[:, t].std()/np.sqrt(n_runs)
            if se > 0:
                worst = max(worst, abs(mean - rv[i])/se)
            print(f'  day {t:4d}: Starsim {mean:9,.0f} ± {se:7,.0f}   SimInf {rv[i]:9,.0f}')
    died = np.mean([run['I'][199] == 0 for run in runs])
    print(f'runs with no infection on day 200: {died:.0%} (SimInf about 7%)')
    print(f'largest difference: {worst:.1f} standard errors')
    assert worst < tolerance, f'The results differ by {worst:.1f} standard errors'

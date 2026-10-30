"""
Compare the Starsim version with the reference results of the original

    python compare.py [n_runs]

The runs are made one after another.
"""
import os
import sys
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
sys.path.insert(0, os.path.join(root, 'examples'))
import tools
from model import sim

n_runs = int(sys.argv[1]) if len(sys.argv) > 1 else 100
times = [92, 183, 365, 547, 729, 911, 1093, 1275, 1457] # Days in the reference (every 7 days from day 1)
tolerance = 3 # Standard errors of the difference from the mean of the 200 runs of the reference, taken to have the same spread
keys = ['S_1', 'I_1', 'S_2', 'I_2', 'S_3', 'I_3', 'I', 'phi', 'nodes_infected', 'node1_I', 'node1_phi']


def one(seed):
    """ One run: the series the reference has, by day (a count at index t is the number on day t, with the transitions of SimInf's day t and, as in SimInf, that day's scheduled events) """
    res = sim.new(rand_seed=seed, verbose=0, results=['I_1', 'I_2', 'I_3', 'phi']).run().results.sise3 # By herd every day, as the days of the reference are not multiples of 7
    out = {key:res[key].values for key in keys[:6]}
    I = res.I_1.strata + res.I_2.strata + res.I_3.strata # By herd
    out['I'] = I.sum(axis=1)
    out['phi'] = res.phi.values/I.shape[1] # The mean over herds
    out['nodes_infected'] = (I > 0).sum(axis=1)
    out['node1_I'] = I[:, 0]
    out['node1_phi'] = res.phi.select(herd='1').values
    return out


if __name__ == '__main__':
    ref = tools.read_results(os.path.join(root, 'examples', 'siminf', 'sise3'))
    with open(os.path.join(root, 'examples', 'siminf', 'sise3', 'reference', 'results.csv')) as f:
        rows = [line.strip().split(',') for line in f][1:]
    band = {(row[1], float(row[0])):(float(row[3]), float(row[4])) for row in rows}
    runs = [one(seed) for seed in range(n_runs)]
    worst = 0
    for key in keys:
        rt, rv = ref[key]
        vals = np.array([run[key] for run in runs])
        print(f'{key}:')
        for t in times:
            i = rt.index(float(t))
            mean, se = vals[:, t].mean(), vals[:, t].std()/np.sqrt(n_runs)
            diff = se*np.sqrt(1 + n_runs/200)
            low, high = band[(key, float(t))]
            inside = np.mean((vals[:, t] >= low) & (vals[:, t] <= high))
            worst = max(worst, abs(mean - rv[i])/diff)
            print(f'  day {t:4d}: Starsim {mean:11,.2f} ± {se:9,.2f}   SimInf {rv[i]:11,.2f} ({low:,.2f} to {high:,.2f}); {inside:.0%} of runs in that range')
    print(f'largest difference: {worst:.1f} standard errors')
    assert worst < tolerance, f'The results differ by {worst:.1f} standard errors'

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
from model import sim, n_groups

ref = tools.read_results(here)

n_runs = 20_000//n_groups # A few seconds, for as many replicates as the reference
tolerance = 12 # People: three standard errors of the difference of two means of 20,000 samples, at the time when runs differ most


if __name__ == '__main__':
    quiet = sim.new(verbose=0).init()
    res = {state:[] for state in 'SIR'}
    for seed in range(n_runs):
        sir = quiet.restart(rand_seed=seed).run().results.sir
        for state in 'SIR':
            res[state].append(np.asarray(sir[state].by('run').values).T) # Replicates by times
    res = {state:np.concatenate(vals) for state,vals in res.items()}
    for state in 'SIR':
        values = res[state]
        ours, theirs = values.mean(axis=0), np.array(ref[state][1]) # A stock at index k is the number at time k, in both
        diff = np.abs(ours - theirs).max()
        print(f'{state}: mean at the end {ours[-1]:7.1f} (original {theirs[-1]:7.1f}); largest difference in the mean {diff:5.1f} people of 1,001; largest standard error {(values.std(axis=0)/np.sqrt(len(values))).max():.1f}')
        assert diff <= tolerance, f'The mean of {state} differs by {diff:.1f} people, against a tolerance of {tolerance}'
    print(f'runs that died out: {(res['R'][:, -1] < 50).mean():.1%}')

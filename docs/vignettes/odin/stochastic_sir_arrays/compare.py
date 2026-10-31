"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))
sys.path.insert(0, os.path.join(root, 'docs', 'models'))
import tools
from model import sim

ref = tools.read_results(os.path.join(root, 'docs', 'models', 'odin', 'stochastic_sir_arrays'))

n_runs = 20_000 # In one process, where they are a single call to the kernels: a few seconds, and as many samples as the reference
tolerance = 12 # People: three standard errors of the difference of two means of 20,000 samples, at the time when runs differ most


if __name__ == '__main__':
    res = ss.parallel(sim.new(verbose=0), n_runs=n_runs, parallel=False).results.sir
    for state in 'SIR':
        values = np.asarray(res[state].values)
        ours, theirs = values.mean(axis=0), np.array(ref[state][1]) # A stock at index k is the number at time k, in both
        diff = np.abs(ours - theirs).max()
        print(f'{state}: mean at the end {ours[-1]:7.1f} (original {theirs[-1]:7.1f}); largest difference in the mean {diff:5.1f} people of 1,001; largest standard error {(values.std(axis=0)/np.sqrt(len(values))).max():.1f}')
        assert diff <= tolerance, f'The mean of {state} differs by {diff:.1f} people, against a tolerance of {tolerance}'
    print(f'runs that died out: {(np.asarray(res.R.values)[:, -1] < 50).mean():.1%}')

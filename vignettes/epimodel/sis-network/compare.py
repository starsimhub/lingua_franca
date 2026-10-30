"""
Compare the Starsim version with the reference results of the original

    python compare.py

Raises an error if the results stop agreeing, within the tolerances below.
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
sys.path.insert(0, os.path.join(root, 'examples'))
import tools
from model import sim

ref = tools.read_results(os.path.join(root, 'examples', 'epimodel', 'sis-network'))
n_runs = 100
tol = 0.05 # Of each number; the means of 100 runs each differ by about 1% by chance
recovered_at_once = 0.95 # EpiModel counts after recovery, which can follow infection within a step: about 5% of those infected (the recovery probability)

if __name__ == '__main__':
    msim = ss.parallel(sim.new(verbose=0), n_runs=n_runs, parallel=False)
    res = msim.results.sis
    theirs = np.array(ref['i.num'][1]) # Index k is the number after k steps in both (the original's first value is the start)
    ours = np.asarray(res.I.values).mean(axis=0)[:len(theirs)]
    flow, their_flow = np.asarray(res.infection.values).mean(axis=0)[:len(theirs)][-200:].mean(), np.mean(ref['si.flow'][1][-200:])
    late, their_late = ours[-200:].mean(), theirs[-200:].mean()
    print(f'infected, mean of the last 200 steps: {late:.1f} (original {their_late:.1f}); after allowing for the order within a step, {late*recovered_at_once:.1f}')
    print(f'infected at step 50: {ours[50]:.1f} ({theirs[50]:.1f}); at step 100: {ours[100]:.1f} ({theirs[100]:.1f})')
    print(f'new infections per step, last 200 steps: {flow:.2f} (original {their_flow:.2f})')
    print(f'original network: {np.mean(ref["edges"][1][-200:]):.0f} edges, mean degree {np.mean(ref["meandeg"][1][-200:]):.2f}, {np.mean(ref["concurrent"][1][-200:]):.0f} people with two or more partners')
    nets = [run.networks[0].results for run in msim.sims]
    print(f'Starsim network: mean degree {np.mean([net.mean_degree[-200:].mean() for net in nets]):.2f}, {500*np.mean([net.concurrency[-200:].mean() for net in nets]):.0f} people with two or more partners')
    assert abs(flow/their_flow - 1) < tol, f'New infections per step differ by more than {tol:.0%}'
    assert abs(late*recovered_at_once/their_late - 1) < tol, f'Infected at equilibrium differ by more than {tol:.0%}, after the order within a step'
    assert abs(ours[50]*recovered_at_once/theirs[50] - 1) < 0.1, 'Infected at step 50 differ by more than 10%, after the order within a step' # The rise is noisier than the equilibrium

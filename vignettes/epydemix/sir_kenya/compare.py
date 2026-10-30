"""
Compare the Starsim version with the reference results of the original

    python compare.py

Raises an error if the peak of the infected, in total or in an age group, differs by more than 1%
or comes more than a day apart, or if the final size differs by more than 0.1 of a percentage point.
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
sys.path.insert(0, os.path.join(root, 'examples'))
import tools
from model import sim, data

ref = tools.read_results(os.path.join(root, 'examples', 'epydemix', 'sir_kenya'))

if __name__ == '__main__':
    res = ss.parallel(sim.new(verbose=0), n_runs=100, parallel=False).results.sir
    total = sum(data['Nk'])
    for group in data['groups'] + ['total']:
        ours = (res.I if group == 'total' else res.I.select(age=group)).mean().values
        theirs = np.array(ref[f'Infected_{group}'][1]) # A stock at index k is the number on day k, in both
        n = min(len(ours), len(theirs))
        print(f'Infected, {group:6s} peak {ours.max():12,.0f} (original {theirs.max():12,.0f}) on day {ours.argmax()} ({theirs.argmax()}); largest difference {np.abs(ours[:n] - theirs[:n]).max()/theirs.max():.1%} of the peak')
        assert abs(ours.max()/theirs.max() - 1) < 0.01, f'The peak in {group} differs by more than 1%'
        assert abs(int(ours.argmax()) - int(theirs.argmax())) <= 1, f'The peak in {group} is more than a day apart'
    final, their_final = res.R.mean().values[-1]/total, ref['Recovered_total'][1][-1]/total # Day 123, the original's last day
    print(f'Recovered at the end: {final:.2%} (original {their_final:.2%})')
    assert abs(final - their_final) < 0.001, 'The final size differs by more than 0.1 of a percentage point'

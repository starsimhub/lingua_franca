"""
Compare the Starsim version with the reference results of the original

    python compare.py

Raises an error if any compartment in either province differs by 1e-6 people or more on any day.
"""
import os
import sys
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))
sys.path.insert(0, os.path.join(root, 'docs', 'models'))
import tools
from model import sim, pop

ref = tools.read_results(os.path.join(root, 'docs', 'models', 'flepimop', 'seir_2pop'))
tol = 1e-6 # People

if __name__ == '__main__':
    res = sim.new(verbose=0).run().results.seir
    worst = 0
    for place in pop:
        for state in 'SEIR':
            ours, theirs = res[state].select(patch=place).values, np.array(ref[f'{place}_{state}'][1]) # A stock at index k is the number on day k, in both
            diff = np.abs(ours - theirs).max()
            worst = max(worst, diff)
            print(f'{place} {state}: at the end {ours[-1]:8.1f} (original {theirs[-1]:8.1f}); peak on day {ours.argmax()} ({theirs.argmax()}); largest difference {diff:6.1f} people')
    assert worst < tol, f'The largest difference is {worst:.2e} people, against a tolerance of {tol}'
    print(f'largest difference: {worst:.1e} people')

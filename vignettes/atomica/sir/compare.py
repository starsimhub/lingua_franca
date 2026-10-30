"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
sys.path.insert(0, os.path.join(root, 'examples'))
import tools
from model import sim

ref = tools.read_results(os.path.join(root, 'examples', 'atomica', 'sir'))
tolerance = 1e-6 # People: the databook's numbers are written here to five decimal places

if __name__ == '__main__':
    res = sim.new(verbose=0).run().results.sir
    for state in ['sus', 'inf', 'rec', 'dead']:
        ours, theirs = res[state].values, np.array(ref[f'adults_{state}'][1]) # A stock at index k is the number at time k, in both
        diff = np.abs(ours - theirs).max()
        print(f'{state:5s} at the end {ours[-1]:8.2f} (original {theirs[-1]:8.2f}); largest difference {diff:.3g} people')
        assert diff < tolerance, f'{state} differs by {diff:.3g} people'
    smooth = sim.new(verbose=0, integrator='rk4', substeps=None).run().results.sir
    print(f'with the default integrator, inf at the end is {smooth.inf[-1]:.1f}: the yearly Euler step is part of the original model')

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
from model import sim, control

ref = {k:np.array(v[1]) for k,v in tools.read_results(here).items()}
tolerances = dict(control=2e-5, measure=2e-3) # As shares of the population; see the README for why the second is wider


def check(name, which, run, tol):
    """ The largest difference from the original over all days and states """
    res = run.results.sir
    diff = max(np.abs(res[c].values - ref[f'{which}_{c}']).max() for c in 'SIR')/1e6
    print(f'{name}: largest difference {diff:.2e} of the population, tolerance {tol:.0e}')
    assert diff < tol


if __name__ == '__main__':
    check('Without the measure', 'control', control.run(), tolerances['control'])
    check('With the measure', 'with', sim.run(), tolerances['measure'])

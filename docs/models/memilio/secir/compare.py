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

ref = tools.read_results(here)
names = dict(S='Susceptible', E='Exposed', INS='InfectedNoSymptoms', ISy='InfectedSymptoms', ISev='InfectedSevere', ICr='InfectedCritical', R='Recovered')

tolerance = 73 # People, of 83,000: the error of the reference itself, which is interpolated between steps of about two days
dead_tolerance = 0.5 # People


def compare(name, ours, tol):
    """ Print the comparison of one series with the reference, and raise if the largest difference is over the tolerance """
    theirs = np.array(ref[name][1])
    diff = np.abs(ours - theirs).max()
    print(f'{name:20s} at the end {ours[-1]:9.1f} (original {theirs[-1]:9.1f}); largest difference {diff:7.1f} people')
    assert diff <= tol, f'{name} differs by {diff:.1f} people, against a tolerance of {tol}'
    return


if __name__ == '__main__':
    res = sim.new(verbose=0).run().results.secir
    for key,name in names.items():
        compare(name, res[key].values, tolerance) # A stock at index k is the number on day k, in both
    compare('Dead', res.death.cum.values, dead_tolerance) # Deaths up to each day

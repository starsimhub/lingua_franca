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

ref = tools.read_results(os.path.join(root, 'docs', 'models', 'memilio', 'secir_ageres'))
names = dict(S='Susceptible', E='Exposed', INS='InfectedNoSymptoms', ISy='InfectedSymptoms', ISev='InfectedSevere', ICr='InfectedCritical', R='Recovered')
tolerance = 1.5 # People, of 10,000: the error of the reference itself, which is interpolated between solver steps
dead_tolerance = 0.02 # People


def report(name, ours, theirs, tol=tolerance, start=0):
    """ Compare from the original's day `start` on; `ours` begins on that day, and may run past the original's last """
    theirs = np.array(theirs)[start:]
    ours = ours[:len(theirs)]
    diff = np.abs(ours - theirs)
    print(f'{name:20s} at the end {ours[-1]:8.1f} (original {theirs[-1]:8.1f}); largest difference {diff.max():5.2f} people, on day {diff.argmax() + start}')
    assert diff.max() <= tol, f'{name} differs by {diff.max():.2f} people, against a tolerance of {tol}'
    return


if __name__ == '__main__':
    for dt in [1, 0.1]:
        res = sim.new(verbose=0, dt=ss.days(dt)).run().results.secir # A shorter step only to show where the differences come from
        step = int(round(1/dt))
        print(f'\nWith a step of {dt} days:')
        # A stock at index k is the number after k steps, so the number on day d is at index d*step
        for key,name in names.items():
            report(name, res[key].values[::step], ref[name][1])
        dead = res.death.cum.values[::step] # Deaths up to each day
        report('Dead', dead, ref['Dead'][1], dead_tolerance)
        for g in range(3):
            report(f'InfectedSymptoms_{g}', res.ISy.select(age=str(g)).values[::step], ref[f'InfectedSymptoms_{g}'][1])

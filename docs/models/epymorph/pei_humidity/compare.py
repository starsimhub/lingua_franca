"""
Compare the Starsim version with the reference results of the original

    python compare.py

Both are stochastic, but with 10,000 people infectious at the start the runs differ little, so the
comparison is of the mean of 20 runs of each. For all six states together and for each, it checks
the peak of the number infectious and its day, and the number infected over the run.
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim, places

ref = {k:np.array(v[1]) for k,v in tools.read_results(here).items()}
tolerances = dict(peak=0.05, day=4, infected=0.03) # Relative, in days, and relative; see the README


def check(name, infectious, infected, suffix=''):
    """ The peak and its day, and the infections, as numbers and as differences from the original """
    theirs, total = ref[f'I{suffix}'], ref[f'new_infections{suffix}'].sum()
    size, day, more = infectious.max()/theirs.max() - 1, infectious.argmax() - theirs.argmax(), infected/total - 1
    print(f'{name:4s} peak {infectious.max():10,.0f} on day {infectious.argmax():3d}, original {theirs.max():10,.0f} on day {theirs.argmax():3d}: {size:+.1%}, {day:+d} days; infected {infected:11,.0f}, original {total:11,.0f}: {more:+.1%}')
    assert abs(size) < tolerances['peak'] and abs(day) <= tolerances['day'] and abs(more) < tolerances['infected']


if __name__ == '__main__':
    res = [run.results.flu for run in ss.parallel(sim, n_runs=20).sims]
    check('All', np.mean([r.I.values for r in res], axis=0), np.mean([r.infection.values.sum() for r in res]))
    for state in places.names:
        check(state, np.mean([r.I.select(patch=state).values for r in res], axis=0), np.mean([r.infection.select(patch=state).values.sum() for r in res]), suffix=f'_{state}')

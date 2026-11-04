"""
Compare the Starsim version with the reference results of the original

    python compare.py

Both are stochastic, so the comparison is of the mean of the runs in which the epidemic takes off: 40
runs of each, as in `run.py`. For the state and each county it checks the peak of the mean number
infectious, its day, and the number recovered at the end.
"""
import os
import sys
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim, places

ref = {k:np.array(v[1]) for k,v in tools.read_results(here).items()}
tolerances = dict(peak=0.08, day=6, recovered=0.03) # Relative, in days, and relative; see the README for why these are wide


def check(name, ours, theirs):
    """ The peak and its day, as numbers and as a difference from the original """
    size, day = ours.max()/theirs.max() - 1, ours.argmax() - theirs.argmax()
    print(f'{name:12s} peak {ours.max():9,.0f} on day {ours.argmax():3d}, original {theirs.max():9,.0f} on day {theirs.argmax():3d}: {size:+.1%}, {day:+d} days')
    assert abs(size) < tolerances['peak'] and abs(day) <= tolerances['day']


if __name__ == '__main__':
    runs = sim.run(n_runs=40).sims
    res = [run.results.sirs for run in runs if run.results.sirs.I.values.max() >= 1000] # The runs in which the epidemic took off
    print(f'The epidemic took off in {len(res)} of {len(runs)} runs')
    check('Arizona', np.mean([r.I.values for r in res], axis=0), ref['I'])
    for county in places.names:
        check(county.split(',')[0], np.mean([r.I.select(patch=county).values for r in res], axis=0), ref[f'I_{county.split(",")[0]}'])
    recovered = np.mean([r.R.values[-1] for r in res])
    diff = recovered/ref['R'][-1] - 1
    print(f'Recovered at the end: {recovered:,.0f}, original {ref["R"][-1]:,.0f}: {diff:+.1%}')
    assert abs(diff) < tolerances['recovered']

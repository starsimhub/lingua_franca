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

ref = {k:np.array(v[1]) for k,v in tools.read_results(here).items()}
groups = ['0-19', '20-39', '40+']
tolerance = 1e-6 # Of each state's largest value, in total and in each age group


def worst(res, prefix='', disease='seir'):
    """ The largest difference in each state, in total and in each age group, as a share of the original's largest value; the original's results are once a day, from day 0 """
    res = res[disease]
    out = {}
    for state in 'SEIR':
        diffs = {}
        for group in [None] + groups:
            theirs = ref[f'{prefix}{state}' + (f'_{group}' if group else '')]
            ours = res[state].values if group is None else res[state].select(age=group).values
            diffs[group or 'total'] = np.abs(ours - theirs).max()/theirs.max()
        out[state] = diffs
    return out


def peak(res, prefix='', disease='seir'):
    """ The peak of I and its day, and the number ever infected, in the Starsim version and the original """
    I, theirs = res[disease].I.values, ref[f'{prefix}I']
    size, their_size = res[disease].R.values[-1] + I[-1] + res[disease].E.values[-1], ref[f'{prefix}R'][-1] + theirs[-1] + ref[f'{prefix}E'][-1]
    return f'peak I {I.max():,.0f} on day {I.argmax()} (original {theirs.max():,.0f} on day {theirs.argmax()}); {size:,.0f} infected (original {their_size:,.0f})'


if __name__ == '__main__':
    res = sim.new(verbose=0).run().results
    diffs = worst(res)
    print('; '.join(f'{s} {max(d.values()):.1e}' for s,d in diffs.items()) + ' (largest differences, in total and by age, as shares of the largest value)')
    print(peak(res))
    for state,d in diffs.items():
        for group,val in d.items():
            assert val <= tolerance, f'{state} ({group}) differs by {val:.1e} of its largest value'

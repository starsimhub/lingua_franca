"""
Compare the Starsim version with the reference results of the original

    python compare.py
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

ref = tools.read_results(os.path.join(root, 'examples', 'odin', 'seir_array'))
ages = {'0-1':'0', '1-5':'1-4', '5-15':'5-14', '15-30':'15-29', '30+':'30+'} # The original's names, and Starsim's labels
tolerance = 0.005 # Of each state's largest value, in total
tolerance_age = 0.01 # The same, in each age group but the youngest,
youngest = dict(S=0.01, E=0.2, I=0.08, R=0.12) # which differs because the original's latent do not age (finding 2 in the README)


def variant(old, new):
    """ The sim of model.py with one piece of its text replaced, for the checks below """
    with open(os.path.join(here, 'model.py')) as f:
        src = f.read()
    assert old in src
    out = dict(__name__='variant')
    exec(src.replace(old, new), out)
    return out['sim']


def worst(sim):
    """ The largest difference in each state over the year, as a share of its largest value: in total, and in the age group where it is largest """
    res = sim.new(verbose=0).run().results.seir
    out = {}
    step = (len(res.S.values) - 1)//365 # The steps in a day
    for state in 'SEIR': # A stock at index k*step is the number on day k, in both
        theirs = np.array(ref[state][1])
        total = np.abs(res[state].values[::step] - theirs).max()/theirs.max()
        by_age = {}
        for age,label in ages.items():
            theirs = np.array(ref[f'{state}_{age}'][1])
            by_age[age] = np.abs(res[state].select(age=label).values[::step] - theirs).max()/theirs.max()
        age = max(by_age, key=by_age.get)
        out[state] = (total, age, by_age[age], res[state].values[::step], by_age)
    return out


def show(label, sim):
    diffs = worst(sim)
    print(f'{label:28s} ' + '; '.join(f'{s} {d[0]:.2%} (worst age {d[1]}: {d[2]:.2%})' for s,d in diffs.items()))
    return diffs


if __name__ == '__main__':
    diffs = show('model.py', sim)
    I, theirs = diffs['I'][3], np.array(ref['I'][1]) # Both from day 0
    print(f'  peak I {I.max():,.0f} on day {I.argmax()} (original {theirs.max():,.0f} on day {theirs.argmax()}); I on day 30 {I[30]:.1f} (original {theirs[30]:.1f})')
    for state,(total,_,_,_,by_age) in diffs.items():
        assert total <= tolerance, f'{state} differs by {total:.2%} of its largest value'
        for age,val in by_age.items():
            limit = youngest[state] if age == '0-1' else tolerance_age
            assert val <= limit, f'{state} in age group {age} differs by {val:.2%} of its largest value'
    assert I.argmax() == theirs.argmax(), 'The peak of I is on another day'
    show('without the workaround', variant('    history', '    # history'))
    show('half a day', sim.new(dt=ss.days(0.5)))

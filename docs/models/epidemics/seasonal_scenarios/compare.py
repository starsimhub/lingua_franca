"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
import model

ref = {k:np.array(v[1]) for k,v in tools.read_results(here).items()}
groups = ['0-19', '20-39', '40+']
tolerances = dict(baseline=1e-3, intervention=1e-2, vaccination=2e-3) # Of each state's largest value; see the README for the second
cuts = [(50, 120, [0.1, 0.01, 0.01]), (65, 90, [0.01, 0.2, 0.2]), (120, 180, [0.05, 0.01, 0.01])] # The vignette's three interventions


def added():
    """ The cuts combined as epidemics combines them, adding where they overlap, as a modifier for each period between their starts and stops """
    edges = sorted({t for start,stop,_ in cuts for t in [start, stop]})
    mods = []
    for start,stop in zip(edges[:-1], edges[1:]):
        total = sum(np.array(r) for a,b,r in cuts if a <= start < b) # Over 1 in the original would be capped at 1
        cut = ss.by(age=1 - total)
        mods += [ss.modify(rel, multiply=cut, when=ss.schedule(start=start, stop=stop)) for rel in [model.seirv.rel_sus, model.seirv.rel_trans]]
    return model.baseline.new(interventions=mods)


def check(name, sim, tol=None):
    """ The largest difference in any state, in total or in an age group, as a share of the original's largest value; the original's results are once a day """
    res = sim.new(verbose=0).run().results.seirv
    step = (len(res.S.values) - 1)//365 # The steps in a day
    big = 0
    for state in 'SEIRV':
        for group in [None] + groups:
            theirs = ref[f'{name}_{state}' + (f'_{group}' if group else '')]
            ours = (res[state] if group is None else res[state].select(age=group)).values[::step]
            if theirs.max() > 0:
                big = max(big, np.abs(ours - theirs).max()/theirs.max())
    I, theirs = res.I.values[::step], ref[f'{name}_I']
    print(f'{sim.label or name}: largest difference {big:.1e} of a largest value' + (f', tolerance {tol:.0e}' if tol else '') +
          f'; peak I {I.max():,.0f} on day {I.argmax()} (original {theirs.max():,.0f} on day {theirs.argmax()}); recovered by day 365 {res.R.values[-1]:,.0f} (original {ref[f"{name}_R"][-1]:,.0f})')
    if tol:
        assert big <= tol, f'{name} differs by {big:.1e}'
    return res


if __name__ == '__main__':
    check('baseline', model.baseline, tolerances['baseline'])
    check('intervention', model.sim, tolerances['intervention'])
    res = check('vaccination', model.vaccination, tolerances['vaccination'])
    print(f'  vaccinated by day 365: {res.V.values[-1]:,.0f} (original {ref["vaccination_V"][-1]:,.0f})')
    check('intervention', added().new(label='intervention, with the cuts added as in epidemics'))
    check('baseline', model.baseline.new(dt=ss.days(0.25), label='baseline, quarter-day steps'))

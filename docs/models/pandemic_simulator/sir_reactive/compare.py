"""
Compare the Starsim version with the numbers published in the Pandemic Simulator's interventions guide

The guide reports a run of the example config: 20 Latin hypercube draws of beta, adherence, and
reduction, summarized by the median at each time. Twenty draws vary, so this makes five sets of them.

    python compare.py
"""
import numpy as np
import scipy.stats.qmc as qmc
import starsim as ss

published = 'peak 25% to 19%, ten days later; infections about 939,000 to 865,000'
pars = dict(total_pop=1e6, start='2026-01-01', stop='2026-12-31', dt=ss.days(1), solver='ode', verbose=0)


def run(beta, multiply=None):
    """ One run: the number infectious at each time, and the infections in all """
    S, I, R = ss.states('S I R')
    sir = ss.Disease(infection=S >> I @ beta*I, recovery=I >> R @ ss.days(10), init_n=dict(I=100), name='sir')
    measure = None if multiply is None else ss.modify(sir.pars.beta, multiply=multiply, where=sir.I.n >= 20_000)
    res = ss.Sim(sir, interventions=measure, **pars).run().results.sir
    return res.I.values.copy(), np.cumsum(res.infection.values) + 100


def summary(runs):
    """ The peak of the median, its day, and the median of the infections at the end """
    median = np.median([r[0] for r in runs], axis=0)
    return median.max()/1e6, median.argmax(), np.median([r[1][-1] for r in runs])


if __name__ == '__main__':
    print(f'Published: {published}')
    for seed in range(5):
        u = qmc.LatinHypercube(d=3, seed=seed).random(20)
        betas, adherence, reduction = 0.2 + 0.2*u[:,0], 0.4 + 0.2*u[:,1], 0.45 + 0.1*u[:,2]
        p0, d0, n0 = summary([run(b) for b in betas])
        p1, d1, n1 = summary([run(b, 1 - a*r) for b,a,r in zip(betas, adherence, reduction)])
        print(f'Draws {seed}: peak {p0:.1%} to {p1:.1%}, {d1 - d0} days later; infections {n0:,.0f} to {n1:,.0f}')

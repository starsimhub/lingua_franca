"""
An SIR with a reactive intervention: the Starsim version of the Pandemic Simulator's declarative teaching example

Everything is the example's central values. The measure removes 25% of transmission (50% adherence
times a 50% reduction) whenever at least 2% of the population is infectious. The example's release
threshold of 1% is left out because the original's default solver does not use it.
"""
import starsim as ss

S, I, R = ss.states('S I R')
beta = ss.par(0.3, bounds=[0.2, 0.4])
sir = ss.Disease(infection=S >> I @ beta*I, recovery=I >> R @ ss.days(10), init_n=dict(I=100), name='sir')
measure = ss.modify(sir.pars.beta, multiply=1 - 0.5*0.5, who=sir.I.n >= 20_000)
sim = ss.Sim(sir, interventions=measure, total_pop=1e6, start='2026-01-01', stop='2026-12-31', dt=ss.days(1), solver='ode', verbose=0)
control = sim.new(interventions=None)

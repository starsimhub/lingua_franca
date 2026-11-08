"""
The flepiMoP two-population tutorial (docs/models/flepimop/seir_2pop), in Starsim: an SEIR in a large
and a small province, whose residents spend part of each day in the other
"""
import starsim as ss

pop     = dict(large_province=9000, small_province=1000)
commute = [[0, 100/9000], [20/1000, 0]] # The share of each province's residents who travel to the other
gamma   = 1/5

S, E, I, R = ss.states('S E I R')
seir = ss.Disease(
    infection = ss.Transition(S, E, rate=2.5*gamma * I),
    onset     = ss.Transition(E, I, rate=1/4),
    recovery  = ss.Transition(I, R, rate=gamma),
    init_n    = dict(E=ss.by(patch=[5, 0])),
)
away = [[0.5*share for share in row] for row in commute] # Travelers are away for half the day
seir.stratify(patch=ss.levels(pop, mobility=ss.geo.Mobility(away, kind='visit')))
sim = ss.Sim(seir, total_pop=sum(pop.values()), start='2020-02-01', stop='2020-08-31', solver=ss.solvers.ode(substeps=1)) # One RK4 step a day, as in the original

if __name__ == '__main__':
    sim.run()
    sim.plot()

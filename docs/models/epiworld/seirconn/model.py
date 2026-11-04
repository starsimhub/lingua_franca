"""
The epiworldR SEIR in a fully connected population (docs/models/epiworld/seirconn), in Starsim:
COVID-19 among 10,000 people who each meet two others a day, starting from one person exposed, run
50 times. Every person is alike and everyone meets everyone, so the original's agents are a chain
binomial, which is how this runs: in whole days, with each day's chances worked out at its start
"""
import starsim as ss

S, E, I, R = ss.states('S E I R')
seir = ss.Disease(
    infection = S >> E @ 2*0.5*I,      # Two contacts a day, each infecting with a chance of 0.5
    onset     = E >> I @ ss.prob(1/7), # A chance of 1 in 7 a day, so 7 days on average
    recovery  = I >> R @ ss.prob(1/3),
    init_n    = dict(E=1),
)
sim = ss.Sim(seir, total_pop=10_000, stop=50, solver='binomial', substeps=1)

if __name__ == '__main__':
    msim = sim.run(n_runs=50)
    msim.plot()

"""
The odin age-structured SEIR with a delay (examples/odin/seir_array), in Starsim: an SEIR in 10
million people in five age groups, with births, deaths, aging, waning immunity, and a latent
period of exactly 14 days
"""
import numpy as np
import starsim as ss

b = 1/50 # Births and deaths, per year
aging = np.array([1, 1/4, 1/10, 1/15, 0]) # Per year: one over the width of each age group
split = b*np.cumprod(np.append(1, aging[:-1])/(aging + b)) # The stable age distribution
surv = np.exp(-b*14/365) # The share of the latent who live for 14 days

S, E, I, R = ss.states(4)
seir = ss.Disease(
    infection = S >> E @ ss.perday(1) * I,
    onset     = E >> I @ ss.constant(ss.days(14)), # Exactly 14 days, as in the original
    recovery  = I >> R @ ss.days(30),
    waning    = R >> S @ ss.days(60),
    births    = ss.birth(S, rate=ss.peryear(b)),
    deaths    = ss.death(rate=ss.peryear(b)),
    history   = ss.null >> I @ ss.timeseries({0: ss.perday(surv), 14: 0}), # Workaround: see README
    init_n    = dict(I=1),
)
seir.stratify(age=[0, 1, 5, 15, 30], split=split)
sim = ss.Sim(seir, total_pop=1e7, unit='day', stop=365)

if __name__ == '__main__':
    sim.run()
    sim.plot()

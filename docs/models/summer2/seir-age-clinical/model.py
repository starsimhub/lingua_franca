"""
The summer2 derived-outputs example (docs/models/summer2/seir-age-clinical), in Starsim: an SEIR by
age, in which the infectious are asymptomatic, symptomatic, isolated, or in hospital, with outputs
by age and by clinical status
"""
import starsim as ss

S, E, I, R = ss.states('S E I R')
seir = ss.Disease(
    infection       = S >> E @ 2 * I,
    incidence       = E >> I @ 0.5 * ss.by(age=[1, 1.1]), # The old's shares sum to 1.1
    recovery        = I >> R @ 0.3,
    infection_death = ss.death(I, rate=0.05 * ss.by(clinical=[0, 1, 1, 2])),
    init_n          = dict(I=ss.by([[5, 0, 0, 0], [5, 0, 0, 0]], dims=['age', 'clinical'])),
)
seir.stratify(age=['young', 'old'])
seir.stratify(clinical=ss.levels( # Clinical status, which those who fall ill take by age
    ['asymptomatic', 'symptomatic', 'isolated', 'hospital'],
    states    = ['I'],
    fractions = ss.by([[0.4, 0.3, 0.2, 0.1], [0.3, 0.3, 0.2, 0.3]], dims=['age', 'clinical']),
))
rel_trans = ss.modify(seir.rel_trans, multiply=ss.by(clinical=[0.5, 1, 0.2, 0.1]))
sim = ss.Sim(seir, connectors=rel_trans, total_pop=1000, dt=0.1, stop=20)

if __name__ == '__main__':
    sim.run()
    sim.plot()

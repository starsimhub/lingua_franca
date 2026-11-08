"""
The camdl age- and patch-structured SEIR (docs/models/camdl/stratified), in Starsim: contacts by age
within each patch, aging, movement between patches, and children vaccinated on day 20
"""
import starsim as ss

contacts = [[12, 4, 1], [4, 8, 2], [1, 2, 3]]
pop = ss.by([[3000, 1000], [5000, 2000], [2000, 500]], dims=['age', 'patch'])

S, E, I, R = ss.states(4)
seir = ss.Disease(
    infection = S >> E @ ss.perday(0.04) * I,
    onset     = E >> I @ ss.days(5),
    recovery  = I >> R @ ss.perday(0.1),
    init_n    = dict(I=ss.by(age=[10, 0, 0], patch=[1, 0])),
    name      = 'seir',
)
seir.stratify(age=[0, 5, 50]) # Children, adults, and elders, who age at 1/5 and 1/45 a year
seir.stratify(patch=ss.levels(['north', 'south'], kind='space', fractions=pop, mobility=ss.geo.Mobility(matrix=[[0, 0.01], [0.01, 0]], kind='migrate')))
vaccinate = ss.vaccinate(seir.S >> seir.R, when=[20], coverage=0.6, who=ss.person.age < 5)
sim = ss.Sim(seir, networks=ss.contacts(contacts), total_pop=13_510, unit='day', stop=150, aging=True)

if __name__ == '__main__':
    ss.parallel(dict(novax=sim, vax=sim.new(interventions=vaccinate))).plot()

"""
The LASER hub-and-spoke example (examples/laser/hub_spoke_seir), in Starsim: an SEIR in a city
and fifteen smaller places on five spokes, coupled by a gravity model
"""
import numpy as np
import starsim as ss

# The places: a city, and on each of five spokes two interim places and a town
angles = 2*np.pi*np.arange(5)/5
names  = ['Central City'] + [f'Town {i+1}' for i in range(5)] + [f'Interim {i+1}{ab}' for i in range(5) for ab in 'AB']
pop    = [1_000_000] + [100_000]*5 + [25_000]*10
dist   = [0] + [150]*5 + [50, 100]*5 # Distance from the city, in km
angle  = [0] + list(angles) + list(np.repeat(angles, 2))
places = ss.geo.geography(names=names, pop=pop, x=dist*np.cos(angle), y=dist*np.sin(angle))

S, E, I, R = ss.states(4)
seir = ss.Disease(
    infection = S >> E @ ss.perday(2/14) * I,
    onset     = E >> I @ ss.normal(7, 1, unit='days'),
    recovery  = I >> R @ ss.normal(14, 2, unit='days'),
    init_n    = dict(I=ss.by(patch=[0, 100] + [0]*14)), # 100 infectious people in Town 1
)
seir.stratify(patch=places, mobility=ss.geo.Mobility(ss.geo.gravity(c=2.5), kind='force', away=3/32))
sim = ss.Sim(seir, total_pop=sum(pop), n_agents=175_000, stop=ss.days(365))

if __name__ == '__main__':
    sim.run()
    sim.plot()

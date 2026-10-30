"""
The LASER England and Wales measles model (examples/laser/england_wales), in Starsim: measles in
towns and cities (here the 53 within 100 km of Norwich), with births, deaths from a life table,
seasonal transmission, importations, and the force of infection moving between places by gravity
"""
import os
import sys
import numpy as np
import starsim as ss

folder = os.environ.get('LASER_DATA', os.path.join(os.path.dirname(__file__), '..', '..', '..', '_envs', 'laser', 'src', 'laser-generic-1.1.0', 'data'))
sys.path.insert(0, folder)
from EnglandWalesMeasles import data as engwal

# The run is scaled down in the same way in the original's reference: the places within 100 km of Norwich, for 10 years
center, radius, years = 'Norwich', 100, 10
distances = np.load(os.path.join(folder, 'EnglandWalesDistances.npy'))
keep = distances[engwal.placenames.index(center)] <= radius
distances = distances[np.ix_(keep, keep)]
names = np.array(engwal.placenames)[keep]
pop = np.array([engwal.places[name].population[0] for name in names], dtype=float)
mean_pop = np.array([place.population.mean() for place in engwal.places.values()]) # The birth rate is the mean over all places
cbr = 1000*np.sum(mean_pop*[np.mean(place.births/place.population) for place in engwal.places.values()])/mean_pop.sum()

# Seasonality: 26 values of log beta, each held for 14 days of a 365-day year
log_betas = np.array([0.155, 0.571, 0.46, 0.34, 0.30, 0.34, 0.24, 0.15, 0.31, 0.40, 0.323, 0.238, 0.202, 0.203, 0.074,
                      -0.095, -0.218, -0.031, 0.433, 0.531, 0.479, 0.397, 0.444, 0.411, 0.291, 0.509])
season = np.exp(log_betas - np.append(np.repeat(log_betas, 14), log_betas[-1]).mean())**1.310744
beta = ss.timeseries({14*i: ss.perday(3.865332*s) for i,s in enumerate(season)}, period=ss.days(365))

# Deaths: the age pyramid is the stable one for the birth rate, and the age at death is drawn from it
r = 365*((1 + cbr/1000)**(1/365) - 1)
ages = np.arange(89)
pyramid = np.exp(-r*ages)

S, E, I, R = ss.states(4)
measles = ss.Disease(
    infection = S >> E @ beta * I,
    onset     = E >> I @ ss.normal(8, 2, unit='days'), # The original's infectious-period distribution, which its transmission is given for the latent period (its gamma is used only for people exposed at the start, of whom there are none)
    recovery  = I >> R @ ss.normal(7, 2, unit='days'), # 8 in the original, which loses a day, see README
    births    = ss.birth(S, rate=ss.peryear(r)),
    deaths    = ss.death(lifetable=ss.lifetable(ages, pyramid)),
    init      = dict(R=0.95),
    init_n    = dict(I=ss.by(patch=[3]*len(pop))),
)
towns = ss.geo.geography(names=names, pop=pop, distances=distances)
with np.errstate(divide='ignore'):
    gravity = pop**0.251464/distances**1.563193 # LASER's gravity model, with a=0
np.fill_diagonal(gravity, 0)
gravity *= 0.044565/gravity.sum(axis=1).mean() # Scaled so that the mean share exported is 0.0446,
gravity *= np.minimum(1, 0.2/gravity.sum(axis=1))[:, None] # and no place exports more than 0.2
measles.stratify(patch=towns, mobility=ss.geo.Mobility(matrix=gravity, kind='force'))
importation = ss.Delivery(move=S >> I, capacity=3, start=ss.days(30), interval=ss.days(30)) # 3 people every 30 days, chosen from everyone susceptible
people = ss.People(int(pop.sum()), age_data=np.array([ages, pyramid]).T)
sim = ss.Sim(measles, people=people, interventions=importation, unit='day', stop=years*365)

if __name__ == '__main__':
    sim.run()
    sim.plot()

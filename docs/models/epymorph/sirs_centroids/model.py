"""
SIRS in Arizona's 15 counties, with commuting that falls off with distance: the Starsim version of epymorph's
vignette "Intro to Movement Models" (exercise 2, the centroids movement model)

Each day 15% of people commute for a third of the day, to a county drawn with a weight of exp(-distance/phi),
phi = 20 miles, which includes their own; so the shares of their time they spend in the other counties are
15% times a third times those weights.
"""
import os
import numpy as np
import pandas as pd
import starsim as ss

counties = pd.read_csv(os.path.join(os.path.dirname(__file__), 'original', 'arizona_counties.csv'))
places = ss.geo.geography(names=counties['name'], pop=counties['population'], lat=counties['latitude'], lon=counties['longitude'])
kernel = np.exp(-places.distances/(20*1.609344)) # phi = 20 miles, in km
commuting = ss.geo.Mobility(matrix=0.15*(1/3)*kernel/kernel.sum(axis=1, keepdims=True))

S, I, R = ss.states('S I R')
sirs = ss.Disease(infection=S >> I @ 0.4*I, recovery=I >> R @ ss.days(4), waning=R >> S @ ss.days(200), init_n=dict(I=ss.by(patch={'Maricopa, AZ': 5})), name='sirs')
sirs.stratify(patch=places, mobility=commuting)
sim = ss.Sim(sirs, start='2022-01-01', stop=ss.days(190), solver='tau', verbose=0)

if __name__ == '__main__':
    sim.run()
    sim.results.sirs.I.by('patch').plot()

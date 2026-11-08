"""
Influenza in six southern US states, driven by humidity (Pei et al. 2018): the Starsim version of the
example in epymorph's USAGE notebook, its IPM and MM `Pei`

An SIRS in which transmission falls as absolute humidity rises, in each state on each day, with two
kinds of travelers for a third of each day: 90% of commuters, and a tenth of the mean number of
commuters between each pair of states in each direction (dispersers).
"""
import os
import numpy as np
import pandas as pd
import starsim as ss

folder = os.path.join(os.path.dirname(__file__), 'original')
states = pd.read_csv(os.path.join(folder, 'states.csv'), index_col='state')
humidity = pd.read_csv(os.path.join(folder, 'humidity.csv'), index_col='date')
commuters = states[states.index].values
travel = (0.9*commuters + 0.1*((commuters + commuters.T)//2))/states.population.values[:, None]/3 # Shares of time away
places = ss.geo.geography(names=states.index, populations=states.population)

S, I, R = ss.states('S I R')
H = ss.by(patch=[ss.timeseries(humidity[state].to_dict()) for state in states.index])
D, L = ss.days(4), ss.days(90)
flu = ss.Disease(
    infection = S >> I @ (np.exp(-180*H + np.log(2.0 - 1.3)) + 1.3)/D*I,
    recovery  = I >> R @ D,
    waning    = R >> S @ L,
    init_n    = dict(I=ss.by(patch={'FL': 10_000})),
    name      = 'flu',
)
flu.stratify(patch=ss.levels(places, mobility=ss.geo.Mobility(matrix=travel)))
sim = ss.Sim(flu, start='2015-01-01', dur=ss.days(150), solver='tau', verbose=0)

if __name__ == '__main__':
    sim.run()
    sim.results.flu.I.by('patch').plot()

"""
The measles metapopulation model (docs/models/measles_metapop/seir_districts), in Starsim: a stochastic
SEIR in 260 districts, with gravity mixing, seasonality, births, vaccination, deaths,
importation, and reported cases
"""
import os
import numpy as np
import pandas as pd
import starsim as ss

folder = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'measles_metapop', 'seir_districts', 'original')
districts = pd.read_csv(os.path.join(folder, 'districts.csv'))
pop = districts['pop']*np.exp(-0.012*10) # Projected back from 2020 to 2010

r0 = 15
immune = 0.8*0.9 # The share of births who are vaccinated and immune
S, E, I, R = ss.states(4)
infection   = S >> E @ ss.seasonal(mean=ss.perday(r0/8), amplitude=0.2, peak=29/365) * I
importation = S >> E @ ss.peryear(0.01/1000) * (S + E + I + R).n / S.n
onset       = E >> I @ ss.days(6)
recovery    = I >> R @ ss.days(8)
births      = ss.birth(S, rate=ss.peryear(0.02*(1 - immune)))
vaccinated  = ss.birth(R, rate=ss.peryear(0.02*immune))
deaths      = ss.death(rate=ss.peryear(0.008))
cases       = ss.outcome(0.01*onset)
measles = ss.Disease(infection, importation, onset, recovery, births, vaccinated, deaths, cases, init=dict(R=1 - 1/r0), name='measles')
places = ss.geo.geography(names=districts['dotname'], pop=pop, lat=districts['lat'], lon=districts['lon'])
measles.stratify(district=places, mobility=ss.geo.Mobility(ss.geo.gravity(c=2), kind='visit', away=0.01))
sim = ss.Sim(measles, total_pop=pop.sum(), start='2010-01-01', stop='2025-12-31', unit='day', solver='binomial', substeps=1) # Whole days, as the original takes them

if __name__ == '__main__':
    sim.run()
    sim.plot()

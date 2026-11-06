"""
The epydemix COVID-19 tutorial (docs/models/epydemix/covid19), in Starsim: an age-structured SEIR
with deaths after an Erlang delay, in Massachusetts, with transmission scaled by mobility and
by season, fitted to weekly deaths and projected under three reopening scenarios
"""
import numpy as np
import pandas as pd
import sciris as sc
import starsim as ss

# Starsim has no bundled population data, so this reads what epydemix downloaded
folder = sc.thispath(__file__)/'../../../models/epydemix/covid19'
data = sc.loadjson(folder/'reference/population.json')
matrix = sum(np.array(layer) for layer in data['contacts'].values()) # Four settings
deaths = pd.read_csv(folder/'original/data/MA_deaths.csv', index_col='date', parse_dates=True) # Weekly, each dated by its last day, a Sunday
deaths.index -= pd.Timedelta(weeks=1) # Dated by the start of the week, as a flow's data is read: the week to the end of the Saturday
deaths = ss.SimData(deaths, aliases=dict(deaths='data'))
mob = pd.read_csv(folder/'original/data/MA_google.csv', index_col='date')

# The contact reduction from mobility, from 23 February to 31 May, and held at its last value after
places = ['retail_and_recreation', 'grocery_and_pharmacy', 'transit_stations', 'workplaces', 'residential']
cols = [f'{place}_percent_change_from_baseline' for place in places]
change = mob.loc['2020-02-23':'2020-05-31', cols].mean(axis=1)
r = ss.timeseries(dict(zip(change.index, (1 + change/100)**2)))

mu     = ss.perday(1/2.5) # Recovery rate
IFR    = np.array([0.00161, 0.00695, 0.0309, 0.0844, 0.161, 0.595, 1.93, 4.28, 7.80])/100
R0     = ss.par(2.22, bounds=[1.5, 6.0])
Delta  = ss.par(20, bounds=[7, 27]) # From recovery to death, in 4 stages
I0     = ss.par(4260, bounds=[10, 9999]) # Initially infected, half exposed and half infectious
smin   = ss.par(0.8, bounds=[0.6, 1.0]) # Transmission in mid-July, relative to mid-January
season = ss.seasonal(mean=(1 + smin)/2, amplitude=(1 - smin)/(1 + smin), peak=ss.days(14)) # 15 January
beta   = R0*mu/max(np.linalg.eigvals(matrix).real)*season*r

S, E, I, R, D0, D1, D2, D3, Dead = ss.states('S E I R D0 D1 D2 D3 Dead')
covid = ss.Disease(
    infection = ss.Transition(S, E, rate=beta * I),
    onset     = E >> I @ ss.perday(1/4),
    outcome   = ss.Transition(I, [D0, R], rate=mu, p=ss.by(age=IFR)), # Death with the IFR
    stage1    = D0 >> D1 @ 4/Delta,
    stage2    = D1 >> D2 @ 4/Delta,
    stage3    = D2 >> D3 @ 4/Delta,
    deaths    = D3 >> Dead @ 4/Delta,
    init_n    = dict(E=I0/2, I=I0/2),
)
covid.stratify(age=[0, 10, 20, 30, 40, 50, 60, 70, 80], fractions=data['Nk'])
sim = ss.Sim(covid, networks=ss.contacts(matrix), total_pop=sum(data['Nk']), data=deaths, unit='day',
             start='2020-02-23', stop='2020-05-31', solver='binomial', substeps=1, aging=False) # The calibration period
reopening = dict(moderate=1.3, high=1.5) # Contacts from 1 June, relative to their level on 31 May
reopening = {k:ss.modify(covid.infection, multiply=v, start='2020-06-01') for k,v in reopening.items()}
scenarios = dict(persistence=None, **reopening)

if __name__ == '__main__':
    fit = sim.fit(method='abc-smc', particles=200, generations=5) # To weekly deaths to 31 May
    fit.plot()
    msim = fit.project(scenarios, n=100, stop='2020-08-03') # To the end of 2 August
    msim.plot()

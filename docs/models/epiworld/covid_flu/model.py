"""
The epiworldR advanced modeling vignette (docs/models/epiworld/covid_flu), in Starsim: COVID-19
and flu spreading together among 50,000 people who each meet four others a day, a vaccine given to
half of them, and two measures that cut contacts, on days 10 and 20. As for the SEIR (../seirconn),
it runs as a chain binomial, in whole days
"""
import numpy as np
import starsim as ss

contacts = ss.par(4) # A day
strains = ss.Strains(
    ['covid', 'flu'],
    infection = [1, 0.35/0.5], # A chance of infection for each contact of 0.5 and 0.35
    recovery  = [1, np.log(0.5)/np.log(0.75)], # A chance of recovery of 1/4 and 1/2 a day
)
vaccine = ss.Vaccine(efficacy=dict(acquisition=0.9, transmission=0.5))

S, I, R = ss.states('S I R')
sir = ss.Disease(
    infection = S >> I @ 0.5*contacts*I,
    recovery  = I >> R @ ss.prob(1/4),
    enhanced  = ss.Transition(I, R, rate=ss.prob(0.5), who=vaccine.held), # The vaccine's chance
    init_n    = dict(I=100), # 50 of each
    strains   = strains,
)
vaccination   = ss.vaccinate(vaccine, coverage=0.5, when=0)
isolation     = ss.modify(contacts, set=2, when=ss.schedule(start=11, stop=21)) # The original's day 10, from day 11
advertisement = ss.modify(contacts, set=1.5, when=ss.schedule(start=21))
sim = ss.Sim(sir, interventions=[vaccination, isolation, advertisement], total_pop=50_000, stop=50,
             solver=ss.solvers.binomial(substeps=1))

if __name__ == '__main__':
    sim.run()
    sim.plot(show_interventions=False) # Marking them fails for now (see the README)

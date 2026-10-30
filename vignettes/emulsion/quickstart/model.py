"""
The EMULSION quickstart model (examples/emulsion/quickstart), in Starsim: 100 animals, each with
an age group, a gestation cycle, and a health state, where gestation needs adulthood, every
farrowing gives a newborn (infected or protected by maternal antibodies, by the mother's health),
infectious mothers may abort, and sick animals are quarantined from April to September while
the quarantine has room
"""
import numpy as np
import starsim as ss

dt = 7 # Days
adult_age = 30 # Days: the YAML gives adult_age twice, and EMULSION uses the second
whole = lambda days: ss.days(dt*round(days/dt)) # EMULSION rounds a minimum stay to whole steps


class Life(ss.Disease):
    """ Workaround: EMULSION's animals start in NG before the first step, not during it """
    def init_post(self):
        super().init_post()
        self.ti_NG[self.NG.uids] = -1
        return


NG, G = ss.states('NG G')
J, A = ss.states('J A')
S, E, I, R, Q, M = ss.states('S E I R Q M')
farrowing = ss.Transition(G, NG, dur=ss.constant(ss.days(240)))
newborns  = ss.birth(M, per=farrowing) # One for each farrowing, in every module

# Uniform up to adult_age, plus the step EMULSION ages them by before its first test, in years
ppl = ss.People(100, age_data=ss.uniform(low=dt/365, high=(adult_age + dt)/365))
# Workaround for "as soon as": a very high rate
growth = ss.Disease(
    maturity = ss.Transition(J, A, rate=ss.perday(1e9), where=ppl.age >= adult_age/365),
    newborns = ss.birth(J, per=farrowing),
    first    = 'J',
    name     = 'growth',
)

dates = {'2021-01-01': 0, '2021-04-01': 1, '2021-09-02': 0, '2022-04-01': 1, '2022-09-02': 0}
quarantine = ss.par(ss.timeseries(dates))
health = ss.Disease(
    infection   = S >> E @ ss.perday(0.1)*I.n/(S + E + I + R + Q + M).n,
    onset       = ss.Transition(E, I, rate=ss.perday(0.3), after=whole(10)),
    recovery    = I >> R @ ss.perday(0.01),
    detection   = I >> Q @ ss.perday(0.01)*quarantine*(Q.n < 20),
    release     = Q >> R @ ss.constant(ss.days(30)),
    waning      = R >> S @ ss.perday(0.01),
    loss        = ss.Transition(M, S, rate=ss.perday(0.04), after=whole(adult_age)),
    deaths      = S + R >> ss.null @ ss.perday(0.002),
    sick_deaths = I + Q >> ss.null @ ss.perday(0.004),
    M_deaths    = ss.Transition(M, ss.null, rate=ss.perday(0.002)*(M.time < whole(adult_age))), # EMULSION's escape
    E_deaths    = ss.Transition(E, ss.null, rate=ss.perday(0.004)*(E.time < whole(10))),
    newborns    = newborns,
    vertical    = ss.Transition(M, [I, M], on=newborns, p=[0.3, 0.7], where=ss.mother(E | I | Q, born=True)), # EMULSION's produce_offspring
    init_n      = dict(I=10),
    name        = 'health',
)

abortion = -np.log(1 - 0.2)/240 # Per day, for infectious mothers only: a 20% chance over a gestation
life = Life(
    conception = ss.Transition(NG, G, rate=ss.perday(0.05), after=whole(90), where=growth.A),
    farrowing  = farrowing,
    abortion   = ss.Transition(G, NG, rate=ss.perday(abortion), where=health.I),
    newborns   = ss.birth(NG, per=farrowing),
    first      = 'NG',
    name       = 'life',
)
sim = ss.Sim([life, growth, health], people=ppl, unit='day', dt=dt, start='2021-01-01', stop=ss.days(735), use_aging=True, solver='abm')

if __name__ == '__main__':
    sim.run()
    sim.plot()

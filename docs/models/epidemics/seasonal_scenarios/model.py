"""
The epidemics vignette on time dependence (docs/models/epidemics/seasonal_scenarios), in Starsim:
the default SEIR-V in three age groups of the UK, with a transmission rate that peaks twice a year,
under three scenarios: no intervention, three overlapping cuts in contacts, and vaccination of
people aged 40 and over between the waves
"""
import numpy as np
import starsim as ss

matrix = np.array([[7.883663, 3.157024, 3.084747], [2.764179, 4.854839, 4.570735], [1.557728, 2.636148, 5.005571]]) # Contacts a day
N = [14865748, 16978469, 29438434] # Aged 0-19, 20-39, and 40+, as the vignette prints them
season = ss.seasonal(amplitude=1, peak=ss.days(365/8), period=ss.days(365/2)) # 1 + sin(πt/91.25)

S, E, I, R, V = ss.states(5)
seirv = ss.Disease(S, E, I, R, V, # V is reached only by the vaccination
    infection = S >> E @ 1.3/7/max(np.linalg.eigvals(matrix).real) * season * I,
    onset     = E >> I @ ss.days(2),
    recovery  = I >> R @ ss.days(7),
    init_n    = dict(I=1e-6*sum(N)),
)
seirv.stratify(age=[0, 20, 40], split=N)


def contacts(start, stop, reduction):
    """ Fewer contacts for each age group, as epidemics' intervention(type='contacts'): both as the infected and as the infectious """
    cut = ss.by(age=1 - np.array(reduction))
    return [ss.modify(rel, multiply=cut, start=start, stop=stop) for rel in [seirv.rel_sus, seirv.rel_trans]]


schools    = contacts(50, 120, [0.1, 0.01, 0.01])
workplaces = contacts(65, 90, [0.01, 0.2, 0.2])
reopening  = contacts(120, 180, [0.05, 0.01, 0.01]) # Schools partly reopened
vaccinate  = ss.Delivery(move=S >> V, capacity=ss.perday(0.001*N[2]), who=ss.ppl.age >= 40, start=120, stop=220) # 0.1% of the group a day

baseline = ss.Sim(seirv, networks=ss.contacts(matrix), total_pop=sum(N), unit='day', stop=365)
sim = baseline.new(interventions=schools + workplaces + reopening)
vaccination = baseline.new(interventions=vaccinate)

if __name__ == '__main__':
    msim = ss.parallel(dict(baseline=baseline, intervention=sim, vaccination=vaccination))
    msim.plot('seirv.I')

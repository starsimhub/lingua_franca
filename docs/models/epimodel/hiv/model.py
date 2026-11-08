"""
The EpiModel Gallery HIV model (docs/models/epimodel/hiv), in Starsim: HIV among 1,500 people over two
networks of partnerships (main and casual), with acute, chronic, and AIDS stages, a care cascade from
testing to viral suppression, PrEP for those at risk, arrivals and departures, and four scenarios
"""
import numpy as np
import starsim as ss

depart = 0.0005 # Departures a week, for everyone not in AIDS
week   = ss.prob # EpiModel uses each rate as the probability of an event in a week (a step)


cascade = ss.par(0, doc='Whether the care cascade runs: testing, linkage, suppression, and stopping ART')
care = lambda move, rate, **kw: ss.transfer(dict(care=move), rate=cascade*week(rate), **kw) # Between the levels of care (below)
S = ss.State()
A = ss.State(rel_trans=5, label='Acute')
C = ss.State(label='Chronic')
D = ss.State(rel_trans=2, label='AIDS')
hiv = ss.Disease(
    infection  = ss.Transition(S, A, rate=week(0.0025) * (A + C + D)), # Per act
    chronic    = A >> C @ week(1/12),
    aids       = C >> D @ week(1/520),
    aids_death = D >> ss.dead @ week(1/104),
    departure  = S + A + C >> ss.outside @ week(depart),
    arrival    = ss.birth(S, rate=0.00065),
    test       = care(('undx', 'dx'), 0.015, states=['A', 'C']),
    test_aids  = care(('undx', 'dx'), 0.05, states=['D']),
    link       = care(('dx', 'art'), 0.1),
    relink     = care(('off', 'art'), 0.03),
    suppress   = care(('art', 'supp'), 1/12),
    stop_art   = care(('art', 'off'), 0.002),
    stop_supp  = care(('supp', 'off'), 0.002),
    infected   = A + C + D,
    init_n     = dict(A=2, C=98, D=20), # 8%, in proportion to the time spent in each stage
)
hiv.stratify(care=ss.levels(dict(undx=1, dx=0, art=0, supp=0, off=0), states=[A, C, D])) # Off is off ART after being on it
supp = ss.by(care=[1, 1, 1, 0.5, 1]) # Suppression halves progression
adjust = [ss.modify(hiv.rel_trans, multiply=ss.by(care=[1, 1, 0.3, 0.01, 1])), ss.modify(hiv.chronic, multiply=supp), ss.modify(hiv.aids, multiply=supp),
          ss.modify(hiv.aids_death, multiply=ss.by(care=[1, 1, 1, 0.1, 1]))]


def indicated(sim):
    """ Workaround: who is indicated for PrEP, from both networks: HIV-negative and not on PrEP, with two or more partners or a partner with HIV """
    hiv = sim.diseases.hiv
    sus = hiv['S'].raw & (sim.people.has_prep.raw == 0)
    positive = hiv['A'].raw | hiv['C'].raw | hiv['D'].raw
    degree, exposed = np.zeros(len(sus)), np.zeros(len(sus), dtype=bool)
    for net in sim.networks.values():
        p1, p2 = net.edges.p1, net.edges.p2
        degree += np.bincount(p1, minlength=len(sus)) + np.bincount(p2, minlength=len(sus))
        exposed[p1[positive[p2]]] = exposed[p2[positive[p1]]] = True
    return ss.uids(np.flatnonzero(sus & ((degree >= 2) | exposed)))


# Partnerships last 200 and 26 weeks in all, counting those ended by a departure (ss.DegreeNet allows for them, as EpiModel's d.rate does)
main   = ss.DegreeNet(n_contacts=0.5, concurrency=0.04, max_contacts=2, dur=200, acts=ss.freqperday(3)) # A day here is a step, a week
casual = ss.DegreeNet(n_contacts=0.3, concurrency=0.10, dur=26, acts=ss.freqperday(1))
prep   = ss.Vaccine(efficacy=0.95, waning=-1/np.log(1 - 0.015)) # Stopped with a probability of 0.015 a week
preps  = [ss.vaccinate(prep, when=[0], coverage=0.5, who=indicated, name='start_prep'), # Half of those indicated at the start
          ss.vaccinate(prep, when=ss.schedule(every=1), coverage=0.015, who=indicated, name='take_prep')] # And then 0.015 a week
sim = ss.Sim(hiv, networks=dict(main=main, casual=casual), n_agents=1500, stop=1040, connectors=adjust) # A step is a week
scenarios = dict(none=sim, cascade=sim.new(pars=dict(cascade=1)), prep=sim.new(interventions=preps), both=sim.new(pars=dict(cascade=1), interventions=preps))

if __name__ == '__main__':
    msim = ss.parallel(scenarios, n_runs=5, workers=1)
    msim.plot()

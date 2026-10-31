"""
The EpiModel introduction (docs/models/epimodel/sis-network), in Starsim: an SIS epidemic over
partnerships that form and dissolve, among 500 people
"""
import starsim as ss

S, I = ss.states('S I')
sis = ss.Disease(
    infection = ss.Transition(S, I, rate=ss.prob(0.4) * I), # A 40% chance for each act
    recovery  = ss.Transition(I, S, rate=ss.prob(0.05)),
    init_n    = dict(I=10),
)
partners = ss.DegreeNet(n_contacts=0.7, concurrency=0.22, max_contacts=3, dur=50, acts=ss.freqperday(2)) # 175 partnerships among 500, 110 with two or more, none with four, lasting 50 steps, with two acts a step
sim = ss.Sim(sis, networks=partners, n_agents=500, stop=500)

if __name__ == '__main__':
    msim = sim.run(n_runs=10)
    msim.plot()

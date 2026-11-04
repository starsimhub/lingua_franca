"""
SIARX with contact tracing, from epipack's tutorial on networks: on a random network, well mixed, and deterministic

People infected become symptomatic (I) or not (A), and those without symptoms are half as
infectious. Symptomatic people are quarantined (X) at a rate, and each time someone is, each of
their contacts who is symptomatic is quarantined too, with a chance of 25%. Tracing needs to know
who someone's contacts are, so the deterministic model has the tutorial's own mean-field form of it
instead, a flow from I to X by contact with I.
"""
import starsim as ss
import starsim.library as ssl

S, I, A, R, X = ss.states('S I A R X')
beta = 2*(1/5 + 1/5)/50 # Per contact per day: R = 2 with 50 contacts
flows = dict(
    infection  = ss.Transition(S, [I, A], rate=beta*(I + 0.5*A), p=[0.7, 0.3]),
    recovery   = (I + A) >> R @ (1/5),
    quarantine = I >> X @ (1/5),
)
siarx = ss.Disease(**flows, init_n=dict(I=100), name='siarx')
tracing = ss.Delivery(move=I >> X, who=siarx.quarantine, trace='contacts', coverage=0.25)
sim = ss.Sim(siarx, networks=ssl.StaticNet(n_contacts=50, name='contacts'), interventions=tracing, n_agents=10_000, unit='day', stop=40, dt=0.1, verbose=0)
well_mixed = sim.new(networks=ss.RandomNet(n_contacts=50, name='contacts'))
mean_field = ss.Disease(**flows, traced=I >> X @ 0.25/5*I*I/(S + I + A + R + X), init_n=dict(I=100), name='siarx') # The whole flow, kappa*p*k0*I*I/N
deterministic = ss.Sim(mean_field, networks=ss.MixingPool(n_contacts=50), total_pop=10_000, unit='day', stop=100, solver='ode', verbose=0)

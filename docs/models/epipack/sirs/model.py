"""
The SIRS of epipack's README, run three ways: as ODEs, by Gillespie's method, and on a random network

epipack writes the well-mixed model with the processes of an EpiModel, and the network model with
the different processes of a StochasticEpiModel, at a rate per link of R0*rho/k0. Here there is one
disease, with a rate per contact, and only the route and the solver change: 50 contacts a day at
0.05 each is the README's 2.5 per day, and on the network each person has 50 contacts on average.
"""
import starsim as ss
import starsim.library as ssl

S, I, R = ss.states('S I R')
sirs = ss.Disease(infection=S >> I @ 0.05*I, recovery=I >> R @ 1, waning=R >> S @ (1/14), init_prev=0.01, name='sirs')
sim = ss.Sim(sirs, networks=ss.MixingPool(n_contacts=50), total_pop=1000, unit='day', stop=40, dt=1, solver='ode', verbose=0)
gillespie = sim.new(solver='gillespie')
network = sim.new(networks=ssl.StaticNet(n_contacts=50), solver='abm', total_pop=10_000, n_agents=10_000, dt=0.025)

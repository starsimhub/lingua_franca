"""
The camdl SIR (docs/models/camdl/sir), in Starsim: a closed epidemic, observed through weekly reported cases
"""
import starsim as ss

beta  = ss.par(ss.perday(0.4),  bounds=[0.05, 1.0], prior=ss.lognormal(log_mean=-1.0, log_std=0.5), doc='transmission rate')
gamma = ss.par(ss.perday(0.15), bounds=[0.01, 0.5], prior=ss.lognormal(log_mean=-2.0, log_std=0.5), doc='recovery rate')
rho   = ss.par(0.6, doc='reporting fraction')
k     = ss.par(10,  doc='dispersion of the reported counts')

S, I, R = ss.states(3)
infection = S >> I @ beta * I
recovery  = I >> R @ gamma
cases     = ss.outcome(rho * infection, likelihood=ss.nbinom(n=k)) # Compared with weekly data as its total over each week

sir = ss.Disease(infection, recovery, cases, init_n=dict(I=10))
sim = ss.Sim(sir, total_pop=10_000, unit='day', stop=ss.weeks(12))

if __name__ == '__main__':
    sim.run()
    sim.plot()

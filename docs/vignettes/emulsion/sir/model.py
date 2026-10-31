"""
The EMULSION SIR (docs/models/emulsion/sir), in Starsim: one model, run as compartments and as individuals
"""
import starsim as ss

S, I, R = ss.states('S I R')
sir = ss.Disease(
    infection = S >> I @ ss.perday(0.5) * I,
    recovery  = I >> R @ ss.perday(0.1),
    init_n    = dict(I=1),
    name      = 'sir',
)
compartment = ss.Sim(sir, total_pop=100, stop=ss.days(100), solver='binomial', substeps=1) # Whole days, as EMULSION takes them
ibm         = ss.Sim(sir, total_pop=100, stop=ss.days(100), solver='abm')

if __name__ == '__main__':
    msim = ss.parallel(compartment=compartment, ibm=ibm, n_runs=20, n_cpus=2)
    msim.plot()

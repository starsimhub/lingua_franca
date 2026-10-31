"""
The epydemix tutorial on population data (docs/models/epydemix/sir_kenya), in Starsim: an SIR in
Kenya's population, with contact matrices between five age groups
"""
import numpy as np
import sciris as sc
import starsim as ss

# Starsim bundles populations and contact matrices, but this uses the numbers epydemix downloaded, so that the two models are the same
data = sc.loadjson(sc.thispath(__file__)/'../../../models/epydemix/sir_kenya/reference/population.json')
matrix = sum(np.array(layer) for layer in data['contacts'].values()) # School, work, home, and community

S, I, R = ss.states('S I R')
sir = ss.Disease(
    infection = ss.Transition(S, I, rate=0.04 * I),
    recovery  = ss.Transition(I, R, rate=0.1),
    init_n    = dict(I=10),
)
sir.stratify(age=[0, 5, 20, 50, 65], split=data['Nk'])
sim = ss.Sim(sir, networks=ss.contacts(matrix), total_pop=sum(data['Nk']), start='2019-12-01', stop='2020-04-02', # To the end of 1 April
             solver='binomial', substeps=1, use_aging=False) # Whole days, as epydemix takes them

if __name__ == '__main__':
    msim = sim.run(n_runs=100)
    msim.plot()

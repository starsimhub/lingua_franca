"""
The odin stochastic SIR with arrays (docs/models/odin/stochastic_sir_arrays), in Starsim: an SIR in
1,001 people, 100 times over. As in the original's array, the 100 replicates are held in one run, as
places that nobody moves between
"""
import starsim as ss

n_groups = 100 # The length of the arrays in the original
S, I, R = ss.states(3)
sir = ss.Disease(
    infection = S >> I @ 0.2 * I,
    recovery  = I >> R @ 0.1,
    init_n    = dict(I=ss.by(run=[1]*n_groups)),
)
sir.stratify(run=ss.levels(list(map(str, range(n_groups))), kind='space')) # kind='space', or else the groups would mix as one population
sim = ss.Sim(sir, total_pop=1001*n_groups, stop=100, solver=ss.solvers.binomial(substeps=1)) # One draw a step, as in the original

if __name__ == '__main__':
    sim.run()
    sim.plot()

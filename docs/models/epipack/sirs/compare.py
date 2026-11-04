"""
Compare the Starsim version with the reference results of the original

    python compare.py

The ODE is compared day by day. The stochastic runs are compared by their mean on each day,
over as many runs as the reference has: 1,000 by Gillespie's method and 100 on the network.
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim, gillespie, network

ref = {k:np.array(v[1]) for k,v in tools.read_results(here).items()}
tolerances = dict(ode=1e-4, gillespie=1e-2, network=3e-2) # As shares of the population; the stochastic ones allow for the error of a mean of many runs


def check(name, which, res, pop, tol, every=1):
    """ The largest difference from the original over all days and states, of one run or the mean of many """
    values = lambda c: res[c].values if res[c].values.ndim == 1 else res[c].values.mean(axis=0)
    diff = max(np.abs(values(c)[::every] - ref[f'{which}_{c}']).max() for c in 'SIR')/pop
    print(f'{name}: largest difference {diff:.2e} of the population, tolerance {tol:.0e}')
    assert diff < tol


if __name__ == '__main__':
    check('ODE', 'ode', sim.run().results.sirs, 1000, tolerances['ode'])
    check('Gillespie, mean of 1,000 runs', 'gillespie', ss.parallel(gillespie, n_runs=1000, n_cpus=2).results.sirs, 1000, tolerances['gillespie'])
    check('On the network, mean of 100 runs', 'network', ss.parallel(network, n_runs=100, n_cpus=2).results.sirs, 10_000, tolerances['network'], every=40)

"""
Compare the Starsim version with the reference results of the original

    python compare.py

The deterministic model is compared day by day, to day 100. The stochastic runs, on the network
and well mixed, are compared by their mean on each day to day 40, over 100 runs, as many as the
reference has.
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim, well_mixed, deterministic

ref = {k:np.array(v[1]) for k,v in tools.read_results(here).items()}
tolerances = dict(deterministic=1e-4, network=2e-2, well_mixed=2e-2) # As shares of the population; the stochastic ones allow for the error of a mean of 100 runs, and for the step
n_runs = 100


def check(name, which, res, tol, every=1):
    """ The largest difference from the original over all days and states, of one run or the mean of many """
    values = lambda c: res[c].values if res[c].values.ndim == 1 else res[c].values.mean(axis=0)
    diff = max(np.abs(values(c)[::every] - ref[f'{which}_{c}']).max() for c in 'SIARX')/10_000
    print(f'{name}: largest difference {diff:.2e} of the population, tolerance {tol:.0e}')
    assert diff < tol


if __name__ == '__main__':
    check('Deterministic', 'ode', deterministic.run().results.siarx, tolerances['deterministic'])
    every = 10 # Steps of a tenth of a day
    check('On the network, mean of 100 runs', 'network', ss.parallel(sim, n_runs=n_runs, n_cpus=2).results.siarx, tolerances['network'], every=every)
    check('Well mixed, mean of 100 runs', 'well_mixed', ss.parallel(well_mixed, n_runs=n_runs, n_cpus=2).results.siarx, tolerances['well_mixed'], every=every)

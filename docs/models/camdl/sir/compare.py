"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np
import pandas as pd
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim

example = here
ref = tools.read_results(example)
weeks = np.arange(7, 85, 7)
tolerance = dict(ode=0.001, stochastic_I=0.03, stochastic_cases=0.04) # Of the largest value; the means of 200 runs hold chance


def weekly(cases):
    """ Reported cases totaled over the week that ends at each reporting time (a flow at index k is the number during the step from time k) """
    return np.array([cases[..., week - 7:week].sum(axis=-1) for week in weeks]).T


def worst(ours, key):
    """ The largest difference from the reference, as a share of its largest value (a stock at index k is the number at time k, in both) """
    ours, theirs = np.asarray(ours), np.array(ref[key][1])
    return np.abs(np.asarray(ours) - theirs).max()/theirs.max()


if __name__ == '__main__':
    # The ODE; cases are totaled over the week that ends at each reporting time
    ode = sim.new(verbose=0).run()
    res = ode.results.sir
    rows = [(f'ode_{key}', worst(res[key], f'ode_{key}')) for key in 'SIR']
    rows.append(('ode_cases', worst(weekly(res.cases.values), 'ode_cases')))

    # The stochastic solver, as the mean of many runs
    msim = ss.parallel(sim.new(verbose=0, solver=ss.solvers.binomial(substeps=1)), n_runs=200, workers=2) # Whole days, as camdl's chain binomial takes them
    res = msim.results.sir
    rows.append(('stochastic_I', worst(res.I.values.mean(axis=0), 'stochastic_I')))
    rows.append(('stochastic_cases', worst(weekly(res.cases.values).mean(axis=0), 'stochastic_cases')))

    for key,diff in rows:
        print(f'{key:18s} largest difference {diff:6.2%}')
        assert diff < tolerance.get(key, tolerance['ode']), f'{key} differs by {diff:.2%}'

    # The posterior (sampled by NUTS) of beta, gamma, and k, from weekly cases drawn around the original's ODE cases
    rng = np.random.default_rng(1)
    mean = np.array(ref['ode_cases'][1])
    data = pd.DataFrame(dict(time=weeks - 7, cases=rng.negative_binomial(10, 10/(10 + mean)))) # Each week dated by its first day, as a flow's data is read
    fit = sim.new(verbose=0, pars=dict(k=ss.par(3, bounds=[0.1, 100]))).fit(data=data, method='nuts', verbose=False)
    print('posterior from cases drawn with beta=0.4, gamma=0.15, k=10 (median and 95% interval):', ', '.join(f'{row.par}={row.median:.3g} ({row.lower:.3g} to {row.upper:.3g})' for row in fit.table.itertuples()))
    for row in fit.table.itertuples():
        if row.par != 'k': # Twelve counts say little about k, whose interval only just reaches the value used
            assert row.lower < dict(beta=0.4, gamma=0.15)[row.par] < row.upper, f'{row.par} is outside its 95% interval'

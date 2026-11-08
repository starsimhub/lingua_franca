"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim

example = here
ref = tools.read_results(example)

if __name__ == '__main__':
    res = sim.new(verbose=0).run().results.sir
    worst = 0
    for state in 'SIR':
        for age in ['young', 'old']:
            for location in ['urban', 'rural']:
                ours = res[state].select(age=age, location=location).values # A stock at index k is the number at time k, in both
                theirs = np.array(ref[f'{state}_{age}_{location}'][1])
                worst = max(worst, np.abs(ours - theirs).max())
    print(f'largest difference in any compartment: {worst:.3g} people (of 1,000)')
    assert worst < 0.08, f'The compartments differ by {worst:.3g} people'

    ode = res.R[-1] # At the stop
    for solver in ['binomial', 'abm']:
        run = sim.new(verbose=0, solver=solver, **(dict(n_agents=1000) if solver == 'abm' else {}))
        runs = ss.parallel(run, n_runs=100, workers=1).results.sir
        recovered = runs.R.values.mean(axis=0)[-1]
        print(f'{solver}: recovered at the end {recovered:.0f} (ODE {ode:.0f})')
        assert abs(recovered/ode - 1) < 0.01, f'{solver} gives {recovered:.0f} recovered, the ODE {ode:.0f}'

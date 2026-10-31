"""
Run the original tutorial script with a fixed seed, and print what `run.py` needs as JSON.

    python simulate.py

Run with the Python of the epydemix environment (see `_envs/epydemix`); `run.py` does this.
The original script sets no seed, so `run_simulations` is wrapped here to pass one.
"""
import os
import sys
import json
import time
import contextlib
import matplotlib
matplotlib.use('Agg') # The original script plots
import numpy as np
import epydemix

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

seed = 1
original = os.path.join(here, 'original', 'sir_kenya.py')

# Give run_simulations a seed unless the caller sets one; before the first call, time one run as a first run (with a seed, so this does not change the results)
run_simulations = epydemix.EpiModel.run_simulations
timing = dict()
def seeded(self, *args, rng=seed, **kwargs):
    if 'first' not in timing:
        start = time.perf_counter()
        run_simulations(self, *args, rng=rng, **dict(kwargs, Nsim=1))
        timing['first'] = time.perf_counter() - start
    return run_simulations(self, *args, rng=rng, **kwargs)
epydemix.EpiModel.run_simulations = seeded


def summarize(stacked, prefix=''):
    """ The mean and the 5% and 95% quantiles over the runs, at each time, for each series """
    rows = []
    for key,vals in stacked.items():
        mean, low, high = vals.mean(axis=0), np.quantile(vals, 0.05, axis=0), np.quantile(vals, 0.95, axis=0)
        rows += [dict(time=t + 1, series=prefix + key, value=float(mean[t]), low=float(low[t]), high=float(high[t])) for t in range(vals.shape[1])]
    return rows


if __name__ == '__main__':
    # Run the original; what it prints goes to stderr, so that stdout is only the JSON
    scope = dict(__name__='__main__')
    with contextlib.redirect_stdout(sys.stderr):
        exec(compile(open(original).read(), original, 'exec'), scope)
    model, results = scope['model'], scope['results']

    # The initial state, which is the same in every run and is not part of the output: time 0 is the start of the first day
    pop = model.population
    initial = model.create_default_initial_conditions(percentage_in_agents=10/pop.Nk.sum())
    rows = []
    for comp,vals in initial.items():
        for name,val in zip([*pop.Nk_names, 'total'], [*vals, vals.sum()]):
            rows.append(dict(time=0, series=f'{comp}_{name}', value=float(val), low=float(val), high=float(val)))

    # Compartments (the state at the end of each day) and transitions (the number moving during each day)
    rows += summarize(results.get_stacked_compartments()) + summarize(results.get_stacked_transitions(), prefix='new_')

    # Time one simulation, and the 100 of the original
    kw = dict(start_date='2019-12-01', end_date='2020-04-01', percentage_in_agents=10/model.population.Nk.sum())
    rerun = tools.time_run(lambda: model.run_simulations(Nsim=1, **kw))
    many = tools.time_run(lambda: model.run_simulations(Nsim=100, **kw))

    info = dict(
        n_runs  = len(results.trajectories),
        start   = str(results.dates[0])[:10],
        end     = str(results.dates[-1])[:10],
        n_steps = len(results.dates),
        seed    = seed,
        groups  = list(pop.Nk_names),
        Nk      = [int(n) for n in pop.Nk],
        initial = {key:[int(v) for v in val] for key,val in initial.items()},
        contacts = {key:np.round(val, 6).tolist() for key,val in pop.contact_matrices.items()},
    )
    print(json.dumps(dict(rows=rows, first=timing['first'], rerun=rerun, many=many, info=info)))

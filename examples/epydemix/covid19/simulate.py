"""
Run the original tutorial script, with three changes that let it run here, and print what `run.py` needs as JSON.

    python simulate.py

Run with the Python of the epydemix environment (see `_envs/epydemix`); `run.py` does this.
The three changes, made from outside without editing the original:

- The epidemiological and mobility data are read from `original/data` (copies from the epydemix
  v1.4.0 repository) rather than from the `main` branch on GitHub.
- The population "United_States_Massachusetts" is loaded as "United_States__Massachusetts", its name
  in the epydemix-data release (v1.2.0) that epydemix 1.4.0 uses; under the old name it fails.
- The ABC-SMC calibration is seeded and made smaller: 200 particles for 5 generations, instead of
  1,000 for 10, which take over an hour.
"""
import os
import sys
import json
import time
import contextlib
import matplotlib
matplotlib.use('Agg') # The original script plots
import numpy as np
import pandas as pd
import epydemix.population
import epydemix.calibration

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

seed = 1
n_particles = 200
n_generations = 5
n_runs = 200 # Runs of the model at fixed parameter values
original = os.path.join(here, 'original', 'covid19.py')

# Read the tutorial's own data from the local copies
read_csv = pd.read_csv
def local_csv(path, *args, **kwargs):
    if isinstance(path, str) and 'massachusetts_data' in path:
        path = os.path.join(here, 'original', 'data', os.path.basename(path))
    return read_csv(path, *args, **kwargs)
pd.read_csv = local_csv

# The population's name in epydemix-data v1.2.0
load_population = epydemix.population.load_epydemix_population
def renamed(name, *args, **kwargs):
    return load_population(name.replace('United_States_Massachusetts', 'United_States__Massachusetts'), *args, **kwargs)
epydemix.population.load_epydemix_population = renamed

# Seed the sampler, and shrink the calibration
sampler_init = epydemix.calibration.ABCSampler.__init__
def seeded_init(self, *args, rng=seed, **kwargs):
    return sampler_init(self, *args, rng=rng, **kwargs)
epydemix.calibration.ABCSampler.__init__ = seeded_init
calibrate = epydemix.calibration.ABCSampler.calibrate
timing = dict()
def smaller(self, strategy='smc', **kwargs):
    kwargs.update(num_particles=n_particles, num_generations=n_generations)
    state = np.random.get_state() # A first run, timed at the values of the rerun below, which leaves the random numbers of the calibration as they were
    start = time.perf_counter()
    self.simulation_function(dict(self.parameters, R0=2.22, Delta=20, I0=4260, seasonality_min=0.8))
    timing['first'] = time.perf_counter() - start
    np.random.set_state(state)
    start = time.perf_counter()
    out = calibrate(self, strategy=strategy, **kwargs)
    timing['calibration'] = time.perf_counter() - start
    return out
epydemix.calibration.ABCSampler.calibrate = smaller


def summarize(vals, series, times):
    """ The mean and the 5% and 95% quantiles over the runs (rows), at each time """
    mean, low, high = vals.mean(axis=0), np.quantile(vals, 0.05, axis=0), np.quantile(vals, 0.95, axis=0)
    return [dict(time=t, series=series, value=float(mean[i]), low=float(low[i]), high=float(high[i])) for i,t in enumerate(times)]


def days(dates, start):
    """ Days from the start of the first day to the end of each date """
    return [int((pd.Timestamp(d) - pd.Timestamp(start)).days) + 1 for d in dates]


if __name__ == '__main__':
    # Run the original; what it prints goes to stderr, so that stdout is only the JSON
    np.random.seed(seed) # The initial conditions are drawn with NumPy's global generator
    scope = dict(__name__='__main__')
    with contextlib.redirect_stdout(sys.stderr):
        exec(compile(open(original).read(), original, 'exec'), scope)
    model, results, reopening = scope['model'], scope['results'], scope['results_reopening']
    epi_data = scope['epi_data']
    start = str(epi_data.date.values[0])[:10]
    cal_dates = scope['epi_data_calibration'].date.values
    all_dates = epi_data.date.values

    # The data, the posterior, the fit, and the projections, as the original produces them
    rows = [dict(time=t, series='data_deaths', value=float(v)) for t,v in zip(days(all_dates, start), epi_data.data)]
    posterior = results.get_posterior_distribution()
    fixed = dict()
    for par in ['R0', 'Delta', 'I0', 'seasonality_min']:
        vals = posterior[par].values.astype(float)
        rows.append(dict(time=0, series=f'posterior_{par}', value=float(vals.mean()), low=float(np.quantile(vals, 0.05)), high=float(np.quantile(vals, 0.95))))
        fixed[par] = float(np.median(vals))
    rows += summarize(results.get_calibration_trajectories()['data'], 'abc_fit_deaths', days(cal_dates, start))
    for scenario,res in reopening.items():
        rows += summarize(res.get_projection_trajectories()['data'], f'abc_{scenario}_deaths', days(all_dates, start))

    # Runs at fixed values (the posterior medians, rounded), the same for every run, for each scenario
    fixed = dict(R0=round(fixed['R0'], 2), Delta=int(round(fixed['Delta'])), I0=int(round(fixed['I0'])), seasonality_min=round(fixed['seasonality_min'], 2))
    groups = list(model.population.Nk_names)
    projection = scope['contact_reductions_projection']
    wrapper = scope['simulate_wrapper']
    def run_fixed(r, n=1, rng=None):
        model.add_parameter('r', r)
        pars = dict(epimodel=model, start_date=all_dates[0], end_date=all_dates[-1], resample_frequency='D', rng=rng, **fixed)
        return [scope['simulate'](**dict(pars, initial_conditions_dict=scope['custom_initial_conditions'](model, fixed['I0']),
                                         beta=scope['compute_beta'](scope['C'], model.parameters['mu'], fixed['R0'])*scope['apply_seasonality'](all_dates[0], all_dates[-1], fixed['seasonality_min'])))
                for i in range(n)]
    rng = np.random.default_rng(seed)
    np.random.seed(seed)
    for scenario in ['persistence', 'moderate', 'high']:
        trajs = run_fixed(projection[f'r_{scenario}'].values, n=n_runs, rng=rng)
        dates = trajs[0].dates
        weekly = lambda key: np.array([pd.Series(tr.transitions[key], index=dates).resample('W').sum().values for tr in trajs])
        weeks = pd.Series(0, index=dates).resample('W').sum().index
        rows += summarize(weekly('D3_to_D4_total'), f'fixed_{scenario}_deaths', days(weeks, start))
        if scenario == 'persistence':
            for group in groups:
                rows += summarize(weekly(f'D3_to_D4_{group}'), f'fixed_{scenario}_deaths_{group}', days(weeks, start))
            for comp in ['S', 'E', 'I', 'R', 'D4']:
                vals = np.array([tr.compartments[f'{comp}_total'] for tr in trajs])
                rows += summarize(vals, f'fixed_{scenario}_{comp}', days(dates, start))
            vals = np.array([sum(tr.compartments[f'D{d}_total'] for d in range(4)) for tr in trajs])
            rows += summarize(vals, f'fixed_{scenario}_D', days(dates, start))

    # Time one evaluation of the wrapper, as the calibration runs it, over the calibration period
    model.add_parameter('r', scope['contact_reductions']['r'].values)
    pars = dict(scope['parameters'], **fixed)
    pars.update(end_date=cal_dates[-1])
    rerun = tools.time_run(lambda: wrapper(dict(pars)))

    pop = model.population
    info = dict(
        start    = start,
        seed     = seed,
        abc      = dict(particles=n_particles, generations=n_generations, seconds=timing['calibration'], tutorial=dict(particles=1000, generations=10)),
        fixed    = fixed,
        n_runs   = n_runs,
        mu       = model.parameters['mu'],
        eps      = model.parameters['eps'],
        IFR      = [float(v) for v in np.ravel(model.parameters['IFR'])],
        groups   = groups,
        Nk       = [int(n) for n in pop.Nk],
        contacts = {key:np.round(val, 6).tolist() for key,val in pop.contact_matrices.items()},
        r        = {scenario:[round(float(v), 6) for v in projection[f'r_{scenario}'].values] for scenario in ['persistence', 'moderate', 'high']},
        dates    = [str(d)[:10] for d in projection.date.values],
        data     = dict(date=[str(d)[:10] for d in all_dates], deaths=[int(v) for v in epi_data.data]),
    )
    print(json.dumps(dict(rows=rows, first=timing['first'], rerun=rerun, info=info)))

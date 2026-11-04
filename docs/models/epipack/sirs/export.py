"""
Run the original in this process and print its results and timing as JSON

This is the part of `run.py` that runs in epipack's environment (see `_envs/epipack`).
The README's SIRS is integrated, simulated by Gillespie's method many times, and run on a
random network many times, each on a network of its own, as `original/sirs_network.py`
makes it. Times are sampled each day, as the state at that moment.

    python export.py n_gillespie n_network
"""
import os
import sys
import json
import time
import random
import runpy
import warnings
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
warnings.simplefilter('ignore') # epipack warns that the optional SamplableSet is missing, and about an escape in a docstring
import tools
from epipack import EpiModel

days = np.arange(41) # Each day, 0 to 40
seed = 1


def build():
    """ The model as `original/sirs.py` builds it """
    S, I, R = list("SIR")
    N = 1000
    return EpiModel([S,I,R],N).set_processes([(S, I, 2.5, I, I), (I, 1, R), (R, 1/14, S)]).set_initial_conditions({S:N-10, I:10})


def on_days(t, result):
    """ The state on each day of a stochastic run, which `simulate()` gives at each event """
    i = np.searchsorted(t, days, side='right') - 1
    return {c:np.asarray(result[c])[i] for c in 'SIR'}


def summary(runs, name):
    """ The mean and 5% to 95% range over runs of each state on each day """
    rows = []
    for c in 'SIR':
        vals = np.array([run[c] for run in runs], dtype=float)
        low, high = np.quantile(vals, [0.05, 0.95], axis=0)
        rows += [dict(time=d, series=f'{name}_{c}', value=v, low=lo, high=hi) for d,v,lo,hi in zip(days, vals.mean(0), low, high)]
    return rows


if __name__ == '__main__':
    n_gillespie, n_network = [int(arg) for arg in sys.argv[1:3]]
    np.random.seed(seed)
    random.seed(seed)
    t = np.linspace(0,40,1000) # As the original integrates it

    # The ODE, timed as the original runs it
    start = time.perf_counter()
    model = build()
    model.integrate(t)
    first = time.perf_counter() - start
    rerun = tools.repeat(lambda: model.integrate(t))
    ode = model.integrate(days)
    rows = [dict(time=d, series=f'ode_{c}', value=v) for c in 'SIR' for d,v in zip(days, ode[c])]

    # Gillespie: simulate() leaves the model at its end, so each run starts it again
    def gillespie():
        model.set_initial_conditions({'S':990, 'I':10})
        return model.simulate(40)
    gillespie_rerun = tools.repeat(gillespie)
    rows += summary([on_days(*gillespie()) for _ in range(n_gillespie)], 'gillespie')

    # On a network: the script itself, each run on a network of its own
    start = time.perf_counter()
    scope = runpy.run_path(os.path.join(here, 'original', 'sirs_network.py'))
    network_first = time.perf_counter() - start
    net = scope['SIRS']
    def network():
        net.set_random_initial_conditions({'S': 10_000 - 100, 'I': 100})
        return net.simulate(40)
    network_rerun = tools.repeat(network, budget=10, least=5)
    runs = [on_days(scope['t_s'], scope['result_s'])]
    for _ in range(n_network - 1):
        scope = runpy.run_path(os.path.join(here, 'original', 'sirs_network.py'))
        runs.append(on_days(scope['t_s'], scope['result_s']))
    rows += summary(runs, 'network')

    times = dict(first=first, rerun=rerun, gillespie_rerun=gillespie_rerun, network_first=network_first, network_rerun=network_rerun)
    print(json.dumps(dict(rows=[{k:float(v) if k != 'series' else v for k,v in row.items()} for row in rows], **times)))

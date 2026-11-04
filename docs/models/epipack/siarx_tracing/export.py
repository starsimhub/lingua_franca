"""
Run the original in this process and print its results and timing as JSON

This is the part of `run.py` that runs in epipack's environment (see `_envs/epipack`).
`original/siarx.py` is run as it is, many times, each time on a network of its own. Each
run simulates the model on the network, then well mixed, then integrates the deterministic
model; `simulate()` and `integrate()` are wrapped here to keep what each returns and how
long it took. The stochastic runs are sampled each day, as the state at that moment.

    python export.py n_runs
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
import networkx # Imported before the timing, as epipack is
import epipack

script = os.path.join(here, 'original', 'siarx.py')
comps = 'SIARX'
seed = 1
calls = [] # Each call of simulate() or integrate(): its result, how long it took, and when it ended


def record(cls, name):
    """ Wrap a method to keep each call's result and time """
    original = getattr(cls, name)
    def wrapped(self, *args, **kwargs):
        start = time.perf_counter()
        out = original(self, *args, **kwargs)
        end = time.perf_counter()
        calls.append(dict(model=self, out=out, seconds=end - start, end=end))
        return out
    setattr(cls, name, wrapped)


def on_days(t, result, days):
    """ The state on each day of a stochastic run, which `simulate()` gives at each event """
    i = np.searchsorted(t, days, side='right') - 1
    return {c:np.asarray(result[c])[i] for c in comps}


def summary(runs, name, days):
    """ The mean and 5% to 95% range over runs of each state on each day """
    rows = []
    for c in comps:
        vals = np.array([run[c] for run in runs], dtype=float)
        low, high = np.quantile(vals, [0.05, 0.95], axis=0)
        rows += [dict(time=int(d), series=f'{name}_{c}', value=float(v), low=float(lo), high=float(hi)) for d,v,lo,hi in zip(days, vals.mean(0), low, high)]
    return rows


if __name__ == '__main__':
    n_runs = int(sys.argv[1])
    np.random.seed(seed)
    random.seed(seed)
    record(epipack.StochasticEpiModel, 'simulate')
    record(epipack.EpiModel, 'integrate')
    days = np.arange(41)

    network, well_mixed, first, network_runs, mixed_runs = [], [], None, [], []
    for i in range(n_runs):
        calls.clear()
        start = time.perf_counter()
        runpy.run_path(script)
        net, mixed, ode = calls
        if first is None: # Making the network and the model, and simulating it on the network, in a fresh process
            first = net['end'] - start
        network_runs.append(net['seconds'])
        mixed_runs.append(mixed['seconds'])
        network.append(on_days(*net['out'], days))
        well_mixed.append(on_days(*mixed['out'], days))

    # The deterministic model: the same each time
    model, t = ode['model'], np.linspace(0,100,1000)
    ode_rerun = tools.repeat(lambda: model.integrate(t))
    res = model.integrate(np.arange(101))
    rows = [dict(time=d, series=f'ode_{c}', value=float(v)) for c in comps for d,v in enumerate(res[c])]
    rows += summary(network, 'network', days) + summary(well_mixed, 'well_mixed', days)
    times = dict(first=first, rerun=min(network_runs), well_mixed_rerun=min(mixed_runs), ode_first=ode['seconds'], ode_rerun=ode_rerun)
    print(json.dumps(dict(rows=rows, **times)))

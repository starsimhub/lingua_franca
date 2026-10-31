"""
Run the original EpiModel script and write its reference results and timing.

    python run.py

Needs the epimodel environment (see `_envs/epimodel`). Takes about four minutes.
"""
import os
import csv
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

model = os.path.join(here, 'original', 'intro_sis.R')
driver = os.path.join(here, 'reference.R') # Runs the original, then repeats its simulation n_runs times
series = ['s.num', 'i.num', 'si.flow', 'is.flow', 'edges', 'meandeg', 'concurrent', 'duration', 'prop.diss']
n_runs = tools.runs(100) # The model is stochastic
seed = 1
n_cores = 2 # The results do not depend on this, as long as it is at least 2


def simulate():
    """ Run the model, returning its simulations (one row per simulation and time step) and the times in seconds of its steps """
    with tempfile.TemporaryDirectory() as tmp:
        tools.run(['Rscript', driver, model, tmp, str(n_runs), str(seed), str(n_cores)], 'epimodel', cwd=tmp)
        with open(os.path.join(tmp, 'runs.csv')) as f:
            runs = [{key:float(val) for key,val in row.items() if val != ''} for row in csv.DictReader(f)]
        with open(os.path.join(tmp, 'seconds.csv')) as f:
            seconds = {row['what']:float(row['seconds']) for row in csv.DictReader(f)}
    return runs, seconds


def summarize(rows, key, time='time'):
    """ The mean and the 5% and 95% quantiles over the runs, at each time """
    rows = [row for row in rows if key in row] # The flows have no value at the first time step
    times = sorted({row[time] for row in rows})
    out = []
    for t in times:
        vals = sorted(row[key] for row in rows if row[time] == t)
        n = len(vals)
        out.append(dict(time=t, value=sum(vals)/n, low=vals[int(0.05*(n - 1))], high=vals[int(0.95*(n - 1))]))
    return out


if __name__ == '__main__':
    runs, seconds = simulate()
    assert len({row['sim'] for row in runs}) == n_runs

    rows = []
    for key in series:
        rows += [dict(series=key, **row) for row in summarize(runs, key)]

    tools.write_results(here, rows)
    first, rerun, netest = seconds['netsim_first'], seconds['netsim_rerun'], seconds['netest']
    what = f'netsim with nsims = 1 (500 steps, 500 nodes), inside one R session. The first run is estimating the network (netest, {netest:.2f} s) and one netsim, after the original script has run; the rerun is the best of 5 netsim calls with the same fitted network. Neither includes starting R or loading EpiModel'
    tools.write_timing(here, rerun, what, first=netest + first)
    print(f'Wrote {len(rows)} rows; a first run takes {netest + first:.3f} s, of which {netest:.3f} s is estimating the network, and a rerun {rerun:.3f} s')

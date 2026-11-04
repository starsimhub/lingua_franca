"""
Run the original epiworldR vignette and write its reference results and timing.

    python run.py

Needs the epiworld environment (see `_envs/epiworld`). Takes about half a minute.
"""
import os
import csv
import sys
import tempfile
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

model = os.path.join(here, 'original', 'run-multiple.R')
driver = os.path.join(here, 'reference.R') # Runs the original, then repeats its simulation n_runs times
states = ['Susceptible', 'Exposed', 'Infected', 'Recovered']
n_runs = tools.runs(1000) # The vignette makes 50; the outbreak takes off in about 60% of runs, so more are needed for its distribution
seed = 1


def simulate():
    """ Run the model, returning the counts of each state in each simulation and day (as an array of runs by states by days), and the times in seconds """
    with tempfile.TemporaryDirectory() as tmp:
        tools.run(['Rscript', driver, model, tmp, str(n_runs), str(seed)], 'epiworld', cwd=tmp)
        with open(os.path.join(tmp, 'runs.csv')) as f:
            rows = list(csv.DictReader(f))
        with open(os.path.join(tmp, 'seconds.csv')) as f:
            seconds = {row['what']:float(row['seconds']) for row in csv.DictReader(f)}
    days = 1 + max(int(row['date']) for row in rows)
    counts = np.zeros((n_runs, len(states), days))
    for row in rows:
        counts[int(row['sim_num']) - 1, states.index(row['state']), int(row['date'])] = float(row['counts'])
    return counts, seconds


def summarize(series, values):
    """ The mean and the 5% and 95% quantiles over the runs (the rows of values), at each day """
    low, high = np.quantile(values, [0.05, 0.95], axis=0, method='inverted_cdf')
    return [dict(time=t, series=series, value=values[:,t].mean(), low=low[t], high=high[t]) for t in range(values.shape[1])]


if __name__ == '__main__':
    counts, seconds = simulate()
    rows = []
    for i,state in enumerate(states):
        rows += summarize(state, counts[:,i])
    rows += summarize('extinct', (counts[:,1] + counts[:,2] == 0).astype(float)) # The share of runs in which nobody is exposed or infectious
    tools.write_results(here, rows)
    what = 'run() of the vignette\'s ModelSEIRCONN for 50 days (10,000 agents), with its progress bar off, inside one R session. The first run is building the model with the vignette\'s own statement and running it once, after the vignette has run; the rerun is the best of repeated run() calls. Neither includes starting R or loading epiworldR'
    tools.write_timing(here, seconds['rerun'], what, first=seconds['first'])
    print(f'Wrote {len(rows)} rows from {n_runs} runs; a first run takes {seconds["first"]:.4f} s, and a rerun {seconds["rerun"]:.4f} s')

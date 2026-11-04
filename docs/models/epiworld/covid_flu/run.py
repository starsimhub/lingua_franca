"""
Run the original epiworldR vignette and write its reference results and timing.

    python run.py

Needs the epiworld environment (see `_envs/epiworld`). Takes about two minutes.
"""
import os
import csv
import sys
import tempfile
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

model = os.path.join(here, 'original', 'advanced-modeling.R')
driver = os.path.join(here, 'reference.R') # Runs the original, then repeats its last simulation n_runs times
series = ['Susceptible', 'Infected', 'Recovered', 'Infected COVID-19', 'Infected Flu']
n_runs = tools.runs(1000) # The vignette makes one run
seed = 1


def simulate():
    """ Run the model, returning the counts of each series in each simulation and day (as an array of runs by series by days, with the vignette's own run first), and the times in seconds """
    with tempfile.TemporaryDirectory() as tmp:
        tools.run(['Rscript', driver, model, tmp, str(n_runs), str(seed)], 'epiworld', cwd=tmp)
        with open(os.path.join(tmp, 'runs.csv')) as f:
            rows = list(csv.DictReader(f))
        with open(os.path.join(tmp, 'seconds.csv')) as f:
            seconds = {row['what']:float(row['seconds']) for row in csv.DictReader(f)}
    days = 1 + max(int(row['date']) for row in rows)
    counts = np.zeros((n_runs + 1, len(series), days))
    for row in rows:
        counts[int(row['sim']), series.index(row['series']), int(row['date'])] = float(row['counts'])
    return counts, seconds


def summarize(name, values):
    """ The mean and the 5% and 95% quantiles over the runs (the rows of values), at each day """
    low, high = np.quantile(values, [0.05, 0.95], axis=0, method='inverted_cdf')
    return [dict(time=t, series=name, value=values[:,t].mean(), low=low[t], high=high[t]) for t in range(values.shape[1])]


if __name__ == '__main__':
    counts, seconds = simulate()
    vignette, runs = counts[0], counts[1:]
    rows = []
    for i,name in enumerate(series):
        rows += summarize(name, runs[:,i])
    for i,name in enumerate(series[:3]): # The vignette's own run, with seed 1912
        rows += [dict(time=t, series=f'vignette {name}', value=v) for t,v in enumerate(vignette[i])]
    tools.write_results(here, rows)
    what = 'run() of the vignette\'s final model for 50 days (50,000 agents, two viruses, a vaccine, and two events), with its progress bar off, inside one R session. The first run is building the model with the vignette\'s own statements and running it once, after the vignette has run; the rerun is the best of repeated run() calls, each after setting the contact rate back to 4. Neither includes starting R or loading epiworldR'
    tools.write_timing(here, seconds['rerun'], what, first=seconds['first'])
    print(f'Wrote {len(rows)} rows from {n_runs} runs; a first run takes {seconds["first"]:.4f} s, and a rerun {seconds["rerun"]:.4f} s')

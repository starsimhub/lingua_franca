"""
Run the original LASER model and write its reference results and timing.

    python run.py

Needs the LASER environment (see `_envs/laser`), and the England and Wales data
from the laser-generic source in `_envs/laser/src/laser-generic-1.1.0/data`.
"""
import os
import sys
import json
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

n_runs = tools.runs(50)
center, radius, scale, years = 'Norwich', 100, 1, 10 # The places within 100 km of Norwich, at their real size, for 10 years


def summarize(runs, key, step=1):
    """ The mean and the 5% and 95% quantiles over the runs, at each time (or each place) """
    vals = np.array([run[key] for run in runs])
    n = len(runs)
    ordered = np.sort(vals, axis=0)
    low, high = ordered[int(0.05*(n - 1))], ordered[int(0.95*(n - 1))]
    return [dict(time=t*step, series=key, value=v, low=lo, high=hi) for t,(v,lo,hi) in enumerate(zip(vals.mean(axis=0), low, high))]


def weekly(vals):
    """ Totals over each whole week """
    vals = np.array(vals)
    weeks = len(vals)//7
    return vals[:weeks*7].reshape(weeks, 7).sum(axis=1).tolist()


if __name__ == '__main__':
    cmd = ['python', os.path.join(here, 'simulate.py'), str(n_runs), center, str(radius), str(scale), str(years)]
    out = json.loads(tools.run(cmd, 'laser'))
    runs = out['runs']
    for run in runs:
        for key in list(run):
            if key.startswith(('new_infections', 'births', 'deaths')):
                run[key] = weekly(run[key])
        run['total_infections'] = [sum(run['new_infections'])]
        run['yearly_infections'] = np.array(run['new_infections'][:52*years]).reshape(years, 52).sum(axis=1).tolist() # Years of 52 weeks
    rows = []
    for key in runs[0]:
        rows += summarize(runs, key, step=7 if key.startswith(('new_infections', 'births', 'deaths')) else 1)

    tools.write_results(here, rows)
    what = f"Building and running the model once in Python ({sum(out['pop']):,} agents in {len(out['pop'])} places, {years*365:,} daily steps, on all cores), with the data loaded and the cells before the run already run. first is the first run, which includes compiling; rerun is the best of {n_runs - 1} more in the same process, each of which builds the model again, since a LASER model cannot be run twice"
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f"Wrote {len(rows)} rows; first run {out['first']:.3f} s, rerun {out['rerun']:.3f} s")

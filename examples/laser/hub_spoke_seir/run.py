"""
Run the original LASER model and write its reference results and timing.

    python run.py

Needs the LASER environment (see `_envs/laser`).
"""
import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

n_runs = 20


def summarize(runs, key):
    """ The mean and the 5% and 95% quantiles over the runs, at each time """
    out = []
    for t in range(len(runs[0][key])):
        vals = sorted(run[key][t] for run in runs)
        n = len(vals)
        out.append(dict(time=t, series=key, value=sum(vals)/n, low=vals[int(0.05*(n - 1))], high=vals[int(0.95*(n - 1))]))
    return out


if __name__ == '__main__':
    out = json.loads(tools.run(['python', os.path.join(here, 'simulate.py'), str(n_runs)], 'laser'))
    runs = out['runs']
    rows = []
    for key in runs[0]:
        rows += summarize(runs, key)

    tools.write_results(here, rows)
    what = f"Building and running the model once in Python (1,750,000 agents, 365 steps, on all cores), not counting starting Python or importing. first is the first run, which includes compiling; rerun is the best of {n_runs - 1} more in the same process, each of which builds the model again, since a LASER model cannot be run twice"
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f"Wrote {len(rows)} rows; first run {out['first']:.3f} s, rerun {out['rerun']:.3f} s")

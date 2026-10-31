"""
Run the original EMULSION quickstart model and write its reference results and timing.

    python run.py

Needs the emulsion environment (see `_envs/emulsion`).
"""
import os
import csv
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

model = os.path.join(here, 'original', 'quickstart.yaml')
keys = ['J', 'A', 'NG', 'G', 'M', 'S', 'E', 'I', 'R', 'Q', 'total_population', 'nb_total_abortions'] # The count in each state of the three state machines, and two of the extra outputs
n_runs = tools.runs(200) # The model is stochastic
seed = 1


def simulate(runs):
    """ Run the model a number of times, returning its outputs (one row per run and time step) """
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ['emulsion', 'run', model, '--runs', str(runs), '--seed', str(seed), '--quiet', '--output-dir', tmp]
        tools.run(cmd, 'emulsion', cwd=tmp)
        with open(os.path.join(tmp, 'counts.csv')) as f:
            return [{key:float(row[key]) for key in ['simu_id', 'step', *keys]} for row in csv.DictReader(f)]


def summarize(rows, key, time='step'):
    """ The mean and the 5% and 95% quantiles over the runs, at each time """
    times = sorted({row[time] for row in rows})
    out = []
    for t in times:
        vals = sorted(row[key] for row in rows if row[time] == t)
        n = len(vals)
        out.append(dict(time=t, value=sum(vals)/n, low=vals[int(0.05*(n - 1))], high=vals[int(0.95*(n - 1))]))
    return out


if __name__ == '__main__':
    counts = simulate(n_runs)
    assert len({row['simu_id'] for row in counts}) == n_runs
    rows = []
    for key in keys:
        rows += [dict(series=key, **row) for row in summarize(counts, key)]
    tools.write_results(here, rows)
    rerun = tools.time_run(lambda: simulate(1))
    what = 'emulsion run quickstart.yaml --runs 1, as one command each time: EMULSION runs a model as a whole command, so first and rerun are the same command, and both include starting Python and reading the model (about 0.7 s)'
    tools.write_timing(here, rerun, what)
    print(f'Wrote {len(rows)} rows; a first run takes {tools.first_run["seconds"]:.3f} s, and a rerun {rerun:.3f} s')

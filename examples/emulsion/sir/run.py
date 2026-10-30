"""
Run the original EMULSION models and write their reference results and timing.

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

variants = dict(compartment='compart_SIR.yaml', ibm='IBM_SIR.yaml', hybrid='hybrid_SIR.yaml') # The name in the results, and the model file
states = ['S', 'I', 'R']
n_runs = 200 # Every variant is stochastic
seed = 1


def simulate(file, runs):
    """ Run a model a number of times, returning its counts (one row per run and time step) """
    model = os.path.join(here, 'original', file)
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ['emulsion', 'run', model, '--runs', str(runs), '--seed', str(seed), '--quiet', '--output-dir', tmp]
        tools.run(cmd, 'emulsion', cwd=tmp)
        with open(os.path.join(tmp, 'counts.csv')) as f:
            return [{key:float(row[key]) for key in ['simu_id', 'step', *states]} for row in csv.DictReader(f)]


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
    rows = []
    for name,file in variants.items():
        counts = simulate(file, n_runs)
        assert len({row['simu_id'] for row in counts}) == n_runs
        for key in states:
            rows += [dict(series=f'{name}_{key}', **row) for row in summarize(counts, key)]

    tools.write_results(here, rows)
    rerun = tools.time_run(lambda: simulate(variants['compartment'], 1))
    what = 'emulsion run compart_SIR.yaml --runs 1, as one command each time: EMULSION runs a model as a whole command, so first and rerun are the same command, and both include starting Python and reading the model (about 0.7 s; EMULSION itself reports about 0.06 s for the simulation)'
    tools.write_timing(here, rerun, what)
    print(f'Wrote {len(rows)} rows; a first compartmental run takes {tools.first_run["seconds"]:.3f} s, and a rerun {rerun:.3f} s')

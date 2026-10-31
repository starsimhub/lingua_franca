"""
Run the original camdl model and write its reference results and timing.

    python run.py

Needs the camdl environment (see `_envs/camdl`).
"""
import os
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

model = os.path.join(here, 'original', 'stratified.camdl')
pars = dict(beta=0.04, gamma=0.1, move=0.01)
cells = [f'I_{age}_{patch}' for age in ['child', 'adult', 'elder'] for patch in ['north', 'south']]
states = 'SEIR'
n_runs = tools.runs(200) # For the chain-binomial backend


def simulate(*args):
    """ Run the model, returning the trajectory as a list of rows, with the totals of each compartment """
    with tempfile.TemporaryDirectory() as tmp:
        traj = os.path.join(tmp, 'traj.tsv')
        cmd = ['camdl', 'simulate', model, '--no-progress', '--output-dir', os.path.join(tmp, 'store'), '-o', traj, *args]
        for key,val in pars.items():
            cmd += ['--param', f'{key}={val}']
        tools.run(cmd, 'camdl')
        with open(traj) as f:
            lines = [line.rstrip('\n').split('\t') for line in f if not line.startswith('#')]
    rows = [dict(zip(lines[0], map(float, line))) for line in lines[1:]]
    for row in rows:
        for state in states:
            row[state] = sum(val for key,val in row.items() if key.startswith(f'{state}_') and not key.startswith('flow'))
    return rows


def summarize(rows, key):
    """ The mean and the 5% and 95% quantiles over the runs, at each time """
    out = []
    for t in sorted({row['t'] for row in rows}):
        vals = sorted(row[key] for row in rows if row['t'] == t)
        n = len(vals)
        out.append(dict(time=t, value=sum(vals)/n, low=vals[int(0.05*(n - 1))], high=vals[int(0.95*(n - 1))]))
    return out


if __name__ == '__main__':
    rows = []
    for label,enable in [('novax', []), ('vax', ['--enable', 'vaccinate'])]:
        traj = simulate('--backend', 'ode', *enable)
        runs = simulate('--replicates', str(n_runs), *enable)
        for key in cells + list(states):
            rows += [dict(time=row['t'], series=f'ode_{label}_{key}', value=row[key]) for row in traj]
            rows += [dict(series=f'stochastic_{label}_{key}', **row) for row in summarize(runs, key)]

    tools.write_results(here, rows)
    with tempfile.TemporaryDirectory() as tmp: # An empty cache, so that the first run compiles the model
        os.environ['XDG_CACHE_HOME'] = tmp
        rerun = tools.time_run(lambda: simulate('--backend', 'ode'))
    what = 'camdl simulate --backend ode, as one command each time: camdl has no way to rerun a model in the same process. First: with an empty cache, so it compiles the model. Rerun: the same command again, with the model cached'
    tools.write_timing(here, rerun, what)
    print(f'Wrote {len(rows)} rows; a first ODE run takes {tools.first_run["seconds"]:.3f} s, and a rerun {rerun:.3f} s')

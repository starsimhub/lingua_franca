"""
Run the original and write its reference results and timing

    python run.py

Needs epymorph's environment (see `_envs/epymorph`), but no network connection: the inputs that the
notebook fetches with ADRIOs are replaced by the data that epymorph bundles for this example. The model
is stochastic, so the reference is the mean and the 5% to 95% range of 20 runs.
"""
import os
import sys
import json
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

n_runs = tools.runs(20)


def summarize(key, values):
    """ The mean and the 5% and 95% quantiles over the runs (rows), at each time (columns) """
    lo, hi = np.quantile(values, [0.05, 0.95], axis=0)
    return [dict(time=t, series=key, value=v, low=l, high=h) for t,(v,l,h) in enumerate(zip(values.mean(axis=0), lo, hi))]


if __name__ == '__main__':
    out = json.loads(tools.run(['python', os.path.join(here, 'export.py'), str(n_runs)], 'epymorph', cwd=here).splitlines()[-1])
    comps = np.array([run['comps'] for run in out['runs']], dtype=float) # Runs, days, states, compartments
    infections = np.array([run['infections'] for run in out['runs']], dtype=float)
    rows = []
    for c,name in enumerate('SIR'):
        rows += summarize(name, comps[:, :, :, c].sum(axis=2))
    rows += summarize('new_infections', infections.sum(axis=2))
    for j,state in enumerate(out['names']):
        rows += summarize(f'I_{state}', comps[:, :, j, 1])
        rows += summarize(f'R_{state}', comps[:, :, j, 2])
        rows += summarize(f'new_infections_{state}', infections[:, :, j])
    tools.write_results(here, rows)
    what = f'first: building the RUME (with the ADRIOs replaced by the data bundled for the example) and running it once, in a process with epymorph already imported. rerun: the same RUME run again, by a new BasicSimulator, as the notebook runs it. Both are a single run of 150 days in 6 states, with two tau steps a day; the reference results are {n_runs} more runs'
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f'Wrote {len(rows)} rows; a first run takes {out["first"]:.3f} s, a rerun {out["rerun"]:.3f} s')

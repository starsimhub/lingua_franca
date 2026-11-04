"""
Run the original and write its reference results and timing

    python run.py

Needs epymorph's environment (see `_envs/epymorph`), but no network connection: the two inputs that the
vignette fetches with ADRIOs are kept in `original/arizona_counties.csv` (see `fetch.py`). The model is
stochastic, so the reference is the mean and the 5% to 95% range of 40 runs, of those in which the epidemic
takes off (with 5 people infectious at the start, about one run in twenty dies out at once).
"""
import os
import sys
import json
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

n_runs = tools.runs(40)
took_off = 1000 # The most people infectious at once, at least, in a run in which the epidemic takes off


def summarize(key, values):
    """ The mean and the 5% and 95% quantiles over the runs (rows), at each time (columns) """
    lo, hi = np.quantile(values, [0.05, 0.95], axis=0)
    return [dict(time=t, series=key, value=v, low=l, high=h) for t,(v,l,h) in enumerate(zip(values.mean(axis=0), lo, hi))]


if __name__ == '__main__':
    out = json.loads(tools.run(['python', os.path.join(here, 'export.py'), str(n_runs)], 'epymorph', cwd=here).splitlines()[-1])
    comps = np.array([run['comps'] for run in out['runs']], dtype=float) # Runs, days, counties, compartments
    infections = np.array([run['infections'] for run in out['runs']], dtype=float)
    keep = comps[:, :, :, 1].sum(axis=2).max(axis=1) >= took_off
    comps, infections = comps[keep], infections[keep]
    rows = []
    for c,name in enumerate('SIR'):
        rows += summarize(name, comps[:, :, :, c].sum(axis=2))
    rows += summarize('new_infections', infections.sum(axis=2))
    for j,county in enumerate(out['names']):
        rows += summarize(f'I_{county.split(",")[0]}', comps[:, :, j, 1])
    tools.write_results(here, rows)
    what = f'first: building the RUME (with the ADRIOs replaced by the values they return) and running it once, in a process with epymorph already imported. rerun: the same RUME run again, by a new BasicSimulator, as the vignette runs it. Both are a single run of 190 days in 15 counties, with two tau steps a day; the reference results are {n_runs} more runs, of which the {keep.sum()} in which the epidemic took off are summarized'
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f'The epidemic took off in {keep.sum()} of {n_runs} runs')
    print(f'Wrote {len(rows)} rows; a first run takes {out["first"]:.3f} s, a rerun {out["rerun"]:.3f} s')

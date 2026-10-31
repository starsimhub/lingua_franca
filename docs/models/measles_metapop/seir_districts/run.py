"""
Run the original model and write its reference results and timing.

    python run.py
"""
import os
import sys
import numpy as np
import pandas as pd

here = os.path.dirname(os.path.abspath(__file__))
examples = os.path.dirname(os.path.dirname(here))
sys.path.insert(0, examples)
sys.path.insert(0, os.path.join(here, 'original'))
import tools
import measles_metapop as mm

n_runs = tools.runs(50) # The model is stochastic


def summarize(frames, prefix):
    """ The mean and the 5% and 95% quantiles over the runs, for each column of a time series """
    stack = np.stack([df.values for df in frames])
    rows = []
    for j,col in enumerate(frames[0].columns):
        vals = np.sort(stack[:, :, j], axis=0)
        n = len(frames)
        for i,t in enumerate(frames[0].index):
            rows.append(dict(time=str(t), series=f'{prefix}_{col}', value=vals[:, i].mean(), low=vals[int(0.05*(n - 1)), i], high=vals[int(0.95*(n - 1)), i]))
    return rows


if __name__ == '__main__':
    districts = mm.load_districts()
    sims = [mm.Sim(districts, seed=seed).run() for seed in range(n_runs)]
    regions = districts['region']
    rows = []
    rows += summarize([sim.results.states.resample('MS').first() for sim in sims], 'national') # S, E, I, R at the start of each month
    rows += summarize([pd.DataFrame(dict(infections=sim.monthly('infections').sum(axis=1), cases=sim.monthly('cases').sum(axis=1))) for sim in sims], 'monthly')
    by_region = [sim.results.infections.loc['2020':].T.groupby(regions).sum().sum(axis=1).to_frame('infections_2020_2025').T for sim in sims] # Infections from 2020 on, in each region
    rows += summarize(by_region, 'region') # Series region_<name>, at the single time "infections_2020_2025"
    tools.write_results(here, rows)
    rerun = tools.time_run(lambda: mm.Sim(districts).run())
    what = 'mm.Sim(districts).run(), with the data already loaded. The model has no separate rerun, so first and rerun are the same: each builds the sim and runs it'
    tools.write_timing(here, rerun, what)
    print(f'Wrote {len(rows)} rows; a first run takes {tools.first_run["seconds"]:.2f} s, and a rerun {rerun:.2f} s')

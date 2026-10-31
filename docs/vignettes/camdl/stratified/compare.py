"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))
sys.path.insert(0, os.path.join(root, 'docs', 'models'))
import tools
from model import sim, vaccinate

ref = tools.read_results(os.path.join(root, 'docs', 'models', 'camdl', 'stratified'))
ages = dict(child='0-4', adult='5-49', elder='50+')
tolerance = dict(ode=0.005, stochastic=0.08) # Of the largest value in each cell; camdl writes whole numbers, which matters in the smallest cells; for the stochastic runs, this is the epidemic rising sooner in the south (see the README)
peak_tolerance = 0.02 # Of the peak, in each cell of the stochastic runs


def worst(res, prefix):
    """ The largest difference in the infectious of any cell (the mean, for many runs), as a share of the largest value there, and the same for the peak """
    out, peaks = {}, {}
    for age,label in ages.items():
        for patch in ['north', 'south']:
            ours = res.I.select(age=label, patch=patch).values
            ours = ours.mean(axis=0) if ours.ndim == 2 else ours # A stock at index k is the number at time k, in both
            theirs = np.array(ref[f'{prefix}_I_{age}_{patch}'][1])
            out[f'{age}_{patch}'] = np.abs(ours - theirs).max()/theirs.max()
            peaks[f'{age}_{patch}'] = abs(ours.max()/theirs.max() - 1)
    return out, peaks


if __name__ == '__main__':
    for label,interventions in [('novax', None), ('vax', vaccinate)]:
        ode = sim.new(verbose=0, interventions=interventions).run().results.seir
        msim = ss.parallel(sim.new(verbose=0, interventions=interventions, solver='binomial', substeps=1), n_runs=200, n_cpus=2) # Whole days, as camdl's chain binomial takes them
        for kind,res in [('ode', ode), ('stochastic', msim.results.seir)]:
            diffs, peaks = worst(res, f'{kind}_{label}')
            print(f'{kind:10s} {label:5s} largest difference in I by cell: ' + ', '.join(f'{k} {v:.2%}' for k,v in diffs.items()))
            print(f'{"":16s} difference in the peak by cell:   ' + ', '.join(f'{k} {v:.2%}' for k,v in peaks.items()))
            assert max(diffs.values()) < tolerance[kind], f'{kind} {label}: the infectious differ by {max(diffs.values()):.2%}'
            assert max(peaks.values()) < peak_tolerance or kind == 'ode', f'{kind} {label}: the peaks differ by {max(peaks.values()):.2%}'
        for key in 'SER': # With vaccination, the move on day 20 shows in Starsim's counts a day later (see the README), so those two rows are left out
            ours, theirs = ode[key].values, np.array(ref[f'ode_{label}_{key}'][1])
            skip = np.arange(len(ours)) != 20
            print(f'ode        {label:5s} {key} largest difference from the original {np.abs(ours - theirs)[skip].max()/theirs.max():.2%}')

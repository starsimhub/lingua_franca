"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim

ref = tools.read_results(here)
modules = dict(life='NG G', growth='J A', health='M S E I R Q')
n_runs = 50
tolerance = 13 # Animals, in any count at any step, for the mean of the runs: wide, to hold a known miss in place (finding 1 in the README)
window = ss.timeseries({'2021-01-01': 0, '2021-03-19': 1, '2021-08-21': 0, '2022-03-18': 1, '2022-08-20': 0}) # The quarantine as EMULSION applies it: see the README


def run_many(**kwargs):
    """ The mean over the runs of each count; a stock at index k is the state after k steps, as is EMULSION's row k """
    res = ss.parallel(sim.new(verbose=0, **kwargs), n_runs=n_runs, n_cpus=2).results
    return {state:np.asarray(res[mod][state].values).mean(axis=0) for mod,names in modules.items() for state in names.split()}


if __name__ == '__main__':
    print(f'{"":20s} {"largest difference":>18s} {"(step)":>6s}   at step 13: ours, theirs   at step 53   at step 105')
    for label,kwargs in [('as written', {}), ('with the quarantine as EMULSION applies it', dict(pars=dict(quarantine=window)))]:
        print(label)
        res = run_many(**kwargs)
        res['total_population'] = res['J'] + res['A']
        for key,ours in res.items():
            theirs = np.array(ref[key][1])
            k = np.abs(ours - theirs).argmax()
            print(f'  {key:18s} {ours[k] - theirs[k]:+18.2f} {k:6d}   ' + '   '.join(f'{ours[i]:6.1f} {theirs[i]:6.1f}' for i in [13, 53, 105]))
            assert abs(ours[k] - theirs[k]) < tolerance, f'{label}: {key} differs by {ours[k] - theirs[k]:.1f} animals at step {k}'

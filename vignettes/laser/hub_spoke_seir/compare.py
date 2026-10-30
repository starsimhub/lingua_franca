"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
sys.path.insert(0, os.path.join(root, 'examples'))
import tools
from model import sim

ref = tools.read_results(os.path.join(root, 'examples', 'laser', 'hub_spoke_seir'))
places = dict(central_city='Central City', town_1='Town 1', interim_1a='Interim 1A', town_3='Town 3')


n_runs = 6 # Each agent stands for ten people, so the 100 at the start are 10 agents, and the day of the peak in one run depends a good deal on chance
tol_recovered, tol_peak, tol_day = 0.02, 0.15, 10 # Share recovered and height of the peak in each place, and the day of the peak


def report(label, results):
    """ Print the means over some runs against the reference, in total and in each place, and raise if they are over the tolerances """
    print(label)
    for key,name in dict(total=None, **places).items():
        # A stock at index k is the number on day k, in both, from day 0 (the start) to day 365 (the stop)
        ours = np.array([res.I.values if name is None else res.I.select(patch=name).values for res in results])
        theirs = np.array(ref['I' if name is None else f'I_{key}'][1])
        done = np.mean([res.R.values[-1] if name is None else res.R.select(patch=name).values[-1] for res in results])
        ref_done = ref['R' if name is None else f'R_{key}'][1][-1]
        peak, day = ours.max(axis=1).mean(), ours.argmax(axis=1).mean()
        print(f'  {key:13s} peak infectious {peak:9,.0f} on day {day:5.1f} (original {theirs.max():9,.0f} on day {theirs.argmax():3d}); recovered at the end {done:9,.0f} ({ref_done:9,.0f})')
        assert abs(done/ref_done - 1) <= tol_recovered, f'{key}: {done:,.0f} recovered, against {ref_done:,.0f}'
        assert abs(peak/theirs.max() - 1) <= tol_peak, f'{key}: a peak of {peak:,.0f}, against {theirs.max():,.0f}'
        assert abs(day - theirs.argmax()) <= tol_day, f'{key}: a peak on day {day:.1f}, against day {theirs.argmax()}'
    return


if __name__ == '__main__':
    abm = [sim.new(rand_seed=seed, verbose=0).run().results.seir for seed in range(n_runs)]
    report(f'As agents ({sim.pars.n_agents:,} agents, the mean of {n_runs} runs; the original, the mean of 20):', abm)
    ode = sim.new(n_agents=None, solver='ode', verbose=0).run().results.seir
    report('As an ODE, with the durations as Erlang stages:', [ode])

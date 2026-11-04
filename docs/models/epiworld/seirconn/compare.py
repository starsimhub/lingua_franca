"""
Compare the Starsim version with the reference results of the original

    python compare.py

Both are stochastic, so this compares the runs of each: the mean number in each state every ten days,
the share of runs in which the infection has died out, and the spread of the number recovered at the
end. Raises an error if a mean, or the 95% quantile of the recovered at the end, differs by more than
three standard errors, or the share died out by more than 0.05. It also runs the model as agents,
which the README discusses, without checking it.
"""
import os
import csv
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim

ref = tools.read_results(here)
with open(os.path.join(here, 'reference', 'results.csv')) as f:
    their_R = [row for row in csv.DictReader(f) if row['series'] == 'Recovered'][-1] # Day 50, with the 5% and 95% quantiles
n_runs = 1000 # As in the reference
states = dict(S='Susceptible', E='Exposed', I='Infected', R='Recovered')
days = [10, 20, 30, 40, 50]


def runs(sim, n=n_runs):
    """ The count of each state in each run, as an array of runs by days, by state """
    res = ss.parallel(sim.new(verbose=0), n_runs=n, parallel=False).results.seir
    return {k:np.asarray(res[k].values) for k in states}


def summary(counts):
    """ The mean and its standard error at each of the days, by state; the share of runs died out; and the 5% and 95% quantiles of the recovered at the end """
    out = {k:(v[:,days].mean(axis=0), v[:,days].std(axis=0)/np.sqrt(len(v))) for k,v in counts.items()}
    out['extinct'] = np.mean(counts['E'][:,-1] + counts['I'][:,-1] == 0)
    final = counts['R'][:,-1]
    out['R_quantiles'] = np.quantile(final, [0.05, 0.95], method='inverted_cdf') # As in run.py
    rng = np.random.default_rng(1)
    out['q95_se'] = np.std([np.quantile(rng.choice(final, len(final)), 0.95) for i in range(200)]) # By the bootstrap
    return out


if __name__ == '__main__':
    ours = summary(runs(sim))
    theirs = {k:np.array(ref[v][1])[days] for k,v in states.items()}
    print(f'Mean of {n_runs} runs on days {days}, Starsim (standard error) and the original')
    for k in states:
        mean, se = ours[k]
        print(f'  {k}: ' + ', '.join(f'{m:.1f} ({s:.1f}) and {t:.1f}' for m,s,t in zip(mean, se, theirs[k])))
        z = np.abs(mean - theirs[k])/(np.sqrt(2)*np.maximum(se, 1e-9)) # Both have about the same standard error
        assert np.all(z < 3), f'The mean of {k} differs by more than three standard errors (by {z.max():.1f})'
    their_extinct = ref['extinct'][1][-1]
    print(f'Runs in which the infection died out by day 50: {ours["extinct"]:.3f}, and the original {their_extinct:.3f}')
    assert abs(ours['extinct'] - their_extinct) < 0.05
    q = ours['R_quantiles']
    print(f'Recovered on day 50, 5% and 95% quantiles: {q[0]:.0f} and {q[1]:.0f}, and the original {float(their_R["low"]):.0f} and {float(their_R["high"]):.0f}')
    z = abs(q[1] - float(their_R['high']))/(np.sqrt(2)*ours['q95_se'])
    print(f'  The 95% quantiles differ by {z:.1f} standard errors (each about {ours["q95_se"]:.0f}, by the bootstrap)')
    assert z < 3, 'The 95% quantile of the recovered at the end differs by more than three standard errors'

    abm = summary(runs(sim.new(solver='abm', n_agents=10_000), n=200)) # As agents, taking each step in order (see the README)
    print(f'As agents (200 runs): recovered on day 50 {abm["R"][0][-1]:.1f} ({abm["R"][1][-1]:.1f}), died out by day 50 {abm["extinct"]:.3f}')

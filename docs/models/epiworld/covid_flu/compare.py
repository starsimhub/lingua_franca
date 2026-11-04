"""
Compare the Starsim version with the reference results of the original

    python compare.py

Both are stochastic, so this compares the means of 1,000 runs of each. While few are infected (to
day 5) the two use the same chance of infection, and every mean must agree within three standard
errors. Later the original's chance of infection is lower when someone meets several infectious
people (see the README): about 5% lower at the peak. So there the tolerance is 7% of the peak number
infected (10% for the flu, which infects far fewer), a day for when it peaks, and 5% of the number
recovered at the end. It also runs the model as agents,
which the README discusses, without checking it.
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim

ref = {k:np.array(v[1]) for k,v in tools.read_results(here).items()}
n_runs = 1000 # As in the reference
early = slice(1, 6) # Days 1 to 5
series = {'S':'Susceptible', 'I':'Infected', 'R':'Recovered', 'covid':'Infected COVID-19', 'flu':'Infected Flu'}


def runs(sim, n=n_runs):
    """ The count in each series in each run, as an array of runs by days, by series """
    res = ss.parallel(sim.new(verbose=0), n_runs=n, parallel=False).results.sir
    out = {k:np.asarray(res[k].values) for k in 'SIR'}
    for strain in ['covid', 'flu']:
        out[strain] = np.asarray(res.I.select(strain=strain).values)
    return out


def peak(x):
    """ The day and size of the peak of a mean """
    return np.argmax(x), x.max()


if __name__ == '__main__':
    ours = runs(sim)
    mean = {k:v.mean(axis=0) for k,v in ours.items()}
    se = {k:v.std(axis=0)/np.sqrt(n_runs) for k,v in ours.items()}
    print(f'Mean of {n_runs} runs, Starsim and the original')
    for k,name in series.items():
        print(f'  {k:5s} days 1 to 5: ' + ', '.join(f'{a:.1f} and {b:.1f}' for a,b in zip(mean[k][early], ref[name][early])))
        z = np.abs(mean[k] - ref[name])[early]/(np.sqrt(2)*np.maximum(se[k][early], 1e-9))
        assert np.all(z < 3), f'{k}: a mean in days 1 to 5 differs by more than three standard errors (by {z.max():.1f})'
    for k,tol in dict(I=0.07, covid=0.07, flu=0.1).items():
        (d1, p1), (d2, p2) = peak(mean[k]), peak(ref[series[k]])
        print(f'  Peak of {k}: {p1:.0f} on day {d1}, and {p2:.0f} on day {d2} ({p1/p2 - 1:+.1%})')
        assert abs(p1/p2 - 1) < tol and abs(d1 - d2) <= 1, f'The peak of {k} differs by more than {tol:.0%} or a day'
    r1, r2 = mean['R'][-1], ref['Recovered'][-1]
    print(f'  Recovered on day 50: {r1:.0f}, and {r2:.0f} ({r1/r2 - 1:+.1%}); the vignette\'s own run {ref["vignette Recovered"][-1]:.0f}')
    assert abs(r1/r2 - 1) < 0.05, 'The number recovered at the end differs by more than 5%'

    abm = runs(sim.new(solver='abm', n_agents=50_000), n=20) # As agents, taking each step in order (see the README)
    (d, p), r = peak(abm['I'].mean(axis=0)), abm['R'][:,-1].mean()
    print(f'As agents (20 runs): peak infected {p:.0f} on day {d}, recovered on day 50 {r:.0f}')

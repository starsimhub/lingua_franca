"""
Compare the Starsim version with the reference results of the original

    python compare.py [n_runs]

Each agent-based run takes about 15 s, and the default is two runs.
"""
import os
import csv
import sys
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
sys.path.insert(0, os.path.join(root, 'examples'))
import tools
from model import sim, names, pop, years

example = os.path.join(root, 'examples', 'laser', 'england_wales')
ref = tools.read_results(example)
ranges = {row['series']:(float(row['low']), float(row['high'])) for row in csv.DictReader(open(os.path.join(example, 'reference', 'results.csv'))) if row['series'] == 'total_infections'}
places = ['Norwich', 'Cambridge', 'Colchester', 'Kings.Lynn', 'Ely', 'Thetford', 'Southwold']
n_days = years*365


def weekly(vals):
    """ Weekly totals of a flow, whose value at index k is the number during the step ending on day k (so the first, at the start, is 0) """
    weeks = n_days//7
    return np.asarray(vals)[1:weeks*7 + 1].reshape(weeks, 7).sum(axis=1)


def run(seed):
    """ One run of the Starsim version, as the same series as the reference """
    s = sim.new(rand_seed=seed, verbose=0).run()
    res = s.results.measles
    out = dict(new_infections=weekly(res.infection.values), births=weekly(res.births.values), deaths=weekly(res.deaths.values))
    for place in places:
        out[f'new_infections_{place.lower()}'] = weekly(res.infection.select(patch=place).values)
    for key in 'SEIR': # A stock at index k is the number on day k, in both (day 0 is the start)
        out[key] = res[key].values
    by_place = np.array([weekly(res.infection.select(patch=name).values) for name in names])
    out['prop_zero'] = (by_place[:, by_place.shape[1]//2:] == 0).mean(axis=1)
    return out


def yearly(weeks):
    """ Infections in each year, from weekly totals (52 weeks to a year) """
    weeks = np.asarray(weeks)
    return weeks[:52*(len(weeks)//52)].reshape(-1, 52).sum(axis=1)


if __name__ == '__main__':
    n_runs = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    runs = [run(seed) for seed in range(n_runs)]
    mean = {key:np.mean([r[key] for r in runs], axis=0) for key in runs[0]}
    print(f'\n{len(names)} places, {pop.sum():,.0f} people, {years} years; Starsim: mean of {n_runs} runs; original: mean of 50 runs')
    N = lambda d: sum(np.array(d[k]) for k in 'SEIR') # noqa: E731
    theirs_N = N({k:ref[k][1] for k in 'SEIR'})
    print(f'  people at the end: {N(mean)[n_days]:,.0f} (original {theirs_N[n_days]:,.0f}); births {mean["births"].sum():,.0f} ({np.sum(ref["births"][1]):,.0f}); deaths {mean["deaths"].sum():,.0f} ({np.sum(ref["deaths"][1]):,.0f}), in the first year {mean["deaths"][:52].sum():,.0f} ({np.sum(ref["deaths"][1][:52]):,.0f})')
    totals = [r['new_infections'].sum() for r in runs]
    low, high = ranges['total_infections']
    print(f'  infections in each run: {", ".join(f"{t:,.0f}" for t in totals)} (original: mean {ref["total_infections"][1][0]:,.0f}, 5% to 95% {low:,.0f} to {high:,.0f})')
    for key in ['new_infections'] + [f'new_infections_{p.lower()}' for p in places]:
        ours, theirs = mean[key], np.array(ref[key][1])
        print(f'  {key[15:] or "total":11s} infections {ours.sum():9,.0f} (original {theirs.sum():9,.0f}, {ours.sum()/theirs.sum() - 1:+.1%}); by year {np.round(yearly(ours)).astype(int)} ({np.round(yearly(theirs)).astype(int)})')
    ours, theirs = mean['prop_zero'], np.array(ref['prop_zero'][1])
    print(f'  share of weeks with no infections in the second half, by place: mean {ours.mean():.3f} (original {theirs.mean():.3f}), correlation {np.corrcoef(ours, theirs)[0, 1]:.3f}, largest difference {np.abs(ours - theirs).max():.3f}')
    print(f'  weekly infections, correlation of the means: {np.corrcoef(mean["new_infections"], ref["new_infections"][1])[0, 1]:.3f}; susceptible at the end {mean["S"][n_days]:,.0f} ({ref["S"][1][n_days]:,.0f})')

    # The tolerances, for two or three runs. Deaths in the first year are not among them: see finding 1 in the README
    total = mean['new_infections'].sum()/np.sum(ref['new_infections'][1])
    assert abs(total - 1) <= 0.05, f'Infections differ by {total - 1:+.1%}'
    for p in places:
        key = f'new_infections_{p.lower()}'
        ratio = mean[key].sum()/np.sum(ref[key][1])
        assert abs(ratio - 1) <= 0.2, f'Infections in {p} differ by {ratio - 1:+.1%}'
    end = N(mean)[n_days]/theirs_N[n_days]
    assert abs(end - 1) <= 0.02, f'People at the end differ by {end - 1:+.1%}'
    assert abs(ours.mean() - theirs.mean()) <= 0.03 and np.corrcoef(ours, theirs)[0, 1] >= 0.95, 'The share of weeks with no infections differs'

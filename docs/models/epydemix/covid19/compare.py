"""
Compare the Starsim version with the reference results of the original

    python compare.py

Takes a few minutes. Raises an error if, at fixed values, weekly deaths differ by more than 3% of their
peak, or deaths by 2 August by more than 3%; or if a parameter's posterior mean falls outside the
original's 5% to 95% range, or projected peak weekly deaths differ by more than 10%. Everything is
run one at a time rather than across processes.
"""
import os
import sys
import numpy as np
import sciris as sc
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
import model
from model import data

example = here
ref = tools.read_results(example)
table = sc.dataframe.read_csv(os.path.join(example, 'reference', 'results.csv')).set_index('series')
n_runs = data['n_runs']
scenarios = ['persistence', 'moderate', 'high']
end = '2020-08-03' # To the end of 2 August, the original's last day
tol_fixed = 0.03 # Of the peak of weekly deaths, and of total deaths
tol_proj = 0.1 # Of the peak of projected weekly deaths: each side's posterior is a small sample


def weekly(daily, times):
    """ Sum daily flows over the weeks ending at each reference time (days to the end of the week's last day; a flow at index k is the number during the step from day k) """
    return np.array([daily[..., max(0, int(t) - 7):int(t)].sum(axis=-1) for t in times]).T


def show(label, ours, key):
    """ The peaks and when they come, and the largest difference from the original's mean, as a share of its peak, which is returned """
    times, theirs = ref[key]
    theirs = np.array(theirs)
    n = min(len(ours), len(theirs))
    diff = np.abs(ours[:n] - theirs[:n]).max()/theirs.max()
    print(f'{label:30s} peak {ours.max():9,.0f} on day {times[ours.argmax()]:3.0f} (original {theirs.max():9,.0f} on day {times[theirs.argmax()]:3.0f}); largest difference {diff:.1%} of the peak')
    return diff


def fixed_runs(scenario):
    """ Runs of a scenario at the fixed values, which are the model's defaults """
    return ss.parallel(model.sim.new(verbose=0, interventions=model.reopening.get(scenario), stop=end), n_runs=n_runs, workers=1).results.covid


if __name__ == '__main__':
    print(f'At fixed values ({data["fixed"]}), the mean of {n_runs} runs:')
    times = ref['fixed_persistence_deaths'][0]
    for scenario in scenarios:
        res = fixed_runs(scenario)
        diff = show(f'{scenario}: weekly deaths', weekly(np.asarray(res.deaths.values), times).mean(axis=0), f'fixed_{scenario}_deaths')
        assert diff < tol_fixed, f'Weekly deaths in {scenario} differ by more than {tol_fixed:.0%} of the peak'
        if scenario == 'persistence':
            for group in data['groups']:
                show(f'  deaths {group}', weekly(np.asarray(res.deaths.select(age=group).values), times).mean(axis=0), f'fixed_{scenario}_deaths_{group}')
            series = {name:res[name].mean().values for name in 'EIR'} | dict(D=sum(res[f'D{i}'].mean().values for i in range(4)))
            for name,vals in series.items(): # The original's day k is at the end of that day, ours at index k (index 0 is the start)
                show(f'  {name}', vals[1:], f'fixed_{scenario}_{name}')
            total, theirs = res.Dead.mean().values[-1], ref[f'fixed_{scenario}_D4'][1][-1]
            print(f'  total deaths by 2 August: {total:,.0f} (original {theirs:,.0f})')
            assert abs(total/theirs - 1) < tol_fixed, f'Total deaths differ by more than {tol_fixed:.0%}'

    abc = data['abc']
    print(f'\nABC-SMC to the weekly deaths up to 31 May, as in the original: {abc["particles"]} particles for {abc["generations"]} generations')
    fit = model.sim.new(verbose=0).fit(method=ss.fitting.method('abc-smc', samples=abc['particles'], generations=abc['generations']), rand_seed=1, verbose=0)
    for par,name in dict(R0='R0', Delta='Delta', I0='I0', seasonality_min='smin').items():
        row = table.loc[f'posterior_{par}']
        vals = fit.samples[name]
        print(f'  {par:16s} Starsim mean {vals.mean():.4g} (5% to 95%: {vals.quantile(0.05):.4g} to {vals.quantile(0.95):.4g}); original {row.value:.4g} ({row.low:.4g} to {row.high:.4g})')
        assert row.low <= vals.mean() <= row.high, f'The posterior mean of {par} is outside the original\'s 5% to 95% range'
    print('Projections from the posterior (mean of 100 draws, in both):')
    draws = fit.samples.sample(n=100, replace=len(fit.samples) < 100, random_state=1)[list(fit.table['par'])]
    sims = [fit.sim.new(label=k, pars=dict(fit.pars), interventions=model.reopening.get(k), stop=end, verbose=0) for k in scenarios]
    msim = ss.parallel(*sims, priors=draws, workers=1) # What fit.project() does, one at a time
    for i,scenario in enumerate(scenarios):
        ours = weekly(np.array([s.results.covid.deaths.values for s in msim.sims if s.label == scenario]), times).mean(axis=0)
        show(f'  {scenario}: weekly deaths', ours, f'abc_{scenario}_deaths')
        peak = np.max(ref[f'abc_{scenario}_deaths'][1])
        assert abs(ours.max()/peak - 1) < tol_proj, f'Peak weekly deaths in {scenario} differ by more than {tol_proj:.0%}'

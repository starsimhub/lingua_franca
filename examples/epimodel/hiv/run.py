"""
Run the original EpiModel Gallery script and write its reference results and timing.

    python run.py

Needs the epimodel environment (see `_envs/epimodel`). Takes about 40 minutes on one core.
"""
import os
import csv
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

original = os.path.join(here, 'original')
driver = os.path.join(here, 'reference.R') # Runs the original with n_runs simulations of each scenario
scenarios = ['none', 'cascade', 'prep', 'both']
series = ['num', 's.num', 'i.num', 'si.flow', 'acute.num', 'chronic.num', 'aids.num', 'dx.num', 'art.num', 'supp.num',
          'prep.num', 'prep.indic.num', 'dep.flow', 'aids.dep.flow', 'arr.flow', 'main.edges', 'main.concurrent', 'cas.edges', 'cas.concurrent']
n_runs = 10 # Per scenario; each takes about 50 s
seed = 1
n_cores = 1 # One process at a time; more cores are faster but give different random numbers


def simulate():
    """ Run the model, returning its simulations (one row per scenario, simulation, and time step), its summary table, and the times in seconds of its steps """
    with tempfile.TemporaryDirectory() as tmp:
        tools.run(['Rscript', driver, original, tmp, str(n_runs), str(seed), str(n_cores)], 'epimodel', cwd=tmp)
        with open(os.path.join(tmp, 'runs.csv')) as f:
            runs = [{key:(val if key == 'scenario' else float(val)) for key,val in row.items() if val not in ('', 'NA')} for row in csv.DictReader(f)]
        with open(os.path.join(tmp, 'summary.csv')) as f:
            summary = list(csv.DictReader(f))
        with open(os.path.join(tmp, 'seconds.csv')) as f:
            seconds = {row['what']:float(row['seconds']) for row in csv.DictReader(f)}
    return runs, summary, seconds


def summarize(rows, key, time='time'):
    """ The mean and the 5% and 95% quantiles over the runs, at each time """
    rows = [row for row in rows if key in row] # The flows have no value at the first time step
    times = sorted({row[time] for row in rows})
    out = []
    for t in times:
        vals = sorted(row[key] for row in rows if row[time] == t)
        n = len(vals)
        out.append(dict(time=t, value=sum(vals)/n, low=vals[int(0.05*(n - 1))], high=vals[int(0.95*(n - 1))]))
    return out


if __name__ == '__main__':
    runs, summary, seconds = simulate()
    rows = []
    for scen in scenarios:
        these = [row for row in runs if row['scenario'] == scen]
        assert len({row['sim'] for row in these}) == n_runs
        for key in series:
            rows += [dict(series=f'{scen}_{key}', **row) for row in summarize(these, key)]

    tools.write_results(here, rows)
    with open(os.path.join(here, 'reference', 'summary.csv'), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    one = seconds['netsim_none'] # The scenario with no intervention, which is the one Starsim's time is of
    netest = seconds['est_main'] + seconds['est_cas']
    each = ', '.join(f'{s} {seconds[f"netsim_{s}"]:.1f} s' for s in scenarios)
    what = f'one netsim simulation (1040 weekly steps, 1500 nodes, two network layers) with no intervention, on one core, inside one R session. The rerun is the mean of {n_runs} runs in one netsim call, as one run cannot be taken alone without a further long run (by scenario: {each}); the first run is that plus estimating the two networks (netest, {netest:.1f} s). Neither includes starting R or loading EpiModel'
    tools.write_timing(here, one, what, first=netest + one)
    print(f'Wrote {len(rows)} rows; one simulation takes {one:.1f} s, and estimating the networks {netest:.1f} s')
    for row in summary:
        print(row)

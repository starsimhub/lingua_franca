"""
Run the original flepiMoP configuration and write its reference results, the values it drew, and its timing.

    python run.py

Needs the flepimop environment (see `_envs/flepimop`). It takes about three minutes.
"""
import os
import csv
import sys
import glob
import time
import shutil
import tempfile
import datetime
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

config = 'config_sample_2pop_vaccine_scenarios.yml'
scenarios = ['no_vax', 'pess_vax', 'opt_vax']
subpops = ['large_province', 'small_province']
states = ['S', 'E', 'I', 'R', 'V']
outcomes = ['incidCase', 'incidHosp', 'currHosp', 'incidDeath']
start = datetime.date(2020, 2, 1) # start_date in the configuration
n_days = 213


def read(pattern):
    """ Read each slot's file of one kind, in the order of the slots """
    out = []
    for path in sorted(glob.glob(pattern)):
        with open(path) as f:
            out.append(list(csv.DictReader(f)))
    return out


def day(row):
    return (datetime.date.fromisoformat(row['date'][:10]) - start).days


def simulate():
    """ Run the configuration (every scenario, ten slots each), returning the series and the values drawn for each slot """
    with tempfile.TemporaryDirectory() as tmp: # flepiMoP reads and writes relative to where it is run
        project = shutil.copytree(os.path.join(here, 'original'), os.path.join(tmp, 'project'))
        cmd = ['flepimop', 'simulate', config, '--write-csv', '--no-write-parquet', '--jobs', '1', '--in-id', 'reference', '--out-id', 'reference'] # Without --in-id, the outcomes look for the SEIR output under another ID and fail
        tools.run(cmd, 'flepimop', cwd=project)
        series = dict() # {(scenario, name): array of slots by days}
        draws = []
        for scen in scenarios:
            folder = os.path.join(project, 'model_output', f'sample_2pop_{scen}', 'reference')
            seir = read(os.path.join(folder, 'seir', '*.seir.csv'))
            hosp = read(os.path.join(folder, 'hosp', '*.hosp.csv'))
            spar = read(os.path.join(folder, 'spar', '*.spar.csv'))
            hpar = read(os.path.join(folder, 'hpar', '*.hpar.csv'))
            assert len(seir) == len(hosp) == 10
            for slot in range(len(seir)):
                Ro = [float(r['value']) for r in spar[slot] if r['parameter'] == 'Ro'][0]
                p_case = [float(r['value']) for r in hpar[slot] if r['outcome'] == 'incidCase' and r['quantity'] == 'probability'][0]
                draws.append(dict(scenario=scen, slot=slot + 1, Ro=Ro, p_case=p_case))
                for subpop in subpops:
                    for kind in ['prevalence', 'incidence']:
                        for state in states:
                            name = f'{subpop}_{state}' if kind == 'prevalence' else f'{subpop}_incidence_{state}'
                            arr = series.setdefault((scen, name), np.zeros((len(seir), n_days)))
                            for row in seir[slot]:
                                if row['mc_value_type'] == kind and row['mc_name'] == state:
                                    arr[slot, day(row)] = float(row[subpop])
                    for outcome in outcomes:
                        arr = series.setdefault((scen, f'{subpop}_{outcome}'), np.zeros((len(seir), n_days)))
                        for row in hosp[slot]:
                            if row['subpop'] == subpop:
                                arr[slot, day(row)] = float(row[outcome])
        return series, draws


if __name__ == '__main__':
    t0 = time.perf_counter()
    series, draws = simulate()
    first = time.perf_counter() - t0
    t0 = time.perf_counter()
    simulate()
    rerun = time.perf_counter() - t0
    rows = []
    for (scen,name),arr in series.items():
        ordered = np.sort(arr, axis=0)
        n = len(arr)
        for t in range(n_days):
            rows.append(dict(time=t, series=f'{scen}_{name}', value=arr[:, t].mean(), low=ordered[int(0.05*(n - 1)), t], high=ordered[int(0.95*(n - 1)), t]))
    tools.write_results(here, rows)
    with open(os.path.join(here, 'reference', 'draws.csv'), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['scenario', 'slot', 'Ro', 'p_case'])
        writer.writeheader()
        writer.writerows(draws)
    what = f'flepimop simulate {config} --jobs 1, as one command, which is the only way to run it: 3 scenarios of 10 runs each, with their outcomes (after the first, each run takes about 2.6 s). The rerun is the same command again, and each is timed once, since it takes about 90 s; both include starting Python and compiling'
    tools.write_timing(here, rerun, what, first=first)
    print(f'Wrote {len(rows)} rows and {len(draws)} draws; the whole command takes {first:.1f} s, and {rerun:.1f} s again')

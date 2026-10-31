"""
Run the original epydemix model and write its reference results and timing.

    python run.py

Needs the epydemix environment (see `_envs/epydemix`), and a network connection: the
population and contact matrices of Kenya are downloaded from epydemix-data (v1.2.0).
"""
import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools


if __name__ == '__main__':
    # simulate.py runs original/sir_kenya.py with a fixed seed, summarizes its 100 runs, and times it
    out = json.loads(tools.run(['python', os.path.join(here, 'simulate.py')], 'epydemix'))
    rows = sorted(out['rows'], key=lambda row: row['series']) # Stable sort: keeps the times in order
    for row in rows:
        for key in ['value', 'low', 'high']:
            row[key] = round(row[key], 2)

    tools.write_results(here, rows)
    with open(os.path.join(here, 'reference', 'population.json'), 'w') as f:
        lines = [f'  {json.dumps(key)}: {json.dumps(val)}' for key,val in out['info'].items()] # One line per key
        f.write('{\n' + ',\n'.join(lines) + '\n}\n')
    what = f'model.run_simulations(Nsim=1): one stochastic run of {out["info"]["n_steps"]} daily steps, in process, with the model already defined, and without the import or the data download. The first run is the first call in the process, and the rerun the best of 5 calls after it (the 100 runs of the original take {out["many"]:.2f} s)'
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f'Wrote {len(rows)} rows from {out["info"]["n_runs"]} runs; a first run takes {out["first"]:.4f} s, and a rerun {out["rerun"]:.4f} s')

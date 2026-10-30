"""
Run the original epydemix model and write its reference results and timing.

    python run.py

Needs the epydemix environment (see `_envs/epydemix`), and a network connection: the
population and contact matrices of Massachusetts are downloaded from epydemix-data (v1.2.0).
Takes about two minutes, most of it the (reduced) ABC-SMC calibration.
"""
import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools


if __name__ == '__main__':
    # simulate.py runs original/covid19.py with a fixed seed and a smaller calibration, summarizes it, and times one run
    out = json.loads(tools.run(['python', os.path.join(here, 'simulate.py')], 'epydemix'))
    rows = sorted(out['rows'], key=lambda row: row['series']) # Stable sort: keeps the times in order
    for row in rows:
        for key in ['value', 'low', 'high']:
            if key in row:
                row[key] = round(row[key], 4 if row['series'].startswith('posterior') else 2)

    tools.write_results(here, rows)
    with open(os.path.join(here, 'reference', 'population.json'), 'w') as f:
        lines = [f'  {json.dumps(key)}: {json.dumps(val)}' for key,val in out['info'].items()] # One line per key
        f.write('{\n' + ',\n'.join(lines) + '\n}\n')
    abc = out['info']['abc']
    what = f'simulate_wrapper(): one stochastic run of the 99 days of the calibration period, as the calibration evaluates it, in process, with the model already defined. The first run is the first call, and the rerun the best of 5 calls after the calibration (the reduced ABC-SMC, {abc["particles"]} particles for {abc["generations"]} generations, takes {abc["seconds"]:.0f} s)'
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f'Wrote {len(rows)} rows; a first run takes {out["first"]:.4f} s, and a rerun {out["rerun"]:.4f} s; the calibration took {abc["seconds"]:.0f} s')

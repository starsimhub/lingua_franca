"""
Run the original summer2 model and write its reference results and timing.

    python run.py

Needs the summer2 environment (see `_envs/summer2`).
"""
import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

if __name__ == '__main__':
    out = json.loads(tools.run(['python', os.path.join(here, 'export.py')], 'summer2'))
    rows, rerun, first = out['rows'], out['rerun'], out['first']
    tools.write_results(here, rows)
    what = 'first: building the model, compiling it with JAX, and running it once, in a fresh process, with summer2 and JAX already imported. rerun: model.run() on that same compiled model'
    tools.write_timing(here, rerun, what, first=first)
    print(f'Wrote {len(rows)} rows; the first run takes {first:.2f} s, a rerun {rerun:.4f} s')

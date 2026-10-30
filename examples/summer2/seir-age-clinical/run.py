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
    rows, rerun, first, first_model = out['rows'], out['rerun'], out['first'], out['first_model']
    tools.write_results(here, rows)
    what = f'first: building, compiling with JAX, and running all seven models, as the original does to get all its outputs, in a fresh process, with summer2 and JAX already imported (the first model alone takes {first_model:.2f} s). rerun: model.run() on the last of the seven, already compiled, with four derived outputs'
    tools.write_timing(here, rerun, what, first=first)
    print(f'Wrote {len(rows)} rows; the first run of all seven takes {first:.2f} s, of the first model alone {first_model:.2f} s, a rerun {rerun:.4f} s')

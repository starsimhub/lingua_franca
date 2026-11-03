"""
Run the original and write its reference results and timing

    python run.py

Needs the Pandemic Simulator environment (see `_envs/pandemic_simulator`). It runs the example with its central
values (`original/central-config.json`, the example's config with no uncertain inputs), with the measure and without.
"""
import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

if __name__ == '__main__':
    out = json.loads(tools.run(['python', os.path.join(here, 'export.py')], 'pandemic_simulator', cwd=here).splitlines()[-1]) # After what the framework logs on import
    tools.write_results(here, out['rows'])
    what = 'first: validating the config, building the model, compiling with JAX, and running it once with the measure, in a fresh process, with JAX and the framework already imported. rerun: the same model run again, already compiled. Both include its results, and neither the two worker processes of its main script, which runs the model with and without the measure'
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f'Wrote {len(out["rows"])} rows; a first run takes {out["first"]:.3f} s, a rerun {out["rerun"]:.4f} s')

"""
Run the original and write its reference results and timing

    python run.py

Needs the Pandemic Simulator environment (see `_envs/pandemic_simulator`). It runs the example with its central
values (`original/central-config.json`, the example's config with no uncertain inputs), once with
the measure and once without, as the framework always does.
"""
import os
import sys
import json
import time
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

model = 'compartment.models.example_parameter_uncertainty_declarative_model.main'
config = os.path.join(here, 'original', 'central-config.json')


def run(filename):
    """ One run in a fresh process, with its two integrations; returns the time in seconds """
    start = time.perf_counter()
    tools.run(['python', '-m', model, '--mode', 'local', '--config_file', config, '--output_file', filename], 'pandemic_simulator', cwd=here)
    return time.perf_counter() - start


if __name__ == '__main__':
    filename = os.path.join(tempfile.mkdtemp(), 'results.json')
    first = run(filename)
    rerun = min(run(filename) for _ in range(tools.runs(3)))
    rows = []
    for result in json.load(open(filename)):
        which = 'control' if result['control_run'] else 'with'
        for day,row in enumerate(result['parent_admin_total']['time_series']):
            rows += [dict(time=day, series=f'{which}_{c}', value=row[c]['age_all']) for c in 'SIR']
    tools.write_results(here, rows)
    what = 'first and rerun: a fresh process each, importing JAX and running the model with and without the measure in two worker processes, as its main script does; the framework has no way to run a model again in the same process'
    tools.write_timing(here, rerun, what, first=first)
    print(f'Wrote {len(rows)} rows; a first run takes {first:.2f} s, a rerun {rerun:.2f} s')

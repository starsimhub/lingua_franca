"""
Run the original in this process and print its results and timing as JSON

This is the part of `run.py` that runs in the Pandemic Simulator's environment (see
`_envs/pandemic_simulator`). The framework's main script starts two workers and runs the model
with and without the measure; here each is run by the function those workers call, so that one
run can be timed alone and run again, as Starsim's is.
"""
import os
import sys
import json
import time
import logging
from copy import deepcopy

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from compartment.cloud_helpers.s3 import record_and_upload_validation
from compartment.helpers import load_config_from_json
from compartment.models.example_parameter_uncertainty_declarative_model.model import ExampleParameterUncertaintyDeclarativeModel as Model
from compartment.run_simulation import simulate_and_postprocess

logging.disable(logging.CRITICAL) # The framework logs to stdout, which carries the JSON here

config = load_config_from_json(os.path.join(here, 'original', 'central-config.json'))


def build():
    """ The model with the measure and the model without it, from the validated config, as `run_simulation()` makes them """
    ok, cleaned = record_and_upload_validation('local', config, Model.MODEL_KEY)
    assert ok
    with_measure = Model(cleaned)
    without = deepcopy(with_measure)
    without.intervention_dict = {}
    return with_measure, without


start = time.perf_counter()
with_measure, without = build()
result = simulate_and_postprocess(with_measure) # Timed with the measure, as Starsim's is
first = time.perf_counter() - start
rerun = tools.repeat(lambda: simulate_and_postprocess(with_measure))

rows = []
for which,res in [('with', result), ('control', simulate_and_postprocess(without))]:
    for day,row in enumerate(res['parent_admin_total']['time_series']):
        rows += [dict(time=day, series=f'{which}_{c}', value=row[c]['age_all']) for c in 'SIR']
print(json.dumps(dict(rows=rows, first=first, rerun=rerun)))

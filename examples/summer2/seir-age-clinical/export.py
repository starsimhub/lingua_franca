"""
Run the original summer2 example and print its results and timing as JSON.

This is the summer2-specific part of `run.py`, which calls it with the Python of
the summer2 environment (see `_envs/summer2`).
"""
import os
import sys
import json
import time
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, 'original'))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
import pandas as pd
import summer2 # Not timed, as importing Starsim is not

pd.DataFrame.plot = property(lambda df: lambda *args, **kwargs: None) # Not timed either; the original plots its results

# The script builds and runs the model seven times, each with different derived outputs; keep each one
models = []
ends = [] # When each run ended
run = summer2.CompartmentalModel.run
def keep(self, *args, **kwargs):
    out = run(self, *args, **kwargs)
    models.append(self)
    ends.append(time.perf_counter())
    return out
summer2.CompartmentalModel.run = keep

start = time.perf_counter()
import derived_outputs as original # Builds, compiles, and runs the models on import
first = time.perf_counter() - start
summer2.CompartmentalModel.run = run

rows = []
model = models[0]
df = model.get_outputs_df()
for comp in model.compartments:
    series = '_'.join([comp.name] + list(comp.strata.values())) # E.g. "S_young" or "I_old_hospital"
    rows += [dict(time=round(float(t), 6), series=series, value=float(v)) for t,v in df[str(comp)].items()]

# The derived outputs of all the runs; the same name in two runs is the same output
seen = {}
for model in models:
    derived = model.get_derived_outputs_df()
    for key in derived.columns:
        values = derived[key].values.astype(float)
        if key in seen:
            assert np.allclose(seen[key], values), key
            continue
        seen[key] = values
        rows += [dict(time=round(float(t), 6), series=key, value=float(v)) for t,v in zip(derived.index, values)]

# Time one run of the last model, which requests four derived outputs
rerun = tools.time_run(models[-1].run)
json.dump(dict(rows=rows, rerun=rerun, first=first, first_model=ends[0] - start, n_models=len(models)), sys.stdout)

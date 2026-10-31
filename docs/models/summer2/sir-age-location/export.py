"""
Run the original summer2 example and print its results and timing as JSON.

This is the summer2-specific part of `run.py`, which calls it with the Python of
the summer2 environment (see `_envs/summer2`).
"""
import os
import sys
import json
import time

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, 'original'))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
import pandas as pd
import summer2 # Not timed, as importing Starsim is not

pd.DataFrame.plot = property(lambda df: lambda *args, **kwargs: None) # Not timed either; the original plots its results

start = time.perf_counter()
import mixing_matrices as original # Builds, compiles, and runs the model on import
first = time.perf_counter() - start

model = original.model
df = model.get_outputs_df()
rows = []
for comp in model.compartments:
    series = '_'.join([comp.name, comp.strata['age'], comp.strata['location']]) # E.g. "S_young_urban"
    rows += [dict(time=round(float(t), 6), series=series, value=float(v)) for t,v in df[str(comp)].items()]

# The example defines no derived outputs, but any that exist are included
derived = model.get_derived_outputs_df()
for key in derived.columns:
    rows += [dict(time=round(float(t), 6), series=key, value=float(v)) for t,v in derived[key].items()]

rerun = tools.time_run(model.run)
json.dump(dict(rows=rows, rerun=rerun, first=first), sys.stdout)

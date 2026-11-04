"""
Run the original in this process and print its results and timing as JSON

    python export.py 20

This is the part of `run.py` that runs in epymorph's environment (see `_envs/epymorph`). It runs the
vignette's own text, changed in three ways without changing the file: the two ADRIOs are replaced by
the values they return, kept in `original/arizona_counties.csv` by `fetch.py`, so that no download is
needed; the diagram of the IPM is left out, since it needs graphviz and LaTeX; and it stops before the
run and the plots. The model is then run once with each of the given number of seeds.
"""
import os
import sys
import json
import time
import numpy as np
import pandas as pd

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from epymorph.kit import *
from epymorph.data_type import CentroidDType

n_runs = int(sys.argv[1])
data = pd.read_csv(os.path.join(here, 'original', 'arizona_counties.csv'), dtype=dict(geoid=str))
cached = dict(
    population = data.population.values,
    centroid = np.array(list(zip(data.longitude, data.latitude)), dtype=CentroidDType),
)
text = open(os.path.join(here, 'original', 'mm_intro_centroids.py')).read()
text = text.replace('acs5.Population()', 'cached["population"]').replace('us_tiger.InternalPoint()', 'cached["centroid"]')
text = text.replace('sirs_ipm.diagram()', '').split('print(rume.params_description())')[0]

start = time.perf_counter()
scope = dict(cached=cached)
exec(text, scope) # Builds the RUME
rume = scope['rume']
assert list(rume.scope.node_ids) == list(data.geoid)
run = lambda seed=5: BasicSimulator(rume).run(rng_factory=default_rng(seed))
run() # The vignette's own run, with its seed
first = time.perf_counter() - start
rerun = tools.repeat(run)

# Each compartment in each county at the end of each day (after its two tau steps), and the day's new infections
runs = []
for seed in range(1, n_runs + 1):
    out = run(seed)
    comps = np.concatenate([out.initial[None], out.compartments[1::2]]) # Days 0 to 190, by county and compartment
    infections = out.events[:, :, 0].reshape(-1, 2, rume.scope.nodes).sum(axis=1) # Days 0 to 189
    runs.append(dict(comps=comps.tolist(), infections=infections.tolist()))
print(json.dumps(dict(runs=runs, names=list(data.name), first=first, rerun=rerun)))

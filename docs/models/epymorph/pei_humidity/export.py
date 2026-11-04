"""
Run the original in this process and print its results and timing as JSON

    python export.py 20

This is the part of `run.py` that runs in epymorph's environment (see `_envs/epymorph`). It runs the
notebook's own text, changed in two ways without changing the file: the three ADRIOs are replaced by
the data that epymorph bundles for this example (`epymorph.data.pei`), so that no download or Census
API key is needed; and it stops before the run, which is then made once with each of the given number of seeds.
"""
import os
import sys
import json
import time
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from epymorph.kit import *

n_runs = int(sys.argv[1])
text = open(os.path.join(here, 'original', 'usage.py')).read()
text = text.replace('from epymorph.data.pei import pei_humidity', 'from epymorph.data.pei import pei_humidity, pei_centroids, pei_population, pei_commuters')
text = text.replace('us_tiger.InternalPoint()', 'pei_centroids').replace('acs5.Population()', 'pei_population').replace('commuting_flows.Commuters()', 'pei_commuters')
text = text.split('# Construct a simulator')[0]

start = time.perf_counter()
scope = dict()
exec(text, scope) # Builds the RUME
rume = scope['rume']
run = lambda seed=1: BasicSimulator(rume).run(rng_factory=default_rng(seed))
run() # The notebook's own run, with its seed
first = time.perf_counter() - start
rerun = tools.repeat(run)

# Each compartment in each state at the end of each day (after its two tau steps), and the day's new infections
runs = []
for seed in range(1, n_runs + 1):
    out = run(seed)
    comps = np.concatenate([out.initial[None], out.compartments[1::2]]) # Days 0 to 150, by state and compartment
    infections = out.events[:, :, 0].reshape(-1, 2, rume.scope.nodes).sum(axis=1) # Days 0 to 149
    runs.append(dict(comps=comps.tolist(), infections=infections.tolist()))
print(json.dumps(dict(runs=runs, names=list(rume.scope.labels), first=first, rerun=rerun)))

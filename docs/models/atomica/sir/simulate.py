"""
Run the original Atomica model and print its results and timing as JSON (called by `run.py`, in the Atomica environment).
"""
import os
import sys
import json
import time
import logging

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, 'original'))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
import atomica as at
import sir

at.logger.setLevel(logging.WARNING) # Atomica prints the time of each run


def extract(result):
    """ The compartments, flows, and main outputs as rows of time, series, and value """
    rows = []
    dt = result.dt
    add = lambda series, vals: rows.extend(dict(time=float(t), series=series, value=float(v)) for t,v in zip(result.t, vals))
    for pop in result.model.pops:
        for comp in pop.comps:
            add(f'{pop.name}_{comp.name}', comp.vals)
        flows = dict() # People per year, adding up the links between the same two compartments
        for link in pop.links:
            key = f'{pop.name}_{link.source.name}_to_{link.dest.name}'
            flows[key] = flows.get(key, 0) + link.vals/dt
        for key,vals in flows.items():
            add(key, vals)
        for name in ['ch_all', 'ch_prev', 'foi']:
            add(f'{pop.name}_{name}', pop.get_variable(name)[0].vals)
    return rows


if __name__ == '__main__':
    start = time.perf_counter()
    P = sir.load()
    load = time.perf_counter() - start
    result = P.run_sim()
    first = time.perf_counter() - start # Reading the spreadsheets and the first run
    rerun = tools.time_run(P.run_sim)
    print(json.dumps(dict(rows=extract(result), first=first, rerun=rerun, load=load, version=at.__version__)))

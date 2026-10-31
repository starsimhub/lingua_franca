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
import hiv_dyn

at.logger.setLevel(logging.WARNING) # Atomica prints the time of each run
characs = ['alive', 'all_people', 'all_dx', 'all_ever_linked', 'all_curr_linked', 'all_tx', 'all_vs']
pars = ['acq_rate', 'test_yield', 'diag', 'link_time', 'initiate', 'loss', 'fail_rate']


def extract(result, scen):
    """ The compartments, flows, characteristics, parameters, and program coverage as rows of time, series, and value """
    rows = []
    dt = result.dt
    add = lambda series, vals: rows.extend(dict(time=float(t), series=f'{scen}_{series}', value=float(v)) for t,v in zip(result.t, vals))
    for pop in result.model.pops:
        for comp in pop.comps:
            if comp.name != 'source':
                add(f'{pop.name}_{comp.name}', comp.vals)
        flows = dict() # People per year, adding up the links between the same two compartments
        for link in pop.links:
            key = f'{pop.name}_{link.source.name}_to_{link.dest.name}'
            flows[key] = flows.get(key, 0) + link.vals/dt
        for key,vals in flows.items():
            add(key, vals)
        for name in characs + pars:
            add(f'{pop.name}_{name}', pop.get_variable(name)[0].vals)
    if result.model.programs_active:
        for prog,vals in result.get_coverage('fraction').items():
            add(f"coverage_{prog.lower().replace(' - ', '_').replace(' ', '_')}", vals)
    return rows


if __name__ == '__main__':
    start = time.perf_counter()
    P = hiv_dyn.load()
    load = time.perf_counter() - start
    result = P.run_sim()
    first = time.perf_counter() - start # Reading the spreadsheets and the first run
    rows = extract(result, 'baseline')
    for result in P.run_scenarios():
        rows += extract(result, result.name.lower().replace(' ', '_'))
    rerun = tools.time_run(P.run_sim)
    scenarios = tools.time_run(P.run_scenarios)
    print(json.dumps(dict(rows=rows, first=first, rerun=rerun, scenarios=scenarios, load=load, version=at.__version__)))

"""
Run the original and write its reference results and timing

    python run.py

Needs the epipack environment (see `_envs/epipack`). It runs `original/siarx.py` 100 times,
each on a network of its own, with `export.py` in that environment. Takes about five minutes.
"""
import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

if __name__ == '__main__':
    n_runs = tools.runs(100)
    out = json.loads(tools.run(['python', os.path.join(here, 'export.py'), str(n_runs)], 'epipack', cwd=here))
    tools.write_results(here, out['rows'])
    what = 'first: making the network and the model, and simulating it on the network with contact tracing for 40 days, in a fresh process, with epipack and networkx already imported. rerun: the best of the simulations on the network of all the runs, each of a model already built on its network. Not timed here: the run well mixed (well_mixed_rerun) and the deterministic model (ode_rerun), which run.log gives'
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f'Wrote {len(out["rows"])} rows; on the network a first run takes {out["first"]:.3f} s and a rerun {out["rerun"]:.3f} s; well mixed a run takes {out["well_mixed_rerun"]:.3f} s, and integrating the deterministic model {out["ode_rerun"]:.4f} s')

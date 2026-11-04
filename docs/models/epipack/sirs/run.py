"""
Run the original and write its reference results and timing

    python run.py

Needs the epipack environment (see `_envs/epipack`). It integrates the README's SIRS, simulates it
1,000 times by Gillespie's method, and runs it 100 times on a random network, with `export.py` in
that environment. Takes about seven minutes.
"""
import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

if __name__ == '__main__':
    n_gillespie, n_network = tools.runs(1000), tools.runs(100)
    out = json.loads(tools.run(['python', os.path.join(here, 'export.py'), str(n_gillespie), str(n_network)], 'epipack', cwd=here))
    tools.write_results(here, out['rows'])
    what = 'first: building the model and integrating it (integrate() at the 1,000 times of the original), in a fresh process, with epipack already imported. rerun: integrating it again. Not timed here: a Gillespie run (simulate(), timed as gillespie_rerun) and a run on the network (network_first, which includes making the network, and network_rerun), which run.log gives'
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f'Wrote {len(out["rows"])} rows; integrating takes {out["first"]:.3f} s at first and {out["rerun"]:.4f} s again; a Gillespie run {out["gillespie_rerun"]:.4f} s; on the network a first run (making the network too) {out["network_first"]:.2f} s, and a rerun {out["network_rerun"]:.2f} s')

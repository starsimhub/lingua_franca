"""
Run the original Atomica model and write its reference results and timing.

    python run.py

Needs the Atomica environment (see `_envs/atomica`).
"""
import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

if __name__ == '__main__':
    out = json.loads(tools.run(['python', os.path.join(here, 'simulate.py')], 'atomica').splitlines()[-1])
    rows = out['rows']
    tools.write_results(here, rows)
    first, rerun = out['first'], out['rerun']
    what = f"Atomica {out['version']}, one run of 20 yearly steps without programs. First: reading the spreadsheets (about {out['load']:.1f} s) and Project.run_sim(). Rerun: Project.run_sim() again on the loaded project. The three budget scenarios (Project.run_scenarios()) take {out['scenarios']:.4f} s together"
    tools.write_timing(here, rerun, what, first=first)
    print(f"Wrote {len(rows)} rows; a first run takes {first:.3f} s, a rerun {rerun:.4f} s, and the three scenarios {out['scenarios']:.4f} s")

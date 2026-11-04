"""
Run the original vignette and write its reference results and timing.

    python run.py

Needs the epidemics environment (see `_envs/epidemics`). The driver is the one of `../seirv/run.py`: it gives the
contact matrix and demography as the vignette prints them, leaves out the plots, and runs the rest of
`original/modelling_time_dependence.R` as it is.
"""
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(here), 'seirv'))
import run as seirv # The driver, shared with the other vignette
tools = seirv.tools

seirv.script = os.path.join(here, 'original', 'modelling_time_dependence.R')
scenarios = ['baseline', 'intervention', 'vaccination'] # The vignette's three calls of model_default(), in order: data, data_npi, and data_vax
seirv.timed = 2 # The scenario with the interventions, which has the most elements

if __name__ == '__main__':
    runs, found = seirv.simulate()
    assert len(runs) == len(scenarios)
    rows = []
    for scen,run in zip(scenarios, runs):
        rows += seirv.to_rows(run, prefix=f'{scen}_')
    tools.write_results(here, rows)
    first, rerun = float(found['FIRST']), float(found['RERUN'])
    what = f'the scenario with the interventions and the seasonal transmission rate: the call of model_default() that makes data_npi (checking the inputs, running the compiled odin model for 365 days, and making its table of results). first is that call as the vignette makes it, in a fresh R session with epidemics loaded, after the baseline scenario; rerun is the best of {seirv.reps} more of the same call. Neither includes starting R or loading the package'
    tools.write_timing(here, rerun, what, first=first)
    print(f'Wrote {len(rows)} rows; first run {first:.4f} s, rerun {1000*rerun:.2f} ms')

"""
Run the original MEmilio example and write its reference results and timing.

    python run.py

Needs the memilio environment (see `_envs/memilio`).
"""
import os
import sys
import json
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

script = os.path.join(here, 'original', 'ode_secir_simple.py')

# The original prints only the last value and plots the rest, so this runs it as it is, keeping what
# it passes through `simulate` and `interpolate_simulation_result`
driver = """
import sys, json, time, importlib.util
import matplotlib
matplotlib.use('Agg')
from memilio.simulation.osecir import InfectionState

spec = importlib.util.spec_from_file_location('ode_secir_simple', sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
kept = dict()

simulate = mod.simulate

def keep(name):
    func = getattr(mod, name)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        out = func(*args, **kwargs)
        kept[name] = out
        kept['args'] = kept.get('args', args) # Those of simulate(), which comes first
        kept['done'] = time.perf_counter()
        kept[name + '_seconds'] = time.perf_counter() - start
        return out
    setattr(mod, name, wrapper)

keep('simulate')
keep('interpolate_simulation_result')
start = time.perf_counter()
mod.run_ode_secir_simulation(show_plot=False)
first = kept['done'] - start # Up to the end of interpolating, which leaves out what the example does next: printing and drawing the plot
rerun = float('inf')
for i in range(100): # The same model through the solver again
    start = time.perf_counter()
    simulate(*kept['args'])
    rerun = min(rerun, time.perf_counter() - start)

arr = kept['interpolate_simulation_result'].as_ndarray()
names = [name for name,state in sorted(InfectionState.__members__.items(), key=lambda item: int(item[1])) if name != 'Count']
assert len(names) == arr.shape[0] - 1
out = dict(time=arr[0].tolist(), steps=kept['simulate'].get_num_time_points(), first=first, rerun=rerun)
out['states'] = {name:arr[i + 1].tolist() for i,name in enumerate(names)}
print('RESULT ' + json.dumps(out))
"""


def simulate():
    """ Run the example, returning the times, the count in each state at each time, and what the solver did """
    with tempfile.TemporaryDirectory() as tmp: # The example saves its plot where it is run
        out = tools.run(['python', '-c', driver, script], 'memilio', cwd=tmp)
    line = [line for line in out.splitlines() if line.startswith('RESULT ')][-1]
    return json.loads(line[len('RESULT '):])


if __name__ == '__main__':
    out = simulate()
    rows = []
    for name,values in out['states'].items():
        rows += [dict(time=t, series=name, value=value) for t,value in zip(out['time'], values)]

    tools.write_results(here, rows)
    what = f'first is one call of the example\'s run_ode_secir_simulation(), with its plot off, up to the end of interpolating the result: building the model and running it ({out["steps"]} adaptive time points), not counting starting Python, importing, or drawing the plot; rerun is the best of 100 more calls of simulate() on the same model'
    tools.write_timing(here, out['rerun'], what, first=out['first'])
    print(f'Wrote {len(rows)} rows; first run {out["first"]*1000:.2f} ms, rerun {out["rerun"]*1000:.3f} ms')

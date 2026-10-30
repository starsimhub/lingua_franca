"""
Run the original LASER England and Wales model several times, each with a
different seed, and print the results as JSON. This is run by `run.py`, in the
LASER environment.

    python simulate.py <n_runs> <center> <radius> <scale> <years>

The model cells of the notebook (1 to 4, and 8) are run as they are, with these
changes made to their text here (the file is not changed): the data are read
from the laser-generic source in `_envs/laser/src`; `import pywt`, which only the
wavelet analysis after the model needs, is left out; the sweep over 150
parameter sets runs one set, the best one the notebook reports (simulation 56);
the seed, which is 4 for every simulation in the notebook, is set for each run;
the length is `years`; only the places within `radius` km of `center` are kept
(with the distances between them); and every place's population is multiplied
by `scale`.
"""
import os
import sys
import json
import time
import tempfile
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, '..', '..', '..', '_envs', 'laser', 'src', 'laser-generic-1.1.0')
best = dict(beta=3.865332, amplitude=1.310744, k=0.044565, b=0.251464, c=1.563193) # Printed by cell 18 of the notebook
places = ['Norwich', 'Cambridge', 'Colchester', 'Kings.Lynn', 'Ely', 'Thetford', 'Southwold'] # Large to small


def replace(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def cells():
    """ The model cells of the notebook, changed as described above """
    with open(os.path.join(here, 'original', '10_England_and_Wales.ipynb')) as f:
        nb = json.load(f)
    code = [''.join(cell['source']) for cell in nb['cells'] if cell['cell_type'] == 'code']
    setup = replace(code[0], 'import pywt\n', '')
    setup = replace(setup, 'Path.cwd().parent.parent.parent / "data"', f'Path({os.path.abspath(src)!r}) / "data"')
    model = replace(code[4], 'run_sims = False', 'run_sims = True')
    sweep = code[5]
    sweep = replace(sweep, 'nsims = 150', 'nsims = 1')
    sweep = replace(sweep, 'nticks = 40*365', 'nticks = years*365')
    for key,old in dict(beta='np.random.uniform(3, 4.5, nsims)', amplitude='np.random.uniform(0.5, 1.5, nsims)', k='10 ** np.random.uniform(-3.5, -1, nsims)',
                        b='np.random.uniform(0.25, 1.0, nsims)', c='np.random.uniform(1, 2, nsims)').items():
        sweep = replace(sweep, old, f'np.full(nsims, {best[key]})')
    sweep = replace(sweep, '{"seed": 4,', '{"seed": seed,')
    scaling = '\n'.join([
        'keep = distances[engwal.placenames.index(center)] <= radius',
        'distances = distances[np.ix_(keep, keep)]',
        'scenario = scenario[keep].reset_index(drop=True)',
        'scenario["nodeid"] = np.arange(len(scenario))',
        'scenario["population"] = np.round(scenario.population*scale).astype(np.uint32)',
    ]) + '\n'
    before = compile('\n'.join([setup, code[1], code[2], code[3], model, scaling]), '10_England_and_Wales.ipynb', 'exec')
    return before, compile(sweep, '10_England_and_Wales.ipynb', 'exec')


def simulate(names, sweep, seed):
    """ Run the model once, returning daily series and the time taken """
    names['seed'] = seed
    start = time.perf_counter()
    exec(sweep, names)
    seconds = time.perf_counter() - start
    nodes, scenario = names['model'].nodes, names['scenario']
    nticks = names['nticks']
    out = dict()
    inc = nodes.newly_infected[:nticks]
    out['new_infections'] = inc.sum(axis=1).tolist()
    for place in places:
        out[f'new_infections_{place.lower()}'] = inc[:, scenario.name.tolist().index(place)].tolist()
    for key in ['S', 'E', 'I', 'R']:
        out[key] = getattr(nodes, key).sum(axis=1).tolist()
    out['births'] = nodes.births[:nticks].sum(axis=1).tolist()
    out['deaths'] = nodes.deaths[:nticks].sum(axis=1).tolist()
    out['imports'] = nodes.imports[:nticks].sum(axis=1).tolist()
    weeks = nticks//7
    weekly = inc[:weeks*7].reshape(weeks, 7, -1).sum(axis=1)
    out['prop_zero'] = (weekly[weeks//2:] == 0).mean(axis=0).tolist() # The share of weeks with no infections in each place, over the second half
    return out, seconds


if __name__ == '__main__':
    n_runs, center, radius, scale, years = int(sys.argv[1]), sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
    stdout, sys.stdout = sys.stdout, sys.stderr # Keep anything the model prints out of the JSON
    os.chdir(tempfile.mkdtemp()) # The notebook saves its outputs to ./outputs
    before, sweep = cells()
    names = dict(center=center, radius=radius, scale=scale, years=years)
    exec(before, names)
    runs, times = [], []
    for i in range(n_runs):
        out, seconds = simulate(names, sweep, seed=1000*(i + 1)) # Spaced out, since LASER seeds thread j with seed + j
        runs.append(out)
        times.append(seconds)
    scenario = names['scenario']
    json.dump(dict(runs=runs, rerun=min(times[1:]), first=times[0], names=scenario.name.tolist(), pop=scenario.population.tolist()), stdout)

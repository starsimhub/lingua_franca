"""
Test the structure of the Optima TB model (see `examples/atomica/optima_tb`): that it runs, in the compiled kernels and at speed, and that it has no data
"""
import ast
import runpy
import numpy as np
import sciris as sc
import paths
import timing

file = paths.root/'examples/atomica/optima_tb/model.py'
v4_seconds = 2.0 # Starsim's run of 5 years, in s, normalized to the reference machine (see timing.py)


def make_sim(stop=2005):
    sim = runpy.run_path(str(file), run_name='model')['sim']
    sim.pars.stop = float(stop)
    return sim


def test_no_data():
    sc.heading('Checking the model has no data')
    text = file.read_text()
    tree = ast.parse(text)
    assert not any(line.lstrip().startswith('#') for line in text.splitlines()), 'comments can hold sources'
    assert 'timeseries' not in text, 'a value that changes in time is data'
    keywords = {kw.arg:kw.value for node in ast.walk(tree) if isinstance(node, ast.Call) for kw in node.keywords}
    numbers = lambda node: {sub.value for sub in ast.walk(node) if isinstance(sub, ast.Constant) and isinstance(sub.value, float)}
    assert len(numbers(keywords['init'])) == 1, 'initial values should be one placeholder'
    assert len(numbers(keywords['split'])) == 1, 'the shares in each population should be one placeholder'
    assert numbers(keywords['total_pop']) == {1e6}
    pars = [node.value for node in tree.body if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == 'ss.par']
    assert {arg.value for par in pars for arg in par.args} <= {0.0, 0.01, 1.0}, 'every parameter should be a default'
    for line in text.splitlines():
        for word in ['provenance', 'calibrat']:
            assert word not in line.lower()
    return


def test_run():
    sc.heading('Running the model')
    sim = make_sim().init()
    assert sim.kernel_reason() is None, 'The whole run should be taken in one call to the kernels'
    sim.run()
    results = sim.results.flatten()
    assert all(np.isfinite(np.array(res)).all() for res in results.values())
    assert np.min(sim.diseases[0].engine.y) >= 0, 'No compartment should go below zero'
    return sim


def test_speed():
    sc.heading('Timing the model')
    seconds, _ = timing.timed(lambda: make_sim().run(), repeats=2)
    timing.check(seconds, v4_seconds, 'Run of 5 years', slowdown=3)
    return seconds

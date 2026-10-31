"""
Test importing camdl models against camdl itself: `.camdl` files compiled with it, its golden models, and its examples' results
"""
import shutil
import subprocess
import warnings
import numpy as np
import pandas as pd
import sciris as sc
import pytest
import paths
from starsim.converters.camdl import load_camdl

lfd = paths.root
camdlc = lfd / '_envs/camdl/bin/camdlc' if (lfd / '_envs/camdl/bin/camdlc').exists() else shutil.which('camdlc') or 'camdlc' # The one built for the examples; another on the PATH may be older
camdl = lfd / '_envs/camdl/bin/camdl' if (lfd / '_envs/camdl/bin/camdl').exists() else shutil.which('camdl') or 'camdl' # Likewise
golden = lfd / '_envs/camdl/src/ocaml/golden' # camdl's library of models, as compiled IR
kw = dict(verbose=False)


sir_pars = dict(beta=0.4, gamma=0.15, rho=0.6, k=10)


@pytest.mark.skipif(not sc.path(camdlc).exists(), reason='needs camdlc')
def test_camdl_file():
    """ A .camdl file, compiled with camdlc, against camdl's own ODE run """
    sc.heading('Testing camdl import from a .camdl file')
    folder = lfd / 'examples/camdl/sir'
    sim = load_camdl(folder / 'original/sir.camdl', pars=sir_pars, camdlc=str(camdlc), **kw).run()
    ref = pd.read_csv(folder / 'reference/results.csv')
    res = sim.results.sir
    for key in 'SIR':
        theirs = ref[ref.series == f'ode_{key}'].value.values # Written as whole numbers
        assert np.abs(res[key].values - theirs).max() <= 0.5, f'{key} should agree with camdl to its rounding'
    theirs = ref[ref.series == 'ode_cases'].value.values
    weekly = res.cases.values[1:].reshape(-1, 7).sum(axis=1) # The cases of each week, as camdl reports them
    assert np.allclose(weekly, theirs, atol=1e-4), 'the weekly cases should agree with camdl (written to 5 digits)'
    return sim


@pytest.mark.skipif(not golden.exists(), reason=f'needs camdl\'s golden models: {golden}')
def test_camdl_golden():
    """ camdl's own library of models (its compiler's golden IR): each imports and runs, and what is not translated is listed """
    sc.heading('Testing camdl\'s golden models')
    for path in sorted(golden.glob('*.ir.json')):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore') # Most list something in ss.errors.ImportIncomplete
            sim = load_camdl(str(path), **kw)
            sim.pars.verbose = 0
            if path.name == 'phenom_mixing_unchecked.ir.json': # camdl's example of a count used for a share, with its unit check turned off: far too fast for the step, so the run stops rather than give numbers that are not
                with pytest.raises(ValueError):
                    sim.run()
                continue
            sim.run()
        assert sim.complete, f'{path.name} should run'
        if path.name == 'polio_spatial_5.ir.json': # Its SIAs are off unless the with_sia scenario enables them: listed, not dropped
            listed = dict(sim.imported.incomplete)
            assert 'sia_north' in listed and 'with_sia' in listed['sia_north']
    return sim


@pytest.mark.skipif(not sc.path(camdl).exists(), reason='needs camdl')
def test_camdl_stratified(tmp_path):
    """ An SEIR by age and patch, with aging and movement, as a .camdl file: against camdl's own ODE run of it, and the saved reference """
    sc.heading('Testing camdl import of a stratified model')
    folder = lfd / 'examples/camdl/stratified'
    model, pars = folder / 'stratified.camdl', dict(beta=0.04, gamma=0.1, move=0.01)
    traj = tmp_path / 'traj.tsv'
    cmd = [str(camdl), 'simulate', str(model), '--backend', 'ode', '--no-progress', '--output-dir', str(tmp_path / 'store'), '-o', str(traj)]
    for key,val in pars.items():
        cmd += ['--param', f'{key}={val}']
    subprocess.run(cmd, check=True, capture_output=True)
    theirs = pd.read_csv(traj, sep='\t', comment='#')
    sim = load_camdl(model, pars=pars, camdlc=str(camdlc), **kw).run()
    res = sim.results[sim.diseases[0].name]
    cells = [key for key in res.keys() if key in theirs.columns]
    assert len(cells) == 24 # 4 states by 3 age groups by 2 patches
    for key in cells:
        assert np.abs(res[key].values - theirs[key].values).max() <= 0.5, f'{key} should agree with camdl to its rounding (it writes whole numbers)'
    ref = pd.read_csv(folder / 'reference/results.csv') # From camdl, which writes whole numbers, so a sum of 6 cells can differ by up to 3
    for c in 'SEIR':
        ours = sum(res[key].values for key in cells if key.startswith(f'{c}_'))
        assert np.abs(ours - ref[ref.series == f'ode_novax_{c}'].value.values).max() <= 3, f'{c} should agree with the reference to its rounding'
    return sim

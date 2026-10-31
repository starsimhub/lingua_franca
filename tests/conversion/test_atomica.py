"""
Test importing Atomica models against its example's results and its own library workbooks
"""
import numpy as np
import pandas as pd
import pytest
import sciris as sc
import paths
from starsim.converters.atomica import load_atomica

examples = paths.root/'examples'
atomica_lib = paths.root/'_envs/atomica/lib/python3.12/site-packages/atomica/library' # Atomica's library workbooks, in its environment
kw = dict(verbose=False)

atomica_demos = dict( # Atomica 1.32.4's own runs at dt=1 (start, stop, values at the end), from v4_design/oct17/switching/atomica.md
    udt      = (2016, 2023, dict(dx=2450.0, tx=3550.0)),
    dt       = (2016, 2024, dict(dx=240.0, tx=3360.0)),
    diabetes = (2014, 2035, dict(sus=1218222.500392, sc_uncomp=775.919855)),
    combined = (2000, 2023, {'SIR_0-4:rec':728.476002}), # The first population type only, as listed
    hiv_dyn  = (2016, 2035, dict(all_vs=1596938.31)), # A characteristic of one compartment, under its own name
)


def test_atomica_reference():
    sc.heading('Testing an Atomica model against the original results')
    folder = f'{examples}/atomica/sir'
    sim2 = load_atomica(f'{folder}/original/sir_framework.xlsx', f'{folder}/original/sir_databook.xlsx', dt=1, **kw).run()
    ref = pd.read_csv(f'{folder}/reference/results.csv')
    for comp in ['sus', 'inf', 'rec', 'dead']:
        theirs = ref[ref.series == f'adults_{comp}'].value.values
        assert np.allclose(sim2.results.SIR[comp].values, theirs), f'{comp} should agree with Atomica'
    return


@pytest.mark.skipif(not atomica_lib.exists(), reason='needs the Atomica environment')
def test_atomica_library():
    sc.heading("Testing Atomica's own library workbooks")
    for demo,(start,stop,ref) in atomica_demos.items():
        sim3 = load_atomica(atomica_lib/f'{demo}_framework.xlsx', atomica_lib/f'{demo}_databook.xlsx', start=start, stop=stop, dt=1, **kw)
        sim3.pars.verbose = 0
        res = sim3.run().results[sim3.diseases[0].name]
        for key,val in ref.items():
            ours = res[key].values[-1] if ':' not in key else res[key.split(':')[1]].select(population=key.split(':')[0]).values[-1]
            assert np.isclose(ours, val, rtol=1e-6), f'{demo}: {key} is {ours} in {stop}, against {val} in Atomica'
    return

"""
The import in the switching demo for the EMULSION seat (the rest is in Starsim's `tests/switching/test_emulsion.py`): the published herd model, from its original file
"""
import numpy as np
import pytest
import sciris as sc
import starsim as ss
import paths

n_runs = 10 # Runs to average over
ref_quickstart = { # Mean of 200 EMULSION 1.1.1 runs after 53 and 105 steps: LFD examples/emulsion/quickstart/reference/results.csv (switching/emulsion.md, "The first day", gives the 66 at the end)
    53:  dict(total=76.83, J=15.83, M=21.48, I=18.84),
    105: dict(total=65.89, J=6.16, M=10.98, I=18.43),
}


def check_quickstart(msim, age='growth', health='health'):
    """ Compare the mean counts over runs with EMULSION's, within the noise of 10 runs """
    mean = lambda mod, *states: np.sum([np.asarray(msim.results[mod][s].values) for s in states], axis=0).mean(axis=0)
    for k,ref in ref_quickstart.items():
        ours = dict(total=mean(age, 'J', 'A')[k], J=mean(age, 'J')[k], M=mean(health, 'M')[k], I=mean(health, 'I')[k])
        for key,val in ref.items():
            assert abs(ours[key] - val) < 0.1*ref_quickstart[105]['total'], f'After {k} steps, {key} is {ours[key]:.1f} against EMULSION\'s {val}'


@pytest.mark.xfail(reason='The import lists the untranslated parts (cond, when, on_cross, statevars, the calendar; minimum stays are now after=), and warns and hands them to the import-model skill when run (15 animals at the end against 66); a complete import needs after=, escapes, and offspring by prototype, as test_emulsion_quickstart', strict=False)
def test_emulsion_import():
    sc.heading('Testing importing EMULSION\'s quickstart and matching its published output')
    sim = ss.import_from(paths.root/'examples/emulsion/quickstart/original/quickstart.yaml', format='emulsion', verbose=False)
    assert not sim.imported.incomplete, f'{len(sim.imported.incomplete)} parts of the model were not translated'
    check_quickstart(sim.new(verbose=0).run(n_runs=n_runs), age='age_group', health='health_state')

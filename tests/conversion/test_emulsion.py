"""
Test importing EMULSION's own examples against their reference results
"""
import numpy as np
import sciris as sc
import starsim as ss
import paths

kw = dict(verbose=0)


def test_sir():
    sc.heading('Testing EMULSION\'s SIR as compartments, individuals, and hybrid groups, against 200 EMULSION runs')
    folder = paths.root/'examples/emulsion/sir'
    ref = sc.dataframe.read_csv(folder/'reference/results.csv')
    for kind in ['compart', 'IBM', 'hybrid']:
        sir = ss.import_from(folder/f'original/{kind}_SIR.yaml', **kw)
        assert not sir.imported.incomplete and 'n=100;' in repr(sir) # 100 animals, not the default number of agents
        final = sir.run(n_runs=200).results[f'{kind}_SIR'].R.values[:, -1].mean() # With one infected at the start, many runs die out, so the mean needs many
        series = dict(compart='compartment', IBM='ibm', hybrid='hybrid')[kind] + '_R'
        expected = ref[(ref.series == series) & (ref.time == 100)].value.iloc[0]
        rtol = 0.1 if kind == 'compart' else 0.2 # As agents, more runs die out at a daily step (24% of them, against 19% at a tenth of a day), a difference of order dt; the runs that take off agree to within 1%
        assert np.isclose(final, expected, rtol=rtol), f'{kind}: {final} recovered at day 100 against EMULSION\'s {expected}'
    return

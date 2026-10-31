"""
Test importing flepiMoP's examples against their reference results
"""
import numpy as np
import pandas as pd
import tempfile
import sciris as sc
import paths
from starsim.converters.flepimop import load_flepimop

kw = dict(verbose=0)
examples = paths.root/'examples/flepimop' # The originals and their reference results


def reference(folder, series):
    """ A series of the original's reference results, in order of time """
    ref = pd.read_csv(folder / 'reference' / 'results.csv')
    return ref[ref.series == series].sort_values('time').value.values


def test_seir_2pop():
    sc.heading('Testing the flepiMoP two-province SEIR')
    folder = examples / 'seir_2pop'
    sim = load_flepimop(folder / 'original' / 'config_sample_2pop.yml', **kw)
    assert not sim.imported.incomplete
    assert sim.pars.solver == 'ode'
    res = sim.run().results.sample_2pop
    tr = sim.diseases[0].graph.transitions.S_to_E
    assert tr.contact, 'Expected the force of infection to be read as exposure to I'

    # The same numbers as flepiMoP's, in every compartment of every province (both are RK4 with a step of a day)
    for place in ['large_province', 'small_province']:
        for state in 'SEIR':
            ours, theirs = res[state].select(subpop=place).values, reference(folder, f'{place}_{state}')
            assert len(ours) == len(theirs) + 1 # The sim runs through the end date, as flepiMoP does, so its last number is the day after
            assert np.abs(ours[:-1] - theirs).max() < 1e-6, f'{place} {state} differs from the original'

    # Only the places in subpop_setup.selected
    config = sc.loadyaml(folder / 'original' / 'config_sample_2pop.yml')
    for key in ['geodata', 'mobility']:
        config['subpop_setup'][key] = str(folder / 'original' / config['subpop_setup'][key])
    config['initial_conditions']['initial_conditions_file'] = str(folder / 'original' / config['initial_conditions']['initial_conditions_file'])
    config['subpop_setup']['selected'] = ['large_province']
    with tempfile.TemporaryDirectory() as tmp:
        sc.saveyaml(sc.path(tmp) / 'config.yml', config)
        one = load_flepimop(sc.path(tmp) / 'config.yml', **kw)
    assert not one.imported.incomplete
    assert one.pars.total_pop == 9000 # The large province only
    return sim


def test_scenarios():
    sc.heading('Testing flepiMoP scenarios and outcomes, with the original\'s draws')
    folder = examples / 'vaccine_scenarios'
    base = load_flepimop(folder / 'original' / 'config_sample_2pop_vaccine_scenarios.yml', **kw)
    assert set(base.imported.scenarios) == {'no_vax', 'pess_vax', 'opt_vax'}
    skipped = dict(base.imported.incomplete)
    assert 'Ro' not in skipped and 'outcomes: incidCase.probability' in skipped, 'Expected the drawn Ro to be imported with its prior, and the drawn outcome probability listed as not translated'
    assert base.new().init().diseases[0].pars.Ro.prior is not None # So ss.parallel(sim, priors=True) draws it

    # Each scenario, run with the values the original drew for each of its ten runs, has the same mean
    draws = pd.read_csv(folder / 'reference' / 'draws.csv')
    for scen in ['no_vax', 'opt_vax']:
        rows = draws[draws.scenario == scen]
        sims = [base.new(pars=dict(Ro=r.Ro, p_incidCase=r.p_case), interventions=base.imported.scenarios[scen], **kw).run() for r in rows.itertuples()]
        res = [sim.results.sample_2pop for sim in sims]
        for place in ['large_province', 'small_province']:
            for key,theirs in [('V', 'V'), ('I', 'I')]:
                ours = np.mean([r[key].select(subpop=place).values[:-1] for r in res], axis=0)
                assert np.abs(ours - reference(folder, f'{scen}_{place}_{theirs}')).max() < 1e-6
            for key,theirs in [('incidCase', 'incidCase'), ('incidDeath', 'incidDeath'), ('n_incidHosp', 'currHosp')]: # A flow at index k is the number in the step ending on day k; the original's on day k is the number during day k
                ours = np.mean([r[key].select(subpop=place).values[1:] for r in res], axis=0)
                assert np.abs(ours - reference(folder, f'{scen}_{place}_{theirs}')).max() < 1e-6, f'{scen} {place} {key} differs from the original' # Including the end date
    return sims

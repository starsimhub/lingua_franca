"""
Test importing summer2 models against summer2 itself and its example's results
"""
import subprocess
import tempfile
import numpy as np
import pandas as pd
import pytest
import sciris as sc
import starsim as ss
import paths
from starsim.converters.summer2 import load_summer2, outputs

examples = paths.root/'docs/models'
summer2_python = paths.root/'_envs/summer2/bin/python' # summer2's environment, to write a live model with Starsim's summer2.py
kw = dict(verbose=False)

summer2_tb = '''
import sys, json
import numpy as np
import summer2
from summer2.parameters import Parameter
from summer2.functions.time import get_sigmoidal_interpolation_function

def build(): # The TB model of v4_design/oct17/switching/summer2.md: named Parameters, a sigmoidal scale-up of detection, and ages with a plain-array mixing matrix
    m = summer2.CompartmentalModel(times=[1950.0, 2025.0], compartments=list('SELITR'), infectious_compartments=['I'], timestep=1.0)
    m.set_initial_population(distribution={'S': 1e6 - 1000, 'I': 1000})
    beta = Parameter('contact_rate')
    m.add_infection_frequency_flow('infection', beta, 'S', 'E')
    m.add_infection_frequency_flow('reinfection_L', beta*Parameter('rr_reinf'), 'L', 'E')
    m.add_infection_frequency_flow('reinfection_R', beta*Parameter('rr_reinf'), 'R', 'E')
    for name,rate,src,dst in [('stabilisation', 2.0, 'E', 'L'), ('early_activation', 0.2, 'E', 'I'), ('late_activation', 0.002, 'L', 'I'), ('self_recovery', 0.2, 'I', 'R'), ('treatment_end', 2.0, 'T', 'R')]:
        m.add_transition_flow(name, rate, src, dst)
    m.add_transition_flow('detection', get_sigmoidal_interpolation_function([1950.0, 1990.0, 2020.0], [0.0, 0.5, 1.0])*Parameter('detect_max'), 'I', 'T')
    m.add_death_flow('tb_death', 0.2, 'I')
    m.add_universal_death_flows('universal_death', death_rate=1/70)
    m.add_crude_birth_flow('birth', 0.02, 'S')
    ages = ['0', '5', '15', '35', '50', '70']
    strat = summer2.AgeStratification('age', [int(a) for a in ages], list('SELITR'))
    strat.set_mixing_matrix(np.array([[3, 1, 1.5, 1, 0.5, 0.3], [1, 8, 2, 1.5, 0.8, 0.4], [1.5, 2, 5, 2.5, 1.5, 0.6], [1, 1.5, 2.5, 4, 2, 0.8], [0.5, 0.8, 1.5, 2, 3, 1.2], [0.3, 0.4, 0.6, 0.8, 1.2, 2]])/4)
    strat.set_flow_adjustments('early_activation', dict(zip(ages, [summer2.Multiply(3.0), summer2.Multiply(1.5), None, None, None, None])))
    strat.add_infectiousness_adjustments('I', dict(zip(ages, [summer2.Multiply(0.1), summer2.Multiply(0.2), None, None, None, None])))
    m.stratify_with(strat)
    m.request_output_for_flow('notifications', 'detection')
    return m

if __name__ == '__main__': # Write it with Starsim's summer2.py (the file given), then run it and write the compartments at the end and the notifications
    import importlib.util
    spec = importlib.util.spec_from_file_location('starsim_summer2', sys.argv[1]) # By another name, so it doesn't hide summer2 itself
    dumper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dumper)
    pars = json.load(open(f'{sys.argv[2]}/pars.json'))
    dumper.dump(build(), f'{sys.argv[2]}/tb.json', pars=pars)
    m = build()
    m.run(pars)
    comps = {str(c):float(v) for c,v in zip(m.compartments, m.outputs[-1])}
    json.dump(dict(comps=comps, notifications=m.get_derived_outputs_df().notifications.tolist()), open(f'{sys.argv[2]}/ref.json', 'w'))
'''


def summer2_model():
    """ summer2's SEIR by age with a clinical stratification of I only, as summer2.py writes it """
    ages = ['young', 'old']
    clinical = ['asymptomatic', 'symptomatic', 'isolated', 'hospital']
    mult = lambda *v: dict(zip(clinical, [None if x is None else ['multiply', x] for x in v]))
    initial = [dict(name=c, strata=dict(age=a), value=495.0 if c == 'S' else 0.0) for c in 'SER' for a in ages]
    initial += [dict(name='I', strata=dict(age=a, clinical=c), value=5.0 if c == 'asymptomatic' else 0.0) for a in ages for c in clinical]
    return dict(
        format = 'summer2',
        compartments = ['S', 'E', 'I', 'R'],
        infectious = ['I'],
        initial_population = dict(S=990, I=10, E=0, R=0),
        initial = initial,
        times = [0, 20],
        timestep = 0.1,
        flows = [
            dict(name='infection', kind='InfectionFrequencyFlow', sources=['S'], dest='E', param=2.0),
            dict(name='incidence', kind='TransitionFlow', sources=['E'], dest='I', param=0.5),
            dict(name='recovery', kind='TransitionFlow', sources=['I'], dest='R', param=0.3),
            dict(name='infection_death', kind='DeathFlow', sources=['I'], dest=None, param=0.05),
        ],
        stratifications = [
            dict(name='age', strata=ages, compartments=['S', 'E', 'I', 'R'], population_split=dict(young=0.5, old=0.5), flow_adjustments={},
                 infectiousness_adjustments={}, mixing_matrix=None, ageing=False, strain=False),
            dict(name='clinical', strata=clinical, compartments=['I'], population_split=dict(asymptomatic=1.0, symptomatic=0.0, isolated=0.0, hospital=0.0),
                 flow_adjustments=dict(
                     incidence = [dict(adjustments=mult(0.4, 0.3, 0.2, 0.1), source_strata=dict(age='young'), dest_strata={}),
                                  dict(adjustments=mult(0.3, 0.3, 0.2, 0.3), source_strata=dict(age='old'), dest_strata={})],
                     infection_death = [dict(adjustments={**mult(None, None, None, 2.0), 'asymptomatic':['overwrite', 0.0]}, source_strata={}, dest_strata={})],
                 ),
                 infectiousness_adjustments=dict(I=mult(0.5, None, 0.2, 0.1)), mixing_matrix=None, ageing=False, strain=False),
        ],
        outputs = dict(
            incidence_old = dict(request_type='flow', flow_name='incidence', source_strata=dict(age='old'), dest_strata={}),
            hospital_occupancy = dict(request_type='comp', compartments=['I'], strata=dict(clinical='hospital')),
            all_infected = dict(request_type='comp', compartments=['I'], strata={}),
            prop_infected_hosp = dict(request_type='param_func', func='(hospital_occupancy / all_infected)'),
            accum_old = dict(request_type='cum', source='incidence_old'),
        ),
    )


def test_summer2_reference():
    sc.heading('Testing a summer2 model against the original results')
    res = load_summer2(summer2_model(), **kw).run().results.summer2
    folder = f'{examples}/summer2/seir-age-clinical'
    ref = pd.read_csv(f'{folder}/reference/results.csv')
    theirs = ref[ref.series == 'I_old_hospital'].value.values
    assert np.abs(res.I.select(age='old', clinical='hospital').values - theirs).max() < 0.01, 'Should agree with summer2'
    return


@pytest.mark.skipif(not summer2_python.exists(), reason='needs the summer2 environment')
def test_summer2_live():
    sc.heading('Testing a live summer2 model, written by summer2 itself')
    with tempfile.TemporaryDirectory() as tmp:
        tmp = sc.path(tmp)
        sc.savetext(tmp/'tb.py', summer2_tb)
        sc.savejson(tmp/'pars.json', dict(contact_rate=10.0, rr_reinf=0.21, detect_max=1.5))
        subprocess.run([str(summer2_python), '-I', str(tmp/'tb.py'), str(sc.path(ss.converters.__file__).parent / 'summer2.py'), str(tmp)], check=True, capture_output=True)
        tb = load_summer2(str(tmp/'tb.json'), **kw)
        ref = sc.loadjson(tmp/'ref.json')
    assert not tb.imported.incomplete
    tbres = tb.run().results.summer2
    levels = dict(zip(['0', '5', '15', '35', '50', '70'], ['0-4', '5-14', '15-34', '35-49', '50-69', '70+'])) # summer2's age groups, as Starsim labels them
    for c,val in ref['comps'].items():
        state, age = c.split('Xage_')
        ours = tbres[state].select(age=levels[age]).values[-1]
        assert np.isclose(ours, val, rtol=1e-3), f'{c} in 2025 should agree with summer2' # The sigmoid is sampled every tenth of a step
    notif = outputs(tb).notifications
    for year in [1990, 2010, 2024]:
        assert np.isclose(notif[year - 1950], ref['notifications'][year - 1950], rtol=0.005), f'Notifications in {year} should agree with summer2' # summer2's is the mean of the rates at either end of the year
    return

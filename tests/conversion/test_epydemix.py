"""
Test importing epydemix's example against its reference results
"""
import os
import numpy as np
import pandas as pd
import pytest
import sciris as sc
import starsim as ss
import paths
from starsim.converters.epydemix import load_epydemix

lf = paths.root/'docs/models' # The original examples
kw = dict(verbose=False)


def test_kenya():
    sc.heading('Testing importing the epydemix SIR in Kenya against the original')
    folder = f'{lf}/epydemix/sir_kenya/reference'
    if not os.path.exists(folder):
        pytest.skip('needs the reference results of the example')
    pop = sc.loadjson(f'{folder}/population.json')
    d = dict(
        format = 'epydemix',
        name = 'sir',
        compartments = ['Susceptible', 'Infected', 'Recovered'],
        transitions = [dict(source='Susceptible', target='Infected', kind='mediated', params=['transmission_rate', 'Infected']),
                       dict(source='Infected', target='Recovered', kind='spontaneous', params='recovery_rate')],
        parameters = dict(transmission_rate=dict(kind='number', value=0.04), recovery_rate=dict(kind='number', value=0.1)),
        population = dict(name='Kenya', groups=pop['groups'], Nk=pop['Nk'], contacts=pop['contacts']),
        run = dict(start_date=pop['start'], end_date=pop['end'], dt=1.0, initial=pop['initial']),
    )
    sim = load_epydemix(d, **kw)
    msim = ss.parallel(sim, n_runs=200) # Restarted in this process; enough runs that the mean is within about 1% of the true one
    ours = msim.results.epydemix.Infected.mean() # Over the runs
    ref = pd.read_csv(f'{folder}/results.csv')
    theirs = ref[ref.series == 'Infected_total'].sort_values('time').value.values
    diff = np.abs(ours - theirs).max()/theirs.max()
    assert diff < 0.03, f'Expected the mean number infected within 3% of the original, not {diff:.1%}'
    return sim

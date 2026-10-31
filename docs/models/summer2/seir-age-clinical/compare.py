"""
Compare the Starsim version with the reference results of the original

    python compare.py
"""
import os
import sys
import numpy as np
import starsim as ss

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools
from model import sim

example = here
ref = {k:np.array(v[1]) for k,v in tools.read_results(example).items()}
ages = ['young', 'old']
clinical = ['asymptomatic', 'symptomatic', 'isolated', 'hospital']
names = dict(zip(clinical, ['Ia', 'Is', 'Ii', 'Ih'])) # As four states


def flow(values):
    """ A flow in each step as summer2 reports it: a rate per unit of time, at the end of the step (as Starsim's is, so the first, at the start, is 0) """
    return values/0.1


def start():
    """ The number in I at the start, by age and clinical status """
    return sim.new(verbose=0).init().diseases.seir.I.values.reshape(len(ages), len(clinical))


def as_states():
    """ The same model with the clinical statuses as four states, started as the stratified model is, as a check of the stratification """
    S, E, Ia, Is, Ii, Ih, R = ss.states('S E Ia Is Ii Ih R')
    starts = start()
    init = {names[c]:ss.by(age=[starts[i, j] for i in range(len(ages))]) for j,c in enumerate(clinical)} # As counts in each age group
    seir = ss.Disease(
        infection  = S >> E @ 2 * (0.5*Ia + Is + 0.2*Ii + 0.1*Ih),
        a          = E >> Ia @ 0.5 * ss.by(age=[0.4, 0.3]),
        s          = E >> Is @ 0.5 * ss.by(age=[0.3, 0.3]),
        i          = E >> Ii @ 0.5 * ss.by(age=[0.2, 0.2]),
        h          = E >> Ih @ 0.5 * ss.by(age=[0.1, 0.3]),
        recovery   = Ia + Is + Ii + Ih >> R @ 0.3,
        death      = Is + Ii >> ss.null @ 0.05,
        hosp_death = Ih >> ss.null @ 0.1,
        init_n     = init,
        name       = 'seir',
    )
    return ss.Sim(seir.stratify(age=ages), total_pop=1000, dt=0.1, stop=20, verbose=0).run().results.seir


if __name__ == '__main__':
    res = sim.new(verbose=0).run().results.seir

    # Compartments, by age and clinical status
    ours = dict()
    for age in ages:
        for state in 'SER':
            ours[f'{state}_{age}'] = res[state].select(age=age).values # A stock at index k is the number at the original's time k
        for name in clinical:
            ours[f'I_{age}_{name}'] = res.I.select(age=age, clinical=name).values
    stocks = {k:np.abs(v - ref[k]).max() for k,v in ours.items()}

    # The derived outputs: summer2's flows are rates, and its cumulative deaths sum those rates without multiplying by the step, so are 10 times the deaths
    hosp = res.I.select(clinical='hospital').values
    outputs = dict(hospital_occupancy=hosp, prop_infected_hosp=hosp/res.I.values, notifications=flow(res.incidence.select(clinical=['isolated', 'hospital']).values))
    for age in ages:
        outputs[f'accum_death_{age}'] = res.infection_death.cum.select(age=age).values / 0.1
        outputs[f'incidence_{age}'] = flow(res.incidence.select(age=age).values)
        for name in clinical:
            outputs[f'incidence_{age}_{name}'] = flow(res.incidence.select(age=age, clinical=name).values)
    for name in clinical:
        outputs[f'incidence_{name}'] = flow(res.incidence.select(clinical=name).values)
    assert sorted(outputs) == sorted(k for k in ref if k not in ours), 'Every output of the original should be compared'
    rel = {k:np.abs(v - ref[k]).max()/np.abs(ref[k]).max() for k,v in outputs.items()}
    for label,d,unit in [('compartment', stocks, ' people (of 1,000)'), ('derived output', rel, ' of its peak')]:
        worst = max(d, key=d.get)
        print(f'largest difference in any {label}: {d[worst]:.3g}{unit} ({worst})')
    end = {k:abs(v[-1] - ref[k][-1])/abs(ref[k][-1]) for k,v in (ours | outputs).items()}
    print(f'largest difference at time 20: {max(end.values()):.1%} ({max(end, key=end.get)})')
    assert max(stocks.values()) < 0.0006 and max(rel.values()) < 6e-5, 'The ODE no longer agrees with the original'
    print(f'starting in I: {start().sum(axis=0).round(2)}; the original starts everyone asymptomatic')

    # The stratification against the same model as four states, from the same start
    states = as_states()
    check = max(np.abs(res.I.select(age=a, clinical=c).values - states[names[c]].select(age=a).values).max() for a in ages for c in clinical)
    print(f'stratified against four states, from the same start: {check:.2g} people')
    assert check < 1e-10, f'The stratified model and the four states differ by {check:.2g} people'

    # The stochastic runs: the epidemic is still rising at time 20, and a mean over runs that take off at different times lags the ODE, so the end of the epidemic is the fair check
    long = sim.new(verbose=0, stop=100).run().results.seir.R[-1]
    for solver,n_runs in [('binomial', 100), ('abm', 20)]:
        pars = dict(n_agents=1000) if solver == 'abm' else {}
        at_20 = ss.parallel(sim.new(verbose=0, solver=solver, **pars), n_runs=100, parallel=False).results.seir.R.values[:, -1]
        at_100 = ss.parallel(sim.new(verbose=0, solver=solver, stop=100, **pars), n_runs=n_runs, parallel=False).results.seir.R.values[:, -1]
        print(f'{solver}: recovered at time 20 {at_20.mean():.0f} ± {at_20.std()/10:.0f} (ODE {res.R[-1]:.0f}); at time 100 {at_100.mean():.0f} (ODE {long:.0f})')
        assert abs(at_100.mean()/long - 1) < 0.01, f'{solver} ends with {at_100.mean():.0f} recovered, the ODE {long:.0f}'
        assert at_20.min() > 0 and abs(at_20.mean()/res.R[-1] - 1) < 0.1, f'{solver} has {at_20.mean():.0f} recovered at time 20, the ODE {res.R[-1]:.0f}'

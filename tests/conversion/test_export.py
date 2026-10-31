"""
Test that what `ss.export_to()` writes is read and run by the tools it is written for

Starsim's own tests read an export back with `ss.import_from()`, which shows only that
Starsim agrees with itself. These give the same files to the other tools, in their own
environments (`_envs/odin` and `_envs/sbml`; see `_envs/README.md`):

- odin compiles the file and integrates it
- libSBML validates the file, and libRoadRunner and COPASI each integrate it

Each trajectory is then compared with Starsim's own run of the model, by state. A model that
an export changes (stratified, here) is only checked to load and run.

    cd tests/conversion && pytest test_export.py
"""
import os
import json
import warnings
import subprocess
import pytest
import numpy as np
import pandas as pd
import sciris as sc
import starsim as ss

here = sc.thispath(__file__)
envs = here.parent.parent / '_envs'
odin_exe = envs / 'odin/bin/Rscript'
sbml_exe = envs / 'sbml/bin/python'
rtol = 1e-4 # Each tool's integrator, and Starsim's, is good to about this
atol_varying = 0.5 # In people: Starsim holds a value that varies in time through each step, and the tools follow it continuously; the gap goes as dt^2
atol = 1e-3 # In people
timeout = 300


def sir_disease(name='sir', beta=0.3):
    S, I, R = ss.states('S I R')
    return ss.Disease(infection=ss.Transition(S, I, rate=ss.perday(beta)*I), recovery=ss.Transition(I, R, dur=ss.days(7)), init_prev=0.01, name=name)


def sir():
    return ss.Sim(sir_disease(), total_pop=1000, unit='day', stop=60, verbose=0)


def seird():
    """ Births, deaths from every state, a branch, and a lognormal dwell time written as Erlang stages """
    S, E, I, R, D = ss.states('S E I R D')
    dis = ss.Disease(
        births    = ss.birth(S, rate=ss.peryear(0.02)),
        infection = ss.Transition(S, E, rate=ss.perday(0.4)*I),
        onset     = ss.Transition(E, I, dur=ss.days(4)),
        outcome   = ss.Transition(I, [R, D], dur=ss.lognorm_ex(ss.days(8), ss.days(3)), p=[None, 0.1]),
        deaths    = ss.death([S, E, I, R], rate=ss.peryear(0.01)),
        init_prev = 0.01, name='seird')
    return ss.Sim(dis, total_pop=1e5, unit='day', stop=120, verbose=0)


def weekly():
    """ Rates given per day, in a sim that counts in weeks """
    return ss.Sim(sir_disease(beta=0.04), total_pop=1000, unit='week', stop=40, verbose=0)


def yearly():
    """ Rates per year and dwell times in months, with waning """
    S, I, R = ss.states('S I R')
    dis = ss.Disease(infection=ss.Transition(S, I, rate=ss.peryear(30)*I.frac), recovery=ss.Transition(I, R, dur=ss.months(1)), waning=ss.Transition(R, S, dur=ss.years(2)), init_prev=0.01, name='endemic')
    return ss.Sim(dis, total_pop=1e4, unit='year', stop=20, verbose=0)


def two_diseases():
    """ Two diseases in one file, whose names are prefixed """
    return ss.Sim([sir_disease('flu', 0.5), sir_disease('cold', 0.3)], total_pop=1000, unit='day', stop=60, verbose=0)


def math_rate():
    """ A fraction and functions in a rate, one of which has another name in odin """
    S, I, R = ss.states('S I R')
    dis = ss.Disease(infection=ss.Transition(S, I, rate=ss.perday(0.5)*I.frac*np.maximum(np.exp(-2*I.frac), 0.2)), recovery=ss.Transition(I, R, rate=ss.perday(0.1)), init_prev=0.01, name='behavior')
    return ss.Sim(dis, total_pop=1000, unit='day', stop=60, verbose=0)


def agents():
    """ An agent-based sim, which is written as its compartmental form """
    return ss.Sim(sir_disease(), networks='random', n_agents=500, unit='day', stop=30, verbose=0)


def stratified():
    """ Stratified by age, which an export sums into one group """
    return ss.Sim(sir_disease(), total_pop=1000, stratify=dict(age=[0, 18]), unit='day', stop=30, verbose=0)


def seasonal():
    """ A rate that varies with time, which is not a number """
    S, I, R = ss.states('S I R')
    dis = ss.Disease(infection=ss.Transition(S, I, rate=ss.seasonal(ss.perday(0.3), amplitude=0.2, peak=0.1)*I), recovery=ss.Transition(I, R, dur=ss.days(7)), init_prev=0.01, name='seasonal')
    return ss.Sim(dis, total_pop=1000, unit='day', stop=60, verbose=0)


def dated_seasonal():
    """ A cycle by the calendar, starting partway through a year """
    S, I, R = ss.states('S I R')
    dis = ss.Disease(infection=ss.Transition(S, I, rate=ss.seasonal(ss.perday(0.3), amplitude=0.5, peak='July')*I), recovery=ss.Transition(I, R, dur=ss.days(7)), waning=ss.Transition(R, S, dur=ss.days(180)), init_prev=0.01, name='dated')
    return ss.Sim(dis, total_pop=1000, unit='day', start='2020-04-01', stop='2021-04-01', verbose=0)


def timeseries(mode, period=None):
    """ A rate given at some times, in each way of going between them """
    def make():
        S, I, R = ss.states('S I R')
        beta = ss.timeseries([0, 20, 40], [ss.perday(0.4), ss.perday(0.1), ss.perday(0.3)], mode=mode, period=period)
        dis = ss.Disease(infection=ss.Transition(S, I, rate=beta*I), recovery=ss.Transition(I, R, dur=ss.days(7)), init_prev=0.01, name='series')
        return ss.Sim(dis, total_pop=1000, unit='day', stop=100, verbose=0)
    make.__name__ = f'timeseries_{mode}' + ('_period' if period else '')
    return make


timeseries_cases = [timeseries('constant'), timeseries('linear'), timeseries('cosine'), timeseries('linear', ss.days(50))]


def route_betas():
    """ A beta for each of two pools """
    S, I, R = ss.states('S I R')
    dis = ss.Disease(infection=ss.Transition(S, I, rate=dict(home=ss.perday(0.1), work=ss.perday(0.05))*I), recovery=ss.Transition(I, R, dur=ss.days(7)), init_prev=0.01, name='routes')
    return ss.Sim(dis, networks=[ss.MixingPool(n_contacts=3, name='home'), ss.MixingPool(n_contacts=8, name='work')], total_pop=1000, unit='day', stop=40, verbose=0)


def contact_matrix():
    """ Contacts by age, whose mean is written, with the groups summed """
    S, I, R = ss.states('S I R')
    dis = sir_disease()
    return ss.Sim(dis, networks=ss.MixingPools(n_contacts=np.array([[4.0, 2.0], [2.0, 3.0]]), src=dict(young=ss.AgeGroup(0, 18), old=ss.AgeGroup(18, None)), dst=dict(young=ss.AgeGroup(0, 18), old=ss.AgeGroup(18, None))), total_pop=1000, stratify=dict(age=[0, 18]), unit='day', stop=30, verbose=0)


exact = [sir, seird, weekly, yearly, two_diseases, math_rate, agents, seasonal, dated_seasonal, *timeseries_cases, route_betas] # An export carries these in full
loads = [stratified, contact_matrix] # An export sums the groups of these, so they are only checked to load and run
cases = [pytest.param(case, id=case.__name__) for case in exact + loads]


def export(make, format, path):
    """ Write a sim to a file; returns the sim, its compartmental form as flat data, and the file """
    sim = make()
    file = path / {'sbml':'model.xml', 'odin':'model.R'}[format]
    with warnings.catch_warnings(): # What is lost is tested in Starsim's own tests
        warnings.simplefilter('ignore', ss.errors.LossyExport)
        ss.export_to(sim, format, filename=file, verbose=False)
        flat = ss.converters.export.flatten(sim)
    return sim, flat, file


def reference(sim):
    """ Starsim's trajectories by state, under the names they have in an export """
    sim, _ = ss.converters.export.compartmental(sim)
    sim.run()
    many = len(sim.diseases) > 1
    out = {}
    for dis in sim.diseases():
        for state in dis.graph.states:
            out[f'{dis.name}_{state}' if many else state] = np.array(sim.results[dis.name][state])
    return out


def compare(table, ref, stages, tool, atol=atol):
    """ Check a tool's trajectories against Starsim's, adding up the stages of a state """
    for name,values in ref.items():
        if name in table:
            got = table[name].values
        else:
            got = sum(table[n].values for n in stages[name].split(' + '))
        assert len(got) == len(values), f'{tool}: {name} has {len(got)} points, not {len(values)}'
        assert np.allclose(got, values, rtol=rtol, atol=atol), f'{tool}: {name} differs by up to {np.abs(got-values).max():n}, of {np.abs(values).max():n}'


def steps(sim):
    """ The number of whole units of time in a sim """
    return ss.converters.export.initialized(sim).t.npts - 1


def tolerance(make):
    """ How closely, in people, a model should match Starsim's run """
    return atol_varying if make in [seasonal, dated_seasonal, *timeseries_cases] else atol


def run(cmd):
    """ Run a command with one thread, and fail with what it printed """
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    done = subprocess.run([str(c) for c in cmd], cwd=here, env=env, capture_output=True, text=True, timeout=timeout)
    assert done.returncode == 0, f'{cmd[0]} failed:\n{done.stdout[-3000:]}\n{done.stderr[-3000:]}'
    return done.stdout


@pytest.mark.parametrize('make', cases)
def test_odin(make, tmp_path):
    if not odin_exe.exists():
        pytest.skip('needs _envs/odin: lingua_franca envs install odin')
    sim, flat, file = export(make, 'odin', tmp_path)
    n = steps(sim)
    run([odin_exe, 'run_odin.R', file, n, tmp_path/'out.csv'])
    table = pd.read_csv(tmp_path/'out.csv')
    assert np.isfinite(table.values).all()
    if make in exact:
        compare(table, reference(sim), flat.exprs, 'odin', atol=tolerance(make))


@pytest.mark.parametrize('make', cases)
def test_sbml(make, tmp_path):
    if not sbml_exe.exists():
        pytest.skip('needs _envs/sbml: lingua_franca envs install sbml')
    sim, flat, file = export(make, 'sbml', tmp_path)
    n = steps(sim)
    errors = json.loads(run([sbml_exe, 'run_sbml.py', file, n, tmp_path/'out']).splitlines()[-1])
    assert not errors, '\n'.join(errors)
    for tool in ['roadrunner', 'copasi']:
        table = pd.read_csv(tmp_path/f'out_{tool}.csv')
        assert np.isfinite(table.values).all(), tool
        if make in exact:
            compare(table, reference(sim), flat.exprs, tool, atol=tolerance(make))

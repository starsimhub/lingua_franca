"""
The parts of the switching demo for the SimInf seat that read SimInf's own herds and register (the rest is in Starsim's `tests/switching/test_siminf.py`)
"""
import numpy as np
import pandas as pd
import sciris as sc
import starsim as ss
import paths
import timing

v4_build, v4_run = 2.0, 3.0 # Starsim's build and run of the herds ten times over, in s, normalized to the reference machine (see timing.py), 2026-10-25
ref_build, ref_run = 2.1, 1.9 # SimInf's time to build and run its herds and events ten times over (16,000 herds, 4,666,920 events, four years) on one thread: switching/siminf.md, "The second week" §2
ref_S100 = [199_906, 199_855, 200_057] # SimInf, 1,600 herds: susceptible on day 100, mean and 5% to 95% range of 200 runs (LFD examples/siminf/sir_herds/reference/results.csv), as in vignettes/siminf/sir_herds/README.md
ref_herds100 = [2.0, 0, 3] # The same for the number of herds infected on day 100


def read_register(ref, copies=1, stop=None):
    """ SimInf's herds and events as a register, replicated so many times (as its s3_scale.R), each copy with one infected animal in its first herd, as in the original """
    u0, events = pd.read_csv(ref/'u0.csv'), pd.read_csv(ref/'events.csv.gz')
    if stop is not None:
        events = events[events.time <= stop]
    n = len(u0)
    u0 = pd.concat([u0.assign(node=u0.node + i*n) for i in range(copies)], ignore_index=True)
    events = pd.concat([events.assign(node=events.node + i*n, dest=np.where(events.dest > 0, events.dest + i*n, events.dest)) for i in range(copies)], ignore_index=True)
    register = pd.DataFrame({'date': events.time, 'from': events.node.where(events.event != 'enter'), 'n': events.n,
                             'to': events.node.where(events.event == 'enter', events.dest.where(events.event == 'extTrans')),
                             'states': (events.event == 'enter').map({True:'S', False:None})})
    return u0, register


def make_herds(u0, register, stop, **kwargs):
    """ SimInf's SIR in herds, linked by the register """
    S, I, R = ss.states('S I R')
    sir = ss.Disease(infection=ss.Transition(S, I, rate=ss.perday(0.16) * I), recovery=ss.Transition(I, R, rate=ss.perday(0.01)),
                     init_n=dict(I=ss.by(herd=u0.I.values)), name='sir')
    size = u0[['S', 'I', 'R']].sum(axis=1)
    sir.stratify(herd=list(u0.node.astype(str)), kind='space', split=size/size.sum(), mobility=ss.geo.Mobility(data=register))
    return ss.Sim(sir, solver='gillespie', unit='day', start=0, stop=stop, total_pop=size.sum(), verbose=0, **kwargs)


def test_siminf_register():
    sc.heading('SimInf\'s 1,600 herds and their register, for the first 100 days')
    res = make_herds(*read_register(paths.root/'examples'/'siminf'/'sir_herds'/'reference', stop=100), stop=100).run().results.sir
    S100, herds100 = res.S.values[100], (np.asarray(res.I.strata)[100] > 0).sum()
    assert ref_S100[1] <= S100 <= ref_S100[2], f'Susceptible on day 100: {S100:,.0f}, SimInf {ref_S100[0]:,} ({ref_S100[1]:,} to {ref_S100[2]:,})'
    assert ref_herds100[1] <= herds100 <= ref_herds100[2], f'Herds infected on day 100: {herds100}, SimInf {ref_herds100}'
    return res


def test_siminf_scale():
    sc.heading('SimInf\'s herds and events ten times over: 16,000 herds and 4.7 million events, for four years')
    u0, register = read_register(paths.root/'examples'/'siminf'/'sir_herds'/'reference', copies=10) # Reading and converting the data is not timed, as in SimInf
    build, sim = timing.timed(lambda: make_herds(u0, register, stop=1460).init(), repeats=2) # Exact, as SimInf (about 6 million events): herds that do not affect each other are always run exactly
    run, _ = timing.timed(sim.run, repeats=1)
    herds = (np.asarray(sim.results.sir.I.strata)[-1] > 0).sum()
    print(f'{herds:,} herds infected at the end')
    timing.check(build, v4_build, 'Built', other=(ref_build, 'SimInf'), slowdown=3) # It has to run on a busy machine, so only a large slowdown fails
    timing.check(run, v4_run, 'Run', other=(ref_run, 'SimInf'), slowdown=3)
    assert herds > 5000 # About 1,250 of each copy's 1,600 when infection takes off there (as at 1,600 herds), which it does in most
    return sim

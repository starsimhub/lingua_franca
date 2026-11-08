"""
The SimInf herds example (docs/models/siminf/sir_herds), in Starsim: an SIR in each of 1,600 cattle
herds, linked only by a register of animals entering, leaving, and moving between herds
"""
import os
import pandas as pd
import starsim as ss

ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reference')
u0 = pd.read_csv(os.path.join(ref, 'u0.csv'))
events = pd.read_csv(os.path.join(ref, 'events.csv.gz'))

# SimInf's events as a register: entering animals are susceptible, and the others are chosen from every state
register = pd.DataFrame({
    'date':   events.time,
    'from':   events.node.where(events.event != 'enter'),
    'to':     events.node.where(events.event == 'enter', events.dest.where(events.event == 'extTrans')),
    'n':      events.n,
    'states': (events.event == 'enter').map({True:'S', False:None}),
})

S, I, R = ss.states('S I R')
sir = ss.Disease(
    infection = S >> I @ ss.perday(0.16) * I,
    recovery  = I >> R @ ss.perday(0.01),
    init_n    = dict(I=ss.by(herd=u0.I.values)),
)
size = u0[['S', 'I', 'R']].sum(axis=1)
sir.stratify(herd=ss.levels(dict(zip(u0.node.astype(str), size/size.sum())), kind='space', mobility=ss.geo.register(register)))
sim = ss.Sim(sir, solver='gillespie', unit='day', start=0, stop=1460, total_pop=size.sum())

if __name__ == '__main__':
    sim.run()
    sim.plot()

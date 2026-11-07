"""
The SimInf SISe3 example (docs/models/siminf/sise3), in Starsim: an SIS in three age categories in each
of 1,600 cattle herds, where animals are infected from an environmental infectious pressure that
the infected shed into and that decays by season, with a register of births, deaths, movements, and
aging between age categories
"""
import os
import numpy as np
import pandas as pd
import starsim as ss

ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reference')
u0 = pd.read_csv(os.path.join(ref, 'u0.csv'))
events = pd.read_csv(os.path.join(ref, 'events.csv.gz'))

# SimInf's events as a register: entering animals are S_1; the others are chosen from one age category (select 4 to 6),
# and internal transfers (shift 1 or 2) move them up an age category in their herd, keeping S or I
ages = events['select'].map({4:'S_1,I_1', 5:'S_2,I_2', 6:'S_3,I_3'})
register = pd.DataFrame({
    'date':      events.time,
    'from':      events.node.where(events.event != 'enter'),
    'to':        events.node.where(events.event.isin(['enter', 'intTrans']), events.dest.where(events.event == 'extTrans')),
    'n':         events.n,
    'states':    ages.where(events.event != 'enter', 'S_1'),
    'to_states': events['shift'].map({1:'S_2,I_2', 2:'S_3,I_3'}),
})

S_1, I_1, S_2, I_2, S_3, I_3 = ss.states('S_1 I_1 S_2 I_2 S_3 I_3')
phi = ss.State(people=False) # The environmental infectious pressure
# SimInf updates phi once a day, to phi*(1 - b) + alpha*I/n, with b by season; the continuous rates that give the same phi
# at the end of each day are a decay of -log(1 - b) and a shedding of alpha*(-log(1 - b))/b
upsilon, gamma, alpha = ss.perday(0.018), ss.perday(0.1), 1.0
seasons = {0: 0.1, 181: 0.125, 364: 0.1} # SimInf's daily decay by the day that ends a step, here by the day that starts it, in its 365-day year
rate = {day:-np.log(1 - b) for day,b in seasons.items()}
beta  = ss.timeseries({day:ss.perday(rate[day]) for day in seasons}, period=ss.days(365))
shed  = ss.timeseries({day:ss.perday(alpha*rate[day]/b) for day,b in seasons.items()}, period=ss.days(365))
sise3 = ss.Disease(
    infection_1 = S_1 >> I_1 @ upsilon * phi.n,
    recovery_1  = I_1 >> S_1 @ gamma,
    infection_2 = S_2 >> I_2 @ upsilon * phi.n,
    recovery_2  = I_2 >> S_2 @ gamma,
    infection_3 = S_3 >> I_3 @ upsilon * phi.n,
    recovery_3  = I_3 >> S_3 @ gamma,
    shedding    = ss.outside >> phi @ shed * (I_1 + I_2 + I_3).n / (S_1 + I_1 + S_2 + I_2 + S_3 + I_3).n,
    decay       = phi >> ss.dead @ beta,
    init_n      = {key:ss.by(herd=u0[key].values) for key in ['I_1', 'S_2', 'S_3']}, # The rest in S_1
)
size = u0[['S_1', 'I_1', 'S_2', 'S_3']].sum(axis=1)
sise3.stratify(herd=list(u0.node.astype(str)), kind='space', fractions=size/size.sum(), states=[S_1, I_1, S_2, I_2, S_3, I_3, phi], mobility=ss.geo.Mobility(data=register))
sim = ss.Sim(sise3, total_pop=size.sum(), solver='gillespie', unit='day', start=0, stop=1460)

if __name__ == '__main__':
    sim.run()
    sim.plot()

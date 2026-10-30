"""
The MEmilio age-resolved SECIR example (examples/memilio/secir_ageres), in Starsim: the SECIR of
examples/memilio/secir in three age groups, with seasonality, a cut in contacts, and symptomatic
people who infect more once testing and tracing is overwhelmed
"""
import numpy as np
import starsim as ss

beta     = ss.seasonal(mean=0.05, amplitude=0.2, peak=ss.days(-60)) # Highest on 1 Jan; day 0 is 2 Mar
contacts = ss.timeseries({0: 1.0, 29: 1.0, 30: 0.3}, mode='cosine') # Cut by 70% over day 29, as MEmilio's damping
S, E, INS, ISy, ISev, ICr, R = ss.states(7)
excess = np.clip((0.91/2*INS.n - 35)/(5*35 - 35), 0, 1) # People becoming symptomatic each day, beyond the 35 that can be traced (to 5 times that)
risk = 0.35 - 0.1*np.cos(np.pi*excess) # So symptomatic people infect more: from 0.25 to 0.45, along half a cosine

secir = ss.Disease(
    infection = S >> E @ beta * contacts * (0.7 * INS + risk * ISy),
    onset     = E >> INS @ ss.days(3.2),
    symptoms  = ss.Transition(INS, [ISy, R], dur=ss.days(2), p=[0.91, 0.09]),
    severe    = ss.Transition(ISy, [ISev, R], dur=ss.days(5.8), p=[0.2, 0.8]),
    critical  = ss.Transition(ISev, [ICr, R], dur=ss.days(9.5), p=[0.25, 0.75]),
    recovery  = ss.Transition(ICr, R, dur=ss.days(7.1), p=0.7),
    death     = ss.Transition(ICr, ss.null, dur=ss.days(7.1), p=0.3),
    init_n    = dict(E=100, INS=50, ISy=50, ISev=20, ICr=10, R=10),
)
secir.stratify(age=['0', '1', '2']) # Three groups of equal size, each with a third of every state
mixing = ss.contacts(np.full((3, 3), 10/3)) # 10 contacts a day, spread evenly over the groups
sim = ss.Sim(secir, networks=mixing, total_pop=10_000, stop=ss.days(50))

if __name__ == '__main__':
    sim.run()
    sim.plot()

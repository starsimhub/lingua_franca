"""
The MEmilio simple SECIR example (docs/models/memilio/secir), in Starsim: infection, then a chain of
increasingly severe states, each of which some people leave by recovering
"""
import starsim as ss

contacts = ss.timeseries({0: 1.0, 29: 1.0, 30: 0.1}, interpolation='cosine') # Cut by 90% over day 29, as MEmilio's damping
S, E, INS, ISy, ISev, ICr, R = ss.states(7)

secir = ss.Disease(
    infection = S >> E @ contacts * (0.67 * INS + 0.25 * ISy),
    onset     = E >> INS @ ss.days(3.2),
    symptoms  = ss.Transition(INS, {ISy: 0.91, R: None}, dur=ss.days(2)),
    severe    = ss.Transition(ISy, {ISev: 0.2, R: None}, dur=ss.days(6)),
    critical  = ss.Transition(ISev, {ICr: 0.25, R: None}, dur=ss.days(12)),
    recovery  = ss.Transition(ICr, R, dur=ss.days(8), p=0.7),
    death     = ss.Transition(ICr, ss.dead, dur=ss.days(8), p=0.3),
    init_n    = dict(E=100, INS=50, ISy=50, ISev=20, ICr=10, R=10),
)
sim = ss.Sim(secir, total_pop=83_000, stop=ss.days(100))

if __name__ == '__main__':
    sim.run()
    sim.plot()

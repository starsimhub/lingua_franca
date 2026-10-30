"""
The Atomica SIR demo (examples/atomica/sir), in Starsim: infection through a number of contacts
per year, recovery, and deaths, stepped a year at a time
"""
import starsim as ss

transpercontact = ss.par(0.008, doc='Transmission probability per contact')
contacts        = ss.par(80,    doc='Number of contacts annually')
susdeath        = ss.par(ss.peryear(0.008), doc='Death rate for susceptible people')
infdeath        = ss.par(ss.peryear(0.016), doc='Death rate for infected people, in addition')

sus, inf, rec, dead = ss.states(4)
prev = inf.n / (sus + inf + rec).n
foi  = (1 - (1 - prev * transpercontact)**contacts) * (1 - susdeath)

sir = ss.Disease(
    infection  = sus >> inf @ foi,
    recovery   = inf >> rec @ ss.years(5),
    death      = sus + inf + rec >> dead @ susdeath,
    inf_death  = inf >> dead @ infdeath,
    init_n     = dict(sus=700, inf=285.71429, rec=14.28571),
)
sim = ss.Sim(sir, total_pop=1000, start=2000, stop=2023, integrator='euler', substeps=1) # Atomica takes one Euler step a year

if __name__ == '__main__':
    sim.run()
    sim.plot()

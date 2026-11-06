"""
The epidemics "Get started" vignette (docs/models/epidemics/seirv), in Starsim: the default
model, an SEIR in three age groups of the UK mixing by a contact matrix from POLYMOD, with
R0 = 1.3, a latent period of 2 days, and an infectious period of 7, over 600 days
"""
import numpy as np
import starsim as ss

matrix = np.array([[7.883663, 3.157024, 3.084747], [2.764179, 4.854839, 4.570735], [1.557728, 2.636148, 5.005571]]) # Contacts a day
N = [14865748, 16978469, 29438434] # Aged 0-19, 20-39, and 40+, as the vignette prints them

S, E, I, R = ss.states(4)
seir = ss.Disease(
    infection = S >> E @ 1.3/7/max(np.linalg.eigvals(matrix).real) * I, # R0 = 1.3
    onset     = E >> I @ ss.days(2),
    recovery  = I >> R @ ss.days(7),
    init_n    = dict(I=1e-6*sum(N)),
)
seir.stratify(age=[0, 20, 40], fractions=N)
sim = ss.Sim(seir, networks=ss.contacts(matrix), total_pop=sum(N), unit='day', stop=600)

if __name__ == '__main__':
    sim.run()
    sim.plot()

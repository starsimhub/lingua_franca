from epipack import EpiModel
import matplotlib.pyplot as plt
import numpy as np

S, I, R = list("SIR")
N = 1000

SIRS = EpiModel([S,I,R],N)\
    .set_processes([
        #### transmission process ####
        # S + I (eta=2.5/d)-> I + I
        (S, I, 2.5, I, I),

        #### transition processes ####
        # I (rho=1/d)-> R
        # R (omega=1/14d)-> S
        (I, 1, R),
        (R, 1/14, S),
    ])\
    .set_initial_conditions({S:N-10, I:10})

t = np.linspace(0,40,1000) 
result_int = SIRS.integrate(t)
t_sim, result_sim = SIRS.simulate(t[-1])

for C in SIRS.compartments:
    plt.plot(t, result_int[C])
    plt.plot(t_sim, result_sim[C])

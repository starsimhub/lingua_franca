"""
Ebola with community, hospital, and burial transmission (Legrand et al. 2007): the Starsim version of the Pandemic Simulator's port

The values are those of the example, for Kikwit in 1995. The shares theta and delta are what the
paper sets; the rates of each exit from I and H are derived from them, as in the paper.
"""
import starsim as ss

S, E, I, H, F, R = ss.states('S E I H F R')
betaI, betaH, betaF = ss.par(0.084), ss.par(0.113), ss.par(1.093)
alpha, gamma_f = ss.par(1/7), ss.par(1/2)
gamma_h, gamma_i, gamma_d = ss.par(1/5), ss.par(1/10), ss.par(1/9.6)
theta, delta = ss.par(0.80), ss.par(0.81)

gamma_ih = 1/(1/gamma_i - 1/gamma_h)
gamma_dh = 1/(1/gamma_d - 1/gamma_h)
delta1 = delta*gamma_i/(delta*gamma_i + (1 - delta)*gamma_d)
delta2 = delta*gamma_ih/(delta*gamma_ih + (1 - delta)*gamma_dh)
weight = theta*(gamma_i*(1 - delta1) + gamma_d*delta1)
theta1 = weight/(weight + (1 - theta)*gamma_h)

ebola = ss.Disease(
    infection = S >> E @ (betaI*I + betaH*H + betaF*F),
    onset     = E >> I @ alpha,
    admitted  = I >> H @ (gamma_h*theta1),
    recovered = I >> R @ (gamma_i*(1 - theta1)*(1 - delta1)),
    died      = I >> F @ (gamma_d*(1 - theta1)*delta1),
    discharged = H >> R @ (gamma_ih*(1 - delta2)),
    died_in_hospital = H >> F @ (gamma_dh*delta2),
    buried    = F >> R @ gamma_f,
    init_n    = dict(I=3),
    name      = 'ebola',
)
measures = [
    ss.modify(ebola.pars[name], multiply=factor, when=ss.schedule(start='1995-05-04'), name=name)
    for name,factor in [('betaI', 0.88), ('betaH', 0), ('betaF', 0)]
]
sim = ss.Sim(ebola, interventions=measures, total_pop=200_000, start='1995-01-06', stop='1996-01-06', dt=ss.days(1), solver='ode', verbose=0)
control = sim.new(interventions=None)

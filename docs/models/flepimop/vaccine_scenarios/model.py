"""
The flepiMoP vaccination scenarios (docs/models/flepimop/vaccine_scenarios), in Starsim: the SEIR in two
provinces with vaccination and waning, three scenarios that switch parts of it off, reported cases,
hospitalizations, and deaths, and ten runs of each with uncertain R0 and case detection
"""
import starsim as ss

pop     = dict(large_province=9000, small_province=1000)
commute = [[0, 100/9000], [20/1000, 0]] # The share of each province's residents who go to the other
gamma   = 1/5

Ro         = ss.par(2.5, prior=ss.truncnorm(loc=2.5, scale=0.1, low=1.1, high=3))
p_case     = ss.par(0.5, prior=ss.truncnorm(loc=0.5, scale=0.05, low=0.3, high=0.7))
nu_pess    = ss.par(0.01)
nu_opt     = ss.par(0.03)
omega_pess = ss.par(0.02)
omega_opt  = ss.par(0.01)

S, E, I, R, V = ss.states('S E I R V')
infection   = S >> E @ Ro*gamma*I
onset       = E >> I @ 1/4
recovery    = I >> R @ gamma
vaccination = S >> V @ nu_pess + nu_opt
waning      = V >> S @ omega_pess + omega_opt
cases       = ss.outcome(p_case*onset, delay=ss.days(5))
hosp        = ss.outcome(0.05*onset, delay=ss.days(7), stay=ss.constant(10, unit='days'))
deaths      = ss.outcome(0.2*hosp, delay=ss.days(14))
transitions = [infection, onset, recovery, vaccination, waning]
seir = ss.Disease(*transitions, cases, hosp, deaths, init_n=dict(E=ss.by(patch=[5, 0])))
away = [[0.5*share for share in row] for row in commute] # Travelers are away for half the day
seir.stratify(patch=list(pop), fractions=list(pop.values()), mobility=ss.geo.Mobility(matrix=away, kind='visit'))
sim = ss.Sim(seir, total_pop=sum(pop.values()), start='2020-02-01', stop='2020-08-31', substeps=1) # One RK4 step a day, as in the original

# The scenarios: each switches off one vaccination program or both (Starsim's stop is the first day off)
off = lambda par: ss.modify(par, multiply=0, start='2020-02-01', stop='2020-09-01')
pess_vax  = [off(nu_opt), off(omega_opt)]
opt_vax   = [off(nu_pess), off(omega_pess)]
scenarios = dict(no_vax=pess_vax + opt_vax, pess_vax=pess_vax, opt_vax=opt_vax)


def runs(n_runs=10, **kwargs):
    """ Every scenario, once with each of n_runs draws from the priors """
    draws = ss.fit.prior_draws(sim, n_runs, seed=1)
    return [sim.new(label=name, pars=dict(Ro=r, p_case=p), interventions=mods, **kwargs)
            for name,mods in scenarios.items() for r,p in zip(draws['Ro'], draws['p_case'])]


if __name__ == '__main__':
    msim = ss.parallel(runs(), parallel=False)
    msim.plot()

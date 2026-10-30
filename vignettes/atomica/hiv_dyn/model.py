"""
The Atomica dynamic HIV demo (examples/atomica/hiv_dyn), in Starsim: the HIV care cascade in
females and males, with births, new infections, testing, linkage, treatment, viral suppression,
loss to follow-up, and deaths, stepped a year at a time; and seven programs whose spending sets
the coverage that changes five of its parameters, under three budgets
"""
import numpy as np
import starsim as ss

sex = lambda f, m: ss.by(sex=[f, m])
sus, undx, dx, linked, tx, lost, vs, dead_hiv, dead_other = ss.states('sus undx dx linked tx lost vs dead_hiv dead_other')

# The databook: in 2016, the number alive, living with HIV, diagnosed, ever in care, in care, treated, and suppressed
cascade = np.array([[28514100, 27395900], [3390000, 2540000], [2440800, 1676400], [2237400, 1384300],
                    [2034000, 1092200], [1728900, 939800], [1017000, 508000]])
# Workaround: Atomica solves for the compartments from the cascade
init = dict(zip(['sus', 'undx', 'dx', 'lost', 'linked', 'tx', 'vs'], -np.diff(cascade, axis=0, append=0)))
births       = sex(287_992.41, 276_698.59)
num_acq      = sex(150_000, 110_000)
num_test     = sex(6_400_000, 3_600_000)
num_initiate = sex(269_448, 179_632)
mort         = 0.015 # Background mortality, per year, as are all the rates

# The progbook: each program's unit cost ($ a person), spending ($ a year), and who it reaches, in both sexes
programs = ss.par(0, doc='Whether the programs set the parameters they affect')
budget   = ss.par(1, doc='Spending, relative to the progbook')
progs = dict(
    clinics  = (5,    42e6,  sus + undx), # Testing
    outreach = (10,   16e6,  sus + undx),
    sameday  = (200,  60e6,  dx + linked), # Initiation counseling
    classic  = (300,  45e6,  dx + linked),
    tracing  = (60,   0.6e6, tx + lost), # Client tracing
    advanced = (150,  0.6e6, tx + lost), # Adherence support
    whatsapp = (0.05, 10e3,  tx + lost),
)
# What a program reaches is shared by everyone eligible in both sexes: .total, where .n is the count in one's own sex
cov = {k: np.minimum(budget*spend/cost/eligible.total, 1) for k,(cost,spend,eligible) in progs.items()}

# Under the programs, a parameter is its baseline plus each program's coverage times its effect (the test yield, which nothing uses then, is left out)
outcome = lambda base, **effects: sex(*base) + sum(cov[k]*(sex(*v) - sex(*base)) for k,v in effects.items())
switch = lambda before, after: (1 - programs)*before + programs*after
pos_test  = num_test*undx.n/(undx + sus).n
acq       = num_acq/np.maximum(sus.n, num_acq)
diag      = switch(pos_test/np.maximum(undx.n, pos_test), outcome([0, 0], clinics=[0.99]*2, outreach=[0.99]*2))
link_time = switch(sex(0.7, 1.2), outcome([1.5, 2.2], clinics=[0.5, 0.6], outreach=[0.3, 0.4], tracing=[0.2, 0.3]))
initiate  = switch(num_initiate/np.maximum(linked.n, num_initiate), outcome([0, 0], sameday=[0.98, 0], classic=[0.92, 0]))
loss      = switch(sex(0.2, 0.3), outcome([0.5, 0.7], advanced=[0.1, 0.15], whatsapp=[0.2, 0.25]))
fail      = switch(0.16, outcome([0.3, 0.4], advanced=[0.1, 0.15], whatsapp=[0.15, 0.2]))


hiv = ss.Disease(
    birth      = ss.null >> sus @ births,
    acq        = sus >> undx @ acq,
    diag       = undx >> dx @ diag,
    link       = dx + lost >> linked @ 1/link_time,
    initiate   = linked >> tx @ initiate,
    loss       = linked + tx + vs >> lost @ loss,
    supp       = tx >> vs @ ss.years(0.2),
    fail       = vs >> tx @ fail,
    death_hiv  = undx + dx + linked + lost >> dead_hiv @ 0.053,
    death_tx   = tx >> dead_hiv @ 0.0258534,
    death_vs   = vs >> dead_hiv @ 0.01219,
    death      = sus + undx + dx + linked + tx + lost + vs >> dead_other @ mort,
    plhiv      = undx + dx + linked + tx + lost + vs,
    diagnosed  = dx + linked + tx + lost + vs,
    treated    = tx + vs,
    init_n     = {k: sex(*v) for k,v in init.items()},
)
hiv.stratify(sex=['females', 'males'], kind='space', split=cascade[0]) # A place, so that .n is the count in each sex
# One step a year, in which Atomica moves at most everyone out of a compartment
sim = ss.Sim(hiv, total_pop=cascade[0].sum(), start=2016, stop=2035, integrator='euler', substeps=1)

# The budget scenarios: the programs act from 2019, and the budget is doubled or cut to nothing from 2020
on = ss.timeseries({2016: 0, 2019: 1})
budgets = dict(default=1, doubled=2, zero=0)
scenarios = {f'{k}_budget': dict(programs=on, budget=ss.timeseries({2016: 1, 2020: v})) for k,v in budgets.items()}

if __name__ == '__main__':
    msim = ss.parallel(baseline=sim, **{k:sim.new(pars=v) for k,v in scenarios.items()}, parallel=False)
    msim.plot()

---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Costing specification

A proposed specification for costs and health economic outcomes in Starsim v4: where costs attach to a model, how DALYs and QALYs are computed, how results are discounted, and how scenarios become cost-effectiveness results.

> **Note:** This is a proposal drawn from the review in this folder. It is not part of the [design](../design/README.md), and nothing here has been decided. It is written in the design's style (MUST, SHOULD, and MAY where a requirement is real; code against `import starsim as ss`) so that it can be moved there if accepted.
>
> **What exists today.** Starsim v4 has `cost=` on products, and a smaller version of this idea in its library: `ssl.Costs` (costs per event and fixed costs), `ssl.DALYs`, `ssl.ICER`, and `ssl.discount()`, shown in [Costs](https://starsim.org/v4/user_guide/library_econ.html). None of `ss.Economics`, `ss.dalys`, `ss.qalys`, `sims.cea()`, or `draws=` exists; parameter draws today are `ss.parallel(..., priors=True)`. The code below is a sketch of what could come next, and only its use of existing names has been checked against v4.

Justified by the review in this folder: [README.md](README.md) for the main findings, [metrics.md](metrics.md) for definitions and formulas, and [cea-software.md](cea-software.md#cross-cutting-patterns) for the API patterns.

## Principles

Each principle is a finding of the review, turned into a decision.

1. **The model counts; the economics layer values.** During the run, the library records quantities: events, person-time in states, deliveries, and deaths with their ages. Money and health weights are applied to those quantities, and discounting is applied after the run. Unit costs and discount rates can then be changed without re-running. This is how OpenMalaria, malariasimulation, tbvax, TLO, and IMPACT NCD work, and why OpenMalaria removed its in-model cost hooks.
2. **Costs attach to things the model already has.** A cost is declared against a transition, an outcome, a state, or a delivery, which already have names and results. There is no separate cost model to keep in step with the disease model, and no tunnel states to stand in for transition costs (heemod's workaround).
3. **Four ways of attaching cover nearly everything:** per event, per unit of time in a state, fixed or one-off, and by a person's history. The first three are declarations; the fourth is a function.
4. **Typed time does the unit checking.** A cost per event is a number; a cost per time in a state is a rate (`ss.peryear(1200)`). Annual costs applied per month and utilities summed as if they were QALYs, the commonest errors in [cea-software.md](cea-software.md#cross-cutting-patterns), cannot happen silently.
5. **Unit costs and weights are parameters.** They are `ss.par` values with a `source` and, if uncertain, a `prior`. So they appear in `describe()`, can be loaded from a table, and are drawn in the same probabilistic sensitivity analysis (PSA) as the epidemiological parameters.
6. **The DALY is one recipe among several.** Burden is weighted person-time plus weighted deaths. DALYs and QALYs are two named configurations of that, with the life table, the comorbidity rule, and the timing of attribution as explicit options.
7. **Perspectives are separate sums, not one total.** Costs are kept by category; a perspective names which categories it sums. Health-system and societal totals are then two results, never one number with an implied choice.
8. **Averted quantities come from paired scenarios.** Scenarios share common random numbers ([11-random.md](../design/11-random.md#common-random-numbers)), and incremental costs and effects are computed per paired run, never as the difference of two independent averages.
9. **The output is a long table.** Scenario × draw × run × time × stratum, with a column per quantity. This is what VIMC, dampack, BCEA, voi, and hesim consume, so a library that emits it gets their analyses for free.
10. **In-loop costing is only for when money changes what happens.** Budgets that set coverage (Optima, Atomica) and finite stock (STIsim) are the exceptions. They are deferred, apart from the `capacity=` that deliveries already have.

## The whole interface

```python
import starsim as ss

# --- the disease, as in the design --------------------------------------------
S, I, R = ss.states(3)
infection = S >> I @ ss.perday(0.2) * I
recovery  = I >> R @ ss.days(10)
death     = I >> ss.null @ ss.perday(0.0001)
hosp      = ss.outcome(0.08 * infection, delay=ss.days(4), duration=ss.days(6))
flu = ss.Disease(infection, recovery, death, hosp)

# --- an intervention, with a cost per dose -------------------------------------
vaccine = ss.Vaccine(efficacy=0.6, waning=ss.years(1), cost=ss.par(3.50, source='UNICEF supply catalogue 2025'))
vx = ss.vaccinate(vaccine, coverage=0.5, at=[2026, 2027, 2028], where=ss.ppl.age >= 65)

# --- the economics: what is costed, and how health is valued -------------------
c_hosp = ss.par(1800, prior=ss.gamma(mean=1800, std=400), source='National tariff 2024, DRG 112')
econ = ss.Economics(
    currency   = 'USD',
    price_year = 2025,
    costs = dict(
        hospital = c_hosp * hosp,                         # per admission
        illness  = ss.peryear(250) * I,                   # per year spent infected (outpatient care)
        delivery = 0.80 * vx.delivered,                   # per dose delivered, on top of the dose itself
        program  = ss.peryear(400_000),                   # fixed: management, cold chain, training
        launch   = {2026: 1_500_000},                     # one-off: introduction cost
    ),
    effects = ss.dalys(weights={I: 0.051, hosp: 0.133}, life_table='gbd2019'),
)

kw   = dict(n_agents=100_000, start=2025, stop=2035, analyzers=econ)
sims = ss.parallel(baseline=ss.Sim(flu, **kw), vaccine=ss.Sim(flu, interventions=vx, **kw), draws=200, n_runs=5)

ce = sims.cea(ref='baseline', discount=0.03, threshold=1000)   # ICERs, dominance, net benefit, from the paired runs
ce.plot()                                                       # the cost-effectiveness plane
ce.ceac(thresholds=range(0, 5000, 100)).plot()                  # the acceptability curve
ce.to_df()                                                      # costs and effects by scenario and draw, with the drawn parameters
sims.diff('baseline').econ.cost.resample('year')                # budget impact: undiscounted annual cost difference
```

Everything after `econ = ...` is described below. What the example does not need, it does not say: there is one perspective (all costs), the base year for discounting is the start of the sim, and comorbidity uses the GBD's multiplicative rule. `describe()` prints each of these as a guess.

## Where costs attach

A cost is an amount of money times a quantity the model already produces. The kind of quantity decides what the amount means.

| Attachment | Written as | The amount is | Examples |
|---|---|---|---|
| **Per event** | a number times a flow: a transition, an outcome, or a delivery's `delivered` | money per event | a test, a dose, an admission, a treatment start, a death |
| **Per time in a state** | a rate times a state, or times an outcome that has a `duration` | money per person per unit time | a year on ART, a day in hospital, the annual cost of a prevalent condition |
| **Fixed or one-off** | a rate alone, or a dict of times to amounts | money per unit time, or money at a time; these have no strata | program management, staff, an introduction cost, equipment |
| **By history** | a function of the sim | whatever the function returns for the step | the last year of life before a cancer death; a cost that depends on time since diagnosis |

These are the same weighted sums that results and outcomes already use ([09-results.md](../design/09-results.md#ratios-and-combinations)), with one addition: a rate times a state is accumulated over person-time. So `c_hosp * hosp + ss.peryear(250) * I` is one cost with two parts, and it is a result like any other.

**Products keep `cost=`.** A product's `cost=` is per delivery, as now. Every delivery whose product has a cost contributes a category named after the delivery (`vx` above), so the dose cost in the example is counted without being written again. The extra `delivery` cost is there because the cost of giving a dose (staff time, transport) is often costed separately from the dose itself.

**A number times a state is an error.** It has no meaning without a time unit: 250 per what? `CostNeedsRate` says so and suggests `ss.peryear(250) * I`. A rate times a flow is an error for the same reason in reverse (`WrongDimension`, which exists already).

**Fixed and one-off costs.** A rate on its own is a cost that accrues whether or not anything happens: `ss.peryear(400_000)` is 400,000 a year, spread over the steps. It takes the forms a parameter takes ([04-parameters.md](../design/04-parameters.md#the-ladder)), so a fixed cost that changes in time is `ss.timeseries({2026: 400_000, 2029: 150_000})` inside the rate. A dict of times to amounts is paid at those times: `{2026: 1_500_000}` is paid at the first time point in 2026.

**Capacity.** A delivery with `capacity=` reports the capacity as a result (`vx.capacity`), so a cost per unit of capacity provided rather than used is a rate times that result: `ss.peryear(30) * art.capacity` costs every slot available, whether or not anyone filled it. This is how TLO costs staff (by headcount, not minutes used) and how PTTI costs labs.

**By history.** A function of the sim returns the cost for the current step. It is tried on what the solver provides, by the design's [try-it rule](../design/03-states-and-transitions.md#functions-in-any-slot): a function that needs per-agent histories runs only as agents.

```python
def end_of_life(sim, uids):
    """The last year of life before a cancer death costs 30,000 a year more than the continuing phase"""
    cc = sim.diseases.cancer
    dying = cc.ti_dead.notnan() & (cc.ti_dead - sim.ti < ss.years(1) / sim.dt)
    return ss.peryear(30_000) * dying[uids]

econ = ss.Economics(costs=dict(terminal=end_of_life, continuing=ss.peryear(4_000) * cancer.diagnosed))
```

**State-of-the-world costs.** The costs that dominate pandemic economics (lost output from closures, lost schooling) attach to the level of a policy, not to people. The best of those models use one parameter for both transmission and output ([pandemics-and-frameworks.md](pandemics-and-frameworks.md#cross-cutting-patterns)); here the cost reads the same modifier that changes the contacts, so the two cannot disagree (`active`, for whether a modifier is on, is a placeholder):

```python
closure = ss.modify(school.pars.n_contacts, multiply=0.2, when=many_cases)
econ = ss.Economics(costs=dict(schooling=lambda sim: ss.peryear(8e9) * closure.active))   # value of a school year, while schools are closed
```

## `ss.Economics`

```python
ss.Economics(
    costs        = None,    # dict: category -> a cost (above)
    effects      = None,    # an effect recipe (ss.dalys, ss.qalys) or a dict of them
    currency     = None,    # a currency code, for labels
    price_year   = None,    # the year the unit costs are expressed in
    perspectives = None,    # dict: perspective -> the cost categories it sums; default one perspective, 'total'
    base_year    = None,    # the year discounting starts from; default the start of the sim
)
```

`ss.Economics` is an analyzer: a module that reads the sim and changes nothing in it ([01-objects.md](../design/01-objects.md)). It is passed with `analyzers=`, its results live under its name (`sim.results.econ`), and it runs under every solver. A sim MAY have more than one, for two analyses that should not be mixed (a health-sector CEA and a macroeconomic one).

- **`costs`** maps a category name to a cost. Categories are kept apart in the results, so the same run can produce a program budget, a CEA total, and a table of costs by type.
- **`currency` and `price_year`** are labels. The library does not convert currencies or inflate prices, because the right way to do so depends on the analysis ([metrics.md](metrics.md#currency-year-inflation-ppp-and-exchange-rates)); unit costs are given in one currency and price year, and the source of each is on its `ss.par`. Both are printed by `describe()` and on every cost plot. Without them, `describe()` notes that costs are unlabeled.
- **`perspectives`** names sums of categories: `perspectives=dict(health_system=['hospital', 'illness', 'vx', 'delivery', 'program'], societal='all')`. Financial versus economic cost (donated drugs, volunteer time) is another pair of perspectives, not a separate tag. Every perspective is a result (`sim.results.econ.health_system`); the default single perspective is `total`.
- **`base_year`** is the time from which discounting counts (the year of introduction, in tbvax). It does not change any undiscounted result.

## Unit costs are parameters

Every amount in a cost can be an `ss.par` ([04-parameters.md](../design/04-parameters.md#sspar)), and SHOULD be one when it comes from somewhere:

```python
c_test = ss.par(4.00, prior=ss.gamma(mean=4.00, std=0.80), source='WHO-CHOICE 2021, Kenya, primary care', doc='rapid test, including consumables')
```

- **`source`** answers the reviewer's first question, and `describe()` lists every unit cost with its value, source, currency, and price year: the costing inputs table that agencies used to Excel submissions expect, and what CHEERS 2022 asks to be reported.
- **`prior`** is the uncertainty used by the PSA ([below](#uncertainty)). A gamma for costs and a beta for utilities and weights are the conventions.
- **Values kept outside the model.** Unit costs come from a table as other parameters do, with `ss.Sim(pars='costs_kenya.csv')`. A file with columns for name, value, prior, and source is the `treasure` and TB-Speed pattern: every unit cost editable, documented, and versioned, with defaults.
- **`ss.by`** gives costs that vary by stratum (`ss.by(age=[12, 25])` for a pediatric and an adult dose), and `ss.timeseries` gives costs that change in time (a drug that comes off patent).

A cost amount MUST NOT be a distribution over agents (variation between people) unless it is used inside a function; a unit cost is one number that is uncertain, not a number that differs per person. `ss.gamma(...)` given directly as an amount raises `CostIsDistribution`, which suggests `ss.par(value, prior=...)`.

## Health effects

Every summary measure of health in [metrics.md](metrics.md#health-outcome-measures) is weighted person-time plus weighted deaths. The library has one mechanism for that and two named recipes on top of it.

### The general form

A weight per unit time in a state is a rate, so person-time weighted by a disability weight is written exactly like a cost per time in a state: `ss.peryear(0.051) * I` is the YLD from `I`, because a disability weight is years of healthy life lost per year lived. An effect that is not a DALY or QALY is this alone:

```python
econ = ss.Economics(effects=dict(heavy_infection_years=ss.peryear(1) * schisto.heavy))    # what schistosomiasis modelers use instead of DALYs
```

### `ss.dalys`

```python
ss.dalys(
    weights      = None,       # dict: state or outcome -> disability weight (a number, ss.par, or ss.by)
    life_table   = 'gbd2019',  # remaining life expectancy at death: a named table, a number (a fixed life expectancy), or ss.by(age=...)
    deaths       = None,       # which deaths count; default every death transition in every disease
    combine      = 'multiply', # several weights at once: 'multiply' (GBD), 'add' (capped at 1), or 'max'
)
```

It produces three results: `yld`, `yll`, and `dalys`, their sum.

- **YLD is prevalence-based**: person-time in each weighted state times its weight. It accrues in the year it is lived, and stops at death, so there is no YLD after death to correct for.
- **YLL is counted at death**: each death adds the remaining life expectancy at that age, from the life table. The whole of it is attributed to the step of the death, including the years that fall after the end of the sim; this is the standard definition and `describe()` states it. The table is interpolated at the exact age (agents) or at the mean age within each age group (compartmental), never read at the start of an age band, which overstates YLL by up to half a band.
- **`life_table`** is a named table from `starsim_data` (the GBD 2019 reference life table, `'gbd2019'`, pulled and cached as other named data are ([04-parameters.md](../design/04-parameters.md#named-data))), the country's own life table (`ss.lifetable('Kenya', year=2024)`, which is a value judgment and is printed as one), a number, which is a fixed life expectancy (Optima and HIV Synthesis use 80: YLL is 80 minus the age at death, or 0), a duration, which is the remaining years assumed for every death whatever its age (`ss.years(30)`), or any value by age.
- **`deaths`** defaults to every transition to `ss.null` in every disease, each attributed to the disease it belongs to. So deaths from background mortality (a demographics module) are not counted. A list of transitions or outcomes narrows it.
- **`weights`** keys are states, outcomes with a `duration` (whose `n_` series is the number currently in them), or conditions. Their sources are GBD rounds, and the round SHOULD be in the `ss.par`'s source.
- **`combine`** is the comorbidity rule, for a person in several weighted states at once (two diseases, or a disease and a sequela). Agents combine per person each step; a compartmental run combines per compartment, which is exact within one disease and assumes independence across diseases (printed).

DALYs are not discounted or age-weighted here. Both are analysis choices ([below](#discounting-and-timing)).

### `ss.qalys`

```python
ss.qalys(
    utilities = None,          # dict: state or outcome -> utility (1 = full health, 0 = dead)
    baseline  = 1.0,           # the utility of people not in any listed state; ss.by(age=...) for population norms
    combine   = 'multiply',    # 'multiply', 'min' (HIV Synthesis), or 'add' (decrements from baseline)
)
```

QALYs are person-time alive weighted by utility, and death enters only through the time not lived within the horizon. The result is `qalys`. The baseline SHOULD decline with age (EQ-5D population norms), and `describe()` notes when it is 1.0 for everyone, since a flat baseline overstates the QALYs gained by extending life at older ages.

**Life-years** are `ss.qalys()` with no utilities: person-time alive. They are not a third recipe.

An acute event with a utility loss (a hospitalization) is a state or an outcome with a `duration`, so the duration is stated where the loss is. A loss per event with no duration is not accepted, because it hides an assumed duration.

## Results

`ss.Economics` produces, under its name:

- one result per cost category (`sim.results.econ.hospital`), per perspective (`total`, or the names given), and per effect (`dalys`, `yll`, `yld`, `qalys`, or the names given);
- each as a flow: the amount accrued in the step that ends at each time point, by the design's results convention ([09-results.md](../design/09-results.md#automatic-results)), so `cum_` versions exist and `.resample('year')` sums;
- each undiscounted, with its time, so that any discount rate can be applied later and budget impact can use the series as it is;
- each with the dimensions of the quantities it was computed from, so costs and DALYs by age, sex, place, or an equity attribute are `.select()` and `.by()` on the result, as for any other ([09-results.md](../design/09-results.md#selecting-strata)). Costs by income quintile need the model to be stratified by income quintile and nothing more.

The quantities the costs were computed from are results already (flows, state counts, deliveries), and the module keeps the person-time and deaths-by-age it computed. So unit costs and weights can be changed after the run without re-running it:

```python
econ = sim.analyzers.econ
econ.evaluate(pars=dict(c_hosp=2100))    # recompute every cost and effect from the stored quantities, with this value
```

`evaluate` returns new results and leaves the run's own unchanged. It cannot change anything that needs the run: which deaths count, which states are weighted, and, under agents, the comorbidity rule, which is applied per person during the run.

**Expected values.** OpenMalaria's `expectedDirectDeaths` adds up probabilities instead of realized events, which steadies the denominator of an ICER in a small stochastic run. Whether effects should be able to accumulate this way is open ([below](#open-questions)).

## Discounting and timing

Discounting is applied after the run, by the functions that compute decision results (`sims.cea()`, `econ.discounted()`), never during it. One run can then serve several rates: 3% for both (iDSI, WHO-CHOICE), 3.5% (NICE), 3% for costs and 0% for effects (Policy1-Cervix), and 0% for budget impact.

```python
sims.cea(ref='baseline', discount=0.03)                                  # costs and effects at 3%
sims.cea(ref='baseline', discount=dict(costs=0.03, effects=0.0))         # differential
econ.discounted(rate=[0, 0.03, 0.035])                                   # several at once: a rate dimension on every result
```

The rules, from [metrics.md](metrics.md#discounting):

- **The discount factor is continuous**, with $\rho = \ln(1+r)$ for an annual rate $r$, counted from `base_year`. Using $e^{-rt}$ with the annual rate is a known error and is not done.
- **A flow over a step** is discounted by its average over the step, $e^{-\rho t}(1 - e^{-\rho\Delta})/(\rho\Delta)$, not at the start or the end of the step. With yearly steps at 3%, that is a difference of about 1.5% a year.
- **YLL is discounted over the years lost**, as $e^{-\rho t_d}(1 - e^{-\rho L})/\rho$ for a death at $t_d$ with remaining life expectancy $L$. To make this possible at any rate after the run, `ss.dalys` keeps, for each step, the deaths binned by remaining life expectancy in one-year bins, not only their sum.
- **Person-time within a step.** Under the ODE and Gillespie solvers person-time is integrated exactly. Under the discrete solvers it is the trapezoid of the counts at the two time points, which is the half-cycle correction done once, by the library, and printed by `describe()`. Costs per event are never corrected this way: an event is counted in the step it happens in.
- **The horizon** is the end of the sim unless `horizon=` is given to the analysis (`sims.cea(..., horizon=2035)`). Costs and person-time stop at the horizon; YLL already counts life after it, and the output says so. Extrapolation beyond the horizon (the remaining discounted life expectancy of everyone alive at the end, for QALYs and life-years) is deferred.

## Scenarios and decision results

Scenarios are sims, as in [08-interventions.md](../design/08-interventions.md#scenarios), and the baseline is what is really in place. Nothing new is needed to run them. Incremental costs and effects are differences of paired runs: with common random numbers, run 3 of `vaccine` is compared with run 3 of `baseline`, so the difference is the effect of the intervention and not noise.

```python
ce = sims.cea(
    ref       = 'baseline',   # the comparator; default the first scenario
    cost      = 'total',      # the perspective; default the first one
    effect    = 'dalys',      # the effect; default the first one. DALYs are averted, QALYs gained
    discount  = 0.03,         # a rate, or dict(costs=, effects=); default 0, printed
    threshold = None,         # willingness to pay per unit of effect, for net benefit; a number or a list
    horizon   = None,         # default the end of the sim
    reference = None,         # a named reference case: 'idsi', 'who-choice', 'nice', 'gbd'
)
```

`ce` holds, for each scenario:

- total cost and effect, and the increments over the comparator, as means over runs with intervals;
- the efficiency frontier and the ICER of each scenario against the next one on it, with strongly and extendedly dominated scenarios marked `D` and `ED`. This is dampack's `calculate_icers()` algorithm, borrowed and not reinvented ([cea-software.md](cea-software.md#dampack-and-the-darth-tutorials));
- net monetary benefit and net health benefit at each threshold.

The rules that are easy to get wrong are done once, in the library:

- **An ICER is a ratio of means, never a mean of ratios.** Increments are averaged over runs (and over draws, for a PSA) before dividing.
- **A negative ICER is not reported as a number.** A scenario that costs less and does more dominates, and is labeled so.
- **ICERs are against the next-best scenario on the frontier**, not each against the baseline. `ce.vs('baseline')` gives the pairwise comparison with one scenario for generalized CEA (WHO-CHOICE's null scenario), and is labeled as such.
- **Cost per case averted, per death averted**, and the like are `ce` with `effect=` naming a flow (`effect='infection'`). They are labeled as intermediate outcomes and are not given a threshold.

**Reference cases.** `reference='idsi'` sets the options that reference case fixes (3% for both, DALYs, a health-system perspective if one is named so) and prints what it set, so the configuration is named, swappable, and reported. Anything also given explicitly overrides it, with a note. A reference case is a convenience: none is the default, because none is right for every analysis.

**Budget impact** needs no function: it is the undiscounted cost difference by year, for the paying perspective, which `sims.diff()` already gives ([08-interventions.md](../design/08-interventions.md#scenarios)):

```python
sims.diff('baseline').econ.health_system.resample('year')
```

**Benefit-cost analysis and ROI.** Monetized benefits (averted treatment costs, productivity, a VSL per death) are costs with the opposite sign in a separate perspective, so benefit-cost ratios and ROI are arithmetic on two perspectives. Which valuation of a life is used (VSL per death, value of a life year, QALYs at a threshold) is the user's, and VSL and human-capital productivity for the same deaths SHOULD NOT both be counted ([metrics.md](metrics.md#benefit-cost-analysis-roi-and-vsl)); the library cannot detect it.

## Uncertainty

A probabilistic sensitivity analysis is a set of parameter draws, each run under every scenario. The draw is shared across scenarios, and so are the random numbers within it.

```python
sims = ss.parallel(baseline=base, vaccine=vacc, draws=500)              # 500 draws from the priors
sims = ss.parallel(baseline=base, vaccine=vacc, draws=fit, n_runs=5)    # draws from a calibration's posterior, five runs each
```

- **`draws=`** on `ss.parallel` takes a number (draws from the `prior` of every `ss.par` that has one, epidemiological and economic alike), or a calibration result (its posterior draws, [13-inference.md](../design/13-inference.md#the-result), with economic parameters drawn from their priors). Parameters without a prior keep their value.
- **Draws and runs are separate dimensions.** In a stochastic model, `n_runs` per draw separates parameter uncertainty from chance; the decision-relevant quantity is the mean over runs at each draw, and that is what `ce` uses ([metrics.md](metrics.md#probabilistic-sensitivity-analysis-psa)).
- **The draws are kept.** The MultiSim stores the drawn parameter values as a table with one row per draw, so every output can be matched to the inputs that produced it.
- **Correlated parameters** are drawn jointly when their priors are given as one multivariate distribution (`ss.par` on a vector), as heemod's `define_correlation()` does.

`ce.ceac(thresholds)` gives the acceptability curve (the share of draws in which each scenario has the highest net benefit), and `ce.plot()` the cost-effectiveness plane with one point per draw.

### Value of information

Value of information asks what it would be worth to know more before deciding: everything (EVPI), some parameters exactly (EVPPI), or what a particular study would show (EVSI). Definitions are in [metrics.md](metrics.md#value-of-information). All three are computed from the PSA that has already been run, with no further simulation, by the regression methods that voi and BCEA use.

```python
ce.evpi()                                          # per person affected by the decision, at each threshold
ce.evppi(pars=['c_hosp', 'efficacy'])              # one value for this group of parameters
ce.evppi(pars=['c_hosp', 'efficacy'], each=True)   # one value per parameter
ce.evsi(study=trial, n=[100, 500, 2000])           # one value per sample size
ce.evpi(population=2e6, years=10)                  # population value: per person, times the discounted number of people affected
```

- **The input is net benefit by draw and scenario**, at the thresholds given to `sims.cea()` (or `threshold=` here, which overrides them). In a stochastic model, net benefit is first averaged over the runs within each draw. Without that, chance would look like uncertainty that information could remove, and the values would be too high. With one run per draw, `VOINoisy` says so.
- **`evpi()`** is the mean over draws of the best scenario's net benefit, minus the best mean net benefit. It is exact given the draws.
- **`evppi(pars=)`** regresses each scenario's net benefit on the named parameters over the draws, and uses the fitted values in place of the inner expectation ([Strong, Oakley and Brennan 2014](https://doi.org/10.1177/0272989X13505910)). `method='gam'` (a generalized additive model, the default for up to four parameters) or `method='gp'` (a Gaussian process, the default above four) is chosen and printed. `pars=` takes names of drawn parameters, as listed in `ce.to_df()`; a parameter that was not drawn has no uncertainty and raises `NotDrawn`.
- **`evsi(study=, n=)`** needs a model of the proposed study: a function that takes one draw's parameters and a sample size and returns the summary statistics the study would report (a trial's observed efficacy, a survey's prevalence). Net benefit is regressed on the simulated statistics, as for EVPPI ([Strong et al. 2015](https://doi.org/10.1177/0272989X15575286)). The study function is the user's, because no library can know what study is proposed; for the two standard cases, `study='binomial'` and `study='normal'` with `pars=` take the place of a function, as voi's built-in designs do.
- **Results are values at each threshold**, with `.plot()` drawing EVPI against willingness to pay, EVPPI as a bar per parameter or group, and EVSI against sample size. They are in the same units as net benefit (money, or health with `effect=`'s units for net health benefit).
- **Accuracy is reported.** Each EVPPI and EVSI carries the standard error of its regression estimate, and `FewDraws` notes when there are too few draws for the number of parameters (fewer than about 500 for a GAM, or fewer than 100 per parameter for a Gaussian process).

The regressions use outside packages, as an optional extra (`pip install starsim[econ]`): `pygam` for the GAM and `scikit-learn` for the Gaussian process. Calling a VOI method without them raises an `ImportError` that names the extra.

`ce.to_df()` is still the input to voi, BCEA, and dampack, for anyone who wants their other methods (INLA, moment matching, or EVSI for designs not covered here).

## Output

```python
ce.to_df()          # one row per scenario and draw: cost, effect, increments, net benefit, and one column per drawn parameter
sims.to_df()        # the long table: scenario, draw, run, time, every stratum, and a column per result, including costs and effects
sims.to_df(format='vimc')    # the same, with VIMC's column names (year, age, country, cohort_size, cases, deaths, dalys)
```

- **`ce.to_df()`** is the contract of BCEA, voi, and dampack's `make_psa_obj()`: costs and effects by sample and strategy, plus the sampled parameters ([cea-software.md](cea-software.md#bcea-and-voi)). It has a `discount` column when more than one rate was asked for.
- **`sims.to_df()`** is the long table every economic pipeline reviewed can join and group. Costs, DALYs, and impact attribution are then joins and group-bys on it, including attribution conventions the library does not compute itself (by birth cohort, as VIMC's `vimpact` does).
- **The analysis settings** (currency, price year, discount rates, base year, horizon, perspective, life table, weights and their sources) are saved with every output and printed by `ce.describe()`: the parts of the CHEERS 2022 checklist that software can fill in.

## How each solver realizes it

| Quantity | Compartmental | Agent-based |
|---|---|---|
| Cost per event | the flow times the amount, by stratum | the same, from the counted events |
| Cost or weight per time in a state | integrated exactly (ODE, Gillespie) or by the trapezoid (discrete solvers) | the trapezoid of the counts, or the person's own time in the state when the step is finer than the stay |
| Fixed and one-off costs | the same | the same |
| Cost by history (a function) | works if the function uses only what groups have; otherwise stops with `CapabilityError`, naming what it asked for | works |
| YLL | deaths by age group, at the mean age within the group; needs the model stratified by age | each death at its exact age |
| Comorbidity | per compartment; independence across diseases (printed) | per person |
| Capacity cost | the capacity result times the rate | the same |

Under `solver='auto'`, an economics module never makes a model agent-based except through a function that needs agents, and then `describe()` says which function.

A YLL needs an age at death. A compartmental model with no age stratification and a life table raises `NoAgeAtDeath`, suggesting `sim.stratify(age=[...])` or a fixed life expectancy per death (`life_table=ss.years(30)`, the remaining years assumed for every death).

## Errors and notes

Proposed errors and notes:

| Name | Level | When |
|---|---|---|
| `CostNeedsRate` | error | A number times a state (or an outcome's count) in a cost or effect. Suggests a rate: `ss.peryear(250) * I` |
| `CostIsDistribution` | error | A distribution given directly as a cost amount. Suggests `ss.par(value, prior=...)` for uncertainty, or a function for costs that vary by person |
| `NoAgeAtDeath` | error | YLL from a life table in a compartmental model without an age stratification |
| `UnknownCategory` | error | A perspective names a cost category that does not exist. Lists the categories |
| `UnpairedScenarios` | error | `sims.cea()` on scenarios that do not share draws or runs (different `n_runs`, or run separately). Says to run them together with `ss.parallel` |
| `CostsUnlabeled` | note | `ss.Economics` has costs but no `currency` or `price_year` |
| `FlatBaselineUtility` | note | QALYs with a baseline utility of 1.0 at every age |
| `CRNWeak` | note | `sims.cea()` on a compartmental stochastic run, where pairing is per run and not per person ([11-random.md](../design/11-random.md#common-random-numbers)), or on scenarios whose populations have diverged by more than half |
| `HorizonTruncates` | note | `horizon=` is earlier than the end of the sim, or YLL counts life beyond the horizon while QALYs do not |
| `NotDrawn` | error | `evppi()` or `evsi()` names a parameter that was not drawn in the PSA. Lists the drawn ones |
| `VOINoisy` | note | Value of information from a stochastic model with one run per draw, so chance is counted as uncertainty. Suggests `n_runs=` |
| `FewDraws` | note | Too few draws for the regression behind `evppi()` or `evsi()` to be reliable, given the number of parameters |

## What this adds to the vocabulary

| Name | Kind |
|---|---|
| `ss.Economics` | a module (an analyzer) |
| `ss.dalys`, `ss.qalys` | effect recipes |
| `ss.lifetable` | a named-data loader, like `ss.people` |
| `sims.cea()`, `econ.evaluate()`, `econ.discounted()`, `ce.ceac()`, `ce.vs()`, `ce.evpi()`, `ce.evppi()`, `ce.evsi()` | methods |
| `draws=` on `ss.parallel` | a keyword |

Four `ss.` names and eight methods. `cost=` on products, weighted sums of results, `ss.par` with `source` and `prior`, `ss.parallel`, `sims.diff()`, `to_df()`, and `describe()` are the design's own, reused. Per [17-vocabulary.md](../design/17-vocabulary.md#adding-to-the-vocabulary), each new name should be justified by a vignette; the candidates are the TB vaccine investment case (tbvax), HPVsim's cervical screening DALYs, and an HIV program cost (Spectrum's Resource Needs Model).

## Deferred

| Item | Note |
|---|---|
| **Budget-driven coverage and optimization** | Spending as the input, with coverage derived through a declared cost-coverage curve (linear, fixed plus variable, saturating), and an optimizer that splits a budget across deliveries (Optima, Atomica). The way in is a delivery whose `capacity=` is a budget divided by a unit cost, so the declaration of unit cost here is the same one an optimizer would use |
| **Finite stock shared across interventions** | STIsim's `Supplies`. `capacity=` covers one delivery's stock; a pool shared by several deliveries, with cost attributed to each and to the pool, waits for STIsim's port to v4 |
| **Currency conversion and inflation** | A helper that converts unit costs between currencies and price years from a named index (`treasure`'s approach). Until then costs are given in one currency and year, and the conversion is the user's, done before the costs are entered |
| **Extrapolation beyond the horizon** | Remaining discounted (quality-adjusted) life expectancy for everyone alive at the end |
| **A per-person ledger** | Each agent's accrued costs and effects, for extended CEA and catastrophic health expenditure, which also need households and incomes |
| **Macroeconomic models** | Lost output by economic sector, with sectors as a stratification of workers (DAEDALUS). State-of-the-world costs above cover the cost side; the sector data is not bundled |
| **Distributional CEA** | Health opportunity costs distributed across equity groups and a social welfare function. The stratified results here are its input |

## Open questions

- **Whether `ss.Economics` is one module or several declarations.** Costs could instead be declared on the sim (`ss.Sim(costs=...)`), as cross-module outcomes are. A module was chosen because currency, price year, base year, and perspectives belong to one analysis, and a sim may want two.
- **Where cost categories live when a product has a cost.** A delivery's cost is a category named after the delivery. Whether it should also be a result of the delivery itself (as now, `vx.cost`), or only of the economics module, is open; keeping both is what is written here.
- **Expected-value accumulation.** Effects accumulated as probabilities (the chance of death each step) rather than realized events, which steadies ICERs in small stochastic runs. It would be a keyword on `ss.dalys`; it is not clear how it should interact with transitions that are drawn.
- **Attribution in time.** YLD by the year lived and YLL by the year of death are the defaults. YLD by the year of onset (incidence-based, as HPVsim's analyzer does) is a different quantity under discounting; whether to offer it, and TLO's practice of storing several versions side by side, is open.
- **Joint occupancy across diseases in a compartmental run.** The combined weight of two diseases needs to know who has both, which separate compartmental modules do not; independence is assumed and printed. A shared stratification would make it exact.
- **Population VOI.** `population=` and `years=` multiply per-person values by the discounted number of people the decision affects. Whether that number should instead come from the sim (the eligible population over the horizon) is open.
- **The name `cea`.** It returns cost-utility results as well (QALYs), and benefit-cost results with a monetized effect. `sims.compare()` is the alternative.

## Rejected

- **Costing code inside each disease.** Costs are declared against the model's names from outside it, so the same disease can be costed two ways in one session.
- **Discounting during the run.** Every in-simulation DALY accumulator in the review leaves results undiscounted, and changing a rate should not need a re-run.
- **A single cost channel for all interventions.** EMOD's `Campaign Cost` was used as a delivery counter as often as for cost. Categories stay apart, and deliveries already count themselves.
- **A money type.** Money is a number, as in [02-types.md](../design/02-types.md#what-is-not-typed). The unit checking that matters is time, which is already typed.
- **Transition costs through extra states.** Transitions and outcomes have flows; a cost per event attaches to the flow.
- **Half-cycle correction as a user setting on every cost.** Person-time is integrated by the library, once, and per-event costs are never corrected.
- **A built-in reference case as the default.** Each is named and opt-in, so the choice is visible in the code.
- **Averaging ICERs across runs or draws.** Increments are averaged, then divided.

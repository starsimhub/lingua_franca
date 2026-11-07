---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# The complete vocabulary

Every public name the specification uses, in one place.

Justified by [best-practices/principles.md](../best-practices/principles.md): a vocabulary nobody can hold in their head is a vocabulary nobody uses correctly.

The base is Starsim, so most of the names are Starsim's own and are marked as such; names this specification adds are in **bold**.

## Capitalization

The rule is Starsim's existing one (`ss.Dist` and `ss.normal`, `ss.Rate` and `ss.perday`):

> **Modules, containers, and base classes are CamelCase. The concrete pieces you put inside a module are lowercase.**

So `ss.Sim`, `ss.MultiSim`, `ss.Disease`, `ss.RandomNet`, `ss.MixingPool`, and `ss.Intervention` are CamelCase, along with the two graph classes `ss.State` and `ss.Transition` and the products `ss.Vaccine`, `ss.Diagnostic`, `ss.Treatment`. Time values, distributions, `ss.par`, `ss.states`, the places outside the model (`ss.unborn`, `ss.dead`, `ss.outside`), the transition constructors, `ss.modify`, `ss.outcome`, the parameter forms, the deliveries, and functions such as `ss.parallel` are lowercase. So are the loaders, which look up named data and return an ordinary object: `ss.population('Kenya')` returns an `ss.People`, and `ss.contacts('Kenya')` a set of `ss.MixingPools`. The tables they read are in `ss.data` (`ss.data.age('Kenya')`, `ss.data.population()`, `ss.data.rates()`, `ss.data.contacts()`, `ss.data.geography()`), which is not listed here, as `ss.geo`'s other names are not.

## The names

`ss.` also exports names that are not listed here: the classes and helpers for writing modules as code, `ss.note`, `ss.CapabilityError`, and `ss.AlreadyRunError`. The other errors and warnings that are classes are in `ss.errors` (`ss.errors.AtBound`), the testing and profiling tools in `ss.debugtools`, and everything else in its own submodule (`ss.solvers.Compartmental`, `ss.expressions.Expr`).

### Sim and modules

| Name | What it is |
|---|---|
| `ss.Sim` | Modules, a population, mixing, a timeline, and a solver. One sim is one run |
| `ss.People` | The population: size, demography, per-agent attributes |
| **`ss.population`** | A named population: `ss.population('Kenya', year=2024)` returns an `ss.People` |
| **`ss.person`** | A property of each person, before there are people: `ss.person.age < 15` is a condition, and `expit(b0 + b1*ss.person.urban)` a rate, with each person's value (each group's, as compartments) |
| `ss.Module` | The one module abstraction; everything below is one |
| `ss.Disease` | Any disease: declared states and the transitions between them, code (`define_states()`, `step()`), or both. Most states hold people; a reservoir or a vector population is a state that holds a count |
| **`ss.Strains`** | The strains of a disease, `ss.Disease(..., strains=ss.Strains(['DS', 'RIF'], ...))`, giving `dis.strains`; unpacked into strain objects (`DS, RIF = strains`) for conditions and `move=DS >> (DS, RIF)`. States are shared (one course, sets carried up to `max_strains`) or each strain's own (`shared=False`, or `shared=['Ca']`); strains can also be diseases of their own sharing a natural history (`ss.Strains([hpv16, hpv18])`) |
| **`ss.AgentDisease`** | An `ss.Disease` written as code that runs only as agents, transmitted over the sim's networks (`beta`, `rel_sus`, `rel_trans`, `set_prognoses()`), with hooks overridable one at a time (`transmit()`, `transmissibility()`, `susceptibility()`, `route_betas()`, `transmit_route()`, `finalize_infections()`); Starsim 3's `ss.Infection` |
| `ss.Demographics` | Births, deaths, pregnancy, migration |
| `ss.Intervention` | Base class for interventions with custom `step()` code |
| `ss.Connector` | Base class for cross-module `step()` code |
| `ss.Analyzer` | Base class for extra results |

Starsim's library modules (`ss.SIR`, `ss.SIS`, `ss.SEIR`, `ss.Births`, `ss.Deaths`, `ss.LegacyPregnancy`, the `ss.infection_log` analyzer, and the rest) remain available and are not listed here; they are models written in the language, not part of it. Nor are the error and warning classes (`ss.CapabilityError`, `ss.errors.ImportIncomplete`, and the rest), which are listed in [15-errors.md](15-errors.md): they are what the library says, not what a user writes.

### States, transitions, parameters, results

| Name | What it is |
|---|---|
| **`ss.State`** | A state, with `people`, `init`, `rel_sus`, `rel_trans`, `infected` (counted in the results `infected` and `prevalence`), `label` |
| **`ss.states`** | Several states at once, named from the variables they are assigned to: `S, I, R = ss.states(3)`. `ss.states('S I R')` when the names are wanted up front |
| **`ss.unborn`**, **`ss.dead`**, **`ss.outside`** | Outside the model, the three instances of `ss.transitions.Outside`: where births come from (`ss.unborn >> S`), where deaths go (`I >> ss.dead @ 0.1`), and where people arrive from and leave to alive (`ss.outside >> S`, `S >> ss.outside`); for a count, the same three (mosquitoes emerge from `ss.unborn`, bacteria are shed from `ss.outside`) |
| **`ss.stay`** | Staying where one is, as a destination of a split: `ss.Transition(N, {L: p, ss.stay: None}, when=...)` |
| **`ss.Transition`** | The one transition class; also built by `a >> b @ x` |
| **`ss.on`** | A trigger: a condition that starts to hold or an event that happens, with `delay=` for a time after an event. `S >> V @ ss.on(ss.person.female & (ss.person.age >= 9))` is the shorthand for a transition's `when=`, and `when=ss.on(screening.positive, delay=ss.months(3))` a delivery three months after an event |
| **`ss.birth`** | Shorthand: an inflow of newborns, at a rate per person, or at an event (`ss.birth(when=preg.delivery, children=2)`) |
| **`ss.death`** | Shorthand: an outflow; `lifetable=` is a death rate for each age band of a life table, by each person's age, under every solver |
| **`ss.immigration`** | Shorthand: an inflow of a number of people per unit time (`n=ss.peryear(100)`), at ages like the population's |
| **`ss.emigration`** | Shorthand: an outflow, recorded as people who left rather than died |
| **`ss.migration`** | Net migration of everyone at a rate per person of either sign, e.g. `ss.migration(rate='Albania')` for the UN's rates |
| **`ss.move`** | A move made now, from code: `ss.move(I >> R, p)`, with `n=` people or `p=` each, among `who=`; not checked against the declared transitions |
| **`ss.lifetable`** | A life table (ages and deaths) for `ss.death(lifetable=...)`, or by year and sex for `ss.Deaths(lifetable=...)` |
| **`ss.transfer`** | Movement between levels of a stratification: `ss.transfer(dict(risk=('low', 'high')), rate=)` |
| **`ss.par`** | A named parameter with `bounds`, `prior`, `source`, `doc` |
| **`ss.pars`** | Several parameters at once, from defaults and the values given, for a disease whose transitions are made in `__init__()`: `p = ss.pars(defaults, **kwargs)` |
| **`ss.attr`** | A value for each person: drawn or recorded at an event (`when=`), or a value for each event (a dict by event); drawn once (a trait); or derived from others. `init=` is the value before any event: a number, or a distribution or expression drawn for each person when they are made |
| **`ss.outcome`** | A reported quantity: a weighted sum of flows, delayed (`delay=`), and given a duration (`dur=`) for the number currently in it |
| `ss.SimData` | A data file or data frame with its columns matched to result names, which `ss.Sim(data=)` makes: `ss.SimData(df, aliases=..., ignore_extra=True)` if it has to be made directly |
| **`ss.ref`** | A state or transition named by its module and name, before the module is made: `ss.ref('hiv.I')` |
| **`ss.mother`** | A condition or value read on each unborn agent's mother (`include_born=True`: also on the mothers of those already born), e.g. `ss.mother(syph.I)` (agents) |

The operators `>>`, `@`, `|`, and arithmetic on states are part of this group and add no names. For whole states `|` and `+` are the same set of people (`(E | I) >> R`, `infected = E | I`, `(E | I).n`); `+` is also arithmetic (weights, rates, `N = S + E + I + R`), and `|` also joins conditions. A dict of destinations is a split (`I >> {ss.dead: p, R: None} @ dur`). A custom per-step function needs no name of its own: a plain function is given as a keyword, or written in `step()`.

### Time

All Starsim's, and **`ss.peract`**, a probability per act, which is not a time value.

| Kind | Type | Constructors |
|---|---|---|
| Duration | `ss.Duration` | `ss.days` `ss.weeks` `ss.months` `ss.years` (whole months and years added to a date follow the calendar), and one unit as `ss.day` `ss.week` `ss.month` `ss.year` |
| Rate (hazard) | `ss.per` | `ss.perday` `ss.perweek` `ss.permonth` `ss.peryear` |
| Probability per period | `ss.prob` | `ss.probperday` `ss.probperweek` `ss.probpermonth` `ss.probperyear` (or `ss.prob(0.1, 'day')`) |
| Frequency (an expected count) | `ss.freq` | `ss.freqperday` `ss.freqperweek` `ss.freqpermonth` `ss.freqperyear` |
| Calendar date | | `ss.date` (`ss.years(2000)` is a duration of 2,000 years from 0, not `ss.date(2000)`) |
| Probability per act, on a network with acts | **`ss.peract`** | `ss.peract(0.01)`, or one value for each of the network's directions, `ss.peract(m2f=0.3, f2m=0.15)` (also `{('m', 'f'): 0.3}`); no unit and no conversion |

That is four types, each with a constructor per unit, and `ss.date`: two choices (which kind, which unit), and a bare number works in every slot for anyone who does not want to use them. A frequency is distinct from a rate: a frequency times a duration is a number of events, where a rate times a duration is a probability, and adding one to the other is an error ([02-types.md](02-types.md#conversion)). A network's `acts=` takes a frequency (or a rate).

### Distributions

Starsim's, with Starsim's names, each given by its moments where it has them (`ss.normal(mean, std)`, `ss.expon(mean)`, `ss.poisson(mean)`, `ss.gamma(mean=, std=)`), with a shift `loc=` as SciPy's (so `ss.gamma(mean=, std=, loc=)`'s mean is of the whole distribution, shift included), and a `TypeError` at construction for a keyword a distribution does not take: `ss.Dist` (the base class, which also wraps any SciPy distribution) and `ss.normal`, `ss.lognormal` (`mean=, std=` of the values, or `log_mean=, log_std=` of their logarithms), `ss.expon`, `ss.gamma`, `ss.weibull`, `ss.poisson`, `ss.nbinom`, `ss.uniform`, `ss.bernoulli`, `ss.constant` (`value=`), `ss.beta_dist` (`mean=, std=`), `ss.choice`; and three new ones, **`ss.erlang`** (a number of exponential stages with a mean, which a compartmental run takes as stages), **`ss.truncnorm`**, and **`ss.binom`** (mostly as a likelihood). The rest of Starsim's set is available and not listed.

### Parameter forms

**`ss.by`** (one value per stratum), **`ss.timeseries`** (varies in time), **`ss.seasonal`** (a yearly cycle). The other forms a parameter can take (a number, a typed quantity, a distribution, a function) need no names of their own.

### Mixing and space

Everything spatial is in the submodule `ss.geo`.

| Name | What it is |
|---|---|
| `ss.Network` | Base class for networks |
| `ss.RandomNet` `ss.SexualNet` | Individual-level networks (Starsim's; who takes part is `who=`, a condition; each edge has a `weight`, and transmissibility is the disease's, by route, not the network's; its other networks are available too, and the library's, e.g. `ssl.StaticNet` for a NetworkX graph). `ss.SexualNet` is partnerships between two groups (`between=`): men and women (`'mf'`, the default), men (`'mm'`), or e.g. sex workers and clients (`('fsw', 'client')`), with acts per unit time in each, as in Starsim 3 (people with no partner are paired), or with a target number of partners at a time (`n_contacts`, `concurrency`, `max_contacts`). Partnerships between anyone (needle sharing), and EpiModel's targets (`match=`), are the library's `ss.DegreeNet`; more structured sexual networks are STIsim's |
| `ss.MixingPool` | Group-level mixing; `ss.MixingPool(n_contacts=10)` with no groups is homogeneous (several together are `ss.networks.MixingPools`, which `ss.contacts` returns) |
| **`ss.contacts`** | A contact matrix as mixing pools: a named one, `ss.contacts('Kenya')`, one by a dimension (`ss.contacts(risk=M)`, `ss.contacts(age=A, area=B)`), one matrix over several dimensions together (`dims=[...]`), or homogeneous mixing (`ss.contacts(10)`). A matrix is read as a contact survey, row `i` the contacts of a person in group `i` |
| **`ss.geo.geography`** | A geography: names, populations, centroids, distances; named (`ss.geo.geography('Kenya', level=1)`) or given directly |
| **`ss.geo.Mobility`** | Movement between places from a matrix (`kind=`, `away=`) |
| **`ss.geo.gravity`** | Movement model, with parameters to fit or guess, and `kind=` and `away=` |
| **`ss.geo.radiation`** | Movement model with no parameters but its scale (Stouffer and competing destinations are deferred; a matrix covers them) |
| **`ss.geo.register`** | A register of moves from data (`ss.geo.register('moves.csv')`) |

### Interactions and interventions

| Name | What it is |
|---|---|
| **`ss.modify`** | While a condition holds (`who=`), and when (`when=`, e.g. `ss.schedule(start=, stop=)`), multiply, add to, or set a named quantity |
| **`ss.immunity`** | Protection between strains, combined by a rule: what protects is `due_to=` (a state, or an attribute), the quantity it lowers is the keyword and the protection its value, a matrix (rows from, columns against) or a number (`ss.immunity(due_to=R, protection=m, combine='sum')`, where 1 is full protection); for `ss.Strains(immunity=)` |
| **`ss.Vaccine`** **`ss.Diagnostic`** **`ss.Treatment`** | Products: nouns for things (Starsim 3's `ss.Vx`, `ss.Dx`, `ss.Tx` remain only as base classes for products written as code, not as aliases; `ss.Diagnostic` was `ss.Test`, renamed so that no product and delivery differ only by case) |
| **`ss.Event`** | Something that happens to people (a move, a counter, a visit), to whom (`who=`), when (`when=`), and to how many (`n=` at most each time, `p=` each) |
| **`ss.Delivery`** | An event that delivers a product (or a move), with `coverage=` and `capacity=` for how many it reaches, and what only interventions need (`trace=`, `skip_reached_within=`, `disease=`) |
| **`ss.vaccinate`** **`ss.screen`** **`ss.treat`** | Deliveries of a product: verbs, subclasses of `ss.Delivery` |
| **`ss.schedule`** | When, in full: `ss.schedule(at=None, every=None, start=None, stop=None)`, with the times (or a function of the date) first, by position or as `at=`; for `when=` |
| **`ss.capacity`** | A capacity with a priority and a queue: `capacity=ss.capacity(ss.peryear(50_000), priority=-hiv.cd4, queue=True)` |
| **`ss.at_age`** | Who reaches an age, as a condition for `who=`: `who=ss.at_age(ss.months(9)) & ss.person.female` |
| **`ss.boxcar`** | A waning: full protection for a time, then an exponential decline (an e-folding time) or none (`waning=ss.boxcar(plateau=ss.days(180), decay=ss.days(730))`), under every solver |

### Running, comparing, saving

`ss.MultiSim` (several runs of a sim, or several sims, whose results have a run dimension; one sim given to it is one run), `ss.parallel` (the one way to run many: `ss.parallel(sim, n_runs=100)` for replicates, `ss.parallel({'Baseline': s1, 'Vaccine': s2})` for scenarios, labeled by a dict, with `workers=` the number of processes), `ss.options` (Starsim's global options; `ss.options.crn = False` turns common random numbers off, `ss.options.num_threads` is the threads of Starsim's own passes, and `ss.options.blas_threads` BLAS's), `ss.load` (a sim saved by `ss.save`, or a model in another framework's format), `ss.save` (a sim with its results), **`ss.compile`** (compile the compartmental solvers' kernels ahead of time, e.g. in a Docker image or before a calibration; until then, small runs are taken uncompiled, with the same results).

### Types you get back or subclass

`ss.Result`, `ss.Timeline`, `ss.Rate`, `ss.TimePar`, all Starsim's. Users rarely construct these. The base classes and machinery behind them are in their submodules (`ss.modules.Base`, `ss.loop.Loop`, `ss.sim.SimPars`, `ss.parameters.Pars`).

Fitting is the submodule `ss.fit`, which `import starsim` does not import (its first use does), so its names are not listed here: `ss.fit.Fit`, what `sim.fit()` returns (called `fit` below), `ss.fit.compare_models` (fit and compare by out-of-sample prediction), `ss.fit.method` (a fitting method with its settings, for `sim.fit(method=)`), and `ss.fit.maximize` and `ss.fit.minimize` (the goal of `sim.optimize()`, which reallocates spending between programs: `sim.optimize(ss.fit.maximize('all_vs', at=2030))`). (Starsim 3's `ss.Calibration` is removed.)

### Methods and attributes

| On | Names |
|---|---|
| A model (`ss.Disease`, any module) | **`describe`** **`diagram`** **`equations`** **`transitions`** **`states`** **`strats`** **`add_callback`** **`stratify`** `copy` `pars` **`R0`** |
| A state or a sum of states | **`n`** **`n_infectious`** **`frac`** **`total`** **`time_in`** **`progress`** **`enter`** **`exit`** |
| A product that people hold (`ss.Vaccine`, `ss.Treatment`) | **`held_share`** |
| A transition | **`to`** **`incidence`** **`uids`** **`ever`** **`n_times`** **`since`** |
| A modifiable quantity (`sir.rel_sus`, a parameter) | **`current_value()`** |
| `ss.Sim` | `init` `run` (`until=`, `verbose=`) `plot` `summarize` `to_df` `loop` `results` **`describe`** **`stratify`** `to_json` **`fit`** **`optimize`** **`sensitivity`** **`check_dt`** **`what_modifies`** **`new`** **`restart`** **`gradient`** **`to_synthetic_data`** |
| `sim.loop` | `insert` `to_df` `plot` |
| A result | **`select`** **`by`** **`cum`** `resample` `sum` |
| A result of an `ss.MultiSim`, which has a run dimension | **`quantiles`** `values` |
| An `ss.MultiSim`, which is what `ss.parallel` returns | `run` `plot` `summarize` `to_df` `results` **`diff`** |
| `fit` | **`sim`** `pars` `plot` `summarize` `to_df` **`project`** **`samples`** |
| What `ss.fit.compare_models` returns | **`fits`** `plot` `summarize` `to_df` |

The split is deliberate: `describe`, `diagram`, `equations` are about the model (each returns text that shows itself at a prompt or in a notebook, and is printed with `print()` in a script); `plot`, `summarize`, `to_df` are about results, as in Starsim. `values` is Starsim's name for the array behind a result; on a MultiSim result it is the full runs-by-time array. `.n` is the number in a state in each place (`(w*I).n` with each person counted by `w`, and `.n_infectious` by their infectiousness; a condition has `.n` too, `(hiv.L | hiv.A).n`), and `.total` in the whole population; `.frac` is the share; `.time_in` is the time each person has spent in it (in `p=` and rates out of it). On a transition with several destinations, `.X` is the flow to its destination `X` (`cin.X`, read `res.cin.X`), not a new name. Reading `sir.rel_sus` gives the base value; `sir.current_value('rel_sus')` gives it with the active modifiers applied (agents only). `msim.check_runs()` is deferred and not listed.

A simple SIR uses four of these names: `ss.states`, `ss.Disease`, `ss.Sim`, and `run` (five with `plot`, and `ss.days` if the duration is typed). A stratified, calibrated national model with interventions uses perhaps forty.

## Keywords

Keywords are not listed above, but they are vocabulary too, so the main sets are listed here.

| On | Keywords |
|---|---|
| `ss.Sim` | the model (a module or a list of modules) as the first argument; `networks` `people` `total_pop` `n_agents` `start` `stop` `dt` `unit` `solver` (a name, or `ss.solvers.ode(integrator=, substeps=, dwells=)`, `ss.solvers.binomial(substeps=)`, `ss.solvers.abm(step=)`) `approximations` (`'note'`, `'allow'`, `'error'`) `rescale` (`True`, or a dict of its options) `stratify` (one dict of dimensions) `rand_seed` `verbose` `interventions` `connectors` `analyzers` `data` `pars` (the model's parameters only) `group_results` `record_people` `aging` `require_kernels` `step_order` `label`; plus `diseases`, `demographics`, `modules` as in Starsim. `sim.pop_scale` is read-only, `total_pop / n_agents` |
| `ss.MultiSim`, `ss.parallel` | the sims (or a dict of them by label); `n_runs` `pars` `priors` `workers` `until` `verbose` `shrink` |
| `ss.Disease` | the transitions and outcomes by position, or as `transitions` `outcomes` `results` (each positional form has a keyword alternative); `name` `dt` `init_prev` (a share, up to 1) `init` `init_n` (a number of people) `default_state` `strains` `stratify` `solver` (its own `ss.solvers.abm(step=)`), and one keyword per member. An instance of a declared disease takes extra states, transitions, and outcomes beside its class's |
| `ss.State` | `name` `people` `init` `init_n` `rel_sus` `rel_trans` `infected` `keep_time` `label` |
| `ss.Transition` | `source` `dest` `rate` `dur` `p` `stages` `who` (who it applies to) `when` (an event, `ss.on(event, delay=)`, or a condition that triggers it; `@ ss.on(...)` is its shorthand) `acquisition` `per_strain` (`'each'` or `'first'`) `move` `increment` `min_stay` `name` `label` |
| `ss.birth` | `rate` (per person) or `when` (an event), `children` `p_female` |
| `ss.immigration` | `n` (a number of people per unit time) |
| `ss.migration` | `rate` (per person, of either sign, or a place) |
| `ss.death`, `ss.emigration` | `rate` `dur`; `lifetable` (`ss.death`) |
| `ss.transfer` | a dict of the dimension and its pair of levels (or `increment`, for a counter), `rate` `dur` `p` `states`, and the delivery keywords |
| `ss.par` | `bounds` `prior` `source` `doc` |
| `stratify` (on a model or a sim) | dimensions only, any number, each its levels (a dict of shares) or `ss.levels(levels, states=, who=, kind=, mobility=, fractions=)`; `inplace` |
| `ss.Strains` | the strains (names, a dict of values by strain, or diseases), `shared` `immunity` `max_strains` `transmit` `fractions` `name` `label`, and values by parameter |
| `ss.immunity` | `due_to` `protection` `combine` |
| `ss.modify` | `multiply` `add` `set` `efficacy` `share` `network` `who` `when` (`ss.schedule(start=, stop=)`, or a function of the date) `until` (a condition, or a duration to hold) `name` |
| `ss.Event` | what happens (a move, a counter, or nothing, a visit) first; `who` `when` `n` `p` `strain` `increment` `name` `label` |
| Deliveries (`ss.Delivery`, `ss.vaccinate`, `ss.screen`, `ss.treat`) | the product (or a move) first; `who` (who is eligible: a condition on people or on the population, a function of the sim, `ss.at_age()`, joined with `&`) `when` (nothing for routine; a time or a list of times; an event; `ss.on(event, delay=)`; a function of the date; or `ss.schedule()`) `coverage` `capacity` (a number, a rate, or `ss.capacity(n, priority=, queue=)`) `strain` `increment` `trace` `skip_reached_within` `disease` |
| `ss.schedule` | `at` (times, or a function of the date; also by position) `every` `start` `stop` |
| `ss.on` | the event or condition; `delay` |
| Products | `efficacy` `waning` `cost` (all); `leaky` (`ss.Vaccine`); `sensitivity` `specificity` `result_delay` `detects` `outcomes` (`ss.Diagnostic`); `cure` (a probability, a dict by state, or a dict by what it moves people along) and `moves` (moves that are not cures) (`ss.Treatment`) |
| `ss.outcome` | `delay` `dur` `likelihood` |
| `ss.SimData` | `aliases` `ignore_extra` |
| `ss.MixingPool` | `n_contacts` `source` `target` |
| `ss.SexualNet` | `between` (`'mf'`, `'mm'`, or a pair of groups) `dur` `acts` `participation` `debut` `n_contacts` `concurrency` `max_contacts` `match` |
| `ss.geo.Mobility` | `matrix` `kind` `away` |
| `ss.geo.gravity`, `ss.geo.radiation` | `kind` `away` (and `source_power` `dest_power` `distance_power` `scale` for gravity, `scale` for radiation) |
| `ss.contacts` | a matrix, a country, a number, or a matrix by dimension as a keyword (`risk=M`); `ages` `dims` `name` `study` `layer` `unit` |
| `ss.RandomNet` | `n_contacts` (the same for everyone; a distribution gives the shape) `dur` (in the sim's unit when a bare number; one step by default) `who` `memory` |
| Networks | `sides` (and `net.directions`, which follow from them; `between` on `ss.SexualNet`); `who` for who takes part |
| `sim.fit` | `pars` `data` `weights` `likelihood` (a distribution for every series, a dict by series, or `False`) `loss` `penalty` `method` (a name, `ss.fit.method(name, **settings)`, or a list) `rand_seed` |
| `ss.fit.method` | the name, and the method's own settings (e.g. `n_trials`, `draws`, `chains`, `particles`, `samples`, `n_runs`, `reseed`, `require_jax`, `workers`) |
| `sim.optimize` | `goal` (`ss.fit.maximize(result, at=)` or `ss.fit.minimize(...)`) `total` `start` `spend` `bounds` `target` |
| `ss.fit.compare_models` | `data` `holdout` `folds` |

## Slots and their types

A bare number in any of these slots takes the slot's type and the sim's unit ([02-types.md](02-types.md#bare-numbers)). In a sim where nothing has a unit, "per unit time" below is per timestep and a duration is a number of steps. Every slot also accepts the rest of the parameter ladder ([04-parameters.md](04-parameters.md#the-ladder)), including a function.

| Slot | A bare number is | Appears on |
|---|---|---|
| `beta=` | a rate per unit time with no network; a probability per contact on a network without acts; a probability per act on a network with acts (`ss.SexualNet`, `ss.DegreeNet(acts=...)`), as `ss.peract`. A dict gives one value per network; directions are named with `ss.peract(m2f=..., f2m=...)` (a pair is an error) | `ss.SIR`, `ss.SIS`, `ss.SEIR` and the library's diseases |
| `rate=`, and a bare number after `@` | a rate (hazard) per unit time | `ss.Transition` and every shorthand constructor |
| `dur=` | a duration in the module's unit; a scalar means an exponential dwell time with that mean (on a network, the mean length of an edge) | `ss.Transition`, `ss.transfer`, `ss.outcome`, networks |
| `p=` | a branch probability, or the chance for each person eligible | `ss.Transition`, `ss.transfer`, `ss.move`, `ss.Event` |
| `n=` | a number of people (at most this many each time); per unit time on `ss.immigration` | `ss.Event`, `ss.move`, `ss.immigration` |
| `stages=` | a whole number of sub-stages | `ss.Transition` |
| `init=` | a share of people, up to 1 (a whole number too, with a warning to write a float); on the disease, a dict of these by state name | `ss.State`, `ss.Disease` |
| `init_n=` | a number of people; on the disease, a dict of these by state name | `ss.State`, `ss.Disease` |
| `init_prev=` | a share of people, up to 1 (above 1 raises, pointing to `init_n=`) | `ss.Disease` |
| `n_contacts=` | a mean: a count of contacts, the same for everyone (`ss.RandomNet`, `ss.MixingPool`, a matrix of `ss.networks.MixingPools`, `ssl.HybridNet`'s layers), or a target or a size that is a Poisson mean (`ss.DegreeNet`, `ss.SexualNet`, `ssl.ClusterNet(cluster_size=)`); a distribution gives the shape | networks, mixing pools |
| `acts=` | on lasting partnerships, an error (it would be acts per step): give a frequency, e.g. `ss.freqperweek(2)` (or a rate) | `ss.SexualNet`, `ss.DegreeNet` |
| `share=` | the share of acts (or contacts) a modifier acts on | `ss.modify` |
| `coverage=` | a fraction of the eligible people | deliveries, `ss.transfer` |
| `capacity=` | a number per round (or step), or a rate per unit time (required for routine delivery); `ss.capacity(n, priority=, queue=)` for a priority or a queue | deliveries |
| `efficacy=`, `sensitivity=`, `specificity=` | a probability | products; `efficacy=` also on `ss.modify` (`multiply=1 - efficacy`) |
| `waning=` | a duration: the product is lost at an exponentially distributed time with that mean; `ss.boxcar(plateau=, decay=)`, under every solver; a function of the time since delivery, `fn(t)` or `fn(t, sim, uids)` (or any of `t`, `self`, `sim`, `uids` by name) with `t` a duration, fades the efficacy instead, as agents only (a new dose restarts either); a dict gives each effect its own; other shapes are written as states ([08](08-interventions.md#products)) | products |
| `during=` | the product is held, and acts, only while people are in these states | products |
| `delay=`, `result_delay=` | a duration | `ss.outcome` and `ss.on`; `ss.Diagnostic` |
| `every=` | a duration | `ss.schedule` |
| `away=` | a fraction of time | `ss.geo.Mobility`, `ss.geo.gravity`, `ss.geo.radiation` |
| `multiply=`, `add=`, `set=` | a multiplier, or a value in the target's own type | `ss.modify` |
| `when=` (a time), `at=`, `start=`, `stop=` | a calendar year (a bare number from 1800 on; one between 1000 and 1800 warns that it is ambiguous), or a date; in a sim with no calendar, a duration from 0 (`ss.days(10)` is day 10, in a list or not), which in a sim with a calendar is an error suggesting `sim.pars.start + ss.days(10)` or a date. A time outside the sim raises a `ValueError` | `ss.schedule`, deliveries and events, `ss.modify`, `ss.timeseries`, a module's `start=`, `sim.run(until=)` |
| `bounds=` | a pair, in the unit of the parameter's value | `ss.par` |
| `cost=` | a plain number | products |

## Removed since the first draft

| Removed | Why | Use instead |
|---|---|---|
| `ss.Effect` | Renamed and split: scaling a quantity is one thing, complex logic another | `ss.modify`, or Python in `step()` |
| `ss.Expr`, and `ss.age`, `ss.sex`, `ss.uid`, `ss.time`, `ss.year`, `ss.weekday`, `ss.has`, `ss.scheduled` | A second set of names for things the sim already has | Conditions on the real attributes: `(ppl.age > 65) & ~sir.vaccinated`, or a function of the sim |
| `ss.Continuous` | A special kind of state and route for reservoirs | An ordinary `ss.State` that is not people, with counts (`W.n`) in rates |
| `ss.stouffer`/`ss.competing_destinations`, `msim.check_runs()` | Deferred from v1: one use case each, and the vocabulary is smaller without them ([19-open-questions.md](19-open-questions.md#c-deferred-not-in-v1)) | A mobility matrix; `check_dt` |
| `ss.process` | A penalty-box name for custom code | A plain function as a keyword, or `step()` |
| `ss.Homogeneous` | Not needed | No network given, or `ss.MixingPool(n_contacts=10)` |
| `ss.Network(edges=)` | Starsim already has names | Starsim's networks; `ssl.StaticNet(graph=...)`, with a NetworkX graph or a function that makes one |
| `ss.Par`, `ss.Outcome` | Capitalization rule | `ss.par`, `ss.outcome` |
| `ss.cascade`, `observe()`, `Model.results()` | A separate observation step (`ss.cascade` came back as a group of steps, and was removed again on 2026-10-20: it ran as its steps would as a list) | Results declared as keywords with the model; the steps as a list |
| `ss.visit`, `ss.Resource`, `ss.share` | Delivery extras, removed 2026-10-20 with stock targets (`target=`, `above=`), shared resources (`uses=`), and `count_events=` | `ss.Delivery(who=...)` with no product; `capacity=` or `who=` as a function of the sim; an analyzer |
| `ss.N`, `ss.count` | Extra names for a sum and a keyword | `N = S + I + R`; `capacity=` |
| `ss.dist(...)` | Duplicate | `ss.Dist(dist=...)` |
| `ss.lognorm`, `ss.binomial`, `ss.neg_binomial`, `ss.rate` | Not Starsim's names | `ss.lognormal`, Starsim's set, `ss.nbinom`, `ss.per` |
| `ss.exp_decay`, `ss.linear_decay` | Covered by existing forms | `waning=` as a duration, a function, or `ss.timeseries` |
| `ss.act`, `queue()`, `phase=`, `sim.substep()` | Queued updates and named phases are gone | Starsim's ordered loop, `sim.loop.insert()` |
| `ss.Stage`, `fit.apply()` | Simpler spellings | `fit(method=[...])`; `fit.sim` |
| `capabilities()`, `closure=`, `to_ode()`, `scale=` | The closure ladder and per-transition hybrid solvers are out of v1 | `describe()`, `solver=`, printed approximations |
| `jacobian()`, `fixed_points()`, `sim.equations()` | Symbolic analysis is not a v1 feature | `sir.equations()` |
| `summary()` on a model, `to_dict()` | `summarize` is about results in Starsim; the model is its code, and `to_json` is a sim's results | `describe()` |
| The dict tuple shorthand `dict(infection=('S -> I', 0.05))` | Ambiguous: it guesses the kind of transition from a bare value | The operator form |
| `ss.transmission`, `ss.progression` (arrow strings) | A second spelling of a transition, with states made from their names and the source of infection guessed | `S >> I @ beta * I`, `ss.Transition(I, R, dur=10)` |
| `rate=ss.on(...)`, `after=` an event, `undriven=` | Duplicates of a trigger, and a flag that only silenced a warning | `when=ss.on(event, delay=)`; a transition with `@ 0` |
| Weighted destinations (`S >> (p*A + (1-p)*B)`), `p=` a function giving a row | Duplicates of the list form of branches | `S >> {A: p, B: None} @ rate`, or `ss.Transition(S, [A, B], p=[p, 1 - p])`; a function for each destination |
| `ss.any` | A reduce of `\|` | `a \| b`, or a list in `who=` |
| `ss.Route` | Starsim's name; the base class is `ss.networks.Route`, not exported | `ss.Network`, passed with `networks=` |
| `ss.stratify(sir, ...)`, `ss.RandomExactNet`, `birth_rate=`/`death_rate=` on `ss.Sim`, a delivery's `years=`/`dates=`/`eligible=`, `track_writes=` | Duplicates of other spellings (D34, D36, D38, D39) | `sir.stratify(...)`, `ss.RandomNet(method='exact')`, `demographics=[ss.birth(...), ss.death(...)]`, `when=`/`who=`, `sim.what_modifies()` |
| `ss.explain`, `ss.conformance`, `mixing=`, `n=`, `route=`, `ontology=`, `kind=` on parameters, `take=`/`doses=`, `min=`/`max=` clamps, `crn_strict`, `run(force=)`, `run(reset=)` | Small things that did not earn a name | Documentation pages; `networks=`; `total_pop=`; inline provenance in `ss.par(source=)` |
| An `'ide'` solver | A name of its own for an option of the ODE (built 2026-10-28) | `ss.solvers.ode(dwells='exact')` |

The second draft's names that went in this revision:

| Removed | Why | Use instead |
|---|---|---|
| `ss.Compartments` | A second module class for states that are not people. The states use the same syntax as the disease's, and the name was confusing, since `S`, `I`, and `R` are compartments too | An ordinary `ss.State` in the disease; `people=False` is inferred, or given |
| `None` as a source or sink (`None >> W`) | Python evaluates `None @ 0.1` before it sees the arrow | `ss.null` (itself replaced on 2026-11-06 by `ss.unborn`, `ss.dead`, and `ss.outside`, below) |
| `method=` on `ss.Sim` and `sim.run`, `methods()`, `'ctmc'` as the name | "Solver" is the word; `method=` stays on `sim.fit` for the fitting method | `solver=`, `'gillespie'`; `ss.solvers.ode(integrator=)` for the ODE scheme |
| `n_reps` on `ss.Sim`, `.trajectories`, `check_reps` | A sim is one run | `ss.MultiSim(sim, n_runs=100)` or `ss.parallel(sim, n_runs=100)`; `.values` and `.quantiles` on its results; `check_runs` (deferred) |
| `crn_key` | No case found where keying common random numbers on agent attributes beats Starsim's slots | Slots; `ss.options.crn = False` to turn CRN off |
| `ss.export` | A model is a Python script, which is already the thing to share | The script; `ss.save` of the sim |
| `ss.Needs`, `sim.needs()` (later `ss.Requires`, `sim.requires()`) | Metadata that was never enforced and that no model used (removed 2026-10-21) | A docstring; `doc=` and `source=` on `ss.par` |
| `ss.People('Kenya')` | A loader is lowercase, like `ss.contacts` | `ss.population('Kenya')` |
| `.sel()` | Spelled out | `.select()`, and `.by()` for one series per group |
| `sim.transmissions` | The log is large and slows the run, so it is recorded on request | `analyzers='infection_log'`, Starsim's analyzer |
| `mean_degree` | Starsim's name | `n_contacts`, which may be a distribution |
| `min_duration=` | A policy with memory is fragile as a keyword | `ss.modify(until=)`; `step()` or an intervention class for anything that has to remember |
| `p=` on `ss.outcome` | A number times a flow already means that fraction of it | `ss.outcome(0.5 * infection)` |
| `summary()` | Starsim's name | `summarize()` |

Since the review of October 2026, these names went, or were promised and never built:

| Removed | Why | Use instead |
|---|---|---|
| `ss.update` | A coded module does it: a connector's `step()` keeps the value, read by a function in a rate | A connector, or `step()` |
| `ss.clock()` | `(A \| B).time_in` is the same clock | `(A \| B).time_in` |
| `X.dwell` | The same clock as `X.time_in`, half a step later | `X.time_in` |
| `ss.spread` | Back-dating a module's start is a longer run; only pregnancy's burn-in keeps it, inside the module | Start the sim earlier |
| `offspring=` | A birth in the same disease does it | `ss.birth(NB, when=farrowing, children=3)` |
| `ss.func` | Never built; a plain function given as a keyword already does what it was for | A plain function, or `step()` |
| `sim.crn_report()` | Never built | `ss.options.crn`, and paired runs ([11-random.md](11-random.md)) |
| `dependence=` and `n_ref=` on `ss.MixingPool` | Never built; density dependence is a count in the rate | `beta * I.n` |
| `.prev` on a state | The code's name is `.frac` | `.frac`, and `.n` or `.total` for counts |
| `.base` on a modifiable array | Reading the array gives the base value | `sir.rel_sus` for the base, `sir.current_value('rel_sus')` for the value with modifiers applied |
| `ss.rate`, `ss.time_prob`, `ss.rate_prob` | Starsim 2 names, deprecated in Starsim 3 (Starsim's other time names are kept) | `ss.peryear(x)`, `ss.probperyear(x)` |
| `solver='sde'`, `'stochastic'`, `'ctmc'` | One solver per method | `'gillespie'` (exact), `'tau'` (tau-leaping), `'binomial'` |
| `ss.Calibration` as the result of a fit | `sim.fit()` returns an `ss.fit.Fit` | `ss.fit.Fit` (Starsim 3's `ss.Calibration` is removed) |
| `sim.to_spec()`, `sim.to_code()`, `sim.hash()`, `ss.diff()` (removed 2026-10-27) | The model is its code: there is nothing to translate a sim back into, and two models are compared by their results or a text diff | The script, `describe()`, and `ss.save('run.sim', sim)`; an import gives code (`sim.imported.code`) |
| `msim.reduce()`, `msim.mean()`, `msim.median()`, `ss.MultiResult`, `ss.multi_run()` | A MultiSim is its results, with a run dimension | `msim.results.sir.I.quantiles()` (and `.median()`, `.mean()`); `ss.parallel(pars=...)` |
| `ss.outcome(every=)`, `annualize()` | Resampling belongs to a result | `result.resample('year')` |
| `ss.routine_vx`, `ss.campaign_vx`, `ss.simple_vx`, `ss.routine_screening`, `ss.campaign_screening`, `ss.routine_triage`, `ss.campaign_triage`, `ss.seasonality`, `ss.rate`, `ss.time_prob`, `ss.rate_prob` | Starsim 3 and 2 duplicates of the language | Products with deliveries, `ss.seasonal`, `ss.per` and `ss.prob`; each is mapped in `skills/migrate-starsim3` |

The vocabulary review of November 2026 ([starsim#1547](https://github.com/starsimhub/starsim/issues/1547)) renamed names that meant different things in different places, or whose short form hid what they were:

| Removed | Why | Use instead |
|---|---|---|
| `ss.ppl`, `ss.people()` | An abbreviation no other name uses; a loader that differed from `ss.People` only by case | `ss.person`, `ss.population('Kenya')` |
| `ss.state()` | Differed from `ss.State` only by case, and also names transitions | `ss.ref()` |
| `ss.simdata` | Users give `data=` to the sim | `ss.SimData`, if it has to be made directly |
| `ss.lognorm_ex`, `ss.lognorm_im`, `ss.beta_mean` | Suffixes that don't say which moments are given | `ss.lognormal(mean=, std=)` or `(log_mean=, log_std=)`; `ss.beta_dist(mean=, std=)` |
| `ss.box` | Signal-processing jargon for a shape whose keywords didn't name its parts | `ss.boxcar(plateau=, decay=)` |
| `ss.dur` (as the type) | A type, not something a model writes | `ss.Duration`; `ss.days()` and the other units in models |
| `ss.MaternalNet`, `ss.AgeGroup` | A copy of `ss.PrenatalNet`; a filter that duplicates conditions on age | `ss.PrenatalNet`; `ss.person.age` conditions |
| `ss.immunity(rel_sus=)` | 1 meant full protection, the reverse of `rel_sus` everywhere else | `protection=` |
| `ss.Sim(results=)`, `approx=`, `nopython=`, `use_aging=`, `people_results=`, `custom=` | Same word as `ss.Disease(results=)`; a three-way Boolean; Numba's jargon; a prefix that added nothing | `group_results=`, `approximations=`, `require_kernels=` (and `require_jax=` on `sim.fit`), `aging=`, `record_people=`, `modules=` |
| `ss.Transition(src=, dst=, first=, after=, per='strain')`, `where=` as a trigger | Abbreviations; `first` read as an ordering, `after` as an event; `per` is also the rate type; `where=` meant two things | `source=`, `dest=`, `ss.Disease(default_state=)`, `min_stay=`, `per_strain=`; `when=` (or `@ ss.on(...)`) |
| `X.time`, `X.n_trans`, `transition.count`, `disease.count()` | `.time` read as the sim's time; "trans" as transitions; `count` meant two things | `X.time_in`, `X.n_infectious`, `transition.n_times`, `(A \| B).n` |
| `ss.birth(per=)`, `ss.birth(sex=)`, `ss.Pregnancy(sex_ratio=)` | `per` is the rate type; three names for one share | `when=`; `p_female=` everywhere |
| Deliveries' `what=`, `deliver=`, `interval=`; `ss.Diagnostic(results=, delay=)`; `ss.Treatment(to=, transition=)`; `ss.modify(route=)` | Words that didn't say what they hold; two meanings of `delay`; four keywords for one decision | the first argument, `who=`, `ss.schedule(every=)`; `outcomes=`, `result_delay=`; `cure=` and `moves=`; `network=` |
| `split=` on `ss.Strains` and `stratify()`; `ss.timeseries(mode='constant')`; `sim.fit(gof=)`; `n_cpus=`; `sim.to_data()` | Clearer words | `fractions=`; `interpolation='step'`; `loss=`; `workers=`; `sim.to_synthetic_data()` |

The transitions review of November 6, 2026 replaced names that hid what they meant, and stopped guessing a result:

| Removed | Why | Use instead |
|---|---|---|
| `ss.null` | One name for births, deaths, and migration, so a flow out of the model did not say whether people died or left, nor a flow in whether they were born or arrived | `ss.unborn` (births), `ss.dead` (deaths), `ss.outside` (arrivals and departures alive), the instances of `ss.transitions.Outside` |
| `res.<transition>.null` | The flow of a branch out of the model | `res.<transition>.dead` |
| A state `D` for deaths | It kept the dead among the living (in `N`, on networks) | `I >> ss.dead` |
| `ss.Infection` | A declared `ss.SIR` is an infection too, so the name misled | `ss.AgentDisease` (written as code, agents only); a declared disease with its own `transmit(transition)` |
| `validate_beta()` | Said what it checked, not what it gives | `route_betas()`, the beta of each network |
| Prevalence worked out from the transitions (`Graph.resolve_prevalence()`) | A guess that missed states infected but not infectious (COVID's severe stages) | Mark the states, `ss.State(infected=True)`, for `infected` and `prevalence`; or declare `prevalence` |
| `(S \| I) >> D` raising, and `\|` and `+` meaning different sets | Two spellings that read alike for one set of people | Either, for whole states; brackets with `\|` as sources, `(E \| I) >> R` |

The API review of November 7, 2026 gave each idea one word across the API, and made every keyword either work or raise:

| Removed | Why | Use instead |
|---|---|---|
| `where=` (on transitions, `ss.modify`, `ss.move`, networks, `stratify()`), `eligibility=` | Two words for who something applies to; `eligibility=` was silently ignored | `who=` everywhere (`stratify()` takes it in `ss.levels()`) |
| `on=`, `at=`, `every=`, `start=`, `stop=`, `delay=`, `at_age=` on events and deliveries; `on=` on transitions, `ss.attr`, `ss.birth`; `start=`/`stop=`/`hold=` on `ss.modify`; a transition's `dur=` with an event | Seven ways of saying when | `when=`: a time or list of times, an event, `ss.on(event, delay=)`, a function of the date, or `ss.schedule(at=, every=, start=, stop=)`; `who=ss.at_age(...)`; `ss.modify(until=)` |
| `ss.schedule(when=)`, `dates=`, `fn=` | Duplicates of what `when=` takes | `ss.schedule(at=...)`, by position or keyword (also a function of the date) |
| `priority=`, `queue=` on deliveries | Rare options on a crowded signature | `capacity=ss.capacity(n, priority=, queue=)` |
| `beta=` on a route; `edges.beta` | Honored as agents and dropped as compartments | The disease's transmissibility by route; `edges.weight` |
| Solver names `'ide'`, `'abm-midstep'`, `'abm-wholestep'`, `'abm-events'`; `integrator=` and `substeps=` on the sim; `suggested_solver` | A solver's options belong to the solver | `ss.solvers.ode(dwells='exact')`, `ss.solvers.abm(step=...)`; `ss.solvers.ode(integrator=, substeps=)`, `ss.solvers.binomial(substeps=)` |
| `rescale_threshold=`, `rescale_factor=`, `pop_scale=` | Did nothing alone; a third way to say the scale | `rescale=dict(threshold=, factor=)`; `total_pop=` with `n_agents=` (`sim.pop_scale` is read-only) |
| `sim.run(n_runs=, parallel=, pars=, rand_seed=, solver=, profile=, shrink=)`, `ss.parallel(label=sim)`, `ss.MultiSim(base_sim=, initialize=)` | Several ways to run many sims | `ss.parallel(sims, n_runs=, workers=)` with labels from a dict; `sim.restart(pars=, rand_seed=).run()`; `sim.new(solver=)`; `sim.profile()`; `sim.shrink()` |
| `rate=` as people per unit time on `ss.immigration`; `ss.birth(n=)`; `ss.Pregnancy(embryos_per_pregnancy=)`; `init_prev=` above 1 as a number of people | `rate=` is per person and `n=` a number of people everywhere else | `ss.immigration(n=)`; `children=`; `init_n=` |
| `ss.Pregnancy(maternal_death_rate=, p_maternal_death=, preterm_threshold=, very_preterm_threshold=, rel_preterm=, rel_preterm_age=)` | Two keywords for one kind of event; five for one option | `maternal_death=` (a rate while pregnant, or a probability at delivery); `preterm=ss.preterm(threshold=, very_threshold=, rel=, by_age=)` |
| `stratify(fractions=, adjust=, where=)` mixed with dimensions | Options and dimensions in one call | Levels as a dict of shares; `ss.levels()`; `ss.by()` in the rate |
| `sim.fit()`'s method settings (`n_runs=`, `reseed=`, `require_jax=`, `n_trials=`, ...); ABC-SMC's `particles=`; `fit.mismatch`; `ss.fit.optimize()`; `df=`, `seed=` | Settings of one method among another's; a name with two meanings | `ss.fit.method(name, ...)`; `samples=`; `fit.objective`; `sim.optimize(ss.fit.maximize(...))`; `data=`, `rand_seed=` |
| `output=` on `describe()` and `equations()`; `sim.summary`, `msim.compare()`, `msim.brief()` | Two ways to read each summary | Text that shows itself; `sim.summarize()`, `msim.summarize(each=True)`, `print(msim)` |
| `ss.datedur` at the top level; `ss.date('2020.5')`; `dur=` on the sim | Identical to `ss.months()`; ambiguous; a second way to say the stop | `ss.months()`, `ss.years()`; `ss.date(2020.5)` or `ss.date('2020-05')`; `stop=` |
| `ss.options.num_threads` as BLAS's, `ss.options.threads` | The name said Starsim's | `ss.options.blas_threads`, `ss.options.num_threads` |
| `ss.outcome(stay=)`; `per_strain=True`, `single_strain=True`; `strains.move()`; `sim.people.person()` | One word for one thing | `dur=`; `per_strain='each'`, `'first'`; `strains.change()`; `sim.people.get_person()` |

## Adding to the vocabulary

There is no fixed budget. Before adding a name, check:

- **Does Starsim already have a name for it?** Use that one.
- **Can it be written with what exists?** A bednet is an `ss.modify`; a metapopulation is a stratification by patch; a junction is a branching transition; a reservoir is a state that is not people.
- **Would more than one kind of model use it?** Something only one framework's specialty needs probably belongs in a library built on top.
- **Does it make some real model shorter than it is in its original framework?** That is the test the whole design is held to.
- **Is a keyword enough?** Routine and campaign delivery are keywords on one function, not two classes.

## Not in the language

Each of these exists in at least one reviewed framework. The reasons are in [best-practices/principles.md](../best-practices/principles.md).

| Not included | Instead |
|---|---|
| A standalone modeling language with its own syntax | Python objects |
| Models written in YAML, JSON, or spreadsheets | Python |
| Many named flow kinds | One transition class whose kind follows from its rate |
| A separate class per solver | `solver=` |
| A sim that is many runs | `ss.MultiSim` |
| A default time unit | Timesteps, when nothing in the model has a unit |
| A separate metapopulation model class | A stratification by patch |
| A special route, or a separate module class, for environmental or vector-borne transmission | Counts in rates, and ordinary states that are not people |
| A class per combination of delivery mode and product | Keywords |
| A rule language for triggers and targeting | Conditions and functions in Python |
| Overwrite adjustments in stratification | Multipliers |
| Positional or integer references to states | Names |
| Required declarations of what a module reads and writes | `sim.what_modifies()`, which lists the declared modifiers |
| Common random numbers keyed on agent attributes | Starsim's slots |

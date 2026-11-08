---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Types: time, rates, and quantities

Durations, rates, probabilities, and frequencies; how bare numbers get their units; and time in a sim.

Justified by [best-practices/time-and-units.md](../best-practices/time-and-units.md). These are Starsim's types and names, with Starsim's names kept: `ss.perday` to `ss.peryear`, `ss.probperday` to `ss.probperyear` (the same as `ss.prob(0.1, 'day')` to `ss.prob(0.1, 'year')`), `ss.freqperday` to `ss.freqperyear`, and the one-unit instances `ss.day` to `ss.year`. In a declared transition a `freq` and a `per` of the same value give the same result ([Conversion](#conversion)). There are two additions: a bare number is accepted in every slot and typed by the slot it appears in, and a model in which nothing has a unit counts time in timesteps.

## The types

| Type | Dimension | Means | Constructors |
|---|---|---|---|
| `ss.Duration` | time | an elapsed duration | `ss.days`, `ss.weeks`, `ss.months`, `ss.years` |
| `ss.per` | time⁻¹ | a hazard: events per unit time, continuously | `ss.perday`, `ss.perweek`, `ss.permonth`, `ss.peryear` |
| `ss.prob` | probability per period | the chance of an event within a period | `ss.probperday`, `ss.probperweek`, `ss.probpermonth`, `ss.probperyear` (the same as `ss.prob(0.1, 'day')` and so on) |
| `ss.freq` | time⁻¹ | an expected number of events per unit time | `ss.freqperday`, `ss.freqperweek`, `ss.freqpermonth`, `ss.freqperyear` |

One more value type is not a time value: **`ss.peract(p)`**, a probability per act, for a transmission over a network that defines acts (`ss.SexualNet`, `ss.DegreeNet(acts=...)`). It has no unit and no conversion, so it means the same at any step: a partnership with `a` acts per unit time transmits over a step with probability `1 − (1 − p)^(a·dt)`. It takes one value, or one for each of the network's directions (`ss.peract(m2f=0.3, f2m=0.15)`; see [06-routes.md](06-routes.md#beta-per-route-and-direction)); each value is a number in [0, 1] (else a `ValueError`), an `ss.par` or an expression of them, an `ss.timeseries`, or an `ss.by`. A typed rate inside it raises a `TypeError`.

`ss.per`, `ss.prob`, and `ss.freq` share the base class `ss.Rate`; all four types share `ss.TimePar`. `ss.per` is the hazard type and keeps its Starsim name. A typed value needs its unit: `ss.Duration(3)` and `ss.per(2)` with no unit raise (they were years in Starsim 3). The one-unit instances `ss.day`, `ss.week`, `ss.month`, and `ss.year` (`ss.days(1)` and so on) stand for a unit where one is wanted, e.g. `ss.prob(0.1, ss.year)`.

`ss.per` and `ss.freq` have the same dimension and are different types. A hazard is the parameter of an exponential clock and converts to a per-step probability by `1 − exp(−r·dt)`; a frequency is an expected count and converts by `f·dt`. So a rate times a duration is a probability, and a frequency times a duration a number of events. Mixing them up is a common quiet error, so adding one to the other raises a `TypeError`. A count per time that is not a hazard takes a frequency (or a rate): a network's `acts=`, whose default is `ss.lognormal(ss.freqperyear(80), ss.freqperyear(30))`.

The difference is only in that conversion, which a module written as code asks for (`to_prob()` for a chance this step, `* dt` for a count this step). A declared transition never asks for it: its rate is always a hazard, which the solver turns into a step itself (the ODE integrates it; the stochastic solvers and agents use `1 − exp(−r·dt)`, except that the chain binomial takes `r·dt` for the exits from a source of infection: see [12-backends.md](12-backends.md)). So in a declared transition `ss.freqperday(0.1)` and `ss.perday(0.1)` give the same result, while `ss.probperday(0.1)` is the hazard that gives a 10% chance a day, `−ln(0.9) = 0.105` a day, and gives a different result (10 days of recovery from 1,000: 368 left at `perday(0.1)` or `freqperday(0.1)`, 349 at `probperday(0.1)`).

Calendar durations are not fixed multiples of days, so a whole number of months or years added to a date follows the calendar, as a `pd.DateOffset` does (every month is the same day of the month); as a number, a month or a year is approximate (a year of 365 days). There is no separate calendar-duration type for users (`ss.dates.datedur` is internal). The time between two dates (`date - date`) is `ss.days`.

Counts are plain numbers. `I.n` is the number of people in a state (the same number as the result `I`) and `I.frac` its fraction ([03-states-and-transitions.md](03-states-and-transitions.md)). `P.time_in`, the time each person has spent in a state, is a number in the sim's unit, as a bare number returned by a function is.

## Conversion

Converting to a timestep is the type's job, not the user's. For a step of length `dt`:

| From | To a per-step probability | To a per-step expected count |
|---|---|---|
| `ss.per(r)` | `1 − exp(−r·dt)` | `r·dt` |
| `ss.prob(p)` per period `T` | `1 − (1 − p)^(dt/T)` | |
| `ss.freq(f)` | | `f·dt` |
| `ss.Duration(d)` | through the rate `1/d` | |

How a solver turns a declared rate into a step is the solver's own choice, made for its accuracy (e.g. the chain binomial takes `r·dt` for the exits from a source of infection: see [12-backends.md](12-backends.md)). **Decided 2026-11-05 (changed):** this was "A solver MUST NOT substitute `r·dt` for `1 − exp(−r·dt)`", removed at Cliff's request ("the spec's 'MUST NOT' is dumb and should be removed"), since the exponential, exact for a single decay, keeps people in a source of infection half a step too long on average, raising R0 by about `r·dt/2`.

**Large steps.** In a run that takes whole steps (`'binomial'`, `'abm'`, or the ODE with Euler steps of a given size), when `rate × dt > 0.1` for a dwell time, the build gives a note, naming the transition, `rate × dt`, the share of people who leave in a step, and what to do (a smaller `dt`, `ss.solvers.ode(substeps=)` or `ss.solvers.binomial(substeps=)`, or `solver='gillespie'`). Under the other solvers, which follow the rates within a step, it is given only for a mean dwell time shorter than the step, which is usually a rate meant as a duration (`rate=10`). It is a note, not an error; `sim.check_dt()` shows how much the results change with a smaller step ([10-execution.md](10-execution.md)).

Continuous-time solvers (`'ode'`, `'gillespie'`) have no `dt` in this sense and do no conversion at all.

## Arithmetic

Starsim's rules, summarized:

| Left | Op | Right | Result | Note |
|---|---|---|---|---|
| `dur` | `+` `−` | `dur` | `dur` | units are converted |
| `dur` | `+` `−` `×` `÷` | number | `dur` | a bare number takes the duration's unit: `ss.days(3) + 2` is 5 days |
| `dur` | `÷` | `dur` | number | |
| `per` | `+` `−` | `per` | `per` | competing hazards add; units are converted |
| `per` | `×` `÷` | number | `per` | |
| `per` | `×` | `dur` | number | the probability of at least one event over the period, `1 − exp(−r·d)`: `ss.perday(0.1) * ss.days(3)` is 0.259 |
| `freq` | `×` | `dur` | number | an expected count, `f·d`: `ss.freqperday(0.1) * ss.days(3)` is 0.3 |
| `prob` | `+` `−` | `prob` | `prob` | through the underlying rates, as competing hazards: `ss.prob(0.1, 'day') + ss.prob(0.1, 'day')` is 0.19 per day, the same as `2 * ss.prob(0.1, 'day')` |
| `prob` | `×` `÷` | number | `prob` | scales the underlying rate, not the probability: `ss.probperyear(0.8) * 0.2` is 0.275 a year, not 0.16 (a relative risk on a probability is a relative risk on its hazard). A probability of 1 is an infinite rate and stays 1; as the rate of a transition it moves everyone in the step (as agents, arrivals in the step too; in compartments, the whole compartment at the start of each step or substep) |
| `prob` | `×` | `dur` | number | the probability over the period |
| rate | `÷` | rate of the same kind | number | |
| number | `÷` | `dur` | `per` | `1 / ss.days(10)` is `ss.perday(0.1)` |
| number | `÷` | `per` or `freq` | `dur` | `2 / ss.perday(0.1)` is `ss.days(20)` |
| `per` | `+` `−` | `prob` or `freq` | error | a `TypeError` |
| rate | `+` `−` | number or `dur` | error | a `TypeError`; a number minus a rate too |
| number | `÷` | `prob` | error | a `TypeError` |
| rate | `×` | rate | error | a `TypeError`: per time squared |
| rate | `÷` | `dur` | error | a `TypeError` |
| `dur` | `×` `÷` | `dur` and rate respectively | error | a `TypeError`: time squared |

Here "rate" is any of `per`, `prob` (with a time unit), and `freq`. Both errors name the two types.

The slot a result lands in is checked too. A rate multiplied by a duration is a plain number, and putting one in a `rate=` slot or after `@` is a mistake, so a `TypeError` points at it:

```text
TypeError: the rate of the transition "recovery" is a plain number (a rate times a duration), not a rate:
       rate = peryear(0.1) * days(3) = 0.00082158
     A rate times a duration is a probability over that duration, not a rate; give the rate itself, e.g. rate=ss.peryear(0.1).
```

The number remembers the rate and the duration it was made from, which is how the slot can tell it from a bare number. The same check applies to the typed values inside an expression, from their time dimensions: in a rate, `ss.perday(0.3) * I * ss.days(3)` is not per unit time and raises, while `R0 * I / ss.days(10)` is and does not; a duration given as `rate=` raises too, as does a rate given as `dur=` (`dur=ss.prob(0.1, 'day')`). A whole duration after `@` is a dwell time, not a rate ([03](03-states-and-transitions.md#what-may-follow-)). A bare number has no dimension of its own, so an expression made of bare numbers is taken at its word.

## Bare numbers

**A bare Python number is accepted in every slot**, with no warning. The slot gives the dimension and the sim gives the unit.

```python
S, I, R = ss.states('S I R')
ss.Transition(S, I, rate=0.05 * I)        # beta, the factor of I, takes the rate's -> 0.05 per unit time
ss.Transition(I, R, dur=10)               # dur= is a duration slot   -> 10 units of time
ss.Transition(I, R, rate=0.1)             # rate= is a rate slot      -> 0.1 per unit time
I >> R @ 0.1                              # after @, a bare number is always a rate
```

A bare number after `@` is a rate, never a duration, because "at" reads as "at rate" and `@ 0.1` and `@ 10` cannot both be guessed from their size. A bare-number duration uses the keyword, `dur=10`.

A slot that can be filled in more than one way (`ss.Transition` takes `dur=` or `rate=`) is decided by which keyword was used, never by the value. The slots and their types are listed in [17-vocabulary.md](17-vocabulary.md).

A typed value (`ss.perday(0.05)`) keeps its own unit and is converted to the sim's. A bare number takes the sim's unit.

### The sim's unit

**The sim's unit** is taken from the first of these that applies:

| | What is given | The sim's unit |
|---|---|---|
| 1 | `unit='day'` | what it says |
| 2 | typed values in the model's diseases, declared or written as code (`dur=ss.days(10)`, or a disease's typed `dt`) | their unit; if they differ, the finest, with a warning when nothing gives the step; if they differ and the model has bare numbers, the unit of the diseases that have them, when those agree (a disease's bare `beta` is in the days of its own durations, beside births per year), else an error asking for `unit=` (which unit the bare numbers are in cannot be guessed). Births and deaths of the whole population (`demographics=`, held by a disease) count only when the disease has no other typed values |
| 3 | `start=` or `stop=` as a date, such as `start='2020-01-01'` | days |
| 4 | a typed `dt` or a typed `start` or `stop`, such as `dt=ss.weeks(1)` | its unit |
| 5 | `start=` or `stop=` as a year, such as `start=2020, stop=2030` | years |
| 6 | typed values in the other modules (networks, demographics, interventions, `ss.Pregnancy`) | the finest of them |
| 7 | none of these | none: time is in timesteps |

The model's unit is a property of the model, so its own typed values come before how the run is written; `dt` then sets only the step. Only `start` and `stop` supply a unit from dates: a date on an intervention or in the data does not. Whether a bare `start` or `stop` is a year is decided as in [Time in a sim](#time-in-a-sim). The unit is never guessed from the size of the numbers: 0.05 is plausible per day and per year.

A function that gives a rate or a duration (`rate=fn`, `dur=fn`) and returns a bare number, in a model whose unit comes from its typed values (rule 2), raises a `TypeError` when the sim runs, saying to return a typed value or give `unit=`: which unit the function meant cannot be guessed, and reading it in the inferred unit gave silent wrong answers when a typed value elsewhere was in weeks (ST33, decided 2026-10-22). Zero is accepted, and with `unit=` given (or no typed values) a bare number is in the sim's unit, as elsewhere.

The rule is the same whether a disease is declared or written as code. The other modules' typed values are their own defaults or settings, which say nothing of the unit of the model's bare numbers, so they count only when nothing else gives a unit. A bare number given for a parameter of a module written as code keeps the unit of its default, as in Starsim 3, with a warning when that differs from the sim's; the networks' `dur=` is in the sim's unit (`ss.RandomNet(dur=5)`, `ss.SexualNet(dur=5)`).

Whenever the unit comes from rules 2 to 6 it is a guess about what the bare numbers meant, so the sim says where it came from, at `init()` and in `describe()`:

```text
>>> ss.Sim(sir, start='2020-03-01', stop='2020-09-01').init()
solver: ode (every part of the model has a compartmental form)
  note: unit='day' (from start and stop dates)
```

and `describe()` shows `unit  day  [from start and stop dates]`.

The default timestep is one unit: one day, one year, or one step; when that comes to more than 3,000 steps and `dt` was not given (ten years in days, say), a warning says so. With no `stop`, a sim runs for 50 units (or 50 steps) from its start. With no `start`, a sim with a calendar in years starts in the year 2000, and any other at 0. The length of the run can be given instead of the stop, as `dur=` (`start=2000, dur=10`, or `start='2020-01-01', dur=ss.days(90)`; a bare number is in the sim's unit): the stop is then the start plus it; any two of `start=`, `stop=` and `dur=` give the third (`stop=2035, dur=10` starts in 2025), all three may be given if they agree (else a `ValueError`), and `sim.new(stop=...)` replaces a `dur=` (and the reverse). `sim.t.dur` is the length either way. A module's `dur=` is a parameter of its own (e.g. `ss.RandomNet(dur=...)`), not a time keyword.

### Time in timesteps

If nothing has a unit (no `unit=`, no unit on any `dt`, no dates, no typed values), time is unitless and counted in timesteps. `beta=0.3` is per step, `dur=10` is ten steps, `stop=100` is 100 steps, results are indexed by step, and nothing is said or assumed about days or years:

```python
S, I, R = ss.states('S I R')
sir = ss.Disease(
    infection = ss.Transition(S, I, rate=0.3 * I),
    recovery  = ss.Transition(I, R, dur=10),
    init_prev = 0.01,
)
ss.Sim(sir, stop=100).run()    # 100 steps
```

This is what a textbook model means. No note is printed, because nothing was guessed; `describe()` shows `unit  none: time is in timesteps`.

- The timestep is one step. With a different `dt`, the bare numbers are per unit of time, a unit with no name: `describe()` then says `time is in units with no name, and a step is 0.1 of them`, `beta = 0.3 per unit`, and `every 0.1 units`, not "per step".
- The times have no dates: `sim.t.datevec` raises, and so does an `ss.seasonal()`, which is a yearly cycle. (The arithmetic is done in days underneath, so a module written as code with typed values, such as `ss.peryear`, takes a step as a day.)
- A unitless sim has no calendar, so it cannot be compared with dated data or given a dated intervention: a date on an intervention is outside the sim (a `ValueError`). Give the sim a unit or dates.
- This differs from Starsim 3, which assumes years when nothing is specified, and which sims with no declared states still do.

## Time in a sim

```python
ss.Sim(sir, start='2020-01-01', stop='2021-06-30', dt=ss.days(1))   # calendar dates
ss.Sim(sir, start=2020, stop=2030, dt=ss.months(1))                 # years
ss.Sim(sir, stop=100, unit='day')                                   # relative time, in days
ss.Sim(sir, stop=100)                                               # relative time, in steps
```

All four are supported. **Whether the sim has a calendar is decided once, from `start`:** a date (a string or an `ss.date`) or a year (a bare number from 1800 on) gives it one; any other number, or a duration (`start=ss.years(2000)`), is a time in the sim's unit from 0, with no calendar. With no `start`, a bare `stop` from 1800 on is a year only if `unit=` is years or not given: `ss.Sim(unit='day', stop=3650)` runs 3,650 days from 0, since the unit is explicit and the stop is not (`unit='day', start=2020` is still a daily sim from 2020). The reading is printed (`unit='year' (from start and stop years)`). Relative time works with or without a unit.

Every other time given to the sim or a module (a bare `stop`, `when=`, the times of `ss.schedule()` and `ss.timeseries()`, `ss.modify()`'s window, a module's `start=` and `stop=`, `sim.run(until=)`) is read on that axis:

- **A bare number** is a calendar year in a sim with a calendar, and a time in the sim's unit from 0 in one without. One above 1000 and below 1800 is read as a time from 0, with a warning that it is ambiguous (for a year that early, give a date). The threshold is 1800 so that a burn-in can start in the 19th century.
- **A duration given as a time** is that long after the sim's start, as in Starsim 3, the same in a list or not: in a sim with a calendar, `when=ss.days(10)` (or `start=ss.days(200)`, `sim.run(until=ss.years(5))`, `ss.schedule(every=ss.years(1), start=ss.months(6))`) is 10 days after the start; in a sim with no calendar it is a point on the sim's own axis counted from 0, the same thing when the start is 0. Every 10 days is `when=ss.schedule(every=ss.days(10))`. It is rounded to a step as dates are, and must fall inside the run. A duration of 1800 years or more (`ss.years(2005)`, as in `sim.t.tvec`) is that calendar year. The sim's own `stop=ss.years(10)` in a sim with a calendar is an error that suggests `dur=ss.years(10)`. A periodic `ss.timeseries` keyed by durations (`period=ss.years(1)`) is read within each cycle from the sim's start, with or without a calendar. (Restored 2026-11-07; for a while a duration as a time was an error in a sim with a calendar.) In a unit other than the sim's or the module's, it warns.
- **As `stop=`**, a duration is read as the start is, a time from 0: `start=ss.years(2000), stop=ss.years(2030)` runs 30 years, and with no start, `stop=ss.days(100)` runs 100 days from 0. In a sim with a calendar, `stop=ss.years(10)` is a `ValueError` that suggests `dur=ss.years(10)` (in a sim of calendar years, `stop=ss.years(2030)` is the year 2030, as above). The length of the run is `dur=`.

`ss.years(2000)` is not `ss.date(2000)`, though they are close: the first is 2,000 years from 0 on a float axis with no calendar (fine for `dt=ss.years(0.1)`), the second the calendar date 2000-01-01, whose steps fall on the calendar's days. `ss.years()` takes a number, not a date string. `ss.date(2020.5)`, a float, is the middle of 2020 and `ss.date('2020-05')` is May; `ss.date('2020.5')` is a `ValueError`, since a string with a decimal point could be either.

The sim's `Timeline` provides the parallel time vectors Starsim already has (`tvec`, `yearvec`, `datevec`, `timevec`, and so on), so output can be requested in the frame the data are in. Nothing is added to it; whether it can be reduced is an open question below.

## The timing contract

A run has N + 1 time points, from `start` to `stop`, and a step is taken from every one of them, the last included, so it takes N + 1 steps: step k goes from time point k to k + 1, and each time point is a period. The full loop is in [10-execution.md](10-execution.md); what a modeler needs is this:

- **One index and one time per step.** Throughout step k, in every phase and every module, `self.ti == k` and `self.now` is time point k, so `self.results.x[self.ti] = v` is right wherever it is written. The first step is `ti == 0`; there is no time point without a step.
- **A row is a period.** At row k, a stock is the state at time point k, the step's start (recorded by `record_stocks()`, before any module's step), and a flow is the total over the step from k to k + 1 (recorded by `record_flows()`, after them, or where it happens). Nothing is 0 or NaN at row 0: its flows are the first step's. The state after the last step is not recorded, so after a run `sim.people` (and an engine's compartments) is one step past the last row.
- **Inputs are read at the step's start.** `self.now` is time point k: values by year, `ss.timeseries`, data labeled by period, and dates (`start=2020` is the first step that starts on or after 2020) are taken there, as in Starsim 3. Code in a step reads this step's stocks at `[self.ti]`; its flows are not known until its end, so `res.x[self.ti - 1]` is the last step's.
- **An infection is dated at the end of its step** (time point `ti + 1`; `ti_I` still reads `ti`, the step it happened in), since it has happened by then. What follows it (a latent period, a recovery) starts then (a disease written as code schedules from `self.ti + 1`, e.g. `self.ti_recovered[uids] = self.ti + 1 + dur`; its seeds are dated by the step before the first, as `self.ti` is -1 while `init_post()` sets their prognoses), so durations ported unchanged from a model that dates infections at the start put the epidemic about a step later (CV5: 11 days on Covasim's daily model, from its latent period). Other moves are taken at the step's start. Either way, `ti_X` reads as the step the move happened in, so `ti_X == self.ti` is "entered this step"; the time spent in a state is its clock, `X.time_in`, not `self.ti - ti_X`, which counts a step more for an infection.
- **A state's count includes people from the time point that ends the step they enter it**, and people stay for their whole dwell, so `X` carries one extra step per stay (ST4: it cost STIsim's trichomoniasis about 14% of its infections against Starsim 3, since people reinfected as soon as they clear are counted per stay).
- **Dwells are whole steps for agents.** A drawn dwell is rounded at random to the step before or after (0.2 steps is 0 steps 80% of the time), which keeps its mean; `dur=0` is instant. The compartmental solvers take dwells as continuous, or as whole slots for a fixed delay.

**Decided 2026-11-05 (changed).** This timing is convention A, adopted at Cliff's request (issue #1548): "'2020' is implicitly taken to mean 2020-01-01 to 2020-12-31 ... 'prevalence' refers to some point during 2020, but 'infections' refers to the total during 2020, whereas B would attribute these infections to 2021". It replaced convention B, in which index 0 was a record-only start with no step, step k went from time point k − 1 to k, `self.now` was time point k − 1, and a flow at row k was over the step that ended at k (so every flow was 0 at row 0).

`describe()` prints the two lines that change counts (CV5 and ST4) for any disease with a transmission.

## Per-module timesteps

A module may have its own timestep:

```python
ss.Sim([sir, ss.Births(dt=ss.years(1))], dt=ss.days(1))
```

Modules with different timesteps are interleaved by absolute time in the loop ([10-execution.md](10-execution.md)). A module with no `dt` uses the sim's. This is Starsim's mechanism, kept as it is.

There are no sub-step offsets. Commuting, which the first draft handled with departure and return times inside a step, is specified instead as the fraction of time a person spends in the destination patch; a commuter contributes to and is exposed in each patch in proportion to the time spent there. See [06-routes.md](06-routes.md).

## Distributions

Distributions use Starsim's names: `ss.normal`, `ss.lognormal` (given the mean and standard deviation of the lognormal itself, `ss.lognormal(mean=, std=)`, or those of its logarithm, `ss.lognormal(log_mean=, log_std=)`), `ss.expon`, `ss.gamma`, `ss.weibull`, `ss.poisson`, `ss.nbinom`, `ss.beta_dist`, `ss.uniform`, `ss.bernoulli`, `ss.constant`, `ss.choice`, and the rest of Starsim's set. Any SciPy distribution can be wrapped with `ss.Dist(dist=...)`. There are two additions: `ss.erlang(k=, mean=)`, an Erlang distribution given by its number of stages and its mean, which is `ss.gamma` with an integer shape (`stages=` on the transition says the same thing); and `ss.truncnorm(mean=, std=, low=, high=)`, a normal distribution truncated to an interval.

**Parameters are named by their moments** where a distribution has them (`ss.normal(mean, std)`, `ss.expon(mean)`, `ss.poisson(mean)`, `ss.gamma(mean=, std=)`), and otherwise by their usual names (`ss.gamma(shape, scale)`, `ss.weibull(shape, scale)`), translated to SciPy's names inside. `loc=` means what it does in SciPy, a shift of the whole distribution (e.g. a shortest duration), and is keyword-only on `ss.gamma` and `ss.weibull`; with a shift, `mean=` is the mean of the whole distribution, shift included (`ss.gamma(mean=, std=, loc=)`, `ss.erlang(k=, mean=, loc=)`). A keyword a distribution does not take is a `TypeError` when it is made, naming those it does (and the moment name for a SciPy one, e.g. `std=` for `scale=` on `ss.normal`).

A distribution is accepted wherever a quantity of the same type is. **Units are given once per distribution**:

```python
ss.lognormal(mean=10, std=3, unit='days')       # the unit applies to both parameters
ss.lognormal(mean=ss.days(10), std=3)           # std inherits the unit of mean
ss.lognormal(mean=10, std=3)                    # no unit: typed by its slot, like a bare number
```

Putting the unit on one parameter is enough; the other parameters of the same dimension inherit it. Shape parameters (`shape` in `ss.gamma` and `ss.weibull`) have no unit.

**In a compartmental run** there are no individuals to draw for, so a distribution is realized in one of two ways. A dwell-time distribution becomes Erlang sub-stages ([03-states-and-transitions.md](03-states-and-transitions.md#dwell-time)). A distribution on a quantity that varies between people, such as `beta` or `rel_sus`, makes the model agent-based under `solver='auto'`; under an explicit `solver='ode'` the mean is used, with a note, and a user who wants the spread kept bins it into a dimension ([05-dimensions.md](05-dimensions.md), [12-backends.md](12-backends.md)).

Random number streams and reproducibility are in [11-random.md](11-random.md).

## What is not typed

- **Counts.** Numbers of people, events, mosquitoes, or bacteria are plain numbers.
- **Money.** `cost=12.50` is a number.
- **Space.** Distances are numbers in the unit of the geography ([06-routes.md](06-routes.md)).
- **Other physical dimensions** (mass, concentration). A state that is not people, such as a water reservoir, holds a number whose unit is whatever the modeler means by it; the cholera example in [03](03-states-and-transitions.md#cholera-an-environmental-reservoir) uses cells/mL and says so in a comment.

Adding a type is a real cost to every user who has to learn it, so the set should stay at Starsim's four unless there is a strong case.

## Open questions

- Whether `ss.prob` keeps its period in the built model or is normalized to a per-step value at build time. The first is more faithful; the second is smaller.
- **The rest of the type lattice.** Adding an `ss.per` to an `ss.freq` or `ss.prob` is an error (above). The rules for every other pair of types need writing down once rather than discovering per operator.
- **Can the Timeline be simpler?** Three views seem irreducible: the step index, time in the sim's own unit, and the calendar date. The other vectors (`yearvec`, `relvec`, `tvec`) could become conversions on request, `sim.t.to('year')`. Whether that is a real simplification needs trying in Starsim.

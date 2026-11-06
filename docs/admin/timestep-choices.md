# Step order: which convention should v4 use? (issue #1548)

Report for [starsimhub/starsim#1548](https://github.com/starsimhub/starsim/issues/1548), 2026-11-04. It covers what the two conventions mean, their pros and cons, what each of v4's influences does (from reading their source, with small runs where that settled a question), and the numerical side: stability, accuracy as the step grows, and how the choice of update interacts with the choice of label.

## Summary

- **The two formulas are usually the same arithmetic with different labels.** `y(t+1) = y(t) + y'(t)` and `y(t) = y(t-1) + y'(t)` both compute the step's flow from the state at its start; they differ only in whether that flow is stored at the index where the step starts (A) or where it ends (B). The numbers are identical, so accuracy and stability are identical too. Read literally, with `y'(t)` evaluated at the new state, B would be backward (implicit) Euler, but none of the 24 frameworks reviewed does that, and nobody in the meeting meant it (as far as I know).
- **In practice there are three conventions, not two:**
  - **B:** stocks at time points, row 0 is the initial condition, and a flow at row k covers the step that ends at k. This is v4 today.
  - **A:** stocks at time points, with row 0 the initial condition, but a flow at row k covers the step that starts at k.
  - **A′:** no initial condition; row k holds the state after step k, labeled with the step's start time. This is Starsim v3 and Covasim.
- **What the influences do.** Of the frameworks that report flows on a grid:
  - B: Starsim v4, camdl, odin 1 and odin2, epidemics, EpiModel's agent models, epiworld, MEmilio, MetaCast, PandemicSimulator, EpiHiper's summary output, TLO's HIV module, and summer2 (approximately).
  - A: Atomica, LASER generic, flepiMoP, EpiModel's ODE models, and individual.
  - A′: Starsim v3, Covasim, EMOD, LASER measles, epydemix, epymorph, and SimInf.
  - In the "Time and units" area of the influences table, the frameworks other than Starsim that use B (camdl, odin, EpiModel, epiworld) carry 19 of the 23 points not held by Starsim.
- **Recommendation: keep B.** It is the majority, and it is what camdl and odin (the most careful of the influences on this point) do and document. It is the only one in which `stock[k] − stock[k−1]` equals the net flow at row k, and `y0 + cumsum(flow)` is the stock. It has a row for the initial condition and no phantom step. A′ is the worst of the three: the stock labeled 2003 is the state at 2004 on a yearly step, and the run covers one step more than `start..stop`.
- **A's real advantages are ergonomic, and B can absorb them.** During a step, A's `ti` and `now` name the same time point, and A's flow labels match data labeled by the start of their period ("cases in 2020", "cases on day 10"). Under B, `sim.now` is the step's start while `sim.ti` is its end, and with a yearly step the infections "in 2020" sit at 2021.0 in the raw array. v4 already handles the second through `resample()` and the fitting code, which put a flow in the period of the step that ends there. What is left is mostly documentation, plus one small API idea (below).
- **The bigger accuracy question is the update, not the label.** At a daily step on an SIR with R0 = 2 and a 4-day infectious period, explicit Euler overestimates the peak by 6%. The `1 − exp(−r·dt)` chain that v4's agents and binomial solver use overestimates it by 28%, because it lengthens the mean infectious period by about dt/2. On an SIS near threshold (R0 = 1.2) it overestimates equilibrium prevalence by 18% even at γ·dt = 0.1, whereas Euler gets the equilibrium exactly at every dt. Updating sequentially within a step (later processes seeing earlier ones' changes) is worse still: −68% on the peak at a daily step. These are much larger effects than anything the labeling choice causes, and they should be the next conversation.

## 1. What the two formulas mean

The issue writes:

```
(A) y(t+1) = y(t) + y'(t)
(B) y(t)   = y(t-1) + y'(t)
```

There are two readings of B.

1. **Relabeling (the usual meaning).** `y'(t)` is "the flow during step t". In A, step t runs from time point t to t+1; in B, it runs from t−1 to t. Both compute that flow from the state at the step's start. So B is A with the flow index shifted by one, and the trajectory of stocks is identical. This is what v4 does, what the meeting was debating, and what every framework below does (when it reports flows at all).
2. **Implicit (the literal meaning).** `y'(t)` is the derivative evaluated at the new state `y(t)`, so B is backward Euler: `y(t) = y(t−1) + dt·f(y(t))`. This is a different numerical method, which needs a nonlinear solve each step (or a linearization). No framework reviewed uses it. Its numerical properties are covered in section 4 for completeness.

The rest of the report takes the first reading unless it says otherwise.

### The third convention (A′)

Several frameworks, including Starsim v3, do neither A nor B cleanly. They run a step from every time point (including the last), record the state after the step, and label it with the step's start time. So:

- there is no row holding the initial condition (in v3, a sim seeded with 100 infections first shows 429);
- the stock at row k is the state at t_{k+1}, but it is labeled t_k;
- a flow and a stock in the same row refer to the same step (the flow over it and the state at its end), which is self-consistent, but the label is the step's start;
- the run covers `start` to `stop + dt`: with `stop=2003` and a yearly step, the last row (labeled 2003) is the state at 2004.

v4 moved from A′ to B (spec `02-types.md` "The timing contract"; `09-results.md`; `10-execution.md` "One time index").

## 2. Pros and cons

### Convention B (v4 today)

Pros:

- **Stocks are at instants, and the initial condition is row 0.** `S[0]` is what the user set. This matches what `scipy.integrate.solve_ivp`, deSolve, odin, camdl and almost every ODE tool return, so a result can be compared with an ODE solution row by row.
- **The accounting identity holds by index.** `X[k] − X[k−1] = inflows[k] − outflows[k]`, and `X[0] + cumsum(net flow)[k] = X[k]`. camdl writes this down as its contract (`state(t_k) − state(t_{k−1}) = Σ flow(t_{k−1}:t_k)`), and summer2's trapezoid flow estimate approximates it. Under A the identity needs an index shift (`X[k+1] − X[k] = flow[k]`), which is a classic off-by-one.
- **No phantom step and no missing row.** N steps give N+1 time points; the flow at row 0 is 0, which is true (nothing has happened yet). Under A the last flow row covers a step after the end, which has to be filled somehow: Atomica fills it with a step it never runs, flepiMoP's last incidence row covers a day past the end date, and EpiModel's ODE models copy the last-but-one value.
- **Changing dt doesn't move the label times.** Stocks at 2020.0 are at 2020.0 whatever the step. (Under A′, the state labeled 2020 is the state at 2020 + dt, so changing dt changes what "2020" means.)
- **Cumulative results line up.** `cum_infections[k]` is the number infected by time point k, which is what "cumulative by date" means in surveillance.
- **It's what the time-type influences do.** camdl and odin both use B and explain why. odin2's `zero_every` takes it as given: an accumulated value at integer time t is the total over (t − p, t], "as if happening at t + eps".

Cons:

- **Two times in a step.** During step k, `sim.ti == k` (where the results go) but `sim.now` is time point k−1 (where inputs are read). Code that does `if self.now >= date:` and `self.results.x[self.ti]` is right, but someone who reads `ti` as "the current time" is one step off. This is the main ergonomic cost.
- **Period-labeled data are labeled by their start, and B labels a flow by its end.** Annual data for "2020" cover [2020, 2021). With a yearly step, the flow over that year is at row 2021.0 under B, and at row 2020.0 under A. The same is true for daily data ("cases on day 10" covers [10, 11)). A user plotting the raw arrays against data labeled this way sees a lag of one step. v4's `resample()` and `sim.fit()` handle this correctly (a time point belongs to the period of the step that ends there, so 1 January is in the previous year, and periods are labeled by their end or by year: `starsim/results.py:873, 899, 906-913`), but a raw `plot(timevec, new_infections)` against such data is off by one step.
- **Row 0 of every flow is zero.** That costs nothing, but it shows up as a dip at the start of a plot of incidence, and a rate computed per row (incidence / population) has a zero there.
- **Interventions on a date read as "the step that starts on that date".** An intervention dated d affects the flow recorded at d + dt. This is correct, but it has to be explained.

### Convention A

Pros:

- **One time per step.** During step k, `ti` and `now` are the same time point, so coded modules have one notion of "now". This is what users intuitively write: `for t in range(T): flow = rate*y[t]; y[t+1] = y[t] + flow`.
- **Flow labels match period-start data.** `new_infections[2020]` is the number in calendar year 2020; "doses on day 10" are at row 10. This is probably why Atomica, which is built around annual programmatic data, uses it.
- **A flow and the state it was computed from are in the same row.** `incidence[k] = beta*S[k]*I[k]/N` exactly, which is handy when checking a model by hand.

Cons:

- **The last flow row is undefined,** or it costs an extra step past the end (see above).
- **A stock and a flow in the same row refer to different times:** an instant, and the interval after it. The accounting identity needs a shift.
- **Writing results from a coded step is inconsistent:** during step k, the step's flows go to row k but the state it produces goes to row k+1. This is part of why Starsim v3 drifted into A′: it wrote both to row k.
- **Resampling sums over [t, t + Δ),** so a stock at the end of a period and the flow over it have different labels.

### Convention A′ (Starsim v3, Covasim, EMOD, epydemix, epymorph, SimInf, LASER measles)

Pros: one index per step, and a stock and a flow in the same row refer to the same step. Cons: no initial condition; stocks labeled one step early; one extra step past `stop`; and comparing with an ODE solution needs a shift. In SimInf, for example, the row labeled t is the state after day [t, t+1), so with u0 = (1000, 10, 0) the first row is (993, 16, 1). Nobody argued for this in the meeting, and v4 has already left it.

## 3. What each influence does

The frameworks are those reviewed in `lingua_franca/docs/approaches/` and counted in `influences.yaml`, plus the three "other" frameworks named there (Covasim, MIRA, PyRoss). All were read from source; most were also run on a two- or three-step SIR. Answers are as of the versions in `lingua_franca/_envs/`, or shallow clones of each project's default branch (2026-11-04). The full write-ups, with file and line citations for each answer, are in the session scratchpad (`working/timestep/group1.md` to `group4.md`; see the end).

"IC" is the initial condition. "Inputs" is when values that vary in time (forcing, schedules, interventions) are read. "Within step" is whether processes in one step all see the state at the step's start (simultaneous) or later ones see earlier ones' changes (sequential).

| Framework | Paradigm | Output rows | Flow label | Inputs read at | Update scheme | Within step | Conf. |
|---|---|---|---|---|---|---|---|
| **Starsim v4** | agents, compartments, ODE | N+1, IC first | **B** | step start | 1−exp(−r·dt), competing hazards, multinomial | sequential across modules (agents); simultaneous (compartmental) | high |
| Starsim v3 | agents | N+1, all after the step, no IC | **A′** | step start | 1−exp(−r·dt) | sequential | high |
| Covasim 3.1.9 | agents, daily | n_days+1, after the step, no IC | **A′** | day start | linear per-contact probability; scheduled dates | sequential | high |
| camdl | chain binomial, ODE, SSA | N+1, IC first (documented invariant), with `t_start`/`t_stop` columns | **B** | step start; interventions at step end, after the draws | Euler-multinomial (as pomp); RK4 or DOPRI5; Gillespie | simultaneous | high |
| odin 1 | difference equations, ODE | requested times, IC first | **B** | step start | user's binomial chain; lsoda or dopri | simultaneous | high |
| odin2 / dust2 | discrete, ODE | requested times, IC first | **B** (`zero_every`) | step start (documented) | binomial chain; adaptive Dormand–Prince | simultaneous | high (read, not run) |
| epidemics (ODE models) | ODE | IC first | **B** (by differencing) | continuous | lsoda | n/a | high |
| epidemics (Ebola) | stochastic discrete | IC first | **B** | t = k+1 for the step (k−1, k] (an off-by-two) | binomial + Erlang boxcars | simultaneous | high |
| EpiModel DCM | ODE | IC first, from t=1 | **A** | continuous | lsoda | n/a | high |
| EpiModel ICM / netsim | agents, networks | IC first, from t=1 | **B** | step end (`at`) | Bernoulli, rates used as probabilities | sequential | high |
| epiworld | agents, daily | IC first | **B** | global events at step end | Bernoulli + roulette | simultaneous | high |
| MEmilio | ODE, IDE, LCT, SDE, agents | IC first; adaptive solver gives irregular rows | **B** (cumulative, differenced) | continuous; Euler at start; agents at midpoint | RK54, Euler, Euler–Maruyama | simultaneous, then mobility | high/medium |
| MetaCast | ODE + events | IC first | **B** | at event time | lsoda, piecewise | n/a | high |
| PandemicSimulator | ODE, stochastic Euler | IC first | **B** | step start | Dormand–Prince; Euler + Poisson, clipped ≥ 0 | simultaneous | high |
| EpiHiper | network agents, ticks | IC first | **B** (summary); A (event log) | tick start | 1−exp(−A·T·Δ), whole-tick dwells | simultaneous | high |
| TLO | discrete events + polling | no grid; logged at period end | **B** (HIV) | event or poll date | linear probability per poll | sequential | medium |
| summer2 | ODE | N+1, IC first | **≈B** (trapezoid of the rates at t_{k−1} and t_k) | continuous | adaptive Dormand–Prince (Euler, RK4 optional) | simultaneous | high |
| Atomica | difference equations | N+1, IC first | **A** (documented: "the actual flow at 2015.0 divided by dt") | step start | Euler on fractions (rate·dt, no 1−exp), rescaled if above 1 | simultaneous (junctions in order) | high |
| LASER generic | spatial agents | N+1 stocks, IC first | **A** (comment: "state(t+1) = state(t) + ∆state(t)") | step start | 1−exp(−λ), timers | sequential components | high |
| LASER measles | compartmental, agents | N, after the step, no IC | **A′** | step start | binomial chain | simultaneous within a process | medium |
| flepiMoP | compartments, several places | N+1 days; prevalence at start of day | **A** (last incidence row runs a day past the end) | that day's value | RK4 (default dt = 2 days); "euler" is really a 1−exp chain | simultaneous; caps in order | high |
| individual | agent toolkit | N, no IC (rendered before each step; final state never rendered) | **A** | step start | Bernoulli | simultaneous, last update wins | medium-high |
| EMOD | agents (C++) | N, after the step, no IC | **A′** (by row) | step start | 1−exp(−λ·dt), infection sub-steps | pool simultaneous; individuals sequential | medium-high |
| epydemix | chain multinomial | N rows (one step more than the period), no IC; row k = after step k, labeled t_k | **A′** | step start | multinomial, 1−exp(−Σr·dt) | simultaneous | high |
| epymorph | Poisson tau-leap, several places | N, no IC (stored separately) | **A′** | step start (daily) | Poisson(rate·τ), overruns corrected | simultaneous; movement before disease | high |
| SimInf | exact CTMC + daily events | no IC; row t = after day [t, t+1) | **A′** | exact t; events after the day's CTMC | Gillespie direct | sequential | high |
| Vivarium | phased agents | no time series by default | either (event time is the step's end) | step start | linear rate·dt clipped to 1, or exponential | sequential | medium |
| epipack | ODE + Gillespie | requested times, IC first | n/a (no flows) | continuous | dopri5 or Euler; Gillespie | one event at a time | high |
| EMULSION | stochastic compartments, agents | IC first | n/a (no flows) | step start | competing hazards, multinomial | simultaneous within a process | high |
| EoN | Gillespie, generations, ODE | IC first; one row per event | n/a | none | SSA; Reed–Frost generations; LSODA | simultaneous | high |
| MIRA | ODE wrapper | IC first | n/a | n/a | vode | n/a | medium |
| PyRoss | ODE, SSA, tau-leaping | IC first | n/a | continuous | odeint; SSA; tau-leaping | n/a | medium |

### Tally

| Convention | Frameworks |
|---|---|
| **B** | Starsim v4, camdl, odin 1, odin2, epidemics, EpiModel (agent models), epiworld, MEmilio, MetaCast, PandemicSimulator, EpiHiper (summary), TLO (HIV), summer2 (approximately) |
| **A** | Atomica, LASER generic, flepiMoP, EpiModel (ODE models), individual |
| **A′** | Starsim v3, Covasim, EMOD, LASER measles, epydemix, epymorph, SimInf |
| n/a | epipack, EMULSION, EoN, MIRA, PyRoss, Vivarium |

Some patterns:

- **Every framework that writes the initial condition as row 0 also uses B, except Atomica, LASER generic, flepiMoP and EpiModel's ODE models.** Frameworks built around an ODE solver arrive at B naturally: the solver returns states at requested times, and incidence is the difference of cumulative counts between them.
- **A′ is mostly found in agent-based and stochastic frameworks.** In these, "run the step, then record" is the natural loop body, and nobody stops to write down the initial state.
- **Several frameworks mix conventions internally,** which is the strongest evidence that the choice is easy to get wrong:
  - EpiModel's ODE models use A and its agent models B.
  - EpiHiper's summary is B and its event log A.
  - EoN's `discrete_SIR` logs transmissions at a generation's start and statuses at its end.
  - flepiMoP has prevalence at time points but incidence over the following day.
  - In odin 1, an `output()` and an accumulator in the same row cover different intervals.
  - LASER's two layers differ.
- **Reading inputs at the step's start is universal** among discrete-time frameworks. The exceptions are EpiModel's agent models and epiworld (global events at the step's end), MEmilio's agents (midpoint), and epidemics' Ebola model (an off-by-two bug, below).

### Side findings: bugs and oddities in other frameworks

These came up while reading, and might be worth writing up for their authors (they are not v4 issues):

- **epidemics (Ebola):** the loop index is R's row index, so the step from k−1 to k reads time-varying inputs at t = k+1. In the ODE models, contact and rate interventions are active only strictly inside (begin, end), while vaccination includes both ends.
- **EMULSION `--deterministic`:** each flow is `(exp(r·dt) − 1)·pop` instead of `(1 − exp(−r·dt))·pop`: 525.9 people left I in one step where 475.8 is exact and Euler gives 500. Nothing stops a flow from exceeding the population.
- **PyRoss Gillespie:** the state written at each output time already includes the first event after that time.
- **MIRA** always integrates from t = 0, whatever the first requested time is.
- **MEmilio** ramps a contact damping dated T in over [T−1, T], so it is fully on at T. Its default adaptive solver returns rows at irregular times (0, 1, 2.81, 3 for dt = 1).
- **epipack's Gillespie output** stops when events run out or the next event falls after `tmax`: `tmax=50, sampling_dt=1` returned times 0–3 only.
- **individual** never renders the final state.
- **flepiMoP** fills odd days by interpolation at its default dt of 2 days and halves incidence.
- **Atomica** computes flows for one step after the last time point, a step that is never run.
- **Starsim v3 and Covasim** run a step at every one of the N+1 time points, so they simulate one dt past `stop`.

## 4. Numerical considerations

Everything here is from one script (`numerics.py`, see the end): a deterministic SIR with β = 0.5/day and γ = 0.25/day (R0 = 2, a 4-day infectious period, I0 = 0.1%, 100 days), compared with an adaptive ODE solution at a tolerance of 1e−11. The schemes compared:

| Scheme | Update | Who uses it |
|---|---|---|
| Euler | `y += dt·f(y)`, all flows from the start of the step | Atomica, PandemicSimulator (stochastic), epymorph (Poisson, in expectation), the linear-probability frameworks (Covasim, TLO, Vivarium, EpiModel's agents), approximately |
| Exponential | each outflow is `x·(1 − exp(−h·dt))`, hazards pooled per source | Starsim v3/v4 (agents and binomial solver), camdl, odin's idiom, epydemix, LASER, EMOD, EpiHiper, EMULSION |
| Sequential | Euler, but recovery uses I after this step's infections are added | agent frameworks that run processes in order without a correction (EpiModel's agents; v4's agents before the half-step correction) |
| Implicit | backward Euler, `y(t) = y(t−dt) + dt·f(y(t))` | none |
| Heun | explicit trapezoid (RK2) | none as a default |
| RK4 | classical Runge–Kutta | flepiMoP, camdl's ODE backend |

The label (A or B) doesn't enter any of this, since the numbers are the same under both. The one place where it does matter (comparison with data) is in section 4.5.

### 4.1 Accuracy as the step grows

Relative error in peak prevalence, the time of the peak (days), and final size:

| Scheme | dt (days) | γ·dt | Peak | Peak time | Final size |
|---|---|---|---|---|---|
| Euler | 0.1 | 0.025 | +0.6% | +0.3 | +0.2% |
| Euler | 1 | 0.25 | +6.0% | +2.0 | +1.8% |
| Euler | 4 | 1.0 | +27% | +9.0 | +9.0% |
| Euler | 7 | 1.75 | +46% | +15 | +20%, and I goes negative |
| Exponential | 0.1 | 0.025 | +2.8% | +0.1 | +0.8% |
| Exponential | 1 | 0.25 | +28% | +1.0 | +7.3% |
| Exponential | 4 | 1.0 | +105% | +5.0 | +19% |
| Exponential | 7 | 1.75 | +156% | +15 | +24% |
| Sequential | 0.1 | 0.025 | −7.5% | +1.3 | −1.6% |
| Sequential | 1 | 0.25 | −68% | +18 | −26% |
| Sequential | 2 | 0.5 | epidemic fails | | −95% |
| Implicit | 1 | 0.25 | −5.8% | −2.0 | −1.6% |
| Implicit | 4 | 1.0 | −20% | −11 | −5.7% |
| Heun | 1 | 0.25 | −0.1% | 0.0 | 0.0% |
| Heun | 7 | 1.75 | −3.4% | +1.0 | −1.8% |
| RK4 | 1 | 0.25 | 0.0% | 0.0 | 0.0% |
| RK4 | 7 | 1.75 | −0.3% | +1.0 | 0.0% |

(The ±1 day on the peak time for Heun and RK4 at coarse steps is the output grid, not an error.)

Observed order of convergence (error in I at day 20, halving dt from 1 day): Euler 0.96, implicit 0.98, exponential 0.63 and sequential 0.65 (both approaching 1 as dt shrinks), Heun 1.93, RK4 3.92. So all the schemes in use for stochastic models are first order: halving dt halves the error. Heun costs two evaluations of the rates per step and is second order. RK4 costs four and is fourth order.

### 4.2 Why the exponential update is less accurate than Euler here

This looks backwards, since `1 − exp(−r·dt)` is exact for a single decay and Euler is not. For a coupled system, however, the per-step chance of recovering is `1 − exp(−γ·dt)`, which is less than `γ·dt`. So the mean number of steps someone stays infectious is `1/(1 − exp(−γ·dt))`, i.e. a mean time of about `1/γ + dt/2`, while they transmit at the full rate for every step they are in I. The effective R0 is therefore about `R0·(1 + γ·dt/2)`. With Euler, the mean stay is exactly `1/γ`, and the two errors (both flows overestimated per step) cancel in the ratio.

The SIS equilibrium shows this cleanly. At R0 = 1.2, the exact prevalence is 1 − 1/R0 = 0.1667:

| γ·dt | Euler | Exponential | Sequential | Implicit |
|---|---|---|---|---|
| 0.1 | 0.1667 | 0.1975 (+18%) | 0.0741 | 0.1667 |
| 0.5 | 0.1667 | 0.2863 | 0 | 0.1667 |
| 1.0 | 0.1667 | 0.3536 | 0 | 0.1667 |
| 2.0 | 0.1667 | 0.4252 | diverges | 0.1667 |

Euler and implicit Euler both have the exact equilibrium at every dt, because a fixed point of `y + dt·f(y)` is a fixed point of `f`. The exponential update moves it by the effective R0 above. The sequential update moves it the other way, because someone infected and then recovered in the same step never transmits: the effective R0 is about `R0·(1 − γ·dt)`.

This is the same effect that the v4 spec already corrects for agents (`10-execution.md`: an SIS at R0 = 1.2 with a quarterly step gave 0.068 where the exact value is 0.167, before the half-step correction). The binomial chain in the compartmental solver and the ODE comparison don't get that correction (as far as I can tell), and `02-types.md` says "A solver MUST NOT substitute `r·dt` for `1 − exp(−r·dt)`". The exponential rule buys bounded probabilities and positivity, but its price is a bias of order γ·dt/2 in R0, which is large near threshold and in endemic models. This is worth a separate issue. It might be possible to keep the exponential for positivity and correct the infectious period by half a step, as the agents already do.

### 4.3 Stability and positivity

For a pure decay `y' = −r·y`, the factor by which one step multiplies y:

| r·dt | Exact | Euler | Exponential | Implicit | RK4 |
|---|---|---|---|---|---|
| 0.5 | 0.607 | 0.500 | 0.607 | 0.667 | 0.607 |
| 1 | 0.368 | 0 | 0.368 | 0.500 | 0.375 |
| 1.5 | 0.223 | −0.5 | 0.223 | 0.400 | 0.273 |
| 2 | 0.135 | −1 | 0.135 | 0.333 | 0.333 |
| 3 | 0.050 | −2 | 0.050 | 0.250 | 1.375 |
| 5 | 0.007 | −4 | 0.007 | 0.167 | 13.7 |

- **Euler** goes negative when r·dt > 1 and diverges in oscillation when r·dt > 2. That is a weekly step with any rate above 1 a week, or a yearly step with background mortality in a high-hazard group. Atomica clips and rescales; PandemicSimulator clips at zero. In the SIR above, Euler at dt = 7 days gives I = −0.07.
- **The exponential update** never goes negative and is exact for a single linear outflow, at any step. This is its real strength, and it's why chain-binomial models use it: a probability is always in [0, 1].
- **Implicit Euler** is stable at any step, but it damps: at r·dt = 5 it keeps 17% where 0.7% is right. For nonlinear models, it needs a solve each step (my Newton solver failed to converge at dt = 7).
- **RK4** is far more accurate but has its own stability limit, r·dt ≈ 2.8, beyond which it blows up. Of the influences, only flepiMoP and camdl use it on a fixed grid. Adaptive solvers (lsoda, Dormand–Prince) avoid the issue by shrinking their step.

### 4.4 When to read inputs that vary in time

With β(t) = 0.5·(1 + 0.5·sin(2πt/30)) and Euler, reading β at the step's start, middle or end gives a maximum error in I of 0.042, 0.040 and 0.040 at dt = 0.5, and 0.119, 0.115 and 0.117 at dt = 2. The state's own first-order lag dominates, so with a first-order update the choice hardly matters, and the step's start is the consistent choice: the whole step is then a left-endpoint rule. Reading at the midpoint is only worth it with a second-order update. This supports what v4 and almost every influence does.

### 4.5 When the label does matter: comparing with data

The label has no effect on the numbers, but it says which interval each count covers, so a mismatch with the data shifts the comparison by a step. Here is the RMS error of each step's count of new infections against the exact count over its interval, as a share of the peak, when the model's label matches the data's and when it is off by one step:

| Scheme | dt | Matched | Off by one step |
|---|---|---|---|
| RK4 | 0.1 | 0.0% | 0.3% |
| RK4 | 1 | 0.0% | 3.4% |
| RK4 | 7 | 1.0% | 22% |
| Heun | 1 | 0.5% | 3.0% |
| Heun | 7 | 11% | 14% |
| Euler | 1 | 8.4% | 5.2% |
| Euler | 7 | 45% | 33% |

With an accurate update, getting the label wrong costs a lot at a weekly step (22% vs 1%). With Euler, the off-by-one comparison happens to look *better*, because Euler's epidemic runs late by about a step (the growth rate of `(1 + r·dt)^(t/dt)` is lower than r), and the wrong label cancels part of that lag. That is a coincidence of the scheme, not an argument for either label. But it is a warning: a model fitted with the wrong label at a coarse step will absorb the error into its parameters. Whichever convention v4 uses, the fitting and resampling code must put each flow in the period it covers, as v4's already does.

## 5. Recommendation

1. **Keep convention B,** as the spec and code have it now. It is what the frameworks closest to v4's time design use (camdl, odin), it has the accounting identity by index, it keeps the initial condition, and it needs no phantom step. A gains one thing B lacks (a single notion of "now" in a step) and loses several, and A′ should not come back.
2. **Make B's two costs visible, rather than changing the convention:**
   - In the docs for coded modules, put "during step k, `self.ti` is k (where this step's results go) and `self.now` is time point k−1 (when the step starts)" next to the first example that uses either. `10-execution.md` says this, but users will meet it in the tutorial. A short alias such as `self.t_start`/`self.t_end` (or `self.step_start`/`self.step_end`) on the module would let code say which one it means. That is a small API idea for Cliff to decide, not something I'd add without asking.
   - For results against data labeled by the start of their period, keep relying on `resample()` and `sim.fit()`. Consider having `to_df()` (or `res.plot()` when a flow is plotted against data) show the interval each row covers, as camdl's `t_start`/`t_stop` columns do. Then a raw annual flow labeled 2021.0 reads as "2020.0–2021.0" and nobody is misled.
3. **Open a separate issue for the update scheme.** This is the larger effect:
   - The exponential chain's +γ·dt/2 bias in R0: +28% on the peak at a daily step in the SIR above, and +18% on SIS prevalence at γ·dt = 0.1.
   - Sequential updates within a step: −68% on the peak at a daily step, which v4's half-step correction already handles for agents.
   - Whether the compartmental chain binomial should get the same half-step correction that the agents have.
   - Whether the "MUST NOT substitute r·dt" rule in `02-types.md` should allow an Euler option for deterministic runs, where it is exact at equilibrium. (`solver='ode'` with an adaptive method already sidesteps all of this for deterministic models.)

## Sources and reproducibility

- Framework findings, with file and line citations for each answer: `working/timestep/group1.md` (Atomica, summer2, epipack, epydemix, epymorph, flepiMoP), `group2.md` (odin, epidemics, EpiModel, SimInf, epiworld, individual), `group3.md` (Starsim v3 and v4, Covasim, LASER, EMOD, TLO, Vivarium), and `group4.md` (camdl, MEmilio, EMULSION, EoN, EpiHiper, MetaCast, PandemicSimulator, MIRA, PyRoss). The check scripts and shallow clones of the frameworks with no local copy are in `group1/` to `group4/` beside them, and the brief the agents worked from is `BRIEF.md`.
- Numerical comparisons: `working/timestep/numerics.py` (`python numerics.py`; about a minute, single-threaded), and `expomid.py` (an exponential update with midpoint hazards, which did not reduce the bias).
- v4's convention: `lingua_franca/docs/design/02-types.md` ("The timing contract"), `09-results.md`, and `10-execution.md` ("One time index"); `starsim/internals/loop.py:78-86`; `starsim/results.py:857-913`.

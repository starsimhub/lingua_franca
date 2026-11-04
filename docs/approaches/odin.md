---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# odin / odin2 (with dust and monty)

|  |  |
|---|---|
| **Language** | R DSL, compiled to C++ (and optionally JavaScript) |
| **Paradigms** | Continuous-time ODE; discrete-time stochastic (difference equations with distributional draws) |
| **Specification style** | Embedded DSL (R syntax, non-R semantics) compiled |
| **Version reviewed** | odin2 0.3.46 |
| **License** | MIT |
| **Code** | <https://github.com/mrc-ide/odin2>, <https://github.com/mrc-ide/dust2>, <https://github.com/mrc-ide/monty> |
| **Docs** | <https://mrc-ide.github.io/odin2>, the [odin & monty book](https://mrc-ide.github.io/odin-monty/) |
| **Paper** | dust: [10.12688/wellcomeopenres.16466.2](https://doi.org/10.12688/wellcomeopenres.16466.2) |
| **Ecosystem** | odin (DSL) → dust (parallel simulation engine) → monty (Monte Carlo inference); ~5 current packages |
| **Moving to Starsim** | [Conversion guide](https://starsim.org/v4/user_guide/conversion/odin.html) |

## What it's for

odin lets a modeler write differential or difference equations much as they would on paper, and get compiled C++ with a particle filter and MCMC attached. It is the workhorse behind much MRC Centre / Imperial modeling, and the closest thing in R to camdl.

The design is three packages: **odin** is a language, **dust** runs models, and **monty** does inference, and they connect through defined interfaces. An odin model compiles to the dust interface, and monty runs particle filters and MCMC on anything that implements it, odin-generated or not.

## How a model is specified

The modeling language looks like R (R's parser reads it) but is not R. Every line is either an **assignment** (`a <- expr`) or a **relationship** (`b ~ Distribution(...)`). `if` exists only as an inline expression, and loops exist only implicitly through array indexing.

A discrete-time stochastic SIR:

```r
gen <- odin2::odin({
  p_IR <- 1 - exp(-gamma * dt)
  N <- parameter(1000)

  p_SI <- 1 - exp(-(beta * I / N * dt))
  n_SI <- Binomial(S, p_SI)
  n_IR <- Binomial(I, p_IR)

  update(S) <- S - n_SI
  update(I) <- I + n_SI - n_IR
  update(R) <- R + n_IR

  initial(S) <- N - I0
  initial(I) <- I0
  initial(R) <- 0

  beta <- parameter(0.2)
  gamma <- parameter(0.1)
  I0 <- parameter(10)
})
```

The continuous-time version replaces `update()` with `deriv()`. **The variables of the system are determined by the presence of `initial()`**, which is common to both, so the same detection logic serves both paradigms.

**The order of statements does not matter**: odin works out the order from the dependencies. The model is a set of equations, not a sequence of operations.

Running is handled separately, by dust:

```r
pars <- list(beta = 0.2, gamma = 0.1, I0 = 10, N = 1000)
sys  <- dust2::dust_system_create(gen(), pars, n_particles = 10)
dust2::dust_system_set_state_initial(sys)
y <- dust2::dust_system_simulate(sys, 0:100)
```

## Core abstractions

| Concept | odin name | Notes |
|---|---|---|
| State variable | anything with an `initial()` | `deriv()` for ODEs, `update()` for discrete time |
| Derived quantity | ordinary assignment | Order-independent; topologically sorted at compile time |
| Parameter | `parameter(default, constant=, differentiate=, type=, rank=)` | Typed (`real`/`integer`/`logical`), with defaults and a differentiability flag |
| Array | `x[]`, with a mandatory `dim(x) <- ...` | Up to 8 dimensions; implicit loops driven by the *left*-hand side |
| Output | `output(y) <- expr` | ODE-only: quantities reported as state without having derivatives |
| Data | `d <- data()` | A time series to compare against |
| Likelihood | `cases ~ Poisson(incidence)` | Comparison to data written in the model file |
| Accumulator | `initial(incidence, zero_every = 1) <- 0` | Auto-resetting accumulator for incidence-style quantities |
| Interpolation | `interpolate(time, value, mode)` | `constant`, `linear`, or `spline` external time series |
| Delay | `delay(...)` | Delay differential equations, with explicit history state |
| Time step | `dt` | Available as a variable in discrete-time models |

## Time

Time is `time`, the step is `dt`, and both are available inside the model. This matters: the modeler writes `p_SI <- 1 - exp(-beta * I / N * dt)` explicitly, so the conversion from rate to probability is *visible in the model*.

This is a defensible choice, and the opposite of Starsim's (where `ss.peryear(0.1).to_prob(dt)` leaves the conversion to the value). odin's way is more transparent and less safe: nothing stops a modeler writing `p_SI <- beta * I / N * dt`, which is correct only for small `dt`, and nothing marks `beta` as a rate. **There are no units or dimensions.** Parameters are `real`, `integer`, or `logical`.

For discrete-time models, the order of events within a step is documented: reset `zero_every` accumulators, read variables, look up interpolations at `t0`, evaluate all assignments (with `time = t0` and all variables at start-of-step values), write new state, and advance time. Then, separately, compare to data at `t0 + dt`. Few frameworks here write this down.

## Stochasticity and reproducibility

Discrete-time models draw from distributions inline: `n_SI <- Binomial(S, p_SI)`. What a draw means is defined with care: `x[] <- Normal(0, 1)` gives every element its own draw, while `a <- Normal(0, 1); x[] <- a` gives every element the same draw. Most frameworks leave this unclear.

Continuous-time models cannot sample: stochastic functions are rejected in ODE mode, an error and not a silent approximation, which is the right choice.

dust runs `n_particles` in parallel, each with its own random stream. There are no common random numbers across scenarios.

## Comparison to data

The likelihood lives in the model file, in two extra lines:

```r
cases <- data()
cases ~ Poisson(incidence)
```

`data()` says a variable comes from the data time series, and `~` adds a log-likelihood term. `dust_filter_create()` builds a particle filter, `dust_likelihood_run()` returns a marginal likelihood estimate, and monty runs MCMC over it.

The `zero_every` accumulator deserves special mention: `initial(incidence, zero_every = 1) <- 0` is a quantity that accumulates within a period and then resets. Incidence per unit time is the most commonly needed output in the field, and this is the neatest way of declaring it in the review.

## Arrays and stratification

There is no stratification *operator*. Age structure, spatial patches, and strata are written as array dimensions:

```r
update(S[]) <- S[i] - n_SI[i]
dim(S) <- n_age
lambda[] <- sum(m_beta[i, ])
ax_tmp[, ] <- a[i, j] * x[j]
ax[] <- sum(ax_tmp[, i])
```

Loop extents come from the left-hand side; `i`, `j`, `k`, `l` are the index variables; `dim()` is mandatory and checked at parse time; `sum()` supports partial sums over slices, which is how contact-matrix products are written.

This is powerful and correct, and lower-level than `summer2`'s `stratify_with()` or camdl's `stratify(by = age)`. Adding age to an odin model means rewriting every equation with indices; in summer2 it means one extra call. In return, odin has no restrictions: any indexed structure you can write works, while a stratification function supports only what it implements.

## Strengths

- **The model is a set of equations, not a program.** Order does not matter.
- **One language, two paradigms.** ODE via `deriv()`, discrete-time stochastic via `update()`, with `initial()` common to both.
- **Compiled.** Generated C++ gives serious performance from a language that reads like maths; a JavaScript target exists and CUDA is planned.
- **Language, engine, and inference are separate.** monty works with any dust model.
- **The likelihood is in the model.** Two lines, and the particle filter follows.
- **`zero_every` accumulators**: the best answer in the review to "how do I declare incidence".
- **Documented order of events** for discrete-time models, including where data comparison happens.
- **Careful rules for random draws**, including scalar versus array draws.
- **Differentiability as a parameter attribute** (`differentiate = TRUE`), checked with `constant` and `type` at compile time.
- **Restricted names are checked** against C, C++, and JavaScript keywords, so generated code cannot collide.

## Limitations

- **No dimensional types.** Rates, probabilities, counts, and durations are all `real`. The `1 - exp(-r*dt)` conversion is written by hand every time, and writing `r*dt` is not an error.
- **Compartmental only.** No agents, no networks, no individual heterogeneity.
- **Stratification is manual.** Adding a dimension means editing every equation.
- **No intervention vocabulary.** Time-varying parameters go through `interpolate()`, and anything else is an equation the modeler writes. There are no scheduled actions, coverage levels, or targeted subgroups.
- **No common random numbers**, so scenarios cannot be paired.
- **Tied to R.** The model is written inside an R call, and parsed and compiled through R's tools. The only route outside R is the JavaScript target.
- **Delays carry hidden state**, and the docs note that continuing a delayed system is not the same as starting one from a given state. This remains unresolved.
- **`parameter(rank = 2)`**, for array dimensions set by data, is an interface the authors expect to change.

## Implications for the lingua franca

1. **Independence from statement order is a requirement.** It is what lets a model be read as a description, not run as a script. If statements had to be read in order, that order would be hidden behavior.
2. **One `initial()` for both paradigms is the right division.** odin finds the state of the system from what has an initial condition, and `deriv()` or `update()` chooses the paradigm. This is a small, elegant version of the paradigm independence this project wants: the states are shared, and only the dynamics differ.
3. **Take `zero_every`.** Accumulators that reset themselves solve the incidence problem in general. With camdl's `incidence(transition)`, this nearly settles how outputs are declared.
4. **Take the rule for random draws**: an assignment to an array draws once per element, and a scalar assigned to an array draws once. State it in the spec, because this ambiguity gives silently wrong models.
5. **Document the order of events for each paradigm, in the spec.** odin does this for discrete time in a dozen lines. A multi-paradigm language needs it for each paradigm, and for how they interleave.
6. **Do not copy the untyped rates.** Writing `1 - exp(-r*dt)` by hand is transparent, but dimensional types exist to check this arithmetic. camdl and Starsim do better here. The lingua franca can keep the transparency by showing the expansion of a typed rate.
7. **Weigh arrays against a stratification function.** odin's arrays are fully general and laborious; summer2's `stratify_with()` and camdl's `stratify(by = ...)` are the opposite. The lingua franca probably needs a function for common cases with explicit indexing underneath, documented as a shorthand for the indexed form, as camdl does.
8. **Separate language, engine, and inference.** The odin/dust/monty split means an engine can be replaced, and the inference layer works for models not written in the language.

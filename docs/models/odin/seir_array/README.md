# odin: age-structured SEIR with a delay

A deterministic SEIR in 10 million people in five age groups (0–1, 1–5, 5–15, 15–30, and 30+ years), over one year in days, with births, deaths, aging, waning immunity, and a latent period of exactly 14 days written as a delay differential equation. It is odin's own age-structured example (the README's "more complicated example", `array_odin.R`, with `E` and a delay added), and one of the six models odin's tests check against hand-written deSolve code.

## Why this model

odin's other examples are a logistic curve, the Lorenz attractor, a Lotka–Volterra system, and the SIR models of the "discrete" vignette, one of which is the wave 1 example (`stochastic_sir_arrays`, whose arrays hold replicates). The suggested `discrete_stochastic_seirds.R` is a scalar SEIRDS with one multinomial branch, little beyond wave 1. This model is the one that uses what odin says it is for: arrays that are coupled (aging moves people from one element to the next, and everyone is infected by the sum over ages), equations written once for a range of indices with special cases for the first element, and `delay()`, which odin turns into a call to `deSolve::dede`.

## What it exercises

- Arrays over age, with equations for `[1]` and for `[2:N_age]`, and `sum()` over an array
- Aging between adjacent age groups at one over each group's width, with nobody aging out of the last
- Births into the youngest group at a constant total (`b * N`), and deaths at the same rate from every state, so the population stays at 10 million
- An initial population in the stable age distribution, worked out in the model (`den`)
- A latent period of exactly 14 days, as a delay: those leaving `E` are those who entered 14 days ago, less those who died (`delay(new_inf[i] * surv, lat_hum)`)
- Homogeneous mixing over all ages (`I_tot / N`), recovery, and waning immunity (`R -> S`)

## Files

- `original/seir_array_odin.R`: the model, unchanged, from `tests/testthat/examples/` of odin 1.2.7
- `run.py`: compiles and runs it as odin's tests do, and writes `reference/`
- `reference/results.csv`: `S`, `E`, `I`, and `R` in each age group (`I_0-1`, `I_1-5`, and so on) and in total, on each day from 0 to 365
- `reference/timing.json`: the time of a first run, with compiling, and of a rerun of the compiled model
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (MIT)

## The model

For each age group `i` of 5:

- **Infection:** `new_inf[i] = beta * S[i] * I_tot / N`, with `beta = 1` per day, `I_tot` the sum of `I` over ages, and `N = 1e7` a constant
- **Latency:** `lag_inf[i] = new_inf[i](t - 14) * exp(-b * 14)`: those infected 14 days ago who have not died leave `E` for `I`
- **Recovery** at `sigma = 1/30` per day, and **waning** from `R` to `S` at `delta = 1/60` per day
- **Births** of `b * N` a day into `S[1]`, and **deaths** at `b = 1/(365 * 50)` per day from every state
- **Aging** at `1 / (365 * width)` per day, for widths of 1, 4, 10, and 15 years, and 0 from the last group
- **Initial conditions:** `S[i] = den[i] * (N - 1)` and `I[i] = den[i]`, where `den` is the stable age distribution given the aging and death rates; `E` and `R` start empty
- **Time:** days 0 to 365 (`mod$run(0:365)`), solved by `deSolve::dede`

Two details of the delay matter for a translation:

- **Before day 14 the delay looks back to before the start.** odin (like deSolve and Berkeley Madonna) then uses the value of the delayed expression at the start, so for the first 14 days `lag_inf` is the initial rate of infection, about one a day, as if infections had been happening at that rate for the 14 days before day 0. About 14 people reach `I` in the first two weeks who never passed through `E` (which runs 14 below what it would otherwise hold, for good). With a reproduction number near 30 this brings the epidemic forward by about 15 days.
- **The latent age but leave by the age they were infected at.** `E` is aged like every other state, but `lag_inf[i]` takes from `E[i]` everyone infected in group `i` 14 days earlier, whether or not they have since aged into group `i + 1`. In total this makes no difference, but in the youngest group, where 1 in 26 of the latent age out within 14 days, `E` falls short of what it holds and `I` gets more than it would.

## Results

With one initial case the epidemic grows slowly for two months and then fast: `I` peaks at 6.19 million on day 125, and on day 365 there are 0.33 million in `S`, 1.31 million in `E`, 2.79 million in `I`, and 5.57 million in `R`, heading for an endemic equilibrium.

## Lines of model code

53: the 50 lines of `seir_array_odin.R` that are not blank or a comment, and the 3 lines of odin's tests that compile and run it (`odin::odin()`, `$new()`, `$run()`). No line is over 100 characters.

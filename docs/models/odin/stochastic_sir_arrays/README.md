---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# odin: discrete-time stochastic SIR, written with arrays

A closed, stochastic SIR epidemic in discrete time, with every variable an array of length 100. It is the third model of odin's "discrete" vignette, one step up from its scalar stochastic SIR.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 27 | 11 | |
| 100 runs | first 0.65 s, rerun 0.00095 s | first 0.013 s, rerun 0.00091 s (Rust) | Each of the original's runs holds 100 replicates in its arrays. The Starsim times are for one run of 100 replicates, held as places that nobody moves between, which is the form of the original. As 100 separate runs (`ss.parallel(sim, n_runs=100)` in one process), a rerun takes 0.013 s. The original's first run includes compiling C code |
| Results | | | **Agree.** The mean of 20,000 replicates is within 6.1 people of 1,001 at every time, against the original's 20,000 replicates; 44.8% die out. `compare.py` allows 12 people, three standard errors of the difference |

Measured on 9 November 2026 with Starsim 4.0.0rc3 (the `v4` branch, commit `be38b9f6`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The original writes out the binomial draws and the update of each compartment by hand; here the stochastic solver does the same thing from two transitions, with `substeps=1` for one draw a step, as the original takes.

## Findings

- **Whole steps have to be asked for.** Starsim's chain binomial now chooses its own substeps, to reduce the error of taking a whole step, but the original's model is defined by its whole steps. Without `substeps=1`, people infected in a step can recover in the same step, and the mean `S` at the end is 22 people too high (5 standard errors), with 47.6% of runs dying out rather than 45.2%. That is a closer answer to the continuous-time model, but a different model from this one. A separate NumPy simulation of the original's equations, 2 million runs, gave the check.
- **Many runs are fast in one process, and not with the default.** `ss.parallel(sim, n_runs=20_000, parallel=False)` is one call to the kernels and takes about 3 s. `sim.run(n_runs=20_000)` has no such option, and took about 300 s on 20 workers with a great deal of memory, since it starts a process for each worker. It would be better if a run the kernels take whole never started workers, or if `sim.run()` took `parallel=False`.
- **The original's compiled model is faster.** The original compiles code for this model; Starsim's kernels are general, working through arrays that describe the model. See the table above for how much.
- **The arrays are not coupled groups.** This example was chosen as a step up from odin's deterministic SIR, but its arrays hold replicates. They are written as places since that is 12× faster to rerun than separate runs, and `kind='space'` is what keeps them independent: as plain groups they mix, and the mean final `S` is 220, with no warning. The [age-structured SEIR](../seir_array) has coupled groups.

## What it exercises

- Discrete time: `update()` gives each variable's value at the next step from the values at this step
- Stochastic transitions drawn from binomial distributions (`rbinom`)
- Rates turned into probabilities for the step (`1 - exp(-rate)`)
- Arrays: every state, intermediate quantity, and draw has a `dim()`, and equations are written once for element `i`
- Parameters with defaults (`user()`), including the length of the arrays
- Equations in any order: odin sorts them by what depends on what

In this model the arrays hold 100 independent copies of the same epidemic, which the vignette uses to get 100 replicates from one run; nothing links one element to another. The array machinery is the same that odin's age-structured models use.

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/discrete_stochastic_sir_arrays.R`: the model, unchanged, from `inst/examples/` of odin 1.2.7
- `run.py`: compiles and runs it as the vignette does, and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range at each of steps 0 to 100, from 200 runs: one group (`S`, `I`, `R`, over all 100 groups of all 200 runs, so 20,000 samples), the total over the 100 groups (`S_total`, `I_total`, `R_total`, 200 samples), and groups 1, 2, and 100 on their own (`S_1`, `I_1`, `R_1`, and so on, 200 samples each)
- `reference/timing.json`: the time of a first run, with compiling, and of a rerun of the compiled model
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (MIT)

## The model

For each group `i` of `nsim`:

- **States:** `S[i]`, `I[i]`, `R[i]`, as whole numbers
- **Total:** `N[i] = S[i] + I[i] + R[i]`
- **Probabilities for one step:** `p_SI[i] = 1 - exp(-beta * I[i] / N[i])` for infection, and `p_IR = 1 - exp(-gamma)` for recovery
- **Draws:** `n_SI[i] ~ Binomial(S[i], p_SI[i])` and `n_IR[i] ~ Binomial(I[i], p_IR)`
- **Updates:** `S[i]` loses `n_SI[i]`; `I[i]` gains `n_SI[i]` and loses `n_IR[i]`; `R[i]` gains `n_IR[i]`
- **Parameters:** all left at their defaults: `beta = 0.2`, `gamma = 0.1`, `S_ini = 1000`, `I_ini = 1`, `nsim = 100`
- **Initial conditions:** 1,000 in `S`, 1 in `I`, and 0 in `R`, in every group
- **Time:** steps 0 to 100 (`x$run(0:100)`), each of one unit of time; the model has no `dt`, so the rates are per step
- **Seed:** `set.seed(1)`, as in the vignette; odin 1.2.7 draws from R's own random number generator

Everything on the right-hand side is the value at the start of the step: both draws use the old `S[i]` and `I[i]`, so an individual infected in a step cannot recover in the same step.

## Results

With one initial case and a reproduction number of about 2, an epidemic in a group either dies out early or infects most of the group. The mean `I` in a group peaks at about 78 around step 66, and the mean `R` at step 100 is 382 of 1,001, with the epidemics that took off still under way. The range for one group is wide (`R` at step 100 from 1 to 800), and the range for the total of 100 groups is narrow (`R_total` from 32,218 to 43,676).

The groups are alike, so `S_1`, `S_2`, and `S_100` estimate the same thing as `S`, with fewer samples. `run.py` makes the 200 runs one after another from one seed, so it writes the same results each time; the first run is the vignette's own.

## Lines of model code

27: the 23 lines of `discrete_stochastic_sir_arrays.R` that are not blank or a comment, and the 4 lines of the vignette that compile and run it (`odin::odin()`, `$new()`, `set.seed(1)`, `$run(0:100)`). No line is over 100 characters.

# odin stochastic SIR with arrays, in Starsim

The translation of [examples/odin/stochastic_sir_arrays](../../../examples/odin/stochastic_sir_arrays). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 27 | 8 | |
| 100 runs | 0.002 s | 0.04 s | Each of the original's runs holds 100 replicates in its arrays. The Starsim times are for one replicate, nearly all of it building the sim, unless `scorecard.py` is told to time `sim.run(n_runs=100)`. The original's first run includes compiling C code |
| Results | | | **Agree.** The mean of 20,000 runs is within 2.8 people of 1,001 at every time, against the original's 20,000 replicates; 45.3% of runs die out. `compare.py` allows 12 people, three standard errors of the difference |

Measured on 13 October 2026 with Starsim 4.0.0 (the `v4` branch) on a 20-core x86-64 Linux machine.

## What was declared and what was not

Everything is declared. The original writes out the binomial draws and the update of each compartment by hand; here the stochastic solver does the same thing from two transitions, with `substeps=1` for one draw a step, as the original takes.

## Findings

- **Whole steps have to be asked for.** Starsim's chain binomial now chooses its own substeps, to reduce the error of taking a whole step, but the original's model is defined by its whole steps. Without `substeps=1`, people infected in a step can recover in the same step, and the mean `S` at the end is 22 people too high (5 standard errors), with 47.6% of runs dying out rather than 45.2%. That is a closer answer to the continuous-time model, but a different model from this one. A separate NumPy simulation of the original's equations, 2 million runs, gave the check.
- **Many runs are fast in one process, and not with the default.** `ss.parallel(sim, n_runs=20_000, parallel=False)` is one call to the kernels and takes about 3 s. `sim.run(n_runs=20_000)` has no such option, and took about 300 s on 20 workers with a great deal of memory, since it starts a process for each worker. It would be better if a run the kernels take whole never started workers, or if `sim.run()` took `parallel=False`.
- **The original's compiled model is faster.** The original compiles code for this model; Starsim's kernels are general, working through arrays that describe the model. See the table above for how much.
- **The arrays are not groups.** This example was chosen as a step up from odin's deterministic SIR, but its arrays hold replicates, not coupled groups, so it exercises nothing about stratification. The [age-structured SEIR](../seir_array) has coupled groups.

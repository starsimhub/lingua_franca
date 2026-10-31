# summer2 mixing matrices, in Starsim

The translation of [examples/summer2/sir-age-location](../../../examples/summer2/sir-age-location). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 35 | 12 | One Starsim line is over 100 characters, so counts twice |
| One ODE run | first 0.87 s, rerun 0.00024 s | first 0.73 s, rerun 0.0014 s (JAX) | Neither time counts importing. The original's first run builds and compiles the model with JAX, which takes much longer than Starsim's; its rerun, once compiled, is faster |
| Results, ODE | | | Every compartment within 0.08 people of 1,000 |
| Results, other solvers | | | The stochastic and agent-based runs give the same number recovered as the ODE, to within 1% (mean of 100 runs) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: three transitions, two stratifications, one adjustment, and the mixing.

## Findings

- **Contact matrices by dimension (fixed).** `ss.contacts` took one matrix with its own age groups. It now also takes a matrix for each of the model's dimensions (`ss.contacts(dict(age=..., location=...))`), multiplied together as summer2 does.
- **Age groups as labels (fixed).** `age=['young', 'old']` clashed with the age every agent already has, which broke an agent-based run. A labeled age dimension is now kept apart from it, and nobody ages between its groups.
- **No unit of time.** The original names none, and neither version needs one: both run in steps of 0.1.
- **The mixing is not reciprocal.** Starsim notes that both matrices give different contacts between two groups, depending on which group is counted. It uses them as given, as summer2 does, with rows as the contacts of a person in each group.
- **Different ways of being fast.** summer2 compiles each model with JAX, which takes a while the first time, and reruns it very quickly. Starsim runs every model on the same precompiled kernels, so it has no such wait.

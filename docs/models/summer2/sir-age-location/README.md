---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# summer2: SIR stratified by age and location, with mixing matrices

An SIR epidemic with disease deaths in 1,000 people over 20 time units, stratified by age (young, old) and by location (urban, rural), each with its own mixing matrix. It is the "Multiple mixing matrices for multiple stratifications" example in summer2's documentation.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 35 | 12 | One Starsim line is over 100 characters, so counts twice |
| One ODE run | first 0.81 s, rerun 0.00022 s | first 0.011 s, rerun 0.00034 s (Rust) | Neither time counts importing. The original's first run builds and compiles the model with JAX, which takes much longer than Starsim's; its rerun, once compiled, is faster |
| Results, ODE | | | Every compartment within 0.08 people of 1,000 |
| Results, other solvers | | | The stochastic and agent-based runs give the same number recovered as the ODE, to within 1% (mean of 100 runs) |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: three transitions, two stratifications, one adjustment, and the mixing.

## Findings

- **Contact matrices by dimension (fixed).** `ss.contacts` took one matrix with its own age groups. It now also takes a matrix for each of the model's dimensions (`ss.contacts(dict(age=..., location=...))`), multiplied together as summer2 does.
- **Age groups as labels (fixed).** `age=['young', 'old']` clashed with the age every agent already has, which broke an agent-based run. A labeled age dimension is now kept apart from it, and nobody ages between its groups.
- **No unit of time.** The original names none, and neither version needs one: both run in steps of 0.1.
- **The mixing is not reciprocal.** Starsim notes that both matrices give different contacts between two groups, depending on which group is counted. It uses them as given, as summer2 does, with rows as the contacts of a person in each group.
- **Different ways of being fast.** summer2 compiles each model with JAX, which takes a while the first time, and reruns it very quickly. Starsim runs every model on the same precompiled kernels, so it has no such wait.

## What it exercises

- A base model written once, then stratified twice: 3 compartments become 12, and 3 flows become 12
- A mixing matrix for each stratification, which the framework combines as their Kronecker product
- A flow adjustment by stratum (rural people die of the infection at three times the rate)
- A population split by stratum, both even by default (age) and stated (location)
- A flow that leaves the model (death), so the population in each stratum falls over time

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/09-mixing-matrices.ipynb`: the notebook from the summer2 documentation, unchanged
- `original/mixing_matrices.py`: the first and fifth code cells of the notebook as a script, unchanged apart from one added line (`import numpy as np`, which the notebook has in a cell that is not used here)
- `export.py`: runs the script in the summer2 environment and prints the results and timing (its plot is skipped)
- `run.py`: calls `export.py` and writes `reference/`
- `reference/results.csv`: each of the 12 compartments at each of the 201 times, named `<compartment>_<age>_<location>` (for example, `S_young_urban`)
- `reference/timing.json`: the time of the first run (building, compiling, and running the model, with summer2 and JAX already imported) and of a rerun of the compiled model
- `meta.yaml`: where it came from
- `LICENSE`: the summer2 license

The example defines no derived outputs (such as incidence), so there are none in the results.

## The model

Compartments `S`, `I`, and `R`, with `I` infectious. Time runs from 0 to 20 with results every 0.1; the notebook does not name the unit.

| Flow | From | To | Rate per person |
|---|---|---|---|
| `infection` (frequency-dependent) | `S` | `I` | `contact_rate = 2` times the force of infection |
| `recovery` | `I` | `R` | `1/3` |
| `infection_death` | `I` | out of the model | `0.05`, times 3 (`0.15`) for rural |

The initial population is `S = 990`, `I = 10`, `R = 0`, split 50% young and 50% old (the default), then 70% urban and 30% rural. So `S` starts at 346.5 in each urban stratum and 148.5 in each rural one, and `I` at 3.5 and 1.5.

The mixing matrices have the infected stratum in rows and the infecting stratum in columns:

| Age | young | old |
|---|---|---|
| young | 0.2 | 0.3 |
| old | 0.5 | 0.7 |

| Location | urban | rural |
|---|---|---|
| urban | 0.8 | 0.2 |
| rural | 0.2 | 0.8 |

The combined 4 × 4 matrix `M` is the Kronecker product of the age matrix and the location matrix, with the strata in the order young urban, young rural, old urban, old rural. The force of infection on stratum `i` is the sum over strata `j` of `M[i,j] * I[j] / N[j]`, where `N[j]` is the current population of stratum `j` (which falls as people die). Integrating these equations independently with SciPy gives the reference results to within 0.003 people.

The solver is the default: an adaptive Dormand–Prince Runge–Kutta method, compiled with JAX, with relative and absolute tolerances of `1.4e-4`. `timestep = 0.1` sets the times of the results, not the step of the solver.

## Lines of model code

35, counting every line of `original/mixing_matrices.py` that is not blank or a comment, and leaving out the imports, the docstring, the two plotting lines, and the two `node_name` lines (which only label the matrices for the notebook's later figure). No line is over 100 characters.

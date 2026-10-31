# summer2: SIR stratified by age and location, with mixing matrices

An SIR epidemic with disease deaths in 1,000 people over 20 time units, stratified by age (young, old) and by location (urban, rural), each with its own mixing matrix. It is the "Multiple mixing matrices for multiple stratifications" example in summer2's documentation.

## What it exercises

- A base model written once, then stratified twice: 3 compartments become 12, and 3 flows become 12
- A mixing matrix for each stratification, which the framework combines as their Kronecker product
- A flow adjustment by stratum (rural people die of the infection at three times the rate)
- A population split by stratum, both even by default (age) and stated (location)
- A flow that leaves the model (death), so the population in each stratum falls over time

## Files

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

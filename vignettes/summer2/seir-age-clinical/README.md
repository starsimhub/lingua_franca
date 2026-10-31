# summer2 derived outputs in a stratified model, in Starsim

The translation of [examples/summer2/seir-age-clinical](../../../examples/summer2/seir-age-clinical). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 134 (55 for the model alone) | 16 | The original builds and runs the model seven times to request its outputs one group at a time. In Starsim every output but one is there without being asked for, by selecting groups of a result (the proportion in hospital is a division in `compare.py`) |
| One ODE run | first 3.8 s, rerun 0.0004 s | first 0.1 s, rerun 0.0025 s (Numba) | Neither time counts importing. The original's first run is all seven models, each built and compiled with JAX, as it takes all seven to get its outputs (`reference/timing.json` of the example gives the first alone); Starsim's is one model with all its results. The original's rerun is the last of the seven, with four outputs |
| Results, ODE | | | Every compartment within 0.0006 people of 1,000; every derived output within 0.006% of its peak. From the same start, the stratified model and the same model written as four states (`as_states()` in `compare.py`) agree to 2e-14 people |
| Results, other solvers | | | At time 20 the mean of 100 stochastic runs has 542 ± 9 recovered and of 100 agent-based runs 547 ± 10, against 580 in the ODE, since the epidemic is still under way and runs take off at different times. No run died out. By time 100 they end with 848 recovered, as does the ODE (847) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

The derived outputs are compared after converting them to summer2's conventions: a flow is divided by the step to give a rate, and is compared with the original's value at the end of the step. The original's cumulative deaths are 10 times the deaths (it sums rates without multiplying by the step; see the example's README), so they are compared with 10 times Starsim's.

## What was declared and what was not

Everything is declared: four transitions and two stratifications, as in the original. Every output of the original is a selection of the automatic results; only the proportion in hospital is a division of two of them, in `compare.py`.

| Original | Starsim |
|---|---|
| `Stratification('age', ...)` | `seir.stratify(age=['young', 'old'], adjust={'incidence': [1, 1.1]})` |
| `Stratification('clinical', ..., ['I'])` | `seir.stratify(clinical=[...], states=['I'], ...)` |
| `incidence` adjusted by clinical status, given age (`source_strata`) | `split=ss.by([[...], [...]], dims=['age', 'clinical'])`, a row for each age, with the old's rows summing to 1.1 given as the `adjust` on age |
| `infection_death` with `Overwrite(0)` and `Multiply(2)` | `adjust={'infection_death': [0, 1, 1, 2]}` |
| `add_infectiousness_adjustments` | `adjust={'rel_trans': [0.5, 1, 0.2, 0.1]}` |
| `set_population_split` (everyone in `I` asymptomatic) | `init_n=dict(I=ss.by([[5, 0, 0, 0], [5, 0, 0, 0]], dims=['age', 'clinical']))` |
| `request_output_for_flow` by age | Automatic: `res.incidence.select(age='old')` |
| `request_output_for_flow` by clinical status, or both | Automatic: `res.incidence.select(age='old', clinical='hospital')` |
| `request_cumulative_output` | Automatic: `res.infection_death.cum.select(age='old')` |
| `request_aggregate_output` (notifications) | Automatic: `res.incidence.select(clinical=['isolated', 'hospital'])` |
| `request_output_for_compartments` (hospital occupancy) | Automatic: `res.I.select(clinical='hospital')` |
| `request_function_output` (proportion in hospital) | `res.I.select(clinical='hospital') / res.I` in `compare.py` |

The stratification by clinical status is also written as four states (`Ia`, `Is`, `Ii`, `Ih`), each entered by its own transition from `E`, in `as_states()` in `compare.py`, as a check.

## Findings

All of these were found in earlier versions of this vignette and have been fixed in Starsim, except that the last is not a problem.

1. **Fixed: entering a stratification by a split that depends on another dimension.** People entering a state with a dimension their old state lacked used to go to its levels by one `split` for everyone. Now `split=ss.by(table, dims=['age', 'clinical'])` gives one row per age. The rows for the old sum to 1.1 in the original; normalizing them, and giving the 1.1 as an `adjust` on age, is exact.
2. **Fixed: infectiousness by level.** `adjust={'rel_trans': [...]}` on `stratify()` replaces a modifier for each level.
3. **Fixed: outcomes.** A sum of flows given to a disease is now an outcome, can be selected by group, and can have a weight by level (`ss.outcome(ss.by(clinical=[0, 0, 1, 1]) * incidence)` would declare notifications). Selecting the groups of the incidence result does the same job here.
4. **Fixed: an initial count by level of a dimension of some states.** It used to take the wrong number of people out of `S`. Now each level gets exactly that many people. Since `I`'s own split is the entry split, `ss.by(clinical=[10, 0, 0, 0])` would put 5.95 young and 4.05 old people in `I`, not 5 and 5 as in the original, so the vignette gives the count by both dimensions.
5. **Fixed: a flow into a dimension of some states was recorded only at its first level.** Such a flow is now recorded at the level people arrive at, so `res.incidence.select(clinical='hospital')` works directly.
6. **Not a problem: no unit of time, and no overwrite.** The original names no unit, and neither version needs one. summer2's `Overwrite(0)` is the multiplier 0.


# Atomica SIR demo, in Starsim

The translation of [examples/atomica/sir](../../../examples/atomica/sir). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 62 | 16 | The original is counted as rows of its two spreadsheets, plus three lines of Python. A spreadsheet row is easier for a non-programmer to fill in than a line of code, so these counts compare unlike things |
| One run | first 0.15 s, rerun 0.0025 s | first 0.084 s, rerun 0.0013 s (Numba) | The original's first run includes reading the spreadsheets, and its rerun is `Project.run_sim()` on the loaded project |
| Results | | | Every compartment identical, to rounding error |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The force of infection is an ordinary expression of counts and parameters, not a function.

## Findings

- **The step is part of the model.** Atomica takes one forward Euler step a year. Matching it needs `integrator='euler', substeps=1`; with Starsim's default integrator there are 18 infected at the end, not 11.
- **A constant inside the force of infection (fixed).** The original multiplies it by one minus the death rate. This version once wrote the number out again, since a typed rate could not be subtracted from 1. `1 - susdeath` now works.
- **Initial conditions as given.** The databook gives the susceptible number, the total, and the prevalence, and Atomica solves for the rest; here the solved values are written in.
- **The data is not in a spreadsheet.** The original's strength is that the structure and the data live in spreadsheets a non-programmer can edit. This version is code, and does not offer that.

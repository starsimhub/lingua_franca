# Atomica dynamic HIV demo, in Starsim

The translation of [examples/atomica/hiv_dyn](../../../examples/atomica/hiv_dyn). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 217 | 64 | The original is counted as rows of its three spreadsheets, plus 29 lines of Python; in Starsim, long lines count twice |
| One run | 0.0054 s | 0.18 s | Without the programs. The original's first run includes reading the spreadsheets, and its rerun is `Project.run_sim()` on the loaded project. Most of Starsim's first run is building the sim (finding 8) |
| Results | | | **Identical,** to rounding error (a largest difference of 1 in 10<sup>14</sup>), in every compartment and every level of the cascade of both sexes, in all four runs: without programs, and with the default, doubled, and zero budgets |

Measured on 30 October 2026 with Starsim 4.0.0 (the `v4` branch, commit a1e3faab) on a 20-core x86-64 Linux machine.

## What was declared and what was not

Everything is declared: the transitions (written as Atomica's transition matrix, one per parameter), the parameters, the formulas that turn annual numbers into rates, the births by sex, the cascade by sex, the programs' coverage and effects, and the scenarios, all as expressions of counts and parameters. There are no functions of the sim left. The one thing written out by hand is marked in `model.py`: the initial state, worked out from the databook's cascade with `np.diff`, where Atomica solves for it (as in the [SIR demo](../sir)).

## Findings

1. **Fixed: a step that moved more than everyone created people.** Atomica turns each parameter into a share moved in a step, and if the shares leaving a compartment add up to more than 1 it scales them down together. Here that happens every step, since the time to viral suppression is 0.2 years and the step is a year. Starsim's Euler step now does the same with `integrator='euler'` and `substeps` given, and a note says so, so the model is plain transitions, one for each parameter of Atomica's transition matrix.
2. **Fixed: a count within one's own group, or over everyone.** Atomica's populations have rates made from their own compartment sizes (`num_acq/max(sus, num_acq)`), but a program's coverage is the number reached over everyone eligible in both populations. In Starsim, `.n` in a rate is the count in the same place, and `.total` is now the count in the whole population. This version once needed a function of the sim for the total, which kept the run out of the fast kernels and stopped `sim.restart()`. Both are gone. Sex is still stratified as a place (`kind='space'`, with no movement), so that `.n` means the count in each sex.
3. **Fixed: an inflow given by group was shared out again.** An inflow whose rate is an `ss.by` now arrives at each level as given, so the births are written by sex, as in the databook.
4. **Programs and budgets have no declared form by hand.** Spending buys a number of people reached, coverage is that number over the eligible (capped at 1), and each parameter moves from a baseline toward each program's outcome in proportion to coverage. Here that is three short expressions (`cov`, `outcome`, `switch`), with the budget and the switch as parameters set by each scenario. Atomica says this more directly, in its program book. Starsim's importer reads a program book, but there is no `ss.program()` for a model written by hand.
5. **Fixed: `ss.by` is an expression.** `1/ss.by(sex=[0.7, 1.2])` and `ss.by(...) - ss.by(...)` work, and level by level.
6. **Fixed: sums of states are kept by group.** A declared sum of states is a stratified result, so `compare.py` compares the cascade (`plhiv`, `diagnosed`, `treated`) for each sex.
7. **Gone: a warning from dividing by nobody.** It came from the branching helper that finding 1 removed.
8. **Most of a first run is building the sim.** Each program-affected rate is a switch of two expressions over seven coverages, so the model takes a while to build. A rerun of a built sim is much quicker.
9. **Fixed: arithmetic on `ss.by` swallowed what it was combined with.** `ss.by(sex=[1, 2]) + I.n` is now an expression, and two `ss.by`s over the same dimension combine level by level, so `model.py` has lost its workarounds (`ss.par` around three values, the expression written first, and `np.subtract`).

---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Atomica: the HIV care cascade, with programs and budgets

Atomica's dynamic HIV demo (`at.demo('hiv_dyn')`): the HIV care cascade in two populations, females and males, of a country of 56 million, from 2016 to 2035 in yearly steps. People are born susceptible, are infected, diagnosed, linked to care, put on treatment, and virally suppressed, can fail treatment or be lost to follow-up and come back, and die of HIV or of other causes. Seven programs (two testing, two kinds of initiation counseling, client tracing, and two kinds of adherence support) turn spending into coverage, and coverage into the values of five parameters, under three budgets. As in the SIR demo, the model is spreadsheets, and the Python only loads and runs them.

It is chosen as Atomica's complex example because it is a demo its authors ship (Atomica's flagship TB demo is held back as a possible separate TB model) and it uses the part of Atomica the [SIR demo](../sir) leaves out: programs and budget scenarios.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 217 | 64 | The original is counted as rows of its three spreadsheets, plus 29 lines of Python; in Starsim, long lines count twice |
| One run | first 0.14 s, rerun 0.0041 s | first 0.038 s, rerun 0.00034 s (Rust) | Without the programs. The original's first run includes reading the spreadsheets, and its rerun is `Project.run_sim()` on the loaded project. Most of Starsim's first run is building the sim (finding 8) |
| Results | | | **Identical,** to rounding error (a largest difference of 1 in 10<sup>14</sup>), in every compartment and every level of the cascade of both sexes, in all four runs: without programs, and with the default, doubled, and zero budgets |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

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

## What it exercises

- Everything the [SIR demo](../sir) does: a model whose structure (the framework), data (the databook), and programs (the progbook) are all spreadsheets, transitions named by a parameter whose format decides how it becomes a fraction moved per step, characteristics, initial conditions solved from characteristics, sinks, and a fixed-step difference equation
- Two populations with the same structure and their own data, which do not interact except through the programs
- A source compartment with a number of births a year, and a characteristic for every level of the cascade (seven nested sums of compartments), all used to set the initial state
- Parameters given as annual numbers and turned into rates by formulas of compartment sizes (`num_acq/max(sus, num_acq)`), so that the number of new infections, tests, and treatment initiations is what the data says while there are enough people to take it
- Outflows that add up to more than everyone in a compartment in a step (the time to viral suppression is 0.2 years, with a step of a year), which Atomica scales down together
- Programs: a unit cost, spending by year, and the compartments and populations each program reaches; the coverage (the number reached, as a share of everyone eligible in both populations, capped at 1); and the effect of each program on each parameter in each population, combined additively from a baseline value
- Budget scenarios that change the spending on every program from a given year, with the programs switched on from the last year of data

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/hiv_dyn_framework.xlsx`, `original/hiv_dyn_databook.xlsx`, `original/hiv_dyn_progbook.xlsx`: the model, its data, and its programs, unchanged from the package
- `original/demos.py`: Atomica's `demos.py`, unchanged, for `make_demo_scenarios()`, which makes the budget scenarios
- `original/hiv_dyn.py`: the lines of Python that load and run them, as `at.demo('hiv_dyn')` does
- `original/sheets/`: every sheet of the three spreadsheets as CSV, written by `dump_sheets.py` (a cell holding a formula is written as its stored result)
- `run.py`: runs the model and writes `reference/`; it calls `simulate.py` in the Atomica environment
- `reference/results.csv`: for each of four runs (`baseline`, without programs, and `default_budget`, `doubled_budget`, and `zero_budget`) and each population (`females`, `males`): the compartments (`baseline_females_sus` and so on), the flows in people per year (`baseline_females_tx_to_vs`), the characteristics (`alive`, `all_people`, `all_dx`, `all_ever_linked`, `all_curr_linked`, `all_tx`, `all_vs`), and the parameters that vary (`acq_rate`, `test_yield`, `diag`, `link_time`, `initiate`, `loss`, `fail_rate`); and for each budget scenario, the coverage of each program (`default_budget_coverage_testing_clinics` and so on)
- `reference/timing.json`: the times of a first run without programs, including reading the spreadsheets, of a rerun, and of the three budget scenarios
- `meta.yaml`: where it came from

## The model

Each population has the same compartments: `sus` (susceptible), `undx` (undiagnosed), `dx` (diagnosed), `linked` (linked to care), `tx` (treated), `lost` (lost to follow-up), `vs` (virally suppressed), and the sinks `dead_hiv` and `dead_other`. Time runs from 2016 to 2035 in steps of `dt = 1` year.

| Transition | Parameter | Format | Value |
|---|---|---|---|
| source to `sus` | `birth_rate` | Number | 287,992 females and 276,699 males a year |
| `sus` to `undx` | `acq_rate` | Rate | `num_acq/max(sus, num_acq)`, with `num_acq` 150,000 and 110,000 |
| `undx` to `dx` | `diag` | Rate | `pos_test/max(undx, pos_test)`, with `pos_test = num_test*undx/(undx + sus)` and `num_test` 6.4 and 3.6 million |
| `dx` and `lost` to `linked` | `link_time` | Duration | 0.7 and 1.2 years |
| `linked` to `tx` | `initiate` | Rate | `num_initiate/max(linked, num_initiate)`, with `num_initiate` 269,448 and 179,632 |
| `linked`, `tx`, and `vs` to `lost` | `loss` | Rate | 0.2 and 0.3 a year |
| `tx` to `vs` | `supp_rate` | Duration | 0.2 years |
| `vs` to `tx` | `fail_rate` | Rate | 0.16 a year |
| `undx`, `dx`, `linked`, `lost` to `dead_hiv` | `death_hiv` | Rate | 0.053 a year |
| `tx` to `dead_hiv` | `death_hivtx` | Rate | 0.0258534 a year |
| `vs` to `dead_hiv` | `death_hivvs` | Rate | 0.01219 a year |
| every living compartment to `dead_other` | `death_other` | Rate | 0.015 a year |

As in the SIR demo, a rate is multiplied by `dt` and a duration is inverted (`dt/duration`) to give the fraction of the source moved in a step, each flow is that fraction of the compartment at the start of the step, and the compartments are updated together. If the fractions leaving a compartment add up to more than 1, they are all scaled down to add up to 1. That happens every step for `tx` (whose fraction to `vs` alone is 5), for females in `dx` and `lost` (1/0.7 to `linked`), and for `linked` whenever `num_initiate` is more than the number linked (males in 2016). The databook gives every value once, as a constant; its columns for 2016 to 2019 are empty.

The initial state is solved from the databook's seven characteristics in 2016, which are nested sums: `alive` (28,514,100 and 27,395,900), `all_people` (3,390,000 and 2,540,000), `all_dx`, `all_ever_linked`, `all_curr_linked`, `all_tx`, and `all_vs` (1,017,000 and 508,000). Each compartment is then the difference between two of them (`sus = alive - all_people`, `lost = all_ever_linked - all_curr_linked`, and so on).

## The programs

| Program | Unit cost | Spending a year | Reaches | Changes |
|---|---|---|---|---|
| Testing, clinics | $5 | $42 million | `sus`, `undx` | `test_yield`, `diag`, `link_time` |
| Testing, outreach | $10 | $16 million | `sus`, `undx` | `test_yield`, `diag`, `link_time` |
| Same-day initiation counseling | $200 | $60 million | `dx`, `linked` | `initiate` |
| Classic initiation counseling | $300 | $45 million | `dx`, `linked` | `initiate` |
| Client tracing | $60 | $600,000 | `tx`, `lost` | `link_time` |
| Advanced adherence support | $150 | $600,000 | `tx`, `lost` | `loss`, `fail_rate` |
| WhatsApp adherence support | $0.05 | $10,000 | `tx`, `lost` | `loss`, `fail_rate` |

Every program reaches both populations. The unit costs are per person, not per person per year, so Atomica treats the programs as one-off: the number reached in a step is the spending times `dt` over the unit cost, and the coverage is that number over everyone eligible (the compartments it reaches, in both populations), capped at 1. The progbook's coverage rows are data, not used in the run, and no program has a capacity constraint or saturation.

A parameter under programs is its baseline value plus, for each program, its coverage times the difference between the program's outcome and the baseline (additive coverage interaction). The baselines and outcomes are in `original/sheets/hiv_dyn_progbook__program_effects.csv`; for example, `link_time` for females is 1.5 years, or 0.5 with full coverage of testing in clinics. The initiation rate of males has a baseline of 0 and no programs, so with programs on no males start treatment. Atomica has a more complicated rule for when the coverages of the programs affecting one parameter add up to more than 1, but in these runs they never do (the largest sum is 0.71). The program values replace the parameters' own values, including those given by formulas (`diag`); `test_yield` is then only an output, since `pos_test`, which uses it, no longer feeds `diag`.

## The scenarios

`at.demo()` adds three budget scenarios with `make_demo_scenarios()`. Each switches the programs on from 2019, the last year of data, with the spending in the progbook. The default budget keeps it; the doubled budget doubles every program's spending from 2020, and the zero budget cuts it to nothing from 2020. The run without programs (the `baseline` here) is the one `at.demo()` stores in the project.

## Lines of model code

217: 188 for the spreadsheets and 29 for the Python.

The spreadsheets are counted as for the SIR demo, from the CSV files in `original/sheets/` with `dump_sheets.py`: every non-empty row, including each table's heading row, with trailing empty cells dropped, and a row over 100 characters counted as two, leaving out the framework's `About` sheet (a description) and `Cascades` sheet (plots). That gives 52 for the framework (databook pages 3, compartments 11, transitions 11, characteristics 8, parameters 19), 60 for the databook (population definitions 3, stocks 21, flows 36), and 76 for the progbook (targeting 10, spending 42, effects 24). The Python is the six statements in `original/hiv_dyn.py` that load the three spreadsheets, set the time step, make the scenarios, and run them, and the 23 lines of `make_demo_scenarios()` in `original/demos.py` (20 lines of code, three of them over 100 characters).

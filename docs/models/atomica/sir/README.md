# Atomica: SIR with deaths, defined in spreadsheets

Atomica's SIR demo (`at.demo('sir')`): one population of 1,000 adults moving between susceptible, infected, recovered, and dead, over 23 yearly steps. The model structure is in one spreadsheet (the framework) and its data in another (the databook); the Python only loads and runs them.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 62 | 16 | The original is counted as rows of its two spreadsheets, plus three lines of Python. A spreadsheet row is easier for a non-programmer to fill in than a line of code, so these counts compare unlike things |
| One run | first 0.12 s, rerun 0.0023 s | first 0.011 s, rerun 0.00023 s (Rust) | The original's first run includes reading the spreadsheets, and its rerun is `Project.run_sim()` on the loaded project |
| Results | | | Every compartment identical, to rounding error |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `e26de815+`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The force of infection is an ordinary expression of counts and parameters, not a function.

## Findings

- **The step is part of the model.** Atomica takes one forward Euler step a year. Matching it needs `integrator='euler', substeps=1`; with Starsim's default integrator there are 18 infected at the end, not 11.
- **A constant inside the force of infection (fixed).** The original multiplies it by one minus the death rate. This version once wrote the number out again, since a typed rate could not be subtracted from 1. `1 - susdeath` now works.
- **Initial conditions as given.** The databook gives the susceptible number, the total, and the prevalence, and Atomica solves for the rest; here the solved values are written in.
- **The data is not in a spreadsheet.** The original's strength is that the structure and the data live in spreadsheets a non-programmer can edit. This version is code, and does not offer that.

## What it exercises

- A model whose structure and data are both spreadsheets: compartments, a transition matrix, and parameters in the framework, and values by population and year in the databook
- Transitions named by a parameter, with the parameter's format (probability, rate, or duration) deciding how it becomes a fraction moved per step
- One parameter driving several transitions (`susdeath` is on the links out of `sus`, `inf`, and `rec`) and two parameters on one transition (`inf` to `dead`)
- A parameter that is a formula of other parameters and of a characteristic (`foi`)
- Characteristics: named sums and ratios of compartments, used as outputs, in formulas, and to set the initial state
- Initial conditions solved from data on characteristics rather than given per compartment
- A sink compartment (`dead`)
- A fixed-step difference equation, not an ODE solver

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/sir_framework.xlsx`, `original/sir_databook.xlsx`: the model and its data, unchanged from the package
- `original/sir.py`: the lines of Python that load and run them
- `original/sheets/`: every sheet of both spreadsheets as CSV, written by `dump_sheets.py` (a cell holding a formula is written as its stored result)
- `run.py`: runs the model and writes `reference/`; it calls `simulate.py` in the Atomica environment
- `reference/results.csv`: for the one population, `adults`, the compartments (`adults_sus`, `adults_inf`, `adults_rec`, `adults_dead`), the flows in people per year (`adults_sus_to_inf`, `adults_inf_to_rec`, `adults_sus_to_dead`, `adults_inf_to_dead`, `adults_rec_to_dead`), the population alive (`adults_ch_all`), prevalence (`adults_ch_prev`), and the force of infection (`adults_foi`)
- `reference/timing.json`: the times of a first run, including reading the spreadsheets, and of a rerun
- `meta.yaml`: where it came from

## The model

One population, `adults`. Time runs from 2000 to 2023 in steps of `dt = 1` year (the demo sets this; Atomica's default is 0.25, and the end is the last databook year, 2018, plus five).

| Transition | Parameter | Format | Fraction of the source moved per step |
|---|---|---|---|
| `sus` to `inf` | `foi` | Rate | `foi*dt` |
| `inf` to `rec` | `recrate` | Duration | `dt/recrate` |
| `inf` to `dead` | `susdeath`, `infdeath` | Rate | `susdeath*dt + infdeath*dt` (two links) |
| `sus` to `dead` | `susdeath` | Rate | `susdeath*dt` |
| `rec` to `dead` | `susdeath` | Rate | `susdeath*dt` |

A rate or probability is multiplied by `dt` and a duration is inverted (`dt/duration`); there is no `1 - exp(-rate*dt)`. If the fractions leaving a compartment sum to more than 1, they are all scaled down to sum to 1. Each flow is its fraction times the source compartment at the start of the step, and the compartments are then updated together (forward Euler).

The force of infection is recalculated at each step from the current prevalence:

```
foi = (1 - (1 - ch_prev*transpercontact)**floor(contacts) * (1 - ch_prev*transpercontact*(contacts - floor(contacts)))) * (1 - susdeath)
ch_prev = inf / ch_all
ch_all = sus + inf + rec
```

That is, the probability of at least one transmission in `contacts` contacts in a year, each with a partner who is infected with probability `ch_prev`, times the probability of not dying. With 80 contacts the second factor is 1.

## Parameter values

The values used are those in the databook, which are constant over time and override the framework's defaults (shown for comparison, as two of them differ by a factor of ten).

| Parameter | Meaning | Databook (used) | Framework default |
|---|---|---|---|
| `transpercontact` | Transmission probability per contact | 0.008 | 0.0008 |
| `contacts` | Contacts per year | 80 | 80 |
| `recrate` | Duration of infection, in years (despite the name) | 5 | 0.5 |
| `infdeath` | Extra death rate when infected, per year | 0.016 | 0.016 |
| `susdeath` | Death rate for everyone, per year | 0.008 | 0.008 |

The databook's parameter tables have a column for each year from 2000 to 2018, so any parameter could vary over time, but all are empty and only the constant is filled in.

## Initial conditions

The databook gives three series for 2000 to 2018, and Atomica solves for the compartments that match them at the first time point:

- Susceptible: 700 in every year
- Total number of entities (`ch_all`): 1,000 in every year
- Prevalence (`ch_prev`): 0.28571429 in 2000, declining each year to 0.0354528 in 2018 (the full series is in `original/sheets/sir_databook__state_variables.csv`)

This gives `sus = 700`, `inf = 285.71429`, `rec = 14.28571`, `dead = 0`. The values after 2000 are data to compare with or calibrate to, and do not affect the run: the model's prevalence rises to 0.41 in 2003 before falling, while the data falls throughout.

## What else the demo has

`at.demo('sir')` also loads `sir_progbook.xlsx`, which defines five programs (risk avoidance, two harm reduction, two treatment) with spending, unit costs, and capacity by year, and their effects on the five parameters. It then adds three budget scenarios from 2018 (default, doubled, and zero budget). None of that is included here: this is the run without programs, `at.demo('sir', addprogs=False)`, and it gives identical results. The framework's `Cascades` sheet defines a care cascade for plotting, which the run does not use. The package also ships a separate `sir_vaccine` framework and databook.

## Lines of model code

62: 59 for the spreadsheets and 3 for the Python.

The spreadsheets are counted from the CSV files in `original/sheets/`, which `dump_sheets.py` does: every non-empty row, including each table's heading row, with trailing empty cells dropped, and a row over 100 characters counted as two. The framework's `About` sheet (a name) and `Cascades` sheet (plots) are left out. That gives 31 for the framework (databook pages 3, compartments 5, transitions 5, characteristics 10, parameters 8) and 28 for the databook (population definitions 2, state variables 11, parameters 15). Most of the two-line rows are the databook's rows of 19 years. The Python is the three statements in `original/sir.py` that load the project, set the time step, and run it.

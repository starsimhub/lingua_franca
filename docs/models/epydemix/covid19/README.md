# epydemix: the first wave of COVID-19 in Massachusetts

An age-structured SEIR with deaths, in the population of Massachusetts (7.0 million people in nine age groups), from 23 February to 2 August 2020. Transmission is scaled each day by a contact reduction computed from Google mobility data and by a seasonal factor; deaths follow the infectious period with the age-specific infection fatality rate, after an Erlang-distributed delay. The model is calibrated by ABC-SMC to weekly deaths up to 31 May, and then projected to 2 August under three reopening scenarios. It is epydemix's seventh tutorial, "Modeling the first wave of COVID-19 in Massachusetts", and its most complete worked example.

This is epydemix's wave 3 example. `model.py` is the Starsim version, and `compare.py` checks it against `reference/` (it takes a few minutes).

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 161 | 39 | Both count the loading of the data, the calibration, and the scenarios; lines over 100 characters count twice. The original is formatted one item per line |
| One run of the calibration period | first 0.037 s, rerun 0.032 s | first 0.024 s, rerun 0.0012 s (Rust) | In process, without the import or the data download. The original's times are with its model already defined; Starsim's first run includes building the sim |
| Results at fixed values | | | **Agree** (tolerance 3% of the peak). The mean of 200 runs: weekly deaths within 0.7% of the peak (833 against 837, in the same week), and 0.5% and 0.4% in the two reopening scenarios; deaths by age within 3% of the peak in every group from age 40; `E`, `I`, `R`, and `D` within 0.5%; 10,507 deaths by 2 August against 10,525 |
| Results of the calibration | | | **Agree** (tolerance: each posterior mean inside the original's 5% to 95% range, and projected peaks within 10%). Posterior means: `R0` 2.28 (original 2.25), `Delta` 18.8 days (19.0), `I0` 4,777 (4,770), and `seasonality_min` 0.79 (0.80), with similar ranges. Peak weekly deaths projected from the posterior are 891 (897), 1,366 (1,363), and 2,231 (2,217) in the three scenarios. This is a change from before: a point estimate gave much smaller second waves |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

The calibration is the same method in both: ABC-SMC with 200 particles for 5 generations (the tutorial's 1,000 for 10 take over an hour). It took 25 s in Starsim and 87 s in the original on a quiet machine (222 s when the machine was busy, so these are a rough guide).

## What was declared and what was not

Everything in the model is declared: nine states, seven transitions (the four stages of the delay to death written out, as in the original, and a split on leaving `I` with `p=ss.by(age=IFR)` in place of two competing rates), a stratification by age with a contact matrix, a time series and a seasonal factor in the transmission rate, the weekly deaths as data, four parameters with bounds (one inside the seasonal factor and one in the initial conditions), and the reopening scenarios as `ss.modify` from 1 June. The weekly totals line up with the data without being asked: a flow is summed over the week ending at each data date. Since a date is the time point at the start of that day, this is the week to the end of the Saturday, a day earlier than epydemix's weeks ending on Sunday (`compare.py` sums its own weeks to the end of each Sunday).

The mobility data is turned into the contact reduction with pandas, as in the original. The transmission rate's scaling by R0 and the leading eigenvalue of the contact matrix is written out, as in the original.

Not translated: the random split of the initial infections between age groups (Starsim splits them in proportion to the population, the mean of the original's draw).

## Findings

1. **`stages=4` is no longer the original's delay (new).** The first version wrote the delay to death as `ss.Transition(D, Dead, dur=Delta, stages=4)`. The chain-binomial solver now moves people through such stages so that the delay averages exactly `Delta`. epydemix takes one step a day through four compartments, each left with a chance of `1 - exp(-4/Delta)`, which averages about 22 days at `Delta = 20`. With `stages=4`, deaths came about 2 days too soon, and weekly deaths differed by 6% of the peak. Writing the four stages out as transitions matches the original, for 3 more lines. Neither is wrong: this is the difference between a dwell time and a discrete-time model.
2. **Needs `substeps=1`.** Without it the chain-binomial solver takes several steps a day, and the epidemic differs from epydemix's, which takes whole days.
3. **Fixed: a parameter used by several modules, in `init_n=`, and inside `ss.seasonal`.** All four of the tutorial's parameters are now fitted, including `I0` and `seasonality_min`.
4. **Fixed: a posterior.** `sim.fit(method='abc-smc')` uses the original's method and distance (`wmape`), and `fit.project()` gives projections from it. Both now agree with the original. A form of `ss.seasonal` given by the minimum would still say what the original means more directly.
5. **Fixed: plotting with dated data.**
6. **Many runs with a modifier run in separate processes.** `sim.run(n_runs=)` is one call to the kernel for the persistence scenario, but with `ss.modify` it is a `MultiSim`, and `fit.project()` has no way to say `parallel=False`, so `compare.py` writes out what it does.
7. **Population data for US states are not available yet.** Starsim bundles countries, but `ss.people('United States:Massachusetts')` cannot be downloaded yet, so the population of Massachusetts and its contact matrices are read from what epydemix downloaded, as a few of the lines.

## What it exercises

- A model written out compartment by compartment (nine compartments, eight transitions), not a predefined one
- Competing exits with age-specific rates (`mu*(1-IFR)` to recovery and `mu*IFR` towards death), with the IFR given per age group
- An Erlang delay to death written as a chain of four compartments (`D0` to `D4`), each left at the rate `4/Delta`
- A transmission rate that varies by day: the product of a value computed from R0 and the leading eigenvalue of the contact matrix, a seasonal cosine, and a contact reduction from mobility data (`beta*r`, two time series given as arrays of daily values)
- Initial conditions drawn at random for each run (`I0` split over the age groups by a multinomial draw, then halved into `E` and `I`)
- Mixing by the sum of four contact matrices (school, work, home, community), with the population and matrices loaded by name, and one-year age groups aggregated into nine
- Weekly totals of a flow (the transition from `D3` to `D4`), as the calibration target
- Calibration by ABC-SMC of four parameters (`R0`, `Delta`, `I0`, and `seasonality_min`), with priors, and the weighted mean absolute percentage error as the distance
- Projections from the posterior under scenarios that change the contact reduction after the calibration period
- A stochastic (chain-binomial) solver with a daily step

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/covid19.py`: code cells 2 to 13 of the tutorial notebook, unchanged (a script extracted from a notebook; the first cell installs packages on Colab, and the last is empty)
- `original/data/`: the weekly deaths (`MA_deaths.csv`) and the Google mobility report (`MA_google.csv`) the tutorial reads, copied from `tutorials/data/massachusetts_data` in the epydemix v1.4.0 repository
- `simulate.py`: runs the original in the epydemix environment, with the changes listed below, and prints the summary and timing as JSON
- `run.py`: calls `simulate.py` and writes `reference/` (it takes about two and a half minutes)
- `reference/results.csv`: everything is in days from the start of 23 February 2020 to the end of the day (or week) it describes, so the week ending 1 March is time 8:
    - `data_deaths`: the weekly deaths the model is fitted to and projected against
    - `posterior_<par>`: the mean and the 5% to 95% range of the ABC-SMC posterior of `R0`, `Delta`, `I0`, and `seasonality_min` (at time 0)
    - `abc_fit_deaths`, and `abc_<scenario>_deaths` for the scenarios `persistence`, `moderate`, and `high`: the mean and 5% to 95% range of the weekly deaths of the accepted particles, and of 100 projections from the posterior
    - `fixed_<scenario>_deaths`: weekly deaths from 200 runs at fixed parameter values (the posterior medians, rounded: `R0` 2.22, `Delta` 20, `I0` 4,260, `seasonality_min` 0.8), for each scenario; for `persistence` also `fixed_persistence_deaths_<group>` by age group, and the daily totals of `S`, `E`, `I`, `R`, `D` (the sum of `D0` to `D3`), and `D4` (the dead)
- `reference/population.json`: the inputs that come from the data rather than the script (the size of each age group and the four contact matrices), the contact reduction in each scenario, the fixed parameter values, and the settings of the run
- `reference/timing.json`: the time of a first run and of a rerun of `simulate_wrapper()`, the function the calibration evaluates
- `meta.yaml`: where it came from
- `LICENSE`: the license of epydemix (GPL-3.0)

## The model

- **Compartments:** `S`, `E`, `I`, `R`, and `D0` to `D4`, each split into the age groups 0-9, 10-19, ..., 70-79, and 80+
- **Infection:** a susceptible person in group `i` is infected at the rate `beta(t) * r(t) * sum_j C[i,j] * I[j] / N[j]`, where `C` is the sum of the four contact matrices and `N[j]` the size of group `j`
- **Transmission rate:** `beta(t) = R0 * mu / max eigenvalue(C) * s(t)`, where `s(t) = 0.5 * ((1 - smin) * cos(2π(t - 15 January)/365) + 1 + smin)` is 1 in mid-January and `smin` in mid-July
- **Contact reduction:** `r(t) = (1 + m(t)/100)²`, where `m(t)` is the mean of five of the mobility report's percentage changes (retail and recreation, grocery and pharmacy, transit stations, workplaces, and residential) on day `t`; after 31 May it is held at its last value (persistence), or at 1.3 or 1.5 times it (moderate and high reopening)
- **Progression:** `E` to `I` at the rate `eps = 1/4` per day; `I` to `R` at `mu * (1 - IFR)` and to `D0` at `mu * IFR`, with `mu = 1/2.5` per day and the IFR from 0.00161% (0-9) to 7.8% (80+); `D0` to `D1` to ... `D4` each at `4/Delta`, so the time from leaving `I` to death is Erlang with four stages and mean `Delta`
- **Initial conditions:** `I0` infected people, split over the age groups by a multinomial draw in proportion to their size; half of each group's number (rounded down) start in `E` and half in `I`, and the rest of the group in `S` (so with an odd number, one person is in no compartment, although `N` still counts them)
- **Observed:** the weekly number moving from `D3` to `D4`, in weeks ending on Sundays (the first "week" is 23 February alone)
- **Calibration:** ABC-SMC with the priors `R0` ~ uniform(1.5, 6), `Delta` ~ integer uniform(7, 27), `I0` ~ integer uniform(10, 9999), `seasonality_min` ~ uniform(0.6, 1), and the distance `wmape = sum|observed - simulated| / sum|observed|`, over the 15 weeks to 31 May
- **Population:** 709,143, 834,913, 956,760, 973,053, 848,593, 911,402, 891,584, 582,877, and 293,074 people in the nine groups (7,001,399 in all)
- **Solver:** chain-binomial with a step of one day: each day the number leaving a compartment in a group is a multinomial draw, with the probability `1 - exp(-rate)` of leaving, split between the destinations in proportion to their rates

## Changes needed to run it

`simulate.py` makes three changes from outside, without editing the original:

- **The population's name.** The tutorial loads `"United_States_Massachusetts"`, which epydemix 1.4.0 rejects: in the data release it uses (epydemix-data v1.2.0) the name is `"United_States__Massachusetts"`, with a double underscore between the levels of the hierarchy. The tutorial as published does not run with the version it was published with.
- **The data.** The tutorial reads the deaths and mobility data from the `main` branch on GitHub; here they are read from the copies in `original/data`, taken from the v1.4.0 tag.
- **A smaller calibration.** The tutorial runs ABC-SMC with 1,000 particles for 10 generations, which took over an hour in the notebook's own output. Here it is 200 particles for 5 generations, which takes 87 s, seeded (`ABCSampler(rng=1)`, and `np.random.seed(1)` for the initial conditions). The posterior is therefore wider than the tutorial's, and the reference results of the calibration are for this smaller run.

Because the posterior of a small ABC-SMC run is itself noisy, the results that a translation is held to are the runs at fixed parameter values (`fixed_*`): the same model, the same inputs, and 200 runs, without the calibration. The calibration (`posterior_*`, `abc_*`) is kept to compare a translation's calibration with, more loosely.

## Data

The population and contact matrices are downloaded when the model runs, from [epydemix-data](https://github.com/epistorm/epydemix-data) at the tag `v1.2.0`, so `run.py` needs a network connection. What was downloaded is recorded in `reference/population.json`. The contact matrices are from the primary source the data release lists for Massachusetts.

## Lines of model code

161: the 150 lines of `covid19.py` that are not blank, a comment, a docstring, an import, a `print` call, or plotting, with the eleven lines over 100 characters counted twice. This counts the loading of the data (the population takes 14 lines, as the age groups are listed one per line) and the calibration and projections, which are the point of the tutorial. The notebook is formatted with one item per line, which accounts for perhaps a third of the count.

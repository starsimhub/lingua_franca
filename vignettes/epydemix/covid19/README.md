# epydemix COVID-19 in Massachusetts, in Starsim

The translation of [examples/epydemix/covid19](../../../examples/epydemix/covid19), epydemix's wave 3 example. The model is `model.py`; `compare.py` checks it against the original's reference results (it takes a few minutes).

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 161 | 39 | Both count the loading of the data, the calibration, and the scenarios; lines over 100 characters count twice. The original is formatted one item per line |
| One run of the calibration period | first 0.046 s, rerun 0.036 s | first 0.029 s, rerun 0.0022 s (Rust) | In process, without the import or the data download. The original's times are with its model already defined; Starsim's first run includes building the sim |
| Results at fixed values | | | **Agree** (tolerance 3% of the peak). The mean of 200 runs: weekly deaths within 0.7% of the peak (833 against 837, in the same week), and 0.5% and 0.4% in the two reopening scenarios; deaths by age within 3% of the peak in every group from age 40; `E`, `I`, `R`, and `D` within 0.5%; 10,507 deaths by 2 August against 10,525 |
| Results of the calibration | | | **Agree** (tolerance: each posterior mean inside the original's 5% to 95% range, and projected peaks within 10%). Posterior means: `R0` 2.28 (original 2.25), `Delta` 18.8 days (19.0), `I0` 4,777 (4,770), and `seasonality_min` 0.79 (0.80), with similar ranges. Peak weekly deaths projected from the posterior are 891 (897), 1,366 (1,363), and 2,231 (2,217) in the three scenarios. This is a change from before: a point estimate gave much smaller second waves |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

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

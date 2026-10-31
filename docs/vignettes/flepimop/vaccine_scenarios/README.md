# flepiMoP vaccination scenarios, in Starsim

The translation of [models/flepimop/vaccine_scenarios](../../../models/flepimop/vaccine_scenarios), flepiMoP's wave 3 model. The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 141, plus 10 lines of CSV | 33 | Lines over 100 characters count twice. Was 38 before the fixes below |
| 6 runs (3 scenarios of 2) | first 30 s, rerun 31 s | first 0.79 s, rerun 0.71 s (Rust) | The original can run only as a whole command, so its first run and rerun are both that command, once each; after its first run each takes 2.6 s. Both are timed at 2 runs of each scenario, not the 10 of the results, to keep the benchmark short; the times shown here are still for 30 runs |
| Results, with the original's draws | | | **Agree exactly, by province** (tolerance 1e-9). Run with the values of `Ro` and of the share of cases detected that the original drew, the mean, 5%, and 95% of all 28 series in each province (5 compartments, 5 incidences, and the 4 outcomes, including the number in hospital) agree within 1e-9 of their largest value in all three scenarios |
| Results, with Starsim's own draws | | | **Agree in distribution** (tolerance 30%, since the original has only ten runs, drawn afresh each time it is run). With 100 runs of each scenario, the mean peak of `I` in the large province is 1,099, 466, and 17 (original, from 10 runs: 1,103, 482, and 15), and the mean deaths are 89.0, 60.0, and 2.2 (88.8, 60.6, and 1.9) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `4473e253`), on a 20-core Linux machine.

## What was declared and what was not

Declared: the five states and five transitions (the vaccination and waning rates as sums of two named parameters), the four outcomes by province (one chained from another, and the stay in hospital as a fixed duration), the stratification by province with visiting, the three scenarios as `ss.modify` with a start and a stop, stacked by putting them in a list, and the uncertainty in `Ro` and the share of cases detected, as `prior=` on `ss.par`, with `ss.truncnorm` as in the original.

`runs()` makes each scenario's sims with its draws. `ss.parallel(sims, n_runs=10, priors=True)` does this in one call, and `compare.py` uses it; `model.py` keeps `runs()` so that the timing can run it as a list of sims.

## Findings

1. **Fixed: parameter uncertainty in forward runs.** flepiMoP draws `Ro` (and an outcome's probability) from a distribution once for each run. `ss.parallel(..., n_runs=10, priors=True)` now does this, and `ss.fit.prior_draws()` gives the draws.
2. **Fixed: truncated normal.** `ss.truncnorm(loc=, scale=, low=, high=)` is flepiMoP's usual way of writing an uncertain parameter, and replaces SciPy's here.
3. **A `MultiSim` given to `ss.parallel()` loses its options** (a bug, new). `ss.parallel(ss.MultiSim(sims, n_runs=2, priors=True))` runs each sim once, without any warning, rather than giving an error or the runs asked for.
4. **Fixed: outcomes are kept by group.** Every outcome now agrees by province, including their delays and durations.
5. **A fixed `duration=` on an outcome is still written as a distribution.** `duration=ss.constant(10, unit='days')` is a stay of exactly ten days, and agrees to 1e-9. A plain `duration=ss.days(10)` is an exponential stay, unlike `delay=ss.days(10)`, which is exact. Whether they should match is still open.
6. **`stop=` is the first day off.** flepiMoP's `period_end_date` is the last day a modifier applies; Starsim's `stop=` is the first day it does not (`[start, stop)`, now documented), so the vignette gives `stop='2020-09-01'`.
7. **`substeps=1` gives the same steps.** The original takes one RK4 step a day. By default Starsim subdivides a step when rates are high, which differs by up to 5e-6 of a series' largest value here; with `substeps=1` the two agree within 1e-9.
8. **Fixed: modifiers that depend only on time stay in one call to the kernel, and are named after their target** (`nu_opt_multiply`). `describe()` no longer calls `Ro` a rate.

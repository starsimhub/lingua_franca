# flepiMoP: vaccination scenarios in two subpopulations

The two-province SEIR of the [wave 1 example](../seir_2pop) with most of what else a flepiMoP configuration can declare for a forward run added on top: a vaccinated compartment with waning, three scenarios defined as modifiers that switch parameters off, outcomes (reported cases, hospital admissions, the number in hospital, and deaths) derived from the incidence of infectiousness by a probability and a delay, and parameter uncertainty, with `Ro` and the probability of detecting a case drawn from truncated normals for each of ten runs ("slots") of each scenario. It is flepiMoP's `config_sample_2pop_vaccine_scenarios.yml`, which brings together the scenarios, outcomes, and parameter uncertainty that the other forward-simulation tutorials show one at a time, and the configuration that flepiMoP's own tests of scenarios and outcomes run (`tests/seir/test_run_parallel_SEIR.py`, `tests/outcomes/test_run_parallel_outcomes.py`).

This is flepiMoP's wave 3 model. `model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 141, plus 10 lines of CSV | 33 | Lines over 100 characters count twice. Was 38 before the fixes below |
| 6 runs (3 scenarios of 2) | first 23 s, rerun 22 s | first 1.2 s, rerun 0.35 s (JAX) | The original can run only as a whole command, so its first run and rerun are both that command, once each; after its first run each takes 2.6 s. Both are timed at 2 runs of each scenario, not the 10 of the results, to keep the benchmark short; the times shown here are still for 30 runs |
| Results, with the original's draws | | | **Agree exactly, by province** (tolerance 1e-9). Run with the values of `Ro` and of the share of cases detected that the original drew, the mean, 5%, and 95% of all 28 series in each province (5 compartments, 5 incidences, and the 4 outcomes, including the number in hospital) agree within 1e-9 of their largest value in all three scenarios |
| Results, with Starsim's own draws | | | **Agree in distribution** (tolerance 30%, since the original has only ten runs, drawn afresh each time it is run). With 100 runs of each scenario, the mean peak of `I` in the large province is 1,099, 466, and 17 (original, from 10 runs: 1,103, 482, and 15), and the mean deaths are 89.0, 60.0, and 2.2 (88.8, 60.6, and 1.9) |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

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

## What it exercises

- Everything in [seir_2pop](../seir_2pop): compartments, transitions as a rate times what they are proportional to, subpopulations coupled by mobility, initial conditions from a file, and a fixed-step RK4 solver
- A rate that is a sum of two parameters (`nu_pess + nu_opt`), so that each part can be modified on its own
- Scenarios (`seir_modifiers`): `SinglePeriodModifier`s that multiply a parameter by a value over a period, `StackedModifier`s that combine them, and a list of the scenarios to run
- Parameters drawn from distributions (`truncnorm`), once for each run, and several runs of each scenario (`nslots: 10`)
- Outcomes (`outcomes`, `method: delayframe`): a probability and a delay applied to the incidence of a compartment, an outcome whose source is another outcome (deaths from hospitalizations), and a duration that gives a prevalence (`currHosp`)

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/config_sample_2pop_vaccine_scenarios.yml`: the configuration, unchanged
- `original/model_input/geodata_sample_2pop.csv`, `mobility_sample_2pop.csv`, `ic_2pop.csv`: the populations, the mobility, and the initial conditions, unchanged (the same as in `seir_2pop`)
- `run.py`: runs it with `flepimop simulate` and writes `reference/`
- `reference/results.csv`: for each scenario (`no_vax`, `pess_vax`, `opt_vax`) and province, the mean and 5% to 95% range over the ten runs of: the amount in each compartment at the start of each day (`no_vax_large_province_S`, ..., `_V`), the amount entering it during the day (`no_vax_large_province_incidence_S`, ...), and each outcome (`no_vax_large_province_incidCase`, `_incidHosp`, `_currHosp`, `_incidDeath`), for days 0 to 212, where day 0 is 1 February 2020. The range is the lowest and the ninth-lowest of the ten runs on each day, as in the other examples
- `reference/draws.csv`: the values of `Ro` and of the probability of detecting a case drawn for each run of each scenario. flepiMoP sets no seed, so another run of `run.py` draws other values; with these, a translation can reproduce the reference exactly
- `reference/timing.json`: the time of the whole command, the first time and again
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (GPL-3.0)

## The model

The compartments are `S`, `E`, `I`, `R`, and `V`, and the populations, mobility, initial conditions, dates, and solver are those of [seir_2pop](../seir_2pop), which describes how flepiMoP couples the provinces.

| Transition | Rate (amount per day) |
|---|---|
| `S` to `E` | `Ro * gamma` times `S` and the mobility-weighted prevalence of `I`, as in `seir_2pop` |
| `E` to `I` | `sigma * E`, with `sigma = 1/4` |
| `I` to `R` | `gamma * I`, with `gamma = 1/5` |
| `S` to `V` | `(nu_pess + nu_opt) * S`, with `nu_pess = 0.01` and `nu_opt = 0.03` |
| `V` to `S` | `(omega_pess + omega_opt) * V`, with `omega_pess = 0.02` and `omega_opt = 0.01` |

`V` gives complete protection, and waning returns people to `S`.

### Parameter uncertainty

`Ro` is drawn from a normal of mean 2.5 and standard deviation 0.1 truncated to [1.1, 3], once for each run, and used in both provinces for the whole run. The ten runs of a scenario differ only in this and in the probability of detecting a case; the SEIR itself is deterministic. In the reference, `Ro` ranged from 2.18 to 2.61 over the 30 runs.

### Scenarios

Each modifier multiplies one parameter by 0 from 1 February to 31 August 2020 (both included, so the whole run) in every subpopulation (a `SinglePeriodModifier`'s `value` multiplies the parameter, because the parameter's `stacked_modifier_method` is the default, `product`). They are stacked into three scenarios, each run separately:

| Scenario | Switched off | Vaccination rate | Waning rate |
|---|---|---|---|
| `no_vax` | all four | 0 | 0 |
| `pess_vax` | `nu_opt`, `omega_opt` | 0.01 | 0.02 |
| `opt_vax` | `nu_pess`, `omega_pess` | 0.03 | 0.01 |

The comments in the configuration call each of `pess_vax`, `opt_vax`, and `no_vax` "turn off all vaccination", which is true only of `no_vax`.

### Outcomes

All are computed after the SEIR, from the daily incidence of `I` (the flow from `E` to `I`) in each subpopulation, by multiplying by a probability and shifting by a whole number of days:

| Outcome | Source | Probability | Delay |
|---|---|---|---|
| `incidCase` | incidence of `I` | truncated normal of mean 0.5, standard deviation 0.05, on [0.3, 0.7], drawn once for each run | 5 days |
| `incidHosp` | incidence of `I` | 0.05 | 7 days |
| `incidDeath` | `incidHosp` | 0.2 | 14 days |

`incidHosp` has a duration of 10 days, which gives `currHosp`: the admissions of the last 10 days, including the current one (a stay of exactly 10 days, not a distribution). With the RK4 solver outcomes are the expected values; with a stochastic solver they would be binomial draws.

## Results

The mean of the ten runs of each scenario, summed over the two provinces:

| Scenario | Peak `I`, large province | Peak `I`, small province | `R` at the end | `V` at the end | Cases | Admissions | Peak in hospital | Deaths |
|---|---|---|---|---|---|---|---|---|
| `no_vax` | 1,064 on day 64 | 118 on day 82 | 8,840 | 0 | 4,160 | 442 | 115 | 88.4 |
| `pess_vax` | 495 on day 74 | 47 on day 105 | 6,117 | 1,338 | 3,103 | 306 | 52 | 61.1 |
| `opt_vax` | 16 on day 40 | 0.1 on day 52 | 206 | 7,344 | 102 | 10 | 1.7 | 2.1 |

At a vaccination rate of 0.03 a day, most people are vaccinated before the epidemic can grow, so in `opt_vax` it never takes off.

## Lines of model code

141: every line of `config_sample_2pop_vaccine_scenarios.yml` that is neither blank nor a comment (including the commented-out `outcome_modifiers` block, which is not counted). No counted line is over 100 characters. The three CSV files add 10 lines of data, including their headers.

## Timing

The whole command (three scenarios of ten runs each, with their outcomes, in one process with `--jobs 1`) took about 96 s. After the first, each run takes about 2.6 s; the outcomes take 0.3 s for each scenario. flepiMoP runs only as a whole command, so a rerun is the command again. Each is timed once, not as the best of several.

## Notes

- `flepimop simulate` with `--out-id` but not `--in-id` runs the SEIR and then fails in the outcomes, which look for the SEIR output under a new, timestamped ID; `run.py` gives both.

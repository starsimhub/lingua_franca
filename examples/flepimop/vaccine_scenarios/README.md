# flepiMoP: vaccination scenarios in two subpopulations

The two-province SEIR of the [wave 1 example](../seir_2pop) with most of what else a flepiMoP configuration can declare for a forward run added on top: a vaccinated compartment with waning, three scenarios defined as modifiers that switch parameters off, outcomes (reported cases, hospital admissions, the number in hospital, and deaths) derived from the incidence of infectiousness by a probability and a delay, and parameter uncertainty, with `Ro` and the probability of detecting a case drawn from truncated normals for each of ten runs ("slots") of each scenario. It is flepiMoP's `config_sample_2pop_vaccine_scenarios.yml`, which brings together the scenarios, outcomes, and parameter uncertainty that the other forward-simulation tutorials show one at a time, and the configuration that flepiMoP's own tests of scenarios and outcomes run (`tests/seir/test_run_parallel_SEIR.py`, `tests/outcomes/test_run_parallel_outcomes.py`).

## What it exercises

- Everything in [seir_2pop](../seir_2pop): compartments, transitions as a rate times what they are proportional to, subpopulations coupled by mobility, initial conditions from a file, and a fixed-step RK4 solver
- A rate that is a sum of two parameters (`nu_pess + nu_opt`), so that each part can be modified on its own
- Scenarios (`seir_modifiers`): `SinglePeriodModifier`s that multiply a parameter by a value over a period, `StackedModifier`s that combine them, and a list of the scenarios to run
- Parameters drawn from distributions (`truncnorm`), once for each run, and several runs of each scenario (`nslots: 10`)
- Outcomes (`outcomes`, `method: delayframe`): a probability and a delay applied to the incidence of a compartment, an outcome whose source is another outcome (deaths from hospitalizations), and a duration that gives a prevalence (`currHosp`)

## Files

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

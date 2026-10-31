# epydemix: SIR in Kenya with age-structured contacts

A stochastic SIR epidemic in the population of Kenya (55.9 million people in five age groups), mixing through contact matrices for school, work, home, and community, over four months. It is the model of epydemix's second tutorial, "Using population data from epydemix_data".

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 7 | 14 | Not counting the loading of the data would be 12. The original has the model predefined and the population bundled |
| One stochastic run | first 0.0076 s, rerun 0.007 s | first 0.016 s, rerun 0.0011 s (Rust) | In process, without imports or loading the data. Both are the time of one run, with the 100 runs of the original taking about 0.6 s |
| Results | | | **Agree** (peaks within 1%, a day apart at most, final size within 0.1 of a percentage point): the mean of 100 runs peaks 0.4% higher than the original, a day sooner, and the final size is the same (99.63%). On any one day the difference is up to 6% of the peak, since the rise is a day ahead (see the findings) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `4473e253`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The population and the contact matrices are read from the file that the original's run wrote, so that the two models are the same.

## Findings

- **Longer than the original.** epydemix has the SIR model predefined and the population bundled, so the whole example is seven lines, which is hard to beat. Starsim now bundles populations and contact matrices too: `ss.contacts('Kenya')` with `people=ss.people('Kenya', year=2020)` needs no file and removes the loading lines. This vignette does not use them because they are a different population, 52.2 million in Starsim's data for 2020 against 55.9 million in epydemix's, so it would not be a test of the same model.
- **`substeps=1` is needed.** epydemix takes one chain-binomial step a day. Starsim's chain binomial now takes substeps by default, so that no more than about a tenth of a compartment leaves in one, and without `substeps=1` the peak comes on day 36 rather than 39 and is 54.0% rather than 54.7%, against the original's 54.5% on day 40. The default is more accurate as an approximation to continuous time; the original's model is discrete by design.
- **Fixed: a result of many runs can be selected by age group.** `res.I.select(age='0-4')` now works on the runs together.
- **Fixed: aging can be switched off.** Stratifying by age turns aging on in a compartmental run; `use_aging=False` turns it off, which is what the original assumes.
- **Ten infected, not eight.** The original spreads ten infections over the age groups and rounds each down, starting with eight. Starsim starts with ten, which is why its peak comes up to a day sooner.

## What it exercises

- A predefined model (`load_predefined_model("SIR")`) rather than one written out: two transitions, one "mediated" (infection) and one "spontaneous" (recovery)
- Stratification by age that comes from the population, not from the model: the model names three compartments, and the population supplies the five groups
- Mixing by a contact matrix that is the sum of four layers, loaded by country name from a data repository
- Initial conditions given as a fraction of the population to seed, split across the age groups
- A stochastic (chain-binomial) solver with a daily step, run 100 times and summarized

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/sir_kenya.py`: code cells 4, 11, 12, and 14 of the tutorial notebook, unchanged (a script extracted from a notebook; the other cells plot the inputs or show other ways to load a population)
- `simulate.py`: runs the original in the epydemix environment with a fixed seed and prints the summary and timing as JSON
- `run.py`: calls `simulate.py` and writes `reference/`
- `reference/results.csv`: the mean and the 5% to 95% range of 100 runs (seed 1), for each compartment (`Susceptible_<group>`, `Infected_<group>`, `Recovered_<group>`) and each daily flow (`new_Susceptible_to_Infected_<group>`, `new_Infected_to_Recovered_<group>`), where `<group>` is `0-4`, `5-19`, `20-49`, `50-64`, `65+`, or `total`
- `reference/population.json`: the inputs that come from the data rather than the script: the size of each age group, the four contact matrices, and the initial state
- `reference/timing.json`: the time of a first run and of a rerun of one stochastic run
- `meta.yaml`: where it came from
- `LICENSE`: the license of epydemix (GPL-3.0)

## The model

- **Compartments:** `Susceptible`, `Infected`, `Recovered`, each split into the age groups 0-4, 5-19, 20-49, 50-64, and 65+
- **Infection:** a susceptible person in group `i` is infected at the rate `transmission_rate * sum_j C[i,j] * Infected[j] / N[j]`, where `C` is the sum of the four contact matrices (contacts per day) and `N[j]` is the size of group `j`
- **Recovery:** at the rate `recovery_rate`
- **Parameters:** `transmission_rate = 0.04` per contact (set in the tutorial), `recovery_rate = 0.1` per day (the default of the predefined model)
- **Population:** 7,066,801, 20,106,945, 22,824,354, 4,243,230, and 1,643,164 people in the five groups (55,884,494 in all), with the contact matrices of Prem et al. 2021, the default source for Kenya
- **Initial conditions:** `percentage_in_agents = 10/N`, which is applied to each group and rounded down, giving 1, 3, 4, 0, and 0 infected (8, not 10); everyone else is susceptible
- **Time:** 1 December 2019 to 1 April 2020, 123 steps of one day
- **Solver:** chain-binomial: each day, the number leaving a compartment in a group is a multinomial draw with the probability `1 - exp(-rate * dt)`

In `results.csv`, time is in days from the start of 1 December 2019. Time 0 is the initial state, which is the same in every run. epydemix reports each compartment at the end of each day and each flow summed over the day, so its first output (dated 1 December) is at time 1.

## Data

The population and contact matrices are downloaded when the model runs, from the [epydemix-data](https://github.com/epistorm/epydemix-data) repository at the tag `v1.2.0` (the version epydemix 1.4.0 asks for), so `run.py` needs a network connection. What was downloaded is recorded in `reference/population.json`.

## The seed

The tutorial sets no seed. `simulate.py` wraps `run_simulations` to pass `rng=1`, which makes the reference results repeatable without changing the original.

## Lines of model code

7: loading the population (1), loading the predefined model (1), setting its population (1), and running it (4). This leaves out the imports, the `print` calls, and the plotting. Loading the population is counted because it defines the age groups and the mixing; without it the count is 6.

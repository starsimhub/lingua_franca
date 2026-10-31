# epydemix: SIR in Kenya with age-structured contacts

A stochastic SIR epidemic in the population of Kenya (55.9 million people in five age groups), mixing through contact matrices for school, work, home, and community, over four months. It is the model of epydemix's second tutorial, "Using population data from epydemix_data".

## What it exercises

- A predefined model (`load_predefined_model("SIR")`) rather than one written out: two transitions, one "mediated" (infection) and one "spontaneous" (recovery)
- Stratification by age that comes from the population, not from the model: the model names three compartments, and the population supplies the five groups
- Mixing by a contact matrix that is the sum of four layers, loaded by country name from a data repository
- Initial conditions given as a fraction of the population to seed, split across the age groups
- A stochastic (chain-binomial) solver with a daily step, run 100 times and summarized

## Files

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

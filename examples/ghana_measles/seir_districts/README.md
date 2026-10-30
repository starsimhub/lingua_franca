# Ghana measles: SEIR in 260 districts

A stochastic metapopulation SEIR model of measles in Ghana's 260 districts, run daily from 2010 to 2025 with binomial draws. It is the rewrite of a LASER-measles notebook in the Ghana measles project.

## What it exercises

- 260 places with great-circle distances, and gravity mixing: residents make a share of their contacts in other districts, in proportion to their population over distance to a power
- Seasonal transmission
- Births at a crude rate, some of whom are immune through routine vaccination, and deaths from every state
- Importation at a constant rate per person
- Reported cases, a fixed share of infections, counted at onset
- A population projected back from 2020 to the start, and a susceptible share that starts at its endemic equilibrium

## Files

- `run.py`: runs the original and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range over 50 runs of the national `S`, `E`, `I`, and `R` at the start of each month (`national_...`), the infections and reported cases in each month (`monthly_infections`, `monthly_cases`), and the infections in each region from 2020 on (`region_<name>`)
- `reference/timing.json`: the times of a first run and a rerun, each building the sim
- `meta.yaml`: where it came from

The source is not copied into `original/`, since the Ghana measles project has no public repository yet; `run.py` reads it from a checkout next to this repository. The default parameters are used throughout.

## Lines of model code

89, counting every line of `ghana_measles/model.py` before `Sim.monthly()` that is not blank, a comment, a docstring, or an import.

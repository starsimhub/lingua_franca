---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Measles metapopulation: SEIR in 260 districts

A stochastic metapopulation SEIR model of measles in 260 made-up districts, run daily from 2010 to 2025 with binomial draws. The districts and all its values are made up.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 89 | 22 | Long lines count twice; two lines read the data |
| One run | first 0.82 s, rerun 0.82 s | first 0.44 s, rerun 0.41 s (Rust) | Both with the data already loaded. The original has no separate rerun, so its first run and rerun both build and run the sim |
| Results | | | **Agree.** Over 2010 to 2025, 1,734,028 infections against 1,740,643 and 17,325 reported cases against 17,396 (means of 50 runs each); monthly means correlate at 0.999 and 0.998; infections from 2020 in each of the 16 regions within 6% (`compare.py` asks for totals within 2%, each year within 20%, a correlation over 0.98, regions within 20%, and `S` and `R` at the end within 3%) |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: seven transitions, an outcome, the districts as a geography, and the mixing between them as visiting (`ss.geo.Mobility(ss.geo.gravity(distance_power=2), kind='visit', away=0.01)`), which is the original's form: residents are exposed to the prevalence where they make their contacts, and do not change who is present there.

## Findings

- **Nothing was missing.** This model has places with latitudes and longitudes, gravity, seasonality, births into two states, deaths from every state, and a reporting share at onset, and each has a direct form.
- **Importation is awkward to write.** The original adds a fixed number of infections per person in the population. A transition's rate is per person in its source, so this is written as `ss.peryear(0.01/1000) * (S + E + I + R).n / S.n`. An inflow into a state from outside the population would read better, but `ss.null >> E` would add people rather than move them.
- **Whole days have to be asked for.** The original takes a binomial draw a day. Starsim's chain binomial takes smaller steps by default, so the model gives `substeps=1`.
- **Results by district are kept weekly by default.** A run of 5,844 days over 260 districts would otherwise keep a lot, so Starsim keeps them by group every 7 days, and says so. `compare.py` needs daily onsets, so it asks for them with `group_results=['onset']`.

## What it exercises

- 260 places with great-circle distances, and gravity mixing: residents make a share of their contacts in other districts, in proportion to their population over distance to a power
- Seasonal transmission
- Births at a crude rate, some of whom are immune through routine vaccination, and deaths from every state
- Importation at a constant rate per person
- Reported cases, a fixed share of infections, counted at onset
- A population projected back from 2020 to the start, and a susceptible share that starts at its endemic equilibrium

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `run.py`: runs the original and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range over 50 runs of the national `S`, `E`, `I`, and `R` at the start of each month (`national_...`), the infections and reported cases in each month (`monthly_infections`, `monthly_cases`), and the infections in each region from 2020 on (`region_<name>`)
- `reference/timing.json`: the times of a first run and a rerun, each building the sim
- `meta.yaml`: where it came from

`original/` has the model, and `make_districts.py`, which writes the districts. The default parameters are used throughout.

## Lines of model code

89, counting every line of `measles_metapop.py` before `Sim.monthly()` that is not blank, a comment, a docstring, or an import.

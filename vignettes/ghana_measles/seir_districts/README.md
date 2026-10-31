# Ghana measles, in Starsim

The translation of [examples/ghana_measles/seir_districts](../../../examples/ghana_measles/seir_districts). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 89 | 23 | Long lines count twice; two lines read the data |
| One run | first 2.3 s, rerun 1.2 s | first 2.8 s, rerun 0.66 s (Rust) | Both with the data already loaded. The original has no separate rerun, so its first run and rerun both build and run the sim |
| Results | | | **Agree.** Over 2010 to 2025, 3,035,293 infections against 3,040,585 and 15,169 reported cases against 15,185 (means of 20 and 50 runs); monthly means correlate at 0.999 and 0.998; infections from 2020 in each of the 16 regions within 7% (`compare.py` asks for totals within 2%, each year within 20%, a correlation over 0.98, regions within 20%, and `S` and `R` at the end within 3%) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: seven transitions, an outcome, the districts as a geography, and the mixing between them as visiting (`ss.geo.Mobility(ss.geo.gravity(c=1.5), kind='visit', away=0.01)`), which is the original's form: residents are exposed to the prevalence where they make their contacts, and do not change who is present there.

## Findings

- **Nothing was missing.** This model has places with latitudes and longitudes, gravity, seasonality, births into two states, deaths from every state, and a reporting share at onset, and each has a direct form.
- **Importation is awkward to write.** The original adds a fixed number of infections per person in the population. A transition's rate is per person in its source, so this is written as `ss.peryear(0.01/1000) * (S + E + I + R).n / S.n`. An inflow into a state from outside the population would read better, but `ss.null >> E` would add people rather than move them.
- **Whole days have to be asked for.** The original takes a binomial draw a day. Starsim's chain binomial takes smaller steps by default, so the model gives `substeps=1`.
- **Results by district are kept weekly by default.** A run of 5,844 days over 260 districts would otherwise keep a lot, so Starsim keeps them by group every 7 days, and says so. `compare.py` needs daily onsets, so it asks for them with `results=['onset']`.

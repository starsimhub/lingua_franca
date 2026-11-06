---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# MEmilio: ODE SECIR model with severity branches

A deterministic COVID-19-type epidemic in one region and one age group of 83,000 people over 100 days: infection, then a chain of worsening states (no symptoms, symptoms, severe, critical), each of which ends in either the next state or recovery, with death from the critical state. Contacts are cut by 90% on day 30.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 44 | 14 | |
| One run | first 0.00046 s, rerun 0.00002 s | first 0.014 s, rerun 0.00037 s (Rust) | Neither counts starting Python or importing. MEmilio's solver is C++ code built in advance, so its first run has little to do |
| Results | | | **Agree.** Within 67 people of 83,000 at every time, which is the error of the reference itself (it is interpolated between steps of about two days); deaths within 0.5, of which 0.4 is the reference's error (it remains with a step of 0.01 days) and 0.12 is Starsim's daily step. `compare.py` allows 73 people and 0.6 deaths |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. Each severity step is one transition with two destinations and a probability; deaths leave the model, so they are counted from the flow and the people who mix are the ones alive, as in the original.

## Findings

- **Fixed: a value that varies in time was held for a whole step.** The original lowers contacts smoothly over day 29, along half a cosine. `ss.timeseries(..., interpolation='cosine')` says the same, and the ODE solver reads it at each stage of a step, so the translation no longer gives that day its average by hand.
- **Two states left out.** The original has two "confirmed" states that nothing flows into; they are not in the translation.
- **The dead are a flow, not a state.** The number dead is `res.death.cum`.

## What it exercises

- A model that is built in, not written: the user sets parameters and initial counts on a ready-made `Model`, and the equations are in C++
- Branching by probability on leaving a state, with one mean time per state (not one per branch)
- Infection from two states with different weights
- Age groups (one here) and a contact matrix with a baseline, a minimum, and dated reductions ("dampings")
- An initial state given as counts, with the susceptibles as the remainder of the total
- An adaptive ODE solver, with results interpolated to whole days

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/ode_secir_simple.py`: the example, unchanged
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the count in each of the 10 states on each of days 0 to 100 (`Susceptible`, `Exposed`, `InfectedNoSymptoms`, `InfectedNoSymptomsConfirmed`, `InfectedSymptoms`, `InfectedSymptomsConfirmed`, `InfectedSevere`, `InfectedCritical`, `Recovered`, `Dead`)
- `reference/timing.json`: the time of a first run and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (Apache-2.0)

The original prints only the final state and plots the rest. `run.py` runs its `run_ode_secir_simulation()` as it is and keeps the time series that the function passes through `interpolate_simulation_result`.

## The model

The equations are in `cpp/models/ode_secir/model.h` (`get_flows`) at the same tag. With one age group:

| Transition | Rate (people per day) |
|---|---|
| `Susceptible` to `Exposed` | `S * c(t) / N * TransmissionProbabilityOnContact * (RelativeTransmissionNoSymptoms * InfectedNoSymptoms + RiskOfInfectionFromSymptomatic * InfectedSymptoms)` |
| `Exposed` to `InfectedNoSymptoms` | `Exposed / TimeExposed` |
| `InfectedNoSymptoms` to `InfectedSymptoms` | `(1 - RecoveredPerInfectedNoSymptoms) * InfectedNoSymptoms / TimeInfectedNoSymptoms` |
| `InfectedNoSymptoms` to `Recovered` | `RecoveredPerInfectedNoSymptoms * InfectedNoSymptoms / TimeInfectedNoSymptoms` |
| `InfectedSymptoms` to `InfectedSevere` | `SeverePerInfectedSymptoms * InfectedSymptoms / TimeInfectedSymptoms` |
| `InfectedSymptoms` to `Recovered` | `(1 - SeverePerInfectedSymptoms) * InfectedSymptoms / TimeInfectedSymptoms` |
| `InfectedSevere` to `InfectedCritical` | `CriticalPerSevere * InfectedSevere / TimeInfectedSevere` |
| `InfectedSevere` to `Recovered` | `(1 - CriticalPerSevere - DeathsPerSevere) * InfectedSevere / TimeInfectedSevere` |
| `InfectedSevere` to `Dead` | `DeathsPerSevere * InfectedSevere / TimeInfectedSevere` (zero here) |
| `InfectedCritical` to `Dead` | `DeathsPerCritical * InfectedCritical / TimeInfectedCritical` |
| `InfectedCritical` to `Recovered` | `(1 - DeathsPerCritical) * InfectedCritical / TimeInfectedCritical` |

- **Branches:** every way out of a state has rate `probability / time in the state`, so the total rate out is `1 / time` and the probabilities split it. The time is the same whichever branch is taken.
- **`N`:** everyone alive, which is the sum of all states but `Dead`, so it falls as people die.
- **Contacts:** `c(t) = baseline - damping(t) * (baseline - minimum)`, with `baseline = 1` and `minimum = 0` contacts per day. The damping is 0 until day 29, 0.9 from day 30, and in between follows half a cosine, `0.45 - 0.45 * cos(pi * (t - 29))`: MEmilio smooths every change of contacts over the day before it. So `c` is 1 until day 29 and 0.1 from day 30.
- **Confirmed states:** `InfectedNoSymptomsConfirmed` and `InfectedSymptomsConfirmed` (detected cases) have the same ways out as the unconfirmed states, and nothing flows into them in this model. They start at 0 and stay there.

### Parameters

| Parameter | Value |
|---|---|
| `TimeExposed` | 3.2 days |
| `TimeInfectedNoSymptoms` | 2 days |
| `TimeInfectedSymptoms` | 6 days |
| `TimeInfectedSevere` | 12 days |
| `TimeInfectedCritical` | 8 days |
| `TransmissionProbabilityOnContact` | 1.0 |
| `RelativeTransmissionNoSymptoms` | 0.67 |
| `RiskOfInfectionFromSymptomatic` | 0.25 |
| `MaxRiskOfInfectionFromSymptomatic` | 0.5 (not reached) |
| `RecoveredPerInfectedNoSymptoms` | 0.09 |
| `SeverePerInfectedSymptoms` | 0.2 |
| `CriticalPerSevere` | 0.25 |
| `DeathsPerCritical` | 0.3 |
| `StartDay` | 0 (1 January; it only matters with seasonality) |

Left at their defaults, and so without effect: `Seasonality = 0`, `DeathsPerSevere = 0`, and `ICUCapacity` and `TestAndTraceCapacity`, both unlimited. With a limit, MEmilio raises the risk of infection from symptomatic people from `RiskOfInfectionFromSymptomatic` towards `MaxRiskOfInfectionFromSymptomatic` as tracing is overwhelmed, and sends people who cannot get a critical care bed to `Dead`.

### Initial state

Of 83,000 people: `Exposed` 100, `InfectedNoSymptoms` 50, `InfectedSymptoms` 50, `InfectedSevere` 20, `InfectedCritical` 10, `Recovered` 10, `Dead` 0, both confirmed states 0, and `Susceptible` the rest, 82,760.

### Time

Days 0 to 100. The solver is MEmilio's default, an adaptive Runge-Kutta (Cash-Karp 5(4), from Boost), with an absolute tolerance of 1e-10 and a relative tolerance of 1e-5; `dt = 0.1` is only its first step. It takes 50 steps. The example then interpolates linearly to whole days.

## Results

About a third of the population is infected: 27,304 have recovered and 375 have died by day 100, and 55,262 are still susceptible. `InfectedSymptoms` peaks at about 7,300 on day 33, just after contacts are cut.

Because the solver's steps are about two days long near the peak and the interpolation between them is linear, the daily values are not as accurate as the solver's tolerance suggests. Against a fixed-step integration of the same equations (fourth-order Runge-Kutta with a step of 0.01 days), the largest differences are 67 people in `Susceptible` (of 77,000, on day 19) and 24 in `InfectedSymptoms`; at day 100 every state agrees to within 1 person. A translation should be compared with that in mind.

## Lines of model code

44, of the 161 lines in the file: the population, time span, and step (7), the model and its age group (2), the five times, the initial counts (11), the eight probabilities, the start day (2), the contacts and their reduction (6), and applying constraints, simulating, and interpolating (3). Not counted: the license header, imports, the list of compartment names (used only for the plot), plotting, printing, the function definition, and the command-line parsing. The only line over 100 characters is in the command-line parsing.

## Notes

- The plot in the original is mislabeled: it assumes 8 states per age group, but the model has 10, so the lines labeled `InfectedSymptoms`, `Hospitalzed`, `InfectedCritical`, `Recovered`, and `Died` are in fact `InfectedNoSymptomsConfirmed`, `InfectedSymptoms`, `InfectedSymptomsConfirmed`, `InfectedSevere`, and `InfectedCritical`. This does not affect the simulation, and `reference/results.csv` takes its names from MEmilio's `InfectionState`.
- The other examples in the same folder upstream add age groups (`ode_secir_groups.py`, `ode_secir_ageres.py`), regions coupled by commuting (`ode_secir_mobility.py`), and vaccination (`ode_secirvvs_simple.py`).

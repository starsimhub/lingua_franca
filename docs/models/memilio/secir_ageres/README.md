# MEmilio: age-resolved ODE SECIR, with seasonality and testing capacity

The SECIR model of [the wave 1 example](../secir) in three age groups of 10,000 people over 50 days, with three things the wave 1 example leaves at their defaults: seasonal transmission, a limited capacity to test and trace (so that symptomatic people infect more once it is overwhelmed), and contacts between every pair of age groups. Contacts are cut by 70% on day 30.

This is the age-resolved example among MEmilio's own Python examples (`pycode/examples/simulation/`). Of the others, `ode_secir_groups.py` adds six age groups with contact matrices from data, `ode_secir_mobility.py` regions coupled by commuting, and `ode_secirvvs_simple.py` vaccination with three layers of immunity; the two `2020_*` and `2021_*` examples are the published German models, and need data downloaded from public sources. This one was chosen because it is the only one that switches on seasonality and a testing capacity, which are the two features of MEmilio's SECIR model that are not plain transitions. Its three age groups are identical, so the age structure itself is a weak test.

## What it exercises

- Everything in [the wave 1 example](../secir): a built-in model whose user sets parameters and initial counts, branches by probability with one mean time per state, infection from two states with different weights, dated reductions in contacts ("dampings"), counts given per state with the susceptibles as the remainder, and an adaptive ODE solver
- Age groups, with a parameter value and initial counts for each, and a contact matrix between them
- Seasonal transmission, with a start day that places day 0 in the year
- A rate that depends nonlinearly on the state of the whole population: the risk of infection from symptomatic people rises along half a cosine as the number needing testing and tracing passes a capacity

## Files

- `original/ode_secir_ageres.py`: the example, unchanged
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the count in each of the 10 states, summed over the age groups, on each of days 0 to 50 (`Susceptible`, `Exposed`, `InfectedNoSymptoms`, `InfectedNoSymptomsConfirmed`, `InfectedSymptoms`, `InfectedSymptomsConfirmed`, `InfectedSevere`, `InfectedCritical`, `Recovered`, `Dead`), and `InfectedSymptoms` in each age group (`InfectedSymptoms_0` to `InfectedSymptoms_2`)
- `reference/timing.json`: the time of a first run and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (Apache-2.0)

The original prints the last value and the solver's time points, and (with `--show_plot`) plots the totals. `run.py` runs its `run_ode_secir_ageres_simulation()` as it is, keeps what `simulate()` returns, and interpolates it to whole days with MEmilio's `interpolate_simulation_result`, as the other MEmilio examples do.

## The model

The equations are in `cpp/models/ode_secir/model.h` (`get_flows`) at the same tag, and are those of [the wave 1 example](../secir#the-model), with these changes for age group `i`:

| Transition | Rate (people per day) |
|---|---|
| `Susceptible` to `Exposed` | `S_i * sum_j season(t) * c_ij(t) / N_j * TransmissionProbabilityOnContact_i * (RelativeTransmissionNoSymptoms_j * InfectedNoSymptoms_j + risk(t) * InfectedSymptoms_j)` |
| `InfectedSevere` to `InfectedCritical` and to `Dead` | as before, except that `CriticalPerSevere` falls towards 0 (and deaths rise to match) as the critical patients approach `ICUCapacity`; with the default capacity, which is unlimited, this has no effect |

- **Seasonality:** `season(t) = 1 + Seasonality * sin(pi * ((StartDay + t) / 182.5 + 0.5))`, which is `1 + 0.2 * cos(2 pi (60 + t) / 365)`: highest on day 0 of the year (1 January), and 60 days past it at the start.
- **Testing and tracing:** `risk(t) = smoother_cosine(T, 35, 5 * 35, 0.25, 0.45)`, where `T = sum_i (1 - RecoveredPerInfectedNoSymptoms_i) / TimeInfectedNoSymptoms_i * InfectedNoSymptoms_i` is the number becoming symptomatic each day, summed over every age group (the number to be tested and traced). `smoother_cosine(x, a, b, ya, yb)` is `ya` below `a`, `yb` above `b`, and half a cosine between. The capacity is `TestAndTraceCapacity = 35`, and the 5 is the default of `TestAndTraceCapacityMaxRisk`. Here `T` exceeds 35 from day 11 to day 34, and reaches 61 on day 30, so `risk` rises to about 0.27.
- **Contacts:** `c_ij(t) = 10/3` for every pair of groups, cut by 70% from day 30 (`c = baseline * (1 - damping)`, with the default minimum of 0), and smoothed over the day before by half a cosine, as in the wave 1 example.
- **`N_j`:** everyone alive in group `j`.

### Parameters

The same in every age group:

| Parameter | Value |
|---|---|
| `TimeExposed` | 3.2 days |
| `TimeInfectedNoSymptoms` | 2 days |
| `TimeInfectedSymptoms` | 5.8 days |
| `TimeInfectedSevere` | 9.5 days |
| `TimeInfectedCritical` | 7.1 days |
| `TransmissionProbabilityOnContact` | 0.05 |
| `RelativeTransmissionNoSymptoms` | 0.7 |
| `RecoveredPerInfectedNoSymptoms` | 0.09 |
| `RiskOfInfectionFromSymptomatic` | 0.25 |
| `MaxRiskOfInfectionFromSymptomatic` | 0.45 |
| `SeverePerInfectedSymptoms` | 0.2 |
| `CriticalPerSevere` | 0.25 |
| `DeathsPerCritical` | 0.3 |

And for the whole model: `StartDay = 60`, `Seasonality = 0.2`, `TestAndTraceCapacity = 35`. Left at their defaults: `TestAndTraceCapacityMaxRisk = 5`, `DeathsPerSevere = 0`, and `ICUCapacity`, unlimited.

### Initial state

Each age group has a third of 10,000 people and a third of each initial count: of 3,333.3, `Exposed` 33.3, `InfectedNoSymptoms` 16.7, `InfectedSymptoms` 16.7, `InfectedSevere` 6.7, `InfectedCritical` 3.3, `Recovered` 3.3, `Dead` 0, both confirmed states 0, and `Susceptible` the rest, 3,253.3. (The script's variable names swap `nb_inf_t0` and `nb_car_t0`, but both are 50.)

### Time

Days 0 to 50, with MEmilio's default solver: an adaptive Runge-Kutta (Cash-Karp 5(4)), with `dt = 0.1` as its first step. It takes 36 time points.

## Results

Because every age group starts the same and mixes evenly, the three groups stay identical. By day 50, 1,810 have recovered and 22 have died, and 7,994 are still susceptible. `InfectedSymptoms` peaks at 318 on day 31, just after the cut in contacts. Seasonality matters most (without it, 8,285 would still be susceptible); testing and tracing less so (with the risk held at 0.25, 8,012).

Against a fixed-step integration of the same equations (fourth-order Runge-Kutta with a step of 0.001 days), the daily values differ by at most 1.5 people (in `Recovered`, on day 43), because the reference is interpolated linearly between solver steps of up to two days. A translation should be compared with that in mind.

## Lines of model code

45, of the 155 lines in the file: the model and its time span (4), the contacts and initial counts (3, with the line of initial counts, at 130 characters, counted twice), the number of groups and the share of each (2), the start day, seasonality, and testing capacity (3), the loop over age groups (2), the five times (5), the initial counts (9), the eight probabilities (8), applying constraints (1), the contacts and their reduction (5), `model = model` (1), and simulating (2). Not counted: the license header, imports, the function definition and docstring, `nb_comp` (used only to sum the results for the plot), printing, summing and plotting the results, and the command-line parsing.

## Notes

- As in the wave 1 example, the plot assumes 8 states per age group but the model has 10, so the labels after `InfectedNoSymptoms` are wrong; and it is saved as `osecir_simple.pdf`. This does not affect the simulation, and `reference/results.csv` takes its names from MEmilio's `InfectionState`.

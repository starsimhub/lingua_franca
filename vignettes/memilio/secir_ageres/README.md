# MEmilio age-resolved SECIR, in Starsim

The translation of [examples/memilio/secir_ageres](../../../examples/memilio/secir_ageres), MEmilio's wave 3 example. The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 45 | 22 | 18 lines, three of them over 100 characters, so counted twice |
| One run | first 0.00088 s, rerun 0.00006 s | first 0.03 s, rerun 0.0021 s (Rust) | Neither counts starting Python or importing. Starsim's first run is nearly all building the sim. MEmilio's solver is C++ code built in advance |
| Results | | | **Agree.** Within 1.5 people of 10,000 at every time (1.3 in `Susceptible`, 1.5 in `Recovered`), the same with a step of a day or a tenth of a day, which is the error of the reference itself (it is interpolated between solver steps); deaths within 0.02. `compare.py` allows 1.5 people and 0.02 deaths |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: the seven states and seven transitions (as in [the wave 1 vignette](../secir)), the three age groups and their contact matrix, the initial counts (split evenly between the groups), seasonality as an `ss.seasonal`, the cut in contacts as an `ss.timeseries` with `mode='cosine'`, and the rise in the risk of infection from symptomatic people as testing and tracing is overwhelmed, as an expression of the count in `INS` (`np.clip` and `np.cos` of `INS.n`) used as the weight of `ISy`.

Left out, as having no effect here: the two confirmed states (nothing flows into them), the ICU capacity (unlimited), and `DeathsPerSevere` (0). The dead leave the model, as in the wave 1 vignette.

## Findings

1. **Fixed: a value that varies in time was held for a whole step.** The ODE read `ss.seasonal` and `ss.timeseries` once at the start of each step, while MEmilio evaluates them at every stage of its solver, which gave differences of 9 people at a step of a day. The ODE now reads them at each stage, and the results no longer depend on the step.
2. **Fixed: a rate could not clip or smooth a count.** The risk is 0.25 below a threshold of the count in `INS`, 0.45 above five times it, and half a cosine between. Rates now accept `np.clip` and `np.cos` of counts and build them into the run, so the risk is two declared lines, `sim.restart()` works, and `describe()` prints the whole formula.
3. **A state's count cannot be read inside a function through the state itself** (still open, but not needed here). In a function of the sim, `INS.n` is a symbolic expression, not a number, so `np.clip(INS.n, 0, 1)` inside a function raises a `TypeError`; the function has to use `sim.diseases.secir.INS.n`. The smallest fix: let the declared states it closes over evaluate to their current counts, or give the error a hint.
4. **The threshold is on a flow, which has to be written again as a count** (open). MEmilio's quantity to trace is the number becoming symptomatic each day, the flow of `symptoms` to `ISy`. Starsim has no way to name a transition's current flow in a rate, so the expression writes it as `0.91/2*INS.n`, repeating the probability and the time from `symptoms`. A `symptoms.flow` that can be used in an expression would remove the repetition.
5. **Fixed: a change in contacts smoothed over a day.** `ss.timeseries({0: 1.0, 29: 1.0, 30: 0.3}, mode='cosine')` is written as MEmilio's damping.
6. **A note that doesn't apply.** Building the sim says that `secir.infection` uses `INS.n` literally, so `contacts` does not apply to it. That is what's wanted here, since the risk depends on the count in the whole population, but the note reads like a warning. The results show that it is harmless.
7. **Seasonality relative to a start day** (fine, but obscure). MEmilio places day 0 at `StartDay = 60` of a 365-day year; with no dates, `ss.seasonal` starts at the beginning of a year, so the peak is written `peak=ss.days(-60)`. It matches exactly.
8. **Age groups as labels** (worked). The groups are named `'0'`, `'1'`, and `'2'`, as MEmilio numbers them; Starsim treats them as labels, not ages, and does not age anyone.

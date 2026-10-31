# SimInf SISe3 in 1,600 herds, in Starsim

The translation of [examples/siminf/sise3](../../../examples/siminf/sise3). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 27 | 40 | 13 of the Starsim lines read the data and turn SimInf's events, all four kinds, into a movement register, which the original gets from the package. The disease itself has four lines that turn SimInf's daily update of `phi` into rates and seasons. The original's equations are in SimInf's C code, and are not counted |
| One run | first 0.36 s, rerun 0.11 s | first 1.1 s, rerun 0.8 s (Rust) | Gillespie's method on one thread in both, as compartments (whole animals by herd, with `phi` a real number). Neither time counts starting up or reading the data (nor, for Starsim, turning the events into a register). A rerun of the original is `run(model)` again |
| Results | | | **Agree, within a herd, between herds, and in the demography.** With 100 runs (`compare.py` now makes 50, to keep the benchmark short, and allows the same three standard errors), every series is within two standard errors of the difference from SimInf's mean on every day checked (three is the tolerance), and 81% to 97% of the runs are inside SimInf's 5% to 95% range for every series on every day. On day 1,457 the mean of 100 runs has 181 ± 13 herds infected (SimInf: 166, range 24 to 352) and 4,175 ± 309 animals (3,770; 519 to 8,138). The spread between herds runs a little high on every day (175 herds in 200 runs), within the noise, so a small difference there cannot be ruled out |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

`python compare.py 100` (100 runs one after another, a few minutes; by default it makes 50) gives, for the mean of the runs (± its standard error) against the mean of SimInf's 200:

| Day | Herds infected | Animals infected | `phi` in node 1 | Infected in node 1 | `S_1` |
|---|---|---|---|---|---|
| 92 | 1.28 ± 0.05 (1.16) | 43 ± 2 (41) | 2.27 ± 0.09 (2.28) | 40 ± 2 (40) | 17,088 (17,088) |
| 183 | 2.5 ± 0.1 (2.3) | 81 ± 3 (75) | 3.84 ± 0.06 (3.90) | 62 ± 1 (63) | 17,822 (17,822) |
| 365 | 4.0 ± 0.3 (3.4) | 99 ± 5 (88) | 2.43 ± 0.04 (2.39) | 45 ± 1 (44) | 12,084 (12,084) |
| 729 | 15.1 ± 1.1 (13.0) | 332 ± 25 (288) | 2.35 ± 0.04 (2.33) | 42 ± 1 (41) | 12,034 (12,036) |
| 1,093 | 54 ± 4 (49) | 1,184 ± 94 (1,059) | 2.36 ± 0.04 (2.32) | 43 ± 1 (43) | 11,952 (11,959) |
| 1,457 | 181 ± 13 (166) | 4,175 ± 309 (3,770) | 2.38 ± 0.04 (2.33) | 47 ± 1 (45) | 11,795 (11,819) |

A count at index `t` is the number on day `t`, with the transitions of SimInf's day `t` and that day's scheduled events. With aging in the register, in SimInf's order (exits, entries, aging, then movements between herds), the susceptible counts agree to within a few animals in the first years.

## What was declared and what was not

Everything is declared. The six compartments are states, and the infectious pressure `phi` is a state that is not people, stratified by herd with the people, so that each herd has its own `phi`. Infection is a spontaneous transition at rate `upsilon * phi.n` (the herd's own `phi`), and recovery goes back to `S_k`. Shedding into `phi` is an inflow at rate `alpha * I.n / N.n`, and its decay an outflow at a seasonal rate, an `ss.timeseries` that repeats every 365 days. The initial conditions are by herd (`ss.by`). All 783,773 events are one movement register: births have no `from`, deaths no `to`, movements a `from` and a `to`, and aging the same herd as `from` and `to` with `to_states` (`states='S_1,I_1'`, `to_states='S_2,I_2'`); `states` names the age category the animals are chosen from.

## Findings

1. **Fixed: a state that is not people was a whole number under the stochastic solvers.** `phi` used to be shed and decayed one unit at a time, so the infection died out, and only agents could run the model. Such a state is now a real number under `gillespie`, `tau`, and `binomial`, with its flows as expected values, while the animals are drawn, as in SimInf.

2. **Fixed: the update of `phi`.** Earlier versions gave too much `phi` at equilibrium, and as agents advanced it inconsistently. Counts are now integrated over each step with the people as they are.

3. **Fixed: a movement register could not move people between states.** SimInf's `intTrans` events, 40% of all the events, age animals from `S_1` to `S_2` and from `I_1` to `I_2`, which used to need a 30-line custom intervention. The register now has a `to_states` column, under every solver, and the events happen in the order of the table, as in SimInf.

4. **Still open: age categories as states.** With the age categories as six states, the register can age animals. Making age a stratification instead (`age=['1', '2', '3']`, `use_aging=False`) would be more natural, but the register can name only states, not a level of another dimension. Suggested change: let a register choose and change the level of any dimension (columns named for the dimension, such as `age` and `to_age`). The states no longer need `people=True`, which they used to.

5. **Fixed: no yearly cycle for a step function.** The seasonal decay is now one line, an `ss.timeseries` with `period=`.

6. **Spread between herds.** This was about 25% too slow in an earlier version, for two reasons. SimInf updates `phi` once a day, after the day's scheduled events, so an infected animal that moves sheds into its new herd from the day it arrives; Starsim now does the same. And SimInf's update is a daily map, `phi*(1 - beta) + alpha*I/n`, not the ODE it approximates, so the model uses the continuous rates that give the same `phi` at the end of each day.

7. **Season dates are a day out if copied directly.** SimInf picks the decay for the day that ends a step, and uses a 365-day year; a step in Starsim starts on its date. Written as days `{0: 0.1, 182: 0.125}` with a period of `ss.years(1)`, the season changed a day late and drifted, which made `phi` in node 1 1.5% too high around the change (4.4 standard errors in 200 runs, day 547). The model now gives `{0: 0.1, 181: 0.125, 364: 0.1}` with `period=ss.days(365)`, and the largest difference in 200 runs is 2.0 standard errors. A modeler converting by hand has to work this out.

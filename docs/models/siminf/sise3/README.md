# SimInf: SIS by age in 1,600 cattle herds, with an environmental infectious pressure

A stochastic SIS in 1,600 cattle herds (nodes) over four years, in three age categories (calves, young stock, and adults), where animals are not infected by each other but by an environmental infectious pressure `phi` in their herd: infected animals shed into it, and it decays at a rate that changes with the season. The herds are linked by a schedule of births, deaths, movements, and aging. It is SimInf's built-in `SISe3()` model, run as in the example in SimInf's documentation of `events_SISe3` and `u0_SISe3`, with the data that come with the package.

It shows what SimInf's compartment models are for (its authors used models of this kind, with three age categories and an environmental pressure, for verotoxigenic *E. coli* O157 in Swedish cattle: Widgren et al. 2016, in the bibliography of SimInf's vignette), and goes further than [sir_herds](../sir_herds), which has the same herds and register:

- A continuous state per node (`phi`) next to the whole-number compartments, advanced by a deterministic forward-Euler step once a day (SimInf's "post time step" function), while the animals move in continuous time
- A rate that depends on the day of the year (the decay of `phi`, constant within each of four intervals)
- Three age categories, with aging as scheduled events (`intTrans` with a `shift`) that move animals between compartments, keeping their infection state
- Events that choose animals from one age category only (`select` 4 to 6), on 783,773 events in all

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 27 | 39 | 13 of the Starsim lines read the data and turn SimInf's events, all four kinds, into a movement register, which the original gets from the package. The disease itself has four lines that turn SimInf's daily update of `phi` into rates and seasons. The original's equations are in SimInf's C code, and are not counted |
| One run | first 0.31 s, rerun 0.094 s | first 0.92 s, rerun 0.62 s (Rust) | Gillespie's method on one thread in both, as compartments (whole animals by herd, with `phi` a real number). Neither time counts starting up or reading the data (nor, for Starsim, turning the events into a register). A rerun of the original is `run(model)` again |
| Results | | | **Agree, within a herd, between herds, and in the demography.** With 100 runs (`compare.py` now makes 50, to keep the benchmark short, and allows the same three standard errors), every series is within two standard errors of the difference from SimInf's mean on every day checked (three is the tolerance), and 81% to 97% of the runs are inside SimInf's 5% to 95% range for every series on every day. On day 1,457 the mean of 100 runs has 181 ± 13 herds infected (SimInf: 166, range 24 to 352) and 4,175 ± 309 animals (3,770; 519 to 8,138). The spread between herds runs a little high on every day (175 herds in 200 runs), within the noise, so a small difference there cannot be ruled out |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `e26de815+`), on a 20-core Linux machine.

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

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/events_SISe3.R`: the example, unchanged, from `man/events_SISe3.Rd` of SimInf 11.1.0 (`man/u0_SISe3.Rd` has the same example; `?SISe3` itself has none)
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 200 runs at each of the recorded days (1, 8, ..., 1,457): the totals over all nodes of each compartment (`S_1`, `I_1`, `S_2`, `I_2`, `S_3`, `I_3`) and of the infected (`I`), the mean of `phi` over the nodes (`phi`), the number of nodes with at least one infected animal (`nodes_infected`), the infected and `phi` of nodes 1 to 3 (`node1_I`, `node1_phi`, and so on), and each compartment of node 1 (`node1_S_1`, and so on)
- `reference/timing.json`: the time of the first run (building the model and running it, with R started and the events read) and of a rerun (`run(model)` again)
- `reference/model.json`: the number of nodes, the compartments, the transitions, the update of `phi`, the parameters, and the number of events of each type
- `reference/u0.csv`: the initial state of each node (`node`, `S_1`, `S_2`, `S_3`, `I_1`, `I_2`, `I_3`), with the 10 infected calves in node 1
- `reference/events.csv.gz`: every event, in the order SimInf processes them (`event`, `time`, `node`, `dest`, `n`, `proportion`, `select`, `shift`); 2.9 MB
- `reference/events_summary.csv`: the events by type, with their count, the animals they affect, and the `select`, `shift`, and `proportion` they use
- `reference/select_matrix.csv` and `reference/shift_matrix.csv`: the `select` and `shift` matrices of the model
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (GPL-3)

## The model

- **Compartments:** `S_k` and `I_k` for the age categories `k` = 1, 2, 3, as whole numbers of animals, and `phi`, a real number, in each of 1,600 nodes
- **Transitions:** in each node, `S_k` to `I_k` at rate `upsilon_k*phi*S_k`, and `I_k` to `S_k` at rate `gamma_k*I_k`; there is no transmission between animals except through `phi`
- **The infectious pressure:** after each day's transitions and events, in each node, `phi <- phi*(1 - beta(day)) + alpha*(I_1 + I_2 + I_3)/N + epsilon` (`phi` alone, plus `epsilon`, if the node is empty), with `day = t %% 365`; the new `phi` is used for the next day's transitions. This is a forward-Euler step of `dphi/dt = alpha*I/N - beta(t)*phi + epsilon`
- **Seasonal decay:** `beta(day)` is `beta_t1` on days 0 to 90, `beta_t2` on 91 to 181, `beta_t3` on 182 to 272, and `beta_t4` on 273 to 364 (`end_t1` to `end_t4` are 91, 182, 273, and 365, the same in every node). Here that is 0.1 a day for the first half of each year and 0.125 for the second
- **Parameters:** `upsilon_k = 0.018` and `gamma_k = 0.1` per day in every age category, `alpha = 1`, `epsilon = 0`, and `phi` starts at 0 in every node
- **Initial conditions:** `u0_SISe3`: 196,168 animals, all susceptible (11,982 calves, 31,757 young stock, and 152,429 adults), in herds of 55 to 214; then 10 infected calves are added to node 1 (`u0$I_1[1] <- 10`)
- **Time:** days 1 to 1,460, recorded every 7 days (`tspan = seq(from = 1, to = 4*365, by = 7)`, so the last record is day 1,457), in continuous time, with events once a day
- **Seed:** `set.seed(123)`, on one thread (`set_num_threads(1)`)

### Events

| Type | Count | `select` | `shift` | Effect |
|---|---|---|---|---|
| `exit` | 182,535 | 4, 5, 6 (`S_k` and `I_k` of one age category) | 0 | Animals of that age, chosen at random, are removed |
| `enter` | 182,685 | 1 (`S_1`) | 0 | Susceptible calves are added |
| `intTrans` | 317,081 | 4, 5 | 1, 2 | Animals of age category 1 (or 2), chosen at random, move to age category 2 (or 3) in the same node, keeping their infection state: `S_1` goes to `S_2` and `I_1` to `I_2` |
| `extTrans` | 101,472 | 4, 5, 6 | 0 | Animals of that age, chosen at random, move to node `dest`, keeping their compartment |

Every event has `proportion = 0` and `n` from 1 to 4 (333,003 animals age in the 317,081 internal transfers); there are events on every day from 1 to 1,460. SimInf applies each day's events after the day's transitions and before `phi` is updated: first those within a node (`exit`, `enter`, then `intTrans`), then the movements between nodes (`extTrans`), each in the order of the table. See [sir_herds](../sir_herds/README.md#events) for how SimInf processes events in general.

## Results

Node 1 never loses the infection: its pressure rises to about 4 in the half of the year with slow decay and falls to about 2.4 in the other, and its number of infected animals swings between about 40 and 65 with it. The infection reaches other herds only when an infected animal is moved, and an animal moved into a clean herd starts its pressure from zero, so the spread between herds is slow and very variable: after four years, on average 166 of the 1,600 herds are infected (24 to 352) and 3,770 animals (519 to 8,138), most of them adults.

`run.py` evaluates the original, which sets the seed and makes one run, and then makes 199 more runs of the same model, so it writes the same results each time.

## Lines of model code

27, counting every line of `events_SISe3.R` that is not blank or a comment, apart from the four calls to `plot()` and the call to `summary()`; no line is over 100 characters. The model's equations are in SimInf's C code (`src/models/SISe3.c`, with the seasonal decay in `src/misc/SimInf_forward_euler_linear_decay.c`), and the initial conditions and the events are data that come with the package; none of them is counted.

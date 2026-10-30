# SimInf SIR in 1,600 herds, in Starsim

The translation of [examples/siminf/sir_herds](../../../examples/siminf/sir_herds). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 12 | 22 | 7 of the Starsim lines turn SimInf's table of events into a movement register, and 4 read the data, which the original gets from the package |
| One run | 0.08 s | 3.0 s | Gillespie's method in both, on one thread. Neither time counts starting up or reading the data (nor, for Starsim, turning the events into a register). A rerun of the original is `run(model)` again |
| Results | | | **Agree.** The mean of 200 runs is within three standard errors (at most 2.7) of the original's mean of 200 at every day checked, for the totals, the number of herds infected, and the first herd, including the total susceptible on day 100, where little else varies (199,901 ± 3 against 199,906). The infection dies out early in 4% of runs (7% in the original), so it takes about 200 runs to compare the means: 20 runs can easily have none of these runs, and then differ a lot |

Measured on 13 October 2026 with Starsim 4.0.0 (the `v4` branch) on a 20-core x86-64 Linux machine.

## What was declared and what was not

Everything is declared. The herds are a stratification by place, with an SIR in each that mixes only within the herd, and the 466,692 events are a movement register (`ss.geo.Mobility(data=...)`): a row with a `from` and a `to` moves animals between herds, one with no `from` adds them (births), and one with no `to` removes them (deaths). The same model runs as agents, one for each of the 196,169 animals (`sim.new(solver='abm', n_agents=196_169)`), which takes a minute or two.

## Findings

- **Scheduled events (fixed).** SimInf's `exit`, `enter`, and `extTrans` events, with their `select` matrix, become one table with named columns: `date`, `from`, `to`, `n`, and `states` (here `S` for the animals that enter, and blank, meaning every state, for the rest). The events dated at a time point are in the numbers at that time point, so Starsim's count on day `t` has the transitions of SimInf's day `t` and that day's events, as SimInf's does. The events of a day happen in the order of the table, which here is SimInf's order (exits, then entries, then movements).
- **A count is a count (fixed).** Initial numbers go in `init_n`, so `ss.by(herd=u0.I.values)` is one infected animal in the first herd, with no chance of reading the 1 as a share of the herd.
- **Gillespie with many groups (fixed).** Starsim used to work out every rate again after each event, over all 1,600 herds. It now runs each herd on its own between events, as SimInf does, since herds do not mix within a day.
- **Births as agents (fixed).** `ss.birth()` used to add nobody in an agent-based run, and a sim with no dimensions crashed once its agents grew past the space first set aside for them.

# LASER hub and spoke, in Starsim

The translation of [examples/laser/hub_spoke_seir](../../../examples/laser/hub_spoke_seir). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 50 | 17 | |
| One agent-based run | first 2.4 s, rerun 0.9 s | first 1.1 s, rerun 0.72 s (Rust) | The original has 1,750,000 agents, on all cores; the Starsim run has 175,000, each standing for ten people, on one core. LASER has no way to run a built model again, so its rerun builds the model too |
| Results | | | **Agree.** As agents, the means of 6 Starsim runs and 20 LASER runs: 1,529,575 recovered at the end, against 1,532,298, and within 0.5% in each place shown; peaks within 5% in size and 9 days in time. As an ODE: 1,532,507 recovered, peaks within 5% in size and 8 days in time. `compare.py` allows 2%, 15%, and 10 days. |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: the places, the model, the durations as distributions, and the mobility, which moves the force of infection between places (`kind='force'`), as LASER does. The same text runs as agents and as an ODE (with the durations as Erlang stages), and the two agree with each other.

## Findings

- **The two frameworks coupled places differently (fixed).** LASER moves the force of infection itself between places, unweighted by their size: `f[j] += Σ f[i]·network[i,j] − f[j]·Σ network[j,i]`. Starsim's commuting moves people, who mix where they are, and with it 80% were infected, against 88%. `ss.geo.Mobility(..., kind='force')` is LASER's form, and with it the results agree. The gravity matrix is the same in both (every row of LASER's is capped at 3/32, which is `away=3/32` here).
- **One run at a tenth of the size says little about timing.** The 100 infectious people at the start are 10 agents here, so the day of the peak moved between 156 and 172 over six runs, where LASER's runs, with 100 agents, move by a few days. The mean of six runs is within 2 days of LASER's in total, so `compare.py` compares means. Running at LASER's size would avoid this, at about ten times the time.
- **LASER is faster per agent.** Starsim runs a tenth of the agents in a similar or longer time (see the table above), so LASER is many times faster per agent, and it uses all the cores. As a compartmental model the size doesn't matter: the same text runs for all 1,750,000 people with `solver='ode'` or `solver='binomial'`.
- **Distances.** The original measures great-circle distances between map coordinates; this version uses the same layout in kilometers on a plane, which is the same to within a fraction of a percent.

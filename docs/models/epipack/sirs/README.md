---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# epipack: SIRS as ODEs, by Gillespie's method, and on a network

The SIRS of epipack's README, its first example: infection at 2.5 a day, recovery at 1 a day, and waning immunity at 1/14 a day, in 1,000 people with 10 infectious at the start, integrated as ODEs and simulated by Gillespie's method for 40 days. The README then runs the same model on a random network of 10,000 people with 50 contacts each, written with the processes of a different class. See the [review](../../../approaches/epipack.md).

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`: the ODEs, the mean of 1,000 Gillespie runs, and the mean of 100 runs on the network, each on a network of its own.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 37 | 8 | The original is two scripts, 12 lines for the well-mixed model and 25 for the network, without the plotting. In Starsim they are one disease and three sims |
| One run | first 0.06 s, rerun 0.057 s | first 0.013 s, rerun 0.00022 s (Rust) | Each is the ODE integrated to day 40, with results; the original's at the README's 1,000 times. A Gillespie run takes 0.024 s in the original and 0.00072 s in Starsim. On the network a run is slower in Starsim: 5.2 s again, against 3.3 s (3.9 s for the first run, which makes the network), with 1,600 steps of 0.025 days; see the findings |
| Results, ODE | 411.87 in `S` on day 40 | 411.87 | **Agree** to 6.5e-6 of the population on every day, with a daily RK4 step against epipack's adaptive solver |
| Results, Gillespie (mean of 1,000 runs) | 526 in `S` on day 40, with 5% to 95% of runs from 344 to 920 | | **Agree** to 5.6e-3 of the population on every day, within the error of a mean of 1,000 runs |
| Results, on the network (mean of 100 runs) | A peak of 2,228 in `I` on day 3, and 4,399 in `S` on day 40 | | **Agree** to 2.1e-2 of the population on every day, with steps of 0.025 days against epipack's continuous time. The largest difference is in the first days, when the epidemic doubles in about 10 hours |

Measured on 3 November 2026 with Starsim 4.0.0rc2 (the `v4` branch, commit `d0107e93`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: three transitions, and the route of each sim (`ss.MixingPool(n_contacts=50)` for the two well-mixed runs, and `ssl.StaticNet(n_contacts=50)`, a random graph with a mean of 50 contacts, for the network). The infection rate is per contact, so the same disease runs on either route; `solver=` chooses ODEs, Gillespie, or agents.

## Findings

- **One disease, not two sets of processes.** epipack writes the well-mixed model as an `EpiModel` with a transmission at 2.5 a day, and the network model as a `StochasticEpiModel`, with a link transmission at `R0*rho/k0` and node transitions, so the model is written twice. Here the disease is written once with a rate of 0.05 per contact, and the routes supply the contacts: 50 a day in the mixing pool, or the edges of the network. With `solver='ode'`, Starsim runs the network sim as homogeneous mixing at its mean number of contacts, which is the README's derivation of the rate, and says that it has done so.
- **Fixed steps against continuous time.** epipack simulates the network in continuous time, event by event, and Starsim's agents take fixed steps, so someone infected during a step can't infect anyone until the next one. With infection at 2.5 a day and recovery at 1 a day, the early epidemic is fast, and the step matters: with steps of 0.1 days the mean differs from the original's by about 6% of the population in the first days, with 0.05 days by 3.5%, and with 0.025 days by 2%, and `sim.check_dt()` shows it. Agreement costs steps: 1,600 of them, which is why the network run is slower than epipack's. An exact, event-by-event solver for agents on a network, as epipack has, would need neither.
- **A rerun of agents is a rebuild.** `sim.restart()` builds an agent-based sim again, as `sim.new()` does, so Starsim's rerun on the network includes making the network of 250,000 edges, which epipack's rerun reuses.
- **The README's network example doesn't run as written.** A line of the README ends in a backslash followed by spaces, which is a syntax error in Python; `original/sirs_network.py` removes the spaces and nothing else.
- **The starting infections.** `init_prev=0.01` is 10 people in 1,000 and 100 in 10,000, as in the README; as agents it starts exactly 100. A number of people, `init_n=dict(I=10)`, is not a parameter, so a sim made from another with `sim.new()` can't change it, and the share is used instead.
- **Importing the original.** `ss.import_from()` reads `original/sirs.py` (through `starsim/converters/epipack.py`, run in epipack's environment) as the same three transitions, and with `solver='ode'` gives the same 411.87 in `S` on day 40; without it, it runs by Gillespie's method, since the script's last call is `simulate()`. The converter looks for a variable called `model`, and the README's is `SIRS`, so it needs a one-line function that returns it. It reads `original/sirs_network.py` as well mixed at the mean degree, and lists the network as not translated.

## What it exercises

- Transmission, recovery, and waning immunity, as rates
- The same model run as ODEs, by Gillespie's method, and on a contact network
- A rate per contact, which the route turns into a rate per day
- A static random network of 10,000 people with a mean of 50 contacts each

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/sirs.py`: the "Basic Definition (EpiModel)" example of epipack's README, unchanged, at version 0.1.5 (commit `52fb26b`)
- `original/sirs_network.py`: the README's "On a Network" example, with the trailing spaces after one backslash removed so that it runs
- `run.py`: runs them and writes `reference/`, with `export.py` in the framework's environment
- `reference/results.csv`: `S`, `I`, and `R` on each day: the ODE, and the mean and 5% to 95% range of the Gillespie runs and of the runs on the network
- `reference/timing.json`: the time of a first run and of a rerun of the ODE; `run.log` gives the others
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (MIT)

## The model

- **Compartments:** `S`, `I`, `R`
- **Transitions:** `S` to `I` at `eta*S*I/N`, `I` to `R` at `rho`, and `R` to `S` at `omega`, per person per day
- **Parameters:** `eta = 2.5` a day, `rho = 1` a day, `omega = 1/14` a day; on the network, 0.05 per contact per day (`R0*rho/k0`, with `R0 = 2.5` and `k0 = 50`)
- **Initial conditions:** 10 of 1,000 infectious; on the network, 100 of 10,000, chosen at random
- **Network:** `networkx.fast_gnp_random_graph(N, k0/(N-1))`, a random graph with a mean degree of 50, made anew for each run
- **Time:** days 0 to 40

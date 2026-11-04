---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# epipack: SIARX with contact tracing, on a network, well mixed, and deterministic

The example of contact tracing in epipack's tutorial on networks: an SIARX model in 10,000 people on a random network with 50 contacts each, where infected people become symptomatic (`I`) or not (`A`), symptomatic people are quarantined (`X`), and each quarantine traces the person's contacts, quarantining each who is symptomatic with a chance of 25%. The tutorial runs it on the network, then well mixed, then as a deterministic model in which tracing is approximated by a flow. See the [review](../../../approaches/epipack.md).

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`: the deterministic model, and the mean of 100 runs on the network and well mixed, each on a network of its own.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 61 | 16 | The original's lines include the 2 added to run the tutorial's code blocks as one script. In Starsim the deterministic model reuses the transitions of the stochastic one, with one transition added |
| One run | first 0.95 s, rerun 0.52 s | first 1.3 s, rerun 1.1 s (Rust) | Each is one run on the network with tracing, for 40 days, with results. Starsim's rerun makes the network of 250,000 edges again, and epipack's reuses it. Well mixed, a run takes 0.89 s in the original and 4 s in Starsim; the deterministic model, to day 100, 0.16 s and 0.00032 s |
| Results, deterministic | 2,941.6 in `S` and 2,921.6 in `X` on day 40 | 2,941.6 and 2,921.6 | **Agree** to 2e-6 of the population on every day to day 100 |
| Results, on the network (mean of 100 runs) | 3,423 in `S` and 2,792 in `X` on day 40 | | **Agree** to 1.2e-2 of the population on every day, with steps of 0.1 days against epipack's continuous time. The largest difference is in `S` as it falls fastest, about three times the standard error of the difference of the two means |
| Results, well mixed (mean of 100 runs) | 2,955 in `S` and 2,919 in `X` on day 40 | | **Agree** to 1.2e-2 of the population on every day, as on the network |

Measured on 3 November 2026 with Starsim 4.0.0rc2 (the `v4` branch, commit `d0107e93`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The infection is one transition that splits 70% to `I` and 30% to `A`, at a rate per contact from `I + 0.5*A`; recovery and quarantine are rates. Tracing is a delivery: `ss.Delivery(move=I >> X, who=siarx.quarantine, trace='contacts', coverage=0.25)` moves a quarter of the symptomatic contacts of each person quarantined to `X`, in the same step. The network is `ssl.StaticNet(n_contacts=50)`, a random graph like the original's, and the well-mixed run is the same sim on `ss.RandomNet(n_contacts=50)`, new contacts every step, as epipack draws `k0` new contacts each time someone is quarantined. The deterministic model adds the tutorial's flow, `I >> X` at `0.25*(1/5)*50*I/N`, written as the whole flow.

## Findings

- **Tracing has a declaration, and one meaning.** epipack's conditional link transmission, `('I', '->', 'X'): [('X', 'I', p, 'X', 'X')]`, is a delivery triggered by an event, to contacts, with a coverage. In neither framework do the people traced trigger tracing in turn: in epipack the conditional event is not the event `I -> X`, and in Starsim a delivery's move is not the transition `quarantine`. One difference is of order `dt`: someone with two contacts quarantined in the same step is offered it once in Starsim and twice in epipack.
- **No compartmental form of tracing.** With `solver='ode'`, a sim with `trace=` raises a `CapabilityError` (on a mixing pool too), so the deterministic model is written with the extra flow, as the tutorial derives it by hand: `I + I -> I + X` at `kappa*p*k0`. For a route that is random mixing, Starsim could offer that approximation itself, as it approximates a network by its mean number of contacts, and say so.
- **A flow out of the state that drives it can't be written per person.** `I >> X @ c*I` reads, by the rule that a bare state is contact, as `c` times the share of contacts in `I`; but Starsim reads it as the whole flow, by the rule that a rate with its source as a factor is the flow, so it becomes `c` per person in `I`, without the share, and nothing says so except a line of `sim.describe()`. The model gave 2,520 in `S` on day 40 instead of 2,942. Written as the whole flow, `c*I*I/N`, it is right. The importer has the same problem: `ss.import_from()` reads the tutorial's deterministic model (`2.5*I*I` in epipack's JSON) as a rate of 2.5 per person, and gives 9,787 in `S` instead of 2,942.
- **Slower as agents.** epipack simulates one event at a time, so its cost grows with the number of events; Starsim's agents take 400 steps, each a pass over the 250,000 edges of the network for transmission, and a rerun makes the network again. The infection is one transition that splits, rather than the original's four transmissions or two transitions from the same sources, since each transmission is a pass over the edges of its own: with two, a run took about 30% longer.
- **Well mixed needs a network to trace on.** A mixing pool has no contacts to trace, so the well-mixed run is a random network redrawn every step, which costs more than the static one.
- **The tutorial's code is in pieces.** Its code blocks leave out their imports, and the run well mixed is described but not shown; `original/siarx.py` adds the imports and the two lines that set the initial conditions again and run it, each marked.

## What it exercises

- Contact tracing: an event of one person (quarantine) that acts on their contacts, with a probability
- Infection that splits on entry into two states, one half as infectious
- Competing exits from `I`: recovery and quarantine
- The same model on a static random network, well mixed with contacts redrawn, and deterministic, with tracing approximated by a mass-action flow

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/siarx.py`: the "Setup" part of the section "Conditional Transmission Processes" and the section "Well-Mixed Systems" of `docs/tutorial/networks.rst` in epipack's repository, at version 0.1.5 (commit `52fb26b`), as one script, with the lines added to run it marked `# Added`
- `run.py`: runs it and writes `reference/`, with `export.py` in the framework's environment
- `reference/results.csv`: each state on each day: the deterministic model to day 100, and the mean and 5% to 95% range of the runs on the network and well mixed, to day 40
- `reference/timing.json`: the time of a first run and of a rerun on the network; `run.log` gives the others
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (MIT)

## The model

- **Compartments:** `S`, `I` (infectious, with symptoms), `A` (infectious, without), `R`, `X` (quarantined)
- **Transitions:** `S` to `I` or `A` by contact with `I` and `A` (70% to `I`, and `A` half as infectious); `I` to `R` and `A` to `R` at 1/5 a day; `I` to `X` at 1/5 a day
- **Tracing:** each time someone moves from `I` to `X`, each of their contacts in `I` moves to `X` with probability 0.25
- **Parameters:** a transmission rate of `Reff*(1/5 + 1/5)/k0 = 0.016` per contact per day, with `Reff = 2` and `k0 = 50`
- **Network:** `networkx.fast_gnp_random_graph(N, k0/(N-1))`, a random graph of 10,000 with a mean degree of 50, made anew for each run
- **Initial conditions:** 100 of 10,000 in `I`, chosen at random
- **Time:** days 0 to 40, and to day 100 for the deterministic model

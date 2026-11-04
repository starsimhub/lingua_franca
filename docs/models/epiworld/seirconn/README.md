# epiworld: SEIR in a fully connected population

COVID-19 as an SEIR among 10,000 agents for 50 days, in which everyone can meet everyone: each person meets two others a day at random, an infectious contact infects with a chance of 0.5, and the infection starts from one person exposed. This is the model of epiworldR's vignette "Run Multiple", which runs it 50 times with `run_multiple()`; it is the template `ModelSEIRCONN`, where `CONN` means fully connected.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`, the distribution of 1,000 runs of the original.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 12 | 8 | |
| One run | first 4.4 ms, rerun 2.9 ms | first 10 ms, rerun 0.21 ms (Rust) | One run of 50 days. The original's first run includes building the model; Starsim's runs the agents as counts (see below), which is why it is faster |
| Results | | | **Agree** (within three standard errors; mean of 1,000 runs each): 398 ± 17 recovered on day 50, against 394, and the infection dies out by day 50 in 22.6% of runs, against 20.8%. Every state agrees on days 10 to 50, and the 95% quantile of the recovered on day 50 is 1,601 against 1,403, 2.1 standard errors apart |

Measured on 3 November 2026 with Starsim 4.0.0rc2 (the `v4` branch, commit `0d5e22f4`), on a 20-core Linux machine. Starsim's rerun took 0.44 ms with the Numba kernels.

## What was declared and what was not

Everything is declared: three transitions, with the chances a day of the original as `ss.prob`, and one person exposed at the start. The sim runs as a chain binomial in whole days (`solver='binomial', substeps=1`).

## Findings

- **The agents are a chain binomial.** In `ModelSEIRCONN` every agent is alike and everyone meets everyone, so the number in each state is all that matters: on each day, each susceptible person is infected with the same chance, which depends only on the number infectious, and each exposed or infectious person moves on with the same chance. That is a chain binomial, and run as one the translation agrees with the original's 1,000 runs, at a fraction of the cost. Starsim's guide suggests this solver for "a model written in discrete time", and it is the right one here; `solver='auto'` would choose the ODE, which has no extinctions.
- **Run as agents, the model is not the same.** With `n_agents=10_000` and `solver='abm'` the infection dies out by day 50 in 46% of runs, against 21%, and 306 ± 39 are recovered on day 50 (200 runs). Starsim's agents take a step's transitions in turn, as an approximation of continuous time: the transitions that are not transmission come first, so someone who becomes infectious during a step has already had half a step's chance of recovering (1 − (2/3)^½ = 0.18 here) before that step's transmission, and so infects others for less time. epiworld works out every day's chances from the states at the start of the day, as the chain binomial does. With chances as large as 1/3 a day this is a large difference. No setting of the sim makes agents work out a step's chances at its start, so a model defined in discrete time that needs agents (one on a network, say) could not be matched. The guide's "Solvers and backends" page says that agents, like the chain binomial with `substeps=1`, take each step whole, "everyone's chance of moving is worked out at the start of the step", which is not what they do.
- **The original's chance of infection is slightly low when people meet several infectious people.** epiworld draws each susceptible person's contacts with infectious people, and then picks at most one infection from them by a "roulette" that takes only the chances of no infection and of exactly one. With two contacts that each infect with a chance of 0.5, the chance of infection is 2/3, not 3/4. Here prevalence stays low, so this is not visible; in [covid_flu](../covid_flu) it is.

## What it exercises

- A fully connected population, with contacts per day and a chance of infection per contact
- Daily chances of moving on (incubation and recovery), so geometric times in each state
- A single introduction, so many runs, some of which die out
- Many runs as a single call (`run_multiple()` with a saver)

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/run-multiple.R`: the vignette's code, word for word, as extracted in `doc/run-multiple.R` of the installed package
- `reference.R`: runs the original, then runs its model 1,000 times and writes the runs and timing for `run.py`
- `run.py`: runs `reference.R` and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 1,000 runs on each day of `Susceptible`, `Exposed`, `Infected`, and `Recovered`, and `extinct`, the share of runs with nobody exposed or infectious
- `reference/timing.json`: the time of a first run and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (MIT)

## The model

- **Population:** 10,000 agents, closed, all alike
- **States:** `Susceptible`, `Exposed`, `Infected`, `Recovered`; only `Infected` is infectious
- **Infection:** each day, each susceptible agent has a number of contacts with infectious agents drawn from a binomial distribution with the number infectious and a chance of `contact_rate / n` = 2/10,000 each; each contact infects with a chance of `transmission_rate` = 0.5, and the roulette above picks at most one
- **Incubation:** an exposed agent becomes infectious with a chance of `1 / incubation_days` = 1/7 a day
- **Recovery:** an infectious agent recovers with a chance of `recovery_rate` = 1/3 a day
- **Initial conditions:** `prevalence = 0.0001` of 10,000, so one agent, starts exposed
- **Time:** 50 days; day 0 is the initial state
- **Runs:** 50 in the vignette, and 1,000 for the reference results

Each day every agent's update reads the states at the start of the day, and the changes are made together at its end. The list of infectious agents, and the distribution of their contacts, are updated at the end of each day, so someone who becomes infectious on a day can first infect others the next day, and someone who recovers on a day could still infect others that day.

## Results

The outbreak grows slowly: the mean number ever infected is about 1,000 by day 50, but the runs vary widely. About a fifth die out (20.8% by day 50), and in the rest the number recovered on day 50 is anywhere from a handful to over 1,400 (the 95% quantile). The mean over 1,000 runs of the recovered on day 50 is 393.5, of the exposed 466.9, and of the infectious 151.4.

`reference.R` runs the vignette as it is, then calls `run_multiple()` on its model again, as the vignette does, with 1,000 simulations on one thread and a fixed seed, so `run.py` writes the same results each time.

## Timing

One run of 50 days takes about 3 ms. `run_multiple()` of 1,000 takes about 6 s, about twice as long as 1,000 runs alone; the saver writes each run's history to disk. The first run builds the model again, with the vignette's own statement, and runs it once.

## Lines of model code

12, counting the lines of `run-multiple.R` that are not blank or comments: the model (9 lines), the saver, `run_multiple()`, and `run_multiple_get_results()`. Left out are `library(epiworldR)`, the two calls of `head()`, and the five lines that select and plot the results. No line is over 100 characters.

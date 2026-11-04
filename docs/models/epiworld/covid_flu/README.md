---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# epiworld: COVID-19 and flu, with a vaccine and two measures

COVID-19 and flu spreading at the same time among 50,000 agents for 50 days, in a fully connected population in which each person meets four others a day. Half of the population is vaccinated at the start, with a vaccine that lowers the chance of infection, the chance of passing it on, and the time infectious, and two measures cut the number of contacts, to two a day from day 10 and to 1.5 from day 20. This is the model of epiworldR's vignette "Advanced Modeling - Multiple Diseases, Tools, and Events", which builds it a step at a time on the template `ModelSIRCONN`: it shows what epiworld is known for, several viruses and the tools that protect against them, carried by the same agents.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`, the distribution of 1,000 runs of the original.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 29 | 20 | |
| One run | first 0.08 s, rerun 0.076 s | first 0.017 s, rerun 0.0012 s (Rust) | One run of 50 days. The original's first run includes building the model; Starsim's runs the agents as counts, as for [seirconn](../seirconn) |
| Results | | | **Agree while few are infected, and within 5% after** (mean of 1,000 runs each): on days 1 to 5 every mean agrees within three standard errors (725 infected on day 5, against 721). Later the epidemic is larger, as expected from the original's chance of infection (see below): it peaks on day 11 in both, at 9,296 against 8,899 (+4.5%), the flu peaks on day 9 at 162 against 155, and 26,855 have recovered on day 50, against 26,509 (+1.3%) |

Measured on 3 November 2026 with Starsim 4.0.0rc2 (the `v4` branch, commit `d0107e93`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The two viruses are two strains of one disease (`ss.Strains`), with their own chances of infection and recovery as multipliers. The vaccine is an `ss.Vaccine` with efficacy against acquisition and transmission, given to half of everyone at the start, and its recovery enhancer is a second transition from `I` to `R`, with a chance of 0.5 a day, for those who hold it (`where=vaccine.held`). The two measures are each an `ss.modify` that sets the contact rate, a parameter in the rate of infection. The sim runs as a chain binomial in whole days (`solver='binomial', substeps=1`), as the SEIR does.

## Findings

- **Two viruses are two strains.** In epiworld a virus is something an agent carries, and the states belong to the model: an agent carries one virus at a time, and recovery from either puts them in `Recovered`, protected from both. That is what `ss.Strains` does with no `immunity=`: one course through the states, one strain at a time, and a new infection takes its source's strain. Two diseases, each with its own states, would let people have both. Each strain's results are there too (`res.I.select(strain='flu')`).
- **A strain's values are multipliers of rates.** The flu's chance of infection per contact, 0.35 against 0.5, is a plain ratio, since the chance per contact is a factor of the rate. Its chance of recovery, 0.5 a day against 0.25, is not: as a multiplier of the rate it is log(0.5)/log(0.75) = 2.41, which has to be worked out. A value for each strain given as a rate or a chance of its own (`recovery=[ss.prob(1/4), ss.prob(1/2)]`) would say it directly.
- **A recovery enhancer is a second chance of recovery.** epiworld combines the virus's chance of recovery with the tool's as 1 − (1 − 1/4)(1 − 0.5) for COVID-19 and 1 − (1 − 1/2)(1 − 0.5) for flu. A vaccine's efficacy on a transition scales its rate, and here the factor would be 3.41 for COVID-19 and 2 for flu, for the same tool. Since rates out of a state compete, a second transition out of `I` with a chance of 0.5 a day, for those who hold the vaccine, gives the original's rule exactly, for both strains. It is short and exact, but this effect of the vaccine is then written in the disease, not in the vaccine, with the other two.
- **The original's measures act a day late, and are not undone.** `globalevent_set_params("Contact rate", 2, day = 10)` sets the parameter at the end of day 10, after that day's update of who is infectious has fixed the next day's contacts with the old value, so the contact rate is 4 to day 11 and 2 from day 12. In Starsim the step from day 11 to day 12 is the one at day 11, so the modifiers start at 11 and 21. More importantly, the parameter is not set back when the model is run again: each `run()` and each simulation of `run_multiple()` starts with the contact rate the last one left, 1.5. The vignette's own run is right, since it is the first with the measures, but the ones after it are not: in `run_multiple()` of six runs of the model with the two measures alone, the first has 106 infections on day 1 and the others 26 to 45, since they start with 1.5 contacts a day. The reference runs set the rate back to 4 before each run. An `ss.modify` changes nothing in place, and parameters are back to their base values after a run, so every run of the Starsim version starts from the same model.
- **The original's chance of infection is lower when many are infectious.** As in [seirconn](../seirconn), epiworld picks at most one infection from a person's contacts by a "roulette" that leaves out the chance of two or more. With 20% infectious and four contacts a day that infect with a chance of 0.5, it gives a chance of infection of 0.312 a day, as measured in the original, where independent contacts give 1 − exp(−4 × 0.2 × 0.5) = 0.330. Starsim's chance is the latter, so the agreement is close while few are infected, and the epidemic is about 5% larger at its peak. The translation does not try to match the roulette.
- **The flu recovers faster than the vignette says.** The vignette says that both viruses have a recovery rate of 1/4, but its `virus()` call does not give one, and `virus()` has `recovery_rate = 0.5` by default. The translation follows the code.
- **Bug: plotting a sim with a delivery and a modifier that stops.** `sim.plot()` raises a `ValueError` ("The truth value of an array ... is ambiguous") for any sim with a delivery at a fixed time and an `ss.modify` with `start=` and `stop=`: `ss.results.intervention_marks()` checks `mark not in out`, which compares the delivery's time, a NumPy number, with the modifier's (start, stop) pair. `model.py` plots with `show_interventions=False` until this is fixed.
- **Run as agents, the epidemic is smaller.** With `n_agents=50_000` and `solver='abm'`, 20 runs peak at 5,624 infected on day 14 and 21,697 have recovered on day 50, against 8,899 and 26,509: someone infected in a step has half a step's chance of recovery before they first infect anyone, which epiworld does not have (see [seirconn](../seirconn)).

## What it exercises

- Two pathogens in one population, which compete for the same susceptible people and protect against each other
- A protective tool, given to half of everyone (infected or not) at the start, with three effects at once: on susceptibility, on infectiousness, and on recovery, the last combined with each virus's own chance
- Global events that change a model parameter on given days
- A fully connected population, with contacts per day and a chance of infection per contact for each virus

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/advanced-modeling.R`: the vignette's code, word for word, as extracted in `doc/advanced-modeling.R` of the installed package
- `reference.R`: runs the original, then runs its final model 1,000 times and writes the runs and timing for `run.py`
- `run.py`: runs `reference.R` and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 1,000 runs on each day of `Susceptible`, `Infected`, `Recovered`, `Infected COVID-19`, and `Infected Flu`; and the vignette's own run (seed 1912) as `vignette Susceptible`, `vignette Infected`, and `vignette Recovered`
- `reference/timing.json`: the time of a first run and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (MIT)

## The model

- **Population:** 50,000 agents, closed
- **States:** `Susceptible`, `Infected`, `Recovered`, shared by the two viruses
- **Viruses:** COVID-19, with a chance of infection per contact of `transmission_rate` = 0.5 and of recovery of `recovery_rate` = 1/4 a day; and flu, with 0.35 and 0.5 (the default). Each starts in `prevalence = 0.001` of the agents, 50 each, different agents
- **Infection:** each day, each susceptible agent has a number of contacts with infectious agents drawn from a binomial distribution with the number infectious and a chance of `Contact rate / n` each; each contact infects with the chance of its virus, times 1 − 0.9 if the susceptible agent is vaccinated and times 1 − 0.5 if the infectious one is; the roulette picks at most one infection
- **Vaccine:** given at the start to 25,000 agents chosen at random from everyone (`distribute_tool_randomly(0.5, TRUE)`), with `susceptibility_reduction = 0.9`, `transmission_reduction = 0.5`, and `recovery_enhancer = 0.5`. Its `death_reduction = 0.9` has no effect, since nobody dies in this model
- **Recovery:** with a chance of 1 − (1 − p)(1 − 0.5) a day for a vaccinated agent and p for the others, where p is the virus's chance
- **Measures:** the contact rate is 4, set to 2 on day 10 and to 1.5 on day 20, by global events, which act from the day after next (above)
- **Time:** 50 days; day 0 is the initial state. The vignette runs it once, with seed 1912

As in [seirconn](../seirconn), each day every agent's update reads the states at the start of the day, and the changes are made together at its end.

## Results

COVID-19 takes over the epidemic: the mean number infected peaks on day 11 at 8,899 (7,747 to 9,793 in 5% to 95% of runs), almost all of them with COVID-19, and the epidemic is over by day 50, with 26,509 recovered (25,786 to 27,107) and 23,487 never infected. The flu peaks at 155 on day 9, and is gone by about day 25: its own reproduction number is lower, and COVID-19 takes the susceptible people it needs. The vignette's own run is within this range (a peak of 9,647 on day 11, and 26,851 recovered).

`reference.R` runs the vignette as it is, and then runs its model 1,000 more times with seeds 2 to 1,001, setting the contact rate back to 4 before each run (above), so `run.py` writes the same results each time.

## Timing

One run of 50 days takes about 88 ms, about 28 million agent-days a second, close to the 30 million that epiworld's documentation gives. The first run builds the model again, with the vignette's own statements, and runs it once.

## Lines of model code

29, counting the lines of `advanced-modeling.R` that are not blank or comments and are needed to build and run the final model: the model (8 lines), the flu and adding it (2), the vaccine, its distribution, and adding it (14), the two events and adding them (4), and the last `run()`. Left out are `library(epiworldR)`, `verbose_off()`, the three earlier runs of the model as it is built, the plots, the summary, and the reproductive numbers. No line is over 100 characters.

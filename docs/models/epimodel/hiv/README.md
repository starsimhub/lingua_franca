---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# EpiModel: HIV with a care cascade and PrEP

HIV among 1,500 people over 20 years in weekly steps, transmitted over two networks of partnerships (main and casual) that form and dissolve, with acute, chronic, and AIDS stages, a care cascade from testing to viral suppression, PrEP for people at risk, and arrivals and departures. Four scenarios compare no intervention, a cascade that reaches the UNAIDS 95-95-95 targets, PrEP at 50% coverage among those indicated, and both. This is the HIV example of the EpiModel Gallery, the set of worked examples maintained by EpiModel's authors, and the one that brings the most of EpiModel together.

This is EpiModel's wave 3 example. `model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 405 | 58 | About 10 lines are the one remaining workaround (who is indicated for PrEP) |
| One run | first 46 s, rerun 45 s | first 2.4 s, rerun 2 s (Numba) | With no intervention. The rerun of the original is the mean of 10 runs, and its first run adds estimating the two networks (netest), which is done once |
| Results | | | **Agree within the noise of the runs in three scenarios; with no intervention, the epidemic is larger, as before** (tolerance: 2.5 percentage points for prevalence, 2 for the care cascade and PrEP; below) |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

| Scenario | Cumulative infections | Final prevalence | Incidence per 100 person-years (second half) | Diagnosed, on ART, suppressed (second half) | PrEP among the HIV-negative |
|---|---|---|---|---|---|
| No intervention | 476 (original 459) | 16.0% (14.4%) | 2.01 (1.80) | | |
| Cascade | 72 (74) | 5.1% (5.1%) | 0.14 (0.14) | 97.7%, 92.0%, 89.9% (97.6%, 91.9%, 89.7%) | |
| PrEP | 225 (244) | 6.7% (7.3%) | 0.74 (0.80) | | 12.0% (12.0%) |
| Both | 39 (45) | 3.9% (3.8%) | 0.067 (0.074) | 98.5%, 93.0%, 91.0% (98.0%, 92.1%, 89.9%) | 12.2% (12.0%) |

Prevalence at 5 and 10 years agrees within 0.9 percentage points in every scenario. With no intervention, 236 ± 8 people have HIV at the end against 210 (the original's 10 runs range from 154 to 247, so its mean has a standard error of about 9); with PrEP alone, 104 ± 5 against 111. The likely cause is the casual network: Starsim's has the targets (a mean degree of 0.30, and 10.2% with two or more casual partners), while the original's is below them (0.28 and 8.9% with no intervention, 0.30 and 9.6% with PrEP). The main network is close in both (a mean degree of 0.49 to 0.50 against 0.49, and 4.1% to 4.3% with two main partners against 4.0% to 4.2%).

## What was declared and what was not

Declared: the four disease states, with the infectiousness of acute and AIDS on the states; transmission over both networks, per act, with three acts a week in a main partnership and one in a casual one; progression, AIDS deaths, other departures, and arrivals; the care cascade as a stratification of the infected states (undiagnosed, diagnosed, on ART, suppressed, and off ART after being on it) with seven transfers, and its effects on infectiousness, progression, and AIDS mortality as `adjust=`; both networks as `ss.DegreeNet` from the same targets as the original; PrEP as a vaccine with 95% efficacy that people stop taking, delivered to half of those indicated at the start and then to 1.5% of them a week; the scenarios, as `pars=dict(cascade=1)` and the PrEP deliveries.

Not declared (one workaround, marked in the code): who is indicated for PrEP, a function that reads both networks.

The original's six modules (305 lines of R) become the disease, the stratification, and two deliveries. Its two attributes for each person, a stage and a care state, are one state and one dimension here, and its history of ART (`art.time`, which decides whether someone starts or restarts ART) is the level `off`. EpiModel's modules can do anything R can, which is why it can state this model at all; here it depends on what Starsim declares.

## Findings

1. **Fixed: scenarios by a parameter.** A parameter in a transfer's rate is now a parameter of the sim, so the model is built once and the cascade is switched with `pars=dict(cascade=1)`.
2. **Fixed: partnerships ended by departures.** `ss.DegreeNet` allows for them, as EpiModel's `d.rate` does, so the mean degree stays on target with `dur=200` and `dur=26` and no subclass.
3. **Still open: no conditions on the network** (a function). PrEP is indicated for HIV-negative people with two or more partners across both networks, or with a partner who has HIV. This is a 10-line function reading the partnerships. A condition such as `hiv.S & ((main.degree + casual.degree >= 2) | ss.partner_of(hiv.infected))`, usable in `where=`, would declare it.
4. **Fixed: networks in a dict.** `networks=dict(main=main, casual=casual)` works. The two PrEP deliveries still need `name=`, since they are in a list.
5. **Fixed: acts in a partnership.** `acts=` on `ss.DegreeNet` makes `beta` a probability per act, so the chance of transmission over a partnership is worked out as in EpiModel. In this sim, with no unit, a day is a step, so `ss.freqperday(3)` means three acts a week, which reads oddly.
6. **Still open: stopping a product at a rate is written as waning.** PrEP is stopped with a probability of 0.015 a week; that is `ss.Vaccine(waning=-1/np.log(1 - 0.015))`, a mean duration of protection. It works, but a product that people take and stop is not a vaccine, and the duration has to be worked out from the probability.
7. **The networks' targets are better matched than the original's, which affects the results.** EpiModel's casual network has a mean degree of 0.28 to 0.30 and 8.9% to 9.6% with two or more partners, against targets of 0.3 and 10%; `ss.DegreeNet` has 0.30 and 10.1% to 10.2%. This is probably why the epidemic with no intervention is about 10% larger here (about two standard errors). It is not a fault in either, but agreement on the targets does not imply agreement on the network. PrEP alone now comes out a little below the original (6.7% against 7.3%), which is within the noise of the runs.
8. **Smaller differences.** EpiModel uses each rate as a probability per step, written here as `ss.prob` (aliased `week`). It starts its seed infections in stages drawn at random in proportion to 12:520:104; here the expected numbers (2, 98, and 20) are given. Its modules run in turn, each from a snapshot of the attributes at its start, so for example someone can be suppressed and stop ART in one step; here the transfers out of a level compete. None of these is visible in the results.
9. **Fixed: a transition named `stop`.** A transition whose name was also a module parameter used to break the sim; it now runs.

## What it exercises

Beyond the wave 1 example ([sis-network](../sis-network)):

- Two network layers on the same people, each estimated as its own model from target statistics (`edges`, `concurrent`, and on the main layer `degrange`), with transmission on both and a different number of acts per partnership on each
- Partnership durations corrected for departures (`dissolution_coefs(..., d.rate = )`), and networks simulated again at every step as people arrive and depart (`resimulate.network = TRUE`, `tergmLite = TRUE`)
- Six user-written modules replacing EpiModel's built-in ones (`infection.FUN`, `progress.FUN`, `cascade.FUN`, `prep.FUN`, `departures.FUN`, `arrivals.FUN`), with custom attributes kept in step with the people
- A disease stage and a care state for each person (two attributes), with infectiousness, progression, and AIDS mortality depending on both
- A history: someone who has been on ART before re-starts at a lower rate than someone starting for the first time
- An intervention whose eligibility depends on the network: PrEP is indicated for HIV-negative people with two or more partners across both layers, or a partner with HIV
- Scenarios given as a table of parameter values (`create_scenario_list`, `use_scenario`)

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/model.R`, `original/module-fx.R`: the model, unchanged
- `reference.R`: runs the original, statement by statement, with more simulations, and writes the runs for `run.py`
- `run.py`: runs `reference.R` and writes `reference/`
- `reference/results.csv`: for each scenario (`none`, `cascade`, `prep`, `both`), the mean and 5% to 95% range of 10 simulations at each week of `num`, `s.num`, `i.num`, `si.flow`, `acute.num`, `chronic.num`, `aids.num`, `dx.num`, `art.num` (on ART, suppressed or not), `supp.num`, `prep.num`, `prep.indic.num`, `dep.flow`, `aids.dep.flow`, `arr.flow`, and the partnerships and people with two or more partners in each layer (`main.edges`, `main.concurrent`, `cas.edges`, `cas.concurrent`). Series from the user's modules have no value in week 1, since the modules first run in week 2
- `reference/summary.csv`: the original's own summary table, from these runs
- `reference/timing.json`: the time of a first run and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the Gallery's license (MIT)

The sources were fetched from the Gallery's repository at commit 5e4f508 into `_envs/epimodel/src/EpiModel-Gallery/` (with the SI with vital dynamics example, which was considered and not used); `original/` is a copy.

## How it is run

`model.R` has two configurations: 1,500 people, 1,040 weeks, and 5 simulations of each scenario in an interactive R session, and 300 people and 100 weeks for the Gallery's tests. `reference.R` uses the full-size one, by masking `interactive()` (and `commandArgs()`, since the script evaluates its first command-line argument as R code). It runs the script as it is in the global environment (it starts with `rm(list = ls())` and sources `examples/hiv/module-fx.R`, so it is run from a folder with that layout), and changes only, just before the scenario loop, the number of simulations (10 of each scenario), the number of cores (1), and the network statistics recorded. The original sets no seed; `reference.R` sets `set.seed(1)` first, so the network estimation and the runs are the same each time. It then runs the rest of the script (the analysis and the plots), and keeps the original's summary table.

The reference was run on one core, as one process, which takes about 40 minutes; with more cores EpiModel runs the simulations in parallel and the random numbers differ.

## Results

The original's summary, from the 10 reference runs of each scenario (the Gallery's README gives the same numbers from its own runs):

| Scenario | Cumulative infections | Final prevalence | Incidence per 100 person-years (second half) | Diagnosed | On ART | Suppressed |
|---|---|---|---|---|---|---|
| No intervention | 459 | 14.5% | 1.81 | | | |
| Cascade (95-95-95) | 74 | 5.1% | 0.14 | 97.7% | 91.9% | 89.8% |
| PrEP (50% coverage) | 244 | 7.3% | 0.80 | | | |
| Cascade + PrEP | 45 | 3.8% | 0.07 | 98.1% | 92.2% | 90.0% |

The networks keep close to their targets as the population changes: over the second half, a mean degree of 0.49 in the main layer (target 0.5) with 4.1% of people having two main partners (target 4%), and 0.28 to 0.30 in the casual layer (target 0.3) with 8.9% to 9.6% having two or more (target 10%). The mean degree stays at its target as the population grows from 1,500 to 1,700 with a working cascade.

## Timing

One simulation takes about 54 seconds on one core, and estimating the two networks 1.2 seconds, once. A rerun is the mean of the 10 runs with no intervention, and a first run adds the estimation.

## Lines of model code

405, counting the lines of `model.R` up to the end of section 3 (the network setup, the parameters, and running the scenarios) that are not blank or comments, without `library(EpiModel)` (100 lines), and every line of `module-fx.R` that is not blank or a comment (305 lines). Section 4 (the derived measures and the summary table) and section 5 (plots) are left out. No line is over 100 characters.

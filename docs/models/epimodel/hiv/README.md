# EpiModel: HIV with a care cascade and PrEP

HIV among 1,500 people over 20 years in weekly steps, transmitted over two networks of partnerships (main and casual) that form and dissolve, with acute, chronic, and AIDS stages, a care cascade from testing to viral suppression, PrEP for people at risk, and arrivals and departures. Four scenarios compare no intervention, a cascade that reaches the UNAIDS 95-95-95 targets, PrEP at 50% coverage among those indicated, and both. This is the HIV example of the EpiModel Gallery, the set of worked examples maintained by EpiModel's authors, and the one that brings the most of EpiModel together.

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

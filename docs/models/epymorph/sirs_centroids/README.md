---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# epymorph: SIRS in Arizona's counties, with commuting by distance

The centroids exercise of epymorph's vignette "Intro to Movement Models": an SIRS in Arizona's 15 counties, 7.2 million people, starting from 5 infectious people in Maricopa County, with a movement model in which 15% of people commute each day for a third of the day, to a county drawn with a weight that falls off with distance. Their own county is one of those drawn, and the others are far away for the kernel's scale of 20 miles, so people spend only 0.06% to 0.8% of their time in other counties. See the [review](../../../approaches/epymorph.md).

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`, the mean of 40 runs of the original.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 29 | 10 | The original's IPM (`SIRS`) and MM (`Centroids`) come from epymorph's library; the Starsim version writes both |
| One run | first 0.43 s, rerun 0.33 s | first 0.016 s, rerun 0.0039 s (Rust) | Each is one stochastic run of 190 days. A first run excludes imports; the original's includes building the RUME, with the ADRIOs' values already fetched |
| Results | Peak 415,899 infectious on day 96 (the mean of the 38 runs of 40 that took off); 3,273,531 recovered at the end | Peak 400,150 on day 93 (39 of 40); 3,240,514 recovered | **Agree** to within 8% at the peak in each county, and 5 days in its timing; 1.0% in the number recovered. Starsim is 1 to 5 days early in every county; see the findings |

Measured on 3 November 2026 with Starsim 4.0.0rc2 (the `v4` branch, commit `d0107e93`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: the counties as a geography, the SIRS, and the commuting as a matrix of the share of time that people spend in each other county. The matrix is two lines of NumPy, the centroids kernel `exp(-distance/phi)` normalized by row, since Starsim's movement models are gravity and radiation and have no kernel that decays exponentially with distance. In the original the movement is a clause that draws the commuters each day, written in Python.

## Findings

- **Fixed steps delay the original.** epymorph draws each event as Poisson over each of its two steps a day, a third and two thirds of a day, with the rates fixed over the step, so its epidemics grow more slowly than in continuous time. In one county with the same numbers, deterministic steps of a third and two thirds of a day put the peak 3 days later and 2% higher than continuous time, which is about the difference in the table. Starsim's `solver='tau'` is close to exact, and Starsim has no solver that leaps at fixed steps of given lengths, so the original's own steps can't be reproduced.
- **Commuting is a share of time, not a time of day.** The original sends commuters away for the first third of each day and brings them home for the rest; Starsim's commuting has people spend the same share of their time away, mixed into one force of infection each day. With at most 0.8% of time away, the two are close here, but the time of day can't be expressed.
- **The importer reads this RUME whole.** `ss.import_from()` on the RUME (written with `starsim/converters/epymorph.py`) lists nothing as untranslated, and the mean of 40 runs peaks at 429,837 on day 94, within the same tolerance. It finds the movement by running the clause for four weeks and averaging it, which here gives the same time away from each county as `model.py`, to within 2%.
- **The data needs a Census API key.** `acs5.Population()` now needs a key, and the Census API refuses requests without one. The populations here are the same estimates (ACS 5-year, 2022, B01001_001E) read from the Census Bureau's summary file, and the centroids come from epymorph's own TIGER ADRIO, which needs no key; `fetch.py` gets both and keeps them in `original/arizona_counties.csv`, so the comparison runs offline.
- **Dying out.** With 5 people infectious at the start, the epidemic dies out at once in about one run in twenty, in both (2 of 40 in the original, 1 of 40 in Starsim). The mean of all the runs depends mostly on how many die out, so both sides compare the runs that take off.
- **Distances.** epymorph measures them in miles and Starsim in kilometers, so `phi` of 20 miles is written as 32.2 km.

## What it exercises

- A geography of real places (Arizona's counties) with populations and centroids
- An SIRS with waning immunity
- Commuting with a kernel that decays with distance, for part of each day
- An epidemic seeded in one place that reaches the others in turn
- Stochastic runs, with some that die out

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/mm_intro_centroids.py`: the vignette's cells for this model, unchanged, joined into one script: those of exercise 1 that set up the model, and those of exercise 2, which uses the centroids movement model
- `original/arizona_counties.csv`: the population and centroid of each county, as the vignette's two ADRIOs give them
- `fetch.py`: fetches those once, in epymorph's environment
- `run.py`: runs it and writes `reference/`, with `export.py` in the framework's environment
- `reference/results.csv`: the mean and 5% to 95% range of the runs that took off, daily, for `S`, `I`, `R`, and `new_infections` in all, and `I` in each county (as `I_Maricopa`)
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (GPL-3.0)

`export.py` runs the vignette's own text, changed in three ways without changing the file: the ADRIOs are replaced by the values in `original/arizona_counties.csv`, the IPM's diagram is left out (it needs graphviz and LaTeX), and it stops before the run and the plots. The seeds of the reference runs are 1 to 40; the vignette's own run, with seed 5, is the one timed first.

## The model

- **Places:** Arizona's 15 counties, with their populations in the ACS 5-year estimates for 2022 (Maricopa 4,430,871, of 7,172,282 in all) and the TIGER internal point of each
- **Compartments:** `S`, `I`, `R`
- **Transitions:** `S` to `I` at `beta*S*I/N` among the people present in a county, `I` to `R` at `gamma*I`, and `R` to `S` at `xi*R`
- **Parameters:** `beta = 0.4`, `gamma = 1/4`, and `xi = 1/200` per day
- **Movement:** each day, `floor(0.15*N)` people of each county commute, to a county drawn with a weight of `exp(-d/phi)`, with `d` the great-circle distance and `phi = 20` miles (their own county, at a distance of 0, included); they leave for the first step of the day, a third of a day, and come back for the second
- **Initial conditions:** 5 infectious people in Maricopa County
- **Time:** 190 days from 1 January 2022, in two steps a day

## Lines of model code

29, counting the lines of `original/mm_intro_centroids.py` that are not blank, comments, imports, displays (`my_scope.labels`, the diagram, and `print`), or plotting (`log10_transform()` and the two plots).

---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# epidemics: the default SEIR-V by age

The model of epidemics' "Get started" vignette: the package's default model (`model_default()`), an SEIR-V in the UK in three age groups (0–19, 20–39, and 40+), mixing by a contact matrix from the POLYMOD survey, with R0 = 1.3, a latent period of 2 days, and an infectious period of 7, run for 600 days from one infectious person in a million. There is no vaccination, so `V` stays empty. See the [review](../../../approaches/epidemics.md).

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`, a run of the vignette.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 36 | 12 | Both count their data: 16 of the original's lines make the contact matrix and demography from the survey, and 2 of Starsim's give them as numbers |
| One run | first 0.02 s, rerun 0.009 s | first 0.59 s, rerun 0.0011 s (JAX) | The vignette's one call of `model_default()`, which includes checking its inputs and making its table of results; the odin model was compiled when the package was installed. Starsim's first run includes building the sim |
| Results | | | **Agree** to 1.4e-7 of each state's largest value, in total and in each age group, on every day. `I` peaks at 1,231,054 on day 369 in both, and 23,438,153 people are infected in both. `compare.py` allows 1e-6 |

Measured on 9 November 2026 with Starsim 4.0.0rc3 (the `v4` branch, commit `be38b9f6`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: four states, three transitions, a stratification by age with the population of each group, and the contact matrix as `ss.contacts()`. The original's transmission rate is R0 over the infectious period, with the contact matrix scaled to a leading eigenvalue of 1; Starsim's is the same, with the eigenvalue written out in the rate. Starsim prints R0 = 1.3 at the start of the run, from the next-generation matrix, which confirms the scaling.

| Original | Starsim |
|---|---|
| `socialmixr::contact_matrix(polymod, ...)` and `wpp2024`, 16 lines | `matrix` and `N`, as the vignette prints them |
| `initial_conditions`, a row of proportions for each age group | `init_n=dict(I=1e-6*sum(N))`, which is split in proportion to the groups |
| `population(...)` | `seir.stratify(age=[0, 20, 40], fractions=N)` and `networks=ss.contacts(matrix)` |
| `model_default(population, time_end = 600)`, with its defaults `transmission_rate = 1.3/7`, `infectiousness_rate = 1/2`, `recovery_rate = 1/7` | The three transitions, with the defaults written in |
| `V`, a compartment of the fixed model | Left out, since nothing reaches it |

## Findings

- **The contact matrix needs no conversion here.** epidemics transposes the matrix, divides it by its leading eigenvalue, and divides each row by the size of its group, so that `lambda[i] = beta * sum(C[j, i]/N[i] * I[j])`. Starsim's frequency-dependent mixing is `lambda[i] = beta * sum(C[i, j] * I[j]/N[j])`. The two are the same when the matrix is reciprocal (`C[i, j]*N[i] = C[j, i]*N[j]`), as socialmixr's is with `symmetric = TRUE`, as here. A matrix that is not reciprocal would give different epidemics in the two, and a translation would have to transpose and rescale it. This is a difference of convention, not a Starsim issue, and the vignette's note on the two conventions says the same.
- **R0 is reported, not given.** The original's parameter is R0, through the scaling of the matrix. Starsim works out R0 from the next-generation matrix and prints it, but the rate is still written as `1.3/7/max(eigenvalues)`, as in the epydemix models. A way to give the transmission rate by its R0 (for example `beta=ss.R0(1.3)`, solved at the start from the same next-generation matrix) would state what the vignette means directly.
- **Only the states that are used.** epidemics' models are fixed, so this one has a `V` compartment that stays empty. Starsim states the model the vignette uses, without it; the next model, [seasonal_scenarios](../seasonal_scenarios), adds it with the vaccination.

## Why this model

It is epidemics' "Get started" example, and the base of every other vignette of the default model: the population, contact matrix, and initial conditions here are shared by them. It is the simple one of the two epidemics models; [seasonal_scenarios](../seasonal_scenarios) is the other.

## What it exercises

- An SEIR stratified by age, mixing by a contact matrix from a survey
- A transmission rate given by R0, through the leading eigenvalue of the matrix
- Initial conditions as a share of each group

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/epidemics.R`: the vignette's code (`vignettes/epidemics.Rmd` at the `v0.5.0` tag), as `knitr::purl()` writes it, unchanged
- `run.py`: runs it in the epidemics environment, giving the contact matrix and demography as the vignette prints them in place of the 16 lines that load them (see [the framework's README](../README.md)), and leaving out the plot; it writes `reference/`
- `reference/results.csv`: `S`, `E`, `I`, `R`, and `V` in each age group (`I_0-19`, `I_20-39`, `I_40+`) and in total, on each day from 0 to 600
- `reference/timing.json`: the time of the vignette's call of `model_default()`, and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (MIT)

## The model

For each age group `i` of 3:

- **Infection:** `lambda[i] = beta * sum(C[j, i]/N[i] * I[j])`, with `beta = 1.3/7` per day and `C` the contact matrix divided by its leading eigenvalue (14.1, 12.2, and 9.2 contacts a day in the three groups, before scaling; the leading eigenvalue is 11.8)
- **Latency** of 2 days and **recovery** after 7, both exponential
- **Population:** 14,865,748, 16,978,469, and 29,438,434 people aged 0–19, 20–39, and 40+ (the UK in 2006, from `wpp2024`), with POLYMOD's UK contacts by the same groups
- **Initial conditions:** one in a million infectious in each group, so 61 in all
- **Time:** days 0 to 600, solved by deSolve's `lsoda` through odin, with results once a day

## Results

The epidemic grows slowly (R0 is 1.3), peaks on day 369 with 1.23 million infectious, and infects 23.4 million people, 38% of the population, by day 600.

## Lines of model code

36: the lines of `epidemics.R` that are not blank or comments, without `library()`, knitr's options, the plot, and the lines that only print an object (`contact_matrix`, `demography_vector`, `initial_conditions`, `uk_population`). 16 of them make the contact matrix and the demography. No line is over 100 characters. Starsim's 12 are counted the same way.

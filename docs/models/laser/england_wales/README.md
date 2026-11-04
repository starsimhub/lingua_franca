---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# LASER: measles in England and Wales

An agent-based model of measles in the 954 towns and cities of England and Wales before vaccination, from the laser-generic tutorial notebook "Spatial features of measles transmission in England and Wales during the pre-vaccine era". Each place has its 1944 population; people are born at the mean crude birth rate of the data, die at an age drawn from a life table, catch measles by a seasonal force of infection that is shared between places by a gravity model, and three infectious people are brought in every 30 days for the first 10 years. The notebook runs 150 simulations of 40 years over a sample of five parameters (transmission, the amplitude of the seasonality, and three of the gravity model), and ranks them against the measles case reports by the share of weeks with no cases in each place (the critical community size) and by the phase of each place's epidemics relative to London's (travelling waves).

The reference here runs the model with the best of those parameter sets, as the notebook reports it, and scaled down (see below).

This is LASER's model for wave 3. `model.py` is the Starsim version, and `compare.py` checks it against `reference/`. Both run the same scaled-down version of the notebook's model: the 53 places within 100 km of Norwich, at their real sizes, for 10 years (see below for why).

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 126 | 46 | Lines over 100 characters count twice. The original's 126 are for one run; with the notebook's sweep over 150 parameter sets, 172 |
| One run | first 4.2 s, rerun 2.8 s | first 12 s, rerun 12 s (Rust) | 667,864 agents for 3,650 days. Each uses its default threads: LASER's on all cores, and Starsim's for its passes over the agents, with one thread for BLAS. With one thread each, LASER takes 4.7 s and Starsim 19.7 s. LASER has no way to run a built model again, so its rerun builds the model too |
| Results | | | **Agree.** Over the 10 years, 107,761 infections against 106,639 (+1.1%; means of 3 and 50 runs, where `compare.py` now makes the last two of the three to keep the benchmark short; the three Starsim runs are 106,611, 106,913, and 109,760, against the original's 5% to 95% range of 103,139 to 108,758); in each of seven places from Norwich to Southwold within 3%, except the smallest, Southwold, at +12%; 537,442 people at the end against 529,833 (+1.4%, finding 1). The share of weeks with no infections in each place, in the second half, is 0.631 against 0.628, and correlates at 0.985 across places. `compare.py` allows 5% in total, 20% in a place, 2% in people at the end, and 0.03 in the share of weeks |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: the four states and three transitions, the latent period and the infectious period as normals (the original gives its transmission the infectious period's normal for the latent period of everyone it infects; its gamma with shape 40 is used only for people exposed at the start, of whom there are none), births into `S`, deaths from a life table, the importation as a delivery, the places with their populations and the original's distance matrix, the coupling as a moving force of infection (`ss.geo.Mobility(..., kind='force')`), the initial conditions in each place, the age pyramid, and the seasonal transmission as a time series that repeats every year.

The one part written by hand is the gravity matrix (5 lines of NumPy, passed as `matrix=`), since its scaling cannot be given to `ss.geo.gravity`. The original also builds it in its own code, so this is no extra work.

## Findings

1. **The life table is declared, and differs from LASER's in the first year (a difference, small for measles).** LASER gives someone part way through a year of age the whole year's chance of dying in what is left of it, which adds deaths at the start only. `ss.death(lifetable=ss.lifetable(ages, pyramid))` spreads deaths evenly through each year of age, which is the usual reading of a life table: 31,276 deaths in the first year against LASER's 43,037. Over the 10 years the gap narrows to 231,525 deaths against 237,762, which leaves 1.4% more people at the end. `compare.py` does not hold the first year's deaths to a tolerance. An earlier version reproduced LASER's estimator exactly by writing each person's time of death by hand (8 lines); the declared form is shorter and agrees as well on measles, so it was kept.
2. **Fixed: importing a fixed number of people on a schedule can be declared.** `ss.Delivery(move=S >> I, capacity=3, start=ss.days(30), interval=ss.days(30))` moves exactly three susceptible people, chosen from everyone, on days 30, 60, and so on to day 3,630, and replaces a function of 7 lines. The people imported stay infectious for the same time as everyone else here, about a day less than in LASER, since the delivery has no dwell time of its own; the total still agrees (+1.1%).
3. **Speed at full size.** At this size Starsim is much slower than LASER (see the table), which threads do not explain. The full model (30 million people, 40 years) is left out of this comparison, as it is in the original's reference.
4. **Fixed: a stop of 1900 or more was read as a calendar year.** With `unit=` given (and not `'year'`), a bare `stop` is now in that unit, however large.
5. **Fixed: no periodic time series.** The seasonality is 26 values, each held for 14 days of a year, repeated every year. `ss.timeseries(..., period=ss.days(365))` gives the profile once.
6. **The gravity model's scaling cannot be given.** The notebook scales the gravity matrix so that the mean share exported, over places, is `k`, and then caps each place at 0.2. `ss.geo.Mobility(away=)` sets every place's share to the same value, and the only cap is 1. Also, `ss.geo.gravity`'s exponent `a` is that of `pop[i]^(a−1)`, so LASER's `a=0` is Starsim's `a=1`, which is easy to get wrong. Here the matrix is built in NumPy, as in the original. Suggested: `ss.geo.Mobility(ss.geo.gravity(b=0.25, c=1.56), kind='force', away=ss.mean(0.0446), cap=0.2)` or similar.
7. **`ss.gamma(40, 0.25)` is not a gamma with shape 40 and scale 0.25.** The second positional parameter is SciPy's `loc`, so this is a latent period of 40.25 days, and nothing warns. LASER (and NumPy) take `(shape, scale)`. It isn't used here, since the gamma is not reached (see above). Suggested: make `loc` keyword-only, or warn when a dwell time has a nonzero `loc`.
8. **The original's infectious period is a day shorter than written (a finding about the original).** The notebook lists the components with `Exposed` before `Infectious`, so someone who becomes infectious counts down on the same day, and is infectious for `round(normal(8, 2)) − 1` days. The translation uses `normal(7, 2)`; with `normal(8, 2)` the reproduction number would be 31 rather than 27.

## What it exercises

- Agents grouped into many places (954 in the notebook, 53 here), with a distance between each pair from a precomputed matrix
- Coupling between places that moves the force of infection, from a gravity model with the exponent of the source's population set to 0, scaled so that the mean share exported is a given value and capped at 0.2 for any place
- Seasonal transmission from a tabulated profile: 26 values, each held for 14 days of a 365-day year, raised to a power (the amplitude)
- Dwell times drawn per agent and counted down by timers: a gamma with shape 40 (an almost fixed 10 days) for the latent period, and a normal(8, 2) rounded to whole days for the infectious one
- Births at a crude birth rate, into the susceptible state
- Deaths from a life table: an age pyramid at the start, and an age at death drawn once for each person (at the start, given their age, and at birth)
- Importation: a fixed number of people, chosen at random from all the susceptible, made infectious on a fixed schedule
- Initial conditions per place: three infectious people in every place, 95% immune, the rest susceptible
- Custom components: the importation and the seasonal transmission are classes written in the notebook

## Scaling down

The full model has 30.2 million agents. One run of 40 years would take about ten minutes in LASER (at a tenth of the size it takes 71 s), which is more than a comparison of many runs can afford. Every population cannot simply be divided by the same factor, because the smallest place (777 people) has to hold 3 infectious people and 95% immune ones, so a tenth is the most it allows, and 3 million agents is still too many. The reference therefore keeps every place within 100 km of Norwich (53 places, 667,864 people, from Saxmundham with 1,356 to Norwich with 101,600), at their real sizes, for 10 years (the years of importation). Distances are those between these places; the gravity model is scaled over them; and the crude birth rate is still the mean over all 954 places, as in the notebook. The same subset is used by the translation.

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/10_England_and_Wales.ipynb`: the notebook, unchanged, with its outputs. The data it reads (`EnglandWalesMeasles.py`, 21 MB, and `EnglandWalesDistances.npy`, 3.6 MB) are not copied here: they are read from the laser-generic source in `_envs/laser/src/data`
- `simulate.py`: runs the model cells of the notebook several times in the LASER environment and prints the results as JSON
- `run.py`: calls `simulate.py` and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 50 runs, of the daily totals of `S`, `E`, `I`, and `R` (time in days, from 0 to 3,650) and of the infections imported (`imports`, days 0 to 3,649); the weekly totals of births, deaths, and infections (time is the first day of the week, for 521 weeks), in total (`new_infections`) and in seven places (`new_infections_norwich`, `_cambridge`, `_colchester`, `_kings.lynn`, `_ely`, `_thetford`, and `_southwold`, from largest to smallest); the infections in each year of 52 weeks (`yearly_infections`, time is the year) and over the whole run (`total_infections`, at time 0); and `prop_zero`, the share of the weeks in the second half of the run (weeks 260 to 520) with no infections in each place, where time is the place's index (the 53 places in alphabetical order, as in the data)
- `reference/timing.json`: the time of a first run and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the laser-generic license (MIT)

`simulate.py` runs cells 1 to 4 and the sweep cell of the notebook (cell 8, the one with `run_sims`) from the notebook's text, with these changes made to the text before running it, without changing the file: the data are read from `_envs/laser/src`; `import pywt` is left out (only the wavelet analysis after the model uses it, and it is not installed); `run_sims` is set to `True`; the sweep runs one parameter set, the best one the notebook reports (simulation 56: `beta` 3.865332, `amplitude` 1.310744, `k` 0.044565, `b` 0.251464, `c` 1.563193); the seed, which is 4 in every simulation of the notebook, is 1000, 2000, and so on (spaced out, since LASER seeds thread `j` with `seed + j`); `nticks` is 10 years; and after the scenario is built, only the places within 100 km of Norwich are kept (with their rows of the distance matrix). With more than one thread, two runs with the same seed still differ, so the reference is a distribution, not an exact trajectory.

## The model

**Each day,** in the order of the notebook's components:

1. Exposed agents count down their timer, and when it reaches zero become infectious and draw an infectious duration, `max(round(normal(8, 2)), 1)` days.
2. Infectious agents count down their timer, and recover when it reaches zero. Since this comes after step 1, someone who has just become infectious counts down on the same day, so the infectious period is in effect one day shorter than the duration drawn: someone is counted as infectious at the start of `k − 1` days.
3. Importation: on days 30, 60, and so on up to 3,630, three susceptible agents, chosen at random from the whole population, become infectious, with a duration drawn as above (and not shortened).
4. Transmission. With the counts at the start of the day, `f_i = beta * season[day % 365] * I_i / N_i` in each place, `f_j <- f_j + sum over i of f_i * network[i, j] - f_j * sum over i of network[j, i]`, and each susceptible agent in place `j` is infected with probability `1 - exp(-f_j)`, and draws a latent duration of `max(round(gamma(40, 0.25)), 1)` days.
5. Births: in each place, a Poisson number with mean `N * ((1 + CBR/1000)^(1/365) - 1)`, with the counts after the day's changes, where CBR is 17.19 per 1,000 per year. Newborns are susceptible.
6. Deaths: agents whose date of death is today die.

**Parameters.** `beta = 3.865` per day; `season[d] = exp(log_beta[d // 14] - mean)^1.3107`, with the 26 values of `log_beta` from Bjørnstad et al. (2002), and the mean over the 365 days; the network is `p_j^0.2515 / d_ij^1.5632` (with a zero diagonal), scaled so that its rows sum on average to `k = 0.0446`, with any row over 0.2 scaled down to 0.2 (none is, here).

**Ages and deaths.** With `r = 365*((1 + CBR/1000)^(1/365) - 1)`, the age pyramid has weight `exp(-r*a)` for each year of age `a` from 0 to 88, and the same weights are the life table: the deaths in each year of age. At the start, each person draws an age from the pyramid (a whole year from the weights, then a day in it); everyone then draws a year of age at death, from those years not younger than their age, in proportion to the weights, and a day in that year (from their birthday if it is the year they are in). Newborns do the same at birth. The mean age at death is about 34 years, so the population falls by about 2% a year, and in the first year by more (6.4% die), because someone who is part way through a year of age has the whole year's chance of dying in what is left of it.

## Lines of model code

126 for one run, counting the lines of the notebook's model cells (1 to 4, and the sweep cell) that are not blank, comments, imports, or the three lines that print versions, without the lines of the sweep cell that only sample, save, or resume the 150 runs, and counting each line over 100 characters as two. With the sweep, 172.

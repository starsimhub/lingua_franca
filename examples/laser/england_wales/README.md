# LASER: measles in England and Wales

An agent-based model of measles in the 954 towns and cities of England and Wales before vaccination, from the laser-generic tutorial notebook "Spatial features of measles transmission in England and Wales during the pre-vaccine era". Each place has its 1944 population; people are born at the mean crude birth rate of the data, die at an age drawn from a life table, catch measles by a seasonal force of infection that is shared between places by a gravity model, and three infectious people are brought in every 30 days for the first 10 years. The notebook runs 150 simulations of 40 years over a sample of five parameters (transmission, the amplitude of the seasonality, and three of the gravity model), and ranks them against the measles case reports by the share of weeks with no cases in each place (the critical community size) and by the phase of each place's epidemics relative to London's (travelling waves).

The reference here runs the model with the best of those parameter sets, as the notebook reports it, and scaled down (see below).

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

- `original/10_England_and_Wales.ipynb`: the notebook, unchanged, with its outputs. The data it reads (`EnglandWalesMeasles.py`, 21 MB, and `EnglandWalesDistances.npy`, 3.6 MB) are not copied here: they are read from the laser-generic source in `_envs/laser/src/laser-generic-1.1.0/data`
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

# LASER England and Wales measles, in Starsim

The translation of [models/laser/england_wales](../../../models/laser/england_wales), LASER's model for wave 3. The model is `model.py`; `compare.py` checks it against the original's reference results. Both run the same scaled-down version of the notebook's model: the 53 places within 100 km of Norwich, at their real sizes, for 10 years (see the example's README for why).

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 126 | 46 | Lines over 100 characters count twice. The original's 126 are for one run; with the notebook's sweep over 150 parameter sets, 172 |
| One run | first 5.7 s, rerun 4.1 s | first 22 s, rerun 19 s (Rust) | 667,864 agents for 3,650 days. LASER runs on all 20 cores; Starsim on one. LASER has no way to run a built model again, so its rerun builds the model too |
| Results | | | **Agree.** Over the 10 years, 107,761 infections against 106,639 (+1.1%; means of 3 and 50 runs, where `compare.py` now makes the last two of the three to keep the benchmark short; the three Starsim runs are 106,611, 106,913, and 109,760, against the original's 5% to 95% range of 103,139 to 108,758); in each of seven places from Norwich to Southwold within 3%, except the smallest, Southwold, at +12%; 537,442 people at the end against 529,833 (+1.4%, finding 1). The share of weeks with no infections in each place, in the second half, is 0.631 against 0.628, and correlates at 0.985 across places. `compare.py` allows 5% in total, 20% in a place, 2% in people at the end, and 0.03 in the share of weeks |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `4473e253`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: the four states and three transitions, the latent period and the infectious period as normals (the original gives its transmission the infectious period's normal for the latent period of everyone it infects; its gamma with shape 40 is used only for people exposed at the start, of whom there are none), births into `S`, deaths from a life table, the importation as a delivery, the places with their populations and the original's distance matrix, the coupling as a moving force of infection (`ss.geo.Mobility(..., kind='force')`), the initial conditions in each place, the age pyramid, and the seasonal transmission as a time series that repeats every year.

The one part written by hand is the gravity matrix (5 lines of NumPy, passed as `matrix=`), since its scaling cannot be given to `ss.geo.gravity`. The original also builds it in its own code, so this is no extra work.

## Findings

1. **The life table is declared, and differs from LASER's in the first year (a difference, small for measles).** LASER gives someone part way through a year of age the whole year's chance of dying in what is left of it, which adds deaths at the start only. `ss.death(lifetable=ss.lifetable(ages, pyramid))` spreads deaths evenly through each year of age, which is the usual reading of a life table: 31,276 deaths in the first year against LASER's 43,037. Over the 10 years the gap narrows to 231,525 deaths against 237,762, which leaves 1.4% more people at the end. `compare.py` does not hold the first year's deaths to a tolerance. An earlier version reproduced LASER's estimator exactly by writing each person's time of death by hand (8 lines); the declared form is shorter and agrees as well on measles, so it was kept.
2. **Fixed: importing a fixed number of people on a schedule can be declared.** `ss.Delivery(move=S >> I, capacity=3, start=ss.days(30), interval=ss.days(30))` moves exactly three susceptible people, chosen from everyone, on days 30, 60, and so on to day 3,630, and replaces a function of 7 lines. The people imported stay infectious for the same time as everyone else here, about a day less than in LASER, since the delivery has no dwell time of its own; the total still agrees (+1.1%).
3. **Speed at full size.** At this size Starsim is much slower than LASER on 20 cores (see the table). The full model (30 million people, 40 years) is left out of this comparison, as it is in the original's reference.
4. **Fixed: a stop of 1900 or more was read as a calendar year.** With `unit=` given (and not `'year'`), a bare `stop` is now in that unit, however large.
5. **Fixed: no periodic time series.** The seasonality is 26 values, each held for 14 days of a year, repeated every year. `ss.timeseries(..., period=ss.days(365))` gives the profile once.
6. **The gravity model's scaling cannot be given.** The notebook scales the gravity matrix so that the mean share exported, over places, is `k`, and then caps each place at 0.2. `ss.geo.Mobility(away=)` sets every place's share to the same value, and the only cap is 1. Also, `ss.geo.gravity`'s exponent `a` is that of `pop[i]^(a−1)`, so LASER's `a=0` is Starsim's `a=1`, which is easy to get wrong. Here the matrix is built in NumPy, as in the original. Suggested: `ss.geo.Mobility(ss.geo.gravity(b=0.25, c=1.56), kind='force', away=ss.mean(0.0446), cap=0.2)` or similar.
7. **`ss.gamma(40, 0.25)` is not a gamma with shape 40 and scale 0.25.** The second positional parameter is SciPy's `loc`, so this is a latent period of 40.25 days, and nothing warns. LASER (and NumPy) take `(shape, scale)`. It isn't used here, since the gamma is not reached (see above). Suggested: make `loc` keyword-only, or warn when a dwell time has a nonzero `loc`.
8. **The original's infectious period is a day shorter than written (a finding about the original).** The notebook lists the components with `Exposed` before `Infectious`, so someone who becomes infectious counts down on the same day, and is infectious for `round(normal(8, 2)) − 1` days. The translation uses `normal(7, 2)`; with `normal(8, 2)` the reproduction number would be 31 rather than 27.

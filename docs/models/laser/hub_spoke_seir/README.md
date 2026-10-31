# LASER: spatial SEIR on a hub and spokes

An agent-based SEIR epidemic in 1,750,000 people living in 16 patches (a central city, five towns around it, and two small places on the way to each town), coupled by a gravity model, over 365 days. It is the SEIR model at the end of the "Grid function examples" notebook in the laser-generic documentation.

## What it exercises

- Agents grouped into patches, each patch with its own compartment counts
- Spatial coupling: a gravity network built from the patch populations and the distances between them, which moves part of each patch's force of infection to the other patches (agents do not move)
- Dwell times drawn per agent from a distribution (normal, rounded to whole days) and counted down by a timer, not constant rates
- A fixed daily step, with the force of infection turned into a probability
- An epidemic seeded in one patch that reaches the others in turn

## Files

- `original/grid_examples_seir.py`: the two notebook cells that define the scenario and the model, unchanged, joined into one script (the cells before them, which only show the `grid()` function, and the plotting cells after them are left out; the plot at the end of the model cell is kept)
- `simulate.py`: runs the original several times in the LASER environment and prints the results as JSON
- `run.py`: calls `simulate.py` and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 20 runs, daily, for `S`, `E`, `I`, `R`, and `new_infections`, each in total and for four patches (suffixes `_central_city`, `_town_1`, `_interim_1a`, and `_town_3`, as in `I_town_1`)
- `reference/timing.json`: the time of a first run and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the laser-generic license (MIT)

The original runs as published against the installed version. `simulate.py` changes its text in two ways before running it, without changing the file: it stops after `model.run()`, leaving out the plot, and it adds `"prng_seed": seed` to the parameters, because without a seed LASER uses the same one (20260101) every time. The seeds are 1000, 2000, to 20000, spaced out because LASER seeds thread `j` with `seed + j`. With more than one thread, two runs with the same seed still differ, so the reference is a distribution, not an exact trajectory.

## The model

**Patches.** Coordinates are in meters (EPSG:3857), around the point (0, 0), and are then converted to longitude and latitude. With angle `2*pi*i/5` for spoke `i = 0` to `4`:

| Patch | Population | Distance from center | Node IDs |
|---|---|---|---|
| Central City | 1,000,000 | 0 | 0 |
| Town 1 to 5 | 100,000 each | 150,000 m | 1, 4, 7, 10, 13 |
| Interim 1a to 5a | 25,000 each | 50,000 m | 2, 5, 8, 11, 14 |
| Interim 1b to 5b | 25,000 each | 100,000 m | 3, 6, 9, 12, 15 |

**Parameters.** `nticks = 365` (one tick is one day), `beta = R0/inf_mean = 2/14` per day, exposed duration normal(7, 1) days, infectious duration normal(14, 2) days, `gravity_c = 2.5`, and LASER's defaults `gravity_k = 500`, `gravity_a = 1`, `gravity_b = 1`. Each duration is rounded to a whole number of days, with a minimum of 1.

**Initial conditions.** Everyone is susceptible except 100 people in Town 1, who are infectious, each with an infectious duration drawn as above. No births or deaths.

**Network.** `network[i, j] = k * p_i^a * p_j^b / d_ij^c`, where `p` is the patch population and `d` the great-circle (haversine) distance in kilometers between the patch centroids (149.8 km from the center to a town, not 150, because of the projection), with a zero diagonal. Each row that sums to more than 3/32 is then scaled down to sum to 3/32. Here every row is far over that, so `k` and `p_i` cancel, and `network[i, j] = (3/32) * (p_j / d_ij^2.5) / sum over l of (p_l / d_il^2.5)`.

**Each day,** in this order:

1. Infectious agents count down their timer and recover when it reaches zero.
2. Exposed agents count down their timer, and when it reaches zero become infectious and draw an infectious duration.
3. Transmission. With the counts at the start of the day, `f_i = beta * I_i / N_i` in each patch, then `f_j <- f_j + sum over i of (f_i * network[i, j]) - f_j * sum over i of network[j, i]`. Each susceptible agent in patch `j` is infected with probability `1 - exp(-f_j)`, and draws an exposed duration.

The counts for day `t + 1` are those for day `t` plus the day's changes. `new_infections` at time `t` is the number infected during day `t` (between the counts at `t` and `t + 1`), so it runs from 0 to 364 while the compartments run from 0 to 365.

About 88% of people are infected in the end, more than the 80% of a single well-mixed population with an R0 of 2, because the coupling moves force of infection, not infectious people: a share of a small patch's force of infection applies in full to a large patch.

## Lines of model code

50, counting the lines of `original/grid_examples_seir.py` up to and including `model.run()` that are not blank, comments, imports, or the notebook display line `scenario.head()`, and counting each of the five lines over 100 characters as two.

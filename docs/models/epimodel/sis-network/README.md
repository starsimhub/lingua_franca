# EpiModel: SIS on a dynamic network

A stochastic SIS epidemic among 500 people whose partnerships form and dissolve over time, for 500 time steps. This is the network example from EpiModel's own introduction: a statistical model of the network is estimated from target statistics, and the epidemic is then simulated over networks drawn from it.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 13 | 9 |  |
| One run | first 6 s, rerun 5.1 s | first 0.52 s, rerun 0.32 s (Rust) | The first run of the original includes estimating the network (`netest`), which is done once; a rerun uses the fitted network |
| Results | | | **Agree, once the order within a step is allowed for** (within 5% at equilibrium): 11.7 new infections a step at equilibrium, against 12.0 (means of 100 runs each). Over the last 200 steps 240 of 500 are infected, against 227.5: EpiModel lets people recover in the step in which they are infected and counts them after that, which makes its count 5% lower for the same epidemic (240 × 0.95 = 228). With the same allowance, 118 are infected after step 50, against 113, where the runs vary most |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: two transitions and a network, described by the same targets as the original (`ss.DegreeNet(n_contacts=0.7, concurrency=0.22, max_contacts=3, dur=50, acts=ss.freqperday(2))`). The chance of transmission is per act, as in EpiModel, and the probabilities per step are written as `ss.prob`.

## Findings

- **Described the way EpiModel describes it, but not an ERGM.** The original fits a network to target statistics: 175 partnerships, 110 people with two or more partners, nobody with four or more. `ss.DegreeNet` takes the same targets: people look for partners at a rate that depends on how many they have, chosen so that the targets are the network's stable state, and partnerships end at a constant rate. It has 176 partnerships and 109 people with two or more (EpiModel's network has 177 and 111). It matches the number of partners people have, and not other structure an ERGM can target, such as triangles. EpiModel's approach is the more general one.
- **Network diagnostics.** The original reports the edges, mean degree, concurrency, and partnership duration of the simulated network over time. `ss.DegreeNet` records the mean number of partners and the share with two or more as results, and `net.check()` compares them with the targets over a few runs, as `netdx()` does.
- **Fixed: acts in a partnership.** The first version worked out a probability per partnership by hand; `acts=` on the network now says it directly. In this sim, with no unit, a day is a step, so `ss.freqperday(2)` reads a little oddly for "two acts a step".

## What it exercises

- A contact network defined by what it should look like (the number of partnerships, how many people have two or more, nobody with four or more) instead of by a rule for making it
- Partnerships with a duration: each lasts 50 time steps on average, so the network changes slowly
- A separate estimation step (`netest`) before any simulation, and diagnostics of the simulated networks against their targets
- Transmission along partnerships between a susceptible and an infectious person, with a probability per act and a number of acts per time step
- Recovery back to susceptible
- Many stochastic simulations, each on its own network

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/intro_sis.R`: the model, from the vignette (see below for what was left out)
- `reference.R`: runs the original, then repeats its simulation and writes the runs for `run.py`
- `run.py`: runs `reference.R` and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 100 simulations at each time step (`s.num`, `i.num`, `si.flow`, `is.flow`, `edges`, `meandeg`, `concurrent`, `duration`, `prop.diss`)
- `reference/timing.json`: the time of a first run and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (GPL-3)

`original/intro_sis.R` is the code of steps 1 to 3 of the "Network Model Pipeline" section of the vignette "Introduction to EpiModel" in EpiModel 2.6.2, word for word, as extracted in `doc/Intro.R` of the installed package. The two `plot(dx)` lines of step 2 are left out, as is everything after step 3 (plots, summaries, and a second example).

## The model

- **Population:** 500 nodes, closed (no births or deaths), one group, no attributes
- **Formation model:** `~edges + concurrent + degrange(from = 4)` with target statistics `c(175, 110, 0)`: 175 partnerships (a mean degree of 2 × 175 / 500 = 0.7), 110 nodes with two or more partners, and no node with four or more
- **Dissolution model:** `~offset(edges)` with `duration = 50`: every partnership ends with probability 1/50 = 0.02 per time step, whatever its age or its nodes (a dissolution coefficient of log(49) = 3.892)
- **Estimation:** `netest` with its defaults, which fits a static ERGM to the targets and then subtracts the dissolution coefficient from the `edges` coefficient to get the formation model of the dynamic network (the "edges dissolution approximation"). The fitted formation coefficients are about -11.5 for `edges`, 1.4 for `concurrent`, and minus infinity for `deg4+`
- **Epidemic parameters:** `inf.prob = 0.4` (per act), `act.rate = 2` (acts per partnership per time step), `rec.rate = 0.05` (per time step)
- **Initial conditions:** `i.num = 10` infectious nodes, chosen at random; the other 490 are susceptible
- **Time:** `nsteps = 500`. A time step has no unit. Step 1 is the initial state, and steps 2 to 500 are simulated, so the flows have 499 values
- **Simulations:** `nsims = 5` in the original; 100 for the reference results

### What happens in a time step

With `control.net(type = "SIS")` and its defaults, EpiModel 2.6.2 does the following, in this order:

1. **Network:** the partnerships of this time step are looked up. By default (`resimulate.network = FALSE`) the whole dynamic network, all 500 steps of it, is simulated once at the start of each simulation, before the epidemic; this is possible because nothing in the epidemic changes the network. Each simulation starts from its own draw of the static network.
2. **Infection:** for every partnership between a susceptible and an infectious node, the susceptible node is infected with probability `1 - (1 - inf.prob)^act.rate` = 1 - 0.6² = 0.64. A susceptible node with several infectious partners has one such draw for each.
3. **Recovery:** every infectious node, including those infected in this time step, recovers with probability `rec.rate` = 0.05. The rate is used as the probability as it is, not as `1 - exp(-rec.rate)`. The time spent infectious is therefore geometric with a mean of 20 time steps.
4. **Counts:** `s.num` and `i.num` are counted at the end of the time step, and `si.flow` and `is.flow` are the numbers infected and recovered during it.

## Results

- `s.num`, `i.num`: the numbers susceptible and infectious at the end of each time step
- `si.flow`, `is.flow`: new infections and recoveries in each time step (from step 2)
- `edges`, `meandeg`, `concurrent`: the number of partnerships, the mean degree, and the number of nodes with two or more partners at each time step, to compare with the targets of 175, 0.7, and 110
- `duration`: the mean age of the partnerships that exist at each time step, as EpiModel computes it for its duration diagnostic (a partnership that already exists at step 1 is given an age drawn from the geometric distribution it should have); the target is 50
- `prop.diss`: the proportion of partnerships that end at each time step; the target is 0.02

The mean of `i.num` rises from 10 to an endemic level of about 227 of 500 (45%) by step 200, with about 12 infections and 12 recoveries per step. Over the last 200 steps the network statistics average 177 partnerships, a mean degree of 0.71, 111 nodes with two or more partners, and a mean partnership age of 50.1 steps.

`reference.R` runs the original as it is, and then runs `netsim` again with the original's own `est`, `param`, `init`, and `control`, changing only `nsims` to 100, the number of cores, and `nwstats.formula` (to record `meandeg` as well as the formation terms). It uses `set.seed(1)` for these runs, so `run.py` writes the same results each time, whatever the number of cores, as long as there are at least two (with one core EpiModel runs the simulations in the main R session and draws its random numbers differently). Every run estimates the network again with the original's `set.seed(12345)`, so the fitted model is also the same each time.

## Timing

One simulation (`netsim` with `nsims = 1`) takes about 4 seconds. About 90% of that is R code that keeps the history of each person's status and looks up the current partnerships at every step; simulating the 500 steps of the network takes about 0.4 seconds. Estimating the network (`netest`) takes about 0.7 seconds and is done once, so a first run counts it and a rerun does not. The diagnostics (`netdx`, 5 networks) take about 1.5 seconds. `run.py` takes a few minutes on 2 cores.

## Lines of model code

13, counting the lines of `intro_sis.R` that are not blank or comments, without `library(EpiModel)` and without the diagnostics line (`netdx`), which is not needed to define or run the model. No line is over 100 characters. With the diagnostics it would be 14.

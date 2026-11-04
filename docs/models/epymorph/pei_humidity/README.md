# epymorph: influenza driven by humidity in six US states (Pei et al. 2018)

The example in epymorph's `USAGE` notebook, its IPM and MM `Pei`, after Pei et al. (2018): an SIRS of influenza in Florida, Georgia, Maryland, North Carolina, South Carolina, and Virginia, 56 million people, in which transmission falls as absolute humidity rises, in each state on each day, with commuters and other travelers moving between the states for a third of each day. It starts from 10,000 infectious people in Florida. See the [review](../../../approaches/epymorph.md).

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`, the mean of 20 runs of the original.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 22 | 19 | The notebook's lines; the IPM and MM it takes from epymorph's library (`original/ipm_pei.py` and `original/mm_pei.py`) are 21 and 62 more |
| One run | first 0.27 s, rerun 0.16 s | first 0.077 s, rerun 0.0022 s (Rust) | Each is one stochastic run of 150 days. A first run excludes imports; the original's includes building the RUME |
| Results | Peak 2,474,561 infectious in all on day 95; 37,075,485 infections | Peak 2,528,987 on day 92; 37,226,473 infections | **Agree** to within 3.4% at the peak in each state, 3 days in its timing, and 0.9% in the number infected. Florida, where it starts, peaks on day 59 in both; the other states peak 1 to 3 days earlier in Starsim, for the reason given for the [SIRS in Arizona](../sirs_centroids/README.md#findings) |

Measured on 3 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `0d5e22f4`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The humidity is a time series for each state, `ss.by(patch=[ss.timeseries(...), ...])`, and the transmission rate is the IPM's own expression of it, `np.exp()` included, so it is worked out for each state on each day. The travel is a matrix of the share of time spent in each other state, one line of NumPy from the commuting data. In the original, the IPM is declared (in SymPy), and the two movement clauses are Python methods that draw the travelers each day.

## Findings

- **The importer flattens the humidity.** `ss.import_from()` on this RUME takes a parameter that varies both in time and by place at each place's mean, and lists that as untranslated, so its runs peak a week late (day 102, against 95), with the seasonal fall in transmission lost. v4 can say this parameter as it is, as `model.py` does, so the importer could write it as a time series for each place.
- **Movement is the expected number of travelers.** The original draws its commuters (binomially, 90% of them) and its dispersers (as Poisson, a tenth of the mean number of commuters each way) afresh each day. Starsim moves the expected share. At most 2.1% of a state's people travel each day (from Maryland, mostly to Virginia), and the runs agree.
- **The notebook's data.** It takes the population from `acs5.Population()`, which needs a Census API key, and the commuters from `commuting_flows.Commuters()` (the ACS commuting flows for 2011 to 2015). Here both come from the data that epymorph bundles for this example (`epymorph.data.pei`, kept as `original/pei_data.py`), copied from Pei's data files, as the humidity already does in the notebook, so the comparison runs offline and needs no key. The ADRIO's commuters are 2% to 4% more than the bundled ones; the centroids that the notebook also passes are not used by the Pei IPM or MM.
- **Two kinds of travelers are one matrix.** The commuters and the dispersers leave and return at the same steps, so in Starsim they add up to one matrix of shares of time, and the model doesn't need to keep them apart.

## What it exercises

- A parameter that varies both in time and by place (the humidity), from data, and a transmission rate that is a nonlinear function of it
- An SIRS with waning immunity
- Movement from a matrix of commuting data, with two kinds of travelers, for part of each day
- An epidemic seeded in one place that reaches the others in turn

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/usage.py`: the notebook's cells that build the RUME and run it, unchanged, at tag `v1.2.0` of the source repository
- `original/ipm_pei.py`, `original/mm_pei.py`, and `original/pei_data.py`: the IPM, the MM, and the data from epymorph's library that the notebook uses, unchanged
- `original/states.csv` and `original/humidity.csv`: the same data as tables, written by `fetch.py`, which the Starsim version reads
- `run.py`: runs it and writes `reference/`, with `export.py` in the framework's environment
- `reference/results.csv`: the mean and 5% to 95% range of 20 runs, daily, for `S`, `I`, `R`, and `new_infections` in all, and `I`, `R`, and `new_infections` in each state (as `I_FL`)
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (GPL-3.0)

`export.py` runs the notebook's own text, changed in two ways without changing the file: the three ADRIOs are replaced by the bundled data, and it stops before the run, which is then made with the seeds 1 to 20 (the notebook's own seed is 1, which is the run timed first).

## The model

- **Places:** the six states, with Pei's populations (Florida 18,811,310, of 56,434,386 in all)
- **Compartments:** `S`, `I`, `R`
- **Transitions:** `S` to `I` at `beta*S*I/N` among the people present in a state, with `beta = (exp(-180*H + log(2.0 - 1.3)) + 1.3)/D` and `H` the absolute humidity in that state on that day; `I` to `R` at `I/D`; and `R` to `S` at `R/L`
- **Parameters:** `D = 4` days infectious, `L = 90` days immune, and the daily humidity of 2015 in each state
- **Movement:** each day, of each state's commuters (from the commuting matrix `C`), a binomial draw with `move_control = 0.9` travel, split between the destinations in proportion to `C`; and a Poisson number `theta = 0.1` times `(C[i,j] + C[j,i])//2` travel from state `i` to `j`. Both leave for the first step of the day, a third of a day, and come back for the second
- **Initial conditions:** 10,000 infectious people in Florida
- **Time:** 150 days from 1 January 2015, in two steps a day

## Lines of model code

22, counting the lines of `original/usage.py` that are not blank, comments, or imports. The IPM and MM are 21 and 62 lines more, counted in the same way (as for `model.py`, without docstrings).

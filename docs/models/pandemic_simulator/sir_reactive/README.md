# Pandemic Simulator: SIR with a reactive intervention

The framework's declarative teaching example, `example_parameter_uncertainty_declarative_model`: a closed SIR in one zone of 1,000,000 people, with a measure that responds to prevalence, run with and without the measure and with three uncertain inputs. See the [review](../../../approaches/pandemic_simulator.md).

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`, a run of the original with the central value of every input.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 99 | 8 | Most of the original's lines are the declaration that also serves the web form and model card, which the Starsim version doesn't have |
| One run | first 0.36 s, rerun 0.0069 s | first 0.081 s, rerun 0.066 s (Rust) | Each is one run with the measure, and includes results. A first run excludes imports; the original's includes compiling with JAX, and Starsim's uses kernels already compiled. A rerun is 10 times faster in the original, whose whole loop is compiled, while Starsim steps this model in Python to check the measure's condition, which also rules out JAX |
| Results, without the measure | | | **Agree** to 1.2e-5 of the population on every day (6 people in `I`), with a daily RK4 step against an adaptive solver |
| Results, with the measure | Peak 198,528 on day 59; 860,705 infections | Peak 198,673 on day 58; 860,467 infections | **Agree** to 4.2e-3 of the population, or 1.2e-3 with `dt=ss.days(0.1)` and 860,695 infections. The difference is when the threshold is noticed: Starsim checks it once a step |
| Results, 20 draws (median at each time) | 23.9% to 16.5% at the peak, 7 days later, and about 938,000 to 844,000 infections, in one run; the guide on interventions gives 25% to 19%, and 939,000 to 865,000 | About 25% to 18%, 8 days later, and 940,000 to 857,000 infections, with 200 draws | **Consistent**: inside the original's 95% band on every day. The original's draws have no seed, so two of its runs differ by this much |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `3e5318d8`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The measure is `ss.modify()` with a condition on a count, and the solver is `solver='ode'`. The original's solver is adaptive, and this one takes fixed daily steps.

## Findings

- **A median of runs is not a run.** The 25% in the guide is the peak of the median curve over draws of `beta`. With the central `beta` the peak is 30%, and the draws peak at different times, so the median curve is lower. A comparison with these numbers has to summarize in the same way.
- **The release threshold.** The config sets a trigger at 2% and a release at 1%, but the guide says that the default solver does not carry the status between steps, and the original's results confirm it: the decline slows as soon as prevalence falls below 2%. So the translation has no release. With `until=sir.I.n <= 10_000`, the release as configured, the peak is the same, with 857,944 infections rather than 860,467.
- **Uncertainty.** `ss.parallel(sim, priors=True)` draws bounded parameters afresh, but not on a Latin hypercube, and the draws can be given directly as `priors=`. The two factors of the measure aren't parameters here, so `compare.py` makes its sims itself.

## What it exercises

- Frequency-dependent transmission, with a recovery period given in days
- A measure switched by prevalence
- Parameter uncertainty on the disease and on the measure
- Paired runs with and without the measure

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/model.py` and `original/example-config.json`: the example, unchanged, at commit `5ec712b` of the source repository
- `original/central-config.json`: the same config with no uncertain inputs
- `run.py`: runs it and writes `reference/`, with `export.py` in the framework's environment
- `reference/results.csv`: `S`, `I`, and `R` on each day, with the measure and without
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (Apache 2.0)

## The model

- **Compartments:** `S`, `I`, `R`, with cumulative totals added by the framework
- **Transitions:** `S` to `I` at `beta*S*I/N`, and `I` to `R` at `1/10` per day
- **Parameters:** `beta = 0.3` per day (uncertain, 0.2 to 0.4), adherence 50% (40% to 60%), reduction 50% (45% to 55%)
- **Initial conditions:** 0.01% of 1,000,000 infectious, so 100 people
- **Time:** 1 January to 31 December 2026, so 364 days

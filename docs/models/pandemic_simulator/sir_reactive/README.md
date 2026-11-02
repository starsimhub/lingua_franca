# Pandemic Simulator: SIR with a reactive intervention

The framework's declarative teaching example, `example_parameter_uncertainty_declarative_model`: a closed SIR in one zone of 1,000,000 people, with a measure that responds to prevalence, run with and without the measure and with three uncertain inputs. See the [review](../../../approaches/pandemic_simulator.md).

**Status: not yet in the benchmark.** The original has not been run here, so this folder has no `reference/`, `run.py`, or `meta.yaml`, and the benchmark skips it. The check below is against the numbers its authors published, which is weaker than a comparison at every time point.

`model.py` is the Starsim version, and `compare.py` checks it against the published numbers.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Size | `model.py` of 188 lines, of which about 110 are a declaration that also serves the web form and model card, and a config of 91 lines | 6 lines of model | Not a fair count: the original's lines include what a web platform needs, and the Starsim version has no form. The rules for counting lines have not been applied |
| Results, central values, with the measure | Not published | Peak 19.9% on day 58; 860,467 infections | From `model.py` |
| Results, 20 draws (median at each time), peak | 25% to 19%, about 10 days later | 24.6–25.9% to 17.8–18.9%, 7–11 days later | **Consistent.** Five sets of 20 draws; 400 draws give 25.2% to 18.0%, 8 days later |
| Results, 20 draws, infections | About 939,000 to 865,000 | 939,751–941,209 to 847,189–868,337 | **Consistent**, read in the same way |

The published row is from [the guide on interventions](https://github.com/WHO-Collaboratory/pandemic-simulator-compartment/blob/main/docs/guides/interventions.md), which does not give the seed of its draws. The ranges are the spread across the five sets. Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4-nov02e` branch, commit `24a36055`).

## What was declared and what was not

Everything is declared. The measure is `ss.modify()` with a condition on a count, and the solver is `solver='ode'`. The original's solver is adaptive, and this one takes fixed daily steps.

## Findings

- **A median of runs is not a run.** The 25% in the guide is the peak of the median curve over draws of `beta`. Each run peaks near 30% at the central `beta`, later or earlier in others, so the median curve is lower than the median peak. A comparison with these numbers has to summarize in the same way.
- **The release threshold.** The config sets a trigger at 2% and a release at 1%, but the guide says that the default solver does not carry the status between steps, so the release is not used. With no memory, the measure is on whenever prevalence is at least 2%. With the release, a separate fine-step calculation gives the same peak, 857,986 infections rather than 860,760, and 90 days under the measure rather than 80. In Starsim, `until=` on `ss.modify()` gives the release (857,944 infections), and the translation leaves it out only to match the original.
- **Uncertainty.** `ss.parallel(sim, priors=True)` draws bounded parameters afresh, but not on a Latin hypercube, and the draws can be given directly as `priors=`. The two factors of the measure aren't parameters here, so `compare.py` makes its sims itself.

## What it exercises

- Frequency-dependent transmission, with a recovery period given in days
- A measure switched by prevalence
- Parameter uncertainty on the disease and on the measure
- Paired runs with and without the measure

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against the published numbers
- `original/model.py` and `original/example-config.json`: the example, unchanged, at commit `5ec712b` of the source repository
- `LICENSE`: the upstream license (Apache 2.0)

## The model

- **Compartments:** `S`, `I`, `R`, with cumulative totals added by the framework
- **Transitions:** `S` to `I` at `beta*S*I/N`, and `I` to `R` at `1/10` per day
- **Parameters:** `beta = 0.3` per day (uncertain, 0.2 to 0.4), adherence 50% (40% to 60%), reduction 50% (45% to 55%)
- **Initial conditions:** 0.01% of 1,000,000 infectious, so 100 people
- **Time:** 1 January to 31 December 2026, so 364 days

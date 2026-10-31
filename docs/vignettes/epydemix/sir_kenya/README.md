# epydemix SIR in Kenya, in Starsim

The translation of [models/epydemix/sir_kenya](../../../models/epydemix/sir_kenya). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 7 | 14 | Not counting the loading of the data would be 12. The original has the model predefined and the population bundled |
| One stochastic run | first 0.0076 s, rerun 0.007 s | first 0.016 s, rerun 0.0011 s (Rust) | In process, without imports or loading the data. Both are the time of one run, with the 100 runs of the original taking about 0.6 s |
| Results | | | **Agree** (peaks within 1%, a day apart at most, final size within 0.1 of a percentage point): the mean of 100 runs peaks 0.4% higher than the original, a day sooner, and the final size is the same (99.63%). On any one day the difference is up to 6% of the peak, since the rise is a day ahead (see the findings) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `4473e253`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The population and the contact matrices are read from the file that the original's run wrote, so that the two models are the same.

## Findings

- **Longer than the original.** epydemix has the SIR model predefined and the population bundled, so the whole example is seven lines, which is hard to beat. Starsim now bundles populations and contact matrices too: `ss.contacts('Kenya')` with `people=ss.people('Kenya', year=2020)` needs no file and removes the loading lines. This vignette does not use them because they are a different population, 52.2 million in Starsim's data for 2020 against 55.9 million in epydemix's, so it would not be a test of the same model.
- **`substeps=1` is needed.** epydemix takes one chain-binomial step a day. Starsim's chain binomial now takes substeps by default, so that no more than about a tenth of a compartment leaves in one, and without `substeps=1` the peak comes on day 36 rather than 39 and is 54.0% rather than 54.7%, against the original's 54.5% on day 40. The default is more accurate as an approximation to continuous time; the original's model is discrete by design.
- **Fixed: a result of many runs can be selected by age group.** `res.I.select(age='0-4')` now works on the runs together.
- **Fixed: aging can be switched off.** Stratifying by age turns aging on in a compartmental run; `use_aging=False` turns it off, which is what the original assumes.
- **Ten infected, not eight.** The original spreads ten infections over the age groups and rounds each down, starting with eight. Starsim starts with ten, which is why its peak comes up to a day sooner.

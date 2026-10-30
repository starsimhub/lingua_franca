# flepiMoP two populations, in Starsim

The translation of [examples/flepimop/seir_2pop](../../../examples/flepimop/seir_2pop). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 42, plus 10 lines of CSV | 16 |  |
| One run | 8.4 s | 0.040 s, or 0.0008 s for a repeated run | The original can run only as a whole command, so its first run and rerun are both that command, about 7 s of which is compiling, on every run |
| Results | | | **Agree exactly** (tolerance 1e-6 people): every compartment in both provinces, on every day, within 3e-12 people |

Measured on 30 October 2026 with Starsim 4.0.0 (the `v4` branch, commit a1e3faab) on a 20-core x86-64 Linux machine.

## What was declared and what was not

Everything is declared. The populations and the travel between them are written in the script; the original keeps them in three CSV files, which is easier to change for many places.

## Findings

- **A third way of coupling places.** In flepiMoP, people who travel are exposed to the residents of the place they go to, and do not infect anyone there. Starsim's commuting has them do both, which brought the epidemic to the small province 12 days sooner. `ss.geo.Mobility(kind='visit')` matches the original exactly.
- **Half a day is hard-coded.** flepiMoP multiplies the travel matrix by 0.5; here that is written out.
- **`substeps=1` gives the same steps.** The original takes one RK4 step a day. By default Starsim subdivides a step when rates are high, which gives a difference of 0.007 people here; with `substeps=1` it takes the same steps as the original and they agree to 12 digits.

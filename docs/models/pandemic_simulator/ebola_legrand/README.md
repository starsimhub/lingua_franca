---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Pandemic Simulator: Ebola with community, hospital, and burial transmission

The framework's `ebola_seihfr_burial_legrand_model`, its port of Legrand et al. (2007): an SEIHFR model of the 1995 outbreak in Kikwit, in 200,000 people, with measures from 4 May 1995. See the [review](../../../approaches/pandemic_simulator.md).

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`, a run of the original with the central value of every input.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 306 | 30 | Most of the original's lines are the declaration that also serves the web form and model card |
| One run | first 0.31 s, rerun 0.0059 s | first 0.021 s, rerun 0.0014 s (Rust) | Each is one run with the measures, and includes results. A first run excludes imports; the original's includes compiling with JAX, and Starsim's uses kernels already compiled. A rerun solves in about the same time on each side (the original's solve alone is 0.98 ms); most of the original's rerun is building its results |
| Results, without the measures | 17,044 left in `S` | 17,044 left in `S` | **Agree** to 2.9e-6 of the population on every day, with a daily RK4 step against an adaptive solver |
| Results, with the measures | 179,445 left in `S` | 179,407 left in `S` | **Agree** to 1.9e-4 of the population, or 3.1e-7 with the original in float64 (`JAX_ENABLE_X64=1`), where it leaves 179,407. See the findings for the difference |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `5a43500f`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. The split rates are expressions of parameters, so they follow any change to `theta` or `delta`; the measures are `ss.modify()` with a start date. The original computes the force of infection and every exit from `I` and `H` by hand in `equation()`, as its schema can't state them.

## Findings

- **A rounding error in the original moves its measures.** It compares `start_date_ordinal + t` with the start date, and JAX's default float32 resolves a number near 728,000 only to 1/16 of a day, so a measure can start up to that much away from its date. That is the whole difference in the table: 38 fewer people infected, and it does not shrink with a smaller step in Starsim. Every dated measure in the framework is compared in this way, in any model; the size of the error depends on the epidemic at that moment.
- **Checked against the source's arithmetic, not the paper.** The derived rates recover what they should: 80% hospitalized, a case fatality of 81%, and R0 of 2.69 (0.50 community, 0.42 hospital, and 1.77 burial), against the 2.7 in the original's notes. The paper itself was not available when this was written, so the equations are compared with the original's code only.
- **Larger than the outbreak.** The original's notes say that the epidemic is far larger than the 315 cases observed, as the paper's own mean-field version is. The translation keeps this.

## What it exercises

- A force of infection summed over three states with their own coefficients
- Exits split by rates derived from target shares
- Three measures with a date, one reducing a rate and two removing it
- Paired runs with and without the measures

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/model.py` and `original/example-config.json`: the model, unchanged, at commit `5ec712b` of the source repository
- `original/central-config.json`: the same config with no uncertain inputs
- `run.py`: runs it and writes `reference/`, with `export.py` in the framework's environment
- `reference/results.csv`: each state on each day, with the measures and without
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (Apache 2.0)

## The model

- **Compartments:** `S`, `E`, `I` (in the community), `H` (in hospital), `F` (dead, not yet buried), `R`
- **Transitions:** `S` to `E` at `(betaI*I + betaH*H + betaF*F)*S/N`; `E` to `I`; `I` to `H`, `R`, or `F`; `H` to `R` or `F`; and `F` to `R`
- **Parameters:** `betaI = 0.084`, `betaH = 0.113`, `betaF = 1.093` per day; incubation 7 days, burial 2 days, onset to hospital 5 days, infectious period 10 days, onset to death 9.6 days; 80% hospitalized and 81% case fatality
- **Measures:** from 4 May 1995, `betaI` falls by 12%, and `betaH` and `betaF` to zero
- **Initial conditions:** 0.0015% of 200,000 infectious, so 3 people
- **Time:** 6 January 1995 to 6 January 1996

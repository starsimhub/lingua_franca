# EMULSION SIR, in Starsim

The translation of [examples/emulsion/sir](../../../examples/emulsion/sir). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 81 (compartments), 86 (individuals) | 10 | The original is one YAML file per paradigm; here one model is run two ways |
| One compartmental run | 0.81 s | 0.017 s | The original runs as a whole command, so its first run and rerun are the same command, and both include starting Python and reading the model (about 0.7 s; it reports 0.06 s for the run itself). Starsim's exclude the import |
| Results, compartments | | | **Agree.** Mean of 200 runs: a peak of 38 infectious on day 18, against 37 on day 18; 86 recovered at the end, against 85 (`compare.py` asks for 1.5 and 2 animals). This needs whole-day steps, `substeps=1` |
| Results, individuals | | | **Agree, within chance.** Mean of 200 runs: a peak of 35 on day 18, against 37 on day 19; 79 recovered at the end, against 81, with 21% of runs dying out early, against about 19% (`compare.py` asks for 3 and 6 animals) |

Measured on 30 October 2026 with Starsim 4.0.0 (the `v4` branch, commit a1e3faab) on a 20-core x86-64 Linux machine.

## What was declared and what was not

Everything is declared, once. The paradigm is the `solver=` argument of the sim, where the original changes `aggregation_type` and adds a level and prototypes to the file.

## Findings

- **Initial numbers (fixed).** `init_n=dict(I=1)` starts exactly one animal infected, as agents and as compartments.
- **Dying out (better).** This version once had noticeably more runs die out early as agents than the original. The gap is now within the chance of 200 runs.
- **Whole days have to be asked for.** Starsim's chain binomial takes smaller steps by default, which gives 88 recovered at the end, against 85. `substeps=1` takes each day whole, as EMULSION does.
- **No hybrid.** The original's third form (groups that hold individuals) has no counterpart, and for this model none is needed: its three forms are statistically the same.
- **The original documents more.** About a quarter of the YAML is names, descriptions, and colors, which is why it is longer, and a reader of the file learns more from it. Here `doc=` on a parameter can do some of this.

# MEmilio SECIR, in Starsim

The translation of [examples/memilio/secir](../../../examples/memilio/secir). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 44 | 14 | |
| One run | first 0.00053 s, rerun 0.00003 s | first 0.021 s, rerun 0.0021 s (Rust) | Neither counts starting Python or importing. MEmilio's solver is C++ code built in advance, so its first run has little to do |
| Results | | | **Agree.** Within 67 people of 83,000 at every time, which is the error of the reference itself (it is interpolated between steps of about two days); deaths within 0.4. `compare.py` allows 73 people and 0.5 deaths |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared. Each severity step is one transition with two destinations and a probability; deaths leave the model, so they are counted from the flow and the people who mix are the ones alive, as in the original.

## Findings

- **Fixed: a value that varies in time was held for a whole step.** The original lowers contacts smoothly over day 29, along half a cosine. `ss.timeseries(..., mode='cosine')` says the same, and the ODE solver reads it at each stage of a step, so the translation no longer gives that day its average by hand.
- **Two states left out.** The original has two "confirmed" states that nothing flows into; they are not in the translation.
- **The dead are a flow, not a state.** The number dead is `res.death.cum`.

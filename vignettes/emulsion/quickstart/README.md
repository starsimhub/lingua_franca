# EMULSION quickstart, in Starsim

The translation of [examples/emulsion/quickstart](../../../examples/emulsion/quickstart), EMULSION's showcase: 100 animals, each with an age group, a gestation cycle, and a health state, with births, abortions, maternal protection, vertical transmission, and a seasonal quarantine with a capacity. The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 280 | 53 | Long lines count twice. About 80 of the original's lines are descriptions, names, and colors |
| One run | first 1.4 s, rerun 1.3 s | first 0.28 s, rerun 0.24 s (Numba) | The original runs as a whole command, so its first run and rerun are the same command, and both include starting Python and reading the model (about 0.7 s). Starsim's exclude the import |
| Results, as written | | | **Do not agree.** The mean of 50 runs ends with 55 animals, against 65, and every count of adults is low from early on (finding 1). Up to step 13 the timing is right apart from the quarantine, which starts two steps sooner in EMULSION (finding 5). `compare.py` asks for 13 animals, so it records this miss and fails if it grows |
| Results, with EMULSION's quarantine | | | **Do not agree.** The quarantine now matches (`Q` within 1.3), and births come on time, but the herd is still too small: 70 animals against 76 at step 53, and 55 against 65 at step 105 (finding 1) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

## What was declared and what was not

Declared: the three state machines, as three modules on the same agents (`life`, `growth`, `health`); every rate; the minimum stays (`after=`) and the deaths during them (a rate times `E.time < ...`, EMULSION's `escape`); the fixed stays in `G` (240 days) and `Q` (30 days); the force of infection, and the quarantine's room (`Q.n < 20`) in the rate of detection; who each conditional transition applies to (`where=`: adults for `J` to `A` and for conception, infectious mothers for abortion); one newborn for each farrowing (`ss.birth(per=farrowing)` in each module), infected or not by the mother's health (`ss.mother()`); the deaths; the quarantine period, as a time series of dates; the initial conditions and ages; and the weekly step in days.

Not declared (each marked in `model.py`):

- **"As soon as"**: `J` to `A` happens on the first step an animal is old enough, written as a rate of 10⁹ a day with `where=`
- **The animals' time of entry at the start**, set to the step before the first in a small subclass (finding 3)
- **Stays in whole steps**: `whole()` rounds a stay as EMULSION does

Left out: `nb_total_abortions`, the abortions of the living animals. The original counts these on each animal. Here the `abortion` result counts all of them, dead or alive, so `compare.py` does not compare it. The original says this more easily.

## Findings

1. **The herd is too small, because of a Starsim change. Open.** As agents, Starsim now gives people half a step of the rates out of a state in the step they arrive in, since on average they arrived halfway through it (decided on 25 October; see `design/10-execution.md`). At a step of a week that matters: with a rate of 0.01 a day, 3.4% leave in the step they arrive, where EMULSION has none leave, since its steps are discrete. So animals pass through `I` and `R` sooner and die sooner, and the adults fall behind from the first weeks (78 against 80 at step 13, 59 against 63 at step 27), which leaves 7% fewer pregnancies, and the gap grows with each generation. This has been tested in three ways. With that half step switched off in a test (not in Starsim itself), this same model agrees: 76 animals against 76 at step 53, and 66 against 65 at step 105, with the total never more than 3.1 off (mean of 50 runs). The earlier step-by-step version of this model, ported as it stood, is just as low (51 against 65, mean of 10 runs), so the declared rewrite did not lose the agreement. And smaller steps do not help (50 or 49 animals at the end, at a half and a quarter of the step, with the stays kept as they are): the half step already makes Starsim follow continuous time, and it is EMULSION's whole steps that it no longer matches. The half step is right for steps that stand for continuous time, but not for a model that is defined in discrete steps. Suggested: an option for whole-step arrivals, as `substeps=1` is for the chain binomial.
2. **Minimum stays (fixed, with one difference).** `after=` and `E.time` replace the function this version once used. EMULSION rounds a stay to whole steps (10 days is one step of 7), while `after=ss.days(10)` means two steps, so `whole()` is needed to match. With the stays unrounded, the epidemic comes a step late.
3. **The start is the same as the first step. Open.** Agents start with entry time 0, the same as those who move during the first step, so a stay from the start lasts a step longer than the same stay entered later. In EMULSION the initial state is before the first step. Without the small subclass, every conception and birth comes a week late. Suggested: give initial agents an entry time before the first step.
4. **Conditions, offspring, and births (fixed).** `where=` takes a state of another module, and `ss.birth(per=)` with `ss.mother()` replaces the subclass that made newborns by hand. Offspring in three modules need the module with the farrowing first in the sim, or the newborns are counted a step late in the others (and `J` can read -1 for a step: a newborn that dies in its birth step is taken off the count before its birth is added, a small bug in Starsim's counts). This changes the order of processes from EMULSION's, with no other effect seen.
5. **The quarantine period differs by EMULSION's rounding.** EMULSION turns April 1 into whole steps by rounding down (step 12, March 26) and applies the condition at the end of the step, so detection starts on what Starsim calls the step of March 19; its year is 52 steps. The model keeps the dates as written, and `compare.py` also runs it with the window as EMULSION applies it. Not a Starsim problem.
6. **Smaller things.** `use_aging=True` has to be given for agents to age. `adult_age` is given twice in the original YAML; the second value (30 days) is used, as EMULSION does.

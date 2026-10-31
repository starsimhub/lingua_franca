# EMULSION: the quickstart model

A stochastic, hybrid (individual-based, grouped) model of 100 animals over two years in weekly steps, each animal with three state machines at once: an age group, a gestation cycle, and a health state. It is the model EMULSION's authors wrote "to provide an overview of several EMULSION features", shipped as `models/quickstart/quickstart.yaml` with EMULSION 1.1.1 and used in its quickstart tutorial.

This is EMULSION's showcase: 100 animals, each with an age group, a gestation cycle, and a health state, with births, abortions, maternal protection, vertical transmission, and a seasonal quarantine with a capacity. `model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 280 | 53 | Long lines count twice. About 80 of the original's lines are descriptions, names, and colors |
| One run | first 1.6 s, rerun 1.6 s | first 0.31 s, rerun 0.29 s (Rust) | The original runs as a whole command, so its first run and rerun are the same command, and both include starting Python and reading the model (about 0.7 s). Starsim's exclude the import |
| Results, as written | | | **Do not agree.** The mean of 50 runs ends with 55 animals, against 65, and every count of adults is low from early on (finding 1). Up to step 13 the timing is right apart from the quarantine, which starts two steps sooner in EMULSION (finding 5). `compare.py` asks for 13 animals, so it records this miss and fails if it grows |
| Results, with EMULSION's quarantine | | | **Do not agree.** The quarantine now matches (`Q` within 1.3), and births come on time, but the herd is still too small: 70 animals against 76 at step 53, and 55 against 65 at step 105 (finding 1) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `4473e253`), on a 20-core Linux machine.

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

## What it exercises

Much more than the [sir](../sir) example, which has one state machine and nothing else:

- Three state machines on the same individuals (`age_group`, `life_cycle`, `health_state`), each run as a process in a given order (aging, then the life cycle, then infection), and each with its own grouping
- A grouping on two state machines at once (`life_cycle` is grouped by `life_cycle` and `age_group`)
- An individual variable (`age`), updated on every step an animal stays in a state (`on_stay`), and a transition conditioned on it (`J` to `A` when `age` reaches `adult_age`)
- Conditions on another state machine's state (`NG` to `G` only for adults, `cond: is_A`; abortion only for infectious mothers, `escape: is_I`)
- Minimum stays in a state (`duration`), which hold back every other way out of the state until they are over, and `escape` transitions, which are allowed only until then
- A transition that takes everyone whose stay is over (`amount-all-but: 0`), probabilities (`proba`) and rates in the same model, and probabilities per day turned into probabilities per week
- Births on crossing a transition (`on_cross: produce_offspring`): each farrowing gives one newborn, which is infected (with probability 0.3 if the mother is `E`, `I`, or `Q`) or else protected by maternal antibodies (`M`), and which gets its age group, life cycle, and age from a prototype
- A count kept for each individual on crossing a transition (`set_var: nb_abortions`), and summed over the living at the level of the population (`aggregate_vars`)
- A calendar: detection into quarantine only from April 1 to September 1 of each year (`when: quarantine_period`)
- A rate that depends on a count through a comparison: detection stops while 20 or more animals are in quarantine (`StrictLessThan(total_Q, quarantine_size)`)
- Deaths that remove the animal (`autoremove`), from six health states at two rates
- Initial ages drawn from a distribution (`randint(0, adult_age)`)

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/quickstart.yaml`: the model, unchanged, from the source distribution of EMULSION 1.1.1 (`models/quickstart/`)
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 200 runs, at each of steps 0 to 105 (days 0 to 735): the count in each state (`J`, `A`, `NG`, `G`, `M`, `S`, `E`, `I`, `R`, `Q`; `D` is always empty, since the dead are removed), `total_population`, and `nb_total_abortions`
- `reference/timing.json`: the times of a first run and a rerun, each as a whole command
- `meta.yaml`: where it came from
- `LICENSE`, `NOTICE`: the upstream license (Apache-2.0) and its notice

## The model

- **Time:** steps of 7 days (`delta_t: 7`) for 730 days, which EMULSION runs as 105 steps (to day 735), from January 1. Rates are per day.
- **Age group:** `J` (juvenile) to `A` (adult) on the first step on which `age` is at least `adult_age`. Every animal's `age` goes up by 7 days at the start of every step, before the test.
- **Life cycle:** `NG` (not gestating; a minimum stay of 90 days) to `G` at 0.05 a day, for adults only; `G` (gestating; 240 days) back to `NG` when the 240 days are over, with one newborn. An infectious mother may abort before then, with a chance of 20% over a gestation (`1 - 0.8^(1/240)` a day), which adds one to her `nb_abortions`.
- **Health:** `M` (maternal protection, a minimum stay of `adult_age`) to `S` at 0.04 a day; `S` to `E` at `0.1 × I/N` a day; `E` (a minimum stay of 10 days) to `I` at 0.3 a day; `I` to `R` at 0.01 a day; `I` to `Q` at 0.01 a day during the quarantine period while there are fewer than 20 in `Q`; `Q` (30 days) to `R` when they are over; `R` to `S` at 0.01 a day. Deaths at 0.002 a day from `M`, `S`, and `R`, and 0.004 a day from `E`, `I`, and `Q`, where the deaths from `M`, `E`, and `Q` are `escape` transitions, so happen only during the minimum stay.
- **Start:** 90 animals in `S` and 10 in `I`, all `J` and `NG`, with ages drawn from `randint(0, adult_age)`.

Some details that matter for a translation:

- **`adult_age` is given twice** in `parameters`, as `365*2` and then as `30`. YAML keeps the second, so adults are 30 days old, the maternal protection lasts 30 days, and the initial ages are 0 to 29 days. The first animals become adults within five weeks.
- **A minimum stay is rounded to whole steps** (`round(duration/delta_t)`: 13 steps for 90 days, 34 for 240, 4 for 30, and 1 for 10), and counted from the step an animal enters the state. The animals present at the start entered before the first step, so their first stay in `NG` ends on step 13.
- **The calendar is in whole steps.** EMULSION converts the dates of the quarantine period to steps by rounding down (April 1 is day 90, so step 12) and its year to 52 steps. Detection is possible on steps 12 to 34 and 64 to 86 (shown by `view_quarantine` in the output).
- **Within a process, transitions are worked out from the state at its start**, then applied together; the processes run one after the other, so the life cycle sees this step's adults and the infection sees this step's newborns.
- **Newborns are made during the life cycle process**, so they take part in the infection process of the step they are born in.
- **The deaths of a step are removed at the end of the infection process**, so `total_population` is the number alive at the end of the step.

## Results

The mean of 200 runs. The epidemic peaks at once, with about 53 infectious on step 11, and dies down to about 12 by step 31 as animals recover and die; the population falls to about 46 by step 46. The first farrowings are on step 47, which brings the population back to about 77 by step 53, with up to 27 newborns at a time protected by maternal antibodies. By the end there are about 66 animals, 18 of them infectious, and on average 2.9 abortions among the living.

`run.py` uses `--seed 1`, so it writes the same results each time.

## Lines of model code

280, counting every line of `quickstart.yaml` that is not blank or a comment (including the two YAML document markers); no line is over 100 characters. About 80 of them are descriptions, names, and colors (`desc`, `name`, `fillcolor`, `model_info`, and the continuation lines of descriptions that span lines). The file is 468 lines long, most of the rest being comments and ASCII-art section banners.

## Timing

One run takes 1.46 s as a command (`emulsion run quickstart.yaml --runs 1`), of which EMULSION reports about 0.52 s as the simulation; the rest is starting Python and reading the model.

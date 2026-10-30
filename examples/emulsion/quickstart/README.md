# EMULSION: the quickstart model

A stochastic, hybrid (individual-based, grouped) model of 100 animals over two years in weekly steps, each animal with three state machines at once: an age group, a gestation cycle, and a health state. It is the model EMULSION's authors wrote "to provide an overview of several EMULSION features", shipped as `models/quickstart/quickstart.yaml` with EMULSION 1.1.1 and used in its quickstart tutorial.

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

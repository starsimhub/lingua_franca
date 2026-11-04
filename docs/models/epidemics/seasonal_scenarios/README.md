---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# epidemics: seasonal transmission with interventions and vaccination

The default SEIR-V of epidemics' "Get started" vignette (the UK in three age groups, mixing by a contact matrix from POLYMOD, with R0 = 1.3), with a transmission rate that varies through the year, `beta * (1 + sin(πt/91.25))`, so that it peaks twice, under the three scenarios of the vignette on time dependence: no intervention; three overlapping cuts in contacts (schools closed from day 50 to 120, workplaces from day 65 to 90, and schools partly reopened from day 120 to 180), each a reduction for each age group; and vaccination of people aged 40 and over between the waves, from day 120 to 220. This is the vignette that composes the most of epidemics' scenario elements: a population, time dependence, contact interventions, and a vaccination. See the [review](../../../approaches/epidemics.md).

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`, a run of the vignette.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 76 | 24 | Both count their data: 16 of the original's lines make the contact matrix and demography from the survey, and 2 of Starsim's give them as numbers |
| One run | first 0.07 s, rerun 0.011 s | first 0.074 s, rerun 0.047 s (Rust) | The scenario with the interventions: the vignette's call of `model_default()` that makes `data_npi`, which includes checking its inputs and making its table of results. Starsim is 5 times slower, because of its modifiers (finding 3); with none, a run takes 1.1 ms. The vaccination scenario takes 147 ms (finding 4) |
| Results, baseline | | | **Agree** to 9.2e-4 of each state's largest value, in total and in each age group, on every day. `I` peaks at 2,377,511 on day 275 (original 2,378,561 on day 275). The difference is the original's: it gives odin the seasonal factor at whole days, and odin interpolates linearly between them. With the same interpolation and steps of a quarter of a day, Starsim agrees to 1e-4 in total. `compare.py` allows 1e-3 |
| Results, with the interventions | Peak 1,374,393 on day 279; 8,364,644 recovered by day 365 | Peak 1,383,754 on day 279; 8,424,253 recovered | **Agree** to 8.6e-3 of each state's largest value. The difference is how overlapping cuts combine: epidemics adds them and Starsim multiplies them (finding 1). With the cuts added by hand, Starsim agrees to 1.6e-3, and its peak is 1,374,560. `compare.py` allows 1e-2 |
| Results, with vaccination | Peak 1,699,837 on day 276; 2,943,844 vaccinated | Peak 1,697,573 on day 276; 2,943,843 vaccinated | **Agree** to 1.4e-3 of each state's largest value. `compare.py` allows 2e-3 |

Measured on 3 November 2026 with Starsim 4.0.0rc2 (the `v4` branch, commit `d0107e93`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: five states, three transitions, a stratification by age, the contact matrix, the seasonal factor in the transmission rate (`ss.seasonal`), each cut in contacts as two modifiers (`ss.modify`) of the susceptibility and the infectiousness of each age group, made by a three-line function, and the vaccination as a delivery that moves a fixed number of people a day from `S` to `V` (`ss.Delivery(move=S >> V, capacity=...)`). The scenarios are the baseline sim with each set of interventions (`baseline.new(interventions=...)`). The whole intervention scenario runs in the kernels; the vaccination does not (finding 4).

| Original | Starsim |
|---|---|
| `mod_beta <- function(time, x, tmax = 365/4) x + x*sinpi(time/tmax)`, given as `time_dependence` | `ss.seasonal(amplitude=1, peak=ss.days(365/8), period=ss.days(365/2))`, the same curve as a cosine |
| `intervention(type = "contacts", time_begin, time_end, reduction)`, three of them, combined with `c()` | `contacts(start, stop, reduction)`: `ss.modify()` of `seirv.rel_sus` and `seirv.rel_trans` by `ss.by(age=1 - reduction)` |
| `vaccination(nu = matrix(0.001, nrow = 3), time_begin, time_end)`, with zero-length windows for the two younger groups | `ss.Delivery(move=S >> V, capacity=ss.perday(0.001*N[2]), who=ss.ppl.age >= 40, start=120, stop=220)` |
| A call of `model_default()` for each scenario, and `new_infections()` of each | `baseline`, `sim`, and `vaccination`, with new infections as the result `seirv.infection` |

## Findings

1. **No way to say that effects add (disagreement of 0.7%; open).** epidemics adds the reductions of interventions that overlap, and caps the total at 1; its design-principles vignette says that additive effects were considered easier for users to understand. So here cuts of 10% and 1% give 11%, not 10.9%. Starsim's modifiers of a quantity multiply, so from day 65 to 90 the youngest group's contacts are cut by 10.9% and the others' by 20.8%, against 11% and 21%, and the epidemic is 0.7% larger. `add=` cannot be used instead: it is refused on `rel_sus` and `rel_trans` ("would replace each person's own value"), and is for parameters and inflows. Adding the cuts by hand, as one modifier for each period between their starts and stops, agrees (`compare.py` does this), but it gives up stating each intervention on its own, which is the point of epidemics' elements. Suggested change, as the review of epidemics suggests: let the rule be stated for a set of modifiers, for example `ss.modify(..., reduce=0.1)` with reductions of the same quantity adding up to a cap of 1, or a `combine='add'` option.

2. **A cut in a group's contacts is written as two modifiers (open; one bug).** In epidemics, a cut of `r[i]` for group `i` multiplies the contacts between groups `i` and `j` by `(1 - r[i])*(1 - r[j])`: people in a group meet fewer people, and so are met by fewer. Here this is a cut in the susceptibility and in the infectiousness of the group, which is exact (with the cuts added, the results agree to 1.6e-3) and takes a three-line function. The natural statement would be a modifier of the contacts themselves, `ss.modify(mixing, multiply=ss.by(age=1 - r))`, but in a compartmental run this fails with a NumPy error (`could not broadcast input array from shape (3,) into shape (1,)`, in `set_contacts()`). A single number works. As agents, the code applies the same modifier to the people who would be infected, so even once the error is fixed it would cut one side of each contact. Suggested change: make a cut in contacts by group act on both ends of each contact, as a cut in a matrix of contacts usually means, and fix the error.

3. **Any modifier makes a run 30 times slower (performance; open).** The baseline runs in 1.1 ms. With one modifier, even a constant one with no start or stop, a run takes about 31 ms, and with the six modifiers here 55 ms, against 11 ms for the original. The run stays in the kernels (`sim.kernel_reason()` is None), but before it the tables of rates are worked out again in Python for every step and every flow (`Compartmental.tables()`, through `Engine.value()` and `held_value()`), on every run, including a rerun of the same sim. Suggested change: keep the tables between runs when nothing they depend on has changed, or work out a modifier that only depends on time (a start and a stop, or a time series) in the kernels, as a seasonal factor already is.

4. **Vaccination at a fixed number a day (works; slow; one gap).** epidemics' `nu` is described as a rate of vaccination, but since version 0.2.0 (#198) it is the share of the group vaccinated a day: `nu` times the size of the group, a fixed number a day (29,438 here) for as long as anyone is left in `S`. `ss.Delivery(move=S >> V, capacity=ss.perday(n))` says exactly this, and gives 2,943,843 vaccinated against 2,943,844. Two things could be better. The delivery is a step of its own, outside the kernels, so the vaccination scenario takes 147 ms a run. And `V` has to be passed to `ss.Disease` as an argument (`ss.Disease(S, E, I, R, V, ...)`), since no transition of the disease reaches it; without it, the delivery stops the build with "move= names None, which is not a state of people". The delivery's `move=S >> V` could add the state itself, as it already names it.

5. **The vignette's text does not match its results (not a Starsim issue).** The text says that the epidemic has "a large first wave, followed by a smaller second wave", and that vaccination gives "approximately 5,000 fewer daily infections" at the peak. The vignette's own figures, which this run of version 0.5.0 reproduces, have a second wave three times the size of the first (377,000 new infections a day at its peak on day 267, against 113,000 on day 90), and vaccination cuts the second peak by 28,000 to 52,000 new infections a day in each age group. Also, the internal R function `.ode_model_default()` in `R/model_default.R` still treats `nu` as a rate per susceptible person; the model that is run, in odin, does not.

## Why this model

epidemics fixes a model's structure and lets the user compose a scenario around it, so its most complex example is the one that composes the most elements, not the one with the largest model. This vignette is the only one that uses time dependence, contact interventions, and vaccination together, in scenarios of the same population, and two of its interventions overlap, which exercises the rule epidemics states for combining them. The other candidates were the Vacamole and diphtheria models, which have larger fixed structures but use fewer elements, and the Ebola model, which is stochastic and takes no vaccination. The simple model of the two is [seirv](../seirv).

## What it exercises

- An SEIR-V stratified by age, mixing by a contact matrix from a survey
- A transmission rate that varies smoothly in time, given as a function of time and the base value
- Interventions that cut contacts by age group, over windows of time that overlap, combined by a stated rule
- Vaccination of one age group, at a fixed number a day over a window of time
- Scenarios from one baseline

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`, and runs two variants: the cuts added by hand, and the baseline with steps of a quarter of a day
- `original/modelling_time_dependence.R`: the vignette's code (`vignettes/modelling_time_dependence.Rmd` at the `v0.5.0` tag), as `knitr::purl()` writes it, unchanged
- `run.py`: runs it in the epidemics environment, with the driver of [seirv](../seirv/run.py), which gives the contact matrix and demography as the vignette prints them in place of the 16 lines that load them, and leaves out the plots; it writes `reference/`
- `reference/results.csv`: `S`, `E`, `I`, `R`, and `V` in each age group and in total, on each day from 0 to 365, for each scenario (`baseline_I_0-19`, `intervention_I`, `vaccination_V_40+`, and so on)
- `reference/timing.json`: the time of the call of `model_default()` with the interventions, and of a rerun
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (MIT)

## The model

As in [seirv](../seirv), with:

- **Transmission:** `beta(t) = 1.3/7 * (1 + sin(πt/91.25))` per day, from 0 to twice its mean, highest on days 46 and 228 and lowest on days 137 and 319. The original works it out for each whole day and odin interpolates linearly between them
- **Contacts:** cut by 10%, 1%, and 1% for the three groups from day 50 to 120 (schools), by 1%, 20%, and 20% from day 65 to 90 (workplaces), and by 5%, 1%, and 1% from day 120 to 180 (schools partly reopened). A cut applies to the contacts between two groups at both ends, and cuts that overlap add up
- **Vaccination:** 0.1% of the group aged 40 and over a day (29,438 people) from day 120 to 220, from `S` to `V`, where they are immune
- **Time:** days 0 to 365, solved by deSolve's `lsoda` through odin, with results once a day

## Results

Without intervention, a first wave peaks on day 98 with 0.71 million infectious, and a second, after the transmission rate rises again, on day 275 with 2.38 million; 16.9 million have recovered by day 365. The cuts in contacts, which come during the first wave, make it a fifth the size (0.14 million at its peak) and leave more people susceptible for the second, which peaks at 1.37 million; 8.4 million have recovered by day 365. Vaccinating 2.94 million people aged 40 and over between the waves lowers the second peak to 1.70 million, with 13.3 million recovered.

## Lines of model code

76: the lines of `modelling_time_dependence.R` that are not blank or comments, without `library()`, knitr's options, the plots (and the line that works out the curve to plot, `output <- mod_beta(...)`, in the same chunk), the lines that only print an object (`npis`, `vax_regime`), and the five lines that label and stack the scenarios for the plots (`$scenario <-` and `bind_rows()`). 16 of them make the contact matrix and the demography. No line is over 100 characters. Starsim's 24 are counted the same way.

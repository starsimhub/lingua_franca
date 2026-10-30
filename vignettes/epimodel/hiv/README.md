# EpiModel HIV with a care cascade and PrEP, in Starsim

The translation of [examples/epimodel/hiv](../../../examples/epimodel/hiv), EpiModel's wave 3 example. The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 405 | 58 | About 10 lines are the one remaining workaround (who is indicated for PrEP) |
| One run | 54 s | 2.5 s | With no intervention. The rerun of the original is the mean of 10 runs, and its first run adds estimating the two networks (netest), which is done once |
| Results | | | **Agree within the noise of the runs in three scenarios; with no intervention, the epidemic is larger, as before** (tolerance: 2.5 percentage points for prevalence, 2 for the care cascade and PrEP; below) |

Measured on 30 October 2026 with Starsim 4.0.0 (the `v4` branch, commit a1e3faab) on a 20-core x86-64 Linux machine. Starsim's numbers are the means of 20 runs of each scenario, the original's of 10.

| Scenario | Cumulative infections | Final prevalence | Incidence per 100 person-years (second half) | Diagnosed, on ART, suppressed (second half) | PrEP among the HIV-negative |
|---|---|---|---|---|---|
| No intervention | 476 (original 459) | 16.0% (14.4%) | 2.01 (1.80) | | |
| Cascade | 72 (74) | 5.1% (5.1%) | 0.14 (0.14) | 97.7%, 92.0%, 89.9% (97.6%, 91.9%, 89.7%) | |
| PrEP | 225 (244) | 6.7% (7.3%) | 0.74 (0.80) | | 12.0% (12.0%) |
| Both | 39 (45) | 3.9% (3.8%) | 0.067 (0.074) | 98.5%, 93.0%, 91.0% (98.0%, 92.1%, 89.9%) | 12.2% (12.0%) |

Prevalence at 5 and 10 years agrees within 0.9 percentage points in every scenario. With no intervention, 236 ± 8 people have HIV at the end against 210 (the original's 10 runs range from 154 to 247, so its mean has a standard error of about 9); with PrEP alone, 104 ± 5 against 111. The likely cause is the casual network: Starsim's has the targets (a mean degree of 0.30, and 10.2% with two or more casual partners), while the original's is below them (0.28 and 8.9% with no intervention, 0.30 and 9.6% with PrEP). The main network is close in both (a mean degree of 0.49 to 0.50 against 0.49, and 4.1% to 4.3% with two main partners against 4.0% to 4.2%).

## What was declared and what was not

Declared: the four disease states, with the infectiousness of acute and AIDS on the states; transmission over both networks, per act, with three acts a week in a main partnership and one in a casual one; progression, AIDS deaths, other departures, and arrivals; the care cascade as a stratification of the infected states (undiagnosed, diagnosed, on ART, suppressed, and off ART after being on it) with seven transfers, and its effects on infectiousness, progression, and AIDS mortality as `adjust=`; both networks as `ss.DegreeNet` from the same targets as the original; PrEP as a vaccine with 95% efficacy that people stop taking, delivered to half of those indicated at the start and then to 1.5% of them a week; the scenarios, as `pars=dict(cascade=1)` and the PrEP deliveries.

Not declared (one workaround, marked in the code): who is indicated for PrEP, a function that reads both networks.

The original's six modules (305 lines of R) become the disease, the stratification, and two deliveries. Its two attributes for each person, a stage and a care state, are one state and one dimension here, and its history of ART (`art.time`, which decides whether someone starts or restarts ART) is the level `off`. EpiModel's modules can do anything R can, which is why it can state this model at all; here it depends on what Starsim declares.

## Findings

1. **Fixed: scenarios by a parameter.** A parameter in a transfer's rate is now a parameter of the sim, so the model is built once and the cascade is switched with `pars=dict(cascade=1)`.
2. **Fixed: partnerships ended by departures.** `ss.DegreeNet` allows for them, as EpiModel's `d.rate` does, so the mean degree stays on target with `dur=200` and `dur=26` and no subclass.
3. **Still open: no conditions on the network** (a function). PrEP is indicated for HIV-negative people with two or more partners across both networks, or with a partner who has HIV. This is a 10-line function reading the partnerships. A condition such as `hiv.S & ((main.degree + casual.degree >= 2) | ss.partner_of(hiv.infected))`, usable in `where=`, would declare it.
4. **Fixed: networks in a dict.** `networks=dict(main=main, casual=casual)` works. The two PrEP deliveries still need `name=`, since they are in a list.
5. **Fixed: acts in a partnership.** `acts=` on `ss.DegreeNet` makes `beta` a probability per act, so the chance of transmission over a partnership is worked out as in EpiModel. In this sim, with no unit, a day is a step, so `ss.freqperday(3)` means three acts a week, which reads oddly.
6. **Still open: stopping a product at a rate is written as waning.** PrEP is stopped with a probability of 0.015 a week; that is `ss.Vaccine(waning=-1/np.log(1 - 0.015))`, a mean duration of protection. It works, but a product that people take and stop is not a vaccine, and the duration has to be worked out from the probability.
7. **The networks' targets are better matched than the original's, which affects the results.** EpiModel's casual network has a mean degree of 0.28 to 0.30 and 8.9% to 9.6% with two or more partners, against targets of 0.3 and 10%; `ss.DegreeNet` has 0.30 and 10.1% to 10.2%. This is probably why the epidemic with no intervention is about 10% larger here (about two standard errors). It is not a fault in either, but agreement on the targets does not imply agreement on the network. PrEP alone now comes out a little below the original (6.7% against 7.3%), which is within the noise of the runs.
8. **Smaller differences.** EpiModel uses each rate as a probability per step, written here as `ss.prob` (aliased `week`). It starts its seed infections in stages drawn at random in proportion to 12:520:104; here the expected numbers (2, 98, and 20) are given. Its modules run in turn, each from a snapshot of the attributes at its start, so for example someone can be suppressed and stop ART in one step; here the transfers out of a level compete. None of these is visible in the results.
9. **Fixed: a transition named `stop`.** A transition whose name was also a module parameter used to break the sim; it now runs.

---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Costing

A review of how disease models do cost, financial, and economic modeling, and how they compute health economic outcomes such as DALYs and QALYs.

> **Note:** This is an early-stage review of how others do this, and it owes a great deal to the models it covers. It is not part of the design. Starsim v4 includes a small costing layer, described in the docs under [Costs](https://starsim.org/v4/user_guide/library_econ.html); the larger proposal in [spec.md](spec.md) has not been decided.

## Purpose

This is not a survey of every economic evaluation ever published. It collects exemplars: models whose costing is open, influential, or distinctive enough to show a pattern. Each exemplar answers the same questions: what is costed, how costs attach to the model, how health outcomes are computed, what analyses are supported, and a real snippet from the source. Where code is closed (CISNET, the WHO cervical cancer consortium, Spectrum, TIME, UNIVAC), the entry is drawn from the papers and says so.

## Contents

| Document | What it covers |
|---|---|
| [metrics.md](metrics.md) | Definitions, formulas, and pitfalls for the indicators: DALYs (YLL, YLD, disability weights, life tables), QALYs, costs and perspectives, discounting, ICERs and dominance, net benefit, thresholds, benefit-cost and ROI, budget impact, PSA and value of information, DCEA and ECEA, allocative optimization, reference cases (iDSI, WHO-CHOICE, NICE, CHEERS 2022). Ends with the outputs a disease model needs to provide. |
| [hiv-and-optimization.md](hiv-and-optimization.md) | Atomica and Optima (HIV, TB, Nutrition), Spectrum (Goals, Resource Needs Model, OneHealth), HIV Synthesis, EMOD-HIV, the HIV Modelling Consortium's common costing, the South African Investment Case, STIsim logistics |
| [malaria-and-ntds.md](malaria-and-ntds.md) | OpenMalaria, malariasimulation with `treasure` and `postie`, EMOD, Optima Malaria, schistosomiasis and STH, onchocerciasis, lymphatic filariasis, dengue, open DALY tools |
| [tb-and-vaccines.md](tb-and-vaccines.md) | TIME, tbvax and the WHO TB vaccine investment case, HEdtree decision trees, VIMC/Montagu burden templates, DynaMICE, PRIME, UNIVAC (with TRIVAC and ProVac), Kid Risk polio |
| [cancer-ncd-and-health-systems.md](cancer-ncd-and-health-systems.md) | Thanzi La Onse, Vivarium, HPVsim, the WHO cervical cancer elimination consortium, CISNET colorectal, IMPACT NCD, WHO-CHOICE and OneHealth, health-system capacity |
| [cea-software.md](cea-software.md) | Dedicated health-economic software: heemod, hesim, dampack and DARTH, BCEA and voi, rdecision, TreeAge and Amua, PyHEOR, NICE-style Excel. Includes an API comparison table. |
| [pandemics-and-frameworks.md](pandemics-and-frameworks.md) | Epi-economic pandemic models (DAEDALUS, preparedness investment cases, SIR-macro, covidm vaccine valuation, PTTI), and a table of which general frameworks (including the Starsim family) support costs and DALYs |
| [spec.md](spec.md) | A proposed specification for Starsim v4, drawn from the findings below: costs per event, per time in a state, fixed, and by history; `ss.Economics`; DALYs and QALYs as recipes over weighted person-time; discounting after the run; paired scenarios, ICERs, PSA, and value of information; and the long-table output |

## Main findings

**The disease model counts; the economics layer values.** Across nearly every open exemplar (OpenMalaria, malariasimulation, tbvax, PRIME, DynaMICE, TLO, IMPACT NCD, HIV Synthesis, DAEDALUS), the simulation emits quantities (events, person-time in states, resource use, deaths by age), and costs and DALYs are applied afterwards from swappable tables. OpenMalaria has gone further and removed its old in-model cost hooks. Costing happens during the run only when money or supply changes what happens: budget-driven coverage (Atomica/Optima), finite stock (STIsim), or costs that depend on stochastic events (Kid Risk polio).

**Costs attach in four ways.** Almost everything reduces to:

1. Unit cost × event count (doses, tests, visits, treatment starts), the most common by far.
2. Cost per unit of person-time in a state (ART-years, annual cost of a prevalent condition, sector closure per day).
3. One-off or fixed costs (introduction costs, program overheads, staff and facilities costed by capacity rather than use).
4. Phase-of-care costs keyed to the time of diagnosis and death (CISNET, cervical cancer models), which need each person's life history.

The CEA packages spell these as state rewards, transition rewards, and starting values ([cea-software.md](cea-software.md#api-comparison)).

**The causal direction differs.** In most models, coverage is the input and cost is derived. In Optima and Atomica, spending is the input and coverage is derived through a cost-coverage curve, which is what makes budget optimization possible. The shape of that curve (linear, fixed plus variable, saturating, Hill-function marginal costs) is a modeling choice that should be declared, not buried.

**DALYs are one recipe among several.** Variants include:

- YLL against the GBD reference life table vs a national table vs a fixed life expectancy (80 years in Optima and HIV Synthesis).
- YLL discounted in continuous time to the time of death, vs undiscounted (VIMC).
- YLD as disability weight × person-time in a state, vs a constant per case, vs phase durations.
- Attribution to the year a burden is lived, the year of death, or the year of onset.
- Comorbidity rules that are additive and capped (TLO), multiplicative (Vivarium), or the minimum utility (HIV Synthesis).

Some fields reject DALYs altogether (schistosomiasis modelers use heavy-infection years). The recipe should be a swappable component, with these choices explicit.

**Agent-based models can do this exactly.** TLO, Vivarium, and HPVsim accrue disability weight × time (and YLL at death) per agent during the run, which is exact, stratifiable, and needs no half-cycle correction. Aggregate post-processing from counts and average ages is where errors creep in. Expected-value accumulation (OpenMalaria's `expectedDirectDeaths`) reduces noise in ICER denominators.

**Discounting belongs after the run.** Every in-simulation DALY accumulator seen leaves results undiscounted, and that is the right default. Discounting at analysis time lets one run serve several rates (3% costs and 0% effects for Policy1-Cervix, 3.5% for NICE, 0% and 3.5% together for IMPACT NCD) and gives budget impact analysis the undiscounted series it needs. It only works if every quantity carries its time.

**Long-format tables are the interchange format.** VIMC formalizes it: age × year × location × scenario × run, with columns for cases, deaths, DALYs, and cohort size. Costs, impact attribution, ICERs, CEACs, and VOI are then joins and group-bys. The R tools that compute decision metrics (dampack, BCEA, voi, hesim) all consume costs and effects by sample and strategy, plus the sampled parameters. A library that emits these tables gets those analyses for free.

**Pandemic economics is a different layer, not a different engine.** In DAEDALUS, PTTI, and SIR-macro, GDP losses from closures dwarf treatment costs, so costs have to attach to states of the world (sector openness, contact reduction), not just to deliveries. The best of these models use one parameter for both transmission and economic output. DAEDALUS's economics is a few hundred lines of R over the trajectory.

**Provenance is fragile.** Unit costs need a currency, price year, source, and inflation index (`treasure` attaches all of these). Disability weights need a GBD round. Life tables need a source. Perspective (provider, payer, household, societal), and financial vs economic cost (donated drugs, volunteer time), should be tags on each cost, so totals are a choice. The most influential models are mostly closed; the reusable patterns come from the open ones.

## Where the Starsim family stands

The building blocks exist in several places ([details](pandemics-and-frameworks.md#the-starsim-family)):

- Starsim v4 has a per-delivery `cost=` on `ss.Vaccine`, `ss.Treatment`, and `ss.Diagnostic`, tallied as a `cost` result by stratum in both agent-based and compartmental runs.
- Its library adds `ssl.Costs` (per-event and fixed costs), `ssl.DALYs`, `ssl.ICER`, and `ssl.discount()`, and `ss.fitting.optimize()` allocates budgets ([how to use them](https://starsim.org/v4/user_guide/library_econ.html)).
- STIsim's `logistics` module has products with unit costs, finite supplies, and cost attribution across shared stock.
- HPVsim has an incidence-based `dalys` analyzer.

Still missing, and shared rather than disease-specific:

- Costs per unit time in a state, and capacity costs.
- Currency and price-year metadata.
- Typed event counters. tbvax stands in for them with duplicate "counter" compartments.
- Unit costs and weights in the same PSA as the epidemiological parameters.
- Export to the VIMC-style long table.

[metrics.md](metrics.md#what-a-disease-model-needs-to-provide) lists the minimum output hooks in more detail.

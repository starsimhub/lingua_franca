---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Epydemix

|  |  |
|---|---|
| **Language** | Python (optional Numba JIT) |
| **Paradigms** | Compartmental: stochastic (default) and deterministic, with age/contact-matrix structure |
| **Specification style** | Imperative construction of a model object: compartments, then transitions, then population |
| **Version reviewed** | 1.x |
| **License** | GPL-3.0 |
| **Code** | <https://github.com/epistorm/epydemix> |
| **Docs** | <https://epydemix.readthedocs.io/>, <https://www.epydemix.org/> |
| **Paper** | Gozzi et al. (2025), *PLOS Comp Biol* 21(11): e1013735, [10.1371/journal.pcbi.1013735](https://doi.org/10.1371/journal.pcbi.1013735) |
| **Ecosystem** | Epistorm: `epydemix-data` (400+ locations of population and contact matrices), plus dashboard and forecast applications |
| **Moving to Starsim** | [Conversion guide](../models/epydemix/index.qmd) |

## What it's for

Epydemix is compartmental epidemic modeling with the data already attached. The project brief names it as a framework to convert to and from, and it sits at the "batteries included" end of the range: the model vocabulary is small, and the value is in `epydemix_data` (population structures and contact matrices for over 400 locations) and built-in Approximate Bayesian Computation.

It is the clearest example in the review of a framework where *the bundled data* is the product and *the modeling language* is deliberately small.

## How a model is specified

```python
from epydemix import EpiModel

model = EpiModel(name="SIR Model", compartments=["S", "I", "R"])
model.add_transition(source="S", target="I", params=(0.3, "I"), kind="mediated")
model.add_transition(source="I", target="R", params=0.1, kind="spontaneous")

results = model.run_simulations(start_date="2024-01-01", end_date="2024-04-10", Nsim=100)
df = results.get_quantiles_compartments()
```

Two transition kinds, `spontaneous` and `mediated`, distinguished by whether the rate depends on another compartment. `params=(0.3, "I")` means "rate 0.3, mediated by compartment I". New kinds can be registered:

```python
model.register_transition_kind("my_kind", my_rate_function)
```

So the set of transition kinds is fixed by default, and users can add to it.

Population and mixing come from the data package:

```python
from epydemix.population import load_epydemix_population

population = load_epydemix_population(
    population_name="United_States",
    contacts_source="mistry_2021",
    layers=["home", "work", "school", "community"],
)
model.set_population(population)
```

## Core abstractions

| Concept | Epydemix name | Notes |
|---|---|---|
| Compartment | string in `compartments` | `add_compartments`, `clear_compartments` |
| Transition | `Transition(source, target, kind, params)` | An object with four fields: data, not code |
| Transition kind | `"spontaneous"`, `"mediated"`, or user-registered | The extension point |
| Parameter | `add_parameter`, `override_parameter` | Named, with a separate *override* mechanism for time-varying values |
| Population | `Population` with age groups and layered contact matrices | From `epydemix_data` or user-supplied |
| Intervention | `add_intervention(layer_name, start_date, end_date, reduction_factor=/new_matrix=)` | Contact-layer reductions, date-scheduled |
| Calibration | ABC (rejection, SMC) with metrics in `epydemix.calibration` | The headline feature |
| Results | `SimulationResults` with `get_quantiles_compartments()` | Quantiles across stochastic replicates as the default output form |

## Time

Simulations run on **calendar dates** (`start_date="2024-01-01"`), and interventions are given by date. This matters in practice: real interventions have real dates, and converting them to step numbers invites off-by-one errors.

There are no dimensional types; rates are floats interpreted per time step.

## Interventions

One mechanism, narrowly scoped and well matched to its use case:

```python
model.add_intervention(
    layer_name="school",
    start_date="2020-03-15",
    end_date="2020-06-01",
    reduction_factor=0.2,
)
```

An intervention is a **change to a contact layer over a date range**: a multiplicative reduction or a replacement matrix. That covers school closures, workplace restrictions, and lockdowns, which is most of what a COVID-era scenario model needs. Pharmaceutical interventions are extra compartments and transitions.

`override_parameter` / `delete_override` / `clear_overrides` handle time-varying parameters separately.

## Calibration

ABC is built in: rejection ABC and ABC-SMC, with a library of metrics, running on the stochastic simulator directly. For cheap stochastic models with an awkward likelihood, this is the right choice, and with the data package a user can go from "United States, mistry_2021" to a calibrated model without writing inference code.

## Agent-facing CLI

Epydemix has a command-line tool designed for LLM agents and automation, covering discovery, config checks, running, and inspecting results, documented in `AGENT.md`. Few frameworks here have thought about being driven by a machine, and its choice of a documented command line over a Python API is a useful data point.

## Strengths

- **Transitions are objects with four fields**, so the model is readable data.
- **A fixed set of transition kinds that users can extend.** `spontaneous` / `mediated` covers the common cases, and `register_transition_kind` adds others. This is a good middle position between summer2's fixed set and epipack's general reaction.
- **Calendar dates throughout**, including for interventions.
- **Population and contact data for 400+ locations**, with several contact-matrix sources and layers. Nothing else in the review saves this much setup.
- **ABC calibration built in**, matched to the stochastic simulator.
- **Quantiles across replicates as the default result**, the right default for a stochastic model, and usually left to the user.
- **A documented command line for agents.**
- **Small and simple.** The vocabulary is compartments, transitions, parameters, population, and interventions.

## Limitations

- **A model is built by a sequence of `add_transition` calls**, as a Python object and not a document, and its structure cannot be saved.
- **No stratification function.** Age structure comes from the `Population`'s contact matrix, which stratifies mixing but not compartments. If progression differs by age, the compartments have to be written out.
- **No dimensional types**, no units, and no distinction between rates and probabilities.
- **Interventions act only on contact layers.** Vaccination, treatment, screening, and testing are compartments and transitions.
- **No observation model.** Calibration compares simulated counts with data through a metric function, with no declared reporting process, delay, or ascertainment.
- **Deterministic runs are secondary.** The focus is stochastic simulation plus ABC.
- **GPL-3.0**, more restrictive than most of the frameworks here, which may matter for conversion tools.

## Implications for the lingua franca

1. **Transition kinds that are fixed but can be extended are a good middle position.** This gets most of summer2's benefit (the framework knows what a transition means) without its limit (a flow not on the list cannot be written). The lingua franca could have a small named core and a way out, with the cost of the way out stated (losing automatic stratification, symbolic analysis, and so on).
2. **Calendar dates should be the default.** Epydemix, Starsim, camdl (with `origin`), and flepiMoP support real dates; odin, summer2, EpiModel, and epipack do not, or do so with more effort. Interventions and data have dates, and converting to step numbers is a recurring source of error.
3. **Data is part of the design.** Epydemix's main contribution is that `load_epydemix_population("United_States", "mistry_2021")` works. A language that can express a contact matrix but not *which* matrix, from *which* source, for *which* place has moved the problem and not solved it. Consider whether references to population and mixing data belong in the language, with their sources (as camdl's `read("data/lga_pop.tsv", column = "patch")` partly does).
4. **Quantiles across replicates as the default output.** The natural result of a stochastic model is a distribution over trajectories. Epydemix makes this the default; most frameworks leave it to the user.
5. **Note the command line for agents.** Epydemix and camdl both chose a documented command line as the way for machines to drive them. For an AI-friendly language, the interface an agent uses may matter as much as what it writes.
6. **The intervention gap repeats.** Epydemix has only contact reductions, summer2 and odin have none, and Starsim 3 and EMOD have rich interventions without structured disease models. Across the review, rigorous model structure and rich interventions have not yet appeared in one framework.

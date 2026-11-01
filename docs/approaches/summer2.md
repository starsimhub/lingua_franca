# summer2

|  |  |
|---|---|
| **Language** | Python, with a JAX computational backend |
| **Paradigms** | Compartmental: ODE (default) and stochastic |
| **Specification style** | Declarative model object; structure built by method calls, then *transformed* by stratification |
| **Version reviewed** | `summerepi2` (Monash EMU) |
| **License** | BSD-2-Clause |
| **Code** | <https://github.com/monash-emu/summer2> |
| **Docs** | <https://summer2.readthedocs.io/> |
| **Paper** | Trauer et al. (2025), *Infectious Disease Modelling* 10(1): 99–109, [10.1016/j.idm.2024.08.005](https://doi.org/10.1016/j.idm.2024.08.005) (used across Monash EMU's TB, COVID-19 and other work) |
| **Moving to Starsim** | [Conversion guide](https://starsim.org/v4/user_guide/conversion/summer2.html) |

## What it's for

summer2 builds stratified compartmental models. What sets it apart is **stratification as a step applied to a finished model**. You build an unstratified SIR, then apply age, vaccination, and strain stratifications, and summer2 rewrites the compartments, flows, mixing, and outputs to match.

This is the most developed answer in the review to "how do you add a dimension to a model without rewriting it", a question close to the center of what the lingua franca has to solve. The project owes it a great deal.

## How a model is specified

Build the base model:

```python
from summer2 import CompartmentalModel, Stratification
from computegraph.types import param

m = CompartmentalModel(times=[0, 100], compartments=["S", "I", "R"], infectious_compartments="I")
m.set_initial_population({"S": 990.0, "I": 10.0})
m.add_infection_frequency_flow("infection", param("contact_rate"), "S", "I")
m.add_transition_flow("recovery", param("recovery_rate"), "I", "R")

incidence = m.request_output_for_flow("incidence", "infection")
m.request_function_output("notifications", incidence * param("cdr"))
m.set_default_parameters({"contact_rate": 0.4, "recovery_rate": 0.1, "cdr": 0.2})
```

Then stratify:

```python
age_strat = Stratification("age", agegroup_keys, ["S", "I", "R"])
age_strat.set_population_split({...})                  # how to split the existing population
age_strat.set_flow_adjustments("recovery", rec_adj)    # per-stratum flow multipliers
age_strat.add_infectiousness_adjustments("I", {...})   # per-stratum infectiousness
age_strat.set_mixing_matrix(mm)                        # heterogeneous mixing between strata
m.stratify_with(age_strat)

# outputs, requested after stratification, can select strata
m.request_output_for_flow("incidenceXage_00", "infection", source_strata={"age": "00"})
```

`stratify_with()` does the work. It splits every listed compartment and flow, applies the flow adjustments, extends the mixing categories, and (for an `AgeStratification`) generates the aging flows. The user does not touch the flows they already wrote.

## Core abstractions

| Concept | summer2 name | Notes |
|---|---|---|
| Compartment | `Compartment(name, strata)` | Names carry their strata; `_original_compartment_names` tracks the pre-stratified set |
| Flow | `add_transition_flow`, `add_infection_frequency_flow`, `add_infection_density_flow`, `add_crude_birth_flow`, `add_replacement_birth_flow`, `add_importation_flow`, `add_death_flow`, `add_universal_death_flows` | A closed vocabulary of **named flow kinds**, not an open rate expression |
| Stratification | `Stratification(name, strata, compartments)` | Plus `AgeStratification` (adds aging flows) and `StrainStratification` (multi-strain force of infection) |
| Stratum adjustment | `Adjustment`: `Multiply`, `Overwrite` | Applied to flows and to infectiousness, per stratum |
| Mixing | `set_mixing_matrix(matrix_or_function)` | Only allowed on a full stratification; builds up `_mixing_categories` |
| Parameter | `param("name")`, `set_default_parameters({...})` | Symbolic: parameters are graph nodes, resolved at run time |
| Derived output | `request_output_for_flow`, `request_output_for_compartments`, `request_function_output` | Tracked in a `networkx` DAG of dependencies, with a whitelist for selective evaluation |
| Computed value | `add_computed_value_func(name, func)` | Runtime-computed intermediate available to flow rates |
| Backend | `BackendType.JAX` (default) | The whole model compiles to JAX, giving autodiff and JIT |

## The key idea: stratification as a transformation

Three properties of `stratify_with()` are what the lingua franca would need to reproduce.

**It is checked against the model.** An adjustment naming a flow or compartment that does not exist is rejected, and strata named in a source or destination are checked.

**Order matters, and stratifications combine.** They apply in sequence, each seeing the model as the last one left it. `AgeStratification` and `StrainStratification` may each be applied once, and a mixing matrix requires a *complete* stratification (all compartments), since you cannot mix on an axis only some compartments have.

**Adjustments connect the base model and the strata.** The base model says "recovery happens at `recovery_rate`"; the stratification says "×1.5 for children, ×0.5 for the elderly". Neither knows about the other. This division (a general process plus a modifier per stratum) lets one model serve many structures.

## Parameters and the computation graph

Parameters are symbolic (`param("contact_rate")`), and derived outputs form a `networkx` dependency graph. The model is not evaluated when it is built. It is *compiled*, and JAX then compiles the whole thing to fast code.

This gives more than speed: **automatic differentiation of the whole model with respect to its parameters**, so gradient-based calibration and sensitivity analysis come for free, and a **dependency graph of outputs** that can be cut down to what was requested.

camdl's internal form and odin's dependency sort make the same move in other ways: separate the description of the model from its evaluation.

## Time

`CompartmentalModel(times=(start, end), timestep=1.0, ref_date=datetime)`. Times may be given as datetimes if `ref_date` is set, and are converted to numbers internally. The constructor checks that the timestep divides the period exactly.

There are **no dimensional types**. Rates are floats, and their units are up to the modeler. `add_infection_frequency_flow` versus `add_infection_density_flow` is the one place where such a distinction is explicit, by *choosing a different function*, which is a coarse but effective check.

## Strengths

- **Stratification as a built-in, checked step.** The best treatment of the problem in the review.
- **A fixed set of named flow kinds.** `add_infection_frequency_flow`, `add_infection_density_flow`, `add_transition_flow`, and `add_crude_birth_flow` carry real epidemiological distinctions, so the framework knows what a flow *means* and can stratify it correctly. A free rate expression cannot be stratified automatically; a named flow kind can.
- **Adjustments (`Multiply` / `Overwrite`)**: a general process plus a modifier per stratum, neither aware of the other.
- **Special handling where it counts.** `AgeStratification` generates aging flows and `StrainStratification` restructures the force of infection, which are laborious and error-prone by hand.
- **Correct restrictions, enforced.** Mixing matrices only on complete stratifications; one age stratification; one strain stratification; strains cannot carry a mixing matrix.
- **Symbolic parameters and a compiled graph**, with JAX giving fast code and automatic differentiation over the whole model.
- **Requested outputs**, with source and destination filters, so incidence in children is one line and not a post-processing script.
- **Checks that can be switched off** (`set_validation_enabled`): thorough by default, off for production runs.
- **A build tracker** (`ModelBuildTracker`) that records the steps taken to build the model, a step toward a readable model history.

## Limitations

- **Compartmental only.** No agents, no networks, no individual state.
- **No dimensional types.** Rates are floats.
- **Flow kinds are a fixed list.** It is a rich list, but a flow not on it has to be approximated by one that is. This is the tradeoff for automatic stratification, which works only because the framework knows what each flow means.
- **Stratification depends on order**, and the rules (age once, strain once, mixing needs a complete stratification) are enforced but not visible in the model: you have to know them.
- **A model is built by a sequence of method calls**, so it is a Python script and not a document. `ModelBuildTracker` records what was done, but the model is not itself data.
- **No intervention vocabulary.** Time-varying parameters go through `summer2.functions.time`, and interventions are parameter changes. There is no coverage, delivery, eligibility, or product.
- **Two phases** (build, then finalize, then run) that the user has to keep in mind.
- **Source comments list work left for a future summer3**: flow adjustments with parameters, arbitrary output dimensions, and xarray output.

## Implications for the lingua franca

1. **Stratification should be one operation, not a rewrite.** summer2 proves this works and shows what it needs: the framework has to know what each flow *means*. This argues for **a fixed set of meaningful transition kinds** (infection by frequency or density, progression, birth, death, importation, aging) alongside free rate expressions.
2. **Adjustments are the right link between base model and strata.** `Multiply` and `Overwrite` per stratum, on flows and infectiousness, keep the base model free of strata. Adopt this, and consider whether `Overwrite` should exist at all, given how it interacts with several stratifications.
3. **Treat specially the stratifications that carry structure.** Age (aging flows), strain (a restructured force of infection), and space (movement) are not generic dimensions. camdl makes the same point by separating population strata from residence structure. The lingua franca needs a way to say which kind a dimension is.
4. **Enforce the restrictions that follow from the structure.** "A mixing matrix requires a complete stratification" is a matter of correctness, and summer2 checks it. A multi-paradigm language will have many such rules, and each should be a named error.
5. **Build a graph first, then compute.** summer2's `networkx` graph, odin's dependency sort, and camdl's internal form are three routes to the same requirement. However the lingua franca is written, the model should become a graph before it is evaluated.
6. **Requested outputs with stratum filters.** `request_output_for_flow("incidence", "infection", source_strata={"age": "00"})` is a good way to ask for outputs, and pairs with camdl's `incidence(transition[age = child])`. Both name a transition and select strata, and the lingua franca should have one such form.
7. **Note the missing intervention layer.** summer2 and odin, the two strongest compartmental designs here, have essentially no intervention vocabulary. Starsim 3, EMOD, and EpiHiper had the strongest intervention vocabularies and the weakest model structure. Closing that split is one of the more concrete contributions open to this project.

# epidemics (Epiverse-TRACE)

|  |  |
|---|---|
| **Language** | R, with models written in the odin DSL |
| **Paradigms** | Deterministic compartmental (ODE via odin); one discrete-time stochastic model |
| **Specification style** | **Model structure is fixed.** The user composes a scenario from *composable elements* |
| **Version reviewed** | 0.5.0 |
| **License** | MIT |
| **Code** | <https://github.com/epiverse-trace/epidemics> |
| **Docs** | <https://epiverse-trace.github.io/epidemics/> |
| **Paper** | — |
| **Ecosystem** | Epiverse-TRACE (data.org, LSHTM, Universidad de los Andes): ~18 interoperating R packages |

## What it's for

`epidemics` is deliberately the opposite of a modeling framework. Its scope statement is unusually clear:

> *epidemics* aims to help public health practitioners — rather than research-focussed modellers — to rapidly simulate disease outbreak scenarios […] *epidemics* **trades away some flexibility in defining model structures for a gain in the ease of defining epidemic scenario components** such as affected populations and model events.

So the compartmental structure is **fixed**, as a library of published models: `model_default` (an age-structured SEIR-V), `model_vacamole` (two-dose leaky vaccination), `model_ebola` (stochastic, with Erlang sub-compartments), and `model_diphtheria` (a camp setting). Users cannot add links between compartments. They *can* build the scenario around the model.

It is here because it states most clearly a question the lingua franca has to answer: **which parts of a model should users define, and which should be a library?**

## How a model is specified

```r
uk_population <- population(
  name               = "UK",
  contact_matrix     = contact_matrix,
  demography_vector  = demography_vector,
  initial_conditions = initial_conditions   # rows = age groups, cols = compartments
)

output <- model_default(population = uk_population, time_end = 600, increment = 1.0)
```

Then compose elements onto it:

```r
close_schools <- intervention(
  type = "contacts", time_begin = 200, time_end = 260,
  reduction = matrix(c(0.5, 0.01, 0.01))     # per demography group
)

mask_mandate <- intervention(
  type = "rate", time_begin = 200, time_end = 300,
  reduction = 0.163                           # on transmission_rate
)

vaccinate <- vaccination(
  name = "vaccinate all", time_begin = ..., time_end = ..., nu = ...
)

output <- model_default(
  population    = uk_population,
  intervention  = list(contacts = close_schools, transmission_rate = mask_mandate),
  vaccination   = vaccinate,
  time_dependence = list(transmission_rate = function(time, x) x * seasonality(time)),
  time_end = 600
)
```

Every element is optional except `population`. Passing lists of elements gives a **scenario grid**, returned as one tidy data frame with scenario identifiers, so the user writes no loop to compare scenarios.

## Core abstractions

| Concept | epidemics name | Notes |
|---|---|---|
| Population | `<population>` S3 class | Contact matrix + demography vector + initial conditions matrix, with rows = demography groups throughout |
| Model | `model_default`, `model_vacamole`, `model_ebola`, `model_diphtheria` | Fixed structures from the literature |
| Intervention | `<intervention>` superclass → `<contacts_intervention>`, `<rate_intervention>` | Time window + reduction, per demography group |
| Vaccination | `<vaccination>` | Time window + per-group rate `nu`, possibly multi-dose |
| Time dependence | named list of `function(time, x)` | Seasonality and other forcing on named parameters |
| Model event | `<event>` | Discrete changes |
| Output | `<data.frame>`-inheriting, tidy | Long format with scenario columns |

## The design decisions, as stated

The package includes a `design-principles.Rmd` vignette. Very few frameworks in this review write down *why*, and we are grateful for it. Some of its decisions matter here.

**Interventions combine additively, not multiplicatively.** Two interventions reducing contacts by X% and Y% give `C × (1 − (X + Y))`, not `C × (1 − X)(1 − Y)`. The stated reason is that additive effects were thought easier for users to understand.

Multiplying is the more common assumption, but the package chose otherwise and **documented the choice and its reason**. Whether or not one agrees, writing it down is right. In many frameworks the rule is simply whatever the code happens to do.

**Each model has its own set of elements.** The Ebola model takes no `vaccination` element, because vaccination is considered unlikely in its use case. It also refuses rate interventions on `infectiousness_rate` and `removal_rate`, because those set the number of Erlang sub-compartments and cannot change mid-run without redistributing individuals. So a **restriction that follows from the model's structure is enforced and explained**, as in camdl's capability checks.

**Two levels of function.** Each model has an internal implementation (`.model_ebola_internal()`) and a user-facing wrapper (`model_ebola()`) that checks inputs and combines scenarios. The checks are substantial: `assert_*()` functions verify each element, and that the elements fit the population.

**Demography in rows.** Initial conditions, vaccination rates, and contact reductions all use rows = demography groups, throughout.

**Reproducibility across scenarios via `withr`.** Seeds are preserved across parameter sets and interventions, so that differences between runs come from the scenario. This has the same goal as common random numbers, achieved by managing seeds.

## Strengths

- **A stated scope, and decisions that follow from it.** The trade (less freedom in structure, more in scenarios) is explicit, justified, and applied consistently.
- **A published design-principles document.** Rare, and valuable.
- **Elements as objects**: `<population>`, `<intervention>`, `<vaccination>`, plus time-dependence functions and events, each optional and each checked.
- **The split between `<contacts_intervention>` and `<rate_intervention>`** separates "changed who meets whom" from "changed a parameter", a distinction usually left unstated.
- **Scenario grids as the normal output**, tidy, with scenario identifiers.
- **The rule for combining interventions is stated** (additive), with the reasoning.
- **Restrictions specific to each model**, enforced, and explained from the model's structure.
- **Extensive cross-checking** between elements and the population.
- **Built on odin**, so the fixed models are compiled and fast, and their source is readable.
- **Works with the Epiverse-TRACE packages**: `socialmixr` contact matrices, `epiparameter` delay distributions, `<incidence2>` data.

## Limitations

- **Users cannot define model structure.** New compartments or links mean contributing a model to the package. That is the design, and a real limit.
- **Adding intervention effects is a debatable default**, however well documented. Two 60% reductions give 120%, which has to be capped somewhere.
- **The library is small**: four models, each with its own parameter names and allowed elements, so the shared interface is thinner than it appears.
- **Deterministic apart from the Ebola model**, which is written in R and not odin for a specific performance reason.
- **No dimensional types**; rates are plain per-day numbers.
- **No observation model and no inference.** Fitting is left to other packages in the ecosystem, by design.
- **Elements do not work uniformly across models**: which elements a model accepts is recorded in the vignettes.

## Implications for the lingua franca

1. **This is the clearest case in the review of a choice the design has to make.** `epidemics` fixes the structure and opens the scenario; camdl, odin, and summer2 do the reverse. A language that opens both has to keep scenarios usable with any structure: `<contacts_intervention>`, for instance, means something only if the model has a contact matrix. **A scenario element needs a way to state which features of the model it requires**, as epymorph's models state the data they require.
2. **State the rule for combining effects, and let it be set.** `epidemics` deserves credit for writing down that interventions add, and why. The lesson is to make the rule **explicit for each effect**. Vivarium's declared combiners are the general mechanism, and any single default would be wrong for someone.
3. **The contacts/rate split is worth keeping.** An intervention changes either the contact structure or a parameter. These differ in meaning, data needs, and when they are valid, and separating them (as `epidemics` does, and as Epydemix and MEmilio do by supporting only the first) lets both be checked.
4. **Restrictions should follow from the model and be explained.** "You cannot apply a rate intervention to `infectiousness_rate` because it determines the number of Erlang sub-compartments" follows from the model's structure, and the package says so. Where dwell times are declared, the language can work this out itself.
5. **Scenario grids as the normal result.** Passing lists of elements and getting one tidy table back is easy to use, and it matches camdl's `batch` and Starsim's `MultiSim`. The lingua franca should treat a set of scenarios as the default unit of a run.
6. **Write the design-principles document.** `epidemics` has one, and almost nothing else here does. For this project, the reasoning behind each decision *is* part of the result, and it goes in `best-practices`.

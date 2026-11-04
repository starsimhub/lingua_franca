---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# epiworld (epiworldR / epiworldpy)

|  |  |
|---|---|
| **Language** | Header-only C++ core; R and Python bindings |
| **Paradigms** | Agent-based: networks, fully-connected mixing, and mixing-matrix models |
| **Specification style** | Model built from states, transition functions, viruses, and tools, either from templates or with a model builder |
| **Version reviewed** | epiworldR 0.14.0.0 (CRAN); two models translated: [an SEIR in a connected population](../models/epiworld/seirconn/README.md) and [COVID-19 and flu with a vaccine](../models/epiworld/covid_flu/README.md) |
| **License** | MIT |
| **Code** | <https://github.com/UofUEpiBio/epiworld>, <https://github.com/UofUEpiBio/epiworldR> |
| **Docs** | <https://uofuepibio.github.io/epiworldR/> |
| **Paper** | Meyer & Vega Yon (2023), *JOSS* 8(90): 5781, [10.21105/joss.05781](https://doi.org/10.21105/joss.05781) |
| **Ecosystem** | `epiworld` (C++ core), `epiworldR`, `epiworldpy`, `epiworldRShiny`: all over the same engine |

## What it's for

epiworld is a fast agent-based epidemic engine (the documentation claims ~30 million agent-days per second), packaged as a header-only C++ library with thin R and Python interfaces. Its two distinguishing features are **several simultaneous diseases** and **a separation of viruses and tools**, which treats pathogens and interventions as the same kind of object attached to agents.

It matters here because `epiworldR` and `epiworldpy` are two front ends over one engine, not parallel implementations, so **a model means the same thing in both languages**. Nothing else in the review can claim that.

## How a model is specified

Templates cover the common cases (`ModelSIR`, `ModelSEIR`, `ModelSIRCONN`, `ModelSEIRCONN`, `ModelSEIRD`, `ModelSEIRMixing`, `ModelSEIRMixingQuarantine`, `ModelDiffNet`) with `CONN` meaning fully connected, `Mixing` meaning a contact matrix over groups, and the plain forms meaning a network.

Beyond templates, the model builder assembles a model from parts:

```r
model <- Model()

add_param(model, "Rec Rate", 0.1)
add_param(model, "Trans Rate", 0.5)

# States, each with an update function
update_fun_s <- update_fun_susceptible()
add_state(model, "S", update_fun_s)

update_fun_i <- update_fun_rate(param_names = "Rec Rate", target_states = 2L)
add_state(model, "I", update_fun_i)

add_state(model, "R", NULL)     # absorbing

# A virus is a separate object with its own rates
flu <- virus("Flu", 0, .5, .2, .01, prevalence = 0, as_proportion = TRUE)
virus_set_state(flu, 1, 2, 2)   # which states the virus moves agents into
set_prob_infecting_ptr(flu, model, "Trans Rate")
set_distribution_virus(flu, distribute_virus_randomly(1L, FALSE))
```

Two features stand out.

**States carry update functions.** A state is a name plus a function saying what happens to an agent in it. `update_fun_rate(param_names = "Rec Rate", target_states = 2L)` is a ready-made, named rule with parameters, so common cases need no custom code. `set_prob_infecting_ptr(flu, model, "Trans Rate")` ties a virus's infection probability to a named model parameter, so calibration can move the parameter and every virus using it follows.

**States are numbered.** `target_states = 2L`, `virus_set_state(flu, 1, 2, 2)`. This is fast, but harder to read and easier to get wrong: the example needs a comment (`0 = S, 1 = I, 2 = R`) to make sense.

## Core abstractions

| Concept | epiworld name | Notes |
|---|---|---|
| Agent | agent | With a status (state index), a set of viruses, and a set of tools |
| State | `add_state(model, name, update_fun)` | Name plus update function; indexed by integer |
| **Virus** | `virus(name, ...)` with its own rates and `virus_set_state` | A built-in transmissible object attached to agents; a model can carry many |
| **Tool** | `tool(...)` | A built-in *protective* object attached to agents (vaccine, mask, treatment) with its own effects on susceptibility, transmissibility, recovery, and death |
| Entity | `entity` | Groups agents (households, schools) for mixing-matrix models |
| Parameter | `add_param(model, name, value)` | Named; bindable by pointer into virus/tool rates |
| Distribution | `distribute_virus_randomly`, `distribute_tool_*` | How viruses and tools are seeded across the population |
| Network | edge list, or `CONN` (fully connected), or `Mixing` (contact matrix) | Three transmission structures over one engine |
| Event | `events.R`, global actions | Scheduled model-level actions |
| Inference | `LFMCMC` | Likelihood-free MCMC, built in |
| Diagram | `ModelDiagram` | Generates a state-transition diagram from a run |

## The virus/tool duality

This is the idea most worth taking. An agent carries two collections:

- **Viruses**: transmissible objects with infection probability, recovery rate, death probability, and a mapping to states.
- **Tools**: protective objects with multiplicative effects on susceptibility, transmissibility, recovery, and death.

An agent's susceptibility depends on its tools, and its transmissibility on its viruses and tools. Several diseases and interventions then combine automatically: adding a second virus does not change the first, and a mask reduces susceptibility to all of them.

This differs from Starsim, where diseases are modules with their own state and interventions change that state. For "several pathogens, several protective measures, all multiplicative", it is arguably neater. It is less general (a tool is four multipliers, not arbitrary behavior), and that is why the pieces combine so well.

## Time

Discrete steps, unitless. No dates, no dimensional types. Rates are per-step probabilities and the modeler holds the interpretation.

## Strengths

- **One engine, two languages, the same results.** A model in `epiworldR` and in `epiworldpy` is the same C++ computation. This is the best multi-language design in the review, and header-only C++ kept it cheap.
- **Several diseases by design**, through the collection of viruses.
- **Viruses and tools**: pathogens and protective measures as built-in objects on agents, with multiplicative effects that combine automatically.
- **Three transmission structures over one engine** (network, fully connected, and mixing matrix), chosen by model class. The same disease runs as an ABM or a mixing-matrix model, which is Starsim's route idea, arrived at independently.
- **Ready-made update functions** (`update_fun_rate`, `update_fun_susceptible`) for common state behaviors.
- **Parameters tied to** virus and tool rates, so calibration reaches every use.
- **Fast.** This is why the C++ core is header-only and the R and Python layers are thin.
- **`ModelDiagram`**: automatic state-transition diagrams.
- **Likelihood-free MCMC built in.**
- **Small and easy to learn.** The whole vocabulary is states, viruses, tools, entities, and parameters.

## Limitations

- **Numbered states.** `target_states = 2L` and `virus_set_state(flu, 1, 2, 2)` need a comment mapping numbers to names, and a wrong number gives a silently different model. This is the clearest argument in the review for names over positions.
- **Update functions are C++ or R functions.** The ready-made ones are simple; anything custom is code, and custom R code crosses into C++.
- **Tools are limited to four multiplicative effects.** That is why they combine, and anything else (a diagnostic with a result, a treatment with a duration, a screening cascade) needs different machinery.
- **No dimensional types, no dates, unitless steps.**
- **Networks are inputs.** An edge list is supplied, and there is no way to describe a network to generate (compare EpiModel's `netest`).
- **No observation model.** LFMCMC compares summary statistics.
- **Single institution, modest adoption**, though CRAN and JOSS give it more visibility than most of its size.
- **A model is a sequence of calls** (`add_state`, `add_param`, `virus_set_state`), not a document.

## Implications for the lingua franca

1. **Viruses and tools deserve serious consideration as a building block.** "Things an agent carries that make it transmit" and "things that protect it", both with declared multiplicative effects on susceptibility, transmissibility, recovery, and death, combine automatically and correctly across diseases and interventions. This is more limited than Starsim's connectors, and so avoids the problem of the last write winning. Where it runs out (cascades, diagnostics, durations) is clear, and other mechanisms can take over.
2. **One engine with many front ends is the right way to distribute.** epiworld shows this can be cheap. For a project built on a model having one standard form, R and Python front ends that are the same computation, and not parallel versions that drift apart, are close to essential. `rstarsim` gets there by embedding Python; epiworld's version is neater.
3. **Names, never numbers.** Avoid `target_states = 2L`. Every reference in the language (to a state, a transition, a parameter, a stratum) should be by name, and checked to exist. camdl's E332/E263 errors show this rule at work.
4. **Ready-made rules with parameters are a good middle layer.** `update_fun_rate(param_names = "Rec Rate", target_states = 2L)` is neither a fixed template nor arbitrary code. Epydemix's registered transition kinds and summer2's named flow kinds have the same shape: **a fixed set of named rules with parameters covers most real models, and custom code is where the language's guarantees stop.**
5. **This is the third independent arrival at routes.** Starsim (`Network` / `MixingPool`), epiworld (`ModelSEIR` / `ModelSEIRCONN` / `ModelSEIRMixing`), and epipack (network versus well-mixed) have all separated the disease process from the contact structure. That is strong evidence for the division, and the differences between them are the detail the design needs to get right.
6. **Automatic model diagrams should be a standard output.** `ModelDiagram` in epiworld, `fillcolor` in EMULSION, `comp_plot` in EpiModel, and `diagram()` in Starsim 4 all point the same way: if the model is data, a picture of it is nearly free, and non-modelers read the picture.

---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# EMULSION

|  |  |
|---|---|
| **Language** | YAML DSL; engine in Python |
| **Paradigms** | Compartmental, individual-based (IBM), **hybrid**, and metapopulation: multi-level and multi-scale |
| **Specification style** | A single human-readable YAML document. No code required |
| **Version reviewed** | 1.2.1 |
| **License** | Apache-2.0 |
| **Code** | <https://forgemia.inra.fr/dynamo/software/emulsion-public> |
| **Docs** | Ships with the repository; quickstart and feature model libraries |
| **Paper** | Picault et al. (2019), *PLOS Comp Biol* 15(9): e1007342, [10.1371/journal.pcbi.1007342](https://doi.org/10.1371/journal.pcbi.1007342) |
| **Moving to Starsim** | [Conversion guide](https://starsim.org/v4/user_guide/conversion/emulsion.html) |

## What it's for

EMULSION is a modeling framework for veterinary and plant epidemiology in which **the model is a document**, not a program. Its stated motivation is communication: models should be "explicit, intelligible and revisable", so that modelers can discuss them with biologists, veterinarians, and economists throughout the work.

For this project, it is the most important framework in the review after camdl and Starsim, for the reason below.

## The finding

**EMULSION got there first.** Compare two of its example models:

```yaml
# compart_SIR.yaml
levels:
  population:
    desc: 'level of the population'
    aggregation_type: 'compartment'
    contains:
      - individuals
  individuals:
    desc: 'level of individuals'
```

```yaml
# IBM_SIR.yaml
levels:
  population:
    desc: 'level of the population'
    aggregation_type: 'IBM'
    contains:
      - individuals
  individuals:
    desc: 'level of the individuals'
```

The rest of both files (the state machine, the transitions, the parameters, the initial conditions, the outputs) is identical. **A one-word change switches the model between a stochastic compartmental model and an individual-based model.** A third value, `hybrid`, gives a mixed formulation where some processes are tracked individually and others in aggregate.

This is the goal of paradigm independence, achieved in an Apache-2.0 package published in 2019. Design work here should start from what EMULSION can and cannot express under that switch, because that boundary is the real research question.

## How a model is specified

One YAML document with named top-level sections:

```yaml
model_name: IBM_SIR

time_info:
  time_unit: 'days'
  delta_t: 1
  origin: 'January 1'
  total_duration: '100'

levels:
  population:
    aggregation_type: 'IBM'
    contains: [individuals]
  individuals:
    desc: 'level of the individuals'

processes:
  individuals:
    - health_state              # names a state machine

state_machines:
  health_state:
    states:
      - S: {name: 'Susceptible', fillcolor: 'wheat'}
      - I: {name: 'Infectious',  fillcolor: 'maroon'}
      - R: {name: 'Resistant',   fillcolor: 'deepskyblue'}
    transitions:
      - {from: S, to: I, rate: 'force_of_infection'}
      - {from: I, to: R, rate: 'recovery'}

parameters:
  transmission_I:
    desc: 'transmission rate from infectious individuals (/day)'
    value: 0.5
  recovery:
    desc: 'recovery rate (/day)'
    value: 0.1
  force_of_infection:
    desc: 'infection function'
    value: 'transmission_I * total_I / total_population'
    source: 'classical function assuming frequency dependence'

prototypes:
  individuals:
    - healthy:  {health_state: S}
    - infected: {health_state: I}

initial_conditions:
  population:
    - {prototype: healthy,  amount: 'initial_population_size - initial_infected'}
    - {prototype: infected, amount: 'initial_infected'}

outputs:
  type: csv
  population:
    period: 1
    extra_vars: [percentage_prevalence, total_population]
```

Every element carries a `desc:`, and parameters may carry a `source:` naming the assumption or citation behind the value. Documentation is part of the model, not adjacent to it.

## Core abstractions

| Concept | EMULSION name | Notes |
|---|---|---|
| Organization level | `levels:` with `aggregation_type` and `contains` | `compartment`, `IBM`, `hybrid`, `metapopulation`; levels nest (individual → herd → metapopulation) |
| Process | `processes:` per level | Names the state machines (or grouped processes) that run at that level |
| State machine | `state_machines:` | States and transitions: the core model structure |
| Transition | `{from:, to:, rate:}` or `{... proba:}` or `{... duration:}` | **Three ways to specify timing**, converted to the time step automatically |
| Parameter | name with `value`, `desc`, `source` | `value` may be a number or an expression over other parameters and aggregates |
| Aggregate | `total_I`, `total_population` | Automatically available names for state totals |
| Prototype | `prototypes:` | Named bundles of initial attribute values: a template for creating individuals |
| Initial condition | `initial_conditions:` | Prototype + amount, where amount is an expression |
| Output | `outputs:` with `period` and `extra_vars` | Declarative |
| Code add-on | optional Python module | The escape hatch for behavior the YAML cannot express |

## Time

`time_info` declares `time_unit`, `delta_t`, `origin` (a calendar date), and `total_duration`. Transitions may be specified as a **rate**, a **probability**, or a **duration**, and the engine converts:

> Rates are automatically converted into probabilities w.r.t the duration of the time step (delta_t), assuming a classical exponential distribution of durations in the states.

Starsim later encoded the same three-way distinction as `per` / `prob` / `dur`. Here they are three alternative keys on a transition. They are not types (a rate is still a number, and its unit is in the `desc:` string), but the *distinction* is in the model, and the engine does the conversion.

## Multi-level and multi-scale

`levels` with `contains` builds a hierarchy: individuals inside herds inside a metapopulation, each with its own `aggregation_type` and processes. A herd-level process (culling, movement, testing) acts on herds, an individual-level process (infection, recovery) acts on individuals, and the engine reconciles them.

No other framework in the review does this. Starsim, EpiModel, and epiworld have one population level, and epymorph has nodes and aggregated individuals. EMULSION lets **each level choose its own paradigm**, which is what makes the hybrid mode possible.

## Strengths

- **Paradigm as a declared property of a level.** `aggregation_type: compartment | IBM | hybrid` on an otherwise identical model. This proves in practice that the project's central idea can work.
- **The model is a document.** YAML that people can read, compare between versions, and review without programming. Transitions, the state machine, and initial conditions are all data.
- **Several levels, each with its own paradigm.** Individual → herd → metapopulation.
- **Three ways to give timing on a transition**: rate, probability, or duration, converted by the engine.
- **Documentation in the model**: `desc:` on everything, and `source:` on parameters recording where a value came from.
- **Prototypes**: named bundles of initial attributes, a neat way to say "create 100 healthy individuals and 1 infected one".
- **Parameters as expressions** over other parameters and automatic totals (`total_I`, `total_population`), so the force of infection is visible and not hidden in the engine.
- **Models can be drawn**: `fillcolor` on states is there because the engine draws the model.
- **A stated communication goal**, and a design that follows from it.

## Limitations

- **YAML makes checking hard.** Checks stop at the file format, expressions sit in strings (`value: 'transmission_I * total_I / total_population'`), there is no editor support or type checking, and errors come from a YAML parser. A dedicated language, like camdl's, avoids these at the cost of readers having to learn it.
- **No dimensional types.** A rate's units are in its `desc:` string.
- **The force of infection is written by hand.** `transmission_I * total_I / total_population` is correct here, but nothing checks it, and nothing knows that this transition is an infection. camdl catches this kind of missing-`/N` error.
- **Totals appear without being declared**, such as `total_I` and `total_population`.
- **Code add-ons handle what YAML cannot**, and a model using them is no longer only a document.
- **Small community, on INRAE's GitLab**, mainly in veterinary and plant epidemiology, so it is less known outside that field.
- **The paradigm switch has undocumented limits.** The examples show `compartment`/`IBM`/`hybrid` on the same simple SIR. What happens with individual attributes that have no compartmental counterpart is not stated in the material reviewed, and this project needs that answered.

## Implications for the lingua franca

1. **Start by mapping where EMULSION's paradigm switch stops.** Take its feature models, try each under `compartment` / `IBM` / `hybrid`, and record where the switch stops working and why. That boundary shows how far paradigm independence can go, and EMULSION provides the means of measuring it.
2. **Paradigm belongs to a *level*, not to a model.** The choice is per level and hierarchical: individuals may be aggregated while herds are explicit, or the reverse. That says more than one flag per model, and matches how hybrid models are built. The lingua franca should let each level declare how it is aggregated.
3. **Rate, probability, and duration are the right three ways to give timing.** They match how epidemiologists hold their parameters (a hazard, a per-step probability, a mean duration), and they convert mechanically. Starsim's types are the rigorous form, and EMULSION's keys the readable one. The lingua franca wants both: `rate`/`prob`/`dur` as *typed* alternatives on a transition.
4. **Keep sources in the model.** `source:` on a parameter ("classical function assuming frequency dependence") is one line that answers every reviewer's question. With camdl's `#'` comments and `@symbol` annotations, this suggests a standard place for *why this value*, as well as *what value*.
5. **Prototypes are a good way to set initial conditions.** Naming a bundle of attributes and saying how many of each to create is neater than a compartment vector (which cannot express correlated attributes) or per-agent code.
6. **Do not build on YAML.** EMULSION shows the value of a model as a document, and also the cost of using a data format as the language. The lingua franca should be as readable as EMULSION's YAML and as checkable as camdl, which means its own language with a standard data form underneath.

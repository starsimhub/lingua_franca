# EpiHiper

|  |  |
|---|---|
| **Language** | C++ (MPI/OpenMP); models specified in JSON against published schemas |
| **Paradigms** | Agent-based on explicit dynamic contact networks, at national scale (300M+ agents) |
| **Specification style** | Five JSON documents against published schemas: config, disease model, initialization, intervention, scenario |
| **Version reviewed** | 2.0.0 |
| **License** | MIT |
| **Code** | <https://github.com/NSSAC/EpiHiper>, schemas at <https://github.com/NSSAC/EpiHiper-Schema> |
| **Docs** | <https://epihiper.readthedocs.io/> |
| **Paper** | [10.1093/pnasnexus/pgae557](https://doi.org/10.1093/pnasnexus/pgae557) |
| **Users** | Biocomplexity Institute, University of Virginia; CDC Scenario Modeling Hub at national scale |

## What it's for

EpiHiper runs US-scale agent-based epidemics (hundreds of millions of agents on a synthetic contact network) on high-performance clusters. It is here for **how models are written**: unlike EMOD, it makes the *disease model itself* data, and its interventions, also data, are the most complete such language in the review.

## How a model is specified

### The disease model is JSON

```json
{
  "$schema": ".../diseaseModelSchema.json",
  "states": [
    { "id": "S",      "ann:label": "Susceptible",  "infectivity": 0, "susceptibility": 1 },
    { "id": "I",      "ann:label": "Infectious",   "infectivity": 1, "susceptibility": 0 },
    { "id": "R",      "ann:label": "Recovered",    "infectivity": 0, "susceptibility": 0 },
    { "id": "V",      "ann:label": "Vaccinated",   "infectivity": 0, "susceptibility": 0.1 },
    { "id": "wanedS", "ann:label": "Waned natural immunity", "infectivity": 0, "susceptibility": 0.7 },
    { "id": "wanedV", "ann:label": "Waned vaccine immunity",  "infectivity": 0, "susceptibility": 0.5 }
  ],
  "initialState": "S",
  "transmissions": [
    { "id": "infection_I_S", "entryState": "S", "exitState": "I",
      "contactState": "I", "transmissibility": 1.0 },
    { "id": "infection_I_V", "entryState": "V", "exitState": "I",
      "contactState": "I", "transmissibility": 1.0 }
  ],
  "transitions": [
    { "id": "I_to_R", "entryState": "I", "exitState": "R",
      "probability": 1, "dwellTime": { "gamma": { "alpha": 1.0, "beta": 5.0 } } },
    { "id": "R_to_wanedS", "entryState": "R", "exitState": "wanedS",
      "probability": 1, "dwellTime": { "gamma": { "alpha": 1.0, "beta": 183.0 } } }
  ]
}
```

Three things stand out.

**States carry `infectivity` and `susceptibility` as numbers.** Vaccine efficacy, waning, and partial immunity are all two numbers per state, not multipliers scattered through transmission code. `V` has susceptibility 0.1 and `wanedV` has 0.5, and that *is* the vaccine model.

**Transmission and transition are separate, named objects.** A `transmission` names an `entryState`, an `exitState`, a `contactState`, and a `transmissibility`. A `transition` names an `entryState`, an `exitState`, a `probability`, and a **`dwellTime` distribution**. This is epipack's spontaneous/neighbor-induced split, as data.

**Dwell times are distributions, declared per transition**, such as `{"gamma": {"alpha": 1.0, "beta": 5.0}}`. MEmilio needed separate LCT and IDE model families for this; EpiHiper makes it a field.

### Interventions are a small declarative language

The intervention file has four sections (`variables`, `sets`, `triggers`, `interventions`), and together they are a language of rules.

**Sets** are built with union and intersection from conditions on nodes and edges:

```json
{
  "id": "school_edges",
  "content": {
    "operation": "union",
    "sets": [
      { "elementType": "edge",
        "left":  { "edge": { "property": "targetActivity", "feature": "activityType" } },
        "operator": "==",
        "right": { "value": { "trait": "activityTrait", "feature": "activityType", "enum": "school" } } },
      { "elementType": "edge",
        "left":  { "edge": { "property": "sourceActivity", "feature": "activityType" } },
        "operator": "==",
        "right": { "value": { "trait": "activityTrait", "feature": "activityType", "enum": "school" } } }
    ]
  }
}
```

**Variables** are named mutable state with scope and reset behavior:

```json
{ "id": "week_day", "initialValue": 0, "scope": "local", "reset": 7 }
```

**Triggers** are boolean expressions over observables and variables, mapped to intervention ids:

```json
{ "trigger": { "and": [
      { "left": { "observable": "time" }, "operator": ">=", "right": { "value": { "number": 0 } } },
      { "left": { "variable": { "idRef": "week_day" } }, "operator": "==", "right": { "value": { "number": 5 } } }
  ] },
  "interventionIds": ["close_schools"] }
```

**Interventions** bind a target set to a list of operations:

```json
{ "ann:id": "maintain_week_day",
  "trigger": { "value": true },
  "target": { "set": { "idRef": "%empty%" } },
  "once": [ { "operations": [
      { "target": { "variable": { "idRef": "week_day" } }, "operator": "+=",
        "value": { "number": 1 } } ] } ] }
```

So "close schools on Fridays" is a variable counting the day of the week that resets every 7, a set built from edge activity types, a trigger, and an intervention acting on the set. **No code.**

## Core abstractions

| Concept | EpiHiper name | Notes |
|---|---|---|
| Disease state | `states[]` entry with `infectivity`, `susceptibility` | Relative transmission encoded as state properties |
| Transmission | `transmissions[]`: entry × exit × contact state × transmissibility | Named |
| Transition | `transitions[]`: entry × exit × probability × `dwellTime` distribution | Named; dwell time is a distribution |
| Contact network | edge list with activity types, durations, and traits | External file; supports temporal networks |
| Trait | `traits.json` | Typed enumerations for agent and edge features |
| Set | union and intersection of conditions on nodes and edges | Computed, named, reusable |
| Variable | named, scoped (`local`/`global`), with `reset` period | Mutable model-level state |
| Trigger | boolean expression over observables, variables, and sets | AND/OR trees |
| Intervention | `target` set × `once`/`sampling` × `operations` | Operations mutate variables, node/edge properties, or health states |
| Scenario | `scenario.json` | Binds config, disease model, network, initialization, and interventions |

## Strengths

- **Both the disease model and the interventions are data**, and this is the only framework in the review of which that is true. EMOD makes interventions data; camdl and odin make the disease data.
- **A dwell-time distribution for each transition**: `{"gamma": {"alpha": ..., "beta": ...}}`, which takes MEmilio four model families.
- **Relative transmission as state properties.** `infectivity` and `susceptibility` per state handle vaccination, waning, and partial immunity in one way.
- **Real sets over the network.** Named, reusable sets of nodes and edges, built from conditions on their traits and combined by union and intersection. This is the most capable targeting in the review, going beyond EMOD's `TargetingLogic` by working on *edges* as well as nodes, and with set operations.
- **Named variables with scope and automatic reset**, enough for day-of-week logic, counters, and policies that remember.
- **Triggers** written as true-or-false expressions over observables and variables, separate from the interventions they start.
- **Published JSON schemas** for every document, referenced in the files themselves.
- **An annotation convention.** The `ann:` prefix (`ann:label`, `ann:id`) marks notes for people, so documentation lives in the model without being mistaken for it.
- **National scale**, with MPI and OpenMP builds and CDC Scenario Modeling Hub use.

## Limitations

- **The longest JSON in the review.** The "close schools on Fridays" example is roughly 200 lines, and one comparison is a nine-line object (`left` / `operator` / `right`, each nested). The expressive power is real, and it is hard to write by hand.
- **Transmission has a fixed form.** Transmissibility is one number per rule, scaled by state infectivity and susceptibility and by edge weight. Dose response, within-host viral load, and density dependence cannot be expressed.
- **No dimensional types.** Dwell times, transmissibilities, and times are bare numbers.
- **Needs a synthetic contact network as input**, which for most users means the Biocomplexity Institute's US datasets. The network is a file, not something a user can describe.
- **Heavy build**: C++, CMake, PostgreSQL, MPI/OpenMP, git submodules.
- **Few documented users outside UVA** (6 stars, 2 forks at last count), despite its national-scale use.
- **No observation model and no inference.**
- **Not practical to write by hand.** The format is realistically generated by software, with no published language above it.

## Implications for the lingua franca

1. **EpiHiper is the closest existing thing to an agent-based model written entirely as data.** Structure and policy are both data. This is unique in the review, and shows that the "no code" goal is reachable for agents, not only compartments.
2. **Take `infectivity` and `susceptibility` as state properties.** Two numbers on a *state* are compact and easy to read, and they combine correctly: a new state with new values needs no change elsewhere. Starsim's `rel_sus` / `rel_trans` are the per-agent version of the same idea.
3. **Take sets, variables, triggers, and operations for interventions.** With EMOD's four-part campaign structure, this is a nearly complete design: named **sets** as targets (over agents *and* contacts), **variables** for the state of a policy, **triggers** on observables, and **operations** as actions. Covering real policies takes rules like these.
4. **A declared dwell-time distribution per transition** is the neatest answer in the review to the exponential-dwell-time problem. Adopt it, and let each solver realize it: Erlang stages in an ODE (as camdl's `via erlang` does), direct sampling for agents, and a memory kernel in an IDE. **One declaration, a different implementation per paradigm: this is what a lingua franca is for.**
5. **Adopt the annotation prefix.** `ann:label` and `ann:id` separate notes for people from what the software acts on, and unlike comments they are kept when the file is read and rewritten.
6. **EpiHiper is the strongest evidence for a readable language with a data form underneath.** It has arguably the best intervention *model* in the review, in a form that is the hardest to write. A readable language could say the same in a few lines. EMOD and EMULSION teach the same lesson.

# epymorph

|  |  |
|---|---|
| **Language** | Python (SymPy for the disease model) |
| **Paradigms** | Metapopulation: compartmental dynamics within nodes, discrete movement between them |
| **Specification style** | Composition of independently declared parts: IPM (disease) × MM (movement) × scope (geography) × initializer × parameters |
| **Version reviewed** | current `main` |
| **License** | (see repository) |
| **Code** | <https://github.com/NAU-CCL/epymorph> |
| **Docs** | <https://docs.epimorph.org> |
| **Paper** | — (EpiMoRPH project, NAU) |

## What it's for

epymorph is a spatial metapopulation framework built on the idea that **disease, movement, and geography are three independent things to be combined**. You can swap the disease without touching the movement model, swap the movement model without touching the disease, and re-run either over different geography with the same code.

This is the clearest separation of parts in the review, and the lingua franca's paradigm independence is a similar idea along a different axis.

## How a model is specified

Four parts and a container.

**The IPM (Intra-Population Model)**: the disease process, as compartments plus symbolic edges:

```python
from epymorph.kit import *
from sympy import Max

class SIRS(CompartmentModel):
    compartments = [
        compartment("S"),
        compartment("I"),
        compartment("R"),
    ]

    requirements = [
        AttributeDef("beta",  type=float, shape=Shapes.TxN, comment="infectivity"),
        AttributeDef("gamma", type=float, shape=Shapes.TxN, comment="progression I→R"),
        AttributeDef("xi",    type=float, shape=Shapes.TxN, comment="progression R→S"),
    ]

    def edges(self, symbols):
        [S, I, R] = symbols.all_compartments
        [β, γ, ξ] = symbols.all_requirements
        N = Max(1, S + I + R)   # avoid division by zero
        return [
            edge(S, I, rate=β * S * I / N),
            edge(I, R, rate=γ * I),
            edge(R, S, rate=ξ * R),
        ]
```

**The MM (Movement Model)**: one or more `MovementClause`s, each declaring what it needs, when it fires, which sub-step travelers leave on, and when they return:

```python
class CentroidsClause(MovementClause):
    requirements = (
        AttributeDef("population", int, Shapes.N),
        AttributeDef("centroid", CentroidType, Shapes.N),
        AttributeDef("phi", float, Shapes.Scalar, default_value=40.0),
        AttributeDef("commuter_proportion", float, Shapes.Scalar, default_value=0.1),
    )

    predicate = EveryDay()
    leaves  = TickIndex(step=0)
    returns = TickDelta(step=1, days=0)
```

**The scope**, a `GeoScope` (US states, counties, census tracts), and **ADRIOs**, which fetch the data each requirement needs from real sources (US Census, ACS, and others), with caching.

**The RUME** (Runnable Modeling Experiment) binds them:

```python
rume = SingleStrataRUME.build(ipm=SIRS(), mm=Centroids(), scope=..., init=..., params=...)
```

A `MultiStrataRUME` composes several IPM/MM/params triples (a "GPM") into one experiment: the mechanism for multi-strain or multi-population models.

## Core abstractions

| Concept | epymorph name | Notes |
|---|---|---|
| Disease process | `CompartmentModel` (IPM) | Compartments + symbolic edges; validated at subclass definition time |
| Transition | `edge(src, dst, rate=expr)` | SymPy expression; also `fork(...)` for branching |
| Data requirement | `AttributeDef(name, type, shape, default_value, comment)` | **Declared, with a type and shape** |
| Shape | `Shapes.Scalar`, `Shapes.N`, `Shapes.T`, `Shapes.TxN`, `Shapes.NxN`, … | Time × node × arm, checked |
| Movement | `MovementModel` of `MovementClause`s | Each with `requirements`, `predicate`, `leaves`, `returns` |
| Timing | `EveryDay()`, `TickIndex(step=)`, `TickDelta(step=, days=)` | Sub-daily ticks; travelers leave on one and return on another |
| Geography | `GeoScope`: states, counties, tracts | With real census hierarchies |
| Data source | ADRIO | Fetches an attribute from an external source, with caching and an inspection report |
| Stratum | `GPM` (Geo-Population Model) | An (IPM, MM, init, params) bundle |
| Experiment | `RUME`: `SingleStrataRUME` / `MultiStrataRUME` | The runnable whole |
| Fitting | `epymorph.parameter_fitting` | Particle-filter-based |

## The requirement/ADRIO contract

This is the idea most worth taking. An IPM does not read data; it **declares what it needs**: a name, a type, a shape, an optional default, and a comment. So does every movement clause. The RUME then finds each one, from values the user supplied or from ADRIOs that fetch real data.

The effects:

- A model states the data it needs *as data*, so this can be checked before anything runs.
- The same disease model runs over any geography that can supply the requirements.
- Shape checks (`Shapes.TxN`, `Shapes.N`, `Shapes.Scalar`) catch arrays of the wrong size before running.
- Every value's source is clear: a named ADRIO, or the user.
- `data_usage.py` can estimate how much data an experiment will fetch before fetching it.

Nothing else in the review declares a model's data needs this way. In most frameworks, the model code fetches what it needs.

## Time

The timeline is `TimeFrame`, and movement runs on **sub-daily ticks**: a clause states which tick travelers leave on (`TickIndex(step=0)`) and when they come back (`TickDelta(step=1, days=0)`). This gives commuting (leave in the morning, mix at the destination, return in the evening) without continuous time.

Disease rates are per-day floats with declared shapes. There are no dimensional types, but **shapes** do a related job: `Shapes.TxN` says a parameter varies by time and node, and passing one number where `TxN` is required is an error.

## Strengths

- **Disease, movement, and geography are independent**, the clearest separation of parts in the review.
- **Declared data requirements** with types and shapes, checked before the run.
- **ADRIOs.** Fetching from real sources (census, ACS) with caching, inspection, and a record of sources. Epydemix bundles its data; these fetch it on request.
- **Symbolic transitions.** IPM edges are SymPy expressions over declared symbols, so the disease model can be read, differentiated, and drawn.
- **Checks when the class is defined**, so a malformed IPM fails at import and not during a run.
- **Sub-daily movement timing** with leave and return, the right model for commuting, and unusual.
- **Several strata in one experiment**, via `MultiStrataRUME`.
- **Checked shapes** that catch size errors before running.

## Limitations

- **The IPM is a Python class**, not a document, and its structure is not designed to be saved.
- **No dimensional types.** Shapes are checked, and units are not.
- **Movement clauses are code.** The `predicate` / `leaves` / `returns` declaration is elegant, but the movement itself (the dispersal kernel, the row normalization) is an ordinary Python method.
- **Focused on the US.** GeoScope and the ADRIOs are built around US Census geography and data. Using it elsewhere means writing ADRIOs.
- **Compartmental within nodes.** No individual agents; heterogeneity is by node and stratum.
- **No intervention vocabulary.** Interventions are time-varying parameters (which the `TxN` shape supports well) or custom code.
- **Limited adoption.** It is well designed but has few users, so its ideas have not been tested at scale.

## Implications for the lingua franca

1. **Adopt declared data requirements.** A model that says "I need `beta`, a float, shaped time × node", with the data supplied separately, can be checked and moved, and its sources are known. This is the most transferable idea here, and it goes beyond geography: every module (disease, network, demography, intervention) could state its data needs the same way. This also helps with Starsim 3's connectors, since declared requirements show dependencies between modules.
2. **Adopt checked shapes.** `Scalar` / `N` / `T` / `TxN` / `NxN` catch errors that dimensional types would not. Dimensions say *what a number means*; shapes say *how many there are, and along which axis*. A language spanning agents, patches, strata, and time needs both.
3. **Follow the three-way division.** Disease × movement × geography for metapopulations generalizes to disease × contact structure × population in general. Starsim's routes aim at the same thing for agents; epymorph shows a fuller separation.
4. **Timing within a step is worth expressing.** "Leave on tick 0, return on tick 1" is a compact way to say commuting, and it differs from a single `dt` and from Starsim's per-module timelines. The language should be able to say this.
5. **Check at definition, not during a run.** epymorph checks an IPM when the class is defined, and camdl when it compiles. The principle of checking as early as possible should be explicit in the design.
6. **Say where data comes from.** Epymorph's ADRIOs, Epydemix's bundled data, and camdl's `read(...)` all show the need to express *where a parameter's value comes from*, as well as its value. That belongs in the design with the model structure.

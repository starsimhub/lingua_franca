---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# LASER

|  |  |
|---|---|
| **Language** | Python with Numba (and C/OpenMP where needed) |
| **Paradigms** | Agent-based, spatial/metapopulation, discrete time; large-scale (national to continental) |
| **Specification style** | A model is a `LaserFrame` of agent properties plus a list of **components**, each with an init and a step function |
| **Version reviewed** | `laser-core` 0.6.x |
| **License** | MIT |
| **Code** | <https://github.com/laser-base/laser-core> |
| **Docs** | <https://docs.idmod.org/projects/laser/en/latest/> |
| **Paper** | — |
| **Ecosystem** | `laser-core` plus disease packages: `laser-polio`, `laser-measles` |
| **Note** | Not in the landscape database; included because it is an IDM framework whose design point differs materially from Starsim's |
| **Moving to Starsim** | [Conversion guide](https://starsim.org/v4/user_guide/conversion/laser.html) |

## What it's for

LASER is IDM's engine for spatial agent-based models at eradication scale: national polio and measles models over thousands of nodes and hundreds of millions of agent-timesteps. Its design follows almost entirely from the need for speed, which gives a way of writing models worth comparing with Starsim's.

The stated principle:

> The core principle of LASER's design is to optimize computational efficiency by aligning the system with what modern CPUs and GPUs excel at — performing billions of floating-point operations per second — while minimizing costly operations like runtime memory allocation and random memory access.

## How a model is specified

The population is a `LaserFrame`: a mutable columnar table, "similar to a db table or a Pandas DataFrame":

```python
from laser_core import LaserFrame

class Model:
    pass

model = Model()
model.population = LaserFrame(capacity=1000)
model.population.add_scalar_property("disease_state", dtype=np.int32, default=0)
model.population.add_vector_property("position", length=3, dtype=np.float32)
start, end = model.population.add(10)
```

Behavior is added as **components**, each with an initializer and a `step` function acting on one or more properties. A script puts them together:

```python
model.components = [VitalDynamics_ABM, DiseaseState_ABM, Transmission_ABM, RI_ABM, SIA_ABM]
```

(These names are from `laser-polio`, the reference disease model.) Each component works through its columns once per timestep.

Parameters are a `PropertySet`: a dict with dot access and `+` composition:

```python
ps1 = PropertySet({'immunity': 'high', 'region': 'north'})
ps2 = PropertySet({'infectivity': 0.7})
combined = ps1 + ps2
```

## The four design principles

From the architecture document, these explain nearly everything else:

1. **Preallocate memory.** All arrays are set up at the start, and nothing is added during the run.
2. **Sequential array access.** Go through the arrays in order, ideally once per timestep, which is fast.
3. **Fixed data structures.** Agents are marked dead and not removed, and "preborn" agents are in the array from the start and activated at the right time. The array never changes size.
4. **Time-specific data slots.** Outputs have a slot per timestep and location, set up in advance.

So the population has a fixed capacity computed up front (`calc_capacity`), births activate existing rows, deaths are flags, and results are arrays indexed by (timestep, node). A model has to state its maximum size and output shape before it runs, which is a limit, and also a form of declaration.

## Core abstractions

| Concept | LASER name | Notes |
|---|---|---|
| Population | `LaserFrame` | Columnar; `add_scalar_property`, `add_vector_property`, `add`, `sort`, `squash`; HDF5-backed |
| Agent property | a column | Typed (`dtype`), with a default |
| Node / patch | `node_id`, a built-in property | Geospatial focus is in the core; single-node models set it uniformly |
| Component | init function + `step` function | The unit of behavior |
| Parameters | `PropertySet` | A dict with dot access, combined with `+`, saved as JSON |
| Migration | `laser_core.migration` | `gravity`, `competing_destinations`, `stouffer`, `radiation`, `distance`, `row_normalizer`: a library of published spatial interaction models |
| Scheduling | `SortedQueue` | Priority queue for scheduled events (non-disease deaths) |
| Demographics | `laser_core.demographics` | Age pyramids, Kaplan–Meier estimators, date-of-birth / expected-date-of-death initialization |

## What distinguishes it from Starsim

Both are IDM Python agent-based frameworks, so the differences are design choices:

| | Starsim | LASER |
|---|---|---|
| **Agent lifecycle** | UIDs added and removed; `auids` view of the living | Fixed capacity; preborn rows activated; dead rows flagged |
| **State ownership** | Each module declares its own states | One shared `LaserFrame`; components add columns to it |
| **Time** | Typed (`dur`/`per`/`prob`/`freq`), per-module timelines, calendar dates | Unitless integer timesteps |
| **Transmission** | Routes: networks and mixing pools | Node-level force of infection with a migration matrix |
| **Spatial** | Optional, via spatial networks, and `ss.geo` in Starsim 4 | Built in: `node_id` is a core property, with a migration library |
| **Module form** | `ss.Module` with a declared lifecycle and locked state | A component is an object with a `step` function |
| **Results** | Declared `ss.Result` objects with labels and timevecs | Preallocated arrays by (timestep, node) |
| **Scale target** | 10⁴–10⁶ agents | 10⁷–10⁹ agent-timesteps |

The migration library is the clearest difference: `gravity`, `competing_destinations`, `stouffer`, and `radiation` are the four standard published spatial-interaction models, implemented and checked. Nothing else in this review includes them, and Starsim 4's geography draws on this work.

## Time

Unitless integer timesteps, with dates left to the disease packages (`laser-polio` has date utilities in `utils.py`). There are no dimensional types.

Scheduling uses `SortedQueue`, a priority queue of future events. `individual`'s `TargetedEvent` and Starsim's `ti_*` arrays do the same thing for the same reason: to avoid checking all agents for something that applies to few.

## Strengths

- **Stated performance principles**, with the whole design following from them. This is rare, and it makes the tradeoffs easy to judge.
- **A migration model library**: gravity, competing destinations, Stouffer, and radiation, with distance calculation, row normalization, and parameter checks. This is the best set of spatial-interaction models in the review.
- **Space in the core.** `node_id` is a built-in property.
- **Agents stored by column** (`LaserFrame`), with typed properties, HDF5 storage, and `sort`/`squash`.
- **Preallocation**: nothing added or resized during a run, so performance at scale is predictable.
- **Preborn agents**: an elegant way to handle births without growing the population arrays.
- **`PropertySet`**: parameter sets that combine, and save as JSON.
- **Demographic setup tools**: age pyramids, Kaplan–Meier, date-of-death sampling.
- **A small core.** `laser-core` is a handful of modules, and the disease models live outside it.

## Limitations

- **No epidemiological vocabulary in the core.** Diseases, transmission, networks, and interventions are in `laser-polio` and `laser-measles`, written per model. `laser-core` is closer to `individual` than to Starsim in what it provides.
- **Components declare nothing.** A component does not state which properties it reads or writes, has no lifecycle beyond init and step, and is ordered only by its place in the list.
- **Order matters, and is not explained.** The list is the order of execution, and nothing states what that order depends on.
- **Shared state.** All components write columns of one `LaserFrame`. This is fast, and it is what Vivarium's `PopulationView` and value pipelines exist to control.
- **Unitless time**, no dates in the core, no dimensional types.
- **Capacity has to be estimated up front**, and a model that exceeds it fails.
- **The architecture document suggests "declarative behavior is encouraged, with step functions optionally described in SQL-like syntax"**, an interesting idea, but what exists is Numba/NumPy code.
- **Small user base**: essentially IDM and collaborators, with two disease packages.
- **No inference in the core**; calibration lives in the disease packages.

## Implications for the lingua franca

1. **Refer to the migration models by name.** Gravity, radiation, Stouffer, and competing destinations are the published models for spatial interaction, and a metapopulation language should be able to say "the mobility matrix is a gravity model with parameters k, a, b, c", as well as "here is a matrix". This matches EpiModel's networks from target statistics: **a structure should be describable by the model that generates it.**
2. **LASER and Starsim mark out the range of agent-based designs at IDM**, and their differences are the design questions: fixed capacity versus changing UIDs, a shared state table versus states owned by modules, unitless steps versus typed time, and space in the core versus space as a network. A language that has to run on both needs to know which of these change a model's *meaning* (typed time, state ownership) and which are only *how it runs* (preallocation, flagging the dead). Most are the latter, which is encouraging, and worth confirming.
3. **The language can make preallocation automatic.** If a model declares its maximum population, nodes, and outputs, a solver can preallocate without the modeler thinking about it.
4. **Shared state is at its most risky here**, which supports the point made under Vivarium and Starsim: components writing any column of a shared table is fast and hard to analyze. Declaring reads and writes costs nothing at run time, and would keep LASER's speed while allowing that analysis.
5. **"SQL-like step functions" are worth pursuing, as LASER's authors already saw the need.** A step that filters agents by a condition, samples some, and updates a column is the "select a set, thin it, act" operation from the `individual` entry, and it can be written as a declaration. LASER's own document supports this form.
6. **Space deserves built-in status.** LASER puts `node_id` in the core, epymorph has geography in the RUME, and MEmilio has graph-ODE and traveler states. Starsim 3 treated space as one network among several, and Starsim 4 adds a [geography module](https://starsim.org/v4/user_guide/populations_geography.html) (`ss.geo`). For eradication or subnational planning, space is not just one more stratification, and the design should decide deliberately how to treat it.

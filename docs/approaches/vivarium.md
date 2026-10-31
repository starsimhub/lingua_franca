# Vivarium

|  |  |
|---|---|
| **Language** | Python (pandas-backed state table) |
| **Paradigms** | Agent-based microsimulation, discrete time; disease as an explicit state machine |
| **Specification style** | Components assembled in a YAML model specification; behavior written as Python `Component` subclasses |
| **Version reviewed** | 4.1.6 |
| **License** | BSD-3-Clause |
| **Code** | <https://github.com/ihmeuw/vivarium-suite> (the `ihmeuw/vivarium` repository is **archived**) |
| **Docs** | <https://vivarium-engine.readthedocs.io/> |
| **Paper** | — |
| **Note** | The package was renamed and moved during this review: `vivarium` → `vivarium-engine`, import path `vivarium` → `vivarium.engine`, source now in the `vivarium-suite` monorepo. The archived `v4.1.6` is the code reviewed here. |

## What it's for

Vivarium is IHME's microsimulation framework: individual-level simulation of health outcomes driven by Global Burden of Disease data, used for intervention and forecasting analyses. Its focus is risk factors, chronic disease, and health systems, not infectious disease. It is here for its **design**, which solves a problem that infectious disease frameworks handle less well:

**how can components written separately modify each other's quantities without interfering?**

## How a model is specified

A YAML specification lists components; the components are Python classes.

```yaml
components:
    vivarium_examples.disease_model:
        population:
            - BasePopulation()
            - Mortality()
        disease:
            - SIS_DiseaseModel('diarrhea')
        risk:
            - Risk('child_growth_failure')
            - RiskEffect('child_growth_failure', 'infected_with_diarrhea.incidence_rate')
        intervention:
            - TreatmentEffect('treatment', 'infected_with_diarrhea.remission_rate')
configuration:
    randomness:
        key_columns: ['entrance_time', 'age']
```

Note `RiskEffect('child_growth_failure', 'infected_with_diarrhea.incidence_rate')`: a component whose entire declared purpose is *"this risk modifies that rate"*, with the target named as a string. That is the design idea.

A component:

```python
class DiseaseTransition(Transition):
    def setup(self, builder: Builder) -> None:
        self.base_rate = builder.configuration[self.cause_key][self.measure]
        builder.value.register_rate_producer(
            self.rate_name,
            source=self._risk_deleted_rate,
            required_resources=[self.joint_paf_pipeline],
        )

    def _probability(self, index) -> pd.Series:
        effective_rate = self.population_view.get(index, self.rate_name)
        return pd.Series(rate_to_probability(effective_rate))
```

## The value pipeline — the idea worth taking

Vivarium's core mechanism is the **value pipeline**. A component *registers a producer* for a named quantity:

```python
builder.value.register_rate_producer("diarrhea.incidence_rate", source=self._base_rate)
```

Other components *register modifiers* on that name:

```python
builder.value.register_value_modifier("diarrhea.incidence_rate", modifier=self._apply_risk_effect)
```

When the value is requested, the framework calls the source, then applies every registered modifier in a defined order, combining them with a declared **combiner** and finishing with a declared **post-processor** (`list_combiner`, `union_post_processor`, and others).

The consequences:

- A component that produces a rate does not know who modifies it.
- A component that modifies a rate does not know who produces it: only its name.
- **Multiple modifiers compose by a declared rule**, not by whoever ran last.
- The dependency graph between components is explicit (`required_resources=[...]`) and used to order setup.

Compare Starsim 3's connectors, where a connector writes `hiv.rel_trans[coinf] = 2.0` directly, which is general, but the last write wins. (Starsim 4's `ss.modify()` owes a lot to this pipeline.) Vivarium's mechanism is more limited, and for that reason two risk factors raising an incidence rate combine correctly without either knowing about the other.

Population attributable fractions show this at work: several risks each add a PAF to a joint pipeline via `list_combiner`, the `union_post_processor` combines them into one joint PAF, and the rate producer divides it out. That is a real epidemiological rule, declared once.

## The lifecycle

Vivarium's other structural idea is a **named lifecycle with priorities**. A component may implement:

`setup` → `on_post_setup` → then per timestep: `on_time_step_prepare` → `on_time_step` → `on_time_step_cleanup` → `on_collect_metrics` → finally `on_simulation_end`.

Each phase has a priority (`time_step_priority`, `collect_metrics_priority`, …, default 5), so order *within* a phase is declared. Breaking the sequence raises `LifeCycleError`: a component cannot, for example, register a producer after setup has closed.

This is more structured than Starsim's `Loop` (which can be read and reordered, but has one step phase per module) and much more than EpiModel's `module.order`.

## Core abstractions

| Concept | Vivarium name | Notes |
|---|---|---|
| Population | a pandas DataFrame: the **state table**, one row per simulant | Columns are attributes |
| Access control | `PopulationView` | A component declares which columns it may read and write |
| Component | `Component` subclass | With `sub_components`, `CONFIGURATION_DEFAULTS`, lifecycle hooks and priorities |
| Value | named pipeline with a source, modifiers, a combiner and a post-processor | The composition mechanism |
| Lookup table | `builder.lookup`, `data_sources` in config | Data indexed by age, sex, year, location: the GBD-data interface |
| Disease | `Machine` / `State` / `Transition` / `TransientState` | An explicit state machine in `framework/state_machine.py` |
| Randomness | `builder.randomness` with `key_columns` | Common random numbers keyed on simulant attributes |
| Observer | `Component` registering observations | The results system |
| Artifact | `builder.data` over an HDF artifact | Pre-extracted input data, versioned |

## Randomness

`randomness: key_columns: ['entrance_time', 'age']` configures a **common-random-numbers scheme keyed on simulant attributes**: a simulant's random draw for a given decision is a deterministic function of its key columns and the decision's name. Two scenarios that differ only in an intervention give the same simulant the same draw.

Starsim gets the same capability from per-agent slots and hashed distribution names, arrived at independently. Here it is a setting.

## Strengths

- **The value pipeline.** Named quantities with a source, registered modifiers, a declared combiner, and a declared post-processor. This is the best answer in the review to "how do independent components modify each other's quantities", and it fills a gap in Starsim 3.
- **Declared dependencies** (`required_resources=[...]`), used to order setup and detect cycles.
- **A structured lifecycle with priorities.** Phases are named, order within a phase is declared, and breaking the sequence is an error.
- **`PopulationView`**: a component states which columns of the state table it reads and writes, and the framework enforces it. Nothing else in the review has this.
- **An explicit disease state machine** (`Machine` / `State` / `Transition` / `TransientState` / `Trigger`).
- **Common random numbers keyed on declared attributes**, set in the model file.
- **Lookup tables and data artifacts** as the standard way to bring in data, with `data_sources` in `CONFIGURATION_DEFAULTS`.
- **Components listed in YAML**, so how a model is put together is data, even though behavior is code.
- **Sub-components**, so that models can be nested.

## Limitations

- **Recently renamed and moved.** `vivarium` → `vivarium-engine`, in a monorepo, with the reviewed repository archived. Code using the old import path has to change.
- **Not an infectious disease framework.** No transmission, contact structure, networks, or force of infection. `SIS_DiseaseModel` in the examples is driven by an incidence *rate*, not contact with infectious simulants.
- **Behavior is Python.** The YAML lists components but does not define them. Disease structure, rates, and effects are code.
- **pandas state table.** Readable, but slow compared with array-based frameworks (Starsim, LASER, epiworld), and memory-hungry at scale.
- **Steep learning curve.** Pipelines, lifecycle phases, population views, lookup tables, artifacts, and resources are a lot to learn before the first line of epidemiology.
- **Built around IHME and GBD data.** Data interfaces assume artifacts indexed by age, sex, year, and location.
- **No observation model or inference.**
- **Sparse public documentation** of how value pipelines behave, given their importance.

## Implications for the lingua franca

1. **Adopt the value pipeline for effects across modules.** This is the most important point here. A co-infection, risk factor, intervention, or seasonal forcing should be able to modify a quantity owned by another module *as a declaration*, with a stated rule for combining. Vivarium's form (**a named quantity, one producer, many registered modifiers, a declared combiner**) solves the Starsim 3 connector problem of hidden dependencies and the last write winning. You can also ask "what modifies `diarrhea.incidence_rate`?" and get an answer.
2. **Declare the combination rule, because it is a modeling decision.** Two interventions each reducing transmission by 40% might multiply (`0.6 × 0.6`) or add (`1 − 0.8`), and the choice changes the answer. Vivarium makes the combiner a named object, `epidemics` chose additive globally and documented why, and most frameworks leave it to the order of operations. **The lingua franca should let this be stated.**
3. **Adopt declared read and write access to state.** A component says which state it reads and writes, and the framework enforces it. Where the goal is no hidden behavior, a module that can silently write another module's state is a gap. epymorph's `AttributeDef` does this for inputs; this extends it to writes.
4. **Named phases with declared priorities beat a flat list of steps.** `time_step_prepare` → `time_step` → `time_step_cleanup` → `collect_metrics` gives components a place for things, and priorities settle the rest. With `individual`'s queued updates (which make order within a phase irrelevant), this is a good target.
5. **Common random numbers keyed on declared attributes travel well.** Starsim keys on an agent slot; Vivarium keys on `['entrance_time', 'age']`, which can be configured and has meaning across populations that are not the same agents. This generalizes better to scenarios with different population sizes, which Starsim's slots handle less well.
6. **A framework can be declarative about *how parts fit together* and still use code for *behavior*.** Vivarium's YAML lists components, and the components are Python. This is a coherent and common position (Starsim's dict form, EMOD's campaigns over a C++ engine). The lingua franca aims further, and Vivarium shows what the fallback looks like and how far it gets you.

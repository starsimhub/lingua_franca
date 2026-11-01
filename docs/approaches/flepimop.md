# flepiMoP

|  |  |
|---|---|
| **Language** | Python (simulation) and R (inference and post-processing) |
| **Paradigms** | Metapopulation compartmental: deterministic (RK4) or stochastic, with a full inference and forecasting pipeline |
| **Specification style** | **One YAML configuration** spanning compartments, transitions, seeding, modifiers, outcomes, and fitting |
| **Version reviewed** | current `main` |
| **License** | (see repository) |
| **Code** | <https://github.com/HopkinsIDD/flepiMoP> |
| **Docs** | `documentation/` in the repository |
| **Paper** | Lemaitre et al. (2024), *Epidemics* 47: 100753, [10.1016/j.epidem.2024.100753](https://doi.org/10.1016/j.epidem.2024.100753) |
| **Users** | Johns Hopkins IDD; US COVID-19 and influenza Scenario Modeling Hub submissions |
| **Moving to Starsim** | [Conversion guide](https://starsim.org/v4/user_guide/conversion/flepimop.html) |

## What it's for

flepiMoP (FLexible EPIdemic MOdeling Pipeline) is the production pipeline behind a large share of US COVID-19 and influenza scenario-hub output. It is less a modeling *framework* than a **configuration language for a modeling pipeline**. That is why it is in this review: it is the most complete example of a whole modeling workflow, from model structure through interventions to likelihood and inference, written as one document.

## How a model is specified

One YAML file. The whole SIR-in-two-subpopulations example:

```yaml
name: sample_2pop
start_date: 2020-02-01
end_date: 2020-08-31
nslots: 1

subpop_setup:
  geodata: model_input/geodata_sample_2pop.csv
  mobility: model_input/mobility_sample_2pop.csv

initial_conditions:
  method: SetInitialConditions
  initial_conditions_file: model_input/ic_2pop.csv
  allow_missing_subpops: TRUE
  allow_missing_compartments: TRUE

compartments:
  infection_stage: ["S", "E", "I", "R"]

seir:
  integration:
    method: rk4
    dt: 1
  parameters:
    sigma: {value: 1 / 4}
    gamma: {value: 1 / 5}
    Ro:    {value: 2.5}
  transitions:
    - source: ["S"]
      destination: ["E"]
      rate: ["Ro * gamma"]
      proportional_to: [["S"], ["I"]]
      proportion_exponent: ["1", "1"]
    - source: ["E"]
      destination: ["I"]
      rate: ["sigma"]
      proportional_to: ["E"]
      proportion_exponent: ["1"]
    - source: ["I"]
      destination: ["R"]
      rate: ["gamma"]
      proportional_to: ["I"]
      proportion_exponent: ["1"]
```

### Compartments are a product of axes

`compartments: {infection_stage: [S, E, I, R]}` declares one axis. Adding more axes gives the Cartesian product:

```yaml
compartments:
  infection_stage: ["S", "E", "I", "R"]
  vaccination_status: ["unvaccinated", "first_dose", "second_dose"]
  variant: ["wild", "alpha", "delta"]
```

and transitions are written over axis *lists*, so `source: [["S"], ["unvaccinated", "first_dose"], ["wild"]]` names a set of compartments rather than one. This is the MetaCast dimension algebra and the camdl `dimensions` block, expressed in YAML: stratification is declared, not written out.

### The transition form is unusually explicit

```yaml
- source: ["S"]
  destination: ["E"]
  rate: ["Ro * gamma"]
  proportional_to: [["S"], ["I"]]
  proportion_exponent: ["1", "1"]
```

A transition is a rate **times a product of compartment terms raised to exponents**. `proportional_to: [["S"], ["I"]]` with exponents `[1, 1]` gives `Ro * gamma * S * I` (frequency-normalized by the pipeline). Setting an exponent to a parameter name gives density-dependent or sub-exponential mixing.

This is more structured than a free rate expression and less structured than summer2's named flow kinds. The *form* of the rate is fixed (a coefficient times a product of powers of compartments), so the pipeline can work with it, while the coefficient stays an expression. This form is what makes automatic stratification over the axes practical.

### Modifiers are the intervention grammar

```yaml
seir_modifiers:
  scenarios: [Ro_lockdown, Ro_all]
  modifiers:
    Ro_lockdown:
      method: SinglePeriodModifier
      parameter: Ro
      period_start_date: 2020-03-15
      period_end_date: 2020-05-01
      subpop: "all"
      value: 0.4
    Ro_relax:
      method: SinglePeriodModifier
      parameter: Ro
      period_start_date: 2020-05-01
      period_end_date: 2020-08-31
      subpop: "all"
      value: 0.8
    Ro_all:
      method: StackedModifier
      modifiers: ["Ro_lockdown", "Ro_relax"]
```

A modifier names a **parameter**, a **date range**, a **subpopulation set**, and a **value**. `StackedModifier` composes them. `scenarios:` names which combinations to run. Modifier values can be given distributions, in which case they become fitted quantities.

This generalizes EpiModel's scenario tables: parameter × time window × place × value, with modifiers that combine, and the set of scenarios in the same file.

### Outcomes are a declarative observation model

```yaml
outcomes:
  method: delayframe
  outcomes:
    incidCase:
      source: {incidence: {infection_stage: "I"}}
      probability: {value: 0.5}
      delay:      {value: 5}
    incidHosp:
      source: {incidence: {infection_stage: "I"}}
      probability: {value: 0.05}
      delay:      {value: 7}
      duration:   {value: 10, name: currHosp}
    incidDeath:
      source: incidHosp
      probability: {value: 0.2}
      delay:       {value: 14}
```

This is flepiMoP's best idea. An observed outcome is **source × probability × delay × duration**, and outcomes can **chain**: `incidDeath` takes `incidHosp` as its source. So the whole surveillance cascade (infections → cases → hospitalizations → deaths, each with its own ascertainment probability and reporting delay) takes a dozen lines, and `duration` with a `name` also gives the prevalence series (`currHosp`).

`outcome_modifiers` then apply the same modifiers to outcome parameters, so "case ascertainment was lower before June 2020" is `parameter: incidCase::probability` over a date range.

## Core abstractions

| Concept | flepiMoP name | Notes |
|---|---|---|
| Compartment | Cartesian product of named axes | Stratification by declaration |
| Transition | source × destination × rate × `proportional_to` × `proportion_exponent` | Structured rate form |
| Subpopulation | `geodata` + `mobility` CSVs | Metapopulation from data files |
| Seeding | `initial_conditions` / `seeding` with named methods | Including importation draws |
| Modifier | parameter × date range × subpop × value; `StackedModifier` | How interventions are written |
| Scenario | named list of modifiers | Declared in the config |
| Outcome | source × probability × delay × duration, chainable | The observation model |
| Inference | `inference:` block with data, likelihoods, and priors | Distributions on parameters and modifier values |
| Slot | `nslots` | Parallel inference chains |

## Strengths

- **The entire workflow is one document**: structure, geography, seeding, interventions, observation model, scenarios, priors, and fitting. Nothing else in the review covers all this in one file.
- **The outcomes block.** Source × probability × delay × duration, chainable, with prevalence series from `duration`. The clearest treatment of the reporting cascade here.
- **Modifiers.** Parameter × time × place × value, combined by stacking, with named scenarios and fittable values: one mechanism for interventions, time-varying parameters, and inference targets.
- **Compartments as a Cartesian product of named axes**, with transitions written over parts of the axes, so a stratification is one line.
- **A structured rate form** (`rate` × ∏ `proportional_to`^`proportion_exponent`) that software can analyze, without limiting rates to a fixed list of kinds.
- **Calendar dates throughout.**
- **Production-proven at national scale**, in a setting where the model is rebuilt weekly against new data.
- **Deterministic and stochastic from the same configuration**, selected by the integration method.

## Limitations

- **YAML, with the usual tradeoffs**: expressions in strings (`rate: ["Ro * gamma"]`), no type checking, no editor support, deep nesting, and errors that come from the pipeline, not from a check of the file.
- **`proportional_to` / `proportion_exponent` is hard to read.** Getting frequency- versus density-dependence right through parallel lists of compartments and exponents is error-prone, and the notation does not make the meaning clear.
- **Configurations are large.** A scenario-hub config runs to hundreds of lines across included files, and splitting files (`*_part.yml`) is a convention, not part of the language.
- **Two languages.** Python simulates, R infers; a user needs both toolchains.
- **Compartmental metapopulation only.** No agents, no networks.
- **No dimensional types.** `rate: ["Ro * gamma"]` is a string; `delay: {value: 5}` is 5 of something.
- **A lot to set up**: batch scripts, cluster configuration, and a build system, as it began as a pipeline and not a library.
- **Documentation is aimed at hub participants**, and the configuration reference is spread across the repository.

## Implications for the lingua franca

1. **Adopt the outcomes block, nearly as it is.** Source × probability × delay × duration, chainable, is the observation model most epidemiological data needs, and it handles the cascade and both incidence and prevalence in one declaration. With camdl's `observations` block (which supplies the likelihood, `~ neg_binomial(...)`, and multiple data streams), this is close to a complete design: **flepiMoP says how the hidden process becomes an observed quantity; camdl says how that quantity relates to the data.** Both halves are needed.
2. **Adopt modifiers for time-varying parameters and scenarios.** Parameter × time window × place or population × value, with stacking, named scenario sets, and values that may be distributions and so fitted. This one mechanism covers EpiModel's scenario table, the contact dampings of Epydemix and MEmilio, and most of what a compartmental model needs from an intervention. It does *not* cover EMOD-style targeted individual interventions, which need an eligibility condition, and the design should treat these as two layers.
3. **The scenario set belongs in the model file.** `scenarios: [Ro_lockdown, Ro_all]` says what to run. camdl uses named scenarios, and flepiMoP combines modifiers. Either way, the counterfactuals are part of the model and not a shell script, which makes a scenario comparison reproducible.
4. **Consider a structured rate form.** flepiMoP's coefficient × ∏ compartment^exponent shows frequency- or density-dependence at a glance and can be stratified automatically, without a fixed list of rate kinds. It sits between summer2's named flow kinds and epipack's free reactions. Whether to take this middle position is a real design decision.
5. **One document for the whole workflow is the right ambition.** flepiMoP shows that structure, geography, interventions, observation, scenarios, and inference *can* live in one file, and that this makes a model rebuilt weekly manageable. camdl deliberately splits this across `.camdl` and `fit.toml`, to keep the model separate from its fitting settings. Both are reasonable. The lingua franca needs to choose, and flepiMoP is evidence that leaving too much to scripts costs reproducibility.
6. **YAML, for the fourth time in this review, shows the same tradeoff.** EMULSION, EMOD, EpiHiper, and flepiMoP all have sound ideas in a format that is hard to write by hand. This is a settled finding.

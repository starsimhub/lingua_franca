---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Atomica

|  |  |
|---|---|
| **Language** | Python engine; **models defined in Excel workbooks** |
| **Paradigms** | Compartmental, deterministic, with cascade analysis and budget optimization |
| **Specification style** | Two spreadsheets: a *framework* workbook defining structure, a *databook* supplying data |
| **Version reviewed** | current `master` |
| **License** | MIT |
| **Code** | <https://github.com/atomicateam/atomica> |
| **Docs** | <https://atomica.tools/docs> |
| **Paper** | None of its own; Optima TB, which runs on it: Goscé et al. (2021), *PLOS Comp Biol* 17(9): e1009255, [10.1371/journal.pcbi.1009255](https://doi.org/10.1371/journal.pcbi.1009255) |
| **Ecosystem** | Atomica / Optima (Burnet Institute; Optima Consortium for Decision Science) |
| **Moving to Starsim** | [Conversion guide](../models/atomica/index.qmd) |

## What it's for

Atomica is a compartmental engine for health-system and disease-program modeling, coupled to allocative-efficiency optimization: given a budget and a set of programs, what allocation minimizes burden? Its models are used for national HIV, TB, and health-system planning.

It is here because of **how models are written**. Atomica is the only framework in the review whose models are written in a spreadsheet, and it is by far the easiest route in the landscape from "domain expert who is not a programmer" to "running model".

## How a model is specified

A framework workbook with named sheets. Here is the shipped SIR framework, in full:

**Compartments**

| Code Name | Display Name | Is Source | Is Sink | Is Junction | Databook Page |
|---|---|---|---|---|---|
| sus | Susceptible | n | n | n | state_variables |
| inf | Infected | n | n | n | |
| rec | Recovered | n | n | n | |
| dead | Dead | n | y | n | |

**Transitions**: a *matrix*, rows = source, columns = destination, cells = the parameter driving that flow:

|  | sus | inf | rec | dead |
|---|---|---|---|---|
| **sus** | | foi | | susdeath |
| **inf** | | | recrate | susdeath,infdeath |
| **rec** | | | | susdeath |
| **dead** | | | | |

**Characteristics**: named aggregates and ratios over compartments:

| Code Name | Display Name | Components | Denominator |
|---|---|---|---|
| ch_all | Total number of entities | sus, inf, rec | |
| ch_prev | Prevalence | inf | ch_all |
| ch_infrec | Number ever infected | inf, rec | |
| ch_propinfrec | Proportion ever infected | ch_infrec | ch_all |

**Parameters**, with a **Format** column that is a de facto type:

| Code Name | Display Name | Format | Targetable | Default | Function |
|---|---|---|---|---|---|
| transpercontact | Transmission probability per contact | Probability | y | 0.0008 | |
| contacts | Number of contacts annually | | y | 80 | |
| recrate | Average duration of infections (years) | Duration | y | 0.5 | |
| infdeath | Death rate for infected people | Rate | y | 0.016 | |
| foi | Force of infection | Rate | | | `(1 - (1-ch_prev*transpercontact)**floor(contacts)*(1-ch_prev*transpercontact*(contacts-floor(contacts))))*(1-susdeath)` |

**Cascades**: named sequences of characteristics for cascade (care-continuum) analysis.

That is the entire model. No code.

## Core abstractions

| Concept | Atomica name | Notes |
|---|---|---|
| Compartment | row on the Compartments sheet | With `Is Source` / `Is Sink` / `Is Junction` flags |
| **Junction** | a compartment flagged `Is Junction` | No time spent here: individuals pass straight through, splitting by outflow proportions. This is how branching is done |
| Transition | a cell in the transition matrix | Contains the *name of the parameter* driving the flow |
| Characteristic | named combination of compartments, optional denominator | Aggregates and prevalences as built-in named objects |
| Parameter | row on the Parameters sheet | With `Format` (Probability / Duration / Rate / Number / Proportion), min/max, default, `Targetable`, and an optional `Function` |
| Function | an expression over parameters and characteristics | Parsed by `function_parser.py` |
| Databook | a second workbook | Time series of data per population, generated *from* the framework |
| Program | `progbook` | Interventions with unit costs, coverage, and outcome effects |
| Cascade | named sequence of characteristics | For care-continuum analysis |
| Optimization | `optimization.py` | Budget allocation across programs |

## What the spreadsheet form gets right

**The transition matrix is the right visual form for a compartmental model.** A square grid of compartments with parameter names in the cells is, at a glance, the flow diagram. It also makes structural errors visible: an empty row is an absorbing state, an empty column is unreachable.

**Parameters have a `Format`.** Probability, Duration, Rate, Number, or Proportion. This is a system of units in a spreadsheet column, coarser than camdl's dimensional types but doing the same job. It is the *only* tool in the review for non-programmers that makes this distinction.

**Characteristics separate what is modeled from what is reported.** Prevalence is not a compartment. It is a named ratio of one set of compartments to another, declared once and available to functions, data entry, and output. This handles derived outputs more neatly than most code-based frameworks.

**The databook is generated from the framework.** Define the structure, and Atomica produces a spreadsheet with exactly the data fields the model needs, per population, with the right units and labels. epymorph states the same data requirements in code; here they are a data-entry form.

**Junctions.** A compartment that people pass straight through, splitting by proportion, is the compartmental equivalent of camdl's branching transitions, and it takes one flag on a row.

## Time

Annual or sub-annual steps set in the framework; parameters carry `Format` (Duration in years, Rate per year) so units are declared even though they are not checked arithmetically. Data is entered by calendar year in the databook.

## Programs and optimization

The `progbook` is a third workbook where interventions are entered as **programs** with unit costs, coverage functions, and effects on targetable parameters. Optimization then reallocates a fixed budget across programs to minimize an objective.

This is an unusual kind of intervention vocabulary: an intervention is a *funded program with a cost function and an effect on parameters*. A health-ministry planner needs this, and almost nothing else in the review provides it. The `Targetable` column on the Parameters sheet connects the two, by declaring which parameters a program may move.

## Strengths

- **A way in for non-programmers.** A domain expert can define a compartmental model, its parameters, its derived indicators, and its intervention programs without writing code. Nothing else in the review comes close.
- **The transition matrix as the way to write a model**: visual, complete, and good at showing errors.
- **Parameter `Format` as a light system of types**: Probability / Duration / Rate / Number / Proportion.
- **Characteristics** as declared derived quantities with denominators.
- **Databook generated from the framework**, so the data requirements are a form rather than a document.
- **Junctions** for branching without residence time.
- **Programs with costs, coverage, and targetable parameters**, plus budget optimization over them.
- **Cascades** as a built-in analysis object.
- **The model *is* data.** An `.xlsx` file, versionable (awkwardly), inspectable, and shareable with people who will never open a terminal.

## Limitations

- **Excel.** The tradeoff for reach is a binary format that is hard to compare between versions, no useful comments, formula cells that can silently break, and a template that relies on cross-sheet formulas to stay in sync. The arguments against JSON and YAML as model languages apply here too, and version control is harder.
- **Deterministic compartmental only.** No stochasticity, no agents, no networks.
- **No stratification operator.** Populations are a separate axis handled by the databook; anything else means more compartments.
- **The `Function` column is an expression in a string**, in a small language of its own parsed by `function_parser.py`. The `foi` example above shows how quickly that gets hard to read. It is the way out when the tables are not enough, and it is where a spreadsheet model stops being easy to follow.
- **`Format` is documentation, not enforcement.** Nothing checks that a Duration is used where a duration is expected.
- **No inference beyond calibration** to time series; no observation model.
- **Small development community**, and documentation aimed at Atomica's own user base rather than at general modelers.
- **No public paper.**

## Implications for the lingua franca

1. **Atomica sets the standard for accessibility.** If only people comfortable with a text-based modeling language can write the lingua franca, it will not reach Atomica's audience. That does not mean adopting spreadsheets. It means the design should have a **standard table form**: the model's compartments, transitions, parameters, and derived quantities as tables that could be shown as a form, a spreadsheet, or a web page, and read back.
2. **The transition matrix is a view worth supporting.** A square compartment × compartment grid with parameter names in the cells is a complete, readable view of a compartmental model. Any language with named transitions can produce it, and should.
3. **Take `Format` and make it a real type.** Probability / Duration / Rate / Number / Proportion matches Starsim's `prob` / `dur` / `per` / `freq` and camdl's `probability` / `time` / `rate` / `count`, in a spreadsheet column. **Three frameworks, written in very different ways, arrived separately at the same small set of parameter kinds.** That is strong evidence for this vocabulary.
4. **Characteristics belong in the language.** A named combination of compartments with an optional denominator covers prevalence, coverage, cascade steps, and most reported indicators. It brings "what to fit to", "what to plot", and "what to report" together. summer2's `request_output_for_compartments` and camdl's `prevalence(...)` are partial versions; Atomica's has the denominator built in.
5. **Generate the data requirements from the model.** Atomica's databook and epymorph's `AttributeDef` are the same idea: the model states what data it needs, and the tools produce a form or fetch the data. The lingua franca's tools should do this as standard.
6. **Programs with costs are a missing part of interventions.** Only Atomica represents an intervention as something with a **unit cost and a coverage function** that a budget constrains. For the policy audience this project serves, that is essential, and no other framework here supplies it. The `Targetable` flag (which parameters a program may move) is also a partial answer to the problem of unconstrained connectors in Starsim 3.

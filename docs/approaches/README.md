# Approaches

A review of the current approaches used in the epi modeling landscape, based on the [disease modeling landscape](https://starsim.org/disease_modeling_landscape). The project owes a great deal to these frameworks. This folder records what it learned from each, for the design. For how they compare with Starsim today, and when one of them is the better choice, see the Starsim docs: [Modeling landscape](https://starsim.org/v4/user_guide/library_landscape.html) and the [conversion guides](https://starsim.org/v4/user_guide/conversion/index.html).

## Purpose

This folder catalogs what already exists: the frameworks, libraries, and conventions that epi modelers use today, and how each one represents the core modeling concepts (states, transitions, populations, networks, interventions, time).

## Contents

One document per framework or family of frameworks, covering:

- What the framework is for, and which modeling paradigms it supports (compartmental/ODE, metapopulation, stochastic compartmental/SDE, agent-based)
- How a model is specified (API, DSL, config file, GUI)
- The core abstractions and their names
- Notable strengths and limitations
- A minimal representative model (SIR if possible), and a more complex fully worked example

Every document follows the same template, so that the sections can be read across frameworks as well as down. See [epimodel.md](epimodel.md) and [starsim.md](starsim.md) for the two reference entries.

## Landscape

### Included — full reviews

24 frameworks, one document each. Sixteen of them also have models translated into Starsim; the [models page](../models/index.qmd#how-the-models-were-chosen) says which, and why each of the others doesn't.

| Framework | Language | Paradigms | Specification style | Why |
|---|---|---|---|---|
| [Starsim](starsim.md) | Python | ABM, network, metapop; compartmental from v4 | v3: classes with declared `define_pars` / `define_states` / `define_results`. v4 adds declared transitions | The starting point for this project; multi-disease, multi-timescale, typed time |
| [EpiModel](epimodel.md) | R | ODE, stochastic ICM, dynamic network (TERGM) | Three parallel APIs (`param`/`init`/`control`) plus swappable module functions | The most widely used epi framework in R; the only mainstream framework that treats one model spec across deterministic and stochastic execution as a built-in idea |
| [camdl](camdl.md) | camdl DSL (OCaml/Rust) | ODE, chain-binomial, Gillespie | Standalone typed DSL with a compiler | The closest existing thing to the target design: dimensional types, compile-time checks, declarative observation model, multiple backends from one source |
| [odin / odin2](odin.md) (+ dust, monty) | R DSL → C/C++ | ODE, discrete-time stochastic | Embedded DSL of equations, compiled | The best-established compiled-DSL approach in epi; equations written as equations, backend chosen separately |
| [summer2](summer2.md) | Python | Compartmental (stratified) | Declarative model object with stratification applied as a transform | The most developed answer anywhere to "how do you stratify a model without rewriting it" |
| [MEmilio](memilio.md) | C++ / Python | ODE, IDE, LCT, SDE, metapop, ABM | C++ template model classes + Python bindings | Single library spanning the most paradigms; a natural test of paradigm interconversion |
| [EMULSION](emulsion.md) | YAML DSL (Python) | Compartmental, ABM, multi-level | Human-readable YAML model description, no code | Model-as-data, and explicit multi-level (individual / herd / population) semantics |
| [epymorph](epymorph.md) | Python | Metapopulation | Composition of independent `IPM` (disease), `MM` (movement), `GEO` (geography) parts | The cleanest separation of disease process from spatial process on offer |
| [MetaCast](metacast.md) | Python | Metapopulation, any stratification | User model function "broadcast" across arbitrary dimensions | Treats stratification/metapopulation as a dimension algebra rather than model structure |
| [Epydemix](epydemix.md) | Python | Compartmental, stochastic | Transitions added imperatively to a model object; bundled populations and contact matrices | Named in the project brief as an interconversion target; the "batteries-included" end of the design space |
| [epipack](epipack.md) | Python | Compartmental (symbolic, numeric, network) | Reaction-style tuples, with a symbolic and a numeric backend over the same spec | One spec, three execution modes (deterministic, stochastic, network): direct evidence for the paradigm-agnostic goal |
| [EMOD](emod.md) | C++ / JSON | ABM (individual-based) | JSON config, campaign, and demographics files against a published schema | The largest fully schema-driven epi model; shows what a data-only specification costs and buys |
| [epiworld](epiworld.md) (epiworldR / epiworldpy) | C++ core, R + Python | ABM, network | Header-only C++ core, model built from states + transition functions | Identical model semantics across two host languages from one engine: the strongest existing multi-language binding story |
| [individual](individual.md) | R / C++ | ABM (state-and-event) | Bitset state variables and scheduled events; no disease concepts at all | Minimal, low-level abstraction: the "assembly language" comparison for our vocabulary |
| [SimInf](siminf.md) | R / C | Stochastic compartmental on networks | Transitions as text propensity expressions, compiled to C; scheduled events for movement | Bridges compartmental, metapopulation, and network in one small vocabulary |
| [Atomica](atomica.md) | Python + Excel | Compartmental, cascade | Model structure defined in a spreadsheet ("framework" workbook), data in another | The strongest non-programmer specification path in the landscape |
| [EoN](eon.md) | Python | Network SIR/SIS, ODE approximations | Function calls over a NetworkX graph; a `Gillespie_simple_contagion` spec for custom processes | Pairs simulation with the corresponding analytic approximations: relevant to converting between paradigms |
| [flepiMoP](flepimop.md) | Python / R | Metapopulation, inference pipeline | YAML configuration spanning model, seeding, interventions, and fitting | Models as config files at production scale, including interventions |
| [EpiHiper](epihiper.md) | C++ / JSON | ABM on explicit contact networks, national scale | Five JSON documents against published schemas | The only framework here where *both* the disease model and the intervention layer are data; declarative dwell-time distributions and a real set/trigger/action rule language |
| [Vivarium](vivarium.md) | Python | Agent-based microsimulation | Components listed in YAML; behavior as `Component` subclasses with a declared lifecycle | The value-pipeline pattern (named quantities with one producer, many registered modifiers, and a declared combiner) is the best answer here to cross-module effects |
| [Thanzi La Onse](tlo.md) | Python | Agent-based microsimulation, whole health system | `Module` subclasses with declared parameters and properties; behavior as scheduled events | The only model here with a health system that can refuse care: requests with staff-time and consumable footprints, priorities, and finite capacity, plus built-in DALY accounting |
| [LASER](laser.md) | Python / Numba | Spatial ABM at eradication scale | A columnar `LaserFrame` of agent properties plus a list of components | IDM's other agent-based engine; its design point differs from Starsim's in instructive ways, and its migration-model library is the best spatial-interaction vocabulary in the review |
| [epidemics](epidemics.md) | R (odin under the hood) | Compartmental, fixed structures | Model structure is a library; the user composes *composable elements* around it | The clearest statement of the opposite design choice (fix the structure, open the scenario) with a published design-principles document |
| [Pandemic Simulator](pandemic_simulator.md) | Python (JAX) | Compartmental (ODE, tau-leaping) | Model classes with a declared schema and a hand-written `equation()` | The clearest case of a model as a published product: the WHO's platform builds validation, a web form, and a model card from each model's declaration |

### Included — brief notes

Shorter entries, collected in [notes.md](notes.md): enough to place each one and to extract whatever the design should learn, without a full review.

| Framework | Language | The idea worth taking |
|---|---|---|
| [Covasim / HPVsim / STIsim / FPsim](notes.md#covasim--hpvsim--stisim--fpsim) | Python | Starsim's lineage; Covasim's `days`/`changes` intervention form was simpler than what replaced it |
| [Kendrick](notes.md#kendrick) | Pharo / Smalltalk | The earliest and most explicit statement of separation-of-concerns as the organizing principle for epidemic models |
| [PyRoss](notes.md#pyross) | Python | Optimal control ("what intervention is best?" rather than "what if we do X?") plus multiple stochastic approximations of one model |
| [epidemik](notes.md#epidemik) | Python | The model prints as its own YAML specification and round-trips through it; R₀ computed generically from the transition graph |
| [Mesa](notes.md#mesa) | Python | Agent activation order as a named, user-selected modeling decision; `AgentSet` as a select-then-act primitive |
| [Vahana.jl](notes.md#vahanajl) | Julia | Locality makes parallel runs automatic: transitions see only their agent and its incoming edges |
| [RepastHPC](notes.md#repasthpc) | C++ | One agent population with several projections (network, grid, continuous space) over it; the HPC reference point for general-purpose ABM |
| [ModelingToolkit.jl / Catalyst.jl](notes.md#modelingtoolkitjl--catalystjl) | Julia | **Per-reaction `PhysicalScale`**: paradigm declared per *transition*, not per model. The sharpest version of this project's central idea, in another field |
| [SBML](notes.md#sbml-systems-biology-markup-language) | XML standard | Twenty-five years of interchange-format experience, including why an unauthorable format degrades into a lossy export target |
| [ASKEM AMR / MIRA](notes.md#askem-model-representation-amr--mira) | JSON / Python | The closest prior art: a closed Template taxonomy of transition types, and **ontology-identified Concepts** that let two models' compartments be compared |

### Selection process and exclusions

The landscape database (as of 2026.08.25) lists 137 tools. Most are not in scope for this project. The filter applied is: **does a user specify a model in it?** A framework here is something where the modeler supplies the states, transitions, populations, and interventions, and the tool supplies the execution. That includes domain-specific languages, model-specification APIs, and configuration-driven engines, but excludes four large groups that the landscape database otherwise contains:

- **Inference and estimation tools**, where the "model" is fixed and the user supplies data: EpiEstim, EpiNow2, epinowcast, EpiLPS, estimateR, NobBS, ern, EpiSewer, R0, serofoi, serosolver, serocalculator, Rsero, first90, Naomi, hivPlatform, linelistBayes, disaggregation, prevR, epigrowthfit.
- **Genomics and phylodynamics**: BEAST, BEAST 2, MASCOT, TransPhylo, phydynR, outbreaker2, nbTransmission, o2geosocial, Nextstrain, Nextclade, Pangolin, scorpio, TreeTime, UShER, civet, ARTIC.
- **Data, surveillance, and workflow utilities**: linelist, incidence2, epiparameter, epicontacts, epitrix, socialmixr, contactdata, simulist, outbreaks, finalsize, projections, scoringutils, hubverse, surveillance, SaTScan, DClusterm, excessmort, mem, aedseo, AMR, Epi Info, SORMAS, Delphi Epidata, malariaAtlas, SynthPops, modelSSE, coarseDataTools, epiflows, EpiContactTrace.
- **Single-disease applications**: OpenMalaria, malariasimulation, AnophelesModel, MGDrivE, Skeeter Buster, EPIONCHO-IBM, PopART-IBM, SimpactCyan, STDSIM, MicroCOSM, HIV Synthesis, Thembisa, Optima HIV, Spectrum, TIME Impact, LiST, OneHealth Tool, CEPAC, OpenCOVID, JUNE, OpenABM-Covid19, Epiabm, COVSIM, CovsirPhy, Bernadette, CoMo, MATSim Episim, PatchSim, nosoi, hybridModels, AADIS, ADSM, epichains, EpiILM, EpiILMCT, epinet.

Other models considered and not included:

- **FRED** ([GitHub](https://github.com/PublicHealthDynamicsLab/FRED)): **excluded on license.** Distributed under a University of Pittsburgh EULA, not an open-source license, per the landscape database's license audit. (Included if open source; it is not.)
- **GLEAM / GLEAMviz**: closed source. A landmark metapopulation model, referenced from [epymorph.md](epymorph.md) as the paradigm's reference point rather than reviewed on its own.
- **Episimmer** ([GitHub](https://github.com/healthbadge/episimmer)): excluded on license (Commons Clause is not open source).
- **UHOHCoronaPolicyLab** ([GitHub](https://github.com/BenVermeulen/UHOHCoronaPolicyLab)): excluded on license (CC BY-NC-SA 4.0 is not open source).
- **PanVADERE**: a single-purpose application (transmission among pedestrians in continuous space), not a model-specification framework. Reasons in [notes.md](notes.md#frameworks-considered-and-not-written-up).
- **[MetaWards](https://github.com/metawards/MetaWards)**, **[GEMS](https://github.com/IMMIDD/GEMS)**, **[Epi Info](https://github.com/Epi-Info/Epi-Info-Community-Edition)**: useful tools, but each is effectively one application with settings, and something already in the list serves this review better. Reasons in [notes.md](notes.md#frameworks-considered-and-not-written-up).
- **NDlib** ([GitHub](https://github.com/GiulioRossetti/ndlib)): a network diffusion library with a compartment-composition API; EoN covers the same ground more rigorously and ships the analytic approximations alongside.
- **statnet / ergm** ([GitHub](https://github.com/statnet)): the network substrate under EpiModel, discussed inside [epimodel.md](epimodel.md).
- **dust / monty**: the engine and inference layers under odin; discussed inside [odin.md](odin.md).
- **Stan, PyMC, NumPyro**: inference substrates rather than model-structure languages. They belong to the calibration discussion in `best-practices`, not here.

**EpiHiper is included** (MIT license, published in *PNAS Nexus*, in national-scale use at the CDC Scenario Modeling Hub) and turned out to be one of the more valuable entries: see [epihiper.md](epihiper.md).

Two categories are added that the landscape database deliberately excludes, because its inclusion criteria are about the IDD community and ours are about model representation:

- **General-purpose modeling substrates** that epi models are commonly built on (Mesa, ModelingToolkit.jl / Catalyst.jl). The database excludes tools "used for, but not unique to, IDD"; for a language design, those are among the most informative comparisons available.
- **Model interchange formats**, which are prior attempts at exactly the thing this project is attempting (SBML, and the ASKEM model representation / MIRA).

## Cross-cutting findings

Things that only became visible by reading across the whole set. These are observations for `best-practices` to argue with, not conclusions.

**1. Structural rigor and intervention expressiveness have not yet appeared in the same framework.** The frameworks with the best model specification (camdl, odin, summer2, epipack) have essentially no intervention vocabulary. The frameworks with the best intervention vocabulary (EMOD, EpiHiper, Starsim 3, Atomica) have weak or absent structural specification. The one exception is EpiHiper, which has both as data, at the cost of being hard to read. Closing this split was the most concrete contribution open to this project.

**2. Five independent arrivals at dimensional typing.** Starsim (`dur`/`per`/`prob`/`freq`), camdl (`rate`/`probability`/`count`/`time`), Atomica (a `Format` column in a spreadsheet), EMULSION (rate/probability/duration as three alternative transition keys), and Catalyst.jl (`@unit_checks`). Five different media, five different communities, one small vocabulary. This is as settled as anything in the review.

**3. Three independent arrivals at the spontaneous/contact-mediated transition split.** EoN's two directed graphs (`H` and `J`), epipack's 3-tuples versus 5-tuples, EpiHiper's `transitions` versus `transmissions`, and MIRA's `NaturalConversion` versus `ControlledConversion` taxonomy. A transition is either autonomous or contact-mediated, and the two have different mathematics. This should be structural, not implicit in whether a rate expression happens to mention another compartment.

**4. Three independent arrivals at route abstraction.** Starsim (`Network` and `MixingPool` behind one `Route`), epiworld (`ModelSEIR` / `ModelSEIRCONN` / `ModelSEIRMixing` over one engine), and epipack (network versus well-mixed). Separating the disease process from the contact structure is the right place to divide. **How to express transmission such that mass-action, contact-matrix, and edge-based forms are the same declaration is the hardest unsolved problem in this review**, and where the project has to do original work.

**5. Four instances of the same tradeoff.** EMULSION (YAML), EMOD (JSON), EpiHiper (JSON), and flepiMoP (YAML) are all models as data, which brings real benefits, and all are hard to write by hand, for the same reason: a data format is used as a language. Expressions end up in strings, there is no type checking, and errors come from a parser that knows nothing about the domain. With SBML's history, the lesson is: **a data format is a good thing to generate and a hard thing to write.**

**6. Paradigm may belong to a transition, not to a model.** EMULSION switches a whole model between compartmental, IBM, and hybrid with one keyword: an existence proof that should be examined closely. Catalyst.jl goes further, with per-reaction `PhysicalScale` metadata so that one system mixes ODE and jump dynamics. That is the sharper formulation, and it is what a hybrid epidemiological model needs.

**7. Dwell-time distribution is a built-in axis that most frameworks silently fix.** ODE means exponential; nearly every framework here assumes it without saying so. MEmilio needed four separate model families (ODE / LCT / GLCT / IDE) to span the axis; EpiHiper declares a distribution per transition; camdl has `via erlang` / `via hyper_erlang`; `individual` and Starsim schedule sampled times. **One declaration ("dwell time in I is Gamma(α, β)") should become Erlang sub-compartments in an ODE backend, a scheduled event in an ABM backend, and a memory kernel in an IDE backend.** That is a concrete, testable instance of paradigm-independence and is worth prototyping early.

**8. Eligibility should be a declared condition, and two frameworks show how.** EMOD's `Targeting_Config` (named conditions combined with AND and OR) and EpiHiper's `sets` (sets of nodes and edges defined by conditions) are data. Starsim 3's `eligibility` function and EpiModel's modules are code. This is the piece missing from every scenario grammar in the review: EpiModel's tables and flepiMoP's modifiers can move a parameter over a time window but cannot target a subgroup.

**9. Cross-module effects need a declared combination rule.** Two interventions each reducing transmission by 40% might compose multiplicatively or additively, and the answer changes. Vivarium declares it (named combiners and post-processors on value pipelines); `epidemics` declares it globally and justifies the choice; in Starsim 3's connectors, the last write wins; most frameworks leave it implicit in execution order. This is a modeling decision that must be statable.

**10. Order dependence is usually hidden, and it does not have to be.** `individual` makes it irrelevant (queued updates, applied after all processes run). Vivarium makes it declared (named lifecycle phases with priorities). Starsim makes it inspectable (`Loop` as a data object). Mesa makes it a user-selected modeling decision. Everyone else leaves it in the order the code happens to run.

**11. Structure should be specifiable by its generating model, not only its realization.** EpiModel fits a network from target statistics (`netest` → `netdx` → `netsim`); LASER ships gravity, radiation, Stouffer, and competing-destinations mobility models; Epydemix and epymorph resolve contact matrices and geography from named data sources. A language that only accepts an edge list or a matrix has moved the problem rather than solved it, because the description, not the realization, is what modelers have.

**12. Only MIRA can tell whether two models' compartments mean the same thing.** MIRA's ontology-identified `Concept`s are what make automated model comparison and merging possible. For a project whose goal includes interconversion, this is an idea to take seriously.

## Relationship to other folders

- Feeds into `best-practices`, which draws these reviews together by paradigm.
- Code from these frameworks is in `examples`.

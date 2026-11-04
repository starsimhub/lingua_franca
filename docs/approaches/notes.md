---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Brief notes

Short entries for frameworks worth learning from without a full review. Each says what it is, the one or two ideas to carry into the design, and why it has no full review.

Full reviews are listed in [README.md](README.md).

---

## Covasim / HPVsim / STIsim / FPsim

**Python · agent-based · Starsim's predecessors and descendants · [covasim.org](https://covasim.org), [hpvsim.org](https://hpvsim.org), [stisim.org](https://stisim.org), [fpsim.org](https://fpsim.org) · code at [github.com/starsimhub](https://github.com/starsimhub)**

Covered in [starsim.md](starsim.md), because the history matters: three disease-specific frameworks became one modular framework, and the cost of three near-identical codebases is what motivated `ss.Module`.

Worth noting individually:

- **Covasim's intervention form.** `change_beta(days=[30, 60], changes=[0.5, 1.0])`, a list of days and a list of changes, is smaller and easier to read than the classes that replaced it. flepiMoP's modifiers and EpiModel's scenario tables have the same shape. Some simplicity was arguably lost in generalizing.
- **HPVsim's genotype-as-a-state-dimension.** Multi-strain modeling by adding an axis to the state array rather than by duplicating the disease module, plus the screening → triage → treatment product cascade that Starsim 3's `BaseTest`/`BaseTreatment` classes generalized.
- **FPsim** demonstrating that the same machinery models a non-infectious process (contraceptive use, pregnancy, birth outcomes), which is why `ss.Disease` sits under a general `ss.Module` rather than at the root.

---

## Kendrick

**Pharo / Smalltalk · compartmental, with separation of concerns as the organizing principle · [github.com/KendrickOrg/kendrick](https://github.com/KendrickOrg/kendrick) · Bui et al. (2015), IEEE RIVF, [10.1109/RIVF.2015.7049888](https://doi.org/10.1109/RIVF.2015.7049888)**

A domain-specific modeling language built around the claim that an epidemiological model is a *composition of independent concerns* (the disease process, the demographic process, the spatial process, the intervention process) and that these should be written separately and combined mechanically rather than being interleaved in one system of equations.

It is important as an idea and little used: it is written in Pharo Smalltalk, has few users outside its own group, and is not in the landscape database.

**What to take:** the framing. Kendrick's separation-of-concerns argument is the same one epymorph makes with IPM/MM/GEO, MetaCast makes with dimensions, and this project makes with paradigm-independence. Kendrick states it earliest and most explicitly, and the paper is worth reading for the argument rather than the tool. Its concern-composition operator (combining a disease process with an age process to get an age-structured disease process) is what `stratify_with()` and `stratify(by = age)` implement in more limited forms.

**Why not a full review:** the implementation is out of reach for most of this project's purposes, and later frameworks show its ideas in practice.

---

## NDlib

**Python · diffusion processes on complex networks · [github.com/GiulioRossetti/ndlib](https://github.com/GiulioRossetti/ndlib) · [ndlib.readthedocs.io](https://ndlib.readthedocs.io)**

*Excluded from the review by choice.* A library of epidemic and opinion-diffusion models on NetworkX graphs, where rules are built from parts (`NodeStochastic`, `NodeThreshold`, `EdgeStochastic`), with a web front end. It is strong on general processes and has less epidemiology; EoN covers network simulation more rigorously, with analytic approximations.

---

## PyRoss

**Python · age-structured stochastic compartmental, with inference and optimal control · [github.com/SoftMatterGroupCambridge/pyross](https://github.com/SoftMatterGroupCambridge/pyross) · Li et al. (2021), *R Soc Open Sci* 8: 211065, [10.1098/rsos.211065](https://doi.org/10.1098/rsos.211065)**

Age-structured compartmental models with several stochastic formulations (Gillespie, tau-leaping, Gaussian/van Kampen approximations), Bayesian inference over them, and (unusually) **optimal control**: computing the intervention trajectory that optimizes an objective subject to constraints.

**What to take:** optimal control. Almost every framework here can answer "what happens if we do X?"; PyRoss can answer "what X is best?". Atomica's budget optimization is the other example. If interventions are declared with their costs and effects, as EMOD's campaigns and Atomica's programs are, optimizing over them follows naturally, and the design should leave room for it.

PyRoss also has several *stochastic approximations* of one model (exact Gillespie, tau-leaping, diffusion) side by side, like MEmilio's grid of paradigms on the stochasticity axis.

**Why not a full review:** models are Python classes with fixed structures and age-contact matrices, which adds little to summer2, epipack, and MEmilio.

---

## epidemik

**Python · compartmental, network, metapopulation · [github.com/DataForScience/epidemik](https://github.com/DataForScience/epidemik) · MIT**

A small library of compartmental models from Data For Science. A model is a set of transitions added to an `EpiModel` object: *interactions* (`add_interaction('S', 'I', 'I', beta=0.2)`, i.e. `S + I -> I + I`) and *spontaneous* transitions (`add_spontaneous('I', 'R', mu=0.1)`). `NetworkEpiModel` runs the same transitions on a contact network, and `MetaEpiModel` couples one `EpiModel` per sub-population through a travel matrix. One of the 20 comparison frameworks in the MEmilio paper (Bicker et al. 2026, Fig. 1a), listed there with ODE, age, and spatial stratification.

**What to take:**

- **The model prints as its own description.** `print(SIR)` gives YAML (compartments, named parameters, `S + I = I beta`, `I -> R mu`), and `save_model` / `load_model` write and read it. One text form for display and for exchange is the cheapest way to share models.
- **Parameters defined from one another** (`mu="beta/2"`), in the model.
- **R₀ from the structure.** `R0()` computes it through the next-generation matrix, because the model is a graph of transitions. Like Catalyst's deficiency analysis, this comes free once the model is data.
- **One model, two kinds of run, the same output.** `integrate()` (ODE) and `simulate()` (seeded discrete-time stochastic) take the same arguments and return the same `DataFrame`, as in epipack.

**Why not a full review:** it is close to epipack's reaction tuples and Epydemix's transitions, both reviewed in full, and adds the YAML round trip and general R₀.

---

## Mesa

**Python · general-purpose agent-based modeling · [github.com/mesa/mesa](https://github.com/mesa/mesa) · v4 in development**

The default general-purpose ABM framework in Python, alongside NetLogo, Repast, and MASON. It is not epidemiological, so it is not in the landscape database, but many one-off epidemic ABMs are built on it.

**What to take:**

- **The order in which agents act is an explicit choice.** Mesa's options (simultaneous, random, staged, or by type) are the general form of the ordering problem that Starsim's `Loop`, EpiModel's `module.order`, Vivarium's priorities, and `individual`'s queued updates answer in their own ways. Mesa treats it as a *modeling decision the user makes*, and names the options. Order changes results, so it should be declared.
- **`AgentSet`** (Mesa 3+): a collection of agents with `select`, `shuffle`, `do`, and `agg`, the same select-then-act operation as in `individual` and LASER.
- **Space as a separate component that can be swapped** (`discrete_space`, continuous space, networks).

**Why not a full review:** it has no epidemiological vocabulary, and the frameworks above show its ideas in this field.

---

## Vahana.jl

**Julia · general-purpose agent-based modeling, distributed · [github.com/s-fuerst/Vahana.jl](https://github.com/s-fuerst/Vahana.jl) · MIT**

A high-performance ABM library built on **graph dynamical systems**: agents and edges are typed, each step applies a transition function per agent type that reads only the agent's own state and its incoming edges, and the result is distributed across processes with MPI. Not epidemiological, but its showcase model is a reimplementation of MATSim-Episim, and it is one of the 20 comparison frameworks in the MEmilio paper (Bicker et al. 2026, Fig. 1a).

**What to take:**

- **Locality makes parallel runs automatic.** Because a transition sees only its own agent and that agent's incoming edges, the framework can split the graph across processes without the user writing any communication code. This is the strongest form of "declare what you read": the restriction is what allows it.
- **Edges as typed, built-in state.** Contacts carry data, and the framework stores and distributes them.

**Why not a full review:** it has no epidemiological vocabulary, and how models are written (structs plus transition functions) adds little to `individual` and Starsim. The locality rule is the one idea to carry forward.

---

## RepastHPC

**C++ · general-purpose agent-based modeling, distributed (MPI) · [github.com/Repast/repast.hpc](https://github.com/Repast/repast.hpc) · New BSD**

The high-performance member of the Repast family (Argonne National Laboratory): agents live in *contexts*, and *projections* (networks, discrete grids, continuous space) are layered over the same agents. Agents are distributed across MPI processes, with non-local agents shared as copies that are synchronized each step. It also ships ReLogo, a Logo-style API on top. One of the 20 comparison frameworks in the MEmilio paper (Bicker et al. 2026, Fig. 1a), where it is the only one listed with all three agent-based styles (network, location graph, continuous) and full shared- and distributed-memory parallelism.

**What to take:**

- **One population, several views.** Network and spatial structure are separate views of the same agents, the separation of population from contact structure that the design wants.
- **Ghost agents show the cost of distributing a model.** Agents read across processes need synchronized copies, which the user declares and manages. This shows what a distributed solver would have to ask of a model.

**Why not a full review:** it has no disease vocabulary. Mesa covers general ABM ideas, and EpiHiper covers distributed ABMs in this field.

---

## ModelingToolkit.jl / Catalyst.jl

**Julia · symbolic reaction networks with automatic multi-paradigm code generation · [github.com/SciML/Catalyst.jl](https://github.com/SciML/Catalyst.jl) · [docs.sciml.ai/Catalyst](https://docs.sciml.ai/Catalyst/stable/) · [10.1371/journal.pcbi.1011530](https://doi.org/10.1371/journal.pcbi.1011530)**

**The strongest existing demonstration anywhere of "one specification, many paradigms", and it is not in epidemiology.**

Catalyst is a symbolic modeling package for chemical reaction networks built on ModelingToolkit/Symbolics. A model is written in a reaction DSL:

```julia
model = @reaction_network begin
    kB, S + E --> SE
    kD, SE --> S + E
    kP, SE --> P + E
end
```

and the *same* `ReactionSystem` then generates an ODE system, an SDE system, a jump (Gillespie) system, a steady-state system, or a hybrid: via `ode_model`, `sde_model`, `jump_model`, `ss_ode_model`. Version 16 adds **per-reaction `PhysicalScale` metadata**, so a single model can have some reactions treated as ODEs and others as jumps, in one simulation.

**What to take:**

1. **`PhysicalScale` per reaction is the clearest form of paradigm independence in this review.** Not "this model is stochastic" but "this *transition* is a jump process and that one is an ODE", in one model. A hybrid epidemiological model needs exactly this (rare importation events as jumps, bulk transmission as an ODE), and EMULSION's `hybrid` mode and MEmilio's hybrid models get there with more effort.
2. **A symbolic core with generated code.** Catalyst uses the symbolic form for sparsity, Jacobians, dependency analysis, and parallelism, epipack's argument at production quality.
3. **Unit checks** (`@unit_checks`, `validate_units`), with non-SI units via DynamicQuantities.jl. This is a fourth independent arrival at dimensional checking.
4. **Models built from parts** (`@network_component`, `compose`, `extend`), as a hierarchy of named sub-networks. Epidemiological frameworks mostly lack this.
5. **Coupled models**: reactions, differential equations, discrete events, Brownian noise (`@brownians`), and Poisson jumps (`@poissonians`) in one system, so environmental forcing and stochastic parameters are part of the model.
6. **Network analysis from the structure** (linkage classes, deficiency, reversibility): results that can be computed because the model is a graph.

**Why not a full review:** it has no epidemiological vocabulary (no interventions, contact structure, or observation model). But **the design team should read its documentation before settling how paradigm conversion works**, because the SciML ecosystem has worked on this problem, at scale, for longer than anyone in this review.

---

## SBML (Systems Biology Markup Language)

**XML standard · model interchange · [sbml.org](https://sbml.org) · [github.com/sbmlteam](https://github.com/sbmlteam) · [10.1093/bioinformatics/btg015](https://doi.org/10.1093/bioinformatics/btg015)**

Twenty-five years of experience with a machine-readable model interchange format for reaction-network models, supported by hundreds of tools, with a curated model repository (BioModels) and a formal specification with versioned Levels.

It is directly relevant as **precedent**, including what proved hard, and this project owes much to that experience.

**What to take:**

- **Levels and Versions say what is compatible.** SBML L2V4 versus L3V2 states what a reader has to support. camdl versions its internal form in the same way, and a lingua franca will need this.
- **Annotation as a separate layer.** SBML keeps the mathematics apart from `<annotation>` blocks carrying MIRIAM-standard identifiers, so a species can be linked to a database without changing what it means. EpiHiper's `ann:` prefix is a lighter version.
- **Units are in the standard** (`unitDefinition`), and are widely ignored, a warning about optional checks.
- **What proved hard:** XML is long enough that people rarely write it by hand, so writing moved to each tool's interface, and the shared format became an *export* format. "Supports SBML" varies widely, because the standard is large and support is partial. Events, delays, and algebraic rules are where writing a model out and reading it back fails.

**The lesson for this project:** a shared format that few people write in becomes a lossy export, and partial support is normal. For the lingua franca to be *both* a language to write in and a way to exchange models, it has to be pleasant to write, and each feature has to be fully supported or clearly refused, as in camdl's capability checks.

---

## ASKEM model representation (AMR) / MIRA

**JSON schemas and a Python meta-model · [github.com/gyorilab/mira](https://github.com/gyorilab/mira) · DARPA ASKEM**

MIRA is a **toolkit for representing and transforming** epidemiological and biological models: the most recent and most comparable attempt at what this project is attempting.

Its core is a `TemplateModel` built from typed **Templates**, a fixed list of kinds of transition:

`NaturalConversion` · `ControlledConversion` · `GroupedControlledConversion` · `NaturalProduction` · `ControlledProduction` · `GroupedControlledProduction` · `NaturalDegradation` · `ControlledDegradation` · `GroupedControlledDegradation` · `MultiConversion` · `ReversibleFlux` · `NaturalReplication` · `ControlledReplication` · `StaticConcept`

Each references **Concepts**: a name, a display name, `identifiers` (a mapping of namespace to ontology identifier), `context` (a mapping of context keys to values), and **`units`** (a SymPy expression over a unit vocabulary).

**What to take (this entry has the most ideas in these notes):**

1. **A fixed, named list of kinds of transition.** `ControlledConversion` (S → I controlled by I) versus `NaturalConversion` (I → R) is the spontaneous versus contact-mediated split that EoN, epipack, and EpiHiper each found, set out as a formal list. `Grouped*` variants handle several controllers. This is the most thought-through answer in the review to "what kinds of transitions are there", because MIRA has to *translate between formats*.
2. **Concepts carry ontology identifiers.** A compartment is a Concept with `identifiers={"ido": "0000511"}` (IDO's "infected population") and `context={"age": "youth", "location": "Boston"}`, and not just the string `"I"`. So two models' compartments can be **compared**, which `mira.metamodel.comparison` and `search.py` use for automated comparison and merging. **No other framework in this review can tell whether two models' compartments mean the same thing.**
3. **Context as a general way to stratify.** A Concept's `context` dict gives its stratum, and `mira.metamodel.ops.stratify()` works on it in general, as MetaCast and camdl do with dimensions, but attached to a concept whose meaning is known.
4. **Units as symbolic expressions**, per Concept. This is a fifth independent arrival at dimensional typing.
5. **A library of model operations**: `stratify`, `rewrite_rate_law`, `simplify_rate_laws`, `aggregate_parameters`, `counts_to_dimensionless`, `deactivate_templates`, `add_observable_pattern`, and `get_observable_for_concepts`. This becomes possible once a model is data, and this project will need it.
6. **Many formats in and out**: SBML, Petri-net AMR, RegNet AMR, StockFlow AMR, ACSets, bilayer, system dynamics (Vensim/Stella), PySB, and `sympy_ode` (extracting ODE systems from papers). The AMR JSON schemas are designed for exchange, with a `semantics` / `metadata` split.
7. **`counts_to_dimensionless`**, a named operation that converts a model between counts and proportions, is the kind of step the lingua franca will need, and only MIRA names it.

**Why not a full review:** MIRA translates and transforms models. You do not write models in it, and it has no simulation engine, intervention vocabulary, or observation model. But **it is the closest prior work to this project's goal of conversion**, its Templates can be reused directly, and the project should consider its ontology-identified Concepts.

---

## Frameworks considered and not written up

Recorded so the decisions are reviewable.

- **FRED** (University of Pittsburgh, [GitHub](https://github.com/PublicHealthDynamicsLab/FRED)): synthetic-population ABM with household/school/workplace networks. **Excluded on license**: distributed under a University of Pittsburgh EULA, not an open-source license, per the landscape database's license audit. (It would have been included if open source.)
- **GLEAM / GLEAMviz**: the landmark global metapopulation model integrating worldwide census and air-travel data. Closed source; referenced from [epymorph.md](epymorph.md) as the reference point for the metapopulation paradigm rather than reviewed.
- **MetaWards** ([GitHub](https://github.com/metawards/MetaWards)): ward-level metapopulation for England and Wales. Effectively one application with settings; epymorph and flepiMoP are more useful here for how metapopulations are written.
- **GEMS** (Julia, [GitHub](https://github.com/IMMIDD/GEMS)): nationwide microsimulation over synthetic German populations. It would have been the only Julia agent-based entry, but how its models are written adds little to `individual` and Starsim, and Catalyst.jl is the more useful Julia entry for this project.
- **Episimmer** ([GitHub](https://github.com/healthbadge/episimmer)): institutional-reopening simulator. Excluded on license (Commons Clause is not open source).
- **UHOHCoronaPolicyLab** (TypeScript, [GitHub](https://github.com/BenVermeulen/UHOHCoronaPolicyLab)): continuous-space COVID-19 policy simulation, one of the comparison frameworks in the MEmilio paper (Bicker et al. 2026, Fig. 1a). Excluded on license: CC BY-NC-SA 4.0's non-commercial clause is not open source.
- **PanVADERE** (Java): pandemic extension of the Vadere pedestrian-dynamics simulator, modeling transmission between individuals moving in continuous space; also in the MEmilio paper's comparison. A single-purpose application (indoor/crowd transmission) rather than a model-specification framework.
- **statnet / ergm** ([GitHub](https://github.com/statnet)): the network substrate under EpiModel; discussed inside [epimodel.md](epimodel.md).
- **dust / monty**: the engine and inference layers under odin; discussed inside [odin.md](odin.md).
- **Stan, PyMC, NumPyro**: inference substrates rather than model-structure languages. They belong to the calibration discussion in `best-practices`.

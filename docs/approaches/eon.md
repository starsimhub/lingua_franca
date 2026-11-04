---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# EoN (Epidemics on Networks)

|  |  |
|---|---|
| **Language** | Python, over NetworkX |
| **Paradigms** | Stochastic simulation on networks, **plus** the full hierarchy of analytic ODE approximations to those simulations |
| **Specification style** | Function calls for the standard models; a pair of directed graphs for custom processes |
| **Version reviewed** | 1.92 |
| **License** | MIT |
| **Code** | <https://github.com/springer-math/Mathematics-of-Epidemics-on-Networks> |
| **Docs** | <http://epidemicsonnetworks.readthedocs.io/> |
| **Paper** | [10.21105/joss.01731](https://doi.org/10.21105/joss.01731); accompanies Kiss, Miller & Simon, *Mathematics of Epidemics on Networks* (Springer, 2017) |

## What it's for

EoN is the software companion to a textbook. It simulates SIS, SIR, and more general processes on networks, and it implements **the analytic approximations to those same processes** (the mean-field, pairwise, and effective-degree closures that the book derives).

That second half is why it is in this review. EoN is the only package here with both a stochastic network simulation *and* a graded family of ODE approximations to it. This project has to ask when a compartmental model is a valid summary of an agent-based one, and EoN lets you find out by running both.

## How a model is specified

**Standard models** are function calls over a NetworkX graph:

```python
import EoN, networkx as nx
G = nx.configuration_model([...])
t, S, I, R = EoN.fast_SIR(G, tau=0.5, gamma=1.0, rho=0.01)
```

**Custom processes** are specified as **two directed graphs**:

```python
import networkx as nx

# Spontaneous transitions: nodes are statuses, edges are transitions
H = nx.DiGraph()
H.add_edge('E', 'I', rate=0.6)      # E -> I
H.add_edge('I', 'R', rate=0.1)      # I -> R

# Neighbour-induced transitions: nodes are (source_status, target_status) pairs
J = nx.DiGraph()
J.add_edge(('I', 'S'), ('I', 'E'), rate=0.1)   # an I-S edge makes the S become E

IC = {node: 'S' for node in G}
t, D = EoN.Gillespie_simple_contagion(G, H, J, IC, return_statuses=('S','E','I','R'), tmax=100)
```

`H` is the spontaneous-transition graph; `J` is the neighbor-induced-transition graph, whose nodes are *pairs* of statuses so that `('I','S') → ('I','I')` reads as "an infectious–susceptible edge turns the susceptible one infectious".

**The model is literally a graph**: a `networkx.DiGraph` you can walk through, draw, and edit in code. This takes transitions as data about as far as it goes, and the figure the textbook uses to explain a model (Fig 4.3, cited in the docstring) is the same object the code runs.

Rates can vary per node or per edge, through a `weight_label` naming an attribute in `G` that multiplies the rate, or a `rate_function(G, u)` / `rate_function(G, source, target)` that works out a scale factor from the network. The rate function may not depend on node *statuses*, because it is computed once at the start. This stated restriction keeps the Gillespie implementation correct.

## The analytic hierarchy

The `EoN.analytic` module implements, for both SIS and SIR:

| Approximation | What it tracks |
|---|---|
| `*_individual_based` | One equation per node: exact-ish, N equations |
| `*_pair_based` | Node and edge pair probabilities |
| `*_homogeneous_pairwise` | Pair counts, homogeneous degree |
| `*_heterogeneous_pairwise` | Pair counts by degree class |
| `*_compact_pairwise` | Reduced pairwise |
| `*_super_compact_pairwise` | Further reduced |
| `*_effective_degree` | Susceptible-neighbor count as a state |
| `*_compact_effective_degree` | Reduced effective degree |
| `*_homogeneous_meanfield` | Standard mass-action ODEs |
| `*_heterogeneous_meanfield` | Degree-block ODEs |
| plus `EBCM` | Edge-based compartmental model |

Each also has a `*_from_graph` variant that extracts the required moments (degree distribution, `Nk`, `NkNl`) from an actual network. So the workflow is: build a network, run the exact simulation, and run any approximation *parameterized from that same network*, then compare.

This is a **ladder of conversions that you can run**. Each step down is an explicit closure assumption, and you can measure what it costs on your network.

Supporting tools: `get_Pk`, `get_PGF`, `get_PGFPrime`, `get_PGFDPrime` (degree distribution and its probability generating function), and `estimate_R0(G, tau, gamma)`.

## Time

Continuous time throughout: Gillespie and the fast event-driven algorithms for simulation, `scipy.integrate.odeint` for the analytics. No timestep, so no rate-to-probability conversion. Rates are per-unit-time floats; no units.

## Strengths

- **The model is a pair of directed graphs** that can be read, drawn, and built in code, and that the textbook uses to explain the model.
- **The spontaneous / neighbor-induced split.** Two kinds of transition, covering SIS, SIR, SEIR, SIRS, competing and cooperating pathogens, and complex multi-status processes. epipack and EpiHiper arrived at the same split independently.
- **The analytic hierarchy, which runs and can be parameterized from a real network.** Nothing else in the review lets you quantify the cost of a closure assumption.
- **Conditional / cascading transmission**: `Gillespie_complex_contagion` and conditional link transmission, which is how contact tracing is written.
- **Per-node and per-edge rate heterogeneity**, by attribute weight or by a rate function, with no dependence on status so that the algorithm stays correct.
- **Fast event-driven algorithms** (`fast_SIR`, `fast_SIS`), orders of magnitude quicker than the general Gillespie implementation.
- **`estimate_R0` and PGF machinery** for network-theoretic quantities.
- **Textbook provenance.** The algorithms are the published ones, with errata tracked.

## Limitations

- **No stratification, no demographics, no interventions.** Rates can vary by node attribute; there is no vocabulary for age structure, births, deaths, vaccination, or treatment.
- **Networks are inputs.** EoN takes a NetworkX graph. It has no way to describe a network to generate, and no dynamic-network model beyond its temporal-network simulations.
- **The two-graph form takes learning.** Writing "an I–S edge infects the S" as an edge from the pair `('I','S')` to `('I','I')` is precise but needs explaining, and the docstring runs to hundreds of lines.
- **Only the second node in a pair may change status**, which is stated but limits what can be modeled.
- **No dimensional types, no dates, no observation model, no inference.**
- **The analytic and simulation halves have different interfaces.** `Gillespie_simple_contagion(G, H, J, ...)` versus `SIR_heterogeneous_pairwise(Sk0, Ik0, ...)`. The approximations are only implemented for SIS and SIR, not for an arbitrary `H`/`J` process, so the conversion ladder exists for the standard models only.
- **Maintenance is intermittent**: a five-year gap between 1.1 and 1.2, though 1.92 (2026) is recent.

## Implications for the lingua franca

1. **EoN is the reference for what paradigm conversion costs.** Converting between paradigms assumes that a compartmental version of an agent-based model means something. EoN's analytic hierarchy is a decade of mathematics saying *when*: mean-field ignores correlations, pairwise closes at pairs, effective-degree tracks susceptible-neighbor counts, and each is right under different network conditions. **The lingua franca should not present network → compartmental conversion as one operation.** It is a choice of closure, and the output should name it, as `SIR_heterogeneous_pairwise` does.
2. **The `H` / `J` split is the third independent arrival at spontaneous versus induced transitions**, with epipack's 3-tuples versus 5-tuples and EpiHiper's `transitions` versus `transmissions`. Each framework needed it, so it looks basic: **a transition is either spontaneous or contact-mediated, and the two have different mathematics.** The lingua franca should build this in, and not leave it to whether a rate mentions another compartment.
3. **Take the rate-modifier restriction seriously.** EoN allows scaling rates per node and per edge but not by node status, as that would break the event-driven algorithm's precomputation. This is a good example of **a solver's limit showing up in the model description**: some rates can be simulated by some algorithms and not others. camdl's capability checks are the general form.
4. **R₀ from the model plus the network should be a language feature.** `estimate_R0(G, tau, gamma)` and epipack's `get_eigenvalues_at_disease_free_state()` reach the same quantity in two paradigms. If the model is symbolic and the contact structure is declared, the lingua franca can offer this generally, and R₀ is the number the audience asks for.
5. **A graph is the natural internal form for the disease process.** EoN runs a `DiGraph`, MIRA's `TemplateModel` is a graph, Atomica's transition matrix is an adjacency matrix, and EpiHiper's JSON is an edge list. However it is written, **the disease model is a labeled directed graph over states**, and the design should say so.
6. **The ladder exists only for standard models.** EoN's approximations cover SIS and SIR, not any `H`/`J` process, because each closure has to be derived. So general paradigm conversion takes a mathematical derivation per class of model, not an automatic step. Where the lingua franca cannot derive a conversion, it should refuse and not approximate silently.

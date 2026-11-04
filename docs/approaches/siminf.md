---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# SimInf

|  |  |
|---|---|
| **Language** | R, with generated C compiled at model-definition time |
| **Paradigms** | Stochastic compartmental (continuous-time Markov chain, Gillespie) on a network of nodes, with scheduled events |
| **Specification style** | Transitions as strings (`"S -> propensity -> I"`) parsed and compiled to C |
| **Version reviewed** | 10.1.0 |
| **License** | GPL-3 |
| **Code** | <https://github.com/stewid/SimInf> |
| **Docs** | <https://CRAN.R-project.org/package=SimInf> |
| **Paper** | [10.18637/jss.v091.i12](https://doi.org/10.18637/jss.v091.i12) |
| **Moving to Starsim** | [Conversion guide](https://starsim.org/v4/user_guide/conversion/siminf.html) |

## What it's for

SimInf simulates disease spread over networks of subpopulations, using Gillespie's algorithm for within-node dynamics and **scheduled events** for between-node movement. It was built for livestock disease modeling, where the data is a national animal-movement register: real, dated, recorded transfers of animals between holdings.

That origin gave a design worth studying, which generalizes well beyond veterinary epidemiology: it separates **continuous-time stochastic dynamics** (the transitions) from **scheduled actions on the population** (the events).

## How a model is specified

```r
model <- mparse(
  transitions = c(
    "S -> beta * S * I / N -> I",
    "I -> gamma * I -> R",
    "N <- S + I + R"
  ),
  compartments = c("S", "I", "R"),
  gdata = c(beta = 0.16, gamma = 0.077),
  u0 = data.frame(S = 100, I = 1, R = 0),
  tspan = 1:100
)

result <- run(model, seed = 22)
plot(result)
```

`mparse` parses the transition strings, builds the state-change matrix `S` and the dependency graph `G`, generates C code, compiles it, and returns a model object. Syntax:

- `"X -> rate_expr -> Y"`: move individuals from `X` to `Y` at propensity `rate_expr`
- `"@"` is the empty set: `"I -> mu*I -> @"` is death, `"@ -> lambda -> S"` is birth
- `"N <- S + I + R"` defines an intermediate variable, usable in any propensity
- `"(int)N <- S+I+R"` forces integer type

**Order does not matter**: the parser resolves the dependency graph. Intermediate variables are the same idea as odin's derived quantities and camdl's `let` bindings.

## Data layers and the local/global split

SimInf is unusually clear about where each parameter applies:

| Layer | Meaning | Form |
|---|---|---|
| `u0` | Initial discrete state per node | data.frame, one row per node |
| `gdata` | **Global** data: parameters common to all nodes | named numeric vector |
| `ldata` | **Local** data: node-specific parameters | data.frame or matrix, one column per node |
| `v0` | Initial **continuous** state per node | Continuous variables alongside the discrete compartments |

The `u`/`v` split is unusual and useful: `u` holds integer compartment counts governed by the Markov chain, and `v` holds continuous node-level variables (environmental contamination, accumulated pathogen load) updated after each step. The built-in `SISe` family uses this for an SIS disease coupled to a continuous environmental compartment.

MetaCast draws the `gdata` / `ldata` distinction as `universal_params` versus `subpop_params`.

## Scheduled events

The second half of the design. Events are a table of dated population movements:

- **Exit**: individuals leave a node
- **Enter**: individuals arrive
- **Internal transfer**: individuals move between compartments within a node
- **External transfer**: individuals move between nodes

Two matrices control them. The **select matrix `E`** says which compartments an event can draw from and with what sampling weights; the **shift matrix `N`** says how individuals are moved between compartments during an event.

So a real animal-movement register (200,000 dated transfers between holdings) can be loaded directly as the events table, and the model runs on actual movements and not a mobility model. The data often support this way of driving a metapopulation.

## Core abstractions

| Concept | SimInf name | Notes |
|---|---|---|
| Compartment | `compartments` | Discrete, per node |
| Transition | `"S -> propensity -> I"` | Parsed to a state-change matrix and a dependency graph |
| Intermediate | `"N <- S + I + R"` | Order-independent, typed (`double` or `(int)`) |
| Global parameter | `gdata` | Same in every node |
| Local parameter | `ldata` | Per node |
| Continuous state | `v0` + `pts_fun` | Per-node continuous variables updated post-step |
| Event | events data.frame + `E` (select) + `N` (shift) | Exit / enter / internal / external transfer |
| Escape hatch | `pts_fun`, `pre_code` | C code inserted into the generated model |
| Inference | `abc`, `pfilter`, `pmcmc` | ABC, particle filter, particle MCMC, built in |
| Packaging | `package_skeleton()` | Turns a model into an installable R package |

## Time

`tspan` is the vector of times at which output is recorded. The process is continuous-time Gillespie, so there is no `dt` and no conversion from rates to probabilities. Events are dated by time index.

Continuous time avoids the conversion errors of discrete-time frameworks, at a cost in scale, since Gillespie's cost grows with the number of events.

No dimensional types; propensities are C expressions, and their units are up to the modeler.

## Strengths

- **Transitions as strings that read like reactions.** `"S -> beta * S * I / N -> I"` is close to what a modeler would write, and it compiles to C.
- **Intermediate variables in any order**, with an optional integer type.
- **A clear split between global and local parameters.**
- **Discrete and continuous state side by side** (`u` and `v`), natural for diseases with environmental transmission.
- **Scheduled events driven by data**, with select and shift matrices controlling which compartments are affected and how.
- **Real movement data can drive the metapopulation.** No mobility model is needed when a register exists.
- **Continuous-time Gillespie**, so no time-step conversion errors.
- **Inference built in**: ABC, particle filter, particle MCMC.
- **`package_skeleton()`** turns a model into an R package, a good idea for reproducibility that nothing else here offers.
- **OpenMP parallelism** across replicates and nodes.

## Limitations

- **Transitions are strings.** They are readable, but unchecked until parsed, and the propensity is C, so an error appears as a C compiler message through R.
- **The `E` and `N` matrices are hard to read.** Seeing what an event does means reading two matrices alongside the events table. This is the hardest part of an otherwise clear design, and it holds the most important logic.
- **Gillespie only.** No ODE limit, tau-leaping, or agent-based mode, so large populations are expensive.
- **No agents.** Individuals in a node are identical, and heterogeneity means adding compartments.
- **No dimensional types**, and no calendar dates in the core (times are indices).
- **No intervention vocabulary** beyond events; interventions are parameter changes or scheduled transfers.
- **Every model is compiled**, so a working C compiler is required.
- **No observation model**; inference compares to compartment counts through user-supplied functions.

## Implications for the lingua franca

1. **The transition string is a good target for readability.** `"S -> beta * S * I / N -> I"` and camdl's `infection : S --> I @ beta * S * (I / N)` have the same shape, and camdl's adds a name and types. So the notation is close to right, and what it needs is names, types, and proper checking.
2. **Take events, and make them easier to read.** "At time t, move n individuals of these compartments from node a to node b" is something the lingua franca needs, because real intervention and movement data arrive this way. SimInf's version is correct, and its matrices are hard to read. MetaCast's transfer dictionaries (`{from_coordinates, to_coordinates, states, parameter}`) express the same thing readably.
3. **Adopt the `u`/`v` split of discrete stochastic and continuous state.** Environmental reservoirs, accumulated exposure, and vector abundance are naturally continuous, and coupled to a discrete disease process. Without this, everything has to be a compartment. Starsim's `FloatArr` states play a similar role for agents.
4. **Declare whether parameters are global or local.** SimInf's `gdata`/`ldata` and MetaCast's `universal_params`/`subpop_params` are the same idea. With dimensions, this becomes "a parameter has a shape", epymorph's more general answer (`Shapes.Scalar`, `Shapes.N`, `Shapes.TxN`).
5. **Continuous time should be a choice of solver, not of paradigm.** SimInf shows the benefit of never converting a rate to a per-step probability, and camdl offers Gillespie, chain binomial, and ODE from one model. Discrete versus continuous time should be a solver choice with a stated cost.
6. **Take `package_skeleton()`.** A command that turns a model into something installable and citable serves reproducibility directly, and is simple once the model is data.

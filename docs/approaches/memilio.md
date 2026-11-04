---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# MEmilio

|  |  |
|---|---|
| **Language** | C++ (core), Python bindings |
| **Paradigms** | ODE, integro-differential (IDE), linear-chain-trick (LCT / GLCT), SDE, metapopulation (graph-ODE), agent-based, and hybrid agent–metapopulation |
| **Specification style** | C++ template model classes; parameters as typed tag structs |
| **Version reviewed** | current `main` |
| **License** | Apache-2.0 |
| **Code** | <https://github.com/SciCompMod/memilio> |
| **Docs** | <https://memilio.readthedocs.io/> |
| **Paper** | Bicker et al. (2026), [arXiv:2602.11381](https://doi.org/10.48550/arXiv.2602.11381), plus a paper per model family |
| **Ecosystem** | DLR / Forschungszentrum Jülich; `memilio-simulation`, `memilio-epidata`, `memilio-generation`, `memilio-surrogatemodel` |
| **Moving to Starsim** | [Conversion guide](https://starsim.org/v4/user_guide/conversion/memilio.html) |

## What it's for

MEmilio is a high-performance C++ library implementing many model families for the same epidemiological problem, so that the *formulation* can be varied and compared. Its model directory is the review's clearest map of the paradigm space:

```
ode_sir  ode_seir  ode_secir  ode_secirvvs  ode_secirts  ode_seair  ode_seirdb  ode_seirv  ode_mseirs4
ide_seir  ide_secir                         # integro-differential
lct_secir  glct_secir  lct_secir_2_diseases # linear chain trick
sde_sir  sde_sirs  sde_seirvv               # stochastic differential
ode_seir_metapop                            # metapopulation
abm  d_abm  graph_abm  smm                  # agent-based variants
hybrid                                      # agent ↔ metapopulation
```

For this project, what matters most is what that list shows: **there are not two or three paradigms but a whole grid of them**, and moving between them changes what a model can express, in specific, documented ways.

## How a model is specified

A model is a C++ class instantiated and configured through typed parameter tags:

```cpp
mio::osir::Model<ScalarType> model(1);   // 1 age group

model.populations[{mio::AgeGroup(0), mio::osir::InfectionState::Infected}]  = 1000;
model.populations[{mio::AgeGroup(0), mio::osir::InfectionState::Recovered}] = 1000;
model.populations[{mio::AgeGroup(0), mio::osir::InfectionState::Susceptible}] = total - ...;

model.parameters.set<mio::osir::TimeInfected<ScalarType>>(2);
model.parameters.set<mio::osir::TransmissionProbabilityOnContact<ScalarType>>(0.5);

auto& contact_matrix = model.parameters.get<mio::osir::ContactPatterns<ScalarType>>().get_cont_freq_mat();
contact_matrix[0].get_baseline().setConstant(2.7);
contact_matrix[0].add_damping(0.6, mio::SimulationTime<ScalarType>(12.5));

model.check_constraints();

auto integrator = std::make_unique<mio::EulerIntegratorCore<ScalarType>>();
auto sir = mio::simulate<ScalarType>(t0, tmax, dt, model, std::move(integrator));
auto interpolated = mio::interpolate_simulation_result<ScalarType>(sir);
```

Three features stand out.

**Parameters are types.** `TimeInfected`, `TransmissionProbabilityOnContact`, and `ContactPatterns` are C++ types, checked when the model is compiled. A misspelled parameter is a compile error and not a silently ignored name, which is the strongest checking of parameter names in the review.

**Populations are indexed by checked coordinates.** `populations[{AgeGroup(0), InfectionState::Infected}]` is a position in an (age × state) space, like MetaCast's coordinates or camdl's strata.

**Constraints are checked explicitly**, in a separate step: `model.check_constraints()`.

## Model families and what distinguishes them

| Family | What it adds | Cost |
|---|---|---|
| **ODE** | Baseline compartmental | Exponential dwell times |
| **LCT / GLCT** | Linear chain trick: sub-compartments give Erlang (and generalized) dwell-time distributions | More state |
| **IDE** | Integro-differential: arbitrary dwell-time distributions via memory kernels | Non-Markovian, harder to solve and to initialize |
| **SDE** | Diffusion-approximation stochasticity | Approximation valid only at moderate-to-large populations |
| **Graph-ODE / metapop** | Nodes with explicit mobility, including traveler states in transit | Mobility formulation matters (there is a paper on exactly this) |
| **ABM** | Individual agents with locations and activity-driven contacts | Cost, and calibration difficulty |
| **Hybrid** | Agents where resolution is needed, metapopulation elsewhere | Coupling semantics at the boundary |

MEmilio has a published paper for nearly every one of these, including *"the Linear Chain Trick in epidemiological models: implications of underlying assumptions for numerical solutions"*. The choice between them is a modeling decision with consequences, and the library is built so they can be compared.

## SBML import

`cpp/sbml_model_generation/sbml_to_memilio.cpp` reads SBML and generates MEmilio model files. This is the only **model-format importer** in the review other than MIRA's, and a direct precedent for the lingua franca's goal of converting between frameworks.

## Time

Simulation time is `ScalarType` with an explicit `dt` passed to `simulate()`, and integrators are pluggable (`EulerIntegratorCore`, adaptive RK). `mio::SimulationTime<ScalarType>` is a separate type used for scheduling (contact-matrix dampings), so time has a type and rates do not.

`interpolate_simulation_result()` puts adaptive-integrator output onto a regular grid, a small, often-needed step that most frameworks leave to the user.

## Interventions

Interventions are **dampings on the contact matrix**: `contact_matrix[0].add_damping(0.6, SimulationTime(12.5))` reduces contacts to 60% from day 12.5, and dampings can be combined. Vaccination and testing are extra compartments in the `secirvvs` and `secirts` variants.

Epydemix's contact-layer interventions are the same design, with the same scope and limit.

## Strengths

- **By far the widest range of paradigms in the review**, each implemented properly.
- **Dwell-time distributions as a modeling choice in their own right**: exponential (ODE), Erlang (LCT), generalized (GLCT), arbitrary (IDE). Every other framework here gives this less attention.
- **Hybrid agent–metapopulation models**, with a paper justifying the coupling.
- **Parameter names checked at compile time**, which nothing else in the review does.
- **Checked population indices** (age × infection state).
- **An SBML importer**, a working precedent for converting between formats.
- **Explicit `check_constraints()`** as a separate step.
- **Result interpolation** onto regular grids from adaptive integrators.
- **Serious performance and parallelism**, with published national-scale applications.
- **Python bindings and a surrogate-model package**, so analysts can reach the C++ core.

## Limitations

- **The model is C++ template code.** Adding a compartment means writing a new model class. There is no model-definition language, and a model cannot be saved or read as data.
- **Every model family is a separate implementation.** `ode_seir`, `lct_secir`, `ide_seir`, and `sde_sir` are different C++ classes with different parameters. No single description generates them. This is the gap this project aims to fill, and MEmilio shows how much it costs: a large, well-funded, multi-year effort wrote each paradigm separately.
- **Hard to get started.** C++17 templates, CMake, and a large API.
- **No intervention vocabulary** beyond contact-matrix dampings.
- **No observation model.** Comparison to data happens outside the library.
- **Rates are not dimensionally typed**, though time partially is.

## Implications for the lingua franca

1. **MEmilio shows what it costs *not* to have a lingua franca.** Twenty-plus model families, each implemented separately, each with its own paper, share a parameter convention but no common description. If one typed description could generate the ODE, LCT, SDE, and metapopulation forms of a model, that work would be saved.
2. **Dwell-time distribution is a modeling choice, and the language should express it.** ODE means exponential, LCT means Erlang with *k* stages, and IDE means an arbitrary kernel. camdl handles this with `via erlang` / `via hyper_erlang` and treats it as *residence structure*, not as a stratification. That distinction is right. Most frameworks here assume exponential dwell times without saying so.
3. **Use the grid of paradigms as the design's map.** There are not four options ("compartmental / metapopulation / SDE / ABM") but several axes: aggregation (compartment ↔ agent), stochasticity (deterministic ↔ diffusion ↔ jump), dwell time (exponential ↔ Erlang ↔ arbitrary), and space (single ↔ patch ↔ explicit mobility). A model picks a point, and a conversion moves along an axis. Which conversions make sense can then be answered per axis.
4. **Checking parameters before running is possible and worth it.** MEmilio gets this from C++ types and camdl from its compiler; Starsim checks at run time, through `define_pars`. EpiModel, Epydemix, and MetaCast do not check. A misspelled parameter name should be an error.
5. **Study the SBML importer.** It is a working example of what this project needs (a shared format → a runnable model), including the parts that do not map cleanly.
6. **People in transit are a real modeling concern.** MEmilio has a paper on representing people moving between patches. A metapopulation language with only "in patch i" or "in patch j" cannot say this, and the lingua franca should decide deliberately whether it can.

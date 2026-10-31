# epipack

|  |  |
|---|---|
| **Language** | Python (with SymPy for the symbolic layer) |
| **Paradigms** | Compartmental: deterministic ODE, stochastic well-mixed (Gillespie), and stochastic on networks; all from one process specification |
| **Specification style** | Reaction-style tuples: the model is a list of processes |
| **Version reviewed** | 0.1.x |
| **License** | MIT |
| **Code** | <https://github.com/benmaier/epipack> |
| **Docs** | <http://epipack.benmaier.org> |
| **Paper** | [10.21105/joss.03097](https://doi.org/10.21105/joss.03097) |

## What it's for

epipack makes the *analysis* of compartmental models cheap, so that changing a model stays cheap. Its motivation is that adding a compartment with pen and paper is easy, while redoing the ODE derivation, numerical integration, stochastic simulation, and stability analysis is not.

For this project it is the most direct evidence that **one list of processes can run in several paradigms**: the same list of tuples goes to `EpiModel` (numeric ODE and Gillespie), `SymbolicEpiModel` (symbolic ODEs, Jacobian, fixed points), or `StochasticEpiModel` (network simulation).

## How a model is specified

The model is a list of reaction tuples. A 3-tuple is a spontaneous transition, a 5-tuple is a transmission:

```python
from epipack import EpiModel

S, I, R = list("SIR")
N = 1000

SIRS = EpiModel([S, I, R], N)\
    .set_processes([
        (S, I, 2.5, I, I),   # S + I --(2.5/day)--> I + I    transmission
        (I, 1, R),           # I     --(1/day)-->   R         transition
        (R, 1/14, S),        # R     --(1/14/day)-> S         waning
    ])\
    .set_initial_conditions({S: N-10, I: 10})

result_int = SIRS.integrate(np.linspace(0, 40, 1000))   # deterministic
t_sim, result_sim = SIRS.simulate(40)                    # stochastic, same model
```

Swap the class and the same tuples become symbolic:

```python
import sympy as sy
from epipack import SymbolicEpiModel

S, I, R, eta, rho, omega = sy.symbols("S I R eta rho omega")

SIRS = SymbolicEpiModel([S, I, R]).set_processes([
    (S, I, eta, I, I),
    (I, rho, R),
    (R, omega, S),
])

SIRS.ODEs_jupyter()                             # renders the ODE system
SIRS.jacobian()                                 # symbolic Jacobian
SIRS.find_fixed_points()                        # symbolic fixed points
SIRS.get_eigenvalues_at_disease_free_state()    # {-omega: 1, eta - rho: 1, 0: 1}
```

Or the network version, where transmission is edge-mediated:

```python
model = StochasticEpiModel([S, I, R], N, links)\
    .set_link_transmission_processes([(I, S, 1.0, I, I)])\
    .set_node_transition_processes([(I, 1.0, R)])\
    .set_random_initial_conditions({S: N-5, I: 5})
```

This last one uses *different* processes (link transmission and node transition are separate), not the same tuples. So the unification is not quite complete, which is a useful finding.

## Core abstractions

| Concept | epipack form | Notes |
|---|---|---|
| Compartment | a string, or a SymPy symbol | Symbols in the symbolic model, strings elsewhere |
| Transition | `(A, rate, B)` | Spontaneous |
| Transmission | `(A, B, rate, C, D)` | `A + B → C + D`; general enough to express fission, fusion, birth, death |
| Rate | number, callable `f(t, y)`, or SymPy expression | Time- and state-dependent rates in all three modes |
| Network | edge list of `(u, v, weight)` | `StochasticEpiModel` only |
| Conditional transmission | `set_conditional_link_transmission_processes` | Cascading events on a link: e.g. contact tracing |
| Model variants | `EpiModel`, `SymbolicEpiModel`, `StochasticEpiModel`, `MatrixEpiModel`, `SymbolicMatrixEpiModel` | Five classes over one conceptual model |

## Time and rates

Rates are plain numbers, callables of `(t, y, *args)`, or SymPy expressions in `t`. Time-varying transmission is written directly:

```python
def infection_rate(t, y, *args, **kwargs):
    return 3 + np.sin(2*np.pi*t/100)
```

or symbolically, in which case `SIRS.ODEs_jupyter()` shows the forced system, and the Gillespie simulation uses the algorithm for inhomogeneous Poisson processes. Most frameworks skip or approximate this *correct* simulation of time-varying rates.

There are no units and no dimensional types.

## Analysis capabilities

Here epipack is unlike anything else in the review. From the symbolic model:

- the ODE system, rendered in LaTeX
- the Jacobian, symbolically
- fixed points, symbolically
- eigenvalues at the disease-free state, which give **the epidemic threshold, derived**

`SIRS.get_eigenvalues_at_disease_free_state()` returning `{-omega: 1, eta - rho: 1, 0: 1}` means R₀ > 1 ⟺ η > ρ, with no derivation by the modeler.

This takes transitions as data further than anything else here: because the model is symbolic, standard dynamical-systems analysis is one function call.

## Strengths

- **One process list, three kinds of run**: deterministic ODE, well-mixed stochastic, and network stochastic. This shows paradigm independence working.
- **Symbolic analysis for free**: ODEs, Jacobian, fixed points, eigenvalues, and the epidemic threshold.
- **A general reaction form.** `(A, B, rate, C, D)` covers transmission, fission, fusion, birth, and death in one form, with no list of flow kinds.
- **Time- and state-dependent rates in every mode**, including a correct inhomogeneous-Poisson Gillespie.
- **Conditional link transmission**: cascading events on an edge, a natural way to write contact tracing, and rare elsewhere.
- **Very short models.** An SIRS model is five lines and reads like the reaction scheme.
- **Interactive exploration** (`InteractiveIntegrator`) and animated networks.

## Limitations

- **No longer actively maintained.** Pinned dependencies (`sympy==1.6`, `pyglet<1.6`, Python 3.6–3.8) and the changelog put it well behind current Python. The ideas remain current.
- **The unification is incomplete.** `StochasticEpiModel` uses `set_link_transmission_processes` / `set_node_transition_processes`, and `EpiModel` uses `set_processes`, so a network model is written differently.
- **No stratification function.** Age structure means writing out `S_child`, `S_adult`, and every process between them by hand, the opposite of summer2.
- **No dimensional types, no units.**
- **No intervention vocabulary.** Interventions are time-varying rates.
- **No observation model or inference.**
- **Networks need a manually installed C++ package** (`SamplableSet`) for acceptable speed.
- **Fixed points and eigenvalues do not scale.** Symbolic analysis works for a few compartments and not for a stratified model, where the derivation by hand would also be hardest.

## Implications for the lingua franca

1. **The strongest proof of the project's central idea.** One description, three paradigms, in a working package. Whatever else is uncertain, this is settled: the same model can run as deterministic, stochastic, and network simulations.
2. **The reaction form `A + B → C + D @ rate` is a candidate building block.** It is more general than summer2's named flow kinds and more structured than a free rate expression. But a general reaction is easy to write and hard to stratify automatically, because the framework does not know what it means. The lingua franca probably needs the general form underneath, with named kinds as shorthand over it, as in camdl.
3. **Symbolic analysis is a reason to keep the model symbolic.** epipack gets the Jacobian and the epidemic threshold because the model is symbolic data. If the lingua franca's internal form is symbolic too, R₀ derivation, sensitivity analysis, and identifiability checks can follow. camdl already uses this for gradients.
4. **Watch where the unification breaks.** epipack's network mode is written differently because edge-based transmission differs from mass action: the rate is per edge, not per pair of populations. Starsim's routes are another attempt at this division. **Writing mass-action, contact-matrix, and edge-based transmission as one declaration is the hardest unsolved problem in this review**, and it is where the lingua franca has to do original work.
5. **Time-varying rates should work the same across paradigms.** epipack takes a function or a symbolic expression and does the right thing in ODE and Gillespie modes. A rate should be an expression in time and state, and each solver should handle it correctly or refuse.
6. **Symbolic methods do not scale, and the language should say so.** For a stratified model, `find_fixed_points()` is impractical. As in camdl, the limit should be named, with no slow failure.

# MetaCast

|  |  |
|---|---|
| **Language** | Python |
| **Paradigms** | Metapopulation ODE: a user-supplied subpopulation model broadcast across arbitrary dimensions |
| **Specification style** | A Python function defining the subpopulation model, plus a declarative dimension specification |
| **Version reviewed** | 0.x |
| **License** | (see repository) |
| **Code** | <https://github.com/m-d-grunnill/MetaCast> |
| **Docs** | <https://metacast.readthedocs.io/> |
| **Paper** | Grunnill et al. (2024), *JOSS* 9(99): 6851, [10.21105/joss.06851](https://doi.org/10.21105/joss.06851) |

## What it's for

MetaCast takes one subpopulation model and "broadcasts" it across a metapopulation whose dimensions the user declares. Its premise is that stratification, metapopulation structure, and any other division of the population are **the same operation** (a dimension the model is repeated over), so the within-group dynamics need writing only once.

It is a small package, and its contribution here is an idea: structure is **a set of dimensions**, separate from the model.

## How a model is specified

The subpopulation model is a function with a fixed signature:

```python
def subpop_model(y, y_deltas, parameters, states_index, subpop_suffix, foi):
    infections               = foi * y[states_index['S']]
    progression_from_exposed = parameters['sigma'] * y[states_index['E']]
    p_hosp                   = parameters['p' + subpop_suffix]   # subpopulation-specific
    progression_from_inf     = y[states_index['I']] * parameters['gamma']
    recovery                 = progression_from_inf * (1 - p_hosp)
    hospitalisation          = progression_from_inf * p_hosp
    hospital_recovery        = y[states_index['H']] * parameters['eta']

    y_deltas[states_index['S']] += -infections
    y_deltas[states_index['E']] += infections - progression_from_exposed
    y_deltas[states_index['I']] += progression_from_exposed - progression_from_inf
    y_deltas[states_index['H']] += hospitalisation - hospital_recovery
    y_deltas[states_index['R']] += recovery + hospital_recovery
    return y_deltas
```

Then the dimensions:

```python
metapop = MetaCaster(
    dimensions        = [['high', 'low'], ['unvaccinated', 'vaccination_lag', 'vaccinated']],
    subpop_model      = subpop_model,
    states            = ['S', 'E', 'I', 'H', 'R'],
    infected_states   = ['E', 'I', 'H'],
    infectious_states = ['I'],
    subpop_params     = {...},
    universal_params  = [...],
)
```

`dimensions` accepts an int, a list of labels, a list of ints, a list of label lists (multidimensional), or a list of **transfer dictionaries** describing flows between subpopulations:

```python
{
  "from_coordinates": ["high", "unvaccinated"],
  "to_coordinates":   ["high", "vaccination_lag"],
  "states":           "all",
  "parameter":        "nu_unvaccinated",
}
```

So "vaccination" is not a process in the model; it is a **transfer between coordinates of the vaccination dimension**, declared in the dimension specification.

## Core abstractions

| Concept | MetaCast name | Notes |
|---|---|---|
| Subpopulation model | a function `(y, y_deltas, parameters, states_index, ...)` | Written once, run per coordinate |
| Dimension | entry in `dimensions` | Ints, labels, nested lists, or transfer dicts |
| Coordinate | a tuple across dimensions, e.g. `[high, vaccinated]` | Suffixes parameter names: `beta_[high,vaccinated]` |
| Transfer | a transfer dictionary | Movement of hosts between coordinates, for named states, at a named rate |
| Force of infection | computed by the framework | From `transmission_term_prefix` (`beta`), `subpop_interaction_prefix` (`rho`), `population_term_prefix` (`N`), and `foi_population_focus` |
| Parameter class | `universal_params` vs `subpop_params` | Explicitly separates "same everywhere" from "varies by dimension" |
| Observed state | `observed_states` | Accumulators appended to the state vector |
| Event | `event_handling.event_queue` | Discrete events: moving populations, changing parameters |
| Sensitivity | LHS + PRCC, parallelised via dask | Built in |

## The force-of-infection convention

MetaCast's boldest choice is to **compute the force of infection for you** from a naming convention. Given prefixes `beta`, `rho`, and `N`, and a `foi_population_focus` setting (`None`, `'i'`, or `'j'`), it builds

λᵢ = Σⱼ ρᵢⱼ · βⱼ · Iⱼ / Nⱼ

with the denominator set by `foi_population_focus`. The subpopulation model receives `foi` as an argument and never computes it.

The instinct is right: force of infection between groups is the part that most often goes wrong, so it belongs outside the model. The tradeoff is that it rests on building parameter names from strings (`'beta_[high,vaccinated]'`), which is easy to break.

Also, `asymptomatic_transmission_modifier` applies automatically to any state in `infectious_states` but not in `symptomatic_states`. This is real epidemiology held in a relationship between sets, and a language should be able to say it.

## Strengths

- **Structure as a set of dimensions.** Age, space, risk, and vaccination status are all dimensions, and within-group dynamics are written once. This is the neatest statement of the stratification problem in the review.
- **Transfers between coordinates, as data.** `{from_coordinates, to_coordinates, states, parameter}` covers vaccination, aging, and migration in one form, as movement along a dimension.
- **Force of infection handled by the framework**, with an explicit `foi_population_focus` for the denominator.
- **Parameters classed** as universal or subpopulation-specific.
- **Declared sets of states**: `infected_states`, `infectious_states`, and `symptomatic_states`, with the asymptomatic modifier following from the difference.
- **An event queue** for scheduled population movements and parameter changes.
- **Sensitivity analysis built in** (LHS + PRCC, in parallel).

## Limitations

- **The subpopulation model is NumPy index arithmetic.** `y_deltas[states_index['S']] += -infections` is code indexing into a shared array. There is no transition object, and sign errors are easy to make.
- **Results depend on position in the state vector.** `y_deltas[-2]` and `y_deltas[-1]` are the observed-state accumulators, with a comment to say so.
- **Parameter names are built from strings.** `parameters['p' + subpop_suffix]`, `'beta_[high,vaccinated]'`. Typos are errors during the run, and nothing checks that all expected names were supplied.
- **ODE only.** No stochastic or agent-based runs.
- **Small, with few users.** One demonstration notebook, a JOSS paper, and limited independent use.
- **No dimensional types**, calendar dates, observation model, or inference beyond sensitivity analysis.
- **The force-of-infection convention is limited** to the frequency-dependent multi-group case it was designed for.

## Implications for the lingua franca

1. **Take the idea that stratification, metapopulation, and multi-group structure are one operation.** MetaCast, summer2 (`stratify_with`), camdl (`dimensions` + `stratify`), and epymorph (`MultiStrataRUME`) attempt the same thing, and MetaCast states the general case most plainly. The lingua franca should have **one concept of a dimension** for age, space, risk, strain, and vaccination status, with a way to mark dimensions that carry extra structure (aging flows, movement, residence times), as summer2 and camdl show.
2. **Transfers between coordinates deserve a declared form.** Vaccination as `{from: [high, unvaccinated], to: [high, vaccination_lag], states: all, rate: nu}` is a useful way of saying it: the individual keeps their disease state and moves along a *dimension*. camdl's `transfer(from = S, to = V)` is close, but MetaCast's works across all states and any dimension at once. This is a strong candidate for the intervention vocabulary.
3. **The framework should compute force of infection, with explicit settings.** Taking λ out of the model is right, and a checked form would be safer than strings. The language needs to say which states are infectious, which mixing applies, and which denominator (`None` / `i` / `j`) is used, because the three are different models, and in most frameworks the difference cannot be seen.
4. **Declare sets of epidemiological states.** Separate `infected_states`, `infectious_states`, and `symptomatic_states` are a small idea worth keeping. They tell a framework that "infected" and "infectious" differ, as Starsim also allows (`infectious` defaults to `infected` but can differ) and most others do not.
5. **Declared transitions would complete this design.** MetaCast's dimensions are declared and checkable, while the model it repeats is index arithmetic. Put camdl's or epipack's transition objects inside MetaCast's dimensions, and you have most of what this project needs.

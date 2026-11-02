# Pandemic Simulator

|  |  |
|---|---|
| **Language** | Python, on JAX |
| **Paradigms** | Compartmental only: deterministic ODE, and stochastic runs as many tau-leaping trajectories |
| **Specification style** | A class per model: a declared schema of compartments, edges, and fields, plus a hand-written `equation()` |
| **Version reviewed** | 0.1.0, `main` at commit `5ec712b` (October 2026), read but not run |
| **License** | Apache 2.0 |
| **Code** | <https://github.com/WHO-Collaboratory/pandemic-simulator-compartment> |
| **Docs** | <https://who-collaboratory.github.io/pandemic-simulator-compartment/> |
| **Paper** | None found |

## What it's for

This is the model layer of the World Health Organization Pandemic Hub's Pandemic Simulator, a web application. Modelers contribute compartmental models as pull requests. After review, anyone can run them from a form in the browser, with no code. Its users are decision makers, so its design question is not how to write a model but how to put someone else's model safely in front of them.

For this project it is the clearest example of **a model as a published product**, with its form, validation, documentation, and review all generated from or attached to the model. No other framework reviewed here goes as far in this direction. It also holds 22 models, many of them translations of published papers, for dengue, Ebola, COVID-19, mpox, measles, hantavirus, chikungunya, and *Klebsiella*.

## How a model is specified

A model is a directory with `model.py`, `example-config.json`, `model.md`, and `main.py`. The class declares a schema and writes the equations:

```python
class MyModel(Model):

    @classmethod
    def define_parameters(cls, schema):
        schema.set_model_info(disease_type='my_sir', label='My SIR', description='...')
        schema.set_model_metadata(questions_answered=[...], key_assumptions=[...], not_for='...')
        schema.add_compartment('S', 'Susceptible', 'Population susceptible to infection')
        schema.add_compartment('I', 'Infected', 'Currently infectious', infective=True)
        schema.add_compartment('R', 'Recovered', 'Recovered and immune')
        schema.add_transmission_parameter(
            source='susceptible', target='infected', variable_name='beta', frequency_dependent=True,
            label='Transmission Rate', description='...', default=0.3,
            default_min=0.1, default_max=0.5, min_value=0.01, max_value=2.0, unit='per day')
        schema.add_transmission_parameter(
            source='infected', target='recovered', variable_name='gamma',
            label='Recovery Period', description='...', default=10.0,
            value_type=ValueType.DAYS, unit='days')
        schema.add_intervention(id='masks', label='Masks', description='...', target_rates=['beta'])

    def equation(self, y, t, p):
        params = self._unpack_params(p)
        states = {c: y[i] for i, c in enumerate(self.compartment_list)}
        prop_infective = states['I'].sum() / (sum(states[c] for c in ('S', 'I', 'R')).sum() + 1e-10)
        rates, self.travel_matrix = self._apply_interventions(t, {'beta': params['beta']}, prop_infective)
        rates['gamma'] = params['gamma']
        derivs = self._compute_equations(states, rates)
        return jnp.stack([derivs[c] for c in self.compartment_list])
```

From the schema alone the framework builds the Pydantic validation of a config, the JSON artifact that drives the web form and database, an example config, cumulative `*_total` compartments, and the registry entry. A JSON config then supplies values, dates, zones, and which inputs are uncertain.

## Core abstractions

| Concept | Form | Notes |
|---|---|---|
| Compartment | `add_compartment(id, label, description, infective=)` | `infective` marks what enters the force of infection |
| Edge | `add_transmission_parameter(source, target, variable_name, ...)` | Both a flow and a form field; source and target are matched by label |
| Value type | `ValueType.RATE`, `DAYS`, `PERCENTAGE`, ... | `DAYS` and `PERCENTAGE` are converted on edges only; other parameters arrive in native units |
| Intervention | `add_intervention(target_rates=, modifies_travel=)` | Scales rates by `1 - adherence*reduction`, or stops travel |
| Zone | An entry of `admin_zones` | Name, population, coordinates, initial infected percentage |
| Age group | `add_demographic_group(id, label, default_weight, age_range=)` | Declaring `age_range` brings in a Prem contact matrix for the country |
| Run mode | Inferred | Deterministic, parameter uncertainty if anything has variance, stochastic if `STOCHASTIC = True` |
| Dataset | `datasets.yaml` beside the model, `self.dataset(name)` | Versioned, up to 500 MB, the same path locally and in the cloud |

## Time, solvers, and stochasticity

Deterministic models use JAX's adaptive `odeint`. Stochastic models set `STOCHASTIC = True`, and `equation()` then draws its own Poisson events and returns a change per day, which a fixed-step Euler loop applies. The output is daily up to 365 days and coarser after that. There are no typed times: the unit of a value depends on its `ValueType` and on where it is read.

## Interventions

A built-in intervention is on in a date window or when prevalence crosses `start_threshold`, and on stochastic models stays on until prevalence falls to `end_threshold`. Thresholds are percentages. It has two levers: scaling named rates, and replacing the travel matrix with the identity. Anything else is hand-written in `equation()`. **Every simulation runs twice, with and without its interventions**, so results always come with a control.

## Population and geography

Age mixing has three layers: the Prem (2021) matrix for the country named by the job's ISO3 code, a schema override, and a per-run override. A country that isn't in the bundled data falls back to the average for its World Bank income group, and then to a global average. Zones are coupled by a travel matrix in which `T[i, j]` is the share of zone `i` present in zone `j`, and a test checks its invariants for every model that declares `travel_sigma`. Models opt in, and each has to use the matrix in its own `equation()`.

## Uncertainty and fitting

Parameter uncertainty is Latin hypercube sampling over declared ranges of edges, interventions, and other parameters, summarized as a median and a 95% interval, by default with 30 runs. The guides say that only uniform distributions are supported, although the helper has four others. There is no calibration, and the measles model fits `beta` by its own code when it is loaded.

## Publishing a model

The most unusual part of the framework is what surrounds a model:

- **A model card as data.** `set_model_metadata()` takes authors, citations, `questions_answered`, `key_assumptions`, `applicability`, `not_for`, `constraints`, `biases`, and `validation`, and `model.md` is shown with the results.
- **A form from the schema.** The default and the range of each parameter, and its unit and label, become the form's fields, so that adding a parameter updates the interface.
- **Smoke tests by discovery.** Any directory with `model.py` and `example-config.json` is tested, with no registration.
- **Three kinds of review.** A guide gives AI prompts to convert a model and then audit it in a fresh chat, with a table per facet of the model giving a verdict and an exact quotation from the source. Human experts review the pull request, and publishing is a separate step.

## Strengths

- **One declaration serves everything around the model**: validation, form, example config, and documentation.
- **It says what a model is for and not for**, in a form that software can show to a reader.
- **Runs always have a control.**
- **A country gets a contact matrix with no extra work**, with a stated fallback when data is missing.
- **The conversion guide treats AI output as a draft to be audited**, against quotations from the source.
- **Its guides are candid** about limits, including that the default solver doesn't remember a threshold's status.
- **Many real translated models**, in one layout.

## Limitations

- **The schema does not describe the dynamics.** By a search of the code, 12 of the 22 models never call `_compute_equations()`, and only 2 use it with no skipped edges or manual flows. Elsewhere an edge can be mainly a form field. In `wuhan_seir_model`, `E -> Ic` is multiplied by a clinical fraction in `equation()`. In the measles model, `beta` is not an edge at all, so that users can't set it. The schema's graph can differ from the model that runs.
- **Compartmental only**, with one kind of solver for each model: changing a model from ODE to stochastic means writing a new `equation()`.
- **Positional and string-matched parts.** Parameters reach `equation()` as a tuple in edge order, compartments are positions in an array, edges match by label, and an unknown name in `target_rates` is skipped silently.
- **No check of units**, and easy slips between percentages and fractions, which the guides warn about. An omitted adherence reads as zero.
- **State in `equation()`.** The intervention status is written to `self` during integration, which is why `odeint` can't carry it between steps and the release threshold works only on stochastic models.
- **Things that look unintended, from reading only.** `example_stochastic_model` reads `seed` only if the config is a `dict`, while the run gives it a `ProcessedSimulation`, so a seed in a config seems not to reach it. Poisson draws per day are multiplied by a step that exceeds one day for runs over a year, which would change their variance. Neither has been tested.
- **Heavy for a simple model**: 188 lines for an SIR with one intervention, most of them metadata. Much of this is what the platform needs.

## Implications for the lingua franca

The [corpus example](../models/pandemic_simulator/sir_reactive/README.md) was translated to check these. Each item says what Starsim v4 already does.

1. **A release threshold is worth one keyword (done).** A lockdown that starts at 2% and ends at 1% is a common policy, and `ss.modify()` needed a coded module for it. `ss.modify(beta, multiply=0.5, where=I.n >= a, until=I.n <= b)` now states it, and every solver carries it, which the Pandemic Simulator's default solver can't.
2. **Audit a conversion against its source (done).** Comparing runs can't catch a mistake that both models share, or check a paper with no code. The `validate-conversion` skill now has the fidelity audit: each facet, a verdict, an exact quotation and where it is, in a fresh context.
3. **An exporter may matter more than an importer.** `ss.export_to(sim, 'pandemic_simulator')` could write a model directory: a declared Starsim model has what `define_parameters()` needs (states, transitions, parameter bounds, units, and labels), and rate expressions can be written as JAX. This would put Starsim models in front of the platform's users. It depends on the platform's reviewers wanting generated code.
4. **An importer in three tiers.** This framework's models are code, but a schema and an example config are available as data. As with summer2 and epydemix, a script run in the framework's own environment would write JSON, for which `python -m compartment.generate_artifact` is most of the work. Tier one, schema edges, covers models that only call `_compute_equations()`. Tier two records calls to `_apply_flow()` while tracing `equation()` under JAX, which gives each manual flow's source and target and, with a Jacobian, its dependence on the states; this covers most of the rest. Tier three is the remainder, such as Poisson draws written by hand, which the importer lists as incomplete for the `convert-model` skill. Reading the edges alone would give wrong models without warning, so the importer has to compare the edges with the traced flows. Probably 300 to 400 lines, like the epydemix importer. It would be tested on the 22 models, once they can be run.
5. **A schema of the model's inputs is a possible general feature.** Starsim's `ss.par` already holds a value, bounds, documentation, and a label. A sim could describe its inputs as JSON Schema, from which a web form, an MCP tool, or a validated config could be built. This is one function, not a platform, and fits the AI-friendliness principle, but nothing needs it yet.
6. **A model card is better as a convention than as a feature.** The fields are good: above all `not_for` and `biases`. A docstring section for library models, requested by the `convert-model` skill, gets most of this with no new API. A `metadata=` keyword could follow if a form or registry needs it.
7. **Fall back to similar countries.** A country with no contact matrix gets the average of its income group here. If `ss.contacts()` has gaps, this is a sensible fallback that can be printed as a guess, in keeping with the design's rule of guessing and saying so.
8. **Latin hypercube draws for `priors=True`.** `ss.fit` already samples this way, so uncertainty runs could too, for better coverage in few runs.
9. **What not to take.** Paired controls are already `msim.summarize(baseline=...)`, and cumulative compartments are already `.cum` on each flow. Parameters as positional tuples, percentages in native units, adherence and reduction as a fixed pair, and a schema separate from the dynamics are all things typed, declared transitions already avoid. It is telling that this framework's most careful guides are warnings about the separation that a declared model doesn't have.

# Principles

The principles the rest of this folder applies. Read this first; every other document assumes it.

## The test

Two statements define success, and every recommendation here is checked against them:

1. **A model should never be easier to write without the lingua franca than with it.**
2. **For each of the main frameworks (MEmilio, EpiModel, Epydemix, and the rest), its own examples can be written in the lingua franca in no more lines of model code than the original, and run in about the same time.**

The second is measurable. [models](../models) is where it gets measured, by `lingua_franca benchmark`, and the rows are published, failures included, on the docs' [conversion pages](https://starsim.org/v4/user_guide/conversion/index.html). Lines are the hard target: a translation fails if it has more lines of model code than the original. Time is two numbers, the first run in a fresh process and the best of five repeated runs. A time fails only if the translation is both more than twice as slow and more than 1 s slower, a difference a user would notice. One allowance: where the original calls a built-in specific to one situation (`interventions=close_schools_uk()`), the lines inside it count as part of the original. The aim is to match what a framework lets a modeler say, not its library of ready-made cases.

The second statement is a measurement, not a reason to add a feature. When the two pull apart (a held-out framework's example would be shorter with a name only that framework needs), principle 9 below wins for the core vocabulary: a proposed addition is checked against the questions in [17-vocabulary.md](../design/17-vocabulary.md#adding-to-the-vocabulary), and one that only a single framework needs belongs in a library built on top, or in that framework's importer, and the translation's row is published as failing.

## Recommendation

1. **The user is an epidemiologist, not a programmer.** Optimize the model text for someone who can read an equation and write a `for` loop, and who will never read the source of the library.
2. **The model text should look like the algorithm in the modeler's head.** If a step of the model takes one sentence to say, it should take about one line to write. `S >> I @ beta * I` is the target.
3. **Guess the default.** When the right answer is obvious 99% of the time, take it and say so when the model is described. A guess fills in what is missing and never reinterprets what was given. An error is for when a wrong guess would be silently harmful.
4. **One vocabulary, several lengths.** The operator form, the explicit form, and the class form are the same words written at different lengths. Keep the short form when adding a feature that only the long form needs.
5. **Complexity belongs in the library.** What the user writes may be tiny and what the library does with it may be large.
6. **Plain Python is always available, and it is not second class.** Real models have parts that are easiest to say as a function or a `step()` method. Those parts work everywhere they can, and the library says where they cannot.
7. **Expressions are Python, not strings.** A formula in a string (Atomica's, or a Polars-style expression) is not ruled out forever, but it gives up checking and error messages that point at the mistake, so it would need a strong reason, and none has come up yet.
8. **Approximate rather than refuse, and say what was approximated, within the supported subset.** A coarser model that runs is more useful than a refusal, as long as the user is told. This applies to the small declared subset that has a compartmental form (spec 12); outside it, `'auto'` runs the model as agents and an explicitly requested compartmental solver refuses before the run, rather than the library emulating individual histories, parent–child links, queues or remembered selection in compartments (decided 2026-10-20). Each approximation is a second way of running a feature, to be built and tested, so one is offered only where it is the standard one ([12-backends.md](../design/12-backends.md#approximations)); where there is none (a modifier with a share for each edge, under `solver='ode'`), the run stops with a `CapabilityError` naming a solver that works. There is no size limit yet: a stratification runs however many groups it makes. A limit past which `'auto'` picks agents and `approx=False` refuses is open ([19](../design/19-open-questions.md#b3-solverauto-and-near-compartmental-models)).
9. **A feature that only pays off in one framework's use case does not go in.** This wins over the second statement of the test when they conflict (see above). Most models will be written by an AI, which can hold any vocabulary. The person who has to read the model and decide whether it is right cannot, and it is the reader that the size of the vocabulary has to fit.
10. **Every core feature earns its place in the library's complexity, not just in the model text.** Principle 5 puts complexity in the library, but the library's size is a cost too: each feature written for every solver is written four to six times, and their combinations are where bugs and slow development come from. A new core feature needs repeated use across independent models, a clear alternative, a statement of which solvers support it, and an explanation of which existing concept it replaces or why it is essential. A few extra lines of ordinary model code (a `step()`, a callback, an explicit state) are fine when they remove a special-purpose framework feature (decided 2026-10-20).

## Why: the audience is the binding constraint

Frameworks differ most in who they are for, and that shapes the rest of their design.

[Atomica](../approaches/atomica.md) sets the standard for accessibility: a national HIV or TB model, with its compartments, parameters, derived indicators, and funded intervention programs, defined by a health ministry analyst in two Excel workbooks and no code. [`epidemics`](../approaches/epidemics.md) states the trade explicitly in its scope document: it "trades away some flexibility in defining model structures for a gain in the ease of defining epidemic scenario components", because its users are "public health practitioners rather than research-focussed modellers". [EMULSION](../approaches/emulsion.md) exists so that a model can be discussed with veterinarians and economists during development rather than translated for them afterwards.

At the other end, frameworks built for speed and scale ask more of their users: [MEmilio](../approaches/memilio.md) requires C++17 templates and CMake, [camdl](../approaches/camdl.md) an OCaml/Rust toolchain, and [EpiHiper](../approaches/epihiper.md) C++, MPI, and PostgreSQL. EpiHiper's "close schools on Fridays" is roughly 200 lines of JSON.

Starsim 3 sat in the middle, and its review flags the cost: "API surface is large. Six module categories, four state types, ~20 distributions, ~15 time classes, three rate types, and a `Loop` API. Each piece is justified; the total is a lot to hold, and the framework leans heavily on AI tooling to make it navigable — which is a signal about the specification burden, not a solution to it."

So **total vocabulary size is a design constraint, and every recommendation in this folder has to justify its share of it.** Several things in the first draft did not pass that test, and they are listed under [what we are not building](#what-we-are-deliberately-not-building).

## One vocabulary, several lengths

Starsim 3 had a short form for library models:

```python
sim = ss.Sim(diseases=dict(type='sir', beta=0.05, init_prev=0.01), networks='random')
```

and classes for everything else, and, as its review says, "there is no path from the first to the second, and the boundary is where most users get stuck." Vivarium has the same split (YAML lists components, Python defines them). EMOD has it (JSON configures, C++ implements). EMULSION has it (YAML, plus "code add-ons" that forfeit the model-as-document property).

The rule that follows:

> **Anything you can say in a short form means the same thing in a longer form, and moving from one to the next never means re-learning the words.** Subclassing adds *behavior*; it never adds *vocabulary*.

The same model, three ways:

```python
# 1. Operators: declare the states, then write the transitions the way they are said aloud
beta = 0.3
dur  = ss.days(10)

S, I, R   = ss.states(3)
infection = S >> I @ beta * I
recovery  = I >> R @ dur
sir = ss.Disease(infection, recovery, init_prev=0.01)

# 2. Explicit: the same transitions, with every part named
S, I, R = ss.states(3)
sir = ss.Disease(
    infection = ss.Transition(S, I, rate=0.3 * I),
    recovery  = ss.Transition(I, R, dur=10),
    init_prev = 0.01,
)

# 3. A class, when there is behavior that is not a transition
class SIR(ss.Disease):
    S, I, R   = ss.states(3)
    infection = S >> I @ 0.3 * I
    recovery  = I >> R @ ss.days(10)

    def step(self):
        super().step()
        self.log_something_bespoke()
```

All three build the same `ss.Transition` objects, and [model-structure.md](model-structure.md) gives the rules. Form 1 is the one to teach: it lists the ingredients before the method, it reads like the equations, and it shows the source of infection. Form 2 spells out what each number is. Form 3 uses form 1's words unchanged.

## Guessing defaults

The rule is not "never error". It is: **an error is a claim that no guess is safe, and that claim has to be true.** And a guess only fills a gap: it never changes the meaning of something the user wrote (a `1.0` is a number, whatever its type; a step of a week does not make a rate per week; a keyword number sets the parameter of that name or is an error).

Guess, and print it:

| Situation | Guess | Evidence |
|---|---|---|
| Initial conditions | Everyone in the first state; `init_prev` seeds the rest (below 1 a share, 1 or more a number of people), `init=` gives shares, and `init_n=` numbers of people; with none given and a transmission, 1% start infected | [odin](../approaches/odin.md) infers the state set from `initial()`; nobody should have to write both 0.99 and 0.01, and a model with nobody infected has no epidemic to show |
| Dwell-time distribution | Exponential, when a scalar duration or a rate is given | It is what every ODE means, and what [EMULSION](../approaches/emulsion.md) already assumes; the difference is that we *print* it |
| Units of a bare number | The model's unit: `unit=`, else the model's typed values (the finest, if they differ and the model has no bare numbers), else days for a dated sim, else a typed `dt`, `start`, or `stop`, else years for year-like `start` and `stop` (`stop=2020`); if nothing has a unit, time is in timesteps. A step of a week never makes a typed rate per day into one per week | Starsim and [Epydemix](../approaches/epydemix.md) apply the sim's unit; most frameworks surveyed count in steps. See [time-and-units.md](time-and-units.md) |
| Mixing, when no network is given | Homogeneous, so `beta` is the textbook transmission rate | It is what an unadorned SIR means |
| How the model is run | The simplest solver that represents it faithfully: an ODE if it can be one, agents otherwise | See [paradigm-conversion.md](paradigm-conversion.md) |
| How modifiers combine | Multiplicatively | See [composition-and-effects.md](composition-and-effects.md) |
| Results | A count for every state, a flow for every named transition | Starsim 3's automatic `n_<state>` results; [camdl](../approaches/camdl.md)'s `incidence(transition)` |
| Goodness of fit | Normalized absolute error against any data supplied | See [calibration.md](calibration.md); nobody should need a likelihood to fit a model |

Stop, because a guess would be wrong quietly:

- A rate expression whose dimensions do not check ([camdl](../approaches/camdl.md)'s missing-`/N` error).
- A stratified coverage that would deliver `1 − (1 − f)^P` instead of `f` (camdl E239).
- A mixing matrix on a partial stratification ([summer2](../approaches/summer2.md) enforces this and is right to).
- A misspelled state or parameter name.
- Typed values with different units in a model that also has bare numbers (which unit the bare numbers are in cannot be guessed).
- A keyword number on a disease that names no parameter.

Note what is *not* on that list: asking for a solver the model does not exactly fit. That gets the standard approximation and a one-line note, not an error; see principle 8 and [paradigm-conversion.md](paradigm-conversion.md).

And in every case, **describe the resolved model**. `sim.describe()` shows the states, the transitions with their dwell-time distributions, the networks, the solver, and the defaults that were filled in. A guess the user can see is not hidden behavior; a guess they cannot see is. (`sim.summarize()` and `sim.plot()` keep their Starsim meanings: they are about results.)

## Plain Python is part of the language

The first draft of this folder treated arbitrary Python as a last resort. That was a mistake. Real transitions are often complicated (a probability of death that depends on age, sex, comorbidity, and time since treatment), and real interactions between modules more so ("find people who are HIV positive, filter by an age- and sex-dependent probability, and schedule an HIV test at their next antenatal visit"). No fixed vocabulary covers these.

So wherever a number can go, a function can go, and any module can have a `step()` method that does whatever it needs. The declared forms let the library do more (draw the diagram, write the equations, run as an ODE, stratify). A function gives up only what it actually prevents: one that works on group totals runs in a compartmental model; one that reaches for individual agents needs agents. The library finds out by trying it, and says so when it does not work.

## Error messages are part of the language

camdl's E237/E238/E239 hold hard-won knowledge about stratified coverage and deliver it exactly when the mistake is made. This matters here too, because many models will be written by an AI that may otherwise give a wrong answer confidently.

The requirement: **every error names what is wrong in the user's own terms, says what exists where that helps (the declared states, the parameters), and states the fix.** Not `ValueError: shape mismatch`. Most errors are ordinary Python ones (a `KeyError`, a `TypeError`) with such a message, and a few that code catches by kind are classes (`ss.CapabilityError`); see [15-errors.md](../design/15-errors.md).

## AI-native means four concrete things

The [approaches README](../approaches/README.md) frames this project as AI-native. In practice, from the frameworks that tried:

1. **Documentation shipped with the version, offline and doc-tested**: camdl's `camdl docs <topic>` and `AGENTS.md`. An agent that reads stale docs writes broken models.
2. **A machine-drivable contract**: [Epydemix](../approaches/epydemix.md) ships a CLI with a documented `AGENT.md` rather than exposing its Python API; camdl does the same. Worth noting that both chose a CLI over an API.
3. **The model is data, so the model can be checked.** Everything in [model-structure.md](model-structure.md) follows from this.
4. **A standard printed form.** If two agents are given the same description, it should be easy to see whether they wrote the same model.

Where Starsim stands on each: (1) the docs are built with each version, with a generated API index for agents (`llms.txt`), and the skills in `starsim_ai` (`import-model`, `validate-import`, `migrate-starsim3`) are shipped with the code; (2) the Python API is the contract, along with a small `starsim` command line (`init`, `compile`); (3) is the declared model; (4) is `describe()`, which prints a model in one form. An earlier normalized model spec (`sim.to_spec()`, `sim.hash()`, `ss.diff()`, `sim.to_code()`) was removed on 2026-10-27: a model is its code ([14-model-spec.md](../design/14-model-spec.md)).

## What we are deliberately not building

Each of these is good work in its own setting. For this project, each would cost more than it returns.

| Rejected | Where it comes from | Why not |
|---|---|---|
| A standalone DSL | [camdl](../approaches/camdl.md), [odin](../approaches/odin.md) | Both are excellent and both cost a toolchain. Python is the constraint, and the type system that makes camdl work is expressible in Python objects. |
| YAML or JSON as the authoring surface | [EMULSION](../approaches/emulsion.md), [EMOD](../approaches/emod.md), [EpiHiper](../approaches/epihiper.md), [flepiMoP](../approaches/flepimop.md) | These formats are easy to generate and to read by machine. The tradeoff is that expressions end up in strings, nothing is type-checked, and errors come from a parser that knows nothing about epidemiology. A data format suits export better than writing by hand, as [SBML](../approaches/notes.md#sbml-systems-biology-markup-language)'s history suggests. |
| Spreadsheet authoring | [Atomica](../approaches/atomica.md) Atomica's workbooks are the most accessible option in the review. The tradeoff is binary files that cannot be compared line by line, and formula cells that can break silently. A table view of a model is worth having: see [model-structure.md](model-structure.md). |
| Refusing to run a model in a paradigm it does not exactly fit | [camdl](../approaches/camdl.md)'s capability checks | Right for camdl's users, who want guarantees. Epidemiologists also routinely and validly write ODE models of sexually transmitted infections, so here the library approximates and says so. |
| Order-independent execution through queued updates | [`individual`](../approaches/individual.md) | Elegant, but a defined module order is easier to reason about and lets infection, testing, and treatment happen in one step. Starsim's ordered, inspectable loop stays. |
| A closed list of things one module may modify in another | [epiworld](../approaches/epiworld.md)'s tools, [EpiHiper](../approaches/epihiper.md)'s state properties | Easier to analyze, but real multi-disease models need more. Any named quantity can be modified; anything more complex is a `step()` method. |
| A predicate mini-language with its own built-in names | [EMOD](../approaches/emod.md)'s `Targeting_Config`, Polars-style column objects | Eligibility is written against the model's real attributes (`people.age`, `sir.vaccinated`), so custom attributes work exactly like built-in ones. |
| Mandatory ontology identifiers on states | [MIRA](../approaches/notes.md#askem-model-representation-amr--mira) | `identifiers={"ido": "0000511"}` on every compartment is valuable for automated model merging, and extra work for every user who is not merging models. Never required. |
| Symbolic fixed-point and eigenvalue analysis | [epipack](../approaches/epipack.md) | Excellent for textbook models, and intractable for large stratified ones. Printing the equations is worth having; the rest is not a v1 feature. |
| A ladder of analytic network approximations | [EoN](../approaches/eon.md) | A decade of fine mathematics for SIS and SIR on networks, more than one library can maintain. Anyone who needs an exact network result can run agents, which is one keyword away. |
| `Overwrite` adjustments | [summer2](../approaches/summer2.md) | Multiplicative adjustments compose; overwrites do not, and their result depends on stratification order. |
| Additive composition as the default | [`epidemics`](../approaches/epidemics.md) | Chosen there for legibility and documented openly, but two 60% reductions summing to 120% has to be clamped somewhere. Multiplicative by default, additive on request. |
| Positional or integer references | [epiworld](../approaches/epiworld.md)'s `target_states = 2L`, [EpiModel](../approaches/epimodel.md)'s derivative-vector ordering | A wrong index is a silently different model. Names, always, checked. |
| Optimal control in v1 | [PyRoss](../approaches/notes.md#pyross), [Atomica](../approaches/atomica.md) | The right long-term capability and not a v1 vocabulary. The obligation is only to *not foreclose* it: interventions with declared costs make it possible later. (Reallocating a fixed budget between programs, as Atomica does, was built for its program books: `ss.fit.optimize()`.) |
| A separate specification for each paradigm | [MEmilio](../approaches/memilio.md)'s twenty-plus model families, [EpiModel](../approaches/epimodel.md)'s three parallel APIs | This gives each paradigm full attention, at the cost of writing everything several times. One model text is the aim here. See [paradigm-conversion.md](paradigm-conversion.md). |

## Trade-offs we are accepting

- **Checks happen when the sim is built, not earlier.** camdl catches a dimensional error before anything runs; here it is caught at `sim.init()`, which is later than a compiled language can manage.
- **The declared forms cover the common structure, not everything.** [summer2](../approaches/summer2.md) accepts the same limit and it is why its stratification operator works at all. Whatever falls outside is written as a function, and the library reports what it can no longer do with that part.
- **Guessing defaults means people need to look at the described model.** If they do not, some guesses will go unnoticed. Mitigation: the description is short, it marks what was guessed, and the one-line notes about the solver and any approximation are printed on `run()`.
- **Approximating instead of refusing means two runs of "the same model" can differ for reasons the user did not think about.** Mitigation: `solver='auto'` never approximates the mixing (the one thing it will do unasked is represent a dwell time by sub-stages, and it says so), every approximation is named when it happens, and `approx=False` turns approximations into errors for anyone who wants that.

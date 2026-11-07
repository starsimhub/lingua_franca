---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# The model as code

There is no model spec (decided 2026-10-27, replacing the JSON spec with `sim.to_spec()`, `sim.hash()`, `ss.diff()`, and `sim.to_code()`). A model is its code: the script that builds the sim is the thing to read, share, version, and compare, and two models are compared by their results, by `describe()`, or by a text diff of their code. There is no code-to-code translator: Starsim never turns a sim back into code.

A declared model can also be written as JSON, Starsim's own format (decided 2026-11-03; [below](#the-json-form)). It is one more format among those of [16-interop.md](16-interop.md), not a second form of the model: it is written from the built model like the other exports, and read like the other imports, by writing the model's code and running it.

| What | How | Holds | Read back |
|---|---|---|---|
| The model | the user's script; for an import, the code the importer writes (`sim.imported.code`, [16-interop.md](16-interop.md)) | the model as Python | it is run |
| The model as JSON | `ss.export_to(sim, 'json')` | the declared model as plain data, in the words of its code ([below](#the-json-form)) | yes, with `ss.import_from('model.json')`, which writes the code (`sim.imported.code`) and runs it |
| The results as JSON | `sim.to_json()` | the sim's parameters (a module among them as a reference, its type and name), its summary, and its results, for reading elsewhere | no |
| A saved sim (a checkpoint) | `sim.save()`, `ss.save('run.sim', sim)` | the sim itself, as a pickle, with its results; saved partway through a run, with its full state, so that it can continue | yes, with `ss.load()`, by the same code |

An import is the one place code is written: each importer reads its format into an `ss.converters.Source`, `ss.converters.write()` writes that as a declared `ss.Disease` and its `ss.Sim`, and the imported sim is that code run, so there is one path (foreign model, then code, then sim). The exporters (SBML, odin) read the built model directly: each disease's graph (its states, transitions, parameters, and expressions) and engine ([16-interop.md](16-interop.md#export)). The record of what was run is the code, its commit or tag, and the Starsim version that a saved sim stores ([11-random.md](11-random.md#run-identity)).

## The JSON form

The JSON form is for moving a model between programs and people without Python: a file a tool can write or read, a model sent to a web app, a model in a database. It reads like the code. Each value and rate is written as it would be in Python without the `ss.` (`"days(10)"`, `"S >> I @ beta * I"`), never as a tree of operations, so a file is as easy to read as the code it stands for (camdl's IR, where `beta * S * I / N` is four nested `bin_op` objects, is the thing to avoid). A stratification is kept as the arguments of `stratify()`, not unrolled into a state per group, and what was left at its default is left out. The values written are those Starsim resolved (each parameter named, each unit explicit), since a reader must get the same model without Starsim's defaults to hand.

```json
{
  "starsim": "4.0.0",
  "total_pop": 2000,
  "unit": "day",
  "stop": 200,
  "diseases": [
    {
      "name": "sir",
      "pars": {
        "R0": {"value": {"by": {"patch": {"urban": 2.5, "rural": 1.8}}}, "bounds": [0.5, 10]},
        "gamma": {"value": 0.1, "bounds": [0.01, 1.0]}
      },
      "states": ["S", "I", "R"],
      "transitions": {"infection": "S >> I @ R0 * gamma * I", "recovery": "I >> R @ gamma"},
      "init_n": {"I": {"by": {"patch": {"urban": 10, "rural": 1}}}},
      "stratify": {"patch": ["urban", "rural"]}
    }
  ],
  "networks": [{"type": "RandomNet", "n_contacts": 5}]
}
```

- **The top level** has `"starsim"`, the version that wrote it (which also tells `ss.import_from()` the format), the sim's settings as they were given (`start`, `stop`, `dt`, `unit`, `total_pop`, `n_agents`, `solver`, `rand_seed`, ...), `"diseases"`, and the other modules (`"networks"`, `"demographics"`, `"interventions"`, `"analyzers"`, `"connectors"`).
- **A declared disease** has its `name`, `pars`, `states`, `transitions`, `results`, starting values (`init`, `init_n`, `init_prev`), `default_state`, and `stratify` (one dict of dimensions, as `stratify()` takes them).
- **A parameter** is its value, or `{"value": ..., "bounds": ..., "prior": ..., "doc": ...}` if it has more. A value is a JSON number, list, or object; a typed value, distribution, or other Starsim value as its code (`"days(10)"`, `"gamma(a=4, scale=days(2.5))"`, `"seasonal(mean=0.26, amplitude=0.3, peak='January')"`); and a value by group as `{"by": {"patch": {...}}}`, the arguments of `ss.by()`.
- **A state** is its name, or `{"name": ..., "people": false, "label": ...}`.
- **A transition** is one line, as the operators write it (`"I >> R @ dur_inf"`, `"unborn >> S @ birth_rate * N"`, `"[S, I, R] >> dead @ mu"`; the three places outside the model are `unborn`, `dead`, and `outside`), if it has only its ends and a rate or a dwell time with a unit; otherwise it is the arguments of `ss.Transition()` (`{"source": "I", "dest": ["P", "R"], "dur": "dur_inf", "p": ["p_paralysis", null]}`, read as `ss.Transition(I, {P: p_paralysis, R: None}, dur=dur_inf)`).
- **A result** is its expression; a result that a rate uses is written there by its name (`"y2 >> x1 @ R1"`), as the code would.
- **Another module** (a network, an intervention, a disease written as code) is its type and the parameters that differ from its defaults, as Starsim 3's dict input gave them: `{"type": "RandomNet", "n_contacts": 5}`, or `"ssl.HouseholdNet"` for one of the library's. A module of the user's own class cannot be written, and is listed.

Reading a file runs no code from it: each expression is parsed and checked, with only the model's own names, Starsim's typed values, distributions, and values, and NumPy's functions allowed, and a module's type must be one of Starsim's or its library's. An unknown name or a part that is not allowed is an error that says where it is.

What the form does not carry yet is listed as `LossyExport` like any other export's: outcomes, modifiers (`ss.modify()`), functions, attributes, strains, transfers, conditions (`who=`), changes of level (`move=`, `increment=`), the sim's own stratification, named populations and geographies (a stratification by places is written as their names), and modules of the user's own classes (`docs/admin/deferred.md`). The test is the round trip: a sim exported and imported again gives the same results, for each model in the library (`tests/devtests/io/test_io_json.py` in Starsim).

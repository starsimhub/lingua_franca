---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Environments

What each framework needs in order to run its models. The recipe is in `docs/models/<framework>`, shared by all of that framework's models: `env.cfg` says how to build it, `requirements.txt` lists the exact versions, and `README.md` gives the version used and what it needs. `sbml`, `epipack`, and `epymorph` have a recipe but no models.

What a recipe builds goes in `_envs/<framework>`, none of which is committed. A model finds its framework at `_envs/<framework>/bin`, which `docs/models/tools.py` puts at the front of the `PATH`.

## Installing

```bash
lingua_franca envs check                 # Compare what is installed with the recipes
lingua_franca envs install               # Build whichever are missing or incomplete
lingua_franca envs install odin siminf   # Or only some of them
lingua_franca envs key odin sbml         # A hash of their recipes, for caching what they build
python scripts/clean_envs.py             # Delete what was built
python scripts/clean_envs.py camdl       # Or only some of it
```


It needs Sciris, and whatever the frameworks being installed need (`uv`, R, or OCaml and Rust: see the `README.md` of each). It follows the steps in each `README.md`, and what a build prints goes to `build.log` in the folder. The Python environments are rebuilt from `requirements.txt`, so they get exactly the versions used. The R ones get CRAN as it was on the date in `src/lingua_franca/envs.py`, so to update them, change that date and `requirements.txt`.

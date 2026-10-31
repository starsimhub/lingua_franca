# Environments

What each framework needs in order to run its examples: one folder per framework, shared by all of that framework's examples.

Each folder has a `README.md` with the version used and how to build it. What the build produces (`src/`, `bin/`, logs) is not committed. An example finds its framework at `_envs/<framework>/bin`, which `examples/tools.py` puts at the front of the `PATH`.

## Installing

`envs.py` builds, checks, and removes the environments:

```bash
python _envs/envs.py check                 # Compare what is installed with the recipes
python _envs/envs.py install               # Build whichever are missing or incomplete
python _envs/envs.py install odin siminf   # Or only some of them
python _envs/envs.py uninstall camdl       # Delete what a build produced
python _envs/envs.py uninstall all
python _envs/envs.py key odin sbml         # A hash of their recipes, for caching what they build
```

It needs Sciris, and whatever the frameworks being installed need (`uv`, R, or OCaml and Rust: see the `README.md` of each). It follows the steps in each `README.md`, and what a build prints goes to `build.log` in the folder. The Python environments are rebuilt from `requirements.txt`, so they get exactly the versions used. The R ones get CRAN as it was on the date in `envs.py`, so to update them, change that date and `requirements.txt`. An uninstall deletes everything in the folder except `README.md` and `requirements.txt`.

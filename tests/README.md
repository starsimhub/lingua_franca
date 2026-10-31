# Tests

Tests of Starsim that need what is in this repo: other frameworks' original examples and results (`examples/`), the Starsim versions of them (`vignettes/`), and the frameworks themselves (`_envs/`). **Starsim runs `conversion/` and `switching/` as a downstream test** (`.github/workflows/test_downstream.yml` in the Starsim repo calls `frameworks.yml` here), so a change here can fail Starsim's CI. They run against whichever Starsim is installed.

| Folder | What it tests | How to run it |
|---|---|---|
| `conversion/` | `ss.import_from()` against other frameworks' examples and the frameworks themselves, and `ss.export_to()` against the tools it writes for | `lingua_franca test conversion` |
| `switching/` | One demo per framework, for its users, written in that field's terms; see its README | `lingua_franca test switching` |
| `threading/` | Whether BLAS threads help Starsim: a separate script for other machines; see its README | `lingua_franca test threading` |

`lingua_franca test all -n auto` runs all three (install it with `pip install -e .` from the top of this repo); anything after the suite goes to pytest, or to `run.py` for `threading` alone. `pytest conversion` from this folder also still works. Tests that need a framework are skipped until its environment is installed (`python _envs/envs.py install <framework>`; see `_envs/README.md`).

`.github/workflows/frameworks.yml` runs these in CI, with one job for each framework: it builds the environment, runs the framework's tests, and runs `lingua_franca benchmark` for its models, whose comparisons with the originals can fail the job (its times cannot). Environments and Starsim's Rust kernels are cached under a hash of their recipe or source, so only what has changed is rebuilt.

`paths.py` says where the top of this repo is, `timing.py` times the speed tests, as Starsim's `tests/timing.py` does but with a more lenient limit, and `conftest.py` lets the subfolders import both.

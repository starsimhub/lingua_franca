# flepiMoP

- **Version:** `gempyor` 2.1, from commit `ad62f2d0` of flepiMoP (27 June 2025, the head of `main` on 13 October 2026)
- **Source:** https://github.com/HopkinsIDD/flepiMoP (GPL-3.0); the Python package is in `flepimop/gempyor_pkg`
- **Commit:** `ad62f2d00082de5b60e62100be7b24fddc6931da`; no release tag could be used (see below)
- **Needs:** `uv`, which fetches Python 3.11 (`gempyor` needs Python 3.10 or 3.11), and `git`; no R, and nothing is compiled when it is installed

## Build

`lingua_franca envs install flepimop` rebuilds this environment from `requirements.txt`. The versions in it came from:

```bash
uv venv --python 3.11 .
rm .gitignore
git init src
git -C src fetch --depth 1 https://github.com/HopkinsIDD/flepiMoP ad62f2d00082de5b60e62100be7b24fddc6931da
git -C src checkout FETCH_HEAD
VIRTUAL_ENV=$PWD uv pip install ./src/flepimop/gempyor_pkg
VIRTUAL_ENV=$PWD uv pip freeze > requirements.txt
```

The install takes under a minute. `requirements.txt` records `gempyor` as a local path, so to get exactly the versions used, install the other lines of it and then `gempyor` from `src` as above (which is what `envs.py` does).

## Why a commit and not a release tag

The repository has three tags, `v1.0.0-alpha`, `v1.1`, and `v1.2`, the latest from November 2023. None of them has the `flepimop simulate` command (they have `gempyor-seir` and `gempyor-outcomes` instead), and none has `examples/tutorials/`: `main` is more than 3,000 commits ahead of `v1.1`. `gempyor` is not on PyPI. So the environment is pinned to a commit of `main`.

## Notes

- `gempyor` gives no upper bounds for what it depends on; the latest versions on 13 October 2026 (NumPy 2.4, pandas 3.0, Numba 0.68) worked without pins.
- The command is `flepimop simulate <config.yml>`, run from the folder that the paths in the configuration are relative to. It writes to `model_output/` there.
- Every run compiles the integrator with Numba, which takes about 7 seconds, and is not cached between runs.
- The R packages (`flepimop/R_packages`), used for inference and post-processing, are not installed.

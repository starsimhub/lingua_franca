# epydemix

- **Version:** 1.4.0, from PyPI
- **Source:** https://github.com/epistorm/epydemix (GPL-3.0)
- **Needs:** Python 3.12 and `uv`; a network connection when an example loads a population, since the data is downloaded from https://github.com/epistorm/epydemix-data (tag `v1.2.0`)

## Build

`lingua_franca envs install epydemix` rebuilds this environment from `requirements.txt`. The versions in it came from:

```bash
uv venv --python 3.12 .
VIRTUAL_ENV=$PWD uv pip install epydemix==1.4.0
VIRTUAL_ENV=$PWD uv pip freeze > requirements.txt
```

Run from `_envs/epydemix`. To rebuild with the same versions of everything, install from `requirements.txt` instead: `VIRTUAL_ENV=$PWD uv pip install -r requirements.txt`.

The optional `numba` extra (`epydemix[numba]`), which speeds up the stochastic solver, is not installed.

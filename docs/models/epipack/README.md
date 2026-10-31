# epipack

- **Version:** 0.1.5, from PyPI
- **Source:** https://github.com/benmaier/epipack (MIT)
- **Needs:** Python 3.12 and `uv`

## Build

`lingua_franca envs install epipack` rebuilds this environment from `requirements.txt`. The versions in it came from:

```bash
uv venv --python 3.12 .
VIRTUAL_ENV=$PWD uv pip install epipack==0.1.5
VIRTUAL_ENV=$PWD uv pip freeze > requirements.txt
```

Run from `_envs/epipack`. To rebuild with the same versions of everything, install from `requirements.txt` instead: `VIRTUAL_ENV=$PWD uv pip install -r requirements.txt`.

The optional `SamplableSet`, which speeds up the stochastic models, is not installed.

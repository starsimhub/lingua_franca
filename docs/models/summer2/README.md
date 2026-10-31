# summer2

- **Version:** 1.3.6 (the PyPI package `summerepi2`), with Python 3.11.11
- **Source:** https://github.com/monash-emu/summer2 (BSD 2-Clause)
- **Needs:** `uv`; everything else (JAX, NumPy, SciPy, pandas, Plotly) is installed as a dependency, on the CPU only

## Build

`lingua_franca envs install summer2` rebuilds this environment from `requirements.txt`. The versions in it came from:

```bash
uv venv --python 3.11 .
VIRTUAL_ENV=$PWD uv pip install summerepi2==1.3.6
VIRTUAL_ENV=$PWD uv pip freeze > requirements.txt
```

The exact versions are in `requirements.txt`; to rebuild from it, replace the second line with `VIRTUAL_ENV=$PWD uv pip install -r requirements.txt`. On a machine with an NVIDIA GPU, JAX warns that it is falling back to the CPU, which is harmless.

# LASER

- **Version:** `laser-generic` 1.1.0 with `laser-core` 1.0.5, from PyPI
- **Source:** https://github.com/InstituteforDiseaseModeling/laser-generic and https://github.com/InstituteforDiseaseModeling/laser (both MIT)
- **Needs:** Python 3.12 and `uv`; no compiler (the model code is compiled by Numba when it first runs, which takes a few seconds)

## Build

`lingua_franca envs install laser` rebuilds this environment from `requirements.txt`. The versions in it came from:

```bash
uv venv --python 3.12 .
VIRTUAL_ENV=$PWD uv pip install laser-generic==1.1.0 laser-core==1.0.5
VIRTUAL_ENV=$PWD uv pip freeze > requirements.txt
```

To rebuild with exactly the same versions of everything, install from `requirements.txt` instead: `VIRTUAL_ENV=$PWD uv pip install -r requirements.txt`.

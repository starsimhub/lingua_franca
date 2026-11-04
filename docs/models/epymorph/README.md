# epymorph

- **Version:** 1.2.0, from PyPI
- **Source:** https://github.com/NAU-CCL/Epymorph (GPL-3.0)
- **Needs:** Python 3.12 and `uv`; a network connection when a model's data comes from an ADRIO (the models here keep the data their ADRIOs fetch, so they run offline)

## Build

`lingua_franca envs install epymorph` rebuilds this environment from `requirements.txt`. The versions in it came from:

```bash
uv venv --python 3.12 .
VIRTUAL_ENV=$PWD uv pip install epymorph==1.2.0
VIRTUAL_ENV=$PWD uv pip freeze > requirements.txt
```

Run from `_envs/epymorph`. To rebuild with the same versions of everything, install from `requirements.txt` instead: `VIRTUAL_ENV=$PWD uv pip install -r requirements.txt`.

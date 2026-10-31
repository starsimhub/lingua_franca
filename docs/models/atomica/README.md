# Atomica

- **Version:** 1.32.4 (1 September 2026), from PyPI
- **Source:** https://github.com/atomicateam/atomica (MIT)
- **Needs:** Python 3.11 or later (3.12 is used here) and `uv`; everything else is installed from PyPI (NumPy, SciPy, pandas, Matplotlib, openpyxl, XlsxWriter, Sciris, and others)

## Build

`lingua_franca envs install atomica` rebuilds this environment from `requirements.txt`. The versions in it came from:

```bash
uv venv --python 3.12 _envs/atomica
VIRTUAL_ENV=_envs/atomica uv pip install atomica==1.32.4
VIRTUAL_ENV=_envs/atomica uv pip freeze > _envs/atomica/requirements.txt
```

Run these from the top of the repository. `requirements.txt` has the exact version of every package, so `uv pip install -r _envs/atomica/requirements.txt` rebuilds the same environment. The demo spreadsheets are in the package, at `lib/python3.12/site-packages/atomica/library/`.

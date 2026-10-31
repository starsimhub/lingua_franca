# SBML

Tools that read SBML, for checking what `ss.export_to(sim, 'sbml')` writes (`tests/conversion/`). There are no examples for this environment.

- **Versions:** `python-libsbml` 5.21.2 (the reference validator), `libroadrunner` 2.11.0, and `copasi-basico` 0.92 with `python-copasi` 4.48.311 (two separate simulators), on Python 3.12
- **Source:** https://sbml.org/software/libsbml, https://libroadrunner.org, https://copasi.org
- **Needs:** `uv`; the wheels include everything else

`requirements.txt` lists the exact versions.

## Build

`python _envs/envs.py install sbml` does this:

```bash
uv venv --python 3.12 --allow-existing .
uv pip install -r requirements.txt
```

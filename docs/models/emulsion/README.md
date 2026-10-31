# EMULSION

- **Version:** 1.1.1 (PyPI, released 19 October 2020)
- **Source:** https://pypi.org/project/emulsion/1.1.1/ (Apache-2.0); the project site, https://sourcesup.renater.fr/emulsion-public/, and its repository, https://git.renater.fr/emulsion-public.git, could not be reached on 13 October 2026
- **Needs:** `uv`, which fetches Python 3.9

## Build

`lingua_franca envs install emulsion` rebuilds this environment from `requirements.txt`. The versions in it came from:

```bash
uv venv --python 3.9 .
VIRTUAL_ENV=$PWD uv pip install emulsion==1.1.1 'bokeh<3' 'numpy<2'
VIRTUAL_ENV=$PWD uv pip freeze > requirements.txt
```

Or, for exactly the versions used: `VIRTUAL_ENV=$PWD uv pip install -r requirements.txt`.

## Pins

EMULSION gives only lower bounds for most of what it depends on, and the latest versions no longer work with it:

- `bokeh<3` (2.4.3 here): EMULSION imports `bokeh.layouts.widgetbox`, which was removed in Bokeh 3.0, and it does so when the `emulsion` command starts, whether or not anything is plotted
- `numpy<2` (1.26.4 here): Bokeh 2.4.3 uses `numpy.bool8`, which was removed in NumPy 2.0
- `sympy==1.1.1`: pinned by EMULSION itself; on Python 3.9 it prints a `SyntaxWarning` at startup, which is harmless

Nothing else needed pinning, and Python 3.9 works.

## Notes

- The wheel has no models. The example models (`models/features/` and `models/quickstart/`) are only in the source distribution, `emulsion-1.1.1.tar.gz`.
- `bin/init_emulsion` is not needed and was not run: it appends shell completion and a `PYTHONPATH` line to `~/.bashrc`.
- Diagrams (`emulsion diagrams`, `--view-model`) need Graphviz, which the examples do not use.

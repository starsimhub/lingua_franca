# MEmilio

- **Version:** 2.4.1 (the `memilio-simulation` wheel from PyPI, for Python 3.11 on Linux x86-64)
- **Source:** https://github.com/SciCompMod/memilio (Apache-2.0); the Python bindings are in `pycode/memilio-simulation`
- **Commit:** tag `v2.4.1` (`c2c884ce`)
- **Needs:** `uv`, which fetches Python 3.11; nothing is compiled, because PyPI has wheels for Linux, macOS (arm64), and Windows, for Python 3.8 to 3.13

## Build

`lingua_franca envs install memilio` rebuilds this environment from `requirements.txt`. The versions in it came from:

```bash
uv venv --python 3.11 .
rm .gitignore
VIRTUAL_ENV=$PWD uv pip install memilio-simulation==2.4.1 matplotlib
VIRTUAL_ENV=$PWD uv pip freeze > requirements.txt
git init src
git -C src fetch --depth 1 https://github.com/SciCompMod/memilio c2c884ce430f248414099bfb901a5045c0295c26
git -C src checkout FETCH_HEAD
```

Or, for exactly the versions used: `VIRTUAL_ENV=$PWD uv pip install -r requirements.txt`.

## Notes

- `matplotlib` is not a dependency of the wheel, but MEmilio's own Python examples import it and save a plot.
- `src` is only there for the examples (`src/pycode/examples/simulation/`), the license, and the C++ that defines the models (`src/cpp/models/`); it is not built.
- Without a wheel, `pip install src/pycode/memilio-simulation` builds the C++ library and its bindings with scikit-build and CMake. That was not needed, and was not tried.

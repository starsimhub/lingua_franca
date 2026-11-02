# Pandemic Simulator

- **Version:** 0.1.0, from GitHub at commit `5ec712b`; it is not on PyPI
- **Source:** https://github.com/WHO-Collaboratory/pandemic-simulator-compartment (Apache 2.0)
- **Needs:** Python 3.13 and `uv`

## Build

`lingua_franca envs install pandemic_simulator` rebuilds this environment from `requirements.txt`. It fetches the commit into `src` and installs it from there. The versions are those of the framework's `uv.lock`, from `uv sync --frozen --no-dev`.

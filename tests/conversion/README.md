# Conversion tests

Tests of converting models, against the other frameworks rather than only Starsim. `test_<framework>.py` imports each framework's examples and compares them with its results, or with the framework itself. `test_optima_tb.py` runs the structure of a large model, with no data. `test_export.py` gives the files from `ss.export_to()` to odin, libSBML, libRoadRunner, and COPASI, and compares their trajectories with Starsim's. Starsim keeps the tests of the same importers that need nothing from this repo (in its `tests/devtests/io/`).

```bash
lingua_franca envs install odin sbml   # From the top of this repo
cd tests/conversion && pytest test_export.py
```

The tests are skipped if an environment is missing. They use the Starsim that is installed.

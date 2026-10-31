# Conversion tests

Tests that what Starsim converts is read by the other tools themselves, rather than only by Starsim. `test_export.py` gives the files from `ss.export_to()` to odin, libSBML, libRoadRunner, and COPASI, and compares their trajectories with Starsim's.

```bash
python _envs/envs.py install odin sbml   # From the top of this repo
cd tests/conversion && pytest test_export.py
```

The tests are skipped if an environment is missing. They use the Starsim that is installed.

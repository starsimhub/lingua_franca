"""
Read an SBML file with the SBML tools themselves, for `test_export.py`. Run with the Python of `_envs/sbml`, as:

    python run_sbml.py model.xml stop out_prefix

Prints a JSON list of what libSBML found wrong (errors only, not advice), and writes each tool's
trajectory, with a row for each whole unit of time from 0 to `stop`, as `<out_prefix>_<tool>.csv`.
"""
import sys
import json
import libsbml
import basico
import roadrunner
import numpy as np
import pandas as pd

tol = 1e-10


def validate(file):
    """ What libSBML finds wrong with a file, at the severity of an error """
    doc = libsbml.readSBML(file)
    doc.checkConsistency()
    errors = [doc.getError(i) for i in range(doc.getNumErrors())]
    return [f'{e.getErrorId()}: {e.getShortMessage()}: {e.getMessage().strip()}' for e in errors if e.getSeverity() >= libsbml.LIBSBML_SEV_ERROR]


def run_roadrunner(file, stop):
    """ A trajectory from libRoadRunner, which compiles the file with LLVM """
    rr = roadrunner.RoadRunner(file)
    rr.integrator.relative_tolerance = tol
    rr.integrator.absolute_tolerance = tol
    species = list(rr.model.getFloatingSpeciesIds())
    out = rr.simulate(0, stop, stop+1, selections=['time'] + species)
    return pd.DataFrame(np.array(out)[:,1:], columns=species)


def run_copasi(file, stop):
    """ A trajectory from COPASI, a separate implementation of SBML """
    basico.load_model(file)
    basico.set_task_settings('Time-Course', {'method':{'Relative Tolerance':tol, 'Absolute Tolerance':tol, 'Max Internal Steps':1_000_000}})
    out = basico.run_time_course(start_time=0, duration=stop, intervals=stop, use_number=True)
    return out.reset_index(drop=True)


if __name__ == '__main__':
    file, stop, prefix = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    errors = validate(file)
    print(json.dumps(errors))
    if not errors:
        run_roadrunner(file, stop).to_csv(f'{prefix}_roadrunner.csv', index=False)
        run_copasi(file, stop).to_csv(f'{prefix}_copasi.csv', index=False)

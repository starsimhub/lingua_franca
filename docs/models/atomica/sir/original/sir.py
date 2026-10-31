"""
Run Atomica's SIR demo from its two spreadsheets: what `at.demo('sir', addprogs=False)` does.
"""
import os
import atomica as at

here = os.path.dirname(os.path.abspath(__file__))


def load():
    """ Read the model structure (the framework) and its data (the databook) """
    P = at.Project(framework=os.path.join(here, 'sir_framework.xlsx'), databook=os.path.join(here, 'sir_databook.xlsx'), do_run=False)
    P.settings.sim_dt = 1.0 # In years; the demo sets this, and Atomica's own default is 0.25
    return P


if __name__ == '__main__':
    P = load()
    result = P.run_sim()
    print(result.export_raw())

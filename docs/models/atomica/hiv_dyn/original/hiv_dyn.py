"""
Run Atomica's dynamic HIV demo from its three spreadsheets: what `at.demo('hiv_dyn')` does, then its budget scenarios.
"""
import os
import atomica as at

here = os.path.dirname(os.path.abspath(__file__))


def load():
    """ Read the model structure (the framework), its data (the databook), and its programs (the progbook), and add the demo's three budget scenarios """
    P = at.Project(framework=os.path.join(here, 'hiv_dyn_framework.xlsx'), databook=os.path.join(here, 'hiv_dyn_databook.xlsx'), do_run=False)
    P.settings.sim_dt = 1.0 # In years; the demo sets this, and Atomica's own default is 0.25
    P.load_progbook(os.path.join(here, 'hiv_dyn_progbook.xlsx'))
    at.make_demo_scenarios(P) # Default, doubled, and zero budget, from the last year of data (see demos.py)
    return P


if __name__ == '__main__':
    P = load()
    baseline = P.run_sim() # Without programs
    scenarios = P.run_scenarios()
    for result in [baseline] + scenarios:
        print(result.name, {pop.name: round(pop.get_variable('all_people')[0].vals[-1]) for pop in result.model.pops})

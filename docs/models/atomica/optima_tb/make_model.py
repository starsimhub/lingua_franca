"""
Write `model.py`: the structure of the Optima TB model, as Starsim code, with no data and no real values

    FRAMEWORK=framework.xlsx DATABOOK=databook.xlsx python make_model.py

Imports the private workbooks as Starsim code, without their calibration, and rewrites that code:

- Every parameter becomes a default set by its format, so no value from the workbooks is kept
- The people in the model, their share in each population, and the share in each state at the start, become defaults
- All comments are dropped; states, transitions, formulas, and their labels are the structure, and are kept

`tests/conversion/test_optima_tb.py` checks the result.
"""
import os
import ast
import warnings
import openpyxl
import sciris as sc
import starsim as ss

here = sc.thispath(__file__)
framework, databook = sc.path(os.environ['FRAMEWORK']), sc.path(os.environ['DATABOOK'])
placeholders = dict(number=0.0, duration=1.0) # By the start of a parameter's format; any other is below
default = 0.01
total_pop = 1e6
share = 0.1 # Of the people, across the states given a start; the rest are in the first state


def formats():
    """ Each parameter's format, from the framework """
    ws = openpyxl.load_workbook(framework, read_only=True, data_only=True)['parameters']
    rows = ws.iter_rows(values_only=True)
    header = list(next(rows))
    name, fmt = [header.index(key) for key in ['code name', 'format']]
    return {row[name]:str(row[fmt]).lower() for row in rows if row[name]}


def placeholder(fmt):
    return next((val for key,val in placeholders.items() if fmt.startswith(key)), default)


def rewrite(code):
    info = formats()
    tree = ast.parse(code)
    lines = []
    for node in tree.body:
        if isinstance(node, ast.If): # The __main__ block
            continue
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = ast.unparse(node.value.func)
            name = node.targets[0].id
            if func == 'ss.par':
                node.value.args = [ast.Constant(placeholder(info.get(name, '')))]
            elif func == 'ss.Disease':
                for kw in node.value.keywords:
                    if kw.arg == 'init': # dict(state=ss.by(population=[...]), ...): the same in each state and population
                        n_cells = sum(len(state.value.keywords[0].value.elts) for state in kw.value.keywords)
                        for state in kw.value.keywords:
                            values = state.value.keywords[0].value
                            values.elts = [ast.Constant(share/n_cells) for _ in values.elts]
                    elif kw.arg == 'name':
                        kw.value = ast.Constant('optima_tb')
            elif func == 'ss.Sim':
                for kw in node.value.keywords:
                    if kw.arg == 'total_pop':
                        kw.value = ast.Constant(total_pop)
        for call in ast.walk(node): # The share of people in each population
            for kw in getattr(call, 'keywords', []):
                if kw.arg == 'split':
                    kw.value.elts = [ast.Constant(1/len(kw.value.elts)) for _ in kw.value.elts]
        lines.append(ast.unparse(node))
    return '"""\nThe structure of the Optima TB model, imported from Atomica, with default values and no data: see make_model.py\n"""\n' + '\n'.join(lines) + '\n'


if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        sim = ss.import_from(framework, format='atomica', databook=databook, start=2000, stop=2051, dt=1/12, verbose=False)
    sc.savetext(here/'model.py', rewrite(sim.imported.code))

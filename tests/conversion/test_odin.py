"""
Test importing odin models against odin itself and its examples' results
"""
import sys
import subprocess
import pytest
import numpy as np
import pandas as pd
import sciris as sc
import starsim as ss
import paths
from starsim.converters.odin import load_odin

lf = paths.root
kw = dict(verbose=False)
# The same as an ODE, run by odin itself with a contact matrix that is not symmetric
odin_age_ode = '''
n_age <- 3
beta <- user(0.02)
S0[] <- user()
I0[] <- user()
m[, ] <- user()
N[] <- S[i] + I[i] + R[i]
s_ij[, ] <- m[i, j] * I[j] / N[j]
lambda[] <- beta * sum(s_ij[i, ])
deriv(S[]) <- -lambda[i] * S[i]
deriv(I[]) <- lambda[i] * S[i] - 0.1 * I[i]
deriv(R[]) <- 0.1 * I[i]
initial(S[]) <- S0[i]
initial(I[]) <- I0[i]
initial(R[]) <- 0
dim(S0) <- n_age
dim(I0) <- n_age
dim(m) <- c(n_age, n_age)
dim(N) <- n_age
dim(s_ij) <- c(n_age, n_age)
dim(lambda) <- n_age
dim(S) <- n_age
dim(I) <- n_age
dim(R) <- n_age
'''
odin_run = '''
options(odin.verbose = FALSE)
args <- commandArgs(TRUE)
mod <- odin::odin_(args[1])$new(S0 = c(29990, 50000, 20000), I0 = c(10, 0, 0), m = matrix(c(10, 1, 4, 2, 6, 1, 1, 3, 2), 3, 3, byrow = TRUE))
write.csv(mod$run(0:200), args[2], row.names = FALSE)
'''
rscript = lf / '_envs/odin/bin/Rscript' # odin's environment


@pytest.mark.skipif(not rscript.exists(), reason='needs the odin environment')
def test_odin_contacts(tmp_path):
    sc.heading('Testing an odin model with a contact matrix against odin itself')
    model, script, out = tmp_path/'age_ode.R', tmp_path/'run.R', tmp_path/'out.csv'
    model.write_text(odin_age_ode)
    script.write_text(odin_run)
    subprocess.run([str(rscript), str(script), str(model), str(out)], check=True, cwd=tmp_path, capture_output=True)
    ref = pd.read_csv(out)
    sim = load_odin(model, stop=200, pars=dict(S0=[29_990, 50_000, 20_000], I0=[10, 0, 0], m=[[10, 1, 4], [2, 6, 1], [1, 3, 2]]), **kw)
    assert not sim.imported.incomplete
    res = sim.run().results.age_ode
    for k in range(3): # The matrix is not symmetric, so a transposed matrix would not agree
        diff = np.abs(res.R.select(age=str(k+1)).values - ref[f'R[{k+1}]'].values).max()
        assert diff < 1, f'Expected R in group {k+1} within 1 person of odin, not {diff:.2f}' # About 0.07 (the two ODE solvers)
    return sim


def test_odin_examples():
    sc.heading('Testing the odin examples against the originals')
    sys.path.insert(0, str(lf / 'docs' / 'models'))
    import tools

    # odin's replicates: 100 alike, independent copies are one model run many times
    ex = lf / 'docs' / 'models' / 'odin' / 'stochastic_sir_arrays'
    sim = load_odin(ex / 'original' / 'discrete_stochastic_sir_arrays.R', stop=100, **kw)
    assert 'n_runs=100' in sc.strjoin(sim.imported.choices)
    res = ss.parallel(sim.new(verbose=0), n_runs=500).results[sim.pars.diseases[0].name]
    ref = tools.read_results(ex)
    for state in 'SIR':
        vals = res[state].values
        diff = np.abs(vals.mean(axis=0) - np.array(ref[state][1])).max()
        tol = 4*vals.std(axis=0).max()/np.sqrt(len(vals)) # Four standard errors of the mean (many runs die out, so it is wide)
        assert diff < tol, f'Expected the mean of {state} within {tol:.1f} people of the original, not {diff:.1f}'

    # Ages from flows between levels, and a delay as a fixed dwell time; the delay's history is listed
    ex = lf / 'docs' / 'models' / 'odin' / 'seir_array'
    sim = load_odin(ex / 'original' / 'seir_array_odin.R', stop=365, **kw)
    assert '.stratify(age={0: ' in sim.imported.code and ', 30: ' in sim.imported.code # The age groups and their shares
    assert [name for name,why in sim.imported.incomplete] == ['lag_inf (history)']
    code = sim.imported.code.replace('    init', f'    history = ss.unborn >> I @ ss.timeseries({{0: ss.perday({np.exp(-14/(365*50))}), 14: 0}}),\n    init', 1)
    ns = {}
    exec(code, ns) # With the workaround that the import lists
    res = ns['sim'].run().results[ns['sim'].diseases[0].name]
    ref = tools.read_results(ex)
    for state in 'SEIR':
        theirs = np.array(ref[state][1])
        diff = np.abs(res[state].values - theirs).max()/theirs.max()
        assert diff < 0.1, f'Expected {state} within 10% of the original, not {diff:.1%}'
    return sim

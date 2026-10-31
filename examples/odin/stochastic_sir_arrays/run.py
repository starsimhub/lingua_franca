"""
Run the original odin model and write its reference results and timing.

    python run.py

Needs the odin environment (see `_envs/odin`).
"""
import os
import csv
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

model = os.path.join(here, 'original', 'discrete_stochastic_sir_arrays.R')
states = ['S', 'I', 'R']
n_groups = 100 # The length of the arrays (`nsim`, left at its default)
n_runs = tools.runs(200, fewest=100) # The model is stochastic
seed = 1 # As in the vignette

# The lines that compile and run the model are those of odin's "discrete" vignette (`odin::odin(path)`,
# `$new()`, `set.seed(1)`, `$run(0:100)`); the rest times them, repeats the run, and writes one row per
# run and time, with one column per variable and group (`S[1]` to `R[100]`)
driver = r'''
args <- commandArgs(TRUE)
n_runs <- as.integer(args[2])
options(odin.verbose = FALSE)
loadNamespace("odin") # Not counted
now <- function() as.numeric(Sys.time()) # In finer steps than system.time(), for a run of 2 ms
path_sir_model_s_a <- args[1]
start <- now()
sir_s_a_generator <- odin::odin(path_sir_model_s_a)
x <- sir_s_a_generator$new()
seconds_compile <- now() - start
set.seed(as.integer(args[4]))
out <- NULL
seconds <- numeric(0)
for (i in seq_len(n_runs)) {
    start <- now()
    x_res <- x$run(0:100)
    seconds <- c(seconds, now() - start)
    out <- rbind(out, cbind(run = i, x_res))
}
write.csv(out, args[3], row.names = FALSE)
cat(sprintf("FIRST %.6f\nRERUN %.6f\n", seconds_compile + seconds[1], min(seconds[-1])))
'''


def simulate(runs):
    """ Compile the model and run it a number of times, returning one row per run and time, and what was printed """
    with tempfile.TemporaryDirectory() as tmp:
        script, out = os.path.join(tmp, 'driver.R'), os.path.join(tmp, 'out.csv')
        with open(script, 'w') as f:
            f.write(driver)
        printed = tools.run(['Rscript', script, model, str(runs), out, str(seed)], 'odin', cwd=tmp)
        with open(out) as f:
            rows = [{key:float(val) for key,val in row.items()} for row in csv.DictReader(f)]
    return rows, printed


def summarize(samples):
    """ The mean and the 5% and 95% quantiles of the samples at each time, from `{time: [values]}` """
    out = []
    for t in sorted(samples):
        vals = sorted(samples[t])
        n = len(vals)
        out.append(dict(time=t, value=sum(vals)/n, low=vals[int(0.05*(n - 1))], high=vals[int(0.95*(n - 1))]))
    return out


if __name__ == '__main__':
    runs, printed = simulate(n_runs)
    assert len({row['run'] for row in runs}) == n_runs
    found = dict(line.split() for line in printed.splitlines() if line.split(' ')[0] in ['FIRST', 'RERUN'])

    rows = []
    for key in states:
        cols = [f'{key}[{i}]' for i in range(1, n_groups + 1)]

        # One group: the groups are independent and alike, so every group of every run is a sample
        group = dict()
        for row in runs:
            group.setdefault(row['step'], []).extend(row[col] for col in cols)
        rows += [dict(series=key, **row) for row in summarize(group)]

        # The total over the groups: one sample per run
        total = dict()
        for row in runs:
            total.setdefault(row['step'], []).append(sum(row[col] for col in cols))
        rows += [dict(series=f'{key}_total', **row) for row in summarize(total)]

        # Three of the groups on their own: one sample per run
        for i in [1, 2, n_groups]:
            one = dict()
            for row in runs:
                one.setdefault(row['step'], []).append(row[f'{key}[{i}]'])
            rows += [dict(series=f'{key}_{i}', **row) for row in summarize(one)]

    tools.write_results(here, rows)
    first, rerun = float(found['FIRST']), float(found['RERUN'])
    tools.write_timing(here, rerun, f'first is generating and compiling the C code with odin::odin, $new(), and one run of 100 groups for 100 steps, not counting starting R or loading odin; rerun is the best of {n_runs - 1} more calls of `x$run(0:100)` on the same model', first=first)
    print(f'Wrote {len(rows)} rows; first run {first:.3f} s, rerun {1000*rerun:.2f} ms')

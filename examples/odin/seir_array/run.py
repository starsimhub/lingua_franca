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

model = os.path.join(here, 'original', 'seir_array_odin.R')
states = ['S', 'E', 'I', 'R']
ages = ['0-1', '1-5', '5-15', '15-30', '30+']
stop = 365 # Days, as in the deSolve version the odin tests compare it with (`t = c(0, 365)`)

# The lines that compile and run the model are those of odin's tests (`odin::odin(path)`, `$new()`, `$run(t)`);
# the rest times them and writes one row per day, with one column per variable and age group (`S[1]` to `R[5]`)
driver = r'''
args <- commandArgs(TRUE)
options(odin.verbose = FALSE)
loadNamespace("odin") # Not counted
now <- function() as.numeric(Sys.time()) # In finer steps than system.time(), for a run of 2 ms
path <- args[1]
t <- 0:as.integer(args[3])
start <- now()
gen <- odin::odin(path)
mod <- gen$new()
y <- mod$run(t)
first <- now() - start
seconds <- numeric(0)
for (i in 1:5) {
    start <- now()
    mod$run(t)
    seconds <- c(seconds, now() - start)
}
write.csv(y, args[2], row.names = FALSE)
cat(sprintf("FIRST %.6f\nRERUN %.6f\n", first, min(seconds)))
'''


def simulate():
    """ Compile the model and run it, returning one row per day, and what was printed """
    with tempfile.TemporaryDirectory() as tmp:
        script, out = os.path.join(tmp, 'driver.R'), os.path.join(tmp, 'out.csv')
        with open(script, 'w') as f:
            f.write(driver)
        printed = tools.run(['Rscript', script, model, out, str(stop)], 'odin', cwd=tmp)
        with open(out) as f:
            rows = [{key:float(val) for key,val in row.items()} for row in csv.DictReader(f)]
    return rows, printed


if __name__ == '__main__':
    out, printed = simulate()
    found = dict(line.split() for line in printed.splitlines() if line.split(' ')[0] in ['FIRST', 'RERUN'])

    rows = []
    for key in states:
        for i,age in enumerate(ages):
            rows += [dict(time=row['t'], series=f'{key}_{age}', value=row[f'{key}[{i+1}]']) for row in out]
        rows += [dict(time=row['t'], series=key, value=sum(row[f'{key}[{i+1}]'] for i in range(len(ages)))) for row in out]

    tools.write_results(here, rows)
    first, rerun = float(found['FIRST']), float(found['RERUN'])
    tools.write_timing(here, rerun, f'first is generating and compiling the C code with odin::odin, $new(), and one run of 365 days with deSolve::dede, not counting starting R or loading odin; rerun is the best of 5 more calls of `mod$run(0:365)` on the same model', first=first)
    print(f'Wrote {len(rows)} rows; first run {first:.3f} s, rerun {1000*rerun:.2f} ms')

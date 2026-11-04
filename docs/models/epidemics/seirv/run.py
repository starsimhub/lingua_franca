"""
Run the original vignette and write its reference results and timing.

    python run.py

Needs the epidemics environment (see `_envs/epidemics`). The vignette's contact matrix and demography come from
socialmixr's POLYMOD survey and the wpp2024 package, which is not on CRAN; the driver gives them as the vignette
prints them instead (see the README), and leaves out the plots. Everything else in `original/epidemics.R` is run as it is.
"""
import os
import csv
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

script = os.path.join(here, 'original', 'epidemics.R')
reps = tools.runs(20)
timed = 1 # Which call of model_default() is timed, counting from 1
compartments = dict(susceptible='S', exposed='E', infectious='I', recovered='R', vaccinated='V')
groups = {'[0,20)':'0-19', '[20,40)':'20-39', '[40,Inf)':'40+'} # The original's labels, and Starsim's

# The inputs as the vignette prints them (socialmixr 0.7.0 and wpp2024, on the package website)
inputs = r'''
groups <- c("[0,20)", "[20,40)", "[40,Inf)")
contact_matrix <- matrix(c(
    7.883663, 3.157024, 3.084747,
    2.764179, 4.854839, 4.570735,
    1.557728, 2.636148, 5.005571
), nrow = 3, byrow = TRUE, dimnames = list(age.group = groups, contact.age.group = groups))
demography_vector <- c(14865748, 16978469, 29438434)
'''

# Runs the original's chunks, without knitr's options, the plots, and the lines that load the survey and demography, which
# `inputs` replaces. Each call of model_default() is kept, and the one timed (`timed`, counting from 1) is repeated, to time a rerun
driver = r'''
args <- commandArgs(TRUE)
now <- function() as.numeric(Sys.time())
lines <- readLines(args[1])
first <- grep("socialmixr::polymod", lines) - 1 # From its comment
last <- grep("demography_vector <- contact_data$demography$population", lines, fixed = TRUE)
lines <- c(lines[seq_len(first - 1)], readLines(args[2]), lines[-seq_len(last)])
chunks <- split(lines, cumsum(startsWith(lines, "## ----")))
chunks <- Filter(function(x) !any(grepl("ggplot\\(|knitr::", x)), chunks)
calls <- list()
model_default <- function(...) {
    start <- now()
    out <- epidemics::model_default(...)
    calls[[length(calls) + 1]] <<- list(args = list(...), seconds = now() - start, out = out)
    out
}
invisible(capture.output(eval(parse(text = unlist(chunks)), envir = globalenv())))
seconds <- numeric(0)
timed <- calls[[as.integer(args[5])]]
for (i in seq_len(as.integer(args[4]))) {
    start <- now()
    do.call(epidemics::model_default, timed$args)
    seconds <- c(seconds, now() - start)
}
for (i in seq_along(calls)) write.csv(calls[[i]]$out, file.path(args[3], sprintf("run%d.csv", i)), row.names = FALSE)
cat(sprintf("FIRST %.6f\nRERUN %.6f\nCALLS %d\n", timed$seconds, min(seconds), length(calls)))
'''


def simulate():
    """ Run the vignette, returning the rows of each call of model_default() and what was printed """
    with tempfile.TemporaryDirectory() as tmp:
        paths = {name:os.path.join(tmp, f'{name}.R') for name in ['driver', 'inputs']}
        for name,text in dict(driver=driver, inputs=inputs).items():
            with open(paths[name], 'w') as f:
                f.write(text)
        printed = tools.run(['Rscript', paths['driver'], script, paths['inputs'], tmp, str(reps), str(timed)], 'epidemics', cwd=tmp)
        found = dict(line.split() for line in printed.splitlines() if line.split(' ')[0] in ['FIRST', 'RERUN', 'CALLS'])
        runs = []
        for i in range(int(found['CALLS'])):
            with open(os.path.join(tmp, f'run{i+1}.csv')) as f:
                runs.append(list(csv.DictReader(f)))
    return runs, found


def to_rows(run, prefix=''):
    """ One series for each compartment in each group, as e.g. `I_0-19`, and in total, as `I` """
    rows, totals = [], {}
    for row in run:
        key, t, val = compartments[row['compartment']], float(row['time']), float(row['value'])
        rows.append(dict(time=t, series=f'{prefix}{key}_{groups[row["demography_group"]]}', value=val))
        totals[(key, t)] = totals.get((key, t), 0) + val
    rows += [dict(time=t, series=f'{prefix}{key}', value=val) for (key,t),val in totals.items()]
    return rows


if __name__ == '__main__':
    runs, found = simulate()
    assert len(runs) == 1
    rows = to_rows(runs[0])
    tools.write_results(here, rows)
    first, rerun = float(found['FIRST']), float(found['RERUN'])
    what = f'first is the call of model_default() in the vignette (checking the inputs, running the compiled odin model for 600 days, and making its table of results), in a fresh R session with epidemics loaded; rerun is the best of {reps} more of the same call. Neither includes starting R or loading the package'
    tools.write_timing(here, rerun, what, first=first)
    print(f'Wrote {len(rows)} rows; first run {first:.4f} s, rerun {1000*rerun:.2f} ms')

"""
Run the original SimInf example and write its reference results and timing.

    python run.py

Needs the siminf environment (see `_envs/siminf`).
"""
import os
import csv
import sys
import json
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(here)))
import tools

original = os.path.join(here, 'original', 'events_SIR.R')
reference = os.path.join(here, 'reference')
n_runs = tools.runs(200, fewest=6) # The model is stochastic; the seed (123) is set in the original
nodes = [1, 2, 3] # The nodes (herds) to report on their own; node 1 has the first infected animal
states = ['S', 'I', 'R']
series = states + ['nodes_infected'] + [f'node{node}_{key}' for node in nodes for key in states]

# Runs the original as it is (which sets the seed, builds `model`, and makes one run, `result`), then
# makes more runs of the same model, and writes one row per run and time; with a folder, it also
# writes the description of the model
driver = r'''
library(SimInf)
args <- commandArgs(TRUE)
n_runs <- as.integer(args[2])
nodes <- as.integer(strsplit(args[4], ",")[[1]])
data_u0 <- u0_SIR() # Read the data before the original, so that reading it is not timed, as in Starsim
data_events <- events_SIR()
u0_SIR <- function() data_u0
events_SIR <- function() data_events
pdf(NULL) # The original plots
first <- 0
for (expr in parse(args[1])) {
    seconds <- system.time(eval(expr))[["elapsed"]]
    target <- if (identical(expr[[1]], as.name("<-"))) expr[[2]]
    if (identical(target, as.name("model")) || identical(target, as.name("result"))) first <- first + seconds # Building the model and its first run
}

out <- NULL
reruns <- numeric(0)
for (i in seq_len(n_runs)) {
    if (i > 1) reruns <- c(reruns, system.time(result <- run(model))[["elapsed"]])
    U <- trajectory(result, format = "matrix") # One row per node and compartment, one column per time
    n <- nrow(U)/3
    S <- U[seq(1, 3*n, by = 3), , drop = FALSE]
    I <- U[seq(2, 3*n, by = 3), , drop = FALSE]
    R <- U[seq(3, 3*n, by = 3), , drop = FALSE]
    df <- data.frame(run = i, time = model@tspan, S = colSums(S), I = colSums(I), R = colSums(R), nodes_infected = colSums(I > 0))
    for (node in nodes) {
        df[[paste0("node", node, "_S")]] <- S[node, ]
        df[[paste0("node", node, "_I")]] <- I[node, ]
        df[[paste0("node", node, "_R")]] <- R[node, ]
    }
    out <- rbind(out, df)
}
write.csv(out, args[3], row.names = FALSE, quote = FALSE)
if (n_runs > 1) cat(sprintf("FIRST %.6f\nRERUN %.6f\n", first, min(reruns[1:min(5, n_runs - 1)])))

if (length(args) > 4) {
    ref <- args[5]
    u0 <- as.data.frame(t(model@u0))
    write.csv(cbind(node = seq_len(nrow(u0)), u0), file.path(ref, "u0.csv"), row.names = FALSE, quote = FALSE)
    ev <- as.data.frame(events(model)) # As the model holds them: sorted by time, then type (exit, enter, intTrans, extTrans), then select
    gz <- gzfile(file.path(ref, "events.csv.gz"), "w")
    write.csv(ev, gz, row.names = FALSE, quote = FALSE)
    close(gz)
    types <- c("exit", "enter", "intTrans", "extTrans")
    summ <- do.call(rbind, lapply(types, function(type) {
        e <- ev[ev$event == type, ]
        data.frame(event = type, count = nrow(e), individuals = sum(e$n), select = paste(sort(unique(e$select)), collapse = ";"),
                   shift = paste(sort(unique(e$shift)), collapse = ";"), proportion = paste(sort(unique(e$proportion)), collapse = ";"),
                   first_time = if (nrow(e)) min(e$time) else NA, last_time = if (nrow(e)) max(e$time) else NA)
    }))
    write.csv(summ, file.path(ref, "events_summary.csv"), row.names = FALSE, quote = FALSE, na = "")
    write.csv(as.matrix(select_matrix(model)), file.path(ref, "select_matrix.csv"), quote = FALSE)
    cat(sprintf("BETA %s\nGAMMA %s\n", model@ldata["beta", 1], model@ldata["gamma", 1]))
    stopifnot(length(unique(model@ldata["beta", ])) == 1, length(unique(model@ldata["gamma", ])) == 1)
}
'''


def simulate(runs, export=False):
    """ Run the original, then more runs of its model up to a total, returning one row per run and time, and what was printed """
    with tempfile.TemporaryDirectory() as tmp:
        script, out = os.path.join(tmp, 'driver.R'), os.path.join(tmp, 'out.csv')
        with open(script, 'w') as f:
            f.write(driver)
        cmd = ['Rscript', script, original, str(runs), out, ','.join(map(str, nodes))]
        if export:
            cmd.append(reference)
        printed = tools.run(cmd, 'siminf', cwd=tmp)
        with open(out) as f:
            rows = [{key:float(val) for key,val in row.items()} for row in csv.DictReader(f)]
    return rows, printed


def summarize(rows, key, time='time'):
    """ The mean and the 5% and 95% quantiles over the runs, at each time """
    by_time = dict()
    for row in rows:
        by_time.setdefault(row[time], []).append(row[key])
    out = []
    for t in sorted(by_time):
        vals = sorted(by_time[t])
        n = len(vals)
        out.append(dict(time=t, value=sum(vals)/n, low=vals[int(0.05*(n - 1))], high=vals[int(0.95*(n - 1))]))
    return out


def describe(printed):
    """ Write the description of the model that a translation needs, next to the tables that the driver wrote """
    found = dict(line.split() for line in printed.splitlines() if line.split(' ')[0] in ['FIRST', 'RERUN', 'BETA', 'GAMMA'])
    with open(os.path.join(reference, 'u0.csv')) as f:
        u0 = list(csv.DictReader(f))
    with open(os.path.join(reference, 'events_summary.csv')) as f:
        events = {row['event']:int(row['count']) for row in csv.DictReader(f)}
    info = dict(
        nodes         = len(u0),
        compartments  = states,
        transitions   = ['S -> beta*S*I/(S+I+R) -> I', 'I -> gamma*I -> R'],
        beta          = float(found['BETA']),
        gamma         = float(found['GAMMA']),
        times         = dict(first=1, last=1460, step=1, unit='day'),
        initial_total = {key:sum(int(row[key]) for row in u0) for key in states},
        events        = events,
        events_total  = sum(events.values()),
        files         = dict(initial='u0.csv', events='events.csv.gz', events_summary='events_summary.csv', select_matrix='select_matrix.csv'),
    )
    with open(os.path.join(reference, 'model.json'), 'w') as f:
        json.dump(info, f, indent=2)
        f.write('\n')
    return float(found['FIRST']), float(found['RERUN'])


if __name__ == '__main__':
    os.makedirs(reference, exist_ok=True)
    runs, printed = simulate(n_runs, export=True)
    assert len({row['run'] for row in runs}) == n_runs
    first, rerun = describe(printed)

    rows = []
    for key in series:
        rows += [dict(series=key, **row) for row in summarize(runs, key)]
    tools.write_results(here, rows)

    what = f'first: SIR() building the model, and its first run(model), of 1,600 nodes for 1,460 days on one thread, with R started, SimInf loaded, and the 466,692 events read. rerun: run(model) on the same model'
    tools.write_timing(here, rerun, what, first=first)
    print(f'Wrote {len(rows)} rows; the first run takes {first:.3f} s, a rerun {rerun:.3f} s')

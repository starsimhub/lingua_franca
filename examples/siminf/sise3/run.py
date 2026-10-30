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

original = os.path.join(here, 'original', 'events_SISe3.R')
reference = os.path.join(here, 'reference')
n_runs = 200 # The model is stochastic; the seed (123) is set in the original
nodes = [1, 2, 3] # The nodes (herds) to report on their own; node 1 has the first infected animals
comps = ['S_1', 'I_1', 'S_2', 'I_2', 'S_3', 'I_3']
series = comps + ['I', 'phi', 'nodes_infected'] + [f'node{node}_{key}' for node in nodes for key in ['I', 'phi']] + [f'node1_{key}' for key in comps]

# Runs the original as it is (which sets the seed, builds `model`, and makes one run, `result`), then
# makes more runs of the same model, and writes one row per run and time; with a folder, it also
# writes the description of the model
driver = r'''
library(SimInf)
args <- commandArgs(TRUE)
n_runs <- as.integer(args[2])
nodes <- as.integer(strsplit(args[4], ",")[[1]])
u0_SISe3 <- SimInf::u0_SISe3 # Read the data before the original, so that reading it is not timed, as in Starsim
events_SISe3 <- SimInf::events_SISe3
pdf(NULL) # The original plots
first <- 0
for (expr in parse(args[1])) {
    seconds <- system.time(eval(expr))[["elapsed"]]
    target <- if (identical(expr[[1]], as.name("<-"))) expr[[2]]
    if (identical(target, as.name("model")) || identical(target, as.name("result"))) first <- first + seconds # Building the model and its first run
}

comps <- c("S_1", "I_1", "S_2", "I_2", "S_3", "I_3")
out <- NULL
reruns <- numeric(0)
for (i in seq_len(n_runs)) {
    if (i > 1) reruns <- c(reruns, system.time(result <- run(model))[["elapsed"]])
    U <- trajectory(result, format = "matrix") # One row per node and compartment, one column per time
    V <- trajectory(result, compartments = "phi", format = "matrix") # One row per node
    n <- nrow(U)/6
    X <- lapply(seq_along(comps), function(k) U[seq(k, 6*n, by = 6), , drop = FALSE])
    names(X) <- comps
    I <- X$I_1 + X$I_2 + X$I_3
    df <- data.frame(run = i, time = model@tspan)
    for (k in comps) df[[k]] <- colSums(X[[k]])
    df$I <- colSums(I)
    df$phi <- colMeans(V)
    df$nodes_infected <- colSums(I > 0)
    for (node in nodes) {
        df[[paste0("node", node, "_I")]] <- I[node, ]
        df[[paste0("node", node, "_phi")]] <- V[node, ]
    }
    for (k in comps) df[[paste0("node1_", k)]] <- X[[k]][1, ]
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
                   first_time = min(e$time), last_time = max(e$time))
    }))
    write.csv(summ, file.path(ref, "events_summary.csv"), row.names = FALSE, quote = FALSE)
    write.csv(as.matrix(select_matrix(model)), file.path(ref, "select_matrix.csv"), quote = FALSE)
    write.csv(as.matrix(shift_matrix(model)), file.path(ref, "shift_matrix.csv"), quote = FALSE)
    for (key in names(model@gdata)) cat(sprintf("GDATA %s %s\n", key, model@gdata[[key]]))
    for (key in rownames(model@ldata)) {
        stopifnot(length(unique(model@ldata[key, ])) == 1)
        cat(sprintf("LDATA %s %s\n", key, model@ldata[key, 1]))
    }
    stopifnot(all(model@v0["phi", ] == 0))
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
    lines = [line.split() for line in printed.splitlines()]
    gdata = {line[1]:float(line[2]) for line in lines if line and line[0] == 'GDATA'}
    ldata = {line[1]:int(float(line[2])) for line in lines if line and line[0] == 'LDATA'}
    first, rerun = [[float(line[1]) for line in lines if line and line[0] == key][0] for key in ['FIRST', 'RERUN']]
    with open(os.path.join(reference, 'u0.csv')) as f:
        u0 = list(csv.DictReader(f))
    with open(os.path.join(reference, 'events_summary.csv')) as f:
        events = {row['event']:int(row['count']) for row in csv.DictReader(f)}
    info = dict(
        nodes         = len(u0),
        compartments  = comps,
        continuous    = ['phi'],
        transitions   = [f'S_{k} -> upsilon_{k}*phi*S_{k} -> I_{k}' for k in [1, 2, 3]] + [f'I_{k} -> gamma_{k}*I_{k} -> S_{k}' for k in [1, 2, 3]],
        phi           = 'after each day: phi <- phi*(1 - beta(day)) + alpha*(I_1 + I_2 + I_3)/N + epsilon, with day = t % 365 and beta(day) = beta_t1 on [0, end_t1), beta_t2 on [end_t1, end_t2), beta_t3 on [end_t2, end_t3), beta_t4 on [end_t3, end_t4)',
        gdata         = gdata,
        ldata         = ldata,
        phi0          = 0,
        times         = dict(first=1, last=1457, step=7, unit='day'),
        initial_total = {key:sum(int(row[key]) for row in u0) for key in comps},
        events        = events,
        events_total  = sum(events.values()),
        files         = dict(initial='u0.csv', events='events.csv.gz', events_summary='events_summary.csv', select_matrix='select_matrix.csv', shift_matrix='shift_matrix.csv'),
    )
    with open(os.path.join(reference, 'model.json'), 'w') as f:
        json.dump(info, f, indent=2)
        f.write('\n')
    return first, rerun


if __name__ == '__main__':
    os.makedirs(reference, exist_ok=True)
    runs, printed = simulate(n_runs, export=True)
    assert len({row['run'] for row in runs}) == n_runs
    first, rerun = describe(printed)

    rows = []
    for key in series:
        rows += [dict(series=key, **row) for row in summarize(runs, key)]
    tools.write_results(here, rows)

    what = f'first: SISe3() building the model, and its first run(model), of 1,600 nodes for 1,460 days on one thread, with R started, SimInf loaded, and the 783,773 events read. rerun: run(model) on the same model'
    tools.write_timing(here, rerun, what, first=first)
    print(f'Wrote {len(rows)} rows; the first run takes {first:.3f} s, a rerun {rerun:.3f} s')

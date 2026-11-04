# Run the original vignette, then repeat its simulations many times and write what run.py needs.
#
#     Rscript reference.R <original script> <output folder> <number of simulations> <seed>
#
# The original is run as it is (so `model_seirconn` is its own); only the number of simulations
# is changed for the reference runs.
suppressMessages(library(epiworldR))
args <- commandArgs(trailingOnly = TRUE)
original <- args[1]
out <- args[2]
n_runs <- as.integer(args[3])
seed <- as.integer(args[4])
now <- function() as.numeric(Sys.time()) # In finer steps than system.time(), for a run of a few ms

# Run the original, which builds the model, runs it 50 times, and plots the runs
exprs <- parse(original)
invisible(capture.output(for (expr in exprs) eval(expr, globalenv())))

# The reference runs: the same model and call, with more simulations, on one thread
saver <- make_saver("total_hist")
invisible(capture.output(run_multiple(model_seirconn, ndays = 50, nsims = n_runs, saver = saver, nthreads = 1, seed = seed)))
runs <- run_multiple_get_results(model_seirconn, nthreads = 1)$total_hist
write.csv(runs[, c("sim_num", "date", "state", "counts")], file.path(out, "runs.csv"), row.names = FALSE)

# The time of one simulation (run() with ndays = 50, without its progress bar): the first, building
# the model with the original's own statement; then the best of as many reruns as fit in 3 s (at most
# 100 once 1 s has been spent), as docs/models/tools.py times Starsim
build <- Filter(function(e) is.call(e) && identical(e[[2]], as.name("model_seirconn")), exprs)[[1]] # model_seirconn <- ModelSEIRCONN(...)
start <- now()
eval(build)
verbose_off(model_seirconn)
run(model_seirconn, ndays = 50)
first <- now() - start
best <- Inf; n <- 0; spent <- 0
while (n == 0 || spent < 1 || (spent < 3 && n < 100)) {
  start <- now()
  run(model_seirconn, ndays = 50)
  elapsed <- now() - start
  best <- min(best, elapsed); n <- n + 1; spent <- spent + elapsed
}
write.csv(data.frame(what = c("first", "rerun"), seconds = c(first, best)), file.path(out, "seconds.csv"), row.names = FALSE)

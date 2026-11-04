# Run the original vignette, then repeat its last simulation many times and write what run.py needs.
#
#     Rscript reference.R <original script> <output folder> <number of simulations> <seed>
#
# The original is run as it is (so `model_sirconn`, with both viruses, the vaccine, and the two events,
# is its own). Its events set the contact rate, which a new run does not set back, so each reference
# run first sets it back to the vignette's value of 4.
suppressMessages(library(epiworldR))
args <- commandArgs(trailingOnly = TRUE)
original <- args[1]
out <- args[2]
n_runs <- as.integer(args[3])
seed <- as.integer(args[4])
now <- function() as.numeric(Sys.time()) # In finer steps than system.time(), for a run of a few ms

# Run the original, which builds the model a step at a time, running and plotting it after each
exprs <- parse(original)
invisible(capture.output(for (expr in exprs) eval(expr, globalenv())))
vignette <- get_hist_total(model_sirconn) # Its last run, with seed 1912

# The reference runs
runs <- list()
for (i in seq_len(n_runs)) {
  set_param(model_sirconn, "Contact rate", 4)
  run(model_sirconn, ndays = 50, seed = seed + i)
  total <- get_hist_total(model_sirconn)
  virus <- get_hist_virus(model_sirconn)
  virus <- virus[virus$state == "Infected", ]
  runs[[i]] <- rbind(
    data.frame(sim = i, date = total$date, series = total$state, counts = total$counts),
    data.frame(sim = i, date = virus$date, series = paste("Infected", virus$virus), counts = virus$counts)
  )
}
runs <- rbind(do.call(rbind, runs), data.frame(sim = 0, date = vignette$date, series = vignette$state, counts = vignette$counts))
write.csv(runs, file.path(out, "runs.csv"), row.names = FALSE)

# The time of one simulation (run() with ndays = 50): the first, building the model with the vignette's
# own statements (all but its runs, plots, and summaries); then the best of as many reruns as fit in 3 s
# (at most 100 once 1 s has been spent), as docs/models/tools.py times Starsim, each setting the contact
# rate back first
builds <- c("<-", "add_virus", "set_distribution_tool", "add_tool", "add_globalevent", "verbose_off")
build <- Filter(function(e) is.call(e) && as.character(e[[1]]) %in% builds && !identical(e[[2]], as.name("repnum2")), exprs)
start <- now()
for (expr in build) eval(expr, globalenv())
run(model_sirconn, ndays = 50)
first <- now() - start
best <- Inf; n <- 0; spent <- 0
while (n == 0 || spent < 1 || (spent < 3 && n < 100)) {
  start <- now()
  set_param(model_sirconn, "Contact rate", 4)
  run(model_sirconn, ndays = 50)
  elapsed <- now() - start
  best <- min(best, elapsed); n <- n + 1; spent <- spent + elapsed
}
write.csv(data.frame(what = c("first", "rerun"), seconds = c(first, best)), file.path(out, "seconds.csv"), row.names = FALSE)

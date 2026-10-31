# Run the original script, then repeat its epidemic simulation many times and write what run.py needs.
#
#     Rscript reference.R <original script> <output folder> <number of simulations> <seed> <cores>
#
# The original is run as it is (so `est`, `param`, `init`, and `control` are its own); only the number
# of simulations and the network statistics that are recorded are changed for the reference runs.
suppressMessages(library(EpiModel))
args <- commandArgs(trailingOnly = TRUE)
original <- args[1]
out <- args[2]
n_runs <- as.integer(args[3])
seed <- as.integer(args[4])
n_cores <- as.integer(args[5])

# Run the original one statement at a time, timing the network estimation
seconds <- c()
for (expr in parse(original)) {
  elapsed <- system.time(suppressMessages(eval(expr)))[["elapsed"]]
  if (is.call(expr) && identical(expr[[1]], as.name("<-")) && is.call(expr[[3]])) {
    seconds[as.character(expr[[3]][[1]])] <- elapsed
  }
}

# The reference runs: the same model, more simulations, and the mean degree recorded as well
control_ref <- control
control_ref$nsims <- n_runs
control_ref$ncores <- n_cores
control_ref$nwstats.formula <- ~edges + meandeg + concurrent + degrange(from = 4)
set.seed(seed)
sim_ref <- netsim(est, param, init, control_ref)

epi <- as.data.frame(sim_ref)
net <- get_nwstats(sim_ref)
names(net)[names(net) == "deg4+"] <- "deg4plus"
diss <- do.call(rbind, lapply(seq_len(n_runs), function(s) {
  d <- sim_ref$diss.stats[[s]][[1]]
  data.frame(sim = s, time = seq_len(nrow(d$meanageimputed)), duration = d$meanageimputed[, 1], prop.diss = d$propdiss[, 1])
}))
all <- merge(merge(epi, net, by = c("sim", "time")), diss, by = c("sim", "time"))
write.csv(all[order(all$sim, all$time), ], file.path(out, "runs.csv"), row.names = FALSE, na = "")

# The time of one simulation (netsim with nsims = 1): the first, and then the best of 5
control_one <- control
control_one$nsims <- 1
time_one <- function() system.time(netsim(est, param, init, control_one))[["elapsed"]]
seconds["netsim_first"] <- time_one()
seconds["netsim_rerun"] <- min(replicate(5, time_one()))
write.csv(data.frame(what = names(seconds), seconds = seconds), file.path(out, "seconds.csv"), row.names = FALSE)

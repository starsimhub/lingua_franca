# Run the original Gallery script, with more simulations, and write what run.py needs.
#
#     Rscript reference.R <original folder> <output folder> <number of simulations> <seed> <cores> <scenarios>
#
# The original is run as it is, statement by statement, in its interactive configuration (N = 1500,
# 1040 weekly steps). Only three things are changed, just before its scenario loop: the number of
# simulations per scenario, the number of cores, and the network statistics that are recorded.
# With only some of the scenarios (a comma-separated list), it stops after them and writes only their times.
suppressMessages(library(EpiModel))
args <- commandArgs(trailingOnly = TRUE)

# The original evaluates its first command-line argument as R code (the Gallery's hook for its tests), and
# then uses its full-size configuration only if R is interactive
attach(list(interactive = function() TRUE, commandArgs = function(...) "NULL"), name = "original_args")

# The original starts with rm(list = ls()) and sources its modules into the global environment, so it
# is run there, and this script's own variables are kept in a local environment
local({
  original <- normalizePath(args[1])
  out <- normalizePath(args[2])
  n_runs <- as.integer(args[3])
  seed <- as.integer(args[4])
  n_cores <- as.integer(args[5])
  only <- strsplit(args[6], ",")[[1]]
  env <- globalenv()

  # The original sources "examples/hiv/module-fx.R", as in the Gallery repository
  dir.create(file.path(out, "examples", "hiv"), recursive = TRUE)
  file.copy(file.path(original, c("model.R", "module-fx.R")), file.path(out, "examples", "hiv"))
  setwd(out)

  set.seed(seed) # The original sets no seed
  seconds <- c()
  for (expr in parse(file.path("examples", "hiv", "model.R"))) {
    if (is.call(expr) && identical(expr[[1]], as.name("for")) && identical(expr[[2]], as.name("scn"))) {
      env$nsims <- n_runs
      env$control$nsims <- n_runs
      env$control$ncores <- n_cores
      env$control$nwstats.formula <- multilayer(~edges + concurrent, ~edges + concurrent)
      env$sims <- list()
      for (scn in env$scenarios.list) { # The original's loop, timed by scenario
        if (!(scn$id %in% only)) next
        seconds[paste0("netsim_", scn$id)] <- system.time(
          env$sims[[scn$id]] <- netsim(list(env$est_main, env$est_cas), use_scenario(env$param_base, scn), env$init, env$control)
        )[["elapsed"]] / n_runs
      }
      if (length(only) < length(env$scenarios.list)) { # The rest of the original needs every scenario
        write.csv(data.frame(what = names(seconds), seconds = seconds), file.path(out, "seconds.csv"), row.names = FALSE)
        quit(save = "no")
      }
      next
    }
    elapsed <- system.time(suppressMessages(capture.output(eval(expr, env))))[["elapsed"]]
    if (is.call(expr) && identical(expr[[1]], as.name("<-")) && is.call(expr[[3]]) && identical(expr[[3]][[1]], as.name("netest"))) {
      seconds[as.character(expr[[2]])] <- elapsed
    }
  }

  # One row per scenario, simulation, and time step, with the network statistics of both layers
  # (the original's analysis adds prep.cov.indic to the PrEP scenarios only, so only the columns all share are kept)
  all <- lapply(names(env$sims), function(s) {
    sim <- env$sims[[s]]
    epi <- as.data.frame(sim)
    for (k in 1:2) {
      net <- get_nwstats(sim, network = k)[, c("time", "sim", "edges", "concurrent")]
      names(net)[3:4] <- paste0(c("main", "cas")[k], ".", names(net)[3:4])
      epi <- merge(epi, net, by = c("sim", "time"))
    }
    cbind(scenario = s, epi)
  })
  keep <- Reduce(intersect, lapply(all, names))
  all <- do.call(rbind, lapply(all, function(df) df[, keep]))
  write.csv(all, file.path(out, "runs.csv"), row.names = FALSE, na = "")
  write.csv(env$summary_tbl, file.path(out, "summary.csv"), row.names = FALSE)
  write.csv(data.frame(what = names(seconds), seconds = seconds), file.path(out, "seconds.csv"), row.names = FALSE)
})

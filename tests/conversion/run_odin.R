# Compile a file with odin and run it, for test_export.py. Run with the Rscript of _envs/odin, as:
#
#     Rscript run_odin.R model.R stop out.csv
#
# Writes the trajectory, with a row for each whole unit of time from 0 to stop.
args <- commandArgs(trailingOnly=TRUE)
generator <- odin::odin_(args[1], verbose=FALSE)
model <- generator$new()
out <- model$run(0:as.integer(args[2]), atol=1e-10, rtol=1e-10)
write.csv(out, args[3], row.names=FALSE)

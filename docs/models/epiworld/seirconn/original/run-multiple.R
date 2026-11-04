## -----------------------------------------------------------------------------
#| label: sirconn-setup
library(epiworldR)
model_seirconn <- ModelSEIRCONN(
  name              = "COVID-19",
  n                 = 10000,
  prevalence        = 0.0001,
  contact_rate      = 2,
  transmission_rate = 0.5,
  incubation_days   = 7,
  recovery_rate     = 1 / 3
)


## -----------------------------------------------------------------------------
#| label: saver-generation
# Generating a saver
saver <- make_saver("total_hist", "reproductive")
# Running and printing
run_multiple(model_seirconn, ndays = 50, nsims = 50, saver = saver, nthreads = 2)


## -----------------------------------------------------------------------------
#| label: retrieving-results
# Retrieving the results
ans <- run_multiple_get_results(model_seirconn, nthreads = 2)
head(ans$total_hist)
head(ans$reproductive)


## -----------------------------------------------------------------------------
#| label: plotting-seirconn-epicurves
seirconn_50 <- ans$total_hist
seirconn_50 <- seirconn_50[seirconn_50$date <= 20, ]
plot(seirconn_50)


## -----------------------------------------------------------------------------
#| label: reproductive-number-plot
seirconn_50_r <- ans$reproductive
plot(seirconn_50_r)
# boxplot(rt ~ source_exposure_date, data = seirconn_50_r,
#         main = "Reproductive Number",
#         xlab = "Source Exposure Date",
#         ylab = "rt",
#         border = "black",
#         las = 2)


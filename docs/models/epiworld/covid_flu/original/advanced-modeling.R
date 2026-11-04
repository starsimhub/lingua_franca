## -----------------------------------------------------------------------------
#| label: create-base-model
library(epiworldR)

model_sirconn <- ModelSIRCONN(
  name              = "COVID-19",
  n                 = 50000,
  contact_rate      = 4,
  recovery_rate     = 1 / 4,
  prevalence        = 0.001,
  transmission_rate = 0.5
)


## -----------------------------------------------------------------------------
#| label: run-base-model
verbose_off(model_sirconn)
run(model_sirconn, ndays = 50, seed = 1912)
plot(model_sirconn)


## -----------------------------------------------------------------------------
#| label: create-flu-virus
flu_virus <- virus(name = "Flu", prob_infecting = .35, prevalence = 0.001, as_proportion = TRUE)


## -----------------------------------------------------------------------------
#| label: add-flu
add_virus(model_sirconn, flu_virus)


## -----------------------------------------------------------------------------
#| label: run-model-flu
run(model_sirconn, ndays = 50, seed = 1912)
plot(model_sirconn)


## -----------------------------------------------------------------------------
#| label: create-vaccine
vaccine_tool <- tool(
  name = "Vaccine",
  susceptibility_reduction = .9,
  transmission_reduction = .5,
  recovery_enhancer = .5,
  death_reduction = .9,
  prevalence = 0.5,
  as_proportion = TRUE
)


## -----------------------------------------------------------------------------
#| label: set-vaccine-distribution
set_distribution_tool(
  tool = vaccine_tool,
  distfun = distribute_tool_randomly(0.5, TRUE)
)


## -----------------------------------------------------------------------------
#| label: add-vaccine
add_tool(model_sirconn, vaccine_tool)


## -----------------------------------------------------------------------------
#| label: run-model-vaccine
run(model_sirconn, ndays = 50, seed = 1912)
plot(model_sirconn)


## -----------------------------------------------------------------------------
#| label: set-events
isolation_day_10 <- globalevent_set_params("Contact rate", 2, day = 10)
advertisement_day_20 <- globalevent_set_params("Contact rate", 1.5, day = 20)


## -----------------------------------------------------------------------------
#| label: add-events
add_globalevent(model_sirconn, isolation_day_10)
add_globalevent(model_sirconn, advertisement_day_20)


## -----------------------------------------------------------------------------
#| label: run-full-model
run(model_sirconn, ndays = 50, seed = 1912)
plot(model_sirconn)


## -----------------------------------------------------------------------------
#| label: model-summary
summary(model_sirconn)


## -----------------------------------------------------------------------------
#| label: reproductive-numbers
repnum2 <- get_reproductive_number(model_sirconn)
plot(repnum2, type = "b")


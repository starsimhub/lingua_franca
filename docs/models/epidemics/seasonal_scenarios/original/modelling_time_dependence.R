## ----include = FALSE----------------------------------------------------------
knitr::opts_chunk$set(
  collapse = TRUE,
  comment = "#>",
  message = FALSE,
  warning = FALSE,
  fig.width = 7,
  fig.height = 5
)


## ----setup--------------------------------------------------------------------
library(epidemics)
library(dplyr)
library(ggplot2)


## -----------------------------------------------------------------------------
# set up initial conditions
polymod <- socialmixr::polymod

# demography data from the wpp2024 package
data("popAge1dt", package = "wpp2024")
uk_pop <- popAge1dt |>
  dplyr::filter(name == "United Kingdom", year == 2006) |>
  dplyr::select(lower.age.limit = age, population = pop) |>
  dplyr::mutate(population = population * 1000)

contact_data <- socialmixr::contact_matrix(
  polymod,
  countries = "United Kingdom",
  survey_pop = uk_pop,
  age_limits = c(0, 20, 40),
  symmetric = TRUE,
  return_demography = TRUE
)
contact_matrix <- contact_data[["matrix"]]
demography_vector <- contact_data$demography$population

# Prepare some initial objects
uk_population <- population(
  name = "UK population",
  contact_matrix = contact_matrix,
  demography_vector = demography_vector,
  initial_conditions = matrix(
    c(1 - 1e-6, 0, 1e-6, 0, 0),
    nrow = nrow(contact_matrix), ncol = 5L,
    byrow = TRUE
  )
)


## -----------------------------------------------------------------------------
# prepare function, refer to transmissiblity as beta in function name
mod_beta <- function(time, x, tmax = 365 / 4) {
  x + (x * sinpi(time / tmax))
}


## -----------------------------------------------------------------------------
# get the function output
# calculate beta - this is done automatically inside epidemic_*()
output <- mod_beta(seq(0, 365), 1.3 / 7.0)

# plot the effect of time dependence
ggplot() +
  geom_line(
    aes(x = seq(0, 365), y = output)
  ) +
  labs(x = "Days", y = "Transmission rate (beta)") +
  theme_bw()


## -----------------------------------------------------------------------------
# note transmission_rate is the function/model parameter
# the function that affects it may have any name
data <- model_default(
  population = uk_population,
  time_dependence = list(
    transmission_rate = mod_beta
  ),
  time_end = 365, increment = 1
)

# get data on new infections
data_infections <- new_infections(data)


## ----class.source = 'fold-hide'-----------------------------------------------
# plot data on new infections
ggplot(data_infections) +
  geom_line(
    aes(x = time, y = new_infections, col = demography_group)
  ) +
  scale_y_continuous(
    labels = scales::comma,
    name = "New infections"
  ) +
  scale_color_brewer(
    palette = "Dark2",
    name = "Age group"
  ) +
  theme_bw() +
  coord_cartesian(
    expand = FALSE
  ) +
  labs(
    x = "Time (days)",
    title = "Effect of time-dependence of transmission rate"
  ) +
  theme(
    legend.position = "top",
    plot.title = element_text(face = "bold")
  )


## -----------------------------------------------------------------------------
# school closures affecting younger age groups
close_schools <- intervention(
  type = "contacts", time_begin = 50, time_end = 120,
  reduction = c(0.1, 0.01, 0.01)
)

# workplace closures affecting mostly adults
close_workplaces <- intervention(
  type = "contacts", time_begin = 65, time_end = 90,
  reduction = c(0.01, 0.2, 0.2)
)

# partially reopen schools
partial_schools <- intervention(
  type = "contacts", time_begin = 120, time_end = 180,
  reduction = c(0.05, 0.01, 0.01)
)

# combine interventions
npis <- c(close_schools, close_workplaces, partial_schools)

# print to examine
npis


## -----------------------------------------------------------------------------
# run the model with interventions and time-dependence
data_npi <- model_default(
  population = uk_population,
  intervention = list(contacts = npis),
  time_dependence = list(
    transmission_rate = mod_beta
  ),
  time_end = 365, increment = 1
)

# get the infections
data_infections_npi <- new_infections(data_npi)


## -----------------------------------------------------------------------------
data_infections$scenario <- "baseline"
data_infections_npi$scenario <- "intervention"

# combine the data
data_npi_compare <- bind_rows(data_infections, data_infections_npi)


## ----class.source = 'fold-hide'-----------------------------------------------
ggplot(data_npi_compare) +
  geom_line(
    aes(
      x = time, y = new_infections,
      col = demography_group, linetype = scenario
    )
  ) +
  scale_y_continuous(
    labels = scales::comma,
    name = "New infections"
  ) +
  scale_color_brewer(
    palette = "Dark2",
    name = "Age group",
    labels = c("Baseline", "Intervention")
  ) +
  scale_linetype_manual(
    name = "Scenario",
    values = c(
      baseline = "dashed",
      intervention = "solid"
    )
  ) +
  theme_bw() +
  coord_cartesian(
    expand = FALSE
  ) +
  labs(
    x = "Time (days)",
    title = "Effect of multiple interventions on contacts"
  ) +
  theme(
    legend.position = "top",
    plot.title = element_text(face = "bold")
  )


## -----------------------------------------------------------------------------
# define vaccination object
vax_regime <- vaccination(
  nu = matrix(0.001, nrow = 3, ncol = 1),
  time_begin = matrix(c(0, 0, 120)),
  time_end = matrix(c(0, 0, 220))
)

# view the vaccination object
vax_regime


## -----------------------------------------------------------------------------
# pass time dependence and vaccination. Note no interventions
data_vax <- model_default(
  population = uk_population,
  vaccination = vax_regime,
  time_dependence = list(
    transmission_rate = mod_beta
  ),
  time_end = 365, increment = 1
)

# collect data and add scenario
data_vax_infections <- new_infections(
  data_vax,
  exclude_compartments = c("exposed", "vaccinated")
)
data_vax_infections$scenario <- "vaccination"

# combine data
data_vax_compare <- bind_rows(data_infections, data_vax_infections)


## ----class.source = 'fold-hide'-----------------------------------------------
ggplot(data_vax_compare) +
  geom_rect(
    aes(
      xmin = 120, xmax = 220,
      ymin = 0, ymax = 20e3
    ),
    fill = "grey", alpha = 0.1
  ) +
  geom_line(
    data = filter(
      data_vax, compartment == "vaccinated", demography_group == "[40,Inf)"
    ),
    aes(time, value / 1e2),
    colour = "darkblue"
  ) +
  annotate(
    geom = "text",
    x = 190,
    y = 10e3,
    label = "Vaccines administered (100 days)",
    angle = 90,
    colour = "darkblue"
  ) +
  geom_line(
    aes(
      x = time, y = new_infections,
      col = demography_group, linetype = scenario
    )
  ) +
  scale_y_continuous(
    labels = scales::comma,
    name = "New infections",
    sec.axis = dup_axis(
      trans = function(x) x * 1e2,
      name = "Individuals vaccinated",
      labels = function(x) {
        scales::comma(x, scale = 1e-6, suffix = "M")
      }
    )
  ) +
  scale_color_brewer(
    palette = "Dark2",
    name = "Age group"
  ) +
  scale_linetype_manual(
    name = "Scenario",
    values = c(
      baseline = "dashed",
      vaccination = "solid"
    )
  ) +
  theme_bw() +
  coord_cartesian(
    ylim = c(0, 20e3),
    expand = FALSE
  ) +
  labs(
    x = "Time (days)",
    title = "Effect of a vaccination regime"
  ) +
  theme(
    legend.position = "top",
    plot.title = element_text(face = "bold")
  )


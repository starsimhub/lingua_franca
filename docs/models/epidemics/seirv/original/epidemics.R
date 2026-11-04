## ----include = FALSE----------------------------------------------------------
knitr::opts_chunk$set(
  collapse = TRUE,
  comment = "#>",
  dpi = 150
)


## ----setup--------------------------------------------------------------------
library(epidemics)
library(dplyr)
library(ggplot2)


## -----------------------------------------------------------------------------
# load contact and population data from socialmixr::polymod
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

# prepare contact matrix
contact_matrix <- contact_data[["matrix"]]

# prepare the demography vector
demography_vector <- contact_data$demography$population
names(demography_vector) <- colnames(contact_matrix)

# view contact matrix and demography
contact_matrix

demography_vector


## -----------------------------------------------------------------------------
# initial conditions
initial_i <- 1e-6
initial_conditions <- c(
  S = 1 - initial_i, E = 0, I = initial_i, R = 0, V = 0
)

# build for all age groups
initial_conditions <- rbind(
  initial_conditions,
  initial_conditions,
  initial_conditions
)

# assign rownames for clarity
rownames(initial_conditions) <- colnames(contact_matrix)

# view initial conditions
initial_conditions


## -----------------------------------------------------------------------------
uk_population <- population(
  name = "UK",
  contact_matrix = contact_matrix,
  demography_vector = demography_vector,
  initial_conditions = initial_conditions
)

uk_population


## -----------------------------------------------------------------------------
# run an epidemic model using `epidemic`
output <- model_default(
  population = uk_population,
  time_end = 600, increment = 1.0
)


## ----class.source = 'fold-hide'-----------------------------------------------
# plot figure of epidemic curve
filter(output, compartment %in% c("exposed", "infectious")) |>
  ggplot(
    aes(
      x = time,
      y = value,
      col = demography_group,
      linetype = compartment
    )
  ) +
  geom_line() +
  scale_y_continuous(
    labels = scales::comma
  ) +
  scale_colour_brewer(
    palette = "Dark2",
    name = "Age group"
  ) +
  expand_limits(
    y = c(0, 500e3)
  ) +
  coord_cartesian(
    expand = FALSE
  ) +
  theme_bw() +
  theme(
    legend.position = "top"
  ) +
  labs(
    x = "Simulation time (days)",
    linetype = "Compartment",
    y = "Individuals"
  )


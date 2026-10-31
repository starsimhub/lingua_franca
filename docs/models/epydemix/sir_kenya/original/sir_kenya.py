# Extracted from tutorials/02_Modeling_with_Population_Data.ipynb in epydemix v1.4.0
# (https://github.com/epistorm/epydemix/blob/v1.4.0/tutorials/02_Modeling_with_Population_Data.ipynb).
# Code cells 4, 11, 12, and 14 of the notebook, unchanged; these comment lines and the cell markers are the only additions.
# The cells left out plot the population and contact matrices, build a toy population, and list other geographies.

# --- Cell 4 ---
from epydemix.population import load_epydemix_population

# Load the population of Kenya from GitHub. For offline use, download the population data from
# https://github.com/epistorm/epydemix-data and provide the local path to 
# the epydemix_data folder using the argument path_to_data
population = load_epydemix_population("Kenya")
print(population)

# --- Cell 11 ---
from epydemix import load_predefined_model

# create a simple SIR model
model = load_predefined_model("SIR", transmission_rate=0.04)

# set the population (alternatively you can import it using model.import_epydemix_population('Kenya'))    
model.set_population(population)

print(model)

# --- Cell 12 ---
from epydemix.visualization import plot_quantiles

# simulate 
results = model.run_simulations(start_date="2019-12-01", 
                                end_date="2020-04-01", 
                                percentage_in_agents=10 / model.population.Nk.sum(),
                                Nsim=100)

# plot results
df_quantiles_comps = results.get_quantiles_compartments()
ax = plot_quantiles(df_quantiles_comps, columns=["Infected_total", "Susceptible_total", "Recovered_total"], legend_loc="center right")

# --- Cell 14 ---
ax = plot_quantiles(df_quantiles_comps, columns=["Infected_0-4", "Infected_5-19", "Infected_20-49", "Infected_50-64", "Infected_65+"], legend_loc="center right")

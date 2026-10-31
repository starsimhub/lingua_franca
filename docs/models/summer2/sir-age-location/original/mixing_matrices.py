# Extracted from docs/examples/09-mixing-matrices.ipynb in https://github.com/monash-emu/summer2
# (commit d1537d6): the first code cell (the base model) and the fifth (two stratifications,
# each with a mixing matrix). The code is unchanged, except for the one line marked "Added".

# --- Cell 1: "Using a mixing matrix"

from summer2 import CompartmentalModel
import pandas as pd
pd.options.plotting.backend = "plotly"

def build_model():
    """Returns a model for the mixing matrix examples"""
    model = CompartmentalModel(
        times=[0, 20],
        compartments=["S", "I", "R"],
        infectious_compartments=["I"],
        timestep=0.1
    )
    model.set_initial_population(distribution={"S": 990, "I": 10})
    model.add_infection_frequency_flow(name="infection", contact_rate=2, source="S", dest="I")
    model.add_transition_flow(name="recovery", fractional_rate=1/3, source="I", dest="R")
    model.add_death_flow(name="infection_death", death_rate=0.05, source="I")
    return model

# --- Cell 5: "Multiple mixing matrices for multiple stratifications"

import numpy as np # Added: in the notebook, this import is in the third code cell

from summer2 import Stratification, Multiply
from summer2.parameters import Data

# Age stratification with young/old mixing
age_strata = ["young", "old"]
age_strat = Stratification(name="age", strata=age_strata, compartments=["S", "I", "R"])
age_mixing_matrix = Data(np.array([
    [0.2, 0.3],
    [0.5, 0.7],
]) )
age_mixing_matrix.node_name = "age_mixing"
age_strat.set_mixing_matrix(age_mixing_matrix)


# Location stratification with urban/rural mixing
loc_strata = ["urban", "rural"]
loc_strat = Stratification(name="location", strata=loc_strata, compartments=["S", "I", "R"])
# Rural people have worse health care, higher mortality rates,
loc_strat.set_flow_adjustments("infection_death", {
    "urban": None,
    "rural": Multiply(3),
})
loc_strat.set_population_split({"urban": 0.7, "rural": 0.3})
loc_mixing_matrix = Data(np.array([
    [0.8, 0.2],
    [0.2, 0.8],
]))
loc_mixing_matrix.node_name = "loc_mixing"
loc_strat.set_mixing_matrix(loc_mixing_matrix)


# Build and run model with the stratifications we just defined
model = build_model()
# Apply age, then location stratifications 
model.stratify_with(age_strat)
model.stratify_with(loc_strat)
model.run()
model.get_outputs_df().plot()

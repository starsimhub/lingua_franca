# Extracted from docs/examples/10-derived-outputs-stratified.ipynb in
# https://github.com/monash-emu/summer2 (commit d1537d6): every code cell, in order, unchanged.
# Each cell after the first builds the model afresh, requests some derived outputs, and runs it.

# --- "Derived outputs in stratified models"

from summer2 import CompartmentalModel, Stratification, Multiply, Overwrite
import pandas as pd
pd.options.plotting.backend = "plotly"

def build_model():
    """Returns a new SIR model"""
    # Create basic SEIR model.
    model = CompartmentalModel(
        times=[0, 20],
        compartments=["S", "E", "I", "R"],
        infectious_compartments=["I"],
        timestep=0.1,
    )
    model.set_initial_population(distribution={"S": 990, "I": 10})
    model.add_infection_frequency_flow(name="infection", contact_rate=2, source="S", dest="E")
    model.add_transition_flow(name="incidence", fractional_rate=0.5, source="E", dest="I")
    model.add_transition_flow(name="recovery", fractional_rate=0.3, source="I", dest="R")
    model.add_death_flow(name="infection_death", death_rate=0.05, source="I")

    # Stratify by age.
    age_strat = Stratification('age', ['young', 'old'], ['S', 'E', 'I', 'R'])
    age_strat.set_population_split({'young': 0.5, 'old': 0.5})
    model.stratify_with(age_strat)
    
    # Stratify by clinical status for infected people.
    strata = ['asymptomatic', 'symptomatic', 'isolated', 'hospital']
    clinical_strat = Stratification('clinical', strata, ['I'])
    clinical_strat.set_population_split({'asymptomatic': 1, 'symptomatic': 0, 'isolated': 0, 'hospital': 0})
    
    # Half of young people become asymptomatic.
    young_incidence_adjustments = {
        "asymptomatic": Multiply(0.4),
        "symptomatic": Multiply(0.3),
        "isolated": Multiply(0.2),
        "hospital": Multiply(0.1),
    }
    clinical_strat.set_flow_adjustments(
        "incidence",
        young_incidence_adjustments,
        source_strata={'age': 'young'}
    )

    # A higher proporiton of old people go to hospital
    old_incidence_adjustments = {
        "asymptomatic": Multiply(0.3),
        "symptomatic": Multiply(0.3),
        "isolated": Multiply(0.2),
        "hospital": Multiply(0.3),
    }
    clinical_strat.set_flow_adjustments(
        "incidence",
        old_incidence_adjustments,
        source_strata={'age': 'old'}
    )
   
    # Adjust risk of dying given clinical status
    clinical_strat.set_flow_adjustments("infection_death", {
        "asymptomatic": Overwrite(0),  # Can't die if no symptoms
        "symptomatic": None,
        "isolated": None,
        "hospital": Multiply(2),  # Severe cases go to hospital
    })

    # Adjust infectiousness given clinical status
    clinical_strat.add_infectiousness_adjustments("I", {
        "asymptomatic": Multiply(0.5),
        "symptomatic": None,
        "isolated": Multiply(0.2),
        "hospital": Multiply(0.1),
    })    
    model.stratify_with(clinical_strat)
    
    return model

# --- "Tracking cumulative deaths by age group"

model = build_model()

age_strata = ["young", "old"]
for age_stratum in age_strata:
    output_name = f"death_{age_stratum}"
    model.request_output_for_flow(
        output_name,
        flow_name="infection_death",
        source_strata={"age": age_stratum},
        save_results=False
    )
    model.request_cumulative_output(f"accum_{output_name}", output_name)
    

model.run()
model.get_derived_outputs_df().plot()

# --- "Tracking disease incidence"

model = build_model()

age_strata = ["young", "old"]
for age_stratum in age_strata:
    model.request_output_for_flow(
        f"incidence_{age_stratum}",
        flow_name="incidence",
        source_strata={"age": age_stratum}
    )

model.run()
model.get_derived_outputs_df().plot()

# --- "Tracking disease incidence"

model = build_model()

clinical_strata = ["asymptomatic", "symptomatic", "isolated", "hospital"]
output_names = [f"incidence_{s}" for s in clinical_strata]
for clinical_stratum, output_name in zip(clinical_strata, output_names):
    model.request_output_for_flow(
        output_name,
        flow_name="incidence",
        dest_strata={"clinical": clinical_stratum}
    )

model.run()
model.get_derived_outputs_df().plot()

# --- "Tracking disease incidence"

from itertools import product

model = build_model()

age_strata = ["young", "old"]
clinical_strata = ["asymptomatic", "symptomatic", "isolated", "hospital"]
strata = list(product(age_strata, clinical_strata))
output_names = [f"incidence_{a}_{c}" for a, c in strata]

for (age, clinical), output_name in zip(strata, output_names):
    model.request_output_for_flow(
        output_name,
        flow_name="incidence",
        dest_strata={"clinical": clinical, "age": age}
    )

model.run()
model.get_derived_outputs_df().plot()

# --- "Tracking daily notifications"

model = build_model()

# Step 1: Get model to track the incidence flows for the notification strata
notify_strata = ["isolated", "hospital"]
output_names = [f"incidence_{s}" for s in notify_strata]
for notify_strata, output_name in zip(notify_strata, output_names):
    model.request_output_for_flow(
        output_name,
        flow_name="incidence",
        dest_strata={"clinical": notify_strata}
    )
    
# Step 2: Aggregate the notification strata
model.request_aggregate_output(
    name="notifications",
    sources=output_names,
)

model.run()
model.get_derived_outputs_df().plot()

# --- "Tracking hospital occupancy"

model = build_model()

model.request_output_for_compartments(
    'hospital_occupancy',
    compartments=["I"],
    strata={"clinical": "hospital"}
)

model.run()
model.get_derived_outputs_df().plot()

# --- "Using DerivedOutput GraphObjects"

from summer2.parameters import DerivedOutput

# --- "Using DerivedOutput GraphObjects"

model = build_model()

model.request_output_for_compartments(
    'hospital_occupancy',
    compartments=["I"],
    strata={"clinical": "hospital"},
    save_results=False
)

model.request_output_for_compartments(
    'all_infected',
    compartments=["I"],
    save_results=False
)

model.request_function_output("prop_infected_hosp", DerivedOutput("hospital_occupancy") / DerivedOutput("all_infected") )

model.run()
model.get_derived_outputs_df().plot()

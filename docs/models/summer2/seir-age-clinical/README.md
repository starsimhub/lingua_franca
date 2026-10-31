# summer2: SEIR by age and clinical status, with derived outputs

An SEIR epidemic with disease deaths in 1,000 people over 20 time units, stratified by age (young, old), with the infectious further stratified by clinical status (asymptomatic, symptomatic, isolated, in hospital). Which clinical status a new case takes depends on their age, and each status has its own infectiousness and death rate. The model is then built and run seven times, each time with a different set of derived outputs: cumulative deaths by age, incidence by age, by clinical status, and by both, notifications, hospital occupancy, and the proportion of the infectious who are in hospital. It is the "Derived outputs in stratified models" notebook in summer2's documentation, the most detailed of its stratification tutorials (notebooks 06 to 10).

## What it exercises

- Two stratifications, the second of only one compartment (`I`): 4 compartments become 14
- Flow adjustments that depend on a stratum of an earlier stratification (`source_strata={'age': 'young'}`), so that the clinical status a new case enters depends on their age
- A flow into a stratified compartment from one that is not, split among the strata by its adjustments, and an initial population split differently (all asymptomatic)
- An `Overwrite(0)` adjustment (the asymptomatic do not die) alongside `Multiply` ones
- Infectiousness by stratum (`add_infectiousness_adjustments`)
- Derived outputs of every kind: flows filtered by source or destination strata, a cumulative output, an aggregate of two outputs, an output of compartments filtered by stratum, and a function of two other outputs (`DerivedOutput("hospital_occupancy") / DerivedOutput("all_infected")`)

The other summer2 example ([sir-age-location](../sir-age-location)) covers two full stratifications with mixing matrices; this one has no mixing matrix (mixing is homogeneous) and instead covers partial and interdependent stratifications and derived outputs.

## Files

- `original/10-derived-outputs-stratified.ipynb`: the notebook from the summer2 documentation, unchanged
- `original/derived_outputs.py`: every code cell of the notebook, in order, as a script, unchanged
- `export.py`: runs the script in the summer2 environment, keeping each of the seven models it builds and runs, and prints the results and timing (its plots are skipped)
- `run.py`: calls `export.py` and writes `reference/`
- `reference/results.csv`: each of the 14 compartments at each of the 201 times, named `<compartment>_<age>[_<clinical>]` (for example, `S_young` or `I_old_hospital`), and the 19 derived outputs that the notebook saves, under their own names (`accum_death_young`, `incidence_old_hospital`, `notifications`, `hospital_occupancy`, `prop_infected_hosp`, ...). An output requested in two cells (`incidence_isolated`, `incidence_hospital`) is the same in both, which `export.py` checks
- `reference/timing.json`: the time of the first run (building, compiling, and running all seven models, with summer2 and JAX already imported; the first model alone is in `what`) and of a rerun of the last model
- `meta.yaml`: where it came from
- `LICENSE`: the summer2 license

## The model

Compartments `S`, `E`, `I`, and `R`, with `I` infectious. Time runs from 0 to 20 with results every 0.1; the notebook does not name the unit.

| Flow | From | To | Rate per person |
|---|---|---|---|
| `infection` (frequency-dependent) | `S` | `E` | `contact_rate = 2` times the force of infection |
| `incidence` | `E` | `I` | `0.5`, split among the clinical strata (below) |
| `recovery` | `I` | `R` | `0.3` |
| `infection_death` | `I` | out of the model | `0.05`, times 0 (asymptomatic), 1, 1, or 2 (hospital) |

The initial population is `S = 990`, `I = 10`, split 50% young and 50% old, with everyone in `I` asymptomatic.

The `incidence` flow is split into one flow to each clinical stratum, with its rate multiplied by:

| Age | Asymptomatic | Symptomatic | Isolated | Hospital | Sum |
|---|---|---|---|---|---|
| young | 0.4 | 0.3 | 0.2 | 0.1 | 1.0 |
| old | 0.3 | 0.3 | 0.2 | 0.3 | 1.1 |

The multipliers for the old sum to 1.1, so the old leave `E` 10% faster than the young (at 0.55, not 0.5); the notebook does not say whether that is intended. Its comment on the young ("Half of young people become asymptomatic") does not match the 0.4 it gives either.

Infectiousness is 0.5 for the asymptomatic, 1 for the symptomatic, 0.2 for the isolated, and 0.1 for those in hospital. There is no mixing matrix, so the force of infection on everyone is `2 × Σ infectiousness × I / N`, where `N` is the current total population (which falls as people die).

The solver is the default: an adaptive Dormand–Prince Runge–Kutta method, compiled with JAX, with relative and absolute tolerances of `1.4e-4`. `timestep = 0.1` sets the times of the results, not the step of the solver.

### Derived outputs

- A flow output is the rate of the flow (people per unit of time, not per timestep) at each output time, averaged with the rate at the time before (the default `raw_results=False`), and at time 0 the rate itself.
- A cumulative output is the running sum of its source over the output times, not multiplied by the timestep. So `accum_death_young` and `accum_death_old` are 10 times the number who died: together they reach 757 by time 20, when 76 people have died. The notebook calls them "the cumulative number of people who have died from the disease".
- `prop_infected_hosp` is `I` in hospital over all of `I`.

## Lines of model code

134, counting every line of `original/derived_outputs.py` that is not blank or a comment, and leaving out the imports, the docstring, the seven plotting lines, and the line that sets the plotting backend, with the two lines over 100 characters counted twice. Of these, 55 are the model itself (`build_model()`); the rest build and run it seven times to request the derived outputs, one group at a time, as the notebook does.

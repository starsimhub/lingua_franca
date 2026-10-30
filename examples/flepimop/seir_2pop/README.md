# flepiMoP: SEIR in two subpopulations

A deterministic SEIR epidemic in two provinces, of 9,000 and 1,000 people, coupled by daily travel, over seven months. It starts with 5 exposed people in the large province and reaches the small one only through mobility. The whole model is one YAML configuration and three small CSV files: this is the configuration that flepiMoP's quick start guide runs first.

flepiMoP calls it its "sample 2pop" model and it is often described as an SIR, but the configuration has an exposed state, so it is an SEIR.

## What it exercises

- A model with no code: compartments, parameters, and transitions are all declared in YAML
- Transitions written as a rate and a list of what they are proportional to, each with an exponent
- Parameters and rates that are expressions (`1 / 4`, `Ro * gamma`)
- Subpopulations from a table of populations, and coupling from a table of travelers
- Initial conditions from a file of amounts per subpopulation and compartment
- A fixed-step solver chosen in the configuration, and daily output of both prevalence and incidence

## Files

- `original/config_sample_2pop.yml`: the configuration, unchanged
- `original/model_input/geodata_sample_2pop.csv`, `mobility_sample_2pop.csv`, `ic_2pop.csv`: the populations, the mobility, and the initial conditions, unchanged
- `run.py`: runs it with `flepimop simulate` and writes `reference/`
- `reference/results.csv`: for each of `large_province` and `small_province`, the amount in each compartment at the start of each day (`large_province_S`, `_E`, `_I`, `_R`) and the amount entering it during that day (`large_province_incidence_E`, `_incidence_I`, `_incidence_R`), for days 0 to 212, where day 0 is 1 February 2020
- `reference/timing.json`: the time of a first run and of a rerun, each the whole command
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (GPL-3.0)

## The model

- **Compartments:** `S`, `E`, `I`, `R`, as one dimension, `infection_stage`. Amounts are real numbers, not whole people.
- **Parameters:** `sigma = 1 / 4` per day, `gamma = 1 / 5` per day, `Ro = 2.5`. The infection rate is the expression `Ro * gamma`, which is 0.5 per day.
- **Populations** (`geodata_sample_2pop.csv`): `large_province` 9,000, `small_province` 1,000. These are fixed numbers, `N`, used in the force of infection.
- **Mobility** (`mobility_sample_2pop.csv`): 100 people a day from `large_province` to `small_province`, and 20 a day the other way.
- **Initial conditions** (`ic_2pop.csv`, `method: SetInitialConditions`): `large_province` has `E = 5` and `S = 8995`; `small_province` has `S = 1000`; anything not listed is 0. There is no `seeding` section, so nothing is added later.
- **Time:** 1 February to 31 August 2020, which is 213 days, with `method: rk4` (classic fourth-order Runge-Kutta) and `dt: 1` day, so one step per day.

### Transitions

In subpopulation `i` (the code is `rk4_integration` in `flepimop/gempyor_pkg/src/gempyor/steps_rk4.py`):

| Transition | Rate (amount per day) |
|---|---|
| `S` to `E` | `S_i * [(1 - 0.5 * p_i) * (Ro * gamma) * I_i / N_i + sum over j of 0.5 * (M_ij / N_i) * (Ro * gamma) * I_j / N_j]` |
| `E` to `I` | `sigma * E_i` |
| `I` to `R` | `gamma * I_i` |

A transition is `rate` times the product of its `proportional_to` terms, each raised to its `proportion_exponent` (all 1 here). The first term is always the source compartment. Any further term is not the plain amount: it is divided by the population and mixed over subpopulations by the mobility, which is the part in square brackets above.

### How mobility couples the subpopulations

`M_ij` is the number who travel from `i` to `j` each day, and `p_i = min(1, sum over j of M_ij / N_i)` is the fraction of `i` that travels. Travelers are taken to spend half of each day away (a fixed 0.5 in the code, not a setting). So a susceptible in `i` meets the prevalence at home, `I_i / N_i`, with weight `1 - 0.5 * p_i`, and the prevalence in each place `j` that residents of `i` go to, `I_j / N_j`, with weight `0.5 * M_ij / N_i`. The weights sum to 1.

Nobody changes subpopulation: mobility changes only who a susceptible is exposed to. Only the row of the origin counts, so people arriving from `j` do not add to the force of infection in `i`. Here `p` is 100/9000 for the large province and 20/1000 for the small one, so the forces of infection are:

- Large: `0.5 * (0.99444 * I_large / 9000 + 0.00556 * I_small / 1000)`
- Small: `0.5 * (0.99 * I_small / 1000 + 0.01 * I_large / 9000)`

### Output

Each day has a "prevalence" row and an "incidence" row per compartment. Prevalence is the amount at the start of the day, so day 0 is the initial conditions. Incidence is the total that flowed into the compartment during the day's step, so `incidence_E` is new infections, `incidence_I` is onsets of infectiousness, and `incidence_R` is recoveries; incidence of `S` is always 0 and is left out of `reference/results.csv`.

## Results

In the large province `I` peaks at 1,141 on day 63, and 8,035 of 9,000 have recovered by day 212. The small province follows 18 days later: `I` peaks at 130 on day 81, and 893 of 1,000 have recovered. Both final sizes are 89%, as expected for `Ro = 2.5`.

The run is deterministic, and writing the equations above as one fourth-order Runge-Kutta step per day reproduces every value to within 1e-11.

## Lines of model code

42: every line of `config_sample_2pop.yml` that is not blank (it has no comments, and no line over 100 characters). The three CSV files add 10 lines of data, including their headers.

## Variants upstream

Only the base configuration is collected. In the same folder:

- `config_sample_2pop_modifiers.yml` adds 65 lines to the same model: `seir_modifiers`, which scale a parameter over a period (`Ro` times 0.4 from 15 March to 1 May, then times 0.8 to 31 August, the two stacked into one scenario); `outcomes`, which derive reported cases, hospitalizations (with a duration, giving current hospitalizations), and deaths from the incidence of `I` by a probability and a delay; and `outcome_modifiers`, which halve the probability of detecting a case until 1 June
- `config_sample_2pop_stochastic.yml` is the same model with `method: stochastic`, `dt: 0.2`, and 20 runs (`nslots: 20`). Each step, the number leaving a compartment is a binomial draw with probability `1 - exp(-dt * rate)`.
- `config_sample_2pop_inference.yml` fits the model to data.

## Notes

- flepiMoP has no release that includes this tutorial or the `flepimop simulate` command, so the example is pinned to a commit of `main` (see `_envs/flepimop/README.md`).
- The run prints "Confused between reading .csv or parquet. Assuming input file is .parquet", although it reads the CSV initial conditions correctly.
- The header of `ic_2pop.csv` names the compartment column `mc_name`; the other files have a space after each comma, which flepiMoP ignores.

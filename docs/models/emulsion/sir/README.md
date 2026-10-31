# EMULSION: SIR as a compartmental, individual-based, and hybrid model

A closed, stochastic, discrete-time SIR epidemic in 100 individuals over 100 days, written three times: once for each of the ways EMULSION can represent a population.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 81 (compartments), 86 (individuals) | 10 | The original is one YAML file per paradigm; here one model is run two ways |
| One compartmental run | first 1 s, rerun 1 s | first 0.017 s, rerun 0.0011 s (Rust) | The original runs as a whole command, so its first run and rerun are the same command, and both include starting Python and reading the model (about 0.7 s; it reports 0.06 s for the run itself). Starsim's exclude the import |
| Results, compartments | | | **Agree.** Mean of 200 runs: a peak of 38 infectious on day 18, against 37 on day 18; 86 recovered at the end, against 85 (`compare.py` asks for 1.5 and 2 animals). This needs whole-day steps, `substeps=1` |
| Results, individuals | | | **Agree, within chance.** Mean of 200 runs: a peak of 35 on day 18, against 37 on day 19; 79 recovered at the end, against 81, with 21% of runs dying out early, against about 19% (`compare.py` asks for 3 and 6 animals) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `4473e253`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared, once. The paradigm is the `solver=` argument of the sim, where the original changes `aggregation_type` and adds a level and prototypes to the file.

## Findings

- **Initial numbers (fixed).** `init_n=dict(I=1)` starts exactly one animal infected, as agents and as compartments.
- **Dying out (better).** This version once had noticeably more runs die out early as agents than the original. The gap is now within the chance of 200 runs.
- **Whole days have to be asked for.** Starsim's chain binomial takes smaller steps by default, which gives 88 recovered at the end, against 85. `substeps=1` takes each day whole, as EMULSION does.
- **No hybrid.** The original's third form (groups that hold individuals) has no counterpart, and for this model none is needed: its three forms are statistically the same.
- **The original documents more.** About a quarter of the YAML is names, descriptions, and colors, which is why it is longer, and a reader of the file learns more from it. Here `doc=` on a parameter can do some of this.

## What it exercises

- One model description run under three paradigms, chosen by a single keyword (`aggregation_type`)
- A state machine: states, and transitions with rates
- Rates that are named expressions of the state counts (`total_I`, `total_population`), which EMULSION provides
- Rates turned into probabilities for the time step
- Initial conditions given as counts per state (compartmental) or as counts of prototype individuals (individual-based and hybrid)
- Outputs declared in the model, including a derived quantity (`percentage_prevalence`)

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/compart_SIR.yaml`, `original/IBM_SIR.yaml`, `original/hybrid_SIR.yaml`: the three models, unchanged, from `models/features/` in the source distribution of EMULSION 1.1.1
- `run.py`: runs them and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 200 runs of each variant, at each of days 0 to 100 (`compartment_S`, `compartment_I`, `compartment_R`, `ibm_S`, `ibm_I`, `ibm_R`, `hybrid_S`, `hybrid_I`, `hybrid_R`)
- `reference/timing.json`: the times of a first run and a rerun of the compartmental variant, each as a whole command
- `meta.yaml`: where it came from
- `LICENSE`, `NOTICE`: the upstream license (Apache-2.0) and its notice

## The model

The same in all three files.

- **States:** `S` (susceptible), `I` (infectious), `R` (resistant), as one state machine, `health_state`
- **Transitions:** `S` to `I` at rate `force_of_infection`, and `I` to `R` at rate `recovery`
- **Force of infection:** `transmission_I * total_I / total_population` (frequency dependent)
- **Parameters:** `transmission_I = 0.5` per day, `recovery = 0.1` per day, `initial_population_size = 100`, `initial_infected = 1`
- **Initial conditions:** 99 in `S`, 1 in `I`, 0 in `R`
- **Time:** 100 days in steps of 1 day (`delta_t: 1`, `total_duration: '100'`), giving 101 output rows per run, for steps 0 to 100
- **Outputs:** the count in each state at every step, plus `percentage_prevalence` (`100 * total_I / total_population`) and `total_population`

A rate becomes a probability for the step as `1 - exp(-rate * delta_t)`; with several ways out of a state, that probability is computed from the total rate and shared in proportion to each rate. Here each state has one way out, so the probabilities are `1 - exp(-0.5 * I/N)` for infection and `1 - exp(-0.1)`, about 0.095, for recovery. The force of infection is evaluated once per step, from the counts at the start of the step.

## How the variants differ

| | Compartmental | Individual-based | Hybrid |
|---|---|---|---|
| `aggregation_type` of the `population` level | `compartment` | `IBM` | `hybrid` |
| Levels | `population` | `population`, containing `individuals` | `population`, containing `individuals` |
| `processes` | `population: [infection]`, a grouping | `individuals: [health_state]`, the state machine itself | `population: [infection]`, a grouping |
| `grouping` | `infection`, by `health_state` | none | `infection`, by `health_state` |
| `prototypes` | none | `healthy` (`health_state: S`), `infected` (`health_state: I`) | the same as individual-based |
| `initial_conditions` | amounts per state (`vars: [S]`, `vars: [I]`) and a total | amounts per prototype | amounts per prototype |

The state machine, parameters, time, and outputs are word for word the same, apart from the model name, its abstract, and the comments.

In behavior:

- **Compartmental:** there are no individuals, only a count per state. Each step, the number leaving a state is one multinomial draw from that count.
- **Individual-based:** there are 100 agents, each holding its own `health_state`. Each step, every agent draws its own transition.
- **Hybrid:** there are 100 agents, but they are grouped by `health_state`, and each step the number leaving a group is drawn once for the group, as in the compartmental model; that many agents are then picked from the group and moved. This keeps the individuals (and anything they carry) at close to the cost of compartments.

These three models are the plainest case, so the individuals carry nothing but their state: no ages, no durations, no individual attributes. Time in `I` is geometric in all three (the discrete-time form of an exponential), and the three give the same distribution of outcomes. Other models in the same folder upstream add what only individuals can carry, such as explicit durations in a state (`IBM_duration.yaml`, `hybrid_duration.yaml`) and age (`IBM_SIR_age_demo.yaml`).

## Results

The three variants agree to within the noise of 200 runs: mean `I` peaks at about 36 around day 20, and the mean final `R` is 81 to 85. With one initial case, some runs die out at once and the rest infect nearly everyone, so the range across runs is wide (final `R` from 1 to 100).

`run.py` uses `--seed 1`, so it writes the same results each time.

## Lines of model code

- Compartmental (`compart_SIR.yaml`): 81
- Individual-based (`IBM_SIR.yaml`): 86
- Hybrid (`hybrid_SIR.yaml`): 92

Each counts every line that is not blank or a comment; no line is over 100 characters. The count includes the two YAML document markers (`---` and `...`) and the descriptive lines that EMULSION encourages (`desc`, `name`, `fillcolor`, `model_info`), which are about a quarter of each file. The files themselves are 286 to 299 lines long, most of that being comments and section banners.

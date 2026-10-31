# individual

|  |  |
|---|---|
| **Language** | R, with a C++ (Rcpp) core |
| **Paradigms** | Agent-based, discrete-time, state-and-event |
| **Specification style** | Construct variables, events, and processes; hand them to a simulation loop |
| **Version reviewed** | 0.1.19 |
| **License** | MIT |
| **Code** | <https://github.com/mrc-ide/individual> |
| **Docs** | <https://mrc-ide.github.io/individual/> |
| **Paper** | [10.21105/joss.03539](https://doi.org/10.21105/joss.03539) |
| **Downstream** | `malariasimulation` and much of the `malariaverse` are built on it |

## What it's for

`individual` is a toolkit for building fast individual-based models in R. It contains **no epidemiology at all**: no compartments, no diseases, no networks, no transmission. It provides typed per-agent variables backed by bitsets, a scheduled-event mechanism, and a simulation loop, and the modeler writes everything else.

It is here as the **minimum**: the building blocks an agent-based epidemiological model needs, with nothing above them. Every other agent-based framework here can be read as `individual` plus some epidemiological vocabulary.

## How a model is specified

The full SIR model from the package tutorial:

```r
# State: a categorical variable over the population
health <- CategoricalVariable$new(categories = c("S","I","R"), initial_values = health_states_t0)

# A process: a function of time that queues state updates
infection_process <- function(t) {
  I <- health$get_size_of("I")
  foi <- beta * I / N
  S <- health$get_index_of("S")               # a Bitset
  S$sample(rate = pexp(q = foi * dt))         # thin it stochastically, in place
  health$queue_update(value = "I", index = S)
}

# An event: something scheduled to happen to specific individuals later
recovery_event <- TargetedEvent$new(population_size = N)
recovery_event$add_listener(function(t, target) {
  health$queue_update("R", target)
})

recovery_process <- function(t) {
  I <- health$get_index_of("I")
  already_scheduled <- recovery_event$get_scheduled()
  I$and(already_scheduled$not(inplace = TRUE))       # bitset algebra
  rec_times <- rgeom(n = I$size(), prob = pexp(q = gamma * dt)) + 1
  recovery_event$schedule(target = I, delay = rec_times)
}

# Output
health_render <- Render$new(timesteps = steps)
health_render_process <- categorical_count_renderer_process(health_render, health, health_states)

simulation_loop(
  variables = list(health),
  events    = list(recovery_event),
  processes = list(infection_process, recovery_process, health_render_process),
  timesteps = steps
)
```

## Core abstractions

There are exactly five:

| Concept | `individual` name | Notes |
|---|---|---|
| **Variable** | `CategoricalVariable`, `IntegerVariable`, `DoubleVariable`, `RaggedInteger`, `RaggedDouble` | Typed per-agent state. Categorical variables are stored as bitsets |
| **Bitset** | `Bitset` | A set of individuals, with `and`, `or`, `not`, `xor`, `sample`, `size`, and in-place variants |
| **Process** | `function(t)` | Runs every timestep; reads state, queues updates |
| **Event** | `Event`, `TargetedEvent` with listeners | Scheduled with a delay; fires on specific individuals |
| **Render** | `Render` | Collects time series output |

There are also ready-made processes (`bernoulli_process`, `fixed_probability_multinomial_process`, `multi_probability_bernoulli_process`, `infection_age_process`, `categorical_count_renderer_process`, `update_category_listener`, `reschedule_listener`) for the most common patterns.

## The two-phase update

This is the most important detail. Processes do not change state directly; they **queue** updates (`health$queue_update(...)`), which the loop applies after every process has run. So every process in a step sees the same start-of-step state, and the result does not depend on the order of processes.

`individual` is the only agent-based framework in the review that does this. Starsim's `Loop`, EpiModel's `module.order`, and Vivarium's priorities make the order explicit, and it still matters. Here it does not.

## Bitsets as the population algebra

`Bitset` is the second important idea. Sets of individuals are bitsets, and selecting a group uses and, or, and not:

```r
I <- health$get_index_of("I")
I$and(already_scheduled$not(inplace = TRUE))   # infectious AND NOT already scheduled
```

Then `$sample(rate = p)` thins the set at random. Together, these cover a remarkable share of what agent-based epidemiological code does, at C++ speed, in short, readable R.

EpiHiper expresses the same operation as sets defined by conditions on the network, and EMOD as `Targeting_Config`. Here it is a sequence of calls, but the logic is identical.

## Time

Unitless integer timesteps. In the tutorial, `dt` is a number the modeler multiplies rates by, `steps = tmax/dt`, and transition probabilities are `pexp(q = rate * dt)`.

Using the exponential CDF to convert a rate to a per-step probability is correct, and it is written out in the model each time, as in odin. No dimensional types.

## Strengths

- **Minimal and complete.** Five building blocks, and `malariasimulation`, one of the most detailed disease models in the field, is built on them.
- **Order does not matter**, through queued updates. This is the strongest correctness property of any agent-based framework in the review.
- **Bitsets for selecting groups**: fast, and a direct match for how modelers think about who is eligible.
- **Thinning at random** (`$sample(rate = p)`) to go with selection.
- **`TargetedEvent` with delays**: schedule a future change for specific individuals, a natural way to express dwell times, and what Starsim does with `ti_*` arrays.
- **Ready-made processes** for the common patterns.
- **Checkpointing** (`save_object_state` / `restore_object_state`) built in.
- **Fast** for R, through its C++ bitset core.
- **Deliberately free of disease concepts**, which makes it reusable.

## Limitations

- **No epidemiology.** Nothing for disease, networks, transmission, interventions, or demographics. Every model is written from the building blocks, and two models of the same thing may share no structure.
- **The model is entirely code.** Processes are R functions, so a model cannot be read by software, saved as data, drawn, or converted.
- **No support for transmission.** The tutorial's `foi <- beta * I / N` is homogeneous mixing by hand, and contact structure is left to the modeler.
- **Unitless time**, with the `dt` convention documented but not enforced.
- **Few result tools** beyond `Render`, which collects numbers a process gives it.
- **No inference, calibration, or scenario tools.**
- **Tied to R**: the C++ core is not meant as a standalone library.

## Implications for the lingua franca

1. **Adopt queued updates, so that order within a step does not matter.** This is `individual`'s most valuable contribution, and it addresses a gap in Starsim: if every process sees the start-of-step state and updates apply at the end, order stops being hidden behavior. Chains within a step ("infect, then immediately test the newly infected") then have to be written as sub-steps, which is a good trade, because the chain becomes visible.
2. **Selecting sets of people is a core operation, and three frameworks agree.** `individual`'s `Bitset`, EpiHiper's `sets`, and EMOD's `Targeting_Config` are the same concept. The lingua franca should have **a declared set expression** over agent state (as EpiHiper does), with bitsets as a natural implementation.
3. **"Select a set, then thin it at random" is the basic agent-based operation.** `S$sample(rate = pexp(q = foi * dt))` is what nearly every agent-based process comes down to. A building block of this shape (*for agents matching this condition, with this probability, do this*) would cover most interventions, progressions, and transmission.
4. **Scheduled events are the right way to handle dwell times for agents.** `recovery_event$schedule(target = I, delay = rec_times)` is the agent-based form of EpiHiper's `dwellTime` and camdl's `via erlang`. **One declaration ("the dwell time in I is Gamma(α, β)") should become a scheduled event for agents, Erlang sub-compartments in an ODE, and a memory kernel in an IDE.** This is a concrete test of paradigm independence, and worth prototyping early.
5. **`individual` sets the minimum, and the gap above it is the project's work.** Every agent-based framework here adds its own vocabulary to roughly these five building blocks (Starsim's modules, epiworld's viruses and tools, EMOD's campaigns, EpiHiper's rules). A lingua franca aims to make those differences unnecessary.

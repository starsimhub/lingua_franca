---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Starsim

|  |  |
|---|---|
| **Language** | Python, with Numba kernels and optional Rust copies, and optional JAX for gradients; R bindings via `rstarsim` |
| **Paradigms** | Starsim 3: agent-based, with network and mixing-pool transmission. Starsim 4 adds ODE, chain binomial, and Gillespie runs of declared models |
| **Specification style** | Starsim 3: Python classes, with declared parameters, states, and results and hand-written `step()` methods. Starsim 4 adds declared states and transitions (`S >> I @ beta*I`) |
| **Version reviewed** | 3.6.0 (2026-08-28), re-checked against 3.7.2 (2026-10-06). Code here is updated to run on 4.0 |
| **License** | MIT |
| **Code** | <https://github.com/starsimhub/starsim> |
| **Docs** | <https://starsim.org/v4>, including a [landscape page](https://starsim.org/v4/user_guide/library_landscape.html) and [conversion guides](https://starsim.org/v4/user_guide/conversion/index.html) |
| **Paper** | Methods paper in preparation; Kerr et al. (2024), SciPy talk, [10.25080/ukpu4584](https://doi.org/10.25080/ukpu4584); predecessor Covasim in *PLOS Comp Biol* [10.1371/journal.pcbi.1009149](https://doi.org/10.1371/journal.pcbi.1009149) |
| **Ecosystem** | ~12 first-party disease models (STIsim, HPVsim, TBsim, FPsim, RSVsim, Rotasim, …) built on `ss.Module` and running in the same `ss.Sim` loop |

*Conflict of interest note: this project was written by Starsim's maintainers, and it became Starsim 4. So read the limitations section first.*

*This entry reviews Starsim 3, the starting point for the design, and its limitations are those of Starsim 3. Notes marked "Starsim 4" say what has since changed. How to use Starsim today is in the [docs](https://starsim.org/v4).*

## What it's for

Starsim simulates several co-circulating diseases and health states in one population of agents on dynamic contact networks. Its central idea is **modularity across health conditions**: diseases, demographics, networks, interventions, connectors, and analyzers are all the same kind of object (`ss.Module`), added to the same `ss.Sim`. They interact through shared per-agent state. Co-infection, pregnancy affecting HIV progression, malnutrition affecting measles severity, and family planning affecting the population pyramid can all be written the same way.

It generalizes a decade of single-disease Python models (Covasim, HPVsim, FPsim) into one framework, and the disease-specific packages now sit on top of it rather than being forks.

## How a model is specified

A model is a `Sim` plus a set of modules. At the simplest, everything is a dict:

```python
import starsim as ss

pars = dict(
    n_agents  = 5_000,
    networks  = dict(type='random', n_contacts=10),
    diseases  = dict(type='sir', init_prev=0.01, beta=0.05),
)
sim = ss.Sim(pars).run()
sim.plot()
```

`networks`, `diseases`, `demographics`, `interventions`, `connectors`, and `analyzers` each accept a string, a dict with a `type` key, a module instance, or a list of these. The dict form could be written as JSON. In Starsim 3 it was the closest thing to a declarative model file, and it covered much routine use.

In Starsim 3, anything beyond that was a Python class. A new disease subclasses `ss.Disease` (or `ss.Infection`, which adds transmission), makes three declaration calls in `__init__`, and implements one or more step methods. This form still works in Starsim 4:

```python
class SIR(ss.Infection):
    def __init__(self, pars=None, **kwargs):
        super().__init__()
        self.define_pars(
            beta      = ss.peryear(0.1),
            init_prev = ss.bernoulli(p=0.01),
            dur_inf   = ss.lognorm_ex(mean=ss.years(6)),
        )
        self.update_pars(pars, **kwargs)

        self.define_states(
            ss.BoolState('susceptible', default=True, label='Susceptible'),
            ss.BoolState('infected', label='Infected'),
            ss.BoolState('recovered', label='Recovered'),
            ss.FloatArr('ti_infected', label='Time of infection'),
            ss.TimeArr('ti_recovered', label='Time of recovery'),
            ss.FloatArr('rel_sus', default=1.0),
            ss.FloatArr('rel_trans', default=1.0),
            reset = True, # Replace the states that ss.Infection already defines
            infectious = 'infected', # Everyone infected is infectious
        )

    def set_prognoses(self, uids, sources=None):
        super().set_prognoses(uids, sources)
        self.susceptible[uids] = False
        self.infected[uids] = True
        self.ti_infected[uids] = self.ti
        self.ti_recovered[uids] = self.ti + self.pars.dur_inf.rvs(uids)

    def step_state(self):
        recovered = (self.infected & self.ti_recovered.due()).uids
        self.infected[recovered]  = False
        self.recovered[recovered] = True
```

The three `define_*` calls are the interesting part. They are **declarations with types**: parameters carry time units (`ss.peryear`, `ss.years`) or distributions (`ss.bernoulli`, `ss.lognorm_ex`); states carry a data type, a default, and a label; results carry a shape, a time vector, and a module. `update_pars` rejects a parameter name that `define_pars` did not declare, and declared states and core attributes (`pars`, `results`, `sim`) cannot be overwritten by plain assignment. This goes a step further than EpiModel's open `...` parameter lists, and it is what makes `sim.to_json()` and automatic results possible.

The step methods are ordinary Python operating on arrays with one entry per agent.

**Starsim 4.** The same model can now be declared as states and transitions, and then run as an ODE, chain binomial, Gillespie, or agent-based model. See [Writing models](https://starsim.org/v4/user_guide/building_writing.html):

```python
S, I, R = ss.states('S I R')
infection = S >> I @ ss.perday(0.5)*I
recovery  = I >> R @ ss.days(10)
sir = ss.Disease(infection, recovery, init_prev=0.01)
sim = ss.Sim(sir, total_pop=100_000, stop=ss.days(120), solver='ode').run()
```

## Core abstractions

| Concept | Starsim name | Notes |
|---|---|---|
| Simulation | `ss.Sim` | Owns `People`, `pars`, `Timeline`, `Loop`, `Results` |
| Everything else | `ss.Module` | Diseases, networks, demographics, interventions, connectors, analyzers are all subclasses with the same lifecycle |
| Population | `ss.People` | Agents have a permanent `uid`; `auids` are those currently alive |
| State | `ss.BoolState`, `ss.BoolArr`, `ss.FloatArr`, `ss.IntArr`, `ss.IndexArr` | Typed, labeled, per-agent arrays owned by the module that declares them. Boolean states automatically generate an `n_<state>` result |
| Transition | code in `step_state()` / `set_prognoses()`, usually via scheduled `ti_*` times | Not a data object in Starsim 3. Starsim 4 adds `ss.Transition` |
| Transmission | `ss.networks.Route`: `ss.Network` (edge-based) or `ss.MixingPool` / `ss.MixingPools` (aggregate) | The same transmission code handles both (`infect()` in Starsim 3, `transmit()` in 4), so moving from an ABM to a metapopulation form swaps the route and leaves the disease alone |
| Contact | edge in `net.edges` with `p1`, `p2`, `beta`, and optional `dur` | Bidirectional by default with per-direction beta |
| Time | `ss.date`, `ss.dur` (`days`/`weeks`/`months`/`years`/`datedur`), `ss.Rate` (`per`, `prob`, `freq`) | Typed and unit-aware; see below |
| Timeline | `ss.Timeline` | Per-sim *and* per-module; modules may run at different `dt` |
| Parameter | entry in `module.pars`, typed | May be a scalar, a `TimePar`, a `Dist`, or a callable of `(module, sim, uids)` |
| Randomness | `ss.Dist` | One RNG per distribution, seeded by hashing its name; see below |
| Intervention | Starsim 3: `ss.Intervention` subclass, with routine and campaign delivery classes. Starsim 4: `ss.vaccinate()`, `ss.screen()`, `ss.treat()` | See below |
| Cross-module coupling | `ss.Connector`, or direct changes to another module's states | Deliberately unstructured in Starsim 3. Starsim 4 adds `ss.modify()` |
| Output | `ss.Result` (a labeled, unit-aware array) in `ss.Results` | Declared, not created ad hoc |
| Execution order | `ss.Loop` | An explicit plan that can be read and changed; see below |

## Time

Time is the part of Starsim most relevant to this project, because there it had already moved from plain numbers to typed values.

There is a class hierarchy under `ss.TimePar`:

- `ss.dur` for durations: `ss.days`, `ss.weeks`, `ss.months`, `ss.years`, and `ss.datedur` for calendar-aware durations
- `ss.Rate`: split three ways, which is the substantive distinction:
  - `ss.per`: a rate over time (`ss.peryear(0.1)`, a hazard, which converts to a probability given `dt`)
  - `ss.prob`: a unitless probability attached to a period (`ss.probperyear(0.1)`)
  - `ss.freq`: a count of events per unit time (`ss.freqperyear(3)`)

Separating *rate*, *probability*, and *frequency* is unusual and worth keeping. `0.1` per year could mean any of the three, each converts to a per-step quantity by a different formula (`1 - exp(-r·dt)`, `1 - (1-p)^dt`, `r·dt`), and mixing them up is a common and quiet error. In Starsim, the value does its own conversion: `beta.to_prob(dt)`.

Durations and rates compose with dates: `ss.date` subclasses `pd.Timestamp`, so a sim can run on real calendar dates, and `ss.datedur` handles the month-length problem that pure float-year arithmetic gets wrong. A `Timeline` gives the same time as `tvec`, `tivec` (indices), `timevec`, `yearvec` (float years), `datevec` (dates), and `relvec` (relative). That is a lot of parallel forms, but output can be had in whatever form the data use.

**Per-module time steps.** Each module has its own `Timeline`, so a within-host progression module can run at `dt = 1 day` while a demographic module runs at `dt = 1 year` in the same sim. The `Loop` interleaves them by absolute time. We found nothing else in the landscape that does this, and it is good evidence that a lingua franca should not assume one global `dt`.

## Stochasticity and reproducibility

Every distribution is an `ss.Dist` object with **its own random number generator**, seeded from the sim's `rand_seed` plus a hash of the distribution's fully-qualified name. Consequences:

- Adding a module, or reordering modules, does not change the random draws of the other modules.
- Distributions can be drawn from independently and in any order without correlating.

On top of that, Starsim implements **common random numbers** at the agent level. Each agent holds a `slot`, and a per-UID draw is generated by hashing `(seed, draw index, slot)`, so agent 7's uniform for a given decision is the same in the baseline and intervention scenarios, regardless of how many other agents drew from that distribution. Paired scenario comparison therefore differences out most of the Monte Carlo noise, and small intervention effects are detectable with far fewer replicates.

This works well, and it also has limits: sampling without replacement, joint draws, and anything that cannot be written as a per-agent inverse CDF fall outside the common random numbers guarantee, and the code has to mark those paths.

`ss.MultiSim` and `ss.parallel()` handle replicates and scenarios. In Starsim 3, `ss.Calibration` wrapped Optuna. Starsim 4 replaces it with [`sim.fit()`](https://starsim.org/v4/user_guide/calibration_fitting.html).

## Populations and mixing

`ss.People` holds agents with permanent UIDs. Births add UIDs, and deaths remove them from `auids`. States are arrays covering all agents, with a view of those alive, which keeps operations over `.uids` fast.

Transmission goes through a route (`ss.networks.Route`), of which there are two families:

- **`ss.Network`**: a list of edges, regenerated or updated each step. Built-ins include random, maternal, and sexual networks, with more in `starsim.library`. Transmission goes through the edges, works out a probability for each from `beta`, `rel_trans`, and `rel_sus`, and draws.
- **`ss.MixingPool` / `ss.MixingPools`**: an aggregate force of infection between groups of agents, with a contact matrix. This is the metapopulation and age-contact-matrix form, and it uses the same transmission path (each route's `compute_transmission()`).

Because both are routes, the *same disease module* can run as a network ABM or as a mixing-matrix metapopulation model without editing the disease. This was a partial version of the paradigm independence this project wanted. It was partial because the disease was still written as agent code, so the compartmental limit came from a homogeneous population and not from solving equations.

## Interventions

Starsim 3 had a well-developed intervention vocabulary, built as a small family of classes:

- **Delivery classes**: `RoutineDelivery` (`years` or `start_year`/`end_year`, with `prob` or `annual_prob`) and `CampaignDelivery` (specific `years`, `prob`).
- **Product base classes**: `BaseTest` → `BaseScreening`, `BaseTriage`; `BaseTreatment` → `treat_num`; `BaseVaccination`.
- **Concrete combinations**: `routine_screening`, `campaign_screening`, `routine_triage`, `campaign_triage`, `routine_vx`, `campaign_vx`, `treat_num`.
- **Products** (`ss.Product`) separate *what is delivered* (a diagnostic, defined by a table of the probability of each test result given each health state, or a vaccine) from *how it is delivered*.

The split between product and delivery is the right one and should survive into the design. Eligibility was a Python function of the sim, which can say anything but cannot be saved as data, drawn, or checked. Anything the classes did not cover (a conditional cascade, a stock-limited campaign, an adaptive trigger) was a custom `Intervention` subclass.

**Starsim 4.** These classes are replaced by `ss.vaccinate()`, `ss.screen()`, and `ss.treat()`, with products `ss.Vaccine`, `ss.Diagnostic`, and `ss.Treatment`, and eligibility as a condition (`where=ss.ppl.age < 5`). See [Interventions](https://starsim.org/v4/user_guide/interventions_interventions.html).

## Execution order

`ss.Loop` collects every module's step methods into an explicit, ordered plan, in a fixed sequence: `start_step` for all modules → population rescaling, if enabled → custom modules → demographics → disease `step_state` → connectors → networks → interventions → disease `step` (transmission) → deaths → results → analyzers → `finish_step`. The plan can be printed, exported with `loop.to_df()`, plotted (`loop.plot()`, `plot_cpu()`), and changed with `loop.insert(func, label=..., before=True)`.

Being able to read and edit the order, which is implicit in the code in most frameworks, is a useful idea, and it serves the "no hidden behavior" design goal.

## Results

Results are declared (`define_results`), not created on demand. An `ss.Result` is an array with a name, label, module, shape, time vector, and unit, so plots and exports label themselves. Boolean states automatically get an `n_<state>` result (Starsim 4 names declared results after their states: `sim.results.sir.I`). `sim.to_df()` flattens everything, and `ss.Analyzer` modules collect anything else.

## Minimal model

```python
import starsim as ss

sim = ss.Sim(
    n_agents = 10_000,
    start    = '2020-01-01',
    stop     = '2021-01-01',
    dt       = ss.days(1),
    networks = ss.RandomNet(n_contacts=ss.poisson(lam=10)),
    diseases = ss.SIR(beta=ss.perday(0.05), dur_inf=ss.days(10), init_prev=0.01),
)
sim.run()
sim.plot()
```

## Worked example

A two-disease model with demographics, a connector, and an intervention, which is what Starsim was built for. This version uses the example diseases in `starsim.library`, as STIsim has not yet moved to Starsim 4. See [Connectors](https://starsim.org/v4/user_guide/interventions_connectors.html):

```python
import starsim as ss
import starsim.library as ssl

# Population and its dynamics
demog = [ss.Births(birth_rate=20), ss.Deaths(death_rate=10)]

# Two diseases on the same sexual network
network = ss.SexualNet(dur=ss.years(1))
hiv = ssl.HIV(beta={'sexualnet': ss.peract(m2f=0.0008, f2m=0.0004)}, init_prev=0.05)

S, I = ss.states('S I')
infection = S >> I @ dict(sexualnet=ss.peract(m2f=0.1, f2m=0.05))*I
recovery  = I >> S @ ss.years(1)
sti = ss.Disease(infection, recovery, init_prev=0.02, name='sti')

# The biological interaction, as modifiers: the STI raises HIV risk and transmissibility
connectors = [
    ss.modify(hiv.rel_sus,   multiply=2.7, where=sti.I),
    ss.modify(hiv.rel_trans, multiply=2.7, where=sti.I),
]

# Intervention: ART scale-up
art = ssl.ART(year=[2015, 2025], coverage=[0.0, 0.8])

sim = ss.Sim(
    n_agents      = 50_000,
    start         = 2010,
    stop          = 2030,
    dt            = ss.months(1),
    demographics  = demog,
    networks      = network,
    diseases      = [hiv, sti],
    connectors    = connectors,
    interventions = art,
)
sim.run()
```

Two things to notice. Cross-disease biology lives in the connectors, and the diseases themselves are unchanged from their single-disease form: the coupling is additive. In Starsim 3 a connector was arbitrary Python that reached into another module's state (`hiv.rel_trans[coinf] = 2.0`). That was flexible, with no structure. `ss.modify()` keeps the same coupling and declares it, so that modifiers combine and do not overwrite each other.

## The predecessor family

Covasim, HPVsim, and FPsim came before Starsim and are part of the design's history.

- **Covasim** (2020, COVID-19) established the pattern: typed per-agent state arrays, interventions as objects with `apply(sim)`, layered contact networks (household/school/work/community), and a results dict. Its interventions were plain callables or objects with a `days` and `changes` list: a simple way to vary parameters over time, some of which Starsim 3's larger set of classes arguably lost.
- **HPVsim** added multi-strain state (genotype as a state dimension), a natural-history model with within-host progression, and the screening/triage/treatment product cascade that Starsim's `BaseTest`/`BaseTreatment` classes generalize.
- **FPsim** demonstrated that the same machinery models a non-infectious process (contraceptive use, pregnancy, birth outcomes), which is why `ss.Disease` is a subclass of a general `ss.Module` rather than the root.

The lesson recorded in the generalization: each of these hard-coded its disease into the framework, and the cost of that was three near-identical codebases. Starsim's `Module` abstraction is a direct response.

## Strengths

- **Typed time.** Durations, rates, probabilities, and frequencies are distinct types that know how to convert themselves given `dt`. This is the most transferable idea here.
- **Per-module time steps**, interleaved by absolute time, showing that a global `dt` is not needed.
- **Common random numbers at agent level**, giving paired scenario comparison with a fraction of the replicates.
- **Per-distribution RNG streams**, so model structure changes do not perturb unrelated draws.
- **One `Module` type** for diseases, networks, demographics, interventions, connectors, and analyzers, which is what lets several diseases and non-disease health states be combined.
- **Routes** that unify networks and mixing pools, so the same disease runs as an ABM or a metapopulation model.
- **Declared parameters, states, and results** with labels and types: enough structure to generate results, save the model's parameters, and check inputs.
- **The execution loop as something you can read**, print, plot, and insert into.
- **A working intervention vocabulary**, with products kept separate from delivery.
- **Multi-language reach**: an R interface (`rstarsim`) over the same Python engine.

## Limitations

These are the limitations of Starsim 3, and they set the agenda for Starsim 4. A note after each says where it stands.

- **Transitions are still code.** `define_states` declares the states, but no object represents "S → I at rate β·I/N". Progression is scheduled by writing `ti_recovered` in `set_prognoses()`. So the model cannot be read as a structure, drawn, dimension-checked, or converted to ODEs automatically. *Starsim 4: `ss.Transition`, with `describe()`, `diagram()`, and `equations()`; diseases written as code keep this limit.*
- **Connectors are unconstrained.** Cross-module interaction is arbitrary Python that changes another module's state. This is why multi-disease models work at all, and it is also the largest gap in the "no hidden behavior" goal: `rel_trans[coinf] = 2.0` in one module silently overwrites whatever another module wrote. *Starsim 4: `ss.modify()` declares these effects; a connector written as code can still overwrite.*
- **Order is visible but still matters.** The loop can be read, but results still depend on whether the connector runs before or after the network updates, and nothing declares that dependency.
- **The compartmental limit is approximate.** Starsim 3 approaches an ODE by simulating homogeneous agents, not by solving equations, so it cannot produce the deterministic solution. *Starsim 4: declared models run as true ODE, chain binomial, and Gillespie models.*
- **Two ways to specify a model.** The dict/`type=` form is declarative; anything more is Python classes. Nothing leads from one to the other, and many users get stuck at that boundary.
- **A model cannot be saved as data.** `sim.to_json()` captures parameters, not model structure, so a model cannot be written out and read back. *Starsim 4: still so by choice; a model is its code, and there is [no model spec](../design/14-model-spec.md).*
- **There is a lot to learn.** Seven module categories, five array types, about 20 distributions, more than 20 time classes, three rate types, and a `Loop`. Each has a reason, but the total is a lot to hold. The AI tooling (`starsim_ai`) helps, but it does not reduce what has to be specified.
- **Time-type conversions have subtle corners**, particularly around calendar durations, `datedur` versus float-year arithmetic, and rate-to-probability conversion at large `dt`.
- **Speed is limited by Python** for anything not vectorized. Numba kernels and optional Rust copies cover the busiest code, but a custom `step()` written without care is slow.

## Implications for the lingua franca

Written when the design began. Most are now in the [design](../design/README.md).

1. **Carry the time types forward, essentially as they are.** `dur` / `per` / `prob` / `freq`, with each value doing its own conversion, are proven in use and serve the rigor goal. They also match camdl's dimensional types (`rate` = time⁻¹): two IDM designs reached the same place from different directions.
2. **Do not assume a global time step.** Per-module timelines already work. Each process should be able to declare its own time resolution, and the runtime should reconcile them.
3. **Make transitions data. This is the gap.** Declaring the *states* gave automatic results and validation. Declaring the *transitions* the same way would give diagrams, dimension checks, paradigm conversion, and generation from prose. That step is the core of what this project adds.
4. **Keep one module type, but give module interaction structure.** `ss.Module` as the single extension point is right. A connector as arbitrary change to another module's state is the wrong tradeoff for a language with no hidden behavior. The design needs a way to say *this module modifies that quantity of that module*, so that conflicts can be detected.
5. **Keep common random numbers, and state when they hold.** Paired comparison is too valuable to give up. But they hold only for draws that can be written as a per-agent inverse CDF, and that condition is noted in code comments and not enforced. With declared transitions it can be checked.
6. **Unify routes in the model description.** Transmission happens through *some* route (edge-based, pool-based, environmental), chosen separately from the disease. This lets one description run as ABM, network, or metapopulation. Generalize it so the compartmental case is exact.
7. **Take the product/delivery split, and add an eligibility expression.** Products and delivery are the right two axes. The missing third piece, eligibility as a declared condition on agent state, is also missing from EpiModel's scenario tables, so the requirement is well evidenced.
8. **Declare results, and generate the obvious ones.** Automatic `n_<state>` results save real work and guarantee consistency. With declared transitions, flows (`new_infections`, `si.flow`) can be generated the same way.
9. **Close the gap between the two ways of writing a model.** Starsim 3's dict form and class form are separate worlds. One text for a person, an AI, and the software to read only works if the simple case and the complex case are the same language, differing in how much is written.

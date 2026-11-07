---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# States and transitions

The core of the language. A model is a set of states and the transitions between them, written so that it reads like the equations.

Justified by [best-practices/model-structure.md](../best-practices/model-structure.md).

## Two spellings, one model

There is one transition class, `ss.Transition`, and two ways to write one: with operators, or by calling the class. They build the same objects, and so the same model. A whole model is likewise written one of two ways: as a call to `ss.Disease` (the function form), or as a class body (the class form).

```python
import starsim as ss

# 1. Operators (states declared first, like ingredients before the method)
beta = 0.3                       # per day (bare numbers take the sim's unit)
dur  = ss.days(10)

S, I, R   = ss.states(3)         # named from the variables when the disease is built
infection = S >> I @ beta * I    # "S goes to I at rate beta times I"
recovery  = I >> R @ dur         # a duration after @ is a mean dwell time
sir = ss.Disease(infection, recovery, init_prev=0.01)   # names taken from the variable names

# 2. Fully explicit
sir = ss.Disease(
    ss.Transition(S, I, rate=beta * I, name='infection'),
    ss.Transition(I, R, dur=ss.days(10), name='recovery'),
    init_prev = 0.01,
)

# The class form, which can also add behavior by defining methods
class SIR(ss.Disease):
    S, I, R   = ss.states('S I R')
    infection = S >> I @ beta * I
    recovery  = I >> R @ dur
```

The first reads like the equations and is the recommended form. The second is for building models programmatically, or from a language with no operators to overload (from R, `ss$Transition(S, I, rate = 0.3 * I)`). There is no third form with the states named in strings: a transition's source and destinations are always `ss.State` objects (or one of the three places outside the model, `ss.unborn`, `ss.dead`, and `ss.outside`), so the engines never see where a state came from, and nothing is inferred from a name.

## `ss.State`

```python
ss.State(
    name       = None,      # taken from the keyword or the variable name if omitted
    init       = None,      # initial fraction or count; see below
    people     = True,      # is this state people? False for a count (see States that are not people)
    rel_sus    = 1.0,       # susceptibility multiplier while in this state
    rel_trans  = 1.0,       # infectiousness multiplier while in this state
    infected   = False,     # are the people in it infected? Counted in the results infected and prevalence
    label      = None,      # human-readable, for plots and forms
)
```

A state is one concept. It is a compartment when the model runs as an ODE and a boolean per-agent array when it runs as agents; the declaration is the same.

`ss.states(3)` returns three `ss.State` objects (`ss.states(1)` returns one state, not a list). They have no names yet: a state takes its name from the variable it is assigned to, found when the module is built by the same lookup that names transitions ([01-objects.md](01-objects.md#names)), so `S I R` is typed once. Use `ss.State(...)` directly when a state needs properties:

```python
S, R = ss.states(2)
I    = ss.State(init=0.01)
V    = ss.State(rel_sus=0.2, label='Vaccinated')
```

`ss.states('S I R')` (the `sympy.symbols` idiom) returns one named state per name, in order, and `ss.State('S')` one named state. Use them when the names are wanted before the module is built, or when the lookup cannot work: states made in a loop or a comprehension, kept in a list or dict, or bound to two variables. A state has no fallback name, because a made-up name for a state would end up in results and in other modules' references. A state that cannot be matched to a keyword, a `name=`, or exactly one variable raises a `ValueError`:

```text
ValueError: state number 2 of the module has no name. It is used in ['S -> <unnamed state>', '<unnamed state> -> R'], and no variable or keyword holding it was found.
     Give the names up front: S, I, R = ss.states('S I R').
```

Inside a class body a state is declared without repeating its name, because Python tells a class attribute what it was called (`__set_name__`):

```python
class SIR(ss.Disease):
    S = ss.State()
    I = ss.State(init=0.01)
    R = ss.State()
```

At module level there is no such hook, which is why the lookup happens when the module is built: `ss.Disease(infection, recovery)` looks once among the caller's variables, and names the states, transitions, and parameters it was given from them. Nothing else looks, and a string never names a state. Picking names up from variables is convenient and slightly magical, so it is kept to this one lookup, in the constructor (and the one in `ss.Sim` that names modules, [01-objects.md](01-objects.md#names)); it stays under review in [19-open-questions.md](19-open-questions.md).

`rel_sus` and `rel_trans` on a state are properties of being in that state, so a partially protective vaccine state is two numbers on a declaration rather than multipliers threaded through transmission code. They multiply with the per-agent `rel_sus` and `rel_trans` that [07-effects.md](07-effects.md) describes.

**Which states are infected is said, not guessed.** `ss.State(infected=True)` or `ss.states('E I', infected=True)` marks a state as infected. The marked states give the disease two results, `infected` (the number in them) and `prevalence` (their share of everyone in the disease's states of people), unless the disease defines its own ([09-results.md](09-results.md#automatic-results)). A disease with no marked states has neither result: prevalence is never inferred from the transitions (decided 2026-11-06; the inference it replaced, from which states acquisitions lead to, missed states that are infected but not infectious, such as COVID's severe stages). A state named `infected` alongside other marked states (or several) is a `ValueError`, since its count and the result would have the same name; a single marked state named `infected` is the result itself. The library's `ss.SIR`, `ss.SEIR`, and `ss.SIS` mark theirs, as do the library's diseases, except where prevalence means something else (TB's is of disease, malaria's the parasite rate), which give it in the explicit form, as a result of their own. The marks are also the disease's infected states wherever else these are needed (strains, products' `detects=` and cures, dynamic rescaling); for those uses only, a disease with no marks still has them worked out from its transitions ([below](#what-counts-as-acquisition)).

A state belongs to the module whose transitions lead into or out of it. A state that appears only inside another module's rate (for example one disease's `I` in another disease's progression rate) is a reference, not a member. One set of states and transitions can build several diseases: when a disease is given states or transitions that another disease already has, they are copied (together, so they still refer to each other) with their parameters, so the second disease is independent of the first: a keyword, `pars=`, or modifier given to one does not change the other. A parameter written into new transitions of several diseases (e.g. one `R0 = ss.par(2)` for several models) is shared: it is one parameter, set by name and fitted once. Two members of one module with the same explicit name raise a `ValueError`.

**The first state** is where people are unless they are put elsewhere: where everyone starts who is given no state, where people born or added by other modules go, and where `init_prev=` seeds from. It is the one given with `ss.Disease(..., default_state='A')` (in a class body, `first = 'A'`); else the state named `S` or `susceptible` (in any case); else the one state that transmission infects people from, if there is one (`Ca` in `Ca >> P @ beta*P`); else the first state of people made, in the order the states were created (`ss.states('A B C')` makes `A` first; a class body declares its states in order; a disease built from another's states keeps their order, since the copies keep it), whatever order the transitions are given in (decided 2026-10-25, replacing "neither raises" of 2026-10-22). The transitions and the state a birth goes to are not used: `ss.birth(NB, ...)` says where births go, not where everyone starts. Taking the first state made is a guess, so `describe()` says so; the code an import writes always gives `default_state=`.

### States are declared

States are created with `ss.states(...)` or `ss.State()`, whether used in operators or passed as keywords (`ss.Disease(S=ss.State(), I=ss.State(init=0.01), ...)`): they are the ingredients list. A transition takes the states themselves; a name instead (`ss.Transition(I, 'R', ...)`) raises a `TypeError` that says to declare the states. A misspelled state is Python's own `NameError`.

### Initial conditions

Give `init` only where it is nonzero. Nobody has to write both 0.99 and 0.01.

```python
I = ss.State(init=0.01)                                    # 1% start in I; the other 99% are placed for you
sir = ss.Disease(infection, recovery, init_prev=0.01)      # the same thing, without declaring I specially
sir = ss.Disease(infection, recovery, init=dict(S=0.90, I=0.01, R=0.09))   # the whole starting distribution, in one place
sir = ss.Disease(infection, recovery, init_n=dict(I=1))    # exactly one person
```

1. `init=` is a share of people, up to 1 (`init=dict(S=1.0)` is everyone); more than 1 raises a `ValueError`, which points to `init_n=`. A whole number is still a share, so `init=dict(I=1)` (or `1` inside an `ss.by`) is everyone, with a warning to write `1.0`. `init_n=` is a number of people (`init_n=dict(I=1)` is one person), on the disease or on the state (`ss.State(init_n=10)`); a state takes one or the other. `init_prev=` keeps its own rule (above 1 a number of people, up to 1 a share). `describe()` prints which it is (decided 2026-10-22).
2. `init` and `init_n` accept the parameter ladder ([04-parameters.md](04-parameters.md)), for example `ss.by(age=[0.0, 0.02, 0.01])` (shares in `init=`, numbers of people in `init_n=`), and `init` also a function of the sim, giving a share (or one for each group), as `init_prev` does, and an expression of people's properties and parameters, `ss.State(init=1 - (A - age)/(k*age + A))`: as agents each person's own share, drawn for each agent of the first state; in a compartmental run each group's value. Its parameters are the model's, so a starting share can be fitted (TY2).
3. Whatever is left over goes to the first state ([above](#ssstate)), so giving one of `S` or `I` is enough. A value given for the first state is kept, never overwritten: then the rest go to the one state of people with no value (`init=dict(S=0.1, I=1e-4)` in an SIR starts 10% susceptible and the rest in `R`, with a note that says how many people that is: "the other 8,999 people start in R"), and if there is none or several, the values must sum to 1 (numbers of people, to the population), or it is an error that says to give the rest a state (`R=0.8999`). `init_prev=` together with `init=` for a state that `init_prev` seeds is ambiguous and an error. This applies to people only. A state that is not people ([below](#states-that-are-not-people)) starts at zero unless it has an `init`, and its `init` is always a count, never a fraction.
4. `init_prev=x` on the disease seeds a fraction `x` through its contact-mediated transition, so the seeded individuals start wherever a new infection starts (`I` in an SIR, `E` in an SEIR). A disease with no contact-mediated transition (environmental or vector-borne, below) uses `init` on a state instead. With no initial values at all, a disease with a transmission (frequency- or density-dependent) seeds 1% of people (`init_prev=0.01`, as in Starsim 3), which `describe()` marks as a guess, and `init()` prints R0 and the number infectious at the start; a state given an initial value turns the default off. A delivery that moves people into an infected state (`ss.Delivery(move=S >> I, at=...)`) beside the default seeding gets a note saying so, and how to turn the default off (`init=dict(I=0)`). `init_prev` also takes an `ss.by` (by a dimension: a share for each group; by a property of people that is not one, such as `ss.by(dict(age=[0, 15, 50], value=[0, 0.1, 0.02]))`: each person's own share, as agents), a function of the sim (a share, or one for each group), or a function that takes `uids` (`fn(self, sim, uids)`, a share for each, as agents); with a share for each agent, each is drawn on its own. Where a new infection has several destinations, the seeded are shared between them as a new infection is. `init=dict(I=ss.by(...))` by a property of people that is not a dimension is drawn for each agent likewise. Under a compartmental solver, a property that is not a dimension, or a function of the agents, raises `CapabilityError`.
5. In an agent-based run the number who start in each state is exact (rounded to whole agents), not a chance for each agent; a state given a number that rounds to no agents gets one, with a note (so a small seed never silently starts no epidemic), and with dynamic rescaling (`rescale=True`), where each agent starts as one person, `init_n=` is a number of agents; in a compartmental run it is used exactly. People who start in a state that an infection puts people into (`I` in an SIR) have been in it for the first step, as if infected in the step before (an infection is dated by the step it happens in, `ti_I = -1` for them as agents, and one slot along a conveyor): so a seeded case with a fixed stay of one step infects for one generation and is gone at the next time point, as in the Reed-Frost model.
6. `init=dict(...)` on the disease gives the starting value of several states at once. Its keys are state names and each value means what the same value would mean as `ss.State(init=...)`. It is for when the whole distribution is wanted; if the values do not account for everyone, the remainder goes where item 3 says.

## `ss.Transition`

```python
ss.Transition(
    src,                # a state, several states (a list, or a set I + R or I | R), or ss.unborn or ss.outside for an inflow
    dst,                # a state, several (branching: a dict of each and its p, or a list with p=), or ss.dead or ss.outside for an outflow
    rate   = None,      # a hazard: number, ss.per, ss.prob, any expression of states and parameters, or a function
    dur    = None,      # a dwell time: a duration or a distribution of durations (instead of rate); with on= an event, the time after it
    p      = None,      # branch probability, with a list of destinations (see Branching)
    stages = None,      # number of sub-stages used to realize the dwell time (with dur, not rate)
    where  = None,      # who it applies to: a condition, as for ss.modify (see below)
    move   = None,      # a change of level in a dimension as well as of state (05-dimensions.md)
    increment = None,   # a counter that goes up as well: its name (adds 1), or a dict of amounts, e.g. dict(parity=2) (05-dimensions.md)
    after  = None,      # a minimum stay in the source state before anyone leaves by it
    before = None,      # for a rate: it applies only until people have been in the source state this long
    acquisition = None, # whether it is an acquisition of the disease (see What counts as acquisition); worked out if not given
    on     = None,      # a trigger instead of a rate or a dwell time: a condition or an event (see A move with no wait)
    name   = None,
    label  = None,
)
```

At most one of `rate`, `dur`, and `on` is given (with `on=` an event, `dur=` is the time after it), and `stages=` goes with `dur=`. A transmission is a rate with the source of infection in it, `rate=beta * I`: there is no `beta=`. `dur=ss.days(10)` and `rate=ss.perday(0.1)` say the same thing and produce the same model.

`min_stay=` is for models that count time in a state, as EMULSION's minimum durations do (an escape is a rate times a condition on the time in the state, `rate*(X.time_in < d)`, as agents) (`weaning = ss.Transition(NB, W, rate=ss.perday(0.5), min_stay=ss.days(21))`); a litter is a birth driven by the transition, `ss.birth(NB, on=farrowing, n=10)` ([below](#births-deaths-and-migration)). A compartmental run takes `min_stay=` by a conveyor of whole steps, as it takes a fixed delay ([below](#a-fixed-delay)), except on a transmission or out of a state that splits on entry (`p=`), which need agents. A dwell time with `min_stay=` starts after the stay. A wait for an event, of this module or another, is `on=` the event (`on=preg.delivery`, or any event `ss.on()` takes): people in the source move when it happens to them, or with `dur=` that long after it (drawn for each person when the event happens, a scalar being the mean of an exponential as for any `dur=`), unless they leave the source first; so "until delivery" is `ss.Transition(X, Y, on=preg.delivery)` and "a month after delivery" adds `dur=ss.constant(ss.months(1))`. As agents only, as for `ss.on()`. A function as `dur=` (`dur=fn`) is the mean of an exponential, which warns, since each person's own time from a function is `dur=ss.constant(fn)`.

**The kind of a transition is derived, not chosen.** If the rate mentions a bare state, the transition is *contact-mediated* and that state is the source of infection; otherwise it is *spontaneous*. `describe()` prints the kind of every transition.

### What counts as acquisition

Whether a transition is an *acquisition* of the disease is a separate question from its kind, and it decides what acts on it: each person's `rel_sus` (and a state's), `ss.modify(dis.rel_sus, ...)`, a product's efficacy against acquisition (a scalar `efficacy`, [08-interventions.md](08-interventions.md#products)), and, for a disease that marks none ([above](#ssstate)), which states are infected, which `ss.treat` cures from. The rule:

- a contact-mediated transition is an acquisition;
- so is every other transition of people out of the first state that is not an outflow, whatever its rate: a bite rate (`Sh >> Eh @ a * b * Iv.n / Nh`), an EIR (`S >> I @ b * eir`), a dose of bacteria (`S >> I @ beta * W.n / (W.n + K)`), or a constant hazard;
- unless a transition out of the first state is contact-mediated, which is then the acquisition: `S >> V @ rate` alongside `S >> I @ beta * I` is a vaccination, not an infection.

`acquisition=True` or `acquisition=False` on the transition says it outright. It is the override for the cases the rule gets wrong: an importation alongside transmission, `ss.Transition(S, I, rate=ss.perday(1e-4), acquisition=True)`, which `rel_sus` and a vaccine should reduce; and a vaccination in a model with no transmission, `ss.Transition(Sh, Vh, rate=ss.perday(0.01), acquisition=False)`, which they should not. Where some states are marked `infected=True`, the infected states are those and the sources of infection, marked or not, since a state that infects others is infected (decided 2026-11-06: marking only `E` in an SEIR gave `R0()` of 0, as `I` was left out); the results `infected` and `prevalence` count the same states. Where no state is marked `infected=True`, the infected states (for products, strains, and rescaling, never for a result) are those that acquisitions move people into, the sources of infection, and the states whose count is the source of infection of a count (`Ih` in mosquitoes' `biting = Sv >> Ev @ a * c * Ih.n / Nh`). In a model where nobody is a source of infection (a staged condition, such as a cancer `none -> s1 -> s2 -> s3`), they are also every state people reach from those without passing through the first state or a state they can be in without having been infected, so all three stages are infected, not only `s1`. A test with no `detects=` or a treatment with no `where=` on a disease with no infected states raises. `describe()` marks a spontaneous acquisition as guessed, and lists the infected states when there is no transmission:

```text
             infected: Eh, Ih                                [cured by ss.treat; mark them infected=True for the results infected and prevalence]
infection    Sh -> Eh   spontaneous, an acquisition          [guessed: acquisition: out of Sh]
```

An acquisition that is not contact-mediated takes `rel_sus` as a multiplier on its rate, as a transmission does, so the bednet idiom `ss.modify(malaria.rel_sus, multiply=0.5, where=...)` and `ss.vaccinate(ss.Vaccine(efficacy=0.9))` change the Ross-Macdonald model below under every solver.

**Outside the model is one of three places**, which say what a flow into or out of the model is: `ss.unborn` is where births come from (`ss.unborn >> S`), `ss.dead` is where deaths go (`I >> ss.dead`), and `ss.outside` is where people arrive from and leave to alive (`ss.outside >> S`, `S >> ss.outside`: migration). For an amount that is not people the same three apply: mosquitoes emerge from `ss.unborn` and die to `ss.dead`, bacteria are shed from `ss.outside` and decay to `ss.dead`. They are the three instances of one class, `ss.transitions.Outside`, with a `kind`. They are named objects and not `None` because Python evaluates `None @ 0.1` before it ever sees the arrow, and `None` cannot answer; they can, so `I >> ss.dead @ 0.1` works with a bare number. None of them is a state: they have no count, no result, and no name in the model. `ss.dead` as a source and `ss.unborn` as a destination raise a `ValueError`. People who die go to `ss.dead`, not to a state `D`, which would keep them among the living (in `N`, in the population, and on networks). As agents, people who arrive from `ss.outside` arrive at any age (drawn from the population's), and those who leave to it are counted in `emigrated`, not among the dead. (Before 2026-11-06 all three were one object, `ss.null`, which said nothing about which was meant; it is gone, and the error for it names the three.)

A transition's name is used for its results, for addressing it (`sir.infection`), and in messages. How the name is found is in [01-objects.md](01-objects.md#names).

## Births, deaths, and migration in short

These constructors return an `ss.Transition`; each is a shorter way of writing one that is not plain arithmetic:

| Constructor | Is the same as |
|---|---|
| `ss.birth(S, rate=r)` | `ss.Transition(ss.unborn, S, rate=r * N.n)`, with `N` everyone alive in the module: an inflow rate is a total per unit time, so the per-capita birth rate is scaled by the population (a bare `r` is per year, and above 1 per 1,000, as `ss.Births` reads it); with no state, into the first state |
| `ss.death(I, rate=r)` | `ss.Transition(I, ss.dead, rate=r)`; with several states, a list (`ss.death([E, I], rate=r)`), and with none, `ss.death(rate=r)` applies to every state that is people |
| `ss.death(lifetable=ss.lifetable(ages, deaths))` | deaths of everyone from a life table (below) |
| `ss.immigration(S, rate=r)` | `ss.Transition(ss.outside, S, rate=r)`, a number arriving per unit time, whose agents arrive at ages drawn from the population's |
| `ss.emigration(I, rate=r)` | `ss.Transition(I, ss.outside, rate=r)`, as `ss.death()`, whose agents are recorded as emigrants (`emigrated`) |
| `ss.transfer(risk=('low', 'high'), rate=r)` | a transition between coordinates of a stratification (below) |

The arrow in `ss.transfer()` and `move=` is between the levels of a dimension, which are labels, not states.

**`beta` may differ by route and direction.** Infectiousness belongs to the disease and contact to the network, and where the pathogen transmits differently through different kinds of contact the disease gives one value per network, as in Starsim:

```python
infection = S >> I @ dict(sexual=ss.peract(m2f=0.008, f2m=0.004), needles=ss.peract(0.006)) * I
sim = ss.Sim(hiv, networks=[ss.SexualNet(), needles])
```

The keys are network names. On a network with acts the value is a probability per act (`ss.peract`, or a bare number), with a value for each of the network's directions where it has them, named from its sides (`m2f` and `f2m` on `ss.SexualNet`; `net.directions` lists them). There are no positional pairs: what `[b1, b2]` meant depended on who the network put in `p1`, so a pair raises a `ValueError`, naming the `ss.peract` spelling. A single value applies to every network. How each network uses its value is in [06-routes.md](06-routes.md).

## The operators

| Expression | Returns | Reads as |
|---|---|---|
| `a >> b` | an `ss.Transition` from `a` to `b` | "a goes to b" |
| `b @ x` | an `ss.Transition` into `b` driven by `x`, with no source yet | "into b, at x" |
| `a >> b @ x` | the complete transition | "a goes to b at x" |
| `S + I + R >> ss.dead`, `(S \| I \| R) >> ss.dead` | a set of states as the source | "any of S, I, R dies" (several sources); for whole states `\|` and `+` mean the same |
| `p * A + (1 - p) * B` | a weighted sum of states | a weighted source of infection (several destinations are a dict, `{A: p, B: None}`, or a list with `p=`) |
| `I >> {ss.dead: p, R: None} @ dur` | a transition with several destinations | "I goes to dead with probability p, else to R, after dur" (`None` is the rest) |
| `I.n` | a count | the number of people in `I`; the same number as the result `I` |
| `I.frac` | a fraction | `I.n` divided by the number of people in `I`'s module |
| `I.total` | a count | the number in `I` in the whole population; in a model stratified by place, `I.n` in a rate is the number in the same place |
| `(w*I).n` | a weighted count | each person in `I` counted by `w`, a value of theirs (a number, an `ss.by`, a property of people), e.g. `(ss.by(biting=[0.5, 1, 2])*I).n`, how much the infectious are bitten (MS3) |
| `I.n_infectious` | a weighted count | each person in `I` counted by their infectiousness (`rel_trans`, with products and modifiers on it, times the state's), e.g. what they shed (TY6) |
| `S + I + R`, `S \| I \| R` | a set of states | a source of infection or a denominator in a rate (`0.3*(Ia \| Is)` is `0.3*(Ia + Is)`); a result when given to the module by name (`infected = E \| I`); `.n`, `.frac`, and `.total` of either. Never a new state |
| `ss.unborn >> S`, `I >> ss.dead`, `ss.outside >> S`, `S >> ss.outside` | an inflow, an outflow | "born into S", "I dies", "arrive in S", "leave from S" |

**Python precedence.** `@` and `*` bind more tightly than `>>`, and equally with each other, so `S >> I @ beta * I` parses as `S >> ((I @ beta) * I)`. This works without parentheses because the transition returned by `I @ beta` forwards arithmetic (`*`, `/`, `+`, `-`) to its rate: multiplying it by `I` gives a transition into `I` at rate `beta * I`, and `S >>` then supplies the source. `(S >> I) @ beta * I` builds the same transition. Three consequences are worth knowing:

- Several sources are a set of states, `S + I + R >> ss.dead @ mu`, which needs no parentheses since `+` binds more tightly than `>>`, or `(E | I) >> R @ gamma`, which does, since `|` binds less tightly than `>>`: without them, `E | I >> R` is read by Python as `E | (I >> R)`, which raises an error that says to add the brackets. For whole states `|` and `+` mean the same set of people, as sources, as a result (`infected = E | I`), and in `.n`, `.frac`, and `.total` (decided 2026-11-06; before, `(S | I) >> D` raised). `+` is arithmetic, for weights, rates, and denominators (`N = S + E + I + R`, `0.5 * A + I`); `|` joins sets of people, as conditions do (`where=S | I`, or `S | (ss.person.age > 65)`).
- For an outflow, `I >> ss.dead @ 0.02` parses as `I >> (ss.dead @ 0.02)`, and `ss.dead` handles the `@` itself, so a bare number works there as it does after a state.
- A destination is a state, or several: `S >> I + R @ rate` cannot be parsed as intended, and raises a `TypeError` that says several destinations are a dict of each and its probability (`I >> {ss.dead: p_death, R: None} @ dur`) or a list with `p=`.
- After a dict of destinations, the value after `@` must be a Starsim object (a duration, a rate, a distribution, or an expression): `{ss.dead: p, R: None} @ ss.days(8)` works because Python evaluates it before `>>`, and the duration answers the `@` (`__rmatmul__`). A dict cannot answer it, so `I >> {ss.dead: p, R: None} @ 8` is Python's own `TypeError`: give the unit (`ss.days(8)`) or a typed rate (`ss.perday(0.125)`).

Arithmetic on a finished transition is about its flow, never its rate: `0.5 * infection` given to a disease is half of its flow (an outcome, `cases = 0.5 * infection`, [09-results.md](09-results.md)), not a second transition at half the rate, and `infection / S` is its flow per person in `S` (a result). A rate is halved where it is written, or with `ss.modify`. `>>` and `@` return new transitions, so a transition can be reused as a starting point; `@` with a second driver raises an error, and so does forwarding arithmetic to a duration (`S >> (I @ ss.days(10)) * I` raises a `TypeError`, which says to divide by the duration instead); a distribution of plain numbers times a state is a rate, so `S >> I @ ss.gamma(a=0.5, scale=3.8)*I` gives each person their own rate, as `rate=ss.gamma(a=0.5, scale=3.8)*I` does, while one of durations still raises).

### What may follow `@`

| After `@` | Means | Example |
|---|---|---|
| a duration | a mean dwell time | `I >> R @ ss.days(10)` |
| a distribution of durations | a dwell-time distribution | `I >> R @ ss.lognormal(mean=10, std=3, unit='days')` |
| an `ss.per` rate, or a bare number | a hazard per unit time (a bare number is in the sim's unit) | `I >> R @ ss.perday(0.1)`, `I >> R @ 0.1` |
| an `ss.prob` | a probability per period, converted as in [02-types.md](02-types.md) | `I >> R @ ss.prob(0.1, 'day')` |
| an expression containing a state | a force of infection | `S >> I @ beta * I` |
| an expression of counts and parameters | a hazard that depends on the model's state | `S >> I @ beta * W.n / (W.n + K)` |
| a function | called each step to get the rate | `I >> R @ my_rate` |

**A bare number after `@` is a rate**, because "at" reads as "at rate". It is never a duration: `I >> R @ 10` meaning "after 10 days" is how some people think, but `@ 0.1` and `@ 10` cannot both be guessed safely from their size. A duration after `@` is typed (`ss.days(10)`); a bare-number duration uses the keyword form, `ss.Transition(I, R, dur=10)`.

A transition between states with nothing driving it and no `p=` (`I >> S`, `ss.Transition(I, S)`) is **undriven**: only a product (`ss.Treatment(moves=)`), a delivery, or custom code moves people along it. It is not the remainder of `p=` branches out of its source. A warning is given at `sim.init()` if nothing in the sim names it (there is no flag to say it is meant: name it in a product, or leave the warning). `@ 0` is still a rate of 0. An inflow with nothing driving it raises a `ValueError`.

## Rates that mention states

There are two ways to mention a state in a rate, and they answer different questions.

- **`I.n` is how many people are in `I`.** It is a number, the same one that appears in the results as `I`. `xi * I.n` says each infectious person sheds `xi`, and nothing more is done to it.
- **A bare `I` is contact with people in `I`**: the chance that a contact is with someone in `I`. With no network that is `I.n / N`, so `beta * I` and `beta * I.n / N` are the same model. With a contact matrix or a network it is the same quantity worked out for each person from whom they actually meet, which cannot be written as one formula. That is why the bare form exists.

So write the bare state when people catch the infection from people, and `.n` when the formula needs the number itself (a reservoir, a vector, a threshold).

### A bare state means exposure

**A bare state inside a rate means "exposure to that state through the model's routes".** In `S >> I @ beta * I`, each person in `S` moves to `I` at a hazard of `beta` times their exposure to people in `I`.

- With no network given, mixing is homogeneous with one contact per unit time, so exposure to `I` is `I.n / N`. Then `beta * I` is the textbook `beta * S * I / N` and `beta` is the classical transmission rate. The user need not write `/ N`, but may ([below](#the-whole-flow)).
- When networks or mixing pools are given (`ss.Sim(sir, networks=...)`), they supply who meets whom and how often, and `beta` is per contact. The exposure of each person is then computed from their own contacts. The full definition is in [06-routes.md](06-routes.md).

The model text is the same in both cases. Exposure through a bare state is always frequency-dependent (a share of contacts); density dependence is written with the count, `beta * I.n`, which is what the importers write for a rate such as `beta * S * I`, and a rate per person that grows with a count of people is noted as density-dependent, since `I.frac` is often what was meant. `describe()` prints every rate with its bare states expanded, including the denominator, so what a rate resolved to can always be checked:

```text
infection    S -> I   transmission, from I
             rate = 0.3 × I.n / N                            [homogeneous mixing]
```

### The whole flow

Most other frameworks write a rate as the whole flow, as in the equation `dI/dt = β·S·I/N` (camdl `S --> I @ beta * S * I / N`, SimInf `S -> beta*S*I/(S+I+R) -> I`, odin, EpiModel's DCMs), while a few imply the source and the total (epydemix's mediated transitions, as the bare state does here) or name the kind (summer2's frequency and density flows). Both are read. **A rate with the transition's source as a factor is the whole flow**: it is divided by the source, and the other states in it are numbers of people. Divided by the total of the module's states that are people (`N = S + I + R`), they are a share, which is contact with people in them through the routes, as for the bare state; otherwise they are the numbers themselves. So the two common forms are:

| | Per person | Whole flow |
|---|---|---|
| Frequency-dependent, `dI/dt = β·S·I/N` | `S >> I @ beta * I` | `S >> I @ beta * S * I / N` |
| Density-dependent, `dI/dt = β·S·I` | `S >> I @ beta * I.n` | `S >> I @ beta * S * I` |

Each pair is the same model, with the same results. Any transition can be written either way (`I >> R @ gamma * I` is `I >> R @ gamma`). `describe()` says when a rate was written as the whole flow, and what it is per person:

```text
infection    S -> I   transmission, from I
             written as the whole flow, beta × S × I / (S + I + R), so per person in S: beta × I
```

Several sources are a sum of exposures: `S >> E @ beta * (I + 0.5 * A)` says asymptomatic people are half as infectious, and `S >> I @ beta * I + beta_vax * I_vax` gives each source its own coefficient. A rate may multiply the exposure by anything that contains no bare state, such as a parameter, a seasonal curve, or a count (`beta * I * (1 - 0.3 * H.frac)`). The rate MUST be linear in the bare states, because exposure through a network is a sum over contacts; `I ** 2` or `I / (I + K)` raises a `ValueError`, which says how to write a rate per person or as the whole flow.

Three things follow from the rule and are worth stating:

- **A rate with no state in it is not transmission.** `S >> I @ beta` is a constant hazard, like `I >> R @ gamma`: everyone in `S` moves to `I` at rate `beta` whether or not anyone is infectious. It is legal and it is spontaneous. Transmission is written with its source, `S >> I @ beta * I`; nothing supplies the source for it.
- **A bare state must be people.** There is no contact with a reservoir to work out, so `S >> I @ beta * W`, with `W` a state that is not people, raises a `ValueError`, which suggests `W.n`.
- **A sum of states is not a state.** `N = S + I + R` makes no new state and nobody is "in" `N`. In a rate it is a source of infection (bare) or a denominator (`N.n`); given to the module by name it is a result ([09-results.md](09-results.md)).

States that are a source of any contact-mediated transition are marked infectious.

### `I.n` is a count, `I.frac` a fraction

`I.n` is the plain number of people in a state (the number represented, after any scaling from `n_agents` to `total_pop`), and `I.frac` is that number as a fraction of the module's people. For a state that is not people, `W.n` is simply its value. A sum of states has them too: `N = S + I + R` then `N.n`. Rates may be arbitrary expressions of counts and parameters, and they are used literally, with no routes involved:

```python
S >> I  @ beta * W.n / (W.n + K)      # environmental: saturating dose-response to a reservoir W
Sh >> Eh @ a * b * Iv.n / Nh          # vector-borne: bites per person from infectious mosquitoes
```

NumPy's elementary functions of an expression are expressions too, so a rate can saturate, switch, or ramp without becoming a function of the sim: `np.minimum`, `np.maximum`, `np.clip`, `np.exp`, `np.log`, `np.sqrt`, `np.abs`, `np.sin`, and `np.cos`. For example, MEmilio's extra risk from symptomatic people once testing and tracing is overwhelmed is `0.35 - 0.1 * np.cos(np.pi * np.clip((0.455 * INS.n - 35) / 140, 0, 1))`. A transition for some people only takes `where=`, a condition as for `ss.modify` ([07-effects.md](07-effects.md#conditions)): `ss.Transition(J, A, rate=ss.perday(1), where=ss.person.age > 1)`. It is the same as a modifier that sets the transition's rate to 0 for everyone else; on a branch chosen with `p=` it changes the branch's probability instead, and the other branches share the rest ([Branching](#branching)). A comparison is 1 or 0, so a rate can stop at a capacity: `I >> Q @ 0.5 * (Q.n < 20)`. A bare state may not appear inside a function or a comparison, since the force of infection must stay linear in the infectious.

People's properties are expressions too. `ss.person.<name>` is each person's value of a property (`ss.person.age`, `ss.person.urban`), and a condition in a rate is 1 for the people it holds for and 0 for the others, so a regression is an ordinary expression: `start = none >> on @ ss.peryear(1) * expit(b0 + b_urban*ss.person.urban + 0.5*(ss.person.age > 30))`, with SciPy's `expit` (`from scipy.special import expit`) beside the NumPy functions above. Its coefficients are parameters that `describe()` prints, `fit()` fits, and `ss.modify` reaches during the run. As compartments, a property that is a dimension is each group's level (a binned one, the bin's middle), and a condition is the share of the group it holds for (on states, of the people in the state the flow leaves). A property that is not a dimension is each person's own, so `'auto'` runs the model as agents, with a note, and an explicit compartmental solver raises `CapabilityError` naming `stratify()`. An unknown name is a `KeyError` when the sim is built. A condition made only of states joined by `|` (`0.3*(Ia | Is)`) is still an error: it almost always meant a sum, `0.3*(Ia + Is)`.

This is how environmental and vector-borne transmission are written. There is no separate route kind for them and no separate class for the reservoir or the vector; worked examples are under [States that are not people](#states-that-are-not-people) below. A transition whose rate uses only counts is spontaneous: every member of the source state has the same hazard.

## Dwell time

A scalar duration means an exponentially distributed dwell time with that mean, not "exactly 10 days". That is what every ODE means; here `describe()` prints it:

```text
recovery   I -> R   time in I ~ exponential(mean = 10 days) [guessed: scalar duration]
```

Any `ss.Dist` of durations is accepted:

```python
I >> R @ ss.days(10)                                   # exponential
I >> R @ ss.erlang(k=3, mean=ss.days(10))              # Erlang with 3 stages, mean 10 days; the same as ss.gamma(a=3, scale=ss.days(10 / 3))
I >> R @ ss.lognormal(mean=10, std=3, unit='days')    # lognormal
I >> R @ ss.weibull(c=2, scale=ss.days(11))
```

How it is realized follows from the solver:

| Dwell time | As agents | As compartments |
|---|---|---|
| exponential (scalar duration or a rate) | sample a time per agent when they enter the state, and schedule the move | one rate, `1 / mean` |
| `ss.gamma` with an integer shape `k` | sample | `k` generated sub-stages at rate `k / mean`, exact |
| `ss.constant`: a fixed delay | sample (every agent the same) | a conveyor of whole steps, exact at each step ([below](#a-fixed-delay)) |
| any other distribution | sample | Erlang sub-stages matched to its mean and variance, with a one-line note |

When the distribution has no exact compartmental form, a compartmental run uses Erlang stages matched to the mean and variance (`k = round((mean / std)²)`, at least 1) and says so in one line (`note: recovery has a lognorm_ex dwell time, approximated by 11 Erlang stages (mean 10 days kept; std 3.02 instead of 3 days)`). This is the one approximation `solver='auto'` makes without being asked: a non-exponential dwell time does not by itself make a model agent-based. A user who wants the distribution sampled exactly asks for `solver='abm'`. `approximations='allow'` hides the note. With `approximations='error'` nothing is approximated: `'auto'` runs the model as agents, where the dwell time is sampled directly, and an explicit compartmental solver raises `CapabilityError`. The approximation policy as a whole is in [12-backends.md](12-backends.md).

**Several non-exponential dwell times out of one state** have a compartmental form when each is for other people, by `where=` (durations by sex: `ss.Transition(A, R, dur=ss.lognormal(...), where=ss.person.female)` and another `where=ss.person.male`): each gets its own stages, and each group enters those of the one it has, worked out from the groups the `where=` holds for when the run starts. Two for the same people (with no `where=`, e.g. clearance against seeking care) race: a compartmental run keeps a compartment for each combination of their Erlang stages (k1 × k2 for two, up to 400 per group), a stage of one clock moves people along its own axis, and its last stage is its exit whatever stage the other is in, which is the exact form of the race between the Erlang dwells (the share leaving by each, and the time to leave, match the integral). A fixed delay alongside another non-exponential dwell time, `min_stay=` on the state, or two with the same `where=` have no compartmental form yet: `solver='auto'` runs the model as agents, and a compartmental solver raises `CapabilityError` naming them. A distribution whose parameters differ by group (`ss.lognormal(mean=ss.by(sex=...), std=...)`) is one dwell time with stages for each group.

**The user can say how explicitly** with `stages=k`: a compartmental run uses `k` sub-stages with the given mean, and agents draw their dwell time from the Erlang distribution with `k` stages and that mean, which is the way to make an agent-based and a compartmental run of a model match.

```python
I, R = ss.states('I R')
ss.Transition(I, R, dur=ss.days(10), stages=3)
```

Generated sub-stages appear in `describe()` and are summed in results, so `I` means what the user meant. `ss.erlang(k=3, mean=ss.days(10))`, `ss.gamma` with an integer shape, and `stages=3` give the same model and the same results.


### A fixed delay

`ss.constant` is a fixed delay, as odin's `delay()` and a reporting lag are: `onset = E >> I @ ss.constant(ss.days(14))`. As agents, everyone's exit is scheduled 14 days after they arrive, rounded to whole steps (see below). A compartmental run does not approximate it by stages (a fixed delay is the one dwell time whose Erlang stages never converge: 200 of them are stiff and still 1.6% off); it keeps a conveyor of whole steps instead. With a delay of `K` steps, the state has `K + 1` compartments, one for the people who arrived in each of the last `K` steps and one for those who arrived during this one; at the end of each step everyone moves along one, and those who have been there `K` steps leave in the next step. The chain-binomial solver lets them leave at its start, once the step's rates are worked out from the people as they were, as agents' scheduled exits come first; Gillespie and tau-leaping, at its middle; and the ODE, at a constant rate over it. So the number in each compartment at each time point is exact for a delay of whole steps, the ODE's release within a step is exact to second order, and the solvers agree with agents step for step. The other exits of the state (deaths, aging) act on everyone in it; in the ODE they act on those leaving until they leave, whose release over the step is lowered to the share those exits leave (h·dt/(exp(h·dt) − 1) for a total rate h), so that a delay of K steps keeps exp(−h·K·dt) of its people, as agents and the stochastic solvers do (it kept exp(−h·(K − ½)·dt): MA7's 12-day incubation with mortality 0.1 a day gave 5,279 infectious mosquitoes for the exact 5,020). Nothing in a conveyor has a rate, so it is not stiff: odin's 14-day SEIR runs in 8 ms and agrees with odin's delay differential equation within 0.25% of the peak at a step of a day (0.06% at half a day).

A delay that is not a whole number of steps is rounded to the nearest one here, with a note. As agents, every dwell time (drawn or fixed, and a delay after an event or before a transfer) is rounded to whole steps at random, up or down in proportion, so its mean is kept: 0.2 steps is no steps for 80% of people and one step for 20%, on the module's own random numbers (FP55, decided 2026-10-22; rounding to the nearest step made a dwell under half a step end in the step it began, for everyone). An explicit `dur=0` is no steps, an exit in the step people enter. The people who start in the state are taken to have just arrived, as agents are. `R0()` takes the conveyor as stages whose stays add up to its length. A minimum stay (`min_stay=`) is a conveyor of the same kind: a transition with `min_stay=` acts on the people who have been in the state that many whole steps or more.

## Branching

One source, several destinations, as a dict of each destination and its share (`None` for the rest):

```python
S >> {Lfast: p, Lslow: None} @ beta * I
I >> {ss.dead: p_death, R: None} @ ss.days(8)                 # a death or a recovery, after one dwell time
ss.Transition(I, {ss.dead: p_death, R: None}, dur=ss.days(8))   # the same, written out
ss.Transition(S, [Lfast, Lslow], p=[p, 1 - p], rate=beta * I)   # two lists, for destinations that are generated
```

The two lists (`[ss.dead, R]` and `p=[p_death, None]`) still work, and suit destinations made in a loop; the dict keeps each destination beside its share. A branching transition is one named transition with several destinations. Its result is the total flow, and each destination has a flow of its own, `<transition>.<state>` (`res.cin.X`; `res.outcome.dead` for a branch to `ss.dead`; [09-results.md](09-results.md#automatic-results)), which is also the destination's name as an event and as the target of a modifier (below); separate transitions with `p=` (below) each have their own flow too.

**`p` is always a branch probability**: the chance of taking this branch. Separate transitions with `p=` are decided when the person enters the source state (or, for a contact-mediated transition, when they are infected), and each then has its own dwell time. One transition with several destinations is decided when the person leaves, from the one dwell time drawn: its `p` is evaluated then, so a time series or a function of the sim sees the person as they are when they leave (an age-dependent share uses their age at exit). A per-period probability that governs timing is not `p=`; it is a typed rate, `rate=ss.prob(0.1, 'day')`.

**A branch probability given the time in the state.** `P.time_in` is the time each person has spent in `P` ([clocks](#events-and-clocks)), as `P.n` is the number in it: an expression, so it prints and fits. In `p=` of a transition with several destinations out of `P` it is the time the person spent there when they leave (`ss.Transition(P, {C: f(P.time_in), R: None}, dur=...)`: in HPV, the chance of CIN rises with the time infected), and in the rate of a transition out of `P` it is a hazard that depends on the time in the state (`P >> R @ k*P.time_in`). Separate transitions with `p=` are decided on entry, when no time has passed, so `p=` there with a clock of the state raises `CapabilityError`, which names the one-transition form. It is whole steps, as agents only: `solver='auto'` runs a model that reads it as agents, and a compartmental solver raises `CapabilityError` (decided 2026-10-20; Erlang stages or fixed delays are the compartmental forms). In a function that takes `uids`, `hpv.P.time_in[uids]` reads the same time. (`P.dwell`, which said the same, is gone.)

- `p` accepts everything a parameter accepts ([04-parameters.md](04-parameters.md)): a constant, `ss.by(age=[...])`, a time series, or a function of the sim returning one value per agent or per group. In real models the split is rarely two constants.
- The probabilities out of one state MUST sum to 1. One entry MAY be left out (`None` in a dict or a list, or one transition with no `p=`) and gets the remainder, which `describe()` marks as guessed; with two destinations a single value is the first one's probability. A constant split that does not sum to 1 raises a `ValueError`. `ss.dead` may be one of several destinations (a death or a recovery, decided by one draw); `ss.outside` as one of them is not yet supported and raises `ss.CapabilityError` (leaving is a transition of its own, `emigration = I >> ss.outside @ rate`), and `ss.unborn` is never a destination. A list of one destination with `p=[1]` (or `p=[None]`) is a plain transition, not a branch: `ss.Transition(I, [F], p=[1.0], rate=r)` is `ss.Transition(I, F, rate=r)`, and several of them out of one state compete as hazards.
- Each entry of `p=` is one destination's probability. A function is one entry, for one destination (a function giving a row for several destinations, normalized, is gone: give one function for each).
- A modifier on a branch ([07-effects.md](07-effects.md)), a vaccine's efficacy against it, and `where=` on it change its probability, and the other branches share the rest; they do not change how long people take to leave. One destination of a transition with several is named `'<transition>.<state>'` (`ss.modify('hpv.progression.C', multiply=0.5)`, or `efficacy={'progression.C': 0.5}`), and a modifier or efficacy on it changes that destination's probability in the same way; one on the transition itself scales its rate. `ss.dead` and `ss.stay` among the destinations are named `'<transition>.dead'` and `'<transition>.stay'` and are branches like the states: a modifier, efficacy, or `adjust=` on one of them scales its probability, and the destinations with none, `ss.dead` and `ss.stay` included, share what is left in proportion to their own (decided 2026-11-06, when a modifier on one state's branch took every death away).

**Each branch may have its own dwell time**: decide the branch on entry, then wait. Write two transitions out of the same state, each with `p=` and its own `dur=`:

```python
S, I, H, R = ss.states('S I H R')
ss.Disease(
    infection = ss.Transition(S, I, rate=0.05 * I),
    severe    = ss.Transition(I, H, p=0.1, dur=ss.days(5)),
    mild      = ss.Transition(I, R, p=0.9, dur=ss.days(10)),
)
```

The rule that covers every case: **separate transitions out of one state that carry `p=` split on entry; one transition with several destinations splits when it is taken; transitions that carry only rates compete as hazards** ([below](#competing-hazards)). They can be mixed: a death hazard out of `I` competes with whichever branch the person was assigned. In a compartmental run, a split with per-branch dwell times is realized as one generated sub-compartment per branch, summed in results, and a split when taken divides the exit flow. A branch with `p=` and no `rate=` or `dur=` happens immediately on entry, in the same step, under every solver, and `describe()` says so. So do its consequences: someone who enters a state with an immediate exit moves on at once, and moves with no wait cascade within the step until nobody moves. A cycle of them raises a `ValueError`, naming it.

Exits are scheduled when a person enters a state: as agents, the branch is drawn, its dwell time sampled, and the time of the exit set at the moment of entry (by a transition, by an intervention, or at placement), so `p=` on entry is evaluated then.

A junction (a zero-duration pseudo-compartment that only splits its inflow) is not needed and is not part of the language.

### A move with no wait: `dur=0` and `on=`

**`dur=0` is "immediately".** So is `dur=ss.constant(0)` (Starsim 3's zero latency). A transition with `dur=0` is taken in the step people arrive in its source: with several destinations, `p=` splits them, as for any branch (`ss.Transition(presenting, {mild: 0.8, severe: None}, dur=0)`, a junction that holds nobody). With `on=` a condition, it is taken as soon as the condition holds for someone in the source, including on arrival (`ss.Transition(I, R, on=others.cancer)`); `where=` only restricts who it applies to. A transition with `on=` an event is immediate for the people of the event, with `p=` the share of them who move (`ss.Transition(infected, resistant, on=drug.failed, p=0.05)`). Nothing else is immediate: a split with `p=` and no rate or duration keeps raising a `ValueError`, which says to give it `dur=0` (the care cascade's decision 17, option a; if `dur=0` is written often, option b, any such split immediate, is the fallback). `describe()` says "immediately".

Under every solver an unconditional `dur=0` exit has no compartment and no rate: the flows into its source are passed to its destinations by the shares of `p=`, both flows recorded, so `X >> R` with `dur=0` costs nothing (the `ss.perday(1e6)` idiom took 48 s for 30 days as an ODE, against 0.08 s). A conditional one (`where=`, or `on=` a condition or an event of the same module) is, as agents, checked after every move in the step; under the compartmental solvers the share of each source compartment and group it holds for moves at the end of each step, after the step's flows, so people an intervention puts in the source between steps move at the end of the next step. `on=` a condition or an event of another module, or a function, is agents only (`solver='auto'` picks agents), except an outcome of a delivery, which moves its people as it happens under every solver.

## Events and clocks

**Events** are what happens to someone at a moment: a transition (`infection`), one branch of it (`outcome.to(D)`), and entering or leaving a state or a set of states (`I.enter`, `(E | I).exit`). Entering a set means arriving from outside it, by a transition, an inflow, or placement; a move within the set is not entering it. An event is a condition, true for the people it happened to from the moment they moved until the same point in the next step (a move made by an intervention is news from the next step), so it can be used in `where=`, `eligible=`, and `on=`; in a running sim, `event.uids` are those people. As compartments, a transition and a branch are events (a fraction of the state they arrived in); entering or leaving a state is not yet (`ss.CapabilityError`).

**Clocks** are elapsed time, as expressions:

```python
EL.time_in                  # time since this person last entered EL
(EL | LL).time_in           # since they entered the set from outside it: moving from EL to LL does not reset it
falling.progress         # the share of the scheduled dwell time in falling that has elapsed, from 0 to 1
```

A clock is a duration in the sim's unit (`EL.time_in / ss.years(1)` is a number of years), and works in `rate=`, `p=`, modifier amounts, and conditions (`where=`, `eligible=`): `ss.modify(syph.rel_trans, multiply=0.5**(latent.time_in/ss.years(1)), where=latent)`. In the `p=` of a transition out of `X`, taken when people leave, `X.time_in` is the dwell just completed. A clock is NaN for anyone outside its states, and its use is checked when the model is built: a transition that reads a clock must leave from its states, and a modifier whose amount reads one must have a `where=` inside them (a `ValueError`; a `where=` that is a function is checked when it runs). `.progress` needs a dwell time scheduled on entry, so a state with only rates out of it raises a `ValueError`. A clock of a set has to be made before the sim, which keeps the time each person entered the set. Clocks are agents only (decided 2026-10-20): `solver='auto'` runs a model that reads a clock as agents, and a compartmental solver raises `ss.CapabilityError`.

## Many-to-one

```python
S + I + R >> ss.dead @ mu     # one transition, several sources; (S | I | R) >> ss.dead is the same
ss.death(rate=mu)               # every state that is people, to outside the model
```

A transition with several sources is one named transition, whose result is the total flow from all of them. The same movement for every combination of a stratification (many-to-many) is `ss.transfer`.

## Births, deaths, and migration

```python
S, I, R = ss.states('S I R')
ss.birth(S, rate=ss.peryear(0.02))            # crude birth rate: 0.02 per person per year, into S
ss.death(I, rate=ss.peryear(0.1))             # disease-specific mortality
ss.death(rate=ss.peryear(0.01))               # background mortality from every state
ss.immigration(S, rate=ss.peryear(500))       # 500 people arriving per year, into S
ss.emigration(rate=ss.peryear(0.01))          # people leaving, from every state

N = S + I + R
ss.unborn >> S @ ss.peryear(0.02) * N.n       # operator forms of the first two
I >> ss.dead @ ss.peryear(0.1)
ss.outside >> S @ ss.peryear(500)             # and of the last two
ss.Transition(S | I | R, ss.outside, rate=ss.peryear(0.01))
```

- An outflow rate is per person in the source state, like any other transition.
- An inflow has no source state to be "per person" of, so in the operator and explicit forms its rate is the total number entering per unit time. `ss.birth(rate=r)` is the epidemiologist's crude birth rate and is shorthand for `r * N.n`, where `N` is everyone alive in the module. A bare number given to `ss.birth(rate=)`, or to `ss.death(rate=)` of everyone (and so `ss.emigration(rate=)` of everyone), is read as `ss.Births` and `ss.Deaths` read theirs (one function, `ss.demographics.bare_rate()`): per year, and per 1,000 people if above 1 (warning between 0.1 and 1, or above 1,000, that it could be either), with a warning saying how it was read; `ss.birth(rate=30)` is `ss.birth(rate=ss.peryear(0.03))`. A typed rate is per person and is not rescaled; above 1 per person per year it warns, giving the per-person value (e.g. `ss.peryear(0.03)` for 30 per 1,000). A death from given states (`ss.death(I, rate=0.1)`) is a rate like any other, and a bare number there is in the model's unit.
- `ss.immigration()` and `ss.emigration()` are the transitions from and to `ss.outside`, an inflow and an outflow like any other in a compartmental run. As agents, immigrants arrive at ages drawn from the population's age distribution (people born with `ss.birth()`, from `ss.unborn`, are newborns), and emigrants are recorded as having left (`sim.results.emigrated`) rather than as having died. A transition written with `ss.outside` (`ss.outside >> S @ r`, `S >> ss.outside @ r`) is the same as these, so the place says which it is, not the constructor.
- `ss.death(lifetable=ss.lifetable(ages, deaths))` takes deaths from a life table (`deaths` is a life table's d(x)) instead of a rate: as agents, each person's age at death is drawn from it once, given their age; in a compartmental run, which then needs a stratification by age, it is a death rate for each age group. The table is stationary: an age at death drawn once cannot follow a trend. Life tables by year and sex are `ss.Deaths(lifetable=...)`, the module written as code (agents): one table, `dict(female=..., male=...)`, or either for each year from which it holds (`{2000: ..., 2010: ...}`), each read as the death rate of each of its age bands, so deaths follow the table of the year and each person's sex and age.
- A death rate (or any rate) by single year of age need not match the model's age groups: `ss.by(dict(age=np.arange(100), value=[...]))` gives each band by its lower edge, read for each person's own age as agents. As compartments each age group needs one value, so bands that split a group raise `CapabilityError` (and `solver='auto'` runs agents); bands coarser than the groups, or the same, are exact. A function whose numbers are in a unit is written with the unit, `ss.peryear(fn)`, which is `ss.peryear(1) * fn`.
- As agents, people age in a model whose births are declared, as they do with demographics modules.
- A birth driven by a transition, `ss.birth(NB, on=farrowing, n=10)`, makes children each time a parent goes through it, including twice in a step (a dwell shorter than a step) and a transition out of the model (to `ss.dead`, e.g. a maternal death at delivery). Newborns enter their states as anyone else does: entering events and the attributes they set fire (as they do for people born of a module written as code, and for people placed at the start, who enter their state by placement), their traits (`ss.attr(dist)`) are drawn, and an exit due at once (`dur=0`) is taken in the step they are born.
- People moved into a state by code before the start (`ss.move()` in `init_post()`) went along no transition, so no history is filled in for them: attributes recorded on the transitions into that state stay as they are (decided 2026-10-22).
- `ss.Pregnancy`'s events for other modules: `preg.delivery` happens to the mother, and to her fetuses (when they are agents) before they are born, so a fetal death `on=preg.delivery` is a stillbirth; `preg.birth` happens to the newborns, so a neonatal death is `on=preg.birth`. Infant mortality is its declared transition `infant_mortality`, at `infant_rate` (0 by default) for children under 1, which `ss.modify()` and `ss.by()` adjust like any other (decided 2026-10-22). Starsim 3's coded pregnancy is ported by rewriting onto these seams; a subclass that overrides one of its methods raises.
- In an agent-based run, removals are requested during the step and carried out at its end (Starsim's `request_death`), so a person who dies this step is still visible to the modules that run after the disease ([10-execution.md](10-execution.md)).

Births, deaths, and migration of everyone are declared once for the population, in `ss.Sim(demographics=[ss.birth(rate=...), ss.death(rate=...)])`: there they run under every solver and add and remove the same people from every disease. The sim makes them transitions of one disease (the first, or the one whose state a birth is into, `ss.birth(sir.S, rate=...)`; with no state, people are born into each disease's first state), whose people are everyone's: as agents the diseases share the people, and in a compartmental run with several declared diseases their states are tracked jointly (a crossing, see [07-effects.md](07-effects.md)). Births or deaths of everyone declared in more than one disease are a `ValueError`, since they would count people twice. `demographics=True` is births and deaths at 20 and 10 per 1,000 people per year, declared the same way; Starsim 3's `birth_rate=` and `death_rate=` (per 1,000, which made the model agents) are removed. With no declared disease, the sim adds a declared module of everyone alive (`population`, with the one state `N`) to hold them, so they are a declared model like any other: `solver='auto'` chooses for them as it would for a disease (compartments, unless something needs agents, such as `n_agents=` or a life table with no stratification by age), and their results are `sim.results.population` (`N`, `births`, `deaths`) as well as the sim's `n_alive` and deaths (decided 2026-10-25; before, they ran as `ss.Births` and `ss.Deaths` unless a compartmental solver was named). `ss.Births` and `ss.Deaths` stay as modules for demography from data (by year, age, and sex), as agents.

## `ss.transfer`

Movement between coordinates of a stratification ([05-dimensions.md](05-dimensions.md)) without a change of disease state:

```python
ss.transfer(risk=('low', 'high'), rate=ss.peryear(0.1))                       # named coordinates: a pair, from and to
ss.transfer(vaccinated=True, rate=ss.peryear(0.2))                            # boolean coordinate: the target value
ss.transfer(resistance=('DS', 'MDR'), rate=ss.peryear(0.05), states=['on_treatment'])
```

- The keyword is the stratification; the value is a pair of its coordinates, `(from, to)` (an arrow string raises). For a boolean coordinate write the value people move to.
- A transfer that happens all the time is part of the model: it is given to the disease as a keyword (`ss.Disease(..., vax=ss.transfer(vaccinated=True, rate=...))`) or to `stratify()`.
- A transfer applies to **every disease state at once** unless `states=[...]` restricts it. The third line is acquired drug resistance, which happens only while on treatment.
- It takes `rate=`, `dur=`, and `p=` with the same meanings as any transition, and any of them accepts the parameter ladder.
- A boolean coordinate that the model does not have yet is created, with everyone starting `False`, and printed by `describe()`. A named stratification that does not exist raises a `KeyError`.

Vaccination, aging between groups, risk-group turnover, and migration are all transfers, which is why a disease model does not have to mention vaccination to be vaccinated against. Delivering a transfer to a target coverage, to an eligible group, or in particular years is an intervention; see [08-interventions.md](08-interventions.md).

## Functions in any slot

Imperative transitions are fine. Any slot (`rate=`, `dur=`, `p=`, and anything after `@`) accepts a function:

```python
def severity(sim):                       # works on agents and on age groups
    return 0.01 + 0.1 * (sim.people.age > 65)

def clearance(self, uids):               # agent-only: uses a per-agent attribute
    return 0.2 / (1 + self.viral_load[uids])

S, I, H, R = ss.states('S I H R')
ss.Disease(
    infection = ss.Transition(S, I, rate=0.05 * I),
    course    = ss.Transition(I, {H: severity, R: None}, dur=ss.days(7)),
    discharge = ss.Transition(H, R, rate=clearance),
)
```

- A function takes any of `self` (the module), `sim`, and `uids` (the agents it is asked about), by name, in any order (`ss.utils.fn_args()`, `call_fn()`), as distributions' functions already did: `S >> I @ (lambda self, sim: self.pars.beta * self.I.n / sim.people.n_alive)`. This holds in every slot that takes a function: rates, `dur=`, `p=`, parameters, conditions (`where=`, `who=`, `eligible=`), coverage, `init_prev=`, and waning (which may also take `t`). A function whose arguments have other names is called by position, as before: `fn(s)` with the sim, `fn(s, u)` with the sim and the agents, `fn(m, s, u)` with the module, the sim, and the agents (decided 2026-11-06).
- It returns a scalar or an array with one value per member of the population it is shown. A function that takes `uids` (`ss.utils.takes_uids()`) is for agent-only logic and returns one value per requested agent; it runs as agents only, and a compartmental run raises `CapabilityError` naming it.
- A method can be a rate: a method named in the class body (`infection = S >> I @ custom_infection`, after `def custom_infection(self, sim): ...`), or `rate=self.custom_infection` in `define_transitions()`; either way it is called with the disease as `self`, so it reads `self.pars` and its states.
- A bare number returned from a function is in the sim's unit; typed values are converted as usual.

**The try-it rule.** A function is tried on whatever the solver provides. In an agent-based run it sees agents. In a compartmental run it sees groups: `sim.people` has one row per stratum, an attribute that is a stratification (`age`, `sex`, `vaccinated`) has one value per group, and state counts are available as `I.n`. If the function only uses things that exist in both (state counts, parameters, time, stratification coordinates), it works in both. If it reaches for something agent-only (`uids`, or an attribute that is not a stratification), the compartmental run stops with `CapabilityError` naming the function and what it asked for:

```text
CapabilityError: the function "clearance" cannot run with solver="ode".
     It takes uids, which exist only per agent. Run with solver="abm".
```

A function that fails on groups for any other reason raises its own error, naming it, rather than being taken to need agents.

There is no static analysis of the function and no declaration of what it reads. The library tries it and reports what happened. `solver='auto'` does the same trial at build time and chooses agents if the function does not work on groups.

## Custom per-step behavior

A plain function passed as a keyword to a module is called once per step, after that module's transitions:

```python
def seed_cluster(sim):
    sir = sim.diseases.sir
    if sim.ti == 30:                     # on step 30, five susceptible people become infectious
        ss.move(sir.S, sir.I, n=5)

sir = ss.Disease(infection, recovery, seeding=seed_cluster)
```

The function is called with the sim, after the module's transitions, every step; there is nothing to wrap it in. Written with `ss.move()` ([below](#moving-people-from-code)), it runs under every solver; written with each agent's state (`sir.S.uids`), only as agents. To pass a function as a named *parameter* rather than as behavior, wrap it in `ss.par(fn)`.

The other way is the class form: subclass `ss.Disease`, declare the states and transitions in the class body, and override `step()` ([01-objects.md](01-objects.md#the-class-form)). A disease written entirely as code, with per-agent arrays and no declared states, is also an `ss.Disease` (or an `ss.AgentDisease`, for one transmitted over the sim's networks, Starsim 3's `ss.Infection`), and runs as agents; one class can mix declared parts and coded ones ([01-objects.md](01-objects.md#the-class-form)). Both are ordinary, supported ways to write a model. What they cost is the choice of solver: custom code runs as agents unless it happens to work on groups, by the same try-it rule, and `describe()` and `solvers()` say which.

### A transmission written as code

A declared disease can write any of its transmissions (its contact-mediated transitions) as code, by defining `transmit(self, transition)` (`ss.Disease.transmit()`), and keep everything else declared. The engine calls it once a step for each transmission, and moves the people it gives along that transition, counted in its flow; `super().transmit(transition)` is exactly what the solver would have done, so the method can add to it or take from it:

```python
class Imported(ss.SIR):
    def transmit(self, transition):
        new = super().transmit(transition)
        if self.sim.solver == 'abm':                       # and 2 imported cases a step
            return new | self.sim.people.auids[self.S.raw[self.sim.people.auids]][:2]
        return new + 2/self.sim.groups.n_groups
```

- As agents it returns the UIDs of the new cases; those not in one of the transition's source states are not moved, and with several sources each case leaves the one it is in.
- As compartments it returns the number infected in each group (or one number), taken from the source states in proportion; `super()` gives the expected number at the start of the step. Anything that needs individuals raises `CapabilityError` in a compartmental run.
- Under the ODE the number is taken once a step, at its start, as a move of that many (as `ss.move()` from code is), so that transition is integrated to first order in `dt`, and a note says so. A rate that is a function (`S >> I @ (lambda self, sim: ...)`) keeps it exact, and is the better form when the transmission can be written as a rate.
- With one transmission the argument can be left out (`def transmit(self):`); with several, a `transmit()` with no argument is a `TypeError`, since it would not say which.
- Not yet with compartments: a disease with strains, or a transmission with several destinations; these raise `CapabilityError` (agents only).

A disease written entirely as code, `ss.AgentDisease`, runs only as agents and has its transmission over the sim's networks done by the same solver code (`ss.solvers.Transmission`: `code_transmit()`, `code_route()`, `code_betas()`, `code_strain_cases()`), which it reaches through thin hooks, each overridable on its own: `transmit()` (the whole step, e.g. to add a route, as `ssl.Cholera` adds the environment), `transmissibility()` and `susceptibility()` (each agent's effective `rel_trans` and `rel_sus`), `route_betas()` (the beta of each network, checked against it; Starsim 3's `validate_beta()`), `transmit_route()` (one network), and `finalize_infections()` (combining the networks' infections). It was called `ss.Infection` before 2026-11-06; the name misled, since a declared `ss.SIR` is an infection too. `ssl.AgentSIR`, `ssl.AgentSIS`, and `ssl.AgentSEIR` are teaching examples of what the declared models do under the hood, written this way, with no advantage over them. Finer hooks of the same kind for a declared disease (`susceptibility(transition)`) are deferred: the declared engine's transmission has strains, acts, mixing pools, and branching, which these hooks do not map onto.

### Moving people from code

A module written as code moves people between states with `ss.move(src, dst, p=, n=)`: `p=` a share of the people in `src` (in each group), or `n=` a number of them (shared among the groups and source states in proportion to who is in them, and at most all of them); with neither, everyone in `src` moves. It is written with the states as the code sees them at run time, `ss.move(sir.I, sir.R, p=0.5)`, or from several states, `ss.move([prot.U, prot.W], prot.B)`, or from any state of the disease, `ss.move(sir, sir.R)`, and it returns the number moved. Its arguments are told apart by what they are, so their order is free but for the source coming before the destination: states (at run time, `sir.I`, or by name, `'I'`, with the disease given), the disease, and agents (`ss.uids`, an array or list of integers, or a mask of agents, such as `sim.people.female`). `disease.move()` is `ss.move()` with the disease given, so `sir.move(uids, sir.R)`, `sir.move(uids, 'R')`, `ss.move(sir, uids, sir.R)`, and, in a disease's own code, `self.move(self.I, self.R, uids=uids)` all work, and `move` is not a name a state or transition can have. `uids=` moves those agents (of those in `src`; with `p=` or `n=`, a share or a number of them), which needs agents: in a compartmental run it raises `ss.CapabilityError`, by the try-it rule ([12-backends.md](12-backends.md)). It moves the same people under every solver: as agents, a share or a number of them chosen at random from the disease's own random numbers (so common random numbers hold; `n=` is people, so with scaling it is the nearest whole number of agents); in a compartmental run, the share of each compartment, drawn as whole people where the solver keeps whole people, and exactly `n` people when `n=` is given. It is a one-off move along no transition, as `ss.Delivery(move=I >> R)` is for a declared intervention, so it is in the states' results and in no transition's flow. Since people are moved and never made or lost, the number of people stays the same in every disease; people are added and removed only by births, deaths, and migration, which are declared ([Births, deaths, and migration](#births-deaths-and-migration)). So the count of a state of people is read, never written: `sir.I.n = 0` raises `ss.CapabilityError` and says to use `ss.move()` (decided 2026-10-25).

A count that is not people ([below](#states-that-are-not-people)) is a number under every solver, so its value may be written (`W.n = 0`, a reservoir emptied), and it is moved the same way, including from and to outside the model: mosquitoes that emerge, `ss.move(ss.unborn, mosq.Sv, n=1000)`, and die, `ss.move(mosq.Sv, ss.dead, p=0.1)`. A count moves as an exact share under every solver, as its declared flows do. A move between people and a count raises a `ValueError`, as a transition between them does; people from or to outside the model are a birth or a death, which are declared.

## States that are not people

Some of what a disease model tracks is not people: bacteria in water, a mosquito population, a wastewater signal. These are ordinary `ss.State` objects, declared and used like any other, with the same transition syntax, in the same `ss.Disease` as the states people are in. There is no separate class for them. It is how environmental and vector-borne transmission are written.

**Saying which they are.** Every state is people unless it is declared a count with `ss.State(people=False)` (or `ss.states(3, people=False)`). It is not worked out from the transitions: a person starts in the disease's first state or is seeded into another and moves only along transitions, but a model can keep two sets of people states with no transition between them (two risk groups), and a reservoir filled by an inflow looks like a group of people born into it, so a guess from the transitions can be wrong either way. A transition between a state of people and a count raises a `ValueError`, a count used bare in a rate raises a `ValueError`, and a group of states of people that no transition links to the first state and that only an inflow (not a birth) fills, as mosquitoes are, raises a `ValueError` too, so a forgotten `people=False` is caught when the module is built. A group of people filled only by an inflow says so with `people=True`.


**What follows.** A state that is not people:

- holds a plain count, a number, whatever the solver. It is never represented as agents;
- is not part of `total_pop`, of `N`, or of `I.frac`'s denominator, and `n_agents` and the scale factor between agents and people do not apply to it;
- starts at zero unless given an `init`, which is a count;
- has no age, sex, or risk group and does not sit on networks. Stratifying by a property of people leaves it unsplit; it is split by `patch`, or by dimensions of its own given with `states=` (`malaria.stratify(species=['gambiae', 'funestus'], states=[Sv, Ev, Iv])`). See [05-dimensions.md](05-dimensions.md#states-that-are-not-people);
- is used in a rate as a count, `W.n`. Used bare it raises a `ValueError` (below);
- is not touched by `ss.death(rate=...)` with no state, which applies to people; its own outflow is written out (`W >> ss.dead @ rate`);
- has results like any other state (`W`, and a flow for each of its transitions).
- can have its value written from code (`W.n = 0`), or be moved with `ss.move()`, from and to outside the model (`ss.unborn`, `ss.dead`, `ss.outside`) too, unlike a state of people ([above](#moving-people-from-code)).

```text
ValueError: the rate for 'infection' uses the bare state W, and W is not people.
       rate = beta * W
     A bare state means contact with people in that state, and there is no contact with a count.
     Write W.n for the number itself, or leave out people=False if W is people.
```

### Cholera: an environmental reservoir

Codeço's SIR-with-water model. People are infected by the concentration of bacteria in the water, with a saturating dose-response; infectious people shed into the water; bacteria decay.

```python
beta = 0.5        # per day: infection hazard at saturating exposure
K    = 1e5        # cells/mL giving half the maximum hazard
xi   = 10         # cells/mL shed per infectious person per day

S, I, R = ss.states(3)
W = ss.State(people=False)                    # bacteria in the water: a count

cholera = ss.Disease(
    infection = S >> I @ beta * W.n / (W.n + K),
    recovery  = I >> R @ ss.days(5),
    shedding  = ss.outside >> W @ xi * I.n,   # inflow: total per day
    decay     = W >> ss.dead @ ss.days(30),   # mean lifetime in water
    init      = dict(I=0.001),
)
sim = ss.Sim(cholera, total_pop=100_000, unit='day', stop=365)
```

`W` is declared a count, so `total_pop=100_000` is the people in `S`, `I`, and `R`. Nothing here is agent-specific, so `solver='auto'` runs it as an ODE. Add `n_agents=10_000` or a network and the people become agents while `W` stays a count; the model text does not change. The corresponding SimInf model keeps `W` in its per-node continuous state `v` and updates it in a C post-timestep function; here it is two more transitions.

### Malaria: a mosquito population

Ross-Macdonald. Humans are infected at a rate proportional to the number of infectious mosquitoes per person; mosquitoes are infected in proportion to human prevalence.

```python
a = 0.3           # bites per mosquito per day
b = 0.5           # probability an infectious bite infects a human
c = 0.5           # probability a bite on an infectious human infects the mosquito

Sh, Eh, Ih, Rh = ss.states(4)
Sv, Ev, Iv     = ss.states(3, people=False)   # mosquitoes: counts
Nh             = (Sh + Eh + Ih + Rh).n

malaria = ss.Disease(
    infection  = Sh >> Eh @ a * b * Iv.n / Nh,
    latency    = Eh >> Ih @ ss.days(12),
    recovery   = Ih >> Rh @ ss.days(100),
    waning     = Rh >> Sh @ ss.days(365),
    emergence  = ss.unborn >> Sv @ ss.perday(5_000),    # an inflow rate is a total per unit time
    biting     = Sv >> Ev @ a * c * Ih.n / Nh,
    incubation = Ev >> Iv @ ss.days(10),
    mortality  = Sv + Ev + Iv >> ss.dead @ ss.days(10),
    init       = dict(Ih=0.01, Sv=50_000),
)
sim = ss.Sim(malaria, n_agents=5_000, unit='day', stop=3 * 365)
```

The mosquito states are declared counts. Here `n_agents=` makes the humans agents; the mosquitoes are three numbers. `infection` is an acquisition, so `ss.modify(malaria.rel_sus, multiply=0.5, where=...)` (a bednet) and a vaccine reduce it, `ss.treat` cures from `Eh` and `Ih`, and `malaria.R0()` is the next-generation value, with the mosquitoes at their disease-free equilibrium (the square root of the classical Ross-Macdonald number, since each passage through the vector is a generation: [12-backends.md](12-backends.md)). `Ih=0.01` is a fraction of the people and `Sv=50_000` is a count of mosquitoes. A seasonal mosquito population is `emergence = ss.unborn >> Sv @ ss.seasonal(mean=5_000, amplitude=0.8, peak='April')`. Several mosquito species are a stratification of the three vector states.

### A value set each step

What is not a flow (a lag, a running maximum, a switch that stays on) is a few lines of a module written as code, whose `step()` sets it, and a function in a rate reads it, as odin's `update()` of a variable does:

```python
class Peak(ss.Connector):                      # the largest prevalence so far
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.peak = 0.0
    def step(self):
        sir = self.sim.diseases.sir
        self.peak = max(self.peak, sir.I.frac)

S, I, R = ss.states(3)
slowing = lambda sim: np.exp(-5 * sim.connectors.peak.peak)      # people take care once they have seen a large epidemic
sir = ss.Disease(infection=S >> I @ ss.perday(0.3) * I * slowing, recovery=I >> R @ ss.days(10), init_n=dict(I=10))
sim = ss.Sim(sir, connectors=Peak(name='peak'), total_pop=10_000, unit='day', stop=200)
```

The connector runs before the diseases in each step, so every rate in the step sees the value from its start. It reads only counts, so it runs under every solver: here as an ODE, a step at a time, with the function called once a step ([12-backends.md](12-backends.md#functions-try-it)); with `n_agents=`, as agents. What accumulates or decays is a flow into a count instead (`ss.outside >> C @ rate`), which every solver runs, and a total by week is a flow's result resampled (`res.infection.resample('week')`). (`ss.update`, a declared form of this for agents only, is gone.)

### How counts are advanced

In a compartmental run this changes nothing: every state, human or mosquito, is a number, advanced by the sim's solver with every other flow. In an agent-based run it is what lets the people be agents while the mosquitoes stay three numbers. The counts are advanced once per step with the rest of their disease, from the current counts (`I.n` is then the number of people the agents in `I` stand for), and their flows are applied as expected values, with the conversions in [02-types.md](02-types.md), because these quantities are usually large and are not individuals. Whether those flows should be random draws by default is open. How each solver advances them is in [12-backends.md](12-backends.md#states-that-are-not-people).

## Competing hazards

Within one module, transitions out of the same state that are driven by rates compete, and they are resolved jointly: the total exit hazard is the sum, the probability of leaving in a step is `1 − exp(−total × dt)`, and the destination is chosen in proportion to each hazard. A discrete-time solver MUST implement this as one multinomial draw per state (or its per-agent equivalent), not as sequential binomial draws, so that the order in which transitions are declared inside a module does not bias results.

This is a statement about one module's transitions out of one state. Across modules, and for custom `step()` code, the sim runs an ordered loop in which each module sees the current state left by the ones before it; that order is defined, printable, and specified in [10-execution.md](10-execution.md).

## What is guessed

Every one of these is a default that `describe()` prints and marks, and each row is tested both ways (`tests/devtests/test_contracts.py`): a model that makes the guess has it marked, and one that does not, not. The guesses about time (a bare time, the unit) are in [02-types.md](02-types.md), and those about dimensions (a dimension's kind and first level, the population's ages, aging) in [05-dimensions.md](05-dimensions.md).

| Guessed | Rule |
|---|---|
| Which states are infectious | The sources of contact-mediated transitions |
| Which states are infected, where none is marked | For strains, products, and rescaling only: the states acquisitions lead to ([above](#what-counts-as-acquisition)); never for a result, so a disease with no `infected=True` has no `infected` or `prevalence` |
| Which transitions are acquisitions | Contact-mediated ones, and the other transitions of people out of the first state when none of those is contact-mediated ([above](#what-counts-as-acquisition)); `acquisition=` overrides it |
| Initial conditions | Whatever is not given goes to the first state (`default_state=`, else the state named `S` or `susceptible`, else the one state transmission infects people from, else the first state made, [above](#ssstate)); with nothing given, nobody is infected (the library's `ss.SIR`, `ss.SIS`, and `ss.SEIR` have `init_prev=0.01`) |
| Dwell-time distribution | Exponential, from a scalar duration or a rate |
| Number of sub-stages | From the distribution, unless `stages=` is given |
| Units of bare numbers | [02-types.md §Bare numbers](02-types.md#bare-numbers) |
| Mixing | Homogeneous, one contact per unit time, when no network is given |
| Names of transitions | [01-objects.md §Names](01-objects.md#names) |
| Size of the population | 10,000 people, when none of `total_pop`, `n_agents`, and `people=` is given |
| Length of the run | 50 units of time (or steps, with no unit), when neither `stop=` nor `dur=` is given |
| Starting value of a fitted parameter | The middle of its bounds (geometric when they span a factor of 10 or more), for `ss.par(bounds=[...])` with no value |

## Looking at the model

Because the model is a set of state and transition objects, these are derived rather than written. Names like `plot`, `summarize`, and `to_df` are kept for results, as in Starsim.

```python
sir.describe()      # the resolved model as text, with every guessed default marked
sir.diagram()       # the state-transition diagram, as a Mermaid flowchart that a notebook draws (a string of its text)
sir.equations()     # the ODE system, with symbolic parameter names
sir.transitions     # the table of transitions; printing it shows the state-by-state matrix
```

`describe()` is specified in [01-objects.md](01-objects.md#describe). `sim.describe()` covers the whole sim, including which solvers can run it.

`equations()` is a method of the disease (or any module with transitions), not of the sim, and it prints parameter names, not numbers:

```text
>>> sir.equations()
dS/dt = -beta * S * I / N
dI/dt =  beta * S * I / N - I / dur
dR/dt =  I / dur
```

It writes the equations the model has under homogeneous mixing or the mixing it was given, with generated sub-stages shown, and says which parts (if any) have no ODE form. It is the only symbolic output in v1.

`transitions` is a table with one row per transition, and printing it also shows the matrix of sources by destinations:

```text
>>> sir.transitions
name        from  to   driven by          kind
infection   S     I    beta * I           transmission, from I
recovery    I     R    dur = 10 days      spontaneous

      S    I            R
S     .    infection    .
I     .    .            recovery
R     .    .            .
```

The matrix is Atomica's transition matrix, and it is the natural grid for a spreadsheet or form view of the model. An empty column for a state that also starts empty means nothing can ever be in it.

`sim.describe()` lists, under the solver, one line per ingredient that matters (each network, non-exponential dwell times, custom functions), saying whether it runs as compartments: `yes`, `approx (how)`, or `no (why)`. It is specified in [12-backends.md](12-backends.md).

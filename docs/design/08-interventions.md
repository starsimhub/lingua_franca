---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Interventions

What is delivered, and how it is delivered: products, delivery, cascades of steps, parameter changes, triggers, and scenarios.

Justified by [best-practices/interventions.md](../best-practices/interventions.md).

## What plus delivery

An intervention has two parts.

- **What**: a product (a vaccine, a test, a treatment) or a change to a quantity. This part is cleanly separable and reusable.
- **Delivery**: who gets it (`who=`), when (`when=`), and how many (`coverage=`, `capacity=`). These are often not separable from each other ("send drugs to the 100 clinics with the most positive tests, while stocks last"), so `who=` may also be one function of the sim that says who is eligible.

```python
bcg = ss.Vaccine(efficacy=0.85)                                                         # what
ss.vaccinate(bcg, who=ss.person.age < 5, coverage=0.7, when=[2021, 2025])              # delivery, by keywords
ss.vaccinate(bcg, who=my_function)                                                     # who, by a function
```

Interventions are passed to the sim with `interventions=`.

## Simple cases that need no product

**A change to a parameter over time** is `ss.modify` of a time series ([below](#changes-at-given-times)):

```python
ss.modify(sir.pars.beta, multiply=ss.timeseries({'2020-03-15': 0.5, '2020-06-01': 1.0}), when=ss.schedule(start='2020-03-15'))
```

**A change that applies to some people, or under a condition,** is `ss.modify` ([07-effects.md](07-effects.md)):

```python
ss.modify('school.pars.n_contacts', multiply=0.2, when=ss.schedule(start='2020-03-15', stop='2020-06-01'))
ss.modify(sir.rel_sus, multiply=0.6, who=sir.has_net)
```

**Vaccination as a move between strata** is a delivery of a level ([05-dimensions.md](05-dimensions.md#moving-between-coordinates-sstransfer)). The disease does not mention vaccination; protection is a value by level, and delivery moves people to the level:

```python
sir.stratify(vaccinated=[False, True])
protection = ss.modify(sir.infection, multiply=ss.by(vaccinated=[1.0, 0.15]))    # 85% protection, declared once
rollout = ss.Delivery(dict(vaccinated=True), who=ss.person.age > 65, coverage=0.7, when=[2021, 2022])
```

## Products

```python
ss.Vaccine(efficacy=0.85, waning=ss.years(5), cost=12.50)
ss.Vaccine(efficacy=dict(acquisition=0.85, transmission=0.3, severity=0.5))
ss.Vaccine(efficacy=0.85, leaky=False)                                          # all or nothing: 85% fully protected, the rest not at all
ss.Diagnostic(sensitivity=0.9, specificity=0.98, cost=4.00, result_delay=ss.days(2))
ss.Treatment(cure=0.95, cost=120.0)
ss.Treatment(cure=dict(infected=0.936, cin=0.936))                              # a cure by state
ss.Vaccine(efficacy=0.8, waning=ss.boxcar(plateau=ss.days(180), decay=ss.days(730)))  # full for 180 days, then an exponential decline
ss.Treatment(efficacy=dict(transmission=0.5), during=ss.ref('typhoid.acute'))  # held, and acting, only while acute
```

Products are nouns for things (`ss.Vaccine`, `ss.Diagnostic`, `ss.Treatment`); the deliveries that hand them out are verbs (`ss.vaccinate`, `ss.screen`, `ss.treat`), so no product and delivery differ only by case (`ss.Diagnostic` was `ss.Test`, which now raises, saying so). They replace Starsim 3's `ss.Vx`, `ss.Dx`, and `ss.Tx`. A product whose effect is code of your own is a subclass of `ss.Product` (or of one of these three) with an `administer(uids)` method, called with the people a delivery gave it to on the step, after what a product of its kind does; it acts on agents, so `'auto'` runs the model as agents and a compartmental solver raises `CapabilityError`. It may return the people with each of its outcomes, as a dict (`dict(positive=uids)`), which are then results and [events](#events) of the delivery, as a test's are, and which `outcome_names()` lists. Starsim 3's delivery classes (`ss.routine_vx`, `ss.campaign_vx`, `ss.routine_screening`, and the rest) are removed; their spellings here are in the migration guide.

**Efficacy.** A scalar `efficacy` on a vaccine means protection against acquisition, and is required. A dict gives efficacy against several things at once. Its keys are `acquisition` (scales `rel_sus`, which acts on every acquisition, including one by a bite rate or an EIR: [03-states-and-transitions.md](03-states-and-transitions.md#what-counts-as-acquisition)), `transmission` (scales `rel_trans`), `mortality` (scales the disease's death transitions), the name of any transition in the disease (`severity` in a model whose transition to severe disease has that name), or one destination of a transition with several (`'progression.C'`, which scales the chance of going to `C`, not the rate of leaving); an unknown key raises a `KeyError`, listing the valid ones. Each entry multiplies its quantity by `1 − efficacy` for the people who hold the product. On a transition chosen with `p=` (one of several branches), it scales that branch's probability, and the other branches share the rest. With `leaky=False` the vaccine is all or nothing: a share `efficacy` of those who receive it are fully protected and the rest not at all.

**Holding a product.** Whether someone holds a product is a property of people named `has_<product>` (`has_bcg`); the product's own name is taken by the product module. A delivery never gives a product to someone who already holds it, except one that fades by a function of time: a new dose restarts it (malariasim's rule, one dose at a time and a new one overwrites; MA15, decided 2026-10-22).

**Waning.** `efficacy` is the effect at full strength and `waning` is how it fades. A duration means the product is lost at an exponentially distributed time with that mean, under every solver, after which the person can receive it again. `ss.boxcar(plateau=, decay=)` is full protection for `plateau`, then an exponential decline with mean `decay` (or none): as agents, the share of protection left; in a compartmental run, holding the product has the levels of the box (`stages=`, 10 by default, each left at `stages/dur`, so the box's end is spread over about `dur/√stages`, which a note says) and a decaying level left at `1/decay` (MS6, decided 2026-10-26: Cliff's spelling, rather than `ss.boxcar(...) + decay`). A function of the time since delivery, `fn(t)` or `fn(t, sim, uids)`, returning the fraction of protection that remains, fades the efficacy while the person still holds the product; `t` is a duration in the sim's unit (an array: `t < ss.days(180)`, `t.years`), and `uids` the agents who hold it, so a function can read their age at delivery, `sim.people.age[uids] - t.years` (TY7; the sim too, since the people are read from it, where the proposal had `fn(t, uids)`). It is agents only (`'auto'` runs the model as agents, and a compartmental solver raises `CapabilityError`), since it is each person's own time since delivery. `waning=` may be a dict by effect (MS5), each a function (or an `ss.boxcar`) or `None` for none: a bed net's protection of its holder fades unlike its killing of mosquitoes; under a compartmental solver every effect must wane by the same box. `during=` holds the product only while people are in some states (a condition): they stop holding it when they leave them, and its effects act only there (TY6).

**Other shapes of waning are written as states (decided 2026-10-22, A3).** Starsim does not build in every shape of waning (only the box, above). A shape that can be drawn as a few boxes and arrows (full protection for a while and then a decay, decay at one rate and then another, a mixture of fast and slow) is written in the user's own code as a declared module of its own, whose states are the stages of protection, and runs under every solver, since its transitions are ordinary ones (a fixed delay is a conveyor; rates are exits). A delivery moves people into it, and `ss.modify(..., who=)` on its states is the efficacy; giving it again restarts it (`U + P1 + P2 >> P1`, from any of several states, written with the states as a transition's sources are):

```python
def box_then_decay(box, decay, name='prot'): # Written in malariasim, not Starsim
    U, B, W = ss.states('U B W')
    return ss.Disease(box=B >> W @ ss.constant(box), wane=W >> U @ decay, default_state='U', name=name)

S, I = ss.states('S I')
mal = ss.Disease(infection=S >> I @ ss.peryear(2.0), recovery=I >> S @ ss.days(150), name='mal')
prot = box_then_decay(ss.days(180), ss.days(365))
rounds = ss.Delivery(prot.U + prot.B + prot.W >> prot.B, coverage=0.8, when=['2025', '2028']) # Its module is found from the states
eff = ss.modify(mal.infection, multiply=0.2, who=prot.B | prot.W)
ss.Sim(diseases=[mal, prot], interventions=rounds, connectors=eff, start='2024', stop='2030', solver='ode', total_pop=1e4, verbose=0).run()
```

Protection that is lost from one stage to the next at random times gives the same mean protection over time as a fraction that fades for everyone (a box then `exp(-t/τ)`), but held by some rather than spread over all, so infections differ (malariasim's vaccine: prevalence about 5% lower after the box than with the fading function, as agents and as the ODE alike). A fade for everyone is written the same way, as stages of decreasing efficacy (`W1`, `W2`, ... each with its own `ss.modify`). The ODE tracks the protection module jointly with the disease it modifies ([12-backends.md](12-backends.md)). This is the public extension point for compartmental forms written outside Starsim; `compartmental_form(sim)` (as `ss.Pregnancy`'s) is a module's own approximation of itself, not a way to add forms.

**The share holding a product is a quantity** (MS4): `itn.held_share` is the share of the people in the same place who hold it, each counted by the protection they have left, and `itn.held_share(fn)` by a function of the time since delivery, so a product can act on anything a rate reads, e.g. the mosquitoes its holders kill: `Sv >> ss.dead @ 1/life + a*f_in*itn.held_share(kill)`. (A delivery's `coverage` is the share it reaches.) In a compartmental run it is worked out from the levels of holding the product (a function is read at the middle of each level of a box), once a step.

**A product is realized as modifiers** on the people who hold it, so it follows the combination rules in [07-effects.md](07-effects.md): two vaccines against acquisition multiply, a vaccine and a stratification adjustment multiply, and all of them are listed by `sim.what_modifies()`.

**Tests.** `sensitivity` and `specificity` are spelled out. A test returns a result per person: its outcomes `positive` and `negative`, which are [events](#events) that the steps after it are triggered by. A test with several results gives them most severe first, each with its probability by state, and the last as everyone else (`outcomes=dict(high_grade=dict(cin=0.9), low_grade=dict(infected=0.1), normal=None)`); each result is an outcome too (`cytology.high_grade`), and `positive` is any result but the last and `negative` the last, so a step after it reads the same after a test with two results or several. A result cannot be called `positive` or `negative`. By default it detects infection with the disease it is delivered for (the states the model treats as infected, printed by `describe()`); `detects=` takes a [condition](07-effects.md#conditions) to say something else (a function of the sim and UIDs makes the sim agent-based). `sensitivity=` may be a dict with one value for each state, each a number or an `ss.by` (`sensitivity=dict(symptomatic=0.91, asymptomatic=ss.by(age=[0.73, 0.78]))`), and the test then detects being in those states. The states can be of several diseases, and those of a disease written as code are its boolean states (`'hpv16.cin'`, which need not be exclusive: each person is tested in the most severe one they are in); delivered with `disease=[...]`, a state with no disease (`'cin'`) is that state of each, and the diseases are tested as the strains of a family, once, in the most severe state (HP70). `result_delay=` is the time from test to result (agents only, as for a step's `when=ss.on(event, delay=...)`).

**Treatments.** `cure=` is the probability that treatment clears the infection, once, when it is given: the person leaves whichever infected state they are in for the state the disease's recovery leads to. It is one number, the same for every state it acts on; a dict by state (`cure=dict(infected=0.936, cin=0.936)`), each a number or an `ss.by`, and people in other states are not cured; or a dict by what cured people move along: transitions of the disease, usually with a rate of 0 (`cure={syph.cure_early: 0.98, syph.cure_late: 0.95}`, from each transition's own states, so a treatment can start from any state), or a move written with the states (`cure={I + CIN >> S: 0.9}`). Not every move a treatment makes is a cure: `moves=` names what it moves people along for a treatment that, say, starts care (`moves=hiv.start_art`), with the probability `cure=` (1 by default) or a dict, and the same outcomes; for a disease written as code, a cure (by state, of its boolean states, or of all its infected) calls its `clear_infection(uids)` (HP70). A treatment that cures has the outcomes `cured`, `failed` (infected, and not cured), and `unneeded` (not infected: overtreatment), which are results and [events](#events) of its delivery. The people it moves count towards that transition's flow, and a delivery with that transition as `when=` includes them from the next step. `efficacy=`, a dict as for vaccines, is what it does while it is held, such as antiretroviral therapy (`efficacy=dict(transmission=0.96, mortality=0.9)`). The two can be given together (`ss.Treatment(cure=0.3, efficacy=dict(transmission=0.9))`); a number for `efficacy=` raises, pointing to `cure=`. With neither, `cure` is 1. Either way a treatment is given to the people who are infected (the states acquisitions lead to and the sources of infection, [03-states-and-transitions.md](03-states-and-transitions.md#what-counts-as-acquisition), so in a malaria model infected by a bite rate, `Eh` and `Ih`) unless `who=` says otherwise.

**Cost.** `cost=` is per delivery. Total cost is then a result of the intervention, which is what cost-effectiveness needs. Allocating a budget between programs is `sim.optimize(ss.fit.maximize(..., at=...))` (or `ss.fit.minimize()`), which reallocates spending parameters (the programs of an imported Atomica program book, or any parameters named with `spend=`) to maximize or minimize a result, keeping the total; a program declared in Python, rather than imported, is not built ([`deferred.md`](../admin/deferred.md)).

## Delivery

```python
ss.Event(what, who=None, when=None, n=None, p=None, strain=None, increment=None)        # something that happens to people: a move, a counter, or a visit
ss.Delivery(what, who=None, when=None, coverage=None, capacity=None, strain=None,       # an event that delivers a product (or a move)
            increment=None, trace=None, skip_reached_within=None, disease=None)
ss.vaccinate(vaccine, ...), ss.screen(diagnostic, ...), ss.treat(treatment, ...)        # subclasses of ss.Delivery for each kind of product
```

Every delivery has three parts, each optional: **what** is delivered (`what=`, also the first argument: a product, or a move as for `ss.Event`), **who** is eligible (`who=`), and **when** (`when=`). With no product, `ss.Delivery(who=...)` is a step people attend (a visit). In the common case of a product given by one delivery, the delivery takes the product's own keywords and makes it (`ss.vaccinate(efficacy=0.9, coverage=0.8, when='2025-02-01')`); a product given by several deliveries is made once and passed to each. `ss.Event` says how many it reaches as `ss.move()` does, with `n=` (at most this many each time) and `p=` (the chance for each person eligible); `ss.Delivery` says the same in the words of services, `coverage=` and `capacity=`, and adds what only interventions need (a product, `trace=`, `skip_reached_within=`, `disease=`, and `ss.capacity()`). Internally they are one class.

**`who=`** is who is eligible, and only that:

| `who=` | Means |
|---|---|
| a condition on people: `ss.person.age < 5`, `~diagnosed`, a state by its path (`'sir.I'`) | the people who meet it |
| a condition on the population: `sir.I.n > 1000` | everyone or no one, decided at each step; joined to one on people with `&` |
| `ss.at_age(ss.months(9))` | people as they reach an age, joined to other conditions with `&` (`ss.at_age(ss.months(9)) & ss.person.female`) |
| a function of the sim | who is eligible: UIDs, a mask, or `True` or `False` for everyone ([below](#who-as-a-function)) |

**`when=`** is when, told apart by type:

| `when=` | Means |
|---|---|
| nothing | routine: each person is offered it once in each spell of being eligible, at its first step |
| a time or a list of them: `'2025-02-01'`, `[2021, 2025]`, or with no calendar `ss.days(10)` | rounds at those times (`ss.days(10)` is day 10, not every 10 days) |
| `ss.schedule(every=ss.years(1), start=2021, stop=2030)` | rounds this far apart, between `start` and `stop` |
| `ss.schedule(start=2025, stop=2030)` | routine between those times |
| an event: `sir.infection`, `screening.positive`, `anc_visit`, or a path (`'sir.infection'`) | a trigger: the people it happened to ([events](#events)), who must also be eligible |
| `ss.on(event, delay=ss.months(3))` | a trigger, delivered that long after the event |
| a function of the date: `lambda now: now.month == 1` | the steps on which it is true |

`ss.schedule(at=None, every=None, start=None, stop=None)` is the full form of a time: `at=` (also the first argument) is the times, or a function of the date; `every=` how often; `start=` and `stop=` the period. A time is given as the times of a time series are ([below](#changes-at-given-times)). Events combine: `when=a | b` is anyone either happened to, each person once, and `when=a & b` anyone both happened to on the same step; an event joined to a condition with `&` (`when=preg.delivery & hiv_rdt.positive.ever`) is those it happened to who meet the condition, which joins `who=`. Each keyword means one thing: an event in `who=` raises an error that points to `when=`, and a condition on people in `when=` one that points to `who=`. An event joined to a condition with `|` raises too, since it is neither.

### Delivery keywords

| Keyword | Meaning |
|---|---|
| `what=` | what is delivered: a product (the first argument), or instead a move between two states for the people reached, written with the states, e.g. `S >> V` (a one-off campaign), or from any of several (`U + B + W >> B`, which restarts the time in `B` of those already there), or with their paths (`'sir.S >> sir.V'`, or `'S >> V'` for the one disease that has them); a level of a stratification (`dict(vaccinated=True)`, or a pair, `dict(risk=('low', 'high'))`); or a change of strains (`DS >> RIF`, [05](05-dimensions.md#strains)); the module is the one that has the states; with `capacity=`, a move seeds a number of people on a schedule |
| `who=` | who is eligible (above) |
| `when=` | when it is delivered (above). With `ss.on(event, delay=)`, the time from the trigger to delivery (HP26): a duration, or a distribution of durations, drawn per person. The people triggered receive it then if they still meet `who=`, and `coverage=` applies then; someone waiting is not triggered again. Agents only, since who is waiting, and since when, is each person's own (decided 2026-10-20). On `ss.screen` it is the step's delay; the time from a test to its result is the test's (`ss.Diagnostic(result_delay=)`). A delivery on a date happens at the start of the step from that time point, and is counted in that row |
| `coverage=` | the fraction of eligible people reached (`p=` on `ss.Event`) |
| `capacity=` | the number that can be delivered (`n=` on `ss.Event`), or `ss.capacity(n, priority=, queue=)`, which also says who is served first (a condition, a list of them, or a score such as `-hiv.cd4`) and whether the rest wait (`queue=True`, or at most a duration; agents only) |
| `strain=` | with a move into a state where people carry a strain, the strain they arrive with |
| `increment=` | instead of a product, a counter that goes up for those reached |
| `trace=` | deliver to the contacts, in this network (or these), of the people that the event in `when=` selects, instead of to them (contact tracing, partner notification); a network with `memory=` also gives the partnerships of that long ago that have ended. Agents only |
| `skip_reached_within=` | skip the people this delivery reached less than this long ago (agents only), e.g. `ss.years(1)` for a re-screening interval |
| `disease=` | the disease the product acts on (default: the only one; for a step with no product, the disease of its trigger, or the first). A list, or a disease whose strains have courses of their own (HP7), delivers it for each: a vaccine's efficacy against each disease, a test detecting each one's infected (or each one's state of a name, `outcomes=dict(high=dict(cin=0.9))`), the worst result over them per person, and a cure of each one's infected; as if its values were keyed by disease, which they then are. A list is agents only (decided 2026-10-20); a product keyed by the diseases itself (`ss.Vaccine(efficacy=dict(hpv16=0.9, hpv18=0.9))`, `ss.Treatment(cure={ng.cure: 0.95, ct.cure: 0.95})`, or a test's `sensitivity=` by their states, whose diseases are then tracked jointly) has a compartmental form. A disease written as code (PL2) is a `disease=` too, as agents: a test detects its `infected`, a cure calls its `clear_infection(uids)`, and a vaccine scales its `rel_sus` and `rel_trans`; a missing part raises naming it |

Each old keyword (`where=`, `on=`, `at=`, `every=`, `start=`, `stop=`, `delay=`, `at_age=`, `move=`, `product=`, `priority=`, `queue=`, `eligibility=`) raises a `TypeError` naming what replaces it.

```python
ss.vaccinate(bcg, who=ss.person.age < 5, coverage=0.7, when=[2021, 2025])                                  # two campaign rounds
ss.vaccinate(bcg, who=ss.person.age < 5, coverage=0.7, when=ss.schedule(every=ss.years(1), start=2021))   # a yearly round
ss.vaccinate(bcg, who=ss.at_age(ss.months(9)), coverage=0.9, when=ss.schedule(start=2021))                # routine: each child as they reach 9 months
```

**Rounds and routine delivery.** With times or `every=`, delivery happens in rounds, and in each round every eligible person is offered the product once. With no `when=`, or only a `start` and `stop`, delivery is routine: each person is offered the product once in each spell of being eligible, at its first step, and the record that they were offered it is a property of people named `offered_<delivery>`. Routine versus campaign is therefore a keyword, not a class. `ss.at_age()` is given as people reach the age: on its first step, the people already past it (as agents, older by more than a step; in a compartmental run, everyone in an age group at or above it) are recorded as offered it, so `who=ss.at_age(ss.months(9))` vaccinates children as they turn 9 months and not everyone older on the first day; it takes no `when=` but a start and stop. A condition on age is not read this way: `who=ss.person.age >= 0.75` is ordinary routine delivery, which reaches everyone that old on the first step. A catch-up of those already older is a campaign round.

**`coverage=` versus `capacity=`.** These are different specifications and both are common.

- `coverage=0.7` is a fraction of the eligible people. It accepts everything a parameter accepts, including `ss.by(age=[...])`, a time series, and a function of the sim returning one probability per person.
- `capacity=50_000` is a number available: a bare number is per round for campaigns (or per step for delivery on events), and a rate (`ss.peryear(50_000)`) is per unit time. Routine delivery has no rounds, so a bare number there raises, asking for a rate. It may be a time series or a function of the sim. It is a total, so `ss.by(...)` raises, saying to make one delivery for each stratum with its own capacity (a capacity per stratum, e.g. per district, is not yet a keyword). When fewer are available than eligible people who would receive one, recipients are chosen by `ss.capacity(priority=)`, or else at random among them, and delivery stops when the capacity is used up ("while stocks last").
- Given together, coverage is applied first and capacity caps the result.

Each delivery reports the number delivered and the realized coverage as results, in total and per stratum. On a stratified model, coverage is a fraction of all eligible people and capacity is a total, not a number per stratum ([05-dimensions.md](05-dimensions.md#coverage-and-counts-on-a-stratified-model)).

`who=` restricts to people; restricting to particular contacts is not needed, because a network already says who is in contact with whom.

### `who=` as a function

When who is eligible depends on more than a condition can say, write one function of the sim. It is called every step and returns who is eligible: UIDs, a mask, or `True` or `False` for everyone. A function that reads only the time (`lambda sim: sim.ti > 20`) says when, not who, so it is an error pointing to `when=`; this holds for `who=` everywhere (`ss.modify`, transitions, `ss.move`). A bare `who=True`, `False`, or number is an error too: leave `who=` out for everyone. `coverage=` and `capacity=` then apply to them as to any eligible people, and `when=` says when; to reach exactly the people it returns at each step, give `when=` every step.

```python
def to_busiest_clinics(sim):
    hiv, ppl = sim.diseases.hiv, sim.people
    waiting  = hiv.diagnosed & ~hiv.on_art                       # diagnosed and not yet treated
    n_waiting = np.bincount(ppl.clinic[waiting], minlength=n_clinics)
    busiest  = np.argsort(n_waiting)[-100:]                      # the 100 clinics with the most
    return (waiting & np.isin(ppl.clinic, busiest)).uids

art = ss.Treatment(efficacy=dict(transmission=0.96, mortality=0.9))
ss.treat(art, who=to_busiest_clinics, capacity=ss.peryear(20_000))    # routine, while stocks last
```

In a compartmental run the function is tried on groups; the example above uses a per-agent attribute and is agent-based.

### Cascades

A cascade of care is steps that people flow through, each an ordinary delivery with its own trigger, coverage, and capacity (which is where people are lost), each producing events and memory that any later step can use. A follow-up is a step of its own, triggered by an outcome of the step it follows; it is not nested in it.

```python
S, I = ss.states('S I')
sis = ss.Disease(infection=ss.Transition(S, I, rate=0.3 * I), recovery=ss.Transition(I, S, dur=ss.days(10)), init_prev=0.01)
rapid = ss.Diagnostic(sensitivity=0.8, specificity=0.95)
pcr   = ss.Diagnostic(sensitivity=0.95, specificity=0.99, result_delay=ss.days(2))
drug  = ss.Treatment(cure=0.95)

screening = ss.screen(rapid, who=rapid.since >= ss.days(28), coverage=0.1, when=ss.schedule(every=ss.days(7)))   # not tested in the last four weeks
confirm   = ss.screen(pcr, when=screening.positive, coverage=0.9)                                                # a follow-up is a step of its own
treatment = ss.treat(drug, when=confirm.positive, capacity=ss.perday(50))                                        # while stocks last

sim = ss.Sim(sis, interventions=[screening, confirm, treatment], unit='day', stop=120, total_pop=50_000).run()
sim.results.treatment.lost_capacity     # who each step lost to capacity; eligible and delivered give those lost to coverage
```

- **Steps are peers.** Any number of steps take the same trigger (a treatment and a vaccination of the same positives); a step can be triggered by several events (`when=screening.high_grade | triage.positive`); one result can feed steps months apart, through memory. `on_positive=` and `on_negative=` are removed: they raise, showing the two steps to write instead.
- **Order within a step.** Each step runs after the steps whose events trigger it, whatever order they are given in, so a follow-up acts on the step its trigger happens (on the step a test's result is available, after its `result_delay`). A cycle of triggers raises, naming it. Reading another step's memory (`screening.positive.ever`) does not order them.
- **The steps are a list.** They are passed to `interventions=` like any other module, in any number and order, and are named from their variables.
- **A visit is a step with no product**, `ss.Delivery(who=...)`: an antenatal visit, a clinic visit for symptoms. Its attendees are its event, so several steps triggered by the same visit reach the same people (one visit, several tests).

```python
anc_visit = ss.Delivery(when=preg.conception, coverage=0.85)          # preg = ss.Pregnancy(): its events are conception, delivery, and loss
anc_hiv   = ss.screen(hiv_rdt, when=anc_visit, disease='hiv')
anc_syph  = ss.screen(rpr, when=anc_visit, disease='syph')
newborn   = ss.screen(pcr, when=preg.delivery, who=anc_hiv.positive.ever, trace='postnatalnet')
```

#### Events

An event is the set of people something happened to on the current step. These are events: a transition (`sir.infection`), and a transfer (agents only); a step (`anc_visit`: the people it reached); an outcome of a step (`screening.positive`, `treatment.failed`); and a product (`hiv_rdt`, `hiv_rdt.positive`: the union over every step that delivers it). A module written as code can trigger a step with a function of the sim that returns the people. A misspelled outcome raises `AttributeError`, listing the outcomes. In a compartmental run an event is a share of each state and group, carried along the moves that later steps of the step make: two outcomes of one step (and the events that follow from them) are disjoint, and an event that follows from another is within it. Events combined with `|` or `&` (`a.positive | b.positive`) are agents only, since who is in both is not known from their shares (decided 2026-10-20).

#### Memory: `.ever`, `.n_times`, `.since`

Every event remembers, per person, whether (`ev.ever`, a condition), how often (`ev.n_times`, compared with numbers), and how long ago (`ev.since`, compared with durations; infinite if never) it happened, including on the current step once the step that fired it has run. They go anywhere a condition goes: a delivery's `who=`, `ss.modify(who=)`, a transition's `who=`. As agents, every step's events (the step and each outcome) are kept, a time and a count per person, so they can be read after a run: `sim.interventions.screening.ever.uids` (HP73); a product's, and in a compartmental run any event's, are kept only if something reads them (found by walking the conditions when the sim is built). In a compartmental run `.ever` is a property of people with two levels (`ever_<event>`), which `describe()` lists; `.n_times` and `.since` are agents only (decided 2026-10-20).

### Event-triggered delivery

An event as `when=` delivers to the people something has just happened to, instead of on a schedule:

```python
ss.screen(hiv_test, when=anc.visit, coverage=0.9)                            # test at antenatal visits
ss.treat(drug, when=tb.diagnosis, coverage=0.85)                             # treat on diagnosis
ss.treat(drug, when=ng.careseek | ct.careseek)                               # either, each person once
ss.screen(pcr, when=ss.on(screening.positive, delay=ss.months(3)))           # three months after a positive test
```

A state or condition given as `when=` is not an event, and raises an error that points to `who=`: the people in a state on each step are `who=sir.I, when=ss.schedule(every=ss.days(1))` in a daily sim. `who=`, `coverage=`, and `capacity=` then apply to those people. An outcome of another delivery triggers on the same step, and a transition of a disease on the next, since deliveries run before the diseases in each step. The worked example in [07-effects.md](07-effects.md#plain-code-in-step) shows an event-triggered delivery next to the same logic written as `step()` code.

### What a delivery reports

Every delivery is a module with results of its own, in total and selectable by stratum like any other result ([09-results.md](09-results.md)): the number delivered each step (`delivered`), the number eligible (`eligible`), the realized coverage (`coverage`, which for several groups is what was delivered over who was eligible in them), the cost if the product (or visit) has `cost=` (`cost`), and with `capacity=`, the number not reached for lack of it (`lost_capacity`).

As agents, `screening.reached()` is the UIDs of the people a delivery (or a product, over its deliveries) reached on its last step, and `screening.reached('positive')` those with one of its outcomes: its last step is the current one once it has run, and otherwise the one before, so a disease or an analyzer, which steps after the interventions, reads the step just taken.

Each outcome is a result of its name too: a test's `positive` and `negative`, counted on the step the result is available (so after the test's `result_delay`), and a cure's `cured`, `failed`, and `unneeded`. For a step named `screening` the positives are `sim.results.screening.positive` (it was `diagnosed`). These are flows, so they can be summed, scaled, and compared with data by name. A cascade adds `sim.results.<cascade>`, whose `to_df()` is its table: for each step, who it is for, the number eligible, reached, lost to coverage, and lost to capacity, and its outcomes.

**Reported cases, when testing is modeled.** `ss.outcome` ([09-results.md](09-results.md)) is a shortcut for a reporting process the model does not represent: "about half of infections are reported, five days later". When the model does represent testing, through one or more interventions, the outcome is not used for cases. Each testing intervention reports the diagnoses it made, and reported cases are their sum:

```python
symptomatic_testing = ss.screen(pcr, when=sir.symptom_onset, coverage=0.6)
screening           = ss.screen(rapid_test, coverage=0.1, when=ss.schedule(every=ss.weeks(1)))

cases = symptomatic_testing.positive + screening.positive
```

So an outcome and a testing intervention never both produce the same cases: if the model has tests, the tests produce the cases. The sum is a result like any other sum of flows, and it is what the `cases` column of a data file is matched to. It belongs to neither intervention, and whether it is declared on the sim or on the disease that both test for is open ([19-open-questions.md](19-open-questions.md)).

The choice between the three ways of representing an observed quantity:

| The model contains | Use |
|---|---|
| No testing or reporting process | `ss.outcome`, a weighted sum of flows with a delay |
| Testing, as one or more interventions | the interventions' own `positive` results, summed |
| Something that changes what happens to the person (a diagnosed person is treated, or isolates) | a step triggered by the test's outcome (`when=screening.positive`), or the outcome's memory (`hiv_rdt.positive.ever`) |

An intervention marks individuals (a positive result triggers the next step, and is remembered per person); an outcome never does, because it never recorded who they were.

## Changes at given times

The simplest time-varying intervention is a modifier whose amount is a time series:

```python
ss.modify(sir.pars.beta, multiply=ss.timeseries({'2020-03-15': 0.5, '2020-06-01': 1.0}), when=ss.schedule(start='2020-03-15'))
ss.modify('school.pars.n_contacts', multiply=ss.timeseries({2020.2: 0.2, 2020.6: 1.0}), when=ss.schedule(start=2020.2))
ss.modify(sir.pars.beta, set=ss.timeseries({ss.days(30): 0.02, ss.days(60): 0.05}), when=ss.schedule(start=ss.days(30)))   # a sim with no calendar
```

- The target is any quantity `ss.modify` accepts.
- The times are points on the sim's axis, which its `start` decides ([02-types.md](02-types.md)). In a sim with a calendar they are dates (`'2020-03-15'`) or calendar years (a bare number, from 1800 on), and a duration is an error that suggests a date or `sim.pars.start + ss.days(30)`; in a sim with no calendar they are durations from 0 (`ss.days(30)` is day 30) or numbers in the sim's unit. A duration in a unit other than the sim's or the module's warns. The same holds for a delivery's `when=`, `ss.schedule()`, and `sim.run(until=)`. A time outside the sim raises a `ValueError`; so does a `start` or a round of a delivery, while a `stop` after the end means it never stops.
- `multiply=` gives multipliers relative to the baseline value (not to the previous entry); `set=` gives absolute values.
- Each value holds from its time until the next (`interpolation='step'`, the default for a time series); a `start` at the first time keeps the baseline before it.

It is an ordinary modifier ([07-effects.md](07-effects.md)): it combines with other modifiers by the same rule, appears in `what_modifies()`, and takes `who=`, `when=`, and `until=`. Starsim 3's `ss.change(target, at=[...], by=[...])` (and `to=`) was a shorthand for it, removed in v4 since it was no shorter; `ss.converters.migrate` rewrites it.

## Triggers

"When" is `when=`, on time alone, for a delivery and for `ss.modify`: times, `ss.schedule()` (a window with only `start=` and `stop=`), or a function of the date (`lambda now: now.month in [6, 7, 8]`); a delivery's may also be an event. A condition on the state of the epidemic is `who=`: a condition on the population (`sir.I.n > 1000`), or a function of the sim returning `True` or `False`:

```python
S, I, R = ss.states('S I R')
sir = ss.Disease(infection=ss.Transition(S, I, rate=0.05 * I), recovery=ss.Transition(I, R, dur=ss.days(10)), init_prev=0.01)
home, school = ss.RandomNet(n_contacts=3, name='home'), ss.RandomNet(n_contacts=10, name='school')

def many_cases(sim):
    new = sim.results.sir.infection
    return new[max(0, sim.ti - 7):sim.ti].sum() > 100  # the last seven completed steps

closures = ss.modify('school.pars.n_contacts', multiply=0.2, who=many_cases)
sim = ss.Sim(sir, networks=[home, school], interventions=closures, n_agents=2000, stop=ss.days(100)).run()
```

A policy with a release takes `until=`, so that it doesn't switch on and off around one threshold: `ss.modify(beta, multiply=0.5, who=I.n >= 2000, until=I.n <= 1000)` is on from when `who=` holds until `until=` does, for each place or group on its own, under every solver.

- The function is called each step, at the intervention's place in the loop, and can read anything in the sim, including the stocks of this step and the flows of the steps before it. Results are read as in Starsim: storage is preallocated for the whole run, and during a step `sim.ti` is the step's own index, where its results go; its stocks (the state at its start) are recorded before any module's step, so are `[sim.ti]`, and its flows at its end, so the flows so far are `[:sim.ti]` ([10-execution.md](10-execution.md)). A shorter spelling for "the steps so far" would be a convenience and is not specified ([19-open-questions.md](19-open-questions.md)).
- It can read any result, including an outcome ([09-results.md](09-results.md)): `who=lambda sim: sim.results.sir.n_hosp[sim.ti] > 500` acts on hospital occupancy without hospitalization being a state.
- A calendar condition is a function of the date in `when=`. "No school contacts on Fridays" is `ss.modify('school.pars.n_contacts', multiply=0.0, when=lambda now: now.weekday() == 4)`, in a sim with dates.

**`who=` and `when=` have no memory, except `until=`.** The intervention is active on exactly the steps where they hold. A bare threshold therefore switches on and off as the quantity crosses it, which is rarely the policy meant. The one memory a modifier has is `until=`: a condition (above), or a duration, so that once `who=` holds for someone it stays on for them for at least that long (`until=ss.days(14)`; a bare number is in the sim's unit), which with a condition on a transition's incidence by place is MEmilio's dynamic NPIs, each place on its own (`who=secir.symptoms.incidence(over=ss.days(7), by='patch') > 200e-5`). Any other rule that remembers what it did (reopen only after two weeks below the threshold, close at most three times) is a module with a `step()`, where the memory is an ordinary attribute and can be read, printed, and tested:

```python
class SchoolClosure(ss.Intervention):
    def __init__(self, threshold=100, hold=ss.weeks(4), **kwargs):
        super().__init__(**kwargs)
        self.define_pars(threshold=threshold, hold=hold)
        self.closed      = False
        self.date_closed = None

    def step(self):
        sim = self.sim
        new = sim.results.sir.infection
        many = new[max(0, sim.ti - 7):sim.ti].sum() > self.pars.threshold
        if many and not self.closed:
            self.closed, self.date_closed = True, sim.now
        elif self.closed and not many and sim.now - self.date_closed >= self.pars.hold:
            self.closed = False

closure = SchoolClosure(name='closure')
effect  = ss.modify('school.pars.n_contacts', multiply=0.2, who=lambda sim: sim.interventions.closure.closed)
sim     = ss.Sim(sir, networks=[home, school], interventions=[closure, effect], n_agents=2000, stop=ss.days(100)).run()
```

The class decides and remembers; the modifier applies the effect, so the base contact rate is never overwritten and comes back when `closed` is cleared ([07-effects.md](07-effects.md#plain-code-in-step)). Whether a function of the sim as `who=` should exist at all, given how little it can say safely, is open ([19-open-questions.md](19-open-questions.md)).

## Scenarios

```python
base = ss.Sim(hiv, networks=ss.SexualNet(), interventions=art_program)                 # what is really in place
prep = ss.Sim(hiv, networks=ss.SexualNet(), interventions=[art_program, prep_rollout])

sims = ss.parallel({'baseline': base, 'prep': prep}, n_runs=10)
sims.plot()
sims.to_df()                # one tidy table: quantiles across the runs, by scenario and time
sims.diff('baseline')       # differences from the baseline, run by run, by scenario, module, and result
```

- **A scenario is a sim.** It contains exactly the interventions passed to it. The baseline contains whatever is really in place (antiretroviral therapy in an HIV model, routine immunization in a measles model); it is not a run with everything switched off.
- `ss.parallel` runs the sims, in parallel, and returns them as one `ss.MultiSim` (labeled by the keys of a dict) whose results have a run axis, selectable by scenario (`select(scenario='prep')`). With `n_runs=` each scenario is run several times ([09-results.md](09-results.md)).
- With common random numbers ([11-random.md](11-random.md)), the scenarios share their random draws, so the difference between two scenarios is the effect of the intervention and not noise.

## How each solver realizes an intervention

Conditions, coverage functions, and `who=` functions are tried on what the solver provides ([07-effects.md](07-effects.md#on-agents-and-on-groups)): agents in an agent-based run, groups in a compartmental one. Nothing is classified in advance; under `solver='auto'`, something that asks for per-agent information makes the sim agent-based, and under an explicit compartmental solver the run stops and says what was asked for. A delivery at time point `ti` happens between the steps and is counted there. Deliveries on a schedule (routine or in rounds), to people chosen by states and stratifications, of a product people hold or a transfer, are taken by the kernels in a whole compartmental run; the others (tests and the steps that follow them, cures, `capacity=`, a function in `who=` or `when=`, events, and memory) step the run from Python. One class does both: the methods of `ss.Delivery` are how it runs as agents, and a compartmental run uses a small adapter for what differs there ([12-backends.md](12-backends.md#how-a-model-is-built)).

| Declaration | Compartmental | Agent-based |
|---|---|---|
| `ss.modify` | a time- or group-varying multiplier on the quantity | a per-agent or scalar multiplier |
| `ss.Delivery(dict(dim=...), coverage=)` | a flow between the dimension's compartments | select eligible agents, thin to coverage, change the property |
| `ss.vaccinate`, `ss.treat` with a product | adds a `has_<product>` dimension to the model (printed) and moves people along it; waning given as a duration is a flow back (a function of time since delivery is agents only) | records who holds the product and when they got it |
| `ss.screen` | flows thinned by sensitivity and specificity (a `result_delay=` is agents only) | a result per agent |
| an event in `when=` (a step, an outcome, a product, a transition) | the share of each state and group it happened to on the step, carried along the moves of later steps in the step; a transfer needs agents | UIDs |
| `\|` and `&` of events | agents only | union and intersection of UIDs |
| `.ever`, `.n_times`, `.since` | `.ever` a property of people with two levels (`ever_<event>`), added only if read; `.n_times` and `.since` agents only | a time and a count per agent |
| `when=fn(now)`, `who=fn(sim)` returning `True` or `False` | called once per step | called once per step |
| a module with `step()` (a trigger with memory) | works if the code uses only what groups have | works |
| `who=` using stratifications and states | selects groups | selects agents |
| `who=` using a per-agent attribute | stops with a message naming the attribute | selects agents |
| `capacity=` | a cap on the total flow, shared across groups in proportion to the eligible | a cap on the number of agents |
| `ss.capacity(queue=)`, `ss.on(delay=)`, a test's `result_delay=` | agents only | who waits, and since when |
| `who=fn(sim)` (or any of `self`, `sim`, `uids` by name) | works if the function uses only what groups have; one that takes `uids` is agents only | returns who is eligible |
| `trace=`: delivery to specific contacts (contact tracing, partner notification) | not available | available on networks that keep contacts |

## Rejected

- **Four independent parts** (where, when, to whom, what) as the organizing idea. "What" separates cleanly; the rest often depend on each other, so they are `who=` and `when=`, each of which can be a function.
- **A class per combination of delivery mode and product** (routine screening, campaign screening, routine vaccination, ...). One function per product type, with keywords.
- **Interventions that are off unless a scenario turns them on.** A sim contains its interventions; a baseline usually has some.
- **Interventions as extra compartments written into the disease.** A transfer along a dimension, or a product, does this without touching the disease.
- **A rule language with its own variables, sets, and operations.** Conditions and functions in Python say the same thing in a line.
- **`min_duration=` on a trigger.** `until=` with a duration is that minimum; other rules with memory are a `step()`.
- **An outcome and a testing intervention both producing cases.** If the model has tests, the tests produce the cases.
- **`days=` as a time keyword.** `when=` and a time series take dates, years, or durations.
- **Several keywords for when** (`at=`, `every=`, `start=`, `stop=`, `on=`, `delay=`) and for who (`where=`, `at_age=`, `eligibility=`). One `when=`, told apart by type, with `ss.schedule()` and `ss.on()` for the full forms; one `who=`.
- **`ss.change(at=, by=, to=)`**, a shorthand for `ss.modify` of a time series. It was no shorter, and was a second name for one idea.
- **Follow-ups nested in a test (`on_positive=`, `on_negative=`).** A cascade is not a tree: a trigger can be the union of several events, one result feeds several steps, and memory carries a result forward. Steps are peers, triggered by events.
- **`who >> what` as the spelling of a step** (`screening.ascus >> ss.screen(hpv_dna)`), by analogy with `S >> I`. Keywords (`when=`, and the product as the first argument) say the same without parentheses around a trigger of several parts.
- **Delivery extras, removed 2026-10-20 (they can come back if needed):** stock targets (`target=`, `above=`, `ss.share`; STIsim keeps its own), a resource shared by steps (`ss.Resource`, `uses=`, and numeric `priority=` classes), `ss.cascade` (it ran as its steps would as a list), `ss.visit` (a delivery with no product), `count_events=` and `events_df()`, and reading any condition on age as delivery by age (only `ss.at_age()` is). A target is `who=` or `capacity=` as a function of the sim, a shared clinic a `capacity=` function that reads what the steps before it used, and a log of events an analyzer.
- **Budget optimization and optimal control in v1.** `cost=` keeps the door open. (Allocating a fixed budget between imported programs, `sim.optimize()`, was added for Atomica's users; optimal control was not.)

# SimInf: SIS by age in 1,600 cattle herds, with an environmental infectious pressure

A stochastic SIS in 1,600 cattle herds (nodes) over four years, in three age categories (calves, young stock, and adults), where animals are not infected by each other but by an environmental infectious pressure `phi` in their herd: infected animals shed into it, and it decays at a rate that changes with the season. The herds are linked by a schedule of births, deaths, movements, and aging. It is SimInf's built-in `SISe3()` model, run as in the example in SimInf's documentation of `events_SISe3` and `u0_SISe3`, with the data that come with the package.

It shows what SimInf's compartment models are for (its authors used models of this kind, with three age categories and an environmental pressure, for verotoxigenic *E. coli* O157 in Swedish cattle: Widgren et al. 2016, in the bibliography of SimInf's vignette), and goes further than [sir_herds](../sir_herds), which has the same herds and register:

- A continuous state per node (`phi`) next to the whole-number compartments, advanced by a deterministic forward-Euler step once a day (SimInf's "post time step" function), while the animals move in continuous time
- A rate that depends on the day of the year (the decay of `phi`, constant within each of four intervals)
- Three age categories, with aging as scheduled events (`intTrans` with a `shift`) that move animals between compartments, keeping their infection state
- Events that choose animals from one age category only (`select` 4 to 6), on 783,773 events in all

## Files

- `original/events_SISe3.R`: the example, unchanged, from `man/events_SISe3.Rd` of SimInf 11.1.0 (`man/u0_SISe3.Rd` has the same example; `?SISe3` itself has none)
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 200 runs at each of the recorded days (1, 8, ..., 1,457): the totals over all nodes of each compartment (`S_1`, `I_1`, `S_2`, `I_2`, `S_3`, `I_3`) and of the infected (`I`), the mean of `phi` over the nodes (`phi`), the number of nodes with at least one infected animal (`nodes_infected`), the infected and `phi` of nodes 1 to 3 (`node1_I`, `node1_phi`, and so on), and each compartment of node 1 (`node1_S_1`, and so on)
- `reference/timing.json`: the time of the first run (building the model and running it, with R started and the events read) and of a rerun (`run(model)` again)
- `reference/model.json`: the number of nodes, the compartments, the transitions, the update of `phi`, the parameters, and the number of events of each type
- `reference/u0.csv`: the initial state of each node (`node`, `S_1`, `S_2`, `S_3`, `I_1`, `I_2`, `I_3`), with the 10 infected calves in node 1
- `reference/events.csv.gz`: every event, in the order SimInf processes them (`event`, `time`, `node`, `dest`, `n`, `proportion`, `select`, `shift`); 2.9 MB
- `reference/events_summary.csv`: the events by type, with their count, the animals they affect, and the `select`, `shift`, and `proportion` they use
- `reference/select_matrix.csv` and `reference/shift_matrix.csv`: the `select` and `shift` matrices of the model
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (GPL-3)

## The model

- **Compartments:** `S_k` and `I_k` for the age categories `k` = 1, 2, 3, as whole numbers of animals, and `phi`, a real number, in each of 1,600 nodes
- **Transitions:** in each node, `S_k` to `I_k` at rate `upsilon_k*phi*S_k`, and `I_k` to `S_k` at rate `gamma_k*I_k`; there is no transmission between animals except through `phi`
- **The infectious pressure:** after each day's transitions and events, in each node, `phi <- phi*(1 - beta(day)) + alpha*(I_1 + I_2 + I_3)/N + epsilon` (`phi` alone, plus `epsilon`, if the node is empty), with `day = t %% 365`; the new `phi` is used for the next day's transitions. This is a forward-Euler step of `dphi/dt = alpha*I/N - beta(t)*phi + epsilon`
- **Seasonal decay:** `beta(day)` is `beta_t1` on days 0 to 90, `beta_t2` on 91 to 181, `beta_t3` on 182 to 272, and `beta_t4` on 273 to 364 (`end_t1` to `end_t4` are 91, 182, 273, and 365, the same in every node). Here that is 0.1 a day for the first half of each year and 0.125 for the second
- **Parameters:** `upsilon_k = 0.018` and `gamma_k = 0.1` per day in every age category, `alpha = 1`, `epsilon = 0`, and `phi` starts at 0 in every node
- **Initial conditions:** `u0_SISe3`: 196,168 animals, all susceptible (11,982 calves, 31,757 young stock, and 152,429 adults), in herds of 55 to 214; then 10 infected calves are added to node 1 (`u0$I_1[1] <- 10`)
- **Time:** days 1 to 1,460, recorded every 7 days (`tspan = seq(from = 1, to = 4*365, by = 7)`, so the last record is day 1,457), in continuous time, with events once a day
- **Seed:** `set.seed(123)`, on one thread (`set_num_threads(1)`)

### Events

| Type | Count | `select` | `shift` | Effect |
|---|---|---|---|---|
| `exit` | 182,535 | 4, 5, 6 (`S_k` and `I_k` of one age category) | 0 | Animals of that age, chosen at random, are removed |
| `enter` | 182,685 | 1 (`S_1`) | 0 | Susceptible calves are added |
| `intTrans` | 317,081 | 4, 5 | 1, 2 | Animals of age category 1 (or 2), chosen at random, move to age category 2 (or 3) in the same node, keeping their infection state: `S_1` goes to `S_2` and `I_1` to `I_2` |
| `extTrans` | 101,472 | 4, 5, 6 | 0 | Animals of that age, chosen at random, move to node `dest`, keeping their compartment |

Every event has `proportion = 0` and `n` from 1 to 4 (333,003 animals age in the 317,081 internal transfers); there are events on every day from 1 to 1,460. SimInf applies each day's events after the day's transitions and before `phi` is updated: first those within a node (`exit`, `enter`, then `intTrans`), then the movements between nodes (`extTrans`), each in the order of the table. See [sir_herds](../sir_herds/README.md#events) for how SimInf processes events in general.

## Results

Node 1 never loses the infection: its pressure rises to about 4 in the half of the year with slow decay and falls to about 2.4 in the other, and its number of infected animals swings between about 40 and 65 with it. The infection reaches other herds only when an infected animal is moved, and an animal moved into a clean herd starts its pressure from zero, so the spread between herds is slow and very variable: after four years, on average 166 of the 1,600 herds are infected (24 to 352) and 3,770 animals (519 to 8,138), most of them adults.

`run.py` evaluates the original, which sets the seed and makes one run, and then makes 199 more runs of the same model, so it writes the same results each time.

## Lines of model code

27, counting every line of `events_SISe3.R` that is not blank or a comment, apart from the four calls to `plot()` and the call to `summary()`; no line is over 100 characters. The model's equations are in SimInf's C code (`src/models/SISe3.c`, with the seasonal decay in `src/misc/SimInf_forward_euler_linear_decay.c`), and the initial conditions and the events are data that come with the package; none of them is counted.

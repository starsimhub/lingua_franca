# SimInf: SIR in 1,600 cattle herds with births, deaths, and movements

A stochastic SIR epidemic in 1,600 cattle herds (nodes) over four years, where the only link between herds is a schedule of animal movements. It is the example in SimInf's documentation of `events_SIR()`, using the data that come with the package.

## What it exercises

- Many nodes, each a small well-mixed population with its own stochastic simulation in continuous time (Gillespie's direct method)
- Scheduled events given as data, 466,692 of them: animals entering a node (births), leaving it (deaths), and moving from one node to another
- Events that choose which animals they affect at random from named sets of compartments (the `select` matrix)
- No transmission between nodes except by moving infected animals
- A population that changes in size, in each node and in total
- A built-in model (`SIR()`) with its initial conditions and events passed as data frames

## Files

- `original/events_SIR.R`: the example, unchanged, from `man/events_SIR.Rd` of SimInf 11.1.0
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the mean and 5% to 95% range of 200 runs at each of days 1 to 1,460: the totals over all nodes (`S`, `I`, `R`), the number of nodes with at least one infected animal (`nodes_infected`), and three nodes on their own (`node1_S`, `node1_I`, `node1_R`, and the same for `node2` and `node3`)
- `reference/timing.json`: the time of the first run (building the model and running it, with R started and the events read) and of a rerun (`run(model)` again)
- `reference/model.json`: the number of nodes, the transitions, the parameters, and the number of events of each type
- `reference/u0.csv`: the initial state of each node (`node`, `S`, `I`, `R`)
- `reference/events.csv.gz`: every event, in the order SimInf processes them (`event`, `time`, `node`, `dest`, `n`, `proportion`, `select`, `shift`); 1.7 MB, or 12 MB unpacked
- `reference/events_summary.csv`: the events by type, with their count, the animals they affect, and the `select`, `shift`, and `proportion` they use
- `reference/select_matrix.csv`: the `select` matrix of the SIR model
- `meta.yaml`: where it came from
- `LICENSE`: the upstream license (GPL-3)

## The model

- **Compartments:** `S`, `I`, `R`, as whole numbers of animals, in each of 1,600 nodes
- **Transitions:** in each node, `S` to `I` at rate `beta*S*I/(S + I + R)` (zero in an empty node), and `I` to `R` at rate `gamma*I`, using that node's own counts
- **Parameters:** `beta = 0.16` and `gamma = 0.01` per day, the same in every node
- **Initial conditions:** `u0_SIR()`: 196,168 animals, all susceptible, in herds of 55 to 214 (mean 123); then one infected animal is added to node 1 (`u0$I[1] <- 1`), so node 1 starts with 143 susceptible and 1 infected
- **Time:** days 1 to 1,460 (`tspan = seq(from = 1, to = 4*365, by = 1)`), in continuous time, with events once a day
- **Seed:** `set.seed(123)`, on one thread (`set_num_threads(1)`)

### Events

| Type | Count | `select` | Effect |
|---|---|---|---|
| `exit` | 182,535 | 4 (`S`, `I`, `R`) | One animal, chosen at random from the node, is removed |
| `enter` | 182,685 | 1 (`S`) | One susceptible animal is added to the node |
| `intTrans` | 0 | | Not used in this example |
| `extTrans` | 101,472 | 4 (`S`, `I`, `R`) | One animal, chosen at random from the node, is moved to node `dest`, keeping its compartment |

Every event here has `n = 1`, `proportion = 0`, and `shift = 0`, and there are events on every day from 1 to 1,460 (128 to 470 a day, 320 on average).

How SimInf processes events in general:

- **Each day** has three parts, in order. First, every node runs its transitions in continuous time from `t` to `t + 1`. Second, the events scheduled for day `t` are applied to the state at the end of that day: first those within a node (`exit`, then `enter`, then `intTrans`), then the movements between nodes (`extTrans`), each group in the order of the events table. Third, the rates of the nodes that events touched are recalculated. Events never interrupt the day.
- **What is stored** for time `t` is the state after all three parts, so the first row of the results (day 1) already includes one day of transmission and the events of day 1; the initial state itself is not in the results.
- **`select`** is a column of the `select` matrix, whose nonzero rows are the compartments the event draws from (for `enter`, adds to), and whose values are weights. For the SIR model, columns 1 to 3 are `S`, `I`, and `R` alone and column 4 is all three with equal weights.
- **`n` or `proportion`:** an event affects `n` individuals; if `n = 0`, the number is drawn from a binomial distribution with probability `proportion` and size the number of individuals in the selected compartments.
- **Which individuals:** with equal weights, the `n` individuals are drawn without replacement from the selected compartments (a multivariate hypergeometric draw), so each individual is equally likely; with unequal weights, they are drawn one at a time with probability in proportion to weight times the number remaining. For `enter` with several compartments, each individual is placed with probability in proportion to the weights. It is an error, which stops the run, to ask for more individuals than the selected compartments hold.
- **`shift`** is a column of a second matrix (`N`, empty for this model) giving, for each compartment, how many rows down an individual moves: `intTrans` needs it (for example, vaccination moving `S` to `R`), and `enter` and `extTrans` can use it; 0 means no shift.

## Results

The outbreak starts in node 1 and reaches other herds only when an infected animal is moved, so it spreads slowly at first: on average 10 herds are infected after 200 days and 129 after a year. It then takes off, with mean `I` peaking at about 49,900 around day 700, and about 1,230 of the 1,600 herds still infected at the end, because births keep adding susceptible animals. In 14 of the 200 runs (7%) the infection dies out in the first herd before it is moved on, which is why the 5% quantile of `I` is 0.

`run.py` evaluates the original, which sets the seed and makes one run, and then makes 199 more runs of the same model, so it writes the same results each time.

## Lines of model code

12, counting every line of `events_SIR.R` that is not blank or a comment, apart from the three calls to `plot()` and the call to `summary()`; no line is over 100 characters. The initial conditions and the events are data that come with the package, and are not counted.

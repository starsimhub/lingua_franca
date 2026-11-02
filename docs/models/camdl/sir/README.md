# camdl: SIR with weekly reported cases

A closed SIR epidemic in 10,000 people over 12 weeks, observed through weekly reported cases.

`model.py` is the Starsim version, and `compare.py` checks it against `reference/`.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 30 | 13 | Long lines count twice |
| One ODE run | first 0.013 s, rerun 0.0056 s | first 0.0094 s, rerun 0.00029 s (Rust) | The original is timed as a whole command, since camdl has no rerun within a process: its first run compiles the model, and its rerun is the same command with the model cached. Starsim's times exclude the import |
| Results, ODE | | | **Agree.** Compartments and weekly cases within 0.02% (`compare.py` asks for 0.1%) |
| Results, stochastic | | | **Agree.** Mean of 200 runs within 0.6% for `I` and 0.9% for weekly cases, chain-binomial in both, with whole-day steps (`compare.py` asks for 3% and 4%) |

Measured on 2 November 2026 with Starsim 4.0.0rc1 (the `v4` branch, commit `e26de815+`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: three states, two transitions, and one outcome with its likelihood. Nothing needed a function or a `step()` method.

## Findings

- **A likelihood on an outcome.** The original says the weekly cases are negative binomial around `rho` times the infections, with dispersion `k`. Here `likelihood=ss.nbinom(n=k)` says the same, and `sim.fit(method='nuts')` samples the posterior, using the priors and fitting `k` too if it has bounds. From weekly cases drawn around the original's ODE cases (with `beta` 0.4, `gamma` 0.15, and `k` 10), the posterior medians and 95% intervals are `beta` 0.40 (0.32 to 0.46), `gamma` 0.16 (0.07 to 0.23), and `k` 29 (10 to 74); twelve weekly counts say little about `k`. The interval for `k` only just reaches the value used, or just misses it, depending on the draws. `compare.py` checks that the intervals for `beta` and `gamma` hold the values used.
- **NUTS speed.** camdl has its own NUTS in Rust, with symbolic gradients. On 15 October, fitting `beta` and `gamma` with 4 chains of 500 warm-up draws and 500 draws, the two took about the same time per effective draw, but Starsim took about 5.5 s overall, against camdl's 2.3 s, because of compiling in JAX. This has not been measured again.
- **A parameter could not multiply a flow (fixed).** `rho * infection` works with `rho` as an `ss.par`.
- **Weekly cases are added up in `compare.py`.** The `cases` result is daily. The original's weekly reporting (`covers = closing_at(time, 7 'days)`) is only used in Starsim when data is attached; to read weekly cases from a run, you add them up yourself.
- **Whole days have to be asked for.** camdl's chain binomial takes whole steps of a day. Starsim's takes smaller steps by default, unless `substeps=1` is given, as `compare.py` does.
- **The unit comes from `stop=`.** With `stop=ss.weeks(12)` and no `unit=`, the sim would run in weeks, although the rates are per day. The original states `time_unit = 'days` once; here `unit='day'` does the same.

## What it exercises

- Transitions written as rates, with a named total (`N = S + I + R`)
- Parameters with units, bounds, and priors
- An observation model: weekly totals of a flow, a reporting fraction, and a negative binomial likelihood
- Deterministic and stochastic runs of the same model

## Files

- `model.py`: the Starsim version
- `compare.py`: checks it against `reference/`
- `original/sir.camdl`: the model, unchanged
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the ODE run (`ode_S`, `ode_I`, `ode_R`, `ode_infection`, and the weekly cases expected from it, `ode_cases`), and the mean and 5% to 95% range of 200 chain-binomial runs (`stochastic_I`, `stochastic_cases`)
- `reference/timing.json`: the times of a first ODE run, which compiles the model, and of a rerun, each as a whole command
- `meta.yaml`: where it came from

The parameter values are those used in camdl's own examples: `beta = 0.4`, `gamma = 0.15`, `rho = 0.6`, `k = 10`.

## Lines of model code

30, counting every line of `sir.camdl` that is not blank or a comment.

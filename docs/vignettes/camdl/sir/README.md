# camdl SIR, in Starsim

The translation of [models/camdl/sir](../../../models/camdl/sir). The model is `sir.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 30 | 13 | Long lines count twice |
| One ODE run | first 0.013 s, rerun 0.0069 s | first 0.021 s, rerun 0.0013 s (Rust) | The original is timed as a whole command, since camdl has no rerun within a process: its first run compiles the model, and its rerun is the same command with the model cached. Starsim's times exclude the import |
| Results, ODE | | | **Agree.** Compartments and weekly cases within 0.02% (`compare.py` asks for 0.1%) |
| Results, stochastic | | | **Agree.** Mean of 200 runs within 0.6% for `I` and 0.9% for weekly cases, chain-binomial in both, with whole-day steps (`compare.py` asks for 3% and 4%) |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `4473e253`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: three states, two transitions, and one outcome with its likelihood. Nothing needed a function or a `step()` method.

## Findings

- **A likelihood on an outcome.** The original says the weekly cases are negative binomial around `rho` times the infections, with dispersion `k`. Here `likelihood=ss.nbinom(n=k)` says the same, and `sim.fit(method='nuts')` samples the posterior, using the priors and fitting `k` too if it has bounds. From weekly cases drawn around the original's ODE cases (with `beta` 0.4, `gamma` 0.15, and `k` 10), the posterior medians and 95% intervals are `beta` 0.40 (0.32 to 0.46), `gamma` 0.16 (0.07 to 0.23), and `k` 29 (10 to 74); twelve weekly counts say little about `k`. The interval for `k` only just reaches the value used, or just misses it, depending on the draws. `compare.py` checks that the intervals for `beta` and `gamma` hold the values used.
- **NUTS speed.** camdl has its own NUTS in Rust, with symbolic gradients. On 15 October, fitting `beta` and `gamma` with 4 chains of 500 warm-up draws and 500 draws, the two took about the same time per effective draw, but Starsim took about 5.5 s overall, against camdl's 2.3 s, because of compiling in JAX. This has not been measured again.
- **A parameter could not multiply a flow (fixed).** `rho * infection` works with `rho` as an `ss.par`.
- **Weekly cases are added up in `compare.py`.** The `cases` result is daily. The original's weekly reporting (`covers = closing_at(time, 7 'days)`) is only used in Starsim when data is attached; to read weekly cases from a run, you add them up yourself.
- **Whole days have to be asked for.** camdl's chain binomial takes whole steps of a day. Starsim's takes smaller steps by default, unless `substeps=1` is given, as `compare.py` does.
- **The unit comes from `stop=`.** With `stop=ss.weeks(12)` and no `unit=`, the sim would run in weeks, although the rates are per day. The original states `time_unit = 'days` once; here `unit='day'` does the same.

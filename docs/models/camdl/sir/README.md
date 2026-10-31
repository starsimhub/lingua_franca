# camdl: SIR with weekly reported cases

A closed SIR epidemic in 10,000 people over 12 weeks, observed through weekly reported cases.

## What it exercises

- Transitions written as rates, with a named total (`N = S + I + R`)
- Parameters with units, bounds, and priors
- An observation model: weekly totals of a flow, a reporting fraction, and a negative binomial likelihood
- Deterministic and stochastic runs of the same model

## Files

- `original/sir.camdl`: the model, unchanged
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the ODE run (`ode_S`, `ode_I`, `ode_R`, `ode_infection`, and the weekly cases expected from it, `ode_cases`), and the mean and 5% to 95% range of 200 chain-binomial runs (`stochastic_I`, `stochastic_cases`)
- `reference/timing.json`: the times of a first ODE run, which compiles the model, and of a rerun, each as a whole command
- `meta.yaml`: where it came from

The parameter values are those used in camdl's own examples: `beta = 0.4`, `gamma = 0.15`, `rho = 0.6`, `k = 10`.

## Lines of model code

30, counting every line of `sir.camdl` that is not blank or a comment.

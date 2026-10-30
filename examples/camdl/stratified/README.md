# camdl: SEIR by age and patch

An SEIR in 13,510 people in two patches over 150 days, written in pycamdl, camdl's Python front end. People mix by an age contact matrix within their own patch, age between three age groups, and move between the patches; 60% of susceptible children can be vaccinated (moved to `R`) on day 20.

## What it exercises

- Two dimensions (age and patch) with a population given for every combination of them
- A contact matrix by age, within each patch
- Aging between named age groups, from the time spent in each
- Movement between patches, for every infection state
- A one-off intervention that moves people between states, switched on or off for a run
- Deterministic and stochastic runs of the same model

## Files

- `original/stratified.py`: the model, unchanged
- `stratified.camdl`: the same model in camdl's own language, without the vaccination, for Starsim's tests: camdl's ODE run of it agrees with the pycamdl original's to camdl's rounding (it writes whole numbers), and so does the model Starsim imports from it (to 1e-9 against the original)
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the infectious in each of the six cells (`I_child_north` and so on) and the totals of `S`, `E`, `I`, and `R`, from the ODE (`ode_novax_...`, `ode_vax_...`) and as the mean and 5% to 95% range of 200 chain-binomial runs (`stochastic_novax_...`, `stochastic_vax_...`), without and with the vaccination
- `reference/timing.json`: the time of one ODE run
- `meta.yaml`: where it came from

## Lines of model code

35, counting every line of `stratified.py` that is not blank, a comment, an import, or the plotting under `if __name__ == '__main__'`, with the one line over 100 characters counted twice.

# camdl: SEIR by age and patch

An SEIR in 13,510 people in two patches over 150 days, in camdl's own language. People mix by an age contact matrix within their own patch, age between three age groups, and move between the patches; 60% of susceptible children can be vaccinated (moved to `R`) on day 20.

## What it exercises

- Two dimensions (age and patch) with a population given for every combination of them
- A contact matrix by age, within each patch
- Aging between named age groups, from the time spent in each
- Movement between patches, for every infection state
- A one-off intervention that moves people between states, switched on or off for a run
- Deterministic and stochastic runs of the same model

## Files

- `original/stratified.camdl`: the model, including the vaccination, with `--enable vaccinate` to switch it on. It was written for this project from an example in pycamdl, camdl's Python front end, and agrees with that version to within 0.1%: camdl's output is rounded to whole numbers
- `stratified.camdl`: the same model without the vaccination, for Starsim's tests
- `run.py`: runs it and writes `reference/`
- `reference/results.csv`: the infectious in each of the six cells (`I_child_north` and so on) and the totals of `S`, `E`, `I`, and `R`, from the ODE (`ode_novax_...`, `ode_vax_...`) and as the mean and 5% to 95% range of 200 chain-binomial runs (`stochastic_novax_...`, `stochastic_vax_...`), without and with the vaccination
- `reference/timing.json`: the times of a first ODE run, including building the model, and of a rerun
- `meta.yaml`: where it came from

## Lines of model code

47, counting every line of `original/stratified.camdl` that is not blank or a comment, with the two lines over 100 characters counted twice.

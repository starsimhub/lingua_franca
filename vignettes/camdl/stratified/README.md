# camdl SEIR by age and patch, in Starsim

The translation of [examples/camdl/stratified](../../../examples/camdl/stratified). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 47 | 16 | Long lines count twice |
| One ODE run | first 0.025 s, rerun 0.015 s | first 0.019 s, rerun 0.0016 s (Rust) | The original is timed as a whole command (camdl has no way to rerun a model in the same process), and its first run includes building the model; Starsim's is in Python, without the import |
| Results, ODE | | | **Agree.** The infectious in every cell within 0.4%, with and without vaccination (`compare.py` asks for 0.5%, since camdl writes whole numbers, which matters in the smallest cells), and the totals of `S`, `E`, and `R` within 0.1%, apart from the day of the vaccination (finding below) |
| Results, stochastic | | | **Agree in size, not quite in timing.** The peak in every cell is within 2%, but with a step of a day the south's epidemic rises about a day sooner, so the mean of 200 runs differs by up to 7% of the peak on the way up (`compare.py` asks for 2% and 8%). The gap is about the two chain-binomial schemes at a coarse step: on 14 October it shrank from 7% to 2% with a quarter-day step |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `13494d38`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: three transitions, two stratifications, the population by age and patch, a contact matrix, movement, and the vaccination as a one-off move.

## Findings

- **Aging has to be asked for.** With no births or deaths, Starsim leaves people in their age group and says so in a note, so this model gives `use_aging=True`. Without it, children have 2% too many infections. The original ages people because it says so in its transitions.
- **A move between states (fixed).** The original moves 60% of susceptible children to `R` on day 20. This version once gave them a fully effective vaccine, which left them in `S`. `ss.vaccinate(move=seir.S >> seir.R, ...)` now says what the original says, and `S` and `R` agree.
- **The day a move shows.** camdl's count on day 20 is after the move, and Starsim's is before it: its move is at the start of the step from day 20 to 21, so it shows on day 21. The two agree from then on. This is why `compare.py` leaves out that row for `S`, `E`, and `R`.
- **Whole days have to be asked for.** Starsim's chain binomial takes smaller steps by default. Against the original's whole days that gives a peak about 4 days sooner, so `compare.py` gives `substeps=1`.
- **The contact matrix is not reciprocal.** Starsim gives a note that the original's matrix has different contacts in the two directions for this population, and uses it as given, as camdl does.
- **Contacts within places, and populations by two dimensions (fixed).** A contact matrix by age now acts within each place, and `split=` takes an `ss.by` over several dimensions, written as the original writes it. As agents, a contact matrix still mixes people across places.
- **Results by group (fixed).** Sums of stratified results keep their groups where they can, and many runs keep the values of each group (unless they would take more than 500 MB).

# Optima TB: the structure of a large model

The structure of the Optima TB model: 97 states, 318 transitions, and 9 populations with aging, as Starsim code, for testing how Starsim handles a model of this size imported from Atomica.

`model.py` has **no data**. It keeps the states, transitions, and formulas. Every parameter, population, and initial value is a default, so its results mean nothing about TB. `make_model.py` wrote it, and `tests/conversion/test_optima_tb.py` checks this.

There is no reference from Atomica, since Atomica would need the workbooks.

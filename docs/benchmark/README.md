---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Benchmark

`lingua_franca benchmark` regenerates every number in the table on the home page. It checks each translation against its original, times the two in turn, and writes the lines and times into each translation's table.

**Last full run:** 30 minutes on 9 November 2026 (compare 11.9, timing 17.6). The slowest model, `laser/england_wales`, took 428 s.

## How long it takes

The whole suite takes about 20 minutes, one model at a time: about 13 for timing and 8 for checking results. To keep it that way:

- Each model is timed by running its original and then Starsim, twice over, and taking the best of each. A round that takes over 30 s isn't repeated.
- Each model uses only the kernels listed for it in [`kernels.yaml`](kernels.yaml): the fastest, and any others within 10% of it, so that a close call is settled each time. The note beside each model gives its reruns under every kernel set. To try them all again and rewrite the list, use `--all-kernels`, which takes about half an hour and also times Numba compiling and rebuilds. Do this after a large change to the kernels.
- Each time within a run is the best of as many calls as fit in 3 s, or 100 calls if that takes at least 1 s (`time_budget`, `most_runs`, and `least_time` in `docs/models/tools.py`). There is always at least one.
- The large reference runs of the originals are not repeated. They are kept in `docs/models/*/*/reference`, and each `run.py` makes only the runs its timing needs. Use `--references` to remake them, which takes over an hour.
- Each `compare.py` uses just enough runs for its check.
- A few models are timed at a smaller size than the examples show, on both sides. `flepimop/vaccine_scenarios` is timed at 3 scenarios of 2 runs each, not 10, and `epimodel/hiv` at one scenario.

If the load average goes over 10, the run pauses before the next model and checks again every 5 minutes; pauses aren't counted in its times.

Each full run saves how long the suite, each stage, and each model took to `timings.json`, updates the line above, and lists any model over 2 minutes.

## Running it

1. **Install Starsim v4 with its Rust kernels.** You need Python, [Rust](https://rustup.rs), and a clone of the [`v4` branch](https://github.com/starsimhub/starsim/tree/v4):

    ```bash
    git clone -b v4 https://github.com/starsimhub/starsim
    pip install -e starsim
    (cd starsim/starsim/solvers/rust && ./build)
    ```

    JAX is optional (`pip install jax`); without it, or without a GPU, those rows are left out.

2. **Install the frameworks.** Each one has its own environment, so that their versions don't clash. These take about 4 GB, and need `uv`, R and a C++ compiler, and OCaml and Rust for camdl (see [the environments](../models/environments.md)):

    ```bash
    lingua_franca envs install
    lingua_franca envs check
    ```

3. **Run it.** For fair times, run it on a quiet machine:

    ```bash
    lingua_franca benchmark                        # Everything
    lingua_franca benchmark --only odin            # Only the models whose name contains "odin"
    lingua_franca benchmark --stages timing tables # Only the times, about 13 minutes
    lingua_franca benchmark --all-kernels          # Try every kernel set, and rewrite kernels.yaml
    ```

    The times go in `timings.json` and `timings.csv` in this folder (`docs/benchmark/`), keeping the last time of any kernel set not run this time, and what each run prints goes to `compare.log` in each translation's folder and `run.log` in each example's folder. It stops short of the text: if a result changes, `compare.py` fails, and the Results row of the translation's table is updated by hand.

The run ends with a scorecard of the north star: one row per model with its lines and times against the original, and whether it fails. A model fails on lines if Starsim has more than the original, and on a time if Starsim is more than 2x slower and more than 1 s slower. `--stages tables` prints it from the last run without timing anything, and `--out` saves it to a file.

Then run `quarto render docs` to rebuild the site.

# Benchmark

This folder regenerates every number in the table on the home page. `benchmark.py` runs the originals, checks each translation against them, times each translation under each set of kernels, and writes the lines and times into each vignette's table.

**Last full run:** 51 minutes on 31 October 2026 (originals 7.8, compare 7.0, timing 30.5). The slowest model, `laser/england_wales`, took 205 s.

## How long it takes

The whole suite is meant to take under an hour, one model at a time. No model should take more than a couple of minutes over all the stages, and most should take well under a minute. To keep it that way:

- The large reference runs of the originals are not repeated. They are kept in `examples/*/*/reference`, and each `run.py` makes only the runs its timing needs. Use `--references` to remake them, which takes over an hour.
- Each time is the best of as many runs as fit in a budget (`budget` in `benchmark.py`, and `time_budget` in `examples/tools.py`), up to 100 runs, but with at least 5 s spent on it. A fast model is timed in 2 fresh processes, and a slow one gets a single rerun.
- Each `compare.py` uses just enough runs for its check.
- A few models are timed at a smaller size than the examples show, on both sides. `flepimop/vaccine_scenarios` is timed at 3 scenarios of 2 runs each, not 10, and `epimodel/hiv` at one scenario.

If the load average goes over 10, the run pauses before the next model and checks again every 5 minutes; pauses aren't counted in its times.

Each full run saves how long the suite, each stage, and each model took to `timings.json`, updates the line above, and lists any model over the limit.

## Running it

1. **Install Starsim v4 with its Rust kernels.** You need Python, [Rust](https://rustup.rs), and a clone of the [`v4` branch](https://github.com/starsimhub/starsim/tree/v4):

    ```bash
    git clone -b v4 https://github.com/starsimhub/starsim
    pip install -e starsim
    (cd starsim/starsim/solvers/rust && ./build)
    ```

    JAX is optional (`pip install jax`); without it, or without a GPU, those rows are left out.

2. **Install the frameworks.** Each one has its own environment, so that their versions don't clash. These take about 4 GB, and need `uv`, R and a C++ compiler, and OCaml and Rust for camdl (see [the environments](../_envs/README.md)):

    ```bash
    python _envs/envs.py install
    python _envs/envs.py check
    ```

3. **Run it.** For fair times, run it on a quiet machine:

    ```bash
    python benchmark/benchmark.py                        # Everything
    python benchmark/benchmark.py --only odin            # Only the models whose name contains "odin"
    python benchmark/benchmark.py --stages timing tables # Only time Starsim, and update the tables
    ```

    The times go in `timings.json` and `timings.csv` in this folder, with every set of kernels tried, and what each run prints goes to `compare.log` in each vignette's folder and `run.log` in each example's folder. It stops short of the text: if a result changes, `compare.py` fails, and the Results row of the vignette's table is updated by hand.

Then run `quarto render` to rebuild the site.

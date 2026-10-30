# Vignettes

Translations of the model examples in `examples` into the lingua franca.

## Purpose

Vignettes show how the lingua franca would be used in practice. Each one takes a model from `examples` and expresses it in the lingua franca, demonstrating that the specification is sufficient.

They are also where the project's test is applied: **a model should never be easier to write without the lingua franca than with it.** Each vignette is held to two numbers from its original: no more lines of model code, and no more time for a rerun. Missing either doesn't fail a vignette: it is a finding for `design`.

## Contents

One vignette per example, containing:

- The lingua franca representation of the model
- A comparison with the original: lines of model code (counted the same way as in `examples`), first-run and rerun time on the same machine, and agreement of the results within a stated tolerance
- Which parts were written as declared transitions and which needed a function or a `step()` method
- Notes on anything awkward, ambiguous, or inexpressible, as feedback to `design`

Where a model can be run under more than one paradigm, the vignette should show the interconversion and discuss what the change of paradigm does and does not preserve.

## Regenerating the scorecard

`scorecard.py`, in the root folder, regenerates every number in the scorecard: it runs the originals, checks each translation against them, times each translation under each set of kernels, and writes the lines and times into each vignette's table.

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

3. **Run it.** All of it takes a few hours, run one model at a time. For fair times, run it on a quiet machine:

    ```bash
    python scorecard.py                        # Everything
    python scorecard.py --only odin            # Only the models whose name contains "odin"
    python scorecard.py --stages timing tables # Only time Starsim, and update the tables
    ```

    The times go in `timings.json` and `timings.csv` in this folder, with every set of kernels tried, and what each run prints goes to `compare.log` in each vignette's folder and `run.log` in each example's folder. It stops short of the text: if a result changes, `compare.py` fails, and the Results row of the vignette's table is updated by hand.

Then run `quarto render` to rebuild the site.

## Relationship to other folders

- Sources its models from `examples`.
- Tests, and generates feedback for, the specifications in `design`.
- Provides the source for the `webapp` comparisons folder.

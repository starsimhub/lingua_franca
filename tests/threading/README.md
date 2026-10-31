# BLAS threads in Starsim

Tests whether setting `OPENBLAS_NUM_THREADS` and similar above 1 is ever worthwhile for Starsim. On an Intel i7-12700H, extra threads never helped Starsim itself, and this checks whether that is true on other machines.

## Running it

On Linux, macOS, or Windows, with Python 3.11 or later:

```bash
python run.py
```

That is all: it installs Starsim from the `v4` branch and what it needs into a `.venv` folder here, compiles Starsim's kernels, runs the test, and prints the report. It also saves the results in `results/`.

The first run spends about 5 minutes installing and compiling. The test then takes about 10 minutes, or about 30 on a Linux machine with two kinds of core. Close other work first, since each setting can use all the CPUs.

| Command | What it does |
|---|---|
| `python run.py --reps 1` | A quick check, with one repeat of each setting |
| `python run.py --update` | Installs from scratch, for the latest Starsim v4 |
| `python run.py --report` | Prints the report from the results so far |
| `python run.py --name "Lab server"` | Names this machine in the report |

## Running it on GitHub

To test platforms you don't have, go to Actions > BLAS threads > Run workflow. It only runs when started this way. The summary page of the run shows one table per platform, and `report.md` can be downloaded from its artifacts.

The platforms are in `.github/workflows/blas_threads.yml`. If a platform fails, for example because a package has no build for it, the others still finish.

GitHub's runners are shared virtual machines with 2 to 4 CPUs, so small differences mean little there, and they can't show what happens with many cores or two kinds of core. Use `run.py` on a real machine for those.

## What it measures

Each setting runs in a fresh process, since BLAS reads its thread count when it loads. The settings are interleaved, and the best of the repeats is kept. The settings are 1, 2, 4, and 8 threads (up to the number of CPUs), and `default`, with nothing set. On Linux, a CPU with two kinds of core is also tested on each kind alone.

| Cases | Why |
|---|---|
| Imports | Starting more threads costs time at import |
| Agent sim | Barely uses BLAS, so it shows the cost of idle threads |
| Compartmental sims | A dense contact matrix over more than 16 places is Starsim's one hot use of BLAS (`dgemv`) |
| Matrix × vector and matrix × matrix | BLAS alone, to show where threads start to help |
| `ss.parallel()` | Several processes at once, each with its own threads |

## Reading the results

The last column of each table is the best time with any other thread count, as a share of the time with 1 thread, so below 1 means threads helped. Look for values well below 1 in the Starsim rows, not only the raw BLAS ones. Differences under about 10% are usually noise. On macOS, NumPy and SciPy use Apple's Accelerate, which the report can't see, so it says `BLAS: none found`; the thread limit is still set.

The runs use Starsim's Rust kernels where they get built (which needs a Rust toolchain, as GitHub's runners have), and otherwise its Numba ones; each table says which. Both call the same BLAS function. Starsim is installed without JAX, which this test doesn't use and which has no build for macOS on Intel or Windows on ARM.

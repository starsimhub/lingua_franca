# epidemics

- **Version:** 0.5.0, from GitHub (the `v0.5.0` tag, commit `ac11c6f`), with odin 1.2.7, `cinterpolate` 1.0.2, `ring` 1.0.8, and BH 1.90.0-1. epidemics is not on CRAN.
- **Source:** https://github.com/epiverse-trace/epidemics (MIT), documented at https://epiverse-trace.github.io/epidemics/
- **Needs:** R (4.6.1 was used, at `/usr/bin/R`), `git`, and a C compiler (gcc 13.3.0): the package's models are written in odin, whose C code is in the package and is compiled when the package is installed

`requirements.txt` lists what is in `lib/`. epidemics' other dependencies were already in R's own libraries, so they were not installed again: `checkmate` 2.3.4, `cli` 3.6.6, `data.table` 1.18.6.1, `glue` 1.8.1, `withr` 3.0.2, `Rcpp` 1.1.1-1.1, `RcppEigen` 0.3.4.0.2, and odin's own (`deSolve` 1.42, `R6`, `jsonlite`, `digest`, `pkgbuild`).

## Build

`env.cfg` gives the repository and commit, so `lingua_franca envs install epidemics` fetches the source into `src/`, installs odin and BH from CRAN into `lib/`, and then installs epidemics from `src/` (its `local =`).

Most of the build is compiling epidemics. `lingua_franca envs check epidemics` then finds every version in `requirements.txt` and the commit in `src/`.

## The vignettes' data

Every vignette makes its contact matrix and demography from socialmixr's copy of the POLYMOD survey and the `wpp2024` package, which is on GitHub and not on CRAN (it is about 280 MB). Neither is installed here. The two models in this folder use the same three age groups (0–19, 20–39, and 40+), and their `run.py` gives the contact matrix and demography as the vignettes print them on the package website, to 7 significant figures, in place of the lines that load them.

# EpiModel

- **Version:** 2.6.2 (CRAN, published 16 September 2026), with ergm 4.12.0, tergm 4.2.2, network 1.20.0, networkDynamic 0.12.0, and statnet.common 4.13.0; every package in the private library is listed in `requirements.txt`
- **Source:** https://cran.r-project.org/package=EpiModel and https://github.com/EpiModel/EpiModel (GPL-3)
- **Needs:** R (4.6.1 was used, at `/usr/bin/R`) with a C, C++, and Fortran compiler (`gcc`, `g++`, `gfortran`), since most of the packages are built from source; nothing needs `sudo`

## Build

`lingua_franca envs install epimodel` does this, apart from the last line, which is what wrote `requirements.txt`:

```bash
mkdir -p lib bin
R_LIBS_USER=$PWD/lib Rscript -e "install.packages('EpiModel', lib='$PWD/lib', repos='https://cloud.r-project.org', Ncpus=8)" > build.log 2>&1
cat > bin/Rscript <<'END'
#!/bin/sh
# Rscript with the private EpiModel library in front (see ../README.md)
here="$(cd "$(dirname "$0")/.." && pwd)"
export R_LIBS_USER="$here/lib"
exec /usr/bin/Rscript "$@"
END
chmod +x bin/Rscript
bin/Rscript -e 'ip <- installed.packages(lib.loc=.libPaths()[1]); writeLines(sprintf("%s==%s", ip[,"Package"], ip[,"Version"]), "requirements.txt")'
```

The build takes about one minute on 8 cores (longer on a machine where all 63 packages have to be built). `bin/Rscript` is the system `Rscript` with `lib/` in front of the library path, so an example that asks for `Rscript` in this environment gets EpiModel.

## What is not in the private library

`install.packages` only installs what is missing, so `lib/` holds the 17 packages that were not already on this machine. The other 46 packages that EpiModel depends on were found in `/usr/local/lib/R/site-library` and are not listed in `requirements.txt`. The versions used were: deSolve 1.42, future 1.75.0, collections 0.3.12, RColorBrewer 1.1-3, lazyeval 0.2.3, ggplot2 4.0.3, tibble 3.3.1, rlang 1.2.0, dplyr 1.2.1, coda 0.19-4.1, Rcpp 1.1.1-1.1, digest 0.6.39, cli 3.6.6, generics 0.1.4, glue 1.8.1, lifecycle 1.0.5, magrittr 2.0.5, pillar 1.11.1, R6 2.6.1, tidyselect 1.2.1, vctrs 0.7.3, purrr 1.2.2, memoise 2.0.1, knitr 1.51, stringr 1.6.0, globals 0.19.1, listenv 1.0.0, parallelly 1.48.0, gtable 0.3.6, isoband 0.3.0, S7 0.2.2, scales 1.4.0, withr 3.0.2, pkgconfig 2.0.3, cpp11 0.5.5, evaluate 1.0.5, highr 0.12, xfun 0.57, yaml 2.3.12, cachem 1.1.0, utf8 1.2.6, farver 2.1.2, labeling 0.4.3, viridisLite 0.4.3, stringi 1.8.7, and fastmap 1.2.0. On a machine with a bare R, the same command installs all of them into `lib/`.

The optional package Rglpk is not installed (it needs the system library GLPK); ergm warns about this and uses lpSolveAPI instead, which is fine for a model of this size.

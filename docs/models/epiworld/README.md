# epiworld

- **Version:** epiworldR 0.14.0.0, from CRAN (published 28 March 2026), which carries its own copy of the epiworld C++ core (also 0.14.0); every package in the private library is listed in `requirements.txt`
- **Source:** https://github.com/UofUEpiBio/epiworldR and https://cran.r-project.org/package=epiworldR (MIT); the C++ core is https://github.com/UofUEpiBio/epiworld
- **Needs:** R (4.6.1 was used, at `/usr/bin/R`) and a C++17 compiler with OpenMP (g++ 13.3.0): the package is built from source

epiworld has two front ends over the same C++ core, epiworldR and epiworldpy. These examples use epiworldR, since the vignettes they come from are epiworldR's and it is the one on CRAN.

## Build

`lingua_franca envs install epiworld` does this:

```bash
mkdir -p lib bin
Rscript -e 'install.packages("epiworldR", lib="lib", repos="https://packagemanager.posit.co/cran/2026-10-13")'
cat > bin/Rscript <<'END'
#!/bin/sh
here="$(cd "$(dirname "$0")/.." && pwd)"
export R_LIBS_USER="$here/lib"
exec /usr/bin/Rscript "$@"
END
chmod +x bin/Rscript
```

The build takes under half a minute. `bin/Rscript` is a wrapper that puts `lib/` at the front of R's library path, so an example that runs `Rscript` in this environment finds epiworldR.

## What is not in the private library

epiworldR's only dependency outside base R is `cpp11` (0.5.5), which it compiles against and which was already in `/usr/local/lib/R/site-library`, so `lib/` holds epiworldR alone. On a machine without it, `install.packages` adds it to `lib/` as well. The packages it suggests (`data.table`, `netplot`, `igraph`, `DiagrammeR`, `quarto`, `tinytest`) are not needed by these examples and are not installed.

The source tarball, `src/epiworldR_0.14.0.0.tar.gz`, was fetched by hand from the same CRAN snapshot to read the C++ core; the build does not need it.

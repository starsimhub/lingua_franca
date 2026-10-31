# odin

- **Version:** 1.2.7, from CRAN (published 7 February 2025), with `dde` 1.0.7, `cinterpolate` 1.0.2, and `ring` 1.0.8. This is the classic `odin`, not `odin2`.
- **Source:** https://github.com/mrc-ide/odin and https://cran.r-project.org/package=odin (MIT)
- **Needs:** R (4.6.1 was used, at `/usr/bin/R`) and a C compiler (gcc 13.3.0): odin writes C code for each model and compiles it when the model is loaded. Discrete-time models also need `dde`, which odin only suggests, so it is installed separately.

`requirements.txt` lists what is in `lib/`. odin's other dependencies were already in R's own libraries, so they were not installed again: `deSolve` 1.42, `R6` 2.6.1, `jsonlite` 2.0.0, `digest` 0.6.39, `glue` 1.8.1, `withr`, and `pkgbuild` 1.4.8 (used to compile; with `cli`, `callr`, `processx`, `desc`). On a machine without them, `install.packages` adds them to `lib/` as well.

## Build

`lingua_franca envs install odin` does this:

```bash
mkdir -p lib bin
Rscript -e 'install.packages(c("odin", "dde"), lib="lib", repos="https://packagemanager.posit.co/cran/2026-10-13")'
cat > bin/Rscript <<'END'
#!/bin/sh
here="$(cd "$(dirname "$0")/.." && pwd)"
export R_LIBS_USER="$here/lib"
exec /usr/bin/Rscript "$@"
END
chmod +x bin/Rscript
```

The build takes about a minute. `bin/Rscript` is a wrapper that puts `lib/` at the front of R's library path, so an example that runs `Rscript` in this environment finds odin.

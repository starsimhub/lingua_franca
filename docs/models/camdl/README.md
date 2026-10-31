# camdl

- **Version:** commit `e8219d1c` (`v0.1.0-alpha-1734`), 13 October 2026
- **Source:** https://github.com/vsbuffalo/camdl (MIT)
- **Needs:** OCaml 5.2 with `dune`, and Rust with `cargo`; `install.sh` in the camdl repository sets both up without `sudo`

## Build

`lingua_franca envs install camdl` does this:

```bash
git init src
git -C src fetch --depth 1 https://github.com/vsbuffalo/camdl e8219d1cda27a27461795753a20a253514fdb1c2
git -C src checkout FETCH_HEAD
make -C src build
mkdir -p bin
install -m 755 src/rust/target/release/camdl bin/camdl
install -m 755 src/ocaml/_build/default/bin/camdlc.exe bin/camdlc
install -m 755 src/ocaml/_build/default/bin/camdlc.exe bin/camdlc-$(bin/camdl --version | sed 's/.*+\([0-9a-f]*\).*/\1/')
```

The build takes about two minutes. `camdl` looks for the model checker as `camdlc-<commit>` next to itself, which is what the last line is for. The commit is abbreviated as git abbreviates it when camdl is built, which `camdl --version` shows: `e8219d1` when only the one commit is fetched, as here, and `e8219d1c` from a full clone.

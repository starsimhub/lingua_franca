"""
Build and check the environments of the frameworks.

    lingua_franca envs check                 # Check all of them
    lingua_franca envs install               # Install whichever are missing or incomplete
    lingua_franca envs install odin siminf   # Install some of them
    lingua_franca envs key odin sbml         # A hash of their recipes, for caching what they build

The recipe of each is in `docs/models/<framework>`: `env.cfg` says how to build it, `requirements.txt`
lists the exact versions, and `README.md` says what it needs. What is built goes in `_envs/<framework>`,
with what the build prints in `build.log`; `python scripts/clean_envs.py` deletes it. An install needs
`uv` (for the Python ones), `Rscript` and compilers (for the R ones), `dune` and `cargo` (for camdl),
and `git`.

In `env.cfg`, `kind` is `python`, `r`, or `camdl`. A Python environment has the version of Python; an R
one has the `packages` to ask CRAN for (`requirements.txt` lists what that installs); and a repository
is fetched into `src/` at one `commit`, with `local` the folder in it to install.
"""
import os
import sys
import json
import shutil
import hashlib
import argparse
import subprocess
import configparser
import sciris as sc

root = sc.thispath(__file__).parent.parent # The top of this repo
built = root / '_envs' # What is built, none of it committed
recipes = root / 'docs' / 'models' # The recipe of each framework
recipe_files = ['env.cfg', 'requirements.txt'] # What a build depends on
cran = 'https://packagemanager.posit.co/cran/2026-10-13' # A snapshot of CRAN, so the R environments stay the versions in requirements.txt


def load_envs():
    """ Read every recipe: a dict of each framework's `env.cfg` """
    out = dict()
    for path in sorted(recipes.glob('*/env.cfg')):
        parser = configparser.ConfigParser()
        parser.read(path)
        out[path.parent.name] = dict(parser['env'])
    return out


envs = load_envs()

# The command in bin/ that shows an environment has been built
commands = dict(python='python', r='Rscript', camdl='camdl')

# What each kind of environment needs in order to be installed
needs = dict(python=['uv'], r=['Rscript'], camdl=['make', 'dune', 'cargo'])

# bin/Rscript: the system Rscript, with the environment's own library in front
r_wrapper = '''#!/bin/sh
here="$(cd "$(dirname "$0")/.." && pwd)"
export R_LIBS_USER="$here/lib"
exec {rscript} "$@"
'''

# Lists the packages in an R environment's library in the format of requirements.txt
r_freeze = 'ip <- installed.packages(lib.loc="lib"); writeLines(sprintf("%s==%s", ip[,"Package"], ip[,"Version"]))'


def environ(folder):
    """ The environment variables for a command: uv and R are pointed at the folder """
    return dict(os.environ, VIRTUAL_ENV=str(folder), R_LIBS_USER=str(folder / 'lib'))


def run(folder, *cmd):
    """ Run a command in an environment's folder, adding what it prints to build.log """
    with open(folder / 'build.log', 'a') as log:
        log.write(f'\n$ {" ".join(cmd)}\n')
        log.flush()
        subprocess.run(cmd, cwd=folder, env=environ(folder), check=True, stdout=log, stderr=subprocess.STDOUT)
    return


def output(folder, *cmd):
    """ Run a command in an environment's folder, and return what it prints """
    out = subprocess.run(cmd, cwd=folder, env=environ(folder), check=True, capture_output=True, text=True)
    return out.stdout.strip()


def versions(text):
    """ Parse lines of `name==version` into a dict; a package installed from a folder has the version "local" """
    out = dict()
    for line in text.splitlines():
        if ' @ ' in line:
            out[line.split(' @ ')[0]] = 'local'
        elif '==' in line:
            name, version = line.split('==')
            out[name] = version
    return out


def camdl_commit(camdl):
    """ The commit that a camdl executable was built from, abbreviated as it is in `camdl 0.1.0+e8219d1c (2026-10-13)` """
    version = output(camdl.parent, str(camdl), '--version')
    return version.split('+')[1].split()[0]


def check(name):
    """ Return what is wrong with an environment, as a list of strings (empty if nothing is) """
    spec = envs[name]
    kind = spec['kind']
    folder = built / name
    if not (folder / 'bin' / commands[kind]).exists():
        return ['not installed']

    problems = []
    if kind == 'camdl':
        short = camdl_commit(folder / 'bin' / 'camdl')
        if not spec['commit'].startswith(short):
            problems.append(f'camdl is commit {short}, not {spec["commit"][:8]}')
        if not (folder / 'bin' / f'camdlc-{short}').exists():
            problems.append(f'camdlc-{short} is missing')
    else:
        if kind == 'python':
            have = versions(output(folder, 'uv', 'pip', 'freeze'))
        else:
            have = versions(output(folder, str(folder / 'bin' / 'Rscript'), '-e', r_freeze))
        want = versions(sc.loadtext(recipes / name / 'requirements.txt'))
        for package, version in want.items():
            if have.get(package) != version:
                problems.append(f'{package} is {have.get(package, "missing")}, not {version}')

    if 'commit' in spec:
        head = 'missing'
        if (folder / 'src').exists():
            head = output(folder, 'git', '-C', 'src', 'rev-parse', 'HEAD')
        if head != spec['commit']:
            problems.append(f'src is {head[:8]}, not {spec["commit"][:8]}')

    return problems


def install(name):
    """ Build an environment from its recipe """
    spec = envs[name]
    kind = spec['kind']
    folder = built / name
    folder.mkdir(parents=True, exist_ok=True)
    tools = needs[kind] + ['git']*('commit' in spec)
    for tool in tools:
        if not shutil.which(tool):
            raise RuntimeError(f'"{tool}" was not found on the PATH (see {recipes / name / "README.md"} for what {name} needs)')

    if 'commit' in spec and not (folder / 'src').exists(): # Fetch the one commit, not the whole history
        run(folder, 'git', 'init', 'src')
        run(folder, 'git', '-C', 'src', 'fetch', '--depth', '1', spec['repo'], spec['commit'])
        run(folder, 'git', '-C', 'src', 'checkout', 'FETCH_HEAD')

    if kind == 'python':
        run(folder, 'uv', 'venv', '--python', spec['python'], '--allow-existing', '.')
        pins = [line for line in sc.loadtext(recipes / name / 'requirements.txt').splitlines() if '==' in line]
        run(folder, 'uv', 'pip', 'install', *pins)
        if 'local' in spec:
            run(folder, 'uv', 'pip', 'install', './' + spec['local'])

    elif kind == 'r':
        rscript = shutil.which('Rscript')
        packages = ', '.join([f'"{package}"' for package in spec['packages'].split()])
        (folder / 'lib').mkdir(exist_ok=True)
        (folder / 'bin').mkdir(exist_ok=True)
        run(folder, rscript, '-e', f'install.packages(c({packages}), lib="lib", repos="{cran}", Ncpus={os.cpu_count()})')
        wrapper = folder / 'bin' / 'Rscript'
        wrapper.write_text(r_wrapper.format(rscript=rscript))
        wrapper.chmod(0o755)

    elif kind == 'camdl':
        camdl = folder / 'src/rust/target/release/camdl'
        camdlc = folder / 'src/ocaml/_build/default/bin/camdlc.exe'
        if shutil.which('opam'): # As in CI; camdl's install.sh sets up a machine without it
            run(folder / 'src/ocaml', 'opam', 'install', '.', '--deps-only', '--yes')
        run(folder, 'make', '-C', 'src', 'build')
        outputs = {'camdl':camdl, 'camdlc':camdlc, f'camdlc-{camdl_commit(camdl)}':camdlc} # camdl looks for the checker as camdlc-<commit>
        (folder / 'bin').mkdir(exist_ok=True)
        for command, path in outputs.items():
            dest = folder / 'bin' / command
            dest.unlink(missing_ok=True) # dune builds camdlc read-only, so a copy of it cannot be overwritten
            shutil.copy(path, dest)
            dest.chmod(0o755)

    return


def key(names):
    """ A hash of the recipes of some environments: what they build changes only when this does """
    found = dict(cran=cran)
    for name in names:
        found[name] = {file:(recipes / name / file).read_text() for file in recipe_files if (recipes / name / file).exists()}
    return hashlib.sha256(json.dumps(found, sort_keys=True).encode()).hexdigest()[:16]


def report(name):
    """ Print whether an environment is all there, and return whether it is """
    problems = check(name)
    if problems:
        sc.printred(f'{name:10s}' + '; '.join(problems))
    else:
        sc.printgreen(f'{name:10s}ok')
    return not problems


def main(args=None):
    parser = argparse.ArgumentParser(prog='lingua_franca envs', description='Build and check the environments of the frameworks')
    parser.add_argument('command', choices=['install', 'check', 'key'])
    parser.add_argument('names', nargs='*', help='which environments (default: all)')
    args = parser.parse_args(args)

    names = args.names if args.names and args.names != ['all'] else list(envs)
    unknown = [name for name in names if name not in envs]
    if unknown:
        parser.error(f'unknown environments {unknown}; the choices are {list(envs)}')

    if args.command == 'key':
        print(key(names))
        return 0

    ok = True
    for name in names:
        if args.command == 'install' and check(name):
            print(f'{name:10s}installing...')
            try:
                with sc.timer(name):
                    install(name)
            except (RuntimeError, subprocess.CalledProcessError) as E:
                sc.printred(f'{name:10s}failed: {E} (see {built / name / "build.log"})')
        ok = report(name) and ok
    return not ok


if __name__ == '__main__':
    sys.exit(main())

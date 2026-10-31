"""
Install, uninstall, and check the environments of the frameworks.

    python _envs/envs.py check                 # Check all of them
    python _envs/envs.py install               # Install whichever are missing or incomplete
    python _envs/envs.py install odin siminf   # Install some of them
    python _envs/envs.py uninstall camdl       # Delete what an install builds
    python _envs/envs.py uninstall all

Each environment is the folder `_envs/<framework>`, whose `README.md` says what it needs and
how it was built by hand; this script follows the same steps. An install needs `uv` (for the
Python ones), `Rscript` and compilers (for the R ones), `dune` and `cargo` (for camdl), and
`git`. What it prints goes to `build.log` in the folder. An uninstall deletes everything in
the folder except the recipe (`README.md` and `requirements.txt`).
"""
import os
import sys
import shutil
import argparse
import subprocess
import sciris as sc

root = sc.thispath(__file__)
keep = ['README.md', 'requirements.txt', 'renv.lock'] # The recipe: the files that .gitignore does not ignore
cran = 'https://cloud.r-project.org'

# A Python environment has the version of Python; an R one has the packages to ask CRAN for
# (requirements.txt lists what that installs); and a repository is fetched into src/ at one commit
envs = dict(
    atomica  = dict(kind='python', python='3.12'),
    camdl    = dict(kind='camdl', repo='https://github.com/vsbuffalo/camdl', commit='e8219d1cda27a27461795753a20a253514fdb1c2'),
    emulsion = dict(kind='python', python='3.9'),
    epimodel = dict(kind='r', packages=['EpiModel']),
    epipack  = dict(kind='python', python='3.12'),
    epydemix = dict(kind='python', python='3.12'),
    epymorph = dict(kind='python', python='3.12'),
    flepimop = dict(kind='python', python='3.11', repo='https://github.com/HopkinsIDD/flepiMoP', commit='ad62f2d00082de5b60e62100be7b24fddc6931da', local='src/flepimop/gempyor_pkg'),
    laser    = dict(kind='python', python='3.12'),
    memilio  = dict(kind='python', python='3.11', repo='https://github.com/SciCompMod/memilio', commit='c2c884ce430f248414099bfb901a5045c0295c26'),
    odin     = dict(kind='r', packages=['odin', 'dde']),
    sbml     = dict(kind='python', python='3.12'),
    siminf   = dict(kind='r', packages=['SimInf']),
    summer2  = dict(kind='python', python='3.11'),
)

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
    folder = root / name
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
        want = versions(sc.loadtext(folder / 'requirements.txt'))
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
    folder = root / name
    tools = needs[kind] + ['git']*('commit' in spec)
    for tool in tools:
        if not shutil.which(tool):
            raise RuntimeError(f'"{tool}" was not found on the PATH (see {folder / "README.md"} for what {name} needs)')

    if 'commit' in spec and not (folder / 'src').exists(): # Fetch the one commit, not the whole history
        run(folder, 'git', 'init', 'src')
        run(folder, 'git', '-C', 'src', 'fetch', '--depth', '1', spec['repo'], spec['commit'])
        run(folder, 'git', '-C', 'src', 'checkout', 'FETCH_HEAD')

    if kind == 'python':
        run(folder, 'uv', 'venv', '--python', spec['python'], '--allow-existing', '.')
        (folder / '.gitignore').unlink(missing_ok=True) # uv ignores the whole folder, which would hide the recipe from git
        pins = [line for line in sc.loadtext(folder / 'requirements.txt').splitlines() if '==' in line]
        run(folder, 'uv', 'pip', 'install', *pins)
        if 'local' in spec:
            run(folder, 'uv', 'pip', 'install', './' + spec['local'])

    elif kind == 'r':
        rscript = shutil.which('Rscript')
        packages = ', '.join([f'"{package}"' for package in spec['packages']])
        (folder / 'lib').mkdir(exist_ok=True)
        (folder / 'bin').mkdir(exist_ok=True)
        run(folder, rscript, '-e', f'install.packages(c({packages}), lib="lib", repos="{cran}", Ncpus={os.cpu_count()})')
        wrapper = folder / 'bin' / 'Rscript'
        wrapper.write_text(r_wrapper.format(rscript=rscript))
        wrapper.chmod(0o755)

    elif kind == 'camdl':
        camdl = folder / 'src/rust/target/release/camdl'
        camdlc = folder / 'src/ocaml/_build/default/bin/camdlc.exe'
        run(folder, 'make', '-C', 'src', 'build')
        built = {'camdl':camdl, 'camdlc':camdlc, f'camdlc-{camdl_commit(camdl)}':camdlc} # camdl looks for the checker as camdlc-<commit>
        (folder / 'bin').mkdir(exist_ok=True)
        for command, path in built.items():
            dest = folder / 'bin' / command
            dest.unlink(missing_ok=True) # dune builds camdlc read-only, so a copy of it cannot be overwritten
            shutil.copy(path, dest)
            dest.chmod(0o755)

    return


def uninstall(name):
    """ Delete everything in an environment's folder except the recipe """
    for path in (root / name).iterdir():
        if path.name not in keep:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
    return


def report(name):
    """ Print whether an environment is all there, and return whether it is """
    problems = check(name)
    if problems:
        sc.printred(f'{name:10s}' + '; '.join(problems))
    else:
        sc.printgreen(f'{name:10s}ok')
    return not problems


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Install, uninstall, and check the environments of the frameworks')
    parser.add_argument('command', choices=['install', 'uninstall', 'check'])
    parser.add_argument('names', nargs='*', help='which environments, or "all" (the default, except to uninstall)')
    args = parser.parse_args()

    names = args.names
    if names == ['all']:
        names = list(envs)
    elif not names:
        if args.command == 'uninstall':
            parser.error('say which environments to uninstall, or "all"')
        names = list(envs)
    unknown = [name for name in names if name not in envs]
    if unknown:
        parser.error(f'unknown environments {unknown}; the choices are {list(envs)}')

    ok = True
    for name in names:
        if args.command == 'check':
            ok = report(name) and ok

        elif args.command == 'uninstall':
            uninstall(name)
            print(f'{name:10s}uninstalled')

        elif args.command == 'install':
            if check(name):
                print(f'{name:10s}installing...')
                try:
                    with sc.timer(name):
                        install(name)
                except (RuntimeError, subprocess.CalledProcessError) as E:
                    sc.printred(f'{name:10s}failed: {E} (see {root / name / "build.log"})')
            ok = report(name) and ok

    sys.exit(not ok)

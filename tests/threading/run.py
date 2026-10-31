"""
Test whether BLAS threads above 1 are worthwhile for Starsim on this machine, on Linux, macOS, or Windows. It needs only
Python 3.11 or later: everything else is installed into a .venv folder here, leaving the rest of the system alone.

    python run.py                # The full test, then the report (see README.md for how long it takes)
    python run.py --reps 1       # A quick check, with one repeat of each setting
    python run.py --update       # Install the latest Starsim v4 first
    python run.py --report       # Print the report from the results so far, without running anything
"""
import argparse
import pathlib
import shutil
import subprocess
import sys
import venv

here = pathlib.Path(__file__).resolve().parent
starsim = 'starsim @ git+https://github.com/starsimhub/starsim@v4'
env = here/'.venv'
python = env/('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
installed = env/'installed' # Written last, so an interrupted install starts again


def install(update=False):
    if update:
        shutil.rmtree(env, ignore_errors=True)
    if not installed.exists():
        print('Installing Starsim and what it needs into .venv...', flush=True)
        venv.create(env, with_pip=True, clear=True)
        subprocess.run([python, '-m', 'pip', 'install', '--quiet', '-r', here/'requirements.txt'], check=True)
        subprocess.run([python, '-m', 'pip', 'install', '--quiet', '--no-deps', starsim], check=True) # Without JAX, which it doesn't need here, and which has no build for some platforms
        installed.touch()
    return


def report(folder):
    """ Combine the reports in a folder, including its subfolders """
    paths = sorted(pathlib.Path(folder).rglob('*.md'))
    print('# BLAS threads in Starsim, by platform\n')
    print('\n'.join(path.read_text(encoding='utf-8') for path in paths) or 'No results found')
    return


def main():
    if sys.version_info < (3, 11):
        sys.exit(f'Starsim needs Python 3.11 or later, but this is {sys.version.split()[0]}')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--reps', type=int, default=5, help='Times to run each setting')
    parser.add_argument('--name', default=None, help='Name of this platform in the results (default: from the platform)')
    parser.add_argument('--out', default=here/'results', help='Folder for the results')
    parser.add_argument('--update', action='store_true', help='Install from scratch, for the latest Starsim v4')
    parser.add_argument('--report', action='store_true', help='Only print the report from the results in the --out folder')
    args = parser.parse_args()

    if not args.report:
        install(args.update)
        cmd = [python, here/'blas_test.py', '--reps', str(args.reps), '--out', args.out] + (['--name', args.name] if args.name else [])
        subprocess.run(cmd, check=True)
        print(f'\nResults saved in {args.out}\n')
    report(args.out)
    return


if __name__ == '__main__':
    main()

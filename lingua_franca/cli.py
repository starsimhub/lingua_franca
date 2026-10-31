"""
Run the benchmark or the tests of this repo. Anything else on the line goes to what is being run.

    lingua_franca benchmark --only odin     # See `lingua_franca benchmark --help`
    lingua_franca test conversion -n auto   # With pytest's options
    lingua_franca test threading --reps 1   # With the options of tests/threading/run.py
    lingua_franca test                      # Everything
"""
import sys
import argparse
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parent.parent # The top of this repo
suites = ['conversion', 'switching', 'threading']


def run_tests(which, extra):
    """ Run the pytest suites, then the threading test, and give the exit code: 0 if everything passed """
    suite_list = suites if which == 'all' else [which]
    tests = root/'tests'
    pytest_suites = [suite for suite in suite_list if suite != 'threading']
    codes = []
    if pytest_suites:
        codes.append(subprocess.run([sys.executable, '-m', 'pytest', *pytest_suites, *extra], cwd=tests).returncode)
    if 'threading' in suite_list:
        args = extra if which == 'threading' else [] # With all the suites, the options are pytest's
        codes.append(subprocess.run([sys.executable, 'run.py', *args], cwd=tests/'threading').returncode)
    return max(codes)


def main(args=None):
    parser = argparse.ArgumentParser(prog='lingua_franca', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('benchmark', add_help=False, help='regenerate the lines, times, and comparisons of every model')
    test = commands.add_parser('test', help='run the tests')
    test.add_argument('which', nargs='?', choices=suites + ['all'], default='all', help='the tests to run (default: all)')
    args, extra = parser.parse_known_args(args)
    if args.command == 'benchmark':
        from . import benchmark # Only here, since it needs Sciris and the repo's examples
        return benchmark.main(extra)
    return run_tests(args.which, extra)


if __name__ == '__main__':
    sys.exit(main())

"""
Shared helpers for the `run.py` of each example: every example writes the same
two files, whatever framework it is written in.

    reference/results.csv   One row per time, series, and value (with low and high, for a summary of many runs)
    reference/timing.json   The wall-clock time of a first run and of a rerun, and the machine they were measured on

The benchmark needs only the timing, so it sets BENCHMARK_QUICK: a `run.py` then makes as
few runs as it can, and the reference results already in the repository are left alone.
"""
import os
import csv
import json
import time
import platform
import subprocess

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
quick = bool(os.environ.get('BENCHMARK_QUICK'))
time_budget = 3 # Seconds of reruns to time, at most
least_time = 1 # Seconds to spend timing, at least, however many runs that takes
most_runs = 100 # Runs to time, once `least_time` has been spent


def env_path(framework):
    """ The PATH with a framework's environment (`_envs/<framework>/bin`) in front """
    return os.path.join(root, '_envs', framework, 'bin') + os.pathsep + os.environ['PATH']


def run(cmd, framework, cwd=None):
    """ Run a command in a framework's environment, and return what it prints """
    env = dict(os.environ, PATH=env_path(framework))
    out = subprocess.run(cmd, cwd=cwd, env=env, check=True, capture_output=True, text=True)
    return out.stdout


def runs(n, fewest=3):
    """ How many runs to make: n for the reference results, or a few if they are only for the timing """
    return min(n, fewest) if quick else n


first_run = dict() # The first call of the latest time_run(), which write_timing() records


def repeat(func, budget=time_budget, least=least_time, most=most_runs):
    """ The best time in seconds of calling a function until the budget is spent, or sooner after `most` calls if `least` seconds have been spent; there is always at least one call """
    best, n, spent = float('inf'), 0, 0
    while not n or spent < least or (spent < budget and n < most):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        best, n, spent = min(best, elapsed), n + 1, spent + elapsed
    return best


def time_run(func):
    """ The best time in seconds of repeated calls of a function, after one first call, which is kept in `first_run` """
    start = time.perf_counter()
    func()
    first_run['seconds'] = time.perf_counter() - start
    return repeat(func)


def write_results(folder, rows):
    """ Write the results, unless they are from a quick run: a list of dicts with keys time, series, value, and optionally low and high """
    path = os.path.join(folder, 'reference', 'results.csv')
    if quick:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['time', 'series', 'value', 'low', 'high'], restval='')
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_timing(folder, rerun, what, first=None):
    """ Write the time of a first run (by default, the first call of the latest time_run()) and of a rerun, with what was timed and where """
    path = os.path.join(folder, 'reference', 'timing.json')
    first = first_run['seconds'] if first is None else first
    info = dict(first=round(first, 5), rerun=round(rerun, 5), product=what, machine=platform.processor() or platform.machine(), cpus=os.cpu_count(), system=platform.platform())
    with open(path, 'w') as f:
        json.dump(info, f, indent=2)
        f.write('\n')
    return path


def read_results(folder):
    """ Read the results back as `{series: (times, values)}` """
    out = dict()
    with open(os.path.join(folder, 'reference', 'results.csv')) as f:
        for row in csv.DictReader(f):
            times, values = out.setdefault(row['series'], ([], []))
            times.append(float(row['time']))
            values.append(float(row['value']))
    return out

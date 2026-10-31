"""
Test whether BLAS threads above 1 are worthwhile for Starsim on this machine: each thread count (and, on a Linux CPU
with two kinds of core, each kind) runs in fresh processes, interleaved, and the best of the repeats is kept.

Use run.py rather than this file: it installs what this needs first.
"""
import argparse
import json
import os
import pathlib
import platform
import subprocess
import sys
import time

os.environ.setdefault('STARSIM_UNCOMPILED_WARNING', '0') # It's compiled below, and the note would go into the report

start = time.perf_counter()
import numpy as np
import_numpy = time.perf_counter() - start
import scipy.linalg # Numba's np.dot uses SciPy's BLAS, which can be a separate library from NumPy's
import sciris as sc
import starsim as ss
import_starsim = time.perf_counter() - start

thread_vars = ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'SCIRIS_NUM_THREADS']
cases = ['import_numpy', 'import_starsim', 'agents', 'comp32', 'comp128', 'comp512', 'dot128', 'dot512', 'dot2000', 'matmul1000', 'parallel']
labels = dict(
    import_numpy   = 'Import NumPy',
    import_starsim = 'Import Starsim (and NumPy, SciPy, Sciris)',
    agents         = 'Agent sim, 200k agents, 100 steps',
    comp32         = 'Compartmental sim, 32 places',
    comp128        = 'Compartmental sim, 128 places',
    comp512        = 'Compartmental sim, 512 places',
    dot128         = 'Matrix × vector, size 128, 200k times',
    dot512         = 'Matrix × vector, size 512, 20k times',
    dot2000        = 'Matrix × vector, size 2000, 500 times',
    matmul1000     = 'Matrix × matrix, size 1000, 5 times',
    parallel       = 'ss.parallel(), 4 sims',
)


def agent_sim(n_agents=200_000):
    return ss.Sim(diseases='sir', networks='random', n_agents=n_agents, start=2000, stop=2100, verbose=0)


def timed(func):
    t = time.perf_counter()
    func()
    return time.perf_counter() - t


def compartmental(n, stop):
    """ A disease in n places with a dense contact matrix, the one hot path in Starsim that uses BLAS (above 16 places) """
    rng = np.random.default_rng(1)
    matrix = rng.random((n, n))
    matrix /= matrix.sum(axis=1, keepdims=True)
    S, I, R = ss.states('S I R')
    sir = ss.Disease(infection=ss.Transition(S, I, rate=0.3*I), recovery=ss.Transition(I, R, dur=10), init_n=dict(I=ss.by(place=[10] + [0]*(n - 1))), name='sir')
    sim = ss.Sim(sir.stratify(place=[f'p{i}' for i in range(n)], kind='space'), networks=ss.contacts(matrix, dims='place'), total_pop=n*1000, unit='day', stop=stop, solver='ode', verbose=0)
    sim.init()
    return timed(sim.run)


def matvec(n, reps):
    A = np.random.default_rng(0).random((n, n))
    v = np.ones(n)
    def run():
        for _ in range(reps):
            A @ v
    return timed(run)


def run_cases():
    """ Run every case once, in this process; the first of each sim, which may compile, is not timed """
    agent_sim(1000).run()
    compartmental(32, 10)
    A = np.random.default_rng(0).random((1000, 1000))
    return dict(
        import_numpy   = import_numpy,
        import_starsim = import_starsim,
        agents         = timed(agent_sim().run),
        comp32         = compartmental(32, 60_000),
        comp128        = compartmental(128, 30_000),
        comp512        = compartmental(512, 6000),
        dot128         = matvec(128, 200_000),
        dot512         = matvec(512, 20_000),
        dot2000        = matvec(2000, 500),
        matmul1000     = timed(lambda: [A @ A for _ in range(5)]),
        parallel       = timed(lambda: ss.parallel([agent_sim(100_000) for _ in range(4)], n_cpus=min(4, os.cpu_count()), verbose=0)),
    )


def core_sets():
    """ The sets of CPUs to compare: all of them, and on Linux with two kinds of core (by top speed), each kind """
    sets = {'all':None}
    if sys.platform == 'linux':
        speeds = {}
        for cpu in os.sched_getaffinity(0):
            try:
                speed = int(pathlib.Path(f'/sys/devices/system/cpu/cpu{cpu}/cpufreq/cpuinfo_max_freq').read_text())
                speeds.setdefault(speed, []).append(cpu)
            except OSError:
                return sets # Most virtual machines don't say
        kinds = {} # Speeds within 10% are one kind: the fastest cores of a CPU can differ slightly
        for speed in sorted(speeds, reverse=True):
            top = next((top for top in kinds if speed > 0.9*top), speed)
            kinds.setdefault(top, []).extend(speeds[speed])
        if len(kinds) > 1:
            for top,cpus in kinds.items():
                sets[f'{top/1e6:g} GHz'] = sorted(cpus)
    return sets


def run_one(threads, cpus):
    """ Run the cases in a fresh process, since BLAS reads its thread count when it loads """
    env = {k:v for k,v in os.environ.items() if k not in thread_vars}
    if threads != 'default':
        env.update({key:str(threads) for key in thread_vars[:-2]})
    cmd = [sys.executable, __file__, '--case']
    if cpus:
        cmd = ['taskset', '-c', ','.join(map(str, cpus))] + cmd
    out = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
    if out.returncode:
        raise RuntimeError(f'threads={threads}, cpus={cpus} failed:\n{out.stderr[-2000:]}')
    return json.loads(out.stdout.strip().splitlines()[-1])


def describe():
    """ What is being tested """
    import threadpoolctl
    info = dict(platform=platform.platform(), machine=platform.machine(), processor=platform.processor(), cpus=os.cpu_count(), python=platform.python_version(),
                numpy=np.__version__, scipy=scipy.__version__, numba=__import__('numba').__version__, starsim=ss.__version__, kernels=ss.compile_status().engine if hasattr(ss, 'compile_status') else 'numba')
    if sys.platform == 'linux':
        for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                info['processor'] = line.split(':')[1].strip()
                break
    elif sys.platform == 'darwin':
        info['processor'] = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True).stdout.strip()
    A = np.ones((200, 200))
    A @ A # So that the BLAS libraries are loaded
    pools = threadpoolctl.threadpool_info()
    info['blas'] = sorted({f"{p.get('internal_api')} {p.get('version') or ''} ({p.get('num_threads')} threads, {p.get('architecture') or 'unknown architecture'})" for p in pools})
    return info


def table(info, results):
    """ The best time of each case for each setting, as Markdown """
    keys = list(results)
    lines = [f"## {info['name']}", '', f"{info['processor']}, {info['cpus']} CPUs, {info['platform']}, Python {info['python']}, NumPy {info['numpy']}, SciPy {info['scipy']}, Numba {info['numba']}, Starsim {info['starsim']}, {info['kernels']} kernels, best of {info['reps']}", '']
    lines += [f"BLAS: {'; '.join(info['blas']) or 'none found'}", '']
    lines += ['| Seconds | ' + ' | '.join(keys) + ' | Best threaded vs 1 thread |', '|---|' + '---:|'*(len(keys) + 1)]
    for case in cases:
        best = {key:min(run[case] for run in results[key]) for key in keys}
        ones = [key for key in keys if key.endswith('threads=1')]
        threaded = [key for key in keys if not key.endswith('threads=1')]
        ratios = [min(best[key] for key in threaded if key.split(', ')[0] == one.split(', ')[0])/best[one] for one in ones]
        lines.append(f"| {labels[case]} | " + ' | '.join(f'{best[key]:.3f}' for key in keys) + f" | {min(ratios):.2f} |")
    lines += ['', 'The last column is the best time with any other thread count, as a share of the time with 1 thread: below 1 means more threads helped. Differences under about 10% are usually noise, especially on shared runners.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--reps', type=int, default=5, help='Times to run each setting')
    parser.add_argument('--name', default=None, help='Name of this platform in the results (default: from the platform)')
    parser.add_argument('--out', default='results', help='Folder for the results')
    parser.add_argument('--case', action='store_true', help=argparse.SUPPRESS) # One process of the run
    args = parser.parse_args()

    if args.case:
        print(json.dumps(run_cases()))
        return

    info = describe()
    info['name'] = args.name or f"{platform.system()} {platform.machine()}"
    info['reps'] = args.reps
    print(json.dumps(info, indent=2), flush=True)
    n_cpus = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else os.cpu_count()
    levels = [n for n in [1, 2, 4, 8] if n <= n_cpus] + ['default']
    sets = core_sets()
    ss.compile() # Otherwise compartmental runs may use plain NumPy rather than the kernels, and so not the path being tested
    run_one(1, None) # Discarded, to fill the disk cache
    results = {}
    for rep in range(args.reps):
        for name,cpus in sets.items():
            for level in levels:
                t = time.perf_counter()
                results.setdefault(f'{name}, threads={level}', []).append(run_one(level, cpus))
                print(f'Repeat {rep + 1} of {args.reps}, {name} CPUs, threads={level}: {time.perf_counter() - t:.0f} s', flush=True)

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = info['name'].replace(' ', '_').replace('/', '_')
    (out/f'{stem}.json').write_text(json.dumps(dict(info=info, results=results), indent=2))
    report = table(info, results)
    (out/f'{stem}.md').write_text(report, encoding='utf-8')
    print(report)
    return


if __name__ == '__main__':
    main()

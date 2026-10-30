"""
Regenerate everything in the scorecard on the home page: for each model, lines of code
and run time for the original and for Starsim, and whether their results agree.

    python scorecard.py                        # Everything (a few hours)
    python scorecard.py --only odin            # Only the models whose name contains "odin"
    python scorecard.py --stages timing tables # Only some stages
    python scorecard.py --kernels rust numba   # Only some kernels

The stages, in order (see vignettes/README.md for what to install first):

    check       Check that each framework's environment in _envs/ is installed
    originals   Run each original (examples/*/*/run.py), writing its results and timing
    compare     Check each translation against those results (vignettes/*/*/compare.py)
    timing      Time each translation under each kernel set, writing vignettes/timings.json and .csv
    tables      Write the lines and times into the table of each vignette's README

Lines are counted, and times taken, as in design/18-conformance.md. The first run is a
fresh process, not counting importing Starsim and reading the model file (so not reading
data, as in the originals). A rerun is the same sim run again, already built. A rebuild
is `sim.new().run()`. Each time is the best of several.

Use --starsim to time a checkout other than the installed Starsim, and --commit to record
which commit that is if it is not a git repository.
"""
import os
import re
import ast
import csv
import sys
import json
import time
import argparse
import tempfile
import datetime
import platform
import subprocess
import sciris as sc

root = sc.thispath(__file__)
stages = ['check', 'originals', 'compare', 'timing', 'tables']
kernels = ['rust', 'numba', 'jax', 'jax-gpu'] # Every set is tried on every model, and JAX is left out where it does not apply
kernel_names = {'rust':'Rust', 'numba':'Numba', 'jax':'JAX', 'jax-gpu':'JAX on a GPU'}
n_rounds = 3 # Fresh processes for each kernel set, taken in turn
n_reruns = 5 # Reruns in each one
slow = 10 # A run over this many seconds gets fewer of both
timeout = 7200 # Seconds for any one command
data = root / 'vignettes' / 'timings.json'

runs = { # What one run is, where it is not the variable `sim` in the model file
    'emulsion/sir': dict(sim='compartment'), # The original timed is the compartmental one
    'flepimop/vaccine_scenarios': dict(code='ss.parallel(runs(verbose=0), parallel=False)'), # The original timed is the 30 runs
    'odin/stochastic_sir_arrays': dict(code='ss.parallel(sim.new(verbose=0), n_runs=100, parallel=False)'), # The original timed is 100 groups
}


def list_models(only=None):
    """ The name of every model, e.g. "odin/seir_array" """
    names = sorted(f'{path.parent.parent.name}/{path.parent.name}' for path in (root/'examples').glob('*/*/meta.yaml'))
    return [name for name in names if not only or only in name]


def model_file(name):
    """ The file holding the Starsim version of a model """
    folder = root / 'vignettes' / name
    path = folder / 'model.py'
    return path if path.exists() else next(path for path in sorted(folder.glob('*.py')) if path.name != 'compare.py')


def count_lines(path):
    """ Lines of model code: no blank lines, comments, docstrings, imports, or `__main__` block, and a line over 100 characters counts twice """
    src = sc.loadtext(path)
    skip = set()
    for node in ast.walk(ast.parse(src)):
        is_import = isinstance(node, (ast.Import, ast.ImportFrom))
        is_doc = isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        is_main = isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and getattr(node.test.left, 'id', None) == '__name__'
        if is_import or is_doc or is_main:
            skip.update(range(node.lineno, node.end_lineno + 1))
    lengths = [len(line.rstrip()) for i,line in enumerate(src.splitlines(), 1) if i not in skip and line.strip() and not line.strip().startswith('#')]
    return sum(2 if length > 100 else 1 for length in lengths)


def command(cmd, cwd=root, env=None, log=None):
    """ Run a command, returning whether it worked and what it printed """
    env = dict(os.environ, MPLBACKEND='agg', STARSIM_SHOW='0', PYTHONDONTWRITEBYTECODE='1', **(env or {}))
    try:
        out = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        ok, text = out.returncode == 0, out.stdout + out.stderr
    except subprocess.TimeoutExpired:
        ok, text = False, f'Took over {timeout} s'
    if log:
        sc.savetext(log, text)
    return ok, text


def last_line(text):
    """ The last line of what a command printed, for a one-line error """
    lines = text.strip().splitlines()
    return lines[-1][:200] if lines else 'no output'


def run_originals(names):
    """ Run each original in its environment """
    failed = {}
    for name in names:
        print(f'Original: {name}')
        ok, text = command([sys.executable, 'run.py'], cwd=root/'examples'/name, env=dict(PYTHONPATH=''), log=root/'examples'/name/'run.log') # In their own environments
        if not ok:
            failed[name] = last_line(text)
    return failed


def run_compares(names, env):
    """ Check each translation against its original's results """
    failed = {}
    for name in names:
        print(f'Compare: {name}')
        ok, text = command([sys.executable, 'compare.py'], cwd=root/'vignettes'/name, env=env, log=root/'vignettes'/name/'compare.log')
        if not ok:
            failed[name] = last_line(text)
    return failed


def worker(name, kernel, reruns):
    """ In a fresh process: read the model, then time its first run, its reruns, and its rebuilds, printing them """
    import starsim as ss # Not timed
    import importlib.util
    used = []
    if kernel.startswith('jax'): # JAX is chosen by each sim rather than by an option
        choose = ss.solvers.choose_engine
        def forced(sim):
            sim.jax = True
            use, why = choose(sim)
            used.append((use, why))
            return use, why
        ss.solvers.choose_engine = forced
    path = model_file(name)
    os.chdir(path.parent)
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('model', path)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    run = runs.get(name, {})

    if 'code' in run:
        first = again = rebuild = lambda: eval(run['code'], dict(vars(model), ss=ss))
    else:
        base = getattr(model, run.get('sim', 'sim'))
        built = [base.new(verbose=0)]
        first = lambda: built[0].run()
        again = lambda: (built[0].restart(), built[0].run())
        rebuild = lambda: base.new(verbose=0).run()

    def timed(func):
        start = time.perf_counter()
        func()
        return time.perf_counter() - start

    out = dict(first=timed(first))
    out['rerun'] = min(timed(again) for i in range(reruns))
    out['rebuild'] = min(timed(rebuild) for i in range(reruns))
    if kernel.startswith('jax') and not any(use for use,why in used):
        out = dict(skipped=used[-1][1] if used else 'no compartmental run')
    print('TIMING ' + json.dumps(out))
    return


def kernel_env(kernel):
    """ The environment variables for a kernel set; JAX runs use the default kernels for anything it leaves to them """
    if kernel == 'jax':
        return dict(JAX_PLATFORMS='cpu')
    elif kernel == 'jax-gpu':
        return dict(JAX_PLATFORMS='gpu', XLA_PYTHON_CLIENT_PREALLOCATE='false')
    return dict(STARSIM_KERNELS=kernel)


def run_worker(name, kernel, reruns, env):
    """ One fresh process, returning its times, or why there are none """
    cmd = [sys.executable, str(root/'scorecard.py'), '--worker', name, kernel, str(reruns)]
    ok, text = command(cmd, env=dict(env, **kernel_env(kernel)))
    found = [line for line in text.splitlines() if line.startswith('TIMING ')]
    return json.loads(found[-1][7:]) if ok and found else dict(skipped=last_line(text))


def time_model(name, sets, env):
    """ Time one model under each kernel set, taking them in turn, with a first round thrown away to fill the caches """
    warm = {kernel:run_worker(name, kernel, 1, env) for kernel in sets}
    out = {kernel:val for kernel,val in warm.items() if 'skipped' in val}
    live = [kernel for kernel in sets if kernel not in out]
    longest = max([warm[kernel]['first'] for kernel in live], default=0)
    rounds, reruns = (2, 2) if longest > slow else (n_rounds, n_reruns)
    for i in range(rounds):
        for kernel in live:
            found = run_worker(name, kernel, reruns, env)
            if 'skipped' in found:
                out[kernel] = found
                continue
            best = out.setdefault(kernel, found)
            if 'skipped' not in best:
                out[kernel] = {key:min(best[key], found[key]) for key in found}
    return out


def fastest(times):
    """ The kernel set with the fastest reruns """
    done = {kernel:val for kernel,val in times.items() if 'rerun' in val}
    return min(done, key=lambda kernel: done[kernel]['rerun']) if done else None


def compile_time(env):
    """ How long Numba takes to compile the kernels, once per install: a single first run can pay this if there is no Rust """
    with tempfile.TemporaryDirectory() as tmp:
        code = 'import time, starsim as ss; start = time.perf_counter(); ss.compile(); print("SECONDS", time.perf_counter() - start)'
        ok, text = command([sys.executable, '-c', code], env=dict(env, STARSIM_KERNELS='numba', NUMBA_CACHE_DIR=tmp))
    found = re.search(r'SECONDS ([\d.]+)', text)
    return float(found.group(1)) if ok and found else None


def starsim_info(env, commit):
    """ Which Starsim is being timed """
    ok, text = command([sys.executable, '-c', 'import starsim as ss; print(ss.__version__, ss.__file__)'], env=env)
    version, path = text.split()[-2:]
    if not commit:
        commit = subprocess.run(['git', '-C', os.path.dirname(path), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    return dict(version=version, commit=commit)


def load_data():
    """ What has been measured so far """
    return sc.loadjson(data) if data.exists() else dict(models={})


def write_csv(info):
    """ Every time for every kernel set, one row each """
    with open(data.with_suffix('.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['model', 'kernels', 'first', 'rerun', 'rebuild', 'fastest', 'skipped'])
        for name,model in info['models'].items():
            for kernel,val in model['kernels'].items():
                writer.writerow([name, kernel, val.get('first'), val.get('rerun'), val.get('rebuild'), kernel == model['fastest'], val.get('skipped')])
    return


def run_timing(names, sets, env, commit):
    """ Time every model, saving as it goes """
    info = load_data()
    info.update(date=str(datetime.date.today()), starsim=starsim_info(env, commit), kernels=sets, cpus=os.cpu_count(), system=platform.platform())
    if 'numba' in sets:
        print('Timing the compiling of the Numba kernels')
        info['numba_compile'] = compile_time(env)
    for name in names:
        print(f'Timing: {name}')
        loads = [os.getloadavg()[0]]
        times = time_model(name, sets, env)
        loads.append(os.getloadavg()[0])
        info['models'][name] = dict(kernels=times, fastest=fastest(times), load=max(loads))
        info['models'] = dict(sorted(info['models'].items()))
        sc.savejson(data, info, indent=2)
        write_csv(info)
    return


def seconds(value):
    """ A time, to two significant figures, without an exponent """
    return f'{float(f"{value:.2g}"):f}'.rstrip('0').rstrip('.') + ' s'


def set_row(text, start, cells):
    """ Replace the second and third cells of the row beginning with a label, keeping the rest """
    def fix(match):
        row = match.group(0).split('|')
        row[2:4] = [f' {cell} ' for cell in cells]
        return '|'.join(row)
    return re.sub(rf'^\| {start}.*$', fix, text, count=1, flags=re.MULTILINE)


def write_tables(names):
    """ Write the lines and the times into each vignette's table """
    info = load_data()
    missing = {}
    for name in names:
        path = root / 'vignettes' / name / 'README.md'
        text = sc.loadtext(path)
        text = set_row(text, 'Lines of model code', [re.search(r'^\| Lines of model code \|([^|]*)\|', text, flags=re.MULTILINE).group(1).strip(), count_lines(model_file(name))])
        sc.savetext(path, text)

        model = info['models'].get(name, {})
        best = model.get('kernels', {}).get(model.get('fastest'))
        if not best:
            missing[name] = 'no timing, so only the lines were written'
            continue
        original = sc.loadjson(root/'examples'/name/'reference'/'timing.json')
        text = set_row(text, r'(?:One|\d+ runs)', [
            f'first {seconds(original["first"])}, rerun {seconds(original["rerun"])}',
            f'first {seconds(best["first"])}, rerun {seconds(best["rerun"])} ({kernel_names[model["fastest"]]})',
        ])
        date = datetime.date.fromisoformat(info['date']).strftime('%-d %B %Y')
        measured = f'Measured on {date} with Starsim {info["starsim"]["version"]} (the `v4` branch, commit `{info["starsim"]["commit"]}`), on a {info["cpus"]}-core Linux machine.'
        text = re.sub(r'^Measured on .*$', measured, text, flags=re.MULTILINE)
        sc.savetext(path, text)
    return missing


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--only', help='only the models whose name contains this')
    parser.add_argument('--stages', nargs='+', choices=stages, default=stages)
    parser.add_argument('--kernels', nargs='+', choices=kernels, default=kernels)
    parser.add_argument('--starsim', help='folder of a Starsim checkout to use rather than the installed one')
    parser.add_argument('--commit', help='the commit of that checkout, if it is not a git repository')
    parser.add_argument('--worker', nargs=3, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.worker:
        name, kernel, reruns = args.worker
        return worker(name, kernel, int(reruns))

    names = list_models(args.only)
    env = dict(PYTHONPATH=args.starsim) if args.starsim else {}
    failed = {}
    if 'check' in args.stages:
        ok, text = command([sys.executable, str(root/'_envs'/'envs.py'), 'check'])
        print(text)
    if 'originals' in args.stages:
        failed.update({f'original {key}':val for key,val in run_originals(names).items()})
    if 'compare' in args.stages:
        failed.update({f'compare {key}':val for key,val in run_compares(names, env).items()})
    if 'timing' in args.stages:
        run_timing(names, args.kernels, env, args.commit)
    if 'tables' in args.stages:
        for key,val in write_tables(names).items():
            print(f'Note: {key}: {val}')

    for key,val in failed.items():
        print(f'FAILED: {key}: {val}')
    print(f'Done: {len(names)} models, {len(failed)} failures')
    return len(failed) > 0


if __name__ == '__main__':
    sys.exit(main())

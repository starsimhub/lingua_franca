"""
Regenerate everything in the benchmark table on the home page: for each model, lines of
code and run time for the original and for Starsim, and whether their results agree.

    lingua_franca benchmark                        # Everything
    lingua_franca benchmark --only odin            # Only the models whose name contains "odin"
    lingua_franca benchmark --stages timing tables # Only some stages
    lingua_franca benchmark --all-kernels          # Try every kernel set, and rewrite kernels.yaml
    lingua_franca benchmark --references           # Also remake the originals' reference results (over an hour)

The stages, in order (see docs/benchmark/README.md for what to install first):

    check       Check that each framework's environment is installed in _envs/
    compare     Check each translation against the originals' results (docs/models/*/*/compare.py)
    timing      Time each original and its translation in turn, writing timings.json and .csv in docs/benchmark
    tables      Write the lines and times into the table of each model's README, and print the scorecard

Lines are counted, and times taken, as in docs/design/18-conformance.md. The first run is a
fresh process, not counting importing Starsim and reading the model file (so not reading
data, as in the originals). A rerun is the same sim run again, already built. A rebuild
is `sim.new().run()`, timed only with --all-kernels. Each model gets `n_rounds` rounds of
its original and then Starsim, in fresh processes, under the kernels listed for it in
kernels.yaml, and each time is the best of them. The scorecard says whether each
model meets the north star: a model fails on lines if Starsim has more than the original,
and on a time if Starsim is more than 2x slower and more than 1 s slower (`--out` saves it).
A full run records how long the whole
suite and each model took, in timings.json and docs/benchmark/README.md.

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

root = sc.thispath(__file__).parent.parent # The top of this repo
models = root / 'docs' / 'models' # Each original, with its Starsim version
folder = root / 'docs' / 'benchmark' # The results, and the page that shows them
sys.path.insert(0, str(models))
import tools

stages = ['check', 'compare', 'timing', 'tables']
kernels = ['rust', 'numba', 'jax', 'jax-gpu'] # Every set is tried with --all-kernels, and JAX is left out where it does not apply
kernel_names = {'rust':'Rust', 'numba':'Numba', 'jax':'JAX', 'jax-gpu':'JAX on a GPU'}
n_rounds = 2 # Rounds of each original and its translation, in turn
slow = 30 # Seconds for a round of one model, over which it gets no more rounds
close = 1.1 # Kernel sets within this factor of the fastest rerun are all listed in kernels.yaml
limit = 120 # Seconds for one model over all the stages, over which it is reported
timeout = 900 # Seconds for any one command
ratio_limit = 2 # A time fails if Starsim is more than this many times slower...
diff_limit = 1 # ...and more than this many seconds slower
max_load = 10 # A load average over this pauses the run before the next model, which is checked again after `pause` seconds
pause = 300
data = folder / 'timings.json'
kernel_file = folder / 'kernels.yaml'
readme = folder / 'README.md'

runs = { # What one run is, where it is not the variable `sim` in the model file
    'emulsion/sir': dict(sim='compartment'), # The original timed is the compartmental one
    'flepimop/vaccine_scenarios': dict(code='ss.parallel(runs(n_runs=2, verbose=0), parallel=False)'), # The original timed is 3 scenarios of 2 runs
}


def list_models(only=None):
    """ The name of every model, e.g. "odin/seir_array" """
    names = sorted(f'{path.parent.parent.name}/{path.parent.name}' for path in models.glob('*/*/meta.yaml'))
    return [name for name in names if not only or only in name]


def model_file(name):
    """ The file holding the Starsim version of a model """
    return models / name / 'model.py'


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


def wait_for_quiet(spent):
    """ Pause while the machine is busy, so as to neither slow it down further nor time a busy machine; the seconds paused are kept in `spent` and left out of the times """
    while os.getloadavg()[0] > max_load:
        print(f'Load {os.getloadavg()[0]:.1f}: pausing for {pause} s', flush=True)
        time.sleep(pause)
        spent['paused'] = spent.get('paused', 0) + pause
    return


def last_line(text):
    """ The last line of what a command printed, for a one-line error """
    lines = text.strip().splitlines()
    return lines[-1][:200] if lines else 'no output'


def run_original(name, references=False):
    """ Run one original in its environment: only for its timing, unless the reference results are to be remade """
    env = dict(PYTHONPATH='') if references else dict(PYTHONPATH='', BENCHMARK_QUICK='1') # In their own environments
    return command([sys.executable, 'run.py'], cwd=models/name, env=env, log=models/name/'run.log')


def remake_references(names, spent, paused):
    """ Run each original in full, remaking its reference results """
    failed = {}
    for name in names:
        wait_for_quiet(paused)
        print(f'Original: {name}', flush=True)
        start = time.perf_counter()
        ok, text = run_original(name, references=True)
        spent.setdefault(name, {})['references'] = time.perf_counter() - start
        if not ok:
            failed[name] = last_line(text)
    return failed


def run_compares(names, env, spent, paused):
    """ Check each translation against its original's results """
    failed = {}
    for name in names:
        wait_for_quiet(paused)
        print(f'Compare: {name}', flush=True)
        start = time.perf_counter()
        ok, text = command([sys.executable, 'compare.py'], cwd=models/name, env=env, log=models/name/'compare.log')
        spent.setdefault(name, {})['compare'] = time.perf_counter() - start
        if not ok:
            failed[name] = last_line(text)
    return failed


def worker(name, kernel, rebuilds):
    """ In a fresh process: read the model, then time its first run and its reruns (and rebuilds, if asked), printing them; JAX stops after the first if it was not used """
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

    if kernel.startswith('jax') and 'code' not in run: # Without a slow first run if JAX does not apply
        built[0].init()
        reason = built[0].kernel_reason()
        use, why = (False, reason) if reason else forced(built[0])
        if not use:
            print('TIMING ' + json.dumps(dict(skipped=why)))
            return

    start = time.perf_counter()
    first()
    out = dict(first=time.perf_counter() - start)
    if kernel.startswith('jax') and not any(use for use,why in used):
        out = dict(skipped=used[-1][1] if used else 'no compartmental run')
    else:
        out['rerun'] = tools.repeat(again)
        if rebuilds:
            out['rebuild'] = tools.repeat(rebuild)
    print('TIMING ' + json.dumps(out))
    return


def kernel_env(kernel):
    """ The environment variables for a kernel set; JAX runs use the default kernels for anything it leaves to them """
    if kernel == 'jax':
        return dict(JAX_PLATFORMS='cpu')
    elif kernel == 'jax-gpu':
        return dict(JAX_PLATFORMS='cuda,cpu', XLA_PYTHON_CLIENT_PREALLOCATE='false')
    return dict(STARSIM_KERNELS=kernel)


def run_worker(name, kernel, env, rebuilds=False):
    """ One fresh process, returning its times, or why there are none """
    cmd = [sys.executable, __file__, '--worker', name, kernel, str(int(rebuilds))]
    ok, text = command(cmd, env=dict(env, **kernel_env(kernel)))
    found = [line for line in text.splitlines() if line.startswith('TIMING ')]
    return json.loads(found[-1][7:]) if ok and found else dict(skipped=last_line(text))


def keep_best(best, found):
    """ The better of two sets of times """
    if 'skipped' in found or not best:
        return found
    return {key:min(best[key], found[key]) for key in found}


def time_model(name, sets, env, rebuilds=False):
    """ Time an original and its translation in turn, returning the best times of Starsim by kernel set and of the original, or an error if the original failed """
    path = models/name/'reference'/'timing.json'
    times, original = {}, {}
    for i in range(n_rounds):
        start = time.perf_counter()
        ok, text = run_original(name)
        if not ok:
            return times, last_line(text)
        timing = sc.loadjson(path)
        original = keep_best(original, {key:timing[key] for key in ['first', 'rerun']})
        sc.savejson(path, dict(timing, **original), indent=2)
        for kernel in sets:
            if 'skipped' not in times.get(kernel, {}):
                times[kernel] = keep_best(times.get(kernel), run_worker(name, kernel, env, rebuilds))
        if time.perf_counter() - start > slow:
            break
    return times, None


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


def listed_kernels(name):
    """ The kernel sets to time a model with """
    return sc.loadyaml(kernel_file)[name]


def pretty_time(value):
    """ A time in the units that read best """
    return f'{float(f"{value*1000:.2g}"):g} ms' if value < 1 else f'{value:.2g} s'


def write_kernels(info):
    """ Write which kernel sets to time each model with: the fastest, and any others close to it """
    lines = [f'# The kernel sets to time each model with: the fastest rerun, and any within {close - 1:.0%} of it, so that a close call is settled each time.', '# Written by `lingua_franca benchmark --all-kernels`; each note gives the reruns measured.']
    for name,model in info['models'].items():
        done = {kernel:val['rerun'] for kernel,val in model['kernels'].items() if 'rerun' in val}
        best = min(done.values())
        use = [kernel for kernel in sorted(done, key=done.get) if done[kernel] <= close*best]
        note = ', '.join(f'{kernel_names[kernel]} {pretty_time(val)}' for kernel,val in sorted(done.items(), key=lambda item: item[1]))
        lines.append(f'{name}: [{", ".join(use)}] # {note}')
    sc.savetext(kernel_file, '\n'.join(lines) + '\n')
    return


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


def run_timing(names, env, commit, spent, paused, all_kernels=False):
    """ Time every model, saving as it goes, and returning any original that failed """
    info = load_data()
    info.update(date=str(datetime.date.today()), starsim=starsim_info(env, commit), cpus=os.cpu_count(), system=platform.platform())
    if all_kernels:
        print('Timing the compiling of the Numba kernels')
        info.update(kernels=kernels, survey=info['date'], numba_compile=compile_time(env))
    failed = {}
    for name in names:
        wait_for_quiet(paused)
        print(f'Timing: {name}', flush=True)
        start = time.perf_counter()
        loads = [os.getloadavg()[0]]
        sets = kernels if all_kernels else listed_kernels(name)
        times, error = time_model(name, sets, env, rebuilds=all_kernels)
        loads.append(os.getloadavg()[0])
        spent.setdefault(name, {})['timing'] = time.perf_counter() - start
        if error:
            failed[name] = error
            continue
        known = info['models'].get(name, {}).get('kernels', {})
        info['models'][name] = dict(kernels=dict(known, **times), fastest=fastest(times), load=max(loads))
        info['models'] = dict(sorted(info['models'].items()))
        sc.savejson(data, info, indent=2)
        write_csv(info)
    if all_kernels:
        write_kernels(info)
    return failed


def write_suite(spent, total):
    """ Record how long the whole suite and each model took, and say so at the top of the README """
    models = {name:round(sum(val.values()), 1) for name,val in spent.items()}
    stage_times = {stage:round(sum(val.get(stage, 0) for val in spent.values()), 1) for stage in stages if any(stage in val for val in spent.values())}
    worst = max(models, key=models.get)
    info = load_data()
    info['suite'] = dict(date=str(datetime.date.today()), seconds=round(total, 1), stages=stage_times, models=dict(sorted(models.items())))
    sc.savejson(data, info, indent=2)
    date = datetime.date.today().strftime('%-d %B %Y')
    each = ', '.join(f'{stage} {val/60:.1f}' for stage,val in stage_times.items())
    line = f'**Last full run:** {total/60:.0f} minutes on {date} ({each}). The slowest model, `{worst}`, took {models[worst]:.0f} s.'
    sc.savetext(readme, re.sub(r'^\*\*Last full run:\*\*.*$', line, sc.loadtext(readme), flags=re.MULTILINE))
    return line


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
    """ Write the lines and the times into each model's table """
    info = load_data()
    missing = {}
    for name in names:
        path = models / name / 'README.md'
        text = sc.loadtext(path)
        text = set_row(text, 'Lines of model code', [re.search(r'^\| Lines of model code \|([^|]*)\|', text, flags=re.MULTILINE).group(1).strip(), count_lines(model_file(name))])
        sc.savetext(path, text)

        model = info['models'].get(name, {})
        best = model.get('kernels', {}).get(model.get('fastest'))
        if not best:
            missing[name] = 'no timing, so only the lines were written'
            continue
        original = sc.loadjson(models/name/'reference'/'timing.json')
        if 'rerun' not in original:
            missing[name] = 'the timing of the original is out of date, so only the lines were written'
            continue
        text = set_row(text, r'(?:One|\d+ runs)', [
            f'first {seconds(original["first"])}, rerun {seconds(original["rerun"])}',
            f'first {seconds(best["first"])}, rerun {seconds(best["rerun"])} ({kernel_names[model["fastest"]]})',
        ])
        date = datetime.date.fromisoformat(info['date']).strftime('%-d %B %Y')
        measured = f'Measured on {date} with Starsim {info["starsim"]["version"]} (the `v4` branch, commit `{info["starsim"]["commit"]}`), on a {info["cpus"]}-core Linux machine.'
        text = re.sub(r'^Measured on .*$', measured, text, count=1, flags=re.MULTILINE)
        sc.savetext(path, text)
    return missing


def original_lines(name):
    """ The original's lines: from its meta.yaml, or else the first number in its table """
    lines = sc.loadyaml(models/name/'meta.yaml').get('lines')
    if isinstance(lines, int):
        return lines
    row = re.search(r'^\| Lines of model code \|([^|]*)\|', sc.loadtext(models/name/'README.md'), flags=re.MULTILINE).group(1)
    return int(re.search(r'\d[\d,]*', row).group().replace(',', ''))


def scorecard(names):
    """ Markdown for each model against the north star: its lines and times against the original's, with a summary of what fails """
    info = load_data()
    rows = ['| Model | Lines: original | Lines: Starsim | First run (s): original | First run (s): Starsim | Rerun (s): original | Rerun (s): Starsim | Fails on |', '|---|---|---|---|---|---|---|---|']
    failures = dict(lines=[], first=[], rerun=[])
    measured = 0
    for name in names:
        ours, theirs = count_lines(model_file(name)), original_lines(name)
        fails = ['lines']*(ours > theirs)
        model = info['models'].get(name, {})
        best = model.get('kernels', {}).get(model.get('fastest'), {})
        path = models/name/'reference'/'timing.json'
        original = sc.loadjson(path) if path.exists() else {}
        cells = []
        for key in ['first', 'rerun']:
            cells += [seconds(original[key]) if key in original else '–', seconds(best[key]) if key in best else '–']
            if key in original and key in best and best[key] > ratio_limit*original[key] and best[key] - original[key] > diff_limit:
                fails.append(key)
        measured += bool(best)
        for key in fails:
            failures[key].append(name)
        rows.append(f"| {name} | {theirs} | {ours} | {' | '.join(cells)} | {', '.join(fails) or '–'} |")
    n = dict(lines=len(names), first=measured, rerun=measured)
    summary = [f"- {key.capitalize()}: {n[key] - len(val)} of {n[key]} pass" + (f": failing {', '.join(val)}" if val else '') for key,val in failures.items()]
    return '\n'.join(rows + [''] + summary) + '\n'


def main(args=None):
    parser = argparse.ArgumentParser(prog='lingua_franca benchmark', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--only', help='only the models whose name contains this')
    parser.add_argument('--stages', nargs='+', choices=stages, default=stages)
    parser.add_argument('--all-kernels', action='store_true', help='try every kernel set on every model, and rewrite kernels.yaml')
    parser.add_argument('--starsim', help='folder of a Starsim checkout to use rather than the installed one')
    parser.add_argument('--commit', help='the commit of that checkout, if it is not a git repository')
    parser.add_argument('--references', action='store_true', help="also remake the originals' reference results, which takes over an hour")
    parser.add_argument('--out', help='also save the scorecard to this file')
    parser.add_argument('--worker', nargs=3, help=argparse.SUPPRESS)
    args = parser.parse_args(args)

    if args.worker:
        name, kernel, rebuilds = args.worker
        return worker(name, kernel, int(rebuilds))

    start = time.perf_counter()
    names = list_models(args.only)
    env = dict(PYTHONPATH=args.starsim) if args.starsim else {}
    failed = {}
    spent = {} # Seconds by model and stage
    paused = {} # Seconds paused for a busy machine
    if 'check' in args.stages:
        ok, text = command([sys.executable, '-m', 'lingua_franca.envs', 'check'])
        print(text)
    if args.references:
        failed.update({f'original {key}':val for key,val in remake_references(names, spent, paused).items()})
    if 'compare' in args.stages:
        failed.update({f'compare {key}':val for key,val in run_compares(names, env, spent, paused).items()})
    if 'timing' in args.stages:
        failed.update({f'original {key}':val for key,val in run_timing(names, env, args.commit, spent, paused, args.all_kernels).items()})
    if 'tables' in args.stages:
        for key,val in write_tables(names).items():
            print(f'Note: {key}: {val}')
        card = scorecard(names)
        print(card)
        if args.out:
            sc.savetext(args.out, card)

    for key,val in failed.items():
        print(f'FAILED: {key}: {val}')
    total = time.perf_counter() - start - paused.get('paused', 0)
    for name,val in spent.items():
        if sum(val.values()) > limit:
            print(f'Over {limit} s: {name}: {val}')
    if not args.only and args.stages == stages and not args.references and not args.all_kernels: # Only a whole run, of the usual size
        print(write_suite(spent, total))
    print(f'Done: {len(names)} models, {len(failed)} failures, in {total/60:.1f} minutes')
    return len(failed) > 0


if __name__ == '__main__':
    sys.exit(main())

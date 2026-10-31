"""
Write the Markdown that compares each example with its vignette, from the files in
`examples/<framework>/<model>` and `vignettes/<framework>/<model>`. The pages that
show it call these functions as they are rendered, so nothing here is saved to a file:

    comparison()    Every model: the original and the Starsim version side by side (webapp/index.qmd)
    benchmark()     One row per model: lines of code, run time, and agreement (index.qmd, examples/index.qmd)
    kernel_table()  One row per model: its times under each kernel set, once `benchmark/benchmark.py` has measured them

To see what either one writes:

    python webapp/build.py
"""
import os
import re
import csv
import html
import sciris as sc

root = sc.thispath(__file__).parent
skip = ['.xlsx', '.pyc', '.ipynb', '.gz', '.html'] # Not shown: binary files, notebooks that are also there as a script, and pages Quarto is part way through writing
languages = {'.py':'python', '.R':'r', '.yaml':'yaml', '.yml':'yaml'} # Anything else is shown as plain text


def read(path):
    """ Read a text file, without the newline at the end """
    return sc.loadtext(path).rstrip('\n')


def code_files(folder, suffix=None, exclude=()):
    """ The source files in a folder and its subfolders (optionally of one kind), as paths relative to it, with those at the top first """
    paths = []
    for path in sc.getfilelist(folder, recursive=True, nopath=False):
        path = sc.path(path)
        if path.is_file() and path.suffix not in skip and path.name not in exclude and '__pycache__' not in path.parts and suffix in [None, path.suffix]:
            paths.append(path.relative_to(folder))
    return sorted(paths, key=lambda path: (len(path.parts), str(path)))


def sheet(path):
    """ A CSV file as a table, laid out as it is in the file: no row is taken to be the header, since a sheet may hold several tables """
    with open(path, newline='') as f:
        rows = list(csv.reader(f))
    width = max(len(row) for row in rows)
    out = ['```{=html}', '<div class="sheet"><table>']
    for row in rows:
        cells = [html.escape(cell.strip()) for cell in row] + ['']*(width - len(row))
        out += ['<tr>' + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>']
    out += ['</table></div>', '```']
    return '\n'.join(out)


def code_block(path):
    """ A file as a fenced code block (with tildes, since the file may contain backticks), or as a table if it is a CSV file """
    if path.suffix == '.csv':
        return sheet(path)
    lang = languages.get(path.suffix, 'default')
    return f'~~~~~{{.{lang}}}\n{read(path)}\n~~~~~'


def code_pane(title, folder, files):
    """ One side of the comparison: a single file, or a tab for each of several """
    out = [f'::::: {{.pane}}\n\n**{title}**\n']
    if len(files) == 1:
        out += [f'`{files[0]}`\n', code_block(folder / files[0])]
    elif len(files) > 1:
        out += [':::::: {.panel-tabset}\n']
        for file in files:
            out += [f'#### {file.name}\n', code_block(folder / file), '']
        out += ['::::::']
    else:
        out += ['*Not written yet.*']
    out += ['\n:::::']
    return '\n'.join(out)


def fix_links(text, folder):
    """ Make the relative links in a file from another folder work from anywhere in the site """
    def fix(match):
        target, hash, anchor = match.group(1).partition('#')
        if not target or target.startswith(('http', 'mailto:', '/')):
            return match.group(0)
        path = os.path.normpath(folder / target)
        if os.path.isdir(path):
            path = os.path.join(path, 'README.md')
        return f'](/{os.path.relpath(path, root)}{hash}{anchor})'
    return re.sub(r'\]\(([^)\s]+)\)', fix, text)


def sections(text):
    """ Split a Markdown file into its title, its opening text, and `{heading: text}` for each second-level section """
    parts = re.split(r'^## +(.*)$', text, flags=re.MULTILINE)
    title, hash, intro = parts[0].partition('# ')[2].partition('\n')
    body = {heading.strip(): content.strip() for heading, content in zip(parts[1::2], parts[2::2])}
    return title.strip(), intro.strip(), body


def table_rows(text):
    """ The rows of the first Markdown table in a text, as lists of cells, without the header """
    rows = []
    for line in text.splitlines():
        if line.startswith('|'):
            rows.append(line.strip().strip('|').split('|'))
        elif rows: # The end of the first table
            break
    return [[cell.strip() for cell in row] for row in rows[2:]]


def friendly_times(text):
    """ Write the times under a second in milliseconds: "0.0024 s" becomes "2.4 ms" """
    def convert(match):
        seconds = float(match.group(1))
        return f'{seconds*1000:g} ms' if seconds < 1 else match.group(0)
    return re.sub(r'(\d+(?:\.\d+)?) s\b', convert, text)


def load_model(folder):
    """ Everything known about one example and its vignette """
    meta = sc.objdict(sc.loadyaml(folder / 'meta.yaml'))
    key = f"{folder.parent.name}/{folder.name}"
    vfolder = root / 'vignettes' / key
    title, intro, body = sections(read(folder / 'README.md'))
    vtitle, vintro, vbody = sections(fix_links(read(vfolder / 'README.md'), vfolder))
    model = sc.objdict(
        key      = key,
        id       = 'm-' + key.replace('/', '-'),
        meta     = meta,
        title    = title,
        intro    = intro.split('\n\n')[0],
        vintro   = vintro,
        table    = friendly_times(vbody.pop('Comparison', '')),
        notes    = vbody,
        folder   = folder / 'original',
        vfolder  = vfolder,
        original = code_files(folder / 'original'),
        starsim  = code_files(vfolder, suffix='.py', exclude=['compare.py']),
    )
    return model


def model_page(model):
    """ The section of the page for one model """
    meta = model.meta
    source = re.sub(r'(https?://[^\s,)]+)', r'<\1>', str(meta.source))
    out = [
        f'::: {{#{model.id} .model}}\n',
        f'## {model.title}\n',
        f'{model.intro}\n',
        f'- **Framework:** {meta.framework} {meta.version} ({meta.license})',
        f'- **Language:** {meta.language}',
        f'- **Source:** {source}',
        f'- **Full detail:** [the example](/examples/{model.key}/README.md) and [the vignette](/vignettes/{model.key}/README.md)\n',
    ]
    if model.table:
        out += [model.table, '']
    else: # There is no comparison yet, so say why
        out += [model.vintro.split('\n\n')[0].partition('. ')[2], '']
    out += [
        ':::: {.compare}\n',
        code_pane(f'Original ({meta.framework})', model.folder, model.original), '',
        code_pane('Starsim', model.vfolder, model.starsim), '',
        '::::\n',
    ]
    for heading, text in model.notes.items():
        out += [f'### {heading}\n', text, '']
    out += [':::\n']
    return '\n'.join(out)


def numbers(text):
    """ The numbers in a cell, in seconds if they are times: "33 ms, or 0.5 ms for a repeated run" gives [0.033, 0.0005] """
    matches = re.findall(r'(\d[\d,]*(?:\.\d+)?)(?: *(ms|s)\b)?', text)
    return [float(value.replace(',', ''))/(1000 if unit == 'ms' else 1) for value, unit in matches]


def mark(original, starsim, index=0):
    """ A cell with the original's number above Starsim's, marked for the stylesheet as meeting its target (no more than the original) or not; it uses Starsim's last number, which is the rerun, against the original's at `index` """
    target = 'pass' if numbers(starsim)[-1] <= numbers(original)[index] else 'fail'
    return f'Original: {original}<br>[Starsim: {starsim}]{{.{target}}}'


def benchmark_row(model):
    """ The row of the benchmark table for one model: lines, time, and whether the results agree """
    link = f'[**{model.meta.framework}**<br>{model.folder.parent.name}](/webapp/index.qmd#{model.id})'
    rows = table_rows(model.table)
    if not rows:
        return f'| {link} | {model.meta.language} | *Not written yet* | | |'
    lines, time = rows[0], rows[1]
    results = '; '.join(row[3] for row in rows[2:])
    return f'| {link} | {model.meta.language} | {mark(lines[1], lines[2])} | {mark(time[1], time[2], index=-1)} | {results} |'


def load_models():
    """ Every example that has a `meta.yaml`, in order of framework """
    folders = sorted(path.parent for path in (root / 'examples').glob('*/*/meta.yaml'))
    return [load_model(folder) for folder in folders]


def comparison():
    """ The comparison page: a link to pick each model, then a section for each """
    models = load_models()
    picker = ' '.join(f'[{model.meta.framework}](#{model.id}){{.model-link}}' for model in models)
    return '\n'.join([f'::: {{.model-picker}}\n{picker}\n:::\n'] + [model_page(model) for model in models])


def benchmark():
    """ The benchmark table: a table with a row for each model """
    out = [
        '| Model | Language | Lines | Time | Results |',
        '|---|---|---|---|---|',
    ] + [benchmark_row(model) for model in load_models()]
    return '\n'.join(out)


def kernel_table():
    """ The times of each model under each kernel set, from `benchmark/timings.json`, written by `benchmark/benchmark.py` """
    info = sc.loadjson(root / 'benchmark' / 'timings.json')
    sets = info['kernels']
    names = dict(rust='Rust', numba='Numba', jax='JAX', **{'jax-gpu':'JAX on a GPU'})
    out = ['| Model | ' + ' | '.join(f'{names[key]}: first | {names[key]}: rerun' for key in sets) + ' |', '|---|' + '---|---|'*len(sets)]
    for name, model in info['models'].items():
        cells = []
        for key in sets:
            time = model['kernels'].get(key, {})
            bold = '**' if key == model['fastest'] else ''
            cells += [f'{time["first"]:.2g}', f'{bold}{time["rerun"]:.2g}{bold}'] if 'rerun' in time else ['', '']
        out += [f'| {name} | ' + ' | '.join(cells) + ' |']
    out += ['', f'Measured on {info["date"]} with Starsim {info["starsim"]["version"]} (commit `{info["starsim"]["commit"]}`) on a {info["cpus"]}-core Linux machine, using each set of kernels\' default threads. Those not in `benchmark/kernels.yaml` were last timed on {info["survey"]}. Compiling the Numba kernels, needed once per install, took {info["numba_compile"]:.0f} s; the Rust kernels are built when Starsim is installed.']
    return '\n'.join(out)


if __name__ == '__main__':
    print(benchmark())
    print(comparison())

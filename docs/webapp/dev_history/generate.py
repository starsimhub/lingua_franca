"""
Generate the data for the git history visualizations in this folder.

Reads the git history of two things and writes one JavaScript data file for each:

- `starsim_data.js`: every Python file in the `starsim` package (`import starsim as ss`), from the `v4` branch of the Starsim repo, one column per file
- `design_data.js`: the design docs (`docs/design` in lingua_franca), one column per `##` section

Each column follows its file through renames. Each edit is recorded as the fraction of the file (or section) it changed: (lines added + lines deleted) / the larger of its lengths before and after, capped at 1. `index.html` turns these into the picture.

Usage:

    python generate.py                                  # both, with the default repo locations
    python generate.py --starsim ~/idm/ssv4 --ref v4    # choose the Starsim checkout and branch
"""

import re
import json
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict

here = Path(__file__).resolve().parent
lf_root = here.parents[2]

starsim_prefixes = ('starsim/', 'stisim/') # stisim was the package's name until January 2024
design_prefixes = ('design/', 'docs/design/') # the design docs moved under docs/ on 2026-10-31


def git(repo, *args, data=None):
    """ Run git in a repo and return its output as bytes """
    return subprocess.run(['git', '-C', str(repo), *args], input=data, capture_output=True, check=True).stdout


def read_log(repo, ref):
    """ Read every non-merge commit (parents first) with each file's status, paths, and lines added and deleted """
    out = git(repo, 'log', ref, '--no-merges', '--topo-order', '--reverse', '-M', '--raw', '--numstat', '-z',
              '--format=%x01%H%x1f%at%x1f%an%x1f%s')
    commits = []
    tokens = out.decode('utf-8', errors='replace').split('\0')
    i = 0
    numstat = re.compile(r'^(\d+|-)\t(\d+|-)\t(.*)$', re.S)
    while i < len(tokens):
        tok = tokens[i].lstrip('\n')
        i += 1
        if tok.startswith('\x01'):
            sha, t, author, subject = tok[1:].split('\x1f', 3)
            commit = dict(sha=sha, t=int(t), author=author, subject=subject.strip(), files={})
            commits.append(commit)
        elif tok.startswith(':'):
            status = tok.split()[-1]
            if status[0] in 'RC':
                old, new = tokens[i], tokens[i+1]
                i += 2
            else:
                old = new = tokens[i]
                i += 1
            commit['files'][new] = dict(status=status[0], old=old, new=new, add=0, dele=0)
        elif (m := numstat.match(tok)):
            a, d, path = m.groups()
            if path == '':
                path = tokens[i+1] # renames list old then new
                i += 2
            if a != '-' and path in commit['files']:
                commit['files'][path].update(add=int(a), dele=int(d))
    return commits


def count_lines(repo, specs):
    """ Count the lines of many blobs (given as 'sha:path') with a single git cat-file call """
    if not specs:
        return {}
    out = git(repo, 'cat-file', '--batch', data=('\n'.join(specs) + '\n').encode())
    counts = {}
    pos = 0
    for spec in specs:
        end = out.index(b'\n', pos)
        header = out[pos:end].split()
        pos = end + 1
        if header[-1] == b'missing':
            counts[spec] = None
            continue
        size = int(header[2])
        blob = out[pos:pos+size]
        pos += size + 1
        counts[spec] = blob.decode('utf-8', errors='replace')
    return counts


class Lineages:
    """ Follow files through renames, giving each a stable integer id """

    def __init__(self):
        self.path2lin = {}
        self.current = [] # the latest path of each lineage

    def update(self, f):
        """ Return the lineage of a changed file, updating it for renames, adds and deletes """
        status, old, new = f['status'], f['old'], f['new']
        if status == 'A':
            lin = self.path2lin.get(new)
            if lin is None or self.current[lin] not in (None, new): # the path now belongs to another file
                lin = self._new()
        else:
            lin = self.path2lin.get(old)
            if lin is None:
                lin = self._new()
        if status == 'D':
            self.current[lin] = None
        else:
            self.current[lin] = new
        self.path2lin[new] = lin # old paths keep pointing here too, for edits on parallel branches
        return lin

    def _new(self):
        self.current.append(None)
        return len(self.current) - 1


def in_scope(path, prefixes, suffix):
    """ Whether a path is part of what's tracked; skips hidden folders such as starsim/.agents """
    return path.startswith(prefixes) and path.endswith(suffix) and '/.' not in path


def file_events(repo, ref, prefixes, suffix):
    """ Shared first pass: the commits, and each in-scope file change with its lineage """
    commits = read_log(repo, ref)
    lineages = Lineages()
    changes = [] # (commit index, lineage, file dict)
    for ci, c in enumerate(commits):
        for f in c['files'].values():
            if f['status'] not in 'AMRCD':
                continue
            lin = lineages.update(f)
            if in_scope(f['old'], prefixes, suffix) or in_scope(f['new'], prefixes, suffix):
                changes.append((ci, lin, f))
    return commits, lineages, changes


def strip_prefix(path, prefixes):
    for p in prefixes:
        if path.startswith(p):
            return path[len(p):]
    return path


def build_starsim(repo, ref):
    """ One column per file in the package """
    commits, lineages, changes = file_events(repo, ref, starsim_prefixes, '.py')
    tip = set(git(repo, 'ls-tree', '-r', '--name-only', ref).decode().splitlines())

    # Lines in each file after each change
    specs = sorted({f"{commits[ci]['sha']}:{f['new']}" for ci, lin, f in changes if f['status'] != 'D'})
    blobs = count_lines(repo, specs)

    cols = {}
    used = set()
    for ci, lin, f in changes:
        c = commits[ci]
        after = 0
        if f['status'] != 'D':
            text = blobs.get(f"{c['sha']}:{f['new']}")
            after = text.count('\n') if text else 0
        before = max(0, after - f['add'] + f['dele'])
        changed = f['add'] + f['dele']
        frac = min(1.0, changed / max(before, after, 1))
        moved_out = not in_scope(f['new'], starsim_prefixes, '.py') or f['status'] == 'D'
        col = cols.setdefault(lin, dict(paths=[], events=[]))
        path = strip_prefix(f['new'] if not moved_out else f['old'], starsim_prefixes)
        if path not in col['paths']:
            col['paths'].append(path)
        col['events'].append([c['t'], round(frac, 4), ci, after if not moved_out else 0, col['paths'].index(path)])
        used.add(ci)

    out = []
    for lin, col in cols.items():
        col['events'].sort(key=lambda e: e[0])
        cur = lineages.current[lin]
        alive = cur is not None and cur in tip and in_scope(cur, starsim_prefixes, '.py')
        out.append(dict(name=col['paths'][-1], group=folder_of(col['paths'][-1]), paths=col['paths'], alive=alive,
                        start=col['events'][0][0], end=None if alive else col['events'][-1][0], events=col['events']))
    out.sort(key=lambda col: (col['start'], col['name']))

    tags = []
    for line in git(repo, 'for-each-ref', 'refs/tags', '--merged', ref, '--format=%(refname:short) %(creatordate:unix)').decode().splitlines():
        name, t = line.split()
        if re.fullmatch(r'v\d+\.\d+\.0', name) or re.fullmatch(r'v4\.0\.0rc1', name):
            tags.append([int(t), name])
    v4_start = git(repo, 'log', ref, '--not', 'main', '--reverse', '--format=%at').decode().split()
    marks = sorted(tags)
    if v4_start:
        marks.append([int(v4_start[0]), 'v4 branch starts'])
        marks.sort()
    return pack(commits, used, out, marks, title='Starsim', unit='file',
                note=f'Every Python file in the starsim package, from the {ref} branch of the Starsim repo')


def folder_of(path):
    return path.split('/')[0] if '/' in path else ''


def sections(text):
    """ Split Markdown into sections at '##' headings (outside code fences); return [(heading, first line, last line)], 1-indexed """
    if text is None:
        return []
    lines = text.splitlines()
    heads = [(0, '(top)')]
    fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith(('```', '~~~')):
            fence = not fence
        elif not fence and line.startswith('## '):
            heads.append((i, line[3:].strip()))
    out = []
    for k, (start, name) in enumerate(heads):
        end = heads[k+1][0] if k + 1 < len(heads) else len(lines)
        if k == 0 and end == 0:
            continue
        out.append((name, start + 1, end))
    return out


def section_at(secs, line):
    for name, first, last in secs:
        if first <= line <= max(last, first):
            return name
    return secs[-1][0] if secs else '(top)'


def build_design(repo, ref):
    """ One column per '##' section of each design doc """
    commits, lineages, changes = file_events(repo, ref, design_prefixes, '.md')
    tip = set(git(repo, 'ls-tree', '-r', '--name-only', ref).decode().splitlines())

    specs = set()
    for ci, lin, f in changes:
        sha = commits[ci]['sha']
        if f['status'] != 'D':
            specs.add(f'{sha}:{f["new"]}')
        if f['status'] != 'A':
            specs.add(f'{sha}^:{f["old"]}')
    texts = count_lines(repo, sorted(specs))

    hunk = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
    cols = {} # (lineage, heading) -> column
    used = set()
    for ci, lin, f in changes:
        c = commits[ci]
        sha = c['sha']
        new_text = texts.get(f'{sha}:{f["new"]}') if f['status'] != 'D' else None
        old_text = texts.get(f'{sha}^:{f["old"]}') if f['status'] != 'A' else None
        new_secs, old_secs = sections(new_text), sections(old_text)
        adds, dels = defaultdict(int), defaultdict(int)
        if f['status'] == 'A':
            for name, first, last in new_secs:
                adds[name] += last - first + 1
        elif f['status'] == 'D':
            for name, first, last in old_secs:
                dels[name] += last - first + 1
        else:
            paths = [f['old'], f['new']] if f['old'] != f['new'] else [f['new']]
            diff = git(repo, 'show', '-M', '-U0', '--format=', sha, '--', *paths).decode('utf-8', errors='replace')
            for line in diff.splitlines():
                if (m := hunk.match(line)):
                    a0, an, b0, bn = m.groups()
                    an = 1 if an is None else int(an)
                    bn = 1 if bn is None else int(bn)
                    for k in range(an):
                        dels[section_at(old_secs, int(a0) + k)] += 1
                    for k in range(bn):
                        adds[section_at(new_secs, int(b0) + k)] += 1
        lens_new = {name: last - first + 1 for name, first, last in new_secs}
        lens_old = {name: last - first + 1 for name, first, last in old_secs}
        order = {name: k for k, (name, _, _) in enumerate(new_secs or old_secs)}
        doc = Path(f['new'] if f['status'] != 'D' else f['old']).stem
        for name in set(adds) | set(dels):
            changed = adds[name] + dels[name]
            frac = min(1.0, changed / max(lens_new.get(name, 0), lens_old.get(name, 0), 1))
            col = cols.setdefault((lin, name), dict(doc=doc, heading=name, events=[], pos=0))
            col['doc'] = doc
            col['pos'] = order.get(name, col['pos'])
            gone = name not in lens_new
            col['events'].append([c['t'], round(frac, 4), ci, lens_new.get(name, 0), 0])
            col['gone'] = gone
            used.add(ci)

    out = []
    for (lin, name), col in cols.items():
        col['events'].sort(key=lambda e: e[0])
        cur = lineages.current[lin]
        alive = cur is not None and cur in tip and not col.get('gone')
        out.append(dict(name=f"{col['doc']} › {name}", group=col['doc'], paths=[f"{col['doc']} › {name}"], alive=alive,
                        start=col['events'][0][0], end=None if alive else col['events'][-1][0], events=col['events'], pos=col['pos']))
    out.sort(key=lambda col: (col['group'], col['pos'], col['start']))
    for col in out:
        del col['pos']
    return pack(commits, used, out, [], title='Design docs', unit='section',
                note=f'Each ## section of the design docs (docs/design) in lingua_franca, from its {ref} branch')


def pack(commits, used, cols, marks, **kwargs):
    """ Keep only the commits that touched a column, and renumber the events to match """
    keep = sorted(used)
    remap = {ci: k for k, ci in enumerate(keep)}
    for col in cols:
        for e in col['events']:
            e[2] = remap[e[2]]
    commit_list = [[commits[ci]['sha'][:9], commits[ci]['t'], commits[ci]['author'], commits[ci]['subject']] for ci in keep]
    return dict(**kwargs, commits=commit_list, columns=cols, marks=marks)


def write(name, data):
    path = here / f'{name}_data.js'
    path.write_text(f'window.GITVIZ = window.GITVIZ || {{}};\nwindow.GITVIZ.{name} = {json.dumps(data, separators=(",", ":"))};\n')
    n_events = sum(len(col['events']) for col in data['columns'])
    print(f'Wrote {path.name}: {len(data["columns"])} columns, {len(data["commits"])} commits, {n_events} edits')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--starsim', default=lf_root.parent / 'ssv4', help='Starsim checkout (default: ../ssv4)')
    parser.add_argument('--ref', default='v4', help='Starsim branch (default: v4)')
    parser.add_argument('--lf', default=lf_root, help='lingua_franca checkout (default: this one)')
    parser.add_argument('--lf-ref', default='HEAD', help='lingua_franca branch (default: HEAD)')
    args = parser.parse_args()
    write('starsim', build_starsim(args.starsim, args.ref))
    write('design', build_design(args.lf, args.lf_ref))

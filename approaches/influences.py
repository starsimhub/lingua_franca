"""
Draw what the lingua franca owes to each framework, from `influences.yaml`. The page
that shows it (approaches/influences.qmd) calls these functions as it is rendered:

    overall()    One bar per framework: its share of the whole design, averaged over the areas
    heatmap()    One row per area and one column per framework, shaded by share

To see what either one writes:

    python approaches/influences.py
"""
import html
import sciris as sc

root = sc.thispath(__file__)
names = dict( # How each framework's name is written, and its review in this folder
    atomica='Atomica', camdl='camdl', emod='EMOD', emulsion='EMULSION', eon='EoN', epidemics='epidemics',
    epihiper='EpiHiper', epimodel='EpiModel', epipack='epipack', epiworld='epiworld', epydemix='Epydemix',
    epymorph='epymorph', flepimop='flepiMoP', individual='individual', laser='LASER', memilio='MEmilio',
    metacast='MetaCast', odin='odin', siminf='SimInf', starsim='Starsim', summer2='summer2', tlo='Thanzi la Onse', vivarium='Vivarium',
)
extras = dict(other='Other', new='New') # Not frameworks with a review: shown last, in gray


def load():
    """ The areas, with each one's shares scaled to add to 100 """
    areas = sc.loadyaml(root / 'influences.yaml')
    for area in areas.values():
        total = sum(area['shares'].values())
        area['shares'] = {key: 100*val/total for key, val in area['shares'].items()}
    return areas


def totals(areas):
    """ Each framework's share of the whole design, with every area weighted equally, largest first and the extras last """
    keys = {key for area in areas.values() for key in area['shares']}
    share = {key: sum(area['shares'].get(key, 0) for area in areas.values())/len(areas) for key in keys}
    order = sorted([key for key in keys if key not in extras], key=lambda key: -share[key]) + [key for key in extras if key in keys]
    return {key: share[key] for key in order}


def label(key, link=True, folder=''):
    """ A framework's name, linked to its review (in `folder`, relative to the page) """
    if key in extras:
        return extras[key]
    return f'<a href="{folder}{key}.md">{names[key]}</a>' if link else names[key]


def overall():
    """ A bar chart of each framework's share of the whole design """
    areas = load()
    share = totals(areas)
    top = max(share.values())
    out = ['```{=html}', '<div class="influence-bars">']
    for key, val in share.items():
        best = sorted(areas, key=lambda name: -areas[name]['shares'].get(key, 0))[:3]
        tip = f'{label(key, link=False)}: {val:.1f}% overall. Most in: ' + ', '.join(f'{name} ({areas[name]["shares"][key]:.0f}%)' for name in best if key in areas[name]['shares'])
        kind = ' extra' if key in extras else ''
        out += [f'<div class="name">{label(key)}</div>',
                f'<div class="track" title="{html.escape(tip)}"><div class="bar{kind}" style="width:{100*val/top:.1f}%"></div><span>{f"{val:.0f}%" if val >= 0.5 else "<1%"}</span></div>']
    out += ['</div>', '```']
    return '\n'.join(out)


def cell(key, val, top, tip):
    """ One cell of the heatmap: shaded by the share, with what was taken on hover """
    if not val:
        return '<td></td>'
    kind = 'extra' if key in extras else 'source'
    dark = ' dark' if kind == 'source' and val/top > 0.45 else '' # White text on the darker blue cells only
    text = f'{val:.0f}' if val >= 0.5 else '<1'
    return f'<td class="{kind}{dark}" style="--share:{val/top:.2f}" title="{html.escape(tip)}">{html.escape(text)}</td>'


def heatmap(folder=''):
    """ A table of areas by frameworks, each cell shaded by the share and explained on hover, with the overall share at the bottom; `folder` is where the reviews are, relative to the page """
    areas = load()
    share = totals(areas)
    keys = list(share)
    top = max(val for area in areas.values() for val in area['shares'].values())
    out = ['```{=html}', '<div class="influence-map"><table>', '<thead><tr><th></th>']
    out += [f'<th><div>{label(key, folder=folder)}</div></th>' for key in keys]
    out += ['</tr></thead><tbody>']
    for name, area in areas.items():
        out += [f'<tr><th>{html.escape(name)}</th>']
        for key in keys:
            val = area['shares'].get(key, 0)
            out += [cell(key, val, top, f'{label(key, link=False)}, {name}: {val:.0f}%. ' + area['notes'].get(key, ''))]
        out += ['</tr>']
    out += ['<tr class="overall"><th>Overall</th>'] # Shaded on the same scale as the areas, so it is paler
    out += [cell(key, share[key], top, f'{label(key, link=False)}: {share[key]:.1f}% of the whole design, with each area counted equally') for key in keys]
    out += ['</tr></tbody></table></div>', '```']
    return '\n'.join(out)

if __name__ == '__main__':
    print(overall())
    print(heatmap())

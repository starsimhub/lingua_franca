---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Dev history

Pictures of how the Starsim codebase and the design docs have changed over time. Time runs down the page. Each column is one file (Starsim) or one `##` section (design docs). A column is gray while the file or section exists. It turns green when edited, with the width of the green showing the share of it that changed. The green then decays exponentially back to gray. Each edit shows as at least one pixel.

Open `index.html` in a browser. Hover over a column to see the file, date, and commits. The controls set the half-life, row and column size, column order, and whether to hide removed files. "Width ∝ length" makes each column as wide as its file at its longest (keeping the mean column width), and the gray band inside it as wide as the file is long at each time.

## Regenerating the data

```sh
python generate.py
```

This reads the `v4` branch of the Starsim checkout at `../ssv4` and this repo's own history, and writes `starsim_data.js` and `design_data.js`. Use `--starsim`, `--ref`, `--lf` and `--lf-ref` to change the source. It takes about 10 seconds.

## How edits are measured

- **Share changed**: (lines added + lines deleted) / the larger of the lengths before and after, capped at 1.
- **Scope**: every `.py` file in the `starsim` package (called `stisim` until January 2024), skipping hidden folders such as `starsim/.agents`. For the design docs, every `.md` file in `docs/design` (called `design` until October 31, 2026).
- **Renames**: a column follows its file through renames. A renamed heading starts a new column, because sections are matched by heading text.
- **Commits**: merge commits are skipped, so each change counts once, at its author date.
- **Markers**: the red lines are Starsim's `vX.Y.0` releases and the start of the `v4` branch.

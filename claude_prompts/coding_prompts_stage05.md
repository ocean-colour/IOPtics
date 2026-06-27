# Code IOPtics — Stage 5: Reporting

## Goal

Turn a scored sweep into shareable, reproducible output. **Exit criterion:**
`standard.build(sweep_id, kind='cross_algorithm')` + `leaderboard.update()` (build
script stage flag 3) produce a provenance-stamped `.rst` page, the standard
figures/tables, a standalone Bokeh figure, and a leaderboard entry ranking the two
algorithms; the page renders in the Sphinx build.

Implements **Reporting** and the **Staged plan / Stage 5** of
`docs/design/IOPtics_implementation.md`. One prompt per module.

## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- `report` consumes only persisted artifacts (results + metrics + chains +
  provenance) — fully regenerable, no re-fitting. Reuse `bing.plotting` where it fits.

## Context

- `docs/design/IOPtics_implementation.md` — §Reporting (`plotting` primitives;
  `report.figures`/`tables` standard set; cross-sweep `leaderboard`; standalone
  BokehJS; `rst`/`standard.build` three report types; single accumulating Sphinx
  site, leaderboard landing page; artifact split [Q22]; default ranking [Q23];
  curated per-obs figures [Q24]; provenance stamping).
- bing: `plotting.{show_anw_fits,corner_plot,hist2d}`.

## Prompts

### Coding

1. `plotting.py` static primitives.
2. `report/figures.py` + `report/tables.py`.
3. `report/leaderboard.py`.
4. `report/bokeh.py`.
5. `report/rst.py` + `report/standard.py`.
6. Tests + wire build-script stage 3.

## Modules

### Tasks

1. **`plotting.py`.** `scatter_log` (1:1/3:1/0.3:1 guides), `ratio_hist`,
   `spectra_band`, `residual_rrs`, `taylor`, `target`, `corner`
   (→`bing.plotting.corner_plot`), `dbic_cdf`; each takes diagnostic/metric arrays,
   returns a `Figure`, no I/O. Tier-1 smoke (figure builds). Q&A. Log.

2. **`report/figures.py` + `tables.py`.** The standard per-(algorithm,dataset)
   set (`scatter_set`, `spectra_set`, `closure_set`, `taylor_target`, `corner_set`,
   `dbic_cdf`) and `tables.accuracy`/`qc`; per-obs figures only for the **curated
   handful** (MCMC subset + a few per trophic bin). Write PNG+PDF/CSV to
   `runs/<sweep_id>/figures/`. Tier-2 on the Stage-4 sweep. Q&A. Log.

3. **`report/leaderboard.py`.** `update(runs_root)` folds every sweep's
   `metrics_scalar` into `$OS_COLOR/IOPtics/leaderboard.parquet` (idempotent;
   re-fold replaces a sweep's rows); default ranking wins → `|bias|`/MAE at ref-λ;
   `render(fmt='rst')`. Tier-1 idempotency + ordering. Q&A. Log.

4. **`report/bokeh.py`.** Standalone BokehJS (`file_html` + `CustomJS`) —
   `interactive_scatter`, `interactive_leaderboard` (select algorithm/dataset/
   stratum; hover/pan/zoom) returning self-contained HTML. Tier-1 (HTML produced,
   contains expected selectors). Q&A. Log.

5. **`report/rst.py` + `standard.py`.** `standard.build(sweep_id, kind ∈
   {per_algorithm, cross_algorithm, per_dataset})` → assemble figures/tables/bokeh
   into `docs/source/reports/<sweep_id>/<kind>.rst`, **copy** lightweight assets
   from `runs/<sweep_id>/figures/`, header-stamp provenance versions; link into the
   toctree; leaderboard as landing page. Tier-2. Q&A. Log.

6. **Tests + build-script stage 3.** Wire `build_v1.py` flag 3 to
   `standard.build` + `leaderboard.update`. Tier-1 rst/leaderboard/bokeh checks;
   Tier-2 end-to-end report on the Stage-4 sweep. Q&A. Log.

### Q&A

## Logs

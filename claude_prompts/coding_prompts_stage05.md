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
- **Q&A holds open questions for JXP** — pose them, do **not** self-answer (JXP
  answers before the next task; decisions/rationale go in the Logs).
- Run tests via the env interpreter directly
  (`/home/xavier/miniforge3/envs/ocean14/bin/python -m pytest -q`); `conda
  activate` fails non-interactively. **Run the suite without `$OS_COLOR`**
  (CI-equivalent) before declaring a task done.
- `report` consumes **only persisted artifacts** (results + metrics + chains +
  provenance) — fully regenerable, no re-fitting. Unlike `metrics`/`diagnostics`
  (which are BING/ocpy-free), `plotting`/`report` **may import `bing.plotting`**
  and matplotlib/bokeh — reuse `bing.plotting` where it fits.
- Capitalize **BING** in prose. Keep docstrings RST-clean so `sphinx-build -W`
  stays green; new public APIs are autodoc'd via `docs/source/api/index.rst`.
  The generated report `.rst` pages must also build under `-W`.

## Context

- `docs/design/IOPtics_implementation.md` — §Reporting (`plotting` primitives;
  `report.figures`/`tables` standard set; cross-sweep `leaderboard`; standalone
  BokehJS; `rst`/`standard.build` three report types; single accumulating Sphinx
  site, leaderboard landing page; artifact split [Q22]; default ranking [Q23];
  curated per-obs figures [Q24]; provenance stamping).
- bing: `plotting.{show_anw_fits,corner_plot,hist2d}`.
- Inputs (per sweep, under `io.sweep_dir(sweep_id, root=...)`):
  `results_{spectral,scalar}.parquet`, `metrics_{spectral,scalar,pairwise}.parquet`,
  `chains/<algorithm>_<obs_id>.npz`, `provenance.yaml`.

### Stage 0–4 carryover (what already exists — the artifacts you render)

- **`io`** — `io.read_results(sweep_id, root=None)` → `(spectral_df, scalar_df)`;
  `io.sweep_dir(...)`; `io.load_chain(path)` → numpy dict. Stage 4 added an
  **`Rrs_obs`** spectral component (the observed Rrs the fit saw; `truth`/bounds
  `NaN`, unit `1/sr`) and made `io.save_chain` persist **`pnames`** (fit-param
  names) in the chain NPZ.
- **`metrics.compute(sweep_id, *, root=None, …)`** reads the results tables and
  writes three **wide, tidy** parquet tables (file-name constants
  `metrics.METRICS_{SPECTRAL,SCALAR,PAIRWISE}_FILE`), returning a
  `metrics.MetricsTables(spectral, scalar, pairwise)` namedtuple. Every table is
  grouped by **`fit_method`** and carries a **`stratum`** column (`'all'` plus the
  Chl bins `oligotrophic`/`mesotrophic`/`eutrophic`); the **intersection count
  `n`** rides on every accuracy row.
  - **`metrics_spectral`** — keys `(dataset, algorithm, fit_method, stratum,
    component, wavelength)`; cols `n, mae, bias, abs_bias, rms_log,
    median_ratio, coverage68, coverage95` over the native grid (truth-bearing
    components `a/bb/a_ph/a_dg/bb_p`).
  - **`metrics_scalar`** — keys `(dataset, algorithm, fit_method, stratum,
    component, ref_wave, ref_match, caveat)`. Three row kinds share the table:
    (i) **ref-band accuracy** for spectral components at 440/443/555/670
    (`ref_match` = the native band used, ±3 nm) with the accuracy cols above plus
    cross-algorithm ranks `mae_rank, abs_bias_rank, rms_log_rank`; (ii)
    **derived-scalar accuracy** for `Chl`/`a_cdom440`/`Sdg` (`ref_wave` NaN);
    (iii) the **§2 closure row** `component='Rrs'` carrying `chi2_nu_median,
    frac_good, frac_overfit, frac_underfit, mae` (= Rrs MAE), `bias` (= Rrs bias),
    `frac_fit_noise, frac_qc_fail`. Closure-only cols are NaN on accuracy rows and
    vice-versa. GLORIA `a_dg` rows are flagged `caveat='CDOM_vs_adg'`.
  - **`metrics_pairwise`** — a `contest` column splits two row kinds: `'wins'`
    rows `(dataset, fit_method, stratum, component, ref_wave, algorithm, wins,
    contests, win_frac, win_frac_rank)` (per-spectrum head-to-head, ties split
    0.5); `'dbic'` rows `(dataset, fit_method, stratum, model_a, model_b, n,
    frac_favor_a, frac_favor_b, median_dbic)` (the `expb_pow`-vs-`giop` ΔBIC
    contest, χ²-only / like-for-like).
- **`diagnostics`** — figure-data (arrays only), BING/ocpy-free; the inputs your
  `plotting` primitives consume:
  - `taylor_stats(table, component, ref=None)` → DataFrame per algorithm
    (`corr, std_model, std_ref, norm_std, crmsd, norm_crmsd, n`), log10 space.
  - `target_stats(table, component, ref=None)` → per algorithm
    (`bias, unbiased_rmsd, signed_unbiased_rmsd, total_rmsd, n`), log10 space.
  - `scatter_data(table, component, ref=None)` → `dict(points[df: algorithm, x, y],
    guides{one_to_one, three_to_one, one_to_three}, lims)`.
  - `ratio_hist_data(table, component, ref=None)` → `dict(edges, centers,
    counts[df per algorithm])` over `metrics.RATIO_EDGES`.
  - `residual_spectra(spectral, scalar, obs_id)` → `dict[algorithm] →
    dict(wave, residual=Rrs_obs−Rrs_model, chi2_nu)`.
  - `corner_data(chain_file)` → `dict(samples[(N, nparam)], labels, Chl, Y)`;
    `labels` are the persisted `pnames` (generic `p0..` only if absent).
  - `dbic_cdf_data(scalar, a, b, by=None)` → `dict(dbic, cdf, n, frac_favor_a,
    frac_favor_b)`.
- **The Stage-4 sweep to report on** (Tier-2): the build prototype
  `ioptics/runs/prototypes/expb_giop/build_v1.py`, `sweep_id =
  expb_giop_L23_v1` (L23; `expb_pow` χ²-only + `giop` with an MCMC subset). Its
  `main(flg)` already stubs flag 2 = `metrics.compute`, flag 3 = `report.standard.build`.

### ⚠ Known constraints / decisions — read before coding

- **Tables are wide, not melted.** A figure/table is a group-by + column select,
  not a `metric=='mae'` filter. `report.tables.accuracy`/`qc` read columns
  directly from `metrics_scalar`.
- **`fit_method` is a key** — pick the population deliberately (χ² for the
  cross-algorithm headline; the MCMC subset for corner/coverage). Don't pool χ²
  and MCMC rows. ΔBIC/wins are already χ²-only / like-for-like.
- **Strata are rows, not a separate axis.** Filter `stratum=='all'` for the
  headline; the per-bin rows feed stratified tables/figures.
- **Scatter guides are 1:1 / 3:1 / 1:3** (the design's "0.3:1" = the 1:3 line,
  factor ⅓). `plotting.scatter_log` should consume `scatter_data`'s `guides`.
- **Ranking inputs** (leaderboard / `tables.accuracy`): rank on
  `metrics_scalar` columns — `mae`/`abs_bias`/`rms_log` (lower better, already
  `*_rank`-ed within `(dataset, fit_method, stratum, component, ref_wave)`) and
  `win_frac` from `metrics_pairwise` (higher better). Default order: wins →
  `|bias|`/MAE at ref-λ (Q23).
- **`corner_data` labels** now come from persisted `pnames`; pass them straight
  to `bing.plotting.corner_plot`.
- **Provenance** lives in `runs/<sweep_id>/provenance.yaml` (versions +
  per-algorithm blocks) — header-stamp report pages from it; don't recompute.

## Prompts

### Coding

1. `plotting.py` static primitives.
2. `report/figures.py` + `report/tables.py`.
3. `report/leaderboard.py`.
4. `report/bokeh.py`.
5. `report/rst.py` + `report/standard.py`.
6. Tests + wire build-script stage 3.

### Pull Requests

1. I have issued a PR for this stage. Please review it and post it to GitHub.  Also, investigate the CI issues and fix them. Please log your work in the Logs section below.
2. Please read the PR comments and make any needed changes to the code to address them.  And, if you have any additional questions, please add them to the Q&A section below. Log your work.

### Stage 6

1. We are ready to start Stage 6.  Modify the prompt file `coding_prompts_stage06.md` to reflect the changes in this stage.

## Modules

### Tasks

1. **`plotting.py`.** `scatter_log` (1:1/3:1/1:3 guides, from `scatter_data`),
   `ratio_hist` (from `ratio_hist_data`), `spectra_band` (value + 68/95 bands),
   `residual_rrs` (from `residual_spectra`), `taylor` (from `taylor_stats`),
   `target` (from `target_stats`), `corner` (→`bing.plotting.corner_plot`, using
   `corner_data`'s `labels`), `dbic_cdf` (from `dbic_cdf_data`); each takes the
   diagnostic/metric arrays, returns a `Figure`, no I/O. Tier-1 smoke (figure
   builds, `Agg` backend). Q&A. Log.

2. **`report/figures.py` + `tables.py`.** The standard per-(algorithm,dataset)
   set (`scatter_set`, `spectra_set`, `closure_set`, `taylor_target`, `corner_set`,
   `dbic_cdf`) and `tables.accuracy`/`qc` read straight from the wide
   `metrics_{spectral,scalar,pairwise}` tables (filter `stratum`/`fit_method`,
   select columns); per-obs figures only for the **curated handful** (the MCMC
   subset + a few per trophic bin). Write PNG+PDF/CSV to
   `runs/<sweep_id>/figures/`. Tier-2 on the `expb_giop_L23_v1` sweep. Q&A. Log.

3. **`report/leaderboard.py`.** `update(runs_root)` folds every sweep's
   `metrics_scalar` (filtered to `stratum='all'`, the χ² population, ref-λ rows)
   into `$OS_COLOR/IOPtics/leaderboard.parquet` (idempotent; re-fold replaces a
   sweep's rows); default ranking wins → `|bias|`/MAE at ref-λ; `render(fmt='rst')`.
   Tier-1 idempotency + ordering. Q&A. Log.

4. **`report/bokeh.py`.** Standalone BokehJS (`file_html` + `CustomJS`) —
   `interactive_scatter`, `interactive_leaderboard` (select algorithm/dataset/
   stratum/`fit_method`; hover/pan/zoom) returning self-contained HTML. Tier-1
   (HTML produced, contains expected selectors). Q&A. Log.

5. **`report/rst.py` + `standard.py`.** `standard.build(sweep_id, kind ∈
   {per_algorithm, cross_algorithm, per_dataset})` → assemble figures/tables/bokeh
   into `docs/source/reports/<sweep_id>/<kind>.rst`, **copy** lightweight assets
   from `runs/<sweep_id>/figures/`, header-stamp provenance versions; link into the
   toctree; leaderboard as landing page. Tier-2. Q&A. Log.

6. **Tests + build-script stage 3.** Wire `build_v1.py` flag 3 to
   `standard.build` + `leaderboard.update`. Tier-1 rst/leaderboard/bokeh checks;
   Tier-2 end-to-end report on the `expb_giop_L23_v1` sweep. Q&A. Log.

### Q&A

## Logs

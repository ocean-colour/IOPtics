# Code IOPtics — Stage 7: Reporting rework (make the comparison usable)

## Goal

Turn sweep artifacts into pages an outside ocean-colour scientist can act on. The
machinery works; the presentation does not. **Exit criterion:** a reader arriving
cold can answer *"which IOP model should I use for water like mine, and can I trust
its uncertainties?"* from the docs site — no published figure is blank, every page
states numbers, the leaderboard folds every sweep with no spurious ranks, and any
published number traces back to the exact configuration that produced it.

Implements **Stage 7** of `docs/design/IOPtics_implementation.md` (§Reporting rework,
§Staged plan) and the revised §Reporting / §Metrics of
`docs/design/IOPtics_design.md` (v0.16). Background conversation, with JXP's answers
to Q1-Q12 and the S1-S13 proposals: `claude_prompts/improve_reporting.md`.

## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- **Q&A holds open questions for JXP** — pose them, do **not** self-answer (JXP
  answers before the next task; decisions/rationale go in the Logs).
- Run tests via the env interpreter directly. **On this Mac that is
  `/Users/xavier/miniforge3/envs/ocean14/bin/python`** (the older docs say
  `miniconda3`, which is the workstation path); `conda activate` fails
  non-interactively. **Run the suite without `$OS_COLOR`** (CI-equivalent) before
  declaring a task done, and with it when the task touches real artifacts.
- `sphinx-build -W` on `docs/source` must stay green — it is green today, so any
  warning is ours. Baseline: **230 passed / 38 skipped** without `$OS_COLOR`,
  **264 / 4** with it.
- Capitalize **BING** in prose. New public APIs are autodoc'd via
  `docs/source/api/index.rst`; keep docstrings RST-clean.
- **Tiered tests** (`ioptics/tests/conftest.py`): guard data-dependent tests with
  `@needs_l23` / `@needs_pangaea` / `@needs_gloria`, and anything shelling out to
  Sphinx with `@needs_sphinx`.
- **The hang guard is load-bearing (Stage 6, Task 2).** `conftest` imposes a
  per-test wall-clock ceiling (`_guard_against_hangs`, dependency-free `SIGALRM`,
  deferring to `pytest-timeout` when installed), so a wedged test fails fast with a
  traceback instead of hanging the run. Do **not** work around it by raising the
  ceiling on a test that hangs — a hang is the finding. Long real-data work belongs
  in a script under `runs/`, not in the suite.
- **Git.** The current branch is `improve-reporting`; PRs #8/#9/#10 all merged into
  **`develop`**, so that is the base for this stage's PR. JXP runs every
  state-changing git command.
- Reporting changes must be **regenerable**: no hand-edited generated pages. A
  hand-written block belongs in a per-sweep `findings.rst` include the builder does
  not overwrite.
- `gh` is available; it has no stored login, so pass a token from the keychain:
  `export GH_TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill | sed -n 's/^password=//p')`.

## Context

### Stage 0-6 carryover (what you are reworking, not rebuilding)

- **`metrics.compute(sweep_id)`** → `metrics_{spectral,scalar,pairwise}.parquet`,
  keyed by `dataset`/`algorithm`/`fit_method`/`stratum`/`component`/`ref_wave`, with
  ±3 nm ref-band matching, χ²ᵥ-based closure QC (`CHI2NU_QC_MAX = 5.0`), relative
  misfit, coverage68/95, wins, and the GLORIA `caveat='CDOM_vs_adg'` stamp.
- **`report/`** — `figures`, `tables`, `leaderboard`, `bokeh`, `rst`, `standard`,
  over `plotting` (matplotlib primitives) and `diagnostics` (figure *data*).
  `standard.build(sweep_id, kind=...)` writes `docs/source/reports/<sweep_id>/`.
- **Two published pages** (`expb_giop_L23_test20`, `gloria_turbid_v3`) and the
  leaderboard landing at `docs/source/reports/index.rst`.
- **Artifacts:** `$OS_COLOR/IOPtics/runs/<sweep_id>/` (parquet, `provenance.yaml`,
  `figures/`, `chains/`) + `$OS_COLOR/IOPtics/leaderboard.parquet`. Never committed.
- **Registry:** `_STANDARD_SEED` = `expb_pow`, `giop`, `gsm`; the turbid trio
  (`expb_pow2flat` k=6, `expb_pow2` k=7, `expb_powflex` k=5) is **opt-in** via
  `register_turbid(overwrite=True, maxfev=TURBID_MAXFEV)` with
  **`TURBID_MAXFEV = 40000`**. That budget is not cosmetic — it is what turned 72
  failed GLORIA fits into none — and it is exactly what provenance fails to record
  (Task 9).
- **Status vocabulary and its thresholds live in `records`** (Stage 6):
  `STATUSES = ('ok', 'poor_fit', 'out_of_scope', 'fit_failed')`, with
  `CHI2NU_POOR_FIT = 5.0` **shared with `metrics.CHI2NU_QC_MAX`** so the per-row
  status and the aggregate `frac_qc_fail` cannot drift, plus an `Rrs`-peak-wavelength
  threshold that marks turbid spectra `out_of_scope`. Keep the four distinct in every
  report: on the GLORIA sweep 63% were `out_of_scope` and 16% `poor_fit`, which is a
  statement about the *models*, not a defect in IOPtics.
- **GLORIA's noise handling is per-dataset and load-bearing** (`prep`): a default
  fractional error floor (0.05) because the quoted errors are too tight for χ² to
  mean anything, and a **wider imputation fraction** (0.10) for the ~70% of spectra
  that quote no uncertainty at any band — tagged `insitu+floor:0.05` vs
  `insitu+imputed:0.1`, with `ImputedUncertaintyWarning` raised once per batch.
  `noise_floor=False` means *no floor*; `noise_imputed=False` means *invent nothing*
  (un-measured bands keep non-finite variance) — the two are independent since PR #9.
  Any GLORIA number in a report must say which regime produced it.
- **Sweep config gained `wv_min`/`wv_max`** (Stage 6) — `multi_v2` uses 400-750 nm,
  which is how a dataset whose native grid overruns the Gordon table is handled.
- **Build scripts have a CLI** (first-sweep step 3a): `build_v1.py <flg>
  [--n-cores N] [--strict BOOL] [--obs-ids A:B]`, threading into
  `main(flg, *, n_cores, strict, obs_ids)`. `runs/first_full_run.src` is the
  `at`-runnable script for the workstation's full L23 sweep.
- **`AlgorithmConfig.overrides` is a trap.** `config` accepts and round-trips
  per-algorithm overrides (`mcmc`, `rt`, priors, …), but `run_sweep` does
  `registry.get(ac.name)` and **never reads them** (verified: no reference to
  `overrides` anywhere in `run.py`). So a sweep's verbatim config copy can advertise
  settings the run never used — Task 9 must apply them or reject them at load.

### ⚠ Known defects (verified; full table in the implementation doc §Reporting rework)

1. Figure set hardcoded to `a(440)`/`bb(555)` + the `expb_pow`-vs-`giop` ΔBIC pair
   → **every static figure on the GLORIA page is a blank "no data" panel**, under
   captions confidently explaining how to read them (`standard._REP_REFS`,
   `figures.dbic_cdf` defaults).
2. A degenerate panel is a valid path, so empty sections publish (`_fig_section`).
3. Generated prose interpolates **no numbers**; parts of it are wrong ("all metrics
   0 = perfect" is false for `coverage68/95`, `median_ratio`, `win_frac`;
   "left/right" for vertically stacked figures; selectors with one option).
4. `spectra_set` only under the never-built `per_algorithm` kind, which **crashes on
   string `obs_id`** (`int(...min())`); `closure_set`, `corner_set`, `ratio_hist`
   never called at all → the pages carry **no spectral information**.
5. No figure styling (no rcParams / layout / units) → colliding tick labels; the
   "Taylor diagram" labels azimuth in degrees with no centred-RMSD arcs.
6. Algorithm colour comes from within-figure order → a model changes colour between
   pages (`plotting.scatter_log` `groupby(sort=False)` + default cycle).
7. `tables.accuracy` drops `dataset` and merges wins on
   `(algorithm, component, ref_wave)`; `tables.qc` merges on `algorithm` alone →
   silent row multiplication on any multi-dataset sweep.
8. `leaderboard._fold_sweep` has the **same dataset-blind wins merge** (reproduced:
   352 rows where 320 expected, win fractions cross-assigned), hard-filters
   `fit_method == 'chisq'` so **MCMC results can never appear**, and drops the
   `bing`/`ocpy` commits.
9. `leaderboard.ranked` ranks by `cumcount()+1` with no finiteness check → **144 of
   160 published rows are all-NaN and still ranked 1-4**.
10. Bokeh depends on `cdn.bokeh.org` (version already drifting 3.9.0/3.9.1 between
    pages); hover lacks `obs_id`; guide-line convention differs from the static
    scatters; `interactive_leaderboard` implemented and unused.
11. `metrics_spectral.parquet` is written, loaded, and **consumed by nothing** — no
    accuracy-vs-λ figure exists. Tables are pinned to `stratum='all'` and
    `fit_method='chisq'`, so per-stratum and MCMC results never reach a page.
12. Provenance omits `maxfev` and the `mcmc` block, records a stale
    `noise_model: pace`, never persists the per-record noise tag, ignores
    `AlgorithmConfig.overrides`, and stops `provenance_id` at `results_scalar`.
13. No `:alt:` text, no column widths, full float64 precision in the CSV tables;
    `standard.build` never prunes orphaned assets.
14. **`metrics.wins` cannot support a paired test** (re-verified at the code):
    it runs the round-robin correctly but tallies into `(group_key, algorithm)` via
    `_bump`, so the **opponent's identity is discarded** — with four algorithms the
    36 "contests" on the GLORIA sweep are 12 spectra × 3 opponents, non-independent,
    and not even the A-vs-B tally survives. Ties split credit 0.5. The per-spectrum
    ΔBIC vector is likewise computed inside the figure builder and thrown away.
15. **Cost is unrecoverable without instrumentation** (verified in the sibling repo):
    `bing/fitting/chisq_fit.py:117-119` calls `curve_fit(..., full_output=False)`, so
    scipy's `infodict` — and with it `nfev` — never reaches IOPtics. No wall time,
    no MCMC step count, and no `maxfev` *actually used* is persisted anywhere.

### ⚠ Decided by JXP (Q1-Q12 in `improve_reporting.md`) — do not re-litigate

- **MOANA is out of scope** for this reporting work.
- Figure sets **data-driven**; empty sections **suppressed**.
- **Polish on the smoke first**; JXP runs the full L23 sweep on the workstation later.
- The GLORIA investigation is **converted to RST and published**, original `.md` kept.
- **10 exemplar spectra per sweep on their own page**: best, worst, 8 median.
- **One style module**, ocean palette from the docs; Taylor made readable *(but see
  Q&A — the community evidence argues for demoting it; JXP to confirm)*.
- Landing page gets **all four** of: headline table + drill-down, all-NaN rows
  hidden, per-sweep summary cards, interactive leaderboard. Leaderboard **re-folds
  every sweep**.
- **Both** per-algorithm and per-dataset reports are built.
- Stale docs fixed; **`gsm` and the turbid trio documented** with equations.
- **BokehJS vendored** into `_static`.
- **All three** discarded slices surfaced: accuracy vs λ, per-stratum, χ² vs MCMC.
- **Over-confident error bars are reported**, and statistically indistinguishable
  algorithms are **said to be indistinguishable** rather than ranked.

## Prompts

### Coding

0. Update this prompt file to reflect changes from any earlier stage.
1. Figure style module + per-algorithm visual identity.
2. Data-driven artifact selection + empty-section suppression.
3. Metrics & table correctness (dataset-aware, honest denominators, coverage).
4. Pairwise statistics that can detect a tie.
5. Leaderboard fold + landing page + vendored BokehJS.
6. Profile pages (per algorithm, per dataset) + coverage matrix + glossary.
7. Exemplar-fits page + wire the unused figure builders.
8. Wavelength-resolved, per-stratum, and χ²-vs-MCMC slices.
9. Provenance hardening.
10. Publish the GLORIA investigation; document `gsm` + the turbid trio; fix stale text.
11. Generate the missing evidence (bounded `multi_v2`, L23 smoke re-run, re-fold).

### Pull Requests

1. I have issued a PR for this stage. Please review it and post it to GitHub. Also,
   investigate any CI issues and fix them. Please log your work in the Logs section
   below.
2. Please read the PR comments and make any needed changes to the code to address
   them. And, if you have any additional questions, please add them to the Q&A
   section below. Log your work.

## Modules

### Tasks

1. **Figure style + algorithm identity.** Add a single style module (rcParams:
   fonts, `constrained_layout`, dpi, the `docs/source/_static/custom.css` ocean
   palette, axis-unit helpers like `a [m⁻¹]`) applied by `ioptics.plotting`, the
   `docs/figures/` generators **and** `reports/scripts/`. Add a **registry-derived
   colour + marker per algorithm** so a model looks the same on every page and
   adding one does not reshuffle the others (marker as well as colour, for
   colour-blind and greyscale readers). Fix the scatter's colliding tick labels and
   annotate statistics **inside** the panel (`N`, scored `n`, ratio, MPD). Taylor:
   correlation-labelled azimuth + centred-RMSD arcs, or demote per Q&A. Tier-1 tests
   on the mapping's stability. Q&A. Log.

2. **Data-driven artifact selection.** 
   Read my answers in the Q&A section below and react accordingly. Then:
   Replace `standard._REP_REFS` and the
   `dbic_cdf` default pair with selection **derived from the sweep**: components and
   ref-λ that actually carry truth, and ΔBIC pairs that exist among the sweep's
   algorithms (all pairs, or the k-extremes — propose). Suppress any section whose
   data is empty, replacing it with one sentence saying why. Fix
   `kind='per_algorithm'`'s `int(obs_id)` crash (string ids) and make
   `standard.build` prune assets it no longer generates. **Verify on
   `gloria_turbid_v3`: the page must show `a_dg(440)` and no blank panels.** Q&A. Log.

3. **Metrics & table correctness.** `tables.accuracy`/`qc`: carry `dataset` and merge
   on it. Name the three denominators distinctly wherever they appear (`n_attempted`,
   spectra scored, surviving truth pairs — 100 / 21 / 12 on the GLORIA sweep).
   Report `coverage68/95` against their nominal targets with a miss flag. Round the
   published CSVs to a sane precision, add `:widths:`/`:alt:`, and state each
   metric's "perfect value" (fixing the false "0 = perfect" prose). Tier-1 tests
   including a two-dataset synthetic table that currently mis-joins. Q&A. Log.

4. **Pairwise statistics that can detect a tie.** `metrics.wins` discards the
   opponent's identity, so no paired test is possible; the per-spectrum ΔBIC vector
   is thrown away too. Add a pass over `results_spectral`/`results_scalar` (no
   re-fitting) that keeps per-pair, per-spectrum differences, and derive the tie
   verdict from it — bootstrap intervals per the Brewin round-robin precedent, an
   effect-size floor, or both (see Q&A). Report "indistinguishable" instead of a
   rank, and **never rank a contest with no finite metric**. Expect small `n` (12 on
   GLORIA `a_dg(440)`) — "underpowered to distinguish" must be printable. Q&A. Log.

5. **Leaderboard + landing page.** Fold: add `dataset` to the wins merge, carry
   `fit_method` (drop the χ²-only filter), keep the closure columns the fold
   discards (`chi2_nu_median`, `frac_poor_fit`/`frac_out_of_scope`/`frac_fit_failed`,
   `rel_misfit_median`), keep the `bing`/`ocpy` stamps + the algorithm digest, and
   promote `frac_ok` to a scored quantity (Brewin's η). Landing page: headline table
   per `(dataset, component)` with the full grid on a drill-down page, all-undefined
   rows hidden, per-sweep summary cards (date, dataset, algorithms, `n`, one-line
   finding) instead of the bare glob toctree, and `interactive_leaderboard` wired up.
   **Vendor BokehJS into `_static`** (drop the CDN tags), state the downsampling
   fraction on the figure, and put `obs_id` in the hover. Q&A. Log.

6. **Profile pages + coverage matrix + glossary.** New cross-sweep report kinds: one
   page per **algorithm** (what it parameterizes from its `AlgorithmSpec`, where it
   wins/loses across datasets and strata, its calibration panel, accuracy vs λ, known
   failure modes, exemplar fits, which sweeps/versions contributed) and one per
   **dataset** (summary paragraph with numbers, the dataset's truth matrix, ranked
   tables with ties grouped, accuracy vs λ, per-stratum breakdown, retrieval-success
   accounting, χ² vs MCMC). Add the **coverage matrix** (algorithms × datasets) that
   distinguishes *not evaluated* / *evaluated but unscorable* / *failed* — built by
   walking the runs tree, since absence of a leaderboard row is ambiguous. Add a
   **metrics glossary** page every table column links to. URL scheme + generated-vs-
   curated split per Q&A. Q&A. Log.

7. **Exemplar-fits page.** Per sweep, a page of **10 exemplars — best, worst, and 8
   median** by fit quality — each panel labelled with `obs_id`, χ²ᵥ and relative
   misfit, in the clear→turbid ordering used by `reports/figures/wide_example_fits.png`.
   Wire the unused builders: `closure_set` (Rrs residual + χ²ᵥ), `corner_set` (where
   chains exist), and a `figures.*` wrapper for `ratio_hist`. Q&A. Log.

8. **The three discarded slices.** Consume `metrics_spectral` for an
   **accuracy-vs-wavelength** figure per component (all algorithms overlaid, small
   multiples where it helps) — the figure an ocean-colour reader looks for first.
   Emit **per-stratum** tables/figures (pass `by=` to `dbic_cdf` too) and a **χ² vs
   MCMC** comparison where both exist. Q&A. Log.

9. **Provenance hardening.** Emit `maxfev` and the `mcmc` block in the algorithm
   block, plus a **digest** of it; resolve or drop the stale `noise_model`; persist
   the per-record `noise_model`/`noise_seed` into `results_scalar` (so the ~70%
   imputed-weight fact is on disk); **apply or reject** `AlgorithmConfig.overrides`
   rather than ignoring them; carry `provenance_id` into `metrics_*` and the
   leaderboard. Cross-sweep identity policy per Q&A. Q&A. Log.

10. **Publish and correct the prose docs.** Convert `reports/gloria_fits_report.md`
    to RST under `docs/source/` (keep the markdown original for posterity; its 11
    figures are referenced exactly once each, so the conversion is mechanical) and
    link it from the site. Document **`gsm`** (registered, currently absent from the
    docs) and give `expb_pow2`, `expb_pow2flat`, `expb_powflex` the equation +
    parameter-table treatment the two defaults get. Fix the stale scoping text
    (`index.rst` "Through Stage 2", `api/index.rst` "Stage-0 modules only",
    `models.rst` "runs two side by side"), and use the orphaned
    `_static/ioptics_graphic.png` as the landing hero. Q&A. Log.

11. **Generate the missing evidence.** Re-run the L23 smoke locally so its rows
    return to the leaderboard, and run the existing-but-never-run `multi_v2`
    ({L23, PANGAEA} × {`expb_pow`, `giop`, `gsm`}) **bounded to PANGAEA's 3 247
    truth-carrying ids** (unbounded is 64 071 obs ≈ 192 000 fits with ~95%
    unscoreable). Then `leaderboard.update()` over everything and confirm the
    coverage matrix fills. If `expb_pow` hits `maxfev` on PANGAEA as it did on
    GLORIA, that is a reportable result, not a blocker. Report counts + wall time.
    Q&A. Log.

### Q&A

> Open questions for JXP (posed, not self-answered). These are P1-P10 from
> `claude_prompts/improve_reporting.md` and items 6-12 of the design doc's Open
> Questions table, restated here so this doc stands alone. Answer either place.

**Blocking Task 4:**

- **What counts as "statistically indistinguishable"?** (a) bootstrap intervals on
  the score, per Brewin et al. 2015 (1000 resamples, scores normalised by the
  all-model average, overlapping intervals = tie); (b) a declared effect-size floor
  (e.g. |Δmae| < 0.01, i.e. ~1%, as "no practical difference"); (c) both — tie by
  statistics, separately flag differences too small to matter. The threshold in (b)
  encodes what *you* consider a scientifically meaningful difference, so it needs
  your number.

>A. Use 10%

**Blocking Task 6:**

- **Page/URL scheme** (permanent once published): `reports/algorithms/<name>` +
  `reports/datasets/<name>`, or top-level `algorithms/` + `datasets/`? Note the
  collision with the existing *reference* pages `models.rst` / `datasets.rst` — I
  would rename those to "Model reference" / "Dataset reference" to keep them
  distinct.
>A. That is fine.
- **Generated, curated, or hybrid?** Fully generated profiles stay current
  automatically but can only say what the metrics say; hybrid (generated
  tables/figures + a hand-written findings block) is what makes them worth reading.
>A. Hybrid
- **How opinionated should the site be?** Publish a per-water-type *recommendation*,
  or only ranked evidence? On the turbid data today an honest recommendation would
  read "none of these four work".
>A. No recommendations yet

**Blocking Task 9:**

- **Cross-sweep identity.** If the same algorithm name ran with different
  `maxfev`/priors/RT in two sweeps, is its profile (a) one page pooling them with a
  "what varied between sweeps" block, or (b) split per spec digest?
>A. (a)

**Affects Task 1:**

- **Taylor diagram: fix or demote?** Your Q6 answer was to make it readable. The
  community evidence points the other way — Brewin computed the full Taylor triple
  and deliberately did not draw the diagram, and Seegers' critique undercuts the
  r²/RMSE basis it rests on. Target (bias vs unbiased RMSD) is uncontroversial and
  stays. Confirm: invest in Taylor, or demote it to optional and spend the effort on
  annotated scatters + ratio distributions?
  > **Update after Task 1:** the readability fix is **done** (correlation-labelled
  > azimuth, centred-RMSD arcs, no colliding labels), so this is no longer blocking —
  > it is now only a question of whether the *report pages* keep giving Taylor a
  > section. Having rendered it on real data I lean toward keeping it available but
  > **not** as a page section: with four algorithms clustered at corr ≈ 0.3 it says
  > far less than the annotated scatter, whose legend states ratio and MPD outright.

>A. Yes, keep Taylor

- **Should `ratio_hist` get a page section now that it is styled?** It is the one
  builder with no `figures.*` wrapper, and the community convention is to pair every
  scatter with a **distribution of the ratios** (GIOP Figs. 1-2). It would slot in
  beside each scatter in Task 2 rather than waiting for Task 7 — say if you want that
  pulled forward.

>A. Yes, give it a page section
  > **Done in Task 2** — `figures.ratio_hist` added and a "Ratio distribution —
  > <comp>(<ref>)" section now follows each scatter.

**New after Task 10:**

- **Should the investigation report's wrong recommendation be corrected in the RST, or
  only flagged?** I flagged it — the text is verbatim and an editorial warning at the
  top lists the four superseded claims. The alternative is editing the recommendation
  itself with a marked inline correction, which reads better for a first-time reader but
  makes the published page diverge from the markdown original. My lean is to keep them
  identical and let the warning carry it, but you are the author of that report and it
  is your call.
- **Should `reports/gloria_fits_report.md` now be regenerated rather than frozen?** Its
  script (`reports/scripts/gloria_fits_report.py`) still runs, and re-running it would
  fix items 2 and 3 (the numbers corrected in prose but not in the tables) at the
  source. That would mean the markdown changes and the RST is reconverted — a bigger
  move than a footnote, and it would lose the round-by-round texture that makes the
  record honest. Freeze, or regenerate?
- **Does `gsm` deserve a sweep of its own before it is advertised?** It is now
  documented as a first-class registered algorithm, but the coverage matrix shows it has
  **never been run** — so the site describes a model it has no results for. That is
  visible (the matrix says "not evaluated") but a reader may still take the
  documentation as evidence of use. Task 11's bounded `multi_v2` includes `gsm`, so this
  resolves itself if that runs; flagging in case you would rather the page carried an
  explicit "not yet evaluated" banner until then.

**New after Task 9:**

- **Should `gloria_turbid_v3` be re-fitted so its provenance is honest, or left as a
  schema-0 sweep?** Its `results_scalar` will never carry the noise tag and its blocks
  will never show the `maxfev=40000` it actually ran at, so the published page's
  provenance is permanently weaker than the code now supports — and `prov_schema = 0`
  is the only thing saying so. Re-running stage 1 is ~100 spectra x 4 algorithms
  (minutes, and it is the sweep the whole site is built on). Options: re-run it in Task
  11 alongside the other sweeps (my lean — the 68%-imputed fact then lands on disk
  where the glossary can cite it); or leave it and treat schema-0 as a permanent
  footnote on that one page.
- **Should a raised `maxfev` be part of the algorithm's identity, or of the sweep's?**
  I put it in the digest, so `expb_pow` at `maxfev=40000` is a *different algorithm*
  from `expb_pow` at the default and the two will not pool on one profile page. That is
  defensible — the iteration budget changes which spectra get an answer at all, and on
  the turbid models it is the difference between a result and a wall of `fit_failed`.
  But it is arguably an *execution* setting like `n_cores`, in which case two sweeps
  differing only in budget should pool with a note. Say which you want; it is a
  one-line change to `_DIGEST_EXCLUDE`.
- **Do you want `overrides` used at all, now that they work?** The mechanism exists and
  is tested, but nothing in the repo uses it — `gloria_turbid_v3` raises `maxfev` by
  *patching the registry inside its build script*, which is exactly what an override is
  for and which the provenance cannot see. Converting that build script to a config
  override would make the raised budget visible in provenance for free. Worth doing in
  Task 11, or leave the build scripts alone?

**New after Task 8:**

- **Should the accuracy-vs-wavelength figure default to `mae`, or show more than one
  metric?** It is built for any column of `metrics_spectral` (`mae`, `bias`,
  `median_ratio`, `rms_log`, `coverage68/95`) but the page draws only `mae`. The
  candidate second panel-set is **coverage vs wavelength** — whether an algorithm's
  uncertainty is honest *per band* rather than only at the reference band, which is
  where over-confidence tends to hide. Cheap to add (one more call); the cost is page
  length. My lean is to add coverage once a sweep with real spectral truth exists,
  since on GLORIA neither renders.
>A. Add coverage once a sweep with real spectral truth exists.

- **Is `min_waves = 2` the right floor for calling something a spectrum?** Two bands
  draw a line segment, which is technically a spectrum and arguably still misleading;
  3-4 would be a more honest minimum for the word. On GLORIA it makes no difference
  (there is 1). Say if you want it raised before the first L23 sweep lands.
>A. Let's use 5

- **`unknown` is published as a trophic stratum.** 27 of GLORIA's 100 observations have
  neither truth nor retrieved Chl, so they form a real population that I show rather
  than drop — dropping it would make the strata look complete when they are not. But
  `unknown` is a *provenance* category, not a water type, and it sits in the same table
  as three water types. Keep it inline, move it to a footnote, or drop it with a stated
  count?
>A. Drop with a stated count.

**New after Task 7:**

- **Is `|log10(χ²ᵥ)|` the fit-quality ranking you want for the exemplars?** I ranked
  by distance from χ²ᵥ = 1 rather than by χ²ᵥ ascending, so the sweep's most *over-fit*
  spectrum is not published as its "best" fit (reasoning in the Task-7 log). The cost
  is that **"worst" is now ambiguous in principle** — it is whichever tail is further
  from 1, so on a sweep with a χ²ᵥ = 0.001 fit and a χ²ᵥ = 100 fit the "worst" panel
  would be the *over-fit* one, which is not what a reader expects from the word. On
  GLORIA it does not arise (the over-fit tail is shallow: one exemplar below 1, at
  0.89). Options: keep it; or rank by distance from 1 but define "worst" as the
  largest χ²ᵥ specifically, so the label always means under-fit. My lean is to keep it
  and let the printed χ²ᵥ disambiguate, but it is your call which the word should mean.
>A. Distance from χ²ᵥ = 1 is correct and define "worst" as the largest χ²ᵥ 

- **Should the exemplars respect `status`, or deliberately ignore it?** They currently
  ignore it, which is why 28 of the 40 (obs x algorithm) rows behind the GLORIA page
  are `out_of_scope` — spectra the model family does not claim. I think that is right,
  since the page exists to show failures and the summary now says so outright. The
  alternative is to select only `ok` fits, which on GLORIA would show 4 rows' worth of
  the clearest water and hide the finding entirely. Confirm, or say if you want a
  second grid restricted to scored fits.
>A. I confirm

- **How many exemplars, and should the count follow the dataset?** Fixed at 10 per your
  prompt (`diagnostics.EXEMPLAR_N`). With 12 rankable observations the "8 median" span
  ranks 2-9 of 12, so they are not tightly clustered around the median — on a
  3 000-spectrum L23 sweep they will be. Fine as-is, or would you rather the median
  eight were drawn from a fixed *quantile window* (e.g. the 40th-60th percentile) so
  the word "median" means the same thing on a thin sweep as on a thick one?
>A. Fine as is.

**New after Task 6:**

- **Do the profile pages belong in the top-level toctree, not just under Reports?**
  They are currently reachable through `reports/index` (the `algorithms/*` and
  `datasets/*` globs) and from the coverage matrix. A reader landing on the site's
  front page sees Installation / Dataset reference / IOP model reference / Reports /
  API — the profiles are one click deeper. Options: leave them under Reports; or add
  "Algorithm profiles" and "Dataset profiles" as top-level toctree entries next to
  the reference pages. My lean is the second, since the whole point of Task 6 was to
  stop the site being sweep-first.
- **Should a dataset profile show the dataset's own characterisation figures?**
  `reports/figures/` holds hand-made GLORIA-vs-L23 plots (`rrs_shape_contrast.png`,
  `peak_wavelength_hist.png`) from the GLORIA investigation that are exactly what a
  dataset page wants, but they live outside `docs/` and are not copied by any build.
  Pull them in (they would need copying into `_static` or the page dir), or leave the
  dataset pages numbers-only until the investigation report is converted in Task 10?

**New after Task 5:**

- **Should the L23 smoke page be un-published rather than left stale?** It is the one
  remaining page carrying the old figure set, the dataset-less CSVs and the false
  "0 = perfect" sentence, because that sweep's artifacts are not on this laptop — and
  it now also still references `cdn.bokeh.org` while every other page is vendored. It
  regenerates in Task 11 when the smoke is re-run. Until then: leave it (a stale page
  a reader might trust), or drop it from the docs tree and re-add it when regenerated?
  My lean is to leave it and fix it in Task 11, since removing a published URL is the
  more disruptive act — but you may prefer the site carry nothing it knows is wrong.
>A. Leave it
- **Does `frac_ok` belong in the rank *ordering*, not just the headline columns?** I
  promoted it to a headline column (Brewin's η is a *scored* test in his round-robin,
  so it arguably belongs in the sort). Ordering is currently wins → |bias| → MAE per
  the design's Q23, and changing it is a design-level decision — say if you want η in.
>A. No, not for now

**New after Task 4:**

- **Did "use 10%" mean what I implemented?** I read it as an **absolute** floor on the
  fractional multiplicative MAE: two algorithms are indistinguishable in practice when
  ``|mae_A − mae_B| < 0.10``, i.e. ten percentage points of multiplicative error (the
  option I offered was phrased that way, with 0.01 as the example). The other reading
  is **relative** — a 10% difference *of* the MAE, so ``|Δmae| < 0.1 × mae``, which on
  L23's mae ≈ 0.1 would be a floor of 0.01 and would call far more pairs
  distinguishable. On the GLORIA contest the choice does not matter (every Δmae is
  under both), but on the full L23 sweep it will. Confirm absolute, or switch to
  relative?
  >A. Absolute
  > **Evidence added after the Task-4 review, which measured the consequence.** With
  > `'absolute'`: two algorithms at **1% and 5%** error — a *fivefold* difference —
  > come out `indistinguishable`, and on an L23-class synthetic (ref-band MAE of a few
  > percent) **no pair can ever clear 0.10**, so every contest is declared equivalent
  > by construction. The 10% floor is effectively calibrated to GLORIA, where both
  > algorithms are ~100% wrong (`mae ≈ 1.0`). With `'relative'` the same 1%-vs-5% pair
  > resolves to a winner. Both modes are implemented (`metrics.PRACTICAL_FLOOR_MODE`,
  > default `'absolute'` per your answer) and there is a test pinning the contrast —
  > switching is a one-constant change.

- **Should the head-to-head verdict feed the leaderboard's ranking?** Today the
  leaderboard still ranks by wins → |bias| → MAE and simply refuses to rank an
  unmeasured contest. It could instead decline to rank *any* group whose pairwise
  verdicts are all ties — printing "indistinguishable" in place of 1-4, which on
  GLORIA is the honest output. That is a leaderboard-shaped decision, so it belongs in
  Task 5; flagging it now so it is not lost.
>A. Yes, feed the leaderboard's ranking

**New after Task 3:**

- **Should `metrics` persist the coverage trial count?** The calibration verdict's
  standard error currently uses `n_pairs`, but `metrics.coverage` counts a different
  population (it needs truth and both credible bounds; it ignores the retrieved
  value). They coincide for every sweep run so far, but a fit whose covariance failed
  has bands for only some pairs, and then the verdict can accuse a thin contest of
  being over-confident. Adding a `coverage_n` column to `metrics_scalar` fixes it
  properly and is a one-line schema addition — do it in Task 9 (which already touches
  the persisted schema), or leave the approximation documented?
>A. Yes, add a `coverage_n` column to `metrics_scalar`

**New after Task 2:**

- **How many `(component, ref-λ)` panels should a page carry?** `MAX_REF_PANELS` is
  3 today, best-covered first, so a full L23 sweep (which scores `a`, `bb`, `a_ph`,
  `a_dg`, `bb_p` at 440/443/555/670) shows 3 of up to ~10 rather than all of them —
  each now costing two figures, since every scatter is paired with a ratio
  distribution. Options: keep 3; raise it; or show all *total* components (`a`, `bb`)
  plus the best-covered decomposed one, which matches the community's
  total-before-decomposed convention. My lean is the last.
>A. ok, try the last

- **Should the ΔBIC contest stay a single k-extreme pair per page?** I implemented
  the k-extremes because that is the "does complexity pay" question. An all-pairs
  ΔBIC/win matrix would say more, but it belongs with the leaderboard work in Task 5
  — confirm you are happy for it to land there rather than on each sweep page.
>A. I confirm

**Affects Tasks 3 and 5:**

- **Which metric family leads?** Ours is the fractional multiplicative form
  (`10^mean|log10(M/O)| − 1`, so 0.109 = 10.9%, 0 = perfect), matching Erickson
  2023. Seegers publishes the **un-subtracted factor** (1.109; "1.5 = 50% error").
  Do we (a) keep ours and label the convention, (b) switch to Seegers' factor form,
  or (c) show both? Also: add GIOP's `Ratio`/`MPD` under those names for continuity
  with the IOP literature (nearly free — we compute both), and MdSA/SSPB for the
  inland/coastal audience that GLORIA belongs to?

>A. Follow Erickson 2023

**Scope questions:**

- **Is computational cost in scope?** Runtime per fit and MCMC step counts are
  recorded **nowhere**, and `nfev` is not retrievable downstream (BING's χ² fitter
  calls `curve_fit(..., full_output=False)`). Reporting cost needs instrumentation in
  Task 9 plus a re-run. A community comparison of a k=3 against a k=7 model usually
  wants it.
>A. No, for now computational cost is not in scope

- **Is the "add your own model" on-ramp part of this stage?** A page showing an
  outsider how to register their parameterization, run a bounded sweep, and get the
  standard report is the highest-leverage item for the stage goal — but it wants the
  profile pages solid first. In Stage 7, or a Stage 8?
>A. No, add your own model is not part of this yet
- **Task 11 execution:** run the bounded `multi_v2` here on the laptop (both datasets
  resolve), or defer it to the workstation alongside the full L23 sweep?
>A. Run the bounded `multi_v2` here on the laptop

## Logs

### 2026-08-07 (Stage 7, Task 10: publish and correct the prose docs)

**No Task-9 answers were outstanding**, and none of the three open ones blocks this.

**The GLORIA investigation is published** at `docs/source/reports/gloria_investigation.rst`
— 904 RST lines from the 707-line markdown, all 11 figures copied to
`reports/gloria_figures/` and resolving, the markdown original byte-identical for
posterity. A Fable subagent did the conversion; I gave it the RST pitfalls that bite
this repo (underline lengths, `list-table` over grid tables, duplicate link names) and
it came back with a build clean apart from the expected "not in any toctree".

**The conversion surfaced seven stale or self-contradictory claims in the original, and
I did not silently fix any of them.** The report is a scientific record and its
self-corrections are its most valuable part, so the text is verbatim and an
**editorial `.. warning::`, explicitly dated and marked as not part of the original**,
now heads the page listing the four that matter:

1. **The closing recommendation is wrong.** It still says "the real fix is a richer
   backscattering model", with the correction 400 lines above it rather than beside it.
   Three richer backscattering models were subsequently built and run, and they agree
   with `expb_pow` and each other **to three decimals**. This was the document's
   biggest live-but-wrong claim and a reader meeting it cold would have been misled.
2. The Round-4 notice claims two numbers were "corrected in place below"; **one was
   not** — the convergence table still reads 5/40 → 15/40 where the corrected figure is
   40/40.
3. The inflated-noise table's `measured` row still reports 0.48 while the paragraph
   beneath identifies 0.48 as the biased value and 0.64 as the honest one.
4. Two dangling cross-references (an unlabelled "Round-3 table", a χ²ᵥ of 7.2e1
   attributed to rounds that do not contain it).

**Wiring it in needed a code change, not a hand-edited toctree.** `reports/index.rst` is
*regenerated* by `build_landing`, so a hand-added entry would be silently dropped on the
next build — and a page in no toctree is a `sphinx -W` failure. `standard.CURATED_REPORT_PAGES`
now names hand-written pages under `reports/`, included **only when the file exists** so
the entry cannot dangle instead. Tested both directions plus idempotency.

**`gsm` is documented** — it was registered and entirely absent from the docs. I read
its constants out of BING rather than assuming them: `S_dg = 0.0206` nm⁻¹ and
`η = 1.0337`, both pivoting at **443 nm** (where `giop`/`expb_pow` pivot backscatter in
the green), which are the canonical Garver–Siegel–Maritorena values. The point worth
making, and now made: `gsm`'s second parameter **is chlorophyll itself**, not an
absorption amplitude — so it is directly comparable against a dataset's Chl truth
without an absorption-to-Chl conversion, and comparing it against `giop` (same *shape*
of model, different fixed constants) isolates how much error comes from the choice of
fixed slope rather than from the model's structure.

**The turbid trio got the equation + parameter-table treatment.** Their `b_bp` forms are
written out (mineral pivoting at 700 nm, organic at 600 nm — each anchored where it does
its work), `Pow2Flat` is identified as `Pow2` with η_min pinned to zero, and every added
parameter has its **prior bounds** in the table. That last part earns its place: read
together with the finding, the bounds show `expb_pow2` was given an explicitly
negative-capable mineral exponent and `expb_powflex` an explicitly negative-capable
single exponent, so **neither was prevented by its prior** from producing the
flat-or-rising backscatter turbid water is supposed to need. The priors were not the
constraint.

**Stale scoping text fixed — and there was more of it than the prompt listed.** The three
named ones (`index.rst` "Through Stage 2", `api/index.rst` "Stage-0 modules only",
`models.rst` "runs two side by side") plus:

- `models.rst` had a **second** "the two" — the heading "Fitting and how the two are
  judged", now "…how the algorithms are judged".
- `api/index.rst`'s claim was doubly false: all 20 `automodule` blocks already carry
  `:members:`, so nothing "shows only its module-level docstring". Replaced with the two
  conventions a reader actually needs (named constants over literals; the strict layer
  separation), and **two genuinely missing modules added** — `ioptics.style` and
  `ioptics.report.profiles`, both Stage-7 additions never wired in.
- `datasets.rst` labelled all three datasets **"active (Stage 6)"** while the coverage
  matrix says L23 and PANGAEA have never been evaluated at all. The column is now
  **"Loader"** and says what it actually means — the adapter works — with the coverage
  matrix named as the authority on evaluation, "because it is built by walking the runs
  tree rather than from prose that can go stale". Same fix for "Scope of the first
  sweep. All 3320 L23 spectra", which claimed a sweep that is not on disk.

**The orphaned hero is on the landing page** (`_static/ioptics_graphic.png`, 379 KB,
untouched since July), with alt text. The surrounding note was rewritten from a
Stage-2 status list to what is true now — the pipeline runs end to end, but *what is
measured is a narrower thing than what runs*, and the coverage matrix says which.

**Verified.** **437 passed** with data plus one new landing test (438 total in that
file's run), clean `sphinx -W` **exit 0** on a fresh tree at every step, all 11
investigation figures resolving in `_images/`, and the hero asset copied.

### 2026-08-06 (Stage 7, Task 9: provenance hardening)

**Your three Task-8 answers applied first.** `min_waves` is now **5**
(`diagnostics.MIN_SPECTRUM_WAVES`) — the shared test fixture only has four bands, so
rather than weaken the tests to a threshold nobody ships I gave them a realistic
hyperspectral grid. `unknown` is **dropped** from the per-stratum tables with its size
stated in prose ("a further **27 spectra (3 scored pairs) have no chlorophyll at all**
… left out rather than shown as a fourth water type"), and its stale CSVs were pruned
from the docs tree automatically. Coverage-vs-λ waits for a sweep with real spectral
truth, per your answer.

**All five sub-tasks done.** What each one actually was:

1. **`maxfev` and the `mcmc` block are now recorded**, plus a **digest**. This matters
   more than it sounds: `maxfev` decides *whether* a fit converges at all, and
   `gloria_turbid_v3` really ran `expb_pow` at `maxfev=40000` (patched into the
   registry by its build script) while its provenance block recorded **no `maxfev`
   whatsoever** — so the block was byte-identical to the default and nothing on disk
   showed the difference.
2. **The stale `noise_model` is gone from the spec entirely**, not merely unemitted.
   It was a per-algorithm field for a *sweep-level* property, defaulting to `'pace'`,
   which produced a **three-way disagreement** on the one real sweep: the algorithm
   blocks said `pace`, the config said `insitu`, and the uncertainty actually attached
   was `insitu+imputed:0.1`. `config.load` already refused it per algorithm, so the
   field was contradicting a rule the package elsewhere enforced.
3. **The per-record noise tag is persisted** — `noise_model`, `noise_seed` and a
   derived `noise_imputed` on `results_scalar`. The "~68% of fits weighted by an
   invented uncertainty" fact existed only as a once-per-batch warning on **stderr**,
   recoverable from no artifact; `noise.py`'s own docstring already claimed it was on
   "every persisted results row", which was false. It is one `groupby` now.
4. **`AlgorithmConfig.overrides` is applied or rejected, never ignored.** It was parsed
   and read by *nobody*: a config asking for `maxfev: 40000` or a different prior ran
   at the registry default **while writing the ignored request verbatim into the
   provenance copy** — provenance advertising settings that never ran. Now
   `AlgorithmSpec.with_overrides` applies a whitelist (`OVERRIDABLE_FIELDS`), merges
   partial `rt`/`mcmc` mappings, deep-copies so the registry's shared object is not
   mutated, and raises on anything else; `config.load` validates the keys so a typo
   fails **before** a multi-hour sweep rather than after.
5. **`provenance_id` reaches `metrics_spectral`/`metrics_scalar`/`metrics_pairwise` and
   the leaderboard.** It is a pure function of `sweep_id` + `algorithm`, both already
   in `_KEY_COLS`, so it cannot split a row that currently merges. Pairwise rows naming
   two algorithms get `provenance_id_a`/`_b` rather than one ambiguous id — a contest
   is not attributable to a single block.

**The highest-risk item, handled deliberately.** Adding fields to the algorithm block
would have changed **every digest** for byte-identical configurations the moment an old
sweep was re-run, and the profile pages' "what varied between sweeps" section keys on
`algo_digest` — so it would have reported *schema versioning as configuration drift*.
Three things prevent that:

- `algorithm_digest` **normalizes** a pre-Task-9 block against the schema-2 defaults, so
  an old sweep and its re-run agree when the configuration really is the same. Verified:
  the real GLORIA block hashes to `75f63215deaf`, identical to a fresh default spec.
- A `schema` version rides on the record and each block (`PROVENANCE_SCHEMA = 2`), and
  the board carries it as `prov_schema`. The honest limitation is stated rather than
  hidden: a schema-0/1 block **cannot** distinguish "ran at the default budget" from
  "ran at a raised budget nobody wrote down" — which is exactly GLORIA's situation.
- `profiles._what_varied` shows `prov_schema` and adds a `.. note::` when the pooled
  sweeps span schemas, saying a digest difference there may reflect what was written
  down rather than what was configured. The schema is deliberately **not** part of the
  "did the configuration vary" decision.

**Also reconciled: two incompatible definitions of "digest" were about to coexist on
disk.** The Task-5 fold hashed the whole block *including* `name`/`label` at 8
characters; provenance now records 12 over the block *without* them. The board's
`algo_digest` could therefore never equal the digest the sweep itself wrote down.
`leaderboard._algorithm_digests` now prefers the recorded digest and falls back to the
same function, so both paths use one definition.

**Tests + verification.** `ioptics/tests/test_provenance_hardening.py` — 20 tests,
including that the digest moves with `maxfev`/`mcmc`/priors but not with a rename, that
it survives the schema change, that overrides do not mutate the registry's shared spec,
that a typo fails at config load, that the imputed fraction is countable from the table,
and that mixed schemas are flagged as such rather than as drift. **437 passed** with
data (was 417), **399 passed / 38 skipped** CI-equivalent, clean `sphinx -W` **exit 0**.

**⚠ The new fields are empty on the only real sweep until stage 1 is re-run.** Stating
it plainly because it is the thing most likely to mislead: `metrics.compute` and
`leaderboard.update` re-read existing artifacts, so `provenance_id` landed on
`gloria_turbid_v3`'s metrics tables and board rows immediately (confirmed). But its
`provenance.yaml` keeps the stale `noise_model: pace` blocks with no `maxfev`/`mcmc`/
`digest`, and its `results_scalar` will **never** gain `noise_model`/`noise_seed`/
`noise_imputed` — so the 68%-imputed fact stays off disk, and `prov_schema` reads **0**
for all four algorithms — until the sweep is re-fitted. Task 11 re-runs sweeps; that is
where these fill in.

**One behaviour change worth flagging for existing configs:** a YAML that previously
carried a decorative override (the `mcmc: {nsteps: ...}` example in `config.py`'s own
module docstring) used to be silently ignored and will now **actually apply**, and an
unknown key now refuses to load at all. That is the point of the task, but it means an
old config can now run differently — or stop loading.

#### Verification of this task (the review agent stalled; I ran its checklist myself)

The Fable recon for this task was excellent and shaped the whole design. The
*adversarial* pass then died mid-run without producing findings, so rather than wait on
another I ran the specific high-risk checks by hand, with demonstrations:

- **The whitelist accepts no inert field.** This was the risk of re-introducing exactly
  the bug being fixed. Every member of `OVERRIDABLE_FIELDS` is plumbed (10 via the
  spec's BING interop, `maxfev` via the runner), and `maxfev` was traced end to end:
  with `with_overrides({'maxfev': 4321})`, BING's `chisq_fit.fit` receives
  `maxfev=4321`.
- **`registry.get()` returns a shared object with a shared `apriors` list**, so the
  deepcopy in `with_overrides` is load-bearing, not defensive: verified that overriding
  or later mutating the returned spec's `apriors` or `rt` does **not** leak back into
  the registry.
- **`_SCHEMA2_DEFAULTS` matches the real `MCMCOptions` defaults**, so normalization
  cannot claim a false equivalence for a default-configured algorithm.
- **`noise.is_imputed(None)` is `False`**, so an untagged record reads as not imputed
  rather than raising or reading as imputed.
- **The fold is idempotent** (60 rows twice), and an **old-format board** (written
  before these columns) folds beside a new sweep with NaN-filled `provenance_id` /
  `prov_schema` — `ranked()` and `render()` both cope.
- **The published page renders them cleanly**: `prov_schema` as `0` (not NaN or blank)
  and `provenance_id` as `gloria_turbid_v3#<algorithm>`.

**Two things the checks surfaced, stated rather than swept:**

1. **The turbid trio's digests *will* change when GLORIA is re-fitted** —
   `334d8cd116a0` → `eb711c169fc6` for `expb_pow2` — because `register_turbid` sets
   `maxfev=40000` and the schema-0 block records none. Normalization cannot recover
   information that was never written; this is the case `prov_schema` and the
   mixed-schema note exist for, and it confirms they are load-bearing rather than
   decorative. It also means the digest normalization protects the *default*-configured
   algorithms (`expb_pow`, `giop`, `gsm`) and not the turbid ones.
2. **NIT, not fixed:** `noise_seed` comes back as `int64` when populated but `object`
   when every value is `None` (GLORIA's case, since in-situ data takes `add_noise=False`),
   and a cross-sweep `concat` coerces to `object`. Nothing performs arithmetic on it and
   the leaderboard folds `metrics_scalar` rather than `results_scalar`, so it never
   enters the fold — but a nullable `Int64` would be tidier if it ever does.

### 2026-08-06 (Stage 7, Task 8: the three discarded slices)

**The blunt summary first: of the three slices, only one has content on the data we
have.** I had a Fable subagent audit that before building anything, because three
figures that all render "no data" would have been the wrong deliverable.

| slice | on `gloria_turbid_v3` | why |
|---|---|---|
| accuracy vs wavelength | **empty** | 16 of 28 080 `metrics_spectral` rows are non-empty: GLORIA's only spectral truth is `a_cdom440`, mapped onto `a_dg` at **one** wavelength |
| per trophic stratum | **real, and it is the finding** | Chl truth on 73 of 100 obs → eutrophic 66 / unknown 27 / mesotrophic 7 |
| χ² vs MCMC | **empty** | one sweep exists on this laptop and it is χ²-only; `chains/` is empty |

All three are built and wired anyway — the code is right and the *data* is the wall, so
they fill in the moment a sweep provides the input. What matters is that the two empty
ones are **suppressed with a specific reason** rather than published blank.

**What per-stratum actually says.** The pooled retrieval success of 21% is a blend of
**mesotrophic 86% (n=7) and eutrophic 14% (n=66)**; median χ²ᵥ runs 0.18 → 2.28 across
the bins, `mae` 1.41 → 0.96, and the coverage verdict flips to **over-confident for all
four algorithms in mesotrophic only**. Pooling hid a regime change, which is exactly the
argument for the slice.

**New code.** `diagnostics.accuracy_spectrum_data` / `scored_components`;
`plotting.accuracy_spectrum` / `accuracy_spectrum_grid` (small multiples, one panel per
component, all algorithms overlaid, a dashed rule at the metric's perfect value);
`metrics.with_strata` / `perfect_value` / `PERFECT_VALUE` / `NOMINAL_COVERAGE`;
`figures.scored_components` / `strata` / `fit_methods` planners and an
`accuracy_spectrum` builder; `figures.dbic_cdf(by=)`; `tables.fit_method_compare`; four
new sections in `standard.build()`.

**`min_waves=2` is the load-bearing decision.** A component scored at a single
wavelength is not a spectrum, and four markers at 440 nm under an "accuracy vs
wavelength" heading would invite a reader to see a trend that does not exist. So the
planner refuses it and the page says why, naming the component and the single band.

**Four defects, all found by attacking the new work rather than by reading it:**

1. **`dbic_cdf(by='stratum')` raised `KeyError: 'stratum'`.** The parameter had existed
   since Stage 2 while the column never has: `compute` derives `stratum` in memory and
   writes it only onto `metrics_*`, so the frame the caller holds
   (`results_scalar`) cannot be grouped by it. Fixed with a public
   `metrics.with_strata`, binning by the same truth-Chl-then-retrieved-Chl rule, so a
   stratified contest bins identically to every published per-stratum number.
2. **The ΔBIC figure and the ΔBIC table disagreed by 5x on the same page.** `compute`
   scores the pairwise contest over status-filtered rows (**n = 21**) while
   `figures.dbic_cdf` passed raw `results_scalar` (**n = 100**). A `fit_failed` row's
   BIC is not a model-selection statement, so `metrics.dbic_cdf` now filters on
   `SCORE_STATUSES` itself (`statuses=None` opts out). Figure and table now both say 21.
3. **`qc`'s `frac_not_ok` was not stratum-scoped** while its closure block was — so the
   first per-stratum QC table I emitted published `frac_not_ok` 0.79 beside `frac_ok`
   0.857, summing to **1.65**. Now the complement of the stratum-scoped `frac_ok`, so
   the two are one population by construction; every stratum sums to 1.0.
4. **`coverage68`'s "perfect" reference line was drawn at 0** — its *worst* possible
   value — because I keyed the perfect value off `median_ratio` alone. Now from a single
   `metrics.PERFECT_VALUE` map, with `tables.NOMINAL_COVERAGE` aliased to it so the
   tables' verdicts and the figures' reference lines cannot drift. An unrecognised
   metric now draws **no** line rather than asserting one at zero.

**Also fixed, from the recon:** `build_algorithm_profile`'s accuracy table listed rows
from up to four strata with **no `stratum` column**, so four rows of the same
(dataset, component, ref_wave) read as duplicates disagreeing with each other. The
column is published now, with a note that a pooled row and its bins are not independent
results.

**Tests + verification.** `ioptics/tests/test_slices.py` — 19 tests, including that a
band nobody scored is not drawn at the perfect value, that a single-band component is
not offered as a spectrum, that `frac_ok`/`frac_not_ok` are complements in every
stratum, that the stratified ΔBIC bins the same way the tables do, and that both empty
slices are suppressed *with* an explanation. One pre-existing assertion in
`test_report_selection.py` was rescoped: it checked `'no data' not in txt` and now
matched the honest "Not shown" boilerplate, so it is scoped to the page body above that
note. **414 passed** with data (was 395), **376 passed / 38 skipped** CI-equivalent,
clean `sphinx -W` **exit 0** on a fresh tree.

**Known gap I did not close:** `standard.build()` hard-codes the χ² CSV filenames
(`accuracy_chisq_<stratum>.csv`), so a page can only ever include the χ² tables even
once MCMC rows exist. The comparison table covers the cross-method view, but the
per-method tables would need the filename parameterised — it belongs with Task 9's
provenance work, which touches the same call sites.

### 2026-08-06 (Stage 7, Task 7: exemplar-fits page + wiring the unused builders)

**No Q&A answers were outstanding for this task** — the two items posed after Task 6
(profiles in the top-level toctree; dataset characterisation figures) are still open
and neither blocks this work.

**The `ratio_hist` wrapper this task asked for was already delivered in Task 2**, so
the work here was the exemplar page plus `closure_set` and `corner_set`.

**What the page is.** `reports/<sweep_id>/exemplar_fits.rst` — one 5x2 grid of the
sweep's best, worst and eight median fits: observed Rrs as black dots with every
algorithm's modelled Rrs laid over it, each legend entry carrying that fit's own χ²ᵥ
and relative misfit, plus a keyed table, the Rrs closure residuals for the two
extremes, and the posterior corner plots wherever a chain exists. Every other figure
in a report describes a *population*; nothing showed a reader a single fit.

**On the real GLORIA sweep this figure is the investigation's headline finding, drawn
rather than asserted.** Ordered clear→turbid, the grid reads:

| obs | role | χ²ᵥ | rel. misfit | Rrs peak |
|---|---|---|---|---|
| `GID_5460` | best | 0.89 | 8% | 400 nm |
| `GID_3654` … `GID_4597` | median (8) | 27 – 31 | 32 – 90% | 540 – 576 nm |
| `GID_7390` | worst | 223 | 94% | 580 nm |

The one blue-peaked spectrum is tracked well; **every turbid panel shows all four
models collapsing onto the same blue-peaked curve** while the observation peaks in the
green — they cannot put the Rrs maximum redward of ~500 nm at all. Four models from
k=5 to k=7 give the same wrong answer.

**Two decisions worth recording, because I departed from the prompt's reference.**

1. **Exemplars are ranked by `|log10(χ²ᵥ)|`, not by χ²ᵥ ascending.** Ascending χ²ᵥ
   crowns the sweep's *most over-fit* spectrum its "best" fit, and this package
   already names χ²ᵥ < 1 over-fitting (`frac_overfit`). On GLORIA χ²ᵥ moved by 5x
   when the assumed error floor changed while the fits did not move at all, so a χ²ᵥ
   of 0.01 is evidence about the noise model, not the retrieval. Both tails are worse
   than the middle; every panel prints its own χ²ᵥ so the reader sees which tail.
   Where several algorithms fit one observation it is ranked by their median χ²ᵥ,
   since the panel shows all of them.
2. **The referenced `wide_example_fits.png` does not do what its own title claims.**
   `reports/scripts/gloria_fits_report.py:575-593` selects by χ²ᵥ rank and then calls
   `sorted({order[0], order[n//3], ...})`, which sorts **positional indices into the
   record list**, not the χ²ᵥ ranks — so its panels are in obs-id order and the
   suptitle's "clear (top-left) to turbid (bottom-right)" is only incidentally true.
   I implemented the *intent*: an explicit sort by observed-Rrs-peak wavelength
   ascending. (Its sibling `_fig_inflated_noise_examples` gets this right, over a
   list already sorted by peak.) The package had the threshold
   (`records.RED_PEAK_NM = 560`) but no clear→turbid sort key; there is one now.

**A latent bug this task made live — pages sharing a report dir deleted each other's
figures.** `standard._prune_stale` knew only the assets of the build that called it,
so building a second page into `reports/<sweep_id>/` pruned the first's. Demonstrated
before fixing: after `cross_algorithm` then `per_algorithm`, all six of the
cross-algorithm scatters, Taylor/Target and ΔBIC panels were gone while
`cross_algorithm.rst` still referenced them — a dangling image, i.e. a `sphinx -W`
failure. Only one kind was ever built per sweep, which is why it had not bitten.
Fixed: an asset survives if **any** surviving sibling page still names it
(`_referenced_elsewhere`), with a test that genuine orphans are still pruned.

**Other fixes made in passing:**

- **`corner_set` would have taken a whole page build down.** `chain_file` is only a
  *path*, so it goes stale the moment a sweep dir is copied between machines or the
  chains are pruned; `io.load_chain` raises. Now skipped per-chain, and `limit=` caps
  how many figures a chain-heavy sweep writes into the docs tree.
- **Per-algorithm linestyles** (`style.SERIES_LINESTYLES`, `algo_linestyle`). Markers
  separate scattered points but not curves, and curves are exactly where series
  coincide: with one linestyle, three of GLORIA's four variants were invisible under
  the fourth and a reader could not tell *identical* from *missing*. Six linestyles,
  one per curated slot — with five, `expb_pow` (slot 0) and `expb_powflex` (slot 5)
  wrapped onto the same solid line, and those two coincide on precisely the turbid
  data where it matters. `algo_style()` now returns `linestyle` too; every call site
  picks keys explicitly, so nothing splatting the dict broke.
- **`rrs_fit_data` filters the χ²ᵥ/status lookup on `dataset` and `fit_method`**, not
  on algorithm alone as `residual_spectra` does — an unfiltered multi-dataset
  `scalar` could otherwise annotate a panel with another dataset's row.
- **`exemplar_grid` resets `EMPTY_FLAG` explicitly.** `_annotate_empty` stamps it on
  the *shared* figure, so without this one missing observation would have suppressed
  the entire 10-panel grid.

**The page states what the numbers mean rather than leaving it implied.** It printed
"above χ²ᵥ = 5 a fit is not a solution" and then a table of ten fits at χ²ᵥ ≈ 30 and
never connected the two, so a data-derived summary now says it outright: *9 of the 10
have a median χ²ᵥ above 5 … 7 peak redward of 560 nm and are therefore outside the
regime these parameterizations claim at all; their misfit is a statement about scope,
not about the fitter*, with the recorded status breakdown (`out_of_scope` 28,
`poor_fit` 8, `ok` 4).

**Tests + verification.** `ioptics/tests/test_exemplars.py` — 32 tests, plus one in
`test_style.py`. The shared `_make_pair` fixture gained `chi2_nu=` and `rrs_peak=`
(via `_rrs_peaking_at`), because a fixture where every fit has χ²ᵥ = 1 and every Rrs
peaks at 440 nm cannot test either the selection or the ordering; the default path is
unchanged. **392 passed** with data (was 359), **354 passed / 38 skipped**
CI-equivalent (was 321/38), clean `sphinx -W` **exit 0** on a fresh tree (checked
without a pipe), site at 14 pages.

**Not done, deliberately:** the profile pages do not link the per-sweep exemplar
pages. Task 6's spec lists "exemplar fits" among a profile's elements, but a
cross-sweep page linking a per-sweep one needs the target to exist or `-W` fails;
that belongs with the Task 8 slices that touch the profiles again.

#### Adversarial review of this task (Fable subagent) — 9 findings, 7 fixed

Task 6 shipped without this pass; Task 7 got it. The review cleared the two design
decisions above (it independently confirmed the `wide_example_fits` ordering bug, the
index arithmetic at totals 0/1/2/3/9/10/11/10000, that the median eight really are
median — ranks 46–53 of 101 on a synthetic, and bracketing the true median on the real
sweep — and that every factual claim on the published GLORIA page checks out against
the runs tree). It found two that mattered:

1. **MAJOR, fixed — a multi-dataset sweep silently pooled two unrelated
   observations.** `obs_id` alone does not identify an observation: the package's own
   convention reuses ids across datasets (`test_sweep_multi` runs `obs in (0, 1)` on
   all three). `exemplar_obs` grouped on `obs_id`, so on a two-dataset sweep it ranked
   **every** observation at χ²ᵥ = 200.5 — the median of an L23 fit at 1.0 and a GLORIA
   fit at 400.0 — making best/worst meaningless. Worse, `exemplar_fits` called
   `rrs_fit_data` *without* `dataset=`, so the dataset filtering I had written and
   documented was never exercised by the only caller: the panel got a model curve with
   duplicated wavelengths sawtoothing through both datasets, χ²ᵥ from an arbitrary
   `iloc[0]`, and a peak from whichever row survived dedup. My own test covered the
   `dataset=`-supplied path only. Fixed by keying on `diagnostics.OBS_KEYS =
   ('dataset', 'obs_id')` end to end: the selection frame carries `dataset`, the
   builders pass it, closure filenames are namespaced (`closure_GLORIA_GID_5460.png`),
   the status breakdown matches on both keys, and the table grows a `dataset` column
   only when the sweep has more than one.
2. **MAJOR, fixed — `corner_set`'s hardening did not cover a *corrupt* chain.**
   `zipfile.BadZipFile` is **not** an `OSError`, so my `(OSError, ValueError,
   KeyError)` tuple let a half-written NPZ through and it would have taken the page
   build down — precisely what the docstring promised it would not. Demonstrated with
   a truncated real NPZ. Fixed by catching around both the load and the render.
3. **MINOR, fixed — the `limit=` guard was unused by the one wired call site**, and
   was applied to *candidate rows* rather than successful reads, so five stale paths
   at the head of the table would have yielded zero corner plots. Now
   `MAX_CORNERS = 8` by default and the budget counts successes.
4. **MINOR, fixed — hard-coded prose contradicted the page it was on.** A
   4-observation sweep published "shows 4 individual fits" and then "the eight nearest
   the median"; the grid suptitle and figure caption asserted clear→turbid even when
   the selection had fallen back to fit-quality order for want of a persisted
   `Rrs_obs`. All three now derive from the selection.
5. **MINOR, fixed — the prune keep-match was too loose.** `path.name in text` kept an
   orphaned `fits.png` alive because a sibling page referenced `exemplar_fits.png`.
   Now matched against the `figure`/`image`/`csv-table` directive target. The failure
   was conservative (it could never delete a live asset), but it defeated the point.
6. **MINOR, already fixed — the `_num` guard.** The review is right about the version
   it read; I had replaced it before the review landed. Verified after the fact:
   `-inf`, `None`, `pd.NA` and `'abc'` all render as em dashes rather than raising or
   publishing the literal string `-inf` under a χ²ᵥ heading.
7. **NIT, fixed — `exemplar_obs(n=1)` returned two rows** (an empty middle range still
   left a best *and* a worst). Slot selection is now `_exemplar_slots`, with `n=0`
   returning nothing and `build_exemplars(n=0)` no longer silently meaning "default".
8. **NIT, fixed — `EXEMPLAR_ROLES` was dead.** It is now the documented role
   vocabulary, and `OBS_KEYS` beside it carries the identity rule.
9. **NIT, not fixed — `_safe` can collide** (`st/1` and `st_1` both give
   `closure_st_1.png`). Two ids differing only in a separator character do not occur
   in any dataset we load, and the alternative is unreadable hashed filenames.

**One thing the review surfaced indirectly:** adding a test file shifted the suite's
consumption of numpy's **global** legacy RNG, which flipped
`test_micro.py::test_fit_mcmc_accepts_string_obs_id` to `fit_failed` in a full run
while passing in isolation. BING seeds its walker init from that global stream, and the
test's own docstring already admitted the order dependence. Pinned with an explicit
`np.random.seed` rather than left as a flake — three consecutive full runs green.

**Re-verified after all fixes:** **392 passed** with data, **354 passed / 38 skipped**
CI-equivalent, clean `sphinx -W` **exit 0** with zero warnings on a fresh tree, and the
GLORIA page regenerated (the renamed closure figures pruned their old names correctly).
`test_exemplars.py` is now 32 tests.

#### Follow-up: your three Task-7 answers applied (2026-08-06)

Two needed no code (exemplars keep ignoring `status`; the fixed count of 10 stays). The
third did: **"worst" now means the largest χ²ᵥ**, while the *selection* still ranks by
distance from χ²ᵥ = 1. The two differ whenever the over-fit tail reaches further from 1
than the under-fit one — χ²ᵥ = 0.001 is three decades below 1, χ²ᵥ = 100 only two above
— and before this change that sweep's "worst" panel was the *over-fit* one.
`diagnostics._worst_slot` picks the largest-χ²ᵥ row and `_exemplar_slots` backfills the
median window when that row falls inside it, so the panel count and role uniqueness are
unchanged. The page prose now states both halves of the rule explicitly. Three new
tests, including the case where the largest χ²ᵥ sits mid-ranking. **The GLORIA page is
unchanged** — its worst was already the largest χ²ᵥ (222.6), which is why the ambiguity
was invisible there. 395 passed.

### 2026-08-05 (Stage 7, Task 6: profile pages + coverage matrix + glossary)

**Your answers applied:** the L23 smoke page stays as-is (it will be regenerated in
Task 11), and `frac_ok` stays out of the rank ordering — neither needed code. The
earlier decisions this task rests on: profiles at `reports/algorithms/<name>` and
`reports/datasets/<name>` with the reference pages retitled to keep them distinct,
**hybrid** (generated tables plus a hand-written findings block), **no
recommendations**, and one **pooled** profile per algorithm with a "what varied"
note.

**The site went from 3 published pages to 13.** New: 6 algorithm profiles, 3 dataset
profiles, the metrics glossary, and the leaderboard drill-down from Task 5, on top of
the two sweep pages and the landing page.

**The coverage matrix is the piece I think matters most.** It is built by **walking
the runs tree**, not by reading the leaderboard, because a missing leaderboard row
cannot distinguish three quite different facts — and it now says which one applies:

| state | meaning |
|---|---|
| `scored (n=…)` | evaluated, with truth to score against |
| `no scoreable truth (k/N fits ok)` | evaluated, but the dataset carries no truth for it |
| `all fits failed (N attempted)` | evaluated and the fitter got nothing |
| `not evaluated` | nobody has tried this pair |

On the real tree it reads: GLORIA scored for the four turbid variants, and **every
other cell "not evaluated"** — `giop` and `gsm` have never been run at all, and
neither L23 nor PANGAEA has a folded sweep. That is the map the site has never had,
and it is on the landing page.

**Profile pages.** Each algorithm page opens with a paragraph *containing numbers*
(its best and worst contest, and the range of `frac_ok`), then its parameterization
**read from the registry** so it cannot drift from what ran, where it has been
evaluated, its accuracy by contest, a calibration section, its head-to-head verdicts,
and — per your pooling decision — a **"What varied between sweeps"** block that
appears only when the pooled runs were *not* identically configured (compared by
`algo_digest`, not by sweep count). Each dataset page opens the same way, then says
what the data can actually score, ranked contests with ties grouped, retrieval-success
accounting, per-stratum and χ²-vs-MCMC breakdowns where they exist. A registered
algorithm nobody has run still gets a page saying so — more use than a missing page.

**The hybrid seam** is a `<name>_findings.rst` beside each profile: included if
present, never written or overwritten by the builder. There is a test asserting the
file survives a rebuild.

**The glossary** (`reports/glossary.rst`) states, for every column, the value a
*perfect* retrieval would produce — the point being that it is not always 0, which is
what the old page-wide claim got wrong. I had a Fable subagent draft it from the
source, then verified its two most specific claims myself (`RED_PEAK_NM = 560` for
`out_of_scope`, and the χ²ᵥ band `1 ± 2√(2/dof)`). It carries the worked
GLORIA denominators (12 pairs / 21 scored / 100 attempted), the coverage detection
windows at n=12 versus n=3320, the equivalence-test verdict vocabulary, the
`ranking` vocabulary, and the measured consequence of the absolute 10% floor. Every
table blurb now links to it.

**A pre-existing bug the new tests found.** `metrics.compute` **crashes** on a sweep
in which every fit failed: `pd.concat([])` on the two empty scalar parts raises
`ValueError: No objects to concatenate`. That is a real state — the GLORIA runs before
the iteration budget was raised failed 72 of 100 — so this was reachable well before
Task 6. Fixed, with the empty case producing an empty frame instead.

**Three of my own bugs, all caught by running:** `io.RESULTS_SCALAR_FILE` does not
exist (it is `io.SCALAR_FILE`); `_what_varied` compared *(sweep, config)* pairs rather
than configurations, so two sweeps with identical configs falsely triggered the "not
identically configured" warning; and my glossary heading had an underline one
character short — which `sphinx -W` failed on, though only on a **clean** build: my
first check passed because the cached environment skipped the file. Clean builds from
here.

**Verification:** CI-equivalent **321 passed / 38 skipped** (was 311); with data
**359 passed**; `sphinx -W` exit 0 on a **fresh** build tree.

**Files:** new `ioptics/report/profiles.py`, `ioptics/tests/test_profiles.py` (10
tests), `docs/source/reports/glossary.rst`, `docs/source/reports/{algorithms,datasets}/*.rst`;
modified `ioptics/metrics.py` (empty-concat guard), `ioptics/report/{standard,rst}.py`,
`ioptics/tests/test_report_standard.py`, `docs/source/{models,datasets}.rst`
(retitled + cross-linked), `docs/source/reports/index.rst`.

### 2026-08-05 (Stage 7, Task 5: leaderboard fold + landing page + vendored BokehJS)

**Your answers implemented:** the practical floor stays **absolute** (no code change —
the constant already documents the L23 consequence), and the head-to-head verdict now
**feeds the leaderboard ranking**: the fold carries a `separable` flag derived from the
pairwise verdicts, and `ranked` refuses to rank a contest that no pair separates,
marking it `ranking='indistinguishable'` instead of printing 1..N.

**The fold.** `fit_method` is now a **key rather than a filter** — it used to
hard-select `chisq`, so an MCMC-fit algorithm was invisible on the board no matter how
well it did, and silently, because the column was not carried either. Added: the
closure block (`frac_ok`, `n_attempted`, `frac_poor_fit`, `frac_out_of_scope`,
`frac_fit_failed`, `chi2_nu_median`, `rel_misfit_median*`) so the board can answer
*why* rows were not scored; the **`bing` and `ocpy` commits** alongside the `ioptics`
one, since BING is where the models and the fitter live and a row stamped only with an
ioptics commit does not identify what produced it; and a per-algorithm **`algo_digest`**
over the persisted algorithm block, so two rows sharing a name can be checked for
being the same algorithm (it cannot yet catch the `maxfev` difference — provenance
omits it until Task 9). `frac_ok` is promoted out of the trailing columns into the
headline set, next to the accuracy numbers: a top rank over a tenth of the spectra is
not a better algorithm than a lower rank over all of them.

**The landing page went from 2 477 lines to 175.** It now carries the
`stratum='all'` **headline table** (narrow columns, unmeasured rows dropped), one
**summary card per folded sweep** — date, datasets, algorithms, spectra scored, and
whether anything separated — the **interactive leaderboard widget** (implemented in
Stage 5 and never once put on a page), and a link to a new **`leaderboard_full`**
drill-down (472 lines) holding every stratum, fit method, closure column and
provenance stamp. On the real board the card reads *"no pair separated — see the
head-to-head table"*, which is the honest one-line summary of that sweep.

**BokehJS is vendored — the CDN is gone.** I had a Fable subagent research the recipe
before writing any code, which paid for itself three times over:

- `CDN.render()` was loading **five** bundles unconditionally; the figure needs
  **two** (`bokeh` + `bokeh-widgets`; the leaderboard's `DataTable` adds
  `bokeh-tables`). Dropping `bokeh-gl`/`bokeh-mathjax` is free.
- No `bokeh.resources` mode emits a clean `_static/` path — `'relative'` points into
  the conda environment and `'server'` hard-codes a `static/js/` infix — so the tags
  are hand-built, sourced from `Resources(mode='absolute')` of the **installed** bokeh
  (the same one that serialized the figure's `docs_json`, so they cannot drift).
- Filenames are **versioned** (`bokeh-3.9.1.min.js`). Report fragments are committed
  and never regenerated, so an unversioned `bokeh.min.js` would silently re-point every
  historical page at a newer BokehJS the day the environment is upgraded.
- Vendoring costs ~1.6 MB in the repo **once**; inlining would have cost ~1.6 MB in
  *every* committed page, per sweep, forever.

Verified in the built HTML at both depths: `../../_static/bokeh/…` from a report page,
`../_static/bokeh/…` from the landing page, with the files actually copied into
`_build/html/_static/bokeh/`. A comment records that switching Sphinx to the `dirhtml`
builder would break the baked depth.

**Also in this task:** the interactive figure's title now states the sampling fraction
(`"1,234 of 5,678 points shown — 22%, stratified sample"`), because a downsampled cloud
with no note reads as the whole population; and the hover carries **`obs_id`**, so a
reader who spots an outlier can go and look at that spectrum. The three build scripts
now call `standard.build_landing()` instead of assembling the landing page themselves.

**Two self-inflicted breakages caught by running, not reading:** I added `obs_id` to
the scatter's field list without adding it to the points frame (`KeyError` on every
build), and changed `_scatter_points`' caller before its signature. Both would have
been invisible to a read-through.

**And one that `-W` nearly hid:** the new `leaderboard_full` page is not one directory
deep, so the `:glob: */*` toctree could not reach it and Sphinx warned
"document isn't included in any toctree" — which `-W` turns into a failure. My first
check reported `rc=0` because I had piped sphinx through `tail`, so the exit code was
`tail`'s; re-running without the pipe showed exit 1. `ensure_glob_toctree` now takes
`extra_docs` and lists the page explicitly.

**Verification:** CI-equivalent **304 passed / 38 skipped** (was 292); with data
**342 passed**; `sphinx -W` exit 0 (checked directly, not through a pipe).

**Files:** modified `ioptics/report/{leaderboard,rst,bokeh,standard}.py`,
`ioptics/runs/prototypes/*/build_v*.py`, `ioptics/tests/{test_sweep,test_sweep_multi,test_report_bokeh}.py`,
`docs/source/reports/{index.rst,gloria_turbid_v3/*}`; new
`ioptics/tests/test_leaderboard_landing.py` (10 tests),
`docs/source/reports/leaderboard_full.rst`, `docs/source/_static/bokeh/*.min.js`
(1.6 MB, committed once).

#### Adversarial review of this task (Fable subagent) — 10 findings, 9 fixed

It found the defect I had asked it to hunt for, and it was disqualifying.

1. **`_CONTEST` omitted `fit_method` while the fold had gained it** — so the moment a
   sweep exercised the new MCMC-on-the-board capability, the ranking layer corrupted
   the board that used it. Reproduced: the *same* algorithm published at **rank 1 and
   rank 2** in one contest, comparing `win_frac` values drawn from different pools
   (metrics computes wins per fit method); the one-horse-race guard bypassed; and
   non-contiguous ranks where a contest's only visible row was "rank 3". My own new
   test checked the *fold* and never called `ranked()` on a mixed board, so the gap
   was untested. **Fixed**: `fit_method` is part of the contest key, and it is now in
   the headline columns and the widget so a reader can see which population a row
   belongs to. New test asserts no algorithm holds two ranks in one contest and that
   every contest is single-method.
2. **An empty board crashed `build_landing`** (`sort_values` on absent rank columns) —
   reachable by running stage 3 before stage 2, or on a machine with an empty runs
   tree. **Fixed**: `ranked` returns an unranked frame when the board is empty or the
   sort keys are missing; tested.
3. **Missing pairwise data ranked silently.** An older sweep with no
   `metrics_pairwise` (or a fit method whose pairs were never computed) got a full
   1..N ranking with no head-to-head support — "a quiet erosion" of your rule.
   **Fixed**: those rows are labelled **`ranked (no head-to-head)`**, so a supported
   rank and an unsupported one are distinguishable in the output.
4. **A sole competitor was labelled `indistinguishable`** — indistinguishable from
   nobody. **Fixed**: `sole competitor`.
5. **`sweep_cards` emitted `:doc:` links with no check that the page exists.**
   `update()` folds every sweep dir with metrics; pages are built per sweep on demand,
   so a folded-but-unbuilt sweep left a dangling reference. **Fixed**: the card links
   only a page that exists and otherwise says so.
6. **`vendor_bokehjs` never repaired a truncated bundle** (copy-if-missing), so an
   interrupted copy would break every figure forever. **Fixed**: size-compared and
   re-copied; tested by truncating one.
7. `_separable(d)` was evaluated twice per sweep (the pairwise parquet read twice) —
   waste, not incorrectness. **Fixed.**
8. `rel_misfit_median` was folded but not rendered in the full grid. **Fixed.**
9. **The L23 smoke page still loads `cdn.bokeh.org`** — five bundles at bokeh
   **3.9.0**, so the site now mixes two BokehJS versions, and that page has no card
   because its sweep is not in this runs tree. **Not fixed**: its artifacts are not on
   this laptop, so it cannot be regenerated until Task 11. This is the Q&A question
   above; the review confirms nothing breaks at build time.
10. **Commit hazard, not code:** `docs/source/_static/bokeh/` is *untracked* while the
    tracked `.rst` diffs already reference it — committing the RST without the JS
    directory would give 404'd script tags and silently blank figures on RTD. Flagged
    in the push set.

Verified sound by the review (it tried and failed to break these): the wins and
coverage merges on a 2-dataset × 2-fit-method fixture (120 rows, zero duplicate keys,
each `frac_ok` on the right fit method), fold idempotency with `fit_method` in the
keys, rank contiguity, `sweep_cards` edge cases (all-NA `n`, missing provenance), the
vendoring depth against the **real built HTML** at both levels with a zero-warning
full build, script-tag/`docs_json` version agreement, and no consumer broken by the
new `render()` signature or the build-script migration.

**After the fixes:** CI-equivalent **311 passed / 38 skipped**; with data **349
passed**; `sphinx -W` exit 0. On the real board the ranking states are now 144 *not
scored* + 16 *indistinguishable* and **zero ranks published** — which is the honest
reading of a sweep where no pair separated.

### 2026-08-04 (Stage 7, Task 4: pairwise statistics that can detect a tie)

**Your answers implemented:** the practical floor is **10%** (`PRACTICAL_MAE_FLOOR =
0.10`, in the fractional-multiplicative MAE units the tables publish — see Q&A, I
want to confirm I read "10%" the way you meant it), and **`coverage_n` is now a
`metrics_scalar` column**, which closes the Task-3 review finding properly rather
than leaving it documented.

**The pairing is kept.** `metrics.paired_abs_log_errors(table, a, b)` returns each
algorithm's per-spectrum `|log10(M/O)|` on the spectra *both* retrieved;
`paired_log_errors` is the difference view. `metrics.head_to_head` runs every
unordered pair in every contest and emits `n_paired`, `win_frac_a`, both MAEs,
`delta_mae`, a bootstrap interval, `resolved`, and a `verdict`. Wired into
`metrics.compute` as `contest='pair'` rows, published by `tables.head_to_head` and a
new **Head-to-head** page section.

**Two thresholds, deliberately separate:** the bootstrap answers *can we tell?* and
your 10% floor answers *would anyone care?* A winner is named only when both say yes.

**A design error I caught by running it on the real GLORIA contest.** My first
version bootstrapped the *median paired difference in log error* while judging the
floor on the *difference of MAEs*. On real data those differ by two orders of
magnitude — `d_median` of −0.002 against a `delta_mae` of −0.227 — because MAE is a
mean of heavy-tailed errors and the paired median is not, so the significance test
and the effect size were measuring different quantities. Rewritten: the bootstrap
resamples **spectra, paired**, recomputing both MAEs per replicate
(`_bootstrap_delta_mae`), so the interval and the floor share the MAE scale. The
interval now brackets the point estimate by construction, which is asserted.

**A verdict-precedence change I made, and then had refuted — see the review below.**
Mid-task I switched the precedence so `|delta_mae|` under the floor won over
"unresolved", labelling such contests **indistinguishable**. That was wrong: the
floor was tested against the *point estimate alone*, so a contest whose interval
still admitted a difference four times the floor was published as "would not matter
even if confirmed". The final logic is an **equivalence test** — see the review
section.

**What it says about the real sweep (final logic).** On GLORIA `a_dg(440)`, of the six
pairs of turbid variants **one** is genuinely **indistinguishable** — `expb_pow` vs
`expb_pow2flat`, whose whole interval `[−0.031, +0.022]` sits inside the 10% floor —
and the other **five are `underpowered`**: small point differences (0.005-0.058) whose
intervals are far too wide to rule a material difference out. That distinction is the
whole value of the task: "we measured them to be the same" and "12 spectra cannot tell"
are different statements, and the previous `mae_rank` of 1-4 asserted neither.

**And the page no longer contradicts itself.** `tables.accuracy` now blanks the
`*_rank` columns and marks `ranking = 'indistinguishable'` for a contest whose pairwise
verdicts separate nobody — the GLORIA accuracy table had been printing `mae_rank`
1,3,2,4 three sections above a head-to-head table declaring the same four algorithms
inseparable (and its two rank columns disagreed about who was first, which was itself
unremarked evidence of a tie).

**Also in this task:** ΔBIC now runs for **every** algorithm pair present, not only
the configured one (a sweep whose algorithms are not `expb_pow`/`giop` used to get no
ΔBIC row at all); `leaderboard.ranked` **no longer ranks a contest with no finite
metric** (the 144-of-160 defect — rank becomes `NA`); and `tables.head_to_head` drops
pairs that share no scoreable spectrum, stating the count (54 of 60 on GLORIA) the
same way the accuracy table does.

**Verification:** CI-equivalent **283 passed / 38 skipped** (was 271); with data
**321 passed**; `sphinx -W` clean; GLORIA page regenerated with the new section.

**Files:** modified `ioptics/metrics.py`, `ioptics/report/{tables,standard,leaderboard}.py`,
`docs/source/reports/gloria_turbid_v3/*`; new `ioptics/tests/test_head_to_head.py`.

#### Adversarial review of this task (Fable subagent) — refuted, then fixed

Its verdict: *"the paired bootstrap machinery is sound; the verdict built on top of it
is not, and on the real GLORIA deliverable it prints the wrong label on 5 of 6
contests."* That was correct. Eleven findings; all addressed.

1. **The headline defect — my precedence collapsed `underpowered` into
   `indistinguishable`.** The floor was tested against the point estimate with the
   interval never consulted, so `expb_pow` vs `expb_powflex` — interval
   `[−0.380, +0.184]`, i.e. compatible with one model being **38% worse, nearly 4x the
   floor** — was published as "would not matter even if confirmed". **Fixed** by making
   it an explicit **equivalence test**: `indistinguishable` now requires the *whole
   interval* to lie inside ±margin (the data rule a material difference out);
   `underpowered` covers both "spans 0" and "excludes 0 but straddles the margin". The
   real sweep now reads 1 indistinguishable + 5 underpowered, matching the reviewer's
   own table.
2. **The requirement was satisfied only vacuously.** `underpowered` was produced **zero**
   times on the real sweep, and my page test passed because both words appear in the
   *static prose*, not because either verdict was produced. Now covered by tests that
   assert the verdict for each shape of input.
3. **Two prose claims were false on the live page** (`indistinguishable` described as
   "a real but immaterial difference", and the table docstring saying "resolved but
   under the floor"). Both rewritten to the equivalence semantics.
4. **The floor is not scale-free** — demonstrated: 1% vs 5% error is a *fivefold* gap
   that an absolute 0.10 floor calls a tie, and on an L23-class synthetic no pair can
   ever clear 0.10, so every contest would be "equivalent" by construction. I did not
   silently switch the rule: `floor_mode` now supports `'absolute'` (your literal
   answer, still the default) and `'relative'` (a tenth of the error being compared),
   the constant documents the measured consequence, and the Q&A question now carries
   these numbers so the choice can be made on evidence.
5. **`MIN_PAIRED` was unreachable** — n=1 and n=2 got verdicts, off a **zero-width
   "95% interval"** (with one spectrum every resample is identical). The guard now runs
   before the equivalence test; tested at n=1 and n=2.
6. **Both headline tests exercised zero-spread data**, so the bootstrap was never
   actually tested. Added tests with genuine per-spectrum spread for the winner case,
   the equivalence case (300 tightly-agreeing spectra), and the GLORIA shape.
7. **One seed for every contest** made all six published intervals share the identical
   resample matrix — reproducible but perfectly correlated, so comparing intervals
   across pairs compared the same noise. Now seeded per contest+pair
   (`_pair_seed`, MD5-derived), still reproducible.
8. **An infinite MAE read as `underpowered`** — the one case needing no statistics.
   Now a decisive loss.
9. **`n_paired` was missing from `_INT_LIKE`**, so the head-to-head CSV published
   `12.0` where the accuracy CSV published `12`. Fixed.
10. **Strict ranks were still published beside the tie verdicts** (finding #4 in its
    list) — fixed by `_blank_tied_ranks`, above.
11. **Dead code**: the no-op `pass` branch in the ΔBIC loop, the inert
    `configured_pair` column (False on all 24 real rows), and the never-called
    `bootstrap_ci`. All removed; `compute`'s docstring corrected. Also fixed a
    one-measured-competitor contest still earning `rank 1` — a one-horse race is not a
    standing.

Verified fine by the review: the paired resampling itself (same index matrix applied to
both error vectors, both MAEs recomputed per replicate), `_mae_from_log_err`'s
`axis=-1`, no sign inversion (7000 randomized designs, 0 hits), no double-counting or
χ²/MCMC contest mixing, `coverage_n` from the 68% bounds being safe for both levels,
and the `Int64` rank rendering cleanly through docutils and Bokeh.

**After the fixes:** CI-equivalent **292 passed / 38 skipped**; with data **330
passed**; `sphinx -W` clean; GLORIA page and leaderboard regenerated.

### 2026-08-04 (Stage 7, Task 3: metrics & table correctness)

**Read your answers first.** Two land here: *"Follow Erickson 2023"* for the metric
form (so the fractional multiplicative `mae`/`bias` stay, and the convention is now
*named* on the page rather than assumed), and *"ok, try the last"* on panel
selection, which I implemented as part of this task — `_plan_panels` now takes every
scored **total** component (`a`, `bb`) plus the best-covered **decomposed** one,
matching the total-before-decomposed convention, instead of a top-N of a mixed list.
Your "I confirm" also parks the all-pairs ΔBIC matrix in Task 5.

**The dataset-blind join, demonstrated before and after.** On a two-dataset synthetic
sweep the old merge turned **40 accuracy rows into 80**, and each L23 row carried both
its own `win_frac` *and* PANGAEA's:

```
dataset algorithm  win_frac        <- OLD, dataset-blind merge
    L23  expb_pow       1.0
    L23  expb_pow       0.0        <- PANGAEA's number on an L23 row
```

`tables.accuracy` and `tables.qc` now key and merge on `dataset`, so the same sweep
yields 40 rows with each win fraction on its own dataset's row. The regression test
makes the winner *flip* between datasets, so a cross-assignment is unmistakable
rather than plausible.

**The three denominators are named apart** — `n_pairs` (surviving retrieval-truth
pairs), `n_scored` (spectra that produced a usable fit), `n_attempted` (spectra
tried). On the GLORIA sweep those are 12 / 21 / 100 for the same contest, previously
all published as some flavour of "n".

**Coverage now states its target — and I caught myself shipping a misleading flag.**
My first version emitted a boolean `coverage68_ok`. Checking it against the real
GLORIA numbers, `coverage68 = 0.4167` against nominal 0.68 came out `True`, which
reads as "well calibrated" and is nothing of the sort: at `n=12` the 2-standard-error
window is `[0.41, 0.95]`, so almost nothing is detectable. I worked out the window at
several `n` (`n=12 → [0.41, 0.95]`; `n=21 → [0.48, 0.88]`; `n=3320 → [0.66, 0.70]`)
and replaced the boolean with a **directional verdict**:
`over-confident` / `consistent` / `conservative`, with the page stating that
*consistent* means "not distinguishable from nominal at this `n_pairs`", not
"calibrated". The direction is the finding — on GLORIA, `expb_powflex` is flagged
**over-confident** at both levels while the others are merely indistinguishable.

**The false "0 = perfect" prose is gone.** Each metric now states its own perfect
value: `mae`/`bias` fractional multiplicative (0 = perfect, and 0.109 means 10.9% —
with Seegers' un-subtracted 1.109 named so the two conventions cannot be confused),
`median_ratio` perfect at 1, `win_frac` 0.5 = tie, `coverage68/95` perfect at nominal.

**Two things I extended beyond the literal task, both for the same reason the task
exists.** The accuracy table published **36 all-empty rows out of 40** on the GLORIA
page — the table equivalent of a blank panel — so unscored rows are dropped and the
count is *stated* in the section prose ("36 further (component, band) rows are
omitted because this sweep scored no retrieval-truth pairs for them"), with
`drop_unscored=False` still available. And the rendered HTML showed Taylor, Target and
ΔBIC with `alt="../../_images/taylor_a_dg_440.png"` — the path, not a description —
because those sections passed no caption; `_fig_section` now accepts one caption *per*
figure, which also fixes the "nothing says which stacked image is which" defect. Every
figure on the page now has real alt text; verified in the built HTML, not assumed.

**Formatting:** CSVs rounded to 4 dp with counts/bands/ranks as integers (`440`, not
`440.0`); `csv_table_block` emits `:widths: auto` (confirmed as the `colwidths-auto`
class in the built HTML) and `figure_block` emits `:alt:`.

**Verification:** CI-equivalent **267 passed / 38 skipped** (was 255); with data
**305 passed**; `sphinx-build -W` clean; the regenerated GLORIA accuracy table is 4
informative rows where it was 40 mostly-empty ones.

**Files:** modified `ioptics/report/tables.py`, `ioptics/report/standard.py`,
`ioptics/report/rst.py`, `docs/source/reports/gloria_turbid_v3/*`; new
`ioptics/tests/test_report_table_correctness.py` (12 Tier-1 tests).

#### Adversarial review of this task (Fable subagent) — 5 real defects, 4 fixed

Worth the round trip: it found the same class of bug I had just fixed, still live one
module over.

1. **The dataset-blind join was still in the leaderboard** (`leaderboard.py:116-122`)
   — it merges wins without `dataset`, so the reviewer's fold of the two-dataset
   fixture turned 80 rows into **160**, with `('L23', 'expb_pow')` carrying both its
   own 1.0 and PANGAEA's 0.0; `ranked()` then ranks the duplicates and both the
   landing page and the interactive leaderboard publish them. Nominally Task 5's
   line-item, but it is two lines and it is wrong *today*, so **fixed here** with a
   test that folds the flip-winner fixture. The landing page itself is regenerated in
   Task 5, so the committed page keeps the duplicated rows until then.
2. **My own new caption violated this task's requirement.** The scatter caption read
   `(n=12 scored per algorithm)`, but that `n` comes from `scored_refs`, which takes
   the **max of `n_pairs` across datasets and algorithms** — so on a multi-dataset
   sweep it would claim a count no algorithm achieved, and "scored" is the word the
   same page's glossary had just reserved for `n_scored`. **Fixed**: "at most 12
   retrieval-truth pairs per algorithm; each legend entry states its own". Also
   aligned `style.series_label` to count pairs the way `metrics.n_valid` does (finite
   **and positive**), so a legend `n` cannot disagree with the table's `n_pairs`.
3. **`_publishable` could truncate and could crash.** `astype('int64')` on a
   ``ref_match`` of **442.5** published **442**, and `astype('Int64')` on a
   non-integral value beside an NA raises `TypeError` — which would abort the whole
   page build. Latent only because every wired dataset happens to sit on integral
   bands. **Fixed**: present as integer only when the values are integral; two tests
   with a half-nm band.
4. **The coverage standard error uses the wrong denominator by construction.** It uses
   `n_pairs`, but `metrics.coverage` counts a different population (it needs truth and
   both bounds, and ignores the retrieved value). They agree whenever every scored
   pair has credible bounds — true for the sweeps run so far — but where bands exist
   for only *k* pairs the SE is too tight by `sqrt(n_pairs/k)` and the verdict can
   accuse a thin contest. **Not fixed**: the honest fix is for `metrics` to persist
   the coverage trial count, which is a schema change. Documented precisely in the
   docstring and raised in Q&A for Task 9.
5. **The per-figure captions I added were paired positionally**, which is unsafe
   precisely because a degenerate figure is not written: if the Taylor diagram were
   degenerate and the Target drew, the Target would be published with the Taylor's
   caption *and alt text*. **Fixed**: captions are now a `{name-keyword: caption}`
   mapping matched against the file name, with a test that feeds only a Target.

Minor items: `MAX_REF_PANELS` was dead (2 totals + 1 decomposed can never reach 4) —
now 3, documented as a guard; and one of my formatting assertions had an `or` chain
whose third clause let it pass when no 440 band appeared at all — tightened.

It also **verified** the parts I claimed: the dataset joins and the win-flip
regression behave as described, `_coverage_flags` handles n=0/NaN and survives a CSV
round trip, `_plan_panels` is deterministic and cannot drop a scored total, `:widths:
auto` / `:alt:` are valid under docutils 0.22.4, every claim in the new conventions
prose matches `metrics.py`, and no other consumer breaks on the renames.

**Still live on the site** (not this task's to fix): the committed
`expb_giop_L23_test20` page carries the old figure set, the dataset-less CSVs **and
the false "0 = perfect" sentence**, because that sweep's artifacts are not on this
laptop. It is re-run and regenerated in Task 11.

**After the fixes:** CI-equivalent **271 passed / 38 skipped**; with data **309
passed**; `sphinx -W` clean; every figure on the regenerated page has real alt text.
Files additionally touched: `ioptics/report/leaderboard.py`, `ioptics/style.py`.

### 2026-08-03 (Stage 7, Task 2: data-driven artifact selection)

**The blank GLORIA page is gone — from the committed docs tree, not just in
principle.** `docs/source/reports/gloria_turbid_v3/` now holds
`scatter_a_dg_440.png`, `ratio_hist_a_dg_440.png`, `taylor_a_dg_440.png`,
`target_a_dg_440.png` and `dbic_cdf_expb_pow2_vs_expb_pow.png`, and the five blank
placeholders are deleted. The page has **zero** occurrences of "no data".

**How the figure set is chosen now.**

- `figures.scored_refs(sweep)` returns the `(component, ref_wave, n)` combinations
  the sweep can actually score — from `metrics_scalar` (`n > 0` at a matched
  `ref_wave`), falling back to counting finite truth pairs in `results_spectral`
  when metrics have not been computed. Ordered best-covered first; the page takes
  the top `MAX_REF_PANELS` (3). On `gloria_turbid_v3` that is exactly
  `[('a_dg', 440.0, 12)]`, which is the whole truth GLORIA carries.
- `figures.dbic_pair(sweep)` picks the **k-extremes** — highest- against
  lowest-parameter algorithm — and returns `None` when there are fewer than two
  algorithms or every `k` is identical (then ΔBIC is not asking the
  does-complexity-pay question). On the GLORIA sweep it picks
  `expb_pow2` (k=7) vs `expb_pow` (k=5), a contest that actually ran, instead of the
  phantom `giop`. I implemented k-extremes rather than an all-pairs matrix; an
  all-pairs win/ΔBIC matrix is a better fit for Task 5's leaderboard work than for a
  per-sweep page, so I left it there.
- Taylor/Target follow the best-covered component instead of a hardcoded `a`/440,
  and **keep their page section** per your answer.

**Blank figures are now unpublishable by construction, not by vigilance.**
`plotting._annotate_empty` stamps `EMPTY_FLAG` on a degenerate figure;
`figures._save` refuses to write such a figure and returns no paths; `_fig_section`
already omits a section with no paths. So a blank panel cannot be saved, copied, or
described — the three places it previously slipped through.

**Suppression is stated, not silent.** A new "Not shown for this sweep" section
lists what was omitted and why (e.g. no spectral truth at any reference wavelength;
no ΔBIC contest available), so a reader can tell "we did not measure this" from "we
measured it and it was fine".

**Also in this task:** `ratio_hist` promoted to a page section beside each scatter,
per your answer, with a `figures.ratio_hist` builder it never had; `taylor_target`
output names now carry the reference band (two refs used to overwrite each other's
file — there is a test); `_curated_obs` replaces `int(obs_id.min())` with the
**median-χ²ᵥ `ok` fit** and no int cast, so `per_algorithm` builds on GLORIA's string
ids and shows a typical rather than a flattering fit; `_prune_stale` deletes display
assets a build did not regenerate, while leaving `.rst` alone (a hand-written
`findings.rst` must survive — also tested).

**Tests:** new `ioptics/tests/test_report_selection.py`, **10 Tier-1 tests** covering
the derived set, the metrics-absent fallback, k-extremes and the two no-contest cases,
non-writing of degenerate figures, the honest "Not shown" note, pruning-but-not-of-RST,
and `per_algorithm` on string obs ids.

**Two test-suite corrections that were findings in their own right:**

- `test_report_figures.test_taylor_target` asserted `taylor_a.png` exists. It passed
  before only because a **blank** figure was being written; with blank figures no
  longer saved, it failed. The real cause is that the synthetic fixture gave every
  observation *identical truth*, so the correlation is undefined and a Taylor diagram
  is genuinely degenerate. Fixed properly by adding a `truth_factor` to the shared
  `_make_pair` helper and spreading truth across observations in that fixture — the
  test now exercises a real Taylor diagram rather than asserting the existence of a
  blank one.
- My own pruning test picked `scatter_a_440.png` as the "stale" file, which that
  fixture legitimately regenerates; the test was wrong, not the pruning.

**Verification:** CI-equivalent **255 passed / 38 skipped** (was 245); with data
**293 passed**; `sphinx-build -W` clean on the regenerated tree; the rebuilt GLORIA
page is 54 KB.

**Files:** modified `ioptics/plotting.py` (`EMPTY_FLAG`/`is_empty`),
`ioptics/report/figures.py` (`scored_refs`, `dbic_pair`, `ratio_hist`, ref in
taylor/target names, non-saving of empties), `ioptics/report/standard.py` (derived
plan, "Not shown", `_curated_obs`, `_prune_stale`), `ioptics/tests/test_metrics.py`
(+`truth_factor`), `ioptics/tests/test_report_figures.py`,
`docs/source/reports/gloria_turbid_v3/*`; new
`ioptics/tests/test_report_selection.py`.

**Not done here, deliberately:** the L23 smoke page still carries the old figure set,
because that sweep's artifacts are not on this laptop — it is re-run in Task 11, and
its page regenerates then.

### 2026-08-03 (Stage 7, Task 1: figure style module + per-algorithm identity)

**New module `ioptics/style.py`** — one place decides how an IOPtics figure looks.

- `RC` (fonts, constrained layout, grid, spines, palette) applied two ways:
  `style.context()` / the `@style.styled` decorator around each builder, so
  **importing IOPtics never mutates a caller's rcParams** (there is a test for that),
  and `use_ioptics_style()` for scripts that draw everything in our style.
- `PALETTE` mirrors the `--iop-*` custom properties in `_static/custom.css`, so
  figures and site chrome finally agree. `SERIES_COLORS` leads with blue/amber
  because that pair survives deuteranopia and greyscale.
- **`algo_style(name)` → fixed `(colour, marker)`.** This is the actual fix for the
  defect: colour is now derived from the algorithm *name*, not from its row order
  within one figure. Curated slots for the six shipped algorithms, MD5-derived slots
  for anything else — **MD5 not `hash()`**, because Python salts string hashing per
  process, so a hash-derived colour would change between runs and quietly betray a
  reader who learned "my model is the teal one".
- Helpers: `component_label` (quantity + unit, e.g. ``retrieved $a_{dg}$(440)
  [m$^{-1}$]``), `ratio_mpd` / `series_label` (GIOP Table-4 statistics), and
  `log_ticks`.

**`plotting.py`** — every builder decorated and restyled: per-algorithm colour and
marker in `scatter_log`, `ratio_hist`, `residual_rrs`, `taylor`, `target`;
`spectra_band` takes its colour from the algorithm and its y-label from the
component; guides and zero-lines use one neutral ink.

**The two visible defects are fixed, and I checked by looking at the output rather
than trusting the code:**

- **Colliding tick labels.** `log_ticks` labels decades and draws minors at 2 and 5,
  labelling them **only** when the axis spans under ~1.2 decades (otherwise there
  would be nothing to read). The published scatter's "2×10⁻² 3 4 6×10⁻²" smear is
  gone.
- **The "Taylor diagram" that wasn't one.** The azimuth is now labelled in
  **correlation** (0, 0.2 … 0.95, 0.99) instead of degrees, and **centred-RMSD arcs**
  are drawn about the reference point, so the third leg of the Taylor identity is
  readable off the figure. Two placement bugs of my own showed up only in the
  rendered PNG and were fixed: arc labels landed wherever clipping ended (now at the
  midpoint of the visible arc, on a small white pad), and a stray radial annotation
  collided with the arcs (dropped; both axis roles live in the title). `target` gained
  constant-RMSD rings so radial distance is quantifiable.

**In-panel statistics (per IOCCG R5 / GIOP practice).** Each scatter series' legend
entry now reads e.g. `expb_pow  n=61, ratio 0.55, MPD 73%` — the numbers on the
figure, not only in a table. Rendered against the real GLORIA `a_dg(440)` data it
immediately shows the four turbid variants sitting on top of each other (ratio
0.47-0.55, MPD 72-76%), which is the null result the pages currently never state.

**Applied project-wide**, per the task: `docs/figures/make_model_components.py` and
`make_l23_overview.py` now call `use_ioptics_style()` (and both regenerated PNGs are
committed), and `reports/scripts/gloria_fits_report.py` does the same.
`docs/scripts/ioptics_graphic.py` was **deliberately left alone** — it is a hand-tuned
hero graphic using `fig.add_axes` with manual positions, which constrained layout
would fight, and it is not in the task's list.

**Two things I broke and caught by running, not by reading:**

- Adding `from ioptics import style` to the `docs/figures/` scripts broke them
  outright (`ModuleNotFoundError`) — run as scripts, `sys.path[0]` is `docs/figures/`
  and the package is not installed in `ocean14`, it is picked up from the cwd. Both
  now carry the same repo-root import guard `reports/scripts/` already used.
- Global constrained layout made the `corner` package warn on every corner plot
  (it lays its grid out with `subplots_adjust`, which matplotlib refuses to honour
  under a layout engine). `style.context()` now takes per-builder overrides and the
  corner builder opts out. Warning count is back to the single pre-existing ocpy one.

**Tests:** new `ioptics/tests/test_style.py`, **15 Tier-1 tests**. The three that
matter pin the identity: an algorithm's style is unchanged when other algorithms join
the figure (the regression test for the original defect, asserted at the figure level
by reading the scatter collections' face colours), it is **stable across processes**
(asserted by running a subprocess — this is what catches a `hash()` regression), and
the six shipped algorithms are distinct in colour *and* marker. Plus rcParams
non-leakage, import purity, label/statistic correctness, and tick-taming both sides of
the 1.2-decade threshold.

**Verification:** CI-equivalent **245 passed / 38 skipped** (was 230/38 — the 15 new
tests); with the data tree **283 passed**; `sphinx-build -W` clean; both docs figure
generators re-run successfully.

**Files:** new `ioptics/style.py`, `ioptics/tests/test_style.py`; modified
`ioptics/plotting.py`, `ioptics/report/figures.py` (passes `component`/`ref` through
for axis labels), `docs/figures/*.py`, `reports/scripts/gloria_fits_report.py`,
`docs/source/_static/{model_components,l23_overview}.png`.

**Q&A:** one new question (below) on whether the Taylor work should continue at all,
which is the Q6-vs-community-evidence conflict — I implemented the readability fix you
asked for, so nothing is blocked either way.

### 2026-08-03 (Stage 7, Task 0: refresh this prompt file against the code)

Re-verified every factual claim in this doc against the current code and repo rather
than trusting the audit it was written from, then added the earlier-stage conventions
it was missing. No code changed.

**Confirmed as written** (so later tasks can rely on them): `_STANDARD_SEED` is
`expb_pow`/`giop`/`gsm` and the turbid trio is opt-in through `register_turbid` with
`TURBID_MAXFEV = 40000`; `CHI2NU_POOR_FIT = 5.0` is shared with
`metrics.CHI2NU_QC_MAX`; `figures.dbic_cdf` defaults to the `expb_pow`-vs-`giop` pair;
`gsm` appears **zero** times in `models.rst`/`datasets.rst`; the three stale scoping
claims are still live (`index.rst` "Through **Stage 2**", `api/index.rst` "Stage-0
modules", `models.rst` "runs two side by side"); `_static/ioptics_graphic.png` is
referenced by no `.rst` or the README; `build_v1.py` has its argparse CLI. Test
baselines re-measured: **230 passed / 38 skipped** without `$OS_COLOR`, **264 / 4**
with it, `sphinx-build -W` clean.

**Two defect claims promoted from "asserted" to "verified at the code"**, and written
into the defect list as items 14-15:

- `metrics.wins` does run the pairwise round-robin, but `_bump` tallies into
  `(group_key, algorithm)` — the **opponent identity is discarded**, so Task 4 cannot
  derive a paired statistic from `metrics_pairwise` and must go back to
  `results_spectral`.
- `bing/fitting/chisq_fit.py:117-119` calls `curve_fit(..., full_output=False)`, so
  scipy's `nfev` never reaches IOPtics — cost reporting genuinely requires new
  instrumentation, not just a new metrics pass.

**Earlier-stage material this doc had omitted** (now in Conventions / carryover):

- The **hang guard** from Stage 6 Task 2 — a per-test `SIGALRM` ceiling in `conftest`
  that defers to `pytest-timeout` — with the instruction not to raise it around a test
  that hangs, since the hang is the finding.
- **GLORIA's per-dataset noise regime**: the 0.05 error floor, the wider 0.10
  imputation fraction for the ~70% of spectra quoting no uncertainty, the
  `insitu+floor:` vs `insitu+imputed:` tags, the once-per-batch
  `ImputedUncertaintyWarning`, and the post-PR-#9 independence of `noise_floor=False`
  from `noise_imputed=False`. Any GLORIA number in a report has to say which regime
  produced it.
- The **four-state status vocabulary** and why reports must not collapse it (63%
  `out_of_scope` on GLORIA is a statement about the models).
- `wv_min`/`wv_max` on `SweepConfig`; the **build-script CLI**;
  `runs/first_full_run.src` for the workstation L23 run.
- **`AlgorithmConfig.overrides` is accepted by `config` and never read by
  `run_sweep`** — verified by grep (no reference in `run.py`), which sharpens Task 9:
  the config copy in provenance can advertise settings that never ran.
- **Git facts**: branch `improve-reporting`; PRs #8/#9/#10 all merged to `develop`, so
  that is this stage's PR base.

No open questions added — the Q&A already carries the blockers (tie statistic for
Task 4, URL scheme and generated-vs-curated for Task 6, cross-sweep identity for
Task 9, the Taylor fix-or-demote conflict with Q6, metric family, cost scope, and
where to run `multi_v2`). **Ready to execute from Task 1.**

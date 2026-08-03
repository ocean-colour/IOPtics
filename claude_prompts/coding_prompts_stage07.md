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

**New after Task 2:**

- **How many `(component, ref-λ)` panels should a page carry?** `MAX_REF_PANELS` is
  3 today, best-covered first, so a full L23 sweep (which scores `a`, `bb`, `a_ph`,
  `a_dg`, `bb_p` at 440/443/555/670) shows 3 of up to ~10 rather than all of them —
  each now costing two figures, since every scatter is paired with a ratio
  distribution. Options: keep 3; raise it; or show all *total* components (`a`, `bb`)
  plus the best-covered decomposed one, which matches the community's
  total-before-decomposed convention. My lean is the last.
- **Should the ΔBIC contest stay a single k-extreme pair per page?** I implemented
  the k-extremes because that is the "does complexity pay" question. An all-pairs
  ΔBIC/win matrix would say more, but it belongs with the leaderboard work in Task 5
  — confirm you are happy for it to land there rather than on each sweep page.

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

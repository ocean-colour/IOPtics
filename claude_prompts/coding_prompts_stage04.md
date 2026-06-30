# Code IOPtics — Stage 4: Metrics & diagnostics

## Goal

Score the sweep uniformly. **Exit criterion:** `metrics.compute(sweep_id)` emits
`metrics_{spectral,scalar,pairwise}.parquet`; the primitives match hand-computed
values on toy `(M,O)` arrays; `expb_pow` vs `giop` ΔBIC and wins are populated.
(All checkable **Tier-1** on a synthetic results table — metrics is table-in; a
real Stage-3 sweep is an optional Tier-2 confirmation.)

Implements **Metrics & diagnostics** and the **Staged plan / Stage 4** of
`docs/design/IOPtics_implementation.md`. One prompt per module/concern.

## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- **Q&A holds open questions for JXP** — pose them, do **not** self-answer (JXP
  answers before the next task; decisions/rationale go in the Logs).
- Run tests via the env interpreter directly
  (`/home/xavier/miniforge3/envs/ocean14/bin/python -m pytest -q`); `conda
  activate` fails non-interactively. **Run the suite without `$OS_COLOR`**
  (CI-equivalent) before declaring a task done.
- `metrics`/`diagnostics` are **pure table-in/table-out** — no BING/ocpy imports,
  no re-fitting. All accuracy metrics are log10 / multiplicative. (Because they
  read the persisted tables, **metrics is fully Tier-1-testable** on synthetic
  results — no L23 needed; see Known constraints.)
- Capitalize **BING** in prose. Keep docstrings RST-clean so `sphinx-build -W`
  stays green; new public APIs are autodoc'd via `docs/source/api/index.rst`.

## Context

- `docs/design/IOPtics_implementation.md` — §Metrics & diagnostics (§1 accuracy,
  §2 Rrs closure + dual-sided window/QC, §3 ΔBIC, §4 coverage + detection, §5
  wins/rankings; non-uniformity intersection rule + coverage accounting; ±3 nm
  ref-band match; Chl strata; `diagnostics` figure-data functions).
- Inputs: `runs/<sweep_id>/results_{spectral,scalar}.parquet`, `chains/`.

### Stage 0–3 carryover (what already exists — the tables you score)

- **`io` reads/writes the tables.** Use `io.read_results(sweep_id, root=None)` →
  `(spectral_df, scalar_df)` and write `metrics_*.parquet` under
  `io.sweep_dir(sweep_id, root=...)`. `io.load_chain(path)` loads a chain NPZ
  (numpy dict: `chains, idx, wave, obs_Rrs, varRrs, Chl, Y`) for `diagnostics`.
- **`results_spectral` columns** (one row per `dataset, obs_id, algorithm,
  fit_method, component, wavelength`): `value, lo68, hi68, lo95, hi95, truth,
  truth_interp, unit`. Components: `a, bb, a_ph, a_dg, bb_p, Rrs_model`. `truth`
  is `NaN` where the dataset lacks it **and for `Rrs_model`** (model-only).
- **`results_scalar` columns** (one row per `dataset, obs_id, algorithm,
  fit_method`): `chi2, chi2_nu, AIC, BIC, n_bands, k`; `Chl, sig_Chl, a_cdom440,
  sig_a_cdom440, Sdg, sig_Sdg, beta, sig_beta`; `Chl_truth, a_cdom440_truth,
  Sdg_truth, beta_truth`; `status, chain_file, provenance_id`. Amplitudes are
  **physical/linear** (a_cdom440 in 1/m); the raw log10 fit params are not in the
  tables.
- A real sweep contains **both `fit_method='chisq'` (all records) and `'mcmc'`
  (the subset)** rows for an MCMC algorithm; χ² rows have `chain_file` null.

### ⚠ Known constraints / decisions — read before coding

- **`fit_method` is a key the design's metric tuples omit.** The same
  `(dataset, obs_id, algorithm)` appears twice (χ² for all, MCMC for the subset).
  `metrics.compute` must **group/filter on `fit_method`** — e.g. score the χ²
  population and the MCMC subset separately, and compute ΔBIC/wins **like-for-like
  (χ² vs χ²)** since `expb_pow` is χ²-only. Decide and document.
- **The observed `Rrs` is NOT in the tables** (`Rrs_model.truth` is `NaN`, per the
  Stage-2 decision). So §2 Rrs closure can do **χ²ᵥ/AIC/BIC/ΔBIC straight from
  `results_scalar`** table-in, but the **log-space Rrs MAE/bias + dual-sided
  window** need the observed `Rrs`. Options to surface to JXP: (a) persist
  `Rrs_obs` (add a spectral component, or revisit `Rrs_model.truth = Rrs_clean`),
  or (b) scope §2 to the scalar χ²ᵥ + the `status` QC already written by `run`.
- **Metrics is fully Tier-1.** Feed a **synthetic results table** — build
  `RetrievalResult`s + records by hand and `io.write_results(...)` to a
  `tmp_path` root, then `metrics.compute` on it — so the orchestration test needs
  no L23. A Tier-2 `@needs_l23` smoke (run a tiny real sweep, then compute) is
  optional/confirmatory. Toy `(M,O)` arrays cover the primitives.
- `diagnostics.corner_data` loads chains via `io.load_chain` (numpy NPZ) — still
  engine-free (no BING import).

## Prompts

### Coding

1. `metrics` §1 accuracy primitives.
2. `metrics` §2 Rrs closure + §3 model selection.
3. `metrics` §4 coverage/detection + §5 wins/rankings.
4. `metrics.compute` orchestration (intersection rule, ref-band match, strata).
5. `diagnostics` figure-data functions.
6. Tests.

### Pull Requests

1. I have issued a PR for this stage. Please review it and post it to GitHub.  Also, investigate the CI issues and fix them. Please log your work in the Logs section below.
2. Please read the PR comments and make any needed changes to the code to address them.  And, if you have any additional questions, please add them to the Q&A section below. Log your work.

## Modules

### Tasks

1. **`metrics` §1 accuracy.** `mae`/`bias`/`rms_log`/`median_ratio`/`ratio_hist`
   (RATIO_EDGES)/`type2_fit` on aligned `(M,O)`; NaN-drop. Tier-1 with known
   answers. Q&A. Log.

2. **`metrics` §2 + §3.** §3 model selection (`delta_bic`/`dbic_cdf`) reads
   χ²ᵥ/AIC/BIC straight from `results_scalar` (compare χ²-vs-χ² rows). §2 Rrs
   closure: χ²ᵥ + the `status` QC are table-in; the **log-space Rrs MAE/bias +
   dual-sided window (`fit_noise`, `Rrs_MAE>0.25`) need the observed `Rrs`, which
   isn't in the tables yet** — resolve the Known-constraints decision (persist
   `Rrs_obs` vs scalar-only §2) with JXP first. Tier-1 on toy/synthetic tables.
   Q&A. Log.

3. **`metrics` §4 + §5.** `coverage` at 68/95% + `detection` (Nσ/upper-limit);
   `wins` (`abs_log_err`, provisional) + `rankings`. Tier-1. Q&A. Log.

4. **`metrics.compute(sweep_id, root=None)`.** Read via `io.read_results`,
   orchestrate the above into `metrics_{spectral,scalar,pairwise}.parquet`
   written under `io.sweep_dir(...)`: **group/filter on `fit_method`**; the
   **intersection rule** (score only non-NaN `(M,O)`, record `n`+coverage); ±3 nm
   **ref-band match** with `ref_match`; Chl **strata** (oligo/meso/eutro); GLORIA
   `caveat` flag. **Tier-1 on a synthetic results table** (build results →
   `io.write_results` to `tmp_path` → `compute`); optional Tier-2 `@needs_l23`
   confirmatory run on a tiny real sweep. Q&A. Log.

5. **`diagnostics`.** `taylor_stats`/`target_stats`/`scatter_data`/
   `ratio_hist_data`/`residual_spectra`/`corner_data`(loads NPZ)/`dbic_cdf_data`,
   returning arrays only. Tier-1 shapes + known values. Q&A. Log.

6. **Tests.** Consolidate Tier-1 metric/diagnostic checks (toy `(M,O)` + a
   synthetic results table through `compute`); the expb_pow-vs-giop ΔBIC + wins
   can be asserted **Tier-1** on a synthetic two-algorithm table. Optional Tier-2
   `@needs_l23`: `compute` over a tiny real sweep. Q&A. Log.

### Q&A

**Task 1 (`metrics` §1 accuracy).**

1. **Type-II regression flavor + orientation.** `type2_fit` is implemented as a
   reduced-major-axis (geometric-mean) fit in log10 space, regressing
   retrieved `M` on truth `O` (slope = sign(r)·σ_logM/σ_logO, intercept through
   the log-means, `r2` = Pearson²). Is RMA the intended Type-II (vs. major-axis /
   orthogonal), and is M-on-O the orientation you want reported?
   >A. Yes, RMA is the intended Type-II and M-on-O is the orientation.

2. **Non-positive guard.** The log-space metrics assume strictly positive IOPs
   and call `np.log10` directly; a zero/negative retrieval would yield `-inf`/
   `nan` (and a warning) rather than being dropped. Should §1 actively drop
   non-positive pairs too (treat them like NaN), or is trusting positivity fine
   since prep/evaluate emit physical IOPs?
   >A. Yes, drop non-positive pairs.

3. **`ratio_hist` output form.** Currently returns raw integer counts per
   `RATIO_EDGES` bucket (length 8). Do you want it to also return/normalize to
   fractions, or keep counts and let `compute`/`diagnostics` normalize?
   >A. Keep counts and let `compute`/`diagnostics` normalize.

**Task 2 (`metrics` §2 + §3).**

4. **BLOCKING for Task 4 — observed `Rrs` persistence.** §3 (`delta_bic`/
   `dbic_cdf`) and the §2 χ²ᵥ flag are fully table-in and done. But the §2
   log-space Rrs MAE/bias + dual-sided window need the *observed* `Rrs`, which
   isn't in the tables (`Rrs_model.truth` is NaN). I implemented `rrs_closure`/
   `rrs_window` as pure array-in helpers so they're ready, but `compute` (Task 4)
   can't feed them until we decide: **(a)** persist `Rrs_obs` — add a spectral
   component, or set `Rrs_model.truth = Rrs_clean` (revisiting the Stage-2
   decision); or **(b)** scope §2 to the scalar χ²ᵥ + `status` QC only and drop
   the Rrs-space MAE/bias from the metrics tables. Which?
   >A. Persist `Rrs_obs`.

5. **χ²ᵥ `good_band` thresholds.** `chi2nu_quality` flags `<0.5` overfit /
   `>1.5` underfit / else good. Is `(0.5, 1.5)` the band you want, or should it
   be tied to dof (e.g. ±2·sqrt(2/dof) around 1) or a different fixed band?
   >A. It should be tied to dof.

6. **`fit_noise` definition.** Currently `fit_noise = (Rrs_MAE < NOISE_FLOOR)`
   with `NOISE_FLOOR=0.05` (~5% measurement noise) and QC-fail at
   `Rrs_MAE>0.25`. "Well below the noise floor" — do you want a stricter factor
   (e.g. `< 0.5·NOISE_FLOOR`) for `fit_noise`, and are 0.05/0.25 the right
   numbers?
   >A. Use 0.5 and 0.25 for now, but make them configurable and record them.

**Task 3 (`metrics` §4 + §5).**

7. **`detection` Nσ semantics.** `detection(med, lo, hi)` marks a *detection*
   when the credible interval excludes zero (`lo > 0`), else a non-detection
   reported as an upper limit (`hi`); the "Nσ" is set by *which* level's bounds
   you pass (95% ≈ 2σ, 68% ≈ 1σ). Is the interval-excludes-zero rule what you
   want, or do you want an explicit significance `med / σ` with a separate Nσ
   threshold (and if so, σ from which bounds)?
   >A. Use the interval-excludes-zero rule.

8. **`wins` tie handling.** A tie in `abs_log_err` awards neither algorithm the
   win but still counts as a contest for both (so a perpetual tie → `win_frac`
   0.5 each only if you split; currently 0/contest each). Prefer split-credit
   (0.5 each) on ties instead?
   >A. Prefer split-credit on ties.

9. **`rankings` column names.** `rankings` ranks `lower_is_better=('mae',
   'abs_bias','rms_log')` ascending and `higher_is_better=('win_frac',
   'coverage')` descending, by intersection with the columns present. Confirm
   these are the column names `compute` (Task 4) should emit into
   `metrics_scalar` (esp. `abs_bias` for |bias|), so the keys line up.
   >A. Confirmed

**Task 4 (`metrics.compute` orchestration).**

10. **Table shape: wide vs fully-long.** I made the three metrics tables **wide
    tidy** (one row per key, metric columns: `mae`, `bias`, `coverage68`, …)
    rather than fully-melted `(…, metric, value)` long. Wide is more compact and
    a direct group-by for `report`/leaderboard. OK, or do you want the melted
    long form the design §1 sketched (`…, metric, value, n`)?
    >A. Keep the wide form.

11. **`Rrs_obs` = observed (noisy), persisted as a component.** I persist
    `record.Rrs` (the noisy observation the fit saw) as a new spectral component
    `Rrs_obs` (not `Rrs_clean`; the design's option (a) phrased it as
    `Rrs_model.truth = Rrs_clean`). §2 closure = `Rrs_model` vs `Rrs_obs`, so it
    measures fit residual vs the ~noise floor — which only makes sense against
    the noisy obs. Confirm observed (not clean), and that a new **component**
    (vs adding an `Rrs_obs` column) is the layout you want.
    >A. Yes, I confirm.

12. **Closure aggregation across obs.** The per-(dataset,algorithm,fit_method,
    stratum) closure row reduces per-obs Rrs MAE/bias by **median** across obs,
    and `fit_noise`/`qc_fail` by mean (fraction). Median OK, or do you want a
    pooled log-space MAE over all (obs×λ) residuals instead?
    >A. Median is fine.
13. **ΔBIC lives in `metrics_pairwise`** with a `contest` column
    (`'wins'` | `'dbic'`); `dbic` rows carry `model_a/model_b/frac_favor_*/
    median_dbic/n` and leave the wins columns NaN (mixed schema, one file). Fine,
    or split ΔBIC into its own artifact?
    >A. Fine.

**Task 5 (`diagnostics`).**

14. **Taylor/Target signature + space.** The design sketched
    `taylor_stats(table, ref)`; I implemented
    `taylor_stats(table, component, ref=None, …)` — **per single component**
    (mixing components in one Taylor point would mix magnitudes) and computed in
    **log10 space** (consistent with the multiplicative metrics). Confirm
    per-component + log-space is right (vs pooling components, or linear space).
    >A. Per-component + log-space is right.
15. **`corner_data` labels are generic.** The chain NPZ persists no parameter
    names, so `corner_data` returns `labels=['p0','p1',…]`. OK, or should the
    chain saver (`io.save_chain` / `run`) also persist `pnames` so corner axes
    are named (a Stage-2/3 touch)?
    >A. Have it persist `pnames`.

16. **Scatter guide ratios.** `scatter_data` returns 1:1, 3:1 and 1:3
    (≈0.33:1) guide lines (design said "1:1/3:1/0.3:1"). Confirm 1:3 (0.333) vs
    a literal 0.3 factor.
    >A.  I confirm

**Task 6 (tests).**

17. **Stage-4 exit criterion met.** Consolidated Tier-1 + a parquet round-trip
    test + a Tier-2 `@needs_l23` `compute`-over-real-sweep (passes locally with
    L23 data). No open questions — flag if you'd like the Tier-2 confirmatory
    test to also assert accuracy thresholds (à la `test_micro`) or a real-chain
    `corner_data` smoke.

**PR Task 1 (review + post + CI).**

18. **PR base branch.** PR #7 (`stage-3` → **`main`**) targets `main`, but
    `develop` exists and the noted convention was for stage PRs to target
    `develop`. Want me (or you) to retarget the base to `develop`, or is `main`
    intended for this stage?

## Logs

### Stage 4 — Task 1: `metrics` §1 accuracy primitives (2026-06-29)

- Implemented in [`ioptics/metrics.py`](../ioptics/metrics.py): `mae`, `bias`,
  `rms_log`, `median_ratio`, `ratio_hist` (with `RATIO_EDGES`), `type2_fit`,
  plus `n_valid` and an internal `_aligned(M, O)` helper that applies the
  intersection rule (drop pairs with NaN in *either* array) — the single place
  the NaN-drop happens, so every primitive shares it.
- All accuracy forms are log10/multiplicative per design §1 (Erickson 2023
  Eqs. 13–14): `mae`/`bias` are `10**mean(...) - 1`, `rms_log` is RMS of
  `log10(M/O)`. Each scalar returns `np.nan` on empty input; `type2_fit` returns
  a `(nan,nan,nan)` triple when <2 pairs or zero log-spread. Shape mismatch
  raises `ValueError`.
- **Decisions:** kept the design's exact primitive signatures (scalars in,
  scalar out) so the per-row `n`/coverage accounting lives in `compute`
  (Task 4); exposed `n_valid` so callers can record the surviving count without
  re-deriving the mask. `type2_fit` chose RMA — flagged for confirmation in Q&A.
- Tier-1 tests: [`ioptics/tests/test_metrics.py`](../ioptics/tests/test_metrics.py)
  — perfect-agreement, constant-factor (`M=2O` → mae=bias=1, rms_log=log10 2),
  bias sign, one-ratio-per-bucket histogram, known log-linear line for
  `type2_fit`, NaN-drop intersection, empty→NaN, shape-mismatch raise.
- Tests: `8 passed` for the new file; full suite `102 passed, 12 skipped`
  (run with `$OS_COLOR` unset, CI-equivalent). No BING/ocpy imports added.

### Stage 4 — Task 2: `metrics` §2 closure + §3 model selection (2026-06-29)

- **§3 model selection (fully table-in):** `delta_bic(bic_a, bic_b)` =
  `BIC_a − BIC_b` (<0 favors model A / the more complex model; broadcasts over
  arrays); `dbic_cdf(df, model_a, model_b, by=None, fit_method='chisq', ...)`
  inner-joins the two algorithms' scalar rows on `(dataset, obs_id)`
  **like-for-like within one `fit_method`** (default χ², since `expb_pow` is
  χ²-only — addresses the Known-constraints `fit_method` note), computes ΔBIC
  per matched spectrum, and returns `dict(dbic[sorted], cdf, n, frac_favor_a,
  frac_favor_b)`; `by=` a column returns the per-stratum dict.
- **§2 closure:** `chi2nu_quality(chi2_nu, good_band=(0.5,1.5))` → `good`/
  `overfit`/`underfit`/`unknown` (table-in, from `results_scalar`).
  `rrs_window(rrs_mae)` → `{fit_noise, qc_fail}` dual-sided flags;
  `rrs_closure(Rrs_model, Rrs_obs)` → `{rrs_mae, rrs_bias, n, fit_noise,
  qc_fail}` reusing the §1 `mae`/`bias` forms. Module constants `NOISE_FLOOR`
  (0.05), `RRS_QC_MAX` (0.25) — provisional.
- **Decision / blocker:** the §2 Rrs-space functions take the `Rrs` arrays
  **explicitly**, so they're correct independent of how `Rrs_obs` gets sourced.
  They are deliberately *not* wired into a table reduction yet — `compute`
  (Task 4) can't feed them until the `Rrs_obs` persistence question (Q&A #4) is
  resolved. Threshold choices (χ²ᵥ band, `fit_noise` factor, 0.05/0.25) flagged
  in Q&A #5–6. Imported `pandas` in `metrics` (allowed — pandas/pyarrow only,
  no BING/ocpy).
- Tests added to [`ioptics/tests/test_metrics.py`](../ioptics/tests/test_metrics.py):
  χ²ᵥ classification + band edges, Rrs window flags, perfect/QC-fail closure,
  `delta_bic` sign (scalar + array), a hand-built two-algorithm scalar table
  where `expb_pow` beats `giop` on 2 of 3 spectra (ΔBIC = −5,−3,+10 →
  frac_favor_a=2/3, exact CDF), `fit_method` filtering (MCMC rows excluded), and
  stratified `by='stratum'`.
- Tests: `16 passed` for the file; full suite `110 passed, 12 skipped`
  (`$OS_COLOR` unset).

### Stage 4 — Task 3: `metrics` §4 coverage/detection + §5 wins/rankings (2026-06-30)

- **Folded in the answered Q&A from Tasks 1–2 (now decided):**
  - #2 — `_aligned` now also drops **non-positive** pairs (`M>0 & O>0`) so the
    log-space metrics never see a zero/negative; added `test_nonpositive_dropped`.
  - #5 — `chi2nu_quality(chi2_nu, dof, *, n_sigma=2.0)` band is now **tied to
    dof**: `1 ± n_sigma·sqrt(2/dof)` (reduced-χ²ᵥ std is `sqrt(2/dof)`). Tests
    updated + `test_chi2nu_band_tightens_with_dof`.
  - #6 — `fit_noise` now triggers at `Rrs_MAE < FIT_NOISE_FACTOR·NOISE_FLOOR`
    (`0.5·0.05`); `FIT_NOISE_FACTOR`/`NOISE_FLOOR`/`RRS_QC_MAX` are module
    constants and all three are per-call configurable (to be recorded by
    `compute`). (#1/#3/#4 needed no code change — RMA/M-on-O kept; `ratio_hist`
    stays counts; `Rrs_obs` persistence is a Task-4 wiring item.)
- **§4:** `coverage(O, lo, hi)` = fraction of truth inside `[lo,hi]` (inclusive;
  finite-mask drop, no positivity requirement — it's a linear-space calibration
  test), `np.nan` if unscorable. `detection(med, lo, hi)` → `dict(detected,
  upper_limit)`: detected where the interval excludes zero (`lo>0`), else the
  upper limit is `hi` (the Nσ is set by which level's bounds you pass — Q&A #7).
- **§5:** `wins(table, by=('dataset','component','ref_wave'),
  metric='abs_log_err')` runs a per-spectrum round-robin (computes
  `abs_log_err=|log10(value/truth)|` if absent), closer-to-truth wins; ties = no
  win but still a contest (Q&A #8). Emits tidy `(by…, algorithm, wins, contests,
  win_frac)` → `metrics_pairwise`. `rankings(metrics_scalar, by=...)` adds
  `<col>_rank` per metric (1=best): `lower_is_better` ascending, `higher_is_better`
  descending, `method='min'` so ties share the best rank (Q&A #9 on column names).
- Tests added: coverage levels/inclusive/NaN-drop, detection upper-limit,
  wins head-to-head (A 2/3 vs B 1/3) + precomputed-metric path, rankings
  ordering + tie-sharing.
- Tests: `25 passed` for the file; full suite `119 passed, 12 skipped`
  (`$OS_COLOR` unset). `ioptics.metrics` is autodoc'd (`:members:`) so the new
  APIs are documented; docstrings use RST double-backtick literals.

### Stage 4 — Task 4: `metrics.compute` orchestration (2026-06-30)

- **Folded Task-3 answers:** `wins` now **splits credit 0.5/0.5 on ties**
  (Q&A #8); `detection`/`rankings` unchanged (#7/#9 confirmed).
- **Persisted observed Rrs (realizes Q&A #4).** `io` now writes an `Rrs_obs`
  spectral component (= `record.Rrs`, the noisy observation; `truth`/bounds NaN,
  unit 1/sr) so the metrics layer can close `Rrs_model` against it — table-in, no
  BING/ocpy. `test_io` updated (7 components now; `Rrs_obs.value == record.Rrs`).
- **`metrics.compute(sweep_id, root=None, …)`** reads via `io.read_results`,
  assigns Chl **strata** (`CHL_BINS`, truth Chl else retrieved) per
  `(dataset, obs_id)`, and emits every reduction for `stratum='all'` **and** each
  bin (via a `_scoped` duplicate-with-`'all'` trick). Grouped by **`fit_method`**
  throughout (χ² population and MCMC subset scored separately; ΔBIC like-for-like).
  Three **wide tidy** tables written under `io.sweep_dir`:
  - `metrics_spectral` — per `(dataset,algorithm,fit_method,stratum,component,
    wavelength)`: §1 `mae/bias/rms_log/median_ratio` + §4 `coverage68/95`, `n`,
    over the native grid (truth-bearing components only).
  - `metrics_scalar` — ±3 nm **ref-band** §1 accuracy (`ref_wave`+`ref_match`
    via `_nearest_within`; unmatched bands omitted) for spectral components,
    derived-scalar accuracy (`Chl/a_cdom440/Sdg`, `ref_wave` NaN), and the §2
    **closure** row (`component='Rrs'`: `chi2_nu_median`, `frac_good/overfit/
    underfit` with the dof-scaled band, Rrs `mae/bias`, `frac_fit_noise/qc_fail`).
    Accuracy rows carry cross-algorithm `*_rank`. GLORIA `a_dg` → `caveat`.
  - `metrics_pairwise` — §5 `wins` per `(…,component,ref_wave)` (+`win_frac_rank`)
    and the §3 ΔBIC contest (`expb_pow` vs `giop`) per `(dataset,fit_method,
    stratum)`, distinguished by a `contest` column.
- **Intersection rule** is inherited from the §1 primitives (`n` recorded on
  every accuracy row); coverage uses a finite-mask (no positivity drop).
- **Bug fixed:** `wins` built its group key via `np.atleast_1d(gkey)`, which
  stringified the mixed str/float key (`ref_wave` → `'440.0'`); now slices the
  tuple directly, preserving dtypes.
- **Decisions flagged in Q&A #10–13:** wide-vs-long table shape; observed (noisy)
  `Rrs_obs` as a component; median closure aggregation; ΔBIC co-located in
  `metrics_pairwise`.
- Tier-1 test: synthetic 2-algorithm sweep (`expb_pow` perfect vs `giop` 2×-high,
  4 obs spanning all Chl strata, +1 MCMC row) → `io.write_results` → `compute`;
  asserts spectral mae/coverage, closure `frac_good`/Rrs MAE/`fit_noise`/`qc_fail`,
  ref-band ranks, wins (1.0 vs 0.0), ΔBIC `frac_favor_a=0.75`, strata present,
  and all three files written.
- Tests: `31 passed` for the file; full suite `125 passed, 12 skipped`
  (`$OS_COLOR` unset).

### Stage 4 — Task 5: `diagnostics` figure-data functions (2026-06-30)

- Implemented [`ioptics/diagnostics.py`](../ioptics/diagnostics.py) — pure
  table-in (no BING/ocpy; imports `io`/`metrics`), all arrays-only:
  - `taylor_stats(table, component, ref=None)` — per-algorithm `corr`,
    `std_model`/`std_ref`, `norm_std`, `crmsd`, `norm_crmsd`, `n` (Taylor 2001),
    log10 space; obeys the Taylor identity (asserted in tests).
  - `target_stats(table, component, ref=None)` — `bias`, `unbiased_rmsd`,
    `signed_unbiased_rmsd` (sign by std over/under-dispersion), `total_rmsd`
    (Jolliff 2009), log10 space.
  - `scatter_data(table, component, ref=None)` — `dict(points[df x=truth,
    y=retrieved], guides{1:1, 3:1, 1:3}, lims)` for log-log scatter.
  - `ratio_hist_data(table, component, ref=None)` — `dict(edges, centers,
    counts[df per algorithm])` over `RATIO_EDGES` (reuses `metrics.ratio_hist`).
  - `residual_spectra(spectral, scalar, obs_id)` — per-algorithm
    `dict(wave, residual=Rrs_obs−Rrs_model, chi2_nu)` (uses the persisted
    `Rrs_obs` component from Task 4).
  - `corner_data(chain_file)` — flattens the saved chain NPZ
    `(nsteps,nwalkers,nparam)`→`(N,nparam)`; `dict(samples, labels, Chl, Y)`.
  - `dbic_cdf_data(scalar, a, b, by=None)` — thin wrapper over
    `metrics.dbic_cdf` (stratifiable).
- **Decisions (flagged Q&A #14–16):** Taylor/Target take an explicit
  `component` (+optional `ref` wavelength, matched via `metrics._nearest_within`)
  and compute in **log10 space**; `corner_data` labels are generic (`p0..`)
  because the NPZ has no `pnames`; scatter guides are 1:1/3:1/1:3.
- Tier-1 tests [`ioptics/tests/test_diagnostics.py`](../ioptics/tests/test_diagnostics.py):
  perfect + 2×-offset cases give known Taylor (corr 1, crmsd 0), Target
  (bias log10 2), scatter (y==x, lims, guide lines), ratio buckets (idx 4 & 6),
  residuals (−0.001, 0), corner shape `(40,3)`, ΔBIC `frac_favor_a=2/3`.
- Tests: `7 passed` for the file; full suite `132 passed, 12 skipped`
  (`$OS_COLOR` unset). `ioptics.diagnostics` is autodoc'd.

### Stage 4 — Task 6: tests (consolidation) + `pnames` persistence (2026-06-30)

- **Folded Q&A #15 (persist `pnames`):** `io.save_chain(..., pnames=None)` now
  stores the fit parameter names (chain-column order) in the chain NPZ;
  `run._run_mcmc_serial` passes `list(res.params)`; `diagnostics.corner_data`
  uses them for `labels` (generic `p0..` fallback when absent). #14/#16 confirmed
  — no change.
- **Consolidated Tier-1** (already broad across `test_metrics.py` +
  `test_diagnostics.py`): added `test_compute_parquet_roundtrip` — re-reads the
  three written parquet files, checks schema and that **ΔBIC + wins are
  populated** (the Stage-4 exit criterion at the persistence level). Split the
  corner test into generic-labels vs persisted-`pnames` cases.
- **Tier-2 `@needs_l23`** `test_compute_over_real_sweep_l23`: `run.run_sweep`
  (tiny χ², 4 obs) → `metrics.compute`; asserts the three files exist, both
  algorithms scored, and the ΔBIC contest is non-empty. Verified locally **with**
  L23 data (passes).
- **Stale-assertion fixes from the Task-4 `Rrs_obs` component** (7 components
  now): `test_sweep.py` (×2, +`Rrs_obs` in the set, +`pnames` size check on
  saved chains) and `test_micro.py` (`2 * 7 * nwave`). `test_run.py:100` left
  as-is — it checks `result.components` (model dict), which correctly excludes
  the io-added `Rrs_obs`.
- **Exit criterion met:** `metrics.compute(sweep_id)` emits
  `metrics_{spectral,scalar,pairwise}.parquet`; primitives match hand-computed
  toy `(M,O)` values; `expb_pow`-vs-`giop` ΔBIC and wins populated — all Tier-1,
  confirmed Tier-2 on a real sweep.
- Tests: full suite **`134 passed, 13 skipped`** (`$OS_COLOR` unset,
  CI-equivalent) and **`147 passed`** with `$OS_COLOR` set (all Tier-2 run).

### Stage 4 — PR Task 1: review + post + CI investigation (2026-06-30)

- **Reviewed PR [#7](https://github.com/ocean-colour/IOPtics/pull/7)** (`stage-3`
  → `main`, "Stage 4") and posted a **COMMENTED** review (no self-approve, per
  the PR-workflow convention) summarizing scope, status checks, and caveats.
- **CI investigation — green, no fixes needed.** The CI workflow
  (`.github/workflows/ci.yml`) runs Tier-1 `pytest -q` on **py3.12 and py3.14**
  only (deliberately light — no sweeps/reports/docs, no coverage floor, no
  fail-on-warning). Both matrix jobs **pass** on the PR head (`7483a9c`). The
  Tier-2 tests skip on the runner (no `$OS_COLOR`), as designed.
- **Extra quality gate checked locally:** `sphinx-build -W` over `docs/source`
  **builds clean** (no warnings) — the new `metrics`/`diagnostics` public APIs
  are autodoc'd and RST-clean. (`docs` build is *not* part of CI; verified per
  the Conventions note about keeping `-W` green.)
- **Local suite:** `134 passed, 13 skipped` (no `$OS_COLOR`); `147 passed` with
  the data tree.
- **Flagged (Q&A #18):** PR base is `main` while a `develop` branch exists and
  the convention had stage PRs target `develop` — left for JXP to decide (did
  not retarget). No code changes made in this task.

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

## Logs

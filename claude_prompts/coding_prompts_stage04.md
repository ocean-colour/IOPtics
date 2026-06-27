# Code IOPtics — Stage 4: Metrics & diagnostics

## Goal

Score the sweep uniformly. **Exit criterion:** `metrics.compute(sweep_id)` emits
`metrics_{spectral,scalar,pairwise}.parquet` for the Stage-3 L23 sweep; the
primitives match hand-computed values on toy `(M,O)` arrays; `expb_pow` vs `giop`
ΔBIC and wins are populated.

Implements **Metrics & diagnostics** and the **Staged plan / Stage 4** of
`docs/design/IOPtics_implementation.md`. One prompt per module/concern.

## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- `metrics`/`diagnostics` are **pure table-in/table-out** — no BING/ocpy imports,
  no re-fitting. All accuracy metrics are log10 / multiplicative.

## Context

- `docs/design/IOPtics_implementation.md` — §Metrics & diagnostics (§1 accuracy,
  §2 Rrs closure + dual-sided window/QC, §3 ΔBIC, §4 coverage + detection, §5
  wins/rankings; non-uniformity intersection rule + coverage accounting; ±3 nm
  ref-band match; Chl strata; `diagnostics` figure-data functions).
- Inputs: `runs/<sweep_id>/results_{spectral,scalar}.parquet`, `chains/`.

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

2. **`metrics` §2 + §3.** Rrs closure (linear χ², log-space MAE/bias, dual-sided
   window → `fit_noise`, `Rrs_MAE>0.25` QC) reading χ²ᵥ/AIC/BIC from
   `results_scalar`; `delta_bic`/`dbic_cdf`. Tier-1. Q&A. Log.

3. **`metrics` §4 + §5.** `coverage` at 68/95% + `detection` (Nσ/upper-limit);
   `wins` (`abs_log_err`, provisional) + `rankings`. Tier-1. Q&A. Log.

4. **`metrics.compute`.** Orchestrate the above into
   `metrics_{spectral,scalar,pairwise}.parquet`: the **intersection rule** (score
   only non-NaN `(M,O)`, record `n`+coverage), ±3 nm **ref-band match** with
   `ref_match`, Chl **strata** (oligo/meso/eutro), GLORIA `caveat` flag. Tier-1 on
   a toy results table; Tier-2 `@needs_l23` on the Stage-3 sweep. Q&A. Log.

5. **`diagnostics`.** `taylor_stats`/`target_stats`/`scatter_data`/
   `ratio_hist_data`/`residual_spectra`/`corner_data`(loads NPZ)/`dbic_cdf_data`,
   returning arrays only. Tier-1 shapes + known values. Q&A. Log.

6. **Tests.** Consolidate Tier-1 metric/diagnostic checks; a Tier-2 `compute` over
   the real Stage-3 sweep asserting populated ΔBIC + wins for expb_pow vs giop.
   Q&A. Log.

### Q&A

## Logs

# IOPtics — First Sweep & Report (L23: `expb_pow` vs `giop`)

## Goal

With Stages 0–5 complete, produce the project's **first real report**: run the
canonical in-tandem L23 sweep end to end (run → metrics → report → leaderboard)
and publish a provenance-stamped **cross-algorithm** page into the docs site.

**Exit criterion:** `docs/source/reports/expb_giop_L23_v1/cross_algorithm.rst`
(+ its PNG/CSV/Bokeh assets) is committed and renders under `sphinx-build -W`;
the leaderboard landing ranks `expb_pow` vs `giop`; the heavy artifacts
(`results_*`/`metrics_*` parquet, `chains/`) live under `$OS_COLOR/IOPtics/runs/`
and are **not** committed.

This executes the sweep the architecture was built for — no new package code
(save any small run-ergonomics tweak decided in Q&A). Driver:
`ioptics/runs/prototypes/expb_giop/build_v1.py` (sequential stages `1`=run,
`2`=metrics, `3`=report), config `run_v1.yaml`.

## Conventions

- `ocean14`; JXP runs git; after each step run `pytest -q` where relevant, Q&A, Log.
- Run via the env interpreter directly
  (`/home/xavier/miniforge3/envs/ocean14/bin/python …`); `conda activate` fails
  non-interactively. This is a **Tier-2** operation — it needs the `$OS_COLOR`
  data tree (L23) mounted; do **not** unset `$OS_COLOR` here.
- `report`/`plotting` need matplotlib (`Agg` is fine headless) + Bokeh + Sphinx.

## Context

- **Config** (`run_v1.yaml`): `sweep_id: expb_giop_L23_v1`, `datasets: [L23]`,
  `noise_model: pace`, `algorithms: [expb_pow (χ²), giop (mcmc)]`,
  `fit_method: chisq`, `mcmc_subset: 200`, `seed: 1234`.
- **Driver** (`build_v1.py`, `main(flg)`): `1` → `run.run_sweep(cfg)`; `2` →
  `metrics.compute(cfg.sweep_id)`; `3` → `report.standard.build(sweep_id,
  kind='cross_algorithm')` + `leaderboard.update()` +
  `rst.write_leaderboard_landing(...)`.
- **Artifact split (design Q22):** the `.rst` page + lightweight display assets
  (figure PNGs, `interactive_scatter.html`, CSV tables) are copied into
  `docs/source/reports/<sweep_id>/` and committed; parquet/chains stay in `runs/`.
- **Leaderboard** lands at `$OS_COLOR/IOPtics/leaderboard.parquet` (runs-root
  sibling) and is not committed.

### ⚠ Read before running — two real gotchas

- **`build_v1.main(1)` runs the FULL L23 dataset, serial, fail-fast.** It calls
  `run.run_sweep(cfg)` with the defaults `n_cores=1, strict=True` and **no
  `obs_ids`** — i.e. every L23 spectrum, χ² for both algorithms + **200 giop MCMC
  fits**, on one core. That is long, and `strict=True` means a **single** failed
  fit aborts the whole sweep (the known run-error-policy TODO). Decide the run
  knobs in Q&A **before** step 1.
- **Getting the knobs in.** `build_v1.main` doesn't expose `obs_ids`/`n_cores`/
  `strict`. Options (Q&A #1): (a) call the stages directly in a short snippet
  (`run.run_sweep(cfg, obs_ids=…, n_cores=…, strict=…)`, then `metrics.compute`,
  then `report.standard.build`+`leaderboard`); or (b) extend `build_v1.main` to
  accept `n_cores`/`strict`/`obs_ids` (tiny, reusable change).

## Decisions — answer before step 1 (Q&A)

D1. **Run scope.** Full L23 (all spectra) for the first report, or a bounded
    `obs_ids` subset (e.g. first N + a few per trophic bin) for a fast first
    pass? (Full is the real deliverable but slow; bounded validates the pipeline
    end-to-end quickly.)
>A. Let's do a short test run of 20 spectra first and then the full run.  Both will be in this first sweep.

D2. **Parallelism.** `n_cores` for the χ² population (`run_batch` pools when
    `n_cores>1`; the 200-spectrum MCMC subset is serial regardless). What core
    count is safe on this box?
>A. Let's use 10 cores.

D3. **Error policy.** Flip to `strict=False` (robust: failed fits become
    `status='fit_failed'` rows + reduced coverage) for this production sweep, per
    the run-error-policy TODO? Recommended for a full run.
>A. Yes, let's use strict=False for the first sweep.

D4. **MCMC subset.** Keep `mcmc_subset: 200`, or trim for the first pass (the
    subset feeds coverage/corner diagnostics; corner plots are omitted from the
    standard page for now).
>A. Let's keep the 200 MCMC subset for the first sweep.

D5. **Publish.** After review, commit the report page + assets into
    `docs/source/reports/` (and link the landing) now, or hold for a Read the
    Docs wiring pass?
>A. Yes, after review, we can commit the report page + assets 

## Q&A (round 2 — resolve before step 1)

Your D1–D5 answers are clear; three operational points need pinning down first
(the "20 then full, both in this first sweep" plan mostly):

Q6. **Sweep IDs (avoid clobber).** `io.write_results` overwrites a sweep dir, so
    the 20-spectrum smoke and the full run can't share `sweep_id` or the full run
    erases the test. Plan: run the smoke under a throwaway
    `sweep_id='expb_giop_L23_test20'` (kept under `runs/`, **not** committed),
    and produce the **committed** report from the full `expb_giop_L23_v1`. OK?
>A. Yes, let's run the smoke under a throwaway sweep_id='expb_giop_L23_test20' and produce the committed report from the full expb_giop_L23_v1.

Q7. **Getting `n_cores`/`strict`/`obs_ids` into the driver.** `build_v1.main`
    doesn't expose them. I recommend a small, reusable tweak — extend
    `build_v1.main(flg, *, n_cores=1, strict=True, obs_ids=None)` and thread them
    into `run.run_sweep(...)` (also helps Stage-6 `build_v2`). Or should I run
    the stages via a one-off snippet (no code change) for this first sweep?
>A. Yes, extend build_v1.main(flg, *, n_cores=1, strict=True, obs_ids=None) and thread them into run.run_sweep(...)

Q8. **Smoke-run cost + report.** For the 20-spectrum smoke, trim its MCMC (e.g.
    `mcmc_subset=5`) so it finishes fast, and render its stage-3 report to a
    **throwaway `docs_root`** (review-only, not committed)? The full run keeps
    `mcmc_subset=200` (D4) and writes stage-3 into the real
    `docs/source/reports/` (D5). Note: even at `n_cores=10`, the full run's
    **200 MCMC fits are serial** (only χ² is pooled) — so that's the long pole;
    flag if you'd rather cap MCMC `nsteps` or the subset for a first full run.
>A. Yes, let's trim the MCMC subset to 5 for the smoke run and render the report to a throwaway docs_root.

Q9. **Execution shape (last check).** Q7's `build_v1.main` extension only adds
    `n_cores`/`strict`/`obs_ids` — it still reads `run_v1.yaml`'s
    `sweep_id=expb_giop_L23_v1` + `mcmc_subset=200`. The **smoke** needs a
    *different* `sweep_id` (`expb_giop_L23_test20`) **and** `mcmc_subset=5`, which
    `build_v1.main` can't override — so the plan is:
    - **Smoke** → a direct snippet: `cfg = config.loads(<test20, mcmc_subset:5,
      L23, expb_pow + giop-mcmc>)`; `run.run_sweep(cfg, obs_ids=range(20),
      n_cores=10, strict=False)` → `metrics.compute` → `report.standard.build(
      docs_root=<tmp>)` + `leaderboard.update(out=<tmp>)` (review-only, not
      committed).
    - **Full** → extended `build_v1.main(1, n_cores=10, strict=False)` then
      `main(2)` then `main(3)` (uses `run_v1.yaml`; writes into the real
      `docs/source/reports/`).
    Good to proceed on that basis?
>A. Yes, let's proceed on that basis.

## Prompts / Steps

### -1. Q&A

1. I have answered your Q&A.  Please read my responses and ask additional questions if you need to.  Log your work in the Logs section below.
2. I have answered your Q&A.  Please read my responses and ask additional questions if you need to.  Log your work in the Logs section below.
3. I have answered your Q&A.  Please read my responses and modify the prompts below as needed.  Log your work in the Logs section below.

**Confirmed plan (D1–D5, Q6–Q9):** two runs this session — a **smoke** (throwaway
`expb_giop_L23_test20`, 20 obs, `mcmc_subset=5`, review-only report to a tmp
`docs_root`) to validate the pipeline, then the **full** deliverable
(`expb_giop_L23_v1`, all L23, `mcmc_subset=200`, report into the real docs tree).
Both use `n_cores=10`, `strict=False`. The smoke runs via a direct snippet; the
full run via the extended `build_v1.main`.

### 0. Preflight
Environment checks only — **no package changes**: `$OS_COLOR` set and L23
resolvable (`@needs_l23` probe passes); `pytest -q` green **with data**; Sphinx +
Bokeh importable; **both** target sweep dirs clean/absent under
`$OS_COLOR/IOPtics/runs/` (`expb_giop_L23_test20`, `expb_giop_L23_v1`); note the
L23 spectrum count (sets full-run expectations). Report readiness. Q&A. Log.

### 1. Driver tweak + SMOKE run (`expb_giop_L23_test20`, 20 obs)
First the sanctioned run-ergonomics tweak (Q7): extend
`build_v1.main(flg, *, n_cores=1, strict=True, obs_ids=None)` to thread those into
`run.run_sweep(...)` (keep defaults backward-compatible; add/adjust the Tier-1
dispatch test). Then run the **smoke** via a direct snippet (Q8/Q9): `cfg =
config.loads(<sweep_id=expb_giop_L23_test20, datasets:[L23], noise:pace,
expb_pow + giop-mcmc, mcmc_subset:5, seed:1234>)`; `run.run_sweep(cfg,
obs_ids=range(20), n_cores=10, strict=False)`. **Verify:** results + provenance +
`chains/` (≤5 giop MCMC) written under `test20`; `status` breakdown (ok vs
fit_failed) and χ²ᵥ look sane. Report counts. Q&A. Log.

### 2. SMOKE metrics + report (review-only, not committed)
`metrics.compute('expb_giop_L23_test20')`; then `report.standard.build(
'expb_giop_L23_test20', kind='cross_algorithm', docs_root=<tmp>)` +
`leaderboard.update(out=<tmp>)` + `rst.write_leaderboard_landing(<tmp>/…)`, and
`sphinx-build -W` the tmp tree. **Verify** the whole pipeline runs clean end to
end and the page renders. This validates everything before the long full run;
the tmp `docs_root` is discarded (nothing committed). Q&A. Log.

### 3. FULL run — Stage 1 (`expb_giop_L23_v1`, all L23)
Extended driver: `build_v1.main(1, n_cores=10, strict=False)` (uses
`run_v1.yaml`: all L23, `mcmc_subset=200`). **Heads-up:** the 200 MCMC fits are
serial — expect this to be the long pole. **Verify:**
`results_{spectral,scalar}.parquet` + `provenance.yaml` + `chains/` (200 giop
MCMC); `status` breakdown + χ²ᵥ distribution sane. Report counts + wall time.
Q&A. Log.

### 4. FULL — Stage 2 metrics + Stage 3 report/leaderboard
`build_v1.main(2)` then `build_v1.main(3)`. **Verify (metrics):** the three
`metrics_*.parquet`; spot-check χ² ref-band accuracy for `a`/`bb` at 440/555, the
ΔBIC `expb_pow`-vs-`giop` contest (`frac_favor_*`), wins. **Verify (report):**
`docs/source/reports/expb_giop_L23_v1/cross_algorithm.rst` + copied
PNG/CSV/`interactive_scatter.html`; `$OS_COLOR/IOPtics/leaderboard.parquet`
folded; the landing has the leaderboard block + globs the page. Report headline
numbers. Q&A. Log.

### 5. Build, review & commit the full report (per D5)
`sphinx-build -W -b html docs/source docs/_build` — must be clean. Eyeball the
rendered `expb_giop_L23_v1` page: provenance header, scatter/Taylor/Target/ΔBIC
figures, accuracy/QC tables, interactive scatter, leaderboard ranking — flag
anything off (empty panels, degenerate strata, wrong ranking). Then **JXP
commits** `docs/source/reports/expb_giop_L23_v1/` + the updated
`reports/index.rst` landing (NOT the `runs/` parquet/chains or the `test20`
smoke). Confirm the artifact split holds (no heavy data staged). Log the commit
scope + the provenance versions the page carries.

### Logs

### First sweep — step -1: read Q&A answers (2026-07-03)

- Read D1–D5. Decisions captured: **D1** smoke run of 20 spectra, then the full
  run (both this session); **D2** `n_cores=10`; **D3** `strict=False`; **D4**
  keep `mcmc_subset=200`; **D5** commit the report page + assets after review.
- Raised three round-2 questions (Q6–Q8) that gate step 1, since "20 then full,
  both in this first sweep" needs disambiguation and the chosen knobs aren't
  exposed by `build_v1.main`:
  - **Q6** — run the smoke under a throwaway `sweep_id` (`expb_giop_L23_test20`)
    so the full `expb_giop_L23_v1` isn't clobbered; commit only the full run's
    report.
  - **Q7** — extend `build_v1.main` to accept `n_cores`/`strict`/`obs_ids`
    (recommended, reusable) vs a one-off snippet.
  - **Q8** — trim the smoke's MCMC + render its report to a throwaway
    `docs_root`; and a heads-up that the full run's **200 MCMC fits are serial**
    (n_cores only pools χ²) → the long pole.
- No code run yet (awaiting Q6–Q8 before step 0/1). No package changes.

### First sweep — step -1 (round 2): read Q6–Q8 answers (2026-07-03)

- Q6–Q8 answered: **Q6** smoke under `expb_giop_L23_test20`, committed report
  from full `expb_giop_L23_v1`; **Q7** extend `build_v1.main(flg, *, n_cores=1,
  strict=True, obs_ids=None)` → `run.run_sweep`; **Q8** smoke `mcmc_subset=5` +
  throwaway `docs_root`.
- One consequence flagged as **Q9**: since Q7's `build_v1.main` extension does
  **not** add `sweep_id`/`mcmc_subset` overrides, `build_v1.main` can drive the
  **full** run (from `run_v1.yaml`) but **not** the smoke (needs `test20` +
  `mcmc_subset=5`). Plan: **smoke via a direct snippet** (custom cfg, tmp
  `docs_root`, review-only); **full via extended `build_v1.main`** (1→2→3, real
  docs tree). Confirming before executing.
- Still no code run / no package changes (the `build_v1.main` extension lands in
  step 1 once Q9 is confirmed).

### First sweep — step -1 (round 3): finalize the step plan (2026-07-03)

- Q9 confirmed → **rewrote steps 0–5** to bake in the decided plan (no more
  open questions). New shape:
  - **0** preflight (checks only; note L23 count; both sweep dirs absent).
  - **1** extend `build_v1.main(flg, *, n_cores, strict, obs_ids)` (Q7 tweak +
    dispatch-test update), then **smoke** run via direct snippet
    (`expb_giop_L23_test20`, `obs_ids=range(20)`, `mcmc_subset=5`, `n_cores=10`,
    `strict=False`).
  - **2** smoke metrics + report to a **tmp `docs_root`** + `sphinx -W`
    (review-only, discarded).
  - **3** full Stage-1 via `build_v1.main(1, n_cores=10, strict=False)` (all L23,
    `mcmc_subset=200`; 200 MCMC serial = long pole).
  - **4** full `main(2)` metrics + `main(3)` report/leaderboard.
  - **5** `sphinx -W` build + review, then JXP commits only the
    `expb_giop_L23_v1` page + assets + landing (artifact split enforced).
- The only package change in the whole runbook is the `build_v1.main` signature
  extension (step 1); everything else is orchestration over existing code.
- Ready to execute from step 0. No code run yet.

### First sweep — step 0: preflight (2026-07-03)

- **Environment ready.** `$OS_COLOR` = `/home/xavier/Projects/Oceanography/data/
  Color/` (present). L23 resolvable (`Hydrolight100.nc` found); **X=1 = 3320
  spectra** (`IOP_Scenario` × 81 λ). Deps: sphinx 9.1.0, bokeh 3.9.0,
  matplotlib 3.10.9, corner 2.2.3, emcee 3.1.6.
- **Clean slate:** no runs root yet — both `expb_giop_L23_test20` and
  `expb_giop_L23_v1` absent; no `leaderboard.parquet`; `docs/source/reports/`
  holds only `index.rst`.
- **Suite green with data:** `183 passed` (`pytest -q`, `$OS_COLOR` set).
- **Full-run scale expectation:** 3320 × 2 algorithms = **6640 χ² fits** (pooled
  at `n_cores=10`) + **200 giop MCMC** (serial — the long pole). Smoke is 20 obs
  × 2 + ≤5 MCMC.
- No package changes in this step. **Ready for step 1** (driver tweak + smoke).

### First sweep — step 1: driver tweak + SMOKE run (2026-07-03)

- **Driver tweak (Q7):** extended
  `build_v1.main(flg, *, n_cores=1, strict=True, obs_ids=None)` → threaded into
  `run.run_sweep`; docstring updated; the Tier-1 dispatch test now also asserts
  the stage-1 knobs reach `run_sweep`. `test_sweep.py` green (2 passed, 2 skipped
  no-data).
- **Smoke run** (`expb_giop_L23_test20`, `obs_ids=range(20)`, `n_cores=10`,
  `strict=False`, `mcmc_subset=5`; via `/tmp/run_smoke.py` — a **file**, since
  multiprocessing can't import `__main__` from a heredoc):
  - `n_results=45` = 20 `expb_pow` χ² + 20 `giop` χ² + 5 `giop` MCMC; **all 45
    `status='ok'`** (none failed).
  - χ²ᵥ over the 40 χ² fits: mean **1.12**, median 1.06, range 0.83–1.57
    (healthy, ≈1). Spectral components: `a/bb/a_ph/a_dg/bb_p` + `Rrs_model` +
    `Rrs_obs`; 5 MCMC chains written.
  - Wrote `results_{spectral,scalar}.parquet` + `provenance.yaml` + `chains/`
    under `runs/expb_giop_L23_test20/` (not committed).
- **⚠ Full-run cost finding (matters for step 3).** giop MCMC default is
  **~40 000 steps/fit**; the 5-fit smoke took **~4.5 min** (χ² is negligible; the
  MCMC dominates). The full run's **200 serial MCMC fits** therefore project to
  **≈2–3 hours**. Options to raise before step 3: run the full sweep in the
  **background**; and/or (revisit D4) cut MCMC `nsteps` or the subset for this
  first full pass. χ² over all 3320×2 is quick (pooled at 10 cores).
- **Ready for step 2** (smoke metrics + report to a tmp docs_root, review-only).

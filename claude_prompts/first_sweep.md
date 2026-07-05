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
  `noise_model: pace`, `seed: 1234`. **`expb_pow` = standard 5-parameter BING**
  (ExpBricaud a_nw + Pow bb_nw; `Adg, Sdg, Aph, Bnw, beta`, k=5) — **MCMC-fit on
  the `mcmc_subset` (1d)**, and χ²-fit over all records like every algorithm;
  **`giop`** = k=3 contrast (GIOP a_nw + Lee bb_nw; `Aexp, Aph, Bnw`) — **LM/χ²
  only (1b)**. `fit_method: chisq` (sweep default → giop); `mcmc_subset: 200`
  (D4; the expb_pow spectra also MCMC-fit).
- **Driver** (`build_v1.py`, `main(flg)`): `1` → `run.run_sweep(cfg)`; `2` →
  `metrics.compute(cfg.sweep_id)`; `3` → `report.standard.build(sweep_id,
  kind='cross_algorithm')` + `leaderboard.update()` +
  `rst.write_leaderboard_landing(...)`.
- **Artifact split (design Q22):** the `.rst` page + lightweight display assets
  (figure PNGs, `interactive_scatter.html`, CSV tables) are copied into
  `docs/source/reports/<sweep_id>/` and committed; parquet/chains stay in `runs/`.
- **Leaderboard** lands at `$OS_COLOR/IOPtics/leaderboard.parquet` (runs-root
  sibling) and is not committed.

### ⚠ Read before running — the run knobs

- **Error policy / fail-fast.** By default `run.run_sweep` is `strict=True` — a
  **single** failed fit aborts the whole sweep (the run-error-policy TODO). For
  the first full sweep use `strict=False` (D3): failures become
  `status='fit_failed'` rows + reduced coverage.
- **Cost (post-1d): χ² fast, MCMC is the long pole.** χ² over all 3320 × 2 is
  minutes (pooled at `n_cores`). But `expb_pow` (BING) is MCMC-fit on the
  **200-spectrum subset**, and those MCMC fits are **serial** (~40 000 steps
  each). The 5-fit smoke took ~5 min → the full **200 MCMC fits project to
  ≈3 hours**. Plan to run the full sweep in the **background** (step 3).
- **Getting the knobs in.** `build_v1.main` now accepts
  `n_cores`/`strict`/`obs_ids` (step-1 tweak) and threads them into
  `run.run_sweep`.

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

Q10. **§2 Rrs-closure QC artifact (found in the step-2 smoke).** The smoke's
    report shows `frac_qc_fail=1.0` for **both** algorithms even though χ²ᵥ≈1
    (good fits). Cause: the §2 Rrs closure reuses the **log-space multiplicative**
    `mae` (fine for strictly-positive IOPs), but **Rrs crosses zero in the red**
    — L23 Rrs at >600 nm is ~0 and goes **negative** under pace noise. So the
    multiplicative MAE is dominated by the red tail (obs0: all-band 0.34 vs
    ≤600 nm 0.13), tripping `RRS_QC_MAX=0.25` spuriously. The committed report's
    QC table would be misleading. Options (metrics-layer / Stage-4 fix — pick):
    (a) base the QC flag on **χ²ᵥ** (inverse-variance weighted, already ≈1)
    instead of the multiplicative Rrs MAE; (b) compute the Rrs closure MAE only
    over bands with `Rrs_obs` above a floor / positive SNR; (c) use a
    noise-relative (χ²-like) Rrs residual rather than log-space for §2.
    Recommend (a) or (b). Resolve before committing the full report (step 5); the
    full **run** (step 3) is unaffected and can proceed meanwhile.
>A. Let's use option (a).

Q11. **Exposing the report on RTD — the Bokeh-iframe gotcha (step 2c).** RTD is
    already wired (`.readthedocs.yaml` builds `docs/source/conf.py` on push,
    `fail_on_warning: false`, installs the package + `docs/requirements.txt`,
    heavy deps mocked). To publish a report you just generate it into the **real**
    `docs/source/reports/<sweep_id>/` (not a tmp `docs_root`), commit the page +
    assets + the updated `reports/index.rst`, and push — RTD's glob toctree picks
    it up. **But** I verified sphinx copies the figure **PNGs** (→ `_images/`) yet
    **not** the standalone `interactive_scatter.html`, so the `report.rst`
    `<iframe src="interactive_scatter.html">` would **404** on RTD (static panels
    fine; interactive figure broken). Fix options (Stage-5 `report` change):
    (a) **inline-embed** the Bokeh figure with `bokeh.embed.components` + a
    BokehJS CDN `<script>` via `.. raw:: html` (figure lives in the page; no
    separate file/iframe; compatible with the mocked-bokeh RTD build since the
    script/div are pre-generated); or (b) keep the standalone file + iframe and
    make sphinx copy it (`html_extra_path`, writing the html to a copied
    location). Recommend **(a)**. Which — and shall I implement it before we
    commit the smoke report?
>A. Let's use option (a).

Q12. **Interactive scatter bakes the whole point cloud (found regenerating the
    smoke, step 2e).** The inline Bokeh embed serializes **every** scatter point
    into the page: the 20-obs smoke = **31,200 points → a 2.5 MB
    `cross_algorithm.rst`**; the full 3320-obs run projects to **~5.2M points →
    ~415 MB inline** — untenable to commit / serve. (The old standalone
    `file_html` had the same all-points payload.) Fix before committing any real
    report (recommend): **downsample** the interactive scatter to ~2–5k points
    (stratified by algorithm/component, or per (component,ref-λ)); optionally
    hexbin/aggregate. A small `report.bokeh` change. Which cap/strategy — and
    shall I implement it before you push the smoke? (Static PNG scatters are
    unaffected — they already summarize the full population.)
>A. Yes, downsample the interactive scatter

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

**Confirmed plan (D1–D5, Q6–Q9, 1b–1d):** two runs this session — a **smoke**
(throwaway `expb_giop_L23_test20`, 20 obs, `mcmc_subset=5`, review-only report to
a tmp `docs_root`) to validate the pipeline, then the **full** deliverable
(`expb_giop_L23_v1`, all L23, `mcmc_subset=200`, report into the real docs tree).
Both use `n_cores=10`, `strict=False`; **`expb_pow` (BING) is MCMC-fit on the
subset + χ² over all, `giop` is LM/χ² only**. The smoke runs via a direct
snippet; the full run via the extended `build_v1.main` (its 200 serial MCMC fits
are the long pole → run in the background).

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
dispatch test). Then run the **smoke** via a direct snippet (Q8/Q9, 1b–1d): `cfg =
config.loads(<sweep_id=expb_giop_L23_test20, datasets:[L23], noise:pace,
expb_pow(fit_method:mcmc) + giop, fit_method:chisq, mcmc_subset:5, seed:1234>)`;
`run.run_sweep(cfg, obs_ids=range(20), n_cores=10, strict=False)`. **Verify:**
results + provenance + `chains/` (5 expb_pow MCMC) under `test20`; `giop` is
χ²-only; `status` breakdown (ok vs fit_failed) and χ²ᵥ look sane. Report counts.
Q&A. Log.

### 1b. Modifications on GIOP MCMC
We should not be doing MCMC analysis on GIOP, only LM.  Please modify the code and prompts to reflect this. If you have any questions, write them in the Q&A section below. Log your work.

### 1c. BING
I am now worried that the first sweep doesn't include a standard 5-parameter BING run.  Does it?  if not, it needs to.  If you have any questions, write them in the Q&A section below. Log your work.

### 1d. BING MCMC
Ok, and does the sweep use MCMC for BING?  It should.  Log your work

### 2. SMOKE metrics + report (review-only, not committed)
`metrics.compute('expb_giop_L23_test20')`; then `report.standard.build(
'expb_giop_L23_test20', kind='cross_algorithm', docs_root=<tmp>)` +
`leaderboard.update(out=<tmp>)` + `rst.write_leaderboard_landing(<tmp>/…)`, and
`sphinx-build -W` the tmp tree. **Verify** the whole pipeline runs clean end to
end and the page renders. This validates everything before the long full run;
the tmp `docs_root` is discarded (nothing committed). Q&A. Log.

### 2b. SMOKE Q&A
I have answered your Q10, please modify the code as needed.

### 2c. SMOKE + expose
I wish to expose the SMOKE report on RTD before continuing on to the full run.  How do I do so?

### 2d. SMOKE
I have answered Q11.  Read it and modify the code accordingly.  Log your work. 

### 2e. Rerun the SMOKE
Rerun the SMOKE test and tell me what to push to expose on RTD.  Log your work.

### 2f. Another Rerun the SMOKE
Ok, see my answer to Q12 and modify the code accordingly.  Log your work.

### 2g. Improve docs
The Report has been exposed on RTD and looks very good.  Please make these improvements:
- Add significant text explaining what was done and why
- Add a separate page that details each of the IOP models examined
- Add text describing the Leaderboard
- Add text describing each figure presented
- Add a separate page that defines each dataset examined
- Use a different Sphinx style than the default on RTD

### 2h. Improve docs
That is excellent, but not quite there yet.  Please:

- Use language that a geoscientist, but not ocean color expert, will understand.  This includes the statistcal conecpts
- Explain the models in greater detail.  Include equations where possible (draw on the BING paper)
- White text on black is rather.. boring.  This is ocean color!  Do better
- Add more, fixed graphics.  On models and datasets.  If you need to create PNGs with Python, save the scripts in docs/

### 3a. FULL run — Stage 1 prep
I wish to run the FULL run on my workstation.  Can you generate a script that I can execute on it with an `at` command to run in the background?  Call it `full_run.src`.  In essence, this will replace the 3b prompt below.  

### 3b. FULL run — Stage 1 (`expb_giop_L23_v1`, all L23)
Extended driver: `build_v1.main(1, n_cores=10, strict=False)` (uses
`run_v1.yaml`: all 3320 L23 spectra; χ² for both + **expb_pow MCMC on the
200-subset**). χ² is quick (pooled at 10 cores); the **200 serial MCMC fits are
the long pole (~3 h)** — **run in the background** (a script file, not a heredoc —
multiprocessing needs an importable `__main__`). **Verify:**
`results_{spectral,scalar}.parquet` + `provenance.yaml` + `chains/` (200 expb_pow
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

### First sweep — step 1b: GIOP is LM-only, no MCMC (2026-07-03)

- **Decision:** neither algorithm is MCMC-fit in this sweep — `expb_pow` and
  `giop` are both **least-squares (LM/χ²)**. (`AlgorithmSpec.fit_method` already
  defaults to `chisq`; only `run_v1.yaml` had opted `giop` into MCMC.)
- **Code:** edited `run_v1.yaml` → `algorithms: [expb_pow, giop]`,
  `fit_method: chisq`, `mcmc_subset: 0`. No engine change — `run_sweep` only runs
  MCMC for algorithms whose effective `fit_method=='mcmc'` gated by
  `mcmc_subset`, so this is now a pure χ² sweep (no `chains/`). The general MCMC
  machinery + its Tier-2 tests are left intact (a capability for future
  algorithms/sweeps, e.g. Stage 6).
- **Prompts:** updated the Config bullet, the "run knobs" box (dropped the
  "200 MCMC serial" long-pole; the χ²-only sweep is minutes), the confirmed-plan
  block, and steps 1/3 (no `mcmc_subset`, no `chains/`).
- **Re-ran the smoke χ²-only** (`test20`, 20 obs, 10 cores, `strict=False`):
  **40 results** (20 `expb_pow` + 20 `giop`, all `chisq`), **all `ok`**, χ²ᵥ
  mean 1.12 / median 1.06 / range 0.83–1.57, no MCMC rows — in **~8 s** (vs
  ~4.5 min with MCMC). `test_sweep.py` still green; `run_v1.yaml` loads as
  χ²-only (`mcmc_subset=0`).
- **Consequence noted:** the standard `cross_algorithm` report is unaffected —
  coverage 68/95 comes from the χ² covariance bounds; corner plots (chains-only)
  were already omitted. No coverage/diagnostic loss for the first report.
- **Supersedes the step-1 "≈2–3 h full run" projection:** the full χ²-only run
  over 3320×2 is now minutes. Q&A: flag if a *future* sweep should include an
  MCMC contestant (for corner/degeneracy diagnostics) — not this one.
- **Ready for step 2** (smoke metrics + report → tmp docs_root, review-only).

### First sweep — step 1c: standard 5-parameter BING is included (2026-07-03)

- **Answer: yes.** `expb_pow` **is** the standard 5-parameter BING — verified by
  building its models: pnames = **`[Adg, Sdg, Aph, Bnw, beta]`** (k=5;
  `ExpBricaud` a_nw = a_dg amplitude + slope + a_ph amplitude, `Pow` bb_nw =
  amplitude + slope). `giop` is the intended k=3 contrast (`[Aexp, Aph, Bnw]`;
  `GIOP` a_nw + `Lee` bb_nw). The smoke's scalar table agrees (k = 5 vs 3).
- **No code change needed** — the sweep already contains the standard BING run.
  Added a clarifying note to the Config bullet naming `expb_pow` as the 5-param
  BING (and `giop` as the k=3 contrast) so it's unambiguous.
- **Ready for step 2** (unchanged).

### First sweep — step 1d: BING (expb_pow) is MCMC-fit (2026-07-03)

- **Decision:** the standard 5-param BING (`expb_pow`) **should use MCMC** —
  refines 1b (which correctly kept `giop` LM-only). Final policy: `expb_pow` →
  χ² over all + **MCMC on the `mcmc_subset`**; `giop` → LM/χ² only.
- **Code:** `run_v1.yaml` → `expb_pow` opts `fit_method: mcmc`, `giop` plain
  (χ² default), `mcmc_subset: 200` restored (D4). No engine change (`run_sweep`
  already χ²-fits every algorithm + adds MCMC for the mcmc-opted one).
- **Prompts:** updated the Config bullet, the run-knobs "cost" box (**MCMC long
  pole is back** — ~3 h for 200 serial expb_pow MCMC → run full in background),
  the confirmed-plan block, and steps 1/3.
- **Re-ran the smoke** (`test20`, 20 obs, subset 5, 10 cores, `strict=False`):
  **45 results** — `expb_pow` 20 χ² + **5 MCMC**, `giop` 20 χ²; all `ok`; χ²ᵥ
  mean 1.12; **5 chain files** written for expb_pow. ~5.3 min (the 5 MCMC
  dominate). `test_sweep.py` green; `run_v1.yaml` loads as
  `expb_pow→mcmc, giop→chisq, mcmc_subset=200`.
- **Full-run projection restored:** χ² minutes + **200 expb_pow MCMC serial ≈
  ~3 h** → step 3 runs the full sweep in the background.
- **Ready for step 2** (smoke metrics + report → tmp docs_root, review-only).

### First sweep — step 2: SMOKE metrics + report (review-only) (2026-07-03)

- Ran `metrics.compute` → `report.standard.build(kind='cross_algorithm',
  docs_root=<tmp>)` → `leaderboard.update(out=<tmp>)` +
  `write_leaderboard_landing` → `sphinx-build -W` on `test20`, via
  `/tmp/smoke_report.py`. **Whole pipeline clean end-to-end in ~3.7 s;
  `sphinx -W` rc=0; the page HTML built.** (tmp docs discarded — nothing
  committed.)
- Tables produced: metrics_spectral 3645 / scalar 126 / pairwise 63 rows;
  report assets = scatter_a_440 / scatter_bb_555 / taylor_a / target_a /
  dbic_cdf PNGs + accuracy/qc CSVs + `interactive_scatter.html`; leaderboard 60
  rows (both algos).
- **Content is coherent** (20-obs smoke): `giop` beats `expb_pow` on a(440/443)
  accuracy (mae 0.062 vs 0.109; wins 0.85 vs 0.15) but is worse at bb(670)
  (0.117 vs 0.079, biased low, coverage68 0.10); ΔBIC median +3.1 → BIC mildly
  favors the simpler `giop` (frac_favor_a=0.4). χ²ᵥ medians ≈1.06/1.09.
- **⚠ Finding → Q10 (§2 Rrs-closure QC artifact).** `frac_qc_fail=1.0` for both
  despite χ²ᵥ≈1. Diagnosed: the §2 closure reuses the **log-space multiplicative
  `mae`**, but **Rrs crosses zero in the red** (L23 >600 nm ≈0, negative under
  pace noise), so the MAE blows up on the red tail (obs0: all-band 0.34 vs
  ≤600 nm 0.13). The QC-fail flag mis-fires. Raised **Q10** with fix options
  (χ²ᵥ-based QC / band-floored Rrs MAE / noise-relative residual) — a Stage-4
  metrics-layer decision to resolve **before committing the full report (step
  5)**; the full **run (step 3)** is unaffected.
- No package changes in this step (diagnosis only). **Ready for step 3** (full
  run in background) — and Q10 to settle before step 4/5.

### First sweep — step 2b: §2 QC → χ²ᵥ-based (Q10a) (2026-07-03)

- **Implemented Q10 option (a)** in `metrics`: §2 closure QC now derives from
  reduced **χ²ᵥ** (noise-weighted), not the log-space multiplicative Rrs MAE.
  - Added `CHI2NU_QC_MAX = 5.0` (a fit with χ²ᵥ above this is a non-solution).
  - `_closure_rows` now emits `chi2_nu_median` + `frac_good/overfit/underfit`
    (dof-scaled band) + **`frac_qc_fail = mean(χ²ᵥ > CHI2NU_QC_MAX)`**; the
    red-band-inflated `rrs_mae`/`rrs_bias`/`frac_fit_noise` are **dropped** from
    the closure row. Removed the now-unused `_rrs_per_obs`; `compute` drops the
    `noise_floor`/`fit_noise_factor`/`rrs_qc_max` params and gains
    `chi2nu_qc_max`. (The `rrs_window`/`rrs_closure` array helpers stay — valid
    for strictly-positive Rrs — just no longer wired into `compute`.)
  - `report.tables.qc` now reports the χ²ᵥ columns (`chi2_nu_median`, `frac_good`,
    `frac_overfit`, `frac_underfit`, `frac_qc_fail`).
- **Tests updated:** `test_metrics` closure test (χ²ᵥ QC; `frac_qc_fail==0` for
  the good synthetic) + new `test_closure_qc_from_chi2nu` (2 of 4 χ²ᵥ>5 → 0.5);
  `test_report_figures.test_tables_qc` (χ²ᵥ columns, no `frac_fit_noise`). Full
  suite **169 passed, 15 skipped** (`$OS_COLOR` unset); `sphinx -W` clean.
- **Verified on real smoke data** (recomputed `test20`): `frac_qc_fail` now
  **0.0** for both (was 1.0); χ²ᵥ classification meaningful (expb_pow
  good 0.90 / underfit 0.10; giop 0.65 / 0.35). The misleading QC artifact is
  gone — **the committed report's QC table will now be trustworthy.**
- **Ready for step 3** (full run in background); Q10 resolved.

### First sweep — step 2c: how to expose the report on RTD (2026-07-03)

- **RTD is already configured** (`.readthedocs.yaml`): builds `docs/source/conf.py`
  on every push, `fail_on_warning: false`, installs the package (`pip install .`)
  + `docs/requirements.txt` (Sphinx + rtd-theme), with `bing/ocpy/bokeh` **mocked**
  in `conf.py` (autodoc-only; report pages are static RST + images). The project
  must be imported/connected on readthedocs.org for the branch to build.
- **Procedure to publish a report:** generate it into the **real** tree —
  `report.standard.build(<sweep_id>, kind='cross_algorithm')` (default
  `docs_root` = repo `docs/source`) + `leaderboard.update()` +
  `rst.write_leaderboard_landing(docs/source/reports/index.rst, render())` —
  then **commit** `docs/source/reports/<sweep_id>/` (rst + PNG + CSV + html) and
  the updated `reports/index.rst`, and **push**. The `:glob: */*` toctree already
  links the new page; RTD builds it. (This is exactly build stage `3`, but into
  the committed docs tree rather than a tmp `docs_root`.)
- **⚠ Found: the interactive Bokeh figure won't render on RTD.** Verified sphinx
  copies the figure **PNGs** (→ `_images/`) but **not** the standalone
  `interactive_scatter.html`, so the `report.rst` `<iframe>` 404s (built report
  dir contained only `cross_algorithm.html`). Static scatter/Taylor/Target/ΔBIC
  + accuracy/QC tables render fine; only the interactive scatter breaks.
- **Raised Q11** with the fix (recommend inline-embed via
  `bokeh.embed.components` + CDN, so the figure lives in the page — no separate
  file/iframe, compatible with the mocked-bokeh RTD build). **Not committed
  anything / no report written into the real tree yet** — awaiting the Q11
  decision so we don't publish a broken iframe.
- No package changes in this step (RTD-mechanics analysis + gotcha diagnosis).

### First sweep — step 2d: inline Bokeh embed for RTD (Q11a) (2026-07-03)

- **Implemented Q11 option (a)** — the interactive scatter is now **embedded
  inline** in the report page (no separate file / iframe), so it survives a
  Sphinx/RTD build:
  - `report/bokeh.py`: extracted `_scatter_layout(...)`; `interactive_scatter`
    still returns the standalone `file_html` (inline BokehJS) for a downloadable
    artifact, and a new **`scatter_embed(sweep)`** returns an HTML **fragment** —
    BokehJS **CDN** `<script>` (`CDN.render()`) + the `bokeh.embed.components`
    `<div>`/`<script>`. Pre-generated at build time, so RTD needs no Bokeh
    install (mocked), only the CDN at view time.
  - `report/rst.py`: added `bokeh_embed(fragment)` (drops the fragment into a
    `.. raw:: html` block); `bokeh_raw` (iframe) kept but no longer used by
    `standard`.
  - `report/standard.py`: the "Interactive" section now uses
    `rst.bokeh_embed(bokeh.scatter_embed(sweep))`; **no `interactive_scatter.html`
    written** into the report dir.
- **Tests:** added `test_report_bokeh.test_scatter_embed` (fragment: CDN +
  components div/script, not a full doc); updated
  `test_report_standard.test_build_cross_algorithm` (no `.html` file; inline
  `.. raw:: html`, no iframe). Full suite **170 passed, 15 skipped**
  (`$OS_COLOR` unset); `sphinx -W` clean.
- **Verified end-to-end:** built the `test20` report to a tmp Sphinx tree with
  `sphinx -W` (rc=0) — the built `cross_algorithm.html` **embeds Bokeh inline**
  (`data-root-id`, loads `cdn.bokeh.org`), **no broken `interactive_scatter.html`
  reference**. The interactive figure will render on RTD.
- **Not written into the real docs tree / not committed yet** — the smoke report
  is now RTD-ready; next action (on your go): generate it into
  `docs/source/reports/expb_giop_L23_test20/`, `sphinx -W`, then you commit +
  push (RTD builds it). No git run (JXP runs git).

### First sweep — step 2e: regenerate smoke into real docs; push set (2026-07-03)

- Regenerated the smoke report into the **real** tree (test20 run results are
  current/deterministic; re-ran `metrics.compute` → `standard.build` →
  `leaderboard.update` → `write_leaderboard_landing`). **`sphinx -W` on
  `docs/source` = rc 0**, `cross_algorithm.html` builds; the interactive scatter
  is embedded inline (no missing file).
- **Push set (to expose the smoke on RTD):**
  - new: `docs/source/reports/expb_giop_L23_test20/` — `cross_algorithm.rst`,
    `scatter_a_440.png`, `scatter_bb_555.png`, `taylor_a.png`, `target_a.png`,
    `dbic_cdf_expb_pow_vs_giop.png`, `accuracy_chisq_all.csv`, `qc_chisq_all.csv`.
  - modified: `docs/source/reports/index.rst` (leaderboard landing between the
    sentinels; glob toctree picks up the page). Push the branch → RTD builds.
  - **NOT** committed: `runs/…` parquet/chains, `$OS_COLOR/IOPtics/leaderboard.parquet`.
- **⚠ Blocker before pushing — Q12.** `cross_algorithm.rst` is **2.5 MB**: the
  inline Bokeh embed serializes all **31,200** smoke scatter points; the full run
  projects to **~5.2M points → ~415 MB** inline. Recommend **downsampling** the
  interactive scatter (~2–5k pts, stratified) — a small `report.bokeh` change —
  **before** committing (else repo/RTD bloat now, and the full report is
  impossible). Static PNGs are fine (already population summaries).
- **Recommendation:** hold the push until Q12 is settled; then I regenerate (page
  drops to a normal size) and hand you the same push set. No git run.

### First sweep — step 2f: downsample interactive scatter (Q12); push set (2026-07-03)

- **Implemented Q12** in `report/bokeh.py`: `_scatter_points` now caps the
  interactive scatter at **`SCATTER_MAX_POINTS = 3000`**, stratified by
  `(algorithm, component, stratum)` (seeded shuffle + `groupby.head` — keeps
  every selectable combo, total ≤ cap, size **independent of sweep size**).
  Added `test_scatter_points_downsampled`. Full suite **171 passed, 15 skipped**;
  `sphinx -W` clean.
- **Regenerated the smoke report** (clean, into the real tree):
  `cross_algorithm.rst` **2.5 MB → 257 KB**; report dir ~496 KB. The full
  3320-obs run will produce the **same ~257 KB** page (cap is constant).
- **Push set (expose the smoke on RTD):**
  - new: `docs/source/reports/expb_giop_L23_test20/` (`cross_algorithm.rst` +
    5 PNG + `accuracy_chisq_all.csv` + `qc_chisq_all.csv`).
  - modified: `docs/source/reports/index.rst` (leaderboard landing).
  - `git add` those two paths, commit, push → RTD builds. **Not** committed:
    `runs/…` parquet/chains, `$OS_COLOR/IOPtics/leaderboard.parquet`.
- **⚠ Package changes ride along** (needed for the page to render right; should
  land in the same branch/PR): `metrics.py` + `report/tables.py` (χ²-QC, 2b);
  `report/bokeh.py`/`rst.py`/`standard.py` (inline embed 2d + downsample 2f);
  `build_v1.py` knobs (step 1) + `run_v1.yaml` (1b/1d); plus the updated tests.
- No git run (JXP runs git). **Ready for step 3** (full run) once the smoke is
  pushed/approved.

### First sweep — step 2g: docs improvements + new theme (2026-07-04)

All six requested improvements:

1. **"What was done & why"** — `standard.build` now emits an **Overview** section
   (`_intro`) naming the algorithms/datasets and what the reader is looking at,
   with links to the new reference pages.
2. **Per-model page** — new `docs/source/models.rst` details each IOP model:
   ``expb_pow`` = standard 5-param BING (Adg/Sdg/Aph/Bnw/beta, ExpBricaud+Pow,
   MCMC-fit) vs ``giop`` = k=3 contrast (Aexp/Aph/Bnw, GIOP+Lee, LM), and why the
   comparison matters (flexibility vs parsimony → ΔBIC).
3. **Leaderboard text** — `reports/index.rst` now has a "Reading the leaderboard"
   section explaining the cross-sweep fold + every column (rank/win_frac/bias/
   mae/coverage). (Replaced the stale "no sweeps yet" note.)
4. **Per-figure descriptions** — each generated figure/table section now carries
   an explanatory paragraph (`_fig_section`/`_table_section` gained a ``desc``):
   scatter (1:1/3:1/1:3 reading), Taylor/Target, ΔBIC CDF, accuracy & QC tables,
   interactive scatter.
5. **Per-dataset page** — new `docs/source/datasets.rst` defines L23 (Loisel
   2023, 3320 spectra, PACE noise, strata) + planned PANGAEA/GLORIA (with the
   CDOM-vs-`a_dg` caveat). Both new pages linked in the top-level toctree.
6. **New theme** — switched `html_theme` from the classic ``sphinx_rtd_theme`` to
   **``furo``** (modern light/dark, brand colors); added ``furo`` to
   `docs/requirements.txt` (dropped ``sphinx-rtd-theme``), installed it in
   `ocean14`.
- **Tests:** the sphinx-render tests now scaffold stub `datasets`/`models` pages
  (the report ``:doc:`` cross-links them). Full suite **171 passed, 15 skipped**;
  `sphinx -W` builds the **full furo site** clean (rc 0). Regenerated the smoke
  report (Overview + descriptions present; rst ~259 KB).
- **Push set (docs):** modified — `docs/requirements.txt`, `docs/source/conf.py`,
  `docs/source/index.rst`, `docs/source/reports/index.rst`,
  `docs/source/reports/expb_giop_L23_test20/cross_algorithm.rst`; new —
  `docs/source/datasets.rst`, `docs/source/models.rst`. (Package changes from
  earlier steps still ride along in the same branch/PR.) No git run.

### First sweep — step 2h: accessible prose, equations, figures, palette (2026-07-05)

Second docs pass, all four asks:

1. **Accessible language (incl. stats).** Rewrote `models.rst`, `datasets.rst`
   and the leaderboard prose for a geoscientist who isn't an ocean-colour expert:
   define :math:`R_{rs}`, IOPs, absorption/backscatter, CDOM/phytoplankton/
   detritus, and the statistics in plain terms — **MAE** (multiplicative/log
   error, "0.1 ≈ 10% off"), **bias** (signed), **wins** (closer-to-truth per
   spectrum), **coverage** (error-bar calibration), **χ²ᵥ** and **ΔBIC/BIC**.
2. **Models in depth + equations.** `models.rst` now derives the forward model
   (:math:`R_{rs}\approx g_1u+g_2u^2`, :math:`u=b_b/(a+b_b)`), the
   :math:`a=a_w+a_{ph}+a_{dg}` / :math:`b_b=b_{bw}+b_{bp}` split, and each
   parameterization (exponential :math:`a_{dg}`, Bricaud :math:`a_{ph}`,
   power-law :math:`b_{bp}`) as ``.. math::`` — expb_pow (k=5) vs giop (k=3, fixed
   slopes) — plus the χ²ᵥ and BIC definitions. Standard bio-optical forms in our
   own notation (no paper text reproduced).
3. **Colour.** Switched to an **ocean palette**: new
   `docs/source/_static/custom.css` (wired via `html_css_files`) — ocean-blue/
   teal/green brand, gradient sidebar-brand, gradient H1 underline, seafoam table
   headers + zebra rows, framed figures; tuned for both furo light **and** dark
   modes.
4. **Fixed graphics (+ scripts in docs/).** Two generated PNGs:
   `_static/model_components.png` (schematic :math:`a_{dg}`/:math:`a_{ph}`/
   :math:`b_{bp}` shapes vs their slopes) on the models page, and
   `_static/l23_overview.png` (phytoplankton-loading histogram + example Rrs
   spectra) on the datasets page. Generators saved in **`docs/figures/`**
   (`make_model_components.py` = data-free; `make_l23_overview.py` = needs L23;
   PNGs committed so RTD serves them without data).
- **Build:** `sphinx -W` full **furo** site clean (rc 0; css + both PNGs copied &
  linked). Full suite **171 passed, 15 skipped** (no package code changed this
  step; the render tests already scaffold stub `models`/`datasets`).
- **Push set (delta):** modified `docs/source/{conf.py,models.rst,datasets.rst,
  reports/index.rst}`; new `docs/figures/`, `docs/source/_static/custom.css`,
  `_static/{model_components,l23_overview}.png`. No git run (JXP).

### First sweep — step 3a: `full_run.src` for the workstation (2026-07-05)

- **JXP will run the full sweep on their workstation** (replaces 3b here). I did
  **not** launch it.
- **Gave `build_v1.py` a CLI** (`_cli`, argparse): `build_v1.py <flg>
  [--n-cores N] [--strict BOOL] [--obs-ids A:B]`, threading into
  `main(...)`; dropped the now-unused `import sys`. Verified `--help`, `flg 0`
  no-op; dispatch test still green.
- **Wrote `full_run.src`** (repo root) — an `at`-runnable POSIX-`sh` background
  script: sets `OS_COLOR`/`PY`/`REPO` (editable at top), then loops
  `STAGES="1 2 3"` calling `build_v1.py <s> --n-cores 10 --strict false`
  (stage 1 = the ~3 h run; 2 = metrics; 3 = report+leaderboard), appending
  timestamps + results/report paths to `full_run.log`. Launch:
  ``at now -f full_run.src`` (or ``nohup sh full_run.src &``); trim to
  ``STAGES=1`` for run-only.
- **Validated** without the heavy run: `sh -n` syntax OK; a `STAGES=0` (no-op)
  dry run exercised the full wiring (env, paths, loop, CLI, logging) → clean log.
- Push set (delta): modified `ioptics/runs/prototypes/expb_giop/build_v1.py`;
  new `full_run.src`. **After the workstation run finishes**, do steps 4–5
  (verify tables/χ²ᵥ/status, review the report page, commit). No git run (JXP).

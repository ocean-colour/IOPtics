# Code IOPtics — Stage 3: Sweep + MCMC

## Goal

Scale the single fit to full sweeps and add the Bayesian path. **Exit criterion:**
a full **L23 × {expb_pow, giop}** sweep driven by a `runs/.../build_v1.py` (stage
flag 1) writes the complete sweep directory; the MCMC subset produces saved
chains; the tables validate. (This sweep builds BING models, so it runs where the
L23 tree is available — the model-free table/chain/IO paths stay Tier-1.)

Implements **Retrieval & run** (sweep layers, MCMC, chains) and the **Staged plan
/ Stage 3** of `docs/design/IOPtics_implementation.md`. One prompt per module.

## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- **Q&A holds open questions for JXP** — pose them, do **not** self-answer (JXP
  answers before the next task; decisions/rationale go in the Logs).
- Run tests via the env interpreter directly
  (`/home/xavier/miniforge3/envs/ocean14/bin/python -m pytest -q`); `conda
  activate` fails non-interactively. **Run the suite without `$OS_COLOR`**
  (CI-equivalent) before declaring a task done — a mounted L23 tree masks CI
  failures.
- **ocpy and bing are both first-class dependencies — use bing freely.** The
  boundary that holds: `metrics`/`diagnostics`/`report` stay engine-free; nothing
  downstream of `prep` imports ocpy. Build models on the **native grid**; **never**
  seed the fit from truth. Capitalize **BING** in prose (the package imports
  lowercase). Keep docstrings RST-clean so `sphinx-build -W` stays green.
- MCMC in tests always uses a **tiny `nsteps`** (correctness, not convergence).

## Context

- `docs/design/IOPtics_implementation.md` — §Retrieval & run (`run_batch`/
  `run_sweep`, chisq-all + MCMC-subset, `evaluate.from_chains`, chain persistence,
  `chain_file` column), §Driving a sweep (`build_vN.py`, integer-flag stages,
  `$OS_COLOR/IOPtics/runs/<sweep_id>/`).
- bing: `fitting.inference.{init_mcmc,fit_one}`,
  `evaluate.reconstruct_from_chains`, `fitting.l23.save_chains` (chain NPZ
  convention). All verified present in the local bing (2026-06-29) — but see the
  CI caveat below.

### Stage 0–2 carryover (what already exists — build on it, don't recreate)

- **The whole χ² vertical slice is implemented and green.** Build on these, do
  not rewrite:
  - `records` (`PreparedRecord`/`RetrievalResult`/`ComponentFit`), `config`
    (`SweepConfig`/`AlgorithmConfig`, with the per-algorithm `fit_method`
    override already parsed).
  - `datasets`/`noise`/`prep` (L23 → `PreparedRecord`); `prep.prep_dataset(...)`
    already maps over records with per-record seeds via `ProcessPoolExecutor`.
  - `algorithms.spec` (`AlgorithmSpec.{from_standard,to_bing_p,build_models}`) +
    `algorithms.registry` (seeded `expb_pow`/`giop`).
  - **`run`**: `run_algorithm(spec, record, *, fit_method=None, perc=...)`
    **already dispatches on method** — the `chisq` path is done; the `mcmc`
    branch currently raises `NotImplementedError` (Stage 3 fills it). Reusable
    internals: `_prepare` (builds models on the native grid, `init_var_gordon`,
    truth-free `init_other_bits`), truth-free `initial_guess`, `fit_chisq`.
  - **`evaluate`**: `from_chisq` + the `_component_fit(wave, samples, perc)`
    helper that turns ``(n_samples, n_wave)`` draws into a `ComponentFit` (median
    + 68/95 bands). `from_chains` should **reuse `_component_fit`** so MCMC and χ²
    intervals are assembled identically.
  - **`io`**: `write_results(sweep_id, pairs, *, root=None)` /
    `read_results`, `results_to_frames`, `sweep_dir(create=True)` (makes
    `chains/`+`figures/`), `runs_root` (`$OS_COLOR/IOPtics/runs` or `root=`). The
    `results_scalar` schema already has a **`chain_file`** column (currently
    `None` for χ² rows).
  - **`provenance`**: `build(sweep_id, cfg, specs, *, datasets, created)`,
    `write(...)`, and `provenance_id(sweep, algo)` = `"<sweep>#<algo>"`. So far
    `run`/`evaluate` emit `provenance_id=''` and it's stamped by the caller;
    **`run_sweep` should stamp it** on every result.

### ⚠ Known constraints — read before writing tests

- **Building any BING model loads L23 data** (`bbNWModel.init_bbw` →
  `loisel23.load_ds(4,0)`). So `run_algorithm`/`run_batch`/`run_sweep` and the
  MCMC path all need the L23 tree — their tests are **Tier-2 (`@needs_l23`)**,
  not the "synthetic records" the tasks below loosely say. Keep the **model-free**
  parts Tier-1 by feeding **synthetic `RetrievalResult`s** (no fitting): the
  results-table flatten/write, the chain-NPZ save/load round-trip, and the
  `build_vN.py` flag dispatch can all be exercised data-free.
- **`reconstruct_from_chains` returns only total `a`/`bb` (+ `Rrs`) bands**, not
  the sub-components. `from_chains` must compute `a_ph`/`a_dg`/`bb_p` over the
  chain itself (via `eval_anw(retsub_comps=True)` / `eval_bbnw`), exactly as
  `from_chisq` does over its covariance samples — then assemble with
  `_component_fit`. It also burn/thins the chain, so feed it a real emcee chain
  (shape `(nsteps, nwalkers, nparam)`), not arbitrary samples.
- **CI installs bing/ocpy from `git@main`.** JXP confirmed BING `main` is current
  as of Stage 2, but re-confirm `inference.{init_mcmc,fit_one}` /
  `reconstruct_from_chains` / `l23.save_chains` exist in the *released* bing
  before relying on them in any **Tier-1** test (Tier-2 tests skip on CI anyway).

## Prompts

### Coding

1. `run.run_batch`.
1. I have answered your Q&A.  Please review them and let's discuss further.
1. I have answered your Q&A.  Please address my responses.
1. `run.run_sweep` + the `runs/.../build_v1.py` skeleton.
1. I have answered your Q&A.  Please address my responses and then move on to the next task.
1. MCMC path: `run_algorithm(method='mcmc')` + `evaluate.from_chains`.
1. I answered your Q&A.  Please address my responses and then move on to the next task. Chain persistence in `io` (`chains/`, `chain_file`).
1. Tests.

### Pull Requests

1. I have issued a PR for this stage. Please review it and post it to GitHub.  Also, investigate the CI issues and fix them. Please log your work in the Logs section below.

## Modules

### Tasks

1. **`run.run_batch`.** One algorithm over many records via `ProcessPoolExecutor`
   (chunked, mirroring `bing.fitting.l23.batch_fit`); wraps the existing
   `run_algorithm`; returns `list[RetrievalResult]`. Since it builds models it
   needs L23 → **Tier-2 (`@needs_l23`)** on a few real `prep.prep_one('L23', i)`
   records. Q&A. Log.

2. **`run.run_sweep` + build script.** Implement `run_sweep(cfg)`: resolve
   algorithm names via `registry`; χ² over all records per algorithm, then re-run
   `cfg.mcmc_subset` with MCMC (honoring any per-algorithm `fit_method` override);
   **stamp `provenance.provenance_id(cfg.sweep_id, algo)` on each result**;
   flatten via `io.write_results` and write `provenance.build(...)` →
   `provenance.write(...)` under `runs_root(cfg.results_root)`. Add
   `ioptics/runs/prototypes/expb_giop/build_v1.py` (integer-flag stages: 1=run,
   2=metrics [stub until Stage 4], 3=report [stub until Stage 5]) + `run_v1.yaml`
   (the L23 expb_pow/giop config). The full sweep is **Tier-2 (`@needs_l23`)**;
   the table/provenance flatten+write is Tier-1 (feed synthetic results). Q&A. Log.

3. **MCMC path.** Replace the `NotImplementedError` in `run_algorithm`'s
   `method='mcmc'` branch (`init_mcmc` → `fit_one`, idx-keyed Chl/Y; reuse
   `_prepare`/`initial_guess` for the walker centroid) and implement
   `evaluate.from_chains` → `RetrievalResult` reusing `_component_fit` so the
   68/95 bands match the χ² path. Compute sub-components (`a_ph`/`a_dg`/`bb_p`)
   over the chain directly (see ⚠ Known constraints — `reconstruct_from_chains`
   gives only total `a`/`bb`). **Tier-2 (`@needs_l23`)**, tiny `nsteps`. Q&A. Log.

4. **Chain persistence in `io`.** Save each MCMC posterior to
   `runs/<sweep_id>/chains/<algorithm>_<obs_id>.npz` (chains + obs_Rrs/varRrs/Chl/Y,
   `save_chains` convention); set the `chain_file` column on `results_scalar`
   (null for χ² rows); add a loader for `diagnostics`/`report`. Q&A. Log.

5. **Tests.** Tier-1 (data-free, model-free): chain-NPZ save/load round-trip and
   `chain_file` wiring on **synthetic** `RetrievalResult`s; `build_v1.py` flag
   dispatch. Tier-2 `@needs_l23`: `run_batch` over a few L23 records; a small real
   `run_sweep` (both algos, χ² over a handful of spectra + a 1–2 record MCMC
   subset, tiny `nsteps`) writes the full sweep directory and validates the
   tables/provenance + that the MCMC rows carry a saved `chain_file`. Q&A. Log.

### Q&A

> Open questions for JXP (posed, not self-answered).

**Task 1 (`run.run_batch`).**

- `run_batch` wraps each fit in `try/except` so a failure becomes a
  `fit_failed` `RetrievalResult` (a sweep over ~3320 L23 spectra survives a bad
  fit; the row's `status` surfaces it). OK, or do you prefer **fail-fast**
  (propagate) during development?
> A. I prefer fail fast during development.  Let's remember to fix this later (modify the design docs, if necessary).
- Parallelism mirrors `prep_dataset`: `ProcessPoolExecutor` + `ex.map` (order
  preserved). Each worker process reloads L23 once into its own
  `L23Adapter` cache. Fine for now, or want chunking / a shared dataset later?
> A. Keep what we have.

**Task 2 (`run.run_sweep` + build script).**

- `run_sweep` currently runs **χ² over all records + MCMC over the subset for
  *every* algorithm** (the design's "for each algorithm: chisq all, then re-run
  the subset with mcmc"). The per-algorithm `fit_method` override (e.g.
  `giop: mcmc`, Q15) is **not yet honored** as a per-algorithm difference. How
  should `ac.fit_method='mcmc'` behave — MCMC over **all** records for that algo
  (skipping χ²), or just guarantee it's in the MCMC subset? (Posing before I
  bake it in.)
  > A. We will not use MCMC for some methods. Allow for that.

- `run_v1.yaml` ships `mcmc_subset: 0` so the build script's flag-1 stage runs
  today (χ²-only, MCMC lands next task). Bump it to ~200 once the MCMC path is in?
  > A. Good, let's do that.
- `run_sweep(cfg, *, obs_ids=None, …)` takes `obs_ids` (cfg carries no obs
  selection) for tests / partial sweeps. Keep that, or should the sweep config
  grow an explicit obs-selection field?
  > A. Keep that.

**Task 3 (MCMC path).**

- `from_chains` and `from_chisq` now share one `_assemble` (samples come from the
  chain vs from `MVN(ans, cov)`), so components/params/scalars/stats are built
  identically. I unified **`params`** to the *sample* median ± std for both
  methods (χ² previously used `ans` ± `sqrt(diag cov)` — numerically the same for
  MVN draws). OK?
  > A. Good, let's do that.
- The MCMC path uses BING's **idx-keyed `Chl`/`Y`** (`pdict['Chl'] =
  zeros(obs_id+1); [obs_id] = Chl`), which assumes an **integer `obs_id`** (true
  for L23). PANGAEA/GLORIA string IDs will need a different keying — flagging for
  Stage 6.
  > A. Good catch
- `from_chains` burns `spec.mcmc.nburn` capped at `nsteps//2` so a tiny-`nsteps`
  test never discards the whole chain. Reasonable?
  > A. Sure
- Per the per-algorithm-MCMC answer, `run_v1.yaml` now sets `giop: {fit_method:
  mcmc}` + `mcmc_subset: 200` (giop = χ²-all + MCMC-subset; expb_pow = χ² only) —
  the design's example. Good?
  > A. Good

**Task 4 (chain persistence in `io`).**

- To carry the chain pointer into `results_scalar`, I added **`chain_file:
  str|None = None`** to `RetrievalResult` (a trailing default field — extends the
  Stage-0 contract but is backward-compatible/picklable). OK, or would you rather
  pass chain paths to `io.write_results` via a side channel instead?
  > A. Ok
- `save_chain` writes the NPZ with **`np.savez` directly** (keys `chains, idx,
  wave, obs_Rrs, varRrs, Chl, Y`, matching `bing.fitting.l23.save_chains`) rather
  than importing bing — keeps `io` numpy/pandas-only. Good?
  > A. Good
- `run_sweep`'s MCMC subset runs **serially** (`_mcmc_subset`) so each chain can
  be saved without shipping large chains back across a process pool. Fine for the
  small subset, or want pooled MCMC + chain-save later?
  > A. Fine for the small subset.

**Task 5 (tests).**

- The Stage-3 tests were written incrementally per task, so Task 5 was a
  **coverage audit** rather than new modules — every Task-5 item is covered (see
  the Log). Anything additional you want exercised before the Stage-3 PR?
  > A. No, that is fine.
- **Exit criterion:** the full `build_v1.py` flag-1 run (all ~3320 L23 records ×
  {expb_pow χ², giop χ²+200-MCMC}) is the **production** sweep — minutes-to-hours,
  so I validate the *machinery* with a small real sweep (`obs_ids=range(3)`,
  `mcmc_subset=2`) instead of launching the full one in a test. Want me to kick
  off the full `build_v1.py 1` run (long), or leave that for you?
  > A. Leave that for me.

## Logs

### 2026-06-29 (Stage 3, Task 1: `run.run_batch`)

Added `run_batch` (one algorithm over many records) to `run.py`.

- **API.** `run_batch(spec, records, *, fit_method=None, n_cores=1, perc=...)`
  → `list[RetrievalResult]`. Wraps the existing `run_algorithm`; serial or a
  `ProcessPoolExecutor` (`ex.map`, order-preserving) via a top-level
  `_run_one_star` worker (picklable), mirroring `prep_dataset` /
  `bing.fitting.l23.batch_fit`.
- **Robust.** Each fit goes through `_run_one_safe` — on any exception it emits
  a `fit_failed` `RetrievalResult` (`_failed_result`) so one bad spectrum can't
  abort a sweep. (Added `from ioptics.records import RetrievalResult` at the top
  of `run.py`.)
- **Tests** (`test_run.py`, Tier-2 `@needs_l23` — builds models): `run_batch`
  over 3 real L23 records, **serial and `n_cores=2`** — both return 3 `ok`
  results in input order, and the parallel point estimate matches serial
  (deterministic fit).
- **Verification.** run tests **4 passed** (L23 present). Full suite **100
  passed** (L23) / **90 passed, 10 skipped** CI-equivalent (`-u OS_COLOR` — the
  new Tier-2 test skips). `sphinx-build -W` clean.

### 2026-06-29 (Stage 3, Tasks 1b/1c: discuss + apply Q&A — `strict` flag)

Discussed the Task-1 Q&A and applied JXP's decisions.

- **Q1 → fail-fast for now.** Added a `strict` flag to `run_batch` (and its pool
  worker): `strict=True` (**default**) propagates a fit error (fail-fast, so dev
  bugs surface with a traceback); `strict=False` catches → `fit_failed`
  `RetrievalResult` (the production mode — failures become flagged rows +
  reduced coverage). JXP: "remember to fix this later" → recorded the TODO to
  flip the default to robust, in the design doc + memory
  [[ioptics-run-error-policy-todo]].
- **Q2 → keep the parallelism.** No change (ex.map over records; per-worker L23
  reload is negligible vs fit cost).
- **Design doc.** Added an "Error policy (`strict`)" note to §"Sweep layers" +
  the updated `run_batch` signature; bumped implementation doc **0.21 → 0.22**.
- **Tests.** Added a Tier-1 **data-free** strict-toggle test (monkeypatch
  `run_algorithm` to raise): `strict=True` propagates `RuntimeError`;
  `strict=False` yields one `fit_failed` result.
- **Verification.** run tests **5 passed** (L23 present); full suite
  CI-equivalent **91 passed, 10 skipped** (+1 Tier-1). `sphinx-build -W` clean.

### 2026-06-29 (Stage 3, Task 2: `run.run_sweep` + build script)

Added the sweep driver and the staged build-script skeleton.

- **`run_sweep(cfg, *, obs_ids=None, n_cores=1, strict=True, root=None)`.** Preps
  records per dataset (`prep.prep_dataset` with the sweep noise model + seed),
  resolves each algorithm via `registry.get`, runs **χ² over all records** +
  (when `cfg.mcmc_subset`) **MCMC over the subset** per algorithm via
  `run_batch`, stamps `provenance_id` on every result (`_tag_pairs`), then writes
  the tables (`io.write_results`) and `provenance.yaml` (`provenance.build`/
  `write`) under `cfg.results_root`/`root`/`$OS_COLOR`. Returns paths + counts.
  (The MCMC branch is wired but only exercised once Task 3 lands the MCMC path;
  `mcmc_subset=0` skips it.)
- **Build script.** `ioptics/runs/prototypes/expb_giop/{build_v1.py, run_v1.yaml}`
  — integer-flag stages (1=run, 2=metrics [Stage-4 stub], 4=report [Stage-5
  stub]); `run_v1.yaml` is the L23 `expb_pow`/`giop` config (`mcmc_subset: 0`
  for now). `runs/` is build-scripts, not a package, so `find_packages` skips it.
- **Tests** (`test_sweep.py`): Tier-1 **data-free** — load `build_v1.py` via
  importlib, confirm `run_v1.yaml` parses (sweep_id/datasets/algorithms) and
  `main(0)` dispatches nothing. Tier-2 `@needs_l23` — a small χ² sweep
  (`obs_ids=range(3)`, both algos) writes the sweep dir: 6 scalar rows, 6×6×nwave
  spectral rows, `provenance.yaml` present, `provenance_id` stamped, all `ok`.
- **Verification.** sweep tests **2 passed** (L23 present). Full suite **103
  passed** (L23) / **92 passed, 11 skipped** CI-equivalent (`-u OS_COLOR`).
  `sphinx-build -W` clean.

### 2026-06-29 (Stage 3, Tasks 2-Q&A + 3: per-algo MCMC + the MCMC path)

Applied the Task-2 answers and implemented the MCMC retrieval path.

- **Per-algorithm MCMC (Q&A "not all methods use MCMC").** `run_sweep` now zips
  `cfg.algorithms` with their specs and only MCMCs an algorithm when its
  **effective `fit_method`** (`ac.fit_method or cfg.fit_method`) is `'mcmc'` —
  χ² still runs over all records for every algorithm. `run_v1.yaml` updated to
  the design example (`giop: {fit_method: mcmc}`, `mcmc_subset: 200`; expb_pow
  χ²-only). `obs_ids=` kept.
- **MCMC path.** `run.fit_mcmc` (mirrors `bing.fitting.l23.fit_one`):
  `_prepare` → truth-free `initial_guess` walker centroid →
  `inference.init_mcmc` → idx-keyed `pdict['Chl']/['Y']` → `inference.fit_one
  (chains_only=True)`. `run_algorithm`'s `mcmc` branch now calls it →
  `evaluate.from_chains`.
- **`evaluate` refactor.** Extracted **`_assemble`** shared by `from_chisq`
  (MVN samples) and the new **`from_chains`** (burn/thin the emcee chain via
  `thin_burn_chains`, burn = `nburn` capped at `nsteps//2`; posterior median as
  the point estimate). Both reuse `_component_fit`, so MCMC and χ² intervals are
  built identically. `params` unified to sample median ± std.
- **Tests.** Added a Tier-2 `@needs_l23` tiny-`nsteps` (200/50) MCMC round-trip
  (`fit_method='mcmc'`, all 6 components on the native grid, ordered 68/95 bands,
  k=3, status ok). Removed the obsolete `mcmc_not_yet` placeholder.
- **Smoke (L23 present).** giop MCMC → χ²ᵥ ≈ 1.54 (matches its χ² fit), bands
  ordered, status ok. Full suite **103 passed** (L23) / **92 passed, 11 skipped**
  CI-equivalent. `sphinx-build -W` clean.

### 2026-06-29 (Stage 3, Task 4: chain persistence in `io`)

Wired MCMC chain saving + the `chain_file` column. Task-3 Q&A all confirmed (no
code change beyond what's below).

- **`io`.** `save_chain(sweep_id, algorithm, record, chains, *, root)` →
  `<sweep>/chains/<algorithm>_<obs_id>.npz` via `np.savez` (keys `chains, idx,
  wave, obs_Rrs, varRrs, Chl, Y`, the `bing.fitting.l23.save_chains` convention)
  — io stays numpy/pandas-only (no bing import). Plus `chain_path` and
  `load_chain(path)` (for diagnostics/report). `_scalar_row` now reads
  `result.chain_file` (was hardcoded `None`).
- **`records`.** Added `chain_file: str|None = None` to `RetrievalResult` (the
  pointer the `results_scalar` schema needs; trailing default, picklable).
- **`run`.** `run_sweep`'s MCMC subset now goes through `_mcmc_subset` — serial
  `fit_mcmc` → `evaluate.from_chains` → `io.save_chain`, stamping `chain_file` +
  `provenance_id` (strict/fail-fast respected). Serial so the large chains aren't
  shipped back across a pool.
- **Tests.** Tier-1 (data-free): `save_chain`/`load_chain` round-trip
  (chains+context preserved), and the `chain_file` column flows from
  `result.chain_file`. Tier-2 `@needs_l23`: a tiny-`nsteps` sweep
  (`giop: mcmc`, `mcmc_subset: 2`) → `expb_pow` 3 χ² rows, `giop` 3 χ² + 2 MCMC
  rows; the 2 MCMC rows carry loadable `chain_file` NPZs, χ² rows `chain_file`
  null.
- **Verification.** io+sweep tests **8 passed** (L23). Full suite **106 passed**
  (L23) / **94 passed, 12 skipped** CI-equivalent. `sphinx-build -W` clean.

### 2026-06-29 (Stage 3, Task 5: tests — coverage audit + Stage 3 complete)

Task-4 Q&A all confirmed (no code change). Tests were built per-module, so Task 5
was an audit against its checklist — everything is covered:

- **Tier-1 (data-free, CI-run):** chain NPZ save/load round-trip
  (`test_io`), `chain_file` column wiring (`test_io`), `build_v1.py` config +
  flag-0 dispatch (`test_sweep`), `run_batch` strict toggle (`test_run`),
  `_component_fit` band ordering (`test_evaluate`).
- **Tier-2 (`@needs_l23`):** `initial_guess` + `fit_chisq` closure
  (`test_run`), MCMC round-trip tiny-`nsteps` (`test_run`), `run_batch`
  serial/parallel (`test_run`), `from_chisq`/`run_algorithm` (`test_evaluate`),
  small χ² `run_sweep` (`test_sweep`), and the MCMC-subset sweep that saves
  chains + populates `chain_file` (`test_sweep`).
- **Gap filled:** extended the MCMC-subset sweep test to also validate the
  **spectral** table (giop's MCMC rows = 2×6×nwave, all six components) — so both
  tables are checked for the MCMC path.
- **Verification.** Full suite **106 passed** (L23) / **94 passed, 12 skipped**
  CI-equivalent (the 12 skips are exactly the `@needs_l23` Tier-2 set).
  `sphinx-build -W` clean.
- **Stage-3 exit criterion MET** (machinery): a real `run_sweep`
  (`expb_pow` χ² + `giop` χ²+MCMC) writes the full sweep directory —
  `results_{spectral,scalar}.parquet` + `provenance.yaml` + saved `chains/` NPZs,
  tables validate. The full `build_v1.py 1` production run (all L23 × 200 MCMC) is
  left for JXP to launch.

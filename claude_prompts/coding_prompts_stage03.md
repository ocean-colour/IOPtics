# Code IOPtics — Stage 3: Sweep + MCMC

## Goal

Scale the single fit to full sweeps and add the Bayesian path. **Exit criterion:**
a full **L23 × {expb_pow, giop}** sweep driven by a `runs/.../build_v1.py` (stage
flag 1) writes the complete sweep directory; the MCMC subset produces saved
chains; the tables validate.

Implements **Retrieval & run** (sweep layers, MCMC, chains) and the **Staged plan
/ Stage 3** of `docs/design/IOPtics_implementation.md`. One prompt per module.

## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- MCMC in tests always uses a **tiny `nsteps`** (correctness, not convergence).

## Context

- `docs/design/IOPtics_implementation.md` — §Retrieval & run (`run_batch`/
  `run_sweep`, chisq-all + MCMC-subset, `evaluate.from_chains`, chain persistence,
  `chain_file` column), §Driving a sweep (`build_vN.py`, integer-flag stages,
  `$OS_COLOR/IOPtics/runs/<sweep_id>/`).
- bing: `fitting.inference.{init_mcmc,fit_one}`,
  `evaluate.reconstruct_from_chains`, `fitting.l23.save_chains` (chain NPZ convention).

## Prompts

### Coding

1. `run.run_batch`.
2. `run.run_sweep` + the `runs/.../build_v1.py` skeleton.
3. MCMC path: `run_algorithm(method='mcmc')` + `evaluate.from_chains`.
4. Chain persistence in `io` (`chains/`, `chain_file`).
5. Tests.

## Modules

### Tasks

1. **`run.run_batch`.** One algorithm over many records via `ProcessPoolExecutor`
   (chunked, mirroring `bing.fitting.l23.batch_fit`); returns `list[RetrievalResult]`.
   Tier-1 on a few synthetic records. Q&A. Log.

2. **`run.run_sweep` + build script.** Implement `run_sweep(cfg)`: χ² over all
   records per algorithm, then re-run `cfg.mcmc_subset` with MCMC; flatten to
   tables; write provenance. Add `ioptics/runs/prototypes/expb_giop/build_v1.py`
   (integer-flag stages: 1=run, 2=metrics [stub until Stage 4], 3=report [stub
   until Stage 5]) + `run_v1.yaml` (the L23 expb_pow/giop config). Q&A. Log.

3. **MCMC path.** Extend `run_algorithm` for `method='mcmc'` (`init_mcmc` →
   `fit_one`, idx-keyed Chl/Y) and implement `evaluate.from_chains`
   (`reconstruct_from_chains` + sub-components on the chain) → `RetrievalResult`
   on the same 68/95% percentile grid as the χ² path. Tier-1 with tiny `nsteps`.
   Q&A. Log.

4. **Chain persistence in `io`.** Save each MCMC posterior to
   `runs/<sweep_id>/chains/<algorithm>_<obs_id>.npz` (chains + obs_Rrs/varRrs/Chl/Y,
   `save_chains` convention); set the `chain_file` column on `results_scalar`
   (null for χ² rows); add a loader for `diagnostics`/`report`. Q&A. Log.

5. **Tests.** Tier-1: `run_batch` over synthetic records; `run_sweep` on a tiny
   synthetic dataset writes the full directory; tiny-`nsteps` MCMC round-trip +
   chain file present. Tier-2 `@needs_l23`: a small real `run_sweep` (both algos,
   χ², a handful of spectra) validates schema + coverage accounting. Q&A. Log.

### Q&A

## Logs

# Code IOPtics — Stage 1: Data in (L23)

## Goal

Build the dataset-agnostic prep layer for **L23 only** (PANGAEA/GLORIA deferred to
Stage 6). **Exit criterion:** `prep.prep_dataset('L23', range(50))` returns valid
`PreparedRecord`s (Tier-2 `@needs_l23`); Tier-1 synthetic-record tests pass in
`ocean14`.

Implements **Data preparation** and the **Staged plan / Stage 1** of
`docs/design/IOPtics_implementation.md`. One prompt per module.

## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- **Run tests via the env interpreter directly** —
  `/home/xavier/miniforge3/envs/ocean14/bin/python -m pytest -q` — because
  `conda activate` fails in a non-interactive shell (Stage-0 finding).
- **ocpy is imported only by `datasets` and `noise`** (the dependency boundary).
  Nothing downstream of `prep` imports ocpy.
- Native wavelength grids are preserved (no `convert_to_satwave`).
- New public functions/classes are **auto-documented**: Stage 0 wired
  `docs/source/api/index.rst` to autodoc `datasets`/`noise`/`prep`. Keep
  docstrings RST-clean so `sphinx-build -W` stays green — in particular never
  glue text onto a closing double-backtick (``` ``x``s ``` breaks docutils).

## Context

- `docs/design/IOPtics_implementation.md` — §Data preparation (adapters table,
  `PreparedRecord`, `attach_noise`, `prep_one`/`prep_dataset`, truth pre-alignment
  + `truth_interp`, `init` Chl/Y, perturb-by-default for L23 with recorded seed).
- ocpy (verified present in `ocean14`): `hydrolight.loisel23.{load_ds,calc_Chl}`,
  `satellites.pace.gen_noise_vector`, `spectra.Spectrum`, and
  **`chl.band_ratios.oc4`/`oc2`** (`band_ratios` is a *submodule* of `ocpy.chl`,
  not an attribute — the OC band-ratio Chl for `init`). bing:
  `fitting.l23.load_one_l23` (Y via Lee 2002, truth extraction) and
  `fitting.l23.prep_one_l23` as the references to generalize.

### Stage 0 carryover (what already exists — build on it, don't recreate)

- **`ioptics.records.PreparedRecord` is implemented** and re-exported from the
  top level (`from ioptics import PreparedRecord`). `prep` must populate its
  **exact fields**: `dataset`, `obs_id`, `wave`, `Rrs`, `varRrs`, `Rrs_clean`,
  `truth`, `truth_interp`, `init`, `noise_model`, `noise_seed`, `meta` (only
  `meta` has a default). Note the precise names — the perturbation seed goes in
  **`noise_seed`** (not `seed`), the un-perturbed spectrum in **`Rrs_clean`**,
  and the noise tag in **`noise_model`** (`'pace'`/`'insitu'`/`'pct:X'`).
  Records are **picklable** (tested) — keep them so for the process pool.
- **`init` is `{'Chl': ..., 'Y': ...}`** — truth-free, from the *observed* Rrs.
- **conftest skip guards already exist** in `ioptics/tests/conftest.py`
  (`needs_data`, `needs_l23`, `needs_pangaea`). Import them
  (`from ioptics.tests.conftest import needs_l23`); do **not** redefine them.
- **`datasets.py` / `noise.py` / `prep.py` exist as docstring-only stubs** (and
  `RawObs` is not yet defined) — these tasks fill them in.
- `RetrievalResult` / `ComponentFit` (Stage 2) and the `config` surface
  (`SweepConfig`/`AlgorithmConfig`, neutral algorithm carrier) also already
  exist but are not used in Stage 1.

## Prompts

### Coding

1. Execute the 1st task (`datasets.py` registry + L23 adapter).
2. Execute the 2nd task (`noise.py`).
3. Execute the 3rd task (`prep.py`).
4. Execute the 4th task (tests).

## Modules

### Tasks

1. **`ioptics/datasets.py` — registry + L23 adapter.** Fill the existing stub:
   the `register_dataset`/`get_adapter` registry and the `Adapter` protocol
   (`obs_ids`, `load_obs`). Define the new internal **`RawObs`** carrier
   (dataclass: `wave`, `Rrs`, optional `Rrs_err`, `truth`, `meta`). Write the
   **L23 adapter** wrapping `ocpy.hydrolight.loisel23.load_ds(X, Y)`: enumerate
   row indices; for one obs return a `RawObs` with native `wave`, `Rrs`, full
   spectral truth mapped to IOPtics keys (`aph`→`a_ph`, `ag+ad`→`a_dg`,
   `bbnw`→`bb_p`, `a`, `bb`, `a_w`, `bb_w`) and scalars (`Chl`, `Y`, `Sdg`),
   plus `meta` (X, Y). Q&A. Log.

2. **`ioptics/noise.py`.** Fill the stub: `attach_noise(wave, Rrs, model, *,
   add_noise, seed)` returning `(varRrs, Rrs_out, Rrs_clean, tag, seed_used)` per
   the doc: `pace` → `gen_noise_vector(wave)`² on the native grid; `insitu` →
   measured errors²; `pct:X` → `(X·Rrs)²`; optional reproducible perturbation.
   These map straight onto `PreparedRecord` in `prep`: `varRrs`→`varRrs`,
   `Rrs_out`→`Rrs`, `Rrs_clean`→`Rrs_clean`, `tag`→`noise_model`,
   `seed_used`→`noise_seed`. Tier-1 tests (pct, seed reproducibility). Q&A. Log.

3. **`ioptics/prep.py`.** Fill the stub: `prep_one`/`prep_dataset` per the doc:
   dataset-aware defaults (`noise='pace'`+`add_noise=True` for L23), optional
   `[wv_min,wv_max]` trim, `attach_noise`, **pre-align each spectral truth
   component onto `wave`** (set `truth_interp`, keep `orig_wave` in metadata, NaN
   out-of-range), compute truth-free `init={'Chl','Y'}` from the observed Rrs
   (Lee-2002 Y; `ocpy.chl.band_ratios.oc4` Chl), and assemble the
   **`PreparedRecord` populating every field** (incl. `Rrs_clean`, `noise_model`,
   `noise_seed`). Parallel via `ProcessPoolExecutor`; per-record seed =
   `seed`+index, stored in `noise_seed`. Q&A. Log.

4. **Tests.** Add `ioptics/tests/test_{datasets,noise,prep}.py`. Tier-1:
   synthetic `RawObs` → `prep_one` checks (truth on `wave`, `truth_interp` flags,
   NaN out-of-range, `init` present, all `PreparedRecord` fields set, picklable).
   Tier-2: import the **existing** guard (`from ioptics.tests.conftest import
   needs_l23`) and mark `prep_dataset('L23', range(5))` smoke (shapes, varRrs>0,
   truth keys, `noise_seed` recorded). Q&A. Log.

### Q&A

## Logs

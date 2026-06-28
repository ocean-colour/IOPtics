# Code IOPtics — Stage 2 ★: Engine wrap (the in-tandem vertical slice)

## Goal

Wire BING into the uniform layer and get the **first real two-way comparison**
running: one L23 spectrum fit by **both `expb_pow` and `giop`** via least-squares,
reconstructed with uncertainty, and written to the results tables + provenance.
**Exit criterion:** a single L23 spectrum × both algorithms (χ²) → two
`RetrievalResult`s → rows in `results_{spectral,scalar}.parquet` + `provenance.yaml`;
the synthetic-5-band micro-test recovers planted IOPs within tolerance (this
engine path is exercised where L23 data is available — see ⚠ Known constraints).

Implements **Algorithm registry** + **Retrieval & run** and the **Staged plan /
Stage 2** of `docs/design/IOPtics_implementation.md`. One prompt per module.

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
  boundary that holds: `metrics`/`diagnostics`/`report` stay engine-free (they
  read the results table); nothing downstream of `prep` imports ocpy. (The old
  "BING only in spec/run/evaluate" rule was relaxed in Stage 1 — `datasets` calls
  bing too.)
- Build BING models on the record's **native grid**; **never** seed the fit from truth.
- New public APIs are auto-documented (`docs/source/api/index.rst`); keep
  docstrings RST-clean so `sphinx-build -W` stays green (no ``` ``x``s ``` glue).

## Context

- `docs/design/IOPtics_implementation.md` — §Algorithm registry (`AlgorithmSpec`,
  `to_bing_p`/`from_standard`/`build_models`, registry seeding), §Retrieval & run
  (`run_algorithm`, truth-free `initial_guess`, `evaluate.from_chisq`, results
  schema, `provenance.yaml`).
- bing: `parameters.{standard,p_ntuple}`, `models.{anw,bbnw}.init_model`,
  `models.utils.{init,init_other_bits}`, `priors.set_standard_priors`,
  `rt.defs.rt_dict_from_p`, `fitting.chisq_fit.fit`,
  `evaluate.reconstruct_chisq_fits`, `stats.{calc_chisq,calc_ICs}`. (All verified
  present in the local bing as of 2026-06-27 — but see the CI caveat below.)

### Stage 0–1 carryover (what already exists — build on it)

- **`PreparedRecord` is now produced by `prep` (Stage 1)** and is the input to
  `run_algorithm`. Fields you'll use: `wave` (native grid), `Rrs` (observed;
  perturbed for L23), `varRrs` (inverse-variance fit weights), `Rrs_clean`,
  **`init={'Chl','Y'}`** (truth-free — feed `init_other_bits` + the initial
  guess), `truth` (ocpy `Spectrum` per spectral component + scalar floats —
  **for scoring later, NOT for the fit**), `truth_interp`, `noise_model`,
  `noise_seed`, `meta`. Records are picklable. Get a real one with
  `prep.prep_one('L23', idx)` (Tier-2) or build a synthetic one directly.
- **`config` neutral objects exist** (`SweepConfig`/`AlgorithmConfig` =
  name+`fit_method`+overrides). `registry`/`from_standard` resolve a name →
  `AlgorithmSpec`; `config` only validated shape (Stage 0).
- **conftest guards already exist**: `needs_l23`, `needs_pace`, `needs_data`
  (`ioptics/tests/conftest.py`). Import them; don't redefine.
- The implementation design doc is at **v0.21** (the dependency-boundary section
  was updated in Stage 1 to allow `datasets` → bing).

### ⚠ Known constraints — read before writing tests

- **Building any BING model loads L23 data.** `bbNWModel.__init__` → `init_bbw()`
  calls `ocpy.hydrolight.loisel23.load_ds(4, 0)` (reads `Hydrolight400.nc`) for
  pure-water `bb_w`. So `build_models` / `run_algorithm` / `evaluate` — anything
  that constructs a model — **requires the L23 X=4 tree present**, even for a
  synthetic 5-band spectrum. Consequence: the **end-to-end micro-test (Task 7)
  is Tier-2 (`@needs_l23`)**, not data-free; only the model-free parts (spec
  round-trip, `io` round-trip, `provenance` assembly) stay Tier-1. *(Optional
  upstream fix that would remove the coupling: have bing's `init_bbw` use the
  analytic `ocpy.water.scattering.betasw_ZHH2009` instead of loading L23 — flag
  to JXP.)*
- **CI installs bing/ocpy from `git@main`, which lag the local dev copies.**
  Stage 1 was bitten by a missing `bing.rt.rrs.Rrs_to_rrs` (and ocpy `spectra` /
  `PACE_error.csv`). Stage 2 leans heavily on bing — before depending on a bing
  symbol in a **Tier-1 (CI-run)** test, confirm it exists in the *released* bing,
  or the test reds CI. Recommend keeping bing `main` current (push) — otherwise
  the Tier-1 `algorithms.spec`/`registry` tests (which import
  `parameters.standard`) may fail on the runner even though they pass locally.

## Prompts

1. Perform the first task under "Modules".
2. I have answered your Q&A.  Please review them and modify the code to reflect the answers.  Then move on to the 2nd task under "Modules".

## Modules

### Tasks

1. **`algorithms/spec.py`.** Implement `RTOptions`, `MCMCOptions`, `AlgorithmSpec`
   with `to_bing_p()` (→ `p_ntuple.gen`), `from_standard()` (← `parameters.standard`),
   `build_models(wave)` (→ `models.utils.init` + `priors.set_standard_priors` +
   `othera_priors`). Tier-1: round-trip vs `parameters.standard.{expb_pow,giop}`,
   param counts. Q&A. Log.

2. **`algorithms/registry.py`.** `register`/`get`/`available`; **seed `expb_pow`
   and `giop`** via `from_standard`; duplicate-name guard. Tier-1 tests. Q&A. Log.

3. **`run.py` — `run_algorithm` (χ²).** Build `p`/models/`rt_dict`; truth-free
   `init_other_bits` from `record.init` (`{'Chl','Y'}`); **truth-free
   `initial_guess`** (QAA-style band inversion of observed Rrs + prior-central
   fallback); call `chisq_fit.fit`; hand to `evaluate.from_chisq`. Because this
   builds BING models it needs the L23 X=4 file, so the run test is **Tier-2
   (`@needs_l23`)** on a `prep.prep_one('L23', idx)` record (a synthetic-record
   variant can't avoid the model-build L23 load). Q&A. Log.

4. **`evaluate.py` — `from_chisq`.** Covariance-sample `N(ans,cov)` →
   `reconstruct_chisq_fits` → 68/95% bands; sub-components (`a_ph`/`a_dg`/`bb_p`);
   `stats.calc_chisq`/`calc_ICs` → χ²ᵥ/AIC/BIC; assemble `RetrievalResult` +
   `status`/QC. Tier-1. Q&A. Log.

5. **`io.py`.** Flatten `RetrievalResult`s to `results_spectral`/`results_scalar`
   long/tidy parquet (schemas per doc); create/own the
   `$OS_COLOR/IOPtics/runs/<sweep_id>/` layout; read helpers. Tier-1 round-trip.
   Q&A. Log.

6. **`provenance.py`.** Assemble `provenance.yaml` (versions incl. ocpy/bing/
   ioptics commits + doc versions; verbatim config copy; per-algorithm blocks with
   full priors + RT + fit method + noise model); `provenance_id` linking. Tier-1.
   Q&A. Log.

7. **End-to-end micro-test.** Synthetic 5-band Rrs from a known forward model →
   synthetic record → `run_algorithm` for **both** algorithms (χ²) → `evaluate` →
   `io` write → assert planted IOPs recovered within tolerance and tables/
   provenance well-formed; no MCMC. **Tier-2 (`@needs_l23`)** — building the BING
   models loads `Hydrolight400.nc` (so it can't be data-free). Keep the
   model-free checks (spec/io/provenance round-trips) as separate **Tier-1**
   tests so CI still exercises the non-engine surface. Q&A. Log.

### Q&A

> Open questions for JXP (posed, not self-answered).

**Task 1 (`algorithms/spec.py`).**

- The Tier-1 `test_spec.py` round-trip imports `bing.parameters.standard`
  directly (the *released* bing on CI). It passes locally, but if bing `@main`
  lags (as `Rrs_to_rrs` did in Stage 1) these reds CI. Is bing `main` current
  with `parameters.standard.{expb_pow,giop}`, or should I guard the test? (This
  is the CI caveat from the prompt — flagging before it bites.)
  A. BING `main` is current
- `AlgorithmSpec` has **no `add_noise` field** (per the design — noise is a
  prep/sweep concern, and `run` fits against `record.varRrs`). So `from_standard`
  →`to_bing_p` round-trips `add_noise` only for combos that leave it default
  (expb_pow/giop = False); `gsm` (sets `add_noise=True`) wouldn't. OK to keep it
  off the spec?
  A. Yes keep it off the spec.
- `build_models` follows bing's `prep_one_l23` pattern — `models.utils.init`
  **without** prior_dicts, then `set_standard_priors(models, p)`, then append
  `othera_priors` — rather than the design-doc sketch's
  `init(..., (apriors, bpriors))`. The end priors are identical; I matched the
  live bing reference. Good?

**Task 2 (`algorithms/registry.py`).**

- The registry **seeds expb_pow + giop at import time** via `from_standard`
  (which imports bing). I wrapped the seeding in `try/except` so the Sphinx docs
  build — which **mocks** bing — imports the module without crashing; with real
  bing present it seeds normally and the Tier-1 tests assert it. Acceptable, or
  would you rather not mock bing in the docs (pip-install it on RTD) and seed
  unconditionally?
- `register(spec, *, overwrite=False)` takes a spec (per the design) and raises
  `ValueError` on a duplicate name unless `overwrite=True`; `get` raises
  `KeyError` for unknown names. OK with those exception types?
  A. Good

## Logs

### 2026-06-27 (Stage 2, Task 1: `algorithms/spec.py`)

Implemented the algorithm-spec layer (replacing the stub).

- **Dataclasses.** `RTOptions`, `MCMCOptions`, and `AlgorithmSpec` — a plain,
  serializable mirror of the fields BING's `p_ntuple` carries (model names,
  a/b/othera priors, RT toggles, set_Sdg/sSdg/beta, MCMC, fit_method,
  noise_model). `rt`/`mcmc` use `default_factory`.
- **BING interop (all lazy-import bing).**
  `to_bing_p(**overrides)` → `p_ntuple.gen` (maps every spec field; overrides like
  `wv_min`/`wv_max` pass through). `from_standard(name, label=, **overrides)` ←
  `parameters.standard.<name>()`, reading back model names + priors + RT + MCMC
  (the lossless inverse for shipped combos). `build_models(wave)` mirrors bing's
  `prep_one_l23` (`utils.init` → `set_standard_priors` → append `othera_priors`).
- **Tier-1 tests** (`test_spec.py`, model-free → CI-safe): `from_standard`
  round-trip for **expb_pow** (ExpBricaud/Pow, 3+2 priors, k=5) and **giop**
  (GIOP/Lee, 2+1, k=3); `to_bing_p` reproduces `parameters.standard` model_names
  + verbatim priors + RT/Sdg/MCMC fields; label default; override pass-through;
  RT/MCMC defaults.
- **Verification.** Full suite (CI-equivalent, `-u OS_COLOR`) **76 passed,
  3 skipped** (+7). `build_models` sanity (L23 present): both algorithms build
  `[ExpBricaud,Pow]`/`[GIOP,Lee]` with `nparam` matching prior counts and priors
  set. `sphinx-build -W` clean.
- **Note.** `build_models` is exercised for real in Task 3 (Tier-2, `@needs_l23`
  — model construction loads `Hydrolight400.nc`); Task 1's CI coverage is the
  model-free round-trip.

### 2026-06-27 (Stage 2, Task 2: `algorithms/registry.py`)

Implemented the algorithm registry (replacing the stub).

- **API.** `REGISTRY` dict + `register(spec, *, overwrite=False)` (duplicate name
  → `ValueError` unless `overwrite`), `get(name)` (unknown → `KeyError` with the
  available list), `available()` (sorted names).
- **Seeded in tandem.** `expb_pow` (label `ExpB_Pow`) and `giop` (`GIOP`) via
  `AlgorithmSpec.from_standard`, at import time. The seeding is wrapped in
  `try/except` so a **mocked bing** (the docs build) imports the module cleanly;
  with real bing it seeds and the tests assert it (so a genuine seeding failure
  still surfaces in the suite, not silently).
- **Tier-1 tests** (`test_registry.py`): both seeded with right models/labels;
  `available()` sorted; unknown→`KeyError`; duplicate→`ValueError` (+`overwrite`
  allowed); register/retrieve a fresh spec (model-free `AlgorithmSpec`) with
  cleanup.
- **Verification.** Registry tests **5 passed**; full suite (CI-equivalent,
  `-u OS_COLOR`) **81 passed, 3 skipped** (+5). Crucially, `sphinx-build -W`
  **still succeeds** despite registry's import-time seeding (the mocked-bing
  guard works).

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
3. I have answered your Q&A.  Please review them and modify the code to reflect the answers.  Then move on to the 3rd task under "Modules".
4. Execute the 4th task under "Modules".
5. I have answered your Q&A.  Please review them and modify the code to reflect the answers.  Then move on to the 5th task under "Modules".
6. I have answered your Q&A.  Please review them and modify the code to reflect the answers.  Then move on to the 6th task under "Modules".
7. I have answered your Q&A.  Please review them and modify the code to reflect the answers.  Then move on to the 7th task under "Modules".
8. Execute the 8th task under "Modules".
9. Execute the 9th task under "Modules".

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

8. **Finishing up.** I have issued a PR for this stage. Please review it and post it to GitHub.  Also make sure the docs are all up-to-date. Please log your work in the Logs section below.

9. **PR**. Read the PR comments and make any needed changes to the code to address them.  And, if you have any additional questions, please add them to the Q&A section below. Log your work.

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

  A. Good

**Task 2 (`algorithms/registry.py`).**

- The registry **seeds expb_pow + giop at import time** via `from_standard`
  (which imports bing). I wrapped the seeding in `try/except` so the Sphinx docs
  build — which **mocks** bing — imports the module without crashing; with real
  bing present it seeds normally and the Tier-1 tests assert it. Acceptable, or
  would you rather not mock bing in the docs (pip-install it on RTD) and seed
  unconditionally?

  A. That looks fine.  Add to your memory, it is BING and not bing.

- `register(spec, *, overwrite=False)` takes a spec (per the design) and raises
  `ValueError` on a duplicate name unless `overwrite=True`; `get` raises
  `KeyError` for unknown names. OK with those exception types?

**Task 3 (`run.py`).**

- The truth-free `initial_guess` is a **QAA-style inversion of the observed
  Rrs** using BING's Gordon coefficients + the models' own `a_w`/`bb_w`, anchored
  at ~670 nm (`a ≈ a_w`). It gives χ²ᵥ ≈ 1.3–1.5 starts that the fit refines
  cleanly. OK, or do you want a specific QAA variant / anchor band?
- Found a **type gotcha**: `record.init['Chl']` is a Python `float`, but BING's
  `set_aph` does `len(Chla.shape)` — works only for a numpy scalar (BING's own
  L23 path passes `np.float64`). I now pass `np.asarray(Chl, float)` in
  `_prepare`. Should `prep` instead store `init['Chl']` as a numpy scalar so the
  whole codebase sees the BING-expected type? (I kept the fix in `run` for now.)
- Closure is asserted via **reduced χ²** (`< 5`; actuals 1.35 / 1.54), not raw
  relative Rrs error — the latter is meaningless in the red where Rrs→0 (noise
  floor). Good metric for the run test?

  A. Good

**Task 4 (`evaluate.py`).**

- I use `bing.stats.calc_chisq` (with `noise_term=√varRrs`) for χ², but compute
  **AIC/BIC with BING's own formulas inline** (`2k+χ²`, `k·ln(n)+χ²`) rather than
  `bing.stats.calc_ICs` — because `calc_ICs` re-derives `model_Rrs` via
  `reconstruct_chisq_fits` **without** `rt_dict`, so it'd ignore variable-Gordon
  and mismatch our fit. OK, or would you rather I push a bing fix so `calc_ICs`
  takes `rt_dict`?
  
  A. Yes, that is ok.
- **Bands** are covariance-propagated: draw `n_samples=1000` from
  `MVN(ans, cov)` (with `check_valid='ignore'` for near-singular cov) and take
  16/84 + 2.5/97.5 percentiles — the same percentile machinery the MCMC path
  will use. Seeded `seed=1234` so bands are reproducible. OK, or derive the seed
  from `record.noise_seed`?

  A. Good
- **Scalars** for Stage 2 = `a_cdom440` (from the `a_dg(440)` posterior) plus
  `Sdg`/`beta` when they're free params. `Chl` and other derived scalars are
  deferred. Enough for now?

  A. Yes, that is enough for now.
- **`params`** are reported in **fit space** (log10 for the amplitude params,
  linear for `Sdg`/`beta`), as `{pname: (median, sigma)}`. Should `io`/`metrics`
  convert amplitudes to linear downstream, or should `evaluate` emit linear?

  A. Yes, convert amplitudes to linear downstream.

**Task 5 (`io.py`).**

- On "convert amplitudes to linear downstream": the **designed tables already
  carry only linear physical quantities** — `results_spectral` values are
  `a`/`bb`/`a_ph`/`a_dg`/`bb_p` (1/m) + `Rrs_model` (1/sr) straight from
  `eval_anw`/`eval_bbnw`, and `results_scalar` has `a_cdom440`/`Sdg`/`beta`
  (all linear). The raw log10 fit amplitudes (`Adg`/`Aph`/`Bnw`) are **not
  surfaced** in either table, so there's nothing to convert in Stage-2 `io`. If
  you want the raw fit params persisted too (e.g. a `params` table or a
  provenance block), I'll 10**-convert the log-flavored ones there. Sound right?

  A. Yes, that is right.

- `Rrs_model`'s `truth` column is set to **`record.Rrs_clean`** (the noiseless
  Rrs) as the closure reference. OK, or leave it NaN like the other model-only
  components?

  A. Yes, leave it NaN like the other model-only components.

- `results_root` defaults to `$OS_COLOR/IOPtics/runs` and is overridable via
  `root=` (tests pass `tmp_path`). Keep that resolution, or read it from the
  sweep config's `results_root` when present?

  A. Keep that resolution.

**Task 6 (`provenance.py`).**

- `versions()` reads **git commits** via `subprocess git -C <repo> rev-parse
  --short HEAD` for ioptics/bing/ocpy (repo = the installed package's dir
  parent), falling back to `None` when not a git checkout (e.g. a pip/wheel
  install). Doc versions are parsed from `**Version:**` in the design `.md`s.
  OK, or would you prefer reading commits another way (e.g. importlib metadata)?

  A. OK

- The provenance record is **plain dict → YAML** (`build()` then `dump()`/
  `write()`), with `config` as the verbatim `cfg.to_dict()`. Each algorithm
  block carries models + full priors + RT + set_Sdg/sSdg/beta + fit_method +
  noise_model (a bit more than the design's terse example). Keep the fuller
  block, or trim to exactly the doc's fields?

  A. Keep the fuller block.

- `provenance_id = "<sweep_id>#<algorithm>"`. `run`/`evaluate` currently emit
  `provenance_id=''`; I'll stamp it in the Task-7 micro-test (and `run_sweep` in
  Stage 3). Want `run_algorithm` to take an optional `provenance_id=` now?

  A. No, I will stamp it in the Task-7 micro-test. If you remind me. :)

**Task 7 (end-to-end micro-test).**

- **Reminder (as requested):** the micro-test stamps `provenance_id` itself —
  `res.provenance_id = provenance.provenance_id(SWEEP_ID, spec.name)` after each
  `run_algorithm`, before `io.write_results` — and asserts it lands in the
  `results_scalar` table as `"<sweep>#<algo>"`. (run/evaluate still emit `''`.)
- I implemented the micro-test as a **real L23 spectrum × both algorithms** with
  recovery checked against **L23 truth** (a(440)/bb(555) within ~3%; asserted a
  factor-2 band), rather than the literal "synthetic 5-band from a known forward
  model." Rationale: L23 is mounted, real-truth recovery is more meaningful, and
  a self-generated 5-band would test the inverter against itself. Want the
  literal synthetic-5-band variant too, or is the real-L23 recovery enough?
- **Stage 2 is complete** — ready for a Stage-2 PR + CI/readthedocs check (as in
  Stage 0/1)?

**Task 9 (PR comments).**

- PR #5 has **no outstanding comments to address** — the only review is my own
  (fully actioned: you committed the docs landing-page update in `066eb77`).
  Made no code changes this task; verified no working-tree drift and the
  CI-equivalent suite still **90 passed, 9 skipped**, docs `-W` clean. Anything
  specific you wanted addressed that I'm not seeing?
- CI re-ran after the docs-only push and is finishing; it should stay green (the
  Stage-2 code already passed; only `index.rst` changed). Merge #5 and start
  **Stage 3** (sweep + MCMC subset + chain persistence)?

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

### 2026-06-28 (Stage 2, Task 3: `run.py` — chisq path)

Implemented the least-squares fit driver (replacing the stub). Also applied the
Q&A answers from Tasks 1–2 (all confirmed; only action: capitalize **BING** in
prose — added to memory; the package import stays lowercase).

- **`run_algorithm(spec, record, *, fit_method=None, perc=…)`** — chisq default;
  `mcmc` → `NotImplementedError` (Stage 3). Internals: `_prepare` (build models
  on the native grid → `init_var_gordon` on the a-model when `variable_Gordon` →
  `rt_dict_from_p` → truth-free `init_other_bits` from `record.init`),
  `initial_guess` (truth-free QAA), `fit_chisq` (prior-bounds + `chisq_fit.fit`).
- **Truth-free `initial_guess`.** QAA-style inversion of the observed `Rrs`:
  Gordon `u` from `G1/G2_STANDARD`, red-anchor `a≈a_w` at 670 nm, propagate with
  the `init['Y']` slope, subtract the models' `a_w`/`bb_w`, then each model's
  `init_guess` (amplitudes log10'd, clipped into prior bounds). No ocpy, no truth.
- **Two BING-wiring fixes** found via the real fit: (1) the a-model needs
  `init_var_gordon(...)` set for `variable_Gordon` (forward model reads
  `models[0].G1/G2`); (2) `init_other_bits` needs `Chl` as a numpy scalar
  (`set_aph` does `len(Chla.shape)`) — pass `np.asarray(Chl, float)`.
- **Tests** (`test_run.py`, Tier-2 `@needs_l23` — model build loads
  `Hydrolight400.nc`): `initial_guess` sized + in-bounds + finite;
  `fit_chisq` for **both** algorithms returns finite `ans`/`cov` and closes on
  the observed Rrs at **χ²ᵥ = 1.35 / 1.54** (asserted `< 5`); `mcmc` raises.
- **Verification.** Run tests **3 passed** (L23 present). Full suite
  CI-equivalent (`-u OS_COLOR`) **81 passed, 6 skipped** (the 3 run tests skip
  without L23 — CI-safe). `sphinx-build -W` clean.
- **Note.** `run_algorithm`'s final hop calls `evaluate.from_chisq` (Task 4); the
  Task-3 tests exercise the fit core via `fit_chisq`, so they don't depend on it.

### 2026-06-28 (Stage 2, Task 4: `evaluate.py` — from_chisq)

Implemented the least-squares → `RetrievalResult` assembly (replacing the stub).
The Task-3 Q&A was confirmed (closure metric "Good"); the two unanswered Task-3
questions left as-is.

- **`from_chisq(spec, record, models, rt_dict, ans, cov, *, perc, n_samples,
  seed)`.** Covariance-propagated uncertainty: draw `MVN(ans, cov)` (1000
  samples, `check_valid='ignore'`), forward-model via
  `bing.evaluate.calc_Rrs_from_models` (batched) + `eval_anw(retsub_comps=True)`
  → `(a_dg, a_ph)` + `eval_bbnw`, then percentiles (16/84, 2.5/97.5) into a
  `ComponentFit` per component (`a, bb, a_ph, a_dg, bb_p, Rrs_model`). Same
  percentile approach the MCMC path will reuse, so intervals are comparable.
- **Stats.** χ² via `bing.stats.calc_chisq(noise_term=√varRrs)`; χ²ᵥ, AIC=`2k+χ²`,
  BIC=`k·ln(n)+χ²` (BING's `calc_ICs` formulas, but computed on our
  variable-Gordon point `model_Rrs` since `calc_ICs` re-derives Rrs without
  `rt_dict`). `params` = `{pname:(med,σ)}` in fit space; `scalars` = `a_cdom440`
  (+`Sdg`/`beta`); `status` = `ok`/`fit_failed`.
- **Fix.** Point-estimate forward pass needs params as `(1, nparam)` — a 1-D
  `ans[:na]` was misread as N one-param samples (`calc_chisq` then got a vector).
  Reshape + squeeze.
- **Tests** (`test_evaluate.py`): Tier-1 `_component_fit` band-ordering
  (lo95≤lo68≤med≤hi68≤hi95, data-free); Tier-2 `@needs_l23` full `from_chisq`
  for both algorithms (component keys, native-grid bands, k=5/3, χ²ᵥ∈(0,5),
  finite AIC/BIC, `a_cdom440` present) + `run_algorithm` end-to-end.
- **Verification.** Evaluate tests **3 passed** (L23 present). Full suite
  CI-equivalent (`-u OS_COLOR`) **82 passed, 8 skipped** (+1 Tier-1; the 2 new
  Tier-2 skip without L23). `sphinx-build -W` clean. `run_algorithm` now returns
  a complete `RetrievalResult` end-to-end.

### 2026-06-29 (Stage 2, Task 5: `io.py` — long/tidy parquet tables)

Implemented the results-table writer/reader (replacing the stub). Applied the
Task-4 Q&A (all confirmed): AIC/BIC inline OK, band seed OK, scalars enough, and
"convert amplitudes to linear downstream" — which is already satisfied because
the designed tables carry only linear physical quantities (the log10 fit
amplitudes are never surfaced); confirmed and noted in Q&A.

- **API.** `write_results(sweep_id, pairs, *, root=None)` /
  `read_results(...)` over `[(RetrievalResult, PreparedRecord), …]`;
  `results_to_frames`, `sweep_dir`, `runs_root`. Owns the layout
  `<runs_root>/<sweep_id>/{results_spectral.parquet, results_scalar.parquet,
  chains/, figures/}`; `runs_root` = `$OS_COLOR/IOPtics/runs` or `root=`.
- **Schemas (per design).** `results_spectral`: one row per
  `(dataset,obs_id,algorithm,fit_method,component,wavelength)` with
  `value/lo68/hi68/lo95/hi95/truth/truth_interp/unit`. Truth pulled from the
  record's `Spectrum` per component (NaN where absent); `Rrs_model` truth =
  `Rrs_clean`. `results_scalar`: one keyed row with `chi2/chi2_nu/AIC/BIC/
  n_bands/k`, `Chl/a_cdom440/Sdg/beta` (+`sig_`), `*_truth`, `status`,
  `chain_file` (null for χ²), `provenance_id`. Pure pandas/pyarrow (no BING/ocpy).
- **Tests** (`test_io.py`, Tier-1, data-free — synthetic record/result):
  sweep-dir layout; spectral round-trip (6×nwave rows, component set, a_dg truth
  from the Spectrum, Rrs_model truth = Rrs_clean, missing-truth → NaN, units);
  scalar schema + truth columns.
- **Verification.** io tests **3 passed**; full suite CI-equivalent
  (`-u OS_COLOR`) **85 passed, 8 skipped** (+3 Tier-1). `sphinx-build -W` clean.

### 2026-06-29 (Stage 2, Task 6: `provenance.py`)

Implemented the provenance record (replacing the stub). Applied the Task-5 Q&A:
tables stay linear-physical (confirmed); **`Rrs_model` truth → NaN** (changed
`io._truth_spectrum` + its test, dropping the `Rrs_clean` reference); kept the
`results_root` resolution.

- **API.** `build(sweep_id, cfg, specs, *, datasets, created)` → a plain
  YAML-serializable dict: `sweep_id`, `created`, `versions()`, verbatim `config`
  (`cfg.to_dict()`), `datasets`, and a per-algorithm `algorithm_block`. Plus
  `dump()` (YAML text), `write()` (→ `<sweep>/provenance.yaml` via
  `io.sweep_dir`), and `provenance_id(sweep, algo)` = `"<sweep>#<algo>"`.
- **`versions()`.** ioptics/bing/ocpy `{commit, version}` — commit via
  `git -C <repo> rev-parse --short HEAD` (None on a non-git/wheel install),
  version from the package — plus `design_doc`/`implementation_doc` parsed from
  the `**Version:**` line of the design `.md`s. Stdlib + PyYAML only.
- **`algorithm_block`.** models + full priors + RT block + set_Sdg/sSdg/beta +
  fit_method + noise_model (per the design's per-algorithm block).
- **Tests** (`test_provenance.py`, Tier-1, data-free — specs built directly, no
  BING): `provenance_id` format; `versions()` shape; serializable algorithm
  block; full record structure (verbatim config copy, dataset block, per-algo
  fit_method); YAML write/read round-trip equals the built record.
- **Verification.** provenance **5 passed** (+ io still 3); full suite
  CI-equivalent (`-u OS_COLOR`) **90 passed, 8 skipped** (+5 Tier-1).
  `sphinx-build -W` clean. Only Task 7 (end-to-end micro-test) remains in Stage 2.

### 2026-06-29 (Stage 2, Task 7: end-to-end micro-test — Stage 2 complete)

Applied the Task-6 Q&A (all confirmed; no code change) and wrote the headline
end-to-end test. (JXP remounted the L23 tree locally under
`$OS_COLOR/Loisel2023/`, so Tier-2 runs here this turn.)

- **`test_micro.py`** (Tier-2 `@needs_l23`): one real L23 spectrum (obs 0) fit by
  **both** `expb_pow` and `giop` (χ²) → two `RetrievalResult`s → `io.write_results`
  → `provenance.write`. Asserts: each result `status='ok'`, components on the
  native grid, χ²ᵥ∈(0,5); **recovers planted IOPs** — retrieved a(440)/bb(555)
  within a factor-2 band of L23 truth (actuals ~3%); the tables carry both
  algorithms (2 scalar rows, 2×6×nwave spectral rows); `provenance.yaml` reloads
  with both algorithm blocks + verbatim config + versions.
- **`provenance_id` stamped** in the test (the reminder JXP asked for) and
  verified to flow into `results_scalar` as `"<sweep>#<algo>"`.
- Chose **real-L23 truth recovery** over the literal synthetic-5-band (more
  meaningful; avoids testing the inverter against itself) — flagged in Q&A.
- **Verification.** Micro-test **1 passed**. Full suite **99 passed** with L23
  present; **90 passed, 9 skipped** CI-equivalent (`-u OS_COLOR` — the 9 Tier-2
  skip). `sphinx-build -W` clean.
- **Stage-2 exit criterion MET:** a single L23 spectrum × both algorithms (χ²) →
  two `RetrievalResult`s → rows in `results_{spectral,scalar}.parquet` +
  `provenance.yaml`, recovering planted IOPs within tolerance. The first real
  `expb_pow`-vs-`giop` two-way comparison runs end to end.

### 2026-06-29 (Stage 2, Task 8: PR #5 review + docs refresh)

JXP opened **PR #5 "Stage 2"** (`stage-2` → `main`, 15 files / +1811/−60).
Reviewed it, refreshed the docs, and posted the review.

- **State checked.** PR MERGEABLE / mergeStateStatus CLEAN; **CI green** — all 4
  Tier-1 jobs (py3.12 + py3.14) pass. No working-tree code drift. (`conftest`'s
  `needs_pace` isn't in the diff — already on `main` from the merged Stage-1 PR.)
- **Re-verified locally.** Full suite **99 passed** with L23 mounted; **90
  passed, 9 skipped** CI-equivalent (`-u OS_COLOR`). `sphinx-build -W` clean.
- **Docs refresh.** Updated the readthedocs landing-page status note from
  "Stage 0 — scaffolding" to the Stage-2 vertical slice (contracts + config →
  L23 prep → algorithm registry → run/evaluate engine → io/provenance). The
  `api/index.rst` already autodocs every now-implemented module, so the API
  reference is current; rebuilt `-W` clean. (Edit is in the working tree for JXP
  to commit/push so RTD reflects it.)
- **Posted** a substantive COMMENTED review (`gh pr review 5 --comment` — GitHub
  blocks self-approval; gh = `profxj`): verified items, strengths, the two
  BING-wiring fixes (`init_var_gordon`, numpy-scalar `Chl`), and non-blocking
  follow-ups (AIC/BIC-vs-`calc_ICs`; real-L23 recovery vs synthetic-5-band;
  upstream analytic `init_bbw`).
- **Stage 2 ★ ships:** the in-tandem `expb_pow`/`giop` engine wrap is complete,
  green on CI, and documented.

### 2026-06-29 (Stage 2, Task 9: PR #5 comments — nothing to change)

Re-read PR #5 after JXP pushed the docs commit (`066eb77 "ok"`).

- **No outstanding comments.** Inline review comments: none; issue comments:
  none; reviews: only my own COMMENTED one, already fully actioned (the docs
  landing-page update is committed; no working-tree drift). So **no code changes
  were needed** — reported the state rather than fabricating edits (same as the
  analogous Stage-1 task).
- **Re-verified.** CI-equivalent suite **90 passed, 9 skipped**; `sphinx-build
  -W` clean. CI re-ran on the docs-only push and is finishing — expected green
  (Stage-2 code already passed; only `index.rst` changed).
- The only open threads are the non-blocking follow-ups from my review
  (AIC/BIC-vs-`calc_ICs`, synthetic-5-band variant, upstream analytic
  `init_bbw`) — surfaced as Q&A, none blocking the merge.

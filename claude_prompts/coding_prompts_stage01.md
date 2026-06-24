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
- **Q&A holds open questions for JXP** — pose them, do **not** self-answer. JXP
  answers before the next task; decisions/rationale go in the Logs.
- **Run tests via the env interpreter directly** —
  `/home/xavier/miniforge3/envs/ocean14/bin/python -m pytest -q` — because
  `conda activate` fails in a non-interactive shell (Stage-0 finding).
- **ocpy and bing are both first-class dependencies.** Data adapters may call
  bing where it is the natural source of truth (e.g. L23 truth via
  `bing.fitting.l23.load_one_l23`) — don't re-derive what bing already provides.
  The boundary that still holds: nothing downstream of `prep` imports ocpy, and
  `metrics`/`diagnostics`/`report` stay engine-free (they read the results table).
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
3. Execute the 3rd task (`Misconceptions`).
4. Execute the 4th task (`prep.py`).
5. Execute the 5th task (Q&A).
6. Execute the 6th task (tests).

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

3. **Misconceptions.**  You currently have two misconceptions that need rectifying:
    - You **are** encouraged to use the BING package.  It will be a dependency
    - You are supposed to write questions in Q&A but **not** answer them yourself.  I will do that before proceeding onto the next task.
    - Please make any changes needed to the docs and code to reflect these.

4. **`ioptics/prep.py`.** Fill the stub: `prep_one`/`prep_dataset` per the doc:
   dataset-aware defaults (`noise='pace'`+`add_noise=True` for L23), optional
   `[wv_min,wv_max]` trim, `attach_noise`, **pre-align each spectral truth
   component onto `wave`** (set `truth_interp`, keep `orig_wave` in metadata, NaN
   out-of-range), compute truth-free `init={'Chl','Y'}` from the observed Rrs
   (Lee-2002 Y; `ocpy.chl.band_ratios.oc4` Chl), and assemble the
   **`PreparedRecord` populating every field** (incl. `Rrs_clean`, `noise_model`,
   `noise_seed`). Parallel via `ProcessPoolExecutor`; per-record seed =
   `seed`+index, stored in `noise_seed`. Q&A. Log.

5. **Q&A.** I just realized you had written questions in Q&A.  I have now answered them.  Please review them and modify the code to reflect the answers.  Also, provide additional information/recommendatoins.  And, if you have any additional questions, please add them to the Q&A section below. Log your work.

6. **Tests.** Add `ioptics/tests/test_{datasets,noise,prep}.py`. Tier-1:
   synthetic `RawObs` → `prep_one` checks (truth on `wave`, `truth_interp` flags,
   NaN out-of-range, `init` present, all `PreparedRecord` fields set, picklable).
   Tier-2: import the **existing** guard (`from ioptics.tests.conftest import
   needs_l23`) and mark `prep_dataset('L23', range(5))` smoke (shapes, varRrs>0,
   truth keys, `noise_seed` recorded). Q&A. Log.

### Q&A

> Open questions for JXP (posed, not self-answered — JXP answers before the next
> task). Decisions already taken are recorded in the Logs.

**Task 1 (`datasets.py` — registry + L23 adapter).**

- The L23 adapter now calls `bing.fitting.l23.load_one_l23` for the full truth
  dict (per the Task-3 "use BING" correction). OK to depend on its entire return
  dict, or do you want a thinner bing entry point?
  A: It is ok to use the entire return dict.

- Truth keys exposed: spectral `a, bb, a_ph, a_dg, bb_p, a_w, bb_w` + scalars
  `Chl, Y, Sdg`. I dropped the redundant `anw`/`bbnw` (`anw=a_ph+a_dg`,
  `bbnw=bb_p`) — keep them dropped?
  A. Yes drop them
- `meta` carries `{dataset, obs_id, X, Y}`, where `meta['Y']` is the solar-zenith
  load option vs `truth['Y']` the Lee-2002 slope — keep both under these names?
  A. Yes keep both under these names.

**Task 2 (`noise.py`).**

- The doc's `attach_noise` signature omits a measured-error argument; I added
  `Rrs_err=` for the `insitu` path. Keep that name/shape?
  A. Yes keep that name/shape.
- With `add_noise=True` and `seed=None` the draw is non-reproducible and
  `seed_used=None`. Acceptable, or should `prep` always force a seed?
  A. This is acceptable.

**Task 4 (`prep.py`).**

- `init['Y']`: bing exposes no standalone Rrs→Y function (it lives inside
  `load_one_l23` against the clean Rrs, and as `bbnw` Lee `compute_Y` needing a
  model instance). I reuse `bing.rt.rrs.Rrs_to_rrs` for the conversion and apply
  the Lee-2002 one-liner inline. OK, or would you prefer I build a Lee `bbnw`
  model and call `compute_Y` (heavier; prep is otherwise model-free)?
  A. Build a Lee `bbnw` model and call `compute_Y`
- `init` is computed from the **perturbed/observed** `Rrs` (what an algorithm
  sees), not the clean `Rrs` — confirm that's intended.
  A. I am not sure.  What module and lines are this?  I will examine.
  > Info (JXP to examine): `ioptics/prep.py` — `prep_one` calls
  > `init = _init_from_rrs(wave, Rrs_out)` at **line 153**, where `Rrs_out` is the
  > perturbed spectrum returned by `attach_noise` (line 147); the helper
  > `_init_from_rrs` is at **lines 70–93**. **Recommendation: keep using the
  > observed (perturbed) `Rrs`.** The design says `init` is "derived from the
  > *observed* Rrs", and an algorithm's least-squares start should be seeded from
  > exactly the spectrum it will fit, so the benchmark stays honest. (`Rrs_clean`
  > is still kept on the record if you ever want a noise-free init as a
  > diagnostic.) Easy to switch to `Rrs_clean` if you prefer a less noisy seed.
- Spectral truth `Spectrum` objects are tagged `units='1/m'` for all components
  (a, bb, a_ph, a_dg, bb_p, a_w, bb_w). Right for every one?
  A. Yes right for every one.
- `_build_truth` aligns every spectral component from the single `RawObs.wave`
  (so L23 `truth_interp` is always `False`). PANGAEA truth arrives on per-family
  grids — should `RawObs` carry per-component `(wave, vals)`, generalized in
  Stage 6, or handle it some other way?
  A. I am not sure.  What do you recommend?
  > Recommendation: **defer to Stage 6, with a small, already-paved extension.**
  > The hard part — `_align_truth(src_wave, src_vals, wave)` — is already general
  > (it interpolates from any source grid, leaves out-of-range `NaN`, and flags
  > the regrid). Only two things need to change when PANGAEA lands: let a
  > `RawObs.truth` value be **either** a plain array on `RawObs.wave` (L23, today)
  > **or** a `(src_wave, values)` pair (PANGAEA per-family grids), and have
  > `_build_truth` dispatch on that. No L23 impact, no change to `PreparedRecord`.
  > I'd not build it now (YAGNI for Stage 1); the seam is ready when Stage 6 needs
  > it.
- `prep_dataset` defaults `obs_ids` to **all** the adapter enumerates (~3320 for
  L23). Keep "all by default", or cap/require an explicit range?
  A. I am not sure.  What lines of code are you referring to?  I will examine.
  > Info (JXP to examine): `ioptics/prep.py` — `prep_dataset` at **line 169**;
  > the default is `if obs_ids is None: obs_ids = adapter.obs_ids(**load_opts)` at
  > **lines 196–197** (for L23 that's `range(3320)`). **Recommendation: keep
  > "all by default" with no cap.** It matches the design (`prep_dataset` maps
  > over ALL obs with a usable Rrs) and the caller already controls scope — the
  > Stage-1 exit explicitly calls `prep_dataset('L23', range(50))`. A silent cap
  > would be a surprising truncation; if anything, a sweep config sets the range.

**Task 5 (new questions).**

- For the Tier-2 L23 tests (Task 6), do you want a light **truth-vs-`init`
  sanity check** (e.g. retrieved-free `init['Chl']` within ~0.5 dex of
  `truth['Chl']` on a clear-water row), or keep Tier-2 as pure smoke (shapes,
  keys, `varRrs>0`, `noise_seed` recorded)?
- `truth['Sdg']` can come back `NaN` if bing's exp fit fails on some L23 rows.
  prep stores it as-is and metrics will skip `NaN` later. OK for Stage 1, or
  should `prep_one` flag/quarantine records with `NaN` scalar truth?

## Logs

### 2026-06-23 (Stage 1, Task 1: `datasets.py` — registry + L23 adapter)

Filled the `datasets.py` stub with the dataset registry and the L23 adapter.

- **Registry.** `ADAPTERS` dict + `register_dataset`/`get_adapter`/
  `available_datasets`, and a `runtime_checkable` `Adapter` Protocol
  (`obs_ids`, `load_obs`). New internal **`RawObs`** dataclass (`wave`, `Rrs`,
  `truth`, `Rrs_err=None`, `meta={}`) — the carrier prep consumes.
- **L23 adapter.** `L23Adapter` loads via `ocpy.hydrolight.loisel23.load_ds(X, Y)`
  (cached per `(X, Y)`). `obs_ids` → `range(N)`; `load_obs` returns native-grid
  `Rrs` + truth: spectral `a, bb, a_ph, a_dg, bb_p, a_w, bb_w` and scalars
  `Chl, Y, Sdg`. Registered as `'L23'`.
- **[Revised in Task 3]** Originally replicated Lee-2002 `Y` and `Sdg` locally to
  keep `datasets.py` bing-free; the Task-3 correction ("use BING") replaced that
  with a direct `bing.fitting.l23.load_one_l23` call, so the adapter now reuses
  bing's canonical L23 truth extraction.
- **Verification (`ocean14`).** Registry seeds `['L23']`; adapter satisfies the
  `Adapter` Protocol; `RawObs` defaults independent; helpers correct (`Sdg`
  recovered to 1e-3 on synthetic input). Full suite **46 passed** (run from the
  IOPtics repo root — note `pytest` will otherwise collect a sibling repo's
  tests if the shell `cwd` drifted).
- **Learned.** `bing.models.functions.fit_Sdg` fits over a fixed 400–525 nm
  window with pivot 440 nm; replicating it (vs importing) is the clean way to
  keep the data layer bing-free.

### 2026-06-23 (Stage 1, Task 2: `noise.py`)

Filled the `noise.py` stub with `attach_noise`.

- **API.** `attach_noise(wave, Rrs, model='pace', *, add_noise=True, seed=None,
  Rrs_err=None)` → `(varRrs, Rrs_out, Rrs_clean, tag, seed_used)` — the tuple
  maps straight onto `PreparedRecord` (`varRrs`, `Rrs`, `Rrs_clean`,
  `noise_model`, `noise_seed`). Three models: `pace`
  (`gen_noise_vector(wave)**2`, native grid), `insitu` (`Rrs_err**2`), `pct:X`
  (`(X·Rrs)**2`). Added `Rrs_err` kwarg (design sketch omitted it) for the
  insitu path. Perturbation is a local `np.random.default_rng(seed)` draw — no
  bing import (boundary kept).
- **Tests.** `tests/test_noise.py` (7 Tier-1): pct variance+tag, seed
  reproducibility (same seed identical, different seeds differ, `Rrs_clean`
  preserved), insitu passthrough + missing-error error, unknown-model and
  bad-pct errors.
- **Verification (`ocean14`).** Suite **53 passed** (46 + 7). Also smoke-tested
  the `pace` path live: σ interpolated onto a 13-band grid (6e-5…6e-4),
  `varRrs>0`, perturbation applied, seed recorded — works off ocpy's bundled
  `PACE_error.csv` (no `$OS_COLOR` needed).
- **Learned.** `ocpy.satellites.pace.gen_noise_vector` already returns the
  absolute PACE Rrs σ interpolated to the requested grid, so the PACE noise
  model needs no resampling — exactly what the native-grid decision wants.

### 2026-06-23 (Stage 1, Task 3: Misconceptions — use BING; Q&A = questions)

Corrected two misconceptions JXP flagged, in code and docs.

- **Use BING (it's a dependency).** Rewrote `L23Adapter.load_obs` to call
  `bing.fitting.l23.load_one_l23(idx, ds=ds)` and map its return dict onto the
  IOPtics truth keys (`aph→a_ph`, `adg→a_dg`, `bbnw→bb_p`, `aw→a_w`, `bbw→bb_w`,
  + `a, bb, Chl, Y, Sdg`). Removed the locally-replicated `_lee2002_Y`/`_fit_Sdg`
  and the `A_RRS`/`B_RRS` constants — the adapter now reuses bing's canonical
  truth extraction instead of re-deriving it. (ds still loaded/cached via ocpy
  and passed in, so `(X, Y)` selection + batch caching are preserved.)
- **Q&A = open questions.** Updated the Conventions to state that Q&A holds
  questions for JXP (no self-answers; JXP answers before the next task) and
  reformatted this stage's Q&A to questions-only — the rationale already lives in
  the Logs. Also relaxed the Conventions dependency-boundary bullet: ocpy **and
  bing** are first-class deps; the data layer may call bing where it's the
  natural source, while `metrics`/`diagnostics`/`report` stay engine-free.
- **Design doc.** Updated the implementation doc's module-granularity dependency
  boundary so it permits `datasets` to import bing for dataset-specific truth
  extraction (and bumped its version).
- **Verification (`ocean14`).** Adapter still satisfies the `Adapter` Protocol;
  replicated helpers confirmed gone; truth map yields the 10 expected keys; full
  suite **53 passed** (real-data `load_one_l23` path remains Tier-2,
  `@needs_l23`, for Task 5).

### 2026-06-24 (Stage 1, Task 4: `prep.py`)

Filled the `prep.py` stub with `prep_one` / `prep_dataset` plus three helpers.

- **`prep_one(dataset, obs_id, *, noise, add_noise, seed, wv_min, wv_max,
  **load_opts)`.** Dataset-aware defaults (`noise='pace'`+`add_noise=True` for
  L23, `insitu`/no-perturb otherwise); loads via the adapter, applies an
  optional `[wv_min,wv_max]` trim (to `Rrs` and any errors), calls
  `attach_noise`, builds truth, derives `init`, and assembles a fully-populated
  `PreparedRecord` (every field incl. `Rrs_clean`, `noise_model`, `noise_seed`).
- **Truth alignment.** `_align_truth` interpolates a component onto `wave` with
  out-of-range → `NaN` (no extrapolation) and flags genuine regrids; an exact
  subset (trim) is **not** a regrid. `_build_truth` wraps spectral truth as ocpy
  `Spectrum` (`units='1/m'`, native grid in `metadata['orig_wave']`) and packs
  scalars as floats. For L23 all spectral truth shares the native grid, so
  `truth_interp` is `False` throughout.
- **`init`.** `_init_from_rrs` from the observed (post-noise) `Rrs`: `Chl` via
  `ocpy.chl.band_ratios.oc4`, `Y` via `bing.rt.rrs.Rrs_to_rrs` + the Lee-2002
  440/555 one-liner. Truth-free by construction (uses observed `Rrs`, never
  `truth`).
- **`prep_dataset`.** Maps `prep_one` over `obs_ids` (default: all the adapter
  enumerates); per-record seed = `seed + index`; `ProcessPoolExecutor` when
  `n_cores>1` via a top-level `_prep_one_star` worker (picklable). ocpy/bing
  imports are lazy (inside the helpers), so `import ioptics.prep` stays cheap.
- **Verification (`ocean14`).** Drove `prep_one`/`prep_dataset` through a
  synthetic adapter: all fields set, `Rrs` perturbed with `Rrs_clean` preserved,
  truth `Spectrum` on `wave` (+`orig_wave`), `truth_interp` correct, `init`
  computed, **picklable** round-trip preserves the truth Spectrum; `_align_truth`
  interp+NaN path verified; per-record seeds `seed+i`. Full suite **53 passed**.
  Real-data `prep_dataset('L23', …)` is Tier-2 (`@needs_l23`) — Task 5.
- **Note.** `_build_truth` aligns from a single `RawObs.wave`; per-component
  truth grids (PANGAEA) are a Stage-6 generalization (see Q&A).

### 2026-06-24 (Stage 1, Task 5: apply Q&A answers)

JXP answered the open Q&A; applied the answers in code and added info/recos.

- **Code change — `init['Y']` via bing's Lee model.** Per JXP's answer, replaced
  the inline Lee-2002 one-liner in `prep._init_from_rrs` with
  `bing.models.bbnw.init_model('Lee', wave, prior_dicts=None)` →
  `lee.compute_Y(rrs[440], rrs[555])` → read `lee.Y`. Keeps the prescription in
  lock-step with bing's `bbNWLee` (no duplicated formula). Verified the value is
  identical to the previous inline result (Y=1.3281 on the synthetic check); full
  suite **53 passed**.
- **Confirmed (no change):** use bing's full `load_one_l23` dict; drop
  `anw`/`bbnw`; keep `meta['Y']` vs `truth['Y']` names; keep `attach_noise`'s
  `Rrs_err=` kwarg; `add_noise`+`seed=None` non-reproducible is acceptable;
  `units='1/m'` on all spectral truth.
- **Answered JXP's questions-back-to-me** in the Q&A (with code line refs):
  (a) `init` uses the observed/perturbed `Rrs` (`prep.py:153`, helper 70–93) —
  recommended keeping (honest seed; `Rrs_clean` available if not); (b)
  per-component truth grids — recommended deferring to Stage 6, noting
  `_align_truth` is already general so only `RawObs`/`_build_truth` need a small
  dispatch; (c) `prep_dataset` "all by default" (`prep.py:196–197`) — recommended
  keeping (matches design; caller controls scope; no silent cap).
- **New questions** raised for Task 6: whether Tier-2 L23 tests should include a
  light truth-vs-`init` sanity check, and how to handle `NaN` `truth['Sdg']` from
  occasional failed exp fits.

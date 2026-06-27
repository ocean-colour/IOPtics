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
7. Execute the 7th task (Q&A).

### Pull Request

1. I have issued a PR for this stage. Please review it and post it to GitHub.  Also, investigate the CI issues and fix them. Please log your work in the Logs section below.

2. Please read the PR and make any needed changes to the code to address the comments.  And, if you have any additional questions, please add them to the Q&A section below. Log your work.

3. Please explain further what you mean by "package ocpy's
  `PACE_error.csv` via `package_data`/`MANIFEST`.".  Maybe generate a prompt for me that I can execute on that package.

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

7. **Q&A**. I have answered your Q&A and fixed the CI issue.  Please see my answers.  Make any needed changes to the code to reflect the answers.  And, if you have any additional questions, please add them to the Q&A section below. Log your work.

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
  A. That is fine

**Task 5 (new questions).**

- For the Tier-2 L23 tests (Task 6), do you want a light **truth-vs-`init`
  sanity check** (e.g. retrieved-free `init['Chl']` within ~0.5 dex of
  `truth['Chl']` on a clear-water row), or keep Tier-2 as pure smoke (shapes,
  keys, `varRrs>0`, `noise_seed` recorded)?
  A. Yes, add the light test
- `truth['Sdg']` can come back `NaN` if bing's exp fit fails on some L23 rows.
  prep stores it as-is and metrics will skip `NaN` later. OK for Stage 1, or
  should `prep_one` flag/quarantine records with `NaN` scalar truth?
  A. Yes, this is OK for Stage 1.

**Task 6 (new question).**

- The L23 data tree is now mounted, so all three Tier-2 `@needs_l23` tests
  **run and pass** here (not just on your machine) — including the truth-vs-init
  Chl check (median < 0.5 dex on real L23). Stage 1's exit criterion is met. Do
  you want a Stage-1 PR + readthedocs check (as in Stage 0), or proceed straight
  to Stage 2?
  A. We want a Stage-1 PR + readthedocs check

**PR review (PR #4) — needs your confirmation.**

- I had to **reverse the Task-5 decision** (build a Lee `bbnw` model for
  `init['Y']`): constructing any `bbnw` model runs `bbNWModel.init_bbw`, which
  loads L23 `Hydrolight400.nc`, so it coupled prep of *every* dataset to the L23
  tree and broke CI. I reverted to the inline Lee-2002 formula (identical value,
  data-free; still uses bing's `Rrs_to_rrs`). Confirm this reversal is OK?
  A. Explain further.  What was the problem?
  > Explanation. `init['Y']` is the truth-free backscatter-slope **seed** for the
  > fit, computed from the observed `Rrs`. Task 5 asked me to compute it by
  > building a bing Lee `bbnw` model and calling `compute_Y`. The problem is a
  > hidden side effect in the **constructor**: `bbNWLee.__init__` →
  > `bbNWModel.__init__` → `init_bbw()`, and `init_bbw()` runs
  > `ocpy.hydrolight.loisel23.load_ds(4, 0)` — it **reads the L23
  > `Hydrolight400.nc` file** to set pure-water backscattering `bb_w` (bing's
  > analytic `betasw_ZHH2009` path is commented out). So just to get one scalar
  > slope, `prep_one` would load the L23 X=4 dataset — for **every** dataset, even
  > non-L23, and even with no fit happening. Wherever that file isn't mounted
  > (fresh checkout, **CI**, a PANGAEA-only run) `prep_one` dies with
  > `FileNotFoundError: Hydrolight400.nc`. That's exactly what broke the Tier-1
  > fake-adapter prep tests once the L23 tree was unmounted. The inline Lee-2002
  > line (`Y = 2.2*(1 − 1.2·exp(−0.9·rrs₄₄₀/rrs₅₅₅))`, `rrs` from bing's
  > `Rrs_to_rrs`) is the **same formula** `bbNWLee.compute_Y` uses (verified
  > bit-identical: Y=1.4127 both ways) but needs no model and no data. This only
  > affected prep's truth-free init; when Stage 2's `run`/`evaluate` build models
  > for a real L23 fit, that L23 load is expected and fine. Reverted unless you
  > object.

- CI for PR #4 is **red for an upstream reason**: the ocpy installed from
  `git+…@main` lacks `ocpy.spectra` and the bundled `PACE_error.csv` — both live
  on your local ocpy `panagea` branch (~30 commits ahead of `main`). Do you want
  to merge ocpy `panagea`→`main` (and package the data files), or should I pin
  `requirements.txt` to `ocpy@panagea` as a stopgap so IOPtics CI goes green?
  A. I have fixed this.
  > Status. Thanks. Confirmed `ocpy.spectra` imports here, and `requirements.txt`
  > is unchanged (no `@panagea` pin needed — your upstream fix is the right call).
  > Two things still gate a green PR #4, both needing a commit + CI re-run (I
  > don't run git): (1) the `prep.py` inline-`Y` fix is in the **working tree,
  > uncommitted** — without it CI still dies on `Hydrolight400.nc`; (2) PR #4's
  > shown checks are the **stale** failed runs from before the fixes. Once the
  > `prep.py` fix is committed/pushed and CI re-runs against the fixed ocpy, I
  > expect green (Tier-1 pass on 3.12/3.14, Tier-2 skip on the runner).

**Task 7 (new question).**

- Both fixes (your ocpy update + my `prep.py` revert) need to land on the
  `stage-1` branch and CI re-run to confirm green. Do you want me to **verify
  PR #4 CI is green** (and re-post a short approving review note) after you push,
  or are we treating Stage 1 as done and moving to Stage 2?

**PR prompt 2 (new questions).**

- PR #4 is now **green and MERGEABLE/CLEAN** (you committed the fixes in
  `9ae5cd5`), with **no outstanding review comments** to address — my own review
  is fully actioned, and there are no other comments. So I made no code changes
  this task. Anything specific you wanted addressed that I'm not seeing?
- The only items still open are the two **upstream** follow-ups from my review:
  publish `bing.rt.rrs.Rrs_to_rrs` to bing `main`, and package ocpy's
  `PACE_error.csv` via `package_data`/`MANIFEST`. Those live in the bing/ocpy
  repos — do you want me to prepare those changes there, or are they yours? (Not
  blocking #4; IOPtics is robust to their absence.)
- Otherwise: merge #4 and proceed to **Stage 2** (engine wrap: algorithms +
  run·chisq + evaluate + io + provenance)?

**PR prompt 3 — explanation: "package ocpy's `PACE_error.csv`".**

- What I meant: a pip-installed Python package ships **only `.py` files** unless
  you explicitly declare data files. `gen_noise_vector` loads
  `importlib.resources.files('ocpy').joinpath('data/satellites/PACE_error.csv')`,
  but ocpy's `setup.py` uses `find_packages()` with **no `package_data`, no
  `include_package_data`, and no `MANIFEST.in`** — and `ocpy/data/` has no
  `__init__.py`, so `find_packages()` skips it. Result: none of the 34
  `ocpy/data/**` files land in the install, so a fresh `pip install` of ocpy
  can't find `PACE_error.csv` (the CI failure). "Package it via
  `package_data`/`MANIFEST`" = the two standard knobs that tell setuptools to
  **include those data files in the wheel/sdist**.
- I wrote a ready-to-run prompt for the ocpy repo:
  [`claude_prompts/ocpy_package_data_fix.md`](ocpy_package_data_fix.md) — it has
  the root cause, the exact `setup.py` + `MANIFEST.in` edits (covers **all** of
  `ocpy/data`, not just PACE), and a verification that builds the wheel and
  confirms the data file is inside + the reader works. Run it in `ocpy`.

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

### 2026-06-25 (Stage 1, Task 6: tests — Stage 1 complete)

Added the dataset/noise/prep test modules; Stage-1 exit criterion met.

- **`test_datasets.py`** (6 Tier-1 + 1 Tier-2): registry seeded with L23,
  `Adapter` protocol, register/retrieve round-trip, `RawObs` default
  independence, the L23 truth-key map (anw/bbnw absent), and the `X=2` guard
  (rejects before any load). Tier-2 `@needs_l23`: `load_obs(0)` — native
  ascending grid, `Rrs` aligned, all 10 truth keys (spectral arrays on grid,
  scalar floats), `meta` X/Y.
- **`test_prep.py`** (9 Tier-1 + 2 Tier-2): `_align_truth` (exact grid, subset
  not-a-regrid, off-grid interp with NaN edges); `prep_one` populates every
  field, truth as `Spectrum` on `wave` (+`orig_wave`, `truth_interp` False),
  truth-free finite `init`, trim, **picklable**; `prep_dataset` per-record seeds
  `seed+i`. Tier-2 `@needs_l23`: `prep_dataset('L23', range(5))` smoke
  (shapes, `varRrs>0`, truth keys, `noise_seed` recorded) + the light
  truth-vs-`init` Chl check JXP approved (median `|log10(init/truth)| < 0.5` dex).
- **`test_noise.py`**: added a Tier-1 `pace` test (bundled CSV, native grid).
- **Verification (`ocean14`).** Full suite **72 passed**. The L23 tree is now
  mounted, so the 3 Tier-2 `@needs_l23` tests **ran and passed against real
  data** (not skipped) — including the init-vs-truth Chl check, which validates
  the OC4 `init` Chl tracks truth within 0.5 dex on real L23.
- **Stage-1 exit criterion MET:** `prep.prep_dataset('L23', range(50))` returns
  valid `PreparedRecord`s (Tier-2, real data) and the Tier-1 synthetic-record
  tests pass in `ocean14`.

### 2026-06-25 (PR review: PR #4 "Stage 1" — found CI-red, fixed one bug)

Reviewed PR #4 (`stage-1` → **`main`**, 49 files; folds Stage 0 + Stage 1) and
posted a COMMENTED review to GitHub (self-approval blocked).

- **CI is RED** — all 4 Tier-1 jobs (py3.12/3.14) failed. From the run logs, two
  upstream-ocpy causes: `ModuleNotFoundError: ocpy.spectra` (prep/datasets truth
  `Spectrum`) and `FileNotFoundError: ocpy/.../PACE_error.csv` (pace noise). The
  ocpy installed from `git+…@main` lacks both; they live on the local ocpy
  **`panagea`** branch (~30 commits ahead of `origin/main`). Resolution is
  upstream: merge ocpy `panagea`→`main` + package the data files (or pin
  `requirements.txt` to `@panagea`). Flagged; **do not merge until CI is green.**
- **IOPtics bug found & fixed.** `prep._init_from_rrs` built a bing Lee `bbnw`
  model for `init['Y']` (Task-5 choice), but `bbNWModel.init_bbw` loads L23
  `Hydrolight400.nc` — coupling prep of *any* dataset to the L23 tree and
  breaking it where absent (incl. CI). **Reverted to the inline Lee-2002
  formula** (identical value, data-free; still uses bing's `Rrs_to_rrs`). This
  reverses the Task-5 Q&A decision — surfaced for JXP's confirmation. After the
  fix: **69 passed + 3 skipped** with no L23 tree (CI-equivalent), **72 passed**
  with it; `sphinx-build -W` clean.
- **Learned.** A green local suite can mask two independent gaps: (1) a complete
  *local* ocpy that the CI `@main` install doesn't match, and (2) a bing model
  ctor with a hidden data-load side effect. The unmounting of the L23 tree this
  turn is what exposed both — worth running the suite **without** `$OS_COLOR`
  (CI-equivalent) before declaring a data-layer stage done.

### 2026-06-26 (Stage 1, Task 7: apply PR-review Q&A answers)

JXP answered the PR-review Q&A (asked me to explain the bug further; fixed the
ocpy CI issue upstream). Responded and re-verified.

- **Explanation provided** (in Q&A) for the Lee-model problem: building any bing
  `bbnw` model runs `bbNWModel.init_bbw` → `loisel23.load_ds(4, 0)`, reading
  `Hydrolight400.nc`, so the Task-5 init-`Y` approach pulled the L23 X=4 data
  load into prep for every dataset and crashed wherever that file is absent
  (fresh checkout / CI / PANGAEA-only). The inline Lee-2002 line is the identical
  formula (Y=1.4127 both ways), data-free.
- **Code state:** the `prep.py` revert (inline `Y`) stands — JXP didn't object,
  asked to understand. No new code change needed this task. `requirements.txt`
  unchanged (JXP fixed ocpy upstream, so no `@panagea` pin).
- **Re-verified.** CI-equivalent run (`env -u OS_COLOR pytest`) → **69 passed,
  3 skipped** (Tier-2 `@needs_l23` skip). `sphinx-build -W` docs build clean
  (readthedocs check, per the Task-6 answer). `ocpy.spectra` imports.
- **Flagged (needs JXP, who runs git):** the `prep.py` fix is uncommitted in the
  working tree and PR #4's shown checks are the stale pre-fix failures — both
  fixes (ocpy upstream + this `prep.py` revert) must land on `stage-1` and CI
  re-run before #4 is green/mergeable. Posed as the Task-7 new question.

### 2026-06-26 (PR #4: investigate + fix remaining CI failures)

JXP committed the earlier fixes (`c6efea3`) and CI re-ran — `ocpy.spectra` now
imports, but **2 new failure causes** surfaced, both from CI installing
`bing`/`ocpy` at `git@main` (behind the local dev copies):

- **6× `test_prep`** — `ImportError: Rrs_to_rrs` not in `bing.rt.rrs@main`
  (prep used it for the `init['Y']` rrs conversion).
- **1× `test_noise::test_pace_model_native_grid`** — ocpy's install lacks
  `data/satellites/PACE_error.csv`.

**Fixes (IOPtics-side, committable):**
1. **Inlined the Gordon `Rrs→rrs`** in `prep._init_from_rrs`
   (`rrs = Rrs/(0.52 + 1.7·Rrs)`, constants mirroring `bing.rt.rrs`), dropping
   the `bing.rt.rrs.Rrs_to_rrs` import. `prep` is now **bing-free** and robust to
   the bing version; `init['Y']` is bit-identical (verified Y=1.4127 on the
   synthetic Rrs). The only remaining bing import is the lazy `load_one_l23` in
   the L23 adapter — Tier-2 only, skipped on CI.
2. **Added `needs_pace`** skip guard (`conftest`) probing
   `ocpy.satellites.pace.gen_noise_vector`; applied to the pace test so it skips
   where ocpy doesn't ship the CSV (still runs locally).

**Verification.** CI-equivalent (`env -u OS_COLOR pytest`) → **69 passed,
3 skipped**; prep is bing-free (grep clean). On the runner I expect Tier-1 green
(prep passes, pace skips, L23 Tier-2 skips).

**Posted** a follow-up review on PR #4 with the investigation, the two fixes, and
**upstream follow-ups** (publish `Rrs_to_rrs` to bing `main`; package
`PACE_error.csv` in ocpy via `package_data`/`MANIFEST`). Needs commit+push to
`stage-1` + CI re-run to confirm green (JXP runs git).

**Learned.** The CI-vs-local gap recurs per dependency: after ocpy `spectra` was
fixed, the *same class* of gap appeared for bing (`Rrs_to_rrs`) and ocpy data
packaging. Making IOPtics robust to the **released** bing/ocpy (inline trivial
formulas, skip-guard bundled-data tests) is more reliable than tracking unmerged
upstream branches.

### 2026-06-27 (PR #4: read comments / address — nothing to change)

Re-read PR #4 after JXP committed the CI fixes (`9ae5cd5`).

- **CI is green** — all 4 Tier-1 jobs (py3.12/3.14) pass. PR is **OPEN,
  MERGEABLE, mergeStateStatus CLEAN**.
- **No outstanding comments to address.** Inline review comments: none; issue
  comments: none; reviews: only my own (`profxj COMMENTED`), already fully
  actioned (the two CI fixes are now committed). So **no code changes were
  needed** this task — confirmed the working tree has no non-prompt drift and
  the CI-equivalent suite is **69 passed, 3 skipped**.
- The only still-open items are the two **upstream** follow-ups my review raised
  (publish bing `Rrs_to_rrs` to `main`; package ocpy `PACE_error.csv`) — bing/
  ocpy repo work, not IOPtics; surfaced as questions for JXP. PR #4 doesn't
  depend on them (IOPtics is robust to their absence).
- Did **not** fabricate changes for a clean PR; reported state instead.

### 2026-06-27 (PR prompt 3: explain ocpy data-packaging; write fix prompt)

JXP asked what "package ocpy's `PACE_error.csv` via `package_data`/`MANIFEST`"
means and for a prompt to run on ocpy.

- **Diagnosed ocpy's packaging.** `setup.py` = `find_packages()` only; **no**
  `package_data`, `include_package_data`, or `MANIFEST.in`, and `ocpy/data/`
  isn't a package (no `__init__.py`). Confirmed `find_packages()` returns no
  data package and that all **34** `ocpy/data/**` files are excluded from an
  install — which is why `importlib.resources.files('ocpy')/.../PACE_error.csv`
  is missing on a fresh pip install (the CI `pace` failure).
- **Explanation** added to Q&A (the `.py`-only default + the two setuptools knobs
  that include data files).
- **Wrote a standalone, runnable prompt** for the ocpy repo:
  `claude_prompts/ocpy_package_data_fix.md` — root cause, exact edits
  (`MANIFEST.in: recursive-include ocpy/data *`; setup.py
  `include_package_data=True` + `package_data={'ocpy': ['data/**/*']}`; optional
  removal of obsolete `use_2to3`/`pytest-runner`), and a verification that builds
  the wheel, checks `PACE_error.csv` is inside, installs clean, and runs
  `gen_noise_vector`. Scoped to **all** of `ocpy/data` (MODIS/SeaWiFS/water/
  phytoplankton/COASTLOOC), not just PACE.
- No IOPtics code changed (this was an explanation + an external-repo prompt).

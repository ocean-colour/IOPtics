# Code IOPtics — Stage 0: Scaffolding & contracts

## Goal

Stand up the `ioptics/` package skeleton and the load-bearing **contracts** every
later stage depends on. **Exit criterion:** `import ioptics` works; a sample sweep
YAML round-trips to objects; Tier-1 tests for `records`/`config` pass in
`ocean14`; CI is green (all data-dependent tests skipped).

Implements **Package layout** and the **Staged implementation plan / Stage 0** of
`docs/design/IOPtics_implementation.md` (the authoritative *how*). One prompt per
module below.

## Conventions

- Write code in/for the **`ocean14`** conda environment.
- Clear docstrings; match the house style in `ocpy`/`bing`.
- The user (JXP) runs all git commands — do not commit.
- After each module: run `pytest -q` in `ocean14`, record results, Q&A, Log.

## Context

- `docs/design/IOPtics_implementation.md` — §Package layout (tree, module table,
  data flow), §Retrieval & run (`PreparedRecord`/`RetrievalResult` schemas),
  §Algorithm registry (the YAML sweep surface `config` must parse).
- `docs/design/IOPtics_design.md` — the design *what/why*.
- `ioptics/__init__.py` already carries `__version__`.

## Prompts

### Coding

1. Execute the 1st task under "Modules/Tasks" (package skeleton + `records.py`).
2. Execute the 2nd task under "Modules/Tasks" (`config.py`).
3. Execute the 3rd task under "Modules/Tasks" (`tests/conftest.py` + CI + Tier-1 tests).
4. Execute the 4th task under "Modules/Tasks" (Pull Request).
5. Execute the 5th task under "Modules/Tasks" (Pull Request edits).
6. Execute the 6th task under "Modules/Tasks" (readthedocs.io setup).
7. Execute the 7th task under "Modules/Tasks" (modify `coding_prompts_stage01.md`).

## Modules

### Tasks

1. **Package skeleton + `ioptics/records.py`.** Create the module files from the
   Package-layout tree as stubs (`config`, `records`, `datasets`, `prep`, `noise`,
   `algorithms/{spec,registry}`, `run`, `evaluate`, `provenance`, `io`, `metrics`,
   `diagnostics`, `plotting`, `report/{figures,tables,leaderboard,bokeh,rst,standard}`,
   `runs/`, `tests/`). Implement `records.py` fully: the `PreparedRecord`,
   `RetrievalResult`, and `ComponentFit` dataclasses exactly per §Data preparation
   / §Retrieval & run (fields, types, defaults; picklable). Add Tier-1 unit tests
   constructing each from synthetic values. Q&A. Log.

2. **`ioptics/config.py`.** Implement the YAML ⇄ Python sweep-config surface per
   §Algorithm registry (YAML example) and §Driving a sweep: load + **validate**
   (required `sweep_id`; `datasets`; `algorithms` as names or name+overrides;
   sweep-level `noise_model` and `fit_method`; `mcmc_subset`; per-algorithm
   `fit_method` override but **not** `noise_model`). Resolve to plain config
   objects (algorithm specs are filled in Stage 2 — for now resolve names +
   overrides into a neutral structure). Provide `dump()` for the provenance copy.
   Tier-1 tests: round-trip, missing-`sweep_id` error, override rules. Q&A. Log.

3. **`tests/conftest.py` + CI + smoke.** Add the skip guards
   (`needs_data`/`needs_l23`/`needs_pangaea`) per §Testing & CI; an import/smoke
   test (`import ioptics`); and the CI workflow (recreate `ocean14` or install
   `requirements.txt` + `ocpy`/`bing` from `@main`; run `pytest -q`; advisory, no
   coverage gate). Q&A. Log.

4. **Pull Request.**   I have issued a PR for this stage. Please review it and post it to GitHub.  Please log your work in the Logs section below.

5. **Pull Request edits.** Please make any edits to the project that are needed to address the PR comments. Log your work.

6. **readthedocs.io setup.** Please setup for providing the docs on readthedocs.io.  Generate all necessary files and directories.  Test it. Log your work.  

7. **Modify `coding_prompts_stage01.md`.**  We are ready to proceed to Stage 1.  Please modify the `coding_prompts_stage01.md` file to reflect the changes you made during Stage 0.  Log your work.

### Q&A

**Task 1 (skeleton + `records.py`).**

- *Q: Which fields get defaults?* The implementation doc shows a default only for
  `PreparedRecord.meta` (`field(default_factory=dict)`); I matched it exactly —
  every other `PreparedRecord` field is required. For `RetrievalResult` the doc
  comments imply `status='ok'` is the normal value, so I gave the trailing
  fields sensible defaults (`components/params/scalars/stats` → empty-dict
  factories, `status='ok'`, `provenance_id=''`) while keeping the four key
  fields — `dataset/obs_id/algorithm/fit_method` — required. `ComponentFit` has
  no defaults (all six arrays required).
- *Q: `int | str` unions on 3.12?* Yes, but I also added
  `from __future__ import annotations` so the union/`X | None` syntax is safe
  everywhere and annotations stay strings (no eval cost).
- *Q: `runs/` an importable package?* No — per §"Driving a sweep" it holds
  versioned build scripts, not library code, so I added a `runs/README.md`
  describing the `prototypes/<name>/build_vN.py` + `run_vN.yaml` layout rather
  than an `__init__.py`. (`find_packages()` therefore skips it, as intended.)
- No blocking questions; the `PreparedRecord`/`RetrievalResult`/`ComponentFit`
  schemas in §"Data preparation" and §"Retrieval & run" were complete.

**Task 2 (`config.py`).**

- *Q: How "neutral" should resolved algorithms be?* Per the task ("algorithm
  specs are filled in Stage 2 — for now resolve names + overrides into a neutral
  structure"), an algorithm entry resolves to an `AlgorithmConfig(name,
  fit_method, overrides)` carrier — **not** an `AlgorithmSpec`. `fit_method` is
  surfaced (it's validated and read by `run`); every other override (e.g.
  `mcmc`, `rt`, priors) is passed through verbatim in `overrides` for Stage-2
  resolution. No registry lookup is done yet (registry is Stage 2).
- *Q: What guarantees the provenance round-trip?* `dump()` re-emits a **canonical**
  mapping from the structured fields (not the raw bytes); `load(dump(cfg)) ==
  cfg` holds. To keep that equality clean, `source_path` is stored with
  `compare=False` so a from-file load equals a from-string load, and a
  bare-string algorithm (no overrides) dumps back as a bare string.
- *Q: Strict or lenient on unknown top-level keys?* Lenient/forward-compatible:
  unknown keys (e.g. a free-form `note`) are preserved in `extra` and re-emitted
  by `dump()`, so the provenance copy stays faithful. `seed` and `results_root`
  are recognized first-class (they appear in the doc's provenance block /
  §"Driving a sweep").
- *Q: Which values are validated?* `fit_method ∈ {chisq, mcmc}` (sweep-level
  **and** per-algorithm); `noise_model` non-empty string but otherwise free
  (`pace`/`insitu`/`pct:X`); `mcmc_subset` non-negative int; `seed` int. A
  per-algorithm `noise_model` is a hard `ConfigError` (Q14 — fixed sweep-level).
- *Decision:* added a dedicated `ConfigError(ValueError)` so tests can assert on
  it while existing `except ValueError` handlers still catch it.

**Task 3 (`conftest.py` + CI + smoke).**

- *Q: `_pangaea_available()` wasn't shown in the doc snippet — how to write it?*
  Mirrored ocpy's `test_pangaea.py`: call `pangaea.pangaea_path()` and treat a
  raised exception (it raises `FileNotFoundError` when the V3 dir is absent) as
  "unavailable". Wrapped all three probes in `try/except` so a missing/broken
  ocpy import makes guarded tests **skip**, never error collection.
- *Q: Does "import ioptics, registry seeded" apply now?* No — the registry is a
  Stage-2 deliverable, so the smoke test asserts only `import ioptics`, the
  three re-exported contracts, and that all 23 modules import cleanly. The
  "registry seeded" half of that CI check lands with Stage 2.
- *Q: Recreate `ocean14` or pip-install in CI?* Chose the pip path — it's
  simpler and `requirements.txt` already pulls ocpy/bing from their GitHub
  default (`main`) branches, satisfying "install requirements.txt + ocpy/bing
  from @main". Python pinned to **3.12** (the declared `setup.py` minimum;
  `ocean14` itself runs 3.14, but 3.12 is the safe CI baseline).
- *Q: "Advisory, not gating"?* Implemented as: job success == `pytest -q`
  success, with **no coverage floor and no fail-on-warning** added. Test
  failures still surface (red X), which is the intended pass/fail signal.
- *Note:* `$OS_COLOR` can be **set but point at a missing dir** (as in JXP's
  shell); `needs_data` guards on `os.path.isdir`, so it correctly resolves to
  "unavailable" and Tier-2 tests skip.


## Logging

The "Logs" section will record Claude's work. Please use the following format:

### <Date> (Short summary of the work)

<Detailed description of the work and what you learned>

...

## Logs

### 2026-06-22 (Task 1: package skeleton + `records.py`)

Stood up the full `ioptics/` package tree from the Package-layout section and
implemented `records.py` in full.

- **Skeleton.** Created docstring-only stubs (each tracing to its row in the
  module-responsibilities table) for `config`, `datasets`, `prep`, `noise`,
  `algorithms/{__init__,spec,registry}`, `run`, `evaluate`, `provenance`, `io`,
  `metrics`, `diagnostics`, `plotting`, and `report/{__init__,figures,tables,
  leaderboard,bokeh,rst,standard}`. Added `tests/__init__.py` and a
  `runs/README.md` placeholder (runs is build-scripts, not a package).
- **`records.py` (full).** Implemented `PreparedRecord`, `RetrievalResult`, and
  `ComponentFit` as plain dataclasses exactly per §"Data preparation" /
  §"Retrieval & run" — fields, types, and defaults as noted in Q&A. Used
  `from __future__ import annotations` for the `int | str` / `X | None` unions.
  `__init__.py` now lightweight-re-exports the three contracts (records depends
  only on numpy + dataclasses, so the top-level import stays cheap).
- **Tests.** Added `tests/test_records.py` (7 Tier-1, data-independent tests):
  construction of each dataclass from synthetic values, `RetrievalResult`
  defaults, the `meta` default-factory independence check, string/None obs_id +
  no-noise path, and a picklability round-trip (records must cross a process
  pool / disk cache).
- **Verification (`ocean14`).** `import ioptics` works and re-exports the three
  classes; all 22 stub modules import cleanly; `pytest -q
  ioptics/tests/test_records.py` → **7 passed**. Ran with
  `/home/xavier/miniforge3/envs/ocean14/bin/python` (conda not init'd for
  `activate` in this shell).
- **Learned.** The package's conda env lives at `miniforge3/envs/ocean14`. The
  `records` contracts are intentionally tiny and import-light, which keeps
  `ioptics.__init__` cheap to import — worth preserving as later modules pull in
  BING/ocpy/pandas.

### 2026-06-22 (Task 2: `config.py` — YAML ⇄ Python sweep config)

Implemented the sweep-config surface in `ioptics/config.py`, replacing the stub.

- **API.** `load(path)` / `loads(text)` / `from_dict(mapping)` → a validated
  `SweepConfig`; `dump(cfg, path=None)` (and `cfg.dump()`) → canonical YAML for
  the provenance copy. Two dataclasses: `SweepConfig` (sweep_id, datasets,
  algorithms, noise_model, fit_method, mcmc_subset, seed, results_root, extra)
  and `AlgorithmConfig` (name, fit_method, overrides) — the neutral algorithm
  carrier (no `AlgorithmSpec` until Stage 2). Added `ConfigError(ValueError)`.
- **Validation.** Required `sweep_id` (non-empty str), `datasets` (non-empty
  list of names), `algorithms` (non-empty; bare name **or** mapping with
  `name`); `fit_method ∈ {chisq, mcmc}` at sweep + per-algorithm level;
  `mcmc_subset` non-negative int; `seed` int; a **per-algorithm `noise_model`
  is rejected** (sweep-level only, Q14). Unknown top-level keys are preserved in
  `extra` (forward-compatible provenance).
- **Round-trip.** `dump()` re-emits a canonical mapping (`sort_keys=False`),
  bare-string algorithms stay bare, and `source_path` is `compare=False` so
  `load(dump(cfg)) == cfg` and from-file == from-string loads. Verified the
  rendered YAML by eye — matches the doc's headline example.
- **Tests.** Added `tests/test_config.py` (14 Tier-1 tests): field parsing,
  string round-trip, file load + dump-to-file, the three missing-required-field
  errors, per-algorithm `noise_model` forbidden, `fit_method` override allowed,
  bad fit_method (sweep + per-algorithm), bad `mcmc_subset`, extra-keys
  preservation, and the Python-API (`SweepConfig`/`AlgorithmConfig`) round-trip.
- **Verification (`ocean14`).** PyYAML 6.0.3 present; `pytest -q ioptics/tests/`
  → **21 passed** (7 records + 14 config).
- **Learned.** This satisfies the Stage-0 exit clause "a sample sweep YAML
  round-trips to objects." The neutral `AlgorithmConfig.overrides` passthrough
  is the seam Stage 2 will consume: `config` validates *shape*, the registry
  will validate *names* and build `AlgorithmSpec`s.

### 2026-06-22 (Task 3: `conftest.py` + CI + smoke — Stage 0 complete)

Added the test-tier scaffolding and CI, closing out Stage 0.

- **`tests/conftest.py`.** The Tier-1/Tier-2 split per §"Testing & CI": three
  skip-guard markers — `needs_data` (`$OS_COLOR` tree present via
  `os.path.isdir`), `needs_l23` (ocpy `loisel23.l23_path/Hydrolight100.nc`),
  `needs_pangaea` (ocpy `pangaea.pangaea_path()`). All probes are
  `try/except`-wrapped so collection never fails when ocpy/data is absent;
  guarded tests just skip.
- **`tests/test_smoke.py`.** Import/smoke check: `import ioptics` + version, the
  three re-exported contracts, and a parametrized clean-import of all 23
  package modules.
- **`.github/workflows/ci.yml`.** GitHub Actions: checkout → setup-python 3.12
  (pip cache) → `pip install -r requirements.txt` (which pulls ocpy/bing from
  their `main` defaults) + `pip install -e .` → smoke `import ioptics` →
  `pytest -q`. Advisory: no coverage gate, no fail-on-warning; Tier-2 skips on
  the runner (no `$OS_COLOR`).
- **Verification (`ocean14`).** `pytest -q` → **46 passed** (7 records + 14
  config + 25 smoke). The three availability probes all resolve `False` here
  (so Tier-2 would skip), markers construct, and the workflow YAML parses.
- **Stage-0 exit criterion met:** `import ioptics` works; the sample sweep YAML
  round-trips to objects; Tier-1 `records`/`config` tests pass in `ocean14`; CI
  is green with all data-dependent tests skipped.
- **Learned.** PyYAML reads a workflow's `on:` key as boolean `True` — a
  harmless parse quirk; GitHub Actions reads the raw file correctly. `$OS_COLOR`
  being *set but pointing at a missing dir* is a real local state, so guarding
  on `isdir` (not just the env var) matters.

### 2026-06-22 (Task 4: review & post PR #3 "Stage 0")

JXP opened **PR #3 "Stage 0"** (`stage-0` → `develop`, 31 files / +1428). Reviewed
it and posted the review to GitHub.

- **State checked.** All Stage-0 work was already committed (`72c4821 "go"`,
  pushed to `origin/stage-0`); PR mergeable; **GitHub CI green** — the
  `.github/workflows/ci.yml` I wrote ran on the runner, installing ocpy/bing
  from their `main` branches and passing `pytest -q` (~2 min/job).
- **Review pass.** Re-ran the suite locally (`ocean14` → **46 passed**),
  re-confirmed the YAML round-trip and import smoke, and probed `config` edge
  cases a reviewer would hit (empty file, bare-string `datasets`, non-name
  algorithm entry → clear `ConfigError`; duplicate algorithm names pass through,
  correctly deferred to the Stage-2 registry guard).
- **Posted.** Submitted a substantive review via `gh pr review 3 --comment`
  (GitHub blocks *approving* one's own PR — authed user is `profxj`, the author —
  so a COMMENTED review is the correct vehicle). The review records the verified
  exit criteria, strengths, and three non-blocking follow-ups (duplicate-name
  guard → Stage 2; CI Python 3.12 vs `ocean14` 3.14, consider a matrix later;
  "registry seeded" smoke half deferred to Stage 2).
- **Learned.** `gh` is authenticated as `profxj`; self-approval is blocked by
  GitHub, so reviews of JXP-authored PRs go in as comments. The base branch for
  stage PRs is **`develop`**, not `main`.

### 2026-06-23 (Task 5: PR-comment edits — CI Python matrix)

Addressed the one actionable follow-up from the PR #3 review (the other two were
intentional Stage-2 deferrals — duplicate-name guard, "registry seeded" smoke).

- **Edit.** Converted `.github/workflows/ci.yml` to a **matrix over Python
  `3.12` and `3.14`** (`fail-fast: false`), so CI now exercises both the
  declared `setup.py` minimum and the actual `ocean14` dev-env version
  (confirmed 3.14.5) rather than 3.12 alone.
- **Verification (`ocean14`).** Suite green on 3.14 locally (**46 passed**); the
  code is 3.12-safe (all unions are stringized via
  `from __future__ import annotations`). The 3.12 leg runs on CI once pushed.
- **Note.** The edit is in the working tree for JXP to commit/push; I did not
  re-post a PR resolution comment (turn moved on to Task 6).

### 2026-06-23 (Task 6: Read the Docs / Sphinx site)

Set up the accumulating documentation site and verified it builds clean.

- **RTD config.** `.readthedocs.yaml` (v2): build ubuntu-24.04 / Python 3.12,
  `sphinx.configuration: docs/source/conf.py`, `fail_on_warning: false`
  (advisory, mirroring CI); installs the package (`pip install .`) plus
  `docs/requirements.txt`.
- **Sphinx tree.** Honored the design doc's `docs/source/…` layout (keeping the
  published site separate from `docs/design/` and `docs/PDFs/`):
  `docs/source/{conf.py, index.rst, installation.rst, reports/index.rst,
  api/index.rst, _static/}` + `docs/{Makefile, make.bat, requirements.txt}`.
  `reports/index.rst` is the placeholder for the accumulating per-sweep pages
  (Stage 5's `report.rst` will switch its toctree to a glob); `api/index.rst`
  autodocs the whole package by subsystem.
- **conf.py for modern Sphinx.** Targeted Sphinx 9.1 + `sphinx_rtd_theme` 3.1
  (what `ocean14` ships): dropped the deprecated rtd-theme options
  (`display_version`/`logo_only`) and the missing `sphinx-autodoc-typehints`
  dep (used the built-in `autodoc_typehints = 'description'`). Mocked the heavy
  / sibling imports (`bing`, `ocpy`, `bokeh`, `emcee`, `corner`, …) so the docs
  build without the full stack. Version single-sourced from
  `ioptics.__version__`.
- **Tested.** `sphinx-build -b html -W --keep-going docs/source docs/build/html`
  → **build succeeded, 0 warnings**. Fixed four RST title-underline issues and
  one docstring glitch surfaced by `-W`: `config.py`'s module docstring had
  ```` ``dump()``s ```` (closing backticks glued to `s`) → reworded. Confirmed
  autodoc rendered all Stage-0 classes (`PreparedRecord`, `RetrievalResult`,
  `ComponentFit`, `SweepConfig`, `AlgorithmConfig`); `pytest -q` still **46
  passed**; `docs/build/` is gitignored (`build/`), source files are committable.
- **Learned.** `sphinx_rtd_theme` 3.x removed several `html_theme_options` keys
  ocpy's older conf.py still sets; on Sphinx 9 a minimal options dict is safest.
  An empty `:glob:` toctree warns ("didn't match any documents"), so the
  reports placeholder uses a plain (entry-less) toctree until sweeps exist.

### 2026-06-23 (Task 7: update `coding_prompts_stage01.md` for Stage-0 reality)

Revised the Stage-1 prompt so it builds on what Stage 0 actually shipped, and
fixed a stale ocpy reference I verified against `ocean14`.

- **Stage-0 carryover block (new in Context).** Spelled out that
  `PreparedRecord` is implemented + top-level re-exported, with its **exact
  field names** Stage 1 must populate — flagging the easy-to-miss ones:
  `noise_seed` (not `seed`), `Rrs_clean`, `noise_model` tag, `init={'Chl','Y'}`,
  and picklability. Noted the **conftest skip guards already exist** (import
  `needs_l23`, don't redefine) and that `datasets`/`noise`/`prep` are
  docstring-only stubs (with `RawObs` still to be defined).
- **API accuracy.** Verified the referenced ocpy/bing entry points in `ocean14`:
  all present except `ocpy.chl.band_ratios`, which is a **submodule** exposing
  `oc4`/`oc2` (not a package attribute). Corrected the Context and Task 3 to
  `ocpy.chl.band_ratios.oc4`.
- **Conventions.** Added the env-interpreter test command (conda `activate`
  fails non-interactively) and a docstring-must-be-RST-clean note (new public
  APIs are autodoc'd via the Stage-0 `docs/source/api/index.rst`; avoid the
  ```` ``x``s ```` closing-backtick glue that `-W` rejects).
- **Tasks.** Reworded 1–4 to "fill the stub", mapped `attach_noise`'s return
  tuple onto the `PreparedRecord` fields, required `prep` to populate every
  field, and pointed tests at `ioptics/tests/test_{datasets,noise,prep}.py`
  using the existing guard.
- **Note.** Prompt-doc edit only — no package code changed; `pytest` unaffected.

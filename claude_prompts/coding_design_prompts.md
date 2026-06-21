# Code IOPtics

## Goals

Produce a **coding / implementation design document** that guides the actual
writing of the IOPtics package. Where `IOPtics_design.md` says *what* IOPtics must
do and *why* (and deliberately avoids code), this effort produces the companion
doc that says *how* — concrete package layout, module APIs and signatures, data
structures, config formats, and how IOPtics wraps the BING and ocpy packages.

The output document will be named `IOPtics_implementation.md` and stored in
`docs/design/`. It is the "companion implementation document (forthcoming)"
referenced by the design document.

We expect the implementation to:

- Wrap **BING** (retrieval engine) and **ocpy** (data loaders, noise models,
  Spectrum classes) as a thin, uniform layer — not re-implement them.
- Run a growing registry of IOP algorithms through one pipeline, developing the
  first two — **`expb_pow` (ExpB_Pow)** and **`giop` (GIOP)** — **in tandem** so
  the comparison tooling is exercised on a real two-way comparison from the start.
- Emit a standardized results table + machine-readable provenance for every sweep.
- Compute uniform metrics/diagnostics and generate reproducible reports
  (.rst → readthedocs, a persistent leaderboard, standalone Bokeh figures).

## Claude

### Skills

Consider using the skills in `.claude/skills/` (e.g. `critical-partner`,
`grill-me`, `code-review`).

## Context

Examine the following before drafting the implementation doc:

- **The design document:** `docs/design/IOPtics_design.md` — the authoritative
  *what/why*. This effort plans the *how* for each of its sections (Data,
  Analysis, Metrics, Reporting) and honors its decisions and Open Questions.
- **`docs/context.md`** — reduced scientific/architectural reference.
- **The BING repository** (local copy; `github.com/ocean-colour/bing`) — the
  engine. Key modules: `models.anw` / `models.bbnw` (model registries +
  `init_model`), `rt.rrs` (Gordon forward model) / `rt.raman` / `rt.chl_fl`,
  `fitting.chisq_fit` + `fitting.inference` (least-squares & MCMC),
  `parameters.standard` (pre-wired combos: `expb_pow`, `giop`, `gsm`, ...),
  `priors`, `evaluate` (reconstruct a/bb ± unc), `stats` (χ²/AIC/BIC), `noise`.
  The canonical end-to-end example is `bing.fitting.l23.prep_one_l23` — IOPtics
  generalizes this into a dataset-agnostic prep.
- **The ocpy package** (`github.com/ocean-colour/ocpy`) — loaders
  `hydrolight.loisel23`, `insitu.pangaea`, `insitu.gloria`; noise
  `satellites.pace`; `spectra` (`Spectrum` / `SpectrumStack` + `spectra.io`
  adapters).
- **The BING and Erickson 2023 papers** (`docs/PDFs/bing.pdf`,
  `docs/PDFs/erickson2023.pdf`) for exact metric definitions.

## Overview

Guidelines for the implementation document (`docs/design/IOPtics_implementation.md`):

- **It WILL include specific code recommendations** — module/file layout, public
  function/class signatures, data-structure and config schemas. (This is the
  explicit complement to the design doc, which forbids them.)
- Add a version number (start at 0.1), a date, and authors (JXP and Claude).
  It is a living document; bump the version whenever sensible.
- Each section should **trace back to the design document** (e.g. "implements
  Analysis §IOP retrieval") so the two stay aligned.
- Respect the design decisions already made: native wavelength grids per dataset;
  `expb_pow` (ExpB_Pow) and `giop` (GIOP) developed **in tandem** as the first two
  algorithms (to drive the comparison tooling), with more added incrementally;
  least-squares first-pass with MCMC on a subset; PACE noise model
  (`ocpy.satellites.pace`) for L23;
  provenance recorded in YAML/JSON beside the results table; single accumulating
  readthedocs site; persistent leaderboard; standalone/static BokehJS.
- Keep the canonical IOP-component scheme question open (design Open Questions);
  the code should not hard-code a single scheme prematurely.
- You are encouraged to propose your own implementation ideas.

## Prompts

### Coding

1. Read this doc. Execute the 1st task under "Prep/Tasks".
2. Read this doc. Execute the 2nd task under "Prep/Tasks".
3. Read this doc. Execute the 3rd task under "Prep/Tasks".

4. Read this doc. Execute the 1st task under "Package layout/Tasks".
5. Read this doc. Execute the 2nd task under "Package layout/Tasks".
6. Read this doc. Execute the 3rd task under "Package layout/Tasks".

7. Read this doc. Execute the 1st task under "Data preparation/Tasks".

4. Read this doc. Execute the 1st task under "Algorithm registry/Tasks".
5. Read this doc. Execute the 1st task under "Retrieval & run/Tasks".
6. Read this doc. Execute the 1st task under "Metrics & diagnostics/Tasks".
7. Read this doc. Execute the 1st task under "Reporting/Tasks".
8. Read this doc. Execute the 1st task under "Testing & CI/Tasks".

(Additional follow-up tasks will be appended to each section as the work
proceeds, mirroring the workflow in `design_prompts.md`.)

## Prep

### Tasks

1. Start the implementation document `docs/design/IOPtics_implementation.md` with
   a **Preamble** (purpose, relationship to the design doc, version 0.1, today's
   date, authors JXP and Claude) and an **Architecture Overview** that maps each
   design-doc section (Data → prep, Analysis → registry/run, Metrics, Reporting)
   to the modules that will implement it, and states the BING/ocpy dependency
   boundary. Ask any questions in the Q&A section below. Log your work.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Prep section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

3. I have answered your new questions in the Q&A section below.  Please proceed to:

    - Make edits to the Prep section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Prep)

Started `docs/design/IOPtics_implementation.md` (v0.1) with a **Preamble**
(purpose, relationship to the design doc, version/date/authors, standing
decisions honored) and an **Architecture Overview** (the BING/ocpy dependency
boundary + a design-section → IOPtics-subsystem map). A few decisions worth your
call before I write the concrete package layout (next task):

1. **Top-level package name & namespacing.** I assume the package stays
   `ioptics/` (matching the repo and `ioptics/__init__.py`) with plain
   subpackages (`ioptics.prep`, `ioptics.registry`, `ioptics.run`,
   `ioptics.metrics`, `ioptics.diagnostics`, `ioptics.report`,
   `ioptics.provenance`). Any naming preferences before I commit them in Package
   layout? (e.g. `algorithms` vs `registry`, `run` vs `sweep`.)

Looks fine. I like algorithms and run.

2. **Config surface for a sweep.** Do you want sweeps driven by a **YAML config
   file** (declarative, shareable, pairs naturally with the YAML provenance), a
   **Python API** (build `AlgorithmSpec` objects in a script), or **both** (YAML
   as the user-facing entry, Python as the underlying API)? I lean toward both
   with YAML as the headline interface.

Both.

3. **Results-table store.** The design doc says CSV/parquet keyed by
   `(dataset, obs_id, algorithm)`. For the spectral, per-wavelength outputs
   (`a(λ)`, `bb(λ)` ± unc) do you prefer a **long/tidy** table (one row per
   `(obs, algorithm, component, wavelength)`) or a **wide** table with array-
   valued cells / a companion NetCDF/`xarray` for the spectra? This shapes the
   metrics layer. I lean long/tidy in parquet for the scalar table plus an
   `xarray`/NetCDF sidecar for full spectra.

I prefer the long/tidy table.

4. **Where the generalized prep ultimately lives.** Per design Q&A item D you
   said this is implementation, not design — for now I'm placing the generalized
   `prep_one`-style layer **inside IOPtics** (`ioptics.prep`) rather than
   contributing it upstream to BING. Confirm that's the intended home, or should
   it be a BING contribution (`bing.fitting.prep_one`) that IOPtics calls?

Yes, it should be inside IOPtics.

#### Claude's questions (2026-06-21, Prep round 2)

Applied all four answers to the implementation doc's **Architecture Overview**
(new "Resolved conventions" subsection: `ioptics.algorithms` + `ioptics.run`
naming; YAML-over-Python config; long/tidy parquet results table; prep inside
IOPtics) and bumped it to **v0.2**. One new question before Package layout:

5. **Sweep output directory layout.** Each sweep emits the long/tidy results
   table + the YAML/JSON provenance + figures, all stamped with versions. Do you
   have a preferred on-disk layout — e.g. a per-sweep directory
   `runs/<sweep_id>/{results.parquet, provenance.yaml, figures/}` with a
   stable/symlinked `latest/`, versus accumulating into a single growing table
   keyed by `sweep_id`? I lean toward per-sweep directories (clean provenance,
   easy to share one sweep) with the leaderboard aggregating across them. Where
   should `runs/` live — in the repo, or under `$OS_COLOR`/a configurable
   results root?

Ok, per-sweep directories sounds fine.  Put runs in `$OS_COLOR/IOPtics/runs/`.

#### Claude's note (2026-06-21, Prep round 3)

Applied Q5 to the implementation doc (per-sweep output directories under
`$OS_COLOR/IOPtics/runs/<sweep_id>/`, leaderboard aggregates across them) and
bumped to **v0.3**. No new questions — the **Prep** section (Preamble +
Architecture Overview, with all conventions resolved) is complete and ready to
seed **Package layout**.

## Package layout

### Tasks

1. Propose the concrete `ioptics/` package structure — modules, their
   responsibilities, and their dependencies on BING and ocpy. Cover at least:
   data prep, algorithm registry, run/sweep, metrics, diagnostics, plotting,
   reporting, and provenance. Write it into the implementation doc. Ask questions
   in the Q&A section below. Log your work.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Package layout section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

3. I have answered your new questions in the Q&A section below.  Please proceed to:

    - Make edits to the Package layout section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Package layout)

Wrote the **Package layout** section into `IOPtics_implementation.md` (v0.4): a
concrete `ioptics/` tree, a per-module responsibility/dependency table (covering
data prep, algorithm registry, run/sweep, metrics, diagnostics, plotting,
reporting, provenance), the inter-module data flow, the two load-bearing
dataclasses (`PreparedRecord`, `RetrievalResult`), and a module-granularity
restatement of the BING/ocpy boundary (ocpy confined to `datasets`+`noise`; BING
to `algorithms.spec`+`run`+`evaluate`). Grounded it by reading the real BING APIs
(`prep_one_l23`, `parameters.standard.{expb_pow,giop}`, `evaluate.*`,
`chisq_fit.fit`, `inference.fit_one/fit_batch`, `stats.calc_ICs`) and ocpy
(`Spectrum`, `satellites.pace`, the three loaders). Questions:

6. **`report` as a subpackage vs. flat modules.** I made `report/` a subpackage
   (`figures`, `tables`, `leaderboard`, `bokeh`, `rst`, `standard`) since
   Reporting carries the most moving parts. Fine, or would you rather keep
   everything flat (`ioptics.report`, `ioptics.leaderboard`, `ioptics.bokeh`)?

Your approach is fine.

7. **`scripts/` CLI vs. notebooks.** I included console entry points
   (`ioptics-run <config.yaml>`, `ioptics-report <sweep_id>`). Do you want a CLI
   as the primary driver, or do you prefer driving sweeps from notebooks/scripts
   (in which case `scripts/` is just thin `__main__` wrappers and the Python API
   is the real interface)?

I prefer driving sweeps from scripts.  See this example for syntax: https://github.com/Sea-Meets-the-Stars/fronts/blob/main/fronts/runs/prototypes/one_full/build_v4.py

8. **Truth-IOP component naming on `PreparedRecord`.** Since the canonical
   component scheme is deliberately open (design Open Q #1), I'm storing truth as
   a free-form dict keyed by component name (`a_ph`, `a_dg`, `bb_p`, scalars)
   rather than fixed fields — each dataset fills what it has. Agree that a dict
   (not a fixed schema) is the right call until the scheme is decided?

This sounds fine for now.

#### Claude's questions (2026-06-21, Package layout round 2)

Applied Q6 (kept the `report/` subpackage), Q7 (replaced the CLI with
script-driven sweeps — added `ioptics/runs/prototypes/<name>/build_vN.py`
following the `fronts` `build_v4.py` convention: one YAML source-of-truth,
integer-flag staged execution, paths from `$OS_COLOR`+sweep_id), and Q8 (made the
`PreparedRecord.truth` free-form dict explicit). Implementation doc → **v0.5**.
One follow-up:

9. **Sweep id.** The build script needs a stable `sweep_id` to name
   `$OS_COLOR/IOPtics/runs/<sweep_id>/`. Do you want it (a) set explicitly in the
   YAML config (e.g. `sweep_id: expb_giop_L23_v1`) — my lean, matching the
   `fronts` `run_id` convention; or (b) auto-derived from the config contents
   (algorithms+datasets+date hash)? Explicit is more legible and shareable; auto
   guarantees uniqueness.

Set explicitly in the YAML config.

#### Claude's note (2026-06-21, Package layout round 3)

Applied Q9 (explicit `sweep_id` in the YAML config). Made `sweep_id` a required
config field in the "Driving a sweep" subsection (author-chosen, not
content-hashed; names `$OS_COLOR/IOPtics/runs/<sweep_id>/`). Implementation doc →
**v0.6**. No new questions — the **Package layout** section is complete and seeds
Data preparation next.

## Data preparation

### Tasks

1. Design the **dataset-agnostic prep layer** that generalizes
   `bing.fitting.l23.prep_one_l23` to L23, PANGAEA, and GLORIA on their native
   wavelength grids, attaching the appropriate `Rrs` uncertainty (PACE noise model
   for L23 via `ocpy.satellites.pace`). Specify the API and the prepared-record
   data structure (the common form fed to the retrieval). Note how truth IOPs are
   attached where available. Write it into the doc. Q&A. Log.

### Q&A

## Algorithm registry

### Tasks

1. Design the **AlgorithmSpec** abstraction and registry: a declarative
   description of one algorithm (absorption + backscattering model choices,
   priors, RT options incl. Raman/Chl-fluorescence toggles, fit method, noise
   model) mapping onto BING's `init_model` / `parameters.standard`. Seed the
   registry with **both `expb_pow` (ExpB_Pow) and `giop` (GIOP)**, developed in
   tandem, and show how the two are configured side by side (and how a third,
   e.g. `gsm`, would be added). Write it into the doc. Q&A. Log.

### Q&A

## Retrieval & run

### Tasks

1. Design the **run/sweep** layer: `run_algorithm(spec, record)` plus single /
   batch / all-algorithms×all-spectra sweeps; least-squares default with MCMC on a
   subset; reconstruction of `a(λ)`/`bb(λ)` ± uncertainty via BING's `evaluate`.
   Define the **results-table schema** (keyed by dataset/obs_id/algorithm) and the
   **YAML/JSON provenance record** (model config, RT options, fit method, noise
   model, priors). Write it into the doc. Q&A. Log.

### Q&A

## Metrics & diagnostics

### Tasks

1. Design the **metrics** module implementing the design doc's Metrics section:
   log-space MAE/bias, `Rrs` closure (χ², reduced χ²ᵥ, MAE with the dual-sided
   window), model selection (AIC/BIC/ΔBIC), uncertainty coverage at 68%/95%,
   "wins", ratio histograms, and the per-component/per-wavelength reduction rules
   (incl. handling partial-retrieval algorithms). Design the **diagnostics**
   (Taylor, Target, corner, residual/closure spectra, ΔBIC CDFs). Both consume the
   results table. Write it into the doc. Q&A. Log.

### Q&A

## Reporting

### Tasks

1. Design the **reporting** module: the standard figure/table set, the on-demand
   standard report, the single accumulating readthedocs (`.rst`) site, the
   persistent **leaderboard**, and the **standalone/static BokehJS** interactive
   figures (select algorithm/dataset to inspect). Specify how reports are stamped
   with provenance/versions for reproducibility. Write it into the doc. Q&A. Log.

### Q&A

## Testing & CI

### Tasks

1. Design the **testing strategy** — data-independent unit tests that always run
   plus skip-guarded tests that need `$OS_COLOR` data (mirroring ocpy's
   `test_pangaea.py` pattern), all in the `ocean14` environment — and any CI
   (noting the design decision that reports are generated on demand, not via CI).
   Write it into the doc. Q&A. Log.

### Q&A

## Logging

The "Logs" section will record Claude's work. Please use the following format:

### <Date> (Short summary of the work)

<Detailed description of the work and what you learned>

### <Date> (Short summary of the work)

<Detailed description of the work and what you learned>

...

## Logs

### 2026-06-21 (Coding #1 → Prep/Tasks #1: started the implementation document)

Executed Coding prompt #1 (Prep/Tasks #1). Before drafting, re-read the design doc
(`IOPtics_design.md` v0.15) and surveyed the two sibling packages to ground the
dependency boundary accurately:
- **BING** subpackages: `models.{anw,bbnw,functions}` (+ `init_model`),
  `parameters.{standard,p_ntuple}` (combos `expb_pow`/`expbf_pow`/`giop`/`gsm`/
  `k2b`), `rt.{rrs,raman,chl_fl,defs}`, `priors`, `fitting.{chisq_fit,inference,
  l23}`, `evaluate`, `stats`, `noise`. Confirmed `fitting.l23.prep_one_l23` is the
  L23-specific canonical example IOPtics must generalize.
- **ocpy** modules: loaders `hydrolight.loisel23`, `insitu.pangaea`,
  `insitu.gloria`; noise `satellites.pace` (+ modis/seawifs/sbg);
  `spectra.{core,io,utils}` (`Spectrum`/`SpectrumStack`).

Created `docs/design/IOPtics_implementation.md` (v0.1, 2026-06-21, authors JXP and
Claude) with two sections:
- **Preamble** — purpose (the *how* companion to the design doc's *what/why*; will
  include code specifics), explicit relationship/traceability table to the design
  doc, the standing decisions it honors (native grids; `expb_pow`+`giop` in
  tandem; chisq-first + MCMC subset; `ocpy.satellites.pace` noise; YAML/JSON
  provenance beside the results table; accumulating readthedocs; leaderboard;
  standalone BokehJS; canonical component scheme left open), supporting material,
  and conventions (`ocean14`; wrap-not-reimplement).
- **Architecture Overview** — a diagram + an explicit **BING/ocpy dependency
  boundary** (ocpy owns the data side: loaders, noise, Spectrum; BING owns the
  retrieval side: models, parameters, rt, priors, fitting, evaluate, stats,
  noise; IOPtics owns the uniform layer between), plus a **design-section →
  IOPtics-subsystem map** (Data→prep, Analysis→registry/run, Metrics→metrics &
  diagnostics, Reporting→reporting, +Testing & CI) naming each subsystem's
  responsibility and what it wraps. Left the detailed file/module API to the next
  task (Package layout) with `(forthcoming)` stubs for the remaining sections.

Wrote 4 questions to the Prep Q&A (package naming, YAML-vs-Python sweep config,
results-table store shape, and where the generalized prep lives).

### 2026-06-21 (Coding #2 → Prep/Tasks #2: applied Prep Q&A decisions)

Read JXP's answers to the four Prep questions and reflected them in
`docs/design/IOPtics_implementation.md`:
- **Q1 (naming):** module names fixed to **`ioptics.algorithms`** (registry) and
  **`ioptics.run`** (run/sweep), per JXP, alongside `ioptics.prep`,
  `ioptics.metrics`, `ioptics.diagnostics`, `ioptics.report`,
  `ioptics.provenance`. Updated the section→module map to name each module.
- **Q2 (config):** **both** — YAML config as the headline/shareable entry over a
  Python `AlgorithmSpec` API, with YAML parsed into the same objects.
- **Q3 (results table):** **long/tidy parquet** (row per
  `(dataset, obs_id, algorithm, component, wavelength)`; scalar summaries keyed by
  `(dataset, obs_id, algorithm)`); no wide/array layout.
- **Q4 (prep home):** the generalized `prep_one`-style layer lives **inside
  IOPtics** (`ioptics.prep`), not contributed upstream to BING.

Added a **"Resolved conventions (Prep Q&A)"** subsection to the Architecture
Overview capturing all four, so Package layout and downstream sections inherit
them. Bumped the implementation doc to **v0.2**. Wrote 1 new question (Q5: per-
sweep output directory layout + where the results root lives) to the Prep Q&A.

### 2026-06-21 (Coding #3 → Prep/Tasks #3: applied Q5, Prep section complete)

Read JXP's answer to Q5 (per-sweep directories; results root
`$OS_COLOR/IOPtics/runs/`). Added a fifth bullet to the implementation doc's
"Resolved conventions" subsection: each sweep writes a self-contained
`$OS_COLOR/IOPtics/runs/<sweep_id>/` directory (`results.parquet`,
`provenance.yaml`, `figures/`); the leaderboard aggregates across sweep
directories rather than mutating one global table; results root configurable.
Bumped the implementation doc to **v0.3**. No new questions — the Prep section
(Preamble + Architecture Overview) is complete and seeds Package layout next.

### 2026-06-21 (Coding #4 → Package layout/Tasks #1: wrote the Package layout section)

Executed Package layout/Tasks #1. Before drafting, read the actual upstream APIs
so the wrapping is thin and accurate:
- **BING:** `fitting.l23.{load_one_l23,prep_one_l23,fit_one,fit_with_LM,batch_fit}`
  (the canonical prep/fit flow IOPtics generalizes); `parameters.standard`
  (`expb_pow` → `['ExpBricaud','Pow']`, `giop` → `['GIOP','Lee']`, plus
  `gsm`/`k2b`); `evaluate.{reconstruct_from_chains,reconstruct_chisq_fits,
  calc_stats,calc_Rrs_from_models}`; `fitting.chisq_fit.fit(items,models,rt_dict,
  bounds)`; `fitting.inference.{init_mcmc,fit_one,fit_batch,run_emcee}`;
  `stats.{calc_chisq,calc_ICs}`; `noise.{scale_noise,add_noise}`;
  `rt.defs.rt_dict_from_p`.
- **ocpy:** `spectra.core.Spectrum`/`SpectrumStack` (dataclasses w/ wavelength/
  values/errors/units/metadata + netcdf/xarray IO); `satellites.pace.{wave,
  gen_noise_vector}`; loaders `hydrolight.loisel23.load_ds`, `insitu.pangaea.*`,
  `insitu.gloria.load_gloria`.

Wrote the **Package layout** section into `IOPtics_implementation.md`:
- Concrete `ioptics/` tree with `algorithms/` and `report/` subpackages and the
  decided module names (`prep`, `algorithms`, `run`, `metrics`, `diagnostics`,
  `report`, `provenance`, plus `config`, `records`, `datasets`, `noise`,
  `evaluate`, `io`, `plotting`, `scripts`, `tests`).
- A per-module responsibility table naming exactly what each wraps in BING/ocpy
  and the design-doc section it traces to (covers all eight required topics: data
  prep, algorithm registry, run/sweep, metrics, diagnostics, plotting, reporting,
  provenance).
- An inter-module **data-flow** diagram and the two load-bearing dataclasses
  (`PreparedRecord`, `RetrievalResult`), with full schemas deferred to the Data
  preparation / Retrieval & run sections.
- A **module-granularity dependency boundary**: ocpy imported only by
  `datasets`+`noise`; BING only by `algorithms.spec`+`run`+`evaluate`; metrics/
  diagnostics/report touch neither (operate on the results table) — keeping
  IOPtics a thin uniform layer with the upstream packages confined to the edges.
Bumped the implementation doc to **v0.4**. Wrote 3 questions (Q6: report
subpackage vs flat; Q7: CLI vs notebook as primary driver; Q8: free-form truth
dict vs fixed schema while the component scheme is open) to the Package layout Q&A.

### 2026-06-21 (Coding #5 → Package layout/Tasks #2: applied Q6–Q8, script-driven sweeps)

Read JXP's answers (Q6 report subpackage fine; Q7 **drive sweeps from scripts**,
with the `fronts` repo `build_v4.py` as the syntax reference; Q8 free-form truth
dict fine). Fetched the `fronts/runs/prototypes/one_full/build_v4.py` example to
mirror its convention (single-integer-flag staged execution, one YAML config as
source of truth, paths derived from an env-var base + run_id). Edits to
`IOPtics_implementation.md`:
- **Q7:** removed the `ioptics-run`/`ioptics-report` CLI; replaced `scripts/` with
  **`ioptics/runs/prototypes/<name>/build_vN.py`** + `run_vN.yaml`. Updated the
  module table row and added a new **"Driving a sweep (script-driven, not a CLI)"**
  subsection with a worked `build_v1.py` skeleton (`python build_v1.py <flg>`;
  bit-flag stages prep/run→metrics→report; YAML single source of truth; paths from
  `$OS_COLOR`+`sweep_id` so producer/consumers share conventions with no drift).
- **Q8:** made `PreparedRecord.truth` an explicit **free-form dict** (keys per
  what each dataset supports; metrics score on the intersection), justified by the
  open canonical-component-scheme decision.
- **Q6:** no change (the `report/` subpackage stays).
Bumped the implementation doc to **v0.5**. Wrote 1 new question (Q9: explicit
`sweep_id` in YAML vs. auto-derived hash) to the Package layout Q&A.

### 2026-06-21 (Coding #6 → Package layout/Tasks #3: applied Q9, section complete)

Read JXP's answer to Q9 (explicit `sweep_id` in the YAML config). Updated the
"Driving a sweep" subsection of `IOPtics_implementation.md` to make `sweep_id` a
required, author-chosen config field (not content-hashed) that names the sweep
output directory `$OS_COLOR/IOPtics/runs/<sweep_id>/`. Bumped the implementation
doc to **v0.6**. No new questions — the Package layout section is complete and
seeds Data preparation next.

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

2. Read this doc. Execute the 1st task under "Package layout/Tasks".
3. Read this doc. Execute the 1st task under "Data preparation/Tasks".
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

## Package layout

### Tasks

1. Propose the concrete `ioptics/` package structure — modules, their
   responsibilities, and their dependencies on BING and ocpy. Cover at least:
   data prep, algorithm registry, run/sweep, metrics, diagnostics, plotting,
   reporting, and provenance. Write it into the implementation doc. Ask questions
   in the Q&A section below. Log your work.

### Q&A

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

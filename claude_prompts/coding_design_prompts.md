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
- Run a growing registry of IOP algorithms through one pipeline (first: `expb_pow`).
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
  `expb_pow` as the first algorithm, added one at a time; least-squares first-pass
  with MCMC on a subset; PACE noise model (`ocpy.satellites.pace`) for L23;
  provenance recorded in YAML/JSON beside the results table; single accumulating
  readthedocs site; persistent leaderboard; standalone/static BokehJS.
- Keep the canonical IOP-component scheme question open (design Open Questions);
  the code should not hard-code a single scheme prematurely.
- You are encouraged to propose your own implementation ideas.

## Prompts

### Coding

1. Read this doc. Execute the 1st task under "Prep/Tasks".
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

### Q&A

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
   registry with `expb_pow` and show how a second algorithm (e.g. `giop`) is
   added. Write it into the doc. Q&A. Log.

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

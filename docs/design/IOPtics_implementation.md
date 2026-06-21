# IOPtics Implementation Document

**Version:** 0.2
**Date:** 2026-06-21
**Authors:** JXP and Claude

---

## Preamble

This is the **coding / implementation design document** for **IOPtics**. Where
[`IOPtics_design.md`](IOPtics_design.md) says *what* IOPtics must do and *why*
(and deliberately avoids code), this document says *how*: the concrete package
layout, module and class/function signatures, data-structure and config schemas,
the results-table and provenance formats, and exactly how IOPtics wraps the
**BING** and **ocpy** packages.

It is the "companion implementation document (forthcoming)" referenced by the
design document.

### What this document is for

- It is the **engineering reference** for building the `ioptics/` package — read
  it alongside the design doc, which remains the authoritative source for scope,
  requirements, and decisions.
- Unlike the design doc, **it will include specific code recommendations** —
  module/file layout, public function/class signatures, data-structure and config
  schemas. This is the explicit complement to the design doc's no-code rule.
- It is a **living document**: the version number and date are bumped whenever
  sensible as the implementation matures.

### Relationship to the design document

Every section here **traces back to a section of the design doc** so the two stay
aligned. The mapping is:

| Design doc section | Implementation concern | This doc |
|---|---|---|
| **Data** | Dataset-agnostic load & prep | Data preparation |
| **Analysis → IOP retrieval** | Algorithm specification & registry | Algorithm registry |
| **Analysis → retrieval / uncertainty / provenance** | Run/sweep engine, results & provenance | Retrieval & run |
| **Metrics** | Metric & diagnostic computation | Metrics & diagnostics |
| **Reporting** | Figures, tables, `.rst` site, leaderboard, Bokeh | Reporting |
| (cross-cutting) | Test strategy & CI | Testing & CI |

Standing design decisions this document honors (from the design doc and its Open
Questions): native wavelength grids per dataset (no resampling); **`expb_pow`
(ExpB_Pow) and `giop` (GIOP) developed in tandem** as the first two algorithms to
exercise the comparison tooling, with more added incrementally; least-squares
first-pass with MCMC reserved for a subset; the **`ocpy.satellites.pace`** noise
model for L23; provenance recorded in **YAML/JSON beside the results table**; a
single accumulating readthedocs site; a persistent leaderboard;
standalone/static BokehJS. The **canonical IOP-component scheme remains open**
(design Open Question #1), so the code must not hard-code a single scheme
prematurely.

### Supporting material

- [`IOPtics_design.md`](IOPtics_design.md) — the authoritative design (v0.15).
- [`docs/context.md`](../context.md) — distilled scientific/architectural reference.
- The **BING** repository (`github.com/ocean-colour/bing`) — the retrieval engine.
- The **ocpy** repository (`github.com/ocean-colour/ocpy`) — data loaders, noise
  models, and `Spectrum` classes.

### Conventions

- Code is written for the **`ocean14`** conda environment.
- Clear, well-documented Python with docstrings (per `CLAUDE.md`).
- IOPtics **wraps** BING and ocpy as a thin, uniform layer; it does not
  re-implement their machinery.

---

## Architecture Overview

IOPtics sits as a thin orchestration layer **on top of two sibling packages it
does not own**, and adds the uniform driving/scoring/reporting layer the design
doc calls for:

```
            ┌─────────────────────────────────────────────┐
            │                  IOPtics                     │
            │   uniform prep · registry · run · metrics ·  │
            │        diagnostics · reporting · provenance  │
            └───────────────┬───────────────┬─────────────┘
                            │               │
                  depends on│               │depends on
                            ▼               ▼
                  ┌──────────────┐   ┌──────────────┐
                  │     ocpy     │   │     BING     │
                  │ data loaders │   │  retrieval   │
                  │ noise models │   │   engine     │
                  │  Spectrum    │   │ (models, rt, │
                  │   classes    │   │ fitting, …)  │
                  └──────────────┘   └──────────────┘
```

### The BING / ocpy dependency boundary

**ocpy owns the data side.** IOPtics calls ocpy for everything that reads or
characterizes observations and never re-implements a reader:

- **Loaders:** `ocpy.hydrolight.loisel23` (L23, `load_ds(X, Y)`),
  `ocpy.insitu.pangaea` (PANGAEA V3), `ocpy.insitu.gloria` (GLORIA).
- **Noise models:** `ocpy.satellites.pace` (the L23 first-pass noise model), with
  `modis`/`seawifs`/`sbg` available.
- **Spectrum containers:** `ocpy.spectra` (`Spectrum` / `SpectrumStack` and the
  `spectra.io` adapters) for carrying `Rrs` on each dataset's native grid.

**BING owns the retrieval side.** IOPtics configures and drives BING but never
re-implements the inversion:

- **Models:** `bing.models.anw` / `bing.models.bbnw` (model registries +
  `init_model`); `bing.models.functions`.
- **Pre-wired combos:** `bing.parameters.standard` (`expb_pow`, `expbf_pow`,
  `giop`, `gsm`, `k2b`) and `bing.parameters.p_ntuple`.
- **Forward model / RT:** `bing.rt.rrs` (Gordon), `bing.rt.raman`,
  `bing.rt.chl_fl`, `bing.rt.defs`.
- **Priors:** `bing.priors`.
- **Fitting:** `bing.fitting.chisq_fit` (least-squares),
  `bing.fitting.inference` (MCMC/emcee: `fit_one`/`fit_batch`/`run_emcee`).
- **Reconstruction & stats:** `bing.evaluate` (reconstruct `a`/`bb` ± unc),
  `bing.stats` (χ²/AIC/BIC), `bing.noise`.
- The canonical end-to-end example, `bing.fitting.l23.prep_one_l23`, is
  **L23-specific**; IOPtics generalizes it into a dataset-agnostic prep rather
  than calling it directly.

**IOPtics owns the uniform layer in between:** the dataset-agnostic prep, the
declarative algorithm specification + registry, the run/sweep driver, the metrics
& diagnostics, the reporting/leaderboard outputs, and the provenance record that
ties a result back to its exact configuration.

### Section → module map

Each design-doc section is implemented by one IOPtics subsystem. (The concrete
file/module names and their public APIs are specified in **Package layout**; this
table fixes the responsibilities and the upstream dependencies.)

| Design doc section | IOPtics subsystem (module) | Responsibility | Wraps / depends on |
|---|---|---|---|
| **Data** | Data preparation (`ioptics.prep`) | Generalize `prep_one_l23` to L23/PANGAEA/GLORIA on native grids; attach `Rrs` uncertainty; emit a common **prepared record**; attach truth IOPs where available | ocpy loaders + `ocpy.satellites.pace` |
| **Analysis → IOP retrieval** | Algorithm registry (`ioptics.algorithms`) | Declarative **AlgorithmSpec** (a_nw/bb_nw model choices, priors, RT toggles, fit method, noise model) + registry; seed `expb_pow` **and** `giop` in tandem | `bing.models.init_model`, `bing.parameters.standard`, `bing.priors`, `bing.rt` |
| **Analysis → retrieval / uncertainty / provenance** | Retrieval & run (`ioptics.run`, `ioptics.provenance`) | `run_algorithm(spec, record)`; single / batch / all×all sweeps; least-squares default, MCMC subset; reconstruct `a`/`bb` ± unc; emit the **results table** + **YAML/JSON provenance** | `bing.fitting.*`, `bing.evaluate`, `bing.stats`, `bing.noise` |
| **Metrics** | Metrics & diagnostics (`ioptics.metrics`, `ioptics.diagnostics`) | Log-space MAE/bias, `Rrs` closure (χ², χ²ᵥ), AIC/BIC/ΔBIC, coverage at 68/95%, wins, ratio histograms; Taylor/Target/corner/residual/ΔBIC-CDF diagnostics; partial-retrieval rules | consumes the results table |
| **Reporting** | Reporting (`ioptics.report`) | Standard figure/table set; on-demand standard report; accumulating `.rst`/readthedocs site; persistent **leaderboard**; standalone/static **BokehJS**; provenance/version stamping | consumes results table + provenance |
| (cross-cutting) | Testing & CI (`ioptics/tests`) | Data-independent unit tests always run + `$OS_COLOR`-skip-guarded tests; reports on demand (not CI) | mirrors ocpy's `test_pangaea.py` pattern |

Cutting across all subsystems, **provenance** is recorded for every result (model
config, RT options, fit method, noise model, and — for MCMC — priors), written in
YAML/JSON beside the results table so any retrieval is reproducible end to end.

### Resolved conventions (Prep Q&A, 2026-06-21)

These choices are fixed here and carried into **Package layout** and the
downstream sections:

- **Package & module names.** The package stays `ioptics/`. Subpackage names use
  **`ioptics.algorithms`** (the registry/AlgorithmSpec) and **`ioptics.run`**
  (the run/sweep driver) — per JXP's preference — alongside `ioptics.prep`,
  `ioptics.metrics`, `ioptics.diagnostics`, `ioptics.report`, and
  `ioptics.provenance`.
- **Sweep config surface: both.** A declarative **YAML config file** is the
  headline, shareable entry point (pairing naturally with the YAML provenance),
  layered over a **Python API** that builds `AlgorithmSpec` objects directly. YAML
  is parsed into the same objects the Python API constructs.
- **Results-table store: long/tidy.** The results table is **long/tidy parquet**
  (one row per `(dataset, obs_id, algorithm, component, wavelength)` for spectral
  outputs; scalar summaries keyed by `(dataset, obs_id, algorithm)`), which keeps
  the metrics layer a straightforward group-by. (A wide/array-valued layout is
  not used.)
- **Generalized prep lives inside IOPtics.** The dataset-agnostic
  `prep_one`-style layer is implemented in **`ioptics.prep`**, not contributed
  upstream to BING; IOPtics calls ocpy loaders and BING models from there.

*The concrete `ioptics/` package structure — module files, their public
signatures, and their exact dependencies — is specified in the next section,
Package layout.*

---

## Package layout

*(forthcoming — Package layout / Tasks #1)*

## Data preparation

*(forthcoming — Data preparation / Tasks #1)*

## Algorithm registry

*(forthcoming — Algorithm registry / Tasks #1)*

## Retrieval & run

*(forthcoming — Retrieval & run / Tasks #1)*

## Metrics & diagnostics

*(forthcoming — Metrics & diagnostics / Tasks #1)*

## Reporting

*(forthcoming — Reporting / Tasks #1)*

## Testing & CI

*(forthcoming — Testing & CI / Tasks #1)*

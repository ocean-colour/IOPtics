# IOPtics Implementation Document

**Version:** 0.10
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
- **Sweep output layout: per-sweep directories under a configurable results
  root.** Each sweep writes a self-contained directory
  `$OS_COLOR/IOPtics/runs/<sweep_id>/` holding `results.parquet` (the long/tidy
  table), `provenance.yaml` (the version-stamped config record), and `figures/`.
  Per-sweep isolation keeps provenance clean and makes a single sweep trivially
  shareable; the persistent **leaderboard** aggregates *across* these directories
  rather than each sweep mutating one global table. The results root defaults to
  `$OS_COLOR/IOPtics/runs/` and is configurable.

*The concrete `ioptics/` package structure — module files, their public
signatures, and their exact dependencies — is specified in the next section,
Package layout.*

---

## Package layout

*Implements the Architecture Overview at the file/module level. Honors the
Resolved conventions above and the design doc's decisions.*

This section fixes the concrete `ioptics/` package tree, each module's
responsibility, and exactly what it wraps in BING and ocpy. Detailed public
signatures and data-structure schemas are specified in the per-topic sections
that follow (Data preparation, Algorithm registry, Retrieval & run, Metrics &
diagnostics, Reporting); here we establish the skeleton and the dependency flow.

### Proposed package tree

```
ioptics/
├── __init__.py            # version; lightweight top-level re-exports
├── config.py              # YAML ⇄ Python sweep-config (load/validate/dump)
├── records.py             # core dataclasses: PreparedRecord, RetrievalResult
├── datasets.py            # dataset registry: thin adapters over ocpy loaders
├── prep.py                # dataset-agnostic prep (generalizes prep_one_l23)
├── noise.py               # Rrs-uncertainty attachment (PACE etc. via ocpy)
├── algorithms/
│   ├── __init__.py
│   ├── spec.py            # AlgorithmSpec dataclass ⇄ bing.parameters.standard
│   └── registry.py        # name → AlgorithmSpec; seeded expb_pow + giop
├── run.py                 # run_algorithm / run_batch / run_sweep (the driver)
├── evaluate.py            # wrap bing.evaluate → reconstruct a/bb ± unc as rows
├── provenance.py          # build/stamp/write YAML/JSON provenance + versions
├── io.py                  # long/tidy parquet results table; sweep-dir layout
├── metrics.py             # log-space MAE/bias, χ²/χ²ᵥ, AIC/BIC/ΔBIC, coverage, wins
├── diagnostics.py         # Taylor/Target/corner/residual/ΔBIC-CDF (compute+data)
├── plotting.py            # low-level static figure primitives (wraps bing.plotting)
├── report/
│   ├── __init__.py
│   ├── figures.py         # the standard static figure set
│   ├── tables.py          # accuracy / QC summary tables
│   ├── leaderboard.py     # persistent leaderboard, aggregated across sweeps
│   ├── bokeh.py           # standalone/static BokehJS interactive figures
│   ├── rst.py             # assemble .rst pages for the readthedocs site
│   └── standard.py        # the on-demand "standard report" orchestration
├── runs/                  # versioned build scripts that drive sweeps (see below)
│   └── prototypes/<name>/
│       ├── build_v1.py    # `python build_v1.py <flg>` — staged sweep driver
│       └── run_v1.yaml    # the sweep config (single source of truth)
└── tests/                 # unit tests (always-run) + $OS_COLOR-skip-guarded
```

### Module responsibilities & dependencies

| Module | Responsibility | Wraps / depends on (BING · ocpy) | Design trace |
|---|---|---|---|
| `config` | Parse a YAML sweep file into the same objects the Python API builds (datasets, algorithm names/overrides, fit method, MCMC subset, output root); validate; dump back for provenance. | — | Analysis (provenance) |
| `records` | The two data structures that flow through the pipeline: **`PreparedRecord`** (one obs ready to fit) and **`RetrievalResult`** (one algorithm's output for one obs). Plain dataclasses, serialization-friendly. | — | Data / Analysis |
| `datasets` | A **dataset registry** mapping `dataset` name → loader adapter returning observations as ocpy `Spectrum`/`SpectrumStack` plus any truth IOPs, on the **native grid**. One adapter per source. | ocpy `hydrolight.loisel23`, `insitu.pangaea`, `insitu.gloria`; `spectra` | Data |
| `prep` | The **dataset-agnostic prep layer** — generalizes `bing.fitting.l23.prep_one_l23` to any dataset: take a loaded observation, attach `Rrs` uncertainty, assemble the `PreparedRecord` (obs `Rrs`+σ on native grid; truth where available). No model/prior init here (that is the algorithm's job at run time). | reads ocpy loaders via `datasets`; calls `noise` | Data prep |
| `noise` | Build the `Rrs` variance vector for a record. L23 first-pass uses **`ocpy.satellites.pace`** (`gen_noise_vector`); in-situ datasets carry their own `errors`. Thin wrapper so the noise model is a provenance-recorded choice. | ocpy `satellites.pace` (+ modis/seawifs/sbg); BING `noise.scale_noise` | Data prep |
| `algorithms.spec` | **`AlgorithmSpec`** — the declarative description of one algorithm (a_nw + bb_nw model names, priors, RT toggles incl. Raman/Chl-fl, fit method, noise model). `.to_bing_p()` emits the BING parameter namedtuple; `.from_standard(name)` seeds from `bing.parameters.standard`. | BING `parameters.standard`, `parameters.p_ntuple`, `priors` | Analysis (IOP retrieval) |
| `algorithms.registry` | Name → `AlgorithmSpec` factory; the growing registry. **Seeded with `expb_pow` and `giop`** side by side; `register()` adds more (e.g. `gsm`). | wraps `algorithms.spec` | Analysis (in-tandem) |
| `run` | The driver: **`run_algorithm(spec, record)`** for one fit; `run_batch` over records; `run_sweep` over algorithms × records. Least-squares **default** (`bing.fitting.chisq_fit.fit`); **MCMC** (`bing.fitting.inference.fit_one/fit_batch`) for a flagged subset. Builds BING models per record via `init_model`, the `rt_dict` via `rt.defs`, runs, hands chains/params to `evaluate`. | BING `models.init_model`, `rt.defs`, `fitting.chisq_fit`, `fitting.inference` | Analysis (retrieval, two fitting modes) |
| `evaluate` | Turn a fit into a **`RetrievalResult`**: reconstruct `a(λ)`/`bb(λ)` and components ± uncertainty (MCMC percentiles or least-squares covariance), compute fit stats. | BING `evaluate.reconstruct_from_chains` / `reconstruct_chisq_fits` / `calc_stats`, `stats.calc_chisq` / `calc_ICs` | Analysis (uncertainty) |
| `provenance` | Assemble the **YAML/JSON provenance record** for a sweep (model config, RT options, fit method, noise model, and — for MCMC — priors) and **stamp versions** (design-doc, registry entry, dataset, ocpy/bing/ioptics commits). Written beside the results table. | reads `AlgorithmSpec`; package versions | Analysis (provenance) |
| `io` | Read/write the **long/tidy parquet** results table and own the **sweep directory layout** `$OS_COLOR/IOPtics/runs/<sweep_id>/{results.parquet, provenance.yaml, figures/}`. | pandas/pyarrow | Reporting (artifacts) |
| `metrics` | Compute the metric battery from the results table: log-space MAE/bias, `Rrs` closure (χ², reduced χ²ᵥ, dual-sided window), AIC/BIC/ΔBIC, 68/95% coverage, wins, ratio histograms; partial-retrieval/coverage rules. | consumes results table; BING `stats` for IC cross-checks | Metrics §1–5 |
| `diagnostics` | Compute the data behind the diagnostic figures: Taylor, Target, corner, residual/closure spectra, ΔBIC CDFs. | consumes results table / chains | Metrics §6 |
| `plotting` | Low-level **static** figure primitives (matplotlib), publication-styled; reuse `bing.plotting` where it fits. | BING `plotting` | Reporting |
| `report.figures` / `.tables` | The **standard** static figure/table set generated uniformly per algorithm/dataset. | `plotting`, `diagnostics`, `metrics` | Reporting |
| `report.leaderboard` | The **persistent leaderboard** — ranks algorithms by headline metrics, aggregated **across** sweep directories (not one mutated global table). | `metrics`, `io` | Reporting (leaderboard) |
| `report.bokeh` | **Standalone/static BokehJS** interactive figures (select algorithm/dataset; hover/pan/zoom) embeddable in readthedocs. | bokeh | Reporting (interactive) |
| `report.rst` / `.standard` | Assemble `.rst` pages for the single accumulating readthedocs site; the on-demand standard report, version/provenance-stamped. | `figures`, `tables`, `leaderboard`, `bokeh`, `provenance` | Reporting (delivery) |
| `runs` | **Versioned build scripts** that drive a sweep end to end (prep → run → report) — *not* a CLI. The Python API below is the real interface; each `build_vN.py` is a thin staged orchestrator over it. | `config`, `run`, `report` | Reporting (on demand) |

### Data flow (the contract between modules)

```
config.yaml ─▶ config ─▶ (datasets + algorithms)
 datasets ─▶ prep (+noise) ─▶ PreparedRecord ─┐
 algorithms.registry ─▶ AlgorithmSpec ────────┤
                                              ▼
                              run.run_algorithm(spec, record)
                                (chisq default | MCMC subset)
                                              │
                                              ▼
                              evaluate ─▶ RetrievalResult
                                              │
                       io ◀── results.parquet ┤ provenance ─▶ provenance.yaml
                                              ▼
                          metrics + diagnostics  (read results table)
                                              ▼
                report.{figures,tables,leaderboard,bokeh,rst,standard}
                                              ▼
                      runs/<sweep_id>/{results.parquet, provenance.yaml, figures/}
```

Two dataclasses are the load-bearing contracts and are kept deliberately small so
every dataset and every algorithm flow through unchanged:

- **`PreparedRecord`** — `dataset`, `obs_id`, `wave` (native grid), `Rrs`,
  `varRrs`, a **free-form `truth` dict** keyed by component name (`a`, `bb`,
  `a_ph`, `a_dg`, `bb_p`, scalars like `Chl`, `a_cdom440`) holding whatever that
  dataset supports, and a `meta` dict. The `truth` dict is deliberately *not* a
  fixed schema while the canonical component scheme stays open (design Open Q #1)
  — each dataset fills only the keys it has, and metrics score on the intersection
  with what an algorithm retrieves. Spectral truth is **pre-aligned onto `wave`**
  by `prep` (with a per-component interpolation flag). The output of `prep`; the
  input to `run`. *(Full schema: Data preparation §.)*
- **`RetrievalResult`** — `(dataset, obs_id, algorithm)` key plus reconstructed
  `a(λ)`/`bb(λ)` and components with ± uncertainty, fit stats (χ²ᵥ, AIC/BIC), the
  fit method, and a pointer to its provenance. Flattened to the long/tidy table by
  `io`. *(Full schema: Retrieval & run §.)*

### Dependency boundary (restated at module granularity)

- **ocpy is imported only by** `datasets` and `noise` (loaders, `Spectrum`,
  satellite noise). Nothing downstream of `prep` imports ocpy — once a
  `PreparedRecord` exists, the pipeline is data-source-agnostic.
- **BING is imported only by** `algorithms.spec`, `run`, and `evaluate` (models,
  parameters, rt, priors, fitting, evaluate, stats). Nothing in `metrics`,
  `diagnostics`, or `report` imports BING — they operate purely on the results
  table. (`plotting` may reuse `bing.plotting` helpers, the one soft exception.)
- This keeps IOPtics a **thin uniform layer**: the upstream packages are confined
  to the edges (data in, retrieval in the middle), and the comparison/reporting
  machinery — the part unique to IOPtics — depends on neither.

### Driving a sweep (script-driven, not a CLI)

Sweeps are driven by **versioned build scripts** under `ioptics/runs/`, following
the lab convention (cf. the `fronts` repo's `runs/prototypes/<name>/build_vN.py`)
rather than a packaged CLI. The library (`config`, `run`, `report`) is the real
interface; the build script is a thin, staged orchestrator so a sweep is
re-runnable stage-by-stage and self-documenting.

- **One YAML config is the single source of truth** for the sweep — an
  **explicit `sweep_id`** (a required field, e.g. `sweep_id: expb_giop_L23_v1`,
  matching the `fronts` `run_id` convention), datasets, algorithms (registry
  names + overrides), fit method + MCMC subset, and the output root. The
  `sweep_id` names the output directory `$OS_COLOR/IOPtics/runs/<sweep_id>/`; it
  is author-chosen rather than content-hashed so it stays legible and shareable.
  The config is read once and also copied verbatim into the sweep's
  `provenance.yaml`.
- **Integer-flag staged execution:** `python build_v1.py <flg>` selects the
  stage(s) to run, so prep / run / metrics / report can be executed and re-run
  independently (long MCMC need not be repeated to regenerate a figure):

  ```python
  # ioptics/runs/prototypes/expb_giop/build_v1.py
  import sys
  from ioptics import config, run, metrics, report

  CONFIG = 'run_v1.yaml'   # single source of truth (sweep id, datasets, algorithms)

  def main(flg):
      flg = int(flg)
      cfg = config.load(CONFIG)
      if flg & 2**0:  run.run_sweep(cfg)              # prep + retrieve → results.parquet (+ provenance)
      if flg & 2**1:  metrics.compute(cfg.sweep_id)   # score the results table
      if flg & 2**2:  report.standard(cfg.sweep_id)   # figures, tables, leaderboard, .rst, Bokeh

  if __name__ == '__main__':
      main(sys.argv[1] if len(sys.argv) > 1 else 0)
  ```

- **Paths derive from `$OS_COLOR` + the sweep id** (per the Resolved conventions):
  every stage reads/writes under `$OS_COLOR/IOPtics/runs/<sweep_id>/`, so the
  producer (run) and consumers (metrics, report) share path conventions
  automatically with no parameter drift.

## Data preparation

*Implements the design doc's **Data** section and Analysis §"Data preparation".
Modules: `ioptics.datasets`, `ioptics.prep`, `ioptics.noise`, `ioptics.records`.*

### What this generalizes (and the key refactor)

BING's `bing.fitting.l23.prep_one_l23` is the canonical end-to-end prep, but it
**entangles two concerns**: (a) loading/conditioning the *data* (read L23, pick a
grid, attach `Rrs` noise, extract truth), and (b) configuring the *algorithm*
(init models + priors, build the `rt_dict`, compute the Gordon forward `Rrs` and a
least-squares initial guess). It is also L23-specific and **resamples to a
satellite grid** via `convert_to_satwave`.

IOPtics splits these:

- **`ioptics.prep` keeps only concern (a)** — the dataset-agnostic data+noise+truth
  step — and emits a `PreparedRecord`. It does **no** model/prior/RT work.
- **Concern (b) moves to `ioptics.run`** (driven by an `AlgorithmSpec`), so the
  same `PreparedRecord` feeds every algorithm unchanged.
- **Native grids are preserved** (design decision): unlike `prep_one_l23`, prep
  does *not* call `convert_to_satwave`. For L23 the PACE noise model is
  **interpolated onto the native Hydrolight grid** instead of moving the data to
  PACE bands.

### Dataset adapters (`ioptics.datasets`)

A registry maps a dataset name to a thin adapter over the ocpy loader. Each
adapter knows how to enumerate observation ids and return one observation's
`Rrs` + truth on the **native grid**. This is the *only* module (with `noise`)
that imports ocpy.

| `dataset` | ocpy loader | `obs_id` | Native grid | Truth provided (ocpy source → IOPtics key) |
|---|---|---|---|---|
| `L23` | `hydrolight.loisel23.load_ds(X, Y)` | row index `0..N-1` | Hydrolight `Lambda` | **full spectral**: `a`, `bb`; `aph`→`a_ph`, `ag+ad`→`a_dg`, `anw`, `bbnw`→`bb_p`, `a−anw`→`a_w`, `bb−bbnw`→`bb_w`; scalars `Chl` (from `aph(440)/0.05582`), `Y` (Lee 2002), `Sdg` (`functions.fit_Sdg`) |
| `PANGAEA` | `insitu.pangaea.load(key)` + `.spectrum(df, id, kind)` | global `ID` | per-family native λ (each `kind` has its own λ set) | `aph`→`a_ph`, `acdom`→`a_dg` (combined CDOM+detrital), `bbp`→`bb_p`, `kd`; scalars `chla`, `tss` |
| `GLORIA` | `insitu.gloria.load_gloria()` | global `ID` | hyperspectral 350–900 @1 nm | **scalar only**: `a_cdom440`, `Chla`, `TSS`, `Secchi` (flag `a_cdom440` is CDOM-only vs retrieved `a_dg`) |

```python
# ioptics/datasets.py
ADAPTERS = {}                       # name -> Adapter

def register_dataset(name, adapter):
    ADAPTERS[name] = adapter

def get_adapter(name):              # 'L23' | 'PANGAEA' | 'GLORIA'
    return ADAPTERS[name]

class Adapter(Protocol):
    def obs_ids(self, **opts) -> list:                  ...   # enumerate observations
    def load_obs(self, obs_id, **opts) -> "RawObs":     ...   # Rrs Spectrum + truth dict + meta
```

`RawObs` is an internal carrier (`wave`, `Rrs`, optional `Rrs_err`, a `truth`
dict, and `meta`); `prep` turns it into the public `PreparedRecord`. L23 load
options `X` (1 first-pass, 4 later; never 2) and `Y` (00) are adapter opts and
are recorded in `meta`/provenance.

### The prepared record (`ioptics.records.PreparedRecord`)

The single common form fed to retrieval. Deliberately small so every dataset and
algorithm flow through it unchanged.

```python
@dataclass
class PreparedRecord:
    dataset:     str                  # 'L23' | 'PANGAEA' | 'GLORIA'
    obs_id:      int | str            # L23 row index, or PANGAEA/GLORIA global ID
    wave:        np.ndarray           # native grid (nm), ascending — the fit grid
    Rrs:         np.ndarray           # observed Rrs [sr^-1] on `wave`
    varRrs:      np.ndarray           # Rrs variance σ² on `wave` (the fit weights)
    Rrs_clean:   np.ndarray           # un-perturbed Rrs (== Rrs if no noise added; L23 truth)
    truth:       dict                 # free-form; see below. {} when none (GLORIA → scalars only)
    truth_interp: dict                # component -> bool: was it regridded onto `wave`?
    noise_model: str                  # provenance tag: 'pace' | 'insitu' | 'pct:0.05'
    noise_seed:  int | None           # RNG seed used to perturb Rrs (None if unperturbed)
    meta:        dict = field(default_factory=dict)   # lat/lon/date/source/sensor; L23 X,Y; water type / trophic bin
```

- **`truth`** is the free-form dict (per Package-layout Q8, kept open until the
  canonical component scheme is decided). Convention for its values:
  - **spectral** components (`a`, `bb`, `a_ph`, `a_dg`, `bb_p`, `a_w`, `bb_w`, …)
    are stored as ocpy **`Spectrum`** objects **pre-aligned to the record's
    `wave`** (per Q10). Prep interpolates each truth component — which may arrive
    on its own native λ set (notably PANGAEA's `a_ph`/`a_dg`/`bb_p`) — onto `wave`
    so truth and retrieval share one grid and scoring is direct. Each component's
    regrid status is recorded in **`truth_interp[component]`** (`True` if
    interpolated; `False` when it was already on `wave`, e.g. all L23 spectral
    truth). The original native grid is retained in the `Spectrum.metadata`
    (`orig_wave`) so nothing is lost. Truth values outside a component's measured
    λ range are left `NaN` (not extrapolated) and excluded by metrics.
  - **scalar** components (`Chl`, `Y`, `Sdg`, `a_cdom440`, `TSS`, `Secchi`) are
    plain floats (`truth_interp` is `False` for them).
  - Metrics later score on the **intersection** of an algorithm's retrieved
    components and the keys present here — now already on the common `wave`.
- **`Rrs`/`varRrs`** are raw arrays on `wave` (what BING's fitters consume); they
  can be viewed as a `Spectrum(wave, Rrs, errors=sqrt(varRrs))` for plotting.
  **`Rrs_clean`** keeps the un-perturbed spectrum so a noise-added L23 fit can
  still be compared against the noiseless input.

### Noise attachment (`ioptics.noise`)

Builds `varRrs` for a record; the choice is recorded as `noise_model` for
provenance. Thin wrappers over ocpy / BING:

```python
def attach_noise(wave, Rrs, model='pace', *, add_noise=True, seed=None):
    """Return (varRrs, Rrs_out, Rrs_clean, tag, seed_used).

    model='pace'   -> sigma = ocpy.satellites.pace.gen_noise_vector(wave)   # interp to native grid
                      varRrs = sigma**2
    model='insitu' -> use the dataset's own measured Rrs errors (varRrs = err**2)
    model='pct:X'  -> varRrs = (X * Rrs)**2                                 # e.g. 'pct:0.05'
    If add_noise: Rrs_out = Rrs + N(0, sqrt(varRrs)) using `seed` (recorded for
    reproducibility); Rrs_clean keeps the input. Else Rrs_out == Rrs_clean.
    """
```

- **L23 first-pass** uses `model='pace'` **with `add_noise=True`** (per Q11):
  the PACE per-band `Rrs` uncertainty (`ocpy.satellites.pace.gen_noise_vector`)
  is evaluated **on the native L23 grid** (no resampling), used both as the
  inverse-variance fit weight **and** to draw a **single noise realization** that
  perturbs the otherwise-noiseless Hydrolight `Rrs` — so the fit sees a realistic
  observation rather than perfect truth. The draw uses a **recorded `seed`**
  (provenance) so the sweep is reproducible, and `Rrs_clean` retains the
  noiseless input. (`bing.noise.scale_noise`/`add_noise` remain available for the
  satellite-band conventions BING already encodes.)
- **PANGAEA / GLORIA** use `model='insitu'` (the loader's measured `Rrs` errors;
  `pct` fallback otherwise) with **`add_noise=False`** — the in-situ `Rrs` is
  already a real, noisy observation, so no synthetic perturbation is added.

### Prep API (`ioptics.prep`)

```python
def prep_one(dataset, obs_id, *, noise=None, add_noise=None, seed=None,
             wv_min=None, wv_max=None, **load_opts) -> PreparedRecord:
    """Generalizes prep_one_l23 (data+noise+truth only). Loads one observation via
    the dataset adapter on its native grid, optionally trims to [wv_min, wv_max],
    attaches varRrs via ioptics.noise, **pre-aligns each spectral truth component
    onto `wave`** (flagging regridded components in truth_interp), and packs
    scalar truth as floats. No model/prior/RT work — that is run's job.

    Dataset-aware defaults (overridable):
      noise:     'pace'  for L23 (synthetic);  'insitu' for PANGAEA/GLORIA.
      add_noise:  True   for L23 (perturb the noiseless Rrs, seed recorded);
                  False  for in-situ (Rrs is already a real observation)."""

def prep_dataset(dataset, *, obs_ids=None, noise=None, add_noise=None,
                 seed=None, n_cores=1, **opts) -> list[PreparedRecord]:
    """Map prep_one over obs_ids (default: ALL with a usable Rrs — prep is
    permissive (Q12); missing truth components are simply absent and metrics
    report per-component coverage). Per-record seeds derive from `seed`+index so
    each L23 realization is independent yet reproducible. Parallel via
    ProcessPoolExecutor, mirroring bing.fitting.l23.batch_fit's pattern."""
```

`prep_dataset` is what a sweep's prep stage calls; the resulting
`list[PreparedRecord]` is handed to `run` (next section). Records are picklable,
so they cross the process pool and can be cached to disk between stages.

For **PANGAEA** (Q12) prep returns *every* `ID` that has a usable `Rrs`, even if
it lacks some truth components (not every ID carries all of `a_ph`/`a_dg`/`bb_p`);
the per-component `truth` dict simply omits what's missing and the metrics layer
reports coverage. No up-front completeness filter is applied.

### Worked example

```python
from ioptics import prep

# L23, first-pass: native Hydrolight grid; PACE noise both weights AND perturbs Rrs
recs = prep.prep_dataset('L23', obs_ids=range(500), seed=1234, X=1, Y=0)
r = recs[0]
r.wave                 # Hydrolight wavelengths (native)
r.Rrs                  # noise-perturbed Rrs (one PACE realization, seed recorded)
r.Rrs_clean            # noiseless Hydrolight Rrs (for reference)
r.varRrs               # PACE-derived variance on `wave`
r.truth['a_ph']        # ocpy Spectrum on `wave` (L23: already native → truth_interp False)
r.truth_interp['a_ph'] # False
r.truth['Chl']         # float

# PANGAEA: real in-situ Rrs (not perturbed); combined a_dg truth regridded onto wave
precs = prep.prep_dataset('PANGAEA')           # noise='insitu', add_noise=False
precs[0].truth['a_dg']         # Spectrum on `wave` (acdom = CDOM+detrital)
precs[0].truth_interp['a_dg']  # True (interpolated from its native λ set)
```

## Algorithm registry

*Implements design doc Analysis §"IOP retrieval" — "an algorithm is a
configuration." Module: `ioptics.algorithms` (`spec.py`, `registry.py`).*

### What a BING algorithm actually is

Reading `bing.parameters.standard`, every pre-wired combo (`expb_pow`, `giop`,
`gsm`, …) is just a factory that fills one namedtuple — `bing.parameters.p_ntuple`
`def_dict` — whose fields fully specify a retrieval:

- **models:** `model_names = [anw_model, bbnw_model]` → resolved by
  `bing.models.{anw,bbnw}.init_model` (a_nw registry: `Exp`, `Bricaud`,
  `ExpBricaud`, `GIOP`, `GSM`, `ExpNMF`, …; bb_nw: `Pow`, `Lee`, `GSM`, `Cst`, …).
- **priors:** `apriors`, `bpriors`, `othera_priors` — lists of BING prior dicts
  (`{flavor, pmin, pmax}`), one per model parameter.
- **RT options:** `variable_Gordon` (+`_G0`/`_bbp`), `include_Raman`,
  `include_Chl_fl`, `phi_C`, `double_gaussian`.
- **fixed slopes:** `set_Sdg`/`sSdg` (CDOM+detrital slope), `beta` (fixed bb slope).
- **noise:** `scl_noise`/`satellite`; **MCMC:** `nsteps`, `nburn`, `nMC`.

IOPtics' `AlgorithmSpec` is a **declarative, serializable mirror of exactly this**
— so an algorithm round-trips losslessly to a BING `p` and to a YAML block, and
nothing about the engine is re-implemented.

### `AlgorithmSpec` (`ioptics.algorithms.spec`)

```python
@dataclass
class RTOptions:
    variable_Gordon:     bool = True
    variable_Gordon_G0:  bool = False
    variable_Gordon_bbp: bool = False
    include_Raman:       bool = False     # elastic-only first pass (L23 X=1)
    include_Chl_fl:      bool = False     # turned on with L23 X=4
    phi_C:               float = 0.02
    double_gaussian:     bool = True

@dataclass
class MCMCOptions:
    nsteps: int = 40000
    nburn:  int = 1000
    nMC:    int | None = None

@dataclass
class AlgorithmSpec:
    name:        str                       # registry key, e.g. 'expb_pow'
    label:       str                       # human label, e.g. 'ExpB_Pow'
    anw_model:   str                       # BING a_nw model name, e.g. 'ExpBricaud'
    bbnw_model:  str                       # BING bb_nw model name, e.g. 'Pow'
    apriors:     list[dict]                # BING prior dicts, one per a-param
    bpriors:     list[dict]                # BING prior dicts, one per bb-param
    othera_priors: list[dict] | None = None
    rt:          RTOptions = field(default_factory=RTOptions)
    set_Sdg:     bool = False
    sSdg:        float = 0.002
    beta:        float | None = None
    fit_method:  str = 'chisq'             # 'chisq' (default) | 'mcmc'
    mcmc:        MCMCOptions = field(default_factory=MCMCOptions)
    noise_model: str = 'pace'              # provenance only — see note below

    # --- BING interop -------------------------------------------------
    def to_bing_p(self, **overrides):
        """Build the BING parameter namedtuple via bing.parameters.p_ntuple.gen,
        mapping spec fields → def_dict keys (model_names, apriors/bpriors/
        othera_priors, the RTOptions flags, set_Sdg/sSdg/beta, nsteps/nburn/nMC).
        `overrides` (e.g. satellite=..., wv_min=...) are passed through."""

    @classmethod
    def from_standard(cls, name, *, label=None, **overrides):
        """Seed from bing.parameters.standard.<name>() — read back model_names and
        a/b priors into a spec, applying any overrides. The lossless inverse of
        to_bing_p for the shipped combos."""

    def build_models(self, wave):
        """models = bing.models.utils.init([anw_model, bbnw_model], wave,
        (apriors, bpriors)); then bing.priors.set_standard_priors(models, p) and
        append othera_priors. Returns the [a_model, bb_model] list run uses."""
```

**Noise-model note (sweep-level, not per-algorithm).** Although `AlgorithmSpec`
carries a `noise_model` field (useful in provenance), `run` always fits against
the **`record.varRrs`** produced by `prep`. The noise model is a **sweep-level
constant held fixed across all algorithms** in a comparison (the design doc
requires the method be fixed within a comparison) — so it is **not** a
per-algorithm YAML override. `config` populates each spec's `noise_model` from the
sweep's single noise choice (the same one `prep` applied), purely so the
provenance is self-describing. Comparing one algorithm under two noise models is
therefore *two sweeps*, by construction.

### Registry (`ioptics.algorithms.registry`) — seeded with both in tandem

```python
REGISTRY: dict[str, AlgorithmSpec] = {}

def register(spec):          REGISTRY[spec.name] = spec
def get(name):               return REGISTRY[name]
def available():             return sorted(REGISTRY)

# --- the first two algorithms, built out together (design: in tandem) -----
register(AlgorithmSpec.from_standard('expb_pow', label='ExpB_Pow'))
register(AlgorithmSpec.from_standard('giop',     label='GIOP'))
```

Seeding **both** from the start is the point: the comparison tooling
(metrics/diagnostics/leaderboard) is exercised on a genuine two-way contest from
day one rather than on a single retrieval.

### The two, side by side

Resolved from `bing.parameters.standard` (verbatim priors):

| Field | `expb_pow` (ExpB_Pow) | `giop` (GIOP) |
|---|---|---|
| `anw_model` | `ExpBricaud` (exp `a_dg` + Bricaud `a_ph`) | `GIOP` |
| `bbnw_model` | `Pow` (power-law `bb_p`) | `Lee` |
| `apriors` | 3 — `Adg` `log_uniform[-6,5]`; `Sdg` `uniform[0.01,0.02]`; `Aph` `log_uniform[-6,5]` | 2 — `Adg`,`Aph` `log_uniform[-6,5]` |
| `bpriors` | 2 — `Bnw` `log_uniform[-6,5]`; `beta` `uniform[0,2]` | 1 — `Bnw` `log_uniform[-6,5]` |
| **free params `k`** | **5** | **3** |
| `set_Sdg` / `sSdg` | `False` / `0.002` | `False` / `0.002` |
| `rt` | elastic Gordon (variable G); Raman/Chl-fl off first pass | same |

The differing **`k` (5 vs 3)** is exactly what drives the AIC/BIC/ΔBIC model-
selection metrics (Metrics §3) — the in-tandem pair gives the leaderboard a real
complexity trade-off to score, not a formality.

### Adding a third (e.g. GSM)

One line, because `gsm` is already a `bing.parameters.standard` combo
(`model_names=['GSM','GSM']`, 2 a-priors + 1 b-prior):

```python
register(AlgorithmSpec.from_standard('gsm', label='GSM'))
```

A genuinely new algorithm (not shipped by BING) is added by constructing an
`AlgorithmSpec` directly with its `anw_model`/`bbnw_model` (must exist in BING's
`init_model` registries, or be contributed to BING) and prior lists — no IOPtics
core changes, just a `register(...)` call.

### YAML surface (sweep config)

Algorithms appear in the sweep YAML by registry name, with optional per-field
overrides; `config` resolves each to an `AlgorithmSpec` (the Python API builds the
identical object), honoring the "both" decision. **`fit_method` is overridable
per algorithm** (Q15) — e.g. run `giop` with MCMC while the rest stay
least-squares — but **`noise_model` is not** (Q14): it is a single sweep-level
key that `config` stamps onto every spec.

```yaml
sweep_id: expb_giop_L23_v1
datasets: [L23]
noise_model: pace                 # sweep-level, fixed for ALL algorithms (Q14)
algorithms:
  - expb_pow                      # registry defaults (sweep fit_method)
  - name: giop
    fit_method: mcmc              # per-algorithm override (Q15)
    mcmc: {nsteps: 40000, nburn: 1000}
fit_method: chisq                 # sweep default (least-squares first pass)
mcmc_subset: 200                  # # spectra to also run with MCMC
```

## Retrieval & run

*(forthcoming — Retrieval & run / Tasks #1)*

## Metrics & diagnostics

*(forthcoming — Metrics & diagnostics / Tasks #1)*

## Reporting

*(forthcoming — Reporting / Tasks #1)*

## Testing & CI

*(forthcoming — Testing & CI / Tasks #1)*

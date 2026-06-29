# IOPtics Implementation Document

**Version:** 0.22
**Date:** 2026-06-29
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
  `$OS_COLOR/IOPtics/runs/<sweep_id>/` holding the long/tidy tables
  (`results_spectral.parquet`, `results_scalar.parquet`), `provenance.yaml` (the
  version-stamped config record), `chains/` (raw MCMC chains for the subset), and
  `figures/`.
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
| `datasets` | A **dataset registry** mapping `dataset` name → loader adapter returning observations as ocpy `Spectrum`/`SpectrumStack` plus any truth IOPs, on the **native grid**. One adapter per source. | ocpy `hydrolight.loisel23`, `insitu.pangaea`, `insitu.gloria`, `spectra`; bing `fitting.l23.load_one_l23` (L23 truth) | Data |
| `prep` | The **dataset-agnostic prep layer** — generalizes `bing.fitting.l23.prep_one_l23` to any dataset: take a loaded observation, attach `Rrs` uncertainty, assemble the `PreparedRecord` (obs `Rrs`+σ on native grid; truth where available). No model/prior init here (that is the algorithm's job at run time). | reads ocpy loaders via `datasets`; calls `noise` | Data prep |
| `noise` | Build the `Rrs` variance vector for a record. L23 first-pass uses **`ocpy.satellites.pace`** (`gen_noise_vector`); in-situ datasets carry their own `errors`. Thin wrapper so the noise model is a provenance-recorded choice. | ocpy `satellites.pace` (+ modis/seawifs/sbg); BING `noise.scale_noise` | Data prep |
| `algorithms.spec` | **`AlgorithmSpec`** — the declarative description of one algorithm (a_nw + bb_nw model names, priors, RT toggles incl. Raman/Chl-fl, fit method, noise model). `.to_bing_p()` emits the BING parameter namedtuple; `.from_standard(name)` seeds from `bing.parameters.standard`. | BING `parameters.standard`, `parameters.p_ntuple`, `priors` | Analysis (IOP retrieval) |
| `algorithms.registry` | Name → `AlgorithmSpec` factory; the growing registry. **Seeded with `expb_pow` and `giop`** side by side; `register()` adds more (e.g. `gsm`). | wraps `algorithms.spec` | Analysis (in-tandem) |
| `run` | The driver: **`run_algorithm(spec, record)`** for one fit; `run_batch` over records; `run_sweep` over algorithms × records. Least-squares **default** (`bing.fitting.chisq_fit.fit`); **MCMC** (`bing.fitting.inference.fit_one/fit_batch`) for a flagged subset. Builds BING models per record via `init_model`, the `rt_dict` via `rt.defs`, runs, hands chains/params to `evaluate`. | BING `models.init_model`, `rt.defs`, `fitting.chisq_fit`, `fitting.inference` | Analysis (retrieval, two fitting modes) |
| `evaluate` | Turn a fit into a **`RetrievalResult`**: reconstruct `a(λ)`/`bb(λ)` and components ± uncertainty (MCMC percentiles or least-squares covariance), compute fit stats. | BING `evaluate.reconstruct_from_chains` / `reconstruct_chisq_fits` / `calc_stats`, `stats.calc_chisq` / `calc_ICs` | Analysis (uncertainty) |
| `provenance` | Assemble the **YAML/JSON provenance record** for a sweep (model config, RT options, fit method, noise model, and — for MCMC — priors) and **stamp versions** (design-doc, registry entry, dataset, ocpy/bing/ioptics commits). Written beside the results table. | reads `AlgorithmSpec`; package versions | Analysis (provenance) |
| `io` | Read/write the **long/tidy parquet** tables and own the **sweep directory layout** `$OS_COLOR/IOPtics/runs/<sweep_id>/{results_spectral.parquet, results_scalar.parquet, provenance.yaml, chains/, figures/}`; save/load MCMC chain NPZs. | pandas/pyarrow | Reporting (artifacts) |
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
- **BING is imported by** `algorithms.spec`, `run`, and `evaluate` (models,
  parameters, rt, priors, fitting, evaluate, stats) **and by `datasets`** for
  dataset-specific truth extraction — the L23 adapter reuses
  `bing.fitting.l23.load_one_l23` rather than re-deriving Chl/Y/Sdg/component
  truth. The boundary that holds is the *downstream* one: nothing in `metrics`,
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
    init:        dict                 # TRUTH-FREE model-init values from observed Rrs: {'Chl','Y'}
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
- **`init`** holds **truth-free** values derived from the *observed* `Rrs` to
  initialize BING model internals at run time — `Y` via the Lee (2002)
  prescription and `Chl` via an OC-style band ratio (`ocpy.chl.band_ratios`).
  These seed `bing.models.utils.init_other_bits` (Bricaud `a_ph`, Lee `bb_p`) and
  the least-squares starting guess **without peeking at truth**, so benchmark
  retrievals stay honest. (Distinct from `truth['Chl']`/`truth['Y']`, which are
  scored, never used to drive a fit.)

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

*Implements design doc Analysis §"IOP retrieval", §"Uncertainty quantification",
and §"Provenance & reproducibility". Modules: `ioptics.run`, `ioptics.evaluate`,
`ioptics.io`, `ioptics.provenance`.*

### `run_algorithm(spec, record)` — one fit, end to end

This is where concern (b) deferred by `prep` happens. Given an `AlgorithmSpec`
and a `PreparedRecord`, `run_algorithm` wires BING **on the record's native
grid** and returns a `RetrievalResult`:

```python
def run_algorithm(spec, record, *, fit_method=None,
                  perc=((16,84),(2.5,97.5))) -> RetrievalResult:
    p        = spec.to_bing_p(wv_min=record.wave.min(), wv_max=record.wave.max())
    models   = spec.build_models(record.wave)        # a_nw, bb_nw on the NATIVE grid
    rt_dict  = bing.rt.defs.rt_dict_from_p(p)
    # truth-free model internals (Bricaud Chl, Lee Y) from record.init
    bing.models.utils.init_other_bits(models, Chl=record.init['Chl'],
                                      Y=record.init['Y'], Rrs=record.Rrs)
    p0       = initial_guess(models, record)          # truth-free (see note)
    method   = fit_method or spec.fit_method          # 'chisq' default
    items    = (record.Rrs, record.varRrs, p0, record.obs_id)

    if method == 'chisq':
        ans, cov, _ = bing.fitting.chisq_fit.fit(items, models, rt_dict, bounds=...)
        return evaluate.from_chisq(spec, record, models, rt_dict, ans, cov, perc)
    else:  # 'mcmc'
        pdict   = bing.fitting.inference.init_mcmc(models, nsteps=spec.mcmc.nsteps,
                                                   nburn=spec.mcmc.nburn)
        pdict['Chl'], pdict['Y'] = _idx_arrays(record)        # BING's idx-keyed lookup
        chains, _ = bing.fitting.inference.fit_one(items, models=models,
                          pdict=pdict, chains_only=True, rt_dict=rt_dict)
        return evaluate.from_chains(spec, record, models, rt_dict, chains, perc)
```

Two points that make this the uniform layer rather than a fork of `prep_one_l23`:

- **Native grid.** Models are built on `record.wave` (no `convert_to_satwave`);
  the design's native-grid decision is honored at the fit, not just at prep.
- **Truth-free initial guess.** `initial_guess()` seeds the least-squares `p0`
  (and walker centroid) from **prior-central values refined by a QAA-style band
  inversion of the observed `Rrs`** — never from `record.truth`. (`prep_one_l23`
  seeds from the true IOPs for convenience; IOPtics must not, or the benchmark is
  circular. A from-truth seed remains available as a diagnostic only.)

### Uncertainty: `ioptics.evaluate`

Uncertainty is a first-class output (design §Uncertainty), produced **the same
way for both fit methods** so intervals are comparable:

- **MCMC** → `bing.evaluate.reconstruct_from_chains(models, chains, rt_dict, perc)`
  gives median + percentile bands for `a(λ)`, `bb(λ)`, and model `Rrs`; sub-
  components `a_ph`/`a_dg` come from `models[0].eval_anw(..., retsub_comps=True)`
  and `bb_p` from `models[1].eval_bbnw(...)` over the chain (as in
  `l23.process_one`).
- **least-squares** → draw `N≈1000` parameter samples from the fitted
  `MultivariateNormal(ans, cov)`, push each through
  `bing.evaluate.reconstruct_chisq_fits`, and take the **same percentiles**. This
  turns curve_fit's covariance into 68/95 % bands consistent with the MCMC path
  (the design's "covariance-propagated intervals").
- **fit stats** via `bing.stats.calc_chisq` and `calc_ICs`: χ², reduced
  **χ²ᵥ = χ²/(n_bands − k)**, AIC, BIC, with `k = Σ model.nparam`,
  `n_bands = len(record.wave)`.

`evaluate.from_chains` / `from_chisq` assemble these into a `RetrievalResult`:

```python
@dataclass
class ComponentFit:                  # one IOP component on the fit grid
    wave: np.ndarray
    med:  np.ndarray
    lo68: np.ndarray; hi68: np.ndarray
    lo95: np.ndarray; hi95: np.ndarray

@dataclass
class RetrievalResult:
    dataset: str; obs_id: int|str; algorithm: str
    fit_method: str                  # 'chisq' | 'mcmc'
    components: dict[str, ComponentFit]   # 'a','bb','a_ph','a_dg','bb_p', + 'Rrs_model'
    params:  dict                    # {pname: (med, sigma)} incl. Sdg, beta, Adg, Aph, Bnw
    scalars: dict                    # derived scalars ± unc: Chl, a_cdom440, ...
    stats:   dict                    # chi2, chi2_nu, AIC, BIC, n_bands, k
    status:  str                     # 'ok' | 'fit_failed' | QC flag (e.g. 'Rrs_MAE>0.25')
    provenance_id: str               # → the sweep's provenance record + algorithm block
```

### Sweep layers

**Error policy (`strict`).** `run_batch`/`run_sweep` take a `strict` flag.
`strict=True` (the current **development** default) fails fast — a fit error
propagates with its traceback so bugs surface. `strict=False` is the intended
**production** mode: a failed fit becomes a `status='fit_failed'`
`RetrievalResult` and the sweep continues (failures show up as flagged rows +
reduced coverage, per the Metrics partial-retrieval rules). **TODO:** flip the
default to robust (`strict=False`) for production sweeps once the engine is
exercised at scale.

```python
def run_batch(spec, records, *, fit_method=None, n_cores=1,
              strict=True) -> list[RetrievalResult]:
    """One algorithm over many records (ProcessPoolExecutor), mirroring
    bing.fitting.l23.batch_fit's chunked parallelism. strict: fail-fast (dev)
    vs fit_failed-and-continue (production)."""

def run_sweep(cfg) -> SweepResult:
    """All algorithms × all records. For each algorithm: run_batch with the sweep
    fit_method (chisq) over ALL records, then re-run the cfg.mcmc_subset records
    with method='mcmc'. Flattens results to the long/tidy tables, **saves the raw
    MCMC chains**, and writes the provenance record under
    $OS_COLOR/IOPtics/runs/<sweep_id>/."""
```

This realizes the design's **least-squares across the full sweep, MCMC on a
subset**: every (algorithm, record) gets a fast χ² fit; only `mcmc_subset`
records additionally get a posterior. Both kinds of result land in the same
tables, tagged by `fit_method`.

**Raw MCMC chains are persisted** (Q18). Because MCMC runs only on the (small)
`mcmc_subset`, `run_sweep` saves each posterior's full chain array to
`$OS_COLOR/IOPtics/runs/<sweep_id>/chains/<algorithm>_<obs_id>.npz` (via BING's
`fitting.l23.save_chains` convention — chains + `obs_Rrs`/`varRrs`/`Chl`/`Y`), so
corner plots, coverage tests, and re-analysis don't require re-fitting. The
matching `results_scalar` rows carry a `chain_file` pointer; least-squares rows
leave it null. The per-sweep directory therefore becomes
`runs/<sweep_id>/{results_spectral.parquet, results_scalar.parquet,
provenance.yaml, chains/, figures/}`.

### Results-table schema (long/tidy parquet)

Per the resolved convention, two tidy parquet files per sweep (both keyed so a
group-by drives the metrics layer directly):

**`results_spectral.parquet`** — one row per
`(dataset, obs_id, algorithm, fit_method, component, wavelength)`:

| column | meaning |
|---|---|
| `dataset, obs_id, algorithm, fit_method` | the retrieval key |
| `component` | `a` `bb` `a_ph` `a_dg` `bb_p` `Rrs_model` |
| `wavelength` | nm (native grid) |
| `value` | median retrieval at that λ |
| `lo68,hi68,lo95,hi95` | credible/confidence bounds |
| `truth` | truth at that λ (NaN if dataset lacks it / out of range) |
| `truth_interp` | bool — was truth regridded onto this λ |
| `unit` | e.g. `1/m`, `1/sr` |

**`results_scalar.parquet`** — one row per `(dataset, obs_id, algorithm,
fit_method)`:

| column | meaning |
|---|---|
| key cols | `dataset, obs_id, algorithm, fit_method` |
| `chi2, chi2_nu, AIC, BIC, n_bands, k` | fit-quality / model-selection |
| `Chl, sig_Chl, a_cdom440, sig_a_cdom440, Sdg, sig_Sdg, beta, sig_beta` | derived scalars ± unc |
| `*_truth` | matching truth scalars (NaN if absent) |
| `status` | `ok` / QC flag |
| `chain_file` | path to the saved MCMC chain NPZ (null for χ² rows) |
| `provenance_id` | link into `provenance.yaml` |

`ioptics.io` owns reading/writing these and the sweep directory. Reference
wavelengths (440/443, 555, 670) are *not* pre-baked — metrics slice them from the
spectral table — so the table stays algorithm/dataset-agnostic.

### Provenance record (`ioptics.provenance` → `provenance.yaml`)

One human-readable YAML per sweep, beside the tables, capturing everything needed
to reproduce it (design §Provenance — including **priors for any MCMC**):

```yaml
sweep_id: expb_giop_L23_v1
created: 2026-06-21T14:00:00Z
versions:
  ioptics: {commit: a1b2c3d, version: 0.0.dev0}
  bing:    {commit: e4f5a6b}
  ocpy:    {commit: 0c9d8e7}
  design_doc: 0.15
  implementation_doc: 0.11
config:                      # verbatim copy of the sweep YAML (single source of truth)
  datasets: [L23]
  noise_model: pace          # fixed across algorithms
  fit_method: chisq
  mcmc_subset: 200
  seed: 1234
datasets:
  L23: {X: 1, Y: 0, n_obs: 3320}
algorithms:
  - name: expb_pow
    label: ExpB_Pow
    anw_model: ExpBricaud
    bbnw_model: Pow
    apriors: [{flavor: log_uniform, pmin: -6, pmax: 5},   # Adg
              {flavor: uniform,     pmin: 0.01, pmax: 0.02}, # Sdg
              {flavor: log_uniform, pmin: -6, pmax: 5}]    # Aph
    bpriors: [{flavor: log_uniform, pmin: -6, pmax: 5},   # Bnw
              {flavor: uniform,     pmin: 0.0, pmax: 2.0}] # beta
    rt: {variable_Gordon: true, include_Raman: false, include_Chl_fl: false}
    set_Sdg: false
    fit_method: chisq
  - name: giop
    label: GIOP
    anw_model: GIOP
    bbnw_model: Lee
    apriors: [{flavor: log_uniform, pmin: -6, pmax: 5}, {flavor: log_uniform, pmin: -6, pmax: 5}]
    bpriors: [{flavor: log_uniform, pmin: -6, pmax: 5}]
    rt: {variable_Gordon: true, include_Raman: false, include_Chl_fl: false}
    fit_method: mcmc
    mcmc: {nsteps: 40000, nburn: 1000}
```

The `provenance_id` on each result row points at `<sweep_id>` + the algorithm
block, so any single row is traceable to the exact model, priors, RT options, fit
method, and noise model that produced it — and the whole sweep regenerates from
`provenance.yaml`.

## Metrics & diagnostics

*Implements the design doc's **Metrics** section (§1–6 and "Handling
non-uniformity"). Modules: `ioptics.metrics`, `ioptics.diagnostics`. Both consume
the long/tidy results tables — neither imports BING or ocpy.*

### Design principle: metrics are table-in, table-out

Every metric is a **group-by reduction over the two results tables**
(`results_spectral`, `results_scalar`). A metric never re-runs a fit or touches a
`Spectrum`; it reads `value`/`truth`/bounds columns and emits a tidy **metrics
table**. This keeps the comparison machinery independent of the engine and means
a new algorithm is scored simply by being present in the table.

```python
def compute(sweep_id, *, levels=(0.68, 0.95), ref_waves=REF_WAVES) -> MetricsTables:
    """Read runs/<sweep_id>/results_{spectral,scalar}.parquet and emit:
      - metrics_spectral.parquet : per (dataset, algorithm, component, wavelength)
      - metrics_scalar.parquet   : per (dataset, algorithm[, stratum]) summaries
      - metrics_pairwise.parquet : per (dataset, component, ref_wave) head-to-head
    All accuracy metrics are log10 / multiplicative (design Conventions)."""

REF_WAVES = {'absorption': (440, 443), 'backscatter': (555, 670)}
```

The metric primitives operate on aligned `(M, O)` arrays (modeled vs
observed/true), already on the common `wave` (prep pre-aligned truth). Pairs with
`NaN` truth (component/λ absent for a dataset) are dropped *before* reduction, and
the surviving **count `n` and coverage are recorded** alongside every number.

### §1 Retrieval accuracy vs. truth (log space)

Adopting Erickson (2023) Eqs. 13–14 / Seegers (2018), all in `log10`:

```python
def mae(M, O):    return 10**np.nanmean(np.abs(np.log10(M) - np.log10(O))) - 1   # multiplicative
def bias(M, O):   return 10**np.nanmean(    np.log10(M) - np.log10(O) ) - 1      # signed
def rms_log(M,O): return np.sqrt(np.nanmean((np.log10(M) - np.log10(O))**2))     # + unbiased RMS
def median_ratio(M, O):           return np.nanmedian(M / O)
def ratio_hist(M, O, edges=RATIO_EDGES):    ...   # Erickson Fig.4 buckets
def type2_fit(M, O):              return slope, intercept, r2          # log–log Type-II regression
RATIO_EDGES = [0, 1/3, 1/2, 3/4, 1, 4/3, 2, 3, np.inf]
```

Applied **per component** (`a`, `bb`, `a_ph`, `a_dg`, `bb_p`) and **per
wavelength** across the native grid, then summarized at the reference wavelengths
(440/443 for absorption, 555/670 for backscatter) — the spectral extension over
BING/Erickson's single-λ reporting. Output rows carry `(dataset, algorithm,
component, wavelength | ref, metric, value, n)`.

**Reference-wavelength matching (Q19).** Native grids rarely land exactly on
440/443/555/670, so a ref-λ summary uses the **nearest native band within ±3 nm**
(no extra interpolation of already-retrieved quantities) and **records the actual
λ used** in a `ref_match` column; if no band falls within tolerance the ref row is
omitted (not forced).

### §2 Internal closure & fit quality (Rrs space)

Computed from the `Rrs_model` component vs `Rrs_obs` (linear-space χ²; log-space
MAE/bias), with the χ²ᵥ/AIC/BIC already in `results_scalar`:

- **χ²ᵥ** carried through from `run` (BING `stats`); headline single-fit flag —
  ≈1 good, **<1 overfit**, >1 underfit.
- **Rrs MAE/bias** (log-space §1 form on `Rrs`) with the **dual-sided window**
  (Erickson): good ≈ measurement noise (~5%); flag **`fit_noise`** when MAE falls
  *well below* the noise floor; QC-fail **`Rrs_MAE>0.25`** marks non-solutions
  (mirrors the `status` set in `run`).

### §3 Model selection / complexity

Straight from `results_scalar` (`AIC`, `BIC`, `k`, `n_bands`):

```python
def delta_bic(bic_a, bic_b):   return bic_a - bic_b      # <0 favors the MORE complex model
def dbic_cdf(df, model_a, model_b, by=None):   ...       # CDF over the dataset, stratifiable
```

The in-tandem `expb_pow` (k=5) vs `giop` (k=3) pair makes ΔBIC a real per-spectrum
contest; reported as a **CDF over the dataset** (fraction favoring each), optionally
stratified by S/N or sensor.

### §4 Uncertainty assessment — incl. the new coverage test

Uses the credible/confidence bounds in the tables (and the persisted chains for
corner/degeneracy work):

```python
def coverage(O, lo, hi):    return np.nanmean((O >= lo) & (O <= hi))   # per level
# scored at 68% and 95%: the fraction inside the X% interval should ≈ X%
def detection(med, lo, hi):  ...     # Nσ detection vs upper-limit (a_ph non-detections)
```

`coverage` is the design's **formal calibration metric** (absent from both source
papers): evaluated per component/ref-λ at the **68% and 95%** levels and reported
as `(level, nominal, empirical, n)`. Parameter **degeneracy** (corner plots,
prior-dominated params) is a diagnostic (below), driven from the saved chains.

### §5 Cross-algorithm comparison

```python
def wins(table, *, by=('dataset','component','ref_wave'), metric='abs_log_err'):
    """Per-spectrum head-to-head: fraction of contests each algorithm is closer to
    truth (Erickson/Seegers). → metrics_pairwise.parquet.
    metric='abs_log_err' = |log10(M/O)| per contest (closer wins). Provisional —
    flagged for revisit (could become within-uncertainty agreement or signed bias)."""
def rankings(metrics_scalar):    ...    # per-variable rank by |bias|, MAE, wins (Erickson Tbl 2)
```

### Handling non-uniformity (partial retrievals)

The one rule that makes "uniform metrics" honest when algorithms/datasets differ:

- **Score the intersection.** For each `(algorithm, dataset, component, λ)` a
  metric is computed only where **both** a retrieval and a truth value exist
  (non-NaN). Everything else is skipped, never zero-filled.
- **Record coverage.** Each metric row stores `n` and a `coverage` fraction (how
  many obs / which components·λ were scorable), so a high score on thin coverage
  is visible. A partial-retrieval algorithm (retrieves only some components) is
  simply absent for the rest — its rows don't exist, and rankings note the reduced
  set it competed on.
- **Dataset truth mapping** is already baked into the table: retrieved `a_dg` vs
  PANGAEA's combined `a_dg`; retrieved `a_dg(440)` vs GLORIA's `a_cdom440` with a
  persisted **`caveat='CDOM_vs_adg'`** flag so reports surface the mismatch.

### Stratification

Every scalar metric is computed overall **and** within strata; `compute` adds a
`stratum` column and repeats the reduction per bin. For the L23 + PANGAEA first
pass (Q20):

```python
CHL_BINS = [(0.0, 0.1, 'oligotrophic'),   # mg m^-3
            (0.1, 1.0, 'mesotrophic'),
            (1.0, np.inf, 'eutrophic')]
```

Chl for binning comes from the **truth** scalar where available (L23; PANGAEA
`chla`), else from `record.init['Chl']`. **S/N** stratification follows from the
fixed sweep noise model. **Water type (Case I/II)** is **deferred** until in-situ
metadata is wired in (no reliable per-obs flag yet for L23/PANGAEA) — the
`stratum` machinery already supports adding it later without schema change.

### Diagnostics (`ioptics.diagnostics`) — figure data, not figures

`diagnostics` computes the **arrays** behind each standard figure (so `report` and
`bokeh` can render them statically or interactively); plotting lives in
`plotting`/`report`.

| function | returns | design ref |
|---|---|---|
| `taylor_stats(table, ref)` | per-algorithm `(corr, norm_std, crmsd)` for the Taylor diagram | §6 Taylor 2001 |
| `target_stats(table, ref)` | per-algorithm `(bias, signed_unbiased_rmsd)` for the Target diagram | §6 Jolliff 2009 |
| `scatter_data(table, comp, ref)` | retrieved-vs-true points (log–log) + 1:1/3:1/0.3:1 guides | §6 |
| `ratio_hist_data(...)` | ratio-histogram counts (RATIO_EDGES) | §1/§6 |
| `residual_spectra(table, obs_id)` | `Rrs_obs − Rrs_model` (+ χ²ᵥ annotation) | §6 |
| `corner_data(chain_file)` | flattened chain samples + labels (loads the saved NPZ) | §4/§6 |
| `dbic_cdf_data(scalar, a, b)` | ΔBIC CDF curve(s), stratifiable | §3/§6 |

Both `metrics` and `diagnostics` are pure functions of the persisted sweep
artifacts, so a report (next section) is fully regenerable from
`runs/<sweep_id>/` with no re-fitting.

## Reporting

*Implements the design doc's **Reporting** section. Subpackage: `ioptics.report`
(`figures`, `tables`, `leaderboard`, `bokeh`, `rst`, `standard`) over
`ioptics.plotting`. Consumes only the persisted sweep artifacts — fully
regenerable, no re-fitting.*

### Inputs and the regenerability contract

`report` reads exactly what `run` and `metrics` wrote under
`$OS_COLOR/IOPtics/runs/<sweep_id>/`:

```
results_spectral.parquet  results_scalar.parquet      # run
metrics_{spectral,scalar,pairwise}.parquet            # metrics.compute
chains/                   provenance.yaml             # run (MCMC subset; provenance)
```

Because every output derives from these files, a report is **regenerable on
demand** (the design's "generated on demand, not via CI") and **provenance-stamped**
(every figure/page carries the versions from `provenance.yaml`).

### `ioptics.plotting` — static figure primitives

Low-level, publication-styled matplotlib builders, reusing `bing.plotting` where
it already fits (`show_anw_fits`, `corner_plot`, `hist2d`). Each takes
diagnostic/metric **arrays** (from `ioptics.diagnostics`/`metrics`) and returns a
`matplotlib.Figure` — no file I/O, no table reads:

```python
def scatter_log(data, *, guides=(1, 3, 1/3)) -> Figure      # retrieved-vs-true, 1:1/3:1/0.3:1
def ratio_hist(data) -> Figure
def spectra_band(comp_fit, truth=None) -> Figure            # a/bb ± uncertainty band
def residual_rrs(resid, chi2_nu) -> Figure
def taylor(stats) -> Figure                                 # Taylor 2001
def target(stats) -> Figure                                 # Jolliff 2009
def corner(chain_data) -> Figure                            # wraps bing.plotting.corner_plot
def dbic_cdf(curves) -> Figure
```

### `report.figures` / `report.tables` — the standard set

The uniform per-(algorithm, dataset) artifact set the design fixes — generated
identically for every algorithm so reports are comparable:

| builder | produces | source |
|---|---|---|
| `figures.scatter_set(sweep, comp)` | retrieved-vs-true scatter per component/ref-λ | `diagnostics.scatter_data` |
| `figures.spectra_set(sweep, obs)` | `a(λ)`/`bb(λ)`±band, decomposed `a_dg`/`a_ph` | `results_spectral` |
| `figures.closure_set(sweep, obs)` | residual/closure `Rrs` (χ²ᵥ annotated) | `diagnostics.residual_spectra` |
| `figures.taylor_target(sweep)` | Taylor + Target diagrams (all algorithms) | `diagnostics.{taylor,target}_stats` |
| `figures.corner_set(sweep)` | corner plots for the MCMC subset | `chains/` |
| `figures.dbic_cdf(sweep)` | ΔBIC CDF (expb_pow vs giop, …) | `metrics_scalar` |
| `tables.accuracy(sweep)` | per-variable bias/MAE/RMS/wins, per stratum | `metrics_{scalar,pairwise}` |
| `tables.qc(sweep)` | fraction flagged non-solution / fit-noise | `results_scalar.status` |

All figures are written to `runs/<sweep_id>/figures/` (PNG + PDF for manuscripts);
tables to CSV alongside.

**Per-obs figure volume (Q24).** `spectra_set`/`closure_set`/`corner_set` are
per-spectrum and would explode for L23 (thousands), so the standard report renders
them only for a **curated handful** — the MCMC subset plus a few exemplars per
trophic bin (selected by `cfg`) — while the full population is covered by the
aggregate figures (scatter, Taylor/Target, ratio-hist) and the interactive Bokeh.

### `report.leaderboard` — persistent, cross-sweep

The headline deliverable: a leaderboard that **accumulates across sweeps** rather
than living inside one. It scans the runs root, reads each sweep's
`metrics_scalar.parquet` + `provenance.yaml`, and folds every (algorithm, dataset)
result into one ranked, append-only store:

```python
def update(runs_root=RUNS_ROOT) -> DataFrame:
    """Aggregate metrics_scalar across ALL runs/<sweep_id>/ into
    $OS_COLOR/IOPtics/leaderboard.parquet, keyed (algorithm, dataset, stratum,
    component, ref_wave, metric) with the source sweep_id + versions. Idempotent:
    re-folding a sweep replaces its rows."""
def render(fmt='rst') -> str:   # ranked table(s) for the site landing page
```

Default ranking (Q23): **wins** first, then `|bias|` and log-space **MAE** at the
reference wavelengths, per `(dataset, component)`; MAE/bias and coverage are shown
as adjacent columns so the familiar accuracy numbers are visible alongside the
head-to-head result.

As algorithms are added (the `expb_pow`/`giop` pair, then `gsm`, …) each new sweep
just calls `leaderboard.update()` and the standing comparison grows — the design's
"accumulates and updates" leaderboard.

### `report.bokeh` — standalone/static interactive figures

Per the pinned decision, **self-contained BokehJS HTML** (no Bokeh server): JS
`CustomJS` callbacks driven by a `ColumnDataSource` built from the metrics tables,
so a reader can **select algorithm / dataset / stratum** and inspect
retrieved-vs-true scatter, spectra ± bands, and the leaderboard with hover/pan/zoom.

```python
def interactive_scatter(sweep_or_runs) -> str   # returns standalone HTML (file_html)
def interactive_leaderboard(runs_root) -> str
# rendered with bokeh.embed.file_html(..., CDN→inline) so the .html works offline /
# embeds directly in readthedocs.
```

### `report.rst` / `report.standard` — the on-demand report & site

`standard.build(sweep_id, kind=...)` assembles one of the design's three report
types from the figures/tables/leaderboard, emitting **reStructuredText** plus its
assets:

```python
def build(sweep_id, *, kind='cross_algorithm') -> Path:
    """kind ∈ {'per_algorithm', 'cross_algorithm', 'per_dataset'}.
    Writes docs/source/reports/<sweep_id>/<kind>.rst + figures/tables/bokeh,
    each page header-stamped with provenance versions (design-doc,
    implementation-doc, registry entry, dataset, ocpy/bing/ioptics commits)."""
```

- **Single accumulating site.** Pages land in the IOPtics Sphinx tree
  (`docs/source/reports/<sweep_id>/`) and are linked from a toctree; the
  **leaderboard is the landing page**. One readthedocs site grows as
  sweeps/algorithms accumulate (no per-sweep micro-sites).
- **What lives where (Q22).** The generated `.rst` pages and their lightweight
  display assets (figure PNGs, the Bokeh HTML) are **committed into the repo docs
  tree** so readthedocs builds them directly; the heavy artifacts (parquet tables,
  raw chains) stay under `$OS_COLOR/IOPtics/runs/` and are **not** committed.
  `standard.build` copies the needed figures/Bokeh from `runs/<sweep_id>/figures/`
  into `docs/source/reports/<sweep_id>/` at build time.
- **Reproducibility stamp.** Every page prints the provenance block, so a reader
  can trace any figure to the exact sweep, config, and code commits — and
  regenerate it from `runs/<sweep_id>/`.
- **On demand.** Reports are built by calling `standard.build` (e.g. stage 3 of a
  `runs/.../build_vN.py`), never auto-built by CI on commit (Testing & CI §).

### How a sweep's report stage looks

```python
# stage 3 of ioptics/runs/prototypes/expb_giop/build_v1.py
from ioptics import report
report.standard.build(cfg.sweep_id, kind='cross_algorithm')  # figures+tables+bokeh+rst
report.leaderboard.update()                                  # fold into the standing board
```

## Testing & CI

*Implements the design doc's testability intent. Tests live in `ioptics/tests/`;
all run in the **`ocean14`** conda environment (per `CLAUDE.md`).*

### Two tiers, mirroring ocpy's `test_pangaea.py`

ocpy's pattern is the template: **data-independent tests always run** on synthetic
inputs; **data-dependent tests skip automatically** when the `$OS_COLOR` data tree
is absent (so the suite is green on a laptop or a fresh CI runner with no data
mounted).

```python
# ioptics/tests/conftest.py
import os, pytest

def _os_color_available():
    return os.getenv('OS_COLOR') is not None and os.path.isdir(os.getenv('OS_COLOR'))

needs_data = pytest.mark.skipif(
    not _os_color_available(), reason='requires the $OS_COLOR data tree')

def _l23_available():
    try:
        from ocpy.hydrolight import loisel23
        return os.path.isfile(os.path.join(loisel23.l23_path, 'Hydrolight100.nc'))
    except Exception:
        return False

needs_l23     = pytest.mark.skipif(not _l23_available(),     reason='requires L23 data')
needs_pangaea = pytest.mark.skipif(not _pangaea_available(), reason='requires PANGAEA V3')
```

### Tier 1 — data-independent (always run)

The bulk of IOPtics is pure transformation of in-memory structures and tables, so
most of it is testable with **tiny synthetic fixtures** and no real data:

| target | test (synthetic) |
|---|---|
| `algorithms.spec` | `from_standard('expb_pow')`/`giop` round-trip to `to_bing_p()` and back; param counts (k=5 / k=3); prior dicts match `bing.parameters.standard` |
| `algorithms.registry` | `expb_pow` **and** `giop` seeded; `register`/`get`/`available`; duplicate-name guard |
| `config` | YAML ⇄ `AlgorithmSpec` parse/validate; required `sweep_id`; per-algorithm `fit_method` override; sweep-level `noise_model` not overridable |
| `records` / `prep` | build a synthetic `PreparedRecord`; truth pre-aligned onto `wave`; `truth_interp` flags; NaN outside range (no extrapolation) |
| `noise.attach_noise` | `pct:X` → varRrs; `add_noise` with a fixed seed is reproducible; in-situ passthrough |
| `metrics.*` | log-space MAE/bias/RMS, median ratio, ratio buckets, coverage, ΔBIC, wins on **hand-built (M,O) arrays with known answers**; NaN intersection rule; ±3 nm ref-band match |
| `diagnostics.*` | Taylor/Target/scatter array shapes & known values on toy inputs |
| `io` | long/tidy parquet round-trip; sweep-dir layout creation |
| `provenance` | record assembles; versions captured; `provenance_id` resolves |
| `report.leaderboard` | `update()` idempotency (re-folding a sweep replaces its rows); ranking order |

A **fast end-to-end micro-test** runs the whole pipeline on a **synthetic 5-band
Rrs** built from a known forward model: `prep → run_algorithm(chisq) → evaluate →
metrics`, asserting the retrieval recovers the planted IOPs within tolerance and
the tables/provenance are well-formed. This exercises the BING wiring (`init_model`,
`chisq_fit.fit`, `evaluate`) without any `$OS_COLOR` dependency or MCMC.

### Tier 2 — data-dependent (skip-guarded)

Marked `@needs_l23` / `@needs_pangaea` / `@needs_data`; run only where the data
tree is mounted:

- `prep.prep_one('L23', 0)` loads via `ocpy.hydrolight.loisel23`, attaches PACE
  noise on the native grid, packs full spectral truth.
- `prep.prep_one('PANGAEA', <id>)` extracts `Rrs` + `a_dg`/`a_ph`/`bb_p` truth.
- A small **real** `run_sweep` (both `expb_pow` and `giop`, χ², a few L23 spectra)
  → tables + provenance + a metrics pass; asserts schema, coverage accounting, and
  that the leaderboard folds.
- One short **MCMC** fit on a single spectrum (tiny `nsteps`) → chains persisted,
  corner data loads — guards the `inference`/chains path without a long run.

### Test data & speed

- **No large fixtures in the repo.** Tier-1 fixtures are generated in-process
  (a forward-modeled 5-band spectrum, a 3-row toy results table). Tier-2 uses the
  real `$OS_COLOR` tree via ocpy.
- MCMC in tests always uses a **tiny `nsteps`** (correctness, not convergence);
  full sweeps are never run under pytest.

### CI

Per the design decision that **reports are generated on demand, not by CI**, CI is
deliberately light:

- **What CI runs:** Tier-1 only — `pytest` in `ocean14` on push/PR. Data-dependent
  tests skip (no `$OS_COLOR` on the runner), so the suite is green and fast.
- **What CI does *not* do:** run sweeps, build reports, or publish the readthedocs
  site. Reports/leaderboard are produced on demand by a `runs/.../build_vN.py`
  (Reporting §); readthedocs builds the **committed** `.rst` independently.
- **Environment & dependencies:** the workflow recreates `ocean14` (or installs
  `requirements.txt`) and installs the two siblings from the **tip of their `main`
  branches** — `pip install git+https://github.com/ocean-colour/ocpy@main` and
  `…/bing@main` — then runs `pytest -q`. This keeps the install simple; the
  trade-off is that a green IOPtics build depends on upstream `main` staying
  importable, which JXP maintains (a PyPI release of ocpy/bing is on the TODO, at
  which point these become version pins in `requirements.txt`).
- **Advisory, not gating:** CI reports pass/fail from `pytest -q` only — **no
  coverage floor and no fail-on-warning** at this stage (the package is young and
  the data-dependent tests skip on CI anyway). A coverage gate can be added later.
- A lightweight **import/smoke** check (`import ioptics`, registry seeded) guards
  against breakage in the BING/ocpy dependency surface.

---

## Staged implementation plan

*How to build the package described above. The order follows the dependency DAG
of the Architecture Overview and is organized as **vertical slices**: rather than
finishing each module in isolation, we get the in-tandem `expb_pow`+`giop`
comparison running end-to-end as early as possible (design: develop the two in
tandem to exercise the comparison tooling), then broaden. Each stage has a single
**exit criterion** and ships with its tests (Testing & CI §).*

### Stage 0 — Scaffolding & contracts

- **Build:** the `ioptics/` skeleton (all module files as stubs), the two
  load-bearing dataclasses in `records.py` (`PreparedRecord`, `RetrievalResult`,
  `ComponentFit`), `config.py` (YAML ⇄ objects, `sweep_id`/validation), and
  `tests/conftest.py` with the skip guards + the CI workflow.
- **Exit:** `import ioptics` works; a sample sweep YAML round-trips to objects;
  Tier-1 tests for `records`/`config` pass in `ocean14`; CI is green (all
  data-tests skipped).
- **Touches:** `records`, `config`, `tests`. **Design:** Package layout.

### Stage 1 — Data in (L23 first)

- **Build:** `datasets` (the registry + the **L23 adapter**), `noise.attach_noise`
  (PACE on native grid; `pct`/`insitu`), and `prep.prep_one`/`prep_dataset` →
  `PreparedRecord` with pre-aligned truth, `init` (Chl/Y), perturbed Rrs + seed.
- **Exit:** `prep.prep_dataset('L23', range(50))` returns valid records (Tier-2
  `@needs_l23`); Tier-1 synthetic-record tests pass.
- **Touches:** `datasets`, `noise`, `prep`. **Design:** Data preparation.

### Stage 2 — Engine wrap: the in-tandem vertical slice ★

- **Build:** `algorithms.spec` + `algorithms.registry` (seed **both** `expb_pow`
  and `giop`), `run.run_algorithm` (**χ² path**), `evaluate.from_chisq`
  (covariance-sampled bands + `stats`), and `io` + `provenance` (write one
  spectrum's results + `provenance.yaml`).
- **Exit:** one L23 spectrum fit by **both** algorithms via least-squares →
  two `RetrievalResult`s → rows in `results_{spectral,scalar}.parquet` +
  provenance; the retrieval recovers planted IOPs within tolerance on the
  synthetic micro-test. *This is the first real two-way comparison — the whole
  point of the in-tandem decision.*
- **Touches:** `algorithms`, `run`, `evaluate`, `io`, `provenance`.
  **Design:** Algorithm registry, Retrieval & run.

### Stage 3 — Sweep + MCMC

- **Build:** `run.run_batch`/`run_sweep` (χ² over all records + MCMC on
  `mcmc_subset`), the **MCMC path** (`inference.fit_one` → `evaluate.from_chains`),
  and chain persistence to `runs/<sweep_id>/chains/`.
- **Exit:** a full **L23 × {expb_pow, giop}** sweep driven by a
  `runs/.../build_v1.py` (stage flag 1) writes the complete sweep directory; the
  MCMC subset produces saved chains; tables validate.
- **Touches:** `run`, `evaluate`, `io`. **Design:** Retrieval & run.

### Stage 4 — Metrics & diagnostics

- **Build:** `metrics.compute` (§1 accuracy, §2 Rrs closure, §3 ΔBIC, §4 coverage,
  §5 wins; partial-retrieval intersection rule; ±3 nm ref bands; Chl strata) and
  `diagnostics` (Taylor/Target/scatter/ratio-hist/residual/corner/ΔBIC-CDF arrays).
- **Exit:** `metrics.compute(sweep_id)` emits `metrics_{spectral,scalar,pairwise}`
  for the Stage-3 sweep; primitives match hand-computed values on toy `(M,O)`;
  `expb_pow` vs `giop` ΔBIC and wins are populated.
- **Touches:** `metrics`, `diagnostics`. **Design:** Metrics & diagnostics.

### Stage 5 — Reporting

- **Build:** `plotting` primitives, `report.figures`/`tables`, `report.leaderboard`
  (cross-sweep), `report.bokeh` (standalone), `report.rst`/`standard.build`.
- **Exit:** `standard.build(sweep_id, kind='cross_algorithm')` +
  `leaderboard.update()` (stage flag 3) produce a provenance-stamped `.rst` page,
  the standard figures/tables, a standalone Bokeh figure, and a leaderboard entry
  ranking the two algorithms; the page renders in the Sphinx build.
- **Touches:** `plotting`, `report`. **Design:** Reporting.

### Stage 6 — Broaden: datasets & algorithms

- **Build:** the **PANGAEA** and **GLORIA** adapters (with the `a_dg`/`a_cdom440`
  truth mapping + caveat flag); add **`gsm`** to the registry (one line); enable
  **L23 X=4** (Raman + Chl-fluorescence RT toggles).
- **Exit:** sweeps run on all three datasets and ≥3 algorithms; the leaderboard
  accumulates across them; GLORIA scalar comparison surfaces the CDOM-vs-`a_dg`
  caveat.
- **Touches:** `datasets`, `algorithms`, `run` (RT toggles). **Design:** Data,
  Algorithm registry, Reporting (leaderboard).

### Dependency / sequencing summary

```
Stage 0 (records, config, CI)
   └─▶ Stage 1 (datasets·L23, noise, prep)
          └─▶ Stage 2 ★ (algorithms+run·chisq+evaluate+io+provenance)  ← first expb_pow vs giop
                 └─▶ Stage 3 (sweep + MCMC + chains)
                        └─▶ Stage 4 (metrics + diagnostics)
                               └─▶ Stage 5 (plotting + report + leaderboard + bokeh)
                                      └─▶ Stage 6 (PANGAEA·GLORIA, gsm, L23 X=4)
```

Every stage is shippable and tested before the next begins; Stages 0–5 deliver the
complete `expb_pow`/`giop` × L23 story (the design's first deliverable), and
Stage 6 turns the cranks the architecture was built to turn.

Each stage has a dedicated code-generation prompt doc,
`claude_prompts/coding_prompts_stage<NN>.md`, with **one prompt per module** in
that stage (run them the same way: "Execute the Nth task").

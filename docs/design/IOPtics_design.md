# IOPtics Design Document

**Version:** 0.8
**Date:** 2026-06-20
**Authors:** JXP and Claude

---

## Preamble

This document describes the design and requirements for **IOPtics**, a Python
package for testing and evaluating a wide range of IOP (inherent optical
property) algorithms. Its purpose is to provide the ocean-optics community with
a common, reproducible framework for running these algorithms on remote-sensing
reflectance (Rrs) spectra, quantifying the retrieved IOPs and their
uncertainties, and comparing the results against ground truth using uniform
metrics and diagnostics.

### What this document is for

- It serves as the **guiding design reference** for the development of IOPtics.
- It captures the package's **goals, scope, requirements, and architecture** at
  a level above specific code. (Code-level recommendations will be maintained in
  a separate document.)
- It is a **living document**: it will evolve as the design matures, with the
  version number and date updated accordingly.

### Scope and goals

IOPtics is expected to, at minimum:

- Run a wide range of IOP algorithms on Rrs spectra.
- Calculate IOP values and their uncertainties:
  - absorption spectra (`a`), separated by water, phytoplankton, CDOM/detritus, etc.
  - backscattering spectra (`bb`), separated by water and particulate components.
  - primarily leveraging the **BING** package for the retrieval machinery.
- Compare algorithm results against ground truth:
  - using simulated spectra (e.g., the Loisel et al. 2023 Hydrolight dataset),
  - using in-situ measurements (e.g., PANAGEA, GLORIA).
- Develop **metrics and diagnostics** that can be applied uniformly to all
  algorithms.
- Share results (figures, reports, etc.) with the community via GitHub and
  readthedocs.io.
- Generate reports and publications on the main findings.

### Supporting material

The scientific and architectural background informing this design is
distilled in [`docs/context.md`](../context.md) (v0.1), which reduces the
foundational sources — the Oceanic Optics Book (Mobley 2022), Werdell et al.
(2013, 2018), and the BING repository — into a working reference.

### Conventions

- This document avoids specific code recommendations; those will live in a
  companion implementation document.
- The authors welcome and will incorporate new design ideas as the work
  progresses.

---

## Data

IOPtics is evaluated against a small set of well-characterized datasets that
together span **synthetic** spectra (known ground-truth IOPs) and **real
in-situ** spectra (measured IOPs / water-quality products). Synthetic data let us
benchmark per-wavelength and per-component retrieval accuracy against exact truth;
in-situ data test the algorithms under real-world optical complexity and
measurement uncertainty.

### Design decisions governing all datasets

- **Native wavelength grids are preserved per dataset.** We do not resample to a
  common grid. Each algorithm is run on, and scored against, the wavelengths a
  given dataset provides. (This keeps the band-vs.-unknown well-posedness honest
  for each source and avoids interpolation artifacts.)
- **A single canonical IOP-component scheme is deferred** (see Open Questions).
  Until decided, each dataset's truth is compared to algorithm output at the
  component granularity that dataset actually supports (e.g. combined `a_dg` for
  PANAGEA, scalar products for GLORIA, full breakdown for L23).
- Data loading is provided by the sibling **`ocpy`** package; IOPtics depends on
  it rather than re-implementing readers.

### Dataset summary

| Dataset | Source | Type | Rrs | Ground-truth available | Role in IOPtics |
|---|---|---|---|---|---|
| **L23** | Loisel et al. 2023 (Hydrolight) | Synthetic | yes | **Full** spectral `a`, `bb`, `aph`, … (exact truth) | **Primary** validation / benchmarking |
| **PANAGEA** | Valente et al. 2022 (V3) | In-situ | yes (native + sat-bands) | `aph`, `a_dg` (CDOM+detrital), `bbp`, `kd`, `chla`, `tss` | Real-world spectral IOP validation |
| **GLORIA** | Lehmann et al. 2023 | In-situ | yes (hyperspectral, 350–900 nm @1 nm) | Scalar only: `aCDOM(440)`, `Chla`, `TSS`, Secchi | Scalar/band-product validation |

### L23 — Loisel et al. 2023 Hydrolight (primary benchmark)

Synthetic Hydrolight radiative-transfer output with **known true IOPs**, making
it our primary tool for quantifying retrieval accuracy (per-wavelength and
per-component error metrics) against exact truth.

- **Location / loader:** `$OS_COLOR/Loisel2023`, via
  `ocpy.hydrolight.loisel23` (`load_ds(X, Y)`).
- **Scenario standardization:** first-pass development uses **`X=1`** (no
  inelastic processes — pure elastic); subsequent evaluation adds **`X=4`**
  (Raman scattering + chlorophyll-a fluorescence). `X=2` (Raman only) is **not**
  used. We use a single solar-zenith geometry, **`Y=00`** (0°).
- **Provides:** `Rrs`, full `a`/`bb` and their components (`aph`, …); Chl is
  derivable from `aph(440)`.

### PANAGEA — Valente et al. 2022 V3 (in-situ spectral IOPs)

Real co-located Rrs and in-situ IOP measurements; itself a curated compilation of
many archives (MOBY, BOUSSOLE, AERONET-OC, SeaBASS, NOMAD, Tara, …), so it
subsumes most other public in-situ sources.

- **Location / loader:** `$OS_COLOR/PANAGEA/V3`, via `ocpy.insitu.panagea`
  (ID-indexed tables; native-wavelength and satellite-band variants).
- **Provides:** `Rrs`, `aph`, `acdom` (the **combined CDOM + detrital** term,
  ≈ `a_dg`), `bbp` (single particulate term), `kd`, plus scalar `chla`, `tss`.
- **Use:** algorithm output is matched to the **combined `a_dg`** term (not
  separate CDOM vs. NAP), at the **native PANAGEA wavelengths**.

### GLORIA — Lehmann et al. 2023 (scalar/band-product validation)

A globally representative **hyperspectral** in-situ Rrs dataset (7,572 spectra,
350–900 nm at 1 nm, 450 water bodies, coastal/inland-heavy) with co-located
**scalar** water-quality measurements only — no spectral IOPs.

- **Loader:** `ocpy.insitu.gloria`. **The data are not yet downloaded locally**
  (the package ships a README pointing to PANGAEA 948492); they must be fetched
  before use.
- **Provides:** hyperspectral `Rrs`; scalar `aCDOM(440)`, `Chla`, `TSS`, Secchi.
- **Use:** **scalar / band-product validation only** (e.g. retrieved
  `a_cdom(440)`). We are **not** using GLORIA for Rrs-space closure or for
  out-of-distribution / representativeness testing at this stage.
- **Caveat (flagged):** GLORIA's truth is `aCDOM(440)` — **CDOM only** — whereas
  algorithms typically retrieve the **combined `a_dg`** (CDOM + detritus). When
  comparing retrieved `a_dg(440)` against GLORIA's `aCDOM(440)`, this
  CDOM-vs-(CDOM+detritus) mismatch must be explicitly flagged in reports; the two
  are not strictly the same quantity.

### Out of scope for now

- **PACE field validation data** — deferred; there is no single consolidated
  "released" PACE validation product to point at yet (PACE field data are
  distributed piecemeal via NASA SeaBASS/OB.DAAC). Revisit once a concrete
  source/DOI is identified.
- **IOCCG synthetic dataset** — deferred; the standard sets are quite dated, so
  L23 serves as our synthetic benchmark for now.
- **NOMAD / raw SeaBASS archive** — not treated as separate datasets, since
  PANAGEA already incorporates them.
- **Tara Oceans `ap`/`cp`** (particle absorption/attenuation, not Rrs-paired) —
  available locally but deferred as an IOP-shape reference rather than a
  validation set.

---

## Analysis

IOPtics applies a **single, algorithm-agnostic analysis pipeline** to every
algorithm so that results are directly comparable. The semi-analytical retrieval
engine is the **BING** package (Gordon-quadratic IOP inversion with both
least-squares and Bayesian fitting); IOPtics adds the uniform layer that drives,
scores, and reports any algorithm identically. This section states *what* the
analysis must do; implementation specifics (modules, functions, code) are left to
a separate implementation document.

### Pipeline overview

Every algorithm flows through the same stages:

1. **Data preparation** — load and condition each dataset's spectra.
2. **IOP retrieval** — derive `a(λ)` and `bb(λ)` and their components.
3. **Uncertainty quantification** — attach uncertainties to every retrieval.
4. **Metrics & diagnostics** — score retrievals uniformly.
5. **Figures, tables & reports** — produce standardized, reproducible outputs.

Cutting across all stages, IOPtics records **provenance** — the full algorithm
configuration behind every result — so the pipeline is reproducible end to end.

### Data preparation

IOPtics needs a defined **process to load and prepare the data for analysis**.
For each dataset (L23, PANAGEA, GLORIA) it must read the `Rrs` spectra on that
dataset's **native wavelength grid** (per the Data decisions), attach an `Rrs`
uncertainty / noise estimate, and assemble the inputs the retrieval requires. The
prepared form is common across datasets and algorithms, so the same downstream
analysis applies uniformly. (Where this preparation lives and how it is coded are
implementation concerns, addressed separately.)

For the synthetic **L23** dataset (effectively noiseless truth), the first-pass
analyses assume a **PACE sensor noise model** (the `ocpy.satellites.pace` model)
for the `Rrs` uncertainty, so that retrieval uncertainties and `Rrs`-closure
thresholds are realistic rather than degenerate.

### IOP retrieval

The retrieval derives absorption `a(λ)` and backscattering `bb(λ)`, separated
into components (water, phytoplankton, combined CDOM+detrital `a_dg`, and
particulate backscatter), via BING's semi-analytical Gordon framework with
optional inelastic terms (Raman, chlorophyll-a fluorescence).

- **An algorithm is a configuration** — a choice of absorption and backscattering
  spectral shapes, priors, and forward-model/RT options. IOPtics represents each
  algorithm as a uniform specification so that "run a wide range of IOP
  algorithms" reduces to running the same pipeline over a set of specifications.
- **Algorithms are built out one at a time.** Rather than enabling all candidate
  algorithms at once, IOPtics adds and validates them incrementally; the design
  supports a growing registry of algorithms over time. The **first algorithm** is
  `expb_pow` (exponential `a_dg` + Bricaud `a_ph` + power-law `bb_p`), BING's
  best-exercised configuration; additional algorithms (e.g. GIOP, GSM) are added
  thereafter.
- **Two fitting modes** are supported: least-squares and Bayesian (MCMC).
  **First-pass analyses use least-squares** across the full sweep (fast), with
  **MCMC reserved for a subset** where full posterior distributions are warranted.

### Uncertainty quantification

Uncertainty is a **first-class output of every retrieval**, not an afterthought.
It combines input `Rrs` uncertainty (a noise model) with the inversion: the
least-squares path propagates parameter covariance to `a(λ)`/`bb(λ)`, while the
MCMC path yields full posterior credible intervals. Because there is no community
consensus on a single uncertainty definition, IOPtics **records which method
produced each budget** and holds the method fixed within any given comparison.

### Provenance & reproducibility

Every result **must record the full details of the model/algorithm used**, so that
any retrieval can be traced and reproduced exactly. At minimum this provenance
record captures the algorithm configuration — the absorption and backscattering
model choices, the forward-model / RT options (Gordon variant, Raman /
chlorophyll-fluorescence toggles), the fitting method, and the noise model — and,
**for any Bayesian (MCMC) inference, the priors used**. The provenance record is
written in a **human-readable format (YAML/JSON)** and stored **alongside the
results table**, so results are self-describing, shareable on GitHub, and
reproducible.

### Metrics & diagnostics

Metrics are computed **uniformly per algorithm and dataset**, and stratified where
meaningful (e.g. by trophic level). They include: comparison against truth (L23,
and PANAGEA where in-situ IOPs exist; per-wavelength and per-component error),
scalar/band-product comparison (GLORIA — with the **flagged** CDOM-vs-`a_dg`
caveat), internal `Rrs` closure, and physical-range quality-control flags to mark
non-solutions. Diagnostics include Taylor and Target diagrams, residual spectra,
and posterior plots. *Full metric definitions are deferred to the Metrics
section.*

### Figures, tables & reports

Standardized figures and tables are generated from a common results table so that
**every algorithm produces the same outputs**, assembled into reproducible reports
(rendered to `.rst` for readthedocs.io and shared via GitHub), as detailed in the
Reporting section.

---

## Metrics

To compare IOP algorithms, IOPtics computes a common battery of metrics, applied
**as uniformly as the algorithms and datasets allow**. True uniformity is not
always achievable — some algorithms retrieve only a subset of the IOPs, datasets
differ in the truth they carry (full spectra for L23; combined `a_dg` for
PANAGEA; scalars for GLORIA), and information content varies with sensor and water
type. The plan below therefore defines the metrics and the rules for applying them
to partial cases. It is grounded in the practice of the BING paper (Prochaska &
Frouin 2025) and Erickson et al. (2023).

### Conventions

- **Log space.** IOPs and Chl are ~log-normally distributed, so accuracy metrics
  are computed on **log10-transformed** quantities (following Erickson 2023 /
  Seegers et al. 2018). Fit/closure statistics on `Rrs` are computed in linear
  space.
- **Spectral and scalar.** Metrics are reported **per wavelength** across each
  dataset's native grid *and* summarized at reference wavelengths — **440/443 nm**
  for absorption, and **555 nm plus a redder band (670 nm)** for backscattering.
  This deliberately extends BING/Erickson, which report accuracy mainly at a
  single wavelength.
- **Per component.** Computed for total `a(λ)` and `bb(λ)` and for each retrieved
  component (`a_ph`, `a_dg`, `a_nw`, `bb_p`, `bb_nw`), matched to the truth the
  dataset supports.
- **Stratification.** Results are stratified by trophic level / Chl bins, water
  type (Case I/II), sensor/spectral sampling, and wavelength.

### 1. Retrieval accuracy vs. truth (IOP space)

The primary comparison, applicable where truth IOPs exist (L23; PANAGEA for the
components it carries). The set below is the **initial standard battery and is
expected to grow** as the comparison matures. Adopt the multiplicative, log-space
definitions of Erickson 2023 (their Eqs. 13–14, after Seegers et al. 2018), with
`M` = modeled, `O` = observed/true, `n` = number of points:

- **MAE** (mean absolute error, multiplicative): `MAE = exp( Σ|log M − log O| / n ) − 1`
- **bias** (signed, multiplicative): `bias = exp( Σ(log M − log O) / n ) − 1`
- **RMS / unbiased RMS** of the log residual (as in BING's accuracy reporting).
- **Median ratio** `= median(M/O)` and **ratio histograms** with accuracy buckets
  (e.g. `<1/3, 1/2, 3/4, 1, 4/3, 2, 3, >3`; Erickson Fig. 4) to show
  over/under-estimation.
- **r² and Type-II regression slope/intercept** (an addition over both source
  papers, which omit them, to characterize systematic tilt).

### 2. Internal closure & fit quality (Rrs space)

Applicable to **every** dataset (all carry `Rrs`), including GLORIA:

- **Cost function** — the inversion objective: `χ²_rel = Σ (Rrs_calc − Rrs_obs)² / σ_Rrs²`
  (Erickson Eq. 9), and its Bayesian form with a prior penalty term `χ²_Bayes`
  (Erickson Eq. 10; BING Eq. 4 likelihood).
- **Reduced χ²ᵥ** as the headline single-fit diagnostic: ≈1 good; **<1 signals
  overfitting**; >1 underfitting (BING).
- **Rrs MAE / bias** (same log-free closure form) with a **dual-sided acceptance
  window** (Erickson): a good fit reproduces `Rrs` to ≈ the measurement
  uncertainty (~5%), and a MAE *much below* the noise floor is also flagged as
  **fitting noise**. A QC failure bound (Erickson uses **>25% Rrs MAE**) marks
  non-solutions.

### 3. Model selection / complexity

To judge whether an algorithm's parameter count is justified by the information
content (central to the BING analysis):

- **AIC** `= 2k − 2 ln ℒ` (BING Eq. 5) and **BIC** `= k ln n − 2 ln ℒ` (Eq. 6),
  with `k` = free parameters, `n` = number of `Rrs` bands.
- **ΔBIC** between two models (Eq. 7): **ΔBIC < 0 favors the more complex model**;
  reported as a **CDF over the dataset** (fraction of spectra favoring each model)
  and stratified by S/N and sensor.
- A **degrees-of-freedom** framing (retrievable parameters vs. independent bands)
  for interpreting well-posedness.

### 4. Uncertainty assessment

Per the Analysis section, uncertainty is a first-class output; here it is *scored*:

- **Credible / confidence intervals** (e.g. 68% and 99%) from the MCMC posterior,
  or covariance-propagated intervals (`J⁻¹ S_R J⁻ᵀ`) for least-squares.
- **Detection significance** — whether a component is detected at Nσ (e.g. the
  credible interval excludes ~zero); non-detections reported as **upper limits**
  (BING's treatment of `a_ph`).
- **Parameter degeneracy** — pairwise posteriors (corner plots) to expose
  correlations (e.g. CDOM–phytoplankton) and **prior-dominated** parameters.
- **Coverage / calibration (new in IOPtics).** Both source papers validate
  uncertainties only informally. IOPtics will add a **formal coverage test** — the
  fraction of retrievals whose X% interval contains truth should be ≈X%, evaluated
  at the **68% and 95%** levels — so that uncertainty quality is itself a
  comparable metric.

### 5. Cross-algorithm comparison

- **"Wins"** — the fraction of head-to-head contests in which an algorithm gives
  the more accurate estimate per variable (Erickson / Seegers).
- **Per-variable ranking** by `|bias|`, MAE, and wins (Erickson Table 2 style).

### 6. Diagnostic figures

Standard set generated uniformly: retrieved-vs-true **scatter (log–log, with
1:1 / 3:1 / 0.3:1 guide lines)**, **ratio histograms**, **per-parameter posterior
/ probability-distribution plots**, **residual / closure `Rrs` spectra** (χ²ᵥ
annotated), **corner plots**, and **ΔBIC CDFs**. In addition, IOPtics produces
two community-standard summary diagrams for ranking many algorithms at once:

- **Taylor diagram** (Taylor 2001) — a polar plot combining correlation with
  truth, normalized standard deviation, and centered RMS difference.
- **Target diagram** (Jolliff et al. 2009) — bias vs. signed unbiased RMSD, so a
  point's distance from the origin is the total RMSD; cleanly separates systematic
  from random error.

These extend BING/Erickson (which use neither) and complement the scalar metrics.

### Handling non-uniformity

Where an algorithm retrieves only a subset of IOPs, metrics are computed on the
**common retrievable subset** and the **coverage** (which components/wavelengths
were scored) is recorded alongside the result. Comparisons are mapped onto the
truth the dataset supports — e.g. retrieved `a_dg` vs. PANAGEA's combined `a_dg`,
and retrieved `a_dg(440)` vs. GLORIA's `aCDOM(440)` with the flagged
CDOM-vs-(CDOM+detritus) caveat.

*Full per-figure styling and table layouts are deferred to the Reporting section.*

---

## Open Questions & Deferred Decisions

A running list of decisions intentionally postponed, tracked in one place so they
are not lost. Items are resolved (and removed or struck) as the design matures.

| # | Topic | Status | Notes |
|---|---|---|---|
| 1 | **Canonical IOP-component scheme** | Deferred | Whether all algorithms report into one fixed component set (e.g. `a_w, a_ph, a_dg, bb_w, bb_p`). Until decided, each dataset's truth is compared at the granularity it supports. |
| 2 | **PACE field validation dataset** | Deferred | No single consolidated "released" PACE validation product to point at yet; revisit once a concrete source/DOI is identified. (Distinct from the PACE *noise model*, which is adopted.) |
| 3 | **IOCCG synthetic dataset** | Deferred | Standard sets are dated; L23 serves as the synthetic benchmark for now. |
| 4 | **Metrics section** | Drafted (v0.8) | Initial battery from BING (Prochaska & Frouin 2025) and Erickson et al. (2023); log-space MAE/bias adopted, coverage test at 68%/95%, Taylor + Target diagrams added. Battery expected to grow. |
| 5 | **Validation section** | Pending | Validation methods to be drafted under a dedicated prompt. |
| 6 | **GLORIA data acquisition** | Pending | Data not yet downloaded locally (ocpy ships only a README → PANGAEA 948492); JXP to source. |

---

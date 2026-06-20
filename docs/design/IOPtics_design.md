# IOPtics Design Document

**Version:** 0.13
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
  - using in-situ measurements (e.g., PANGAEA, GLORIA).
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
  PANGAEA, scalar products for GLORIA, full breakdown for L23).
- Data loading is provided by the sibling **`ocpy`** package; IOPtics depends on
  it rather than re-implementing readers.

### Dataset summary

| Dataset | Source | Type | Rrs | Ground-truth available | Role in IOPtics |
|---|---|---|---|---|---|
| **L23** | Loisel et al. 2023 (Hydrolight) | Synthetic | yes | **Full** spectral `a`, `bb`, `a_ph`, … (exact truth) | **Primary** validation / benchmarking |
| **PANGAEA** | Valente et al. 2022 (V3) | In-situ | yes (native + sat-bands) | `a_ph`, `a_dg` (CDOM+detrital), `bb_p`, `kd`, `chla`, `tss` | Real-world spectral IOP validation |
| **GLORIA** | Lehmann et al. 2023 | In-situ | yes (hyperspectral, 350–900 nm @1 nm) | Scalar only: `a_cdom(440)`, `Chla`, `TSS`, Secchi | Scalar/band-product validation |

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
- **Provides:** `Rrs`, full `a`/`bb` and their components (`a_ph`, …); Chl is
  derivable from `a_ph(440)`.

### PANGAEA — Valente et al. 2022 V3 (in-situ spectral IOPs)

Real co-located Rrs and in-situ IOP measurements; itself a curated compilation of
many archives (MOBY, BOUSSOLE, AERONET-OC, SeaBASS, NOMAD, Tara, …), so it
subsumes most other public in-situ sources.

- **Location / loader:** `$OS_COLOR/PANGAEA/V3`, via `ocpy.insitu.pangaea`
  (ID-indexed tables; native-wavelength and satellite-band variants).
- **Provides:** `Rrs`, `a_ph`, `a_dg` (the **combined CDOM + detrital** term;
  the ocpy column is named `acdom`), `bb_p` (single particulate term), `kd`, plus
  scalar `chla`, `tss`.
- **Use:** algorithm output is matched to the **combined `a_dg`** term (not
  separate CDOM vs. NAP), at the **native PANGAEA wavelengths**.

### GLORIA — Lehmann et al. 2023 (scalar/band-product validation)

A globally representative **hyperspectral** in-situ Rrs dataset (7,572 spectra,
350–900 nm at 1 nm, 450 water bodies, coastal/inland-heavy) with co-located
**scalar** water-quality measurements only — no spectral IOPs.

- **Loader:** `ocpy.insitu.gloria`. **The data are not yet downloaded locally**
  (the package ships a README pointing to PANGAEA 948492); they must be fetched
  before use.
- **Provides:** hyperspectral `Rrs`; scalar `a_cdom(440)`, `Chla`, `TSS`, Secchi.
- **Use:** **scalar / band-product validation only** (e.g. retrieved
  `a_cdom(440)`). We are **not** using GLORIA for Rrs-space closure or for
  out-of-distribution / representativeness testing at this stage.
- **Caveat (flagged):** GLORIA's truth is `a_cdom(440)` — **CDOM only** — whereas
  algorithms typically retrieve the **combined `a_dg`** (CDOM + detritus). When
  comparing retrieved `a_dg(440)` against GLORIA's `a_cdom(440)`, this
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
  PANGAEA already incorporates them.
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
For each dataset (L23, PANGAEA, GLORIA) it must read the `Rrs` spectra on that
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
and PANGAEA where in-situ IOPs exist; per-wavelength and per-component error),
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
PANGAEA; scalars for GLORIA), and information content varies with sensor and water
type. The plan below therefore defines the metrics and the rules for applying them
to partial cases. It is grounded in the practice of the BING paper (Prochaska &
Frouin 2025) and Erickson et al. (2023).

### Conventions

- **Log space.** IOPs and Chl are ~log-normally distributed, so the accuracy
  metrics (MAE and bias — including the `Rrs`-closure MAE/bias) use the
  **multiplicative, log10** form (following Erickson 2023 / Seegers et al. 2018).
  The χ² cost functions are evaluated in linear `Rrs` space.
- **Spectral and scalar.** Metrics are reported **per wavelength** across each
  dataset's native grid *and* summarized at reference wavelengths — **440/443 nm**
  for absorption, and **555 nm plus a redder band (670 nm)** for backscattering.
  This deliberately extends BING/Erickson, which report accuracy mainly at a
  single wavelength.
- **Per component.** Computed for total `a(λ)` and `bb(λ)` and for the components
  `a_ph`, `a_dg`, and `bb_p`, matched to the truth the dataset supports.
- **Stratification.** Results are stratified by trophic level / Chl bins, water
  type (Case I/II), sensor/spectral sampling, and wavelength.

### 1. Retrieval accuracy vs. truth (IOP space)

The primary comparison, applicable where truth IOPs exist (L23; PANGAEA for the
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
- **Rrs MAE / bias** (the multiplicative log-space form of §1, applied to `Rrs`)
  with a **dual-sided acceptance window** (Erickson): a good fit reproduces `Rrs`
  to ≈ the measurement
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

- **Credible / confidence intervals** (e.g. 68% and 95%, matching the coverage
  levels below) from the MCMC posterior, or covariance-propagated intervals
  (`J⁻¹ S_R J⁻ᵀ`) for least-squares.
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
truth the dataset supports — e.g. retrieved `a_dg` vs. PANGAEA's combined `a_dg`,
and retrieved `a_dg(440)` vs. GLORIA's `a_cdom(440)` with the flagged
CDOM-vs-(CDOM+detritus) caveat.

*Full per-figure styling and table layouts are deferred to the Reporting section.*

---

## Reporting

IOPtics turns each analysis sweep into **shareable, reproducible reports** for the
ocean-optics community. Reporting consumes the standardized results table and its
provenance record (see Analysis) so that every output is regenerable from a single
sweep and traceable to the exact configuration that produced it. The plan reflects
the reporting practice of BING (Prochaska & Frouin 2025) and Erickson et al.
(2023), generalized to many algorithms and datasets.

### Outputs / artifacts

Each sweep produces a consistent set of artifacts:

- **Machine-readable results** — the results table (CSV / parquet) keyed by
  `(dataset, obs_id, algorithm)`, plus the **provenance record** (YAML/JSON)
  stored alongside it.
- **Figures** — the standard diagnostic set defined in the Metrics section:
  retrieved-vs-true scatter (log–log), ratio histograms, per-parameter posterior /
  probability-distribution plots, residual / closure `Rrs` spectra (χ²ᵥ
  annotated), retrieved IOP spectra with uncertainty bands, corner plots, ΔBIC
  CDFs, and **Taylor** and **Target** diagrams. Spatial maps are produced where a
  scene/gridded product applies (cf. Erickson Fig. 5).
- **Tables** — per-variable accuracy summaries (`bias`, MAE, RMS, "wins"),
  per-dataset and per-stratum (trophic level / water type), and QC summaries
  (fraction flagged as non-solutions).

### Report types

- **Per-algorithm report** — one algorithm across datasets and strata; the
  "scorecard" for a single algorithm.
- **Cross-algorithm comparison report** — the headline IOPtics deliverable:
  many algorithms ranked on common metrics and the summary diagrams, with the
  caveats from "handling non-uniformity" surfaced.
- **Per-dataset report** — all algorithms on one dataset, for dataset-focused
  questions.

A **standard report** template covers these; reports are generated **on demand**
(not auto-built by CI on every commit).

### Leaderboard

The cross-algorithm comparison is anchored by a **persistent leaderboard** that
ranks algorithms by the headline metrics across datasets and strata. Because
algorithms are added to the registry one at a time, the leaderboard **accumulates
and updates** as each new algorithm is evaluated, giving the community a single,
evolving view of relative performance.

### Interactive figures

In addition to static publication figures, IOPtics provides **interactive Bokeh
figures** that let a user **select an algorithm (and dataset/stratum) and inspect
its results** — e.g. browse retrieved-vs-true scatter, spectra with uncertainty
bands, and the leaderboard interactively. These are delivered as
**standalone/static BokehJS** (self-contained HTML with JS callbacks — dropdown
select, hover, pan/zoom), so they embed directly in the readthedocs site with no
running Bokeh server.

### Format & delivery

- Reports are authored as **reStructuredText (`.rst`)** and rendered on a
  **single, accumulating readthedocs.io site** that hosts all reports, with the
  source and artifacts shared via **GitHub**.
- Figures are **publication-ready** (the BING/Erickson figure styles), so report
  figures can flow directly into manuscripts.
- **Reproducibility:** every report is generated programmatically from the results
  table + provenance, and is stamped with the versions it depends on (design-doc
  version, algorithm-registry entry, dataset version, and code commit), so a
  reader can reconstruct exactly what was run.

### Publications

The reports are the substrate for manuscripts on the main findings: the
cross-algorithm comparison, its figures, and its tables are assembled into
community publications, with the same provenance ensuring the published results
are reproducible.

*Per-figure styling, the `.rst` site layout, and build automation are
implementation details, addressed separately.*

---

## Open Questions & Deferred Decisions

A running list of decisions intentionally postponed, tracked in one place so they
are not lost. Items are resolved (and removed or struck) as the design matures.

| # | Topic | Status | Notes |
|---|---|---|---|
| 1 | **Canonical IOP-component scheme** | Deferred | Whether all algorithms report into one fixed component set (e.g. `a_w, a_ph, a_dg, bb_w, bb_p`). Until decided, each dataset's truth is compared at the granularity it supports. |
| 2 | **PACE field validation dataset** | Deferred | No single consolidated "released" PACE validation product to point at yet; revisit once a concrete source/DOI is identified. (Distinct from the PACE *noise model*, which is adopted.) |
| 3 | **IOCCG synthetic dataset** | Deferred | Standard sets are dated; L23 serves as the synthetic benchmark for now. |
| 4 | **Metrics section** | Drafted | Initial battery from BING (Prochaska & Frouin 2025) and Erickson et al. (2023); log-space MAE/bias adopted, coverage test at 68%/95%, Taylor + Target diagrams added. Battery expected to grow. |
| 5 | **GLORIA data acquisition** | Pending | Data not yet downloaded locally (ocpy ships only a README → PANGAEA 948492); JXP to source. |

---

## References

Works cited in this design document. A fuller scientific reference list is in
[`docs/context.md`](../context.md).

- Erickson, Z. K., McKinna, L., Werdell, P. J., Cetinić, I. (2023). "Bayesian
  approach to a generalized inherent optical property model." *Optics Express*
  31(14), 22790–22801. https://doi.org/10.1364/OE.486581
- Jolliff, J. K., et al. (2009). "Summary diagrams for coupled hydrodynamic-
  ecosystem model skill assessment." *J. Marine Systems* 76(1–2), 64–82.
  https://doi.org/10.1016/j.jmarsys.2008.05.014
- Lehmann, M. K., et al. (2023). "GLORIA – A globally representative hyperspectral
  in situ dataset for optical sensing of water quality." *Scientific Data* 10, 100.
  https://doi.org/10.1038/s41597-023-01973-y (PANGAEA 948492)
- Loisel, H., et al. (2023). Hydrolight synthetic IOP/Rrs dataset ("L23").
  https://doi.org/10.6076/D1630T
- Prochaska, J. X., Frouin, R. (2025). "On the challenges of retrieving
  phytoplankton properties from remote-sensing observations." *Biogeosciences*
  22, 4705–4728. (the **BING** paper)
- Seegers, B. N., et al. (2018). "Performance metrics for the assessment of
  satellite data products: an ocean color case study." *Optics Express* 26(6),
  7404–7422. https://doi.org/10.1364/OE.26.007404
- Taylor, K. E. (2001). "Summarizing multiple aspects of model performance in a
  single diagram." *J. Geophysical Research* 106(D7), 7183–7192.
  https://doi.org/10.1029/2000JD900719
- Valente, A., et al. (2022). "A compilation of global bio-optical in situ data for
  ocean-colour satellite applications – version three" ("PANGAEA" V3). *Earth
  System Science Data* 14, 5737–5770. https://doi.org/10.5194/essd-14-5737-2022
- Werdell, P. J., et al. (2013). GIOP. *Applied Optics* 52(10), 2019–2037.
- Werdell, P. J., et al. (2018). IOP retrieval review. *Progress in Oceanogra_phy*
  160, 186–212.
- Mobley, C. D. (ed.) (2022). *The Oceanic Optics Book*. IOCCG.

---

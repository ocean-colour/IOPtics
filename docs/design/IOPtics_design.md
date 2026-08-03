# IOPtics Design Document

**Version:** 0.16
**Date:** 2026-08-03
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

**The primary goal, sharpened (2026-08).** IOPtics exists so that **a member of the
ocean-colour community can compare the performance of different IOP models** — both
by reading the published comparison and by running IOPtics on a model of their own.
That reframes the deliverable: the site must answer *"which model should I use for
water like mine, and can I trust its uncertainties?"* rather than *"what did sweep
`X` do"*, and the package must make adding a competing model cheap enough that an
outsider will actually do it (the registry's one-call registration is the mechanism;
a documented on-ramp is the missing half). Every reporting decision in the Reporting
section below is downstream of this sentence.

### Supporting material

The scientific and architectural background informing this design is
distilled in [`docs/context.md`](../context.md) (v0.1), which reduces the
foundational sources — the Oceanic Optics Book (Mobley 2022), Werdell et al.
(2013, 2018), and the BING repository — into a working reference.

### Conventions

- This document avoids specific code recommendations; those will live in a
  companion implementation document (forthcoming).
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
  (ID-indexed tables; native-wavelength and satellite-band variants). *(On the
  current data tree the directory is spelled `PANAGEA`; resolution works regardless,
  so leave it alone until someone checks what ocpy keys on.)*
- **Scale, and the subset that can be scored (measured 2026-08):** the adapter
  enumerates **64 071** observations with usable `Rrs`, but only **3 247** of those
  ids appear in the IOP table — so ~95% carry no spectral truth. A PANGAEA sweep
  should be bounded to the truth-carrying subset (comparable in size to L23's 3 320),
  and any report must state that selection explicitly.
- **Provides:** `Rrs`, `a_ph`, `a_dg` (the **combined CDOM + detrital** term;
  the ocpy column is named `acdom`), `bb_p` (single particulate term), `kd`, plus
  scalar `chla`, `tss`.
- **Use:** algorithm output is matched to the **combined `a_dg`** term (not
  separate CDOM vs. NAP), at the **native PANGAEA wavelengths**.

### GLORIA — Lehmann et al. 2023 (scalar/band-product validation)

A globally representative **hyperspectral** in-situ Rrs dataset (7,572 spectra,
350–900 nm at 1 nm, 450 water bodies, coastal/inland-heavy) with co-located
**scalar** water-quality measurements only — no spectral IOPs.

- **Loader:** `ocpy.insitu.gloria`. **Data acquired 2026-07** into
  `$OS_COLOR/GLORIA` (PANGAEA 948492) and wired through the `GLORIA` adapter.
- **Provides:** hyperspectral `Rrs`; scalar `a_cdom(440)`, `Chla`, `TSS`, Secchi.
- **Use:** **scalar / band-product validation** (e.g. retrieved `a_cdom(440)`)
  — extended in practice to **Rrs-space closure**, which is where GLORIA turned out
  to be most informative: the fits fail in turbid water because the required
  backscattering in the red far exceeds what a power-law `b_bp` can produce, not
  because of CDOM/detritus absorption. See `reports/gloria_fits_report.md`.
- **Two data properties that shape any GLORIA result**, both learned the hard way:
  only ~29% of spectra quote an `Rrs` uncertainty at any band (70% quote none at
  all), so fit weights are largely **imputed** and must be tagged as such; and the
  quoted uncertainties are tight enough that χ²ᵥ is uninterpretable without an
  error floor. Statistics computed on the uncertainty-carrying subset are therefore
  drawn from a biased ~29% of the dataset unless said otherwise.
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
- **The first two algorithms are developed in tandem.** IOPtics begins with
  **`expb_pow` (ExpB_Pow)** — exponential `a_dg` + Bricaud `a_ph` + power-law
  `bb_p`, BING's best-exercised configuration — **and `giop` (GIOP)**, the
  community-standard generalized model, built out *together*. Developing two
  algorithms from the start exercises and validates the **comparison tooling**
  (metrics, diagnostics, leaderboard) on a real two-way comparison rather than a
  single retrieval. Further algorithms (e.g. GSM) are then added incrementally to
  the growing registry.
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
- **Which form of the number is published (2026-08).** The accuracy metrics are
  reported in the **fractional multiplicative** form — `mae = 10^mean|log10(M/O)|
  − 1`, so `0.109` means **10.9%** and `0` is perfect (Erickson 2023). Note that
  Seegers et al. 2018 publishes the **un-subtracted factor** (`1.109`, where
  "1.5 = 50% error"), so every table and glossary entry must **state which
  convention it uses**; an unlabelled `0.109` is misread as a factor by readers
  from that lineage. Seegers' companion guidance is adopted as well: report **no
  more than one metric each** for bias, accuracy and precision, and treat RMSE,
  r² and regression slope as supporting detail rather than headline scores (they
  assume Gaussian residuals and amplify outliers). "Wins" remains the ranking
  metric, which is Seegers' own recommendation.
- **Total before decomposed.** Report total `a(λ)` / `bb(λ)` separately from the
  decomposed `a_dg`, `a_ph`, `bb_p`, never blended into one aggregate score: the
  decomposed products are consistently the weaker retrievals, and an aggregate
  that hides that is (rightly) distrusted. This mirrors IOCCG Report 5 and GIOP
  (Werdell et al. 2013), whose evaluation tables the IOP community reads as the
  reference form — `Ratio = median(M/O)` and `MPD = median(100|M/O − 1|)` are
  worth carrying under those names for continuity, since IOPtics already computes
  both (`median_ratio`, and `rel_misfit` for GIOP's spectral ΔRrs).
- **Synthetic and in-situ are parallel tracks, never pooled.** L23 (Hydrolight,
  radiometric closure by construction) isolates inversion skill; PANGAEA/GLORIA do
  not. Following IOCCG Report 5's design — and GIOP's — every comparison reports
  the two tracks side by side rather than producing one blended winner.

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
- ~~**Rrs MAE / bias** with a dual-sided acceptance window and a **>25% Rrs MAE**
  QC bound~~ — **superseded 2026-07.** The log-space multiplicative MAE is invalid
  for `Rrs`, which **crosses zero in the red**: L23 `Rrs` above ~600 nm is ≈0 and
  goes negative under PACE noise, so the red tail dominated the ratio and tripped
  the 25% bound on fits whose χ²ᵥ was ≈1. Replaced by:
- **χ²ᵥ-based QC.** The closure flag derives from the noise-weighted reduced χ²ᵥ
  (a fit above `CHI2NU_QC_MAX` is a non-solution), reported with the dof-scaled
  `frac_good` / `frac_overfit` / `frac_underfit` split.
- **Relative misfit** — median `|Rrs_model − Rrs_obs| / Rrs_obs` over the
  strictly-positive bands: noise-model-independent, and the metric that exposed a
  case where χ²ᵥ moved 5× when the assumed error floor changed while the fits did
  not move at all. This is GIOP's **ΔRrs** in all but name, so it is reported as
  such.

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
  - **Promoted to a headline result (2026-08).** Coverage is reported next to its
    **nominal target** and **flagged when it misses**, because the first real sweep
    produced exactly the case this metric exists for: on L23, `giop` is the more
    accurate retrieval (mae 0.062 vs 0.109, winning 85% of head-to-head contests)
    yet its 68%/95% intervals contain truth only 45%/65% of the time, while
    `expb_pow` sits at 65%/100%. "More accurate but over-confident" is a
    first-class finding, not a footnote in a CSV.
  - **This is genuinely novel, and must be labelled as such.** A survey of the
    community's practice (IOCCG Report 18; McKinna et al. 2019) found an
    established convention for *propagating* per-retrieval uncertainty but **no
    established convention for validating whether the stated uncertainty is
    calibrated**. IOPtics' coverage diagnostic is therefore a contribution, and
    reports should present it as new rather than as standard practice.

### 5. Cross-algorithm comparison

- **"Wins"** — the fraction of head-to-head contests in which an algorithm gives
  the more accurate estimate per variable (Erickson / Seegers).
- **Per-variable ranking** by `|bias|`, MAE, and wins (Erickson Table 2 style).
- **Ties are reported as ties (2026-08).** Where algorithms are statistically
  indistinguishable the comparison **says so instead of ranking them 1..N**. The
  first turbid sweep made this unavoidable: four `bb_p` parameterizations returned
  χ²ᵥ medians of 0.4602 / 0.4629 / 0.4616 / 0.4602 and identical status fractions,
  and presenting that as a 1-4 ranking invents a result. Two consequences for the
  implementation: a contest whose metrics are all undefined must **never** be
  assigned a rank, and the tie rule needs a stated statistical basis (the
  ocean-colour precedent is Brewin et al. 2015's round-robin, which derives rank
  uncertainty from **1000 bootstrap resamples** with each model's score normalised
  by the all-model average — overlapping intervals mean indistinguishable). Note
  that the *current* pairwise table cannot support a paired test: it tallies wins
  per algorithm and discards the opponent's identity, so this needs a new metrics
  pass over the per-spectrum results (no re-fitting).
- **Retrieval success is a scored metric, not a footnote.** Brewin's round-robin
  scores **η, the percentage of possible retrievals**, on the stated grounds that an
  algorithm "should not be a source of more gaps in the data than would be the case
  if other algorithms were used". IOPtics' `frac_ok` is that quantity and is
  promoted accordingly, alongside the honest denominators (below).
- **Name the denominators.** Three different `n`s coexist and must be labelled
  distinctly wherever they appear: `n_attempted` (spectra the sweep tried),
  spectra **scored** (status `ok`), and surviving **(retrieved, truth) pairs** after
  the positivity/NaN intersection. On the first GLORIA sweep these were 100, 21 and
  12 for the same contest. IOCCG Report 5 sets the precedent by tabulating both
  `N` (tested) and `n` (valid) and stating plainly that excluding failures yields
  "likely better statistical results".

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

**Figure conventions added 2026-08**, from a survey of how the community presents
IOP-algorithm inter-comparisons:

- **Annotate the statistics inside the panel** (`N`, valid `n`, ratio, MPD). Both
  IOCCG Report 5 and GIOP put the numbers in the plot corner; a scatter with no
  numbers on it cannot be read without the table.
- **Pair every scatter with a distribution of the ratios** (GIOP's ratio-histogram
  panels; a violin or box plot of log ratios is a legitimate modern rendering).
  Central tendency alone hides the spread that decides whether a model is usable.
- **Metric-vs-wavelength is mandatory, not optional**, in IOP work — as small
  multiples over (component × algorithm) where space allows. IOPtics already
  computes the per-wavelength table for this.
- **Type-II (major-axis) regression** wherever a fit line is drawn; never OLS, since
  both axes carry error.
- **Taylor is demoted to optional.** It stays available, but the community signal is
  against leaning on it: Brewin et al. 2015 computed the full Taylor triple and
  deliberately did not draw the diagram, and Seegers' critique undercuts the
  r²/RMSE basis it rests on. Target (bias vs unbiased RMSD) maps cleanly onto the
  bias/accuracy split and is retained. Neither may be the *only* summary.
- **A pairwise win-rate matrix** per band and per stratum, which is what "wins"
  supports and what a reader scanning for "who wins where" actually looks for.

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

**Artifact selection rules (added 2026-08, after the first published reports.)** The
first cross-algorithm pages exposed a structural flaw: the figure set was fixed at
`a(440)` / `bb(555)` / `expb_pow`-vs-`giop`, so a sweep on a dataset with different
truth (GLORIA, whose only spectral truth is `a_dg(440)`) published **five blank "no
data" panels beneath confident captions explaining how to read them**. Therefore:

- **The figure set is data-driven, never hardcoded.** Components, reference
  wavelengths and the ΔBIC pair are chosen from what the sweep actually has truth
  and algorithms for.
- **A section with no data is suppressed, not published empty.** A degenerate panel
  must never reach a page; where a whole class of figures is unavailable the page
  says why in prose.
- **Every page states results, not just how to read figures.** Generated prose must
  interpolate the actual numbers (winner, its error, its calibration, the `n` it was
  scored on); a page whose text would be identical for any sweep is not a report.
  Hand-written findings live in a per-sweep include the generator will not clobber.
- **A curated set of exemplar spectra per sweep** on its own page: the **best fit,
  the worst fit, and eight median fits** (10 total), each panel labelled with its
  `obs_id`, χ²ᵥ and relative misfit. This is the "look at an actual fit" view that
  aggregate scatter plots cannot provide.
- **One figure style for the whole project.** A single style module (fonts,
  constrained layout, the docs' ocean palette, axis units) is applied by the
  plotting primitives, the documentation figure generators and the standalone
  analysis scripts alike — the first reports shipped colliding tick labels and
  default-matplotlib colours against ocean-palette documentation figures.
- **A fixed colour and marker per algorithm, project-wide.** Colour must be assigned
  from the registry, not from within-figure appearance order, so an algorithm is the
  same colour on every page and adding an algorithm does not reshuffle the others.
  Marker shape as well as colour, so the figures survive colour-blind readers and
  greyscale printing.

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

**All three are first-class (confirmed 2026-08).** Both audiences are real — "how
does *my* algorithm do across datasets?" and "which algorithm should I use for *this*
water?" — so per-algorithm and per-dataset reports are built, not just the
cross-algorithm page. Two refinements follow from the community's reading habits:

- **Standing answers vs. audit trail.** Every published URL is currently a *sweep
  id*, which only answers "what did this run do" — a question no outside reader
  arrives with. The report types therefore split by lifetime: **profiles**
  (per-algorithm and per-dataset, folded across *all* sweeps) are the entry points
  and stable citable URLs, while the **per-sweep pages** remain the
  provenance-stamped record, reachable from the profiles rather than being the front
  door. *(URL scheme and generated-vs-curated split still open — see Open
  Questions.)*
- **A coverage matrix as the site's opening figure**: algorithms × datasets, each
  cell carrying the headline skill and `n`, and each *empty* cell reading **"not
  evaluated"**. It answers "has anyone tested X on Y?" before any ranking matters.
  Note that "not evaluated" must be distinguished from "evaluated and failed", and
  that absence of a row is currently ambiguous in the persisted artifacts (it
  conflates never-run, run-but-unscored, and run-under-MCMC), so the matrix is built
  by walking the runs tree rather than trusting the leaderboard alone.

**Reader-facing slices to surface.** Three dimensions are computed today and then
discarded before they reach a page: **per-stratum** results (tables are pinned to
`stratum='all'`), the **MCMC population** (pinned to χ²), and **wavelength-resolved**
accuracy (the per-λ metrics table is written, loaded, and consumed by nothing). All
three belong on the profile pages; the per-λ figure is the one an ocean-colour reader
looks for first.

### Leaderboard

The cross-algorithm comparison is anchored by a **persistent leaderboard** that
ranks algorithms by the headline metrics across datasets and strata. Starting
from the initial `expb_pow`/`giop` pair and growing as algorithms are added to the
registry, the leaderboard **accumulates and updates** as each new algorithm is
evaluated, giving the community a single, evolving view of relative performance.

**Rules added 2026-08, from what the first published leaderboard actually did:**

- **Never rank a contest with no data.** 144 of the 160 published rows had no finite
  metric and yet each carried a rank of 1-4, because ranks were assigned by position
  after sorting. A row without a measurement gets no rank.
- **Fold every sweep.** The published board contained one sweep; re-folding must
  restore the others, and the fold has to be **dataset-aware** — the current wins
  merge omits `dataset`, which row-multiplies a multi-dataset sweep and cross-assigns
  win fractions between datasets. It must also carry **`fit_method`**, or an
  MCMC-only algorithm is invisible on the board no matter how well it performed.
- **Keep the upstream stamps.** The fold reduces provenance to an `ioptics`
  commit; the **`bing` and `ocpy` commits are dropped**, though BING is where the
  model forms and the fitter live. Two rows sharing an algorithm name are not
  otherwise guaranteed to be the same algorithm.
- **Landing page presentation:** a headline table per `(dataset, component)` with the
  full grid on a drill-down page, all-undefined rows hidden, per-sweep **summary
  cards** (date, dataset, algorithms, `n`, one-line finding) in place of a bare glob
  toctree, and the interactive leaderboard widget — already implemented and unused —
  wired up.

### Interactive figures

In addition to static publication figures, IOPtics provides **interactive Bokeh
figures** that let a user **select an algorithm (and dataset/stratum) and inspect
its results** — e.g. browse retrieved-vs-true scatter, spectra with uncertainty
bands, and the leaderboard interactively. These are delivered as
**standalone/static BokehJS** (self-contained HTML with JS callbacks — dropdown
select, hover, pan/zoom), so they embed directly in the readthedocs site with no
running Bokeh server.

**Refinements 2026-08:**

- **BokehJS is vendored into the docs' static assets**, not loaded from
  `cdn.bokeh.org`. The published pages currently carry five CDN script tags with the
  version pinned into committed RST (and already drifting — 3.9.0 on one page, 3.9.1
  on another), so the interactive figures break offline, behind a restrictive CSP,
  and eventually when the CDN moves. *(Longer term, dropping interactivity in favour
  of richer static panels remains on the table.)*
- **Point counts are capped and the sampling is stated.** The embedded payload is
  downsampled (stratified, seeded) so page size is independent of sweep size; the
  figure must say what fraction of the population it is showing, since a reader
  otherwise assumes they are seeing everything.
- **Hover carries `obs_id`**, so an outlier can be traced back to a spectrum — and
  the interactive figure must use the same 1:1 / 3:1 / 1:3 guide convention as the
  static scatters rather than its own.

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

**Added 2026-08:**

- **Hand-written analyses are published too.** A generated page cannot state a
  diagnosis. The GLORIA fit investigation — which established that the wall in turbid
  water is backscattering, not CDOM/detritus absorption, and that 70% of GLORIA
  spectra quote no `Rrs` uncertainty at all — lived only as a repository markdown
  file with its figures outside the docs tree, while the published pages depended on
  its conclusions through code comments. Such analyses are **converted to RST and
  published on the site**, with the original markdown retained for posterity.
- **The numbers are reusable, not just readable.** Each page offers the table behind
  it as CSV, the leaderboard as a single downloadable file, and a snippet that
  regenerates the page from the persisted artifacts.
- **Citable, frozen releases alongside the live site.** The community norm for
  comparison products is a versioned, DOI'd deliverable (IOCCG reports carry ISBN +
  DOI via Ocean Best Practices; OC-CCI ships numbered validation reports), while the
  best evaluation dashboards elsewhere in earth science — WeatherBench 2, ILAMB —
  publish open evaluation code plus baseline data and generate leaderboard and
  diagnostics as one artifact. IOPtics follows both: **pin and DOI a frozen benchmark
  release** (data snapshot + algorithm versions + evaluation code) that a paper can
  cite, while the live site tracks HEAD and shows its release tag on every page.
- **Structural borrowings from the NASA ATBD form**, which this audience reads
  fluently: a **plain-language summary**, an explicit **usage-constraints** section,
  and validation split into methods / uncertainties / errors.
- **Provenance must survive to be trustworthy (see also Analysis §Provenance).** The
  first sweeps revealed that the persisted algorithm block omits the fit budget
  (`maxfev`) and the MCMC block, records a stale `noise_model`, and ignores
  config-level per-algorithm overrides entirely — so a sweep whose fits only
  converged because of a raised iteration budget is indistinguishable from one run at
  the default. Cross-sweep profiles are only honest once the block carries those
  fields plus a digest, and once a results row can be traced back to its
  configuration.

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
| 4 | **Metrics section** | Drafted | Initial battery from BING (Prochaska & Frouin 2025) and Erickson et al. (2023); log-space MAE/bias adopted, coverage test at 68%/95%, Taylor + Target diagrams added. Battery expected to grow. Revised 2026-08: χ²ᵥ-based closure QC replaces the Rrs-MAE window; relative misfit added; coverage promoted to a headline result; ties reported as ties; Taylor demoted to optional. |
| 5 | ~~**GLORIA data acquisition**~~ | **Resolved** (Stage 6) | Data downloaded to `$OS_COLOR/GLORIA` and the adapter wired; the resulting fit investigation is `reports/gloria_fits_report.md`, to be published as RST. |
| 6 | **Metric family to lead with** | Open | Fractional multiplicative `mae`/`bias` + wins (current, Erickson form) vs. Seegers' un-subtracted factor as the published form, with GIOP's `Ratio`/`MPD` alongside for continuity; whether to add MdSA/SSPB for the inland/coastal audience (relevant to GLORIA). |
| 7 | **Statistical basis for "indistinguishable"** | Open | Bootstrap-resampled score intervals (Brewin et al. 2015 precedent) vs. a declared effect-size floor vs. both. Needs a new metrics pass either way — the current pairwise table discards opponent identity. |
| 8 | **Cross-sweep algorithm identity** | Open | Whether one profile page pools sweeps that ran the same algorithm name under different `maxfev`/priors/RT (with a "what varied" block) or splits by spec digest. Blocked on the provenance hardening above. |
| 9 | **How opinionated the site is** | Open | Publish a per-water-type *recommendation*, or only ranked evidence? On the turbid data the honest recommendation today would be "none of these four work". |
| 10 | **Profile page URLs and generation** | Open | Where profiles live in the docs tree (a permanent choice), and whether they are fully generated, hand-curated, or generated tables plus a hand-written findings block. |
| 11 | **Computational cost as a metric** | Open | Runtime per fit / MCMC steps are recorded **nowhere** and are not retrievable downstream (the χ² fitter discards scipy's `infodict`). Reporting cost requires new instrumentation and a re-run; in or out of scope? |
| 12 | **Community on-ramp ("add your own model")** | Open | A documented path — register your parameterization in one call, run a bounded sweep, get the standard report, optionally contribute the numbers — is the highest-leverage item for the stated goal, but wants the profile pages solid first. |
| 13 | **MOANA** | Out of scope | Tracked as a separate IOPtics effort; its report may be exposed on the docs site eventually but it is not part of the model-comparison reporting. |

---

## References

Works cited in this design document. A fuller scientific reference list is in
[`docs/context.md`](../context.md).

- Erickson, Z. K., McKinna, L., Werdell, P. J., Cetinić, I. (2023). "Bayesian
  approach to a generalized inherent optical property model." *Optics Express*
  31(14), 22790–22801. https://doi.org/10.1364/OE.486581
- Brewin, R. J. W., et al. (2015). "The ocean colour climate change initiative:
  III. A round-robin comparison on in-water bio-optical algorithms." *Remote Sensing
  of Environment* 162, 271–294. https://doi.org/10.1016/j.rse.2013.09.016 (the
  round-robin scoring model: η as a scored test; bootstrap-resampled rank
  uncertainty)
- IOCCG (2006). *Remote Sensing of Inherent Optical Properties: Fundamentals, Tests
  of Algorithms, and Applications.* Lee, Z.-P. (ed.), IOCCG Report 5.
  https://ioccg.org/reports/report5.pdf (the IOP algorithm inter-comparison
  precedent: log-space statistics, Type-II regression, `N` tested vs `n` valid)
- IOCCG (2019). *Uncertainties in Ocean Colour Remote Sensing.* IOCCG Report 18.
  https://ioccg.org/group/uncertainties/
- Jolliff, J. K., et al. (2009). "Summary diagrams for coupled hydrodynamic-
  ecosystem model skill assessment." *J. Marine Systems* 76(1–2), 64–82.
  https://doi.org/10.1016/j.jmarsys.2008.05.014
- McKinna, L. I. W., et al. (2019). "Approach for propagating radiometric data
  uncertainties through NASA ocean color algorithms." *Frontiers in Earth Science* 7,
  176. https://doi.org/10.3389/feart.2019.00176
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

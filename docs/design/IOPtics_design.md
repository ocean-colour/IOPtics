# IOPtics Design Document

**Version:** 0.2
**Date:** 2026-06-19
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
| **PACE field data** | NASA PACE validation team (released product) | In-situ | yes (hyperspectral) | Hyperspectral IOP / AOP match-ups | Forward-looking hyperspectral validation |

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

### PACE field validation data (forward-looking)

Hyperspectral in-situ IOP/AOP match-ups from the NASA PACE mission era
(post-2024), taken from the **PACE validation team's released validation
product**. Included to keep IOPtics aligned with current hyperspectral
validation efforts. *(Specific loader path TBD.)*

### Out of scope for now

- **IOCCG synthetic dataset** — deferred; the standard sets are quite dated, so
  L23 serves as our synthetic benchmark for now.
- **NOMAD / raw SeaBASS archive** — not treated as separate datasets, since
  PANAGEA already incorporates them.
- **Tara Oceans `ap`/`cp`** (particle absorption/attenuation, not Rrs-paired) —
  available locally but deferred as an IOP-shape reference rather than a
  validation set.

---

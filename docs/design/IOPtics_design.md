# IOPtics Design Document

**Version:** 0.1
**Date:** 2026-06-17
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
  - using in-situ measurements (e.g., PANGAEA/PANGAEA, GLORIA, NOMAD).
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

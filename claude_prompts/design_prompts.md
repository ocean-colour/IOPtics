# Design IOPtics

## Goals

We wish to generate a document that describes the design of IOPtics and its requirements.  This Repository will be used to test a wide range of IOP (inherent optical properties) algorithms.  We will generate metrics and diagnostics to share with the community.

We expect the package to do at least the following:

- Run a wide range of IOP algorithms on Rrs spectra
- Calculate IOP values and their uncertainties
   - absorption spectra (a), separated by water, CDOM, etc.
   - backscattering spectra (bb), separated by water, CDOM, etc.
   - We will primarily use the BING package for htis work
- Compare the results of the algorithms with ground truth values
   - Using simulated spectra
   - Using in-situ measurements
- Develop metrics and diagnostics that can be applied uniformly to all algorithms
- Share the results (figures, reports, etc.) with the community via GitHub
- Generate reports and publications on the main findings

## Claude

### Skills

Consider using the skills in .claude/skills/

## Context

Examine the following files that may help generating the design:

- The code and files in the BING Repository: https://github.com/ocean-colour/BING.  There is a local copy on this computer
- The docs/context.md file in this repository
- The BING paper: docs/PDFs/bing.pdf

## Overview

Guidelines for the design document which will be named IOPtics_design.md and will be stored in docs/design/.  Keep in mind:

- You are encouraged to suggest your own design ideas 
- This document will be used to guide the development of the IOPtics package
- It will not include specific code recommendations; we will generate a separate doc for that

## Prompts

### Context

- The Ocean Optics book, currently located in docs/PDFs/mobley-oceanicopticsbook.pdf
- The GIOP publication by Werdell+2013.  I have placed it in docs/PDFs/werdell_2013.pdf
- The review paper by Werdell+2018.  I have placed it in docs/PDFs/werdell2018.pdf

1. Read the Context section above.  Read the files in the BING Repository and the Ocean Optics book.  Generate a docs/context.md file that you can refer to which is a reduced form of the information in the files.  Add a version number and date to the file.  Log your work in the Logs section below.

### Prep

1. Start the design document by including a preamble of what it is for.  Title that section "Preamble".

   - Add any other information you think is relevant
   - Add a version number to the document (0.1)
   - Add a date to the document (today's date)
   - Add a author to the document (JXP and Claude)

2.  Oops, rename the document to IOPtics_design.md and store it in docs/design/.

### Designing

1. Read this doc.  Execute the 1st task under "Data/Tasks".

## Data

The following will describe several of the inital datasets to be used in IOPtics.

### The Hydrolight dataset provided by Loisel+2023, aka L23

Unless otherwise specified, these data are located in $OS_COLOR/Loisel2023

I have included a copy of their paper in docs/PDFs/Loisel_et_al_ESSD_2023.pdf

These are simulated spectra, so we know the ground truth values for the IOPs.

The API to load these data is provided through ocpy/ocpy/hydrolight/loisel23.py

### PANAGEA dataset

The ocpy package has a module for the PANAGEA dataset.  It is located in ocpy/insitu/panagea.py.  It is described in ocpy/docs/panagea.rst and also at https://doi.pangaea.de/10.1594/PANGAEA.941318.

These are real spectra with associated in-situ IOP measurements.

### The GLORIA dataset provided by Werdell+2013, aka G13

### What else?

Please explore the Internet to see if you can find any other in-situ datasets that are relevant to the development of IOPtics.

### Tasks

1. Examine the datasets listed above (you will need to explore GLORIA on your own) and start a conversation with me about the datasets and how we will use them in IOPtics.  Write questions in the Conversation section below and I will then answer them.  Log your work.

### Conversation

#### Claude's questions (2026-06-17)

I examined the three datasets via their `ocpy` modules and the literature. A quick
summary of what each actually provides, then my questions.

| Dataset | Source | Type | Rrs | Ground-truth IOPs | Notes |
|---|---|---|---|---|---|
| **L23** | Loisel et al. 2023 (Hydrolight) | Synthetic | yes | **full** `a, bb, aph, ...` (known truth) | `$OS_COLOR/Loisel2023`, `ocpy.hydrolight.loisel23`; X=inelastic scenario (1/2/4), Y=solar zenith (00/30/60) |
| **PANAGEA** | Valente et al. 2022, V3 | In-situ (real) | yes (native + sat-bands) | `aph`, `acdom` (CDOM+detrital combined), `bbp`, `kd`, + `chla`, `tss` | `$OS_COLOR/PANAGEA/V3`, `ocpy.insitu.panagea`; ID-indexed; itself a compilation of MOBY/BOUSSOLE/AERONET-OC/SeaBASS/NOMAD/Tara/... |
| **GLORIA** | Lehmann et al. 2023 | In-situ (real) | yes, **hyperspectral** 350–900 nm @1 nm, 7572 spectra | **none spectral** — only `Chla`, `TSS`, `aCDOM(440)`, Secchi | `ocpy.insitu.gloria`; **data not yet downloaded locally** (only a README pointer); heavily coastal/inland water types |

**A. Naming / identity (need to confirm before I rely on it)**

1. The Data section labels GLORIA as *"provided by Werdell+2013, aka G13."* That
   looks like a mix-up: the GLORIA in `ocpy` is **Lehmann et al. 2023** (Nature
   Sci. Data, PANGAEA 948492), and Werdell+2013 is the GIOP paper. Should I treat
   GLORIA = Lehmann 2023, and is "G13" a label you still want to use (and for
   which dataset)?

**B. How we use each dataset**

2. **L23** is the only source with full known-truth `a(λ)`/`bb(λ)`. I propose it
   be our **primary validation/benchmarking** dataset (per-wavelength and
   per-component error metrics). Agree? And which simulation scenarios do we
   standardize on — `X=1` (elastic only) for first-pass, or also `X=2/4`
   (Raman / + Chl-fluorescence)? Which solar zenith(s) `Y`?

3. **GLORIA** has no spectral IOPs — only `aCDOM(440)`, `Chla`, `TSS`, Secchi.
   So it can't validate full `a(λ)`/`bb(λ)` retrievals. How do you want to use
   it? Options: (a) validate scalar/band products only (e.g. retrieved
   `a_cdom(440)`); (b) **Rrs-space closure** (reconstructed vs. observed Rrs);
   (c) representativeness / out-of-distribution testing of input Rrs (you already
   have GLORIA UMAP/OOD notebooks in `ocpy`); (d) all of the above. Or do we
   defer GLORIA for now?

4. **PANAGEA** gives real co-located Rrs + `aph`/`acdom`/`bbp`. Note `acdom` is
   the **combined CDOM+detrital** term (≈ `a_dg`), and `bbp` is a single
   particulate term. Is matching algorithm output to that combined `a_dg` (rather
   than separate CDOM vs. NAP) the right comparison, and at which wavelengths?

**C. Cross-dataset consistency**

5. The three datasets define IOP components differently (L23 full breakdown;
   PANAGEA combined `a_dg`; GLORIA scalar only). Do you want a single canonical
   component scheme that all algorithms report into (e.g. `a_w, a_ph, a_dg, bb_w,
   bb_p`), with each dataset's truth mapped onto whatever subset it supports?

6. Wavelength grids differ (L23 Hydrolight grid; PANAGEA native + sat-bands;
   GLORIA 1 nm hyperspectral). What's the target convention — keep native per
   dataset, or resample everything to a common grid / set of sensor bands
   (PACE, MODIS, ...)? This drives the well-posedness (bands vs. unknowns) design.

**D. Other datasets ("What else?")**

7. Candidates I'd consider, with the caveat that **PANAGEA already absorbs many
   of them** (it's the Valente V3 compilation):
   - **IOCCG synthetic dataset** — forward-modeled Rrs↔IOP with optical closure;
     a synthetic complement to L23 (simpler optics, no Raman/fluorescence).
   - **NOMAD / SeaBASS** (NASA) — real IOPs+Rrs; largely *inside* PANAGEA already,
     so probably redundant unless we want the raw archive.
   - **Tara Oceans `ap`/`cp`** — you already have this locally (parquet); particle
     absorption/attenuation, not Rrs-paired, so more of an IOP-shape reference.
   - **PACE validation field data** (post-2024) — hyperspectral, forward-looking.

   Which of these (if any) do you want in scope for the first version?

## Analysis

We will develop a set of analysis methods that can be applied uniformly to all algorithms.  These will include:
- Calculating the IOPs from the spectra
- Calculating the uncertainties in the IOPs
- Calculating the metrics and diagnostics
- Generating figures and tables
- Generating reports and publications

For this, we will primarily use the BING package.

### Tasks

1. Please examine the BING package and generate a plan for the analysis methods.  Write the plan in the Planning document.  If you have any questions, write them in the Q&A section below. Log your work.

### Q&A

## Validation

We will develop a set of validation methods that can be applied uniformly to all algorithms.  These will include:

## Metrics

## Reporting

We will generate reports and publications on the main findings.  This will include figures, tables, and text.  These will be shared via readthedocs.io which will neccesitate .rst files.

## Logging

The "Logs" section will record Claude's work.  Please use the following format:

### <Date> (Short summary of the work)

<Detailed description of the work and what you learned>

### <Date> (Short summary of the work)

<Detailed description of the work and what you learned>

...

## Logs

### 2026-06-17 (Prep #1: started the design document with a Preamble)

Created the design document (v0.1, 2026-06-17, authors JXP and Claude) per Prep
prompt #1. Added a titled **Preamble** section covering: the document's purpose
(guiding reference for IOPtics development, code-free design, living document),
the package scope/goals (running IOP algorithms on Rrs, computing a/bb and
uncertainties via BING, comparison against simulated and in-situ ground truth,
uniform metrics/diagnostics, community sharing via GitHub/readthedocs), a pointer
to the distilled `docs/context.md` reference, and conventions. Included the
requested version (0.1), date (today), and authors.

### 2026-06-17 (Prep #2: renamed the design document)

Per Prep prompt #2, renamed `docs/design/IOPtics_dashboard_design.md` to
`docs/design/IOPtics_design.md`. Document contents unchanged.

### 2026-06-17 (Designing #1 → Data/Tasks #1: examined datasets, opened conversation)

Executed Designing prompt #1, which points to Data/Tasks #1. Examined the three
datasets through their `ocpy` modules and the literature:

- **L23** (`ocpy.hydrolight.loisel23`): synthetic Hydrolight; the only source
  with full known-truth IOP spectra (`a, bb, aph`; Chl derivable from aph@440).
  Files `Hydrolight{X}{Y}.nc` in `$OS_COLOR/Loisel2023`; X = inelastic scenario
  (1/2/4), Y = solar zenith (00/30/60).
- **PANAGEA** (`ocpy.insitu.panagea`): the Valente et al. 2022 V3 in-situ
  compilation. Real co-located Rrs (native + sat-bands) with `aph`, `acdom`
  (combined CDOM+detrital ≈ `a_dg`), `bbp`, `kd`, `chla`, `tss`. ID-indexed.
  Itself aggregates MOBY/BOUSSOLE/AERONET-OC/SeaBASS/NOMAD/Tara/etc.
- **GLORIA** (`ocpy.insitu.gloria`): Lehmann et al. 2023, hyperspectral Rrs
  (350–900 nm @1 nm, 7572 spectra, 450 water bodies) but **no spectral IOPs** —
  only `Chla`, `TSS`, `aCDOM(440)`, Secchi; coastal/inland-heavy. **Not yet
  downloaded locally** (ocpy ships only a README pointing to PANGAEA 948492).

Key learnings / flags: (1) the prompt's "GLORIA = Werdell+2013, aka G13" appears
to be a mislabel — GLORIA is Lehmann 2023, Werdell 2013 is GIOP. (2) GLORIA can't
validate full a(λ)/bb(λ) (scalar/band/closure/OOD use only). (3) datasets differ
in component definitions and wavelength grids, which bears on uniform metrics and
well-posedness. Web search confirmed GLORIA contents and that PANAGEA already
subsumes most candidate in-situ archives; remaining distinct candidates are the
IOCCG synthetic set, raw NOMAD/SeaBASS, Tara `ap`/`cp`, and PACE field data.

Wrote 7 questions to the Conversation section (grouped: naming/identity, per-
dataset use, cross-dataset consistency, other datasets) for JXP to answer.
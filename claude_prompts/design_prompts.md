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
2. Read this doc.  Execute the 2nd task under "Data/Tasks".
3. Read this doc.  Execute the 3rd task under "Data/Tasks".

4. Read this doc.  Execute the 1st task under "Analysis/Tasks".
5. Read this doc.  Execute the 2nd task under "Analysis/Tasks".
6. Read this doc.  Execute the 3rd task under "Analysis/Tasks".
7. Read this doc.  Execute the 4th task under "Analysis/Tasks".
8. Read this doc.  Execute the 5th task under "Analysis/Tasks".

9. Read this doc.  Execute the 1st task under "Metrics/Tasks".
10. Read this doc.  Execute the 2nd task under "Metrics/Tasks".
11. Read this doc.  Execute the 3rd task under "Metrics/Tasks".

12. Read this doc.  Execute the 1st task under "Reporting/Tasks"
13. Read this doc.  Execute the 2nd task under "Reporting/Tasks"

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

2. See my answers to the questions in the Conversation section below.  Then proceed to:

   - Add a Data section to the design document that lists the datasets and how we will use them.
   - Ask me any new questions you have in the Conversation section below.
   - Bump the version number of the design document 
   - Log your work in the Logs section below.

3. See my answers to the questions in the Conversation section below.  Edit the Data section to reflect the decisions.  Log your work.  If you have any new questions, write them in the Conversation section below.

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

Yes, GLORIA = Lehmann 2023, and we will use it for validation of the algorithms.

**B. How we use each dataset**

2. **L23** is the only source with full known-truth `a(λ)`/`bb(λ)`. I propose it
   be our **primary validation/benchmarking** dataset (per-wavelength and
   per-component error metrics). Agree? And which simulation scenarios do we
   standardize on — `X=1` (elastic only) for first-pass, or also `X=2/4`
   (Raman / + Chl-fluorescence)? Which solar zenith(s) `Y`?

Yes, L23 will be our primary validation/benchmarking dataset.  We will standardize on `X=1` (elastic only) for first-pass, and then `X=4` (Raman / + Chl-fluorescence).  We will use `Y=00` (0° solar zenith).

3. **GLORIA** has no spectral IOPs — only `aCDOM(440)`, `Chla`, `TSS`, Secchi.
   So it can't validate full `a(λ)`/`bb(λ)` retrievals. How do you want to use
   it? Options: (a) validate scalar/band products only (e.g. retrieved
   `a_cdom(440)`); (b) **Rrs-space closure** (reconstructed vs. observed Rrs);
   (c) representativeness / out-of-distribution testing of input Rrs (you already
   have GLORIA UMAP/OOD notebooks in `ocpy`); (d) all of the above. Or do we
   defer GLORIA for now?

Yes, we will validate the algorithms using the scalar/band products only.  We will not use the Rrs-space closure.  We will not use the representativeness / out-of-distribution testing of input Rrs.

4. **PANAGEA** gives real co-located Rrs + `aph`/`acdom`/`bbp`. Note `acdom` is
   the **combined CDOM+detrital** term (≈ `a_dg`), and `bbp` is a single
   particulate term. Is matching algorithm output to that combined `a_dg` (rather
   than separate CDOM vs. NAP) the right comparison, and at which wavelengths?

Yes, we will match the algorithm output to the combined `a_dg` term.  We will use the wavelengths provided in the PANAGEA dataset.

**C. Cross-dataset consistency**

5. The three datasets define IOP components differently (L23 full breakdown;
   PANAGEA combined `a_dg`; GLORIA scalar only). Do you want a single canonical
   component scheme that all algorithms report into (e.g. `a_w, a_ph, a_dg, bb_w,
   bb_p`), with each dataset's truth mapped onto whatever subset it supports?

I am not sure at the moment.  Let's defer this decision.

6. Wavelength grids differ (L23 Hydrolight grid; PANAGEA native + sat-bands;
   GLORIA 1 nm hyperspectral). What's the target convention — keep native per
   dataset, or resample everything to a common grid / set of sensor bands
   (PACE, MODIS, ...)? This drives the well-posedness (bands vs. unknowns) design.

Keep the native per-dataset grids.

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

Let's include the IOCCG synthetic dataset and the PACE validation field data.

#### Claude's new questions (2026-06-19)

Thanks — I added a **Data** section to `IOPtics_design.md` and bumped it to v0.2.
A few new questions surfaced while writing it:

8. **GLORIA download.** The data aren't local yet (only a README pointing to
   PANGAEA 948492). Do you want me to download/unpack it now into the `ocpy`
   GLORIA folder, or leave that to you (you run git/data ops)?

I will find the GLORIA data and download it.  Proceed without it for now.

9. **IOCCG synthetic dataset.** There are a few versions (e.g. the classic IOCCG
   Report 5 / Lee 2006 synthetic set, and newer ones). Which specific IOCCG set
   do you mean, where should it live (`$OS_COLOR/IOCCG`?), and is there an `ocpy`
   loader for it yet or do we need to write one?

I didn't realize how old these were.  Let's ignore them for now.

10. **PACE field validation data.** Which source do you have in mind — NASA
    SeaBASS PACE match-ups, a specific cruise/campaign, or the PACE validation
    team's released product? This determines the loader and what truth variables
    (spectral IOPs vs. AOPs) we get.

Use the PACE validation field data from the PACE validation team's released product.

11. **L23 scenario scope.** You chose `X=1` then `X=4`, `Y=00`. Do you also want
    me to keep `X=2` (Raman only) available for an ablation (isolating Raman vs.
    fluorescence), or strictly `X=1` and `X=4`?

We will not use `X=2` (Raman only). 

12. **GLORIA scalar metric.** For scalar validation, retrieved `a_dg(λ)` must be
    reported at 440 nm to compare against GLORIA's `aCDOM(440)`. Note GLORIA's
    truth is CDOM-only at 440 while algorithms typically retrieve combined
    `a_dg` — do you want that comparison flagged as CDOM-vs-(CDOM+detritus)
    mismatch, or is the 440 nm comparison acceptable as-is?

Yes, we should flag it.

#### Claude's new questions (2026-06-19, round 2)

Applied all of your Q8–Q12 answers to the Data section. One follow-up:

13. **PACE validation product specifics.** I'm not aware of a single consolidated
    "released validation product" from the PACE validation team yet — PACE
    field/validation data are usually distributed through NASA **SeaBASS** (and
    OB.DAAC). When you have it, can you point me to the specific release / DOI /
    SeaBASS query so I (or `ocpy`) can write the right loader and know which truth
    variables (spectral `a`/`bb` vs. AOPs) we actually get? Marked TBD in the doc
    for now.

I don't know either.  I will ask around.  For now, let's not include this.

## Analysis

We will develop a set of analysis methods that can be applied uniformly to all algorithms.  These will include:

- Calculating the IOPs from the spectra
- Calculating the uncertainties in the IOPs
- Calculating summary metrics and diagnostics
- Generating figures and tables
- Generating reports and publications

For this, we will primarily use the BING package.

### Tasks

1. Please examine the BING package and generate a plan for the analysis methods.  Write the plan in the Planning document in an Analysis section.  If you have any questions, write them in the Q&A section below. Log your work.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Add the Analysis section to the design document.
    - Make edits to the Analysis section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Bump the version number of the design document
    - Log your work in the Logs section below.

3. I have answered your new questions in the Q&A section below.  Please proceed to:

    - Make edits to the Analysis section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Add to the design doc:
      - We must record the details of the model used, for provenance.
      - This must include Priors for any Bayesian inference.
    - Log your work in the Logs section below.

4. I have answered your new questions in the Q&A section below.  Please proceed to:

    - Make edits to the Analysis section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

5. I have answered your new questions in the Q&A section below.  Please proceed to: 

    - Make edits to the Analysis section to reflect the decisions.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-20)

I examined the BING package and wrote the analysis plan in a new Planning
document, `docs/design/IOPtics_planning.md` (Analysis section). Questions:

A. **Planning document location/name.** No Planning doc existed, so I created
   `docs/design/IOPtics_planning.md` as the implementation-oriented companion to
   the design doc. Is that the right home/name, or did you have a specific file
   in mind?

No, you should have used the IOPtics_design.md document.  Please do so and remove the Planning document.

B. **Fitting method default.** BING offers both least-squares (`chisq_fit`) and
   MCMC (`emcee`). MCMC gives the fullest uncertainties but is far more
   expensive. For the first-pass L23 sweep across many algorithms × spectra,
   should the default be least-squares (fast, gradient covariance) with MCMC
   reserved for a subset, or MCMC throughout?

Yes, for first pass use `chisq_fit` with MCMC reserved for a subset.

C. **Algorithm set for v1.** BING ships standard combos `expb_pow`, `expbf_pow`,
   `giop`, `gsm`, `k2b`. Which do you want in the first IOPtics comparison — all
   of them, or a chosen subset? (This defines the initial algorithm registry.)

We will build them out one by one.  The design document should reflect this.

D. **`bing.fitting.l23` generalization.** My plan generalizes `prep_one_l23` into
   a dataset-agnostic prep so PANAGEA/GLORIA feed the same engine. Do you want
   that prep layer to live in IOPtics, or be contributed back upstream into BING
   (e.g. a `prep_one` alongside `prep_one_l23`)?

This is more about implementation than design.  For now, make it clear we will need a process to load and prepare the data for the analysis.

E. **Metrics scope now vs. later.** I sketched the metrics in the plan but left
   full definitions to the design doc's **Metrics** section (still empty). Should
   I draft that Metrics section next, or wait for a dedicated prompt?

Wait for a dedicated prompt.

#### Claude's questions (2026-06-20, round 2)

Moved the analysis content into `IOPtics_design.md` as a design-level **Analysis**
section, removed the standalone Planning document, reflected the "one at a time"
and "chisq first, MCMC for a subset" decisions, and bumped the design doc to v0.3.
Two new questions:

F. **First algorithm to build out.** Since algorithms are added one at a time,
   which should be the seed? Natural candidates: BING's default `expb_pow`
   (exponential a_dg + Bricaud a_ph + power-law bbp) or the community-standard
   `giop`. I'd suggest starting with `expb_pow` (BING's best-exercised path) — agree?

Yes, we will start with `expb_pow`.

G. **L23 noise model for first-pass.** L23 is synthetic (effectively noiseless
   truth). For the first-pass retrieval + uncertainty/closure metrics, what Rrs
   uncertainty should we assume — a PACE-like sensor noise model, a fixed percent
   of Rrs, or run noiseless first? This affects the uncertainty budget and ΔRrs
   closure thresholds.

Yes, we will assume a PACE-like sensor noise model.

#### Claude's questions (2026-06-20, round 3)

Applied F (seed = `expb_pow`) and G (PACE-like noise for L23 first-pass) to the
Analysis section, and added a **Provenance & reproducibility** subsection (records
the full algorithm config incl. priors for Bayesian inference). Two questions:

H. **PACE noise model specifics.** BING's noise module supports named satellite
   models (PACE/MODIS/SeaWiFS). For "PACE-like," do you want BING's built-in PACE
   OCI noise model as-is, or a particular SNR/Rrs-uncertainty spec? (Affects the
   uncertainty budget magnitude.)

We will use the ocpy.satellites.pace noise model.

I. **Provenance record format/location.** Should the provenance live alongside the
   results table (e.g. a config record per run, plus a run-level manifest), and do
   you want it human-readable (YAML/JSON) for sharing on GitHub? This is partly
   implementation, but I want the design to state the intent if you have a
   preference.

Yes, we will use YAML/JSON for the provenance record and put it next to the results table.

J. **Version bump policy.** Task #3 didn't ask for a version bump, so I left the
   design doc at **v0.3** (these are same-day refinements). Want me to bump to
   v0.4 given the new provenance requirement, or keep bumps only when you request
   them?

You should bump the version number of the design document whenever you consider it sensible.

#### Claude's questions (2026-06-20, round 4)

Applied H (use the `ocpy.satellites.pace` noise model), I (YAML/JSON provenance
record stored next to the results table), and J (I'll bump the version whenever
sensible — bumped to **v0.4** now). One question:

K. **Consolidate deferred decisions?** Several items are now deferred (canonical
   IOP-component scheme; PACE/IOCCG datasets; full Metrics/Validation sections).
   Want me to add a short running **"Open questions / deferred decisions"** section
   to the design doc so they're tracked in one place, or keep them inline where
   they arise?

Sure, do that.

## Metrics

To compare the various IOP algorithms, we will need to develop a set of metrics.  Ideally, these will be able to be applied uniformly to all algorithms.  However, some algorithms will retrieve only a subset of the IOPs and there will be other factors that make true uniformity difficult to achieve.  

### Tasks

1. Based on your understanding of BING and especially the analysis performed in the `docs/PDFs/bing.pdf` and `docs/PDFs/erickson2023.pdf` papers, generate a plan for the metrics.  Write the plan in the Metrics section of the design document.  If you have any questions, write them in the Q&A section below. Log your work.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Metrics section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

3. I have answered your new questions in the Q&A section below.  Please proceed to:

    - Make edits to the Metrics section to reflect the decisions.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-20, Metrics)

Wrote the Metrics section of `IOPtics_design.md` (v0.6), grounded in BING
(Prochaska & Frouin 2025) and Erickson et al. (2023). Both papers' key choices and
gaps shaped it; a few decisions are worth your call:

L. **Primary accuracy metric convention.** I adopted Erickson's **multiplicative,
   log-space MAE & bias** (Seegers et al. 2018) as the primary accuracy metrics
   (BING reported unspecified % bias/MAE/RMS). OK to standardize on the
   Seegers/Erickson log-space definitions across all algorithms?

Yes, this is a fine start.  I am certain we will include more.

M. **Taylor / Target diagrams.** Neither BING nor Erickson use them, but they're
   common in the broader community (and noted in `context.md`). Include them in
   the standard diagnostic set, or leave them out for now?

What are these?  Point me to a few references and then I'll decide.

N. **Uncertainty coverage test.** I proposed adding a *formal* coverage/calibration
   test (fraction of truths inside the X% interval ≈ X%) — absent from both
   papers. Confirm you want this as a first-class, comparable metric, and at which
   level(s) (e.g. 68% and 95%)?

Yes, that is a good idea. 

O. **Reference wavelengths.** I set absorption summaries at 440/443 nm and
   backscatter at 555 nm (matching the papers), in addition to full-spectrum
   metrics. Are those the reference wavelengths you want, or a different set
   (e.g. add 490, 670)?

Let's include a redder wavelength for backscatter too.

#### Claude's answers + new questions (2026-06-20, Metrics round 2)

Applied your decisions to the Metrics section (v0.7): kept log-space MAE/bias as
the **initial** battery (noted it will grow, per L); set the coverage test at the
**68% and 95%** levels (N); added a **redder backscatter reference wavelength,
670 nm**, alongside 555 nm (O). Taylor/Target left **out** pending your review (M).

**Re M — what Taylor & Target diagrams are (references):**

- **Taylor diagram** — a single polar plot that places each algorithm by three
  linked statistics at once: correlation with truth (azimuth), normalized standard
  deviation (radius), and centered RMS difference (distance to the "truth" point).
  Great for ranking many algorithms on one figure.
  - Taylor, K. E. (2001), *JGR* 106(D7), 7183–7192,
    https://doi.org/10.1029/2000JD900719
- **Target diagram** — a Cartesian plot of **bias** (y) vs. **unbiased RMSD** (x,
  signed), so a point's distance from the origin is the total RMSD; it separates
  systematic from random error at a glance.
  - Jolliff et al. (2009), *J. Marine Systems* 76(1–2), 64–82,
    https://doi.org/10.1016/j.jmarsys.2008.05.014
- Both are used in ocean-color algorithm validation; `context.md` §6 also lists
  them. They're complementary: Taylor for correlation+variance, Target for
  bias+random error.

P. **Taylor/Target decision.** Given the above, do you want either/both added to
   the standard diagnostic set? (They're cheap to produce from the results table.)

Yes, let's add both.

## Reporting

We will generate reports and publications on the main findings.  This will include figures, tables, and text.  These will be shared via readthedocs.io which will neccesitate .rst files.

### Tasks

1. Based on your understanding of BING and especially the analysis performed in the `docs/PDFs/bing.pdf` and `docs/PDFs/erickson2023.pdf` papers, generate a plan for the Reporting.  Write the plan in the Reporting section of the design document.  If you have any questions, write them in the Q&A section below. Log your work.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Reporting section to reflect the decisions.
    - Include the following additions:
      - Interactive Bokeh figures that allow the user to select an algorithm and inspect the results.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-20, Reporting)

Wrote the Reporting section of `IOPtics_design.md` (v0.9): artifacts (results
table + provenance, figures, tables), three report types (per-algorithm,
cross-algorithm comparison, per-dataset), `.rst`/readthedocs + GitHub delivery,
reproducibility stamping, and publications. Questions:

Q. **Build automation.** Should reports rebuild automatically via CI (e.g. GitHub
   Actions) on each sweep / commit, or be generated on demand? (Affects whether
   readthedocs always reflects the latest sweep.)

There should be a standard report generated, but only demand.

R. **Single site vs. per-report.** One IOPtics readthedocs site that accumulates
   all reports (with a comparison "dashboard" landing page), or separate
   builds/pages per sweep? The repo name `IOPtics_dashboard_design.md` (original)
   hinted at a dashboard — do you still want a dashboard-style landing page?

One readthedocs site for all reports. 

S. **Leaderboard.** For the cross-algorithm comparison, do you want a persistent
   **leaderboard** (algorithms ranked by the headline metrics across datasets)
   that updates as algorithms are added one-by-one, or just static per-sweep
   comparison tables?

I like that. Let's include a Leaderboard

#### Claude's questions (2026-06-20, Reporting round 2)

Applied Q (standard report, generated on demand — not CI), R (single accumulating
readthedocs site), S (added a persistent, accumulating **Leaderboard**), and added
the requested **interactive Bokeh figures** (select algorithm/dataset to inspect
results). Design doc → v0.10. One question:

T. **Bokeh delivery constraint.** Interactive Bokeh embedded in readthedocs works
   as **standalone/static HTML** (BokehJS, `output_file`/`components`) — full
   server-backed callbacks (`bokeh serve`) won't run on readthedocs. Is
   standalone-Bokeh interactivity (hover, select-from-dropdown via JS callbacks,
   pan/zoom) sufficient, or do you envision a live server (which would need
   separate hosting)?

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

### 2026-06-19 (Designing #2 → Data/Tasks #2: added Data section, bumped to v0.2)

Read JXP's answers to the 7 questions, then executed Data/Tasks #2. Decisions
captured: GLORIA = Lehmann 2023 (validation); L23 is the primary benchmark,
standardizing on X=1 (elastic) then X=4 (Raman+Chl-fluorescence), Y=00; GLORIA
used for scalar/band-product validation only (no Rrs closure, no OOD); PANAGEA
output matched to combined `a_dg` at native PANAGEA wavelengths; native
wavelength grids kept per dataset; canonical component scheme deferred; added
IOCCG synthetic and PACE field data to scope (NOMAD/SeaBASS dropped as subsumed
by PANAGEA; Tara deferred).

Added a **Data** section to `docs/design/IOPtics_design.md` (cross-dataset design
decisions, a summary table, and per-dataset subsections) and a brief
"Out of scope for now" note. Fixed a Preamble typo (`PANGAEA/PANGAEA` →
`PANAGEA`). Bumped the document to **v0.2** and dated it 2026-06-19. Wrote 5 new
follow-up questions (Q8–Q12: GLORIA download, which IOCCG set, which PACE source,
X=2 ablation, GLORIA CDOM-vs-a_dg metric mismatch) to the Conversation section.

### 2026-06-19 (Designing #3 → Data/Tasks #3: refined Data section per Q8–Q12)

Read JXP's answers to Q8–Q12 and edited the Data section accordingly:
- **GLORIA (Q8):** JXP will source/download the data; kept the "not yet
  downloaded locally" note and proceeded without it.
- **IOCCG (Q9):** dropped from scope (sets are dated) — removed its table row and
  subsection; moved it to "Out of scope for now".
- **PACE (Q10):** specified the source as the PACE validation team's released
  validation product (updated table + subsection).
- **L23 (Q11):** made the `X=2` (Raman-only) exclusion explicit in the L23
  subsection.
- **GLORIA metric (Q12):** added an explicit caveat that `aCDOM(440)` is CDOM-only
  vs. retrieved combined `a_dg`, to be flagged in reports.

Did **not** bump the version (task #3 didn't request it; these are same-day
refinements to the v0.2 Data section — header stays v0.2, 2026-06-19). Wrote one
new question (Q13: which specific PACE release/DOI/SeaBASS query, since I'm not
aware of a single consolidated PACE validation product yet) to the Conversation.

### 2026-06-20 (Designing #4 → Analysis/Tasks #1: examined BING, wrote analysis plan)

First applied JXP's Q13 answer (don't include PACE for now): removed PACE from
the Data section's summary table and subsection, and added it under "Out of scope
for now" in `IOPtics_design.md`.

Then executed Analysis/Tasks #1. Mapped the BING package's analysis-relevant
public API and end-to-end data flow (Rrs → models[anw,bbnw] → priors → RT[Gordon
+optional Raman/Chl-fl] → fit[chisq or MCMC/emcee] → reconstruct a/bb±unc →
stats). Verified signatures directly: `models.anw/bbnw.init_model`, model
registries (anw: Cst/Exp/ExpFix/Bricaud/ExpBricaud/.../GIOP/ExpNMF/GSM/Chase;
bbnw: Cst/Every/Pow/GSM/Lee), `parameters.standard.{expb_pow,expbf_pow,giop,gsm,
k2b}`, `rt.rrs.calc_Rrs` + `wave_dependent_gordon`, `fitting.chisq_fit.fit`,
`fitting.inference.fit_one/fit_batch/run_emcee`, `evaluate.reconstruct_from_chains
/reconstruct_chisq_fits/calc_stats`, `stats.calc_chisq/calc_ICs`, `noise.scale_
noise/add_noise`. Key insight: `fitting.l23.prep_one_l23` is the canonical
end-to-end example but is L23-specific; everything else is data-agnostic, so
IOPtics' core job is generalizing that prep into a dataset-agnostic layer feeding
the same engine.

Created a new Planning document `docs/design/IOPtics_planning.md` (v0.1) with an
**Analysis** section: A0 engine/seams table, A1 uniform AlgorithmSpec + registry,
A2 retrieval (`run_algorithm`/sweep), A3 uniform uncertainties (MCMC percentiles
vs. least-squares covariance + noise), A4 metrics/diagnostics/QC, A5 figures/
tables, A6 reports, and a tentative module layout. Used an Explore subagent to
accelerate the API mapping. Wrote 5 questions (A–E: planning doc location, default
fit method, v1 algorithm set, where the generalized prep lives, whether to draft
Metrics next) to the Q&A section.

### 2026-06-20 (Designing #5 → Analysis/Tasks #2: moved Analysis into design doc, removed Planning doc)

Read JXP's Q&A answers and executed Analysis/Tasks #2. Per answer A, the analysis
content belongs in `IOPtics_design.md` (not a separate Planning doc), so I:
- Added a design-level **Analysis** section to `docs/design/IOPtics_design.md`
  (pipeline overview; data preparation; IOP retrieval; uncertainty quantification;
  metrics & diagnostics; figures/tables/reports) — kept at the design altitude
  with no code/function/module specifics, per the doc's no-code-recommendations
  convention.
- Reflected the decisions: first-pass uses least-squares with MCMC reserved for a
  subset (answer B); algorithms are **built out one at a time** via a growing
  registry (answer C); stated that a defined data load/prep **process** is needed
  without specifying where it lives (answer D); deferred Metrics definitions
  (answer E).
- **Removed** the standalone `docs/design/IOPtics_planning.md` (answer A).
- Bumped the design document to **v0.3**, dated 2026-06-20.
- Wrote 2 new questions (F: which algorithm to seed the registry — I suggest
  `expb_pow`; G: what Rrs noise model to assume for the synthetic L23 first-pass)
  to the Q&A section.

### 2026-06-20 (Designing #6 → Analysis/Tasks #3: reflected F/G, added provenance requirement)

Read JXP's answers to F (start with `expb_pow`) and G (assume a PACE-like sensor
noise model). Executed Analysis/Tasks #3 on `docs/design/IOPtics_design.md`:
- IOP retrieval subsection now names **`expb_pow`** as the first algorithm built
  out, with GIOP/GSM to follow.
- Data preparation subsection now states the synthetic **L23 first-pass assumes a
  PACE-like sensor noise model** so uncertainties/closure thresholds are realistic.
- Added a new **Provenance & reproducibility** subsection (and a cross-cutting
  note in the pipeline overview): every result must record the full algorithm
  configuration — model choices, RT options, fitting method, noise model — **and
  the priors for any Bayesian inference** — per JXP's requested additions.

Did not bump the version (task #3 didn't request it; stays v0.3) and asked about
it explicitly (Q J). Wrote 3 new questions (H: which PACE noise spec; I:
provenance record format/location; J: version-bump policy) to the Q&A section.

### 2026-06-20 (Designing #7 → Analysis/Tasks #4: reflected H/I/J)

Read JXP's answers to H/I/J and executed Analysis/Tasks #4 on
`docs/design/IOPtics_design.md`:
- Data preparation now specifies the L23 first-pass noise model as the
  **`ocpy.satellites.pace`** PACE model (answer H; verified the module exists at
  `ocpy/satellites/pace.py`).
- Provenance & reproducibility subsection now states the record is written in
  **YAML/JSON** and stored **alongside the results table** (answer I).
- Per answer J (bump whenever sensible), bumped the design doc to **v0.4**.
- Wrote 1 new question (K: whether to add a consolidated "Open questions /
  deferred decisions" section) to the Q&A. Also saved a feedback memory about the
  version-bump policy.

### 2026-06-20 (Designing #8 → Analysis/Tasks #5: added Open Questions section)

Read JXP's answer to K (yes, consolidate). Added an **Open Questions & Deferred
Decisions** section to `docs/design/IOPtics_design.md` — a table tracking the six
postponed items in one place: (1) canonical IOP-component scheme, (2) PACE
validation dataset, (3) IOCCG synthetic dataset, (4) Metrics section, (5)
Validation section, (6) GLORIA data acquisition. This complements the existing
inline "(see Open Questions)" reference in the Data section. Bumped the design doc
to **v0.5**. (Task #5 did not request new questions, so none were added.)

### 2026-06-20 (Designing #9 → Metrics/Tasks #1: drafted the Metrics section)

Executed Metrics/Tasks #1. Read `docs/PDFs/bing.pdf` (Prochaska & Frouin 2025) and
`docs/PDFs/erickson2023.pdf` (Erickson et al. 2023, "Bayesian approach to a
generalized IOP model", Optics Express) via two parallel subagents to extract
exactly which metrics each uses. Key takeaways folded into the plan:
- BING: reduced χ²ᵥ as fit diagnostic (≈1 good, <1 overfit); AIC/BIC/ΔBIC model
  selection (ΔBIC<0 favors complex; CDF over dataset); bias/MAE/RMS accuracy at a
  single wavelength (aph(440), bb_nw(440)), log–log; 68%/99% credible intervals +
  Nσ detection / upper limits; corner plots for degeneracy; **no Taylor/Target,
  no r²/regression, no formal coverage test**.
- Erickson: multiplicative **log-space MAE & bias** (Eqs. 13–14, Seegers 2018);
  χ²_rel / χ²_Bayes objectives; **dual-sided fit-quality window** (reproduce Rrs
  to ~5% measurement noise, but not below → overfitting; >25% MAE = QC fail);
  ratio histograms; "wins" head-to-head ranking; per-variable/per-wavelength
  stratification.

Wrote a new **Metrics** section in `IOPtics_design.md` (conventions; 1 retrieval
accuracy vs truth; 2 internal closure/fit quality; 3 model selection; 4
uncertainty assessment incl. a *new* formal coverage test; 5 cross-algorithm
comparison/wins; 6 diagnostic figures; handling non-uniformity). Improved on the
papers by reporting metrics **spectrally** (not just one wavelength) and adding
r²/regression and coverage. Updated the Open Questions table (Metrics → Drafted)
and bumped the design doc to **v0.6**. Wrote 4 questions (L: adopt Seegers
log-space MAE/bias; M: include Taylor/Target; N: formal coverage test + levels;
O: reference wavelengths) to the Q&A section.

### 2026-06-20 (Designing #10 → Metrics/Tasks #2: refined Metrics per L–O)

Read JXP's answers (L–O) and edited the Metrics section of `IOPtics_design.md`:
- L: noted the log-space MAE/bias battery is the **initial** set and will grow.
- N: set the uncertainty **coverage test at 68% and 95%**.
- O: added a **redder backscatter reference wavelength (670 nm)** alongside 555 nm
  (absorption stays 440/443 nm).
- M: JXP asked what Taylor/Target diagrams are before deciding — left them **out**
  of the standard set, gave concise definitions + primary references (Taylor 2001
  JGR; Jolliff et al. 2009 J. Mar. Sys.) in the Q&A, and asked Q P for the
  decision.
Updated the Open Questions table (Metrics row → Drafted v0.7; coverage/MAE
adopted; Taylor/Target pending) and bumped the design doc to **v0.7**.

### 2026-06-20 (Designing #11 → Metrics/Tasks #3: added Taylor + Target diagrams)

Read JXP's answer to P (add both). Added **Taylor (Taylor 2001)** and **Target
(Jolliff et al. 2009)** diagrams to the Metrics "Diagnostic figures" subsection of
`IOPtics_design.md`, with one-line descriptions of what each conveys. Updated the
Open Questions table (Metrics → Drafted v0.8, Taylor/Target now resolved) and
bumped the design doc to **v0.8**. (Task #3 requested no new questions, so none
added.)

### 2026-06-20 (Designing #12 → Reporting/Tasks #1: drafted the Reporting section)

Executed Reporting/Tasks #1. Drawing on the reporting practice in BING (Prochaska
& Frouin 2025) and Erickson et al. (2023) — both already extracted in the Metrics
work — wrote a new **Reporting** section in `IOPtics_design.md` (inserted after
Metrics): artifacts (machine-readable results table + YAML/JSON provenance,
the standard figure set incl. Taylor/Target and spatial maps, accuracy/QC tables);
three report types (per-algorithm scorecard, cross-algorithm comparison as the
headline deliverable, per-dataset); `.rst` → readthedocs + GitHub delivery;
publication-ready figures; and reproducibility stamping (design-doc/registry/
dataset/commit versions) so every report regenerates from one sweep. Kept it at
design altitude (build automation, site layout, styling left to implementation).
Bumped the design doc to **v0.9**. Wrote 3 questions (Q: CI auto-build vs.
on-demand; R: single accumulating site / dashboard landing page vs. per-sweep; S:
persistent leaderboard for the cross-algorithm comparison) to the Q&A section.

### 2026-06-20 (Designing #13 → Reporting/Tasks #2: refined Reporting; added Leaderboard + Bokeh)

Read JXP's answers (Q/R/S) and edited the Reporting section of `IOPtics_design.md`:
- Q: reports are generated **on demand** via a standard report template (not CI
  auto-built on every commit).
- R: a **single, accumulating readthedocs.io site** hosts all reports.
- S: added a **Leaderboard** subsection — persistent ranking by headline metrics
  across datasets that accumulates/updates as algorithms are added one-by-one.
- Requested addition: an **Interactive figures** subsection — interactive **Bokeh**
  figures letting the user select an algorithm (and dataset/stratum) to inspect
  results, embedded in the readthedocs site.
Bumped the design doc to **v0.10**. Wrote 1 question (T: whether standalone/static
BokehJS interactivity is sufficient given readthedocs can't run `bokeh serve`, vs.
needing a live server with separate hosting) to the Q&A section.
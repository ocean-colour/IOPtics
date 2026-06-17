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
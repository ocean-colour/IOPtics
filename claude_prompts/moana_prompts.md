# IOPtics — Explore MOANA

## Goal

Explore the NASA MOANA algorithm.  We will attempt to reproduce the model and tests its accuracy.

## Conventions

- `ocean14`; JXP runs git; after each step run `pytest -q` where relevant, Q&A, Log.
- Run via the env interpreter directly
  (`/home/xavier/miniforge3/envs/ocean14/bin/python …`); `conda activate` fails
  non-interactively. This is a **Tier-2** operation — it needs the `$OS_COLOR`
  data tree (L23) mounted; do **not** unset `$OS_COLOR` here.
- `report`/`plotting` need matplotlib (`Agg` is fine headless) + Bokeh + Sphinx.

## Context

- Design docs in `docs/design`
- The paper that developed the algorithm initially: `papers/lange2020.pdf`
- Papers and websites on the Atlantic Meridional Transect 24 (AMT24).  

*(Added 2026-08-01 by prompt 1. All DOIs below were resolved and verified — via
`doi.org`, or via the Crossref/DataCite APIs where the publisher blocks
automated requests. Items marked **key** are load-bearing for reproducing
MOANA.)*

### MOANA — the operational NASA PACE algorithm

**MOANA = "Multiple Ordination ANAlysis"** (ATBD title; the Earthdata product
titles render it "Multi-Ordination ANAlysis"). *Moana* is also "ocean" in
Hawaiian. It is the first operational PACE Phytoplankton Community Composition
(PCC) product to exploit OCI's full spectral resolution, and it is the Lange+2020
algorithm essentially unchanged.

- **key** — **MOANA ATBD v1.2** (16 Dec 2024), P. K. Lange, P. J. Werdell,
  I. Cetinić; eds. I. Cetinić & G. Wang. NASA Algorithm Publication Tool.
  DOI [10.5067/0AV5267G5C77](https://doi.org/10.5067/0AV5267G5C77) ·
  landing page <https://www.earthdata.nasa.gov/apt/documents/moana/v1.0> ·
  PDF <https://oceancolor.gsfc.nasa.gov/files/atbd/atbd-obdaac-phytoplankton-groups-MOANA.pdf>.
  **Downloaded to `papers/moana_atbd.pdf`.** This is the single most useful new
  document: it gives the operational recipe *and tabulates the 25 regression
  coefficients* (its p. 5), which the paper does not.
- **key** — OCSSW reference implementation `src/l2gen/get_Cpicophyt.c`
  (author Minwei Zhang, created 2023-09-29). The Ocean Color doxygen pages have
  since been retired (they 301 to the OB.DAAC landing page); a working snapshot is
  <http://web.archive.org/web/20250712185034/https://oceancolor.gsfc.nasa.gov/docs/ocssw/get__Cpicophyt_8c_source.html>.
  It reads the PCA loadings from `$OCDATAROOT/common/pca_picophyto.h5`
  (datasets `component` [nwave × npc] and `wavelength` [int, nm]) and the
  regression coefficients from `$OCDATAROOT/common/picophyt.json`
  (keys `npc`, `pro_coef`, `syn_coef`, `apeuk_coef`). *Neither of those two data
  files is published in the literature* — see Q&A #1.
- PACE data-products overview (MOANA section, POC Ivona Cetinić):
  <https://pace.oceansciences.org/data.htm>
- Products — PACE OCI Regional Mapped MOANA, cell abundances [cells mL⁻¹],
  2024-03-05 to present:
  - L3M v3.1 DOI [10.5067/PACE/OCI/L3M/MOANA/3.1](https://doi.org/10.5067/PACE/OCI/L3M/MOANA/3.1)
  - L4M v3.1 DOI [10.5067/PACE/OCI/L4M/MOANA/3.1](https://doi.org/10.5067/PACE/OCI/L4M/MOANA/3.1)
  - v3.2 and a v3.2 NRT stream are listed in the Earthdata catalog
    (`ob-cloud-pace-oci-l4m-moana-3.2`, `…-nrt-3.2`) but their DOIs were **not yet
    registered** as of 2026-07-31, so cite v3.1 for now.
  - **Corrected 2026-08-01 (prompt 3), after opening a real granule:** the CMR
    collections that actually exist are **`PACE_OCI_L4M_MOANA` v3.2** and
    `PACE_OCI_L4M_MOANA_NRT` v3.2 — there is **no** L3M MOANA collection in CMR
    despite the catalog page above. And the in-file variable names are the
    misspelled L2-style **`prococcus_moana`, `syncoccus_moana`, `picoeuk_moana`**,
    *not* the `prochlorococcus_moana` / `synechococcus_moana` the Earthdata
    catalog page advertises. Use the in-file names. The Rrs input lives in
    **`PACE_OCI_L3M_AOP` v3.2** (variable `Rrs`, 172 OCI wavelengths spanning
    346–719 nm, so 414–660 is fully covered).
- **Validation status (important):** the ATBD states plainly that *"PACE OCI MOANA
  products have not been validated yet."* Operational validation is against
  SeaBASS cell counts following Bailey & Werdell (2006). The only published skill
  numbers are Lange+2020 Tables 1–3 (AMT in-situ and Aqua-MODIS).
- Cetinić, I., et al. (2024). "Phytoplankton composition from sPACE:
  Requirements, opportunities, and challenges." *Remote Sensing of Environment*
  302, 113964. DOI [10.1016/j.rse.2023.113964](https://doi.org/10.1016/j.rse.2023.113964)
  — the PACE PCC roadmap; the ATBD points here for background.
- Mouw, C. B., et al. (2017). "A Consumer's Guide to Satellite Remote Sensing of
  Multiple Phytoplankton Groups in the Global Ocean." *Frontiers in Marine
  Science* 4, 41. DOI [10.3389/fmars.2017.00041](https://doi.org/10.3389/fmars.2017.00041)

Method lineage the ATBD credits for the principal-component-regression approach:

- Craig, S. E., et al. (2012). *Remote Sensing of Environment* 119, 72–83.
  DOI [10.1016/j.rse.2011.12.007](https://doi.org/10.1016/j.rse.2011.12.007)
- Bracher, A., et al. (2015). *Ocean Science* 11, 139–158.
  DOI [10.5194/os-11-139-2015](https://doi.org/10.5194/os-11-139-2015)
- Seegers, B. N., et al. (2018). *Optics Express* 26, 7404–7422.
  DOI [10.1364/OE.26.007404](https://doi.org/10.1364/OE.26.007404) — the
  log-space bias/MAE metrics Lange+2020 uses (already in the IOPtics design doc).
- Bailey, S. W. & Werdell, P. J. (2006). *Remote Sensing of Environment* 102,
  12–23. DOI [10.1016/j.rse.2006.01.015](https://doi.org/10.1016/j.rse.2006.01.015)
  — the satellite/in-situ matchup protocol.
- Werdell, P. J., et al. (2003). "Unique data repository facilitates ocean color
  satellite validation." *Eos* 84(38), 377–387.
  DOI [10.1029/2003EO380001](https://doi.org/10.1029/2003EO380001) — SeaBASS.

### AMT24 — the MOANA training cruise

AMT24 = RRS *James Clark Ross*, cruise **JR20140922 / JR303**, Immingham (UK) →
Stanley (Falkland Islands), 22 Sep – 2 Nov 2014 (Lange+2020 uses the
30 Sep – 1 Nov window); principal scientist Tim Smyth (PML); 70 CTD stations plus
30-minute underway sampling across the South Atlantic Gyre front (25–45°S).

- AMT programme site <https://amt-uk.org/>, cruise page
  <https://www.amt-uk.org/Cruises/AMT24>, data page <https://amt-uk.org/data/>
- BODC cruise summary report (JR20140922)
  <https://www.bodc.ac.uk/resources/inventories/cruise_inventory/report/15038/>
- **key** — **AMT24 flow-cytometric cell abundances** (the MOANA training truth):
  Tarran, G. A. & Zubkov, M. V. (2020), BODC/NOC/NERC.
  DOI [10.5285/a2104adc-e98f-6789-e053-6c86abc0d557](https://doi.org/10.5285/a2104adc-e98f-6789-e053-6c86abc0d557)
  (shortDOI `10/ds9g`). *Prochlorococcus*, *Synechococcus*, pico- and
  eukaryotic phytoplankton by FACSort, 200 m → surface.
- Flow-cytometry datasets for the five **validation** cruises used in
  Lange+2020 §2.2 (all BODC, 2020):
  | Cruise | DOI | shortDOI |
  |---|---|---|
  | AMT20 (JC053, Oct–Nov 2010) | [10.5285/a2104adc-e993-6789-e053-6c86abc0d557](https://doi.org/10.5285/a2104adc-e993-6789-e053-6c86abc0d557) | `10/dsrh` |
  | AMT22 (JC079, Oct–Nov 2012) | [10.5285/a2104adc-e991-6789-e053-6c86abc0d557](https://doi.org/10.5285/a2104adc-e991-6789-e053-6c86abc0d557) | `10/dsrm` |
  | AMT23 (JR300, Oct–Nov 2013) | [10.5285/a2104adc-e990-6789-e053-6c86abc0d557](https://doi.org/10.5285/a2104adc-e990-6789-e053-6c86abc0d557) | `10/ds7f` |
  | AMT25 (JR15001, Sep–Nov 2015) | [10.5285/a2104adc-e98e-6789-e053-6c86abc0d557](https://doi.org/10.5285/a2104adc-e98e-6789-e053-6c86abc0d557) | `10/dq4r` |
  | AMT28 (JR18001, Sep–Oct 2018) | [10.5285/a147c314-688b-55e9-e053-6c86abc0dc81](https://doi.org/10.5285/a147c314-688b-55e9-e053-6c86abc0dc81) | `10/dqwc` |
- Parent BODC collection, "Biological and Hydrographic station data collected
  during the AMT programme (1995–)", AMT13→AMT30:
  DOI [10.5285/41479c42-4dfb-4da9-be97-4c532ce13922](https://doi.org/10.5285/41479c42-4dfb-4da9-be97-4c532ce13922)
- Rees, A. P., et al. (2017). "The Atlantic Meridional Transect programme
  (1995–2016)." *Progress in Oceanography* 158, 3–18.
  DOI [10.1016/j.pocean.2017.05.004](https://doi.org/10.1016/j.pocean.2017.05.004)
- Rees, A., Robinson, C., Smyth, T., Aiken, J., et al. (2015). "20 Years of the
  Atlantic Meridional Transect — AMT." *Limnology and Oceanography Bulletin* 24,
  101–107. DOI [10.1002/lob.10069](https://doi.org/10.1002/lob.10069)

### AMT bio-optics — directly useful to IOPtics

- **key** — Jordan, T. M., Dall'Olmo, G., Tilstone, G., Brewin, R. J. W.,
  Nencioli, F., Airs, R., Thomas, C. S., Schlüter, L. (2025). "A compilation of
  surface inherent optical properties and phytoplankton pigment concentrations
  from the Atlantic Meridional Transect." *Earth System Science Data* 17,
  493–516. DOI [10.5194/essd-17-493-2025](https://doi.org/10.5194/essd-17-493-2025).
  Data: Zenodo DOI [10.5281/zenodo.12527954](https://doi.org/10.5281/zenodo.12527954)
  and SeaBASS <https://seabass.gsfc.nasa.gov/archive/PML/AMT>.
  Underway particulate absorption / scattering / attenuation (~400–720 nm,
  ~270k hyperspectral + ~40k multispectral records) plus HPLC pigments for
  **nine cruises including AMT24** — i.e. real in-situ IOPs on the very cruise
  that trained MOANA. This is a candidate new IOPtics dataset in its own right.
- Brewin, R. J. W., Dall'Olmo, G., Pardo, S., van Dongen-Vogels, V., Boss, E. S.
  (2016). "Underway spectrophotometry along the Atlantic Meridional Transect
  reveals high performance in satellite chlorophyll retrievals." *Remote Sensing
  of Environment* 183, 82–97.
  DOI [10.1016/j.rse.2016.05.005](https://doi.org/10.1016/j.rse.2016.05.005)
  — Lange+2020 refs 42/43; the source of the HyperSAS Rrs processing protocol.
- **key for noise** — Lin, J., Dall'Olmo, G., Tilstone, G. H., et al. (2022).
  "Derivation of uncertainty budgets for continuous above-water radiometric
  measurements along an Atlantic Meridional Transect." *Optics Express* 30,
  45648. DOI [10.1364/OE.470994](https://doi.org/10.1364/OE.470994)
  — per-band Rrs uncertainty for exactly this instrument/platform, i.e. the
  honest `varRrs` for an AMT fit instead of a flat 5%.
- Alikas, K., Vabson, V., Ansko, I., Tilstone, G. H., et al. (2020). "Comparison
  of Above-Water Seabird and TriOS Radiometers along an Atlantic Meridional
  Transect." *Remote Sensing* 12, 1669.
  DOI [10.3390/rs12101669](https://doi.org/10.3390/rs12101669)
- Pardo, S., Tilstone, G. H., Brewin, R. J. W., et al. (2023). "Radiometric
  assessment of OLCI, VIIRS, and MODIS using fiducial reference measurements
  along the Atlantic Meridional Transect." *Remote Sensing of Environment* 299,
  113844. DOI [10.1016/j.rse.2023.113844](https://doi.org/10.1016/j.rse.2023.113844)
- Brotas, V., Ferreira, A., Veloso, V., et al. (2023). "Assessing phytoplankton
  community composition in the Atlantic Ocean from in situ and satellite
  observations." *Frontiers in Marine Science* 10, 1229692.
  DOI [10.3389/fmars.2023.1229692](https://doi.org/10.3389/fmars.2023.1229692)
  — validates satellite size classes against AMT flow-cytometric cell counts;
  the closest published analogue to what we want to do with MOANA.
- Lange, P. K., Brewin, R. J. W., Dall'Olmo, G., Tarran, G. A., et al. (2018).
  "Scratching Beneath the Surface: A Model to Predict the Vertical Distribution
  of *Prochlorococcus* Using Remote Sensing." *Remote Sensing* 10, 847.
  DOI [10.3390/rs10060847](https://doi.org/10.3390/rs10060847)
  — the same author's precursor; relevant because MOANA is surface-only
  (top 10 m) by construction.

## Coding

Here are guidelines for coding:

- Use Python
- Add inline comments to explain the effort
- Reuse existing code when possible
- Use methods, not classes
- Place MOANA relaated code in the `ioptics/moana/` folder.
- Use matplotlib or seaborn for plotting
- Place import statements at the top of the file.
- Include a description of inputs/outputs in the doc string of all methods

## Prompts

1. **Context**.  Please read all of the files listed in the Context section above.  Then search the NASA PACE websites for any discussion of the MOANA algorithm which was developed for the PACE mission from the Lange+2020 paper. Also search for literature that discusses the AMT24 and its data. If you find any, add them to the Context section above; include DOIs. If you have any questions, please write them in the Q&A section below.  Log your work.  Use Fable if you can.

2. **Existing code**.  It is possible that the MOANA code is available on the NASA PACE website.  Please search for it and report back in the Reports section below.  You may need to download the (very) large C source code that NASA Ocean Color provides.  If you have any questions, please write them in the Q&A section below.  Log your work.  Use Fable if you can.

3. **Answers**.  I have answered the questions in the Q&A section below.  Please review them and proceed accordingly.  Use Fable if you can. Log your work.

4. **MOANA Report**.  I have answered the latest round of Q&A; read them.  Now that you have all of these papers and code, generate a report -- `reports/MOANA_Claude_Report.md` with your complete understanding of the MOANA algorithm.  You should include any of the inconsistencies you have identified in your exploration.  Be sure to explain how it works.  And, explain how you'd improve it. Use Fable if you can. Log your work.  If you have any additional questions, please write them in the Q&A section below.

5. **MOANA Report 2**.  I have answered the latest round of Q&A; read them and update the report accordingly.  Use Fable if you can. Log your work.  If you have any additional questions, please write them in the Q&A section below.

6. **Data**.  We are going to reproduce the MOANA algorithm using the AMT24 data.  Please download the data from the AMT24 website and put it in the folder `$OS_COLOR/AMT24`.  If you can't find it, provide a list of the places you searched.  If you have any questions, please write them in the Q&A section below.  Log your work.  Use Fable if you can.

7. **Design**.  Let us generate a design doc for the MOANA algorithm.  We will write it in the file `docs/design/moana_design.md`.  This doc will both describe the algorithm and our approach to coding it.  We will use the files in the Context section above to help us.  Before proceeding, if you have any questions, please write them in the Q&A section below.  Log your work.  Use Fable if you can.

8. **Code**.  Let us generate the code for the MOANA algorithm.  We will write it in the file `code/moana.py`.  This code will implement the algorithm described in the Design doc.  Before proceeding, if you have any questions, please write them in the Q&A section below.  Log your work.  Use Fable if you can.

9. **Test**.  Let us generate the tests for the MOANA algorithm.  We will write it in the file `tests/moana_tests.py`.  This code will test the algorithm described in the Design doc.  Before proceeding, if you have any questions, please write them in the Q&A section below.  Log your work.  Use Fable if you can.

10. **Validation**.  Let us generate the validation for the MOANA algorithm.  We will write it in the file `validation/moana_validation.py`.  This code will validate the algorithm described in the Design doc.  Our goal is to apply MOANA on held out data, ideally from a cruise distinct from AMT24. Before proceeding, if you have any questions, please write them in the Q&A section below.  Log your work.  Use Fable if you can.

## Q&A

### From prompt 1 (2026-08-01) — Claude

1. **The training PCA loadings are the one hard blocker.** Neither Lange+2020 nor
   the ATBD publishes the loading matrix `V(λ, i)`. Operationally it lives in
   `$OCDATAROOT/common/pca_picophyto.h5` and the regression coefficients in
   `$OCDATAROOT/common/picophyt.json` — two OCSSW *data* files, not source.
   Without `V` we can apply MOANA only in "published-coefficients" mode and only
   if we can get that file. Which route do you want?
   (a) install OCSSW/SeaDAS and pull the two files from `$OCDATAROOT/common`
   (this is prompt 2's territory, so I did not start it);
   (b) email Lange / Cetinić / Minwei Zhang for `pca_picophyto.h5`;
   (c) re-derive the PCA ourselves from AMT24 — scientifically the most
   satisfying, and it makes "reproduce the model" literal, but it needs the
   AMT24 hyperspectral Rrs (see #2) and will not reproduce NASA's coefficients
   exactly (sign/ordering of eigenvectors is arbitrary).
>A. We will install OCSSW/SeaDAS and pull the two files from `$OCDATAROOT/common`.

2. **Where is the AMT24 hyperspectral Rrs?** The *cell counts* have a clean BODC
   DOI. I could **not** confirm a public archive for the AMT24 HyperSAS Rrs
   (414–660 nm at 2 nm) that trained the PCA. Jordan+2025 puts AMT24 *IOPs and
   pigments* on SeaBASS/Zenodo but that is `ap`/`cp`/HPLC, **not** Rrs. Prompt 3
   says "download the data from the AMT24 website" — is it fine if I spend the
   effort digging through SeaBASS `PML/AMT` and BODC for the radiometry, or do you
   already know where the Rrs lives / would you rather just ask PML?
>A. Yes, please spend the effort digging through SeaBASS `PML/AMT` and BODC for the radiometry.

3. **Scope — how does MOANA sit inside IOPtics?** This matters before prompt 4
   (design doc). MOANA is *not* an IOP algorithm: it outputs cell abundances, has
   no `a(λ)`/`bb(λ)`, no BING forward model, no χ² Rrs closure, no free parameters
   to count, so ~none of the existing `ioptics.metrics` battery (§2 closure, §3
   AIC/BIC/ΔBIC, §4 coverage) applies. Its accuracy metrics (log-space bias, MAE,
   R²) *do* already match ours. Do you want it as
   (a) a separate "empirical PCC products" track alongside the IOP track,
   (b) a genuine `AlgorithmSpec` variant that bypasses the BING wrapper, or
   (c) purely exploratory under `papers/moana/` with no `ioptics/` changes yet?
   Prompts 5–7 point at bare `code/`, `tests/`, `validation/` directories that
   don't exist in this repo and sit outside the `ioptics/` package layout — I'd
   like to confirm that's deliberate rather than shorthand.
>A. It is separate from the IOP track, and we will not be evaluating it against the IOP track.  We will be exploring it separatlely and eventually will write a report with our main findings.

4. **What is the primary validation target?** Ranked candidates:
   (i) reproduce Lange+2020 Tables 1–2 on AMT24 (needs #1 and #2);
   (ii) apply the published coefficients to AMT20/22/23/25/28 — genuinely
   held-out cruises, DOIs now in Context, which is exactly what prompt 7 asks;
   (iii) validate the *operational* PACE OCI MOANA L3/L4 product against SeaBASS
   cell counts (note the ATBD admits this has never been done — a real, publishable
   gap);
   (iv) run MOANA on L23 synthetic Rrs. I'd argue (ii) is the best first target
   and (iv) is nearly meaningless — see #5.
>A. We will do (i), (ii) and (iii) as best we can.

5. **SST, and why L23 may be a dead end for MOANA.** The *Prochlorococcus*
   equation needs `log10(SST)`, and operationally that SST is the PACE reference
   field (GHRSST CMC L4). L23 is synthetic and has **no SST at all**, so the Pro
   model cannot be run on L23 without inventing a temperature — and *Synechococcus*
   / picoeukaryotes would be extrapolating a PCA trained on real Atlantic spectra
   onto Hydrolight spectra. Do you agree we skip L23 for MOANA? And for real
   cruises, do we have GHRSST/CMC under `$OS_COLOR`, or should I add an `ocpy`
   loader?
>A. Yes, we will skip L23 for MOANA.

6. **A discrepancy to resolve before coding.** The ATBD writes a *different,
   non-contiguous* PC subset per taxon — Pro: `U1,U2,U6,U17`; Syn:
   `U1,U2,U3,U5,U8,U9,U10,U11,U12,U13`; picoeuk: `U2,U3,U4,U5,U10,U13,U15` — but
   `get_Cpicophyt.c` multiplies coefficient `i` by PC `i` **contiguously** over the
   first `npc` PCs. The only way both are true is if `picophyt.json` zero-pads the
   unused slots. Relatedly, the paper says 14 PCs were retained yet the indices run
   to 17. Do we (a) treat the ATBD table as authoritative and zero-pad, or (b) hold
   until we can actually read `picophyt.json`? I lean (b), since it also
   independently checks the coefficient values.
>A. Let's do (b)

7. **Which wavelength grid?** The ATBD is internally inconsistent: its abstract
   says the algorithm needs valid Rrs over **395–705 nm**, while its Mathematical
   Theory section (and Lange+2020) says **414–660 nm at 2 nm** = 124 bands. I
   propose we implement 414–660 @ 2 nm because that is what the PCA was trained on,
   and treat 395–705 as a mere data-availability screen. Confirm?
>A. We will implement 414–660 @ 2 nm.

8. Minor but worth deciding early: the OCSSW code standardizes each spectrum with
   the **sample** standard deviation (N−1 denominator). Lange+2020 Eq. 3 just says
   "standard deviation". Since the scores scale inversely with this, N vs N−1 shifts
   every retrieval slightly. I'll match OCSSW (N−1) unless you object.
>A. We will match OCSSW (N−1).

### From prompt 2 (2026-08-01) — Claude

*(Questions 1, 6, 7 and 8 above are now settled as fact by the OCSSW data files —
see the prompt-2 report. Q&A #1's blocker is gone entirely: we have the loadings.)*

9. **The one that matters.** The operational `picophyt.json` puts the last
   Prochlorococcus coefficient on **PC7** (ATBD says U17) and the last
   *Synechococcus* coefficient on **PC16** (ATBD says U13); all values are
   identical and picoeukaryotes agree exactly. The ATBD's assignment uses **14
   distinct PCs** across the three taxa — matching Lange+2020's "14 PCs survived
   the significance cut" — while the JSON uses **15**. That is decent evidence the
   ATBD is faithful and the operational LUT has two coefficients in the wrong
   slots, i.e. the shipping PACE products may not be the published algorithm.
   I propose we (a) implement both mappings behind a flag, (b) settle it
   empirically by reproducing a real PACE MOANA granule, and (c) email
   Lange/Cetinić/Zhang once we have that evidence in hand. Do you want to be the
   one to make that contact, and should we hold off publishing the discrepancy
   until they reply?
>A. Yes, let's do (a) and (b) and I will make the contact later.

10. **Bit-exactness check before AMT24?** I'd like to download one PACE OCI L3M Rrs
    granule plus its matching L3M MOANA granule and verify our reimplementation
    reproduces NASA's three fields pixel-for-pixel. It is the cleanest possible
    test of our transcription *and* it settles #9. It needs an Earthdata login for
    `earthaccess` — do you have credentials set up (`~/.netrc` or
    `EARTHDATA_USERNAME`/`_PASSWORD`), or should I plan around that?
>A. I have credentials set up (`~/.netrc`) 

11. **How should clipped zeros be treated?** OCSSW silently sets negative
    Prochlorococcus to 0 rather than flagging it, and casts all three products to
    truncated `int32`. Zeros are fatal to log-space bias/MAE. Do we (a) keep NASA's
    behaviour exactly and mask zeros at the metrics stage, or (b) retain the raw
    float value and record the clip as a QC flag, so we can report how often MOANA
    goes unphysical? I lean (b) for our own runs, with (a) available for
    bit-comparison against NASA.
>A. Let's do (b)

12. **Where do the two LUT files live for us?** They are currently at
    `$OS_COLOR/ocssw/share/common/{pca_picophyto.h5,picophyt.json}` — the canonical
    OCSSW location. Since they are 24 KB and 390 bytes and are the crux of the whole
    exercise, do you want copies committed into the repo (e.g. `ioptics/moana/data/`)
    for reproducibility, or should the code read them from `$OCDATAROOT`/`$OS_COLOR`
    and keep the repo data-free as the design doc prefers?
>A. Yes, copy into the repo (`ioptics/data/moana/`) for reproducibility.

### From prompt 3 (2026-08-01) — Claude

*(All 12 answers above are acted on; see the prompt-3 report. The unanswered half of
#5 — where GHRSST SST comes from — is now resolved: `CMC0.1deg-CMC-L4-GLOB-v3.0` is
reachable via `earthaccess` at 0.1°, matching the MOANA grid. No `ocpy` loader
needed.)*

13. **The 18 % clipping problem may be the most interesting result we have.**
    *Prochlorococcus* is exactly 0 in 18.0 % of real ocean retrievals in the one
    day I examined, because the regression goes negative and OCSSW silently clamps
    it; *Synechococcus* is 0 in another 8.9 % from integer truncation. For
    validation targets (i)–(iii), how should those be treated? Options: (a) exclude
    them (cleanest, but flatters the algorithm by hiding its failures); (b) treat
    them as **censored data / upper limits**, which is defensible and which the BING
    paper already has machinery for; (c) keep them as zeros and report a separate
    "fraction unphysical" statistic alongside bias/MAE. I lean (b) **and** (c)
    together — report the failure rate as a headline number, since a fifth of the
    field going unphysical is arguably more important than the MAE of the
    remainder.
>A. (b) and (c) together.

14. **How hard do we push the product-level defects?** The land-as-254 encoding,
    the `INT32_MIN` pixels, and the unenforced `valid_max` (picoeukaryotes 68× over)
    are defects in a shipping NASA product, not in the science. They belong in the
    final report, but do you want them (a) as a prominent section — they are
    genuinely useful to the community and to OBPG — or (b) as an appendix, keeping
    the report focused on algorithm accuracy? Also: should I report the land-254
    trap to OBPG, or does that go with your Q&A #9 contact?
>A. (b).  Remind me to include this when I reach out to them.

15. **Matchup design for target (iii).** Since there is no L3M MOANA, the
    operational validation has to use L4M composites (daily / 8-day / monthly).
    Bailey & Werdell (2006) — the protocol the ATBD names — is designed around L2
    granules with a 5×5 box and strict time windows, which does not map cleanly onto
    a daily 0.1° composite. Do we (a) use daily L4M and accept the looser matchup,
    (b) run `l2gen`/`l3gen` ourselves from L2 AOP to make true L2 MOANA and follow
    Bailey & Werdell properly, or (c) simply document the mismatch and use daily
    L4M? (b) is the rigorous option and OCSSW is now installed, but it is
    substantially more work.
>A. (c), and we will consider (b) later.

16. Minor: `earthaccess` is now a real dependency of the MOANA track. Add it to
    `requirements.txt`, or keep the MOANA track's dependencies separate since it is
    a side track (answer #3) and CI shouldn't need Earthdata credentials? I'd add it
    to `requirements.txt` but guard the tests with a skip when `~/.netrc` is absent,
    mirroring the existing `$OS_COLOR` skip pattern.
>A. Add it to `requirements.txt`, and guard the tests with a skip when `~/.netrc` is absent, mirroring the existing `$OS_COLOR` skip pattern.

### From prompt 4 (2026-08-01) — Claude

*(#16 is done: `earthaccess` added to `requirements.txt` with a note about the
`~/.netrc` test guard. #13, #14, #15 are reflected in the report — clipped values as
censored data plus a headline unphysical fraction; product defects in Appendix A
rather than the main argument; L4M matchups with the Bailey & Werdell departure
documented.)*

17. **Is §9 a reading list or a work plan?** The report proposes eight improvements.
    Three are cheap and would make a real contribution if we actually implemented and
    benchmarked them against stock MOANA — that would turn the report from "here is
    what MOANA is" into "here is how much better it could be", which is a much
    stronger paper. Specifically: **§9.3's out-of-domain flag** (the truncated-basis
    reconstruction residual) needs **no retraining and no new data** — we could build
    and demonstrate it on PACE granules immediately. **§9.1** (log-link GLM to kill
    the 18 % negatives) and **§9.2** (feed back the two amplitude numbers that
    standardisation discards) both require *retraining*, so they are blocked on the
    same AMT24 training data as validation target (i). Do you want me to scope any of
    these in, or is the report the deliverable and we stay descriptive?
>A. The report is the first deliverable, so we should stay descriptive.  We will then code up MOANA in Python.

18. **Should we ask NASA for the PCA eigenvalues?** They are published nowhere —
    not in the paper, not the ATBD, not even in the LUT, which ships only the
    loadings. Without them we cannot independently confirm the ">96 % on PC1" figure,
    cannot whiten or variance-weight the scores, and cannot reproduce the original
    component-selection decisions. Worth adding to your contact list alongside the
    §7.1 discrepancy?
>A. Yes, add the list of things to ask/tell NASA.

19. **Where should the report live?** It is at `reports/MOANA_Claude_Report.md` as
    instructed, with its figure in `reports/figures/` and its generator in
    `reports/scripts/` — matching the `gloria_fits_report.md` precedent. Do you also
    want it rendered into the Sphinx/readthedocs tree
    (`docs/source/reports/moana/`) like the IOP sweep reports, or does the MOANA
    track stay outside the published site until it is further along?
>A. It stays outside for now.

20. **How many more figures do you want?** The report currently has one (the PC
    loadings basis). Obvious further candidates, all cheap: a map of the PACE MOANA
    product with the land-254 and clipped-zero masks made visible; a histogram of the
    clipped fraction by taxon; and — once we run the bit-exactness test — a
    scatter of our retrieval against NASA's. Say the word and I will add them via
    `reports/scripts/moana_report_figs.py`, which is already structured for it.
>A. I like you suggestions, please add all of them.

### From prompt 5 (2026-08-01) — Claude

*(All four answers are acted on. #17 → §9 stays descriptive and says so explicitly;
#18 → new report §11 consolidates everything to ask/tell NASA, and the §10 reminder
now points at it; #19 → nothing added to the Sphinx tree; #20 → two of the three
figures are in, the third is deferred because it needs the implementation.)*

21. **The clipping turns out to be diagnosable, which changes its status.** Making
    the mask figure exposed something I had not seen from summary statistics: the
    18 % clipped *Prochlorococcus* pixels are strongly spatially organised — median
    |latitude| 47.9° vs 31.7°, 74.6 % poleward of 40°, and 4.5× the picoeukaryote
    abundance where the model fails versus where it succeeds. So the failures are
    **out-of-domain extrapolation into cold productive water**, not noise. That makes
    the §9.3 out-of-domain flag testable *without any retraining*: compute the
    truncated-basis reconstruction residual per pixel and check whether it predicts
    the clipping. Given #17 says stay descriptive, I have only written this up — but
    it is a one-afternoon experiment that would likely be a genuine contribution, and
    it needs no data we do not already have. Worth slotting in after the Python
    implementation?

22. **Should the report get a "how to read the product" section?** Between the
    land-254 trap, the unflagged clipped zeros, the unenforced `valid_max` and the
    `INT32_MIN` pixels, there is now enough for a short, practical "if you are using
    PACE MOANA, mask these four things" recipe. That would be the most immediately
    useful thing in the document for anyone outside this project, and it is
    orthogonal to the accuracy analysis. Add it as a §12, or keep the report
    analytical and save it for a community-facing note later?

23. Minor, and only if you care: the figures are light-mode PNGs, matching the
    existing `gloria_fits_report.md` figures. The house data-viz guidance wants a
    dark-mode variant for anything rendered as a web page. Since #19 keeps this out
    of the Sphinx site, I have not made dark variants. Flag it if the report is ever
    published so I can add them.

## Reports

### Prompt 3 (2026-08-01) — Answers reviewed; decisions locked in; access verified

All twelve answers reviewed and acted on. This section records the decisions so
prompts 4–9 don't have to re-litigate them, reports what I verified, and flags what
opening a real NASA granule turned up.

#### Decisions now locked in

| # | Decision | Consequence for later prompts |
|---|---|---|
| 1 | Get the loadings from OCSSW | **Done** (prompt 2). No email needed. |
| 2 | Dig for the AMT24 Rrs in SeaBASS/BODC | **NOT DONE.** A delegated search was started (SeaBASS `PML/AMT`, BODC/NERC, PANGAEA/Zenodo, plus the data-availability statements of Lin+2022 / Pardo+2023 / Brewin+2016) but the agent died before reporting, so **no findings were obtained** — nothing here to carry forward. It got as far as reverse-engineering the SeaBASS `search_results` POST form (`searchType=bio`, `bio_products_custom_text1=<field>`), which is a useful starting point for the retry. To be done under prompt 5 (Data), where it belongs |
| 3 | MOANA is a **separate track** from the IOP work, ending in its own report | No `AlgorithmSpec`, no BING wrapper, no shared metrics table. Code goes in `ioptics/moana/`, data in `ioptics/data/moana/` |
| 4 | Validation targets **(i) AMT24 reproduction, (ii) held-out AMT cruises, (iii) operational PACE product** | (iii) is unblocked *now*; (i) and (ii) wait on #2 |
| 5 | **Skip L23** entirely for MOANA | No Hydrolight path to build |
| 6 | Read `picophyt.json` rather than assume | **Done** (prompt 2) — zero-padding confirmed |
| 7 | Implement **414–660 nm @ 2 nm** | Confirmed by the LUT itself (124 bands) |
| 8 | Standardize with the **sample (N−1)** sd | Matches OCSSW |
| 9 | Implement **both** PC mappings behind a flag; settle empirically; JXP contacts the authors later | Default to the operational mapping so we can reproduce NASA bit-for-bit |
| 10 | Earthdata credentials available | **Verified working** |
| 11 | Keep **raw floats + a QC flag**, not NASA's silent clipping | Our reader must not truncate to int except in bit-comparison mode |
| 12 | Vendor the two LUT files into the repo | **Done** — `ioptics/data/moana/` |

#### Q12 — done

`ioptics/data/moana/` now holds `pca_picophyto.h5` and `picophyt.json`, checksums
matching NASA's manifest, plus a `README.md` documenting provenance, the file
layout, the slot→PC mapping, the known ATBD/LUT discrepancy, and the algorithm
recipe. The repo is now self-sufficient: MOANA can be run without OCSSW installed.

#### Q10 — Earthdata access verified, and the bit-exactness test is de-risked

`earthaccess` 0.18.0 (JXP installed it) authenticates against `~/.netrc`. What I
confirmed about the data we need:

- **NASA's MOANA output:** `PACE_OCI_L4M_MOANA` **v3.2**, daily / 8-day / monthly,
  at 4 km and 0.1°. A daily 0.1° granule is only ~2 MB.
- **There is no L3M MOANA collection in CMR** — only L4M and L4M_NRT — despite the
  `ob-cloud-pace-oci-l3m-moana-3.1` catalog page. Context corrected.
- **The Rrs input:** `PACE_OCI_L3M_AOP` **v3.2**, variable `Rrs`, **172 OCI
  wavelengths from 346.0 to 719.3 nm**. That fully brackets 414–660 nm, so MOANA
  never extrapolates on real OCI data. Spacing is irregular (~1.2–2.5 nm), which is
  exactly why the algorithm interpolates onto its own regular 2 nm grid. A daily
  0.1° granule is ~173 MB, and its header can be read by streaming without
  downloading the whole file.
- **Grids are co-registered.** All 1400 MOANA latitudes and 1100 longitudes appear
  *exactly* in the global AOP grid — MOANA 0.1° is a clean spatial subset
  (lat ±69.95, lon −84.95…24.95, i.e. the Atlantic sector). Alignment is by
  coordinate value; no regridding.
- **SST is available** (this was the unanswered half of Q&A #5):
  `CMC0.1deg-CMC-L4-GLOB-v3.0` — GHRSST CMC L4 at **0.1°, the same resolution as
  the MOANA grid** — is searchable and has granules for our test date. No `ocpy`
  loader needed; `earthaccess` reaches it directly.

**Key de-risking point:** *Synechococcus* and picoeukaryotes need **no SST at all**.
So we can run the full bit-exactness test — interpolation, standardization, scores,
and two of the three regressions — from Rrs alone, and that alone settles the
disputed *Synechococcus* PC index (operational PC16 vs ATBD U13). Only
*Prochlorococcus* needs the SST field, and its disputed index (PC7 vs U17) can be
tested afterwards. We are not blocked on SST for the discrepancy question.

Downloaded one reference granule to `$OS_COLOR/PACE/`:
`PACE_OCI.20250701.L4m.DAY.MOANA.V3_2.0p1deg.nc`.

#### What opening a real granule revealed — four product-level defects

I inspected that granule rather than trusting the catalog. Composition of the
1400×1100 grid:

| category | pixels | share |
|---|---|---|
| land sentinel `254` | 450,592 | 29.3 % |
| `_FillValue` = −32767 | 906,297 | 58.9 % |
| `INT32_MIN` = −2147483648 | 6 | — |
| **real ocean retrievals** | **183,105** | **11.9 %** |

**(a) Land is encoded as `254 cells mL⁻¹`.** Not as `_FillValue`, and worse, `254`
sits *inside* the declared valid range `[0, valid_max]`. Anyone who screens the
honest way — `valid_min ≤ x ≤ valid_max` — silently ingests 450,592 land pixels as
though *Prochlorococcus*, *Synechococcus* and picoeukaryotes were each present at
254 cells mL⁻¹. It nearly caught me: `254` is the modal *and* median value of all
three variables, at 71 % of everything that passes the declared range check. Land
identity confirmed by spot-testing the Congo basin, Sahara, Amazon, Andes and
interior Greenland (all 254) against four open-ocean points (fill or real values).
**Our reader must mask 254 explicitly.**

**(b) Six pixels carry `INT32_MIN`** in `prococcus_moana` — the signature of
`(int32_t)` casting a NaN or out-of-range float, which is undefined behaviour in C.
Not the declared fill value, and ~3500× outside the valid range.

**(c) The declared `valid_max` is not enforced.** On this single day:

| variable | valid_max | actual max | over by | pixels over |
|---|---|---|---|---|
| `prococcus_moana` | 600,000 | 706,915 | 1.2× | 41 (0.02 %) |
| `syncoccus_moana` | 300,000 | 6,594,758 | **22×** | 44 (0.02 %) |
| `picoeuk_moana` | 40,000 | 2,712,984 | **68×** | 930 (0.51 %) |

**(d) Silent clipping is common, not rare.** `prococcus_moana` is *exactly* 0 in
**18.0 %** of real ocean retrievals — that is the negative-clamp in
`get_Cpicophyt.c` firing on nearly a fifth of the product, with no flag to say so.
`syncoccus_moana` is 0 in **8.9 %**, which is the `int32` cast truncating genuine
sub-1 cell mL⁻¹ values to zero. This vindicates answer #11(b): had we copied NASA's
behaviour we would have silently thrown away, or log-transformed, a fifth of the
Prochlorococcus field.

Where the retrievals *are* real they look physically sensible — median 202,098
cells mL⁻¹ for *Prochlorococcus*, 5,145 for *Synechococcus*, 2,963 for
picoeukaryotes — so these are edge-case defects, not a broken product. But (a) and
(d) directly threaten any accuracy assessment, which is the point of this project.

Two smaller documentation mismatches: the in-file variable names are the misspelled
`prococcus_moana` / `syncoccus_moana` / `picoeuk_moana`, **not** the
`prochlorococcus_moana` / `synechococcus_moana` the Earthdata catalog advertises;
and the file's `title` says "OCI Level-3 Standard Mapped Image" while its
`product_name` says `L4m`.

### Prompt 2 (2026-08-01) — Existing MOANA code: located, downloaded, and decoded

**Bottom line: the blocker from Q&A #1 is gone.** The MOANA implementation is
public in full, and the two data files that neither Lange+2020 nor the ATBD
publishes — the PCA loadings and the regression coefficients — are now on disk
with checksums verified against NASA's own manifest. We can reimplement MOANA
bit-for-bit. Decoding those files also turned up a **substantive inconsistency
between NASA's documentation and NASA's operational code** (§4 below).

#### 1. Where the code lives

There is exactly one implementation, in C, inside OCSSW (the Ocean Color Science
Software that also backs SeaDAS). It is not on GitHub — `github.com/nasa/ocssw`
does not exist — and the Ocean Color doxygen browser has been retired (every
`oceancolor.gsfc.nasa.gov/docs/ocssw/…` URL now 301s to the OB.DAAC landing
page). The distribution route is the `install_ocssw` script.

Installed **OCSSW tag V2026.4** (newest of 30 available) to **`$OS_COLOR/ocssw`**:

```
$OS_COLOR/ocssw/
├── install_ocssw, manifest.py       # fetched from oceandata.sci.gsfc.nasa.gov/manifest/
├── ocssw_src/src/l2gen/             # ← the C source, incl. get_Cpicophyt.c
├── share/common/                    # ← the MOANA LUT + coefficients + product.xml
├── opt/                             # 3rd-party sources (pulled in by --src)
└── install.log
```

Command used (`--src` also pulls `opt_src` and `python`; `--common` is the share
bundle holding the MOANA tables):

```
python install_ocssw --tag V2026.4 --install_dir $OS_COLOR/ocssw --src --common
```

~11.5 GB total, of which `share/common` is 10 GB. The first run died partway
through `common` on a read timeout from `oceandata.sci.gsfc.nasa.gov`; re-running
with `--common` resumed and completed. **Note the two files we actually care about
are 24 KB and 390 bytes and are individually addressable** — no 11 GB install is
needed to get them:

```
https://oceandata.sci.gsfc.nasa.gov/manifest/tags/T2023.31/common/pca_picophyto.h5
https://oceandata.sci.gsfc.nasa.gov/manifest/tags/T2023.31/common/picophyt.json
```

(The bundle manifest at `…/tags/V2026.4/common/manifest.json` maps each file to
the tag that last changed it — both MOANA files are pinned at `T2023.31`, i.e.
they have not been touched since 2023 and predate the ATBD.)

MOANA-related source files:

| File | Role |
|---|---|
| `ocssw_src/src/l2gen/get_Cpicophyt.c` | the whole algorithm (279 lines; author Minwei Zhang, created 2023-09-29) |
| `ocssw_src/src/l2gen/l2prod.h` | product catalogue ids: `CAT_prochlorococcus` 353, `CAT_synechococcus` 354, `CAT_autotrophic_picoeukaryotes` 355 |
| `ocssw_src/src/l2gen/prodgen.c:1090` | dispatch — all three ids call `get_Cpicophyt` |
| `ocssw_src/src/l2gen/l12_proto.h:242` | prototype (note: output buffer is `int32_t*`) |
| `share/common/pca_picophyto.h5` | PCA loadings **V** |
| `share/common/picophyt.json` | regression coefficients |
| `share/common/product.xml` | official units / valid ranges / types |

No other implementation exists publicly: no Python or R port, nothing in
`nasa/oceandata-notebooks`, and Lange's original R analysis code was never
released.

#### 2. The two data files, decoded

**`pca_picophyto.h5`** — 24,488 bytes, sha256 `478ace87…deb57`:

- `component` — **(124, 45) float32**: the loading matrix `V[λ, i]`, 45 retained PCs.
  Columns are **orthonormal** (unit norm; `max|offdiag(VᵀV)| = 1.2e-7`), so this is
  a clean truncated eigenvector basis.
- `wavelength` — **(124,) int32 = 414, 416, …, 660 nm**. This settles Q&A #7 as a
  matter of fact, not preference: the operational grid *is* 414–660 nm at 2 nm.
- PC1 is a smooth blue→red ramp (max +0.171 at 414 nm, min −0.097 at 658 nm;
  correlation with wavelength −0.97), matching the paper's description of PC1 as
  backscatter slope plus water absorption.

**`picophyt.json`** — 390 bytes, sha256 `cd6b5c1c…756d4`. Verbatim:

```json
{ "npc": "17",
  "pro_coef":   "-4562144, 770448, 343590, 54975, 0, 0, 0, 290751, -1041404, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0",
  "syn_coef":   "-17.52889, 1.95949, 0.33859, 0.49127, 0, 1.04400, 0, 0, -1.06453, -1.55528, -2.25345, -3.41758, -1.67013, 0, 0, 0,-3.19241, 0",
  "apeuk_coef": "3.31202, 0, 0.21332, 0.09385, 0.72960, 0.97040, 0, 0, 0, 0, 0.67274, 0, 0, -2.25057, 0, -3.45864, 0, 0" }
```

**Q&A #6 is answered: yes, the coefficient vectors are zero-padded.** Their
lengths (19, 18, 18) match the C allocations `malloc(npc+2)`, `malloc(npc+1)`,
`malloc(npc+1)` with `npc=17` exactly, so the padding is by design, and
coefficient slot *k* maps to a fixed PC index.

#### 3. The algorithm as actually implemented

Per pixel, from `get_Cpicophyt.c`:

1. **Drop invalid bands.** Build `(wave_valid, Rrs_valid)` from bands where
   `Rrs != BAD_FLT`. If none are valid → `BAD_INT`.
2. **Linearly interpolate** `Rrs` onto the 124-point 414–660 nm grid. Indices are
   clamped at both ends, so out-of-range points are **extrapolated**, not flagged.
3. **Standardize the spectrum**: `Rrs' = (Rrs − mean)/sd` across those 124 values,
   with `sd` using the **sample (N−1)** denominator (Q&A #8 confirmed — this is
   per-spectrum standardization over wavelength, *not* feature-wise centering on a
   training mean, so **no training mean is needed anywhere**).
4. **Scores** for all 45 PCs: `U_i = Σ_λ V[λ,i]·Rrs'[λ]` — a plain dot product.
5. **Regressions**, using only the first `npc_used = 17` scores:
   ```
   Pro          = pro_coef[0] + pro_coef[1]·log10(SST) + Σ_{i=0..16} pro_coef[i+2]·U_{i+1}
   log10(Syn)   = syn_coef[0]                          + Σ_{i=0..16} syn_coef[i+1]·U_{i+1}
   log10(peuk)  = apeuk_coef[0]                        + Σ_{i=0..16} apeuk_coef[i+1]·U_{i+1}
   ```
   Syn and picoeuk are then exponentiated; **Prochlorococcus is not** (it was fit
   linearly, per the paper).
6. **SST** = `l2rec->sst` if `proc_sst` is on, else the reference field
   `l1rec->sstref` (the ATBD says that reference is GHRSST CMC L4).
7. **Clamp and cast**: a negative Pro becomes 0 when Syn and picoeuk are both
   positive; all three are then **truncated to `int32`**.

A self-consistency check confirms the loading file and the coefficient file belong
together. Because `Rrs'` is standardized, `‖Rrs'‖₂ = √123 = 11.09` exactly, and
because `V`'s columns are orthonormal, **every score is bounded by ±11.09**. Using
that ceiling, Prochlorococcus evaluates to 1.5×10⁵ (SST 15 °C) to 3.6×10⁵ cells/mL
(SST 28 °C) — physically correct for *Prochlorococcus*, and inside the official
`validMax` of 6×10⁵. It only lands in range when `U₁` sits near its ceiling, which
is precisely what >96 % of covariance on PC1 implies. The huge Pro coefficients
(~10⁶) are therefore real, not a transcription error.

#### 4. Inconsistencies found

**(a) The serious one: the ATBD equations and the operational coefficients disagree
about two PC indices.** Decoding `picophyt.json` through the C indexing and
comparing against the ATBD v1.2 equations:

| Taxon | PCs per operational `picophyt.json` | PCs per ATBD v1.2 equations |
|---|---|---|
| Prochlorococcus | 1, 2, 6, **7** | 1, 2, 6, **17** |
| *Synechococcus* | 1, 2, 3, 5, 8, 9, 10, 11, 12, **16** | 1, 2, 3, 5, 8, 9, 10, 11, 12, **13** |
| picoeukaryotes | 2, 3, 4, 5, 10, 13, 15 | 2, 3, 4, 5, 10, 13, 15 ✓ |

Every coefficient *value* matches (to ATBD rounding: `0.33859`→`0.3385`,
`-3.19241`→`-3.1924`). Picoeukaryotes agree completely. But for Prochlorococcus and
*Synechococcus* the **last** coefficient sits on a different principal component in
the file that runs than in the document that describes it.

Evidence on which is right: the union of PCs across all three taxa is **14 distinct
PCs for the ATBD** version versus **15 for the JSON** — and Lange+2020 states that
exactly **14** PCs survived the significance cut for the hyperspectral PCA. The
per-taxon counts (4 / 10 / 7) match the paper's prose either way. So the ATBD
equations reproduce the paper's PC budget exactly and the JSON does not, which
points to `picophyt.json` having two coefficients in the wrong slots — meaning the
**operational PACE MOANA products may not be computing the published algorithm.**
I would not assert that as fact without the authors confirming; the alternative is
that the ATBD subscripts are typos and the paper's "14" counts something slightly
different. Either way it is worth an email, and our implementation should support
both mappings so we can quantify how much the retrievals actually differ.

**(b) The ATBD contradicts itself on spectral range** — abstract says Rrs must be
valid over 395–705 nm, Mathematical Theory says 414–660 nm. The LUT settles it:
414–660 at 2 nm.

**(c) The ATBD says "only 14 PCs were selected"** but its own equations index up to
U17, and the LUT ships 45 components with `npc_used = 17`. These are reconcilable
(14 *used*, 17 *scanned*, 45 *stored*) but nothing in the documentation says so.

**(d) Product short names are misspelled and inconsistent across levels.** L2 uses
`prococcus` / `syncoccus` / `picoeuk`; the L3/L4 files use `prochlorococcus_moana` /
`synechococcus_moana` / `picoeuk_moana`. Any reader we write must handle both.

#### 5. Quirks that will bite a reimplementation

- **Integer output.** `product.xml` declares `<type>int</type>` and the code casts
  with `(int32_t)`, which **truncates rather than rounds**. Sub-1 cell/mL effects
  only, so minor — but it means a bit-exact match to NASA's product requires
  truncating too.
- **Negative Prochlorococcus is silently zeroed, not flagged.** Since Syn and
  picoeuk come from `pow(10, …)` and are always positive when valid, the guard
  reduces to "clip Pro at 0". Zeros cannot be log-transformed, so this materially
  affects any log-space validation statistic — we must decide whether to treat
  clipped zeros as data or as flags.
- **Two dead-code paths**, harmless but confusing when reading: `bindx` is computed
  via `windex` and never used, and the `< 0` tests on `pow(10, …)` results can
  never fire.
- **A latent out-of-bounds read.** With very few valid bands the interpolation
  clamp can select `j = 1` while only index 0 was filled, reading uninitialized
  `wave_valid`/`Rrs_valid`. There is no minimum-valid-band check. Harmless for OCI
  in practice (hundreds of bands) but our version should require a sane minimum.
- **Extrapolation is silent** at the grid edges rather than masked.
- MOANA also runs under `l3gen` (there is an explicit `npix` realloc for it), which
  is consistent with the operational products being L3/L4 mapped rather than L2.

#### 6. Official product metadata (from `share/common/product.xml`)

| L2 name | units | type | validMin | validMax | display |
|---|---|---|---|---|---|
| `prococcus` | cells ml⁻¹ | int | 0 | 6×10⁵ | 1–5×10⁵, linear |
| `syncoccus` | cells ml⁻¹ | int | 0 | 3×10⁵ | 1–1.5×10⁵, log |
| `picoeuk` | cells ml⁻¹ | int | 0 | 4×10⁴ | 1–3×10⁴, log |

All three cite Lange et al. (2020) as the reference.

#### 7. What is still missing

Only one thing, and it is not code: **the AMT24 training data** — the
hyperspectral Rrs in particular (Q&A #2). We can now *run* MOANA exactly as NASA
does; we cannot yet *retrain* it or reproduce Lange's Tables 1–2 without the
training spectra. Also absent: any uncertainty estimate (MOANA emits none), and any
published validation of the satellite products.

#### 8. Recommended next step

Before touching AMT24, do a **bit-exactness check against NASA**: download one PACE
OCI L3M Rrs granule plus the matching L3M MOANA granule and confirm our Python
implementation reproduces NASA's three fields pixel-for-pixel. That validates our
transcription against the operational truth in one shot, and it is the cleanest way
to settle §4(a) empirically — if we reproduce NASA's product with the JSON mapping
but not the ATBD mapping, the operational code is definitively using PC7/PC16.

### Logs

### 2026-08-01 (Prompt 4 — MOANA report written; earthaccess added to requirements; loadings figure generated)

**Model:** run as Claude Fable 5, per "Use Fable if you can".

**Read the new answers first, as instructed.** #13 → clipped values treated as
censored data *and* the unphysical fraction reported as a headline number; #14 →
product defects go in an appendix, and JXP wants reminding to raise them with NASA
(that reminder is now written into the report body so it cannot get lost); #15 →
document the Bailey & Werdell departure and use daily L4M, revisit true L2 later;
#16 → `earthaccess` added to `requirements.txt` with a comment recording the
`~/.netrc` test-skip convention. That last one was the only code-adjacent action and
is done.

**Wrote `reports/MOANA_Claude_Report.md`.** Structured so it is self-contained — the
equations, all 25 coefficients with their PC assignments, the file formats, and the
data-source collections are all in it, so an implementation can be built from the
report alone without re-reading the paper, the ATBD or the C. Ten sections plus two
appendices: what MOANA is; why the approach can work; the five algorithm steps; the
coefficient table; a provenance matrix of which constant comes from which source;
published performance; inconsistencies; an assessment; eight proposed improvements;
and the plan. Product-level defects went to Appendix A per #14, file formats to
Appendix B.

Two things I was careful about. First, **separating verified statements from
inferences** — behaviour read out of the C and the data files is verified, whereas
"the ATBD is probably right and the operational LUT probably has two coefficients
misplaced" is an inference from a single coincidence (the 14-PC union count) and is
labelled as such. Second, **not over-claiming on mechanism**: the PC5 loading has
narrow structure near 450/510/605 nm which would be a tidy phycobiliprotein story
for why hyperspectral helps *Synechococcus* most, and I wrote it down explicitly as
untested speculation rather than as a finding, because post-hoc pigment attribution
of PCA components is easy to get wrong.

**The improvements section is where I put the most thought.** Ranked by value per
unit effort, the substantive ones are: replace the identity-link linear
*Prochlorococcus* model with a **log-link GLM** so negatives become structurally
impossible (this is a better answer than either option Lange et al. considered,
since fitting `log₁₀(y)` by least squares carries a retransformation bias that is
plausibly what "significantly reduced the performance" actually measured); **feed
back the two amplitude numbers that standardisation throws away**
(`log₁₀(mean(Rrs))` and `log₁₀(sd(Rrs))`) as extra predictors, since they are already
computed and cost nothing; add **per-pixel uncertainty**, which is nearly free for a
linear model on fixed components; and add an **out-of-domain flag** from the
truncated-basis reconstruction residual `‖Rrs' − VVᵀRrs'‖`, which needs no
retraining and replaces silent extrapolation with a principled novelty score. Also
argued for retraining the basis at OCI's real spectral resolution (the current basis
inherits the 2014 HyperSAS's ~10 nm resolution, so it cannot contain the fine
structure PACE exists to measure), for regularisation instead of stepwise AIC at
n = 73, for **spatially blocked** cross-validation instead of random splits of
autocorrelated underway data, and for shipping an Rrs-only *Prochlorococcus* variant
so that studies of temperature–*Prochlorococcus* coupling are not circular.

**Made one figure.** `reports/scripts/moana_report_figs.py` draws the first six PCA
loadings from the vendored LUT, annotated with which taxa use each component. It
follows the repo's existing `reports/{figures,scripts}` convention and needs no
satellite or in-situ data, so it runs anywhere the repo is checked out. Useful side
effect: the script re-derives the PC assignments independently of my earlier
analysis and got the same answer (Pro 1/2/6/7, Syn 1/2/3/5/8/9/10/11/12/16, picoeuk
2/3/4/5/10/13/15), which is a genuine check on the decode rather than a restatement
of it. It also prints the invariants the report leans on — orthonormality to
1.2×10⁻⁷ and `‖Rrs'‖₂ = 11.091`.

**Corrections I caught while writing.** I had mixed up the multispectral and
hyperspectral numbers in Lange et al.'s CTD-versus-underway retraining experiment
(the −29 % bias is the multispectral case; hyperspectral is −16 % with MAE 1.37) and
fixed it against the paper. I also had to fix a matplotlib title that used `$…$` and
was silently mathtext-mangling `pca_picophyto.h5` into a subscript.

**Deliberately not done:** I did not run the bit-exactness test, even though it
would have let the report settle §7.1 definitively. It needs a 173 MB granule
download and interpolation code, which are prompts 5 and 7; the report specifies the
experiment precisely instead and flags it as the highest-value next step.

**No `pytest` run:** no package code was touched (the figure script is a report
artefact under `reports/scripts/`, matching the existing precedent). Nothing
committed.

**Files changed.** New: `reports/MOANA_Claude_Report.md`,
`reports/scripts/moana_report_figs.py`, `reports/figures/moana_pc_loadings.png`.
Modified: `requirements.txt` (added `earthaccess`),
`claude_prompts/moana_prompts.md` (Q&A #17–20 and this entry).

### 2026-08-01 (Prompt 3 — answers reviewed and acted on; LUTs vendored; PACE access verified; product defects found)

**Model:** run as Claude Fable 5, per "Use Fable if you can".

Reviewed all twelve answers and acted on everything actionable without stepping into
prompts 4–9 (report, data download, design, code). The decision table and the full
findings are in the prompt-3 report above; this is the work record.

**Q12 — vendored the reference tables.** Created `ioptics/data/moana/` with
`pca_picophyto.h5` and `picophyt.json` copied from
`$OS_COLOR/ocssw/share/common/`, checksums re-verified after the copy. Wrote a
`README.md` there covering provenance (upstream tag, direct URLs, SHA-256s), the
dataset layout, the coefficient-slot→PC mapping, the known ATBD/LUT discrepancy, and
the algorithm recipe. The repo can now run MOANA with no OCSSW install.

**Q10 — verified access and de-risked the bit-exactness test.** `earthaccess` 0.18.0
authenticates from `~/.netrc`. Established that NASA's MOANA output is
`PACE_OCI_L4M_MOANA` v3.2 (there is **no** L3M MOANA collection in CMR, contrary to
the catalog page I cited in prompt 1 — Context corrected), that the Rrs input is
`PACE_OCI_L3M_AOP` v3.2 with 172 OCI bands spanning 346–719 nm (so 414–660 is fully
covered and MOANA never extrapolates on real data), and that the two grids are
exactly co-registered — all 1400 MOANA latitudes and 1100 longitudes appear verbatim
in the global AOP grid, so alignment is by coordinate value with no regridding.

Also closed the half of Q&A #5 that went unanswered: GHRSST CMC L4 SST is
`CMC0.1deg-CMC-L4-GLOB-v3.0`, reachable through `earthaccess` at 0.1° — the same
resolution as the MOANA grid — so no `ocpy` loader is needed.

The useful realisation here: *Synechococcus* and picoeukaryotes need no SST, so the
bit-exactness test can run from Rrs alone and by itself settles the disputed
*Synechococcus* PC index (operational PC16 vs ATBD U13). We are not blocked on SST
for the question that matters.

**Four defects in the shipping product.** I downloaded one daily 0.1° MOANA granule
(2 MB) rather than trusting the catalog, and it was worth doing. The most important
find is that **land is encoded as `254 cells mL⁻¹`** — not as `_FillValue`, and
inside the declared valid range, so the honest screen `valid_min ≤ x ≤ valid_max`
swallows 450,592 land pixels as real abundance. This nearly fooled me: my first pass
reported a median of 254 for all three variables and I only caught it because an
identical median across three independent regressions is impossible. Spot-testing
the Congo basin, Sahara, Amazon, Andes and interior Greenland (all 254) against four
open-ocean points settled it. Also found six `INT32_MIN` pixels (undefined behaviour
from the `(int32_t)` cast), `valid_max` unenforced (picoeukaryotes reach 68× their
declared ceiling), and — most consequential — **`prococcus_moana` is exactly zero in
18.0 % of real ocean retrievals**, which is the silent negative-clamp firing on
nearly a fifth of the field, plus 8.9 % zeros in *Synechococcus* from integer
truncation. Correct ocean-only statistics are tabulated in the report.

That last one vindicates answer #11(b). Had we mirrored NASA's behaviour we would
have log-transformed or silently discarded a fifth of the Prochlorococcus field
without noticing.

**Method note for my own future reference:** I twice caught myself about to record a
number that was an artefact — the "median 254" above, and a spurious 0.1° lat offset
that came from my own `searchsorted` misuse on descending coordinate arrays rather
than from the data. Both were resolved by re-checking with a different method
(raw unscaled reads; exact set membership) before writing anything down.

**No `pytest` run:** this step added a data directory and a README, no package code.
Nothing was committed.

**Files changed.** `claude_prompts/moana_prompts.md` — corrected the product/variable
names in Context, added the prompt-3 report, Q&A #13–16, and this log entry. New:
`ioptics/data/moana/{pca_picophyto.h5,picophyt.json,README.md}`. New outside the
repo: `$OS_COLOR/PACE/PACE_OCI.20250701.L4m.DAY.MOANA.V3_2.0p1deg.nc`.

### 2026-08-01 (Prompt 2 — OCSSW installed; MOANA loadings and coefficients recovered and decoded)

**Model:** run as Claude Fable 5, per "Use Fable if you can".

The full findings are in the prompt-2 report above; this is the work record.

**Searching.** Confirmed there is exactly one public MOANA implementation, the C
routine inside OCSSW. `github.com/nasa/ocssw` does not exist, and the Ocean Color
doxygen browser that hosted the readable source in prompt 1 has been retired
(everything under `/docs/ocssw/` now 301s to the OB.DAAC landing page). No Python
or R port exists — not in `nasa/oceandata-notebooks`, not in the PACE Hackweek
material — and Lange's original R analysis code was never released. So OCSSW is the
only authority, which is why installing it mattered.

**Installing.** `install_ocssw` and `manifest.py` come from
`oceandata.sci.gsfc.nasa.gov/manifest/` (the `/ocssw/install_ocssw` path 404s).
Listed 30 tags and took the newest, **V2026.4**, installing the `--src` and
`--common` bundles into `$OS_COLOR/ocssw` (~11.5 GB; `share/common` alone is 10 GB).
The first run died partway through `common` on a read timeout from NASA; re-running
with `--common` resumed cleanly and finished. Disk left: ~473 GB.

Worth recording for anyone repeating this: **the 11.5 GB install was not actually
necessary.** The bundle manifest at `…/manifest/tags/V2026.4/common/manifest.json`
lists every file with its size, sha256 and originating tag, and individual files are
directly fetchable. Both MOANA tables — 24,488 bytes and 390 bytes — came down in
under a second from `…/manifest/tags/T2023.31/common/`, and I verified both against
the manifest checksums before trusting them. (The `T2023.31` tag also tells us these
tables have not changed since 2023 and therefore predate the Dec-2024 ATBD.)

**What the files contain.** `pca_picophyto.h5` holds `component`, a (124, 45)
float32 loading matrix, and `wavelength`, int32 414–660 nm in 2 nm steps. I checked
that the columns are genuinely orthonormal (`max|offdiag(VᵀV)| = 1.2e-7`), so it is
a proper truncated eigenvector basis. `picophyt.json` holds `npc = 17` and three
comma-separated coefficient strings of length 19/18/18 — exactly matching the C
allocations `npc+2`, `npc+1`, `npc+1`, which confirms the zero-padding hypothesis I
raised in Q&A #6.

The thing I most wanted to be sure of: **there is no training mean to recover.** The
standardization is per-spectrum across wavelength (Lange Eq. 3), not feature-wise
centering, and the scores are a plain dot product with the loadings. So these two
small files plus the code are genuinely everything needed to run MOANA exactly as
NASA runs it. Q&A #1 is closed.

**Reading the code.** `get_Cpicophyt.c` in the installed tree is 279 lines against
the 256 of the 2022 snapshot I read in prompt 1. The differences matter: the output
buffer changed from `float*` to `int32_t*` (so abundances are now **truncated** to
whole cells/mL), a valid-band filter was added ahead of the interpolation, and an
`npix` realloc was added so the algorithm can run under `l3gen` — consistent with
the operational products being L3/L4 mapped. Also catalogued the surrounding
plumbing (`l2prod.h` ids 353–355, the `prodgen.c` dispatch) and pulled the official
units and valid ranges from `share/common/product.xml`.

**Verification I did.** Rather than hand-count coefficient positions, I decoded
`picophyt.json` with a script replicating the C indexing exactly
(`pro_coef[i+2]·pc[i]`, `syn_coef[i+1]·pc[i]`, `apeuk_coef[i+1]·pc[i]`) and
diffed the result against the ATBD equations. Picoeukaryotes match perfectly;
Prochlorococcus and *Synechococcus* each have their final coefficient on a
different PC than the ATBD states, with identical values. Separately I
re-extracted the ATBD coefficient table in `pypdf` layout mode to rule out a
column-mixing artefact in my prompt-1 transcription — the numbers were correct.

I also ran a self-consistency check on the two files together. Because a
standardized spectrum has `‖Rrs'‖₂ = √123 = 11.09` and `V`'s columns are
orthonormal, every score is bounded by ±11.09; feeding that ceiling through the
Prochlorococcus regression gives 1.5–3.6×10⁵ cells/mL across SST 15–28 °C, which is
physically right and sits inside the official `validMax` of 6×10⁵. That the huge
~10⁶ coefficients only produce sane abundances when `U₁` is near its ceiling — which
is exactly what >96 % of covariance on PC1 implies — is good evidence the loading
file and coefficient file belong to each other and that my index mapping is right.

**The substantive finding.** The union of PCs used across the three taxa is 14
distinct PCs under the ATBD's assignment and 15 under the operational JSON's, and
Lange+2020 says exactly 14 survived the significance cut. That is a real argument
that `picophyt.json` has two coefficients in the wrong slots, i.e. the shipping PACE
MOANA products may not implement the published algorithm. I have deliberately *not*
asserted this as established — the alternative is that the ATBD subscripts are
typos — and have proposed settling it empirically by reproducing a real PACE granule
before contacting the authors (Q&A #9, #10).

**No `pytest` run:** this step wrote no package code. Nothing was committed.

**Files changed.** `claude_prompts/moana_prompts.md` — added the prompt-2 report,
four new Q&A items (#9–#12), and this log entry. New on disk outside the repo:
`$OS_COLOR/ocssw/` (OCSSW V2026.4).

### 2026-08-01 (Prompt 1 — context assembled; MOANA ATBD and OCSSW implementation located)

**Model:** run as Claude Fable 5, per "Use Fable if you can".

**What I read.** `docs/design/IOPtics_design.md` (v0.15) and
`docs/design/IOPtics_implementation.md` (v0.22) in full, and all 24 pages of
`papers/lange2020.pdf` (text extracted with `pypdf` in `ocean14`).

**Lange et al. 2020 in brief.** *Optics Express* 28(18), 25682–25705,
DOI `10.1364/OE.398127`. Empirical principal-component regression predicting
surface cell abundances of *Prochlorococcus*, *Synechococcus* and autotrophic
picoeukaryotes. Trained on AMT24 (Sep–Nov 2014): underway HyperSAS Rrs
interpolated to 2 nm over 414–660 nm, each spectrum standardized (Eq. 3) to
suppress amplitude and expose shape, PCA via R `prcomp`, then backward stepwise
multilinear regression on the PC scores with AIC-based selection, optionally
adding SST. 20 PCs survived the variance cut, 14 the significance cut. PC1 alone
carries >96 % of the covariance (backscatter slope + water absorption), PC2 ~3.5 %
(Chl absorption), PC3 ~0.16 % (accessory pigments). *Prochlorococcus* is fit
**linearly** (it is normally distributed); the other two in log10. SST helps Pro
markedly (hyperspectral MAE 1.49→1.31, R² 0.42→0.82) and does nothing for Syn.
Hyperspectral beats 7-band MODIS throughout — the paper's headline argument for
PACE. Skill degrades on satellite Rrs (Syn MAE 2.04) and degrades further on the
five held-out cruises (Pro MAE 2.26, bias 1.75). One methodological lesson worth
carrying: the fine 30-minute underway sampling across the South Atlantic front is
what gave *Synechococcus* its dynamic range — retraining on CTD casts alone drove
its bias from ~0 to −29 %.

**What I found on the NASA side.** Three things, in increasing order of value:

1. MOANA is a *current operational PACE product*, not just a paper. Level-3 and
   Level-4 Regional Mapped MOANA (v3.1, and an unregistered v3.2 + NRT), variables
   `prochlorococcus_moana` / `synechococcus_moana` / `picoeuk_moana` in cells mL⁻¹,
   2024-03-05 onward. It is part of the first PACE OCI PCC suite and was used for
   the PACE "first light" image. The ATBD concedes the *satellite* products **have
   not been validated**, which is a real opening for us.
2. **The ATBD (v1.2, 16 Dec 2024)** — downloaded to `papers/moana_atbd.pdf`,
   DOI `10.5067/0AV5267G5C77`. It confirms MOANA = "Multiple Ordination ANAlysis"
   and, crucially, **tabulates all 25 regression coefficients** that Lange+2020
   omits, along with which PC index each multiplies:
   - `Pro       = p1 + p2·log10(SST) + p3·U1 + p4·U2 + p5·U6 + p6·U17`  (linear)
   - `log10(Syn) = s1 + s2·U1 + s3·U2 + s4·U3 + s5·U5 + s6·U8 + s7·U9 + s8·U10 + s9·U11 + s10·U12 + s11·U13`
   - `log10(picoeuk) = a1 + a2·U2 + a3·U3 + a4·U4 + a5·U5 + a6·U10 + a7·U13 + a8·U15`
   with `U_i = Σ_λ Rrs'(λ)·V(λ,i)` over 414–660 nm. SST is the PACE reference
   field (GHRSST CMC L4). Note the hyperspectral picoeukaryote model needs **no**
   SST, consistent with Table 1 of the paper.
3. **The OCSSW implementation**, `src/l2gen/get_Cpicophyt.c` (Minwei Zhang,
   2023-09-29). The Ocean Color doxygen tree has been retired — every
   `oceancolor.gsfc.nasa.gov/docs/ocssw/…` URL now 301s to the OB.DAAC landing
   page — so I recovered it from a 2025-07-12 Wayback snapshot. Reading it settles
   several things the prose leaves vague: Rrs is **linearly** interpolated onto the
   PCA grid; standardization uses the **sample** sd (N−1); scores are a plain dot
   product of the standardized spectrum with a loading column (no re-centering on a
   training mean, no singular-value scaling); Syn and picoeuk are exponentiated,
   Pro is not; and a negative Pro is clamped to 0 when the other two are positive,
   else flagged `BAD_FLT`. It also reveals where the two missing data files live:
   loadings in `$OCDATAROOT/common/pca_picophyto.h5` (`component` [nwave × npc],
   `wavelength`), coefficients in `$OCDATAROOT/common/picophyt.json`. I did not
   pursue the OCSSW download itself — that is prompt 2 — but flagged it there.

**AMT24 and its data.** The training cell counts have a citable BODC DOI, as do
all five Lange+2020 validation cruises (AMT20/22/23/25/28) — the full table is now
in Context, every DOI resolved against DataCite and `doi.org`. The most valuable
incidental find is **Jordan et al. 2025** (*ESSD* 17, 493–516): underway
particulate IOPs (~400–720 nm) and HPLC pigments for nine AMT cruises **including
AMT24**, on SeaBASS and Zenodo. That is in-situ IOP truth on the exact cruise that
trained MOANA, and it is a plausible new IOPtics dataset independent of this MOANA
work. Second most valuable: **Lin et al. 2022** (*Opt. Express* 30, 45648), an
uncertainty budget for continuous above-water AMT radiometry — the principled
`varRrs` for an AMT fit, in place of the flat-5 % fallback `ioptics.prep` currently
uses for in-situ data without per-band errors.

**Gap I could not close.** I found no public archive for the AMT24 hyperspectral
Rrs itself, and no published PCA loading matrix. Both are prerequisites for a true
reproduction; see Q&A #1 and #2.

**Verification.** Every DOI written into Context was checked: resolved through
`doi.org` where the publisher permits it, and via the Crossref or DataCite REST
APIs for the six that return 403 to automated clients (Wiley, MDPI, AGU) or that
are DataCite-only. Two DOIs advertised on Earthdata — `…/L4M/MOANA/3.2` and
`…/L3M/MOANA/3.2` — are **not yet registered** and do not resolve; Context cites
v3.1 and says so. No `pytest` run: this step touched no package code.

**Files changed.** `claude_prompts/moana_prompts.md` (Context, Q&A, this log);
added `papers/moana_atbd.pdf` (6.9 MB, downloaded from OB.DAAC).

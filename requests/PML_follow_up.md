# PML follow-up list — AMT24 / MOANA reproduction

**Prepared:** 2026-08-16 (Claude, for JXP — consolidating every PML-bound item
from `claude_prompts/moana_prompts.md` Q&A #25, #27–31, #35)
**Context for the recipients:** we received the AMT24 HyperSAS Level-2 delivery
(37 daily directories, ~1 M spectra, `LT`/`LI`/`ES`/`RRS` as daily CSVs + IDL
`.sav`) and are reimplementing the Lange et al. (2020) / NASA PACE MOANA
algorithm from it. Everything below arose from a full inspection of that
delivery. Likely contacts: **Bob Brewin** (supplied the data), **Gavin
Tilstone**, **Giorgio Dall'Olmo**, **Tim Smyth** (AMT24 optics team / PI), and
**Glen Tarran** (flow cytometry).

Ordered by how much each item blocks the science.

---

## 1. The underway flow-cytometry samples (→ Tarran) — *highest priority*

The BODC deposit (DOI `10.5285/a2104adc-e98f-6789-e053-6c86abc0d557`) contains
**CTD-bottle samples only**: 814 samples at 68 stations, all `Gear=CTD`. But
Lange et al. (2020) trained MOANA on n = 73–78 samples **including the
~30-minute underway flow-cytometry sampling** across the South Atlantic Gyre
front — and their own sensitivity test (their Table 2) shows the underway
samples are what make the *Synechococcus* model work (CTD-only retraining
degrades Syn MAE from 1.27 to 1.37).

**Ask:** are the AMT24 underway FCM cell counts (Pro / Syn / picoeukaryotes)
available — as a second BODC deposit we may have missed, or directly? Without
them, any retraining is confined to the degraded CTD-only configuration.

## 2. Bug report: the ES CSVs in the Level-2 delivery are wrong

`AMT24_HSAS_<day>_ES.dat` is a **byte-identical copy** of
`AMT24_HSAS_<day>_LT.dat` on **all 37 days** (verified by `md5sum`) — the
export evidently wrote the LT matrix twice. The true downwelling irradiance is
intact inside the `.sav` files (`matrix_es`: ~90–175 µW cm⁻² nm⁻¹, correct
solar shape), so nothing is lost — but anyone using the CSVs alone would
compute Rrs with radiance in place of irradiance.

**Ask:** none needed for us (we read the `.sav`); flagged so PML can fix the
export before the delivery goes to anyone else.

## 3. Two missing days inside the MOANA training window

The delivery covers DOY 266–305 (2014) but **DOY 267, 273 and 298 are absent**.
Lange's training window is 30 Sep – 1 Nov = DOY 273–305, so **273 (30 Sep) and
298 (25 Oct)** are real holes: any flow-cytometry samples on those days lose
their radiometry matchup.

**Ask:** do those days exist (instrument up, files just not exported), or was
the HyperSAS down? If they exist, please include them.

## 4. Processing-chain documentation for the Level-2 delivery

The delivery came with no README. We reverse-engineered the processing
empirically and would like it confirmed or corrected:

- shipped `RRS` = `(LT − 0.0280·LI)/ES` exactly — fixed Mobley ρ, applied
  per-spectrum at ~0.86 s cadence;
- **no** NIR-residual/glint-offset subtraction (median Rrs(750–796 nm)
  ≈ 0.0020 sr⁻¹);
- **no** tilt/azimuth/solar-zenith screening and **no** time binning;
- spectra already resampled to a uniform 306–796 nm @ 3.5 nm grid
  (HyperOCR native is ~3.3 nm, non-uniform);
- units: ES in µW cm⁻² nm⁻¹, LT/LI in µW cm⁻² nm⁻¹ sr⁻¹;
- ancillary SST/salinity columns are corrupt on DOY 266 (pre-departure).

**Ask:** a one-page note (or email) stating the calibration applied (pre/post
cruise averaging?), the dark treatment, the resampling, and anything else
between raw HyperSAS and these files.

## 5. Native-resolution spectra (lower priority)

Because the delivery is already interpolated once (native ~3.3 nm → uniform
3.5 nm), reaching MOANA's 414–660 nm @ 2 nm grid forces a second interpolation.
We accept the small smoothing for now (Q&A #31).

**Ask (when convenient):** the native-grid Level-2 spectra, to remove one
interpolation from the chain.

## 6. Lange et al.'s processed training matrix (if PML holds it)

The cleanest possible reproduction target is the **processed 414–660 nm @ 2 nm
Rrs matrix that was actually fed to `prcomp`** in Lange et al. (2020) — their
glint minimisation, screening and noise filtering differ from anything
derivable from the Level-2 delivery without re-implementing it (which we are
doing, but exact reproduction of their PCA needs their exact matrix).
Priscila Lange processed it, but the underlying data and possibly the
processing scripts are PML's.

**Ask:** does PML hold that matrix (or the processing code), and can it be
shared for reproduction purposes?

## 7. Encourage a BODC deposit of the AMT24 radiometry

BODC already publishes AMT in-situ hyperspectral Rrs for **AMT23, 25, 26, 28**
(Brewin et al. 2023, DOI `10.5285/f3198e10-faf3-1525-e053-6c86abc0d2f6`) —
same data type, same programme, same group. AMT24 is the *training cruise of an
operational NASA PACE product* and its radiometry is currently unpublished
(we verified: no SeaBASS, no DataCite, no BODC series).

**Ask/suggestion:** depositing the AMT24 radiometry (this Level-2 set or
better) with BODC would make MOANA reproducible from public data for the first
time.

---

*Not for PML:* the algorithm-side questions (PC-mapping discrepancy, PCA
eigenvalues, regression covariance, the paper-vs-ATBD SST term for
picoeukaryotes) go to the NASA/MOANA authors — that list lives in
`reports/MOANA_Claude_Report.md` §11.

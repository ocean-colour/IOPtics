# WATERHYPERNET -- Exploring this dataset

## Goal

Examine at a high-level the WATERHYPERNET dataset, Release 2

## Conventions

- `ocean14`; JXP runs git; after each step run `pytest -q` where relevant, Q&A, Log.
- Run via the env interpreter directly
  (`/home/xavier/miniforge3/envs/ocean14/bin/python …`); `conda activate` fails
  non-interactively. This is a **Tier-2** operation — it needs the `$OS_COLOR`
  data tree (L23) mounted; do **not** unset `$OS_COLOR` here.
- `report`/`plotting` need matplotlib (`Agg` is fine headless) + Bokeh + Sphinx.

## Context

- **Config** (`run_v1.yaml`): `sweep_id: expb_giop_L23_v1`, `datasets: [L23]`,
  `noise_model: pace`, `seed: 1234`. **`expb_pow` = standard 5-parameter BING**
  (ExpBricaud a_nw + Pow bb_nw; `Adg, Sdg, Aph, Bnw, beta`, k=5) — **MCMC-fit on
  the `mcmc_subset` (1d)**, and χ²-fit over all records like every algorithm;
  **`giop`** = k=3 contrast (GIOP a_nw + Lee bb_nw; `Aexp, Aph, Bnw`) — **LM/χ²
  only (1b)**. `fit_method: chisq` (sweep default → giop); `mcmc_subset: 200`
  (D4; the expb_pow spectra also MCMC-fit).
- **Driver** (`build_v1.py`, `main(flg)`): `1` → `run.run_sweep(cfg)`; `2` →
  `metrics.compute(cfg.sweep_id)`; `3` → `report.standard.build(sweep_id,
  kind='cross_algorithm')` + `leaderboard.update()` +
  `rst.write_leaderboard_landing(...)`.
- **Artifact split (design Q22):** the `.rst` page + lightweight display assets
  (figure PNGs, `interactive_scatter.html`, CSV tables) are copied into
  `docs/source/reports/<sweep_id>/` and committed; parquet/chains stay in `runs/`.
- **Leaderboard** lands at `$OS_COLOR/IOPtics/leaderboard.parquet` (runs-root
  sibling) and is not committed.

### ⚠ Read before running — the run knobs

- **Error policy / fail-fast.** By default `run.run_sweep` is `strict=True` — a
  **single** failed fit aborts the whole sweep (the run-error-policy TODO). For
  the first full sweep use `strict=False` (D3): failures become
  `status='fit_failed'` rows + reduced coverage.
- **Cost (post-1d): χ² fast, MCMC is the long pole.** χ² over all 3320 × 2 is
  minutes (pooled at `n_cores`). But `expb_pow` (BING) is MCMC-fit on the
  **200-spectrum subset**, and those MCMC fits are **serial** (~40 000 steps
  each). The 5-fit smoke took ~5 min → the full **200 MCMC fits project to
  ≈3 hours**. Plan to run the full sweep in the **background** (step 3).
- **Getting the knobs in.** `build_v1.main` now accepts
  `n_cores`/`strict`/`obs_ids` (step-1 tweak) and threads them into
  `run.run_sweep`.

### WATERHYPERNET

The data files are located in `$OS_COLOR/WATERHYPERNET` under RELEASE_2

## Prompts

### Explore

1. Read the files in Context.  Then explore the data tree for WATERHYPERNET.
We are going to eventually write a context file in named 
`context/WHN/WATERHYPERNET.md`.
First, ask me a series of questions in the Q&A/Explore section below.  
Use Fable if you can.  Log your work.

2. I have answered your first round of Q&A.  Please see my answers and
ask another round if needed.  
Use Fable if you can.  Log your work.

3. I have answered your 2nd round of Q&A.  Please see my answers and
proceed to finish your exploration, generate the Python scripts and figures, and
write the `context/WHN/WATERHYPERNET.md` file.
Use Fable if you can.  Log your work.

## Q&A

### Explore

**What I found first (so the questions make sense).** 56,669 NetCDF files, 9.8 GB,
11 sites, `SITE_X/YYYY/MM/DD/*.nc`, one above-water hyperspectral measurement per
file. `_H` = HYPSTAR (7 sites), `_P` = PANTHYR (4 sites); VEIT has both. **No IOPs,
no Chl, no in-water measurements of any kind** — the release is reflectance +
geometry + QC only. Both systems ship `reflectance` (NIR/SWIR-SimSpec-corrected)
and `reflectance_nosc` (uncorrected); I verified `reflectance_nosc == pi*Lw/Ed`
exactly, so these are **rho_w, not Rrs** (Rrs = rho_w/pi).

**Q1 — What is this dataset *for* in IOPtics?** WATERHYPERNET carries no truth
IOPs and no Chl, so none of the existing truth-scored metrics apply. Is the intent
(a) Rrs-space closure only — fit, score the Rrs residual, and compare algorithm
*self-consistency* / retrieved-IOP spread with no truth; (b) a match-up target to
be joined later against an external IOP/Chl source (PANGAEA, satellite, PI data);
or (c) purely a spectral-shape exploration for now, no sweep?
>A. I believe there are IOPs and other in-situ measurements.  I will find out, but assume so for now.  Add to the report this glaring absence, however.

**Q2 — Which reflectance product?** The release notes call `reflectance_nosc`
"definitely recommended" at the turbid sites (LPAR, MAFR, O1BE) because the
SimSpec-corrected `reflectance` is "known to be poor" there. Do we (a) always use
`reflectance_nosc`, (b) always use `reflectance`, or (c) use `reflectance` except
at the three turbid sites? And do you want the stored quantity to be Rrs
(= rho_w/pi) or rho_w?
>A. Let's use (c) for now.  I'll ask the experts for further guidance too.

**Q3 — Wavelength trim and grid.** README says <400 nm, >900 nm and ~762 nm
(O2-A) are unreliable and not recommended. Trim to 400-900 nm and notch 762?
Separately, the **HYPSTAR grid changes with instrument serial number** — GAIT,
LPAR, MAFR and VEIT_H each contain two different grids (1536-1541 points,
~0.49 nm), while PANTHYR is a fixed 237-point 355-945 @ 2.5 nm grid. Keep each
record on its native grid (the adapter contract allows it) or resample everything
to one common grid — and if so, which (PANTHYR 2.5 nm? a 5 nm hyperspectral grid?
PACE bands?)?
>A. Right now we are just exploring, so no need to trim or resample yet. 

**Q4 — Scope.** All 11 sites / 56,669 spectra, or a subset? Note the per-site
imbalance: VEIT_H alone is 17,668 files (31%) while WRUK is 889. If we subset, by
what — per-site cap, one spectrum per day, a date window, specific sites?
>A. How about we aim for a ~100 repreesentative spectra per site?

**Q5 — HYPSTAR and PANTHYR: one dataset or two?** They have genuinely different
schemas (dims, dtypes, variable names: `std_reflectance` vs `reflectance_std`,
`irradiance` vs `downwelling_irradiance_mean`) and very different spectral
resolution. Register as one `WATERHYPERNET` adapter that normalises both, or two
(`WHN_HYPSTAR` / `WHN_PANTHYR`) so results are never silently pooled? VEIT is
co-located for both, which would make a nice cross-system check.
>A. I like keeping them separate with `WHN_HYPSTAR` and `WHN_PANTHYR` adapters.

**Q6 — Uncertainty / fit weights.** The release reports **no** uncertainty budget
(`unc_comps = []`, and the README calls uncertainties "not yet mature"). The
`std_*` variables are scan-to-scan radiance variability only — and in the HYPSTAR
files I sampled `std_reflectance` is entirely NaN. Options: (a) use `std_*` as
`Rrs_err` where finite and fall back to the flat 5% `insitu` model otherwise
(what PANGAEA does today), (b) always flat 5%, (c) a fixed floor you'd prefer.
>A. Let's use (a) but with a fall back of 10%

**Q7 — QC and negative reflectance.** `quality_flag` was 0 in every one of the
3,300 files sampled (HYPSTAR has a 30-bit flag definition; PANTHYR's is
placeholder `flag1..flag8` and, with `_FillValue=0`, xarray masks it). So the
release looks pre-filtered. But negative reflectance is common and *deliberately*
retained — 100% of sampled BEFR/GAIT/THFR/VEIT_H/WRUK files contain some negative
band (min -0.039 at LPAR). Do we (a) pass them through untouched, (b) drop
records with negatives in the fit window, (c) drop records where the blue/green
peak itself is negative? This materially changes how many spectra are fittable.
>A.  Do not drop negative Rrs.  I will ask about QC algorithms

**Q8 — Where does the loader live?** Follow the GLORIA/PANGAEA pattern —
`ocpy.insitu.waterhypernet` doing the I/O, thin `WATERHYPERNETAdapter` in
`ioptics/datasets.py` — or keep everything in IOPtics? (`ocpy/insitu/` currently
has only `gloria.py` and `pangaea.py`; nothing WATERHYPERNET exists anywhere yet.)
>A. Let's put the loader in ocpy.  I have moved onto a `whn` branch

**Q9 — obs_id and an index.** Scanning 56k files per sweep is not viable. I'd
propose building a manifest parquet once (site, system, datetime, rel. azimuth,
sza/vza, path, grid id) and keying `obs_id` off it. Filename stem as the id? Note
WRUK has 345 acquisition-timestamp collisions (two azimuths, same `sequence_id`),
so site+timestamp alone is not unique.
>A. That sounds fine, but we aren't doing a sweep yet.  We are just exploring.

**Q10 — How much do you want written down?** Should `context/WATERHYPERNET.md` be
(a) a data-description doc only, or (b) data description + the adapter/loader
design decisions (the answers above), so it doubles as the implementation spec?
>A. Let's do (a) for now. 

### Explore — round 2

**Two of your answers rest on facts I had wrong or unverified, so I checked first.**

**R2-Q1 — The IOPs are definitively not in this release; where should I look?**
You said to assume in-situ IOPs exist. They are not in RELEASE_2. I read every
variable and global-attribute name in 440 files spanning all 11 sites: the sets
are perfectly constant (29 variables HYPSTAR, 22 PANTHYR) and contain nothing
optical-in-water — no absorption, backscatter, chlorophyll, TSS, turbidity,
salinity (the only name that even pattern-matched was `system_temperature`, an
instrument housekeeping attribute, and it is NaN). The release notes agree:
"The core business of HYPERNETS is to provide uniquely valuable in situ
measurements of hyperspectral water reflectance" (p.4), and the word
absorption/chlorophyll/IOP appears nowhere in the document. So: is the companion
data (a) a separate WATERHYPERNET/HYPERNETS product or portal I should be
pointed at, (b) PI-held data per site (the notes name a PI per site) you will
request, or (c) an entirely different archive we match up to? **I have recorded
this absence prominently, as you asked.** One lead from the notes: AERONET-OC is
co-located at VEIT, CBUS, TBBE and LPAR — though that is also radiometry, not
IOPs.
>A. I will find out, but for now don't worry about it.

**R2-Q2 — Your Q6 answer was based on a wrong fact of mine; please re-decide.**
I reported that HYPSTAR `std_reflectance` was all-NaN. That was wrong. It is
present and fully finite in **all 220 files I sampled across all 11 sites**, both
`std_reflectance` and `std_reflectance_nosc` (PANTHYR likewise). Typical
magnitude, median over 450-650 nm of std/|reflectance|: VEIT_P 0.8%, CBUS 1.1%,
MAFR 1.5%, WRUK 1.6%, VEIT_H 1.9%, BEFR 2.1%, GAIT 2.5%, O1BE/LPAR/TBBE 2.5-2.7%,
THFR 2.9% (the `_nosc` values run slightly higher, 1.0-4.0%). So the measured
sigma is always available and your 10% fallback would essentially never fire.
Given that — and given this std is **scan-to-scan variability only**, excluding
calibration and glint-correction systematics, so it understates true uncertainty
— do you want (a) sigma = std as-is, (b) sigma = max(std, X% of Rrs) with a floor
you choose, or (c) keep the flat 10% regardless and ignore the std?
>A. Go with (a)

**R2-Q3 — You did not answer the rho_w vs Rrs half of Q2.** Both products are
rho_w. I recommend the loader store **Rrs = rho_w/pi** (and sigma = std/pi) so
records are directly comparable with L23/PANGAEA/GLORIA and need no special-
casing downstream. Confirm? Also, on your (c) choice: the notes name exactly
LPAR, MAFR and O1BE as sites where the corrected `reflectance` is poor. Is the
`nosc` switch exactly those three, or do you want it per-system (all PANTHYR on
one product) or per-site-configurable?
>A. I confirm.  Let's go with exactly those 3 for now.

**R2-Q4 — What does "representative" mean for the ~100 per site?** The sites are
not comparable in coverage: BEFR is 2023-06 to 2024-01 only, WRUK is a single
year (2024) over 7 months, CBUS 7 months, GAIT 9 — only 6 of 11 sites see a full
seasonal cycle. So pick the axis: (a) uniform in time (every Nth spectrum,
date-sorted — simple, reproducible, but VEIT_H's 17,668 and WRUK's 889 sample
very differently in density); (b) stratified by year x month; (c) stratified by
**optical diversity** — cluster the normalised spectra and sample across
clusters, which is what actually matters for exercising IOP algorithms; (d)
stratified by solar zenith. My preference is (c) with (a) as a tiebreak. Also:
11 site-directories x 100 = ~1,100 spectra, and VEIT counts twice (VEIT_H and
VEIT_P) — is that what you want? And should the sample be forced to cover both
azimuths where they exist (LPAR 4670x270 vs 1312x090; WRUK 476x270 vs 413x225)
and both instrument serials at the four HYPSTAR sites that changed instrument
(each has its own wavelength grid)?
>A. Yes, go with (c)

**R2-Q5 — What should exploration actually produce?** You said no trim, no
resample, no sweep — just explore. So what do you want to look at: a per-site
summary table (N, date span, sza range, Rrs magnitude/shape stats), per-site
median spectrum with percentile envelopes, a spectral-shape/OWT clustering view,
band time series, or something else? And where do the figures go — IOPtics
`papers/`, ocpy `nb/`, or a scratch location?
>A. Let's do:
   - A per site summary Table
   - A figure showing all the WHN locations on the globe
   - A figure indicating the amount of data at each site
   - Per-site median spectrum with percentile envelopes
   - A spectral-shape/OWT clustering view
   - Band time series

Put the Python scripts and figures in the `context/WHN` folder


**R2-Q6 — Code placement, now that the loader is going in ocpy.** Confirmed ocpy
is on the `whn` branch. Should the *exploration* script/notebook also live in
ocpy (`nb/` or `papers/`), or stay in IOPtics? And do you want a skip-guarded
`ocpy/tests/test_waterhypernet.py` following the `test_pangaea.py` pattern, given
the data are not bundled?
>A. Stay in IOPtics, in `context/WHN`.  Yes, have the skip-guarded test.

## Logs

### 2026-09-15 — Explore prompt 1 (survey, no code written)

- Read the Context files: `ioptics/runs/prototypes/expb_giop/run_v1.yaml` and
  `build_v1.py` (L23-only today; datasets resolved through the
  `ioptics.datasets` registry).
- Reviewed the adapter contract in `ioptics/datasets.py` —
  `obs_ids(**opts)` + `load_obs(obs_id) -> RawObs(wave, Rrs, truth, Rrs_err,
  meta)`, `register_dataset(...)`. Three precedents: `L23Adapter` (synthetic,
  full spectral truth), `PANGAEAAdapter` (per-family native grids, no
  `Rrs_err` -> flat 5%), `GLORIAAdapter` (hyperspectral + measured per-band
  std -> genuine `insitu` weights, scalar-only truth).
- Confirmed no WATERHYPERNET loader exists in `ocpy.insitu` (only `gloria.py`,
  `pangaea.py`) or in IOPtics. `context/` was empty.
- Surveyed `$OS_COLOR/WATERHYPERNET/RELEASE_2` with a Fable agent (read-only):
  file counts/sizes per site, filename grammar, full NetCDF structure for one
  HYPSTAR and one PANTHYR file, QC flag definitions, and the Release-2 notes PDF
  (`0_README/WATERHYPERNET_ReleaseNotes_2-0.pdf`).
- Spot-verified by hand: 56,669 `.nc` / 9.8 GB; BEFR HYPSTAR file = 1539 bands,
  350.14-1099.75 nm, `quality_flag=0`, 75 negative bands; O1BE PANTHYR file =
  237 bands, 355-945 nm, `quality_flag` masked by `_FillValue=0`.
- Established the product definition numerically: `reflectance_nosc` /
  (`water_leaving_radiance` / Ed) = 3.1416 = pi exactly for both systems, while
  the SimSpec-corrected `reflectance` gives 3.20 (HYPSTAR) / 2.96 (PANTHYR).
  So both products are **rho_w**, `water_leaving_radiance` is the *uncorrected*
  Lw, and **Rrs = rho_w / pi**.
- Key blocker for a sweep: the release contains **no truth** (no IOPs, no Chl,
  no TSS) and **no uncertainty budget**. Questions posed above; no code written
  and nothing modified under `$OS_COLOR`.

### 2026-09-15 — Explore prompt 2 (answers reviewed, round 2 posed)

- Read the round-1 answers. Two of them rested on claims that needed checking
  before a second round was worth asking, so I verified both.
- **Correction to my own round-1 report:** I stated HYPSTAR `std_reflectance`
  was "entirely NaN". It is not. Sampling 20 files per site x 11 sites (220
  files), `std_reflectance` and `std_reflectance_nosc` are **fully finite in
  every file**, read both with netCDF4 auto-masking on and off with `_FillValue`
  excluded explicitly. Median std/|reflectance| over 450-650 nm ranges 0.8%
  (VEIT_P) to 2.9% (THFR). The Q6 answer (10% fallback) was made on the wrong
  premise and is re-asked as R2-Q2.
- **Verified the absence of IOPs.** Union of all variable and global-attribute
  names over 440 files spanning all 11 sites: constant at 29 vars / 57 attrs
  (HYPSTAR) and 22 vars / 58 attrs (PANTHYR). No absorption, backscatter,
  chlorophyll, TSS, turbidity or salinity variable exists anywhere; the only
  regex hit was the housekeeping attribute `system_temperature` (NaN).
- Extracted the full text of `0_README/WATERHYPERNET_ReleaseNotes_2-0.pdf`
  (6 pages, 14,605 chars) and searched it: no mention of IOPs, chlorophyll, TSS
  or water sampling anywhere. p.4 states the network's "core business" is
  hyperspectral water reflectance. The only in-situ lead is AERONET-OC, noted as
  co-located at VEIT, CBUS, TBBE and LPAR. Negative reflectance is retained
  deliberately (p.2: "metrologically entirely valid", and filtering biases the
  statistics).
- Filename-only coverage census (no file opens): per-site year/month/hour spans
  and azimuth-token counts. Key result for the ~100-per-site sample — only 6 of
  11 sites span a full seasonal cycle; BEFR (2023-06..2024-01), WRUK (2024 only),
  CBUS (7 months) and GAIT (9 months) do not. Azimuth counts re-derived
  independently and they match round 1.
- Confirmed ocpy is on branch `whn`; reviewed the `ocpy.insitu` house pattern
  (`gloria.py` / `pangaea.py`: `$OS_COLOR/<DATASET>` path resolution, module-level
  loaders, skip-guarded tests).
- Two Fable agents launched for the census work died without reporting after
  ~30 min (over-specified prompts: per-file double reads plus per-band stats over
  ~1,650 files each). Redone directly with narrower scans, as described above.
- No code written; nothing modified under `$OS_COLOR`; `context/` still empty.

### 2026-09-15 — Explore prompt 3 (exploration finished; scripts, figures, context doc)

Built to the round-2 answers: `reflectance` except LPAR_H/MAFR_H/O1BE_P
(`reflectance_nosc`); Rrs = rho_w/pi and sigma = sigma(rho_w)/pi; archive sigma
used as-is, no floor; optical-diversity sampling; no trim, no resample; negatives
kept; code and figures in `context/WHN`; skip-guarded test.

- **`context/WHN/whn_explore.py`** — data layer. Stage 1 indexes all 56,669 files
  from their filenames alone (both grammars parse; zero unparsable). Stage 2
  reads 400 spectra per site spread uniformly through each site's record (4,400
  total, **zero read failures**), clusters the L2-normalised 400-800 nm shapes
  across all sites at once (KMeans k=8, seed 1234), and apportions each site's
  100 spectra across the clusters it occupies by largest remainder, min one per
  occupied cluster, spread in time within a cluster. L2 rather than area
  normalisation because retained negatives can drive an integral to zero.
- **`context/WHN/whn_figures.py`** — `summary_table.{csv,md}` plus the five
  requested figures in `figs/`: site map (world + Europe inset), data volume
  (bar + month x site coverage heatmap), per-site median spectra with 25-75 and
  10-90 envelopes, clustering view (cluster shapes, per-site composition,
  absolute-unit cluster medians, blue-green vs magnitude scatter), and band time
  series at 490/560/665 nm.
- **`context/WHN/test_whn_explore.py`** — 14 tests, Tier 1 logic + Tier 2
  `@needs_whn`. All pass; full suite **282 passed**.
- **`context/WHN/WATERHYPERNET.md`** — the context document (data description
  only, per Q10), leading with the absence of IOPs.
- Intermediates (index/pool/sample parquet, spectra npz) go to
  `$OS_COLOR/IOPtics/whn_explore/`, not the repo, per the artifact split.

Findings added beyond rounds 1-2:

- **Optical range is wide.** Median Rrs(560) spans 0.0030 sr^-1 (WRUK) to 0.036
  (MAFR), a factor of 12; blue-green Rrs(490)/Rrs(560) spans 0.52 (BEFR) to 1.03
  (VEIT_H). Sites occupy distinct clusters rather than one continuum.
- **Grid count corrected.** Counting distinct (n_bands, start) pairs rather than
  band count alone: GAIT, LPAR, MAFR and VEIT_H each carry 2 HYPSTAR grids
  (MAFR's two instruments both give 1538 bands but start 0.18 nm apart). PANTHYR
  sites have used 2-3 sensor serials each but the 237-band grid never changes.
- **quality_flag verified myself** this time: 0 in all 440 files checked (40 per
  site, raw values with masking off). The earlier 3,300-file figure came from the
  agent survey and is not repeated in the doc.
- **A negative-spectrum cluster exists** (n=9 of 4,400): spectra negative across
  most of the range. Retained, not dropped, per the release policy.
- Three bugs found and fixed while building: netCDF4 cannot fill an integer
  variable with NaN (PANTHYR `quality_flag` is uint8 with `_FillValue=0`), which
  killed every PANTHYR read until the cast-to-float-first fix; cartopy silently
  auto-selects a finer Natural Earth scale for a zoomed extent and blocks on the
  download (scales now pinned); and cartopy does not clip annotation text, so
  out-of-extent site labels distorted the saved map.

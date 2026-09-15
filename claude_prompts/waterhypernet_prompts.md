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
We are going to eventually write a context file in named `context/WATERHYPERNET.md`.
First, ask me a series of questions in the Q&A/Explore section below.  
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

**Q2 — Which reflectance product?** The release notes call `reflectance_nosc`
"definitely recommended" at the turbid sites (LPAR, MAFR, O1BE) because the
SimSpec-corrected `reflectance` is "known to be poor" there. Do we (a) always use
`reflectance_nosc`, (b) always use `reflectance`, or (c) use `reflectance` except
at the three turbid sites? And do you want the stored quantity to be Rrs
(= rho_w/pi) or rho_w?

**Q3 — Wavelength trim and grid.** README says <400 nm, >900 nm and ~762 nm
(O2-A) are unreliable and not recommended. Trim to 400-900 nm and notch 762?
Separately, the **HYPSTAR grid changes with instrument serial number** — GAIT,
LPAR, MAFR and VEIT_H each contain two different grids (1536-1541 points,
~0.49 nm), while PANTHYR is a fixed 237-point 355-945 @ 2.5 nm grid. Keep each
record on its native grid (the adapter contract allows it) or resample everything
to one common grid — and if so, which (PANTHYR 2.5 nm? a 5 nm hyperspectral grid?
PACE bands?)?

**Q4 — Scope.** All 11 sites / 56,669 spectra, or a subset? Note the per-site
imbalance: VEIT_H alone is 17,668 files (31%) while WRUK is 889. If we subset, by
what — per-site cap, one spectrum per day, a date window, specific sites?

**Q5 — HYPSTAR and PANTHYR: one dataset or two?** They have genuinely different
schemas (dims, dtypes, variable names: `std_reflectance` vs `reflectance_std`,
`irradiance` vs `downwelling_irradiance_mean`) and very different spectral
resolution. Register as one `WATERHYPERNET` adapter that normalises both, or two
(`WHN_HYPSTAR` / `WHN_PANTHYR`) so results are never silently pooled? VEIT is
co-located for both, which would make a nice cross-system check.

**Q6 — Uncertainty / fit weights.** The release reports **no** uncertainty budget
(`unc_comps = []`, and the README calls uncertainties "not yet mature"). The
`std_*` variables are scan-to-scan radiance variability only — and in the HYPSTAR
files I sampled `std_reflectance` is entirely NaN. Options: (a) use `std_*` as
`Rrs_err` where finite and fall back to the flat 5% `insitu` model otherwise
(what PANGAEA does today), (b) always flat 5%, (c) a fixed floor you'd prefer.

**Q7 — QC and negative reflectance.** `quality_flag` was 0 in every one of the
3,300 files sampled (HYPSTAR has a 30-bit flag definition; PANTHYR's is
placeholder `flag1..flag8` and, with `_FillValue=0`, xarray masks it). So the
release looks pre-filtered. But negative reflectance is common and *deliberately*
retained — 100% of sampled BEFR/GAIT/THFR/VEIT_H/WRUK files contain some negative
band (min -0.039 at LPAR). Do we (a) pass them through untouched, (b) drop
records with negatives in the fit window, (c) drop records where the blue/green
peak itself is negative? This materially changes how many spectra are fittable.

**Q8 — Where does the loader live?** Follow the GLORIA/PANGAEA pattern —
`ocpy.insitu.waterhypernet` doing the I/O, thin `WATERHYPERNETAdapter` in
`ioptics/datasets.py` — or keep everything in IOPtics? (`ocpy/insitu/` currently
has only `gloria.py` and `pangaea.py`; nothing WATERHYPERNET exists anywhere yet.)

**Q9 — obs_id and an index.** Scanning 56k files per sweep is not viable. I'd
propose building a manifest parquet once (site, system, datetime, rel. azimuth,
sza/vza, path, grid id) and keying `obs_id` off it. Filename stem as the id? Note
WRUK has 345 acquisition-timestamp collisions (two azimuths, same `sequence_id`),
so site+timestamp alone is not unique.

**Q10 — How much do you want written down?** Should `context/WATERHYPERNET.md` be
(a) a data-description doc only, or (b) data description + the adapter/loader
design decisions (the answers above), so it doubles as the implementation spec?

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

# The RT-ladder experiment: what we ran, what it says, and where it lives

*IOPtics debrief, 2026-09-21. The experiment is the one specified and logged in
`claude_prompts/rt_tests.md` (Goal, Q&A rounds 1–10, Logs 2026-09-05 →
2026-09-18). Every number below is either **(P)** recomputed here directly from
the sweep parquets / chain files / run logs under
`$OS_COLOR/IOPtics/runs/`, or **(L)** quoted from a dated log entry in
`rt_tests.md` and attributed as such. Nothing is quoted from memory. Interpreter:
`/home/xavier/miniconda3/envs/ocean14/bin/python`; `$OS_COLOR =
/home/xavier/Oceanography/data/Color`.*

---

## 1. What the experiment is

**One IOP model, five radiative transfers.** The whole design is a controlled
substitution: the inherent-optical-property parameterization is held *fixed* at
`expb_pow` (ExpBricaud absorption + power-law backscattering) while the forward
model that turns (a, b_b) into R_rs is swapped five ways. Any difference between
two rows of a result table is therefore the radiative transfer and nothing else.
The five rungs are registered opt-in by
`ioptics.algorithms.registry.register_rt_variants()` — they are deliberately not
in the standard algorithm seed.

| # | Rung | The physics it adds |
|---|---|---|
| 1 | `expb_pow_ztt_el` | **ZTT analytic, elastic.** retrieve-or-bust's closed-form Zaneveld–Twardowski–Tonizzo relation; no learned component, no inelastic source terms. |
| 2 | `expb_pow_hyb_el` | **Hybrid, elastic.** The same analytic core plus the L23-trained neural correction (`robust_hybrid`), valid over 350–750 nm. Still elastic. |
| 3 | `expb_pow_hyb_ram` | **+ Raman.** Adds the Raman-scattering source term to the hybrid elastic base. |
| 4 | `expb_pow_hyb_ramfl` | **+ chlorophyll fluorescence.** Adds the ~685 nm Chl-a emission line (double-Gaussian emission in the fits). |
| 5 | `expb_pow_hyb_ramflcdom` | **+ CDOM fluorescence — the full stack.** Adds the third inelastic process via the Hawes et al. (1992) excitation–emission kernel (`robust.rt.cdom_fl`), driven by a fixed-fraction CDOM proxy **a_cdom = 0.8 × a_dg** (`bing.rt.defs.CDOM_FRACTION_DEFAULT`, Q32). |

The "configured" headline contest throughout is rung 2 vs rung 5 — elastic
hybrid against the full inelastic stack — so that the learned emulator is held
constant and only the inelastic physics varies. Rung 1 exists to price the
emulator itself.

### Why three sweeps and not one

A sweep carries exactly **one** noise convention, so the arms had to split
(Q53). The fixed-vs-free treatment of `B_p` — the phase-function /
backscattering-ratio parameter the robust forward models require — then split
along the same lines:

| Sweep id | Population | Noise model | `B_p` | k | Bands |
|---|---|---|---|---|---|
| `rt_tests_A_l23_v1` | **3,320** L23 X=4 synthetic spectra (the full set, Q54) | `pace` (absolute per-band) | **free**, prior U[0.004, 0.05] (Q51) | 6 | 71 |
| `rt_tests_A_pangaea_v1` | **97** frozen PANGAEA/NOMAD ids | `insitu` (flat 10% fallback) | **fixed at 0.01** (Q52) | 5 | 5–11 |
| `rt_tests_B_v1` | **100** frozen PACE OCI pixels | per-pixel `Rrs_unc` from the granule | **free** (Q51) | 6 | 136 |

*(P — band counts, k and populations read from `results_scalar.parquet`;
conventions from `ioptics/runs/prototypes/rt_tests/run_rta_l23.yaml`,
`run_rta_pangaea.yaml`, `run_rtb.yaml`.)*

`B_p` was kept **free** on L23 and PACE deliberately — the point was to show it
is *not* well constrained, not to hide that (Q51). It was **fixed** on PANGAEA
because at 5–11 bands a sixth free parameter makes many NOMAD spectra
underdetermined by construction (Q52); fixing it kept all 97 ids fittable in
principle.

Three data populations, three different questions: L23 X=4 is the only one with
**inelastic truth** (HydroLight computed Raman and Chl-fluorescence into the
radiances), so it is the only arm where "which forward model is *right*" can be
asked against truth. PANGAEA-97 is real in-situ radiometry with real IOP truth
but thin spectra. PACE-100 is real satellite radiance with no truth at all, so
there the only population statement possible is truth-free: *how much does the
physics move the retrieval*. The frozen id lists are committed:
`ioptics/runs/prototypes/rt_tests/pangaea97_ids.csv` and `pace100_ids.csv`.

All fits ran both χ² and **full MCMC** (emcee, 16 walkers, 40,000 production
steps, thinned by 20; verified from the chain NPZ headers — P). Window 400–750
nm on the A arms.

---

## 2. Headline results

### 2.1 The ladder verdict differs by population — that is the finding

ΔBIC below is **BIC(`hyb_el`) − BIC(`hyb_ramflcdom`)**, MCMC, spectra both rungs
fitted successfully: **positive favours the full inelastic stack.**

| Arm | n | median ΔBIC | % favouring full stack | % strongly (ΔBIC > 10) |
|---|---|---|---|---|
| **L23 X=4** | 3,300 | **+2.14** | **70.6%** | **16.5%** |
| **PANGAEA-97** | 72 | **−1.08** | 31.9% (→ **68.1% favour elastic**) | 0.0% |
| **PACE-100** | 99 | **+1.21** | 51.5% | **30.3%** |

*(P — recomputed twice: from `metrics_pairwise.parquet` (`contest == 'dbic'`,
`configured == True`, `stratum == 'all'`, `fit_method == 'mcmc'`) and
independently by pivoting `BIC` out of `results_scalar.parquet` per obs_id.
Both agree: L23 median +2.140, frac>0 = 0.7064, frac>10 = 0.1652; PACE median
+1.207, frac>0 = 0.5152, frac>10 = 0.3030; PANGAEA median −1.0845, frac>0 =
0.3194, frac>10 = 0.0000. These reproduce the 2026-09-17 and 2026-09-18 log
entries exactly.)*

Read together:

- **On synthetic data with inelastic truth, the inelastic stack wins, but
  modestly.** A median ΔBIC of +2.1 is "positive evidence", not decisive; only
  one scene in six is a strong win. The ladder is detecting a real signal the
  data-generating model genuinely contains, and it is a few-percent signal.
- **On thin real in-situ spectra the inelastic terms do not pay for
  themselves.** Elastic is slightly favoured and there are *no* strong inelastic
  wins at all. The χ²ᵥ medians say why: they **rise** for the fluorescence rungs
  (P: `ztt_el` 1.663, `hyb_el` 1.450, `hyb_ram` 1.528, `hyb_ramfl` **2.096**,
  `hyb_ramflcdom` **1.940**). On 6–11 bands under a flat-10% error, adding an
  emission line you cannot resolve costs fit quality *and* parameters. This is a
  real result about band-limited retrievals, not a bug.
- **On real PACE radiances the distribution is bimodal.** The median is barely
  positive (+1.2, 51.5%) but **30.3% of pixels favour the full stack strongly
  (ΔBIC > 10)** while 23.2% disfavour it just as strongly (P). For about a third
  of PACE pixels the inelastic physics matters a great deal; for the rest it is
  noise. A single median hides this completely — which is exactly why the
  truth-free fractional-change figure was built as that arm's headline.

### 2.2 χ²ᵥ medians per rung (MCMC, ok rows) — P

| Rung | L23 | PANGAEA | PACE |
|---|---|---|---|
| `ztt_el` | 1.124 | 1.663 | 0.423 |
| `hyb_el` | 1.136 | 1.450 | 0.558 |
| `hyb_ram` | 1.137 | 1.528 | 0.595 |
| `hyb_ramfl` | **1.069** | 2.096 | 0.501 |
| `hyb_ramflcdom` | 1.076 | 1.940 | 0.537 |

On L23 the **fluorescence** term — not Raman — is what moves χ²ᵥ (1.136 →
1.069). PACE's sub-unity χ²ᵥ across the board reflects a conservative per-pixel
`Rrs_unc`.

### 2.3 How far the physics moves the retrieval (truth-free) — P

Median fractional change in the retrieved decomposition from `hyb_el` to
`hyb_ramflcdom` (MCMC posterior medians, nearest band to 443 nm), computed with
`ioptics.diagnostics.fractional_change_data`:

| Arm | band | a_ph | a_dg | b_bp |
|---|---|---|---|---|
| L23 | 445 nm | −11.1% | +8.3% | −29.5% |
| PANGAEA | 443 nm | −68.7% | +37.8% | −23.9% |
| **PACE** | 442 nm | **+4.6%** | **+1.4%** | **−21.1%** |

The PACE row reproduces the figures quoted in the 2026-09-18 task-14 log
(a_ph +5%, a_dg +1%, b_bp −21%, n = 99). The consistent message across all three
populations is that **backscattering is what the inelastic physics really
moves** (−21% to −30% at blue wavelengths) — the inelastic source terms supply
blue-green radiance that the elastic model had to buy with b_bp.

### 2.4 Accuracy against truth, L23 (MCMC, per rung) — P

From `docs/source/reports/rt_tests_A_l23_v1/rt_ladder_mcmc_all.csv`. MAE in the
table's units; `cov68` is 68% credible-interval coverage.

| Rung | a(440) MAE | a(440) cov68 | b_b(555) MAE | b_b(555) cov68 |
|---|---|---|---|---|
| `ztt_el` | 0.0533 | 0.656 | 0.2631 | 0.000 |
| `hyb_el` | 0.0523 | 0.625 | 0.1919 | 0.018 |
| `hyb_ram` | 0.0510 | 0.595 | 0.0592 | 0.515 |
| `hyb_ramfl` | 0.0587 | 0.594 | 0.0471 | 0.635 |
| `hyb_ramflcdom` | **0.0495** | **0.696** | 0.0523 | 0.586 |

The striking column is **b_b(555) coverage**: the two elastic rungs are at
0.0–0.018 — their credible intervals essentially never contain the truth —
while adding Raman lifts coverage to 0.52 and the fluorescence rungs to
0.59–0.64. The elastic models are not merely biased in backscattering; they are
*confidently* biased. Every `hyb_ramflcdom` accuracy cell carries the
`no_CDOMfl_truth` caveat (see §3).

### 2.5 Chain health

**(L, 2026-09-17 and 2026-09-18 entries):** across 25 sampled chains per rung
per A-sweep, integrated autocorrelation τ (raw steps) had medians 360–744 and a
maximum of 1,853 against 40,000-step chains → **ESS median ≈ 840–1,730, minimum
337**. For RT-B, 15 sampled chains per rung: τ medians 318–595 → **ESS median
1,048–1,962, minimum 162**. Healthy everywhere, with no rung- or
dataset-dependence of concern. (Acceptance fractions are not persisted in the
chain NPZs, so ESS/τ is the health metric.)

**(P — independent re-sample, this session):** 15 randomly chosen chains per
rung per sweep, τ taken as the **maximum** over parameters rather than the mean,
gives ESS medians 666–1,445 with a minimum of 166. Same conclusion (healthy,
thousands of effective samples); the numbers differ from the logged ones because
of the different sample draw and the stricter per-parameter reduction. Where the
two disagree, prefer the logged pair — it used the larger 25-chain sample on the
A arms.

### 2.6 `B_p` posteriors sit above the emulator's trained span — P

The hybrid emulator was trained over `B_p ∈ [0.0103, 0.018]`. The free-`B_p`
posterior medians land **above** it:

- L23: per-rung medians **0.0262–0.0295** (all five rungs above 0.018).
- PACE: per-rung medians **0.0163–0.0242** (`ztt_el` 0.0163, the four hybrid
  rungs 0.0202–0.0242).

*(P. Note a small discrepancy with the 2026-09-17 log, which recorded RT-B
`B_p` medians as "0.020–0.028" from a 15-chain sample; over the full 99-pixel
population the range is 0.0163–0.0242, with the low end set by the `ztt_el`
rung — which is the analytic backend and so not subject to the emulator's
domain at all. The substance is unchanged: every hybrid rung sits above 0.018.)*

Edge pile-up against the prior is negligible (L, 2026-09-17: ≤0.3% of samples
within 2% of the 0.004 floor, ≤2.3% near the 0.05 ceiling) — the posteriors are
not being pinned by the prior, they genuinely prefer values the emulator was
never trained on. This is the accepted Q50(c) caveat and it is the single most
important limitation of the hybrid rungs.

### 2.7 The PAB consistency check: PASS — P

`rt_tests_B_v1`'s `hyb_el` rung was matched pixel-for-pixel against PAB's
`run1k` stored Gordon-elastic ExpBPow posteriors
(`ioptics/runs/prototypes/rt_tests/pab_consistency.py`, output
`tables/pab_consistency{,_summary}.csv`). **99 of 99 pixels matched.**

- The two pipelines fitted **identical data**: max |ΔR_rs| = 0 and max |Δ var
  R_rs| = 0 across all 136 bands.
- Posterior-median correlations: **A_dg 0.987, S_dg 0.939, A_ph 0.965, B_nw
  0.998, β 0.935**.
- Median (ours − PAB): −0.010 (A_dg), −0.0007 (S_dg), +0.022 (A_ph), **+0.048
  (B_nw)**, −0.078 (β).
- Derived **Chl ratio ours/PAB: median 1.053**, 16–84% [0.94, 1.36],
  log-correlation 0.965.

The only systematic is the **+0.05 dex in B_nw**, which is the expected imprint
of the elastic-model swap (`robust_hybrid` sits above Gordon in R_rs by 1.4–3.7%)
plus the extra free `B_p`. Nothing else moved. **PASS.**

### 2.8 Completeness, refusals, and what was excluded — P

| Sweep | MCMC records | ok | poor_fit | out_of_scope | fit_failed | chains written |
|---|---|---|---|---|---|---|
| `rt_tests_A_l23_v1` | 16,600 (3,320 × 5) | 16,518 | 27 (0.16%) | 55 | 0 | **16,545** |
| `rt_tests_A_pangaea_v1` | 485 (97 × 5) | 390 | 85 (17.5%) | 0 | 10 | **475** |
| `rt_tests_B_v1` | 500 (100 × 5) | 495 | 0 | 5 | 0 | **495** |

- **The 11 L23 out-of-scope scenes.** 55 out-of-scope MCMC rows = exactly
  **11 distinct scenes × 5 rungs** (P: `obs_id.nunique() == 11`). Because the
  red-peak screen rejects them identically on every rung, the ladder stays
  fair — no rung is scored on a population another rung was spared.
- **PANGAEA's 2 five-band refusals.** The 10 `fit_failed` rows are obs_ids
  **26563 and 26564**, both with `n_bands = 5` against `k = 5` — underdetermined
  and refused up front by `run.UnderdeterminedFitError`, not crashed (P:
  `n_bands` and `k` read off the failed rows). 95 of 97 ids were fittable, as
  designed.
- **PACE:** one pixel excluded by the red-peak screen, identically on all five
  rungs.
- **Zero tracebacks** in either run log (P: `grep -c Traceback` → 0 in both
  `rt_tests_A_run.log` and `rt_tests_B_run.log`).
- **Nothing folded into the leaderboard.** All three sweeps carry
  `leaderboard: false` in `provenance.yaml` (schema 4) and the board contains
  zero `rt_tests_*` rows (P, verified §5). Five near-clones of one algorithm
  under five physics packages are not a cross-algorithm standing.

### 2.9 Timing — P

Per-rung wall-clock spans on `rt_tests_A_l23_v1` (from chain-file mtimes,
3,309 chains per rung, 20 cores):

| Rung | span |
|---|---|
| `ztt_el` | 21.0 h |
| `hyb_el` | 22.4 h |
| `hyb_ram` | 33.2 h |
| `hyb_ramfl` | 35.6 h |
| `hyb_ramflcdom` | **41.1 h** |
| **sum** | **153.3 h** |

**The inelastic terms roughly double the per-fit cost** (21–22 h elastic → 33–41
h inelastic). The L23 arm ran 6.6 days wall (launched 2026-09-10 05:34 PT,
finished 2026-09-16 19:24 PT), overshooting the 4.5–6-day estimate because of
~2 days of competing load mid-run (L, 2026-09-17). PANGAEA's arm was 2.6 h of
rung-span and RT-B 3.9 h (P), the latter completing in **4.8 h wall** on
2026-09-17 (L).

---

## 3. Caveats — read these before quoting anything above

These are the accepted limitations, faithful to the decisions recorded in
`rt_tests.md`. Each one is also carried in the limitations block of each of the
three report pages.

1. **Nadir-only geometry.** θ_v = 0 and Δφ = 0 **everywhere**, on all three
   arms. No off-nadir viewing was tested, on synthetic, in-situ or satellite
   data.
2. **CDOM absorption is a fixed-fraction proxy.** `a_cdom = 0.8 × a_dg`
   (Q32, `bing.rt.defs.CDOM_FRACTION_DEFAULT`). The CDOM-fluorescence rung is
   therefore driven by a scaled version of a quantity the fit is
   simultaneously retrieving — it is *not* an independent CDOM measurement.
3. **Packaged-sky E_d.** Downwelling irradiance comes from
   retrieve-or-bust's packaged `ed_l23.npz` table, not from a per-observation
   atmosphere. Every fluorescence rung inherits that spectrum.
4. **Learned corrections off.** `corrections=False` throughout. The "hybrid"
   in `robust_hybrid` is the elastic emulator only.
5. **The hybrid emulator is evaluated outside its trained domain, on
   purpose.** The free-`B_p` prior is U[0.004, 0.05]; the emulator's trained
   span is [0.0103, 0.018]; the posteriors sit **above** the trained span
   (§2.6). This was accepted, not clamped (Q50(c)), and it produced a
   DomainWarning on essentially every hybrid-backend fit — 13,619 warned MCMC
   records on the A arms (L, 2026-09-17; P: 27,232 `DomainWarning` lines in
   `rt_tests_A_run.log`, 792 in `rt_tests_B_run.log`). **Any hybrid-rung result
   is an extrapolation of the emulator.** On PANGAEA, where `B_p` is fixed at
   0.01, that value sits 2.6% *below* the trained span — the same acceptance.
6. **The L23 truth does not contain CDOM fluorescence, and its Chl-fl line
   shape differs from the fits'.** L23 X=4 has Raman and chlorophyll
   fluorescence but **no** CDOM fluorescence, and it used a **single**-Gaussian
   emission line where the fits used a **double** Gaussian. Every accuracy cell
   for `expb_pow_hyb_ramflcdom` on the L23 arm therefore carries the
   `no_CDOMfl_truth` caveat — **exactly 80 rows in
   `metrics_scalar.parquet`, all of them (L23 × `ramflcdom`), and zero caveat
   rows in the PANGAEA and PACE sweeps** (P, verified this session; matches the
   2026-09-17 log). The rung-5 numbers in §2.4 are being scored against a truth
   that lacks one of rung 5's processes.
7. **Robust's CDOM-fluorescence path is analytic-only and unvalidated.** The
   Hawes-kernel implementation has no HydroLight cross-check behind it; that
   validation is RoB milestone **M6** and has not happened (Q41). Rung 5 is the
   least-trusted rung on the ladder.
8. **PANGAEA's noise is invented.** PANGAEA V3 quotes no per-band R_rs
   uncertainty, so the arm runs on the flat-10% `insitu` fallback (Q52/Q53).
   The PANGAEA χ²ᵥ values and every ΔBIC on that arm inherit that assumption.
   (This is the same scoring issue documented at length in
   `reports/pangaea_fits_report.md`.)
9. **PACE has no truth.** Every truth-referenced panel is absent from the RT-B
   page by design; its red bands are noisy and its per-pixel `Rrs_unc` is
   conservative (hence χ²ᵥ ≈ 0.4–0.6).

---

## 4. How to view everything

### The three RT-ladder report pages

| Arm | Repo path | Published URL (see note) |
|---|---|---|
| L23 X=4 | `docs/source/reports/rt_tests_A_l23_v1/rt_ladder.rst` | `https://ioptics.readthedocs.io/en/develop/reports/rt_tests_A_l23_v1/rt_ladder.html` |
| PANGAEA-97 | `docs/source/reports/rt_tests_A_pangaea_v1/rt_ladder.rst` | `https://ioptics.readthedocs.io/en/develop/reports/rt_tests_A_pangaea_v1/rt_ladder.html` |
| PACE-100 | `docs/source/reports/rt_tests_B_v1/rt_ladder.rst` | `https://ioptics.readthedocs.io/en/develop/reports/rt_tests_B_v1/rt_ladder.html` |

> **Note — these URLs are not live yet.** The three pages exist only on the
> local `rt-tests` branch (HEAD `3a7d6cb`), which is 8 commits ahead of
> `origin/develop`; `git ls-tree origin/develop docs/source/reports/` shows no
> `rt_tests_*` directories. The URLs above are the addresses the pages **will**
> have once `rt-tests` is merged to `develop` and Read the Docs rebuilds. Until
> then, build locally.

Each page carries, in order: an overview derived from the artefacts (rungs
present, n spectra, window, noise tag, `B_p` free or fixed, truth or not); the
limitations block (§3 above); the fractional-change headline at ~443 nm; the
ladder tables (MCMC then χ²); retrieved-vs-true panels, ratio histograms and
accuracy-vs-wavelength where truth exists; ΔBIC CDF and histogram for the
configured pair under both fit methods plus the all-pairs contest table;
head-to-head verdicts; accuracy and QC tables; and a "not shown" section. The
PACE page additionally carries the **"Consistency with PAB's fits of the same
pixels"** section (§2.7).

### Building the docs locally

```bash
cd /mnt/tank/Oceanography/python/IOPtics
sphinx-build -W -b html docs/source docs/_build/html   # -W = warnings are errors, as CI runs it
# or:  make -C docs html
```

Read the Docs itself builds `docs/source/conf.py` with `fail_on_warning: false`
(advisory), per `.readthedocs.yaml`.

### Raw artefacts

Everything lives under `$OS_COLOR/IOPtics/runs/<sweep_id>/` for each of
`rt_tests_A_l23_v1`, `rt_tests_A_pangaea_v1`, `rt_tests_B_v1`:

- `results_scalar.parquet`, `results_spectral.parquet` — one row per
  (obs, rung, fit_method).
- `metrics_scalar.parquet`, `metrics_spectral.parquet`,
  `metrics_pairwise.parquet` — the scored reductions; the ΔBIC contests are
  `metrics_pairwise` rows with `contest == 'dbic'`.
- `chains/<rung>_<dataset>_<stem>.npz` — the full MCMC chains (16 walkers ×
  40,000 steps, thinned 20), plus the observed `Rrs`/`varRrs` handed to the
  fitter.
- `figures/`, `tables/` — the display assets the report page was built from.
- `provenance.yaml` — schema 4, carrying the `leaderboard: false` flag.

### Frozen populations and run logs

- `ioptics/runs/prototypes/rt_tests/pangaea97_ids.csv` — the 97 NOMAD ids
  (criteria in the file header; generated by `derive_pangaea97.py`).
- `ioptics/runs/prototypes/rt_tests/pace100_ids.csv` — the 100 PACE pixels
  (extracted by `extract_pace_100.py`).
- L23 needs no id list: the arm is all 3,320 X=4 spectra.
- `$OS_COLOR/IOPtics/runs/rt_tests_A_run.log` (17.7 MB, the 6.6-day A run) and
  `$OS_COLOR/IOPtics/runs/rt_tests_B_run.log` (604 KB, the 4.8-h B run), with
  their detached runners `rt_tests_A_runner.sh` / `rt_tests_B_runner.sh`
  alongside.

### Re-running or extending

`ioptics/runs/prototypes/rt_tests/build_v1.py` is the staged driver — stage 1
runs the A sweeps, 3 runs RT-B, 2/4 compute metrics, **stage 5 builds the
report pages** (`('rta_pangaea', 'rta_l23', 'rtb')`, skipping any arm whose
sweep has no results). Configs: `run_rta_l23.yaml`, `run_rta_pangaea.yaml`,
`run_rtb.yaml`, all heavily annotated with the Q-references behind each choice.

---

## 5. What changed in the codebases

Four repositories moved to make this experiment possible. **Nothing is merged
to a default branch and nothing here was committed by this session** — JXP runs
git.

| Repo | Branch | HEAD (read-only `git log --oneline -3`) |
|---|---|---|
| **bing** | `rob_cdom` | `bf56f6d ok` / `87a7a1c mo` / `1d624b8 chl` |
| **retrieve-or-bust** | `inelastic-rt` | `e1f4289 off nadir` / `5ca740d Merge pull request #21 from ocean-colour/cdom-rt` / `0fd2e0b 10` |
| **IOPtics** | `rt-tests` | `3a7d6cb v2 is close?` / `5890c81 PhD` / `92eea90 runnin` |
| **ocpy** | `pace_giop` | `c3132a6 unc` / `3aed28a Merge PR #19 (gloria)` / `0ac5340 Merge PR #18` |

**bing (`rob_cdom`)** — the CDOM-fluorescence path. `bing/rt/defs.py` grew
`include_CDOM_fl` and `cdom_fraction` (default `CDOM_FRACTION_DEFAULT = 0.8`),
bringing `rt_dict_from_p` to its **twelve-key** surface: seven legacy Gordon
toggles (`variable_Gordon`, `variable_Gordon_G0`, `variable_Gordon_bbp`,
`include_Raman`, `include_Chl_fl`, `phi_C`, `double_gaussian`) plus five
backend keys (`rt_backend`, `fit_Bp`, `Bp_value`, `include_CDOM_fl`,
`cdom_fraction`). The new keys take **real defaults, never `None`**, so any
legacy `p` or pickled `rt_dict` still describes a valid Gordon-backend
configuration. `bing/evaluate.py` carries the source term and the a_dg → a_cdom
proxy, and `validate_rt_dict` checks the configuration once at fit setup.

**retrieve-or-bust (`cdom-rt` → merged into `inelastic-rt`)** — the physics.
`robust/rt/cdom_fl.py` implements the Hawes excitation–emission kernel
(`cdom_kernel`, `cdom_excitation_grid`) as the third inelastic process, wired
through `Inelastic(cdom_fl=...)` in `robust/rt/types.py` — **default `None`, so
the elastic path stays bit-identical**. `robust/solar.py` is the solar-zenith
utility added for IOPtics' geometry resolution.
`robust/rt/validation.py::cdom_gradient_report` is the diagnostic. PR #21 merged
`cdom-rt` into `inelastic-rt` **during the RT-A run**; bing's CDOM tests (30/30)
and IOPtics' RT tests (43/43) were re-verified green against the new HEAD before
RT-B launched (L, 2026-09-17).

**IOPtics (`rt-tests`)** — all the plumbing:
- `ioptics/config.py`: **`dataset_opts`**, a `{dataset: {option: value}}`
  mapping, which is how `L23: {X: 4}` selects the inelastic HydroLight
  realization.
- `ioptics/algorithms/spec.py`: **`RTOptions`** gained the five backend fields
  (`rt_backend`, `fit_Bp`, `Bp_value`, `include_CDOM_fl`, `cdom_fraction`),
  mapping 1:1 onto bing's twelve-key `rt_dict` through
  `AlgorithmSpec.to_bing_p`.
- `ioptics/run.py`: **`resolve_geometry`** — every `robust_*` backend *requires*
  an observation geometry; the solar zenith is never silently defaulted.
- **`B_p` outputs**: `B_p` / `sig_B_p` columns on `results_scalar`, and `B_p`
  appended as the trailing element of every saved chain when `fit_Bp` is true.
- **Provenance schema 4** with the sweep-level **`leaderboard` flag**
  (`report/leaderboard.py::_leaderboard_enabled`), which is what keeps the three
  RT sweeps off the board.
- **PACE adapter** (`ioptics/datasets.py::PACEAdapter`) — the only adapter that
  reads a pre-extracted artifact (`$OS_COLOR/IOPtics/pace_pab_100/`) rather than
  going through ocpy.
- **The RT-ladder page type**: `ioptics/report/rt_ladder.py`, supported by
  `diagnostics.fractional_change_data`, `plotting.fractional_change_hist`,
  `plotting.dbic_hist`, and `report/figures.py`'s `rt_fractional_change` /
  `dbic_hist` / `dbic_cdf_method`; plus
  `ioptics/runs/prototypes/rt_tests/pab_consistency.py` and the test modules
  `tests/test_report_rt_ladder.py` and `tests/test_rt_tests.py`.

**Test state (P, this session):** `env -u OS_COLOR python -m pytest -q` →
**516 passed, 61 skipped, 4 warnings** in 247 s, exit 0.

---

## 6. Housekeeping: the Q54 transfer consolidation (2026-09-21)

The 2026-09-17 Mac→`profx` transfer left two trees staged at
`$OS_COLOR/IOPtics/transfer_2026-09-17/` because they collided with copies
`profx` already held (`rt_tests.md` Round 10, Q54; JXP: *"use your
recommendation"*). Resolved this session; a `README.md` recording the outcome
now sits in that directory.

1. **`multi_L23_PANGAEA_v2` parquets — `profx`'s kept** (the later 2026-08-10
   run). Untouched.
2. **The Mac's `figures/`/`tables/` were not copied — they are redundant.**
   Re-running that sweep's stage-3 build
   (`report.standard.build_exemplars` + `build(..., kind='cross_algorithm')`;
   `build_landing()` deliberately **not** called) against `profx`'s parquets
   reproduced the committed page **exactly**: every PNG and every CSV
   byte-identical, `exemplar_fits.rst` byte-identical, and `cross_algorithm.rst`
   differing only in three randomly generated Bokeh embed UUIDs. The regenerated
   file was restored from the scratchpad snapshot, so the docs tree is
   byte-identical to `HEAD`. The committed page had **already** been rebuilt
   from `profx`'s parquets before this session (in `3a7d6cb`; its provenance
   stamp reads `Generated: 2026-08-10T15:02:31Z`), which is why regeneration is
   a no-op now.
3. **`leaderboard.parquet` — `profx`'s kept, and
   `report.leaderboard.update()` is a byte-identical no-op**: the fold had
   already happened on 2026-09-18. The board carries **788 rows over five
   sweeps** — `expb_giop_L23_mcmc_full` 120, **`expb_giop_L23_test20` 90**
   (transferred), **`gloria_turbid_v3` 160** (transferred),
   `multi_L23_PANGAEA_v2` 268, `pangaea_fits_v2` 150 — and **zero
   `rt_tests_*` rows**, as intended.
4. The staged directory (202 MB) is left in place for JXP to decide on
   deletion. Nothing committed or published depends on it.

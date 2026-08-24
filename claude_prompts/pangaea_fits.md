# IOPtics — Why the PANGAEA in-situ fits fail

## Goal

Find out why the open-ocean IOP models return a usable retrieval for only **5–28%**
of PANGAEA spectra while returning one for **~99%** of L23's, and say which part of
that gap is a real physical limit, which is a scoring artifact, and which is a bug in
our own pipeline. **Exit criterion:** every percentage point of the gap is attributed
to a named cause with a diagnostic behind it, and the report says plainly which
causes we fixed, which we cannot fix, and which turn out not to have been failures at
all.

Modelled on the GLORIA investigation (`claude_prompts/coding_prompts_stage06.md`
Tasks 8–15 → `reports/gloria_fits_report.md`), which is the standard to match: a
round-by-round record that **states its own corrections** rather than quietly
absorbing them. That report's most valuable content is the places it was wrong.

Deliverables: `reports/pangaea_fits_report.md` with figures, the scripts that made
them at `reports/scripts/pangaea_fits_report.py`, and — if the conclusions warrant
it — changes to IOPtics.

## Conventions

- `ocean14`; docstrings; **JXP runs all git commands**; after each task run
  `pytest -q`, add to Q&A, add to the Logs.
- **Q&A holds open questions for JXP** — pose them, do **not** self-answer.
- Run tests via the env interpreter directly:
  `/Users/xavier/miniforge3/envs/ocean14/bin/python`. Run the suite **without**
  `$OS_COLOR` (CI-equivalent) before declaring a task done, and with it when the task
  touches real artifacts.
- `sphinx-build -W` on `docs/source` must stay green. Check the exit code **without a
  pipe** — `$?` through `| tail` is tail's status, which has bitten this project.
- Long real-data work belongs in a script under `reports/scripts/`, never in the test
  suite (the `conftest` hang guard is load-bearing and a hang is a finding).
- Figures go through `ioptics.style` so the report matches the site.
- Use Fable where it helps.

## Context

### Where the number comes from

The bounded `multi_L23_PANGAEA_v2` sweep (Stage 7 Task 11): {L23, PANGAEA} ×
{`expb_pow`, `giop`, `gsm`}, χ², PANGAEA restricted to its 1 593 spectral-truth ids.
Retrieval success:

| dataset | `expb_pow` | `giop` | `gsm` |
|---|---|---|---|
| L23 (synthetic) | 99.8% | 98.9% | 99.0% |
| PANGAEA (in-situ) | **19.5%** | **26.6%** | **3.4%** |

### What the reconnaissance already established

A read-only diagnostic pass over the wider 3 896-id variant of that sweep. **These are
measured, not hypotheses** — the investigation should start from them, not re-derive
them. (Numbers below are from the 3 896-id run; the committed sweep is now the
1 593-id one, so re-confirm the headline rates before quoting them.)

**It is at least four different failures.** Status shares for `expb_pow` /
`giop` / `gsm`: `poor_fit` 47.6 / 54.1 / 79.2%, `fit_failed` 30.3 / 9.3 / 3.5%,
`out_of_scope` 3.4 / 8.6 / 12.2%.

1. **Most of `poor_fit` may not be a fit failure at all.** PANGAEA V3 ships **no
   per-band Rrs uncertainty**, so `prep` falls back to a flat 5% — every χ²ᵥ on this
   dataset is `(rel_misfit / 0.05)²`, and χ²ᵥ = 5 therefore means only ~11% RMS
   misfit. Measured: **38–56% of `poor_fit` rows have a median relative misfit under
   10%**, and their water is *statistically indistinguishable* from `ok` water
   (median Chl 0.42–0.74 vs 0.23–0.68 mg m⁻³). A large part of the headline number
   may be a fit that misses by <10% being scored against an invented error bar.
2. **`n_bands = k` is a deterministic kill, and our own adapter admits it.**
   `PANGAEAAdapter.obs_ids(min_rrs=5)` enumerates spectra with ≥5 finite bands, and
   `expb_pow` has k = 5. **All 315 five-band observations failed under `expb_pow`**,
   every one with `LinAlgError: SVD did not converge` — underdetermined by
   construction. `giop` (k=3) fits the same spectra at a **76%** ok rate.
3. **`maxfev` fixes the crash but not the fit.** Re-fitting 40 `fit_failed` spectra
   with `maxfev=40000`: 29/40 had failed on scipy's default budget, and **28 of the 30
   with ≥6 bands then converged — but only 1 became `ok`.** The rest migrated into
   `poor_fit`/`out_of_scope`. Raising the budget would cut `expb_pow`'s `fit_failed`
   from 30% to a ~9% deterministic floor (five-band + non-positive-Rrs spectra) and
   move ~1 300 rows from "crashed" to "honestly scored".
4. **Turbidity is the GLORIA failure again, but capped.** 14% of PANGAEA peaks
   redward of 560 nm; `fit_failed` is 35–57% red-peaked against that 14% base rate,
   and `out_of_scope` χ²ᵥ medians run 80–144. Real, and at most ~14% of the dataset.
5. **Cruise-level systematics.** NOMAD is 81% of the sample and contributes 81% of
   the failures — so it is *not* "three bad cruises". But per-subdataset ok rates span
   **0% to 83%**, and three NOMAD cruises (`oceania1998`, `oceania2000`, `i8si9n`)
   are **100% converged and 100% `poor_fit`** — a uniform moderate misfit across a
   whole cruise, which smells like calibration or convention rather than physics.
6. **Killed hypothesis: sparse bands as a general cause.** Beyond the exact `n = k`
   case the correlation runs the *other* way — low-band spectra fit better (`giop`
   76% ok at 5 bands vs 28% overall). Do not spend time here.
7. **The L23 contrast is not a noise-model confound.** 15 L23 spectra prepped under
   both `pct:0.05` and native `pace` fit 60/60 ok either way. L23 is self-consistent
   by construction — the perturbation added equals the error assumed — so ~99% is
   near-guaranteed. What is *not* comparable between the datasets is the χ²ᵥ scale.

### Two pipeline defects the reconnaissance turned up

Both make the persisted tables misleading and should be fixed early, since everything
downstream reads them:

- **`n_bands` is 0 on every `fit_failed` row** (`ioptics/io.py`, filling
  `st.get('n_bands', 0)` from `_failed_result`'s empty stats dict in
  `ioptics/run.py`). A reader counting bands from `results_scalar` gets zero for
  exactly the rows they most want to diagnose; the true count is only recoverable from
  the spectral table's `Rrs_obs` rows.
- **Nothing refuses an underdetermined fit.** A spectrum with `n_bands ≤ k` cannot
  constrain the model, and we discover that as an `LinAlgError` deep in scipy rather
  than as a status we chose.

## Prompts

### Coding

1. Characterise and attribute the gap (below).
2. Read my Task-1 answers and continue; add example fits to the report.
3. Literature: what do published in-situ IOP comparisons report for retrieval
   success on compilations like PANGAEA/NOMAD, and how do they score it?
4. Propose changes based on what you found. **Describe them and ask; do not
   implement yet.**
5. Implement what I approve.
6. NOMAD cruise provenance.

### Pull Requests

1. Review the PR for this work and post it to GitHub; investigate any CI failures and
   fix them. Log your work.
2. Read the PR comments, make the needed changes, add any new questions to Q&A, log.

## Modules

### Tasks

1. **Characterise and attribute.** Reproduce the headline rates on the committed
   1 593-id sweep, then split the gap into named causes with a figure for each. The
   ranked hypotheses, in the order the evidence supports them:

   a. **Re-score on a noise-model-free statistic.** The one number that owes nothing
      to the invented 5%: median relative misfit. Report ok-rates under (i) the
      current χ²ᵥ ≤ 5, (ii) a GLORIA-style inflated floor (10%, 15%), and (iii) a
      relative-misfit threshold. If the rate moves from 19/27/3% to something like
      50–70%, then most of the "failure" is metric calibration and the report should
      say so in its first paragraph. If `gsm` stays low while the others rise, that is
      model rigidity and a genuinely different finding.
   b. **Fix the two pipeline defects above**, then re-run and report how many rows
      move. Expect ~1 300 of the `fit_failed` rows to become honestly-scored fits and
      the residue to be a *deterministic* floor you can name exactly.
   c. **Per-subdataset residual spectra.** Mean `Rrs_model − Rrs_obs` against
      wavelength, per cruise, for the 0%-ok-but-100%-converged cruises against a
      high-ok cruise. A common spectral signature across a whole cruise is a
      calibration/convention issue. Control for peak wavelength and `n_bands` — they
      are confounded with cruise (16-band spectra are specific NOMAD collections).
   d. **The red-peaked 14%.** Run the `register_turbid` variants on them. Given GLORIA
      (where all four variants returned the *same* fit) the expected answer is "no
      improvement", and a *confirmation* on a second dataset is worth having.

   Write `reports/pangaea_fits_report.md` + `reports/scripts/pangaea_fits_report.py`.
   Q&A. Log.

2. **Continue.** Per my Task-1 answers. Add example fits — the same clear→turbid
   ordering the exemplar pages use, and at least one from a 100%-`poor_fit` cruise.
   Q&A. Log.

3. **Literature.** What retrieval-success rates do published comparisons report on
   in-situ compilations, and against what error model? If the field routinely assumes
   a floor rather than a measured uncertainty, that is directly relevant to (1a).
   References with DOIs. Q&A. Log.

4. **Propose.** Given the above, what should change — in the scoring, in the adapter,
   in the models, or in what the site claims? Describe and ask; do not implement.
   Q&A. Log.

5. **Implement** what I approve. Q&A. Log.

6. **NOMAD cruise provenance** (added per JXP's Task-1 Q&A answer). The tidy
   tables carry one processing-chain key: `contributor` (PI/instrument group,
   inherited from SeaBASS via NOMAD), and coverage stratifies hard on it —
   giop ok-rates run 0% (Stramski, 78 spectra / 4 cruises; Morrison) through
   52% (Siegel, 374 / 63) to 72% (Bélanger), all at ~100% convergence. Chase
   the instrument/processing provenance behind the low-ok contributors: the
   NOMAD documentation (Werdell & Bailey 2005, doi:10.1016/j.rse.2005.07.001),
   SeaBASS cruise metadata for the never-ok cruises, and the Valente et al.
   (2022) V3 source notes. Goal: say whether the common residual signature is
   instrument/processing convention or water type. Q&A. Log.

### Q&A

> Open questions for JXP. Pose them; do not self-answer.

- **Is a 5% assumed error the right default for a dataset that quotes none?** It sets
  the χ²ᵥ scale for every PANGAEA number we publish, and at 5% a fit that misses by
  11% is already "not a solution". GLORIA's investigation ended up using a 10% floor.
  Should PANGAEA use one too, and if so should the *published* status thresholds move
  with it or stay fixed so sweeps remain comparable?
>A. Yes, PANGAEA should use a 10% floor. The published status thresholds should stay fixed so sweeps remain comparable.
- **Should `out_of_scope` be assigned before fitting rather than after?** It is
  currently a post-hoc label on a poor fit whose Rrs peaks red. Assigning it up front
  from the spectrum alone would separate "we declined to fit this" from "we fitted it
  and it failed" — but it would change what every existing sweep's counts mean.
>A. Yes, out_of_scope should be assigned before fitting rather than after. We will need to sweep again.
- **May I ask you to fast-forward the `bing` sibling checkout to `main`?** On this
  workstation `/mnt/tank/Oceanography/python/bing` is on `PAB_edits`, a strict
  ancestor of `origin/main` 18 commits back — before `chisq_fit.fit(maxfev=...)` and
  the turbid `Pow2`/`Pow2Flat` models. Every IOPtics χ² fit `TypeError`s against it
  (the suite showed 1 failure + 6 errors from this alone). `git checkout main &&
  git pull` loses nothing (working tree clean bar two untracked CSVs). Task 1 ran
  with a read-only `git archive` copy of bing@`f242b0e` on `PYTHONPATH`; the report
  script assumes bing ≥ that commit.
>A. Done.
- **Should refused underdetermined fits get their own status?** The new guard
  records them as `fit_failed` with true `n_bands`/`k` (identifiable as
  `n_bands ≤ k`), which keeps `STATUSES` and every existing count stable. A
  dedicated `underdetermined` status is cleaner but changes what every sweep's
  coverage block means — same trade-off family as the pre-fit `out_of_scope`
  question above.
>A. Keep as fit_failed
- **Should the shipped `maxfev` default for the open-ocean algorithms rise to
  40 000 (the turbid variants' budget)?** At scipy's default, 30% of `expb_pow`'s
  PANGAEA rows "crash"; at 40 000 the `fit_failed` floor is 5.9% and fully named
  (63 underdetermined + 28 non-positive-Rrs + 3). But only 7 recovered rows become
  `ok`, and changing the registry default changes every future sweep — Task 1 used
  per-sweep overrides and left the default alone.
>A. Yes, the default should rise to 40000.
- **Should `PANGAEAAdapter.obs_ids`' `min_rrs=5` default rise?** It admits spectra
  that are underdetermined by construction for k = 5 models (63 of the 1 593). The
  guard now refuses them cleanly, but enumeration could exclude them instead —
  at the cost of making the id set algorithm-dependent.
>A. Yes, the default should rise to 5.
- **Is cruise-level processing/calibration metadata reachable for NOMAD?** The
  never-ok cruises share a common residual signature (model ~20–40% low at
  520–570 nm, high at ~660 nm; controls flat). Distinguishing water-type
  spectral-shape mismatch from per-cruise calibration/convention needs
  instrument/processing provenance we don't have in the tidy tables.
>A. I don't have the provenance, but you are encouraged to try to find it.  Add that to your task list.
- **`min_rrs` — did you mean 6?** Your answer to "should `obs_ids`'
  `min_rrs=5` default rise?" was "Yes, the default should rise to 5" — but 5
  is the current value, so I could not tell whether you meant **6** (= k+1
  for the k=5 models, excluding underdetermined-by-construction spectra from
  enumeration) or **keep 5** (the guard now refuses them cleanly as
  `fit_failed`). Left at 5 pending your answer; nothing else in Task 2
  depended on it.
- **Should the published coverage block gain a community-equivalent validity
  row?** Task 3 found the field's operational acceptance test for
  semi-analytical IOP retrievals is NASA's GIOP-DC validity: component
  bounds + **mean relative Rrs misfit ≤ 33% over 400–600 nm** (no χ², no
  measured error; GIOP ATBD doi:10.5067/ZGBW3QECROJ2), and Werdell et al.
  (2013) report "GIOP-DC ran successfully on 90% of stations in NOMAD".
  Scored that way, our force-fitted PANGAEA rates are **89.4/92.8/93.1%** —
  right on their 90%. Publishing a `frac_valid` under that criterion beside
  `frac_ok` would make the site's numbers comparable to the literature
  (χ²ᵥ ≤ 5 answers a stricter question nobody else publishes). Add it in
  Task 5, or keep the coverage block as is?
- **How should the committed site sweep be regenerated under the new
  defaults?** "We will need to sweep again" — agreed, and the code now runs
  the approved semantics by default. But `multi_L23_PANGAEA_v2` is a *mixed*
  sweep with one sweep-level noise model (`pct:0.05` for both datasets). Under
  the new rules the natural form is **two native-noise sweeps folded into the
  leaderboard** (L23 under `pace`, PANGAEA under `insitu` → 10% imputed) —
  the design's intended pattern — rather than one uniform `pct:0.1`. Which do
  you want published, and should it replace `multi_L23_PANGAEA_v2` on the
  site or sit beside it as `_v3`? (`pangaea_fits_v2` under
  `$OS_COLOR/IOPtics/runs/` is the PANGAEA half, already run.)

**Task-4 proposals** (full descriptions with sketches and blast radii in
`reports/pangaea_fits_report.md` § Round 4; each needs a yes/no/modify —
none is implemented):

- **A2 — persist per-fit `rel_misfit` on `results_scalar`?** One float
  column written at result assembly; the investigation's most-used number,
  currently recomputed from ~5M spectral rows on every use.
>A. yes 

- **A3 — stamp the error model on every published rate?** Site pages print
  the noise provenance ("scored against `pct:0.1` — imputed...") wherever
  coverage appears. Templates only.
>A. yes
- **A4 — robust per-band loss (soft-L1), park or explore?** Would defuse
  the en372-style one-band kills, but changes the estimator, breaks χ²ᵥ
  comparability across sweeps, and needs bing-side changes. My
  recommendation: park until the forward-model work lands.
>A. park
- **B1 — per-record spectral-shape quality score, as annotation not
  exclusion?** QWIP (closed-form, cheap) now; Wei et al. QA score (23
  water-type tables, NOMAD-proven) if the reference tables check out.
  Gives Task 6 an instrument-artifact signal per cruise.
>A. yes
- **B2 — carry `subdataset` + `contributor` onto `results_scalar`?** Two
  nullable columns; turns per-cruise/per-contributor coverage into a
  groupby. Task 6 needs it.
>A. yes
- **B3 — non-positive Rrs bands: trim at prep (my recommendation), refuse
  the spectrum, or leave as-is?** The 28-spectrum floor carries unphysical
  weights under a fractional noise model; trimming (provenance-tagged)
  salvages the 10–15 good bands each spectrum typically has.
>A. Leave as is.  Because of uncertainty, Rrs bands can be negative.
- **C1/C2 — agreed that no model work happens now?** Red-peaked fraction
  waits for your forward model (the `fits_turbid` machinery is ready to
  test it); the common-signature cruises route to Task 6 as a data
  question.
- **D2 — caveat the L23 ~99% on the site?** One sentence: noise-free
  synthetic scored under its own assumed noise, so ~99% is near-guaranteed.
>A. yes
- **D3 — one-line scope-rule note where coverage is shown?** So 11.8%
  `out_of_scope` reads as "declined pre-fit", not a failure mode.
>A. yes
- **B1 follow-up — the Wei QA reference tables are MATLAB-only.** The
  distribution page (oceanoptics.umb.edu/score_metric/) ships MATLAB code
  with the 23 water-type bounds embedded — no Python port, no standalone
  tables. QWIP is implemented and already earning its keep (the `nomad_en372`
  near-miss spectrum scores **−0.207**, outside the paper's ±0.2 screening
  threshold, while a clear `ok` spectrum scores −0.025). Options for Wei QA:
  (a) port the tables out of the MATLAB source into a vendored data file
  (attribution note; moderate effort), (b) leave QWIP as the sole shape
  annotation, or (c) revisit during Task 6 if QWIP proves insufficient.
  Which?
- **Task 6 residue — dig or park?** Three open-ocean, QWIP-clean cruise
  groups remain unexplained (`ant-xxiii-1` Polarstern/SPMR 31% median miss;
  `i8si9n` CLIVAR 19%; `amlr2004` — PRR-800 era yet never-ok, the one
  contradiction to the winched-MER story). Next step would be per-cruise
  processing forensics: pull the SeaBASS data-file headers (login needed —
  do you have SeaBASS credentials?) and compare extrapolation/processing
  conventions against a well-fitting SPMR cruise. Dig now, or park with
  the classes documented?
- **Should the regional-optics cruises get scope treatment?** Task 6
  establishes three water classes the open-ocean family genuinely does not
  cover: subarctic seas (`oceania*` — Nordic/Arctic, where band-ratio
  bio-optics are documented to fail ~2×), estuarine (`ties*`, Chesapeake),
  and optically-shallow shelf (`wfs*`/`eh*`, bottom reflectance). The
  red-peak rule catches some but not all of their spectra. Options: a
  region/water-class flag (annotation like QWIP), an adapter-level scope
  predicate (changes counts again), or leave as poor_fit with the report's
  explanation. Which?

### Logs

### 2026-08-14 (PR task 2: address the PR #11 review comments)

**One review finding (Cursor Bugbot, medium) — confirmed real, fixed, and
pinned.** The comment: `_mcmc_subset` called `fit_mcmc` directly, bypassing
the pre-fit guards that Task 2/5 added on `run_algorithm` — so an MCMC
subset could fit (and even score `ok` on) red-peaked spectra its own χ²
pass had declined, and a `strict=True` sweep **aborted** on an
underdetermined record instead of recording the refusal.

Fix, in `ioptics/run.py`: the scope decision is factored into a shared
`_prefit_decline()` used by both `run_algorithm` and `_mcmc_subset` (so the
two entry points cannot drift apart again); the subset declines red-peaked
records `out_of_scope` before any sampling (no chain written), and catches
`UnderdeterminedFitError` ahead of the strict re-raise so the refusal is
`fit_failed` with true `n_bands`/`k` in both strict modes. New Tier-2 test:
`test_mcmc_subset_applies_the_prefit_guards`. Replied on the PR thread with
the fix description (the commit is yours to push).

No new Q&A questions arose — the finding was actionable as-is and its fix
follows decisions you already made (pre-fit `out_of_scope`; underdetermined
stays `fit_failed`).

**Verified:** suite without `$OS_COLOR` **406 passed, 41 skipped** (the new
test is Tier-2); with `$OS_COLOR` **447 passed**. `sphinx-build -W` exit
**0**, no pipe. Changes: `ioptics/run.py`, `ioptics/tests/test_run.py`.

### 2026-08-12 (Task 6: NOMAD cruise provenance — the never-ok cruises, named)

**The 1c common signature decomposes into named classes, and the largest is
an instrument era.** Deliverables: report § Round 5,
`pangaea_qwip_provenance.png`, two Task-6 sections in the report script
(QWIP×coverage; the fluorescence-trim experiment, cached under
`runs/pangaea_fits_qwip/`), two new Q&A questions. No package changes.

1. **QWIP exonerates the spectra (mostly).** The never-ok cruises are
   QWIP-clean (median −0.03 to −0.13, ~0% flagged) — naturally-shaped
   spectra missed everywhere — except `nomad_en372` at **21% flagged**, the
   highest anywhere, confirming its band-artifact class. Caveat noted in
   the report: QWIP is magnitude-invariant, so smooth calibration tilts are
   invisible to it.
2. **A hypothesis raised and refuted in one round** (recorded per the house
   rules): blue/green-peaked spectra carrying a ≥678 nm band (chlorophyll
   fluorescence, absent from the elastic forward model) fit far worse
   (12.7% vs 40.8% ok, giop). But refitting those 552 spectra with the
   band trimmed — same noise, same budget — recovers almost nothing
   (12.7→16.5% ok; misfit 0.159→0.157). The band doesn't cause the miss;
   it identifies a *cohort*.
3. **The cohort has a name.** SeaBASS/NOMAD/SIMBIOS provenance: Mitchell's
   (SIO) group used a **winched Biospherical MER-2040/2048 from the stern
   A-frame** (their own SIMBIOS report: ship-shadow-prone) through 2000,
   switching to the **free-fall PRR-800 from 2001**. The never-ok years
   (`amlr2000`, `cal9702–0004`, `jes9906`, `indoex99`) are the winched era;
   the same group's free-fall years (`amlr2002/2006`, `cal0411`) fit at
   58–75% ok **in the same waters**. Same PI, same region, different
   deployment → convention, not water.
4. **The rest classifies as:** regional bio-optics the family shouldn't
   cover — `oceania*` is *not* Baltic but Nordic/Arctic AREX (standard
   bio-optics documented to fail ~2×, Stramska et al. 2003), `ties*` is
   estuarine Chesapeake (NOMAD's only self-shading-corrected profiles),
   `wfs*`/`eh*` optically-shallow WFS; the `en372` band artifact; and an
   honest **unresolved residue** (`ant-xxiii-1` open-ocean SPMR at 31%
   miss, `i8si9n` CLIVAR at 19%, `amlr2004` PRR-era-yet-never-ok — the one
   contradiction). Q&A asks: dig into SeaBASS file headers (credentials?)
   or park; and whether the regional classes deserve scope treatment.

**Verified:** no package changes; suite without `$OS_COLOR` **406 passed,
40 skipped**; with `$OS_COLOR` **446 passed**; `sphinx-build -W` exit
**0**, no pipe.

### 2026-08-12 (Task 5: implement the approved Task-4 proposals)

**A2, A3, B1, B2, D2, D3 are in; A4 parked, B3 left as-is, and A1/C/D1
untouched (unanswered).** Package changes: `evaluate`, `io`, `metrics`,
`prep`, `records`, `datasets`, `report/standard`, `docs/source/datasets.rst`,
plus tests.

1. **A2 — `rel_misfit` persisted per fit.** Computed in
   `evaluate._assemble` next to χ² and emitted as a `results_scalar` column
   (NaN on unfitted rows and pre-2026-08-12 sweeps). `metrics.compute` now
   prefers the persisted value and falls back to its spectral-table
   reduction for older sweeps — a plain merge collided on the column name
   (caught by the suite; fixed with a fill-from-fallback).
2. **B1 — QWIP spectral-shape score, annotation only.** `prep.qwip_score`
   implements Dierssen et al. (2022) Eqs. 2–5 with coefficients verified
   digit-for-digit from the paper (regression-pinned at figure-readable
   anchors); computed in `prep_one` on the spectrum the fit sees, persisted
   as `PreparedRecord.qwip_score` → `results_scalar.qwip_score`. Documented
   multispectral caveat: spectra are linearly interpolated to 1 nm, no
   Vandermeulen sensor-specific AVW conversion. **Spot check on real
   records: the `nomad_en372` near-miss spectrum (giop misses by 1%, never
   ok) scores −0.207 — outside the paper's ±0.2 threshold — while a clear
   `ok` spectrum scores −0.025.** The community's shape metric flags the
   same spectrum our χ² flagged. Wei QA: distribution is MATLAB-only with
   embedded tables → new Q&A question (port, skip, or revisit in Task 6).
3. **B2 — `subdataset` + `contributor` persisted.** `PANGAEAAdapter`
   meta → two nullable `results_scalar` columns (None on other datasets).
   Verified on real records end-to-end with B1.
4. **A3 + D3 — the coverage sections now say what they mean.**
   `report/standard.py` QC sections (pooled + per-stratum) append a dynamic
   **Error model** line naming each dataset's per-record noise tags
   (`pct:X` spelled out as an *assumed* flat fraction), and the
   `frac_out_of_scope` description now reads "declined before fitting …
   'we declined to fit this', not 'we fitted it and it failed'".
5. **D2 — L23 caveat** in `docs/source/datasets.rst`: read L23's ~99% as a
   consistency check, not a score (noise-free by construction, scored
   against its own perturbation model).

**Not done, by your answers:** B3 (non-positive Rrs bands stay — "because
of uncertainty, Rrs bands can be negative"), A4 (parked). **Not done,
awaiting answers:** A1 `frac_valid` row, D1 site regeneration, `min_rrs`
clarification. Site pages were *not* rebuilt — the template changes land on
the next `report.standard.build`, which D1's answer governs.

**Verified:** suite without `$OS_COLOR` **406 passed, 40 skipped**; with it
**446 passed** (+3 tests: QWIP polynomial pin, QWIP edge cases, prep
attachment; plus extended schema/stats assertions). `sphinx-build -W` exit
**0**, no pipe (one iteration: RST parsed `|score|` in the new docstrings
as a substitution — escaped).

### 2026-08-11 (Task 4: propose changes — described and asked, not implemented)

**Eleven proposals across the four areas the task names, each posed as a
Q&A decision.** Deliverables: `reports/pangaea_fits_report.md` § Round 4
(descriptions, implementation sketches, blast radii) + the Task-4 block in
Q&A above. **No code, table, or site change was made.**

- **Scoring:** A1 community-equivalent `frac_valid` row (already pending
  from Task 3); A2 persist per-fit `rel_misfit` on `results_scalar`; A3
  stamp the error model on every published rate; A4 robust per-band loss —
  described but recommended *parked* (estimator change, comparability
  break).
- **Adapter/data:** B1 spectral-shape QA per record (QWIP now, Wei QA
  score if its reference tables check out) as annotation, never exclusion;
  B2 persist `subdataset` + `contributor`; B3 trim non-positive Rrs bands
  at prep (recommended) vs refuse vs leave — the named 28-spectrum floor;
  B4 `min_rrs` awaits your clarification.
- **Models:** C1 no new backscattering work — the red-peaked fraction
  waits for your forward model (1d showed variants return the same fits;
  `fits_turbid` machinery is ready to test the new model when it lands);
  C2 the common-signature cruises are a data question → Task 6.
- **Site claims:** D1 regenerate as two native-noise sweeps folded
  (recommended `_v3`, keep v2 page) — pending your earlier answer; D2
  caveat L23's near-guaranteed ~99%; D3 one-line scope-rule note beside
  coverage blocks.

**Verified:** no package changes; suite without `$OS_COLOR` **403 passed,
40 skipped**; `sphinx-build -W` exit **0**, no pipe.

### 2026-08-11 (Task 3: literature — how the field scores retrieval success)

**Nobody in the published record scores in-situ IOP inversions against a
measured Rrs error bar — they can't, and their acceptance test is a
relative-misfit threshold three times looser than anything we've used.**
Deliverables: Round-3 section in `reports/pangaea_fits_report.md` (verified
quotes + DOIs), a `giop_dc_validity()` section in the report script, one new
Q&A question. No package changes.

1. **The compilations carry no uncertainties.** NOMAD ships binary
   provenance flags, "data ... considered accurate *as is*" (Werdell &
   Bailey 2005); Valente V3 (our source; its 68 641 Rrs observations are
   exactly what the adapter enumerates) provides none and says uncertainties
   are "different and unpredictable" across sources; IOCCG Report 5 states
   the SeaBASS gap outright; GLORIA confirms it for inland/coastal SeaBASS
   entries. L23 is noise-free by construction.
2. **The 5% we assumed in Round 1 is a mission goal, not a measurement.**
   IOCCG Report 18 traces it to the SeaWiFS objectives (McClain et al.
   1992: water-leaving radiance within 5% absolute, *clear waters*).
   GLORIA's empirical reconstruction spread (5–16% green, −30/+170% UV/NIR)
   brackets our new 10% imputation, not 5%.
3. **The operational acceptance test is ΔRrs ≤ 33%.** NASA's standard IOP
   products accept an LM solution iff component bounds hold and the mean
   relative Rrs misfit over 400–600 nm is ≤ 33% (GIOP ATBD v1.0, Eqs.
   11–15); non-convergence → `PRODFAIL`. GIOP-DC's optimization is
   **unweighted** ("if reliable values of σ(λi) are not available, they are
   set to 1.0"). Werdell et al. 2013: "GIOP-DC ran successfully on **90%**
   of stations in NOMAD"; IOCCG-5 tabulates GSM at 95.8/98.5% valid (and
   warns that excluding invalid retrievals "likely" flatters statistics);
   Brewin et al. 2015 score η = "percentage of possible retrievals" and
   their supplementary χ² has no σ² denominator at all. The GSM paper
   itself (Maritorena 2002) reports **no** convergence rate, fits an
   unweighted objective, and validates against truths *derived from Chl*;
   QAA's only QC is negative-value exclusion (~95–99% "valid" by
   construction, QAA_v5 doc); and the Bayesian GIOP (Erickson et al. 2023)
   benchmarks fit quality against a "typical" 5% Rrs uncertainty and finds
   **44% of NOMAD stations exceed 25% Rrs MAE** — the field's own closure
   failure, at rates consistent with ours (their 3-par GIOP Rrs-fit MAE
   4.8±2.9% vs our converged medians 6.7–13.1%).
4. **Scored by the field's rule, our fits are normal.** Computed in the
   script (Round 3): force-fitted PANGAEA validity under ΔRrs ≤ 33% is
   **89.4/92.8/93.1%** for `expb_pow`/`giop`/`gsm` — sitting on Werdell's
   90% — vs the published 19.5/26.6/3.4% under χ²ᵥ ≤ 5 @ 5%. Directly
   confirms 1a: the headline was a scoring choice, and even the new
   10%-floor headline (43/53/38%) is stricter than community practice.
   Q&A asks whether to publish a community-equivalent `frac_valid` row.

**Verified:** no package changes; suite without `$OS_COLOR` **403 passed,
40 skipped**; `sphinx-build -W` exit **0**, no pipe.

### 2026-08-10 (Task 2: implement the Task-1 answers, example fits, Round 2)

**The approved defaults are in, and the re-swept headline matches Round 1's
prediction exactly.** Deliverables: Round-2 section in
`reports/pangaea_fits_report.md`, `pangaea_example_fits.png`, the
`pangaea_fits_v2` sweep, four package changes, two new tests, docs prose
updates, Task 6 added below.

1. **Implemented per your answers:** `prep._INSITU_PCT_FALLBACK` 0.05 → 0.10
   (tag `pct:0.1`); `registry.DEFAULT_MAXFEV = 40000` seeds every algorithm
   (`TURBID_MAXFEV` now aliases it, so contests stay budget-equalized);
   **pre-fit `out_of_scope`** via a new `AlgorithmSpec.fits_turbid` flag —
   False for the open-ocean seed (declined up front by
   `run.run_algorithm`/`run.is_red_peaked`), True for the turbid variants,
   overridable per sweep for diagnostics; provenance schema 2 → 3 records
   `fits_turbid` per block (old digests unchanged via the schema-defaults
   mechanism). Underdetermined refusals stay `fit_failed`, as you chose.
2. **New headline** (`pangaea_fits_v2`: 1 593 ids, `insitu` → 10% imputed,
   new defaults): ok = **43.2 / 52.6 / 37.6%** for `expb_pow`/`giop`/`gsm`;
   `out_of_scope` = 11.8% for all three (exactly the 188 red-peaked ids);
   `fit_failed` = 5.8/2.0/1.8% (the named deterministic floor). Round 1's
   prediction (rescore @10%, drop red) matches **to four decimal places** —
   the v2 fits are the Round-1 fits; only scoring and scope moved. Cost of
   pre-fit scope, measured: 27 of 188 red-peaked spectra would have scored
   `ok` under force-fitted `expb_pow`.
3. **Correction (caught before it shipped):** the first v2 run had
   `out_of_scope` 159≠188 for `expb_pow` — my 1d turbid comparison had
   *registered* a force-fit `expb_pow` over the registry entry and Round 2
   inherited it. Fixed (force-fit spec is local now), polluted sweep deleted
   and re-run. The new provenance field flagged it (`fits_turbid: true` in
   the sweep's provenance.yaml) — recorded in the report per the
   states-its-own-corrections standard.
4. **Example fits** (clear→turbid, report + figure): a clear ok fit
   (rel 1–5%); `nomad_en372` id 28678 — `giop` misses by a **median 1%**
   and is still `poor_fit` (one anomalous band carries χ²ᵥ over 5 with
   7 bands) — the scoring artifact in one panel; `nomad_oceania2000`
   id 16268 showing the 1c common signature (models 20–40% low at
   450–550 nm); `nomad_wfs0511` id 50274 (peak 570 nm, missed by ~50% —
   the GLORIA wall). Both middle panels are from 100%-`poor_fit` cruises.
5. **NOMAD provenance, first pass (your "try to find it"):** the tidy
   tables carry `contributor` (PI/instrument group, from SeaBASS). Coverage
   stratifies hard on it: 0% ok (Stramski 78/4 cruises, Morrison 27/3)
   through 52% (Siegel 374/63) to 72% (Bélanger), all ~100% converged —
   and Morrison's spectra miss by the *same* median 5.4% as Siegel's.
   Points at processing convention over water type (still confounded —
   Harding is Chesapeake). Full hunt is now **Task 6**.
6. **Q&A:** two new questions — your `min_rrs` answer reads as a typo
   ("rise to 5" is the current value; did you mean 6?), and how the
   committed mixed sweep should be regenerated (two native-noise sweeps
   folded vs uniform `pct:0.1`, replace `multi_L23_PANGAEA_v2` or add
   `_v3`). Docs prose updated (`datasets.rst` 10% fallback,
   `models.rst` shared budget + scope flag).

**Verified:** bing checkout confirmed on `main@f242b0e` (thanks — shim
retired). Full suite: without `$OS_COLOR` **403 passed, 40 skipped**; with
it **443 passed** (both +2 for the new tests: pre-fit decline, turbid
scope). `sphinx-build -W` exit **0**, no pipe. Package changes:
`ioptics/{prep,run,records,evaluate,provenance,datasets}.py`,
`ioptics/algorithms/{spec,registry}.py`, tests, and the two docs pages;
committed sweep tables and site pages untouched (regeneration is the Q&A
question).

### 2026-08-10 (Task 1: characterise and attribute the gap)

**The headline gap is mostly the score, not the fit.** Deliverables:
`reports/pangaea_fits_report.md` + `reports/scripts/pangaea_fits_report.py`
(7 figures under `reports/figures/pangaea_*.png`), two package fixes, one new
test. Everything below is from the committed 1 593-id sweep (reproduced
bit-for-bit on PANGAEA: ok = 19.52/26.55/3.39% for `expb_pow`/`giop`/`gsm`)
plus two PANGAEA-only control re-runs (`pangaea_fits_base`,
`pangaea_fits_maxfev` under `$OS_COLOR/IOPtics/runs/`).

1. **1a (re-scoring).** Median relative misfit of converged PANGAEA fits is
   6.7/9.0/13.1% — ~2× L23's 3.3–4.8%, not 20×. At a 10% floor the ok-rates are
   43/54/39%; at 15%, 53/71/69% (58/71/69 with the budget fix) — squarely the
   "50–70%" the prompt anticipated, so the report says "metric calibration" in
   its first paragraph. **The `gsm` rigidity hypothesis is dead**: 3.4 → 69%
   at a 15% floor (it converges on 96.7% of spectra; the 5% assumption just
   punished its fatter misfit distribution hardest).
2. **1b (defects + budget).** Fixed in `ioptics`: `run._failed_result` now
   records true `n_bands`/`k` (io defaults NaN, not 0), and a new
   `UnderdeterminedFitError` refuses `n_bands ≤ k` before scipy, in both
   strict modes (test: `test_underdetermined_fit_is_refused_as_a_status`).
   Verified the fixes move **0 of 4 779** statuses. `maxfev=40000` recovers
   308/109/25 crashed rows, of which only **7** become `ok` — the budget fixes
   the crash, not the fit; recovered `expb_pow` rows triple its `out_of_scope`
   (crashes were hiding turbid spectra). Remaining floor, named exactly:
   63 underdetermined (`expb_pow` only) + 28 non-positive-Rrs (same 28 for all
   three algorithms) + ≤3 other.
3. **1c (cruises).** 18 NOMAD cruises ≥95% converged yet ≤5% ok, spanning
   `nomad_en372` (median misfit **4.8%**, never ok — pure scoring artifact) to
   `nomad_wfs0504/0511` (49–64%, genuinely turbid). The never-ok cruises share
   a common residual signature; controls sit flat (figure in the report).
4. **1d (turbid variants).** On the 188 red-peaked ids, all four bbp variants
   return the same fits (paired median misfit 16.4–16.6%) — GLORIA's verdict
   confirmed on a second dataset; the forward model remains the suspect.
5. **Attribution table** (exit criterion) is in the report: per algorithm,
   ok / underdetermined / other-crash / out-of-scope / scoring-artifact /
   genuine-misfit sum to 100% of attempted spectra, on both the committed and
   the budget-equalized runs.

**Environment notes (this workstation).** The `bing` sibling checkout is on
`PAB_edits` (pre-`maxfev`, pre-turbid-models) — no χ² fit runs against it; I
worked around it with a read-only `git archive` of bing@`f242b0e` on
`PYTHONPATH` and put the fast-forward request in Q&A (git is yours). The docs
toolchain was absent from every env here, so I installed
`docs/requirements.txt` (sphinx, furo) into `ocean14`.

**Verified:** full suite with the bing@main shim: without `$OS_COLOR`
(CI-equivalent) **402 passed, 39 skipped**; with `$OS_COLOR` **441 passed**
(the Stage-7 laptop count plus the new test). `sphinx-build -W` exit **0**,
checked without a pipe. Package changes are limited to
`ioptics/run.py`, `ioptics/io.py`, `ioptics/tests/test_run.py`; nothing in
the committed sweep tables or site pages was modified.

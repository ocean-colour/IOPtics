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

### Q&A

> Open questions for JXP. Pose them; do not self-answer.

- **Is a 5% assumed error the right default for a dataset that quotes none?** It sets
  the χ²ᵥ scale for every PANGAEA number we publish, and at 5% a fit that misses by
  11% is already "not a solution". GLORIA's investigation ended up using a 10% floor.
  Should PANGAEA use one too, and if so should the *published* status thresholds move
  with it or stay fixed so sweeps remain comparable?
- **Should `out_of_scope` be assigned before fitting rather than after?** It is
  currently a post-hoc label on a poor fit whose Rrs peaks red. Assigning it up front
  from the spectrum alone would separate "we declined to fit this" from "we fitted it
  and it failed" — but it would change what every existing sweep's counts mean.

### Logs

# IOPtics — Improve Reporting

## Goal

Now that we have our first reports, let's make them all the better.  In presentation, detail, etc.


## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- **Q&A holds open questions for JXP** — pose them, do **not** self-answer (JXP
  answers before the next task; decisions/rationale go in the Logs).
- Run tests via the env interpreter directly
  (`/home/xavier/miniconda3/envs/ocean14/bin/python -m pytest -q`); `conda
  activate` fails non-interactively. **Run the suite without `$OS_COLOR`**
  (CI-equivalent) before declaring a task done. (`ocean14` now lives under
  `miniconda3`, not `miniforge3`; it needs `pyarrow` — now in `requirements.txt`
  — for the parquet metrics tables, plus `ocpy`/`bing` (installed editable from
  the local sibling checkouts, as `requirements.txt`'s git deps).)
- New adapters live in `datasets` (with `noise`, the only ocpy-importing modules).
- Adding an algorithm must be **one `register(...)` call** — no core changes.
- Capitalize **BING** in prose. Keep docstrings RST-clean so `sphinx-build -W`
  stays green; new public APIs are autodoc'd via `docs/source/api/index.rst`.
- **Tiered tests** (`ioptics/tests/conftest.py`): guard data-dependent tests with
  `@needs_l23` / `@needs_pangaea` / `@needs_pace`, and any test that shells out to
  Sphinx with `@needs_sphinx` (CI is pytest-only — no data tree, no Sphinx).
- The current reports, given here: `https://ioptics.readthedocs.io/en/develop/reports/`

## Context

- All of the code in this repo
- The first reports
- `docs/design/IOPtics_implementation.md` — §Data preparation (adapters table:
  PANGAEA `acdom`→`a_dg`, `bbp`→`bb_p`, scalars `chla`/`tss`; GLORIA scalar
  `a_cdom440`/`Chla`/`TSS`/`Secchi` + caveat), §Algorithm registry (`gsm` one-liner),
  §Retrieval & run / §Metrics (RT toggles, `caveat='CDOM_vs_adg'`).
- ocpy: `insitu.pangaea.{load,spectrum,file_catalog}`, `insitu.gloria.load_gloria`.
- bing: `parameters.standard.gsm`; `rt.{raman,chl_fl}` + the `rt_dict` toggles.
- **Build-script template:** `ioptics/runs/prototypes/expb_giop/build_v1.py`
  (`main(flg)`; sequential stages `1`=run, `2`=metrics, `3`=report). Stage-6's
  `build_v2.py` mirrors it.


## Prompts 

1. I want to improve the reporting for the first reports.  I want to make them more informative and more visually appealing.  I want to add more text to the reports, and I want to add more graphics.  First, let's have a conversation on them.  Remind me of where the files are located for each of them.  And ask me a series of questions in Q&A below.  Use Fable.  Log your work.

2. I have answered your questions; see the answers. One of the major goals of IOPtics is for a member of the ocean color community to use IOPtics to compare the performance of different IOP models.  We need to make it easier for them to do so.  Please suggest ways to do this in the Q&A section below.  I think it should include summary Reports for each of the datasets and algorithms.  Log your work. Use Fable.  Still no coding yet.

3. Ok, read my responses to your questions and then please update the two design docs in the `docs/design/` directory to reflect the changes we have discussed.  Log your work. Use Fable.  Then generate a new set of one or more prompt docs to execute the next steps.  Call them `improve_reporting_##.md`.

## Reports

### Where every report file lives (2026-08-03)

**What is actually published** at
`https://ioptics.readthedocs.io/en/develop/reports/` — three pages, no more:

| # | Page | Source file | Assets alongside it |
|---|---|---|---|
| 1 | Leaderboard landing | `docs/source/reports/index.rst` (2477 lines) | none — the table is inline |
| 2 | Cross-algorithm — `expb_giop_L23_test20` | `docs/source/reports/expb_giop_L23_test20/cross_algorithm.rst` (266 KB) | `scatter_a_440.png`, `scatter_bb_555.png`, `taylor_a.png`, `target_a.png`, `dbic_cdf_expb_pow_vs_giop.png`, `accuracy_chisq_all.csv`, `qc_chisq_all.csv` |
| 3 | Cross-algorithm — `gloria_turbid_v3` | `docs/source/reports/gloria_turbid_v3/cross_algorithm.rst` | same seven filenames |

Page 1's prose ends at line 48; lines 50-2472 are the auto-generated leaderboard
`list-table` between the `LEADERBOARD_START` / `LEADERBOARD_END` sentinels, and
2473-2477 is a bare `:glob: */*` toctree (which is why pages 2 and 3 appear as
undescribed links).

**The reference pages the report pages link to:** `docs/source/models.rst` (342
lines, equations), `docs/source/datasets.rst` (206 lines), plus
`docs/source/index.rst`, `installation.rst`, `api/index.rst`.

**The report that is *not* published:** `reports/gloria_fits_report.md` (708
lines) with 11 figures in `reports/figures/` and its generator
`reports/scripts/gloria_fits_report.py`. Sphinx here has no `myst_parser`, the
figures sit outside `docs/`, and nothing links to it — the site's conclusions
depend on it only through code comments.

**Generators (code):** `ioptics/report/{standard,figures,tables,bokeh,rst,leaderboard}.py`
over `ioptics/plotting.py` + `ioptics/diagnostics.py`. Hand-written doc figures:
`docs/figures/make_model_components.py`, `docs/figures/make_l23_overview.py`;
`docs/scripts/ioptics_graphic.py` (its 379 KB `_static/ioptics_graphic.png` is
referenced nowhere). Styling: `docs/source/_static/custom.css` (ocean palette),
theme **furo** in `docs/source/conf.py`.

**Heavy artifacts (not committed):** `$OS_COLOR/IOPtics/runs/gloria_turbid_v3/`
(the only sweep on this Mac: `results_*`/`metrics_*` parquet, `provenance.yaml`,
`figures/`, empty `chains/`) and `$OS_COLOR/IOPtics/leaderboard.parquet` (160
rows — `gloria_turbid_v3` × GLORIA × four algorithms, nothing else).

**Missing:** the flagship `expb_giop_L23_v1` — the full 3320-spectrum L23 sweep.
`runs/first_full_run.src` is the workstation script, and `first_sweep.md`'s log
stops at step 3a, so page 2 above is the **20-spectrum smoke**, not the real run.

### What I found wrong with them (2026-08-03)

1. **Page 3 is empty.** All five of its PNGs are blank "no data" axes — four are
   byte-identical (12 387 B). `accuracy_chisq_all.csv` is 40 rows of `n=0`/NaN.
   Cause is structural, not a bad run: `standard.py:39` hardcodes
   `_REP_REFS = [('a', 440), ('bb', 555)]`, Taylor/Target is hardcoded to
   `'a'`/440 (`:152`), and ΔBIC to `model_a='expb_pow', model_b='giop'`
   (`figures.py:114`). GLORIA has spectral truth for **none** of those — only
   `a_dg(440)`, from `a_cdom440` — and `giop` was never run in that sweep. The
   templated captions confidently explain how to read each blank panel.
2. **The prose describes figure *types*, never results.** Every paragraph is an
   f-string in `standard.py` (`_intro` `:89-109`, the `desc=` blurbs `:142-200`).
   Nothing on page 3 says what the sweep found; the real finding (all four
   backscatter models return the same fit) exists only in a hand-written note in
   `models.rst:171-186`.
3. **The most informative figures are implemented and never rendered.**
   `figures.spectra_set` (retrieved `a`/`bb` ± 68/95% bands vs truth) is only
   emitted for `kind='per_algorithm'` (`standard.py:171`), and `per_algorithm` /
   `per_dataset` have never been built. `figures.closure_set` (Rrs residual with
   χ²ᵥ) and `figures.corner_set` are never called at all, and
   `plotting.ratio_hist` / `diagnostics.ratio_hist_data` have no `figures.py`
   builder. The design doc's §Reporting promises all of them.
4. **"Publication-styled" is aspirational.** `ioptics/plotting.py` sets no
   rcParams, no `tight_layout`/`constrained_layout`, no titles or units; only
   `figures.py:80` does `dpi=150, bbox_inches='tight'`. Visible consequences on
   the live pages: the L23 scatter's x tick labels overprint into an unreadable
   smear, and the Taylor diagram labels its azimuth in **degrees** instead of
   correlation and draws no centred-RMSD arcs (so it is not really a Taylor
   diagram). The report figures also ignore the ocean palette the docs figures
   use.
5. **The leaderboard folds exactly one sweep.** 160 rows, all GLORIA, every
   accuracy cell `nan`; the L23 smoke's rows are gone from both the parquet and
   the rendered landing. `report.bokeh.interactive_leaderboard` exists and is
   unused.
6. **Parts of the generated prose are simply wrong.** `_intro` asserts "All
   accuracy metrics are log-space / multiplicative (**0 = perfect**)"
   (`standard.py:107-108`) — false for three columns of the very next table:
   `coverage68`/`coverage95` are perfect at 0.68/0.95, `median_ratio` at 1,
   `win_frac` at 0.5. The Accuracy blurb (`:191`) repeats it by grouping
   "**mae**/**bias** and **coverage** (0 = perfect)". The Taylor/Target text says
   "left/first" and "right/second" (`:156`) when the two PNGs are stacked
   **vertically** at 90% width with no captions, so nothing identifies which is
   which. The Interactive text promises "pick the dataset, algorithm, component
   and trophic stratum" (`:206`) where the dataset selector has exactly one
   option in both sweeps and GLORIA's component selector has exactly one.
7. **Whole tables of computed metrics never reach a page.**
   `metrics_spectral.parquet` (per-native-wavelength accuracy and coverage) is
   computed, persisted, loaded into `SweepArtifacts` (`figures.py:33-34`) and
   consumed by **nothing** — there is no wavelength-resolved accuracy figure in
   the system. Strata are computed for every metric, but both tables are pinned
   to `stratum='all'` and `fit_method='chisq'` (`standard.py:184-185`), so
   per-stratum results **and the entire MCMC population** are unreachable from a
   page; `plotting.dbic_cdf` even accepts a `by=` stratification that nothing
   passes. The derived scalars `Chl` / `a_cdom440` / `Sdg` are scored, then
   filtered out of the report table (`tables.py:41-42`).
8. **A latent multi-dataset defect that blocks per-dataset reporting.**
   `tables.accuracy` drops `dataset` from its `keep` list and merges wins on
   `['algorithm','component','ref_wave']`; `tables.qc` merges closure on
   `algorithm` alone. On a sweep with two datasets both tables silently duplicate
   or mis-join rows, and no column tells the reader which dataset a row is. Both
   committed sweeps are single-dataset, so it has never surfaced — but it has to
   be fixed before any per-dataset summary page is trustworthy.
9. **The leaderboard ranks contests that have no data.** `ranked()` assigns
   `rank` by `groupby(...).cumcount() + 1` (`leaderboard.py:178`) regardless of
   whether any metric is finite, so **144 of the 160 published rows are all-NaN
   yet each carries a rank of 1-4.** A reader sees a ranking where there is no
   measurement.
10. **The one real, interesting result on the L23 page goes unremarked.** `giop`
    beats `expb_pow` on a(440) accuracy (mae 0.062 vs 0.109, `win_frac` 0.85) —
    but its error bars are badly over-confident: `coverage68` = 0.45 and
    `coverage95` = 0.65 against nominal 0.68/0.95, where `expb_pow` sits at
    0.65/1.00. "More accurate but dishonest about its uncertainty" is exactly the
    trade-off this project exists to surface, and no prose mentions it.
    Symmetrically, GLORIA's four algorithms agree to ~16 digits and are presented
    as four separately ranked rows without a word saying they are
    indistinguishable.
11. **Table and asset hygiene.** `rst.figure_block` emits no `:alt:` text;
    `csv_table_block` sets no `:widths:` and the CSVs carry full float64
    precision (`0.09642020657366057`), ranks as `2.0` and wavelengths as `440.0`
    across 17 columns — a horizontally overflowing table with no units and no
    column glossary on the page. `figures.taylor_target` names its output
    `taylor_<component>.png` with no ref band, so a second reference wavelength
    would silently overwrite the first. `standard.build` never prunes the report
    dir, so changing the figure set leaves orphaned PNGs committed. The two pages
    already pin different BokehJS versions (3.9.0 vs 3.9.1), the interactive
    scatter draws only a dashed 1:1 line (inverting the static figures' solid
    1:1 + dashed 3× convention), and its hover carries wavelength but not
    `obs_id`, so an outlier cannot be traced back to a spectrum.
12. **Stale scoping claims:** `index.rst:14-26` says "Through **Stage 2**" and
   "seeded with `expb_pow` and `giop`"; `api/index.rst:5-8` says only Stage-0
   modules are documented; `models.rst:43-45` says two algorithms run side by
   side. `gsm` is registered by default (`registry.py:55`) and appears **nowhere**
   in the docs, and the turbid trio (`expb_pow2`, `expb_pow2flat`,
   `expb_powflex`) gets prose but no equations or parameter table.

## Q&A

**Prompt 1 (conversation about the reports).** Ten questions, roughly in the
order that answers unblock work. Q1-Q4 change what we build; Q5-Q10 are how.

- **Q1. Who is the report for, and is MOANA in scope?** CLAUDE.md says the point
  is "metrics and diagnostics to share with the ocean optics community", which
  reads as: a stranger's first 60 seconds on the page must convey what was
  compared and who won. But `papers/moana_atbd.pdf` (the MOANA v1.2 ATBD) and
  `papers/lange2020.pdf` appeared untracked on Jul 31, right as the first reports
  landed — are those (a) the **format model** you want these reports to grow
  toward (ATBD-style: theoretical basis, assumptions, validation, uncertainty
  budget), (b) a **new algorithm** (MOANA) to register and report on, or (c)
  unrelated reading? My work differs a lot between those.
>A. MOANA is a separate effort in IOPtics and is not in scope for the main reporting.  I may expose its current report on readthedocs eventually, but ignore it for now.  The reporting is for the ocean color community to use IOPtics to compare the performance of different IOP models.

- **Q2. How should a report adapt to a dataset with no spectral truth?** This is
  what makes page 3 blank. Options: (a) make the figure set **data-driven** —
  choose components and reference wavelengths from what the sweep actually has
  truth for, so GLORIA gets an `a_dg(440)` scatter instead of an empty `a(440)`;
  (b) add a **scalar-truth report kind** for datasets like GLORIA; (c) simply
  **suppress** sections with no data rather than publishing a blank panel with a
  confident caption; (d) all three. I lean (a)+(c) as the minimum — publishing
  blank axes under authoritative prose is the worst failure mode on the site.
>A. (a) an (c)

- **Q3. Do we run the full L23 sweep before polishing?** The only L23 page is the
  20-spectrum smoke, and `first_sweep.md` stops at step 3a with
  `runs/first_full_run.src` never run to completion. Options: (a) run
  `expb_giop_L23_v1` now (on your workstation — I can't; the L23 tree here has
  the data but the run is ~3 h with the 200 MCMC fits) and make **that** the
  flagship page, retiring the smoke; (b) polish presentation on the smoke first
  and re-render when the full run lands; (c) leave the smoke published
  permanently, labelled as a pipeline demo. I lean (a) — no amount of styling
  fixes a headline page built on 20 spectra.
>A. (b).  I will run the full sweep on my workstation after polishing the smoke.

- **Q4. Publish the GLORIA investigation, and how?** `reports/gloria_fits_report.md`
  is the best science in the repo (the b_b wall, the 70% missing-uncertainty data
  gap, the retracted Round-2 test) and it is invisible to readers. Options: (a)
  add `myst_parser` and publish the `.md` nearly as-is; (b) convert it to RST
  once; (c) fold its figures and findings into the `gloria_turbid_v3` page. And
  the general form of the question: should **every** sweep page carry a
  hand-written "What we found" section that the generator will not clobber
  (a `findings.rst` the builder includes if present)?
>A. Do migrate that report into readthedocs.  We should keep the original for posterity and for reference.  But otherwise, convert it to RST and put in docs to be exposed on readthedocs. 

- **Q5. Which figures should a sweep page carry?** Today: two scatters, Taylor,
  Target, ΔBIC. Available but unrendered: retrieved `a`/`bb` spectra ± credible
  bands vs truth, `Rrs` closure residuals with χ²ᵥ, corner plots, ratio
  histograms. The design doc says a **curated handful** of per-spectrum figures
  (MCMC subset + a few exemplars per trophic bin). How many exemplar spectra per
  page, and chosen how — best/median/worst fit, or per trophic stratum? (The
  hand-written GLORIA report's clear→turbid 2×2 example-fit panels are the model
  I would copy.)
>A. Let's show 10 exemplar spectra per page, but as a separate page.  Show best, worst, and 8 median fits.

- **Q6. One figure style for the whole project?** I would add a single style
  module (rcParams: fonts, `constrained_layout`, the `custom.css` ocean palette,
  consistent axis units like `a [m⁻¹]`) applied by `ioptics.plotting`, the
  `docs/figures/` generators **and** `reports/scripts/`. Do you want that, and do
  you want the Taylor diagram fixed properly (correlation-labelled azimuth,
  centred-RMSD arcs) or replaced with something you find more readable?
>A. Yes, let's add a single style module.  Use the ocean palette from the docs.  And let's fix the Taylor diagram to be more readable.

- **Q7. What should the landing page be?** Right now it is 2423 lines of
  `list-table` with all-NaN GLORIA cells and no per-sweep descriptions. Options:
  (a) a headline table per `(dataset, component)` with the full grid moved to a
  drill-down page; (b) drop all-NaN rows; (c) replace the bare glob toctree with
  **per-sweep summary cards** (date, dataset, algorithms, n spectra, one-line
  finding); (d) wire up `report.bokeh.interactive_leaderboard`, which is written
  and unused. Also: should the leaderboard re-fold **all** sweeps so the L23 rows
  come back, or is the ranking meant to be GLORIA-only for now?
>A. (a), (b), (c) and (d)!  The leaderboard should re-fold all sweeps so the L23 rows come back.  I will need to re-run the L23 SMOKE sweep on this laptop

- **Q8. `per_algorithm` and `per_dataset` pages — generate them or fold them in?**
  Both `kind`s are implemented and have never been built. A `per_algorithm` page
  is where spectra and corner plots naturally live. Do you want three pages per
  sweep, or one richer `cross_algorithm` page?
>A. We are going to want both.  Some folks will want to see how one algorithm performs on multiple datasets, and others will want to see how a dataset performs on multiple algorithms.

- **Q9. Fix the stale claims and document `gsm` + the turbid trio as part of
  this?** That means: correcting the Stage-2 scoping text and the api/index
  note, adding a `gsm` section to `models.rst`, and giving `expb_pow2`,
  `expb_pow2flat`, `expb_powflex` the same equation + parameter-table treatment
  the two defaults get. In scope for "improve reporting", or a separate pass?
>A. Yes, fix these.

- **Q10. Interactive figures: keep the CDN dependency?** Each page carries five
  `cdn.bokeh.org` script tags with the version pinned into committed RST, and the
  embedded JSON is what makes the L23 page 266 KB. Options: (a) keep as-is;
  (b) vendor BokehJS into `_static` so the site works offline and stops drifting
  with CDN versions; (c) drop interactivity and spend the budget on richer static
  panels. What do you want to be true when someone opens the page on a plane —
  or from a PDF of the paper?
>A. Let's try (b), but we might migrate to (c) someday.

- **Q11. Which slices of the metrics deserve a page?** Three whole dimensions are
  computed and then discarded: **per-stratum** results (both tables are pinned to
  `stratum='all'`), the **MCMC population** (pinned to `fit_method='chisq'`, so
  posterior-based results never appear), and **wavelength-resolved** accuracy
  (`metrics_spectral.parquet` is loaded and used by nothing — there is no
  accuracy-vs-λ figure anywhere). Which do you want surfaced: accuracy vs λ per
  component (my first pick — it is what an ocean-colour reader will look for), a
  per-stratum breakdown (oligo/meso/eutrophic), χ² vs MCMC side by side, or all
  three?
>A. Let's try for all 3.

- **Q12. Should uncertainty calibration be a headline result?** On the L23 page
  `giop` is the more accurate retrieval yet its error bars are over-confident
  (coverage68 0.45 / coverage95 0.65 against nominal 0.68/0.95) while `expb_pow`
  is honest (0.65/1.00) — a real finding the page never mentions. Do you want
  coverage promoted to a first-class column with its nominal target shown and
  flagged when it misses, and stated in prose next to the accuracy winner?
  Related: when algorithms are statistically indistinguishable (GLORIA's four
  agree to ~16 digits) should the report say so instead of ranking them 1-4?
>A. Indeed, over-confient error bars should be addressed.  And yes, when algorithms are statistically indistinguishable, the report should say so instead of ranking them 1-4.

**Prompt 2 — making IOPtics usable by the ocean-colour community for model
comparison.** Suggestions S1-S10, then decisions I need (P1-P7). No code yet.

*The framing that drives all of it:* today every URL on the site is a **sweep
id**, so the site can only answer "what did `gloria_turbid_v3` do". A visitor
from the community arrives with a different question — **"which IOP model should
I use for water like mine, and can I trust its uncertainties?"** — and no page
answers it. Your Q1-Q12 answers already commit us to most of the machinery
(data-driven figure sets, both profile kinds, all three metric slices,
calibration, indistinguishability, one style, vendored BokehJS). These
suggestions are about the **shape of the deliverable and the reader's path
through it**.

- **S1. Split the site into standing answers and an audit trail.** Two page
  families with different jobs. **Profiles** — one per algorithm, one per dataset
  — are folded across *all* sweeps and are the front door. **Sweep pages** (what
  exists now) stay as the provenance-stamped record of one run, reachable *from*
  the profiles. Nobody outside the project knows a sweep id, and sweep ids will
  multiply; profiles are stable URLs a paper can cite. This is the structural
  version of your Q8 answer ("some folks want one algorithm across datasets,
  others want one dataset across algorithms").
>A. I like this

- **S2. Make a coverage matrix the centrepiece of the landing page.** One grid:
  **algorithms (rows) × datasets (columns)**, each cell carrying the headline
  skill, `n`, and a link to that intersection — and each *empty* cell saying
  **"not evaluated"** outright. Built today it would read: `gsm` never run
  anywhere, PANGAEA never swept at all, L23 only via the 20-spectrum smoke,
  GLORIA the only populated column. That is an honest and genuinely useful map of
  the evidence, and it answers "has anyone tested X on Y?" in one glance — which
  is the question a community member asks before any ranking matters. It sits
  above your Q7(a) headline table, which then does the per-`(dataset, component)`
  detail.
>A. I like this too.

- **S3. Per-dataset summary report** (the "how do all models do on this data?"
  page). Proposed contents, in reading order:
  1. **A summary paragraph containing numbers** — winner, its error, its
     calibration, how many spectra it was scored on. This is the single cheapest
     improvement on the whole site: today's prose is templated but *numberless*,
     so no page states a result.
  2. **The dataset's truth matrix** — which components have truth, at which
     wavelengths, spectral vs scalar-only, and the caveats (GLORIA's `a_dg` is
     CDOM absorption, not CDOM+detritus). This is what makes the empty-panel
     problem impossible to repeat: the reader sees *up front* that GLORIA can
     only score `a_dg(440)`.
  3. **Ranked table per component × reference wavelength**, with
     statistically-indistinguishable algorithms **grouped rather than ranked**
     (Q12).
  4. **Accuracy vs wavelength**, all algorithms overlaid (Q11's first slice) —
     from the `metrics_spectral` table that is currently computed and discarded.
  5. **Per-stratum breakdown** (oligo/meso/eutrophic) — the "which model for my
     water type" cut.
  6. **Retrieval-success accounting**: `n_attempted → n_ok → n_scored` with the
     status split (`poor_fit` / `out_of_scope` / `fit_failed`). GLORIA's 63%
     `out_of_scope` is currently a bare cell in a CSV; a reader must be told what
     it means and why, or they will read it as a bug in IOPtics.
  7. **χ² vs MCMC side by side** where both exist (Q11).
  8. **Links out**: the exemplar-fit page, the sweeps that contributed, the
     dataset reference page.

- **S4. Per-algorithm summary report** (the "how does this model do everywhere?"
  page). Proposed contents:
  1. **What it parameterizes, auto-generated from its `AlgorithmSpec`** —
     `a_nw`/`bb_nw` models, parameter names, k, priors, RT toggles, fit method —
     with the equations from `models.rst`. Generating this from the spec means it
     cannot drift from what actually ran.
  2. **Where it wins and loses**, across datasets and water types (its row of the
     S2 matrix, expanded).
  3. **A calibration panel** — `coverage68`/`coverage95` against their nominal
     0.68/0.95 per dataset and component, flagged when they miss (Q12). "Accurate
     but over-confident", as `giop` is on L23, is a first-class result here.
  4. **Accuracy vs wavelength** across datasets.
  5. **Known failure modes** in prose — e.g. the power-law `b_bp` wall in turbid
     water, which is the central finding of the GLORIA investigation and belongs
     on `expb_pow`'s page, not buried in one sweep.
  6. **Exemplar fits** for this algorithm (your Q5 set: best, worst, 8 median).
  7. **Provenance**: which sweeps contributed, which code versions, and whether
     the spec changed between sweeps (see P1).

- **S5. A short "choose by water type" page.** Two or three sentences plus one
  table: for each stratum, which model(s) the evidence favours, with `n` and the
  explicit statement that this is measured evidence on specific datasets, not an
  endorsement. This is the page a working scientist will actually screenshot. It
  needs P3 answered first — how opinionated you want to be.

- **S6. Honesty features, because trust is the product.** Beyond Q12's
  indistinguishability grouping: never rank a contest whose metrics are all NaN
  (currently 144 of 160 leaderboard rows carry ranks 1-4 with no data);
  distinguish **"not evaluated"** from **"evaluated and failed"** everywhere;
  show `n` beside every number; explain `caveat = CDOM_vs_adg` inline where it is
  rendered rather than nowhere; and add a **Methods & metrics glossary** page that
  every table column header links to (log-space MAE, signed bias, wins, coverage,
  χ²ᵥ, `rel_misfit`, ΔBIC, the status vocabulary, the ±3 nm band matching, the
  stratum definitions). The glossary is also where the currently-false "all
  metrics are 0 = perfect" claim gets replaced by a per-metric "perfect value"
  column. Pair it with a **Scope & limits** section: L23 is Hydrolight-synthetic,
  in-situ "truth" carries its own uncertainty, PANGAEA falls back to a flat 5%
  `Rrs` error, GLORIA's `a_dg` truth is CDOM-only.

- **S7. Give every algorithm a fixed colour and marker, project-wide.** Today
  `plotting.scatter_log` groups with `sort=False` and takes matplotlib's default
  cycle, so an algorithm's colour depends on its row order *within that figure* —
  the same model is a different colour on different pages, and adding an
  algorithm reshuffles everything. A single registry-level mapping (colour +
  marker per registered algorithm, drawn from the ocean palette of Q6) lets a
  reader learn "teal = `giop`" once and carry it across every figure, page and
  sweep. It also enables **small multiples** (facet per algorithm) instead of the
  current overplotting, which is what makes a 4-algorithm scatter unreadable —
  and marker shape plus colour is what makes it work for colour-blind readers.

- **S8. The biggest adoption lever: an "add your own model" quickstart.** The
  registry already guarantees a new algorithm is *one* `register()` call, but
  nothing on the site tells an outsider that, or shows them the path. A short
  page: register your `a_nw`/`bb_nw` parameterization, run a bounded L23 sweep
  (with the expected wall time and what you need mounted), get the standard
  report locally, and — optionally — contribute the numbers so your model appears
  on the leaderboard beside the others. Include a copy-pasteable template build
  script. A community member who can get *their own* model onto the same axes as
  `expb_pow` and `giop` in an afternoon is the difference between a site people
  read once and a tool people use.

- **S9. Let sweep pages be the audit trail they are.** Keep the provenance
  header; add a hand-written `findings.rst` include the generator will not
  clobber (Q4's general form, so the sweep's actual conclusion is on its page);
  suppress sections with no data (Q2c); and replace the bare glob toctree with
  per-sweep cards carrying date, dataset, algorithms, `n`, and a one-line finding
  (Q7c). A reader who lands on a sweep page should be able to tell in five
  seconds whether it is the current answer or a historical run — including the
  smoke sweep, which should say on its face that it is 20 spectra (Q3b).

- **S10. Fill the evidence matrix first — the driver is already written.**
  Profile pages are only worth writing if there is evidence to profile, and right
  now there is one real sweep. But
  `ioptics/runs/prototypes/multi_v2/{build_v2.py,run_v2.yaml}` already defines
  `multi_L23_PANGAEA_v2` = **{L23, PANGAEA} × {expb_pow, giop, gsm}**, χ²-only,
  uniform `pct:0.05` noise, 400-750 nm — and it has **never been run on real
  data**. The Stage-6 log is explicit that the multi-dataset path was verified on
  a *synthetic* Tier-1 table, with the only real-data attempt being a GLORIA sweep
  where every `expb_pow` fit hit `maxfev`. Running that one existing driver would
  take the coverage matrix from one populated column to three datasets × up to six
  algorithms — including the first real numbers for `gsm` and for PANGAEA. That,
  plus your L23 smoke re-run and the existing GLORIA sweep, is enough evidence to
  make every page in S3/S4 meaningful.

  **But it needs bounding, and I had to check rather than assume.** PANGAEA *does*
  resolve on this laptop, and the adapter is deliberately permissive: it enumerates
  **64 071** observations with usable `Rrs`. At three algorithms that is ~192 000
  χ² fits — hours, not the "minutes" a χ²-only sweep suggests. Of those, only
  **3 247** appear in PANGAEA's IOP table, i.e. only ~5% can be scored against
  spectral truth at all; the other 95% would produce fits with nothing to compare
  them to. So the sensible run is **`obs_ids` bounded to the truth-carrying
  subset** (comparable in size to L23's 3 320, and every fit contributes a scored
  row). Two practical notes: the tree spells the directory `$OS_COLOR/PANAGEA`
  (transposed letters) yet resolution works, so that typo should be left alone
  until someone checks what ocpy actually keys on; and the report will need to
  state the 3 247-of-64 071 selection explicitly, or the page silently reports on a
  5% subset — the same mistake the GLORIA report caught itself making with the 29%
  uncertainty-carrying subset. See P8.

- **S11. Make the numbers reusable, not just readable.** Every profile page
  offers the exact table behind it as CSV, the leaderboard as a single
  downloadable file, and a one-line snippet that regenerates the page from the
  persisted sweep artifacts. Add a citation block naming the version, so a paper
  can cite a specific state of the comparison rather than "the website".

>A. Ok, all of this is great.  I have no push back.

### Decisions I need before building any of this (P1-P10)

- **P1. Cross-sweep identity of an algorithm.** If `expb_pow` ran with different
  priors, RT toggles or `maxfev` in two sweeps, is its profile page (a) one
  profile with a provenance note listing the variations, or (b) split per distinct
  spec? (a) is friendlier, (b) is stricter; my lean is (a) **provided** the page
  shows a "what varied between sweeps" block, because silently pooling two
  different configurations under one name is the sort of thing a reviewer will
  catch. **See S12 below — the feasibility audit turned this from a preference into a bug: the variation is currently not even detectable from the artifacts.**
>A.  Ok, (a) is ok.  But, yes, let's make sure we track the variations

- **P2. What counts as "statistically indistinguishable"?** Q12 says report it —
  I need the rule. Options: (a) a paired test on the per-spectrum differences
  (the pairwise wins machinery already works per spectrum, so a sign test or
  bootstrap CI on `win_frac` is natural); (b) a fixed effect-size floor, e.g.
  |Δmae| < 0.01 dex ≈ 2%, declared as "no practical difference"; (c) both — tie
  by statistics, and separately flag differences too small to matter. I lean (c),
  with the threshold in (b) set by you since it encodes what *you* consider
  scientifically meaningful.
>A. Both is good, but the fixed effect-size floor should be 20%.

- **P3. How opinionated should the site be?** Does it publish a
  **recommendation** ("for eutrophic water, prefer X"), or only ranked evidence
  and let the reader decide? A recommendation is far more useful and far more
  exposed — on GLORIA today it would have to say "none of these four work", which
  is honest and useful but is a strong public statement about published models.
>A. For now, no recommendations

- **P4. URL and page scheme** (permanent, so worth one minute now):
  `reports/algorithms/<name>` + `reports/datasets/<name>` under the existing
  reports tree, or top-level `algorithms/` + `datasets/` alongside the current
  `models.rst`/`datasets.rst` reference pages? Note the collision risk: we would
  then have a *reference* page called `datasets.rst` and a *results* page called
  `datasets/<name>` — I would rename the reference pages (e.g. `models.rst` →
  "Model reference") to keep them distinct.
>A. I am agnostic.  Go with the one you prefer

- **P5. Generated, curated, or hybrid profiles?** Fully generated profiles stay
  current automatically but can only say what the metrics say; hybrid (generated
  tables/figures + a hand-written findings block per profile) is what makes the
  pages worth reading. I lean hybrid, same pattern as S9's `findings.rst`.
>A. Ok, hybrid is good.

- **P6. Is S8 (the "add your own model" on-ramp) in scope for this pass**, or a
  follow-up once the profile pages exist? It is the highest-leverage item for
  your stated goal but it is also the one that most needs the rest to be solid
  first.
>A. No add your own model on-ramp yet.

- **P7. Build order.** My proposed sequence, given your Q3(b) answer (polish on
  the smoke, full L23 later) and your note that you will re-run the L23 smoke on
  this laptop: (1) the style module + data-driven figure sets + empty-section
  suppression (Q2, Q6) — these unblock everything and fix the currently-broken
  pages; (2) the metrics/table fixes: dataset-aware joins, no ranks without data,
  coverage targets, indistinguishability (Q12, P2); (3) profile pages + the S2
  matrix + glossary; (4) exemplar-fit pages (Q5); (5) leaderboard landing rework
  and vendored BokehJS (Q7, Q10); (6) the GLORIA report conversion to RST (Q4)
  and the doc corrections (Q9). Object anywhere this order does not match your
  priorities — in particular, if you want the GLORIA report published early
  because it is the strongest science, it can move to the front.
>A. This order looks good

- **P8. Do we run `multi_v2` as part of this pass (S10), and over which PANGAEA
  subset?** Both datasets resolve on this laptop, so I can run it here — but see
  S10: unbounded it is ~192 000 fits with only ~5% scoreable. My proposal is to run
  it over the **3 247 truth-carrying PANGAEA ids** plus L23, which is a
  couple-of-thousand-fit job per algorithm and yields fully scored rows. Do you
  want (a) that bounded run, here, as part of this pass; (b) the full 64 071 (hours,
  95% unscoreable, but it would characterize fit *success* across all of PANGAEA);
  or (c) defer it to your workstation with the full L23 sweep? If `expb_pow` hits
  `maxfev` on PANGAEA the way it did on GLORIA, that is a reportable result rather
  than a blocker — and it is exactly the kind of thing the profile pages should
  say out loud.
>A. Let's do (a).  I think my laptop can handle running these.

### Feasibility check — what the persisted artifacts can and cannot support

Everything below was verified against the code and the real parquet files, not
assumed. The short version: **S3/S4 are mostly a groupby away — no re-fitting** —
but five things distort or block them, and one of them turns P1 from a question
into a bug.

1. **The tables are there.** `leaderboard.parquet` already carries, per
   `(sweep_id, dataset, algorithm, stratum, component, ref_wave)`: `n`, `mae`,
   `bias`, `abs_bias`, `rms_log`, `coverage68/95`, `ref_match`, `win_frac`,
   `caveat`, `frac_ok`, `n_attempted`, `frac_overfit`, `rel_misfit_median_all`,
   `versions`. Per-wavelength curves live in each sweep's `metrics_spectral`
   (28 080 rows for GLORIA alone), which nothing reads yet. So the profile pages
   need a reader and a renderer, not new science.

2. **The leaderboard cannot express MCMC at all.** `_fold_sweep` filters
   `fit_method == 'chisq'` for both accuracy and wins (`leaderboard.py:99,116`)
   and `fit_method` is **not a leaderboard column** (verified). An algorithm run
   only under MCMC is invisible there. Q11's "χ² vs MCMC side by side" therefore
   requires the fold itself to gain `fit_method` — otherwise the comparison can
   only ever be built per-sweep.

3. **The dataset-blind join is in the leaderboard too, not just `tables.py`.**
   The wins merge is `on=['stratum','component','ref_wave','algorithm']` — no
   `dataset` (`leaderboard.py:118-122`, verified). Folding a synthetic
   two-dataset `metrics_scalar` through the real code returns **352 rows instead
   of 320**, with GLORIA rows carrying the *other* dataset's `win_frac`. This is
   the one must-fix before any multi-dataset page exists, and it is why S10's
   `multi_v2` run and the per-dataset pages cannot land in either order without
   it.

4. **Three different denominators, none named consistently.** On the GLORIA sweep:
   the accuracy row's `n = 12` is surviving *(retrieved, truth)* pairs; the closure
   row's `n = 21` is spectra actually scored; `n_attempted = 100`. All three are on
   disk under overlapping names. Every page that prints an `n` has to say which one
   it means — this belongs in S6's glossary as a table of "which n is this".

5. **"Never evaluated" is ambiguous, so the S2 matrix needs care.** Absence of a
   leaderboard row conflates *never run*, *run but not yet scored* (the fold
   returns `None` when `metrics_scalar.parquet` is missing or the accuracy slice is
   empty) and *run under MCMC* (item 2). Distinguishing them means walking the runs
   tree rather than trusting the leaderboard — worth doing, because a matrix that
   mislabels "we never tried" as "it failed" is worse than no matrix.

6. **P2 needs a new metrics pass, and the raw material is already persisted.**
   `metrics_pairwise` tallies wins *per algorithm with the opponent discarded*, so
   GLORIA's "36 contests" are 12 spectra × 3 opponents, non-independent — no paired
   test can be recovered from it. But `results_spectral` holds per-`(obs_id,
   algorithm)` retrieved-vs-truth, and `results_scalar` holds per-spectrum
   `BIC`/`k`, so paired per-spectrum differences and a per-spectrum ΔBIC vector are
   a groupby away. **Caution on power:** only 12 GLORIA spectra have `a_dg(440)`
   truth *and* `status == 'ok'`, so a paired test there is n = 12. The honest
   output may often be "underpowered to distinguish", which is itself worth
   printing rather than hiding behind a rank.

7. **Computational cost is recorded nowhere.** No wall time, no function-evaluation
   count, no MCMC step count on any row — and `nfev` is not even retrievable
   downstream, because BING's `chisq_fit` calls `curve_fit(..., full_output=False)`.
   If runtime belongs on a profile page (S4 item 6) it needs new instrumentation
   *and* a re-run. See P9.

- **S12. Harden provenance before publishing cross-sweep profiles — P1 is a bug,
  not a preference.** For `gloria_turbid_v3`, `expb_pow` ran with
  `maxfev=40000` injected by registry mutation (`build_v3.py`), which the script
  itself credits with the difference between 72 failed fits and none. The
  persisted algorithm block has **no `maxfev` key at all** (verified: its keys are
  `anw_model, apriors, bbnw_model, beta, bpriors, fit_method, label, name,
  noise_model, othera_priors, rt, sSdg, set_Sdg`) and is otherwise identical to a
  default `expb_pow` — so the sweep is indistinguishable from one run with the
  default budget. The same block says `noise_model: pace` while the config says
  `insitu` and the real per-record tags were `insitu+floor:0.05` /
  `insitu+imputed:0.05`. `AlgorithmConfig.overrides` are accepted by `config` and
  never applied by `run_sweep`. And the leaderboard's version stamp is
  **ioptics-only** — the `bing` and `ocpy` commits are dropped by the fold, though
  BING is where the model forms and the fitter live. Consequence: two leaderboard
  rows sharing an algorithm name are not guaranteed to be the same algorithm.
  Minimum fix before profiles go public: carry `maxfev` + the `mcmc` block + a
  digest of the algorithm block into provenance, fix or drop the stale
  `noise_model`, apply-or-reject config overrides rather than silently ignoring
  them, keep the bing/ocpy stamps through the fold, and let `provenance_id` reach
  `metrics_*`/the leaderboard so a row can be traced back to its configuration.

- **P9. Do you want cost measured?** Runtime per fit (and MCMC steps) is a number
  the community will ask for when comparing a k=3 model against a k=7 one, but it
  needs instrumentation plus a re-run to exist at all. In scope, or explicitly out?

- **S13. Present quantities the community already recognizes.** The good news from
  the conventions research: we compute nearly the right things and *display* them in
  the wrong form. Specifics, with the two load-bearing ones verified at source:

  1. **Back-transform the log-space errors.** Seegers et al. 2018
     ([doi:10.1364/OE.26.007404](https://doi.org/10.1364/OE.26.007404)) — now the
     NASA-aligned default — defines `bias = 10^mean(log₁₀M − log₁₀O)` (1.0 =
     unbiased) and `MAE = 10^mean|log₁₀M − log₁₀O|` (1.5 = 50% error), and says
     explicitly (verified quote) that "a reported log10 value of 0.3 does not
     indicate 30% uncertainty, but rather approximately a 100% uncertainty
     (10^0.3 = 1.995), suggesting a preferred practice of reporting 1.995 in lieu
     of 0.3." **Correction to what I first wrote here:** I claimed our tables
     publish the raw dex value. They do not — `metrics.mae` is
     `10**mean|log10(M/O)| - 1` and `metrics.bias` likewise, so the L23
     `expb_pow` mae of 0.109 already means **10.9%** (the underlying log error is
     0.045 dex). That matches Erickson 2023 and this design's own definition, and
     the numbers are right. The residual risk is narrower and purely
     presentational: ours is the **fractional** form (0 = perfect) while Seegers
     reports the **un-subtracted factor** (1.109; "1.5 = 50% error"), so a reader
     from that lineage can misread `0.109` as a factor of 0.109. Fix = state the
     convention in the column header and the glossary, and consider showing the
     factor form alongside. No metric change needed.
  2. **Cut the metric count.** Same paper: "Select no more than one metric for each
     estimate of bias, accuracy, and precision to reduce the likelihood of decision
     bias caused by redundant metrics." We ship 17 columns including `mae`,
     `abs_bias`, `rms_log` and `median_ratio` plus three rank columns. Also worth
     knowing: it explicitly **discourages RMSE, r² and regression slope** as
     headline scores (non-Gaussian, outlier-amplifying) — and it recommends
     **percent wins** as the ranking metric, which is what our `win_frac` already
     is. We are aligned on ranking and merely bury it.
  3. **Keep continuity with the IOP literature specifically.** Werdell et al. 2013
     (GIOP, [doi:10.1364/AO.52.002019](https://doi.org/10.1364/AO.52.002019)) is
     *the* reference evaluation table for this exact problem: `N`, `Ratio =
     median(M/O)`, `MPD = median(100|M/O − 1|)`, plus the IOP-specific closure
     metrics **ΔRrs** and **ΔIOP** as median + SIQR. We already compute
     `median_ratio` (= their Ratio) and `rel_misfit` (≈ ΔRrs), so naming them the
     way that audience names them is nearly free recognition.
  4. **The leaderboard already has a published blueprint** — Brewin et al. 2015
     ([doi:10.1016/j.rse.2013.09.016](https://doi.org/10.1016/j.rse.2013.09.016)),
     the ocean-colour round-robin. Two features to copy, both verified in the
     paper: **η, "percentage of possible retrievals" (`η = N_E/N_M × 100`, Eq. 13),
     is one of the *scored* tests** — not a footnote — on the stated grounds that an
     algorithm "should not be a source of more gaps in the data than would be the
     case if other algorithms were used" (that is our `frac_ok` promoted to a first-
     class score); and **rank uncertainty comes from bootstrapping — 1000
     resamples with replacement** — with each model's total score normalised by the
     all-model average. **This answers P2 with precedent instead of an invented
     threshold: overlapping bootstrap intervals mean the ranks are
     indistinguishable.** (I verified η, the 1000-resample bootstrap and the
     normalisation; I did not read their per-test 0/1/2 point rules line by line.)
     One more Brewin practice worth mirroring: plausibility screening is applied
     **per variable, not per spectrum**, so a spectrum rejected for `a_ph` still
     contributes to `a` — which is a different policy from our per-fit `status`.
  5. **Stratification conventions align with what we already have, with one
     addition.** Wavelength always; trophic bins All/Oligo/Meso/Eutrophic (GIOP
     Table 4 — matches our strata, though their exact Chl edges were **not**
     verified, so check before hard-coding); and the addition — **separate the
     total products (`a`, `bb`) from the decomposed ones (`a_dg`, `a_ph`)**,
     because the decomposed ones are consistently worse and an aggregate that
     hides that is distrusted. Optical water types are where the field is heading
     but there is **no agreed scheme** (an IOCCG working group exists precisely
     because of that), so if we go there, name the scheme and make it swappable.
  6. **Synthetic and in-situ are two parallel tracks, never pooled.** That is
     IOCCG Report 5's design (a HydroLight synthetic set *and* an in-situ set,
     with every algorithm chapter reporting both) and GIOP's. It maps exactly onto
     our L23 vs GLORIA/PANGAEA split: synthetic has radiometric closure by
     construction and isolates inversion skill, in-situ does not. So the S2 matrix
     and any ranking should keep the two tracks visually and statistically
     separate rather than producing one blended winner.
  7. **Figure conventions we currently miss:** put the statistics **inside the
     panel** (N, n, ratio, MPD) — ours annotate nothing; pair each scatter with a
     **ratio distribution** (a violin/box of log ratios is a legitimate modern
     rendering of GIOP's ratio-histogram panels); use **Type-II / major-axis**
     regression if a fit line is drawn at all, never OLS, since both axes carry
     error; and metric-vs-wavelength small multiples are treated as **mandatory**
     in IOP work, which independently confirms Q11's first slice. **On Q6's Taylor
     question the community verdict cuts against investing in it:** Target (bias
     vs unbiased RMSD) is well established, but Brewin computed the full Taylor
     triple and chose *not* to draw Taylor diagrams, and Seegers undercuts the
     r²/RMSE basis Taylor rests on. Suggest demoting Taylor to optional and
     spending that effort on the annotated scatter + ratio distributions instead —
     which changes your Q6 answer, so flagging it rather than acting on it.
  8. **Failure reporting has explicit precedent** — IOCCG R5 tabulates both `N`
     (tested) and `n` (valid) and states outright that excluding failures yields a
     smaller dataset and "likely better statistical results"; GIOP reports
     `N% = 100 × N_valid/N_total` per bin plus an overall 10% failure rate with its
     causes named. That is precisely the three-denominator fix, and it means our
     status taxonomy is an asset to publish, not an embarrassment to hide.
  9. **One place where we would be ahead of convention, and should say so.** There
     appears to be **no established community convention for validating whether
     stated uncertainties are calibrated** — the propagation practice exists
     (McKinna et al. 2019, IOCCG Report 18) but the coverage diagnostic does not.
     So Q12's calibration panel is a genuine contribution; it should be labelled as
     new rather than presented as standard practice.
  10. **Archival norms for S11:** IOCCG reports carry ISBN + DOI minted through
     Ocean Best Practices (`10.25607/OBP-…`); the NASA ATBD structure is worth
     copying selectively — a **Plain Language Summary**, an explicit **Algorithm
     Usage Constraints** section, and validation split into methods / uncertainties
     / errors. The dashboard models are WeatherBench 2 and ILAMB: open evaluation
     code plus published baseline data, with the leaderboard and the per-variable
     diagnostics generated as the *same* artifact. Practical shape: **pin and DOI a
     frozen benchmark release** (data snapshot + algorithm versions + evaluation
     code) that a paper can cite, while the live site tracks HEAD and shows the
     release tag on every page. Anti-pattern to avoid: OC-CCI's versioned reports
     whose download links no longer resolve.

- **P10. Which metric family leads?** Given S13, my recommendation is: headline
  **Seegers-style multiplicative `bias`/`MAE` + percent wins**, with GIOP's
  `Ratio`/`MPD` shown alongside for continuity with the IOP literature, and MdSA/
  SSPB added only if you want the inland/coastal audience served explicitly (that
  lineage matters for GLORIA; my source for it was summaries rather than the
  paywalled full text, so treat it as unconfirmed). Do you agree — and do you want
  the leaderboard rebuilt on **Brewin's bootstrap-scored** model (which also
  resolves P2), or kept as the simpler wins → |bias| → MAE ordering with bootstrap
  intervals added on top?

Also found while checking: **`kind='per_algorithm'` cannot run on the only sweep we
have.** `standard.py:172` does `int(sweep.spectral['obs_id'].min())` and GLORIA's
`obs_id`s are strings (`GID_1`). A one-line fix, but it means the page family your
Q8 answer asks for has never once been exercised on real data.

## Logs

### 2026-08-03 (Improve reporting: Stage-7 prompt doc created)

You asked whether I had made the prompt docs for the next steps. **I had not** —
prompt 3 was scoped to `docs/design/`, and the Stage 7 I added to the implementation
doc left its own convention line ("each stage has a dedicated code-generation prompt
doc, `claude_prompts/coding_prompts_stage<NN>.md`, with one prompt per module") owing a
file that did not exist. Now written: **`claude_prompts/coding_prompts_stage07.md`**,
following the Stage 0-6 house structure (Goal + exit criterion, Conventions, Context
with carryover, Prompts, Modules/Tasks, Q&A, Logs).

- **11 tasks**, in dependency order: style module + per-algorithm visual identity →
  data-driven artifact selection → metrics/table correctness → pairwise stats that can
  detect a tie → leaderboard fold + landing page + vendored BokehJS → profile pages +
  coverage matrix + glossary → exemplar-fits page → the three discarded slices →
  provenance hardening → publish the GLORIA report and fix the stale prose → generate
  the missing evidence (bounded `multi_v2`, L23 smoke re-run, re-fold).
- **Context carries the 13 condensed defects** with the file each lives in, so a fresh
  session does not have to re-derive them, plus a "decided by JXP — do not re-litigate"
  block holding your Q1-Q12 answers.
- **Q&A restates P1-P10** grouped by which task they block, so the doc stands alone;
  answer in either file. Two are hard blockers (the tie statistic for Task 4; the URL
  scheme and generated-vs-curated split for Task 6), and one flags that the community
  evidence argues against your Q6 Taylor answer.
- **Conventions corrected for this machine:** the env interpreter here is under
  `miniforge3`, not the `miniconda3` path the older prompt docs carry, and the current
  test baselines (230/38 without `$OS_COLOR`, 264/4 with it) are recorded so a
  regression is attributable.

No code or design-doc changes in this step.

### 2026-08-03 (Improve reporting, prompt 3: design docs updated)

Updated **both** docs in `docs/design/` to reflect the decisions and the findings, and
bumped their versions — `IOPtics_design.md` **0.15 → 0.16**, `IOPtics_implementation.md`
**0.22 → 0.23** — since `provenance._doc_version` parses those lines and stamps them
into every sweep (verified it now reads 0.16 / 0.23). No package code touched.

**Ground rule I held to:** your Q1-Q12 answers are recorded as design; my S1-S13
suggestions that you have **not** yet ruled on are written as proposals and their
decisions are parked in the design doc's Open Questions table (new items 6-12), so the
docs never silently self-answer a live question.

**`IOPtics_design.md`:**
- **§Scope and goals** — added the sharpened primary goal: a community member comparing
  IOP models, both by reading the comparison and by running IOPtics on their own model.
  Every reporting decision is declared downstream of that sentence.
- **§Data** — GLORIA is no longer "not yet downloaded"; recorded that it was acquired,
  that its use extended to Rrs-space closure (where it proved most informative), and the
  two data properties that shape any GLORIA result (29% quote uncertainties, tight enough
  to need a floor). PANGAEA gained the measured 64 071-vs-3 247 scale note and the
  `PANAGEA` spelling caveat.
- **§Metrics** — pinned which *form* of the accuracy number is published (fractional
  multiplicative, 0 = perfect) and required tables to say so, since Seegers publishes the
  un-subtracted factor; adopted "one metric each for bias/accuracy/precision" and
  demoted RMSE/r²/slope; added total-before-decomposed reporting and synthetic-vs-in-situ
  as parallel tracks (IOCCG R5 / GIOP); struck the superseded Rrs-MAE QC window in favour
  of χ²ᵥ-based QC + relative misfit (= GIOP's ΔRrs); promoted coverage to a headline
  result **and** flagged it as genuinely novel, since no community convention for
  validating calibration appears to exist; added ties-reported-as-ties with the Brewin
  bootstrap precedent, η as a scored metric, and the three named denominators.
- **§Metrics §6** — new figure conventions: statistics annotated in-panel, ratio
  distributions beside every scatter, metric-vs-wavelength as mandatory, Type-II
  regression, pairwise win-rate matrices, and **Taylor demoted to optional** (flagged
  as cutting against your Q6 answer rather than quietly overriding it).
- **§Reporting** — artifact-selection rules (data-driven figure sets, suppress empty
  sections, numbers in prose, the 10-exemplar page, one style module, registry-assigned
  colour/marker); all three report kinds first-class with the profiles-vs-audit-trail
  split and the coverage matrix; the three discarded slices to surface; leaderboard rules
  (no ranks without data, fold every sweep, dataset-aware, carry `fit_method` and the
  bing/ocpy stamps, landing-page shape); vendored BokehJS; publishing hand-written
  analyses as RST; reusable numbers and a DOI'd frozen release; ATBD structural
  borrowings; and a pointer that provenance must be hardened first.
- **§Open Questions** — marked GLORIA acquisition resolved, revised the metrics row, and
  added items 6-13 (metric family, tie statistic, cross-sweep identity, how opinionated
  the site is, profile URLs/generation, cost, the on-ramp, MOANA as out of scope).
- **§References** — added Brewin et al. 2015, IOCCG Report 5, IOCCG Report 18 and
  McKinna et al. 2019, since the new text leans on them.

**`IOPtics_implementation.md`:**
- **§Provenance record** — a ⚠ block listing the gaps that make cross-sweep identity
  unreliable: `maxfev` and the `mcmc` block missing from the emitted algorithm block (the
  turbid sweep's 40 000-iteration budget is invisible), the stale `noise_model: pace`, the
  per-record noise tag never persisted, `AlgorithmConfig.overrides` accepted-but-ignored,
  `provenance_id` stopping at `results_scalar`, and no cost recorded anywhere.
- **§Metrics** — §2 rewritten around χ²ᵥ QC + relative misfit with the old Rrs-MAE window
  struck and the reason (Rrs crosses zero in the red); §5 gained the "`wins` cannot
  support a paired test" revisit with what a new pass must keep; §Stratification gained
  the "computed but never surfaced" warning (stratum/MCMC/per-λ) plus the optical-water-
  type note.
- **§Reporting** — a new ⚠ subsection at the top tabulating **15 verified defects** with
  the file each lives in, followed by the contract changes that follow. Also corrected the
  `report.figures` status (only three builders have ever rendered; the "curated handful"
  is now pinned at best/worst/8-median), the leaderboard's required fold changes, and the
  `report.bokeh` reality (inline `components` embed, CDN dependency to vendor,
  `interactive_leaderboard` unused).
- **§Staged plan** — added **Stage 7 — Reporting rework** with build order, exit
  criterion ("a reader arriving cold can answer *which model should I use for water like
  mine, and can I trust its uncertainties?*"), the evidence still to generate
  (`multi_v2`, the full L23 sweep), and the gating open decisions; extended the
  dependency diagram.

**One correction I made to my own prompt-2 write-up before it could propagate.** I had
claimed our tables publish raw log₁₀ errors needing back-transformation. `metrics.mae` is
`10**mean|log10(M/O)| - 1`, so the L23 `expb_pow` value of 0.109 already means 10.9%
(0.045 dex underlying) and is consistent with both Erickson 2023 and this design's own
definition. S13.1 and the prompt-2 log now carry the correction, and the design doc
records the real (narrower) issue: ours is the fractional form, Seegers' is the factor
form, so the convention must be labelled.

### 2026-08-03 (Improve reporting, prompt 2: how to make model comparison easy)

No code changed, per your instruction.

**Read your Q1-Q12 answers** and took them as settled: MOANA out of scope;
data-driven figure sets + suppress empty sections; polish on the smoke first and
you run the full L23 later; convert the GLORIA investigation to RST for the site
while keeping the `.md` for posterity; 10 exemplar spectra (best, worst, 8 median)
on their own page; one style module on the ocean palette with a readable Taylor
diagram; landing page gets all four of (a)-(d) and the leaderboard re-folds every
sweep; **both** profile kinds; fix the stale docs and document `gsm` + the turbid
trio; vendor BokehJS; all three metric slices; and treat over-confident error bars
and statistical ties as reportable results.

**Wrote S1-S10 + P1-P7** into the Q&A above. The organizing insight is that every
URL on the site is currently a **sweep id**, so the site can only answer "what did
this run do", while a community visitor asks "which model should I use for water
like mine, and can I trust its uncertainties?". Hence S1's split between *standing
answers* (per-algorithm and per-dataset profiles, folded across all sweeps — the
front door) and the *audit trail* (per-sweep pages), and S2's coverage matrix,
which as of today would honestly report that `gsm` has never been run, PANGAEA has
never been swept, and L23 exists only as a 20-spectrum smoke.

**New facts I established for this task** (beyond prompt 1's audit):

- **Algorithm colour is not stable anywhere.** `plotting.scatter_log` groups with
  `sort=False` and takes matplotlib's default cycle, so a model's colour depends
  on its row order within that one figure — it changes between pages and shifts
  when an algorithm is added. Hence S7 (registry-level colour + marker, which also
  buys small multiples and colour-blind safety).
- **The GLORIA report converts cleanly.** All 11 figures in `reports/figures/` are
  referenced exactly once each in the `.md`, so Q4's RST conversion is mechanical
  rather than a rewrite.
- **Baseline is green** before any of this work: `sphinx-build -W` on the full
  site succeeds today, so any regression during the build-out is ours.
- **The multi-dataset driver already exists and has never been run on real data.**
  `runs/prototypes/multi_v2/` defines `multi_L23_PANGAEA_v2` = {L23, PANGAEA} ×
  {`expb_pow`, `giop`, `gsm`}, χ²-only; the Stage-6 log shows the multi-dataset
  path was verified on a *synthetic* Tier-1 table, with the only real-data attempt
  being a GLORIA sweep whose `expb_pow` fits all hit `maxfev`. Running it is the
  cheapest way to populate the evidence matrix → S10, P8.
- **I wrote "minutes" for that run and then checked it, which turned out to be
  wrong.** PANGAEA resolves locally and its adapter enumerates **64 071**
  observations, so three algorithms is ~192 000 χ² fits — hours. Worse, only
  **3 247** of those ids appear in PANGAEA's IOP table, so ~95% cannot be scored
  against spectral truth at all. S10/P8 now propose bounding the run to the
  truth-carrying subset and stating that selection on the page. (Also noted: the
  data tree spells the directory `PANAGEA` yet resolution works — leave it alone
  until someone checks what ocpy keys on.)

**Two Fable subagents** ran in parallel for this task: one auditing what a
cross-sweep profile page can actually be built from without re-fitting, one
researching how the ocean-colour community conventionally presents IOP-algorithm
inter-comparisons (so the pages look familiar to a reader from OBPG/IOCCG rather
than invented here). Both were still running when S1-S11/P1-P8 were written, so
nothing there depends on them.

**The feasibility audit landed** and produced the "Feasibility check" block above
plus **S12** and **P9**. I verified its load-bearing claims against the code and
the real parquet files before recording any of them — the leaderboard's
`fit_method == 'chisq'` filter and missing `fit_method` column, the dataset-less
`win_frac` merge keys, the absence of `maxfev`/`mcmc` from the persisted algorithm
block alongside its stale `noise_model: pace` against a config saying `insitu`, and
the complete absence of runtime instrumentation. Two of its findings changed the
plan rather than decorating it: **P1 is a bug, not a preference** (the GLORIA sweep
ran `expb_pow` with `maxfev=40000` and nothing on disk records it, so two
leaderboard rows with the same algorithm name are not necessarily the same
algorithm → S12), and **P2 needs a new metrics pass** because `metrics_pairwise`
throws away the opponent identity — though `results_spectral` retains everything
needed, and the honest answer on GLORIA will often be "n = 12, underpowered".

**The community-conventions research also landed**, and produced **S13** + **P10**.
Its verdict is encouraging: we compute nearly the right quantities and *display*
them in the wrong form. I verified the two claims that would change our metric
presentation at source rather than trusting the summary — Seegers et al. 2018 for
the multiplicative `bias`/`MAE` definitions and the explicit instruction to
back-transform out of log₁₀ before reporting (its own example: 0.3 dex is ~100%
error, not 30%, so report 1.995), and the Brewin et al. 2015 round-robin for η as a
*scored* test (Eq. 13) and for rank uncertainty from **1000 bootstrap resamples**
with scores normalised by the all-model average (read out of the paper PDF directly,
since it would not convert). Three consequences worth naming:

- **I got one thing wrong here and caught it before it reached the design docs.** I
  wrote that our `mae`/`bias` publish raw log₁₀ values needing back-transformation.
  Checking `metrics.py` shows they are already `10**mean|log10(M/O)| - 1`, so 0.109
  means 10.9% (0.045 dex underlying) — correct, and matching both Erickson 2023 and
  this project's own design doc. What survives is only a labelling issue: Seegers
  reports the un-subtracted factor, so our fractional 0.109 should say which
  convention it is. Corrected in S13.1 rather than left standing.
- **P2 now has precedent instead of an invented threshold**: overlapping bootstrap
  intervals mean the ranks are indistinguishable. That is a better answer than the
  |Δmae| floor I proposed, and it composes with the new metrics pass P2 already
  needs.
- **It argues against part of your Q6 answer.** Brewin computed the full Taylor
  triple and deliberately did not draw Taylor diagrams, and Seegers undercuts the
  r²/RMSE basis Taylor rests on. Rather than invest in fixing our Taylor diagram, I
  would demote it to optional and spend the effort on annotated scatters and ratio
  distributions — flagged in S13.7 for you to overrule rather than acted on.

Carried-forward uncertainties from that research, so nobody treats them as settled:
GIOP's exact trophic bin edges were not verified (check before hard-coding), the
MdSA/SSPB inland-coastal lineage came from summaries rather than the paywalled full
text, and there is apparently **no** community convention for validating uncertainty
*coverage* — which makes Q12's calibration panel a contribution to label as new
rather than standard.

**Open on my side:** P1-P7 are genuine forks — especially P2 (what counts as
indistinguishable, which needs your threshold, since it encodes what *you* call a
scientifically meaningful difference) and P3 (whether the site publishes
recommendations or only evidence, which on GLORIA today would mean publishing
"none of these four work").

### 2026-08-03 (Improve reporting, prompt 1: conversation — inventory + Q&A)

No code changed; this task was reconnaissance and questions.

**What I did.** Read the live site
(`https://ioptics.readthedocs.io/en/develop/reports/` plus the rendered
`gloria_turbid_v3` page), then the generating code
(`report/{standard,figures,tables,bokeh,rst,leaderboard}.py`, `plotting.py`,
`diagnostics.py`), the committed pages and their assets, the design doc's
§Reporting (which is the yardstick — it promises more than we render), and the
local sweep artifacts + leaderboard parquet. Ran two **Fable** subagents in
parallel: one auditing the generated-report layer, one auditing the standalone
`.md` report and the docs pages. I also opened the published PNGs as images
rather than trusting filenames — which is how the blank panels surfaced.

**Headline findings** (detail in Reports above): the `gloria_turbid_v3` page is
**entirely blank figures** because the figure set is hardcoded to `a(440)` /
`bb(555)` / `expb_pow`-vs-`giop` and GLORIA has spectral truth for none of them;
the only L23 page is the **20-spectrum smoke** (the full run never finished); the
generated prose explains figure types but never states a result; the richest
figures (spectra ± bands, closure residuals, corner) are implemented but never
rendered on any page; `plotting.py` has no styling despite the docstring, with
visible label collisions and a mislabelled Taylor diagram; the leaderboard folds
one sweep with all-NaN accuracy; and the best science in the repo
(`reports/gloria_fits_report.md`) is not on the site at all.

**One thing I checked before believing it:** the "Interactive" section looked
empty when fetched as text, but the live HTML does carry the BokehJS CDN tags and
a `data-root-id` root — that section is fine; a text fetch just cannot run JS.

**Posed Q1-Q12** above and did not self-answer them, per the conventions; Q1-Q4
(audience/MOANA, empty-page policy, whether to run the full L23 sweep first,
whether to publish the investigation report) gate what I build next.

**Addendum — second audit landed** (the report-layer Fable agent, after the first
write-up). It added findings 6-11 above; I verified its four load-bearing claims
against the code and data before recording them, rather than taking them on
trust: `metrics_spectral` really is loaded and never consumed
(`figures.py:33-34`, no other reference); `tables.accuracy` really drops
`dataset` and merges wins on `['algorithm','component','ref_wave']`
(`tables.py:43,52-54`) with `tables.qc` merging on `algorithm` alone (`:96`);
`ranked()` really assigns ranks by `cumcount()+1` with no finiteness check
(`leaderboard.py:178`), giving 144 all-NaN rows a rank; and the L23 coverage
numbers are as quoted (`giop` a@440: coverage68 0.45, coverage95 0.65,
`win_frac` 0.85, mae 0.062 — vs `expb_pow` 0.65/1.00, mae 0.109). Those four
prompted the two extra questions, **Q11** (stratum / MCMC / wavelength-resolved
slices, all computed and discarded) and **Q12** (whether calibration is a
headline result, and whether indistinguishable algorithms should be ranked at
all). The multi-dataset join defect is not a question but a bug — it has to be
fixed before any per-dataset summary page can be trusted, which is directly on
the path of prompt 2.

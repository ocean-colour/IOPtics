# Code IOPtics

## Goals

Produce a **coding / implementation design document** that guides the actual
writing of the IOPtics package. Where `IOPtics_design.md` says *what* IOPtics must
do and *why* (and deliberately avoids code), this effort produces the companion
doc that says *how* — concrete package layout, module APIs and signatures, data
structures, config formats, and how IOPtics wraps the BING and ocpy packages.

The output document will be named `IOPtics_implementation.md` and stored in
`docs/design/`. It is the "companion implementation document (forthcoming)"
referenced by the design document.

We expect the implementation to:

- Wrap **BING** (retrieval engine) and **ocpy** (data loaders, noise models,
  Spectrum classes) as a thin, uniform layer — not re-implement them.
- Run a growing registry of IOP algorithms through one pipeline, developing the
  first two — **`expb_pow` (ExpB_Pow)** and **`giop` (GIOP)** — **in tandem** so
  the comparison tooling is exercised on a real two-way comparison from the start.
- Emit a standardized results table + machine-readable provenance for every sweep.
- Compute uniform metrics/diagnostics and generate reproducible reports
  (.rst → readthedocs, a persistent leaderboard, standalone Bokeh figures).

## Claude

### Skills

Consider using the skills in `.claude/skills/` (e.g. `critical-partner`,
`grill-me`, `code-review`).

## Context

Examine the following before drafting the implementation doc:

- **The design document:** `docs/design/IOPtics_design.md` — the authoritative
  *what/why*. This effort plans the *how* for each of its sections (Data,
  Analysis, Metrics, Reporting) and honors its decisions and Open Questions.
- **`docs/context.md`** — reduced scientific/architectural reference.
- **The BING repository** (local copy; `github.com/ocean-colour/bing`) — the
  engine. Key modules: `models.anw` / `models.bbnw` (model registries +
  `init_model`), `rt.rrs` (Gordon forward model) / `rt.raman` / `rt.chl_fl`,
  `fitting.chisq_fit` + `fitting.inference` (least-squares & MCMC),
  `parameters.standard` (pre-wired combos: `expb_pow`, `giop`, `gsm`, ...),
  `priors`, `evaluate` (reconstruct a/bb ± unc), `stats` (χ²/AIC/BIC), `noise`.
  The canonical end-to-end example is `bing.fitting.l23.prep_one_l23` — IOPtics
  generalizes this into a dataset-agnostic prep.
- **The ocpy package** (`github.com/ocean-colour/ocpy`) — loaders
  `hydrolight.loisel23`, `insitu.pangaea`, `insitu.gloria`; noise
  `satellites.pace`; `spectra` (`Spectrum` / `SpectrumStack` + `spectra.io`
  adapters).
- **The BING and Erickson 2023 papers** (`docs/PDFs/bing.pdf`,
  `docs/PDFs/erickson2023.pdf`) for exact metric definitions.

## Overview

Guidelines for the implementation document (`docs/design/IOPtics_implementation.md`):

- **It WILL include specific code recommendations** — module/file layout, public
  function/class signatures, data-structure and config schemas. (This is the
  explicit complement to the design doc, which forbids them.)
- Add a version number (start at 0.1), a date, and authors (JXP and Claude).
  It is a living document; bump the version whenever sensible.
- Each section should **trace back to the design document** (e.g. "implements
  Analysis §IOP retrieval") so the two stay aligned.
- Respect the design decisions already made: native wavelength grids per dataset;
  `expb_pow` (ExpB_Pow) and `giop` (GIOP) developed **in tandem** as the first two
  algorithms (to drive the comparison tooling), with more added incrementally;
  least-squares first-pass with MCMC on a subset; PACE noise model
  (`ocpy.satellites.pace`) for L23;
  provenance recorded in YAML/JSON beside the results table; single accumulating
  readthedocs site; persistent leaderboard; standalone/static BokehJS.
- Keep the canonical IOP-component scheme question open (design Open Questions);
  the code should not hard-code a single scheme prematurely.
- You are encouraged to propose your own implementation ideas.

## Prompts

### Coding

1. Read this doc. Execute the 1st task under "Prep/Tasks".
2. Read this doc. Execute the 2nd task under "Prep/Tasks".
3. Read this doc. Execute the 3rd task under "Prep/Tasks".

4. Read this doc. Execute the 1st task under "Package layout/Tasks".
5. Read this doc. Execute the 2nd task under "Package layout/Tasks".
6. Read this doc. Execute the 3rd task under "Package layout/Tasks".

7. Read this doc. Execute the 1st task under "Data preparation/Tasks".
8. Read this doc. Execute the 2nd task under "Data preparation/Tasks".

9. Read this doc. Execute the 1st task under "Algorithm registry/Tasks".
10. Read this doc. Execute the 2nd task under "Algorithm registry/Tasks".

11. Read this doc. Execute the 1st task under "Retrieval & run/Tasks".
12. Read this doc. Execute the 2nd task under "Retrieval & run/Tasks".

13. Read this doc. Execute the 1st task under "Metrics & diagnostics/Tasks".
14. Read this doc. Execute the 2nd task under "Metrics & diagnostics/Tasks".

15. Read this doc. Execute the 1st task under "Reporting/Tasks".
16. Read this doc. Execute the 2nd task under "Reporting/Tasks".

17. Read this doc. Execute the 1st task under "Testing & CI/Tasks".
18. Read this doc. Execute the 2nd task under "Testing & CI/Tasks".


## Prep

### Tasks

1. Start the implementation document `docs/design/IOPtics_implementation.md` with
   a **Preamble** (purpose, relationship to the design doc, version 0.1, today's
   date, authors JXP and Claude) and an **Architecture Overview** that maps each
   design-doc section (Data → prep, Analysis → registry/run, Metrics, Reporting)
   to the modules that will implement it, and states the BING/ocpy dependency
   boundary. Ask any questions in the Q&A section below. Log your work.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Prep section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

3. I have answered your new questions in the Q&A section below.  Please proceed to:

    - Make edits to the Prep section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Prep)

Started `docs/design/IOPtics_implementation.md` (v0.1) with a **Preamble**
(purpose, relationship to the design doc, version/date/authors, standing
decisions honored) and an **Architecture Overview** (the BING/ocpy dependency
boundary + a design-section → IOPtics-subsystem map). A few decisions worth your
call before I write the concrete package layout (next task):

1. **Top-level package name & namespacing.** I assume the package stays
   `ioptics/` (matching the repo and `ioptics/__init__.py`) with plain
   subpackages (`ioptics.prep`, `ioptics.registry`, `ioptics.run`,
   `ioptics.metrics`, `ioptics.diagnostics`, `ioptics.report`,
   `ioptics.provenance`). Any naming preferences before I commit them in Package
   layout? (e.g. `algorithms` vs `registry`, `run` vs `sweep`.)

Looks fine. I like algorithms and run.

2. **Config surface for a sweep.** Do you want sweeps driven by a **YAML config
   file** (declarative, shareable, pairs naturally with the YAML provenance), a
   **Python API** (build `AlgorithmSpec` objects in a script), or **both** (YAML
   as the user-facing entry, Python as the underlying API)? I lean toward both
   with YAML as the headline interface.

Both.

3. **Results-table store.** The design doc says CSV/parquet keyed by
   `(dataset, obs_id, algorithm)`. For the spectral, per-wavelength outputs
   (`a(λ)`, `bb(λ)` ± unc) do you prefer a **long/tidy** table (one row per
   `(obs, algorithm, component, wavelength)`) or a **wide** table with array-
   valued cells / a companion NetCDF/`xarray` for the spectra? This shapes the
   metrics layer. I lean long/tidy in parquet for the scalar table plus an
   `xarray`/NetCDF sidecar for full spectra.

I prefer the long/tidy table.

4. **Where the generalized prep ultimately lives.** Per design Q&A item D you
   said this is implementation, not design — for now I'm placing the generalized
   `prep_one`-style layer **inside IOPtics** (`ioptics.prep`) rather than
   contributing it upstream to BING. Confirm that's the intended home, or should
   it be a BING contribution (`bing.fitting.prep_one`) that IOPtics calls?

Yes, it should be inside IOPtics.

#### Claude's questions (2026-06-21, Prep round 2)

Applied all four answers to the implementation doc's **Architecture Overview**
(new "Resolved conventions" subsection: `ioptics.algorithms` + `ioptics.run`
naming; YAML-over-Python config; long/tidy parquet results table; prep inside
IOPtics) and bumped it to **v0.2**. One new question before Package layout:

5. **Sweep output directory layout.** Each sweep emits the long/tidy results
   table + the YAML/JSON provenance + figures, all stamped with versions. Do you
   have a preferred on-disk layout — e.g. a per-sweep directory
   `runs/<sweep_id>/{results.parquet, provenance.yaml, figures/}` with a
   stable/symlinked `latest/`, versus accumulating into a single growing table
   keyed by `sweep_id`? I lean toward per-sweep directories (clean provenance,
   easy to share one sweep) with the leaderboard aggregating across them. Where
   should `runs/` live — in the repo, or under `$OS_COLOR`/a configurable
   results root?

Ok, per-sweep directories sounds fine.  Put runs in `$OS_COLOR/IOPtics/runs/`.

#### Claude's note (2026-06-21, Prep round 3)

Applied Q5 to the implementation doc (per-sweep output directories under
`$OS_COLOR/IOPtics/runs/<sweep_id>/`, leaderboard aggregates across them) and
bumped to **v0.3**. No new questions — the **Prep** section (Preamble +
Architecture Overview, with all conventions resolved) is complete and ready to
seed **Package layout**.

## Package layout

### Tasks

1. Propose the concrete `ioptics/` package structure — modules, their
   responsibilities, and their dependencies on BING and ocpy. Cover at least:
   data prep, algorithm registry, run/sweep, metrics, diagnostics, plotting,
   reporting, and provenance. Write it into the implementation doc. Ask questions
   in the Q&A section below. Log your work.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Package layout section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

3. I have answered your new questions in the Q&A section below.  Please proceed to:

    - Make edits to the Package layout section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Package layout)

Wrote the **Package layout** section into `IOPtics_implementation.md` (v0.4): a
concrete `ioptics/` tree, a per-module responsibility/dependency table (covering
data prep, algorithm registry, run/sweep, metrics, diagnostics, plotting,
reporting, provenance), the inter-module data flow, the two load-bearing
dataclasses (`PreparedRecord`, `RetrievalResult`), and a module-granularity
restatement of the BING/ocpy boundary (ocpy confined to `datasets`+`noise`; BING
to `algorithms.spec`+`run`+`evaluate`). Grounded it by reading the real BING APIs
(`prep_one_l23`, `parameters.standard.{expb_pow,giop}`, `evaluate.*`,
`chisq_fit.fit`, `inference.fit_one/fit_batch`, `stats.calc_ICs`) and ocpy
(`Spectrum`, `satellites.pace`, the three loaders). Questions:

6. **`report` as a subpackage vs. flat modules.** I made `report/` a subpackage
   (`figures`, `tables`, `leaderboard`, `bokeh`, `rst`, `standard`) since
   Reporting carries the most moving parts. Fine, or would you rather keep
   everything flat (`ioptics.report`, `ioptics.leaderboard`, `ioptics.bokeh`)?

Your approach is fine.

7. **`scripts/` CLI vs. notebooks.** I included console entry points
   (`ioptics-run <config.yaml>`, `ioptics-report <sweep_id>`). Do you want a CLI
   as the primary driver, or do you prefer driving sweeps from notebooks/scripts
   (in which case `scripts/` is just thin `__main__` wrappers and the Python API
   is the real interface)?

I prefer driving sweeps from scripts.  See this example for syntax: https://github.com/Sea-Meets-the-Stars/fronts/blob/main/fronts/runs/prototypes/one_full/build_v4.py

8. **Truth-IOP component naming on `PreparedRecord`.** Since the canonical
   component scheme is deliberately open (design Open Q #1), I'm storing truth as
   a free-form dict keyed by component name (`a_ph`, `a_dg`, `bb_p`, scalars)
   rather than fixed fields — each dataset fills what it has. Agree that a dict
   (not a fixed schema) is the right call until the scheme is decided?

This sounds fine for now.

#### Claude's questions (2026-06-21, Package layout round 2)

Applied Q6 (kept the `report/` subpackage), Q7 (replaced the CLI with
script-driven sweeps — added `ioptics/runs/prototypes/<name>/build_vN.py`
following the `fronts` `build_v4.py` convention: one YAML source-of-truth,
integer-flag staged execution, paths from `$OS_COLOR`+sweep_id), and Q8 (made the
`PreparedRecord.truth` free-form dict explicit). Implementation doc → **v0.5**.
One follow-up:

9. **Sweep id.** The build script needs a stable `sweep_id` to name
   `$OS_COLOR/IOPtics/runs/<sweep_id>/`. Do you want it (a) set explicitly in the
   YAML config (e.g. `sweep_id: expb_giop_L23_v1`) — my lean, matching the
   `fronts` `run_id` convention; or (b) auto-derived from the config contents
   (algorithms+datasets+date hash)? Explicit is more legible and shareable; auto
   guarantees uniqueness.

Set explicitly in the YAML config.

#### Claude's note (2026-06-21, Package layout round 3)

Applied Q9 (explicit `sweep_id` in the YAML config). Made `sweep_id` a required
config field in the "Driving a sweep" subsection (author-chosen, not
content-hashed; names `$OS_COLOR/IOPtics/runs/<sweep_id>/`). Implementation doc →
**v0.6**. No new questions — the **Package layout** section is complete and seeds
Data preparation next.

## Data preparation

### Tasks

1. Design the **dataset-agnostic prep layer** that generalizes
   `bing.fitting.l23.prep_one_l23` to L23, PANGAEA, and GLORIA on their native
   wavelength grids, attaching the appropriate `Rrs` uncertainty (PACE noise model
   for L23 via `ocpy.satellites.pace`). Specify the API and the prepared-record
   data structure (the common form fed to the retrieval). Note how truth IOPs are
   attached where available. Write it into the doc. Q&A. Log.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Data preparation section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Data preparation)

Wrote the **Data preparation** section into `IOPtics_implementation.md` (v0.7).
Grounded it in the real loaders (`loisel23.load_ds`/`calc_Chl`,
`pangaea.load`/`spectrum` with families rrs/aph/acdom/bbp/kd,
`gloria.load_gloria`, `pace.gen_noise_vector`) and `prep_one_l23`. Key design
move: I **split `prep_one_l23`** into a data+noise+truth step (`ioptics.prep`,
dataset-agnostic, emits `PreparedRecord`) and an algorithm-config step (models/
priors/RT/initial-guess, moved to `ioptics.run`); native grids preserved (PACE σ
interpolated onto the native L23 grid rather than resampling to PACE bands).
Specified the dataset-adapter registry, the full `PreparedRecord` dataclass
(spectral truth as ocpy `Spectrum` per component → handles PANGAEA's per-family
grids; scalar truth as floats), `noise.attach_noise`, and the `prep_one`/
`prep_dataset` API. Three questions:

10. **L23 truth on its own grid vs. the Rrs grid.** I store each spectral truth
    component as an ocpy `Spectrum` on its native grid and let **metrics**
    interpolate truth→comparison grid at scoring time (keeps prep lossless). For
    L23 the truth and Rrs share the Hydrolight grid anyway; for PANGAEA they
    differ. OK to defer all truth/retrieval regridding to the metrics layer
    (prep stays lossless), or would you rather prep pre-align truth to `wave`?

We should pre-align truth to wave, and store a flag indicating that interpolation was performed.

11. **Default L23 `Rrs` perturbation.** I default `add_noise=False` for L23 — fit
    the clean Hydrolight `Rrs` using the PACE σ only as the inverse-variance
    weight (cleanest truth-recovery), with `add_noise=True` reserved for explicit
    Monte-Carlo. Agree that unperturbed-by-default is right, or do you want a
    single noise realization added by default (closer to a "real" observation)?

We need to perturb the spectrum by adding noise.

12. **PANGAEA `obs_id` subsetting.** PANGAEA has many IDs with varying
    completeness (not every ID has all of aph/acdom/bbp). For a first sweep,
    should prep (a) return *all* IDs and let metrics handle missing truth per
    component, or (b) filter to IDs that have a usable `Rrs` (+ at least one truth
    component) up front? I lean (a) — prep is permissive, metrics report coverage.

Let's use option (a).

#### Claude's questions (2026-06-21, Data preparation round 2)

Applied Q10/Q11/Q12 to the Data preparation section (impl doc → **v0.8**):
- **Q10:** prep now **pre-aligns** each spectral truth component onto the record's
  `wave` and records a per-component `truth_interp` flag (orig grid kept in the
  `Spectrum.metadata`; out-of-range → NaN, not extrapolated).
- **Q11:** L23 now defaults to **`add_noise=True`** — PACE σ both weights and
  perturbs the Hydrolight Rrs (single realization, seed recorded); added
  `Rrs_clean` to keep the noiseless input. In-situ stays unperturbed.
- **Q12:** prep is **permissive** — returns all PANGAEA IDs with a usable Rrs;
  missing truth components are simply absent and metrics report coverage.
One follow-up:

13. **Per-record noise seed bookkeeping.** I derive each L23 record's seed from a
    sweep-level `seed` + obs index (independent but reproducible realizations),
    and store `noise_seed` on the record + in provenance. Is a single sweep-level
    seed (deterministically expanded per obs) the right granularity, or do you
    want N independent Monte-Carlo realizations **per** spectrum (a `n_MC` knob,
    as in BING's `nMC`) already in the first design? I've assumed one realization
    per spectrum for now and left `n_MC` as a later extension.

## Algorithm registry

### Tasks

1. Design the **AlgorithmSpec** abstraction and registry: a declarative
   description of one algorithm (absorption + backscattering model choices,
   priors, RT options incl. Raman/Chl-fluorescence toggles, fit method, noise
   model) mapping onto BING's `init_model` / `parameters.standard`. Seed the
   registry with **both `expb_pow` (ExpB_Pow) and `giop` (GIOP)**, developed in
   tandem, and show how the two are configured side by side (and how a third,
   e.g. `gsm`, would be added). Write it into the doc. Q&A. Log.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Algorithm registry section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Algorithm registry)

Wrote the **Algorithm registry** section into `IOPtics_implementation.md` (v0.9).
Grounded it in the real BING surface: `parameters.p_ntuple.def_dict` (the full
field set), `parameters.standard.{expb_pow,giop,gsm}` (verbatim priors),
`models.{anw,bbnw}.init_model` registries, and `models.utils.init`. Designed
`AlgorithmSpec` as a serializable mirror of the BING `p` namedtuple
(`to_bing_p`/`from_standard`/`build_models`), a `register()`/`get()` registry
**seeded with both `expb_pow` and `giop`**, an expb_pow-vs-giop side-by-side table
(k=5 vs 3 → drives AIC/BIC), the one-line `gsm` addition, and the YAML surface.
Two questions:

14. **Noise model in `AlgorithmSpec` vs. on the record.** I kept `noise_model` as
    a provenance-only field on `AlgorithmSpec` but made `run` always fit against
    `record.varRrs`, treating the noise model as a **sweep-level constant held
    fixed across algorithms** (for fair comparison per the design doc). Agree the
    noise model should not vary per-algorithm within a sweep? (If you ever want to
    compare an algorithm under two noise models, that'd be two sweeps.)

That is correct, the noise model should not vary per-algorithm within a sweep.

15. **`fit_method` per-algorithm vs. per-sweep.** I allow `fit_method` both as a
    sweep default (`chisq` first pass) and as a per-algorithm override in YAML,
    plus a separate `mcmc_subset: N` (run MCMC on N spectra in addition to the
    least-squares pass). Is per-algorithm override useful, or would you rather
    `fit_method` be strictly sweep-level with the MCMC subset chosen by spectrum
    (not by algorithm)?

Per-algorithm override makes sense.

#### Claude's note (2026-06-21, Algorithm registry round 2)

Both answers confirmed the v0.9 design. Tightened the wording: the noise-model
note now states `noise_model` is **sweep-level and not a per-algorithm YAML
override** (Q14), and the YAML example shows a single sweep-level `noise_model:`
key alongside the per-algorithm `fit_method` override (Q15). Implementation doc →
**v0.10**. No new questions — the Algorithm registry section is complete and seeds
Retrieval & run next.

## Retrieval & run

### Tasks

1. Design the **run/sweep** layer: `run_algorithm(spec, record)` plus single /
   batch / all-algorithms×all-spectra sweeps; least-squares default with MCMC on a
   subset; reconstruction of `a(λ)`/`bb(λ)` ± uncertainty via BING's `evaluate`.
   Define the **results-table schema** (keyed by dataset/obs_id/algorithm) and the
   **YAML/JSON provenance record** (model config, RT options, fit method, noise
   model, priors). Write it into the doc. Q&A. Log.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Retrieval & run section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Retrieval & run)

Wrote the **Retrieval & run** section into `IOPtics_implementation.md` (v0.11).
Grounded in `chisq_fit.fit(items, models, rt_dict, bounds)`,
`inference.{init_mcmc,fit_one}`, `evaluate.{reconstruct_from_chains,
reconstruct_chisq_fits}`, `stats.{calc_chisq,calc_ICs}`, and
`rt.defs.rt_dict_from_p`. Specified `run_algorithm`/`run_batch`/`run_sweep`
(chisq over all + MCMC on `mcmc_subset`), the `RetrievalResult`/`ComponentFit`
dataclasses, uncertainty via covariance-sampling (least-squares) and chain
percentiles (MCMC) on the same percentile grid, the two long/tidy parquet schemas
(`results_spectral`, `results_scalar`), and the `provenance.yaml` record (incl.
priors). Three questions:

16. **Truth-free initial guess (important).** `prep_one_l23` seeds the
    least-squares `p0` from the *true* IOPs — fine for a demo, **circular for a
    benchmark**. I specified a truth-free `initial_guess()` (prior-central values
    refined by a QAA-style band inversion of the observed Rrs) and added a
    truth-free `record.init = {Chl, Y}` (Lee-2002 Y; OC band-ratio Chl) to seed
    BING's `init_other_bits`. Do you agree retrievals must never see truth (so I
    build the QAA-style seed), or is a from-truth seed acceptable for the L23
    first pass (faster to stand up, but not a fair benchmark)?

Yes, best to not see truth.

17. **Least-squares uncertainty by covariance sampling.** For the χ² path I draw
    ~1000 samples from `N(ans, cov)` and push them through
    `evaluate.reconstruct_chisq_fits` to get 68/95% bands matching the MCMC
    treatment. Acceptable (consistent intervals, ~1000× forward evals per fit but
    still cheap), or would you rather linearized propagation `J Σ Jᵀ` (faster, but
    Gaussian-in-param-space and breaks the log/positivity of amplitudes)?

Your approach is fine.  Should be fast enough.

18. **MCMC chains: persist or discard?** `run_sweep` reduces each MCMC fit to
    percentile bands in the tables. Should I **also** save the raw chains (NPZ, à
    la `bing.fitting.l23.save_chains`) under `runs/<sweep_id>/chains/` for corner
    plots / re-analysis, or is the reduced table enough (chains are large —
    ~nsteps×nwalkers×nparam×4 bytes each)? I lean: persist chains only for the
    `mcmc_subset` (it's small by design).

Save the chains.

#### Claude's note (2026-06-21, Retrieval & run round 2)

Q16 (no truth) and Q17 (covariance sampling) confirmed the v0.11 design as
written — no change. Q18 (save the chains) was the substantive edit: `run_sweep`
now persists each MCMC posterior's raw chains to
`runs/<sweep_id>/chains/<algorithm>_<obs_id>.npz` (BING `save_chains` convention),
`results_scalar` gains a `chain_file` pointer, and the per-sweep directory layout
(+ the `io` row and the sweep-output convention) now lists `chains/` and the two
`results_{spectral,scalar}.parquet` tables. Implementation doc → **v0.12**. No new
questions — the Retrieval & run section is complete and seeds Metrics &
diagnostics next.

## Metrics & diagnostics

### Tasks

1. Design the **metrics** module implementing the design doc's Metrics section:
   log-space MAE/bias, `Rrs` closure (χ², reduced χ²ᵥ, MAE with the dual-sided
   window), model selection (AIC/BIC/ΔBIC), uncertainty coverage at 68%/95%,
   "wins", ratio histograms, and the per-component/per-wavelength reduction rules
   (incl. handling partial-retrieval algorithms). Design the **diagnostics**
   (Taylor, Target, corner, residual/closure spectra, ΔBIC CDFs). Both consume the
   results table. Write it into the doc. Q&A. Log.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Metrics & diagnostics section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Metrics & diagnostics)

Wrote the **Metrics & diagnostics** section into `IOPtics_implementation.md`
(v0.13). Designed both modules as **pure table-in/table-out functions** of the
persisted sweep artifacts (no BING/ocpy imports, no re-fitting): `metrics.compute`
emits `metrics_{spectral,scalar,pairwise}.parquet`; the §1–5 primitives
(log10 MAE/bias/RMS, median ratio, ratio-hist buckets, Type-II regression; Rrs
closure with dual-sided window + QC; ΔBIC CDF; 68/95% coverage; wins/rankings) and
the partial-retrieval rule (score the non-NaN intersection, record `n`+coverage,
GLORIA `caveat` flag). `diagnostics` returns the arrays behind Taylor/Target/
scatter/ratio-hist/residual/corner/ΔBIC-CDF figures (corner loads the saved
chains). Three questions:

19. **Reference-wavelength matching to native grids.** I summarize accuracy at
    440/443 (abs) and 555/670 (bb), but native grids rarely hit those exactly
    (L23 Hydrolight grid; PANGAEA bands). Do you want metrics to (a) use the
    **nearest** native band within a tolerance (e.g. ±3 nm) and record the actual
    λ used, or (b) **interpolate** retrieval+truth to the exact ref-λ? I lean (a)
    (no extra interpolation of already-retrieved quantities; honest about the band
    actually used).

Use the nearest native band within a tolerance of ±3 nm.  Record it

20. **Stratification bins.** The design calls for stratifying by trophic
    level/Chl, water type (Case I/II), and S/N. For the L23+PANGAEA first pass,
    which Chl bins do you want (e.g. oligo `<0.1`, meso `0.1–1`, eutro `>1`
    mg m⁻³), and is Case I/II available/important now, or defer water-type
    stratification until GLORIA/in-situ metadata is wired in?

I like your 3 level stratification.

21. **`abs_log_err` as the "wins" tie-breaker metric.** For head-to-head wins I
    score each spectrum by `|log10(M/O)|` per component/ref-λ (closer wins). Is
    absolute log-ratio the right per-contest metric, or do you want wins decided
    on a different quantity (e.g. within-uncertainty agreement, or signed bias)?

Use yours for now.  We will revist this

#### Claude's note (2026-06-21, Metrics & diagnostics round 2)

Applied Q19/Q20/Q21 (impl doc → **v0.14**):
- **Q19:** ref-λ summaries use the **nearest native band within ±3 nm** and record
  the actual λ in a `ref_match` column (ref row omitted if none within tolerance).
- **Q20:** added a **Stratification** subsection with the 3-level Chl bins
  (oligo `<0.1`, meso `0.1–1`, eutro `>1` mg m⁻³); Chl from truth else
  `record.init`; S/N from the fixed noise model; Case I/II **deferred** until
  in-situ metadata is wired (the `stratum` machinery already supports adding it).
- **Q21:** marked `abs_log_err` (`|log10(M/O)|`) as the provisional wins metric,
  flagged for revisit.
No new questions — the Metrics & diagnostics section is complete and seeds
Reporting next.

## Reporting

### Tasks

1. Design the **reporting** module: the standard figure/table set, the on-demand
   standard report, the single accumulating readthedocs (`.rst`) site, the
   persistent **leaderboard**, and the **standalone/static BokehJS** interactive
   figures (select algorithm/dataset to inspect). Specify how reports are stamped
   with provenance/versions for reproducibility. Write it into the doc. Q&A. Log.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Reporting section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Reporting)

Wrote the **Reporting** section into `IOPtics_implementation.md` (v0.15). Designed
`ioptics.report` as a pure consumer of the persisted sweep artifacts (results +
metrics + chains + provenance): `plotting` static primitives (reusing
`bing.plotting.{show_anw_fits,corner_plot,hist2d}`); `report.figures`/`tables` for
the standard per-(algorithm,dataset) set (scatter, spectra±band, closure,
Taylor/Target, corner, ΔBIC-CDF, accuracy/QC tables); a **persistent cross-sweep
`leaderboard`** (`$OS_COLOR/IOPtics/leaderboard.parquet`, idempotent `update()`);
**standalone BokehJS** (`file_html` + CustomJS, select algorithm/dataset);
`report.rst`/`standard.build(sweep_id, kind=...)` for the three report types into
one accumulating Sphinx/readthedocs tree with the leaderboard as landing page and
provenance version stamps. Three questions:

22. **Where the `.rst` site lives.** I put generated pages under
    `docs/source/reports/<sweep_id>/` in the IOPtics repo Sphinx tree (committed,
    so readthedocs builds them), while the heavy artifacts (parquet/chains) stay
    under `$OS_COLOR/IOPtics/runs/`. Figures (PNG/PDF) and the Bokeh HTML get
    **copied** into the docs tree at report-build time. Is committing generated
    `.rst`+figures into the repo acceptable, or do you want the docs tree
    git-ignored and built fresh (readthedocs runs `build` as part of its build)?

That is good

23. **Leaderboard headline metric & ranking.** The leaderboard needs a default
    sort. I propose ranking primarily by **wins** then `|bias|`/MAE at the
    reference wavelengths, per (dataset, component). Is "wins" the right headline
    ranking, or would you rather lead with log-space **MAE** (more familiar) and
    show wins as a column?

Sure, that is fine.

24. **Per-obs figure volume.** `figures.spectra_set`/`closure_set` are per-spectrum
    — thousands for L23. I assume the standard report renders these only for a
    **curated handful** (e.g. the MCMC subset + a few per trophic bin) and relies
    on the interactive Bokeh + scatter/Taylor for the full population. Agree, or do
    you want per-obs figures for all spectra (large, slow)?

Agreed, only a handful.

#### Claude's note (2026-06-21, Reporting round 2)

All three answers confirmed the v0.15 design. Tightened the wording (impl doc →
**v0.16**): Q22 — made the artifact split explicit (`.rst` + figure PNGs + Bokeh
HTML committed into `docs/source/reports/<sweep_id>/`; parquet/chains stay under
`$OS_COLOR/IOPtics/runs/`, copied at build time); Q23 — documented the default
leaderboard ranking (wins, then `|bias|`/MAE at ref-λ per dataset/component, with
MAE/bias/coverage as adjacent columns); Q24 — stated per-obs figures render only
for a curated handful (MCMC subset + a few per trophic bin), full population via
aggregate + Bokeh. No new questions — the Reporting section is complete and seeds
Testing & CI (the final section) next.

## Testing & CI

### Tasks

1. Design the **testing strategy** — data-independent unit tests that always run
   plus skip-guarded tests that need `$OS_COLOR` data (mirroring ocpy's
   `test_pangaea.py` pattern), all in the `ocean14` environment — and any CI
   (noting the design decision that reports are generated on demand, not via CI).
   Write it into the doc. Q&A. Log.

2. I have answered your questions in the Q&A section below.  Please proceed to:

    - Make edits to the Testing & CI section to reflect the decisions.
    - Ask me any new questions you have in the Q&A section below.
    - Log your work in the Logs section below.

### Q&A

#### Claude's questions (2026-06-21, Testing & CI)

Wrote the **Testing & CI** section into `IOPtics_implementation.md` (v0.17) —
completing all eight topic sections. Mirrored ocpy's `test_pangaea.py` two-tier
pattern: a `conftest.py` with `needs_data`/`needs_l23`/`needs_pangaea` skip
guards; **Tier 1** data-independent tests (always run, synthetic fixtures) for
`algorithms`/`config`/`prep`/`noise`/`metrics`/`diagnostics`/`io`/`provenance`/
`leaderboard` plus a fast synthetic-5-band end-to-end micro-test (prep→run
chisq→evaluate→metrics, no $OS_COLOR, no MCMC); **Tier 2** skip-guarded tests on
real L23/PANGAEA incl. a small real sweep + one tiny-nsteps MCMC. CI runs Tier-1
`pytest` in `ocean14` on push/PR only (no sweeps, no report build — reports stay
on demand), plus an import/smoke check. Two questions:

25. **CI runner & the BING/ocpy GitHub installs.** Tier-1 CI needs `ocpy` and
    `bing` importable (they're GitHub installs, not PyPI). On a GitHub Actions
    runner, do you want the workflow to `pip install
    git+https://github.com/ocean-colour/{ocpy,bing}` against their **main**
    branches each run (simple, but a green IOPtics build then depends on upstream
    main staying importable), or pin them to a commit/tag (reproducible, manual
    bumps)? I lean pin-to-commit for a stable CI signal.

Let's use their **main** branches.  It will be on me to update them.  It is on my TODO list to put them on PyPi

26. **Coverage threshold / gating.** Do you want CI to enforce a coverage floor or
    fail-on-warning, or keep it advisory (just run `pytest -q`, report pass/fail)
    for now? I lean advisory at this stage — the package is young and the
    interesting tests are data-dependent (skipped on CI anyway).

Advisory is fine.

#### Claude's note (2026-06-21, Testing & CI round 2)

Applied Q25/Q26 (impl doc → **v0.18**): the CI workflow installs `ocpy`/`bing`
from the tip of their **`main`** branches (`git+…@main`) — JXP maintains
importability; PyPI release is on the TODO, after which these become version pins
— and CI is **advisory** (pass/fail from `pytest -q`; no coverage floor, no
fail-on-warning). No new questions — the Testing & CI section is complete, which
completes the implementation document.

## Logging

The "Logs" section will record Claude's work. Please use the following format:

### <Date> (Short summary of the work)

<Detailed description of the work and what you learned>

### <Date> (Short summary of the work)

<Detailed description of the work and what you learned>

...

## Logs

### 2026-06-21 (Coding #1 → Prep/Tasks #1: started the implementation document)

Executed Coding prompt #1 (Prep/Tasks #1). Before drafting, re-read the design doc
(`IOPtics_design.md` v0.15) and surveyed the two sibling packages to ground the
dependency boundary accurately:
- **BING** subpackages: `models.{anw,bbnw,functions}` (+ `init_model`),
  `parameters.{standard,p_ntuple}` (combos `expb_pow`/`expbf_pow`/`giop`/`gsm`/
  `k2b`), `rt.{rrs,raman,chl_fl,defs}`, `priors`, `fitting.{chisq_fit,inference,
  l23}`, `evaluate`, `stats`, `noise`. Confirmed `fitting.l23.prep_one_l23` is the
  L23-specific canonical example IOPtics must generalize.
- **ocpy** modules: loaders `hydrolight.loisel23`, `insitu.pangaea`,
  `insitu.gloria`; noise `satellites.pace` (+ modis/seawifs/sbg);
  `spectra.{core,io,utils}` (`Spectrum`/`SpectrumStack`).

Created `docs/design/IOPtics_implementation.md` (v0.1, 2026-06-21, authors JXP and
Claude) with two sections:
- **Preamble** — purpose (the *how* companion to the design doc's *what/why*; will
  include code specifics), explicit relationship/traceability table to the design
  doc, the standing decisions it honors (native grids; `expb_pow`+`giop` in
  tandem; chisq-first + MCMC subset; `ocpy.satellites.pace` noise; YAML/JSON
  provenance beside the results table; accumulating readthedocs; leaderboard;
  standalone BokehJS; canonical component scheme left open), supporting material,
  and conventions (`ocean14`; wrap-not-reimplement).
- **Architecture Overview** — a diagram + an explicit **BING/ocpy dependency
  boundary** (ocpy owns the data side: loaders, noise, Spectrum; BING owns the
  retrieval side: models, parameters, rt, priors, fitting, evaluate, stats,
  noise; IOPtics owns the uniform layer between), plus a **design-section →
  IOPtics-subsystem map** (Data→prep, Analysis→registry/run, Metrics→metrics &
  diagnostics, Reporting→reporting, +Testing & CI) naming each subsystem's
  responsibility and what it wraps. Left the detailed file/module API to the next
  task (Package layout) with `(forthcoming)` stubs for the remaining sections.

Wrote 4 questions to the Prep Q&A (package naming, YAML-vs-Python sweep config,
results-table store shape, and where the generalized prep lives).

### 2026-06-21 (Coding #2 → Prep/Tasks #2: applied Prep Q&A decisions)

Read JXP's answers to the four Prep questions and reflected them in
`docs/design/IOPtics_implementation.md`:
- **Q1 (naming):** module names fixed to **`ioptics.algorithms`** (registry) and
  **`ioptics.run`** (run/sweep), per JXP, alongside `ioptics.prep`,
  `ioptics.metrics`, `ioptics.diagnostics`, `ioptics.report`,
  `ioptics.provenance`. Updated the section→module map to name each module.
- **Q2 (config):** **both** — YAML config as the headline/shareable entry over a
  Python `AlgorithmSpec` API, with YAML parsed into the same objects.
- **Q3 (results table):** **long/tidy parquet** (row per
  `(dataset, obs_id, algorithm, component, wavelength)`; scalar summaries keyed by
  `(dataset, obs_id, algorithm)`); no wide/array layout.
- **Q4 (prep home):** the generalized `prep_one`-style layer lives **inside
  IOPtics** (`ioptics.prep`), not contributed upstream to BING.

Added a **"Resolved conventions (Prep Q&A)"** subsection to the Architecture
Overview capturing all four, so Package layout and downstream sections inherit
them. Bumped the implementation doc to **v0.2**. Wrote 1 new question (Q5: per-
sweep output directory layout + where the results root lives) to the Prep Q&A.

### 2026-06-21 (Coding #3 → Prep/Tasks #3: applied Q5, Prep section complete)

Read JXP's answer to Q5 (per-sweep directories; results root
`$OS_COLOR/IOPtics/runs/`). Added a fifth bullet to the implementation doc's
"Resolved conventions" subsection: each sweep writes a self-contained
`$OS_COLOR/IOPtics/runs/<sweep_id>/` directory (`results.parquet`,
`provenance.yaml`, `figures/`); the leaderboard aggregates across sweep
directories rather than mutating one global table; results root configurable.
Bumped the implementation doc to **v0.3**. No new questions — the Prep section
(Preamble + Architecture Overview) is complete and seeds Package layout next.

### 2026-06-21 (Coding #4 → Package layout/Tasks #1: wrote the Package layout section)

Executed Package layout/Tasks #1. Before drafting, read the actual upstream APIs
so the wrapping is thin and accurate:
- **BING:** `fitting.l23.{load_one_l23,prep_one_l23,fit_one,fit_with_LM,batch_fit}`
  (the canonical prep/fit flow IOPtics generalizes); `parameters.standard`
  (`expb_pow` → `['ExpBricaud','Pow']`, `giop` → `['GIOP','Lee']`, plus
  `gsm`/`k2b`); `evaluate.{reconstruct_from_chains,reconstruct_chisq_fits,
  calc_stats,calc_Rrs_from_models}`; `fitting.chisq_fit.fit(items,models,rt_dict,
  bounds)`; `fitting.inference.{init_mcmc,fit_one,fit_batch,run_emcee}`;
  `stats.{calc_chisq,calc_ICs}`; `noise.{scale_noise,add_noise}`;
  `rt.defs.rt_dict_from_p`.
- **ocpy:** `spectra.core.Spectrum`/`SpectrumStack` (dataclasses w/ wavelength/
  values/errors/units/metadata + netcdf/xarray IO); `satellites.pace.{wave,
  gen_noise_vector}`; loaders `hydrolight.loisel23.load_ds`, `insitu.pangaea.*`,
  `insitu.gloria.load_gloria`.

Wrote the **Package layout** section into `IOPtics_implementation.md`:
- Concrete `ioptics/` tree with `algorithms/` and `report/` subpackages and the
  decided module names (`prep`, `algorithms`, `run`, `metrics`, `diagnostics`,
  `report`, `provenance`, plus `config`, `records`, `datasets`, `noise`,
  `evaluate`, `io`, `plotting`, `scripts`, `tests`).
- A per-module responsibility table naming exactly what each wraps in BING/ocpy
  and the design-doc section it traces to (covers all eight required topics: data
  prep, algorithm registry, run/sweep, metrics, diagnostics, plotting, reporting,
  provenance).
- An inter-module **data-flow** diagram and the two load-bearing dataclasses
  (`PreparedRecord`, `RetrievalResult`), with full schemas deferred to the Data
  preparation / Retrieval & run sections.
- A **module-granularity dependency boundary**: ocpy imported only by
  `datasets`+`noise`; BING only by `algorithms.spec`+`run`+`evaluate`; metrics/
  diagnostics/report touch neither (operate on the results table) — keeping
  IOPtics a thin uniform layer with the upstream packages confined to the edges.
Bumped the implementation doc to **v0.4**. Wrote 3 questions (Q6: report
subpackage vs flat; Q7: CLI vs notebook as primary driver; Q8: free-form truth
dict vs fixed schema while the component scheme is open) to the Package layout Q&A.

### 2026-06-21 (Coding #5 → Package layout/Tasks #2: applied Q6–Q8, script-driven sweeps)

Read JXP's answers (Q6 report subpackage fine; Q7 **drive sweeps from scripts**,
with the `fronts` repo `build_v4.py` as the syntax reference; Q8 free-form truth
dict fine). Fetched the `fronts/runs/prototypes/one_full/build_v4.py` example to
mirror its convention (single-integer-flag staged execution, one YAML config as
source of truth, paths derived from an env-var base + run_id). Edits to
`IOPtics_implementation.md`:
- **Q7:** removed the `ioptics-run`/`ioptics-report` CLI; replaced `scripts/` with
  **`ioptics/runs/prototypes/<name>/build_vN.py`** + `run_vN.yaml`. Updated the
  module table row and added a new **"Driving a sweep (script-driven, not a CLI)"**
  subsection with a worked `build_v1.py` skeleton (`python build_v1.py <flg>`;
  bit-flag stages prep/run→metrics→report; YAML single source of truth; paths from
  `$OS_COLOR`+`sweep_id` so producer/consumers share conventions with no drift).
- **Q8:** made `PreparedRecord.truth` an explicit **free-form dict** (keys per
  what each dataset supports; metrics score on the intersection), justified by the
  open canonical-component-scheme decision.
- **Q6:** no change (the `report/` subpackage stays).
Bumped the implementation doc to **v0.5**. Wrote 1 new question (Q9: explicit
`sweep_id` in YAML vs. auto-derived hash) to the Package layout Q&A.

### 2026-06-21 (Coding #6 → Package layout/Tasks #3: applied Q9, section complete)

Read JXP's answer to Q9 (explicit `sweep_id` in the YAML config). Updated the
"Driving a sweep" subsection of `IOPtics_implementation.md` to make `sweep_id` a
required, author-chosen config field (not content-hashed) that names the sweep
output directory `$OS_COLOR/IOPtics/runs/<sweep_id>/`. Bumped the implementation
doc to **v0.6**. No new questions — the Package layout section is complete and
seeds Data preparation next.

### 2026-06-21 (Coding #7 → Data preparation/Tasks #1: designed the prep layer)

Executed Data preparation/Tasks #1. Read the real ocpy loaders
(`hydrolight.loisel23.{load_ds,calc_Chl}`; `insitu.pangaea.{file_catalog,load,
spectrum}` with spectral families rrs/aph/acdom/bbp/kd on per-family native λ;
`insitu.gloria.load_gloria`; `satellites.pace.{wave,gen_noise_vector}`) and
re-read `bing.fitting.l23.{load_one_l23,prep_one_l23}` to see exactly what to
generalize. Wrote the **Data preparation** section of `IOPtics_implementation.md`:
- **Key refactor:** `prep_one_l23` entangles data-conditioning with
  algorithm-config; IOPtics splits them — `ioptics.prep` does only data+noise+truth
  and emits a dataset-agnostic `PreparedRecord`; model/prior/RT/initial-guess move
  to `ioptics.run`. Native grids preserved (no `convert_to_satwave`); for L23 the
  PACE σ is interpolated onto the native Hydrolight grid.
- **Dataset adapters** (`ioptics.datasets`): a registry of thin ocpy wrappers
  (L23/PANGAEA/GLORIA) with an `obs_ids`/`load_obs` Protocol; a table maps each
  ocpy truth source to the IOPtics component key (e.g. L23 `ag+ad`→`a_dg`,
  `bbnw`→`bb_p`; PANGAEA `acdom`→`a_dg`; GLORIA scalar `a_cdom440`).
- **`PreparedRecord`** full dataclass: `dataset/obs_id/wave/Rrs/varRrs/truth/
  noise_model/meta`; spectral truth stored as ocpy `Spectrum` per component (each
  on its own native grid → handles PANGAEA), scalar truth as floats; `truth` left
  free-form per the open component scheme.
- **`ioptics.noise.attach_noise`** (`pace`|`insitu`|`pct:X`, optional add_noise)
  and the **`prep_one`/`prep_dataset`** API (parallel via ProcessPoolExecutor,
  picklable records), plus a worked L23/PANGAEA example.
Bumped the implementation doc to **v0.7**. Wrote 3 questions (Q10: defer truth↔
retrieval regridding to metrics vs pre-align in prep; Q11: L23 unperturbed-by-
default vs one noise realization; Q12: permissive vs filtered PANGAEA obs_id
subsetting) to the Data preparation Q&A.

### 2026-06-21 (Coding #8 → Data preparation/Tasks #2: applied Q10–Q12)

Read JXP's answers and edited the Data preparation section of
`IOPtics_implementation.md`:
- **Q10 (pre-align truth):** reversed the lossless-prep stance — prep now
  interpolates each spectral truth component onto the record's `wave`, adds a
  `truth_interp: dict[component→bool]` flag, keeps the original grid in
  `Spectrum.metadata['orig_wave']`, and leaves out-of-range truth as NaN (no
  extrapolation). Updated the `PreparedRecord` dataclass, the truth convention,
  the example, and the Package-layout summary to match.
- **Q11 (perturb Rrs):** flipped `attach_noise`/`prep` defaults so **L23 adds a
  single PACE noise realization** (seed recorded for reproducibility) and added a
  `Rrs_clean` field for the noiseless input; in-situ datasets stay unperturbed
  (`add_noise=False`). Made `noise`/`add_noise` dataset-aware defaults.
- **Q12 (permissive subsetting):** documented that `prep_dataset` returns all
  PANGAEA IDs with a usable Rrs; missing truth components are absent and metrics
  report coverage (no completeness filter).
Bumped the implementation doc to **v0.8**. Wrote 1 new question (Q13: single
sweep-level seed expanded per obs vs. an `n_MC` per-spectrum Monte-Carlo knob now)
to the Data preparation Q&A.

### 2026-06-21 (Coding #9 → Algorithm registry/Tasks #1: designed AlgorithmSpec + registry)

Executed Algorithm registry/Tasks #1. Read the BING configuration surface in full
— `parameters.p_ntuple.{def_dict,gen}` (every field a retrieval needs),
`parameters.standard.{expb_pow,giop,gsm,k2b}` (the verbatim model_names + prior
dicts), `models.anw.init_model` / `models.bbnw.init_model` registries, and
`models.utils.init` — confirming a BING "algorithm" is exactly one filled
namedtuple. Wrote the **Algorithm registry** section of
`IOPtics_implementation.md`:
- **`AlgorithmSpec`** dataclass mirroring the BING `p` losslessly: models
  (`anw_model`/`bbnw_model`), prior lists, nested `RTOptions`/`MCMCOptions`,
  Sdg/beta, `fit_method`, `noise_model`; with `to_bing_p()` (→ `p_ntuple.gen`),
  `from_standard()` (← `parameters.standard`), and `build_models(wave)` (→
  `models.utils.init` + `priors.set_standard_priors`).
- **Registry** (`register`/`get`/`available`) **seeded with both `expb_pow` and
  `giop`** via `from_standard`, with the in-tandem rationale.
- A side-by-side table (expb_pow `ExpBricaud`+`Pow`, k=5 vs giop `GIOP`+`Lee`,
  k=3) noting the k difference is what drives the AIC/BIC/ΔBIC metrics; the
  one-line `gsm` addition; and the YAML sweep surface (algorithms by name +
  per-field overrides), honoring the both-YAML-and-Python decision.
- A **noise-model note**: the field is provenance-only on the spec; `run` fits
  `record.varRrs`, with noise held fixed per-sweep for comparability.
Bumped the implementation doc to **v0.9**. Wrote 2 questions (Q14: noise fixed
per-sweep, not per-algorithm; Q15: `fit_method` per-algorithm override vs strictly
sweep-level) to the Algorithm registry Q&A.

### 2026-06-21 (Coding #10 → Algorithm registry/Tasks #2: applied Q14/Q15)

Read JXP's answers — both confirmed the v0.9 design (Q14: noise model must not
vary per-algorithm; Q15: per-algorithm `fit_method` override is wanted). Tightened
`IOPtics_implementation.md`:
- **Q14:** rewrote the noise-model note to state `noise_model` is a sweep-level
  constant, **not** a per-algorithm YAML override; `config` stamps the single
  sweep noise choice onto every spec for provenance. Added a top-level
  `noise_model: pace` key to the YAML example.
- **Q15:** affirmed `fit_method` is overridable per algorithm in the YAML surface
  text and example.
Bumped the implementation doc to **v0.10**. No new questions — the Algorithm
registry section is complete and seeds Retrieval & run next.

### 2026-06-21 (Coding #11 → Retrieval & run/Tasks #1: designed run/sweep, results schema, provenance)

Executed Retrieval & run/Tasks #1. Read the BING fitting/eval/stats surface
(`chisq_fit.fit`, `inference.{init_mcmc,fit_one,run_emcee}`,
`evaluate.{reconstruct_from_chains,reconstruct_chisq_fits,calc_stats}`,
`stats.{calc_chisq,calc_ICs}`, `rt.defs.rt_dict_from_p`,
`models.utils.init_other_bits`). Wrote the **Retrieval & run** section of
`IOPtics_implementation.md`:
- **`run_algorithm(spec, record)`** wires BING **on the record's native grid**
  (no `convert_to_satwave`): `spec.build_models(record.wave)`, `rt_dict_from_p`,
  truth-free `init_other_bits` from `record.init`, a **truth-free initial guess**
  (QAA-style, never from truth — a deliberate fix to `prep_one_l23`'s from-truth
  seed), then `chisq_fit.fit` (default) or `inference.fit_one` (MCMC).
- **Uncertainty (uniform across methods):** MCMC via `reconstruct_from_chains` +
  `eval_anw`/`eval_bbnw` sub-components; least-squares via covariance sampling
  (`N(ans,cov)` → `reconstruct_chisq_fits`) on the same 68/95% percentile grid;
  χ²ᵥ/AIC/BIC via `stats`. Defined `RetrievalResult`/`ComponentFit`.
- **Sweep layers** `run_batch` / `run_sweep` (chisq over all records + MCMC on
  `cfg.mcmc_subset`), writing under `$OS_COLOR/IOPtics/runs/<sweep_id>/`.
- **Results schema:** two long/tidy parquet files — `results_spectral`
  (row per dataset/obs_id/algorithm/fit_method/component/wavelength with
  value+68/95 bands+truth) and `results_scalar` (fit-quality + derived scalars ±
  unc + truth). Reference wavelengths sliced by metrics, not pre-baked.
- **`provenance.yaml`:** versions (ioptics/bing/ocpy commits, doc versions),
  verbatim config copy, per-algorithm block with full priors (incl. for MCMC),
  RT options, fit method, noise model; `provenance_id` links every result row.
- Added a truth-free `init` field to `PreparedRecord` (Chl/Y from observed Rrs)
  and noted it in the Data preparation section for consistency.
Bumped the implementation doc to **v0.11**. Wrote 3 questions (Q16: enforce
truth-free initial guess / build QAA seed; Q17: covariance-sampling vs linearized
LSQ uncertainty; Q18: persist raw MCMC chains for the subset) to the Retrieval &
run Q&A.

### 2026-06-21 (Coding #12 → Retrieval & run/Tasks #2: applied Q16–Q18)

Read JXP's answers: Q16 (no truth) and Q17 (covariance sampling) confirmed the
v0.11 design unchanged; Q18 (save the chains) was the substantive edit. Updated
`IOPtics_implementation.md`:
- **Q18:** `run_sweep` now persists each MCMC posterior's raw chains to
  `runs/<sweep_id>/chains/<algorithm>_<obs_id>.npz` (BING `save_chains`
  convention: chains + obs_Rrs/varRrs/Chl/Y) so corner plots / coverage tests /
  re-analysis need no re-fitting; added a `chain_file` column to
  `results_scalar` (null for χ² rows); updated the per-sweep directory layout in
  three places (Retrieval & run, the `io` module row, and the sweep-output
  convention) to list `chains/` and the two `results_{spectral,scalar}.parquet`
  tables.
- **Q16/Q17:** no change — the truth-free initial guess and covariance-sampling
  uncertainty stand as written.
Bumped the implementation doc to **v0.12**. No new questions — the Retrieval &
run section is complete and seeds Metrics & diagnostics next.

### 2026-06-21 (Coding #13 → Metrics & diagnostics/Tasks #1: designed metrics + diagnostics)

Executed Metrics & diagnostics/Tasks #1, implementing the design doc's Metrics
§1–6 + "Handling non-uniformity". Wrote the **Metrics & diagnostics** section of
`IOPtics_implementation.md`:
- **Principle:** both modules are pure **table-in/table-out** functions of the
  persisted results tables — no BING/ocpy imports, no re-fitting; a new algorithm
  is scored merely by appearing in the table.
- **`metrics.compute(sweep_id)`** → `metrics_{spectral,scalar,pairwise}.parquet`,
  with primitives for §1 (log10 multiplicative MAE/bias, RMS/unbiased RMS, median
  ratio, Erickson ratio-hist buckets, Type-II log–log regression + r²; per
  component, per wavelength, summarized at 440/443 & 555/670), §2 (Rrs closure:
  χ²ᵥ headline, log-space MAE/bias with the dual-sided window, `fit_noise` /
  `Rrs_MAE>0.25` QC), §3 (ΔBIC `<0`→complex, CDF over dataset; expb_pow k=5 vs
  giop k=3), §4 (68/95% **coverage** calibration test — the new metric — plus Nσ
  detection/upper-limits), §5 (wins + per-variable rankings).
- **Non-uniformity rule:** score only the non-NaN `(M,O)` intersection, record
  `n`+coverage on every row, GLORIA `caveat='CDOM_vs_adg'` flag; partial-retrieval
  algorithms are simply absent for unscored components.
- **`diagnostics`** returns the arrays behind each standard figure (Taylor,
  Target, scatter+guide-lines, ratio-hist, residual spectra, corner [loads saved
  chains], ΔBIC CDF) — figures rendered later by `plotting`/`report`.
Bumped the implementation doc to **v0.13**. Wrote 3 questions (Q19: nearest-band
vs interpolate for ref-λ summaries; Q20: Chl/water-type stratification bins for
the first pass; Q21: `abs_log_err` as the wins metric) to the Metrics &
diagnostics Q&A.

### 2026-06-21 (Coding #14 → Metrics & diagnostics/Tasks #2: applied Q19–Q21)

Read JXP's answers and edited the Metrics & diagnostics section:
- **Q19:** ref-λ accuracy summaries now use the **nearest native band within
  ±3 nm** (no re-interpolation) and record the matched λ in a `ref_match` column
  (omit the ref row if none within tolerance).
- **Q20:** added a **Stratification** subsection — 3-level Chl bins
  (oligotrophic `<0.1`, mesotrophic `0.1–1`, eutrophic `>1` mg m⁻³), Chl sourced
  from truth then `record.init`; S/N from the fixed noise model; Case I/II water
  type deferred (the `stratum` column supports adding it later, no schema change).
- **Q21:** marked the wins metric `abs_log_err` = `|log10(M/O)|` provisional,
  flagged for revisit.
Bumped the implementation doc to **v0.14**. No new questions — the Metrics &
diagnostics section is complete and seeds Reporting next.

### 2026-06-21 (Coding #15 → Reporting/Tasks #1: designed the reporting subpackage)

Executed Reporting/Tasks #1. Checked `bing.plotting` for reusable primitives
(`show_anw_fits`, `corner_plot`, `hist2d`). Wrote the **Reporting** section of
`IOPtics_implementation.md`:
- **Regenerability contract:** `report` reads only the persisted sweep artifacts
  (results + metrics + chains + provenance), so every report is on-demand and
  provenance-stamped — no re-fitting.
- **`plotting`** static primitives (scatter_log w/ 1:1/3:1 guides, ratio_hist,
  spectra_band, residual_rrs, taylor, target, corner→`bing.plotting.corner_plot`,
  dbic_cdf).
- **`report.figures`/`tables`:** the uniform per-(algorithm,dataset) standard set
  (scatter, spectra±band/decomposed, closure, Taylor+Target, corner for the MCMC
  subset, ΔBIC-CDF; accuracy + QC tables) → `runs/<sweep_id>/figures/`.
- **`report.leaderboard`:** persistent, **cross-sweep** — `update()` folds every
  sweep's `metrics_scalar` into `$OS_COLOR/IOPtics/leaderboard.parquet`
  (idempotent), `render()` for the landing page; grows as algorithms are added.
- **`report.bokeh`:** standalone/static BokehJS (`file_html` + CustomJS, select
  algorithm/dataset/stratum), embeddable in readthedocs, no server.
- **`report.rst`/`standard.build(sweep_id, kind)`:** the three report types
  (per_algorithm / cross_algorithm / per_dataset) into one accumulating Sphinx
  tree, leaderboard as landing page, each page provenance/version-stamped; built
  on demand (e.g. stage 3 of a `build_vN.py`), never by CI.
Bumped the implementation doc to **v0.15**. Wrote 3 questions (Q22: commit
generated .rst+figures vs git-ignore/build-fresh; Q23: leaderboard headline metric
wins vs MAE; Q24: per-obs figures for a curated handful vs all spectra) to the
Reporting Q&A.

### 2026-06-21 (Coding #16 → Reporting/Tasks #2: applied Q22–Q24)

All three answers confirmed the v0.15 design; tightened the wording in
`IOPtics_implementation.md`:
- **Q22:** made the artifact split explicit — `.rst` pages + figure PNGs + Bokeh
  HTML committed into `docs/source/reports/<sweep_id>/`; parquet tables + raw
  chains stay under `$OS_COLOR/IOPtics/runs/` (uncommitted), copied into the docs
  tree by `standard.build` at report time.
- **Q23:** documented the default leaderboard ranking (wins, then `|bias|`/MAE at
  the reference wavelengths per dataset/component; MAE/bias/coverage shown as
  adjacent columns).
- **Q24:** stated per-obs figures (spectra/closure/corner) render only for a
  curated handful (MCMC subset + a few per trophic bin); the full population is
  covered by the aggregate figures + interactive Bokeh.
Bumped the implementation doc to **v0.16**. No new questions — the Reporting
section is complete and seeds Testing & CI (the final section) next.

### 2026-06-21 (Coding #17 → Testing & CI/Tasks #1: designed the test strategy + CI)

Executed Testing & CI/Tasks #1 — the **final topic section**. Read ocpy's
`tests/test_pangaea.py` to mirror its skip-guard pattern (`_data_available()` +
`pytest.mark.skipif`). Wrote the **Testing & CI** section of
`IOPtics_implementation.md`:
- **Two tiers:** Tier-1 data-independent tests **always run** on synthetic
  fixtures (round-trip `AlgorithmSpec`↔BING `p`; registry seeding; YAML config
  parse/validation; prep truth pre-alignment + flags; noise reproducibility;
  metric primitives on hand-built (M,O) with known answers; io parquet round-trip;
  provenance; leaderboard idempotency) plus a **synthetic-5-band end-to-end
  micro-test** (prep→run chisq→evaluate→metrics, no `$OS_COLOR`, no MCMC).
  Tier-2 `@needs_l23`/`@needs_pangaea` tests run only with the data tree (real
  prep, a small real sweep, one tiny-`nsteps` MCMC to guard the chains path).
- **`conftest.py`** skip guards keyed on `$OS_COLOR` / L23 / PANGAEA availability.
- **CI deliberately light** (per the design's reports-on-demand decision): Tier-1
  `pytest` in `ocean14` on push/PR (data tests skip → green & fast), an
  import/smoke check; **no** sweeps/report builds in CI; readthedocs builds the
  committed `.rst` independently.
- No large fixtures in the repo; MCMC-in-tests always tiny `nsteps`.
Bumped the implementation doc to **v0.17**. Wrote 2 questions (Q25: pin ocpy/bing
GitHub installs to a commit vs track main in CI; Q26: coverage gating vs advisory)
to the Testing & CI Q&A.

**All eight topic sections of `IOPtics_implementation.md` are now drafted**
(Preamble + Architecture Overview, Package layout, Data preparation, Algorithm
registry, Retrieval & run, Metrics & diagnostics, Reporting, Testing & CI) — the
companion implementation doc the design doc referenced now exists end to end.

### 2026-06-21 (Coding #18 → Testing & CI/Tasks #2: applied Q25/Q26)

Read JXP's answers and finalized the CI subsection of `IOPtics_implementation.md`:
- **Q25:** CI installs `ocpy`/`bing` from the tip of their **`main`** branches
  (`git+https://github.com/ocean-colour/{ocpy,bing}@main`); JXP keeps upstream
  main importable, with a PyPI release on the TODO (after which these become
  version pins in `requirements.txt`).
- **Q26:** CI is **advisory** — pass/fail from `pytest -q`, no coverage floor or
  fail-on-warning (data-dependent tests skip on CI anyway); a gate can be added
  later.
Bumped the implementation doc to **v0.18**. No new questions — Testing & CI is
complete, which finishes the implementation document: all eight sections are
drafted and every Q&A through Q26 is resolved except none outstanding.

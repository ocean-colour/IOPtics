# Code IOPtics — Stage 6: Broaden (datasets & algorithms)

## Goal

Turn the cranks the architecture was built for: more datasets, more algorithms,
inelastic RT. **Exit criterion:** sweeps run on all three datasets and ≥3
algorithms; the leaderboard accumulates across them; the GLORIA scalar comparison
surfaces the CDOM-vs-`a_dg` caveat.

Implements **Data preparation** (PANGAEA/GLORIA adapters), **Algorithm registry**
(`gsm`), **Retrieval & run** (L23 X=4 RT toggles), and the **Staged plan / Stage 6**
(the final stage) of `docs/design/IOPtics_implementation.md`. One prompt per
module/addition.

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

## Context

- `docs/design/IOPtics_implementation.md` — §Data preparation (adapters table:
  PANGAEA `acdom`→`a_dg`, `bbp`→`bb_p`, scalars `chla`/`tss`; GLORIA scalar
  `a_cdom440`/`Chla`/`TSS`/`Secchi` + caveat), §Algorithm registry (`gsm` one-liner),
  §Retrieval & run / §Metrics (RT toggles, `caveat='CDOM_vs_adg'`).
- ocpy: `insitu.pangaea.{load,spectrum,file_catalog}`, `insitu.gloria.load_gloria`.
- bing: `parameters.standard.gsm`; `rt.{raman,chl_fl}` + the `rt_dict` toggles.
- **Build-script template:** `ioptics/runs/prototypes/expb_giop/build_v1.py`
  (`main(flg)`; sequential stages `1`=run, `2`=metrics, `3`=report). Stage-6's
  `build_v2.py` mirrors it.

### Stage 0–5 carryover (what already exists — the machinery you extend)

- **`datasets` — the adapter seam you add to.** `register_dataset(name, adapter)`
  + the `Adapter` Protocol (`obs_ids(**opts)`, `load_obs(obs_id, **opts) →
  RawObs`); `RawObs` carries `Rrs`, per-component `truth` (spectral values as
  **plain numpy arrays** on the native grid — `prep` wraps them as ocpy
  `Spectrum`s) + scalar truth, optional `Rrs_err`, and `meta`. `L23Adapter` (X=1
  elastic; **X=4** = +Raman/Chl-fl, already loadable; X=2 rejected) is the working
  template; `prep`/`noise` condition a `RawObs` into a `PreparedRecord`. New
  adapters import ocpy here and nowhere downstream.
- **`algorithms` — one-line registration.** `registry.register(AlgorithmSpec.
  from_standard('gsm', label='GSM'))`; a spec is fully declarative (a_nw/bb_nw
  models, priors, `rt` toggles, fit method) and round-trips through `run` unchanged.
- **`run`/`evaluate`** drive χ² over the sweep + MCMC on a subset; `AlgorithmSpec.rt`
  (`variable_Gordon`, `include_Raman`, `include_Chl_fl`, …) flows into the `rt_dict`
  the forward model consumes — the seam for L23 X=4 inelastic RT.
- **`io`** — `read_results`/`write_results`; the spectral table carries the model
  components + `Rrs_obs` (observed Rrs); chains persist `pnames`.
- **`metrics.compute(sweep_id, root=None, …)`** → wide, tidy
  `metrics_{spectral,scalar,pairwise}.parquet`, keyed with `dataset`/`fit_method`/
  `stratum` and ±3 nm ref-band match. **The GLORIA caveat is automatic:** compute
  stamps `caveat='CDOM_vs_adg'` on rows where `dataset` starts with `GLORIA` and
  `component == 'a_dg'` (see `metrics._caveat`) — an adapter just needs to name the
  dataset `GLORIA` and provide `a_dg` truth (from `a_cdom440`). PANGAEA's `a_dg`
  (from `acdom`) is genuine → **no** caveat.
- **`diagnostics`/`plotting`** — figure-data (arrays) + matplotlib primitives, all
  keyed by dataset/component so multi-dataset works unchanged.
- **`report`** (Stage 5, all wired): `report.standard.build(sweep_id,
  kind='cross_algorithm', root=None, docs_root=None)` → provenance-stamped
  `<kind>.rst` + copied PNG/CSV/Bokeh assets under
  `docs/source/reports/<sweep_id>/` + glob toctree; `report.leaderboard.update(
  runs_root=None, *, root=None, out=None, sweep_ids=None)` **accumulates across sweeps**
  (idempotent fold; keyed `(sweep_id, dataset, algorithm, stratum, component,
  ref_wave)`), `render`/`ranked` (wins → |bias| → MAE, all strata);
  `report.rst.write_leaderboard_landing(index_rst, render())` refreshes the
  landing. `report.bokeh.interactive_{scatter,leaderboard}` already carry a
  **dataset** selector.

### ⚠ Known constraints / decisions — read before coding

- **Build scripts use sequential stage numbers**, not a bitmask: `build_v2.py`
  `main(flg)` → `1` run, `2` `metrics.compute`, `3`
  `report.standard.build` + `leaderboard.update` + `write_leaderboard_landing`
  (mirror `build_v1.py`).
- **GLORIA caveat surfacing.** metrics stamps `caveat` and `tables.accuracy`
  carries it, so per-sweep report tables surface the mismatch. **But
  `leaderboard.update` currently folds only accuracy + wins and drops `caveat`.**
  If the *leaderboard* must show the caveat (exit criterion reads "GLORIA scalar
  comparison surfaces the caveat"), add `caveat` to the fold in `report.leaderboard`
  (Task 2/5) — decide with JXP.
- **Multi-dataset is a group-by, not new plumbing.** `metrics`/`report` already key
  on `dataset`; a two-dataset sweep just produces more rows. The Bokeh scatter +
  leaderboard table already filter by dataset.
- **`gsm` is χ²-first.** Register + a tiny χ² fit; MCMC is optional/per-spec.
- **Noise:** PANGAEA `noise='insitu'` (measured `Rrs` error → `varRrs`); GLORIA is
  scalar-truth-only (no spectral truth), skip-guarded until data is local.
- **CI stays light.** Data tests skip via the `needs_*` guards; the Sphinx-render
  report tests skip via `@needs_sphinx`. Keep new heavy tests Tier-2.

## Prompts

### Coding

0. Update this prompt file to reflect the changes from any earlier stage.
1. PANGAEA adapter in `datasets`.
2. GLORIA adapter in `datasets` (+ caveat flag).
3. Register `gsm`.
4. Enable L23 X=4 (Raman + Chl-fluorescence).
5. Tests + a multi-dataset / multi-algorithm sweep.

### Pull Requests

1. I have issued a PR for this stage. Please review it and post it to GitHub.  Also, investigate any CI issues and fix them. Please log your work in the Logs section below.
2. Please read the PR comments and make any needed changes to the code to address them.  And, if you have any additional questions, please add them to the Q&A section below. Log your work.

## Modules

### Tasks

1. **PANGAEA adapter.** Add to `datasets`: enumerate IDs (permissive — any usable
   `Rrs`), `load_obs` via `pangaea.load`/`spectrum` returning `Rrs` + truth
   (`a_ph`, `a_dg`←`acdom`, `bb_p`←`bbp`) on per-family native λ + scalars
   (`chla`, `tss`). `noise='insitu'`. `register_dataset('PANGAEA', …)`. Tier-2
   `@needs_pangaea`. Q&A. Log.

2. **Hanging**.  When executing the task below, you are hanging. I think on a test.  So investigate what might be wrong and implement a way to avoid your hanging.  Log your work.

3. **Grab GLORIA**.  Grab the GLORIA dataset from this URL `https://doi.pangaea.de/10.1594/PANGAEA.948492`.  Put it in the `$OS_COLOR/GLORIA` directory.  Log your work.

4. **GLORIA adapter.**  See my answers to your question.  Then, 
   add to `datasets`: `load_obs` via `gloria.load_gloria` →
   hyperspectral `Rrs` + scalar truth (`a_cdom440`, `Chla`, `TSS`, `Secchi`),
   mapped so `a_dg(440)` truth = `a_cdom440`; name the dataset `GLORIA` so
   `metrics` auto-stamps `caveat='CDOM_vs_adg'` (no per-adapter flag needed — but
   see Known-constraints re: surfacing it in the *leaderboard*). Skip-guarded
   (data may not be local). Q&A. Log.

5. **Register `gsm`.** `registry.register(AlgorithmSpec.from_standard('gsm',
   label='GSM'))`; confirm it round-trips and runs through `run_algorithm`
   unchanged. Tier-1 + a tiny χ² fit. Q&A. Log.

6. **L23 X=4 (inelastic).** Load `X=4` via the L23 adapter and wire the
   `include_Raman`/`include_Chl_fl` `AlgorithmSpec.rt` toggles → `rt_dict` so
   `run`/`evaluate` apply Raman + Chl-fluorescence. Tier-2 `@needs_l23` smoke
   (X=4 fit completes; `Rrs_model` differs from the elastic run). Q&A. Log.

7. **Tests + multi-everything sweep.** A `runs/prototypes/<name>/build_v2.py`
   (sequential stages, mirroring `build_v1.py`) over {L23(X=1), PANGAEA} ×
   {expb_pow, giop, gsm} (χ²) → tables + `metrics.compute` + `report.standard.build`
   + `leaderboard.update` accumulation; assert per-dataset/component coverage
   accounting and that the GLORIA caveat surfaces (Tier-2 with data; Tier-1 on a
   synthetic multi-dataset results table where possible). Q&A. Log.

8. **GLORIA fits.**  I have answered your Task 7 questions; see my responses.  It sounds like the GLORIA fits are not converging.  So, please investigate why and write a separate report on this called `reports/gloria_fits_report.md`.  Be sure to include Figures and save the Python scripts as `reports/scripts/gloria_fits_report.py`.  If you have any questions, please add them to the Q&A section below.  Log your work.  Use Fable if you can.

9. **More GLORIA fits.**  I have answered your Task 8 questions; see my responses.  Continue your exploration.  Also add a few example fits to the report.  Log your work.  Use Fable if you can.

10. **More More GLORIA fits.**  I have answered your Task 9 questions; see my responses.  Continue your exploration.  Also add a few example fits to the report.  Log your work.  Use Fable if you can.

11. **Dig into the literature**.  Please scour the literature for any relevant information backscattering in turbid waters.  Please add what you find to the report.  Include references and DOI citations. Log your work.  Use Fable if you can.

12. **Modifying bbp**.  Given your recommendations after exploring GLORIA fits and the literature, we should allow for backscattering functions that are representatitve of turbid waters.  Please describe the changes you propose making and any questions you have in the Q&A section. Do not make any changes to the code yet.  Log your work.  Use Fable if you can.

13. **BING changes**.  I agree that the next steps are to modify BING to allow for backscattering functions that are representatitve of turbid waters.  Please generate a new prompt doc in `Oceanography/python/bing/prompts` named `turbid_waters.md`.  I will then use it to add the new functionality to BING.  Log your work.  Use Fable if you can.

### Q&A

> Open questions for JXP (posed, not self-answered — JXP answers before the next
> task). Decisions already taken are recorded in the Logs.

**Task 0 (refresh prompt file).**

- **GLORIA caveat in the *leaderboard* (decide before Task 2/5).** The exit
  criterion reads "the GLORIA scalar comparison surfaces the CDOM-vs-`a_dg`
  caveat." `metrics.compute` already stamps `caveat='CDOM_vs_adg'` and per-sweep
  report tables carry it, but I confirmed `report.leaderboard` still folds only
  accuracy + wins and **drops `caveat`** (grep clean). Do you want the caveat
  added to the leaderboard fold (so the accumulated cross-sweep leaderboard shows
  it), or is surfacing it in the per-sweep report table sufficient to meet the
  exit criterion?
>A. Sure, add the caveat to the leaderboard fold.
- **ocpy/bing on CI `main` vs local checkouts.** Stage 6's PANGAEA/GLORIA/`gsm`
  work depends on `ocpy.insitu.{pangaea,gloria}` and `bing.parameters.standard.gsm`.
  They import fine here from the **local editable** `ocpy`/`bing`, but Stage 1's
  CI-lag pattern recurs whenever these aren't on the `git@main` that CI installs.
  Should I keep the new PANGAEA/GLORIA adapter tests Tier-2 (`@needs_pangaea`,
  skip-guarded) so CI stays green regardless, and treat "publish these to ocpy/bing
  `main`" as an upstream follow-up (as with `Rrs_to_rrs`/`PACE_error.csv`)?
>A. Yes, do so but add a reminder to remove it once I finally get the BING package on PyPI.

**Task 1 (PANGAEA adapter).**

- **Chlorophyll truth key: `Chl` vs `chla` (please confirm).** The task/design
  table name PANGAEA's scalar `chla`, but the machinery scores chlorophyll under
  the key **`Chl`**: `io._scalar_value(record, 'Chl')` fills `Chl_truth`
  (`io.py:186`) and `metrics.SCALAR_VARS` maps `Chl → Chl_truth`. So I mapped
  ocpy's `chla` (HPLC, falling back to fluorometric) onto the IOPtics truth key
  **`Chl`** — otherwise PANGAEA chlorophyll would be carried but silently
  **unscored**, and not comparable to L23's `Chl` in the leaderboard. `tss` is
  kept as-is (carried for provenance; nothing scores it yet — `beta_truth` is
  NaN). Confirm `Chl`, or do you want literal `chla` (and a metrics change in
  Task 5 to score it)?
  >A. Yes, use `Chl`.
- **In-situ noise with no measured error (please confirm the fraction).**
  PANGAEA V3 exposes no per-band `Rrs` uncertainty (the loader parses no error
  family), so `noise='insitu'` can't build `varRrs`. Per the design's "pct
  fallback otherwise," `prep_one` now falls back to `pct:0.05` when an `insitu`
  record has no `Rrs_err`, recording the honest tag `noise_model='pct:0.05'`
  (constant `prep._INSITU_PCT_FALLBACK`). Is 5% the fraction you want, or should
  in-situ Rrs error come from somewhere else (e.g. a per-sensor table)?
  >A. Ok, let's use 5%, but let's make sure this is clearly documented in the code, and in the documentation and any reports.
- **Permissive enumeration floor.** `obs_ids(min_rrs=1)` returns every `ID` with
  ≥1 finite `Rrs` band (design Q12 "any usable Rrs"). I verified `prep_one` does
  **not** crash even on a 1-band spectrum (OC4 `init` degrades gracefully), so
  nothing forces a higher floor — but a 1-band `Rrs` can't support a real fit.
  Keep the default at 1 (and let the Task-5 sweep pass a higher `min_rrs`), or
  set a more useful default floor (e.g. 5) here?
  >A. Let's use 5.
- **Reminder (per your Task-0 answer):** the PANGAEA (and forthcoming GLORIA)
  adapter tests are Tier-2, skip-guarded (`@needs_pangaea`), and prep imports
  ocpy lazily. **TODO: once BING/ocpy are on PyPI, revisit whether these can be
  promoted to always-run and drop the local-checkout dependence.**

**Task 2 (GLORIA adapter).**

- **GLORIA meta column names (please confirm).** The GLORIA CSVs aren't bundled
  in ocpy (only a download README) and aren't on disk here, so I inferred the
  meta-table column names from ocpy's GLORIA notebooks (`nb/GLORIA/*.ipynb`),
  **not** a data dictionary: id `GLORIA_ID`, CDOM `aCDOM440`, chlorophyll `Chla`,
  `TSS`, Secchi `Secchi_depth`; Rrs mean via `parse_table(df,'Rrs')`, std via
  `parse_table(df,'Rrs_std')`. Are these exact (esp. `aCDOM440` vs `aCDOM_440`,
  and `Secchi_depth`)? If any differ, it's a one-line change in the adapter's
  `_GLORIA_*` maps.
- **Row alignment.** `load_gloria` returns `(df_meta, df_Rrs, df_Rrs_std, qc)`;
  `parse_table` drops row identity, so I align `df_meta` rows **positionally**
  with the parsed spectra columns (same order/length). Is that how GLORIA ships,
  or should I join on `GLORIA_ID` if `df_Rrs` also carries it?
- **`a_cdom440` as a single-point `a_dg` (confirm the approach).** GLORIA's only
  IOP constraint is CDOM at 440 nm. To make it flow through the *existing*
  machinery (score retrieved `a_dg(440)`, derive `a_cdom440_truth`, and
  auto-stamp the `CDOM_vs_adg` caveat — all keyed on component `a_dg`), I map
  `aCDOM440` to a **single-point `a_dg` truth at 440 nm** (`NaN` elsewhere) rather
  than a plain scalar. Verified end-to-end (data-free + against real
  `gloria.parse_table`): on GLORIA's native 1 nm grid this yields
  `a_cdom440_truth = aCDOM440` and the caveat. **Caveat of the caveat:** it needs
  440 nm on the record grid (always true natively; a `[wv_min,wv_max]` trim must
  keep 440). OK, or would you prefer a scalar `a_cdom440` truth + a small
  `io`/`metrics` change (core) to score it and stamp the caveat?
- **`Chla → Chl`, `TSS → tss`, `Secchi_depth → Secchi`** (same rationale as
  PANGAEA `Chl`). `Secchi` is carried for provenance (nothing scores it yet).
  Confirm.
- **Surfacing the PANGAEA 5% fallback "in reports" (per your Task-1 answer).**
  Done in **code** (constant/comment + `prep` module & `prep_one` docstrings +
  `PANGAEAAdapter` docstring) and **documentation** (`docs/source/datasets.rst`
  note + design-doc §Noise). The per-record `noise_model` tag is honestly
  `pct:0.05`. For **reports**, `provenance.yaml` currently records the *configured*
  `noise_model` ('insitu'), not the effective per-record tag — I'll make Task-5's
  `build_v2` provenance/report note the effective 5% fallback for PANGAEA. OK to
  defer that surfacing to Task 5?

**Task 2 (Hanging — per-test hang guard).**

- **Default ceiling of 120 s (confirm).** I added a dependency-free per-test
  wall-clock guard in `conftest.py`; a stuck test now fails fast with a
  traceback instead of hanging the run. The default ceiling is 120 s
  (`$IOPTICS_TEST_TIMEOUT`; per-test `@pytest.mark.timeout(n)`; `0` disables).
  Every real test here runs in well under a second, so 120 s only ever trips on
  a genuine hang — but if you'd rather have a tighter default (e.g. 30 s) so a
  wedged local run frees up faster, say so and I'll change the one constant.
- **`pytest-timeout` as a hard dependency?** The guard is self-sufficient on
  Linux (CI included) and needs nothing installed, but it **defers to
  `pytest-timeout`** if that plugin is present (it catches some C-level hangs
  `SIGALRM` cannot). Want me to add `pytest-timeout` to `requirements.txt` so CI
  always has the stronger mechanism, or keep the zero-dependency guard as-is?
>A. Keep the zero-dependency guard as-is.
- **Separate finding (not the hang): local `bing` is broken with data mounted.**
  Running the suite with `$OS_COLOR` set, 14 tests fail at
  `import bing.fitting.l23` → `ModuleNotFoundError: No module named
  'correct_atmosphere'`. That's a missing module in the **local editable `bing`
  checkout**, not an IOPtics regression and not the hang. Flagging it so you can
  fix/ignore the `bing` side; it does not affect CI (Tier-1 skips these).
>A. Ok, I will fix the `bing` side.

**Task 3 (Grab GLORIA).**

- **Loader-path mismatch — where should GLORIA live so ocpy can read it?** I
  downloaded + extracted the dataset to `$OS_COLOR/GLORIA` as instructed (14
  files, flat). **But `ocpy.insitu.gloria.load_gloria()` reads from ocpy's
  *packaged* dir `<ocpy>/data/Rrs/GLORIA/`, not `$OS_COLOR`** — so as placed, the
  loader (and the `needs_gloria` guard, which probes the same ocpy path) still
  won't find it. To make Task 4 actually load real GLORIA, pick one: (a) symlink
  `<ocpy>/data/Rrs/GLORIA` → `$OS_COLOR/GLORIA` (quick, but writes into the ocpy
  checkout); (b) copy the CSVs into `<ocpy>/data/Rrs/GLORIA/` (ocpy loads
  unchanged, but ~250 MB inside the package tree); or (c) make `load_gloria()`
  (upstream ocpy) `$OS_COLOR`-aware and have the IOPtics adapter point it at
  `$OS_COLOR/GLORIA` (cleanest; an upstream ocpy change). Which do you want? I'll
  wire it in Task 4.
>A. That's not right.  Re-inspect the code in ocpy.
- **Column names now confirmed against the real data (no longer inferred).** The
  earlier "Task 2 (GLORIA adapter)" Q&A guessed the meta columns from notebooks;
  the downloaded `GLORIA_meta_and_lab.csv` header confirms them exactly:
  `GLORIA_ID`, `aCDOM440` (**not** `aCDOM_440`), `Chla`, `TSS`, `Secchi_depth`;
  `GLORIA_Rrs.csv` is keyed by `GLORIA_ID` with `Rrs_<nm>` columns from 350 nm.
  So the adapter's `_GLORIA_*` maps are correct as written — that part of the
  GLORIA-adapter Q&A is resolved by data.

**Task 4 (GLORIA adapter).**

- **Reminder: the `$OS_COLOR`-aware `load_gloria` is an *uncommitted* ocpy edit.**
  The GLORIA loader now resolving `$OS_COLOR/GLORIA` is a working-tree change in
  your local `ocpy` checkout (`M ocpy/insitu/gloria.py`), not on `ocpy@main`
  that CI installs. It doesn't break CI (GLORIA Tier-2 skips with no data tree),
  but GLORIA won't load anywhere until this lands upstream — same
  publish-to-ocpy-`main` follow-up as `Rrs_to_rrs`/`PACE_error.csv`. Flagging so
  it's on the TODO; no action needed from me unless you want me to do anything
  on the ocpy side.

**Task 5 (Register `gsm`).**

- **`h5py` was silently missing — I installed it + added to `requirements.txt`
  (confirm).** Running any L23 fit failed at `loisel23.load_ds` →
  `h5netcdf` → `ImportError: No module named 'h5py'`. `h5netcdf` needs `h5py` as
  its backend to read the L23 `.nc` files, but it wasn't in the env or
  `requirements.txt`. CI never noticed because all `@needs_l23` tests skip there
  (no data tree). I installed `h5py` (3.16.0) into `ocean14` and added it to
  `requirements.txt` — same pattern as the Task-0 `pyarrow` fix. OK? (It's a
  genuine missing dependency of the documented L23 workflow, so I think it
  belongs there regardless.)
- **`gsm` is registered chisq-first, priors as-shipped.** BING's
  `standard.gsm` sets very broad `log_uniform[-6,5]` priors and `add_noise=True`;
  `AlgorithmSpec` intentionally does **not** carry `add_noise` (IOPtics owns
  noise via `record.varRrs` + the sweep-level `noise_model`, same as
  expb_pow/giop). The χ² fit converges fine on L23 (χ²ᵥ≈2.2, a(440)/bb(555)
  ratios ≈0.96/0.92). Registering + the tiny χ² check is all I did per the task;
  say if you want a per-spec MCMC config for gsm too (else it inherits the
  default `MCMCOptions`).

**Task 6 (L23 X=4 inelastic).**

- **Raman is numerically unstable blueward of ~400 nm — where should the trim
  live?** On the native 350–900 nm grid an `include_Raman` fit returns an
  **all-NaN** `Rrs_model` (Raman excitation wavelengths fall off the water/Gordon
  tables at the blue end, and the correction factor divides by ~0). Trimming to
  `[400, 700]` (bing's own X=4 convention, `test_l23_fitting.py:610`) fixes it —
  I do that in the smoke test. For Task-7's `build_v2`, should the **sweep
  config** carry `wv_min/wv_max=[400,700]` for inelastic algorithms, or should
  `run`/`_prepare` **auto-clamp** the fit grid when `include_Raman` is on
  (raising/logging if the record can't supply 400–700)? I lean toward the
  config (explicit, per your existing `prep_one` trim), but it's your call.
>A. Use the config.
- **`correct_atmosphere` dependency for Chl fluorescence — add to
  `requirements.txt`?** The Chl-fl `Ed` comes from `correct_atmosphere.
  downwelling` (I wired `_prepare` to seed it, mirroring `bing.fitting.l23`).
  It's importable now (you fixed the bing side — thanks), but it's a local
  package (not on PyPI, not pinned in `requirements.txt`). Add it as a git/
  editable dep next to `ocpy`/`bing`, or leave it as a bing-side transitive dep?
  The X=4 test is `@needs_inelastic`-guarded so CI stays green either way.
>A. Add it to `requirements.txt`.
- **FYI (benign):** importing `correct_atmosphere` emits a
  `RuntimeWarning: numpy.ndarray size changed` — a C-extension built against a
  different numpy ABI. Harmless here (no crash), flagging in case you want it
  rebuilt.

**Task 7 (multi-everything sweep).**

- **Per-dataset noise in one sweep (confirm the approach).** A sweep carries a
  **single** `noise_model`, but the datasets want different ones (L23 `pace`,
  PANGAEA/GLORIA `insitu`). `build_v2` uses a uniform `pct:0.05` for the one
  cross-dataset {L23, PANGAEA} sweep (fair + comparable). To compare *native*
  noise models, run them as **separate per-dataset sweeps** and let
  `leaderboard.update` accumulate them (the design's "group-by / accumulate
  across sweeps"). OK, or do you want per-dataset `noise_model` added to the
  config?
>A. Run them as separate per-dataset sweeps.

- **`obs_ids` can't subset a mixed-id sweep.** `run_sweep` passes the same
  `obs_ids` to every dataset, and L23 ids are ints while PANGAEA/GLORIA are
  strings — so a small mixed L23/PANGAEA smoke isn't expressible (the Tier-1
  multi-dataset test therefore uses a **synthetic** results table, per the
  task's "where possible"). `build_v2` runs full datasets (`obs_ids=None`).
  Add per-dataset `obs_ids` to the config/`run_sweep`, or leave it?
>A. Add per-dataset `obs_ids` to the config.

- **GLORIA χ² fits don't converge (needs a decision).** A real GLORIA
  `expb_pow` χ² sweep (trimmed 400–750) **fails to converge** —
  `curve_fit: "Optimal parameters not found: max function evaluations
  exceeded"` on every sampled spectrum (turbid inland waters + broad GSM-style
  priors). So a real GLORIA leaderboard is currently empty of `a_dg` rows (all
  `fit_failed`). The **caveat mechanism is fully verified** on a synthetic
  GLORIA-named sweep (Tier-1), but surfacing it from *real* GLORIA needs the fit
  to succeed first. Want me to (a) raise `curve_fit`'s `maxfev` / improve the
  GLORIA initial guess, (b) fit GLORIA with MCMC instead, or (c) treat GLORIA
  fit-quality as a post-Stage-6 follow-up?
>A. This deserves further investigation.  

- **`wv_min/wv_max` added to the sweep config (per your Task-6 "use the
  config").** Beyond the Raman trim, it's needed for any dataset whose native
  grid exceeds the Gordon-coefficient table (GLORIA → 900 nm fails at 751 nm);
  `build_v2` sets `[400, 750]`. Flagging the small `config`/`run_sweep` change
  in case you'd have scoped it differently.
>A. Sounds fine

**Task 8 (GLORIA fits — convergence investigation).**

- **`fit_mcmc` crashes on GLORIA's string ids (real bug).** `ioptics/run.py`
  (`fit_mcmc`) does `idx = int(record.obs_id)` for BING's idx-keyed `Chl`/`Y`
  lookup, but GLORIA `obs_id`s are strings (`'GID_1'`) → `ValueError`. So GLORIA
  MCMC sweeps can't run today. Fixing it needs an indexing decision (synthesize a
  positional int index? change BING's Chl/Y keying?) — want me to fix it, and
  how?
>A. Synthesize a positional int index.

- **Turbid-water model family?** The investigation's root cause is **model
  inadequacy**: `expb_pow`/`giop`/`gsm` are open-ocean parameterisations and
  cannot represent GLORIA's turbid green-red Rrs (converged fits have median
  χ²ᵥ ≈ 250 vs ≈ 1 for L23). Should IOPtics grow a dedicated turbid/inland model
  family (NAP/mineral backscatter, wider CDOM, green-red-admitting a_ph), or is
  GLORIA intended as a stress-test the open-ocean models are *expected* to fail?
>A.  I'm not sure I understand.  Why can't a model with larger CDOM and NAP fit the GLORIA data?  Continue to explore this.
- **`maxfev` exposure.** Raising scipy `curve_fit`'s `maxfev` ~40× ~triples the
  yield (12.5%→37.5% for `expb_pow`) — necessary but not sufficient. Prefer
  raising it inside `bing/fitting/chisq_fit.py`, or plumbing a `maxfev` through
  an IOPtics `AlgorithmSpec`/RT option?
>A. Plumb a `maxfev` through an IOPtics `AlgorithmSpec`/RT option.
- **Reporting policy for poor fits.** How should a sweep record a GLORIA fit
  that "converges" but with χ²ᵥ ≈ 250 — as `fit_failed`, a new `poor_fit`
  status, or `ok` with the stat attached (and let metrics/leaderboard flag it)?
>A. As `poor_fit`.

**Task 9 (more GLORIA fits — range vs form).**

- **Which form extension to prototype first?** The exploration ruled out
  "wider CDOM/NAP" (see Log) — the wall is functional form in 500–750 nm. Do you
  want prototyped first: (a) a free-shape / multi-Gaussian `a_ph`, (b) an added
  mineral-NAP absorption+backscatter component, or (c) a published turbid-water
  scheme (QAA-turbid / red-NIR two-band)? I'd add it as a new `AlgorithmSpec`
  under `reports/` for testing.
>A. I'm not sure I follow.  I don't think CDOM/NAP will affect those wavelengths.  If you think you do, find me a reference from the literature that demonstrates this.  Continue to explore this.
- **NIR window for turbid waters.** The worst spectra rise strongly at
  700–750 nm (one peaks at 750). Extend the fit window past 750 nm for turbid
  GLORIA, or fit turbid GLORIA on a red-NIR sub-window?
>A. Stick with <750nm
- **Regime status vocabulary.** OK to classify turbid GLORIA (red-shifted peak /
  high χ²ᵥ) as `out_of_scope` rather than `fit_failed`? (Relatedly, you approved
  `poor_fit` in Task 8 — is `out_of_scope` a *distinct* third status, or should
  turbid GLORIA just be `poor_fit`?)
>A. Ok, add `out_of_scope` as yet another status.
- **Noise floor.** GLORIA's measured per-band `varRrs` (~2.3e-8, σ~1.5e-4 sr⁻¹)
  is so tight that even clear-water fits sit several σ/band off. Trust the 1-nm
  measured error, or fit GLORIA with an inflated / error-floor noise model?
>A.  Hmm..  Ok, let's try the inflated noise model and make sure to clearly state we did so.

**Deferred (Task-8 answers approved, not yet implemented — confirm the plan).**
- **`maxfev` via `AlgorithmSpec`.** Blocked on a BING change: `bing.fitting.
  chisq_fit.fit` takes no `maxfev` and doesn't reach `curve_fit`'s. I can (a) add
  a `maxfev` kwarg to BING's `chisq_fit.fit` + an `AlgorithmSpec` field, or (b)
  keep it IOPtics-only by having `fit_chisq` call `curve_fit` itself. Which?
>A. (a)
- **`poor_fit` status.** A reporting change touching `run`/`evaluate`/`io`/
  `metrics` (threshold policy + filtering). I deferred it pending the regime-flag
  decision above (so `poor_fit` vs `out_of_scope` are designed together).
>A. Ok

**Task 10 (more more GLORIA fits — it's backscatter, not CDOM/NAP).**

- **Which backscatter extension to prototype?** The corrected diagnosis: the
  single power-law `b_bp` can't supply the backscatter the red needs (see Log).
  Options for a turbid `b_bp`: (a) let `beta` go negative/flat for turbid water,
  (b) a two-component `b_bp` (mineral + organic, independent amplitudes), or (c) a
  published turbid `b_bp` slope parameterization. Add which as a new
  `AlgorithmSpec` under `reports/` for testing?
- **Is required `b_b` ≈ 0.2–0.4 m⁻¹ at 700 nm physically plausible** for these
  sites, or does it hint the **fixed Gordon `G` coefficients / `a_w`** are being
  pushed outside validity in very turbid water? If `G` should vary for turbid
  water, that's a separate lever worth testing — want me to?
- **Regime-flag threshold.** OK to classify turbid GLORIA as `out_of_scope`
  (distinct from `fit_failed`, per your Task-9 answer) using a relative-misfit or
  peak-wavelength threshold — and what threshold (e.g. red-shifted peak > 560 nm,
  or relative Rrs misfit > 25%)?
- **Round 4?** Do you want me to actually implement + benchmark a candidate
  turbid backscatter model (in `reports/`, not touching `ioptics/`), or is the
  diagnosis sufficient for now?

**Task 12 (Modifying bbp — turbid backscatter models; design only, no code yet).**

> Full proposal (map + formulas + priors) is in the Log entry below. These are the
> decisions I need before implementing. **No code changed this task.**

- **Which model(s) to build first?** (a) `Pow2` two-component (mineral+organic)
  only; (b) `Pow2` **plus** a cheap `PowFlex` single-power-law-with-free-slope
  ablation to prove two components are genuinely needed; (c) also a published
  turbid scheme (e.g. turbidity-dependent slope). **I recommend (b).**
- **`eval_bbnw` dispatch — add branches or refactor?** BING's
  `bbnw.bbNWModel.eval_bbnw` (`bbnw.py:240`) dispatches on `self.name` via a
  string `if/elif`, not polymorphically. Adding a model means adding an `init_model`
  dict entry **and** an `eval_bbnw` branch — a BING "core" edit either way. OK to
  just add branches, or would you prefer I first refactor `eval_bbnw` so each
  subclass overrides its own `eval_bbnw` (cleaner, but touches all existing
  models)?
- **Two-component form/priors.** Proposed
  `b_bp(λ) = B_min·(600/λ)^η_min + B_org·(600/λ)^η_org`, mineral term flat/large
  (`η_min` ~ uniform[-0.5, 0.5]), organic term steeper (`η_org` ~ uniform[0.5, 2]),
  both amplitudes `log_uniform[-6, 5]`. OK with pivot=600 nm and these ranges, or
  do you want η/amplitude priors anchored to specific literature values
  (Twardowski 2001 refractive-index/ratio ranges; Snyder 2008 slopes)?
- **Identifiability.** A 4-param bb + 3-param a model against GLORIA's tight
  measured noise may be degenerate under χ². Fit turbid GLORIA with **MCMC** (now
  works on GLORIA), the **inflated-noise floor** (Task-9 approved), and/or **fix
  `η_min`** to reduce the parameter count? Which combination do you want?
- **Where do the new models live?** They must go in the sibling **`bing`** package
  (`bing/models/bbnw.py` + `bing/parameters/standard.py`) because IOPtics imports
  all models from bing and `AlgorithmSpec.from_standard('<name>')` reads a
  `standard.<name>()` factory. IOPtics then adds each in **one line**
  (`registry.register(AlgorithmSpec.from_standard('expb_pow2', label='ExpB_Pow2'))`)
  with **no IOPtics core change**. Confirm bing is the intended home (and that you
  will push to bing `main` so CI/IOPtics see them — same publish-to-main follow-up
  as `Rrs_to_rrs`/`correct_atmosphere`/`load_gloria`).
- **Default seed or opt-in?** Register the turbid models into the always-on
  `registry._STANDARD_SEED`, or keep them opt-in (referenced only by the
  GLORIA/turbid sweep configs) so the open-ocean leaderboard isn't diluted?
- **Bundle with the deferred implementation pass?** The Task-8/9 approved-but-
  unimplemented items (`maxfev` via a `chisq_fit.fit` kwarg + `AlgorithmSpec`
  field; `poor_fit` and `out_of_scope` statuses; inflated-noise floor for GLORIA)
  pair naturally with these bb models so turbid fits both *converge* and are
  *scored/flagged* correctly. Do them in the same pass as the bb models, or bb
  models first in isolation?

## Logs

### 2026-07-26 (Stage 6, Task 13: BING prompt doc for turbid-water backscattering)

Wrote the requested BING-side prompt doc:
**`Oceanography/python/bing/prompts/turbid_waters.md`** (~430 lines). **No code
changed** in either repo — this task's deliverable is the prompt doc JXP will use
to drive the BING work. (Per "use Fable if you can": I *am* Fable this session, so
I did the code-map verification and drafting directly rather than delegating —
every code claim in the doc is checked against the current `bing` source, not
recalled from the Task-12 design.)

**Doc structure** (mirrors the house style of `prompts/chl_fl.md` / `rt.md`:
Goals → Skills → Code → Testing → … → Prompts → Logging → Logs, so JXP can drive
it prompt-by-prompt and Claude logs into the same file):

- **Goals + Why.** Four deliverables (`Pow2`, `PowFlex`, `maxfev`, tests/docs/
  benchmark) and the evidence that motivates them, condensed from
  `reports/gloria_fits_report.md`: required red `b_b` ~0.2–0.4 m⁻¹ vs fitted
  ~0.013 m⁻¹; "form, not range" (over-wide priors change χ²ᵥ by nothing);
  CDOM/NAP have no leverage at 500–750 nm; noise inflation is bookkeeping
  (χ²ᵥ 247→20 but misfit stays ~48%). Plus the 12 turbid-backscatter literature
  citations **with the DOIs as verified in the report** (Snyder 2008; Gordon 2009;
  Doxaran 2009/2002; Twardowski 2001; Boss 2004; Whitmire 2007; McKee 2009;
  Sullivan & Twardowski 2009; Neukermans 2012; Babin 2003 *L&O*; Nechad 2010;
  Gitelson 1992; Gons 1999). Links to the report and its script.
- **Code map with line numbers** — `bbnw.init_model` (`bbnw.py:76`), the base
  `__init__` (`:200`), the **string `if/elif` dispatch** in `eval_bbnw` (`:240`),
  `eval_bb_ex` (`:288`), `functions.powerlaw` (`functions.py:61`),
  `standard.expb_pow` (`standard.py:8`), `chisq_fit.fit` (`:42`), and the p0/
  bounds code in `l23.py:385-390`/`:611-618`.
- **The two contracts that bite** (found by reading, and the reason I didn't just
  reuse the skill's scaffold): (1) `init_guess` returns amplitudes in **linear**
  space and the *caller* log10s slots selected **by prior flavor**
  (`l23.py:387`, `ioptics/run.py::_log_mask`) — so `pnames` order must match the
  prior-dict order, with a `log_*` prior on every amplitude; (2) chi-squared
  bounds are read from `prior.pmin/.pmax` (`l23.py:611`,
  `ioptics/run.py::_prior_bounds`) — so new params must be `uniform`/
  `log_uniform`, never `gaussian`.
- **Concrete implementation sketches** for `standard.expb_powflex()` (a
  *parameters-only* change — `beta` prior widened to `uniform(-1, 2)`; no class,
  no eval branch, since `functions.powerlaw` already handles a negative
  exponent), the `bbNWPow2` class + its `eval_bbnw` branch (two `powerlaw` calls
  on `params[..., 0:2]` / `[..., 2:4]`, which preserves the `(nsample, nwave)`
  contract for 1-D *and* 2-D input), `init_guess`, and the prior table.
- **A 9-item test plan** for a new `bing/tests/test_bbnw.py` (the module doesn't
  exist yet), including the two guards I think matter most: `Pow2` must **reduce
  to `Pow`** when one amplitude is driven to zero (proves it's a strict
  generalization), and it must **honour the `wave=` kwarg** so
  `eval_bb_ex`/Raman is right — `Pow` honours it, but `Lee`/`GSM` silently
  ignore it, a pre-existing inconsistency the doc explicitly says not to copy.
- **`maxfev`** (JXP-approved option (a)): I verified in the installed scipy
  (1.18, `_minpack_py.py`) that `curve_fit` **renames `maxfev` → `max_nfev`**
  for the bounded 'trf' branch, so one `maxfev` kwarg on `chisq_fit.fit` is
  correct for both bounded and unbounded paths. Worth knowing because our fits
  always pass finite bounds, so the naïve `maxfev`-only-works-for-'lm' worry
  doesn't apply.
- **Benchmark + docs tasks**, and a *Downstream (IOPtics)* section restating that
  IOPtics needs **no core change** (one `registry.register(...)` line), that the
  models must land on **bing `main`** for CI, and one gotcha I found while
  checking: `ioptics/io.py:174` extracts a scalar literally named `beta`, so
  `Pow2` (whose exponents are `eta_min`/`eta_org`) will report `beta = NaN`
  unless JXP wants one renamed.
- **Design decisions I identified as JXP's, carried into the doc's own Open
  Questions** so they aren't lost: literature-anchored vs generic priors, pivot
  wavelength (600 nm vs a red pivot for the mineral term), whether to fix
  `eta_min` (3-param instead of 4-param, killing most of the degeneracy risk),
  whether to add a published turbid scheme as a third model, and whether the
  fixed Gordon `G` coefficients are valid at these backscatter levels.
  **The Task-12 Q&A above is still unanswered**; where those questions belong to
  BING (which models first, eval-dispatch refactor, form/priors, identifiability)
  the doc now carries them, and the `eval_bbnw` refactor is scoped as an explicit
  **opt-in step 8** rather than bundled in.
- **Flagged stale docs the pass must fix.** Both `bing/CLAUDE.md`'s "New
  Backscattering Model Template" and `.claude/skills/add-bbnw-model/SKILL.md`
  show `super().__init__(wave)` and a *subclass-level* `eval_bbnw` override —
  neither matches the code (priors are built in the base `__init__(wave,
  prior_dicts)`, and evaluation is the base-class string dispatch). The doc warns
  the implementer up front and puts the corrections in the docs task. Also noted
  that `docs/references.rst` is in the `index.rst` toctree but **does not exist**
  in `docs/`.

**No tests run** — nothing executable changed in IOPtics (the only new file is a
markdown prompt doc in the sibling `bing` repo).

### 2026-07-26 (Stage 6, Task 12: propose turbid backscatter (bbp) models — design only)

Design task per the prompt: *given the GLORIA/literature findings, propose how to
allow backscattering functions representative of turbid waters; describe the
changes and pose questions; **do not change code yet***. **No code changed** — I
mapped the existing backscatter machinery (read-only) and wrote the proposal
below + decision questions in Q&A. (Tried to run the code map through a **Fable**
subagent per "use Fable if you can"; JXP interrupted that call, so I did the
investigation directly.)

**What I read (the seam map, with refs).**
- **BING `bing/models/bbnw.py`** — base `bbNWModel` + subclasses `Cst`
  (spectrally flat, 1 param), `Pow` (power law `Bnw·(600/λ)^β`, 2 params:
  `Bnw`,`beta`, `bbnw.py:407`), `GSM` (fixed η=1.0337, 1 param), `Lee` (dynamic
  Y from Rrs ratio, 1 param), `Every` (one param/channel). Selection is a dict in
  `init_model` (`bbnw.py:64`); **evaluation is a string `if/elif` on `self.name`
  in `eval_bbnw` (`bbnw.py:240`)**; `eval_bb = bb_w + eval_bbnw` (`bbnw.py:275`);
  pure-water `bb_w` from L23 (`init_bbw`, `bbnw.py:217`).
- **BING `bing/parameters/standard.py`** — `expb_pow()` = `['ExpBricaud','Pow']`
  with `bpriors=[Bnw log_uniform(-6,5), beta uniform(0,2)]` — i.e. **`beta ≥ 0`,
  a *decreasing*-only power law** (`standard.py:8`). `giop`→`Lee`, `gsm`→`GSM`.
- **BING `bing/models/functions.py::powerlaw`** — `10^Bnw · (pivot/λ)^beta`,
  pivot 600 (`functions.py:60`).
- **IOPtics `ioptics/algorithms/spec.py`** — `AlgorithmSpec.bbnw_model` is a plain
  **string**; `to_bing_p` passes `[anw_model, bbnw_model]` to BING (`spec.py:115`);
  `build_models` → `bing.models.utils.init` → `bbnw.init_model` (`spec.py:186`);
  `from_standard(name)` just calls `bing.parameters.standard.<name>()`
  (`spec.py:146`). `registry.register` + `_STANDARD_SEED` (`registry.py:51`).

**Key architectural finding.** A turbid backscatter model is **purely a BING
change**; **IOPtics needs no core change**. Because `bbnw_model` is a string that
BING resolves and `from_standard` reads a `standard.<name>()` factory, IOPtics
adds a turbid algorithm in **one line**
(`registry.register(AlgorithmSpec.from_standard('expb_pow2', label='ExpB_Pow2'))`),
satisfying the "one `register()` call, no core changes" constraint. The catch:
the new models must land on **bing `main`** (CI installs bing from git) — same
publish-to-main follow-up as `Rrs_to_rrs`/`correct_atmosphere`/`load_gloria`.

**Proposed changes (all in the `bing` sibling package).**

1. **`Pow2` — two-component particulate backscatter (the literature-backed fix).**
   New `bbNWPow2(bbNWModel)` in `bbnw.py`:
   `b_bp(λ) = 10^B_min·(600/λ)^η_min + 10^B_org·(600/λ)^η_org` — a **mineral** term
   (large amplitude, ~flat slope) + an **organic** term (steeper). 4 params
   (`Bmin, eta_min, Borg, eta_org`). This supplies the ~0.1–0.4 m⁻¹ the red needs
   (flat mineral term) while the organic term preserves the blue — directly
   matching the composition split in the literature (Snyder 2008; Twardowski 2001;
   Boss 2004; Neukermans 2012; Doxaran 2009; Gordon 2009, all now cited in the
   report). Needs: the subclass, an `init_model` dict entry, an `eval_bbnw` branch
   (sum of two `functions.powerlaw` calls), and `standard.expb_pow2()`.
2. **`PowFlex` — free-slope single power law (cheap ablation).** Same `Pow` form
   but `beta` prior widened to ~uniform[-1, 2] so the slope can flatten or **rise**
   toward the red (the "white/mineral" limit). Implementable as just a new
   `standard.expb_powflex()` with a wider `beta` prior — **no new eval branch**.
   The GLORIA report already showed a *single* power law is insufficient, so this
   is the control that proves two components are genuinely needed, not the fix.
3. **(Optional) a published turbid slope** (turbidity-dependent η, or reuse the
   existing `Lee` dynamic-Y) — lower priority.

**Recommended path.** Build `Pow2` (primary) + `PowFlex` (ablation); register both
in IOPtics via `from_standard`; benchmark on a turbid GLORIA subset vs L23 to
confirm turbid χ²ᵥ / relative-misfit drops materially **and** clear/L23 is not
regressed. Because a 4-param bb + 3-param a model may be degenerate against
GLORIA's tight noise, pair the fit with MCMC (now GLORIA-capable) and/or the
Task-9-approved inflated-noise floor, and consider fixing `η_min`. This dovetails
with the deferred (approved, unimplemented) `maxfev` plumbing + `poor_fit`/
`out_of_scope` statuses so turbid fits both converge and are scored/flagged
correctly. Decisions needed → Q&A (Task 12).

### 2026-07-22 (Stage 6, Task 11: literature on turbid-water backscattering)

Scoured the peer-reviewed IOP literature for backscattering in turbid waters and
folded the findings — with **verified DOIs** — into `reports/gloria_fits_report.md`.
Ran the review via a **Fable** subagent (per the task), then independently
verified every DOI myself. **Report-only change** — no `ioptics/` source, no
script change.

- **New report section: "What the literature says about backscattering in
  turbid waters."** Organises published evidence under the report's four
  mechanistic claims: (1) the particulate-backscatter spectral **slope flattens**
  toward wavelength-independence in mineral-dominated water (Snyder 2008; Gordon
  et al. 2009 `n≈0.4-1.0`; Doxaran 2009), well below the assumed λ⁻¹-λ⁻²; (2) the
  **backscattering ratio** is several-fold higher in mineral water (~0.02-0.04 vs
  open-ocean ~0.005-0.01) as a composition signature (Twardowski 2001; Boss 2004;
  Whitmire 2007; McKee 2009; Sullivan & Twardowski 2009 VSF shape); (3) turbid
  backscatter **magnitude** is set by suspended mineral sediment, ~10× the organic
  mass-specific value (Neukermans 2012; Babin 2003 *L&O*); (4) the green/red-NIR
  reflectance peaks are backscatter through absorption minima and are the basis of
  SPM retrieval (Doxaran 2002; Nechad 2010; Gitelson 1992; Gons 1999). Each strand
  is tied back to the report's numbers (required `b_b`~0.2-0.4 vs fitted ~0.013;
  "form, not range") as external corroboration of the corrected diagnosis.
- **References section reworked.** The old note "*DOIs are omitted deliberately*"
  is replaced — all 8 pre-existing references now carry **verified** DOIs, and 11
  new turbid-backscatter sources were added, split into "absorption/water/model"
  and "backscattering in turbid/mineral waters" groups. 32 `doi:` citations total.
- **DOI verification (the load-bearing requirement).** Every DOI was checked
  against **Crossref** (`api.crossref.org/works/<doi>`) — author/year/title/journal
  all matched; the two the subagent flagged as inferred (Gordon et al. 2009
  *Opt. Express* `10.1364/OE.17.016192`; Gitelson 1992 IJRS
  `10.1080/01431169208904125`) were confirmed via both doi.org 302-resolution to
  the correct publisher URIs **and** Crossref metadata. The only item without a
  DOI is the IOCCG Report No. 5 (report series, no registered DOI) — stated as
  such, not fabricated.
- **Attribution note.** The 2009 *Optics Express* "Spectra of particulate
  backscattering in natural waters" is **Gordon et al. 2009**, not Sullivan &
  Twardowski (a common mix-up); the genuine Sullivan & Twardowski 2009 is the
  *Applied Optics* backward-VSF paper. Both cited correctly. The report did not
  previously contain this error (it had no Sullivan & Twardowski entry).
- **Suite.** CI-equivalent (`env -u OS_COLOR`) → **184 passed, 25 skipped** —
  unchanged baseline, as expected for a docs-only change. (An interim run showed
  9 `ModuleNotFoundError: ocpy` failures because this macOS `ocean14` lacked the
  editable `ocpy`/`bing`; JXP installed `ocpy` and the suite is green again.)

### 2026-07-21 (Stage 6, Task 10: GLORIA — corrected diagnosis, it's backscatter)

Third exploration round via the same **Fable** subagent. JXP was right that
CDOM/NAP can't govern 500–750 nm; corrected the analysis and the report. Only
`reports/` changed (no `ioptics/` change this task).

- **Corrected root cause: the red misfit is a *backscatter* deficit, not
  absorption.** CDOM/NAP absorption ∝ exp(−S(λ−440)) is essentially gone by the
  green-red (in the actual fits `a_dg` is ~8% of total absorption at 560 nm and
  ~0.06% at 700 nm), so widening CDOM/NAP priors has **zero** leverage there —
  the Round-2 "range-vs-form" test was the wrong lever (now marked *superseded*).
  Across 500–750 nm absorption is owned by **pure-water `a_w`** (rises ~500× from
  440→750; Pope & Fry 1997) + the `a_ph` 675 nm band — both already in the model.
  Inverting the observed turbid Rrs through the Gordon relation with the model's
  own absorption shows the **required** `b_b` rises to ~0.2–0.4 m⁻¹ in the red,
  while the fitted single **power-law `b_bp`** sits flat at ~0.013 m⁻¹ — short by
  ~an order of magnitude, and a decreasing power law can't make the rising/
  structured shape without wrecking the blue. The green/NIR Rrs peaks are
  backscatter shining through the absorption-minimum windows; the model finds the
  windows but can't fill them.
- **Numbers.** Backscatter is already free (`Bnw`∈1e-6..1e5, `beta`∈[0,2]);
  wide priors + MCMC still median χ²ᵥ ≈ 247 — the power-law *form* is the wall,
  not the range. **Inflated noise** (σ = max(σ_measured, f·Rrs), JXP-approved,
  clearly labelled): convergence stays 15/40; median χ²ᵥ drops 247→72 (f=5%)→20
  (f=10%) but the true relative Rrs misfit stays **~48%** — noise inflation is χ²
  bookkeeping, not a cure. Clear spectra fit (χ²ᵥ≈0.1, ~6% misfit); turbid miss
  by 80–91%.
- **Report + refs.** Round-2 section marked *superseded*; new "Correction: what
  governs Rrs at 500–750 nm" section; corrected Summary + Recommendation (the fix
  is a richer **backscattering** model, not wider absorption priors); a
  **References** section with canonical sources (Pope & Fry 1997; Bricaud/Morel/
  Prieur 1981; Babin et al. 2003; Bricaud et al. 1995; Gordon et al. 1988;
  Gitelson 1992; Gons 1999; Dall'Olmo & Gitelson 2005; IOCCG Report 5). 3 new
  figures — `iop_decay.png` (CDOM/NAP decay vs a_w rise vs b_bp), `iop_
  decomposition.png` (Rrs + absorption components + fitted-vs-required
  backscatter), `inflated_noise_examples.png` (4 clear→turbid fits at a 5%
  floor). 11 figures total; script gains `fit_sigma`/`floor_frac`,
  `round3_backscatter_and_noise` + 3 figure fns, self-contained/rerunnable
  (`py_compile` clean).
- **JXP decisions recorded (Task-9 answers; not yet implemented — held for an
  implementation pass):** `maxfev` via a BING `chisq_fit.fit` kwarg + an
  `AlgorithmSpec` field (option a); add a distinct **`out_of_scope`** status
  *and* the `poor_fit` status; keep the fit window **<750 nm**; GLORIA fits use
  an **inflated noise floor** (state it in outputs).

### 2026-07-20 (Stage 6, Task 9: GLORIA range-vs-form exploration + MCMC id fix)

### 2026-07-20 (Stage 6, Task 9: GLORIA range-vs-form exploration + MCMC id fix)

Continued the GLORIA investigation to answer JXP's Task-8 question — *why can't
larger CDOM/NAP fit GLORIA?* — via the same **Fable** subagent (resumed with its
report context), and applied the approved `fit_mcmc` id fix. Only `reports/`
(exploration) + the one-line `run.fit_mcmc` fix + its test changed.

- **Answer: it is functional FORM, not parameter range — tested, not asserted.**
  The amplitude priors (`Adg`/`Aph`/`Bnw`) are already `log_uniform` ~1e-6..1e5
  (effectively unbounded), so "larger CDOM/NAP" was *always* allowed. A
  deliberately over-wide `expb_pow` (amplitudes 1e-8..1e8, wider `Sdg`/`beta`)
  refit of 40 GLORIA spectra gives **byte-identical** median χ²ᵥ ≈ 2.47e2 (LM);
  MCMC with wide priors (independent of LM/`maxfev`) lands at ≈ 2.55e2. Three
  independent levers → same χ²ᵥ. **Residual localises to 500–750 nm** (relative
  residual saturates near −100%): the open-ocean form decays to ~0 exactly where
  turbid GLORIA has its green peak / ~649 nm hump / NIR rise. Failure tracks
  turbidity — *clear* GLORIA fits fine (best χ²ᵥ ≈ 0.08, blue-peaked), the worst
  (peak 750 nm) hits χ²ᵥ ~2.9e5.
- **Conclusion sharpened, JXP's remedy ruled out with numbers.** "Model
  inadequacy" stands but is now pinned to **functional form** in 500–750 nm; the
  fix is a richer model *form* (free/multi-Gaussian `a_ph` + explicit NAP), not
  wider ranges. Nuance added: the current models are adequate for *clear* GLORIA
  → flag by regime, don't reject GLORIA globally.
- **Report updated** (`reports/gloria_fits_report.md` gains "Continued
  exploration: can wider CDOM/NAP fit GLORIA?") with **example fits** (JXP asked)
  and 3 new figures — `range_vs_form.png` (wide-vs-standard χ²ᵥ on the 1:1 line +
  χ²ᵥ vs peak-λ collapse), `wide_example_fits.png` (4 clear→turbid overlays with
  χ²ᵥ), `residual_localization.png` (Rrs + relative residual, green-red band
  shaded). Script gains `continued_exploration()` + 3 figure fns, still
  self-contained/rerunnable (~40 spectra, MCMC nsteps=400); `py_compile` clean.
- **`fit_mcmc` id fix (approved).** `run.fit_mcmc` now synthesizes a positional
  index (`idx=0`, size-1 Chl/Y arrays) instead of `int(record.obs_id)`, so MCMC
  runs on GLORIA string ids (`'GID_1'`) — verified on GLORIA + L23. Regression
  test `test_micro.py::test_fit_mcmc_accepts_string_obs_id` (`@needs_l23`, tiny
  chain, string obs_id). CI-equivalent (`env -u OS_COLOR`) → **184 passed, 25
  skipped** (+1 skip). Under the hang guard.
- **Deferred (Q&A):** `maxfev` plumbing (needs a BING `chisq_fit` change) and the
  `poor_fit` status (reporting change, designed with the regime-flag decision).

### 2026-07-19 (Stage 6, Task 8: GLORIA fit-convergence investigation + report)

### 2026-07-19 (Stage 6, Task 8: GLORIA fit-convergence investigation + report)

Investigated why real GLORIA χ² fits don't converge and wrote a standalone
report with figures + a reproducible script. Ran the investigation via a **Fable**
subagent (per the task), seeded with the grounding facts I measured first; I
verified its deliverables. **No package source changed** — only `reports/`.

- **Root cause: model inadequacy (dominant) + too-small `maxfev` (secondary).**
  BING's open-ocean forward models can't represent GLORIA's turbid,
  green-red-peaked Rrs (peak ~568 nm + humps at ~649/700 nm; L23 peaks ~405 nm
  and decays). Even converged GLORIA fits sit at median χ²ᵥ ≈ **2.5e2** vs ≈
  **1.0** for L23 — the model misses by ~16σ/band, so LM never contracts its
  trust region and exhausts the eval budget (surfacing as the `maxfev` error).
  Raising `maxfev` ~40× lifts `expb_pow` yield 12.5%→37.5% (necessary, not a
  cure); band down-sampling (30 nm) and `varRrs`×100 do nothing (rules out band
  count / stiffness as independent causes); OC4 Chl init is unreliable in turbid
  water (0.1–2224 mg/m³) — a tertiary factor.
- **Corrected my earlier "0/20".** That was a benign contiguous-GID cluster
  (where even maxfev→100% fails); across the full 7572 the true `expb_pow`
  baseline is ~12.5%, maxfev ceiling ~37.5% — so sample choice matters and
  `maxfev` is not a general fix.
- **Convergence table (40 GLORIA / 40 L23, 400–750 nm):** expb_pow 12.5%, giop
  17.5%, gsm 25.0% baseline; all three ~37.5% at maxfev 20k; varRrs×100 and
  ds-30 nm stay 12.5%; L23 expb_pow 100%. Tiny MCMC (nsteps=300) ran on GLORIA.
- **Recommendation:** don't report the current models' GLORIA fits as successes;
  short-term bump `maxfev` + flag GLORIA as its own regime; real fix is a
  turbid-water forward model and/or MCMC + a turbid-robust Chl init.
- **Found a real bug (Q&A):** `run.fit_mcmc` `int(record.obs_id)` crashes on
  GLORIA string ids — GLORIA MCMC can't run until fixed.
- **Deliverables:** `reports/gloria_fits_report.md`,
  `reports/scripts/gloria_fits_report.py` (self-contained, rerunnable, `Agg`,
  bounded runtime; `py_compile` clean), and 5 figures in `reports/figures/`
  (Rrs shape contrast, peak-λ histogram, convergence-rate bars, χ²ᵥ
  distribution, fit overlay). Verified files present + figures non-empty; did
  not re-run the ~35 min script. Suite unaffected (no `ioptics/` change).

### 2026-07-19 (Stage 6, Task 7: multi-everything sweep + leaderboard caveat)

### 2026-07-19 (Stage 6, Task 7: multi-everything sweep + leaderboard caveat)

The final Stage-6 task: the multi-dataset × multi-algorithm sweep driver, the
leaderboard caveat fold (per your Task-0 answer), and the config wavelength trim
(per your Task-6 answer). Exit criterion — ≥3 algorithms, multi-dataset sweep,
leaderboard accumulates, GLORIA caveat surfaces — is met (see the GLORIA
fit-convergence caveat in Q&A).

- **`runs/prototypes/multi_v2/{build_v2.py,run_v2.yaml}`** — mirrors `build_v1`
  (sequential stages `1` run / `2` `metrics.compute` / `3`
  `standard.build` + `leaderboard.update` + `write_leaderboard_landing`). Sweep:
  `{L23, PANGAEA} × {expb_pow, giop, gsm}`, χ², uniform `pct:0.05` noise,
  `wv_min/wv_max=[400,750]`.
- **Leaderboard now folds the GLORIA caveat** (`report.leaderboard`). `_fold_
  sweep` carries the `caveat` column from `metrics_scalar` through the fold, and
  `render` shows it (with `fillna('')` so pre-caveat/non-GLORIA rows stay blank).
  So the accumulated cross-sweep leaderboard surfaces `CDOM_vs_adg` on GLORIA
  `a_dg` rows — the exit criterion. (Was the open Known-constraint;
  you approved adding it.)
- **`wv_min/wv_max` added to `SweepConfig`** (+ `from_dict` validation, `to_dict`
  round-trip) and threaded through `run_sweep → prep_dataset`. Implements your
  "use the config" answer for the Raman trim, and unblocks datasets whose native
  grid overruns the Gordon table (GLORIA).
- **`correct_atmosphere` added to `requirements.txt`** (git dep, next to
  ocpy/bing) — your Task-6 answer.
- **Tests (Tier-1, always run).** `test_sweep_multi.py`:
  (1) `build_v2` config parses + stage dispatch (mirrors the build_v1 test);
  (2) a synthetic **{L23, PANGAEA, GLORIA} × {expb_pow, giop, gsm}** results
  table → `metrics.compute` + `leaderboard.update` asserting per-dataset/
  component coverage **and** that the GLORIA `CDOM_vs_adg` caveat is stamped on
  GLORIA `a_dg` rows only (not L23/PANGAEA `a_dg`, not GLORIA non-`a_dg`) and
  appears in the rendered table. `_make_pair` gained a `dataset=` kwarg
  (default `'L23'`, back-compatible).
- **Real-data check (not committed — flaky).** A real GLORIA χ² sweep confirmed
  the load/trim/metrics/leaderboard chain runs, but every `expb_pow` fit failed
  to converge (`curve_fit` maxfev) → no `a_dg` rows; hence the caveat is
  verified via the synthetic Tier-1 path and GLORIA fit-convergence is posed in
  Q&A.
- **Suite.** CI-equivalent (`env -u OS_COLOR`) → **184 passed, 24 skipped**
  (was 181/24: +3 Tier-1 — build_v2 config, build_v2 dispatch, multi-dataset
  coverage+caveat). Config round-trip green. Under the hang guard; no wedge.
  Changed: `report/leaderboard.py`, `config.py`, `run.py`, `requirements.txt`,
  `tests/test_metrics.py`, new `tests/test_sweep_multi.py` + `runs/prototypes/
  multi_v2/`.

### 2026-07-15 (Stage 6, Task 6: L23 X=4 inelastic RT)

### 2026-07-15 (Stage 6, Task 6: L23 X=4 inelastic RT)

Wired Raman + Chl-fluorescence through the fit and verified an X=4 fit's
`Rrs_model` shifts vs the elastic run.

- **Toggle -> rt_dict was already wired (Stage 2).** `AlgorithmSpec.rt.
  include_Raman/include_Chl_fl` -> `to_bing_p` -> `p` -> `rt_defs.rt_dict_from_p`
  -> `rt_dict`, which `bing.evaluate` (the fit + reconstruction forward model)
  reads. Confirmed end-to-end; no change needed there.
- **Raman: no extra wiring, but trim the grid.** Both models call `init_raman()`
  in their constructors (`wave_ex`/`bb_R` always set), so `eval_a_ex`/
  `eval_bb_ex` work and the forward model applies Raman for free. **But** on the
  native 350–900 nm grid the reconstruction is all-NaN (blue-end excitation off
  the tables); trimming to `[400, 700]` (bing's X=4 convention) gives a finite
  `Rrs_model` differing from elastic by ~1.5%. Documented in a `_prepare`
  comment; trim decision posed for Task 7 (Q&A).
- **Chl fluorescence: added the missing model setup in `run._prepare`.** When
  `spec.rt.include_Chl_fl`, `_prepare` now seeds the a-model's downwelling
  irradiance — `Ed = downwelling.downwelling_irradiance(wave, 0.)`,
  `Ed_em` at `chl_fl.LAMBDA_FL_PRIMARY` (685 nm), then
  `models[0].init_Chl_fluorescence(Ed, Ed_em)` — mirroring `bing.fitting.l23`.
  `correct_atmosphere`/`bing.rt.chl_fl` imported lazily (only when the toggle is
  on). Without this the fl branch crashed (`i_Chl_ex/Ed_ex` unset).
- **X=4 loads via the L23 adapter.** `load_obs(0, X=4)` → `meta['X']==4`; its
  `Rrs` differs from X=1 by ~1.8e-3 (the inelastic signal in the synthetic obs).
- **Verified (data-mounted).** Fitting an L23 X=4 record (trimmed 400–700) with
  expb_pow: elastic χ²ᵥ≈1.47; +Raman differs by 1.7e-4; +Chl_fl by 9.6e-4; both
  on by 1.2e-3 — all `status='ok'`, finite `Rrs_model`. `correct_atmosphere` is
  importable now (bing-side fix).
- **Test.** `test_micro.py::test_l23_x4_inelastic_rt_shifts_rrs_model`
  (`@needs_l23` + new `@needs_inelastic` guard for `correct_atmosphere`): elastic
  vs Raman+Chl_fl on an X=4 record; both complete, `Rrs_model` differs
  (rel > 1e-3). `conftest` gains `_correct_atmosphere_available` +
  `needs_inelastic`.
- **Suite.** `test_micro` with data → **3 passed**; CI-equivalent
  (`env -u OS_COLOR`) → **181 passed, 24 skipped** (+1 skip = the guarded X=4
  test). Under the hang guard; no wedge. Only `run.py` + tests/conftest changed.

### 2026-07-15 (Stage 6, Task 5: register `gsm`)

### 2026-07-15 (Stage 6, Task 5: register `gsm`)

Added `gsm` to the algorithm registry as a **one-line** seed entry (no core
changes) and verified it round-trips and fits.

- **Registration.** Appended `('gsm', 'GSM')` to `registry._STANDARD_SEED`, so
  `AlgorithmSpec.from_standard('gsm', label='GSM')` seeds it alongside
  expb_pow/giop. `registry.available()` → `['expb_pow', 'giop', 'gsm']`. No
  change to `spec`/`run`/anything else — `gsm` flows through the existing
  declarative machinery unchanged.
- **Verified data-free (Tier-1).** `from_standard('gsm')` → models `GSM`/`GSM`,
  2 apriors (Adg, Aph) + 1 bprior (Bbp) = k=3 free params, `othera_priors=None`,
  `fit_method='chisq'`; `to_bing_p()` round-trips model names + priors verbatim
  against `standard.gsm()`.
- **Verified the χ² fit (Tier-2, `@needs_l23`).** `run_algorithm(registry.get(
  'gsm'), prep_one('L23', 0))` → `status='ok'`, χ²ᵥ≈2.23, components
  `{a, bb, a_ph, a_dg, bb_p, Rrs_model}`, recovers planted IOPs (a(440) ratio
  0.96, bb(555) ratio 0.92). Confirms gsm runs through `run_algorithm` unchanged.
- **Env fix (flagged in Q&A).** `h5py` was missing (h5netcdf's backend for the
  L23 `.nc` files) — no L23 fit could run until installed. Installed into
  `ocean14` (3.16.0) and added `h5py` to `requirements.txt` (CI never hit this
  because `@needs_l23` skips there). Mirrors the Task-0 `pyarrow` addition.
- **Tests.** `test_spec.py::test_from_standard_gsm`,
  `test_registry.py::test_seeded_with_gsm` (Tier-1, always run);
  `test_micro.py::test_gsm_chisq_fit_recovers_iops` (Tier-2, `@needs_l23`).
  gsm-focused → **15 passed**; CI-equivalent full suite (`env -u OS_COLOR`) →
  **181 passed, 23 skipped** (was 179/22: +2 Tier-1 always-run, +1 Tier-2
  skip-on-CI). All under the hang guard; no wedge.

### 2026-07-14 (Stage 6, Task 4: GLORIA adapter — verified against real data)

### 2026-07-14 (Stage 6, Task 4: GLORIA adapter — verified against real data)

With the dataset grabbed (Task 3) and JXP's `$OS_COLOR`-aware `load_gloria`
edit in ocpy, drove the (already-implemented) `GLORIAAdapter` end-to-end against
the **real** GLORIA-2022 data and made the tiered guard match the new loader.

- **Re-inspected ocpy (per JXP's Task-3 answer).** `gloria.load_gloria()` now
  reads `$OS_COLOR/GLORIA` when `$OS_COLOR` is set (else the packaged
  `data/Rrs/GLORIA`). My earlier "reads only the package dir" claim was stale —
  corrected. So the Task-3 download location is exactly where the loader looks.
- **`conftest._gloria_available()` now mirrors that resolution** (`$OS_COLOR/
  GLORIA` first, else packaged) instead of probing only the package tree — so
  the `@needs_gloria` Tier-2 tests **run** where the data is mounted and still
  skip cleanly on CI.
- **Real-data verification (`$OS_COLOR` set, under the hang guard).**
  `obs_ids()` → 7,572 spectra in ~0.8 s (the feared heavy `parse_table` load is
  actually fast; the guard stays as insurance). A sampled obs: native 350–900 nm
  1 nm grid (551 bands, ascending), all-finite `Rrs`, measured `Rrs_err`
  present; single-point `a_dg` truth = `(array([440.]), array([aCDOM440]))`;
  `prep_one` → `noise_model='insitu'` (genuine, from the measured std; no
  perturbation), `varRrs>0`; `metrics._caveat('GLORIA','a_dg')=='CDOM_vs_adg'`
  and `''` for `a_ph`; the a_dg truth aligns onto the fit grid as exactly one
  finite point at 440 nm.
- **Row alignment resolved by data (Q&A).** All three GLORIA tables
  (`meta_and_lab`, `Rrs`, `Rrs_std`) ship 7,572 rows in the **same `GLORIA_ID`
  order**, so the adapter's positional alignment of `df_meta` against the parsed
  spectra columns is correct (each table also carries `GLORIA_ID`, so it can be
  hardened to a join later if a future release reorders — not needed now).
  Scalar-truth coverage: aCDOM440 4393, Chla 5132, TSS 4623, Secchi 3948 finite
  of 7,572.
- **Tests.** Tier-2 GLORIA tests (`test_datasets`/`test_prep`) now **run** with
  data: `-k "gloria or GLORIA or caveat"` → **6 passed, 0 skipped** (was 4
  passed / 2 skipped when data-guarded off). CI-equivalent (`env -u OS_COLOR`)
  full suite → **179 passed, 22 skipped** (GLORIA Tier-2 correctly skip with no
  data). No adapter code change needed — implementation from 2026-07-07 is
  confirmed correct against real data; only the test guard was updated.

### 2026-07-14 (Stage 6, Task 3: grab the GLORIA dataset)

### 2026-07-14 (Stage 6, Task 3: grab the GLORIA dataset)

Downloaded the GLORIA-2022 dataset (Lehmann et al. 2023,
doi:10.1594/PANGAEA.948492) into `$OS_COLOR/GLORIA` per JXP's instruction.

- **Source.** The DOI landing page's `link` header exposes the archive item
  `https://download.pangaea.de/dataset/948492/files/GLORIA-2022.zip`
  (`application/zip`, 58,956,647 B / ~59 MB). Downloaded with `curl`;
  `unzip -t` verified integrity (zip OK).
- **Placed.** Extracted **flat** (`unzip -j`) into
  `/home/xavier/Oceanography/data/Color/GLORIA/` — 14 files, ~250 MB
  uncompressed, incl. the four the ocpy loader uses (`GLORIA_Rrs.csv`,
  `GLORIA_Rrs_std.csv`, `GLORIA_qc_flags.csv`, `GLORIA_meta_and_lab.csv`) plus
  the raw radiometry (`Es/Lsky/Lt/Lu/Lw`), `GLORIA_Rrs_mean.csv`,
  `qc_ancillary`, `waterqual_uncert`, and the `variables_and_methods.xlsx` /
  `method_references.ris` docs. Kept `GLORIA-2022.zip` alongside for provenance
  (delete if you don't want the extra 59 MB).
- **Verified.** `GLORIA_Rrs.csv` header = `GLORIA_ID,Rrs_350,Rrs_351,…` (native
  1 nm grid from 350 nm, keyed by `GLORIA_ID`); `GLORIA_meta_and_lab.csv`
  carries `GLORIA_ID`, `aCDOM440`, `Chla`, `TSS`, `Secchi_depth` — confirming the
  adapter's inferred `_GLORIA_*` maps exactly (see Q&A).
- **⚠ Wiring gap (flagged in Q&A, deferred to Task 4).** `load_gloria()` reads
  ocpy's *packaged* `<ocpy>/data/Rrs/GLORIA/`, not `$OS_COLOR/GLORIA`, so the
  data is grabbed but not yet reachable by the loader/`needs_gloria` guard.
  Posed the symlink-vs-copy-vs-upstream choice for JXP; no code changed this
  task (data grab only).

### 2026-07-14 (Stage 6, Task 3: GLORIA adapter — execute under the hang guard)

### 2026-07-14 (Stage 6, Task 3: GLORIA adapter — execute under the hang guard)

Task 3 is the task the hang struck on ("the task below" in Task 2). The
`GLORIAAdapter` itself was written on 2026-07-07 (log below); this pass **runs
it to completion** now that the Task-2 hang guard is in place — the step the
hang had blocked — and confirms it no longer wedges.

- **No hang, full coverage.** GLORIA-focused run (`-k "gloria or caveat or
  a_cdom440 or a_dg"`, under a 60 s per-test ceiling) → 4 passed, 2 skipped in
  ~1.6 s; full CI-equivalent suite (`env -u OS_COLOR`) → **179 passed, 22
  skipped in ~15 s**, no wedge. If GLORIA data were local the heavy full-CSV
  `_load` (two `parse_table` ~300 MB allocations) could be slow, but the guard
  now fails it fast with a traceback instead of hanging — so the original
  failure mode can't recur silently.
- **What's verified data-free (Tier-1):** registry seeding + `Adapter` protocol
  (`test_datasets.py`), the `_GLORIA_*` column maps, and the end-to-end
  single-point-`a_dg` → `a_cdom440_truth` → **`CDOM_vs_adg` caveat** path
  (`test_prep.py::test_prep_gloria_single_point_adg_and_caveat` asserts
  `metrics._caveat('GLORIA','a_dg')=='CDOM_vs_adg'` and `''` for `a_ph`;
  genuine `insitu` noise from the measured Rrs std).
- **What's skip-guarded (Tier-2, `@needs_gloria`):** adapter `load_obs`
  (hyperspectral grid + measured std + single-point a_dg) and
  `prep_dataset('GLORIA', ids[:5])` — GLORIA CSVs are unbundled and not on disk
  here, so these skip (as designed).
- **Still open — GLORIA Q&A awaits JXP.** The "Task 2 (GLORIA adapter)" Q&A
  block (column names `aCDOM440`/`Secchi_depth`, positional row alignment, the
  single-point-`a_dg` approach, `Chla→Chl`/`TSS→tss`/`Secchi_depth→Secchi`,
  deferring the 5%-fallback report surfacing) is unanswered; those are inferred
  from ocpy notebooks and can only be confirmed against real GLORIA data. Not
  self-answering per the Conventions — they don't block the adapter compiling or
  the suite passing, but a wrong column name would surface the first time GLORIA
  data is mounted.

### 2026-07-13 (Stage 6, Task 2: hang guard)

Investigated the reported hang and added a durable guard so no test can wedge
the run (or me) indefinitely.

- **Repro attempts.** The suite does **not** currently hang: CI-equivalent
  (`env -u OS_COLOR`) → 179 passed / 22 skipped in ~14 s; data-mounted
  (`$OS_COLOR` set) completes in ~26 s (with the pre-existing `bing` import
  failures noted below, no hang). Ran both under `faulthandler_timeout` to catch
  any stuck test — none. The real exposure is structural: several Tier-2 tests
  drive `ProcessPoolExecutor` batch fits, blocking data loads, and MCMC, and
  there was **no per-test time limit**, so one wedged test hangs the whole run.
- **Fix — `conftest._guard_against_hangs`** (autouse). A dependency-free
  per-test wall-clock ceiling via Unix `SIGALRM`/`setitimer` (main thread only;
  no-ops elsewhere). On expiry it dumps all thread tracebacks (`faulthandler`)
  then raises `TimeoutError`, failing just that test so the rest of the suite
  continues. Deferred to `pytest-timeout` when installed. Ceiling is 120 s by
  default (`$IOPTICS_TEST_TIMEOUT`), overridable per-test with
  `@pytest.mark.timeout(n)` (`0` disables); `timeout` marker registered via
  `pytest_configure`.
- **Verified the guard fires.** A throwaway `test_hangguard_tmp.py` (removed):
  `while True: pass` and `time.sleep(10_000)` both **failed** with `TimeoutError`
  (+ traceback) under a 3 s ceiling in ~6 s total — not killed by an outer
  watchdog — and `@pytest.mark.timeout(0)` correctly opted out. The full
  CI-equivalent suite still passes with the guard active (179 passed / 22
  skipped), confirming zero interference with real tests.
- **Docs.** Added a "Hang guard" subsection to design-doc §Testing & CI; module
  docstring in `conftest.py` documents the mechanism and tunables.
- **Flagged (Q&A):** default ceiling value + whether to make `pytest-timeout` a
  hard dependency; and the unrelated local-`bing` `correct_atmosphere`
  `ModuleNotFoundError` surfaced by the data-mounted run.

### 2026-07-07 (Stage 6, Task 1 follow-ups + Task 2: GLORIA adapter)

Applied JXP's Task-1 answers, then added the GLORIA adapter.

**Task-1 follow-ups (from JXP's answers).**
- `Chl` key confirmed — no change (already mapped ocpy `chla → Chl`).
- **5% in-situ fallback kept and documented everywhere JXP asked:** code
  (`prep._INSITU_PCT_FALLBACK` constant + comment, `prep` module docstring,
  `prep_one` docstring, `PANGAEAAdapter` docstring), documentation
  (`docs/source/datasets.rst` PANGAEA note + table; design-doc §Noise made the
  "pct fallback otherwise" explicit as 5% with the honest `noise_model='pct:0.05'`
  tag). Report-surfacing (provenance records the *configured* model, not the
  effective per-record tag) is deferred to Task-5 `build_v2` — flagged in Q&A.
- **Permissive floor → `min_rrs=5`** (`PANGAEAAdapter.obs_ids` default; still
  overridable to 1 for the fully-permissive set). Docstrings updated.

**Task 2 — `datasets.GLORIAAdapter`** (registered `'GLORIA'`). Loads via
`ocpy.insitu.gloria.load_gloria`; parses mean `Rrs` (`parse_table(·,'Rrs')`) and
its per-band std (`parse_table(·,'Rrs_std')`) onto the native 350–900 nm grid.
- **Genuine `insitu` noise:** GLORIA *does* ship a per-band Rrs std, so
  `Rrs_err = Rrs_std` → `varRrs = Rrs_std**2`, `add_noise=False` (no fallback).
- **Scalar-only truth**, mapped `aCDOM440 → a_dg` (single point at 440 nm),
  `Chla → Chl`, `TSS → tss`, `Secchi_depth → Secchi`. The single-point `a_dg`
  representation makes CDOM-at-440 flow through the existing machinery: `io`
  derives `a_cdom440_truth` from it, and — because the dataset is named `GLORIA`
  — `metrics._caveat` auto-stamps `CDOM_vs_adg` on its `a_dg` rows (no per-adapter
  flag, per design). PANGAEA `a_dg` stays genuine (no caveat).
- **`needs_gloria` guard** added to `conftest` (GLORIA CSVs are unbundled;
  probes ocpy's `data/Rrs/GLORIA/GLORIA_Rrs.csv`).
- **Tests.** Tier-1 (data-free): registry/protocol/`_GLORIA_*` maps; and a full
  end-to-end representation test — synthetic `GLORIA`-named adapter → `prep_one`
  → single-point `a_dg` finite only at 440, `io._scalar_value` gives
  `a_cdom440_truth`, `metrics._caveat` gives `CDOM_vs_adg` (and `''` for `a_ph`),
  `noise_model='insitu'`. Tier-2 `@needs_gloria`: adapter `load_obs` (hyperspectral
  grid, measured std, single-point a_dg) + `prep_dataset('GLORIA', ids[:5])` smoke.
- **Verification.** GLORIA data isn't local, so I validated the adapter against
  the **real** ocpy `gloria.parse_table`/`load_gloria` (monkeypatched loader,
  synthetic frames): on a GLORIA-like 1 nm grid → `a_dg(440)=aCDOM440`,
  `a_cdom440_truth` matches, caveat stamped, genuine `insitu`; NaN-CDOM rows
  correctly omit `a_dg`; Chl/tss/Secchi NaN-dropped. Found and documented that the
  single-point `a_dg` needs 440 nm on the grid (native 1 nm always has it; keep it
  in any trim). CI-equivalent suite (`env -u OS_COLOR`) → **179 passed, 21
  skipped** (was 175/19; +4 Tier-1, +2 Tier-2 skips). Docstrings + `datasets.rst`
  kept RST-clean (no glued backticks, no nested inline markup, no private xrefs);
  Sphinx isn't installed in this light env so no `-W` build (docs not in light CI).

### 2026-07-07 (Stage 6, Task 1: PANGAEA adapter)

Added the PANGAEA V3 (Valente et al. 2022) in-situ adapter to `datasets`, plus
the per-family-truth-grid seam in `prep` it needs, and an in-situ noise fallback.

- **`datasets.PANGAEAAdapter`** (registered as `'PANGAEA'`). Loads the tidy
  `rrs`/`iop`/`chla` tables via `ocpy.insitu.pangaea.load` (cached per table).
  `obs_ids(min_rrs=1)` is **permissive** (design Q12): every global `ID` with
  ≥`min_rrs` finite `Rrs` bands, via `pangaea.n_spectral`. `load_obs` returns
  native-grid `Rrs` + spectral truth from `pangaea.spectrum` — `aph→a_ph`,
  `acdom→a_dg` (combined CDOM+detrital), `bbp→bb_p` — as **`(src_wave, values)`
  pairs** on each family's own grid, only for components present; scalars `Chl`
  (HPLC→fluorometric merge) and `tss`; lat/lon/depth/date into `meta`.
  `Rrs_err=None` (V3 has no per-band Rrs error).
- **`prep._build_truth` per-family seam** (the Stage-1-flagged extension). Truth
  values that are `(src_wave, values)` tuples align from their own grid onto
  `wave` (out-of-range → `NaN`, regrid flagged); plain arrays still align from
  `raw.wave`. L23 path unchanged (all `truth_interp` still `False`); PANGAEA
  components come back `truth_interp=True`. No change to `PreparedRecord`.
- **In-situ noise fallback.** PANGAEA's default `noise='insitu'` has no measured
  `Rrs_err`, so `prep_one` falls back to `pct:0.05` (design §Noise "pct fallback
  otherwise"), recording the honest tag `noise_model='pct:0.05'`
  (`prep._INSITU_PCT_FALLBACK`). `add_noise` stays `False` for in-situ (real Rrs
  not perturbed).
- **Truth-key decision (flagged in Q&A):** mapped ocpy `chla → Chl` (not literal
  `chla`) because `io`/`metrics` score chlorophyll under `Chl`/`Chl_truth`
  (`io.py:186`); otherwise PANGAEA Chl would be unscored and non-comparable to
  L23. `a_dg(440)` auto-yields `a_cdom440_truth` via `io._scalar_value`, and the
  dataset is **not** `GLORIA`, so no caveat is stamped (correct — PANGAEA `a_dg`
  from `acdom` is genuine). Awaiting JXP's confirm on `Chl` and the 5% fraction.
- **Tests.** Tier-1 (data-free, always run): `_build_truth` per-family alignment
  (Spectrum on `wave`, `truth_interp=True`, NaN edges, `orig_wave` retained) and
  the insitu→pct fallback, both via a new PANGAEA-shaped synthetic adapter;
  registry/protocol/kind-map checks. Tier-2 `@needs_pangaea` (skip where V3 isn't
  mounted): adapter `load_obs` grid/truth-pair shape + permissive-floor
  monotonicity; `prep_dataset('PANGAEA', ids[:5])` smoke (native grid, `varRrs>0`,
  `pct:0.05`, per-family regrid).
- **Verification.** Since PANGAEA V3 isn't mounted here, I validated the adapter
  against the **real** ocpy parser (`pangaea._build_columns`/`spectrum`/
  `n_spectral`) on a synthetic PANGAEA-format frame: per-family pairs on distinct
  grids, HPLC→fluor Chl merge, `tss` NaN-drop, permissive `min_rrs`, and full
  `prep_one` (interp with NaN edges, `orig_wave`, `init` computed) all correct;
  a 1-band obs does not crash. CI-equivalent suite (`env -u OS_COLOR`) →
  **175 passed, 19 skipped** (was 170/16; +5 Tier-1, +3 Tier-2 skips, +1 fixed).
  Docstrings kept RST-clean (fixed a glued `` ``ID``s ``; no private xrefs);
  Sphinx isn't installed in this light env so no `-W` build was run (docs are not
  in light CI — `@needs_sphinx`).

### 2026-06-27 (Stage 6, Task 0: refresh prompt file for earlier-stage changes)

Re-read `coding_prompts_stage06.md` and verified every carryover/API claim against
the current post-Stage-5 code before editing.

- **Environment drift (the real change).** The `ocean14` interpreter is no longer
  at `/home/xavier/miniforge3/envs/ocean14/bin/python` (the Stage-1 path) — the env
  now lives under **`miniconda3`**. JXP freshly created it; it was missing
  `pyarrow` (parquet backend for the metrics tables) and `ocpy`/`bing`. Installed
  `pyarrow` and editable `ocpy`/`bing` from the local sibling checkouts
  (`/mnt/tank/Oceanography/python/{ocpy,bing}`), matching the working `os_313` env.
  **Added `pyarrow` to `requirements.txt`**; updated the Conventions interpreter
  path + a note on the env move and deps.
- **RawObs truth representation corrected.** The carryover said `RawObs.truth`
  spectral values are "ocpy `Spectrum`s on the native grid." They are actually
  **plain numpy arrays** on the native grid; `prep` (not the adapter) wraps them as
  ocpy `Spectrum`s. Fixed the bullet so new PANGAEA/GLORIA adapters follow the L23
  contract (return arrays, let prep wrap).
- **`leaderboard.update` signature.** Real signature is
  `update(runs_root=None, *, root=None, out=None, sweep_ids=None)` — added the
  `root` kwarg the doc omitted.
- **Verified accurate (no change):** `datasets` registry/`Adapter` Protocol/
  `RawObs`/`L23Adapter` (X=2 rejected at `datasets.py:129`); `AlgorithmSpec`
  `rt` toggles `variable_Gordon`/`include_Raman`/`include_Chl_fl` + `from_standard`
  + `fit_method='chisq'`; `run.fit_chisq`/`evaluate.from_chisq`/`from_chains` and
  the `rt_dict` seam; `io.read_results`/`write_results` with `Rrs_obs` + chain
  `pnames`; `metrics.compute(sweep_id, *, root=None, …)` → `metrics_{spectral,
  scalar,pairwise}.parquet` and `metrics._caveat` stamping `CDOM_vs_adg`;
  `report.standard.build(sweep_id, kind='cross_algorithm', …)`,
  `leaderboard.{update,render,ranked}`, `rst.write_leaderboard_landing`,
  `bokeh.interactive_{scatter,leaderboard}`; `build_v1.py main(flg)` sequential
  stages 1/2/3; conftest guards `needs_l23`/`needs_pangaea`/`needs_pace`/
  `needs_sphinx`. All upstream APIs the file cites
  (`ocpy.insitu.{pangaea,gloria}`, `ocpy.spectra`, `bing.parameters.standard.gsm`,
  `bing.rt.{raman,chl_fl}`) import in `ocean14`.
- **Confirmed still-open constraint:** `report.leaderboard` does **not** fold
  `caveat` — the exit-criterion decision flagged in Known-constraints is genuinely
  still pending (posed in Q&A).
- **Verification (`ocean14`, CI-equivalent `env -u OS_COLOR`).** Full suite
  **170 passed, 16 skipped** — env is sound. No IOPtics source code changed this
  task (prompt-file + `requirements.txt` only).

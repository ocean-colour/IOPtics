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
  (`/home/xavier/miniforge3/envs/ocean14/bin/python -m pytest -q`); `conda
  activate` fails non-interactively. **Run the suite without `$OS_COLOR`**
  (CI-equivalent) before declaring a task done.
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
  RawObs`); `RawObs` carries `Rrs`, per-component `truth` (ocpy `Spectrum`s on the
  native grid) + scalar truth, optional `Rrs_err`, and `meta`. `L23Adapter` (X=1
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
  runs_root=None, out=None, sweep_ids=None)` **accumulates across sweeps**
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

2. **GLORIA adapter.** Add to `datasets`: `load_obs` via `gloria.load_gloria` →
   hyperspectral `Rrs` + scalar truth (`a_cdom440`, `Chla`, `TSS`, `Secchi`),
   mapped so `a_dg(440)` truth = `a_cdom440`; name the dataset `GLORIA` so
   `metrics` auto-stamps `caveat='CDOM_vs_adg'` (no per-adapter flag needed — but
   see Known-constraints re: surfacing it in the *leaderboard*). Skip-guarded
   (data may not be local). Q&A. Log.

3. **Register `gsm`.** `registry.register(AlgorithmSpec.from_standard('gsm',
   label='GSM'))`; confirm it round-trips and runs through `run_algorithm`
   unchanged. Tier-1 + a tiny χ² fit. Q&A. Log.

4. **L23 X=4 (inelastic).** Load `X=4` via the L23 adapter and wire the
   `include_Raman`/`include_Chl_fl` `AlgorithmSpec.rt` toggles → `rt_dict` so
   `run`/`evaluate` apply Raman + Chl-fluorescence. Tier-2 `@needs_l23` smoke
   (X=4 fit completes; `Rrs_model` differs from the elastic run). Q&A. Log.

5. **Tests + multi-everything sweep.** A `runs/prototypes/<name>/build_v2.py`
   (sequential stages, mirroring `build_v1.py`) over {L23(X=1), PANGAEA} ×
   {expb_pow, giop, gsm} (χ²) → tables + `metrics.compute` + `report.standard.build`
   + `leaderboard.update` accumulation; assert per-dataset/component coverage
   accounting and that the GLORIA caveat surfaces (Tier-2 with data; Tier-1 on a
   synthetic multi-dataset results table where possible). Q&A. Log.

### Q&A

## Logs

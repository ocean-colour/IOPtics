# Code IOPtics — Stage 6: Broaden (datasets & algorithms)

## Goal

Turn the cranks the architecture was built for: more datasets, more algorithms,
inelastic RT. **Exit criterion:** sweeps run on all three datasets and ≥3
algorithms; the leaderboard accumulates across them; the GLORIA scalar comparison
surfaces the CDOM-vs-`a_dg` caveat.

Implements **Data preparation** (PANGAEA/GLORIA adapters), **Algorithm registry**
(`gsm`), **Retrieval & run** (L23 X=4 RT toggles), and the **Staged plan / Stage 6**
of `docs/design/IOPtics_implementation.md`. One prompt per module/addition.

## Conventions

- `ocean14`; docstrings; JXP runs git; after each module run `pytest -q`, Q&A, Log.
- New adapters live in `datasets` (the only ocpy-importing module besides `noise`).
- Adding an algorithm must be **one `register(...)` call** — no core changes.

## Context

- `docs/design/IOPtics_implementation.md` — §Data preparation (adapters table:
  PANGAEA `acdom`→`a_dg`, `bbp`→`bb_p`, scalars `chla`/`tss`; GLORIA scalar
  `a_cdom440`/`Chla`/`TSS`/`Secchi` + caveat), §Algorithm registry (`gsm` one-liner),
  §Retrieval & run / §Metrics (RT toggles, `caveat='CDOM_vs_adg'`).
- ocpy: `insitu.pangaea.{load,spectrum,file_catalog}`, `insitu.gloria.load_gloria`.
- bing: `parameters.standard.gsm`; `rt.{raman,chl_fl}` + the `rt_dict` toggles.

## Prompts

### Coding

1. PANGAEA adapter in `datasets`.
2. GLORIA adapter in `datasets` (+ caveat flag).
3. Register `gsm`.
4. Enable L23 X=4 (Raman + Chl-fluorescence).
5. Tests + a multi-dataset / multi-algorithm sweep.

## Modules

### Tasks

1. **PANGAEA adapter.** Add to `datasets`: enumerate IDs (permissive — any usable
   `Rrs`), `load_obs` via `pangaea.load`/`spectrum` returning `Rrs` + truth
   (`a_ph`, `a_dg`←`acdom`, `bb_p`←`bbp`) on per-family native λ + scalars
   (`chla`, `tss`). `noise='insitu'`. Tier-2 `@needs_pangaea`. Q&A. Log.

2. **GLORIA adapter.** Add to `datasets`: `load_obs` via `gloria.load_gloria` →
   hyperspectral `Rrs` + scalar truth (`a_cdom440`, `Chla`, `TSS`, `Secchi`);
   stamp the `caveat='CDOM_vs_adg'` so metrics/reports flag the CDOM-vs-`a_dg`
   mismatch. (Skip-guarded — data may not be local yet.) Q&A. Log.

3. **Register `gsm`.** `register(AlgorithmSpec.from_standard('gsm', label='GSM'))`;
   confirm it round-trips and runs through `run_algorithm` unchanged. Tier-1 +
   a tiny fit. Q&A. Log.

4. **L23 X=4 (inelastic).** Allow the L23 adapter to load `X=4`; wire the
   `include_Raman`/`include_Chl_fl` RT toggles through `AlgorithmSpec.rt` →
   `rt_dict` so `run` applies Raman + Chl-fluorescence. Tier-2 `@needs_l23` smoke
   (X=4 fit completes). Q&A. Log.

5. **Tests + multi-everything sweep.** A `runs/.../build_v2.py` over
   {L23(X=1), PANGAEA} × {expb_pow, giop, gsm} (χ²) → tables + metrics +
   leaderboard accumulation; assert coverage accounting per dataset/component and
   the GLORIA caveat surfaces where applicable. Q&A. Log.

### Q&A

## Logs

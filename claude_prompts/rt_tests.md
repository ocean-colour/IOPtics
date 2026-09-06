# RT Testing

## Goal

We wish to examine the differences when running BING with different RT models.  We will use the following RT models:
- Elastic only
- Elastic + Raman
- Elastic + Chl-FL + Raman
- Elastic + Chl-FL + Raman + CDOM

BING will take advantage of the new RT models in the RoB repository

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
- RoB: `Oceanography/python/retrieve-or-bust/`
- PAB: `Oceanography/python/PAB/`
- **Build-script template:** `ioptics/runs/prototypes/expb_giop/build_v1.py`
  (`main(flg)`; sequential stages `1`=run, `2`=metrics, `3`=report). Stage-6's
  `build_v2.py` mirrors it.


## Prompts 

### Planning

1. We have developed a new set of RT code in the RoB repository.  We wish to test the differences when running BING with different RT models.  We will create a plan to do so.  Start by exploring the context and then ask me a series of questions in Q&A below.  Use Fable.  Log your work.

2. Read my answers to the Q&A below and then ask me another set of questions.  Note that I have asked to add PACE analysis which will not have ground truth.  There, I am seeking to see how much the difference in RT models makes.  Use Fable.  Log your work.

3. Read my answers to the Q&A below and then ask me another set of questions.  Use Fable.  Log your work.

4. Read my answers to the Q&A below and see if you need to ask me any more questions.  Use Fable.  Log your work.

5. Read my answers to the Q&A below and then generate a series of prompts for the execution phase in Execution below.
Use Fable.  Log your work.

### Execution

**Pinned decisions** (Q&A rounds 1–4; details in Logs):
- **Algorithms (5):** `expb_pow_ztt_el`, `expb_pow_hyb_el`, `expb_pow_hyb_ram`,
  `expb_pow_hyb_ramfl`, `expb_pow_hyb_ramflcdom` — `expb_pow` only, registered
  via opt-in `register_rt_variants()`, **excluded** from the shared leaderboard.
- **RT config:** `fit_Bp=True` (linear [0.004, 0.05]); `phi_C=0.02` fixed;
  `double_gaussian=True`; CDOM-fl `scale=1.0` with **`a_cdom = 0.8 × a_dg`**
  (fixed CDOM fraction — document prominently); Ed from RoB's packaged
  `ed_l23.npz` table everywhere; learned corrections stay off.
- **Geometry:** θ_s = 0 for L23; computed per-record (NOAA formula) for
  PANGAEA/PACE; θ_v = 0, Δφ = 0 everywhere (stated limitation in report).
- **Data:** L23 X=4 (3,320, via new `dataset_opts`); PANGAEA = the 97 NOMAD
  ids with all three truth families; PACE = 100 seeded-random of the 274
  run1k chain NPZs, 400–700 nm, `varRrs = Rrs_unc²` (2% floor), keep
  negative Rrs.
- **Sweeps:** RT-A = L23 + PANGAEA-97 @ 400–750; RT-B = PACE-100 @ 400–700.
  χ² + full MCMC on everything. Headline ΔBIC: `expb_pow_hyb_el` vs
  `expb_pow_hyb_ramflcdom`. Variant-5 L23 rows get a truth-lacks-CDOM-fl
  caveat tag.
- **Branches:** BING `rob_cdom`, RoB `cdom-rt`, IOPtics `rt-tests`. JXP runs git.

6. **BING: CDOM-fluorescence path** (repo `bing`, branch `rob_cdom`). Add
   `include_CDOM_fl` (default False) and `cdom_fraction` (default 0.8) to
   `rt_dict_from_p` and `validate_rt_dict` (CDOM-fl requires a robust backend
   and an a-model with a separable a_dg component; reject on `gordon` and on
   `robust_baseline`). In `evaluate`: feed `a_cdom = cdom_fraction × a_dg`
   into `IOPs`, pass `Inelastic(cdom_fl=CDOMFl(scale=1.0))` inside the jit
   factory with `scale`/`cdom_fraction` in the cache key, and thread through
   `calc_Rrs_from_iops_robust`, `reconstruct_*`, and the domain check. Unit
   tests mirroring `test_evaluate_robust.py` groups (off-by-default
   byte-identity, on-adds-signal, gordon rejects, cache separation, MCMC
   round-trip). Run BING's full `pytest -q`. Q&A, Log.

7. **RoB: solar-zenith utility** (repo `retrieve-or-bust`, branch `cdom-rt`).
   New module (e.g. `robust/solar.py`): dependency-free NOAA solar-position
   `solar_zenith(time, lat, lon)` (UTC datetime/ISO string; vectorized;
   degrees; ±0.1° adequate). Docstring cites the NOAA algorithm. Tests
   against a few published ephemeris values incl. edge cases (polar night,
   date line). Run RoB's `pytest -q`. Q&A, Log.

8. **IOPtics: core plumbing** (this repo). (a) `dataset_opts` key in
   `SweepConfig` threaded `run_sweep → prep_dataset` and recorded in
   provenance; (b) extend `RTOptions` with `rt_backend`, `fit_Bp`,
   `Bp_value`, `include_CDOM_fl`, `cdom_fraction`, mapped through
   `to_bing_p`; (c) per-record geometry: adapters/prep stash time/lat/lon,
   `run._prepare` computes θ_s (0 for L23; `robust.solar` otherwise), builds
   `ObsGeometry`, and passes the 5-tuple into both fit paths, with `B_p`
   handled in results/chains; (d) `PROVENANCE_SCHEMA` 3→4 +
   `_SCHEMA_FIELD_DEFAULTS`; (e) `leaderboard: false` sweep flag honored by
   `leaderboard.update()`. Tests for each; run `pytest -q` without
   `$OS_COLOR` (CI-equivalent) and with. Q&A, Log.

9. **IOPtics: PACE dataset** (this repo + one extraction script). Extraction
   script (may import PAB code paths and `run1k/pab.db`): seeded
   (`default_rng(20260906)`) sample of 100 of the 274 run1k chain NPZs →
   single parquet/NPZ under `$OS_COLOR/IOPtics/pace_pab_100/` with wave,
   Rrs, varRrs, lat/lon, granule mid-time, computed θ_s, and matchup ids.
   Then a `PACE` adapter in `ioptics/datasets.py` reading that file (no
   `pab` import in the package), `Rrs_err` from stored varRrs, truth `{}`,
   a `needs_pace_pab` test tier. Tests; `pytest -q` both modes. Q&A, Log.

10. **IOPtics: variants, configs, build script, smoke run.**
    `register_rt_variants()` in `ioptics/algorithms/registry.py` (opt-in,
    five specs per the pinned matrix). Helper to derive + freeze the
    PANGAEA-97 id list (NOMAD ∩ aph∩acdom∩bbp truth) into a committed CSV.
    New `ioptics/runs/prototypes/rt_tests/`: `build_v1.py` (template style;
    stages 1=RT-A run, 2=RT-A metrics, 3=RT-B run, 4=RT-B metrics,
    5=report), `run_rta.yaml` (L23 `dataset_opts {X:4}` + PANGAEA-97,
    400–750, full MCMC, `leaderboard: false`), `run_rtb.yaml` (PACE,
    400–700), plus a `test20`-style micro config. Metrics: `dbic_pair`
    override + variant-5-on-L23 caveat tag. **Smoke run** the micro config
    end-to-end (χ²+MCMC on ~8 spectra × 5 variants) and sanity-check
    outputs before any long run. `pytest -q`. Q&A, Log.

11. **Run sweep RT-A** (L23 X=4 + PANGAEA-97; χ² all + full MCMC ×5
    variants; ~a day-plus wall time — use checkpointing, `--n-cores`, and
    report progress). Then stage-2 metrics. Verify chain health on a sample
    (autocorrelation, acceptance, B_p posteriors vs prior edges). Log
    timings and any failures/domain warnings. Q&A, Log.

12. **Run sweep RT-B** (PACE-100; χ² + full MCMC ×5 variants), then
    metrics. Compare `expb_pow_hyb_el` posteriors against PAB's stored
    run1k ExpBPow (gordon-elastic) posteriors for the same pixels as a
    consistency check. Q&A, Log.

13. **Report round.** Stage-5 report build: cross-variant pages for both
    sweeps + the PACE headline figure (distribution of fractional change in
    retrieved a_ph/a_dg/bb_p at 443 nm, elastic → full inelastic, plus the
    ΔBIC histogram) and the L23 truth-comparison views. Report text must
    state the limitations: θ_v = 0 everywhere, `a_cdom = 0.8 × a_dg`,
    packaged-sky Ed, corrections off, L23 X=4 truth lacks CDOM-fl and used
    a single-Gaussian emission line while fits used double. Landing/
    leaderboard untouched by these sweeps. `sphinx-build -W` green;
    full `pytest -q` without `$OS_COLOR`. Final summary in Logs. Q&A, Log.

## Q&A

Questions for JXP after exploring BING's `rt` package, the RoB `robust.rt` code,
and the IOPtics sweep machinery (2026-09-05). Please answer before the next task.

### A. What "BING takes advantage of RoB" means

1. **Integration mode.** RoB's forward model (`robust.rt.hybrid.forward`) is
   JAX-based with a different interface (`IOPs`/`Geometry`/`Inelastic` pytrees,
   no `rt_dict`), while BING's own NumPy `bing.rt` already implements the same
   Raman + Chl-fl physics and is cross-checked against RoB at rtol ≤ 1e-6.
   Which do you intend?
   - (a) BING calls `robust.rt.forward` inside `log_prob`/`chisq_fit` (needs an
     `rt_dict` → `Inelastic` translator, JAX inside emcee, and `PhaseParams.B_p`
     + `Geometry` inputs BING's models don't carry);
   - (b) BING keeps its own NumPy RT (numerically identical for the analytic
     terms) and RoB is used as the reference/validation and the source of any
     *new* physics (CDOM-fl); or
   - (c) something in between (e.g. RoB only for the learned correction heads)?

>A. I have put us on the right branch: `develop`.  That has code that links BING to RoB.

2. **Elastic backbone.** RoB offers three elastic models (Gordon baseline, ZTT,
   hybrid ZTT+emulator). BING uses variable-Gordon G(λ). Is the elastic model
   held fixed at variable Gordon across all five RT variants (so only the
   inelastic terms differ), or is the elastic backbone also part of the test?

>A. Only use the elastic model from RoB.

3. **Learned corrections.** RoB's corrected heads reach 0.34% rRMS vs 2%
   analytic — but they were trained on L23. If we fit L23 with them, the
   forward model has seen the truth (circularity). Analytic-only for this
   experiment, corrected heads, or both as separate variants?

>A. Agreed, but that is ok.  The other datasets will provide further validation.  In addition, we wish to fit 100 random PACE spectra from the PAB project.  I have added that Repo to the Context.  Examine it.

### B. The CDOM-fluorescence variant

4. RoB's CDOM fluorescence is **interface-only** as of `834466f`: the `CDOMFl`
   pytree and `IOPs.a_cdom` exist, but there is no `K_cdom` kernel, no
   composition wiring (a CDOM-only config silently returns elastic Rrs), no
   trained δ_C head, and no HydroLight truth to validate against (deferred to
   RoB M6). BING has no CDOM-fl code at all. For variant 5
   (Elastic + Chl-FL + Raman + CDOM), do you want to:
   - (a) implement the Hawes (1992) kernel per `design/rt_cdom_fluorescence_model.md`
     as part of this work (and if so — in RoB, in BING, or both?),
   - (b) defer variant 5 until RoB M5/M6 lands and run the four-variant
     comparison now, or
   - (c) something else?

>A. Check again now that I am on `develop`.

5. If CDOM-fl is implemented in BING, it means a new `RTOptions` field, a new
   `p_ntuple` key, an eighth `rt_dict` key, forward-model support, and an
   IOPtics `PROVENANCE_SCHEMA` bump 3→4. Confirm you're OK with those touches
   (the provenance bump is the only IOPtics-core change of the set).

>A. Same.  No coding should be required

### C. Experiment design

6. **Datasets.** L23 X=4 is the only dataset with inelastic Rrs + full IOP
   truth (the controlled experiment: same truth, five forward models).
   Should the sweep be L23 X=4 only, or also PANGAEA (real spectra + Chl, but
   no RT ground truth) and/or L23 X=1 (to quantify the penalty of fitting
   elastic-generated Rrs with inelastic models)?

>A. Let's include PANGAEA.  Is there no in-situ data from it for validation?
e.g. the files that Erickson+23 included in their analysis.

7. **`dataset_opts` plumbing.** `run_sweep` currently passes no load options
   to `prep_dataset`, so **L23 X=4 is unreachable from a sweep YAML** — the
   one gap the experiment can't work around. OK to add a
   `dataset_opts: {L23: {X: 4}}` key to `SweepConfig` and thread it through
   `run_sweep` (recorded in provenance), or would you rather the build script
   prep records directly?

>A. Yes, add that.

8. **Algorithms.** Which BING parameterizations run under the RT variants —
   `gsm` only, or the full standard trio (`expb_pow`, `giop`, `gsm`)? Note the
   fluorescence term is driven by the fitted a_ph amplitude, so all three
   support it without new parameters.

>A. Let's only use `expb_pow`.

9. **Variant naming.** Plan is to register each RT variant as a distinct
   registry name via an opt-in `register_rt_variants()` (following the
   `register_turbid()` pattern), e.g. `gsm_el`, `gsm_ram`, `gsm_fl`,
   `gsm_ramfl`, `gsm_ramflcdom` — distinct names keep results/metrics/
   leaderboard keys from colliding. Any preference on the naming scheme, and
   should these variants fold into the shared leaderboard or stay out of it?

>A. That's good, but prefix them for `expb_pow`

### D. Fit configuration

10. **Wavelength window.** Raman is unstable blueward of ~400 nm
    (`run.py` comment) → `wv_min=400`. But `wv_max`: 700 truncates the 730 nm
    secondary fluorescence line; 750 keeps it. Which window — and should all
    five variants use the *same* window so ΔBIC/χ² are comparable?

>A. Let's use the same window for all five variants.  And use 400-750 nm.

11. **Emission line shape.** The L23 X=4 HydroLight truth used a single 685 nm
    Gaussian (BING's regression test sets `double_gaussian=False`), but BING's
    default is `double_gaussian=True`. Single for the L23 sweep?

>A. Use double.

12. **φ_C.** Fixed at 0.02 (matching HydroLight) as today, or is fitting the
    quantum yield as a free parameter part of this experiment? (No free-φ_C
    machinery exists; adding it touches model `nparam`/priors.)

>A. Fix it

13. **Fit methods and scale.** Full χ² pass over all 3,320 L23 spectra plus
    the usual MCMC subset? What `mcmc_subset` size, given MCMC cost on this
    machine (~24 cores)?

>A. Do a full MCMC analysis too.  

14. **Metrics head-to-head.** `dbic_pair` defaults to `('expb_pow','giop')`.
    For an RT contest, which pair(s) matter most — e.g. elastic vs
    Raman+Chl-FL of the same algorithm? (Identical k across RT variants makes
    ΔBIC a pure likelihood contest, which seems like the right primary metric —
    but you decide the headline comparison.)

>A.  Make the headline elastic vs. full inelastic.

---

### Round 2 (2026-09-05) — after exploring BING@develop, PAB, and the PANGAEA/Erickson question

**First, the answer to your Q6 question (in-situ PANGAEA validation):** Yes.
The PANGAEA tree is the **Valente et al. (2022) V3** compilation. 1,593 of the
64,071 Rrs ids carry co-located spectral IOP truth (a_ph 1,293 / a_dg 1,140 /
bb_p 584; 263 with all three), already wired into IOPtics and previously fit.
Erickson+23 (Optics Express 31, 22790) analyzed **NOMAD** — and NOMAD is *inside*
Valente V3, supplying 83% (1,324) of the 1,593 truth ids, tagged per-record via
`subdataset`. Requiring all three truth families and NOMAD gives 97 records vs
Erickson's 86 stations (their exact station list isn't recoverable from disk,
but the substrate is the same). No Erickson-specific file exists in any repo.

### E. Environment & branches

15. **`robust` is not installed in ocean14** — and BING@develop imports it
    unconditionally, so `import bing.evaluate` currently *fails* in ocean14
    (the whole BING/IOPtics test suite would die at collection). Also, BING's
    `setup.py` pins `retrieve-or-bust @ cdom-rt`, but the local RoB checkout is
    on `inelastic-rt` (834466f), which predates `robust/rt/cdom_fl.py`;
    `origin/cdom-rt` (363951d) has the full CDOM-fl implementation + tests.
    Since you run git: shall I have you check out `cdom-rt` in the RoB repo,
    and then I `pip install -e` it (plus `flax`) into ocean14 and add both to
    IOPtics' requirements?

>A. I have just installed it into the ocean14 environment. Please confirm.

### F. Backend configuration

16. **Which RoB elastic?** "Only use the elastic model from RoB" — BING@develop
    offers `rt_backend='robust_ztt'` (pure Twardowski/Tonizzo analytic) and
    `'robust_hybrid'` (ZTT + L23-trained emulator residual; restricted to
    350–750 nm; learned inelastic corrections are hard-wired OFF in BING
    regardless). Which backend — and the same one for all five variants,
    I assume?

>A. Let's use both `robust_ztt` and `robust_hybrid`, but when I refer to "elastic" assume `robust_hybrid`.

17. **Geometry.** Robust backends require `theta_s` explicitly (never
    defaulted). Choices per dataset:
    - L23: the Hydrolight scenario zenith (θ_s = 0 for the standard load) —
      or do you want a nonzero-zenith L23 load?
    - PANGAEA: compute solar zenith from each record's date/time/lat/lon, or
      adopt a single fixed θ_s for all records?
    - PACE: per-pixel solar zenith from the granule, or fixed?
    And θ_v = 0, Δφ = 0 everywhere?

>A. Use 0 for L23 and compute it for the other two.  If you need to genrate code for this, put it in the RoB repo.

18. **B_p (particulate backscattering ratio).** The robust path needs it:
    fixed at the default 0.01, or fit it (`fit_Bp=True`, uniform [0.004,
    0.05], adds one parameter — same k across variants either way)?

>A. Fit it.

### G. The CDOM variant — coding is required after all

19. BING@develop has **no CDOM-fluorescence path**: no rt_dict key, `CDOMFl`
    is never passed, and the model's a_dg component is never fed into
    `IOPs.a_cdom`. The physics now exists on RoB `cdom-rt`
    (`robust/rt/cdom_fl.py`, 410 lines + ~680 test lines), so the gap is a
    small BING patch: (a) an `include_CDOM_fl` rt_dict key through
    `rt_dict_from_p`/`validate_rt_dict`, (b) feed the exponential a_dg
    component as `a_cdom` in the adapter, (c) pass
    `Inelastic(cdom_fl=CDOMFl(scale=…))` in the jitted closure with `scale`
    in the jit signature, (d) tests. Proceed with that BING patch, or drop
    variant 5 and run four variants?

>A. Good catch.  I have jumped on to the `cdom-rt` branch in the RoB repo.  And I have moved onto a `rob_cdom_fl` branch in the BING repo.  You can create code for BING as needed.

20. If we proceed: CDOM-fl amplitude `CDOMFl.scale` — fixed at 1.0 (the Hawes
    kernel as-is), or something else? (Fitting it would add a parameter, like
    φ_C it's currently a fixed scalar.)

>A. Fixed at 1.0.

### H. Datasets & sampling

21. **PANGAEA subset.** Given full MCMC × 5 variants, which population:
    (a) the 1,593 spectral-truth ids, (b) NOMAD-only (1,324), (c) the 97
    NOMAD ids with all three truth families (closest to Erickson+23), or
    (d) something larger? (An `subdataset`-based NOMAD stratum in metrics is
    cheap to add in any case.)

>A. (c) is good

22. **PACE sampling route.** Three ways to get 100 random PACE spectra:
    - (a) sample the **274 existing run1k chain NPZs** (real V3_2 spectra,
      per-pixel Rrs_unc, already windowed 400–700 nm; bonus: each carries an
      existing elastic ExpBPow posterior to compare against);
    - (b) seeded random good-mask pixels from the **1,104 local V3_1
      granules** (full native 346–719 nm grid + Rrs_unc, zero download);
    - (c) re-download the full-run V3_2 matchup granules (~0.5 GB each).
    Which do you want? (b) gives the cleanest "random PACE" sample; (a) ties
    into the PAB analysis.

>A. (a) is good

23. **PACE adapter mechanics.** Proposal: a one-time extraction script (using
    PAB's reader) writes the 100 spectra + meta to a single file under
    `$OS_COLOR/IOPtics/`, and a new lightweight `PACE` adapter in
    `ioptics/datasets.py` reads that file — no `pab` dependency in IOPtics
    (PAB isn't pip-installed anyway). `varRrs = Rrs_unc²` from the granule,
    with PAB's 2%-floor fallback for bad values. OK?

>A. That is ok.

24. **PACE window & QC.** PACE OCI L2 stops at 719 nm, has a 588–613 nm gap,
    and carries 30–44% fractional uncertainty redward of 613 nm (where the
    inelastic signal lives). Use 400–719 for PACE while L23/PANGAEA use
    400–750? Any extra screening beyond PAB's standard L2 flag mask (e.g.
    reject spectra with negative Rrs bands)?

>A. Yes, use 400-719 nm for PACE.  Do not reject Rrs with negative values.

### I. Scale & reporting

25. **Full-MCMC cost.** Robust backends are ~6–7× slower per log_prob call
    than Gordon (measured in BING's benchmark). Ballpark at default
    nsteps=10,000: L23 3,320 × 5 variants = 16,600 MCMC fits ≈ a day-plus of
    wall time on the 24 cores; PANGAEA and PACE add proportionally (plus
    per-worker JAX recompile overhead in process pools). Full MCMC on *all
    three* datasets as answered — or full MCMC for L23 + the PANGAEA subset,
    and χ²+MCMC for the 100 PACE? Happy either way, just confirming the
    budget before I size checkpointing.

>A. That is fine.  This workstation is all yours for the using.

26. **PACE deliverable.** With no truth, accuracy metrics are empty; what the
    machinery *can* produce: closure (χ²ν), ΔBIC elastic-vs-full-inelastic,
    and cross-variant deltas of retrieved a_ph/a_dg/bb_p (and Chl). Proposed
    headline figure: distribution over the 100 spectra of the fractional
    change in retrieved IOPs at 443 nm (elastic → full inelastic), alongside
    the ΔBIC histogram. Does that match your intent?

>A. Yes that is good.  

27. **Leaderboard.** Unanswered from round 1: should the five
    `expb_pow_*` RT variants fold into the shared cross-sweep leaderboard
    (adding five profile pages and diluting the headline board), or stay
    sweep-local like an investigation?

>A. No, do not include them in the shared leaderboard for now.

28. **IOPtics core touches — confirming scope.** "No coding should be
    required" holds for BING's four existing variants, but IOPtics itself
    needs: new `RTOptions` fields (`rt_backend`, `fit_Bp`, `Bp_value`, a
    geometry source, and `include_CDOM_fl` if variant 5 proceeds), geometry
    threading through `run._prepare`/fit tuples, the agreed `dataset_opts`
    key, a PACE adapter, and a `PROVENANCE_SCHEMA` 3→4 bump. Confirm that
    scope is acceptable.

>A. That is acceptable.

---

### Round 3 (2026-09-05) — after verifying the install, branches, and data joins

**Confirmations you asked for (Q15/Q19):** `robust` is installed editable in
ocean14 pointing at the local RoB checkout, now on `cdom-rt` (363951d);
`flax` 0.12.9 present; `robust.rt.cdom_fl` imports; `bing.evaluate` imports;
the 10-key `rt_dict` is live; a smoke subset of `test_evaluate_robust.py`
passes (3/3). One nit: the new BING branch is named `rob_cdom` (you said
`rob_cdom_fl`) — I'll use `rob_cdom` as checked out.

Also verified (no questions needed): the run1k chain NPZs carry only
`wave/Rrs/varRrs/chains/param_names/Chl`, but their filenames join to
`run1k/pab.db`, whose `matchup_pixels` (per-pixel lat/lon) and `granules`
(`time_start`) give everything needed to compute per-spectrum solar zenith;
PANGAEA V3's IOP table has per-record `Date/Time`, `Latitude`, `Longitude`,
so its θ_s is computable too.

### J. Variant matrix & headline

29. **Backend × variant matrix.** "Use both `robust_ztt` and `robust_hybrid`,
    elastic = `robust_hybrid`" — which matrix did you mean?
    - (a) all five RT variants under *both* backends → 10 registered
      algorithms, doubling the full-MCMC budget on every dataset; or
    - (b) the five variants under `robust_hybrid` only, plus a single
      elastic-only `robust_ztt` run as a backbone cross-check → 6.
    Naming would carry the backend, e.g. `expb_pow_hyb_ramfl` /
    `expb_pow_ztt_el`.

>A. I want these 5:
- Elastic only (ztt)
- Elastic only (hybrid)
- Elastic + Raman
- Elastic + Chl-FL + Raman
- Elastic + Chl-FL + Raman + CDOM

Your naming schema is fine.

30. **"Full inelastic" for the headline ΔBIC pair.** With five variants,
    elastic-vs-full-inelastic means which partner:
    `expb_pow_*_ramfl` (Raman + Chl-fl — the physics L23 X=4 truth actually
    contains) or `expb_pow_*_ramflcdom` (everything we can turn on)?

>A. Everything we can turn on.

31. **Variant 5 on L23.** L23 X=4 truth has *no* CDOM fluorescence (and used
    a single-Gaussian emission line, while we fit double per Q11). Running
    the CDOM variant on L23 is still informative — it measures whether
    surplus physics degrades a fit — but confirm you want variant 5 run on
    all three datasets, not just PANGAEA/PACE. And should variant-5 rows on
    L23 carry a metrics `caveat` tag (à la `CDOM_vs_adg`) noting the truth
    lacks that process?

>A. Yes, let's run it on all three datasets.  And add a caveat tag noting the truth lacks CDOM fluorescence.

### K. CDOM input & code placement

32. **a_dg as a_cdom.** `expb_pow`'s exponential component is combined
    CDOM+detrital (`a_dg`), but the Hawes kernel wants pure CDOM absorption —
    feeding `a_dg` in will overestimate the fluorescence source by the
    detrital fraction. It's the only spectrum the model has. Accept `a_dg` as
    the `a_cdom` proxy as-is (scale stays 1.0 per Q20), or apply a fixed
    CDOM fraction?

>A. Good catch.  Let's apply a fixed CDOM fraction for 0.8 and be clear about this.

33. **RoB branch for the solar-zenith utility.** Per Q17, the
    `solar_zenith(time, lat, lon)` helper goes in the RoB repo. RoB is
    currently on `cdom-rt` (a PR-ready branch, per its last commits) — do I
    write the utility on `cdom-rt` too, or do you want to cut a separate
    branch for it first? I plan a dependency-free NOAA solar-position
    formula (±0.1°, ample here) unless you prefer astropy/pvlib.

>A. Yes, let's stay on the `cdom-rt` branch.

### L. Sweep partitioning

34. **Two sweeps.** The wavelength window is sweep-level in `SweepConfig`,
    and PACE needs a different one. Plan: sweep RT-A = L23 X=4 + PANGAEA-97
    at 400–750; sweep RT-B = PACE-100 at its own window; one combined report
    round. OK, or would you rather I add per-dataset window plumbing so one
    sweep holds all three?

>A. OK

35. **PACE window, final.** The chosen route (a) NPZs are pre-windowed to
    400–700 nm — the 700–719 nm bands are *not recoverable* from them (Q24's
    400–719 would require re-extracting those pixels from V3_2 granules,
    i.e. downloading up to ~100 granules ≈ 50 GB). Accept 400–700 for PACE
    (also keeps our fits comparable to PAB's 14,609 existing elastic fits),
    or re-extract?

>A. 400-700 is good, do not re-extract.

---

### Round 4 (2026-09-05) — final gaps

The plan is now pinned except for two input-data choices on the real
datasets. The settled matrix, for the record: `expb_pow_ztt_el`,
`expb_pow_hyb_el`, `expb_pow_hyb_ram`, `expb_pow_hyb_ramfl`,
`expb_pow_hyb_ramflcdom` (variants 3–5 on `robust_hybrid`, per "elastic =
`robust_hybrid`"); headline ΔBIC pair = `expb_pow_hyb_el` vs
`expb_pow_hyb_ramflcdom`; `a_cdom = 0.8 × a_dg` (documented prominently);
variant 5 on all three datasets with an L23 caveat tag; zenith utility on
RoB `cdom-rt`; two sweeps; PACE at 400–700.

36. **Ed source for the inelastic terms on PANGAEA/PACE.** The Raman ratio
    and fluorescence kernel need downwelling irradiance Ed(λ). Two options:
    - (a) RoB's packaged Ed table (`robust/rt/data/ed_l23.npz`: one clear-sky
      spectrum, interpolated in θ_s over 0–60°) — self-consistent with the
      L23 sweep, zero new inputs;
    - (b) per-record Ed from `correct_atmosphere.downwelling` (what BING's
      legacy Chl-fl path uses), routed via the `Geometry.Ed` override.
    (a) treats sky spectral shape as universal — likely fine since the Raman
    term self-normalizes on Ed(λ′)/Ed(λ) — but it's a physics choice you
    should own. Which?
>A. Let's go with (a).

37. **Viewing geometry for PACE.** PACE pixels are viewed off-nadir (sensor
    zenith up to ~60°), but route (a) NPZs + `pab.db` do not store sensor
    geometry, and RoB's hybrid emulator was trained nadir-view only. So the
    practical choice is θ_v = 0, Δφ = 0 for PACE (solar zenith still computed
    per-pixel per Q17) — i.e. the RT comparison is at-nadir-equivalent, and
    absolute geometry effects are out of scope. Confirm, or should I flag
    this as a stated limitation in the report text as well?
>A. I confirm and also note it in the report text.

One implementation note inside the accepted Q28 scope (no question): keeping
the RT variants out of the shared leaderboard (Q27) needs an explicit
exclusion mechanism, since `leaderboard.update()` folds *every* sweep under
the runs root whenever any build calls `build_landing()` — I'll add a
provenance flag (e.g. `leaderboard: false` in the sweep config) that
`leaderboard.update` honors, so the exclusion survives future rebuilds.

## Logs

### 2026-09-06 — Prompt 5: final answers recorded; execution prompts generated (Fable)

Final decisions from JXP's round-4 answers:
- **Q36 (Ed source):** option (a) — RoB's packaged `ed_l23.npz` clear-sky Ed
  table, interpolated in θ_s, for all datasets. Self-consistent with L23;
  no `correct_atmosphere` dependency on the robust path.
- **Q37 (PACE viewing geometry):** θ_v = 0, Δφ = 0 confirmed; to be stated
  as a limitation in the report text.

With that, all open questions are resolved. Wrote the Execution section:
a pinned-decisions header (so each execution prompt is self-contained) and
eight prompts (6–13, continuing the global numbering):
6 = BING CDOM-fl path (`include_CDOM_fl` + `cdom_fraction` rt_dict keys,
a_cdom = 0.8×a_dg wiring, jit-cache keys, tests) on `rob_cdom`;
7 = RoB dependency-free NOAA `solar_zenith` on `cdom-rt`;
8 = IOPtics core plumbing (`dataset_opts`, extended `RTOptions`, geometry
threading with the 5-tuple, `PROVENANCE_SCHEMA` 4, `leaderboard: false`);
9 = PACE extraction script (seeded 100-of-274 run1k NPZs + pab.db join +
θ_s) and the `PACE` adapter with a `needs_pace_pab` tier;
10 = `register_rt_variants()`, the frozen PANGAEA-97 id list, the
`rt_tests` build script + YAMLs, metrics `dbic_pair`/caveat, and a micro
smoke run before anything long;
11 = sweep RT-A run + metrics + chain-health checks;
12 = sweep RT-B run + metrics + consistency check vs PAB's stored elastic
posteriors;
13 = report round with the PACE headline figure, the stated-limitations
paragraph, sphinx `-W`, and the CI-equivalent test pass.

Ordering rationale: BING (6) and RoB (7) changes are independent of each
other but both precede IOPtics plumbing (8), which 9–10 build on; the
smoke run in 10 gates the two expensive sweeps (11–12); reporting (13)
consumes only persisted artifacts. Each prompt ends with the standing
conventions (pytest -q, Q&A, Log). No code written this prompt → no
pytest run.

### 2026-09-05 — Prompt 4: round-3 answers digested; two final questions (Fable)

Decisions recorded from JXP's round-3 answers:
- **Variant matrix (Q29):** five registered algorithms — elastic-only under
  *both* backends (`expb_pow_ztt_el`, `expb_pow_hyb_el`), then
  `+Raman`, `+Raman+Chl-fl`, `+Raman+Chl-fl+CDOM` under `robust_hybrid`
  (`expb_pow_hyb_ram`, `expb_pow_hyb_ramfl`, `expb_pow_hyb_ramflcdom`).
  The standalone Elastic+Chl-FL variant was dropped from the Goal list.
- **Headline (Q30):** ΔBIC elastic vs everything-on
  (`expb_pow_hyb_el` vs `expb_pow_hyb_ramflcdom`).
- **Variant 5 everywhere (Q31):** runs on L23, PANGAEA-97, and PACE-100;
  L23 rows get a metrics caveat tag noting the X=4 truth lacks CDOM
  fluorescence (mechanism mirrors `CDOM_vs_adg`).
- **CDOM source (Q32):** `a_cdom = 0.8 × a_dg` — fixed CDOM fraction 0.8,
  to be documented prominently in code, provenance, and report text.
- **Zenith utility (Q33):** goes on RoB `cdom-rt`; dependency-free NOAA
  solar-position formula.
- **Sweeps (Q34):** two — RT-A (L23 X=4 + PANGAEA-97, 400–750 nm),
  RT-B (PACE-100, 400–700 nm per Q35); one combined report round.

Remaining opens posed as Q36–Q37 (Ed source for the inelastic terms on the
real datasets; θ_v = 0 confirmation for PACE). Everything else is settled;
once these two are answered, the next prompt can commission the design/
coding plan and implementation can begin. Also flagged (not a question): a
`leaderboard: false` exclusion flag is needed so `leaderboard.update()`
doesn't fold the RT sweeps into the shared board on future rebuilds —
within the Q28-accepted core scope.

No code written this prompt → no pytest run.

### 2026-09-05 — Prompt 3: round-2 answers digested; environment verified; round-3 questions (Fable)

Decisions recorded from JXP's round-2 answers: robust installed by JXP into
ocean14 (verified below); use both `robust_ztt` and `robust_hybrid` with
"elastic" meaning `robust_hybrid` (matrix ambiguity → Q29); θ_s = 0 for L23,
computed from time/lat/lon for PANGAEA and PACE, with any new code placed in
the RoB repo (branch → Q33); **fit B_p** (adds one linear parameter
[0.004, 0.05] to every variant — k stays equal across variants); RoB moved to
`cdom-rt`, BING to a new branch for the CDOM patch, and I am authorized to
write the BING CDOM-fl code (Q19); `CDOMFl.scale` fixed at 1.0; PANGAEA
population = the 97 NOMAD ids with all three truth families; PACE route (a)
= sample 100 of the 274 run1k chain NPZs (window conflict → Q35); PACE
adapter via one-time extraction file, `varRrs = Rrs_unc²` + 2% floor; keep
negative-Rrs spectra; full MCMC on all three datasets ("workstation is all
yours"); PACE headline = fractional IOP change at 443 nm + ΔBIC histogram;
RT variants stay **out** of the shared leaderboard; IOPtics core scope
(RTOptions fields, geometry threading, `dataset_opts`, PACE adapter,
PROVENANCE_SCHEMA 3→4) accepted.

Verification performed this prompt (all in ocean14):
- RoB checkout now on `cdom-rt` @363951d; BING on `rob_cdom` @51a0fb9 (note:
  branch is `rob_cdom`, not `rob_cdom_fl` as stated in the Q19 answer).
- `import robust` resolves to the editable local checkout;
  `robust.rt.cdom_fl` imports (Hawes constants visible); flax 0.12.9;
  jax 0.11.1; `import bing.evaluate` now works; `rt_dict_from_p` returns the
  10-key dict (7 legacy + `rt_backend`/`fit_Bp`/`Bp_value`).
- BING robust smoke tests: `pytest -q test_evaluate_robust.py -k "import or
  parity or defaults"` → **3 passed** in 1.5 s.
- run1k chain NPZ keys = `{wave, Rrs, varRrs, chains, param_names, Chl}` —
  no geometry inside, but filenames (wmo_cycle_granule_ix_iy_model) join to
  `run1k/pab.db`: `matchup_pixels` has per-pixel lat/lon, `granules` has
  `time_start` → per-spectrum solar zenith is computable. 274 NPZs on disk.
- PANGAEA V3 IOP table carries `Date/Time`, `Latitude`, `Longitude` per
  record → θ_s computable for the 97-id subset.

Round-3 questions Q29–Q35 posed above (variant×backend matrix, headline
pair, variant 5 on L23 + caveat, a_dg-as-a_cdom proxy, RoB branch for the
zenith utility, two-sweep partitioning, PACE 400–700 acceptance). No modules
written → no new pytest beyond the smoke check above.

### 2026-09-05 — Prompt 2: round-1 answers digested; BING@develop, PAB, Erickson explored (Fable)

Decisions recorded from JXP's round-1 answers: RoB elastic only; corrected-head
circularity on L23 accepted (other datasets + 100 random PACE spectra from PAB
provide further validation); PANGAEA included; `dataset_opts` approved;
`expb_pow` only, variants registered as prefixed distinct names; same 400–750 nm
window for all five variants; `double_gaussian=True`; φ_C fixed at 0.02; full
MCMC; headline = elastic vs full inelastic.

Explored with three parallel subagents:

**BING@develop (51a0fb9, PRs #27/#29 `rob_rt`):**
- The BING↔RoB link is real and end-to-end: `rt_dict` grew 3 keys
  (`rt_backend` ∈ {gordon, robust_ztt, robust_hybrid, robust_baseline},
  `fit_Bp`, `Bp_value`); dispatch in `log_prob`/`fit_func`/reconstructors to
  `evaluate.calc_Rrs_from_models_robust`, which translates to
  `robust.rt.forward` via an lru-cached jit factory. Elastic = ZTT or
  ZTT+emulator (Gordon G(λ) not consulted); learned inelastic corrections
  hard-wired OFF (`corrections=False`, jit safety); geometry = new
  `ObsGeometry(theta_s, theta_v, dphi)` threaded as optional 5th element of
  the obs tuple, θ_s required (never defaulted) for robust backends;
  B_p fixed (0.01) or fittable as a trailing linear parameter [0.004, 0.05].
  ~85 new tests (`test_evaluate_robust.py`); benchmark: robust ≈ 6–7× slower
  per log_prob than gordon (5,991 vs 38,936 calls/s), no emcee pooling,
  per-worker JIT recompile in process pools.
- **No CDOM-fl path in BING** — no rt_dict key, `CDOMFl` never passed, a_dg
  never fed as `a_cdom`. The physics landed on RoB branch `origin/cdom-rt`
  (363951d: `robust/rt/cdom_fl.py` 410 lines + tests), which BING's setup.py
  pins — but the local RoB checkout is on `inelastic-rt` (834466f, pre-CDOM).
  So variant 5 needs a small BING patch (Q19) + RoB branch switch (Q15).
- **ocean14 cannot currently import `bing.evaluate`**: `robust` (and `flax`)
  are not installed in the env; BING@develop imports robust unconditionally.
  Blocking for everything; raised as Q15.
- Known accuracy note (BING skill docs): robust's inelastic terms differ from
  BING's reference NumPy implementation by mean ~5.6%/max ~11.4% (Raman)
  and ~5.8%/9.2% (fluorescence) — from interpolating emission-grid IOPs
  rather than re-evaluating the parametric models; acceptable per the rob_rt
  design, noted here for interpreting L23 fits.

**PAB (`/mnt/tank/Oceanography/python/PAB`, branch `first-full-run`):**
- PAB = PACE × BGC-Argo matchups + BING fits (full run: 14,610 matchups,
  14,609 ExpBPow fits; chains on Nautilus, not local). No spectra archived —
  pixels re-read from granules; but 274 run1k chain NPZs on disk hold real
  V3_2 spectra (wave/Rrs/varRrs, 400–700 nm).
- Local granule archive under `$OS_COLOR/PACE/`: 1,104 V3_1 L2_AOP granules
  (384 GB) → random good-mask pixels extractable today with
  `pab.pace.cloud.read_datatree` + `flags.good_mask` + `extract_spectrum`
  (verified working in ocean14; pab not pip-installed but extraction path
  needs only installed deps).
- PACE OCI grid: 172 bands 346–719 nm, **588–613 nm gap**, ~1 nm sampling
  640–719; per-pixel `Rrs_unc` cube is real and used (5–6% blue rising to
  30–44% at 613–719 nm — the inelastic-signal region is the noisiest).
  No random-spectrum sampler exists; routes posed as Q22.

**PANGAEA/Erickson (answer written into Q&A preamble):** Valente+22 V3
compilation; 1,593 spectral-truth ids (83% NOMAD = Erickson+23's substrate;
97 NOMAD ids with all three IOP families vs their 86 stations); per-record
`subdataset` tag makes a NOMAD stratum trivial. No Erickson-specific file
exists; their role in IOPtics is the metrics convention.

Round-2 questions Q15–Q28 posed above. No code written → no pytest run
(note: the suite can't run against BING@develop until Q15 is resolved anyway).

### 2026-09-05 — Prompt 1: context exploration and Q&A (Fable)

Explored the three codebases with parallel subagents; no code written yet.

**BING (`/mnt/tank/Oceanography/python/bing`, @850000b, clean):**
- Forward model funnels through `evaluate.calc_Rrs_from_models(...)`; RT
  variants toggle via the 7-key `rt_dict` (`rt/defs.py::rt_dict_from_p`):
  `variable_Gordon(_G0/_bbp)`, `include_Raman`, `include_Chl_fl`, `phi_C`,
  `double_gaussian`. Raman enters *multiplicatively*
  (`calc_raman_correction_factor`, S&P98 two-flow), Chl-fl *additively*
  (`calc_Rrs_fluorescence`, Gordon-79-style with excitation integral).
- Chl-fl is driven by the last a-model parameter (a_ph amplitude / log10 Chl
  for GSM); φ_C is a fixed scalar, not fitted.
- Regression tests vs L23 inelastic fixture exist (`test_l23_inelastic.py`,
  X2/X1 Raman increment < 15%, X4−X2 fluorescence peak within ±15% at 685 nm).
- **No CDOM fluorescence anywhere in BING.**
- Stale note: `.claude/skills/inelastic-rrs/SKILL.md` claims fluorescence isn't
  wired into `log_prob` — it is (via `calc_Rrs_from_models`).

**RoB (`/mnt/tank/Oceanography/python/retrieve-or-bust`, @834466f):**
- Package imports as `robust`; all RT under `robust/rt/` — JAX/flax,
  differentiable, batched. Single entry point
  `hybrid.forward(iops, phase_params, geometry, wave, mode, inelastic=,
  corrections=)`; variants selected by the `Inelastic` pytree
  (`raman`/`fluorescence` static flags, `phi_C` leaf, `cdom_fl`), not an
  rt_dict. Composition: Rrs_total = elastic(ZTT+emulator) × f_R + φ_C·K_fl,
  additive in rrs space.
- Physics ported term-for-term from fixed BING, cross-checked rtol ≤ 1e-6
  (`test_inelastic_bing_xcheck.py`). Analytic inelastic: ~2% rRMS vs L23 X4;
  with learned δ_R/δ_F correction heads (trained on L23): 0.34%. Heads valid
  only λ ≥ 400 nm, nadir view, θ_s ∈ [0,60°].
- **CDOM-fl is interface-only** (M5 task 1): `CDOMFl`/`IOPs.a_cdom` types +
  fail-fast guard landed, but no kernel, no wiring (CDOM-only config silently
  returns elastic), no training truth (L23 lacks CDOM-fl; deferred to M6).
  Design: `design/rt_cdom_fluorescence_model.md` (Hawes 1992).
- No code dependency in either direction; RoB uses BING only as a numerical
  reference in tests.

**IOPtics (branch `rt-tests`):**
- RT flags already flow end-to-end: `RTOptions` (7 fields mirroring rt_dict) →
  `spec.to_bing_p()` → `rt_dict_from_p` → `chisq_fit.fit`/`inference.fit_one`;
  YAML `rt:` overrides merge partially and are provenance-digested.
  `run._prepare` already wires `init_var_gordon`/`init_Chl_fluorescence`
  (guarded by `needs_inelastic` — `correct_atmosphere` dependency).
- **Gap:** `run_sweep` passes no `**load_opts` to `prep_dataset`, so L23 X=4
  is unreachable from a sweep config (only `test_micro.py` reaches it via
  direct `prep_one('L23', 0, X=4)`). Needs a `dataset_opts` key or
  build-script-local prep.
- Variant collision: YAML `rt:` overrides don't change the registry name, so
  RT variants in one sweep must be registered under distinct names
  (`register_turbid()` is the pattern; `build_v3.py` the precedent).
- Metrics need no changes for a variant contest (group by algorithm; equal k
  makes ΔBIC a pure likelihood contest); `dbic_pair` default would need
  overriding. `caveat` mechanism (`CDOM_vs_adg`) is the template for flagging
  e.g. inelastic-model-on-X1-truth rows.
- Build template confirmed: `build_v1.py` `main(flg)` stages 1=run, 2=metrics,
  3=report (exemplars → cross_algorithm → landing); `build_v2.py` adds bounded
  obs_ids and skips exemplars; `build_v3.py` shows opt-in registration.
- Only L23 has inelastic-truth Rrs (X=4 sibling with identical IOP truth —
  the controlled experiment). PANGAEA = real spectra, no RT truth; GLORIA
  weak for RT. No PACE dataset adapter (PACE is a noise model here).

**Open questions** posed in Q&A above (integration mode, CDOM-fl scope,
datasets, plumbing, naming, window, φ_C, MCMC scale, headline metric).
No modules written → no pytest run this prompt.
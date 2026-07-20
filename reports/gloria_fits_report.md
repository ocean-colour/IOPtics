# Why BING chi-squared fits of GLORIA hyperspectral Rrs fail

*IOPtics investigation report. All numbers below are produced by
`reports/scripts/gloria_fits_report.py` (ocean14 interpreter, `Agg` backend) on
a fixed sample of 40 GLORIA and 40 L23 spectra trimmed to 400-750 nm.*

## Summary

**Root cause (two coupled factors, not one).**

1. **Functional-FORM inadequacy is the dominant cause — tested, not assumed.**
   JXP rightly pushed back on the first draft: *why can't a model with larger
   CDOM and NAP fit?* We tested it directly (new section below). The amplitude
   priors on CDOM (`Adg`), phytoplankton (`Aph`) and NAP backscatter (`Bnw`) are
   **already** `log_uniform` over 1e-6..1e5 — effectively unbounded — so "more
   CDOM/NAP" is already allowed. Widening them further to 1e-8..1e8 *and* opening
   the CDOM slope `Sdg` and the bbp slope `beta` leaves the fit **byte-identical**
   (median reduced chi-squared **2.47e2**, standard and wide priors alike; the
   points fall exactly on the 1:1 line), with only 3/15 fits anywhere near a
   bound. An independent wide-prior **MCMC** (which does not use LM or a
   `maxfev` budget) lands at the **same** chi-squared (median 2.55e2). So the
   problem is not parameter *range* and not the optimiser — it is the model's
   spectral *form*: a single-exponential `a_dg` + fixed-shape Bricaud `a_ph` +
   power-law `bbp`, run through the Gordon relation, cannot generate GLORIA's
   green-red multi-hump. The miss is localised to the **green-red 500-750 nm
   band** (relative residual approaching -100%), while the blue is fit to within
   ~10-30%.
2. **The default `curve_fit` evaluation budget is too small** for the stiff
   351-band GLORIA objective. Raising `maxfev` ~40x roughly triples the success
   rate (**12.5% -> 37.5%** for `expb_pow`) — necessary, but far from sufficient,
   and irrelevant to the deeper form problem above.

Band down-sampling (30 nm) and `varRrs` inflation (100x) do **not** help at all
(both stay at 12.5%), ruling out "too many bands" or "objective too stiff" as
independent causes. Crucially, the model *does* fit **clear/less-turbid** GLORIA
spectra well (best reduced chi-squared **0.08**, Rrs peak ~505-526 nm); failure
grows monotonically as the Rrs peak moves red (bad fits peak ~571 nm, the worst
at 750 nm). GLORIA Rrs peaks near **568 nm** (median) with secondary humps at
~649 and ~700 nm; L23 peaks near **405 nm** and decays monotonically.

**Recommendation.** Do not expect `expb_pow`/`giop`/`gsm` as configured to fit
turbid GLORIA. This is **not** fixed by widening CDOM/NAP priors (shown below).
Short term: bump `maxfev` (cheap, roughly triples yield) and treat turbid GLORIA
fits as a distinct, out-of-scope regime. Medium term the real fix is a richer
**forward-model form**: an absorption parameterisation with a free (or
multi-component) `a_ph` shape and NAP/detritus term, and a backscatter model
that, together, can produce a green-red-peaked, NIR-rising Rrs. Widening ranges
alone will not do it.

## Problem

A real GLORIA chi-squared sweep with `expb_pow` fails with scipy
`curve_fit`'s `RuntimeError: Optimal parameters not found: The maximum number of
function evaluations is exceeded.` The initial guess is in-bounds (this is
genuine LM non-convergence, not prior rejection). The task is to quantify the
failure across variants and attribute the cause.

## Data characterisation

| quantity | GLORIA (400-750 nm) | L23 (400-750 nm) |
|---|---|---|
| bands | **351** (1 nm) | **71** (5 nm) |
| median `varRrs` | 2.28e-08 | 2.48e-08 |
| median Rrs-peak wavelength | **568 nm** | **405 nm** |
| Rrs shape | green-red, multi-humped | blue, monotonic decay |

The two datasets have essentially the same per-band noise variance, so `varRrs`
magnitude is **not** what separates them. What differs is (a) band count (351 vs
71) and (b) spectral shape. GLORIA's OC4-derived Chl initial guess spans a
nonsensical range — median 15.7, min 0.1, **max 2224 mg/m^3** — because the OC4
blue/green band ratio breaks down in turbid water, so the LM start is sometimes
far off for the worst spectra (a secondary contributor).

![Rrs shape contrast](figures/rrs_shape_contrast.png)

![Peak-wavelength distribution](figures/peak_wavelength_hist.png)

## Method

The script reuses the package's own fit path (`ioptics.run._prepare`,
`run.initial_guess`, `run._prior_bounds`) and BING's `fit_func`, but calls
scipy `curve_fit` directly so it can vary `maxfev`, thin the band grid, or
inflate `varRrs` **without editing package source**. For each variant it records
the convergence rate over the same 40 GLORIA spectra and, for successes, the
reduced chi-squared (`chi^2 / (n_bands - k)`) evaluated at the fitted parameters
using the record's own `varRrs`. A tiny MCMC (`nsteps=300`) is run as an
alternative sampler.

## Results

### Convergence rates

| variant | converged | rate |
|---|---|---|
| `expb_pow` baseline | 5/40 | **12.5%** |
| `giop` baseline | 7/40 | 17.5% |
| `gsm` baseline | 10/40 | 25.0% |
| `expb_pow` varRrs x100 | 5/40 | 12.5% |
| `expb_pow` down-sample 30 nm | 5/40 | 12.5% |
| `expb_pow` maxfev 20k | 15/40 | **37.5%** |
| `giop` maxfev 20k | 15/40 | 37.5% |
| `gsm` maxfev 20k | 15/40 | 37.5% |
| `expb_pow` ds30 + maxfev | 15/40 | 37.5% |
| **`expb_pow` baseline (L23)** | 40/40 | **100.0%** |

![Convergence rates](figures/convergence_rates.png)

Reading the table: L23 converges 100% out of the box; GLORIA converges 12.5%.
Raising `maxfev` ~40x (to 20000) lifts GLORIA to 37.5% — the only lever that
moves the needle — but down-sampling to 30 nm and inflating `varRrs` 100x change
nothing. Fewer-parameter models (`giop` 3 params, `gsm` 3 params) do marginally
better at baseline than `expb_pow` (5 params), consistent with a smaller
Jacobian needing fewer evaluations, but all three converge on the same subset
(~37.5%) once the budget is lifted.

> Note on the earlier "0/20" measurement: the first 20 contiguous GLORIA ids
> happen to be a benign cluster where `maxfev` alone reaches 100%. Across a
> sample spread over all 7572 spectra the true baseline is ~12.5% and the
> `maxfev` ceiling is ~37.5% — so the sample choice matters, and `maxfev` is not
> a general fix.

### Model adequacy

The decisive result: for the GLORIA spectra that *do* converge, the fit is still
bad. Median reduced chi-squared is **2.47e2** for GLORIA (maxfev 20k) versus
**0.97** for L23. A chi-squared per degree of freedom of ~250 means the model
misses the data by ~16 sigma per band on average.

![Reduced chi-squared distribution](figures/chi2_distribution.png)

The example overlay makes the mechanism visible: `expb_pow` cannot reproduce
GLORIA's green peak and the secondary ~649 / ~700 nm humps — it produces a
single smooth blue-shifted bump — whereas it tracks L23 tightly.

![Fit overlay](figures/fit_overlay.png)

### MCMC alternative

A tiny MCMC (`nsteps=300`) ran to completion on 3/3 GLORIA spectra, i.e. the
sampler does not choke the way LM does. (It explores rather than demanding a
descent to a minimum that the model cannot reach; it does not, of course, fix
the underlying shape mismatch.)

## Root cause

- **Primary: forward-model shape mismatch.** `expb_pow`/`giop`/`gsm` are
  open-ocean parameterisations. Against GLORIA's turbid green-red Rrs the best
  achievable fit has reduced chi-squared ~2.5e2 (vs ~1 for L23). Because no
  parameter set gets close to the tiny in-situ noise floor, LM's trust region
  never contracts and it burns through its evaluation budget — surfacing as the
  `maxfev` error.
- **Secondary: evaluation budget.** scipy `curve_fit` with bounds uses the `trf`
  method with a default `max_nfev ~ 100 * n_params`. For the 351-band GLORIA
  objective that budget is exhausted before convergence; raising it ~40x roughly
  triples the yield (12.5% -> 37.5%).
- **Tertiary: initial guess.** OC4 Chl init is unreliable in turbid water
  (GLORIA range 0.1-2224 mg/m^3), placing the LM start far from any good region
  for the worst spectra.
- **Bug found (not a fit issue):** `ioptics.run.fit_mcmc` did
  `int(record.obs_id)` to index BING's idx-keyed Chl/Y arrays, which assumed
  L23-style integer ids and raised `ValueError` on GLORIA's string ids
  (`'GID_1'`). JXP has since fixed this (it now synthesises a positional index),
  so `run.run_algorithm(spec, rec, fit_method='mcmc')` runs on GLORIA — used in
  the continued exploration below.

## Continued exploration: can wider CDOM/NAP fit GLORIA?

JXP pushed back on the "model inadequacy" verdict: *why can't a model with
larger CDOM and NAP fit the GLORIA data?* This section tests the hypothesis
rather than restating the conclusion, and cleanly separates **parameter-RANGE**
inadequacy (curable by widening priors) from **functional-FORM** inadequacy (the
model's spectral shapes genuinely cannot make the green-red multi-hump).

### The amplitude ranges were never the constraint

The shipped `expb_pow` priors are already permissive: the CDOM (`Adg`),
phytoplankton (`Aph`) and NAP-backscatter (`Bnw`) **amplitudes** are all
`log_uniform` over `pmin=-6, pmax=5`, i.e. 1e-6 to 1e5 in linear units — a range
that already spans clear ocean to extreme turbidity. Only two parameters are
genuinely narrow: the CDOM slope `Sdg` (`[0.01, 0.02]`) and the bbp slope `beta`
(`[0, 2]`). So "larger CDOM/NAP" is *already* allowed by the standard config.

### Widen everything and refit — no change

We built a deliberately over-wide `expb_pow`: amplitudes opened to 1e-8..1e8,
`Sdg` to `[0.005, 0.03]`, `beta` to `[-1, 4]`, and refit the 40-spectrum sample
with a raised `maxfev`.

| fit | median reduced chi^2 | n | at a bound |
|---|---|---|---|
| standard priors, LM | **2.47e2** | 15 | — |
| WIDE priors, LM | **2.47e2** | 15 | 3/15 |
| WIDE priors, MCMC | **2.55e2** | 3 | — |

The wide- and standard-prior chi-squared values are **identical** (every point
lands on the 1:1 line) and only 3/15 wide fits sit anywhere near a bound — so the
priors were never the binding constraint. An independent wide-prior **MCMC**
(which uses neither LM nor a `maxfev` budget) reaches the **same** chi-squared
per spectrum (e.g. clear GID_3749: LM 7.75e-2 / MCMC 8.41e-2; turbid GID_2155: LM
2.47e2 / MCMC 2.55e2; extreme GID_7384: LM / MCMC both 2.87e5). Three independent
levers — wider amplitudes, wider slopes, a global sampler — all land in the same
place. This is functional form, not range.

![Range vs form](figures/range_vs_form.png)

The right-hand panel shows the mechanism: fit quality is fine for clear spectra
(reduced chi^2 as low as **0.08**, Rrs peak ~505-526 nm) and collapses as the
Rrs peak moves red into the turbid green-red regime (bad fits peak ~571 nm; the
worst, peaking at 750 nm, reaches chi^2_nu ~2.9e5).

### Where the model misses

For a best-effort wide-prior fit we plot the residual vs wavelength. The model
reproduces the **blue** (400-500 nm) to within ~10-30% but the relative residual
saturates near **-100%** across the entire **green-red 500-750 nm** band: the
open-ocean form decays monotonically to ~0 exactly where turbid GLORIA has its
green peak, its ~649 nm hump, and its NIR (700+ nm) rise.

![Residual localization](figures/residual_localization.png)

### Example fits (clear -> turbid)

Overlays of the wide-prior model against observed Rrs for four representative
spectra, annotated with reduced chi^2. A clear, blue-green spectrum (peak
~526 nm) is fit essentially perfectly (chi^2_nu = 0.08). A moderately turbid
green-peaked spectrum gets a single smooth bump but misses the sharpness and the
~690 nm hump. The most turbid spectrum (NIR-rising, peak 750 nm) is missed
entirely — the model cannot lift the green-red at all.

![Wide-prior example fits](figures/wide_example_fits.png)

### Verdict: form, not range — earlier conclusion sharpened, not reversed

The first draft's "model inadequacy" call was correct, but it is now pinned down
and, importantly, JXP's specific remedy (more CDOM/NAP) is **ruled out with
numbers**: widening the CDOM/NAP/backscatter ranges (amplitude *and* slope) and
switching to a global MCMC sampler leave the median reduced chi^2 unchanged at
~2.5e2. The deficiency is the model's **functional form** — a single-exponential
`a_dg`, a fixed-shape Bricaud `a_ph`, and a power-law `bbp` cannot, in the Gordon
relation, produce the green-red-peaked, NIR-rising reflectance of turbid inland
water — and it is **localised to 500-750 nm**. The model remains adequate for
clear GLORIA spectra.

## Recommendation

1. **Short term:** raise `curve_fit`'s `maxfev` in
   `bing/fitting/chisq_fit.py` (or expose it via IOPtics) — cheap and roughly
   triples GLORIA yield. Keep it modest; it is not a cure.
2. **Report GLORIA as its own regime.** Even converged fits are poor
   (chi^2_nu ~ 250); IOPtics metrics should flag GLORIA as out-of-scope for the
   current open-ocean models rather than reporting them as successes.
3. **Medium term (the real fix) is a richer forward-model FORM, not wider
   ranges.** Widening CDOM/NAP priors is proven above *not* to help. GLORIA needs
   an absorption parameterisation with a free or multi-component `a_ph` shape
   (to admit the green peak and the ~649/690 nm humps) plus an explicit
   NAP/detritus term, paired with a backscatter model that together can produce
   a green-red-peaked, NIR-rising Rrs.
4. **MCMC** works on GLORIA now (JXP's obs_id fix) and does not suffer the LM
   budget failure, but it converges to the same poor optimum under the current
   form — so it is a fix for the *sampler*, not for the model. Also
   replace/augment the OC4 Chl init with a turbid-robust estimator (OC4 returns
   up to 2224 mg/m^3 here).
5. **Flag by regime, not globally.** The current models are adequate for clear
   GLORIA spectra (reduced chi^2 ~0.1); IOPtics should report turbid spectra
   (red-shifted Rrs peak / high chi^2_nu) as out-of-scope rather than failures.

## Reproducibility

```bash
cd /mnt/tank/Oceanography/python/IOPtics
/home/xavier/miniconda3/envs/ocean14/bin/python \
    reports/scripts/gloria_fits_report.py
```

The script is self-contained and rerunnable: no network, `Agg` backend, a fixed
deterministic sample (40 GLORIA spread across the dataset, 40 L23), tiny MCMC. It
writes all figures to `reports/figures/*.png` and prints the convergence table,
the reduced-chi-squared summary, and the range-vs-form table. Runtime is a few
minutes. It reads GLORIA CSVs from `$OS_COLOR/GLORIA` and does not modify any
package source.

Figures produced: `rrs_shape_contrast.png`, `peak_wavelength_hist.png`,
`convergence_rates.png`, `fit_overlay.png`, `chi2_distribution.png`, and (this
round) `range_vs_form.png`, `wide_example_fits.png`,
`residual_localization.png`.

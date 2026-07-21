"""Investigate why BING chi-squared fits of GLORIA in-situ hyperspectral Rrs fail.

Self-contained, rerunnable investigation script for the IOPtics report
``reports/gloria_fits_report.md``. It:

  1. Reproduces the baseline ``expb_pow`` / ``giop`` / ``gsm`` chi-squared
     convergence on a fixed sample of GLORIA spectra (and L23 for contrast).
  2. Tests remedies -- raising scipy ``curve_fit`` ``maxfev``, down-sampling the
     351 hyperspectral bands, inflating ``varRrs`` -- and attributes the cause.
  3. Measures reduced chi-squared for the converged fits (model adequacy).
  4. Tries a tiny MCMC as an alternative to Levenberg-Marquardt.

It writes every figure to ``reports/figures/*.png`` and prints a summary table.

Run (from the repo root, no ``conda activate``)::

    /home/xavier/miniconda3/envs/ocean14/bin/python \
        reports/scripts/gloria_fits_report.py

No network required. Runtime is bounded: ~40 GLORIA + ~40 L23 spectra, MCMC
uses tiny nsteps. Does NOT modify package source under ``ioptics/``.
"""
from __future__ import annotations

import os
import sys
import time
import dataclasses
import warnings
from functools import partial

import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# --- repo-root import guard -------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, '..', '..'))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)
_FIGDIR = os.path.join(_REPO, 'reports', 'figures')
os.makedirs(_FIGDIR, exist_ok=True)

from ioptics import prep, run, datasets as D          # noqa: E402
from ioptics.algorithms import registry                # noqa: E402
from ioptics.algorithms.spec import MCMCOptions         # noqa: E402
from bing.fitting.chisq_fit import fit_func             # noqa: E402
from bing import evaluate as bing_eval                  # noqa: E402
from scipy.optimize import curve_fit                    # noqa: E402

# --- configuration (time-bounded) ------------------------------------------
N_SAMPLE = 40           # GLORIA spectra to fit per variant
N_L23 = 40              # L23 spectra for contrast
WV_MIN, WV_MAX = 400.0, 750.0
MAXFEV_BIG = 20000      # ~40x the LM/trf default for these param counts
DS_STEP_NM = 30.0       # coarse-grid spacing for the down-sample test
VAR_INFLATE = 100.0     # varRrs multiplier for the "loosen the objective" test
MCMC_NSTEPS = 300       # tiny MCMC
MCMC_NBURN = 50
N_MCMC_SPECTRA = 3


def gloria_sample():
    """A fixed, spread-out sample of GLORIA obs ids (deterministic)."""
    gids = list(D.get_adapter('GLORIA').obs_ids())
    idx = np.linspace(0, len(gids) - 1, N_SAMPLE).astype(int)
    return [gids[i] for i in idx]


def l23_sample():
    ids = list(D.get_adapter('L23').obs_ids())
    idx = np.linspace(0, len(ids) - 1, N_L23).astype(int)
    return [ids[i] for i in idx]


def downsample(rec, step_nm=DS_STEP_NM):
    """Return a copy of ``rec`` thinned to ~``step_nm`` band spacing."""
    w = rec.wave
    keep = [0]
    for i in range(1, len(w)):
        if w[i] - w[keep[-1]] >= step_nm:
            keep.append(i)
    keep = np.array(keep)
    rc = None if rec.Rrs_clean is None else rec.Rrs_clean[keep]
    return dataclasses.replace(rec, wave=rec.wave[keep], Rrs=rec.Rrs[keep],
                               varRrs=rec.varRrs[keep], Rrs_clean=rc)


def fit_sigma(rec, *, var_inflate=1.0, floor_frac=None):
    """The 1-sigma weight vector for a fit.

    Base is the record's measured ``sqrt(varRrs)`` (optionally ``var_inflate``d).
    When ``floor_frac`` is given, an **error floor** is applied,
    ``sigma = max(sigma_measured, floor_frac * |Rrs|)`` -- the same
    max-of-measured-or-fractional idea as the project's PANGAEA percentage
    fallback. Every result using ``floor_frac`` is an *inflated-noise* result.
    """
    sigma = np.sqrt(np.asarray(rec.varRrs, dtype=float) * var_inflate)
    if floor_frac is not None:
        sigma = np.maximum(sigma, floor_frac * np.abs(np.asarray(rec.Rrs, float)))
    return sigma


def chisq_fit(spec, rec, maxfev=None, var_inflate=1.0, floor_frac=None):
    """Least-squares fit mirroring ``ioptics.run.fit_chisq`` but with a tunable
    ``curve_fit`` ``maxfev``, an optional ``varRrs`` inflation, and an optional
    fractional error floor (``floor_frac``; inflated-noise runs).

    Returns ``(ans, models, rt_dict)`` or raises (curve_fit RuntimeError etc.).
    """
    _, models, rt = run._prepare(spec, rec)
    p0 = run.initial_guess(models, rec)
    bounds = run._prior_bounds(models)
    pf = partial(fit_func, models=models, rt_dict=rt)
    sigma = fit_sigma(rec, var_inflate=var_inflate, floor_frac=floor_frac)
    kw = {}
    if maxfev is not None:
        kw['maxfev'] = maxfev
    ans, _ = curve_fit(pf, None, np.asarray(rec.Rrs, dtype=float),
                       p0=p0, sigma=sigma, bounds=bounds, **kw)
    return ans, models, rt


def model_rrs(models, rt, ans):
    na = models[0].nparam
    pred = bing_eval.calc_Rrs_from_models(models[0], np.atleast_2d(ans)[:, :na],
                                          models[1], np.atleast_2d(ans)[:, na:],
                                          rt, full_return=True)[0]
    return np.atleast_1d(np.squeeze(np.asarray(pred, dtype=float)))


def reduced_chisq(rec, models, rt, ans, *, floor_frac=None):
    """chi^2 / dof at the fitted parameters (measured varRrs, or an error floor
    when ``floor_frac`` is given -- must match the sigma used to fit)."""
    pred = model_rrs(models, rt, ans)
    obs = np.asarray(rec.Rrs, dtype=float)
    sigma = fit_sigma(rec, floor_frac=floor_frac)
    chi2 = float(np.sum(((pred - obs) / sigma) ** 2))
    dof = max(obs.size - ans.size, 1)
    return chi2 / dof


def median_relerr(rec, models, rt, ans):
    """Median absolute relative Rrs residual -- a noise-independent misfit."""
    pred = model_rrs(models, rt, ans)
    obs = np.asarray(rec.Rrs, dtype=float)
    return float(np.median(np.abs(pred - obs) / np.maximum(np.abs(obs), 1e-6)))


def run_variant(label, specname, recs, *, maxfev=None, var_inflate=1.0,
                ds=False, want_chi2=False):
    """Fit every record under one variant; return convergence + chi2_nu stats."""
    spec = registry.get(specname)
    ok, chi2s = 0, []
    t0 = time.time()
    for rec in recs:
        r = downsample(rec) if ds else rec
        try:
            ans, models, rt = chisq_fit(spec, r, maxfev=maxfev,
                                        var_inflate=var_inflate)
            ok += 1
            if want_chi2:
                chi2s.append(reduced_chisq(r, models, rt, ans))
        except Exception:
            pass
    rate = ok / len(recs)
    dt = time.time() - t0
    print(f"  {label:<34s} {ok:2d}/{len(recs)}  ({100*rate:5.1f}%)  {dt:5.1f}s")
    return {'label': label, 'rate': rate, 'n': len(recs), 'ok': ok,
            'chi2_nu': np.array(chi2s)}


def main():
    print("Preparing GLORIA + L23 samples ...")
    gsample = gloria_sample()
    lsample = l23_sample()
    grecs = [prep.prep_one('GLORIA', g, noise='insitu',
                           wv_min=WV_MIN, wv_max=WV_MAX) for g in gsample]
    lrecs = [prep.prep_one('L23', i, wv_min=WV_MIN, wv_max=WV_MAX)
             for i in lsample]

    # Characterise the data.
    g0, l0 = grecs[0], lrecs[0]
    g_peaks = np.array([r.wave[np.argmax(r.Rrs)] for r in grecs])
    l_peaks = np.array([r.wave[np.argmax(r.Rrs)] for r in lrecs])
    g_chl = np.array([r.init.get('Chl', np.nan) for r in grecs])
    print(f"GLORIA: n_bands={g0.wave.size}, varRrs median="
          f"{np.median(g0.varRrs):.2e}, Rrs peak wv median={np.median(g_peaks):.0f} nm")
    print(f"L23   : n_bands={l0.wave.size}, varRrs median="
          f"{np.median(l0.varRrs):.2e}, Rrs peak wv median={np.median(l_peaks):.0f} nm")
    print(f"GLORIA OC4 Chl init: median={np.median(g_chl):.1f} "
          f"range [{np.nanmin(g_chl):.1f}, {np.nanmax(g_chl):.1f}] mg/m^3")

    # ---------------------------------------------------------------- variants
    print("\nConvergence variants (GLORIA sample):")
    results = []
    results.append(run_variant('expb_pow baseline', 'expb_pow', grecs,
                               want_chi2=True))
    results.append(run_variant('giop baseline', 'giop', grecs))
    results.append(run_variant('gsm baseline', 'gsm', grecs))
    results.append(run_variant('expb_pow varRrs x100', 'expb_pow', grecs,
                               var_inflate=VAR_INFLATE))
    results.append(run_variant(f'expb_pow downsample {DS_STEP_NM:.0f}nm',
                               'expb_pow', grecs, ds=True))
    results.append(run_variant('expb_pow maxfev 20k', 'expb_pow', grecs,
                               maxfev=MAXFEV_BIG, want_chi2=True))
    results.append(run_variant('giop maxfev 20k', 'giop', grecs,
                               maxfev=MAXFEV_BIG))
    results.append(run_variant('gsm maxfev 20k', 'gsm', grecs,
                               maxfev=MAXFEV_BIG))
    results.append(run_variant(f'expb_pow ds{DS_STEP_NM:.0f}+maxfev',
                               'expb_pow', grecs, ds=True, maxfev=MAXFEV_BIG))

    print("\nL23 reference:")
    l23_res = run_variant('expb_pow baseline (L23)', 'expb_pow', lrecs,
                          want_chi2=True)

    # ------------------------------------------------------ small MCMC probe
    print("\nTiny MCMC probe (GLORIA):")
    spec = registry.get('expb_pow')
    spec_mcmc = dataclasses.replace(
        spec, fit_method='mcmc',
        mcmc=MCMCOptions(nsteps=MCMC_NSTEPS, nburn=MCMC_NBURN))
    # NOTE: ioptics.run.fit_mcmc does `int(record.obs_id)` (L23-style integer
    # ids) to index BING's idx-keyed Chl/Y arrays; GLORIA ids are strings
    # ('GID_1'), so the packaged MCMC path raises ValueError on GLORIA. We give
    # the record an integer obs_id here just to exercise the probe -- see the
    # report's "Root cause / bug" note.
    mcmc_ok = 0
    t0 = time.time()
    for rec in grecs[:N_MCMC_SPECTRA]:
        rec_int = dataclasses.replace(rec, obs_id=0)
        try:
            run.fit_mcmc(spec_mcmc, rec_int)
            mcmc_ok += 1
        except Exception as e:
            print(f"    MCMC fail: {type(e).__name__}: {str(e)[:70]}")
    print(f"  MCMC expb_pow (nsteps={MCMC_NSTEPS}): {mcmc_ok}/"
          f"{N_MCMC_SPECTRA} ran  ({time.time()-t0:.1f}s)")
    print("  (NB: packaged run.fit_mcmc raises on GLORIA string obs_ids;"
          " probe used an integer obs_id.)")

    # ============ CONTINUED EXPLORATION: range vs form (JXP's question) =====
    wide = continued_exploration(grecs)

    # ==== ROUND 3: it is BACKSCATTER + water absorption, not CDOM/NAP =======
    r3 = round3_backscatter_and_noise(grecs)

    # =========================================================== FIGURES ====
    _fig_shape_contrast(g0, l0)
    _fig_peak_hist(g_peaks, l_peaks)
    _fig_convergence_bars(results)
    _fig_fit_overlay(grecs, lrecs)
    _fig_chi2_dist(results, l23_res)

    # =========================================================== SUMMARY ====
    print("\n" + "=" * 66)
    print("SUMMARY: GLORIA chi-squared convergence by variant")
    print("=" * 66)
    print(f"{'variant':<34s}{'converged':>12s}{'rate':>10s}")
    print("-" * 66)
    for r in results:
        print(f"{r['label']:<34s}{r['ok']:>7d}/{r['n']:<4d}{100*r['rate']:>8.1f}%")
    print(f"{l23_res['label']:<34s}"
          f"{l23_res['ok']:>7d}/{l23_res['n']:<4d}{100*l23_res['rate']:>8.1f}%")
    print("-" * 66)

    def _med(res):
        c = res['chi2_nu']
        c = c[np.isfinite(c)]
        return np.median(c) if c.size else np.nan
    base = next(r for r in results if r['label'] == 'expb_pow baseline')
    mf = next(r for r in results if r['label'] == 'expb_pow maxfev 20k')
    print("\nReduced chi^2 (median, converged fits):")
    print(f"  expb_pow GLORIA maxfev 20k : {_med(mf):.2e}")
    print(f"  expb_pow L23   baseline    : {_med(l23_res):.2e}")

    print("\n" + "=" * 66)
    print("RANGE vs FORM: does widening CDOM/NAP priors fix GLORIA?")
    print("=" * 66)
    print(f"  expb_pow standard priors, LM  : median chi2_nu = "
          f"{wide['med_std']:.2e}  (n={wide['n_std']})")
    print(f"  expb_pow WIDE priors,     LM  : median chi2_nu = "
          f"{wide['med_wide']:.2e}  (n={wide['n_wide']})")
    print(f"  expb_pow WIDE priors,     MCMC: median chi2_nu = "
          f"{wide['med_mcmc']:.2e}  (n={wide['n_mcmc']})")
    print(f"  wide-prior fits sitting at a bound: {wide['n_atbound']}/{wide['n_wide']}")
    print(f"  good fits (chi2_nu<10): median Rrs-peak = {wide['peak_good']:.0f} nm; "
          f"bad fits: {wide['peak_bad']:.0f} nm")

    print("\n" + "=" * 66)
    print("ROUND 3: inflated-noise floor (INFLATED-NOISE results)")
    print("=" * 66)
    print(f"{'noise model':<20s}{'conv':>8s}{'med chi2_nu':>14s}{'med relerr':>12s}")
    print("-" * 66)
    for row in r3['noise_table']:
        print(f"{row['label']:<20s}{row['ok']:>5d}/{row['n']:<2d}"
              f"{row['med_chi2']:>14.2e}{row['med_relerr']:>12.2f}")
    print("-" * 66)
    print("  Inflating noise lowers chi2_nu (bookkeeping) but does NOT change the")
    print("  convergence rate or the ~median relative misfit: the misfit is real.")
    print("=" * 66)
    print("Figures written to reports/figures/")


# ------------------------------------------------------------------ figures
def _fig_shape_contrast(g0, l0):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(g0.wave, g0.Rrs / np.max(g0.Rrs), color='#1b7837', lw=2,
            label=f'GLORIA {g0.obs_id} (peak {g0.wave[np.argmax(g0.Rrs)]:.0f} nm)')
    ax.plot(l0.wave, l0.Rrs / np.max(l0.Rrs), color='#2166ac', lw=2,
            label=f'L23 #{l0.obs_id} (peak {l0.wave[np.argmax(l0.Rrs)]:.0f} nm)')
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel('Rrs / max(Rrs)')
    ax.set_title('Spectral shape contrast: GLORIA (turbid, green-red)\n'
                 'vs L23 (open-ocean, blue)')
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'rrs_shape_contrast.png'), dpi=130)
    plt.close(fig)


def _fig_peak_hist(g_peaks, l_peaks):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bins = np.arange(395, 755, 10)
    ax.hist(g_peaks, bins=bins, color='#1b7837', alpha=0.75,
            label=f'GLORIA (n={g_peaks.size})')
    ax.hist(l_peaks, bins=bins, color='#2166ac', alpha=0.6,
            label=f'L23 (n={l_peaks.size})')
    ax.axvline(np.median(g_peaks), color='#1b7837', ls='--', lw=1.5)
    ax.axvline(np.median(l_peaks), color='#2166ac', ls='--', lw=1.5)
    ax.set_xlabel('wavelength of Rrs peak [nm]')
    ax.set_ylabel('count')
    ax.set_title('Distribution of Rrs-peak wavelength')
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'peak_wavelength_hist.png'), dpi=130)
    plt.close(fig)


def _fig_convergence_bars(results):
    labels = [r['label'] for r in results]
    rates = [100 * r['rate'] for r in results]
    colors = ['#b2182b' if r < 50 else ('#f4a582' if r < 90 else '#1a9850')
              for r in rates]
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(labels))
    ax.barh(y, rates, color=colors)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel('chi-squared convergence rate [%]')
    ax.set_xlim(0, 105)
    ax.set_title('GLORIA convergence by fit variant')
    for yi, r in zip(y, rates):
        ax.text(r + 1, yi, f'{r:.0f}%', va='center', fontsize=9)
    ax.grid(axis='x', alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'convergence_rates.png'), dpi=130)
    plt.close(fig)


def _first_ok_fit(specname, recs, **kw):
    spec = registry.get(specname)
    for rec in recs:
        try:
            ans, models, rt = chisq_fit(spec, rec, **kw)
            return rec, model_rrs(models, rt, ans)
        except Exception:
            continue
    return None, None


def _fig_fit_overlay(grecs, lrecs):
    grec, gpred = _first_ok_fit('expb_pow', grecs, maxfev=MAXFEV_BIG)
    lrec, lpred = _first_ok_fit('expb_pow', lrecs)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    if grec is not None:
        axes[0].plot(grec.wave, grec.Rrs, 'k.', ms=3, label='observed')
        axes[0].plot(grec.wave, gpred, color='#1b7837', lw=2, label='expb_pow model')
        axes[0].set_title(f'GLORIA {grec.obs_id}\nexpb_pow, maxfev 20k (best-effort)')
    axes[0].set_xlabel('wavelength [nm]')
    axes[0].set_ylabel('Rrs [1/sr]')
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.3)
    if lrec is not None:
        axes[1].plot(lrec.wave, lrec.Rrs, 'k.', ms=3, label='observed')
        axes[1].plot(lrec.wave, lpred, color='#2166ac', lw=2, label='expb_pow model')
        axes[1].set_title(f'L23 #{lrec.obs_id}\nexpb_pow, default maxfev (converges)')
    axes[1].set_xlabel('wavelength [nm]')
    axes[1].set_ylabel('Rrs [1/sr]')
    axes[1].legend(frameon=False)
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'fit_overlay.png'), dpi=130)
    plt.close(fig)


def _fig_chi2_dist(results, l23_res):
    mf = next(r for r in results if r['label'] == 'expb_pow maxfev 20k')
    g = mf['chi2_nu'][np.isfinite(mf['chi2_nu'])]
    l = l23_res['chi2_nu'][np.isfinite(l23_res['chi2_nu'])]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    lo = min(g.min() if g.size else 1, l.min() if l.size else 1, 1e-1)
    hi = max(g.max() if g.size else 1, l.max() if l.size else 1)
    bins = np.logspace(np.log10(max(lo, 1e-2)), np.log10(hi * 1.5), 25)
    ax.hist(g, bins=bins, color='#1b7837', alpha=0.75,
            label=f'GLORIA (maxfev 20k), median {np.median(g):.1e}')
    ax.hist(l, bins=bins, color='#2166ac', alpha=0.6,
            label=f'L23 (baseline), median {np.median(l):.1e}')
    ax.axvline(1.0, color='k', ls=':', lw=1, label='chi2_nu = 1')
    ax.set_xscale('log')
    ax.set_xlabel('reduced chi-squared (converged fits)')
    ax.set_ylabel('count')
    ax.set_title('Model adequacy: expb_pow reduced chi^2, GLORIA vs L23')
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'chi2_distribution.png'), dpi=130)
    plt.close(fig)


# =================== CONTINUED EXPLORATION: range vs form ==================
def wide_expb_spec():
    """`expb_pow` with deliberately over-wide CDOM/NAP/backscatter priors.

    Amplitude priors (Adg, Aph, Bnw) are pushed to 1e-8..1e8 (the shipped ones
    are already 1e-6..1e5 -- essentially unbounded), the CDOM slope Sdg is opened
    from [0.01, 0.02] to [0.005, 0.03], and the bbp slope beta from [0, 2] to
    [-1, 4]. If GLORIA fails for lack of CDOM/NAP *range*, this must fix it.
    """
    s = registry.get('expb_pow')
    apriors = [{'flavor': 'log_uniform', 'pmin': -8, 'pmax': 8},   # Adg (CDOM)
               {'flavor': 'uniform',     'pmin': 0.005, 'pmax': 0.03},  # Sdg
               {'flavor': 'log_uniform', 'pmin': -8, 'pmax': 8}]   # Aph
    bpriors = [{'flavor': 'log_uniform', 'pmin': -8, 'pmax': 8},   # Bnw (NAP bb)
               {'flavor': 'uniform',     'pmin': -1.0, 'pmax': 4.0}]  # beta
    return dataclasses.replace(s, apriors=apriors, bpriors=bpriors)


def continued_exploration(grecs):
    """Test JXP's hypothesis: is GLORIA a parameter-RANGE problem (widen CDOM/
    NAP priors and it fits) or a functional-FORM problem (the shapes can't make
    the green-red multi-hump)? Fits the sample under standard vs wide priors
    (LM, raised maxfev) and under a wide-prior MCMC, records where fits land and
    where the residual concentrates, and writes the range-vs-form figures.
    """
    std = registry.get('expb_pow')
    wide = wide_expb_spec()

    peaks, chi2_std, chi2_wide, atbound = [], [], [], 0
    per_spec = []                       # (rec, ans, pred, chi2nu) for wide fits
    for rec in grecs:
        pk = rec.wave[np.argmax(rec.Rrs)]
        try:
            a_s, m_s, rt_s = chisq_fit(std, rec, maxfev=MAXFEV_BIG)
            chi2_std.append(reduced_chisq(rec, m_s, rt_s, a_s))
        except Exception:
            pass
        try:
            a_w, m_w, rt_w = chisq_fit(wide, rec, maxfev=MAXFEV_BIG)
            c = reduced_chisq(rec, m_w, rt_w, a_w)
            chi2_wide.append(c)
            peaks.append(pk)
            per_spec.append((rec, a_w, model_rrs(m_w, rt_w, a_w), c))
            lo, hi = run._prior_bounds(m_w)
            if np.any(np.isclose(a_w, lo, rtol=1e-3) |
                      np.isclose(a_w, hi, rtol=1e-3)):
                atbound += 1
        except Exception:
            pass

    chi2_std = np.array(chi2_std)
    chi2_wide = np.array(chi2_wide)
    peaks = np.array(peaks)
    good = chi2_wide < 10.0

    # Wide-prior MCMC on 3 representative spectra (best / median / worst wide-LM
    # chi2_nu) as an independent, budget-free check.
    spec_mcmc = dataclasses.replace(
        wide, fit_method='mcmc',
        mcmc=MCMCOptions(nsteps=MCMC_NSTEPS, nburn=MCMC_NBURN))
    order = np.argsort([c for _, _, _, c in per_spec])
    picks = sorted({order[0], order[len(order) // 2], order[-1]})
    mcmc_chi2 = []
    print("\nWide-prior MCMC check (independent of LM/maxfev):")
    for j in picks:
        rec = per_spec[j][0]
        try:
            res = run.run_algorithm(spec_mcmc, rec, fit_method='mcmc')
            mcmc_chi2.append(res.stats['chi2_nu'])
            print(f"  {rec.obs_id} peak {rec.wave[np.argmax(rec.Rrs)]:.0f} nm: "
                  f"LM chi2_nu={per_spec[j][3]:.2e}  MCMC chi2_nu="
                  f"{res.stats['chi2_nu']:.2e}")
        except Exception as e:
            print(f"  MCMC fail {rec.obs_id}: {type(e).__name__}: {str(e)[:60]}")
    mcmc_chi2 = np.array(mcmc_chi2)

    # ---- figures ----
    _fig_range_vs_form(peaks, chi2_std, chi2_wide)
    _fig_wide_example_fits(per_spec)
    _fig_residual_localization(per_spec)

    return {
        'med_std': np.median(chi2_std) if chi2_std.size else np.nan,
        'n_std': chi2_std.size,
        'med_wide': np.median(chi2_wide) if chi2_wide.size else np.nan,
        'n_wide': chi2_wide.size,
        'med_mcmc': np.median(mcmc_chi2) if mcmc_chi2.size else np.nan,
        'n_mcmc': mcmc_chi2.size,
        'n_atbound': atbound,
        'peak_good': np.median(peaks[good]) if good.any() else np.nan,
        'peak_bad': np.median(peaks[~good]) if (~good).any() else np.nan,
    }


def _fig_range_vs_form(peaks, chi2_std, chi2_wide):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    # (a) wide vs std chi2_nu -- identical points lie on the 1:1 line.
    n = min(chi2_std.size, chi2_wide.size)
    ax = axes[0]
    if n:
        ax.loglog(chi2_std[:n], chi2_wide[:n], 'o', color='#762a83', ms=6)
        lim = [min(chi2_std.min(), chi2_wide.min()) * 0.5,
               max(chi2_std.max(), chi2_wide.max()) * 2]
        ax.plot(lim, lim, 'k--', lw=1, label='1:1')
    ax.set_xlabel('reduced chi^2, standard priors')
    ax.set_ylabel('reduced chi^2, WIDE priors')
    ax.set_title('Widening CDOM/NAP priors does not\nchange the fit (points on 1:1)')
    ax.legend(frameon=False)
    ax.grid(alpha=0.3, which='both')
    # (b) chi2_nu vs Rrs-peak wavelength -- failure grows toward the red.
    ax = axes[1]
    ax.semilogy(peaks, chi2_wide, 'o', color='#1b7837', ms=6)
    ax.axhline(10, color='k', ls=':', lw=1, label='chi2_nu = 10')
    ax.axhline(1, color='grey', ls='--', lw=1, label='chi2_nu = 1')
    ax.set_xlabel('Rrs-peak wavelength [nm]')
    ax.set_ylabel('reduced chi^2 (WIDE priors)')
    ax.set_title('Fit quality collapses as the Rrs peak\nmoves to green-red '
                 '(turbid)')
    ax.legend(frameon=False)
    ax.grid(alpha=0.3, which='both')
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'range_vs_form.png'), dpi=130)
    plt.close(fig)


def _fig_wide_example_fits(per_spec):
    """Overlay model vs observed Rrs for ~4 representative GLORIA spectra
    (spanning clear to turbid) under the wide-prior fit, annotated with chi2_nu.
    """
    if not per_spec:
        return
    chis = np.array([c for _, _, _, c in per_spec])
    order = np.argsort(chis)
    n = len(order)
    picks = sorted({order[0], order[n // 3], order[2 * n // 3], order[-1]})
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, j in zip(axes.ravel(), picks):
        rec, _, pred, c = per_spec[j]
        ax.plot(rec.wave, rec.Rrs, 'k.', ms=3, label='observed')
        ax.plot(rec.wave, pred, color='#1b7837', lw=2, label='expb_pow (wide)')
        pk = rec.wave[np.argmax(rec.Rrs)]
        ax.set_title(f'{rec.obs_id}  (peak {pk:.0f} nm)  '
                     f'chi2_nu = {c:.1e}', fontsize=10)
        ax.set_xlabel('wavelength [nm]')
        ax.set_ylabel('Rrs [1/sr]')
        ax.legend(frameon=False, fontsize=8)
        ax.grid(alpha=0.3)
    for ax in axes.ravel()[len(picks):]:
        ax.axis('off')
    fig.suptitle('Wide-prior expb_pow fits: clear (top-left) to turbid '
                 '(bottom-right)', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'wide_example_fits.png'), dpi=130)
    plt.close(fig)


def _fig_residual_localization(per_spec):
    """For the worst (most turbid) wide-prior fit, show where the model misses:
    relative residual vs wavelength, with the green-red band shaded.
    """
    if not per_spec:
        return
    chis = np.array([c for _, _, _, c in per_spec])
    j = int(np.argmax(chis))
    rec, _, pred, c = per_spec[j]
    obs = np.asarray(rec.Rrs, dtype=float)
    relres = (pred - obs) / np.maximum(np.abs(obs), 1e-6)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    ax1.plot(rec.wave, obs, 'k.', ms=3, label='observed')
    ax1.plot(rec.wave, pred, color='#b2182b', lw=2, label='wide-prior model')
    ax1.axvspan(500, 750, color='#1b7837', alpha=0.08)
    ax1.set_ylabel('Rrs [1/sr]')
    ax1.set_title(f'{rec.obs_id}: model misses the green-red band '
                  f'(chi2_nu = {c:.1e})')
    ax1.legend(frameon=False)
    ax1.grid(alpha=0.3)
    ax2.plot(rec.wave, relres, color='#b2182b', lw=1.5)
    ax2.axhline(0, color='k', lw=0.8)
    ax2.axvspan(500, 750, color='#1b7837', alpha=0.08,
                label='green-red (500-750 nm)')
    ax2.set_xlabel('wavelength [nm]')
    ax2.set_ylabel('(model - obs) / obs')
    ax2.legend(frameon=False)
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'residual_localization.png'), dpi=130)
    plt.close(fig)


# ============ ROUND 3: backscatter / water absorption / noise =============
# Literature slopes for the CDOM / NAP exponential absorption decay.
#   S_CDOM ~ 0.0176 nm^-1, S_NAP ~ 0.0123 nm^-1  (Babin et al. 2003, JGR-Oceans)
#   both a_g, a_d ~ exp(-S (lambda - 440))  (Bricaud, Morel & Prieur 1981, L&O)
S_CDOM = 0.0176
S_NAP = 0.0123


def _gordon_required_bb(wave, Rrs, a_total):
    """Invert observed Rrs to the backscatter b_b(lambda) *required* to produce
    it given the model's total absorption ``a_total`` (Gordon 1988 relation, the
    same inversion ``ioptics.run.initial_guess`` uses)."""
    from bing.rt import rrs as bing_rrs
    Rrs = np.asarray(Rrs, dtype=float)
    rrs = Rrs / (bing_rrs.A_Rrs + bing_rrs.B_Rrs * Rrs)
    G1, G2 = bing_rrs.G1_STANDARD, bing_rrs.G2_STANDARD
    disc = np.clip(G1 * G1 + 4.0 * G2 * rrs, 0.0, None)
    u = np.clip((-G1 + np.sqrt(disc)) / (2.0 * G2), 1e-3, 1.0 - 1e-3)
    return u * np.asarray(a_total, float) / (1.0 - u)


def _decompose(spec, rec, floor_frac=0.05, maxfev=MAXFEV_BIG):
    """Best-effort fit (inflated noise) + full IOP decomposition for one record.

    Returns a dict with a_total/a_w/a_ph/a_dg, b_b fitted, b_b required, model
    and observed Rrs, and the reduced chi^2 / relerr.
    """
    ans, models, rt = chisq_fit(spec, rec, maxfev=maxfev, floor_frac=floor_frac)
    na = models[0].nparam
    ap = np.atleast_2d(ans)[:, :na]
    bp = np.atleast_2d(ans)[:, na:]
    pred, a_tot, bb_tot = bing_eval.calc_Rrs_from_models(
        models[0], ap, models[1], bp, rt, full_return=True)[:3]
    a_dg, a_ph = models[0].eval_anw(ap, retsub_comps=True)
    a_tot = np.squeeze(np.asarray(a_tot, float))
    return {
        'wave': rec.wave, 'Rrs_obs': np.asarray(rec.Rrs, float),
        'Rrs_mod': np.squeeze(np.asarray(pred, float)),
        'a_tot': a_tot, 'a_w': np.asarray(models[0].a_w, float),
        'a_ph': np.squeeze(np.asarray(a_ph, float)),
        'a_dg': np.squeeze(np.asarray(a_dg, float)),
        'bb_fit': np.squeeze(np.asarray(bb_tot, float)),
        'bb_req': _gordon_required_bb(rec.wave, rec.Rrs, a_tot),
        'chi2_nu': reduced_chisq(rec, models, rt, ans, floor_frac=floor_frac),
        'relerr': median_relerr(rec, models, rt, ans),
        'obs_id': rec.obs_id,
        'peak': rec.wave[np.argmax(rec.Rrs)],
    }


def round3_backscatter_and_noise(grecs):
    """Redo the exploration on the correct physics: CDOM/NAP absorption is ~0 at
    500-750 nm (widening it cannot move Rrs there); the terms that govern that
    band are particulate backscatter b_bp, pure-water absorption a_w, and the
    a_ph 675 nm band. Tests (i) an inflated-noise floor and (ii) an IOP
    decomposition showing the model runs out of *backscatter* in the red.
    """
    spec = registry.get('expb_pow')

    # (i) inflated-noise floor: convergence rate + chi2_nu + true relative misfit
    noise_table = []
    for label, ff in [('measured', None), ('5% floor', 0.05),
                      ('10% floor', 0.10)]:
        ok, chi2s, rels = 0, [], []
        for rec in grecs:
            try:
                ans, models, rt = chisq_fit(spec, rec, maxfev=MAXFEV_BIG,
                                            floor_frac=ff)
                ok += 1
                chi2s.append(reduced_chisq(rec, models, rt, ans, floor_frac=ff))
                rels.append(median_relerr(rec, models, rt, ans))
            except Exception:
                pass
        noise_table.append({
            'label': label, 'ok': ok, 'n': len(grecs),
            'med_chi2': np.median(chi2s) if chi2s else np.nan,
            'med_relerr': np.median(rels) if rels else np.nan})

    # (ii) decompositions across the turbidity range
    decs = []
    for rec in grecs:
        try:
            decs.append(_decompose(spec, rec))
        except Exception:
            pass
    decs.sort(key=lambda d: d['peak'])

    # ---- figures ----
    _fig_iop_decay(grecs[0])
    _fig_iop_decomposition(decs)
    _fig_inflated_noise_examples(decs)

    return {'noise_table': noise_table, 'n_decomp': len(decs)}


def _fig_iop_decay(rec):
    """The kill-shot for the CDOM/NAP hypothesis: a_g, a_d ~ exp(-S(lambda-440))
    vanish by ~550 nm, while a_w rises steeply in the red and a smooth b_bp is
    broad -- so 500-750 nm is owned by backscatter and water, not CDOM/NAP.
    """
    _, models, _ = run._prepare(registry.get('expb_pow'), rec)
    w = np.asarray(rec.wave, float)
    a_w = np.asarray(models[0].a_w, float)
    a_g = np.exp(-S_CDOM * (w - 440.0))          # normalised to 1 at 440 nm
    a_d = np.exp(-S_NAP * (w - 440.0))
    bbp = (w / 550.0) ** (-1.0)                  # illustrative power-law b_bp
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(w, a_g, color='#b8860b', lw=2, label=f'a_CDOM ~ exp(-{S_CDOM}(λ-440))')
    ax.plot(w, a_d, color='#8c510a', lw=2, ls='--',
            label=f'a_NAP ~ exp(-{S_NAP}(λ-440))')
    ax.plot(w, a_w / a_w[np.argmin(np.abs(w - 440))], color='#2166ac', lw=2,
            label='a_water (Pope & Fry 1997), norm@440')
    ax.plot(w, bbp, color='#1b7837', lw=2, ls=':',
            label='b_bp ~ (λ/550)^-1 (illustrative)')
    ax.axvspan(500, 750, color='grey', alpha=0.08)
    for wl in (550, 650, 700):
        i = np.argmin(np.abs(w - wl))
        ax.annotate(f'{100*a_g[i]:.0f}%', (wl, a_g[i]), textcoords='offset points',
                    xytext=(0, 6), fontsize=8, color='#b8860b', ha='center')
    ax.set_yscale('log')
    ax.set_ylim(1e-3, 1e3)
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel('relative magnitude (log; each norm @ 440 nm)')
    ax.set_title('Who owns 500-750 nm? CDOM/NAP absorption vanishes;\n'
                 'water absorption + particulate backscatter dominate')
    ax.legend(frameon=False, fontsize=8, loc='lower center')
    ax.grid(alpha=0.3, which='both')
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'iop_decay.png'), dpi=130)
    plt.close(fig)


def _fig_iop_decomposition(decs):
    """For a turbid spectrum: a(lambda) components (a_w owns the red, a_dg ~ 0
    there) and b_b -- fitted power-law vs the b_b *required* to make the observed
    green/NIR Rrs. The model runs out of backscatter where a_w is large.
    """
    if not decs:
        return
    # pick a turbid, green-red-peaked case (peak >= 560 nm) with a real misfit
    cand = [d for d in decs if d['peak'] >= 560 and d['relerr'] > 0.3]
    d = cand[len(cand) // 2] if cand else decs[-1]
    w = d['wave']
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
    ax1.plot(w, d['Rrs_obs'], 'k.', ms=3, label='observed')
    ax1.plot(w, d['Rrs_mod'], color='#b2182b', lw=2, label='model (5% floor)')
    ax1.axvspan(500, 750, color='grey', alpha=0.07)
    ax1.set_ylabel('Rrs [1/sr]')
    ax1.set_title(f"{d['obs_id']} (peak {d['peak']:.0f} nm): model misses "
                  f"green-red (relerr {d['relerr']:.2f})")
    ax1.legend(frameon=False, fontsize=8)
    ax1.grid(alpha=0.3)
    ax2.plot(w, d['a_tot'], 'k', lw=2, label='a_total')
    ax2.plot(w, d['a_w'], color='#2166ac', lw=1.8, label='a_water')
    ax2.plot(w, d['a_ph'], color='#1b7837', lw=1.5, label='a_ph')
    ax2.plot(w, d['a_dg'], color='#b8860b', lw=1.5, label='a_dg (CDOM+NAP)')
    ax2.axvspan(500, 750, color='grey', alpha=0.07)
    ax2.set_yscale('log')
    ax2.set_ylabel('absorption [1/m]')
    ax2.set_title('a_dg is negligible across 500-750 nm; a_water owns the red')
    ax2.legend(frameon=False, fontsize=8, ncol=2)
    ax2.grid(alpha=0.3, which='both')
    ax3.plot(w, d['bb_fit'], color='#b2182b', lw=2, label='b_b fitted (power law)')
    ax3.plot(w, d['bb_req'], color='#762a83', lw=2, ls='--',
             label='b_b required (invert observed Rrs)')
    ax3.axvspan(500, 750, color='grey', alpha=0.07)
    ax3.set_yscale('log')
    ax3.set_xlabel('wavelength [nm]')
    ax3.set_ylabel('backscatter [1/m]')
    ax3.set_title('The wall: required b_b >> fitted power-law b_b in the red')
    ax3.legend(frameon=False, fontsize=8)
    ax3.grid(alpha=0.3, which='both')
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'iop_decomposition.png'), dpi=130)
    plt.close(fig)


def _fig_inflated_noise_examples(decs):
    """~4 GLORIA fits (inflated 5% noise floor), clear -> turbid, annotated with
    reduced chi^2 (inflated) and the noise-independent relative misfit."""
    if not decs:
        return
    n = len(decs)
    picks = sorted({0, n // 3, 2 * n // 3, n - 1})
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, j in zip(axes.ravel(), picks):
        d = decs[j]
        ax.plot(d['wave'], d['Rrs_obs'], 'k.', ms=3, label='observed')
        ax.plot(d['wave'], d['Rrs_mod'], color='#1b7837', lw=2,
                label='expb_pow (5% floor)')
        ax.set_title(f"{d['obs_id']} (peak {d['peak']:.0f} nm)  "
                     f"chi2_nu={d['chi2_nu']:.1f}  relerr={d['relerr']:.2f}",
                     fontsize=9)
        ax.set_xlabel('wavelength [nm]')
        ax.set_ylabel('Rrs [1/sr]')
        ax.legend(frameon=False, fontsize=8)
        ax.grid(alpha=0.3)
    for ax in axes.ravel()[len(picks):]:
        ax.axis('off')
    fig.suptitle('Inflated-noise (5% floor) expb_pow fits: clear -> turbid',
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'inflated_noise_examples.png'), dpi=130)
    plt.close(fig)


if __name__ == '__main__':
    main()

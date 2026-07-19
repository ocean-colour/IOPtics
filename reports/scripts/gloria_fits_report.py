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


def chisq_fit(spec, rec, maxfev=None, var_inflate=1.0):
    """Least-squares fit mirroring ``ioptics.run.fit_chisq`` but with a tunable
    ``curve_fit`` ``maxfev`` and an optional ``varRrs`` inflation.

    Returns ``(ans, models, rt_dict)`` or raises (curve_fit RuntimeError etc.).
    """
    _, models, rt = run._prepare(spec, rec)
    p0 = run.initial_guess(models, rec)
    bounds = run._prior_bounds(models)
    pf = partial(fit_func, models=models, rt_dict=rt)
    sigma = np.sqrt(np.asarray(rec.varRrs, dtype=float) * var_inflate)
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


def reduced_chisq(rec, models, rt, ans):
    """chi^2 / dof at the fitted parameters, using the record's own varRrs."""
    pred = model_rrs(models, rt, ans)
    obs = np.asarray(rec.Rrs, dtype=float)
    var = np.asarray(rec.varRrs, dtype=float)
    chi2 = float(np.sum((pred - obs) ** 2 / var))
    dof = max(obs.size - ans.size, 1)
    return chi2 / dof


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


if __name__ == '__main__':
    main()

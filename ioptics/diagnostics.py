"""Compute the data behind the diagnostic figures.

Taylor, Target, scatter, ratio-histogram, residual/closure spectra, corner, and
ΔBIC-CDF *figure data* — the numeric arrays each standard figure draws, so
``report``/``bokeh`` can render them statically or interactively (plotting lives
in :mod:`ioptics.plotting`/:mod:`ioptics.report`, not here).

Like :mod:`ioptics.metrics`, this module is **pure table-in/table-out**: it
consumes the persisted long/tidy results tables (``results_spectral`` /
``results_scalar``) and saved chain NPZs, and imports no BING/ocpy. The Taylor
and Target statistics, the scatter points and the ratio histograms are computed
in ``log10`` space (consistent with the multiplicative accuracy metrics), since
IOPs span orders of magnitude.

The accuracy diagnostics operate on a single ``component`` (and an optional
reference wavelength ``ref``, matched to the nearest native band within
:data:`ioptics.metrics.REF_TOL` nm); ``truth`` is the Taylor/Target reference
field and each ``algorithm`` is a test field.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ioptics import io, metrics


# --------------------------------------------------------------------------- #
# shared slicing / cleaning
# --------------------------------------------------------------------------- #

def _slice(table, component, ref=None, *, fit_method=None):
    """Filter a spectral table to one component (+ optional ref band/fit_method).

    With ``ref`` set, keeps — per dataset — the single native band nearest the
    target within :data:`ioptics.metrics.REF_TOL` nm (datasets with no band in
    tolerance contribute nothing).
    """
    df = table[table['component'] == component]
    if fit_method is not None:
        df = df[df['fit_method'] == fit_method]
    if ref is not None:
        keep = []
        for _, dsub in df.groupby('dataset'):
            native = np.unique(dsub['wavelength'].to_numpy(dtype=float))
            matched = metrics._nearest_within(native, ref)
            if matched is not None:
                keep.append(dsub[np.isclose(dsub['wavelength'], matched)])
        df = (pd.concat(keep, ignore_index=True) if keep
              else df.iloc[0:0])
    return df


def _clean_log(M, O):
    """Aligned, finite, strictly-positive ``(log10 M, log10 O)`` pair arrays."""
    M = np.asarray(M, dtype=float)
    O = np.asarray(O, dtype=float)
    keep = np.isfinite(M) & np.isfinite(O) & (M > 0) & (O > 0)
    return np.log10(M[keep]), np.log10(O[keep])


def _by_algo(df, value_col='value', truth_col='truth'):
    """Yield ``(algorithm, M, O)`` linear arrays per algorithm in ``df``."""
    for algo, g in df.groupby('algorithm', sort=False):
        yield algo, g[value_col].to_numpy(dtype=float), \
            g[truth_col].to_numpy(dtype=float)


# --------------------------------------------------------------------------- #
# §6 Taylor (Taylor 2001) + Target (Jolliff 2009)
# --------------------------------------------------------------------------- #

def taylor_stats(table, component, ref=None, *, fit_method=None):
    """Per-algorithm Taylor-diagram statistics (Taylor 2001), in log10 space.

    Returns a DataFrame with one row per ``algorithm``: ``corr`` (correlation
    with the truth field), ``std_model``/``std_ref`` (standard deviations),
    ``norm_std`` (= ``std_model/std_ref``), ``crmsd`` (centered RMS difference)
    and ``norm_crmsd`` (= ``crmsd/std_ref``), with the count ``n``. The three
    obey the Taylor identity ``crmsd² = std_model² + std_ref² −
    2·std_model·std_ref·corr``.
    """
    rows = []
    for algo, M, O in _by_algo(_slice(table, component, ref,
                                      fit_method=fit_method)):
        y, x = _clean_log(M, O)            # y = log model, x = log truth
        n = x.size
        if n < 2 or np.std(x) == 0 or np.std(y) == 0:
            rows.append({'algorithm': algo, 'corr': np.nan,
                         'std_model': np.nan, 'std_ref': np.nan,
                         'norm_std': np.nan, 'crmsd': np.nan,
                         'norm_crmsd': np.nan, 'n': int(n)})
            continue
        sr, sm = np.std(x), np.std(y)
        corr = np.corrcoef(y, x)[0, 1]
        crmsd = np.sqrt(np.mean(((y - y.mean()) - (x - x.mean())) ** 2))
        rows.append({'algorithm': algo, 'corr': float(corr),
                     'std_model': float(sm), 'std_ref': float(sr),
                     'norm_std': float(sm / sr), 'crmsd': float(crmsd),
                     'norm_crmsd': float(crmsd / sr), 'n': int(n)})
    return pd.DataFrame(rows)


def target_stats(table, component, ref=None, *, fit_method=None):
    """Per-algorithm Target-diagram statistics (Jolliff 2009), in log10 space.

    Returns a DataFrame with one row per ``algorithm``: ``bias`` (log-space mean
    difference ``mean(logM) − mean(logO)``), ``unbiased_rmsd`` (the centered
    RMSD), ``signed_unbiased_rmsd`` (the Target x-axis, signed by whether the
    model over/under-disperses: ``sign(std_model − std_ref)·unbiased_rmsd``),
    ``total_rmsd`` and ``n``.
    """
    rows = []
    for algo, M, O in _by_algo(_slice(table, component, ref,
                                      fit_method=fit_method)):
        y, x = _clean_log(M, O)
        n = x.size
        if n < 1:
            rows.append({'algorithm': algo, 'bias': np.nan,
                         'unbiased_rmsd': np.nan,
                         'signed_unbiased_rmsd': np.nan,
                         'total_rmsd': np.nan, 'n': 0})
            continue
        bias = y.mean() - x.mean()
        crmsd = np.sqrt(np.mean(((y - y.mean()) - (x - x.mean())) ** 2))
        sign = np.sign(np.std(y) - np.std(x))
        total = np.sqrt(np.mean((y - x) ** 2))
        rows.append({'algorithm': algo, 'bias': float(bias),
                     'unbiased_rmsd': float(crmsd),
                     'signed_unbiased_rmsd': float(sign * crmsd),
                     'total_rmsd': float(total), 'n': int(n)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# scatter + ratio histogram
# --------------------------------------------------------------------------- #

def scatter_data(table, component, ref=None, *, fit_method=None):
    """Retrieved-vs-true scatter points (+ 1:1, 3:1, 1:3 guides), linear space.

    Returns ``dict(points, guides, lims)``: ``points`` is a DataFrame
    ``(algorithm, x=truth, y=retrieved)`` of the finite, positive pairs;
    ``guides`` maps ``'one_to_one'``/``'three_to_one'``/``'one_to_three'`` to
    ``(x, y)`` line arrays spanning ``lims = (lo, hi)`` (the common data range).
    Plot on log-log axes.
    """
    df = _slice(table, component, ref, fit_method=fit_method)
    pts = []
    vals = []
    for algo, M, O in _by_algo(df):
        keep = np.isfinite(M) & np.isfinite(O) & (M > 0) & (O > 0)
        x, y = O[keep], M[keep]
        vals.append(x)
        vals.append(y)
        pts.append(pd.DataFrame({'algorithm': algo, 'x': x, 'y': y}))
    points = (pd.concat(pts, ignore_index=True) if pts
              else pd.DataFrame(columns=['algorithm', 'x', 'y']))
    allv = np.concatenate(vals) if vals else np.array([])
    if allv.size:
        lo, hi = float(allv.min()), float(allv.max())
    else:
        lo, hi = np.nan, np.nan
    line = np.array([lo, hi])
    guides = {'one_to_one': (line, line),
              'three_to_one': (line, 3.0 * line),
              'one_to_three': (line, line / 3.0)}
    return {'points': points, 'guides': guides, 'lims': (lo, hi)}


def ratio_hist_data(table, component, ref=None, *, fit_method=None,
                    edges=metrics.RATIO_EDGES):
    """Per-algorithm ratio-histogram counts over :data:`metrics.RATIO_EDGES`.

    Returns ``dict(edges, centers, counts)`` where ``counts`` is a DataFrame
    indexed by ``algorithm`` with one column per bucket (``len(edges)-1`` bins).
    ``centers`` are the geometric bucket centers (the open ``+inf`` edge uses the
    last finite edge as its representative).
    """
    edges = np.asarray(edges, dtype=float)
    df = _slice(table, component, ref, fit_method=fit_method)
    rows = {}
    for algo, M, O in _by_algo(df):
        rows[algo] = metrics.ratio_hist(M, O, edges=edges)
    counts = pd.DataFrame.from_dict(rows, orient='index')
    # geometric bucket centers; the open [.., +inf) bin uses its lower edge.
    right = np.where(np.isfinite(edges[1:]), edges[1:], edges[:-1])
    centers = np.sqrt(edges[:-1] * right)
    return {'edges': edges, 'centers': centers, 'counts': counts}


# --------------------------------------------------------------------------- #
# residual spectra + corner + ΔBIC CDF
# --------------------------------------------------------------------------- #

def residual_spectra(spectral, scalar, obs_id, *, dataset=None,
                     fit_method=None):
    """Rrs closure residuals (``Rrs_obs − Rrs_model``) for one observation.

    Returns ``dict`` keyed by algorithm, each ``dict(wave, residual, chi2_nu)``
    — the residual spectrum (1/sr) on the native grid and the χ²ᵥ annotation
    pulled from ``results_scalar``. Filters to ``obs_id`` (and ``dataset`` /
    ``fit_method`` if given).
    """
    sp = spectral[spectral['obs_id'] == obs_id]
    sc = scalar[scalar['obs_id'] == obs_id]
    if dataset is not None:
        sp = sp[sp['dataset'] == dataset]
        sc = sc[sc['dataset'] == dataset]
    if fit_method is not None:
        sp = sp[sp['fit_method'] == fit_method]
        sc = sc[sc['fit_method'] == fit_method]
    mod = sp[sp['component'] == 'Rrs_model']
    obs = sp[sp['component'] == 'Rrs_obs']
    out = {}
    for algo, gmod in mod.groupby('algorithm', sort=False):
        gobs = obs[obs['algorithm'] == algo]
        merged = gmod.merge(gobs, on=['dataset', 'obs_id', 'algorithm',
                                      'fit_method', 'wavelength'],
                            suffixes=('_mod', '_obs')).sort_values('wavelength')
        cn = sc[sc['algorithm'] == algo]['chi2_nu']
        out[algo] = {
            'wave': merged['wavelength'].to_numpy(dtype=float),
            'residual': (merged['value_obs'].to_numpy(dtype=float)
                         - merged['value_mod'].to_numpy(dtype=float)),
            'chi2_nu': float(cn.iloc[0]) if len(cn) else np.nan,
        }
    return out


def corner_data(chain_file):
    """Flattened posterior samples + labels from a saved chain NPZ.

    Loads the NPZ via :func:`ioptics.io.load_chain` and flattens ``chains``
    (``nsteps, nwalkers, nparam``) to ``(nsteps·nwalkers, nparam)``. Returns
    ``dict(samples, labels, Chl, Y)``. Parameter names are not persisted in the
    chain NPZ, so ``labels`` are generic (``'p0'``, ``'p1'``, …).
    """
    data = io.load_chain(chain_file)
    chains = np.asarray(data['chains'], dtype=float)
    if chains.ndim == 3:
        nsteps, nwalkers, nparam = chains.shape
        samples = chains.reshape(nsteps * nwalkers, nparam)
    else:
        samples = chains
        nparam = samples.shape[-1]
    return {'samples': samples,
            'labels': [f'p{i}' for i in range(nparam)],
            'Chl': float(data['Chl']) if 'Chl' in data else np.nan,
            'Y': float(data['Y']) if 'Y' in data else np.nan}


def dbic_cdf_data(scalar, a, b, *, by=None, fit_method='chisq'):
    """ΔBIC CDF curve(s) for the ``a`` vs ``b`` contest (thin wrapper).

    Delegates to :func:`ioptics.metrics.dbic_cdf`, returning its array dict
    (``dbic`` sorted, ``cdf``, ``n``, ``frac_favor_a``, ``frac_favor_b``); with
    ``by`` set, a ``{stratum: dict}`` mapping. Stratifiable for the per-S/N or
    per-sensor CDFs.
    """
    return metrics.dbic_cdf(scalar, a, b, by=by, fit_method=fit_method)

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


def rrs_fit_data(spectral, scalar, obs_id, *, dataset=None, fit_method=None):
    """Observed **and** modelled Rrs for one observation, with its fit numbers.

    :func:`residual_spectra` gives the *difference* between the two spectra and
    discards both absolutes, which is the right view for closure but the wrong one
    for an exemplar panel: a reader judging whether a fit is any good wants to see
    the model laid over the observation, in the shape the spectrum actually has.

    Returns ``dict(obs_id, wave, rrs, peak_nm, models)`` where ``models`` maps
    algorithm to ``dict(wave, rrs, chi2_nu, rel_misfit, status)``. ``peak_nm`` is
    the wavelength of the observed Rrs maximum — the clear→turbid ordering key
    (:data:`ioptics.records.RED_PEAK_NM` is the packaged threshold), and ``nan``
    when no observed spectrum was persisted. ``rel_misfit`` is recomputed here
    from the two spectra via :func:`ioptics.metrics.rel_misfit` because it is a
    per-fit quantity that is **not** on disk: ``metrics_scalar`` persists only its
    per-algorithm median.

    Unlike :func:`residual_spectra`, the ``chi2_nu``/``status`` lookup is filtered
    on ``dataset``/``fit_method`` as well as algorithm, so an unfiltered
    multi-dataset ``scalar`` cannot annotate a panel with another dataset's row.
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
    out = {'obs_id': obs_id, 'wave': np.array([], dtype=float),
           'rrs': np.array([], dtype=float), 'peak_nm': np.nan, 'models': {}}

    # The observation is the same spectrum whichever algorithm inverted it, but it
    # is stored once per algorithm; de-duplicate on wavelength so a four-algorithm
    # sweep does not draw the observed points four times over.
    if not obs.empty:
        o = (obs.drop_duplicates(subset='wavelength').sort_values('wavelength'))
        wave = o['wavelength'].to_numpy(dtype=float)
        rrs = o['value'].to_numpy(dtype=float)
        out['wave'], out['rrs'] = wave, rrs
        good = np.isfinite(rrs)
        if good.any():
            out['peak_nm'] = float(wave[good][int(np.argmax(rrs[good]))])

    for algo, gmod in mod.groupby('algorithm', sort=False):
        gobs = obs[obs['algorithm'] == algo]
        merged = gmod.merge(gobs, on=['dataset', 'obs_id', 'algorithm',
                                      'fit_method', 'wavelength'],
                            suffixes=('_mod', '_obs')).sort_values('wavelength')
        row = sc[sc['algorithm'] == algo]
        m = merged['value_mod'].to_numpy(dtype=float)
        o_ = merged['value_obs'].to_numpy(dtype=float)
        g = gmod.sort_values('wavelength')
        out['models'][str(algo)] = {
            'wave': g['wavelength'].to_numpy(dtype=float),
            'rrs': g['value'].to_numpy(dtype=float),
            'chi2_nu': (float(row['chi2_nu'].iloc[0])
                        if len(row) and 'chi2_nu' in row else np.nan),
            'rel_misfit': metrics.rel_misfit(m, o_) if m.size else np.nan,
            'status': (str(row['status'].iloc[0])
                       if len(row) and 'status' in row else ''),
        }
    return out


#: How many exemplar fits a page carries: best, worst, and the rest drawn from the
#: middle of the fit-quality distribution (Stage 7 Task 7 asks for 10).
EXEMPLAR_N = 10

#: The ``role`` values :func:`exemplar_obs` assigns, in fit-quality order.
EXEMPLAR_ROLES = ('best', 'median', 'worst')

#: What identifies one observation. ``obs_id`` alone does **not**: the package's own
#: multi-dataset convention reuses ids across datasets (``test_sweep_multi`` runs
#: ``obs in (0, 1)`` on all three), so grouping on ``obs_id`` alone silently pools
#: two unrelated spectra — it ranked every observation of a two-dataset sweep at the
#: median of an L23 fit (χ²ᵥ ≈ 1) and a GLORIA fit (χ²ᵥ ≈ 400).
OBS_KEYS = ('dataset', 'obs_id')

_EXEMPLAR_COLS = ['dataset', 'obs_id', 'role', 'chi2_nu', 'rel_misfit',
                  'peak_nm', 'fit_quality']


def _obs_keys(df):
    """The subset of :data:`OBS_KEYS` this frame actually carries."""
    return [k for k in OBS_KEYS if k in getattr(df, 'columns', ())]


def exemplar_obs(scalar, spectral=None, *, fit_method='chisq', n=EXEMPLAR_N,
                 statuses=None):
    """Pick the exemplar observations for a sweep: best, worst, and ``n-2`` median.

    Fit quality is ranked by **distance from χ²ᵥ = 1 in log space**,
    ``|log10(chi2_nu)|``, not by χ²ᵥ ascending. Ascending χ²ᵥ calls the *most
    over-fit* spectrum in the sweep the "best" one, and this package already names
    χ²ᵥ < 1 as over-fitting (``frac_overfit`` in the closure row) — on GLORIA, where
    the assumed error floor moved χ²ᵥ by 5x while the fits did not move at all, a
    χ²ᵥ of 0.01 is evidence about the noise model, not about the retrieval. Both
    tails are therefore "worse" than the middle, and each panel prints its own χ²ᵥ
    so the reader can see which tail it came from.

    Where several algorithms fit the same observation, the observation is ranked by
    the **median** χ²ᵥ across them: the panel shows every algorithm at once, so it
    is the observation, not one algorithm's fit, being chosen. "The same
    observation" means the same :data:`OBS_KEYS`, *not* the same ``obs_id``.

    Returns a DataFrame (:data:`OBS_KEYS`, ``role``, ``chi2_nu``, ``rel_misfit``,
    ``peak_nm``, ``fit_quality``) ordered **clear→turbid** by ``peak_nm`` when
    ``spectral`` carries ``Rrs_obs``, else by ``fit_quality`` ascending. Empty if
    nothing is rankable.
    """
    empty = pd.DataFrame(columns=_EXEMPLAR_COLS)
    if scalar is None or scalar.empty or 'chi2_nu' not in scalar.columns:
        return empty
    sub = scalar
    if fit_method is not None and 'fit_method' in sub.columns:
        sub = sub[sub['fit_method'] == fit_method]
    if statuses is not None and 'status' in sub.columns:
        sub = sub[sub['status'].isin(list(statuses))]
    sub = sub[np.isfinite(sub['chi2_nu'].to_numpy(dtype=float))
              & (sub['chi2_nu'] > 0)]
    if sub.empty:
        return empty

    keys = _obs_keys(sub)
    per_obs = (sub.groupby(keys, sort=False)['chi2_nu'].median().reset_index())
    per_obs['fit_quality'] = np.abs(np.log10(
        per_obs['chi2_nu'].to_numpy(dtype=float)))
    ranked = (per_obs.sort_values(['fit_quality'] + keys)
                     .reset_index(drop=True))

    idx, roles = _exemplar_slots(
        len(ranked), n, worst=_worst_slot(ranked))
    picked = ranked.iloc[idx].copy()
    picked['role'] = roles

    # per-observation relative misfit + Rrs peak, both derived from the spectra
    peaks, misfits = {}, {}
    if spectral is not None and not spectral.empty:
        sp = spectral
        if fit_method is not None and 'fit_method' in sp.columns:
            sp = sp[sp['fit_method'] == fit_method]
        wanted = set(map(tuple, picked[keys].to_numpy()))
        sp = sp[sp[keys].apply(tuple, axis=1).isin(wanted)] if not sp.empty else sp
        obs_rows = sp[sp['component'] == 'Rrs_obs']
        for kvals, g in obs_rows.groupby(keys, sort=False):
            g = g.drop_duplicates(subset='wavelength').sort_values('wavelength')
            wave = g['wavelength'].to_numpy(dtype=float)
            rrs = g['value'].to_numpy(dtype=float)
            good = np.isfinite(rrs)
            if good.any():
                key = kvals if isinstance(kvals, tuple) else (kvals,)
                peaks[key] = float(wave[good][int(np.argmax(rrs[good]))])
        misfits.update(_rel_misfit_per_obs(sp, keys=keys))

    rows = [tuple(r) for r in picked[keys].to_numpy()]
    picked['peak_nm'] = [peaks.get(r, np.nan) for r in rows]
    picked['rel_misfit'] = [misfits.get(r, np.nan) for r in rows]

    sort_key = 'peak_nm' if picked['peak_nm'].notna().any() else 'fit_quality'
    picked = picked.sort_values(sort_key, na_position='last')
    for missing in (c for c in _EXEMPLAR_COLS if c not in picked.columns):
        picked[missing] = np.nan
    return picked[_EXEMPLAR_COLS].reset_index(drop=True)


def _worst_slot(ranked):
    """Row position of the **largest χ²ᵥ** in a fit-quality-ranked frame.

    JXP's decision: the *selection* ranks by distance from χ²ᵥ = 1 (so the most
    over-fit spectrum is not published as the sweep's best fit), but the word
    **"worst" means the largest χ²ᵥ** — the most under-fit spectrum. Those differ
    whenever the over-fit tail reaches further from 1 than the under-fit one does
    (χ²ᵥ = 0.001 is 3 decades below 1, χ²ᵥ = 100 only 2 above), and "worst" pointing
    at an over-fit panel is not what the word conveys to a reader.
    """
    if ranked.empty:
        return None
    return int(np.argmax(ranked['chi2_nu'].to_numpy(dtype=float)))


def _exemplar_slots(total, n, *, worst=None):
    """``(indices, roles)`` into a fit-quality-ranked list of ``total`` entries.

    ``n`` is the number of panels wanted; the middle ``n - 2`` are taken from around
    the median so "median" means median rather than "whatever was left". Asking for
    fewer than three panels yields exactly that many (``n=1`` used to return *two*
    rows, since an empty middle range still left a best and a worst).

    ``worst`` is the row position to label ``'worst'`` — :func:`_worst_slot`'s
    largest-χ²ᵥ row rather than simply the last rank. It is ``None`` for callers that
    want the last rank.
    """
    n = max(0, int(n))
    if total <= 0 or n == 0:
        return [], []
    if n == 1:
        return [0], ['best']
    if worst is None or not 0 <= worst < total:
        worst = total - 1
    if worst == 0:                      # a degenerate sweep: one χ²ᵥ for everything
        worst = total - 1
    if total <= n:
        idx = list(range(total))
        roles = ['median'] * total
        roles[0] = 'best'
        if total >= 2:
            roles[worst] = 'worst'
        return idx, roles
    # the middle n-2, taken around the median and never reusing best or worst
    n_mid = n - 2
    mid = total // 2
    start = min(max(1, mid - n_mid // 2), total - 1 - n_mid)
    middle = [i for i in range(start, start + n_mid) if i not in (0, worst)]
    for i in range(1, total - 1):       # backfill if worst fell inside the window
        if len(middle) >= n_mid:
            break
        if i not in middle and i not in (0, worst):
            middle.append(i)
    middle = sorted(middle)[:n_mid]
    return ([0] + middle + [worst],
            ['best'] + ['median'] * len(middle) + ['worst'])


def _rel_misfit_per_obs(spectral, *, keys=None):
    """``{obs key: median relative misfit across algorithms}`` from the Rrs rows."""
    need = {'Rrs_model', 'Rrs_obs'}
    if not need <= set(spectral.get('component', pd.Series(dtype=str))):
        return {}
    keys = list(keys) if keys else _obs_keys(spectral)
    fit_keys = keys + [k for k in ('algorithm', 'fit_method')
                       if k in spectral.columns]
    cols = fit_keys + ['wavelength', 'value']
    mod = spectral[spectral['component'] == 'Rrs_model'][cols]
    obs = (spectral[spectral['component'] == 'Rrs_obs'][cols]
           .rename(columns={'value': 'obs'}))
    both = mod.merge(obs, on=fit_keys + ['wavelength'])
    if both.empty:
        return {}
    out = {}
    for kvals, g in both.groupby(fit_keys, sort=False):
        kvals = kvals if isinstance(kvals, tuple) else (kvals,)
        obs_key = kvals[:len(keys)]
        out.setdefault(obs_key, []).append(metrics.rel_misfit(
            g['value'].to_numpy(dtype=float), g['obs'].to_numpy(dtype=float)))
    return {k: float(np.nanmedian(v)) if np.isfinite(v).any() else np.nan
            for k, v in out.items()}


def accuracy_spectrum_data(metrics_spectral, component, *, metric='mae',
                           dataset=None, fit_method='chisq', stratum='all',
                           min_n=1):
    """Accuracy **as a function of wavelength**, per algorithm, for one component.

    ``metrics_spectral`` already carries one row per
    ``(dataset, algorithm, fit_method, stratum, component, wavelength)`` — the whole
    table was computed and persisted but never read by the report layer, so the
    figure an ocean-colour reader looks for first (how a retrieval's error varies
    across the spectrum) was not being drawn from data we already had.

    Returns ``dict(component, metric, series, perfect)`` where ``series`` maps
    algorithm to ``dict(wave, value, n)`` sorted by wavelength, and ``perfect`` is
    the metric's perfect value (0 for the multiplicative errors, 1 for
    ``median_ratio``) so the panel can draw the right reference line. Rows with
    ``n < min_n`` or a non-finite metric are dropped: a band nobody scored must not
    be drawn as a point at zero error.
    """
    out = {'component': component, 'metric': metric, 'series': {},
           'perfect': metrics.perfect_value(metric)}
    ms = metrics_spectral
    if ms is None or getattr(ms, 'empty', True):
        return out
    need = {'component', 'wavelength', 'algorithm', metric}
    if not need <= set(ms.columns):
        return out
    sub = ms[ms['component'] == component]
    if dataset is not None and 'dataset' in sub.columns:
        sub = sub[sub['dataset'] == dataset]
    if fit_method is not None and 'fit_method' in sub.columns:
        sub = sub[sub['fit_method'] == fit_method]
    if stratum is not None and 'stratum' in sub.columns:
        sub = sub[sub['stratum'] == stratum]
    if 'n' in sub.columns:
        sub = sub[sub['n'].fillna(0) >= min_n]
    sub = sub[np.isfinite(sub[metric].to_numpy(dtype=float))]
    if sub.empty:
        return out
    for algo, g in sub.groupby('algorithm', sort=True):
        g = g.sort_values('wavelength')
        out['series'][str(algo)] = {
            'wave': g['wavelength'].to_numpy(dtype=float),
            'value': g[metric].to_numpy(dtype=float),
            'n': (g['n'].to_numpy(dtype=float) if 'n' in g
                  else np.full(len(g), np.nan)),
        }
    return out


def scored_components(metrics_spectral, *, dataset=None, fit_method='chisq',
                      stratum='all', metric='mae', min_waves=1):
    """Components whose accuracy varies over enough bands to plot, best-covered first.

    Returns ``[(component, n_waves, n_algos)]``. ``min_waves`` is the point of it: a
    component scored at a *single* wavelength cannot show a spectral shape, so
    plotting it as one lone marker per algorithm invites a reader to see a trend
    that is not there.
    """
    ms = metrics_spectral
    if ms is None or getattr(ms, 'empty', True):
        return []
    if not {'component', 'wavelength', 'algorithm', metric} <= set(ms.columns):
        return []
    sub = ms
    if dataset is not None and 'dataset' in sub.columns:
        sub = sub[sub['dataset'] == dataset]
    if fit_method is not None and 'fit_method' in sub.columns:
        sub = sub[sub['fit_method'] == fit_method]
    if stratum is not None and 'stratum' in sub.columns:
        sub = sub[sub['stratum'] == stratum]
    if 'n' in sub.columns:
        sub = sub[sub['n'].fillna(0) > 0]
    sub = sub[np.isfinite(sub[metric].to_numpy(dtype=float))]
    if sub.empty:
        return []
    agg = sub.groupby('component').agg(n_waves=('wavelength', 'nunique'),
                                       n_algos=('algorithm', 'nunique'))
    agg = agg[agg['n_waves'] >= int(min_waves)]
    agg = agg.sort_values(['n_waves', 'n_algos'], ascending=False)
    return [(str(c), int(r.n_waves), int(r.n_algos)) for c, r in agg.iterrows()]


def corner_data(chain_file):
    """Flattened posterior samples + labels from a saved chain NPZ.

    Loads the NPZ via :func:`ioptics.io.load_chain` and flattens ``chains``
    (``nsteps, nwalkers, nparam``) to ``(nsteps·nwalkers, nparam)``. Returns
    ``dict(samples, labels, Chl, Y)``. ``labels`` are the persisted ``pnames``
    when present, else generic (``'p0'``, ``'p1'``, …).
    """
    data = io.load_chain(chain_file)
    chains = np.asarray(data['chains'], dtype=float)
    if chains.ndim == 3:
        nsteps, nwalkers, nparam = chains.shape
        samples = chains.reshape(nsteps * nwalkers, nparam)
    else:
        samples = chains
        nparam = samples.shape[-1]
    pnames = [str(p) for p in data['pnames']] if 'pnames' in data else []
    labels = pnames if len(pnames) == nparam else [f'p{i}' for i in range(nparam)]
    return {'samples': samples, 'labels': labels,
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

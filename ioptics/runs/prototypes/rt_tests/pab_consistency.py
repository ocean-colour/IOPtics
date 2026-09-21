"""RT-B consistency check against PAB's stored ``run1k`` fits (rt_tests task 13).

The 100 PACE spectra in sweep ``rt_tests_B_v1`` are the very pixels PAB fitted
in its ``run1k`` development run with BING's ``ExpBPow`` under the **Gordon**
elastic forward model.  IOPtics refit them under ``robust_hybrid`` elastic
(``expb_pow_hyb_el``) with one extra free parameter, ``B_p``.  If the two
pipelines agree on the shared parameters to within what an elastic-model swap
plus a free ``B_p`` can move them, the RT-B arm is standing on the same data
PAB published from; if they do not, something upstream (window, weights,
spectrum, priors) differs and every PACE number on the ladder page is suspect.

What is compared, per pixel
---------------------------
* the observed spectrum and its variance handed to each fitter
  (``obs_Rrs``/``Rrs`` and ``varRrs``; both pipelines claim 400–700 nm, the
  136-band OCI grid with the 588–613 nm gap) — max absolute difference;
* the posterior **medians** of the five shared parameters ``Adg``, ``Sdg``,
  ``Aph``, ``Bnw``, ``beta`` (``Adg``, ``Aph`` and ``Bnw`` are log10 amplitudes
  in BING; ``Sdg`` and ``beta`` are linear), from post-burn chains on both sides
  (PAB stores its production chain after ``run_emcee`` discarded the burn-in;
  IOPtics stores the thinned production chain with its own burn discarded);
* the derived chlorophyll, ``Chl = 10**Aph / 0.05582`` (Bricaud a*_ph at
  440 nm; the same formula on both sides, so the ratio is exactly
  ``10**(Aph_ours - Aph_pab)``).

Summary statistics across pixels: Pearson correlation of the medians,
median and 16–84 % span of the difference (ours − PAB), and for Chl the
median and span of the ratio plus the log10 correlation.  The check is a
sanity gate, not a result: it says the same spectra were fitted and that the
answers differ by what the physics swap predicts (``robust_hybrid`` sits
1.4–3.7 % above Gordon in Rrs on L23), nothing more.

Usage
-----
::

    python pab_consistency.py [--sweep rt_tests_B_v1] [--rung expb_pow_hyb_el]
                              [--pab-run $OS_COLOR/PAB/run1k]

Writes ``tables/pab_consistency.csv`` (one row per pixel) and
``tables/pab_consistency_summary.csv`` (one row per compared quantity) under
the sweep dir; the RT-ladder page picks the summary up when it exists.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

#: Parameters shared by PAB's ``ExpBPow`` (Gordon) and the RT rung; chain order
#: on the PAB side is exactly this, on the IOPtics side this plus ``B_p``.
SHARED = ('Adg', 'Sdg', 'Aph', 'Bnw', 'beta')

#: Which of the shared parameters BING fits in log10.
LOG10 = {'Adg': True, 'Sdg': False, 'Aph': True, 'Bnw': True, 'beta': False}

#: Bricaud a*_ph(440) for Chl = 1 mg m^-3 — BING's ``Chl = 10**Aph / 0.05582``.
APH_STAR_440 = 0.05582


def _medians(chains, names):
    """Posterior medians per named parameter from a ``(nstep, nwalker, nparam)`` chain."""
    flat = np.asarray(chains, dtype=float).reshape(-1, np.asarray(chains).shape[-1])
    return {str(n): float(np.median(flat[:, i])) for i, n in enumerate(names)}


def compare_pixel(ours, theirs):
    """One row of the per-pixel table from two loaded NPZ dicts.

    ``ours`` is an IOPtics chain NPZ (``chains``, ``pnames``, ``obs_Rrs``,
    ``varRrs``), ``theirs`` a PAB run1k NPZ (``chains``, ``param_names``,
    ``Rrs``, ``varRrs``).  Spectra are compared on the bands both carry.
    """
    m_ours = _medians(ours['chains'], [str(p) for p in ours['pnames']])
    m_pab = _medians(theirs['chains'], [str(p) for p in theirs['param_names']])
    row = {}
    w_o, w_p = np.asarray(ours['wave'], float), np.asarray(theirs['wave'], float)
    common = np.intersect1d(np.round(w_o, 3), np.round(w_p, 3))
    io_ = np.isin(np.round(w_o, 3), common)
    ip_ = np.isin(np.round(w_p, 3), common)
    row['n_bands_ours'] = int(w_o.size)
    row['n_bands_pab'] = int(w_p.size)
    row['n_bands_common'] = int(common.size)
    row['max_abs_dRrs'] = float(np.nanmax(np.abs(
        np.asarray(ours['obs_Rrs'], float)[io_] - np.asarray(theirs['Rrs'], float)[ip_])))
    row['max_abs_dvarRrs'] = float(np.nanmax(np.abs(
        np.asarray(ours['varRrs'], float)[io_] - np.asarray(theirs['varRrs'], float)[ip_])))
    for p in SHARED:
        row[f'{p}_ours'] = m_ours.get(p, np.nan)
        row[f'{p}_pab'] = m_pab.get(p, np.nan)
        row[f'{p}_diff'] = row[f'{p}_ours'] - row[f'{p}_pab']
    row['B_p_ours'] = m_ours.get('B_p', np.nan)
    row['Chl_ours'] = 10 ** m_ours['Aph'] / APH_STAR_440 if 'Aph' in m_ours else np.nan
    row['Chl_pab'] = 10 ** m_pab['Aph'] / APH_STAR_440 if 'Aph' in m_pab else np.nan
    row['Chl_ratio'] = row['Chl_ours'] / row['Chl_pab']
    return row


def summarise(per_pixel):
    """Across-pixel summary: one row per compared quantity."""
    df = pd.DataFrame(per_pixel) if not isinstance(per_pixel, pd.DataFrame) else per_pixel
    rows = []
    for p in SHARED:
        a, b = df[f'{p}_ours'].to_numpy(float), df[f'{p}_pab'].to_numpy(float)
        ok = np.isfinite(a) & np.isfinite(b)
        d = (a - b)[ok]
        rows.append({
            'quantity': p, 'scale': 'log10' if LOG10[p] else 'linear',
            'n': int(ok.sum()),
            'correlation': float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() > 2 else np.nan,
            'median_diff': float(np.median(d)) if d.size else np.nan,
            'p16_diff': float(np.percentile(d, 16)) if d.size else np.nan,
            'p84_diff': float(np.percentile(d, 84)) if d.size else np.nan,
            'median_abs_diff': float(np.median(np.abs(d))) if d.size else np.nan,
        })
    r = df['Chl_ratio'].to_numpy(float)
    lo = np.log10(df['Chl_ours'].to_numpy(float))
    lp = np.log10(df['Chl_pab'].to_numpy(float))
    ok = np.isfinite(r) & (r > 0) & np.isfinite(lo) & np.isfinite(lp)
    rows.append({
        'quantity': 'Chl (derived, ours/PAB)', 'scale': 'ratio', 'n': int(ok.sum()),
        'correlation': float(np.corrcoef(lo[ok], lp[ok])[0, 1]) if ok.sum() > 2 else np.nan,
        'median_diff': float(np.median(r[ok])) if ok.any() else np.nan,
        'p16_diff': float(np.percentile(r[ok], 16)) if ok.any() else np.nan,
        'p84_diff': float(np.percentile(r[ok], 84)) if ok.any() else np.nan,
        'median_abs_diff': np.nan,
    })
    rows.append({
        'quantity': 'observed Rrs handed to the fitters', 'scale': 'sr^-1',
        'n': int(df['max_abs_dRrs'].notna().sum()), 'correlation': np.nan,
        'median_diff': float(df['max_abs_dRrs'].max()), 'p16_diff': np.nan,
        'p84_diff': np.nan, 'median_abs_diff': float(df['max_abs_dvarRrs'].max()),
    })
    return pd.DataFrame(rows)


def run(sweep_dir, pab_run, *, rung='expb_pow_hyb_el', dataset='PACE'):
    """Match every ``<rung>_<dataset>_<stem>.npz`` chain to ``<pab_run>/fit_chains/<stem>.npz``."""
    sweep_dir, pab_run = Path(sweep_dir), Path(pab_run)
    prefix = f'{rung}_{dataset}_'
    rows, missing = [], []
    for path in sorted((sweep_dir / 'chains').glob(f'{prefix}*.npz')):
        stem = path.name[len(prefix):-len('.npz')]
        theirs_path = pab_run / 'fit_chains' / f'{stem}.npz'
        if not theirs_path.is_file():
            missing.append(stem)
            continue
        with np.load(path, allow_pickle=False) as ours, \
                np.load(theirs_path, allow_pickle=False) as theirs:
            row = compare_pixel(ours, theirs)
        row = {'obs_id': stem, **row}
        rows.append(row)
    per_pixel = pd.DataFrame(rows)
    summary = summarise(per_pixel) if not per_pixel.empty else pd.DataFrame()
    tables = sweep_dir / 'tables'
    tables.mkdir(parents=True, exist_ok=True)
    per_pixel.to_csv(tables / 'pab_consistency.csv', index=False)
    summary.round(4).to_csv(tables / 'pab_consistency_summary.csv', index=False)
    return per_pixel, summary, missing


def _cli(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    os_color = os.environ.get('OS_COLOR', '.')
    p.add_argument('--sweep', default='rt_tests_B_v1')
    p.add_argument('--rung', default='expb_pow_hyb_el')
    p.add_argument('--pab-run', default=os.path.join(os_color, 'PAB', 'run1k'))
    a = p.parse_args(argv)
    from ioptics import io
    sweep_dir = io.sweep_dir(a.sweep)
    per_pixel, summary, missing = run(sweep_dir, a.pab_run, rung=a.rung)
    print(f'{len(per_pixel)} pixels matched, {len(missing)} without a PAB chain')
    if missing:
        print('  missing:', ', '.join(missing[:5]), '...' if len(missing) > 5 else '')
    with pd.option_context('display.width', 200, 'display.max_columns', 20):
        print(summary.round(4).to_string(index=False))
    print(f"wrote {sweep_dir / 'tables' / 'pab_consistency.csv'} and _summary.csv")


if __name__ == '__main__':
    _cli()

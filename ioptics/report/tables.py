"""Accuracy / QC summary tables for the standard report.

Pure column selects/group-bys over the **wide** metrics tables (no re-fitting):
``tables.accuracy`` folds the ref-band §1 accuracy (``metrics_scalar``) together
with the head-to-head ``win_frac`` (``metrics_pairwise``); ``tables.qc`` folds
the non-solution rate (``results_scalar.status``) together with the §2 closure
fractions (``metrics_scalar`` ``component='Rrs'`` rows). Each returns a tidy
``DataFrame`` and writes a CSV alongside the figures in ``runs/<sweep_id>/figures/``.
"""

from __future__ import annotations

from ioptics import metrics
from ioptics.report import figures

# Accuracy columns surfaced per (algorithm, component, ref_wave).
_ACC_COLS = ['n', 'bias', 'abs_bias', 'mae', 'rms_log', 'median_ratio',
             'coverage68', 'coverage95', 'mae_rank', 'abs_bias_rank',
             'rms_log_rank']


def _require(df, what):
    if df is None:
        raise FileNotFoundError(
            f'{what} not found — run metrics.compute(sweep_id) first')
    return df


def accuracy(sweep, *, fit_method='chisq', stratum='all', root=None,
             write=True):
    """Per-(algorithm, component, ref-λ) accuracy + wins table.

    Ref-band §1 accuracy rows from ``metrics_scalar`` (spectral components with a
    matched ``ref_wave``) joined to ``win_frac`` from the ``metrics_pairwise``
    ``wins`` rows. Filtered to one ``fit_method`` and ``stratum``. Writes
    ``accuracy_<fit_method>_<stratum>.csv`` when ``write``; returns the DataFrame.
    """
    sweep = figures._resolve(sweep, root)
    ms = _require(sweep.metrics_scalar, 'metrics_scalar')
    acc = ms[(ms['fit_method'] == fit_method) & (ms['stratum'] == stratum)
             & ms['component'].isin(metrics.ACCURACY_COMPONENTS)
             & ms['ref_wave'].notna()].copy()
    keep = ['algorithm', 'component', 'ref_wave', 'ref_match', 'caveat']
    keep += [c for c in _ACC_COLS if c in acc.columns]
    acc = acc[keep]

    pw = sweep.metrics_pairwise
    if pw is not None and 'contest' in pw.columns:
        wins = pw[(pw['contest'] == 'wins') & (pw['fit_method'] == fit_method)
                  & (pw['stratum'] == stratum)]
        if not wins.empty:
            acc = acc.merge(
                wins[['algorithm', 'component', 'ref_wave', 'win_frac']],
                on=['algorithm', 'component', 'ref_wave'], how='left')

    acc = acc.sort_values(['component', 'ref_wave', 'algorithm']) \
             .reset_index(drop=True)
    if write:
        out = figures._figdir(sweep) / f'accuracy_{fit_method}_{stratum}.csv'
        acc.to_csv(out, index=False)
    return acc


def qc(sweep, *, fit_method='chisq', stratum='all', root=None, write=True):
    """Per-algorithm QC summary: non-solution rate + §2 closure fractions.

    ``frac_not_ok`` is the fraction of ``results_scalar`` rows whose ``status``
    is not ``'ok'`` (fit failures / QC flags); the closure fractions
    (``frac_good``, ``frac_fit_noise``, ``frac_qc_fail``, ``chi2_nu_median``)
    come from the ``metrics_scalar`` ``component='Rrs'`` rows. Writes
    ``qc_<fit_method>_<stratum>.csv`` when ``write``; returns the DataFrame.
    """
    sweep = figures._resolve(sweep, root)
    sc = sweep.scalar[sweep.scalar['fit_method'] == fit_method]
    not_ok = (sc.assign(_bad=sc['status'].ne('ok'))
                .groupby('algorithm')['_bad'].mean()
                .rename('frac_not_ok').reset_index())

    ms = _require(sweep.metrics_scalar, 'metrics_scalar')
    closure = ms[(ms['fit_method'] == fit_method) & (ms['stratum'] == stratum)
                 & (ms['component'] == 'Rrs')]
    cols = [c for c in ('algorithm', 'chi2_nu_median', 'frac_good',
                        'frac_fit_noise', 'frac_qc_fail') if c in closure.columns]
    out = not_ok.merge(closure[cols], on='algorithm', how='left') \
                .sort_values('algorithm').reset_index(drop=True)
    if write:
        path = figures._figdir(sweep) / f'qc_{fit_method}_{stratum}.csv'
        out.to_csv(path, index=False)
    return out

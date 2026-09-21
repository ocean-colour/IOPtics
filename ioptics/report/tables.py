"""Accuracy / QC summary tables for the standard report.

Pure column selects/group-bys over the **wide** metrics tables (no re-fitting):
``tables.accuracy`` folds the ref-band §1 accuracy (``metrics_scalar``) together
with the head-to-head ``win_frac`` (``metrics_pairwise``); ``tables.qc`` folds
the non-solution rate (``results_scalar.status``) together with the §2 closure
fractions (``metrics_scalar`` ``component='Rrs'`` rows). Each returns a tidy
``DataFrame`` and writes a CSV alongside the figures in ``runs/<sweep_id>/figures/``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ioptics import metrics, records
from ioptics.report import figures

# Accuracy columns surfaced per (dataset, algorithm, component, ref_wave).
_ACC_COLS = ['n', 'bias', 'abs_bias', 'mae', 'rms_log', 'median_ratio',
             'coverage68', 'coverage95', 'coverage_n', 'mae_rank',
             'abs_bias_rank', 'rms_log_rank']

#: The contest key. ``dataset`` leads: without it a multi-dataset sweep
#: row-multiplies on the wins join and cross-assigns one dataset's win fraction to
#: another's rows (reproduced: 352 rows where 320 were expected).
_CONTEST_KEY = ['dataset', 'algorithm', 'component', 'ref_wave']

#: Published decimals. The CSVs carried full float64 (`0.09642020657366057`,
#: ranks as `2.0`, wavelengths as `440.0`), which renders as an unreadable,
#: horizontally overflowing table.
_ROUND = 4

#: Nominal coverage per level — the value a *calibrated* uncertainty would hit.
#: Aliased from :mod:`ioptics.metrics` so the tables' verdicts and the figures'
#: reference lines cannot drift apart.
NOMINAL_COVERAGE = metrics.NOMINAL_COVERAGE

#: How many binomial standard errors a coverage may miss its nominal target by
#: before the table flags it. 2σ ≈ 95% confidence that the miss is real, so a
#: thin-`n` contest is not accused of being mis-calibrated on noise alone.
COVERAGE_MISS_SIGMA = 2.0


def _require(df, what):
    if df is None:
        raise FileNotFoundError(
            f'{what} not found — run metrics.compute(sweep_id) first')
    return df


#: Columns that are counts or bands, not measurements — printed as integers.
_INT_LIKE = ('n_pairs', 'n_scored', 'n_attempted', 'n', 'n_paired',
             'coverage_n', 'ref_wave', 'ref_match',
             'mae_rank', 'abs_bias_rank', 'rms_log_rank', 'win_frac_rank', 'rank')


def _publishable(df):
    """Round floats and print counts/bands as integers, for a readable table.

    Cosmetic, but the tables are the page: full float64 (`0.09642020657366057`)
    across 17 columns overflows the page horizontally, and a rank of `2.0` or a
    wavelength of `440.0` reads as sloppy.
    """
    out = df.copy()
    for col in out.columns:
        vals = out[col]
        if col in _INT_LIKE and vals.dtype.kind in 'fiu':
            # Only present as an integer when the values *are* integral. A band
            # centre of 442.5 nm (a half-nm sensor grid) must not be published as
            # 442 — and ``astype('Int64')`` on a non-integral value with an NA
            # present raises, which would abort the whole page build.
            finite = vals.dropna()
            if finite.empty or ((finite % 1) == 0).all():
                out[col] = vals.astype('Int64')
                continue
        if vals.dtype.kind == 'f':
            out[col] = vals.round(_ROUND)
    return out


def _coverage_flags(df):
    """Add a ``coverage68_verdict`` / ``coverage95_verdict`` against nominal.

    Coverage is the one metric on these tables whose perfect value is **not** 0:
    a calibrated 68% interval contains truth 68% of the time. An algorithm can be
    the most accurate *and* badly over-confident — on the L23 smoke, ``giop`` won
    85% of head-to-head contests at a(440) while its 68%/95% intervals held truth
    only 45%/65% of the time — so the table states the target and says which way a
    real miss goes, instead of leaving the reader to compare two bare numbers.

    The verdict is a **word, not a boolean**, for two reasons. The direction is the
    finding (``over-confident`` intervals are too narrow, ``conservative`` too
    wide). And a boolean ``True`` invites reading "well calibrated" when all it can
    mean is *not distinguishable from nominal at this* ``n``: the test is
    :data:`COVERAGE_MISS_SIGMA` binomial standard errors, so at ``n=12`` only a
    coverage68 outside ``[0.41, 0.95]`` is flagged at all, while at ``n=3320`` the
    window narrows to ``[0.66, 0.70]``. ``consistent`` is therefore a statement
    about the evidence, not a certificate. ``NA`` = nothing was scored.

    The standard error uses **``coverage_n``** — the trials coverage was actually
    measured over (:func:`ioptics.metrics.coverage_n`), which is a different
    population from the accuracy row's ``n``: coverage needs ``truth`` and both
    bounds and ignores the retrieved value, so a fit whose covariance failed has
    bounds for fewer rows. Testing a k-trial proportion with an n-trial standard
    error would make it too tight by ``sqrt(n/k)`` and could accuse a thin contest
    of mis-calibration. (``n`` is the fallback for a sweep whose metrics predate the
    ``coverage_n`` column.)
    """
    for col, nominal in NOMINAL_COVERAGE.items():
        if col not in df.columns:
            continue
        emp = df[col].astype(float)
        # The number of trials coverage was actually measured over — NOT the
        # accuracy row's ``n``, which counts finite-and-positive (retrieved,
        # truth) pairs and can exceed the rows that had credible bounds.
        for cand in ('coverage_n', 'n'):
            if cand in df.columns:
                n = df[cand].astype(float)
                break
        else:
            n = pd.Series(np.nan, index=df.index)
        se = (nominal * (1.0 - nominal) / n) ** 0.5
        verdict = pd.Series('consistent', index=df.index, dtype=object)
        verdict[emp < nominal - COVERAGE_MISS_SIGMA * se] = 'over-confident'
        verdict[emp > nominal + COVERAGE_MISS_SIGMA * se] = 'conservative'
        df[f'{col}_verdict'] = verdict.where(emp.notna() & (n > 0))
    return df


_RANK_COLS = ('mae_rank', 'abs_bias_rank', 'rms_log_rank')


def _blank_tied_ranks(acc, sweep, *, fit_method='chisq', stratum='all'):
    """Replace ranks with ``NA`` + a ``ranking`` note where no pair is separable.

    Returns ``(table, n_tied_contests)``. The pairwise verdicts
    (:func:`ioptics.metrics.head_to_head`, persisted as ``contest='pair'``) are the
    authority: if no pair in a contest resolves to a winner, a 1..N ordering of that
    contest is noise dressed as a standing.
    """
    if acc.empty:
        return acc, 0
    pw = getattr(sweep, 'metrics_pairwise', None)
    out = acc.copy()
    out['ranking'] = 'ranked'
    if pw is None or 'contest' not in getattr(pw, 'columns', []):
        return out, 0
    pairs = pw[(pw['contest'] == 'pair') & (pw['fit_method'] == fit_method)
               & (pw['stratum'] == stratum)]
    if pairs.empty:
        return out, 0
    key = [c for c in ('dataset', 'component', 'ref_wave') if c in pairs.columns
           and c in out.columns]
    n_tied = 0
    for kvals, grp in pairs.groupby(key, sort=False):
        decided = grp['verdict'].isin(set(grp['model_a']) | set(grp['model_b']))
        if decided.any() or grp['n_paired'].fillna(0).le(0).all():
            continue
        sel = pd.Series(True, index=out.index)
        for col, val in zip(key, kvals if isinstance(kvals, tuple) else (kvals,)):
            sel &= out[col] == val
        if not sel.any():
            continue
        n_tied += 1
        for col in _RANK_COLS:
            if col in out.columns:
                out.loc[sel, col] = np.nan
        out.loc[sel, 'ranking'] = 'indistinguishable'
    return out, n_tied


def accuracy(sweep, *, fit_method='chisq', stratum='all', root=None,
             write=True, drop_unscored=True):
    """Per-(algorithm, component, ref-λ) accuracy + wins table.

    Ref-band §1 accuracy rows from ``metrics_scalar`` (spectral components with a
    matched ``ref_wave``) joined to ``win_frac`` from the ``metrics_pairwise``
    ``wins`` rows. Filtered to one ``fit_method`` and ``stratum``. Writes
    ``accuracy_<fit_method>_<stratum>.csv`` when ``write``; returns the DataFrame.

    Keyed on :data:`_CONTEST_KEY` — **``dataset`` included**. The column is both
    carried into the output and used in the wins join: without it a multi-dataset
    sweep silently row-multiplies and hands one dataset's ``win_frac`` to another's
    rows, and no column tells the reader which dataset a row describes.

    ``n`` is renamed **``n_pairs``**: it counts surviving *(retrieved, truth)*
    pairs after the positivity/NaN intersection, which is a different number from
    the spectra scored (``n_scored`` in :func:`qc`) and from the spectra attempted
    (``n_attempted``). On the first GLORIA sweep those three were 12, 21 and 100 for
    the same contest, all previously published as some flavour of "n".
    """
    sweep = figures.resolve(sweep, root)
    ms = _require(sweep.metrics_scalar, 'metrics_scalar')
    acc = ms[(ms['fit_method'] == fit_method) & (ms['stratum'] == stratum)
             & ms['component'].isin(metrics.ACCURACY_COMPONENTS)
             & ms['ref_wave'].notna()].copy()
    keep = [c for c in _CONTEST_KEY if c in acc.columns]
    keep += [c for c in ('ref_match', 'caveat') if c in acc.columns]
    keep += [c for c in _ACC_COLS if c in acc.columns]
    acc = acc[keep]
    acc = _coverage_flags(acc)

    pw = sweep.metrics_pairwise
    if pw is not None and 'contest' in pw.columns:
        wins = pw[(pw['contest'] == 'wins') & (pw['fit_method'] == fit_method)
                  & (pw['stratum'] == stratum)]
        if not wins.empty:
            on = [c for c in _CONTEST_KEY if c in wins.columns and c in acc.columns]
            acc = acc.merge(wins[on + ['win_frac']], on=on, how='left')

    sort_by = [c for c in ('dataset', 'component', 'ref_wave', 'algorithm')
               if c in acc.columns]
    acc = acc.sort_values(sort_by).reset_index(drop=True)
    acc = acc.rename(columns={'n': 'n_pairs'})

    # Rows with nothing scored behind them are the table equivalent of a blank
    # figure panel — on the first GLORIA report 36 of 40 rows were all-NaN,
    # because that dataset has spectral truth for one component only. Drop them
    # and record the count so the page can say how many, rather than either
    # publishing empty rows or hiding them silently.
    n_unscored = 0
    if drop_unscored and 'n_pairs' in acc.columns:
        unscored = acc['n_pairs'].fillna(0) <= 0
        n_unscored = int(unscored.sum())
        acc = acc[~unscored].reset_index(drop=True)

    # A contest whose every pairwise verdict is a tie has no ranking to publish.
    # Printing mae_rank 1-4 beside a head-to-head table that says "these are
    # indistinguishable" is the same page contradicting itself — and on the GLORIA
    # sweep the two rank columns did not even agree on who was first.
    acc, n_tied = _blank_tied_ranks(acc, sweep, fit_method=fit_method,
                                    stratum=stratum)

    acc = _publishable(acc)
    acc.attrs['n_unscored_rows'] = n_unscored
    acc.attrs['n_tied_contests'] = n_tied
    if write:
        out = figures.subdir(sweep, 'tables') \
            / f'accuracy_{fit_method}_{stratum}.csv'
        acc.to_csv(out, index=False)
    return acc


def head_to_head(sweep, *, fit_method='chisq', stratum='all', root=None,
                 write=True, drop_unscored=True):
    """Per-pair head-to-head verdicts, from the ``contest='pair'`` metrics rows.

    The table that lets a page say **"indistinguishable"** rather than invent a
    ranking. Columns: the pair, ``n_paired``, ``win_frac_a``, each side's ``mae``,
    ``delta_mae`` with its paired bootstrap interval (``d_lo``/``d_hi``), and the
    ``verdict`` — a winner's name, ``indistinguishable`` (resolved but under the
    practical floor) or ``underpowered`` (not resolved at this sample size).

    Returns an empty frame when the sweep has no pair rows (a single-algorithm
    sweep), so the caller omits the section rather than publishing an empty table.
    """
    sweep = figures.resolve(sweep, root)
    pw = sweep.metrics_pairwise
    if pw is None or 'contest' not in getattr(pw, 'columns', []):
        return pd.DataFrame()
    rows = pw[(pw['contest'] == 'pair') & (pw['fit_method'] == fit_method)
              & (pw['stratum'] == stratum)]
    if rows.empty:
        return pd.DataFrame()
    cols = [c for c in ('dataset', 'component', 'ref_wave', 'model_a', 'model_b',
                        'n_paired', 'win_frac_a', 'mae_a', 'mae_b', 'delta_mae',
                        'd_lo', 'd_hi', 'verdict')
            if c in rows.columns]
    out = rows[cols].copy()
    sort_by = [c for c in ('dataset', 'component', 'ref_wave', 'model_a',
                           'model_b') if c in out.columns]
    out = out.sort_values(sort_by).reset_index(drop=True)

    # A pair that shares no scoreable spectrum has no contest — publishing it is
    # the same mistake as a blank figure panel (on the GLORIA sweep it would be
    # 54 of 60 rows).
    n_unscored = 0
    if drop_unscored and 'n_paired' in out.columns:
        empty = out['n_paired'].fillna(0) <= 0
        n_unscored = int(empty.sum())
        out = out[~empty].reset_index(drop=True)

    out = _publishable(out)
    out.attrs['n_unscored_rows'] = n_unscored
    if write:
        path = (figures.subdir(sweep, 'tables')
                / f'head_to_head_{fit_method}_{stratum}.csv')
        out.to_csv(path, index=False)
    return out


#: Columns compared side by side between fit methods. Accuracy first, then the
#: **calibration** pair — which is the interesting axis: a χ² fit reports the
#: curvature of the likelihood at one point, MCMC samples the posterior, and the
#: question a reader has is whether the sampler's wider intervals are also more
#: honest ones.
_FIT_COMPARE_COLS = ('n', 'mae', 'bias', 'median_ratio',
                     'coverage68', 'coverage95', 'coverage_n')

#: Fit-quality columns taken from the closure row rather than the accuracy row.
_FIT_COMPARE_CLOSURE = ('chi2_nu_median', 'rel_misfit_median', 'frac_ok',
                        'n_attempted')


def fit_method_compare(sweep, *, stratum='all', root=None, write=True,
                       methods=('chisq', 'mcmc')):
    """χ² against MCMC for the algorithms fitted **both** ways, side by side.

    ``metrics_*`` has carried ``fit_method`` as a grouping key since Stage 2, so both
    populations are scored in parallel and nothing ever compared them. The comparison
    is only meaningful like-for-like, so it is restricted to the ``(dataset,
    algorithm, component, ref_wave)`` contests present under *both* methods.

    Returns a wide frame with ``<col>_chisq`` / ``<col>_mcmc`` pairs plus ``d_mae``
    (mcmc − chisq; negative means MCMC is more accurate). Empty when the sweep has
    only one fit method — which is every sweep run so far, so callers must check.
    """
    sweep = figures.resolve(sweep, root)
    ms = _require(sweep.metrics_scalar, 'metrics_scalar')
    a, b = methods
    have = set(ms['fit_method'].unique()) if 'fit_method' in ms.columns else set()
    if not {a, b} <= have:
        return pd.DataFrame()

    acc = ms[(ms['stratum'] == stratum) & ms['ref_wave'].notna()]
    closure = ms[(ms['stratum'] == stratum) & (ms['component'] == 'Rrs')]

    frames = []
    for method in (a, b):
        part = acc[acc['fit_method'] == method]
        cols = [c for c in _FIT_COMPARE_COLS if c in part.columns]
        part = part[_CONTEST_KEY + cols].rename(
            columns={c: f'{c}_{method}' for c in cols})
        cl = closure[closure['fit_method'] == method]
        ccols = [c for c in _FIT_COMPARE_CLOSURE if c in cl.columns]
        if ccols:
            on = [k for k in ('dataset', 'algorithm') if k in cl.columns]
            part = part.merge(
                cl[on + ccols].rename(
                    columns={c: f'{c}_{method}' for c in ccols}),
                on=on, how='left')
        frames.append(part)

    out = frames[0].merge(frames[1], on=_CONTEST_KEY, how='inner')
    if out.empty:
        return out
    if f'mae_{a}' in out.columns and f'mae_{b}' in out.columns:
        out['d_mae'] = (out[f'mae_{b}'].astype(float)
                        - out[f'mae_{a}'].astype(float))
    out = out.sort_values(_CONTEST_KEY).reset_index(drop=True)
    out = out.rename(columns={f'n_{a}': f'n_pairs_{a}', f'n_{b}': f'n_pairs_{b}'})
    out = _publishable(out)
    if write:
        path = (figures.subdir(sweep, 'tables')
                / f'fit_method_compare_{stratum}.csv')
        out.to_csv(path, index=False)
    return out


def qc(sweep, *, fit_method='chisq', stratum='all', root=None, write=True):
    """Per-algorithm QC summary: non-solution rate + §2 closure fractions.

    ``frac_not_ok`` is the fraction of ``results_scalar`` rows whose ``status``
    is not ``'ok'`` (fit failures / QC flags), over all strata; the closure
    columns (``chi2_nu_median``, the noise-model-free ``rel_misfit_median`` /
    ``rel_misfit_median_all``, ``frac_good``, ``frac_overfit``,
    ``frac_underfit``, ``frac_qc_fail``) and the per-status **coverage** block
    (``n_attempted`` + one ``frac_<status>`` per
    :data:`ioptics.records.STATUSES`) come from the ``metrics_scalar``
    ``component='Rrs'`` rows. The coverage block is what says *why* rows were
    not scored — a ``frac_out_of_scope`` of 0.8 and a ``frac_fit_failed`` of
    0.8 are the same ``frac_not_ok`` and very different findings.

    Writes ``qc_<fit_method>_<stratum>.csv`` when ``write``; returns the DataFrame.
    """
    sweep = figures.resolve(sweep, root)
    sc = sweep.scalar[sweep.scalar['fit_method'] == fit_method]
    by = [c for c in ('dataset', 'algorithm') if c in sc.columns]
    not_ok = (sc.assign(_bad=sc['status'].ne('ok'))
                .groupby(by)['_bad'].mean()
                .rename('frac_not_ok').reset_index())

    ms = _require(sweep.metrics_scalar, 'metrics_scalar')
    closure = ms[(ms['fit_method'] == fit_method) & (ms['stratum'] == stratum)
                 & (ms['component'] == 'Rrs')]

    # ``frac_not_ok`` above counts every row of the algorithm, but the closure block
    # is scoped to ``stratum`` — so on a per-stratum table the two disagreed: GLORIA's
    # mesotrophic rows published ``frac_not_ok`` 0.79 (whole sweep) beside ``frac_ok``
    # 0.857 (that stratum), which sum to 1.65. Take the complement of the
    # stratum-scoped ``frac_ok`` instead, so the two are the same population by
    # construction; the all-rows computation stays as the fallback for a sweep whose
    # metrics predate the per-status coverage block.
    if 'frac_ok' in closure.columns and not closure.empty:
        scoped = closure[by + ['frac_ok']].copy()
        scoped['frac_not_ok'] = 1.0 - scoped['frac_ok'].astype(float)
        not_ok = (not_ok.drop(columns=['frac_not_ok'])
                        .merge(scoped.drop(columns=['frac_ok']), on=by, how='left'))
        # a group with no closure row keeps the unscoped estimate rather than NaN
        fallback = (sc.assign(_bad=sc['status'].ne('ok'))
                      .groupby(by)['_bad'].mean().rename('_fb').reset_index())
        not_ok = not_ok.merge(fallback, on=by, how='left')
        not_ok['frac_not_ok'] = not_ok['frac_not_ok'].fillna(not_ok['_fb'])
        not_ok = not_ok.drop(columns=['_fb'])
    cols = [c for c in tuple(by) + ('n_attempted', 'n', 'chi2_nu_median',
                                    'rel_misfit_median', 'rel_misfit_median_all',
                                    'frac_good', 'frac_overfit', 'frac_underfit',
                                    'frac_qc_fail')
            + tuple(f'frac_{s}' for s in records.STATUSES)
            if c in closure.columns]
    on = [c for c in by if c in closure.columns]
    out = not_ok.merge(closure[cols], on=on, how='left') \
                .sort_values(by).reset_index(drop=True)
    out = out.rename(columns={'n': 'n_scored'})
    out = _publishable(out)
    if write:
        path = figures.subdir(sweep, 'tables') / f'qc_{fit_method}_{stratum}.csv'
        out.to_csv(path, index=False)
    return out

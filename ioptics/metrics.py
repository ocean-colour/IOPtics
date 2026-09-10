"""Compute the metric battery from the results table.

Log-space MAE/bias, ``Rrs`` closure (chi^2, reduced chi^2), AIC/BIC/Delta-BIC,
68/95% coverage, wins, ratio histograms, and partial-retrieval/coverage rules.
Consumes the results table; imports no BING/ocpy (save BING ``stats`` for IC
cross-checks).

This stage implements **§1 retrieval accuracy vs. truth** (design doc
§"Metrics & diagnostics"). Every primitive operates on aligned ``(M, O)``
arrays — modeled/retrieved ``M`` vs observed/true ``O``, already on the common
``wave`` grid (``prep`` pre-aligns the truth). All accuracy metrics are
**log10 / multiplicative** (Erickson 2023 Eqs. 13-14 / Seegers 2018).

Non-uniformity rule: pairs with a ``NaN`` (or non-positive value, which the
log-space forms cannot take) in *either* ``M`` or ``O`` — a component/wavelength
absent for a dataset — are dropped *before* the reduction; the surviving count
is returned by :func:`n_valid` and recorded alongside every number at the
``compute`` stage. Nothing is zero-filled.
"""

from __future__ import annotations

import hashlib
from collections import namedtuple

import numpy as np
import pandas as pd

from ioptics import io
from ioptics import provenance
from ioptics import records

# Erickson (2023) Fig. 4 ratio buckets for M / O (multiplicative agreement).
RATIO_EDGES = [0, 1 / 3, 1 / 2, 3 / 4, 1, 4 / 3, 2, 3, np.inf]


def _aligned(M, O):
    """Return ``(M, O)`` as 1-D float arrays, keeping only valid pairs.

    This is the single point where the intersection rule is applied: a metric
    is computed only where *both* a retrieval and a truth value exist, are
    finite, **and are strictly positive** (the accuracy metrics are log-space,
    so a zero/negative retrieval is dropped like a NaN rather than producing
    ``-inf``/``nan``; per Q&A all IOPs are physical positives).
    """
    M = np.asarray(M, dtype=float).ravel()
    O = np.asarray(O, dtype=float).ravel()
    if M.shape != O.shape:
        raise ValueError(
            f"M and O must have the same shape; got {M.shape} and {O.shape}")
    keep = np.isfinite(M) & np.isfinite(O) & (M > 0) & (O > 0)
    return M[keep], O[keep]


def n_valid(M, O):
    """Number of surviving ``(M, O)`` pairs after the NaN-drop (the metric ``n``)."""
    M, O = _aligned(M, O)
    return int(M.size)


def mae(M, O):
    """Multiplicative mean absolute (log10) error, ``10**mean|log10(M/O)| - 1``."""
    M, O = _aligned(M, O)
    if M.size == 0:
        return np.nan
    return 10.0 ** np.mean(np.abs(np.log10(M) - np.log10(O))) - 1.0


def bias(M, O):
    """Signed multiplicative bias, ``10**mean(log10(M/O)) - 1`` (>0 = over-estimate)."""
    M, O = _aligned(M, O)
    if M.size == 0:
        return np.nan
    return 10.0 ** np.mean(np.log10(M) - np.log10(O)) - 1.0


def rms_log(M, O):
    """Root-mean-square error in ``log10`` space, ``sqrt(mean(log10(M/O)**2))``."""
    M, O = _aligned(M, O)
    if M.size == 0:
        return np.nan
    return float(np.sqrt(np.mean((np.log10(M) - np.log10(O)) ** 2)))


def median_ratio(M, O):
    """Median of the linear ratio ``M / O`` (1 = unbiased)."""
    M, O = _aligned(M, O)
    if M.size == 0:
        return np.nan
    return float(np.median(M / O))


def ratio_hist(M, O, edges=RATIO_EDGES):
    """Counts of the ratio ``M / O`` per Erickson Fig. 4 bucket.

    Returns an integer array of length ``len(edges) - 1``; bin ``i`` counts
    ratios in ``[edges[i], edges[i+1])`` (the last bin is closed on the right
    at ``+inf``). Non-finite / non-positive pairs are dropped first.
    """
    M, O = _aligned(M, O)
    counts, _ = np.histogram(M / O, bins=np.asarray(edges, dtype=float))
    return counts.astype(int)


def type2_fit(M, O):
    """Log-log Type-II (reduced major axis) regression of ``M`` on ``O``.

    Returns ``(slope, intercept, r2)`` in ``log10`` space. The RMA slope is the
    ratio of standard deviations carrying the sign of the correlation; the
    intercept passes through the log-means; ``r2`` is the squared Pearson
    correlation. Returns ``(nan, nan, nan)`` if fewer than two pairs survive or
    either log-spread is zero.
    """
    M, O = _aligned(M, O)
    if M.size < 2:
        return np.nan, np.nan, np.nan
    x = np.log10(O)
    y = np.log10(M)
    sx = np.std(x)
    sy = np.std(y)
    if sx == 0 or sy == 0:
        return np.nan, np.nan, np.nan
    r = np.corrcoef(x, y)[0, 1]
    slope = np.sign(r) * sy / sx
    intercept = np.mean(y) - slope * np.mean(x)
    return float(slope), float(intercept), float(r ** 2)


# --------------------------------------------------------------------------- #
# §2 Internal closure & fit quality (Rrs space)
# --------------------------------------------------------------------------- #
# χ²ᵥ / AIC / BIC are carried through from ``run`` (BING ``stats``) and read
# straight from ``results_scalar`` — those parts are pure table-in. The
# log-space Rrs MAE/bias and the dual-sided window additionally need the
# *observed* ``Rrs``, which is not yet persisted (``Rrs_model.truth`` is NaN per
# the Stage-2 decision). The functions below take the Rrs arrays explicitly, so
# they are correct regardless of how ``Rrs_obs`` is eventually sourced; wiring
# them into ``compute`` waits on the persistence decision (see Q&A / Task 4).

# Rrs-closure thresholds for the array helpers :func:`rrs_window`/:func:`rrs_closure`
# (Erickson dual-sided window). NOTE: ``compute`` no longer uses these for the §2
# QC flags — the log-space multiplicative Rrs MAE is ill-defined where ``Rrs``
# crosses zero (the red tail of hyperspectral spectra goes ~0 / negative under
# noise), so QC is derived from **χ²ᵥ** instead (:data:`CHI2NU_QC_MAX`). The
# helpers remain valid for closure on strictly-positive Rrs bands.
NOISE_FLOOR = 0.05
FIT_NOISE_FACTOR = 0.5
RRS_QC_MAX = 0.25

# §2 QC (noise-weighted): a fit with reduced χ²ᵥ above this is a non-solution.
#: Reduced chi-squared above which a fit is not a solution. Same number as
#: the per-row ``poor_fit`` status uses, imported so the aggregate metric
#: and the row label cannot drift apart.
CHI2NU_QC_MAX = records.CHI2NU_POOR_FIT

#: Row statuses that are **scored**. A leaderboard ranks *solutions*, so only
#: ``'ok'`` rows enter the accuracy and closure reductions; the other statuses
#: (:data:`ioptics.records.STATUSES`) are reported as **coverage** — the
#: ``frac_ok`` / ``frac_poor_fit`` / ``frac_out_of_scope`` / ``frac_fit_failed``
#: columns on the ``component='Rrs'`` closure row — rather than averaged in.
#: Without this an algorithm's median is taken over whichever spectra it
#: happened to fit, so two algorithms' numbers are not comparable at all.
SCORE_STATUSES = ('ok',)


def rel_misfit(Rrs_model, Rrs_obs):
    """Median absolute **relative** misfit, ``median(|M - O| / O)``.

    The one fit-quality number that owes nothing to the noise model: it is a
    direct statement about how far the model spectrum sits from the observed
    one, in fractions of the observation. That independence is the point.
    Reduced χ²ᵥ moved by 5x on GLORIA when the assumed error floor changed
    while the fits themselves did not move at all, and the GLORIA report's
    headline misfit was wrong by a third for a reason χ² could not reveal
    (``reports/gloria_fits_report.md``, Round-4 notice) — on data whose quoted
    uncertainties are absent or untrustworthy, this is the number to read
    first.

    Restricted to bands where ``Rrs_obs`` is **strictly positive** and both
    values are finite: the ratio is meaningless where the observation crosses
    zero, which hyperspectral red tails routinely do. (That is also why the
    log-space Rrs MAE was dropped from the closure row in Stage 2 — but a
    median of ratios survives the restriction where a log does not, because it
    needs only the *observation* to be positive.)

    Returns ``np.nan`` if no band qualifies.
    """
    M = np.asarray(Rrs_model, dtype=float).ravel()
    O = np.asarray(Rrs_obs, dtype=float).ravel()
    if M.shape != O.shape:
        raise ValueError(
            f"Rrs_model and Rrs_obs must have the same shape; "
            f"got {M.shape} and {O.shape}")
    keep = np.isfinite(M) & np.isfinite(O) & (O > 0)
    if not keep.any():
        return np.nan
    return float(np.median(np.abs(M[keep] - O[keep]) / O[keep]))


def chi2nu_quality(chi2_nu, dof, *, n_sigma=2.0):
    """Headline single-fit flag from reduced χ²ᵥ, with a dof-scaled good band.

    ≈1 is a good fit; **<1 overfit**, **>1 underfit** (design §2). The
    acceptance band is tied to the degrees of freedom (Q&A): reduced χ²ᵥ has
    standard deviation ``sqrt(2/dof)`` about 1, so the band is
    ``1 ± n_sigma·sqrt(2/dof)`` — wide for few bands, tight for many. Values
    below the band are ``'overfit'``, above ``'underfit'``, inside ``'good'``; a
    non-finite χ²ᵥ or ``dof <= 0`` returns ``'unknown'``.
    """
    if not np.isfinite(chi2_nu) or dof <= 0:
        return 'unknown'
    half = n_sigma * np.sqrt(2.0 / dof)
    if chi2_nu < 1.0 - half:
        return 'overfit'
    if chi2_nu > 1.0 + half:
        return 'underfit'
    return 'good'


def rrs_window(rrs_mae, *, noise_floor=NOISE_FLOOR,
               fit_noise_factor=FIT_NOISE_FACTOR, qc_max=RRS_QC_MAX):
    """Dual-sided Rrs-closure flags from the (multiplicative, log-space) Rrs MAE.

    Returns ``dict(fit_noise=..., qc_fail=...)``:

    - ``fit_noise`` — MAE falls *well below* the measurement-noise floor (the
      fit is tracking the noise; over-fitting), i.e.
      ``rrs_mae < fit_noise_factor * noise_floor``.
    - ``qc_fail`` — ``rrs_mae > qc_max`` marks a non-solution (mirrors the
      ``status`` QC that ``run`` records).

    A non-finite MAE returns both flags ``False`` (nothing to judge).
    """
    if not np.isfinite(rrs_mae):
        return {'fit_noise': False, 'qc_fail': False}
    return {'fit_noise': bool(rrs_mae < fit_noise_factor * noise_floor),
            'qc_fail': bool(rrs_mae > qc_max)}


def rrs_closure(Rrs_model, Rrs_obs, *, noise_floor=NOISE_FLOOR,
                fit_noise_factor=FIT_NOISE_FACTOR, qc_max=RRS_QC_MAX):
    """Log-space Rrs closure: MAE/bias (§1 forms on Rrs) + dual-sided window.

    ``Rrs_model`` vs the *observed* ``Rrs_obs`` (both 1/sr, aligned on ``wave``).
    Returns ``dict(rrs_mae, rrs_bias, n, fit_noise, qc_fail)``. NaN-drop and the
    multiplicative log10 forms are inherited from :func:`mae` / :func:`bias`.
    """
    rrs_mae = mae(Rrs_model, Rrs_obs)
    flags = rrs_window(rrs_mae, noise_floor=noise_floor,
                       fit_noise_factor=fit_noise_factor, qc_max=qc_max)
    return {'rrs_mae': rrs_mae, 'rrs_bias': bias(Rrs_model, Rrs_obs),
            'n': n_valid(Rrs_model, Rrs_obs), **flags}


# --------------------------------------------------------------------------- #
# §3 Model selection / complexity
# --------------------------------------------------------------------------- #
# Straight from ``results_scalar`` (AIC, BIC, k, n_bands) — fully table-in.

def delta_bic(bic_a, bic_b):
    """ΔBIC = ``BIC_a - BIC_b``; **< 0 favors model A** (lower BIC).

    With the in-tandem ``expb_pow`` (k=5) vs ``giop`` (k=3) pair, passing
    ``a=expb_pow`` makes ΔBIC < 0 favor the more complex model.
    """
    return np.asarray(bic_a, dtype=float) - np.asarray(bic_b, dtype=float)


def dbic_cdf(df, model_a, model_b, *, by=None, fit_method='chisq',
             bic_col='BIC', algo_col='algorithm',
             keys=('dataset', 'obs_id'), statuses=SCORE_STATUSES):
    """Per-spectrum ΔBIC contest between two algorithms, as a CDF.

    Pairs ``model_a`` vs ``model_b`` rows of ``results_scalar`` on the common
    spectrum keys (``dataset``, ``obs_id``) **like-for-like** within a single
    ``fit_method`` (default ``'chisq'``, since ``expb_pow`` is χ²-only), and
    computes ΔBIC = ``BIC(model_a) - BIC(model_b)`` per matched spectrum.

    Restricted to rows whose ``status`` is in ``statuses`` (default
    :data:`SCORE_STATUSES`), for the same reason every other reduction is: a
    ``fit_failed`` or ``poor_fit`` row is not a solution, and its BIC is not a
    statement about model complexity. This also makes the figure agree with the
    table — :func:`compute` scores the pairwise ΔBIC over status-filtered rows, so
    an unfiltered caller published ``n = 100`` for the contest whose
    ``metrics_pairwise`` row said ``n = 21``, on the same page. Pass
    ``statuses=None`` to score every row.

    Returns ``dict(dbic, cdf, n, frac_favor_a, frac_favor_b)`` where ``dbic`` is
    sorted ascending, ``cdf`` is the matching empirical CDF in ``[0, 1]``,
    ``frac_favor_a`` is the fraction with ΔBIC < 0 (model A wins) and
    ``frac_favor_b`` the fraction with ΔBIC > 0 (ties favor neither). If ``by``
    is given (a column name), returns ``{stratum: dict(...)}`` per group.
    """
    if fit_method is not None and 'fit_method' in df.columns:
        df = df[df['fit_method'] == fit_method]
    if statuses is not None:
        df = _scored(df, statuses)

    if by is not None:
        out = {}
        for stratum, sub in df.groupby(by):
            out[stratum] = dbic_cdf(sub, model_a, model_b, by=None,
                                    fit_method=None, bic_col=bic_col,
                                    algo_col=algo_col, keys=keys,
                                    statuses=None)
        return out

    a = df[df[algo_col] == model_a][list(keys) + [bic_col]]
    b = df[df[algo_col] == model_b][list(keys) + [bic_col]]
    merged = a.merge(b, on=list(keys), suffixes=('_a', '_b'))
    d = delta_bic(merged[f'{bic_col}_a'].to_numpy(),
                  merged[f'{bic_col}_b'].to_numpy())
    d = d[np.isfinite(d)]
    d = np.sort(d)
    n = int(d.size)
    cdf = (np.arange(1, n + 1) / n) if n else np.array([])
    return {
        'dbic': d, 'cdf': cdf, 'n': n,
        'frac_favor_a': float(np.mean(d < 0)) if n else np.nan,
        'frac_favor_b': float(np.mean(d > 0)) if n else np.nan,
    }


# --------------------------------------------------------------------------- #
# §4 Uncertainty assessment — coverage + detection
# --------------------------------------------------------------------------- #

def coverage_n(O, lo, hi):
    """How many trials the empirical :func:`coverage` was measured over.

    Its own column because it is **not** the accuracy row's ``n``: that counts
    ``(retrieved, truth)`` pairs surviving the finite-and-positive rule, while
    coverage needs ``truth`` and both bounds and ignores the retrieved value. The
    two coincide only when every scored pair also has credible bounds — a fit
    whose covariance failed has bounds for fewer — and a calibration verdict
    tested with the wrong trial count is too tight by ``sqrt(n/coverage_n)``.
    """
    O = np.asarray(O, dtype=float).ravel()
    lo = np.asarray(lo, dtype=float).ravel()
    hi = np.asarray(hi, dtype=float).ravel()
    if not (O.shape == lo.shape == hi.shape):
        raise ValueError("O, lo, hi must have the same shape")
    return int((np.isfinite(O) & np.isfinite(lo) & np.isfinite(hi)).sum())


def coverage(O, lo, hi):
    """Empirical coverage: fraction of truth values inside ``[lo, hi]``.

    The design's formal calibration metric (absent from the source papers):
    scored per component/ref-λ at the 68% and 95% levels (pass the matching
    ``lo``/``hi`` bounds), where the empirical fraction should ≈ the nominal
    level. Elements with a non-finite ``O``, ``lo`` or ``hi`` are dropped before
    the reduction (linear-space test — no positivity requirement). Returns
    ``np.nan`` if nothing is scorable.
    """
    O = np.asarray(O, dtype=float).ravel()
    lo = np.asarray(lo, dtype=float).ravel()
    hi = np.asarray(hi, dtype=float).ravel()
    if not (O.shape == lo.shape == hi.shape):
        raise ValueError("O, lo, hi must have the same shape")
    keep = np.isfinite(O) & np.isfinite(lo) & np.isfinite(hi)
    if not keep.any():
        return np.nan
    O, lo, hi = O[keep], lo[keep], hi[keep]
    return float(np.mean((O >= lo) & (O <= hi)))


def detection(med, lo, hi):
    """Classify each retrieval as a detection or an upper limit.

    A quantity is *detected* when its credible interval excludes zero
    (``lo > 0``) — the retrieval is bounded away from non-detection at the level
    of the supplied bounds (pass the 95% bounds for a ~2σ test, 68% for ~1σ).
    Otherwise it is a **non-detection**, reported as an ``upper_limit`` (``hi``).

    Returns ``dict(detected, upper_limit)`` with element-wise arrays: ``detected``
    is boolean; ``upper_limit`` holds ``hi`` where not detected and ``nan`` where
    detected. Elements with a non-finite bound are not detected (``upper_limit``
    is ``hi``, possibly ``nan``).
    """
    med = np.asarray(med, dtype=float).ravel()
    lo = np.asarray(lo, dtype=float).ravel()
    hi = np.asarray(hi, dtype=float).ravel()
    if not (med.shape == lo.shape == hi.shape):
        raise ValueError("med, lo, hi must have the same shape")
    detected = np.isfinite(lo) & (lo > 0)
    upper_limit = np.where(detected, np.nan, hi)
    return {'detected': detected, 'upper_limit': upper_limit}


# --------------------------------------------------------------------------- #
# §5 Cross-algorithm comparison — wins + rankings
# --------------------------------------------------------------------------- #

def wins(table, *, by=('dataset', 'component', 'ref_wave'),
         metric='abs_log_err', obs_col='obs_id', algo_col='algorithm',
         value_col='value', truth_col='truth'):
    """Per-spectrum head-to-head wins between algorithms (Erickson/Seegers).

    Within each ``by`` group, every spectrum (``obs_col``) hosts a round-robin of
    pairwise contests among the algorithms present; the algorithm **closer to
    truth** wins each contest. The contest metric is ``abs_log_err`` =
    ``|log10(value) - log10(truth)|`` (computed from ``value_col``/``truth_col``
    if a ``metric`` column is absent; smaller wins). Provisional — flagged for
    revisit (could become within-uncertainty agreement or signed bias).

    Returns a tidy DataFrame: one row per ``(by..., algorithm)`` with ``wins``,
    ``contests`` and ``win_frac = wins / contests``. Ties split credit (0.5 each)
    and still count as a contest for both; non-finite metrics are dropped.
    """
    df = table.copy()
    if metric not in df.columns:
        with np.errstate(divide='ignore', invalid='ignore'):
            df[metric] = np.abs(np.log10(df[value_col].to_numpy(dtype=float))
                                - np.log10(df[truth_col].to_numpy(dtype=float)))
    df = df[np.isfinite(df[metric].to_numpy(dtype=float))]

    group_cols = [c for c in by if c in df.columns]
    tally = {}   # (group_key_tuple, algo) -> [wins, contests]

    def _bump(key, algo, credit):
        rec = tally.setdefault((key, algo), [0.0, 0])
        rec[0] += credit
        rec[1] += 1

    for gkey, spectrum in df.groupby(group_cols + [obs_col], sort=False):
        # the group key without the obs_id tail (preserve original dtypes —
        # np.atleast_1d would stringify a mixed str/float key)
        key_list = list(gkey) if isinstance(gkey, tuple) else [gkey]
        gtuple = tuple(key_list[:len(group_cols)])
        rows = spectrum[[algo_col, metric]].to_numpy(dtype=object)
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                ai, ei = rows[i][0], float(rows[i][1])
                aj, ej = rows[j][0], float(rows[j][1])
                ci = 1.0 if ei < ej else (0.0 if ej < ei else 0.5)
                _bump(gtuple, ai, ci)
                _bump(gtuple, aj, 1.0 - ci)

    out = []
    for (gtuple, algo), (w, c) in tally.items():
        row = dict(zip(group_cols, gtuple))
        row[algo_col] = algo
        row['wins'] = w
        row['contests'] = c
        row['win_frac'] = w / c if c else np.nan
        out.append(row)
    return pd.DataFrame(out, columns=group_cols + [algo_col, 'wins',
                                                   'contests', 'win_frac'])


#: Practical-significance floor for a head-to-head verdict, in the units of
#: :func:`mae` (fractional multiplicative error). JXP's decision: **10%**. Two
#: algorithms whose ref-band MAE differs by less than this are reported as
#: indistinguishable *in practice* even when the paired test resolves a
#: difference — the threshold encodes what counts as scientifically meaningful,
#: which is a judgement, not a statistic.
PRACTICAL_MAE_FLOOR = 0.10

#: How :data:`PRACTICAL_MAE_FLOOR` is applied. ``'absolute'`` is the literal
#: reading of JXP's "use 10%" — a fixed difference in fractional MAE — and is the
#: default. **Known consequence, measured:** on a dataset where both algorithms are
#: accurate (ref-band MAE of a few percent, as an L23-class synthetic gives) two
#: algorithms whose errors differ five-fold (1% vs 5%) are still 0.04 apart and are
#: therefore declared equivalent; no pair can ever clear an absolute 0.10 there.
#: ``'relative'`` scales the margin to the better MAE so "10%" means a tenth of the
#: error being compared. Pending confirmation in the Q&A.
PRACTICAL_FLOOR_MODE = 'absolute'

#: Bootstrap resamples for the paired-difference interval, after the ocean-colour
#: round-robin precedent (Brewin et al. 2015, which resamples the in-situ data
#: 1000 times to put uncertainty on a ranking).
BOOTSTRAP_RESAMPLES = 1000

#: Fixed seed: a published verdict must not change because the report was
#: regenerated.
BOOTSTRAP_SEED = 1234

#: Below this many paired spectra, do not pretend to a verdict at all.
MIN_PAIRED = 3


def paired_abs_log_errors(table, model_a, model_b, *, obs_col='obs_id',
                          algo_col='algorithm', value_col='value',
                          truth_col='truth'):
    """Per-spectrum ``|log10(M/O)|`` for two algorithms, on shared spectra.

    Returns a 2-column DataFrame indexed by observation, columns ``model_a`` and
    ``model_b``, restricted to spectra where **both** produced a finite, positive
    retrieval against the same truth. Empty if the pairing yields nothing.

    Keeping both columns (rather than only their difference) is what lets the
    bootstrap resample the *same* statistic the tables publish: a paired resample
    of spectra recomputes each algorithm's MAE, so the interval and the practical
    floor are both on the fractional-multiplicative MAE scale. Bootstrapping the
    median difference of log errors instead would put the significance test and
    the effect size on different scales — on the real GLORIA contest those differ
    by two orders of magnitude, because MAE is a mean of heavy-tailed errors while
    the paired median is not.
    """
    keep_cols = [obs_col, algo_col, value_col, truth_col]
    sub = table[table[algo_col].isin([model_a, model_b])][keep_cols].copy()
    if sub.empty:
        return pd.DataFrame()
    m = sub[value_col].to_numpy(dtype=float)
    o = sub[truth_col].to_numpy(dtype=float)
    ok = np.isfinite(m) & np.isfinite(o) & (m > 0) & (o > 0)
    with np.errstate(divide='ignore', invalid='ignore'):
        err = np.abs(np.log10(m) - np.log10(o))
    err[~ok] = np.nan
    sub['_err'] = err
    wide = sub.pivot_table(index=obs_col, columns=algo_col, values='_err',
                           aggfunc='mean')
    if model_a not in wide.columns or model_b not in wide.columns:
        return pd.DataFrame()
    return wide[[model_a, model_b]].dropna()


def _mae_from_log_err(err):
    """``mae`` from already-computed absolute log errors (``10**mean − 1``).

    A retrieval many orders of magnitude off overflows to ``inf`` here; that is the
    honest answer (an unbounded error), and :func:`head_to_head` reads it as a
    decisive loss rather than an unresolved contest, so the overflow is expected
    rather than a warning worth raising.
    """
    err = np.asarray(err, dtype=float)
    if err.size == 0:
        return np.nan
    with np.errstate(over='ignore', invalid='ignore'):
        return 10.0 ** np.mean(err, axis=-1) - 1.0


def paired_log_errors(table, model_a, model_b, **kwargs):
    """Per-spectrum paired difference in absolute log error, ``A − B``.

    The quantity a head-to-head verdict needs and :func:`wins` cannot provide:
    ``wins`` tallies into ``(group, algorithm)`` and **discards the opponent's
    identity**, so its "contests" are not independent trials of any one pairing
    (with four algorithms, 36 contests are 12 spectra x 3 opponents) and no paired
    statistic can be recovered from it. Here the pairing is kept.

    Returns ``|log10(M_A/O)| − |log10(M_B/O)|`` per shared spectrum (negative
    means ``model_a`` was closer) — the win-tally view of
    :func:`paired_abs_log_errors`.
    """
    both = paired_abs_log_errors(table, model_a, model_b, **kwargs)
    if both.empty:
        return np.array([])
    return (both.iloc[:, 0] - both.iloc[:, 1]).to_numpy(dtype=float)


def _pair_seed(group_key, model_a, model_b, *, base=BOOTSTRAP_SEED):
    """A reproducible but contest-specific bootstrap seed.

    One global seed reuses the *same* resample index matrix for every pair, so all
    published intervals move together — a reader comparing intervals across pairs
    would be comparing correlated noise. Deriving the seed from the contest key and
    the pair names keeps every interval reproducible while making them independent
    draws.
    """
    key = repr((group_key, model_a, model_b)).encode('utf-8')
    return (base + int(hashlib.md5(key).hexdigest()[:8], 16)) % (2 ** 32)


def _floor_value(floor, mode, mae_a, mae_b):
    """The practical-significance margin, absolute or relative to the better MAE.

    ``'absolute'`` (JXP's stated 10%) is a fixed difference in fractional MAE.
    Note the consequence, which is why ``'relative'`` exists as an option: on an
    accurate dataset where both algorithms sit at a few percent error, *no* pair can
    ever differ by 0.10, so every contest is declared equivalent by construction.
    ``'relative'`` scales the margin to the better of the two MAEs, so "10%" means
    a tenth of the error being compared.
    """
    if mode == 'absolute':
        return float(floor)
    if mode != 'relative':
        raise ValueError(f"floor_mode must be 'absolute' or 'relative'; got {mode!r}")
    best = np.nanmin([mae_a, mae_b])
    if not np.isfinite(best):
        return float(floor)
    return float(floor) * float(best)


def _bootstrap_delta_mae(err_a, err_b, *, level=0.95,
                         resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    """Percentile interval for ``mae(A) − mae(B)`` under a **paired** resample.

    Resamples spectra (not algorithms), so each replicate re-computes both MAEs on
    the same draw and the difference keeps its pairing — the Brewin round-robin's
    approach to putting uncertainty on a ranking, applied to one pair.
    """
    err_a = np.asarray(err_a, dtype=float)
    err_b = np.asarray(err_b, dtype=float)
    if err_a.size == 0 or err_a.size != err_b.size:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, err_a.size, size=(int(resamples), err_a.size))
    deltas = _mae_from_log_err(err_a[idx]) - _mae_from_log_err(err_b[idx])
    tail = (1.0 - level) / 2.0
    return (float(np.quantile(deltas, tail)),
            float(np.quantile(deltas, 1.0 - tail)))


def head_to_head(table, scalar=None, *,
                 by=('dataset', 'fit_method', 'stratum', 'component',
                     'ref_wave'),
                 algo_col='algorithm', floor=PRACTICAL_MAE_FLOOR,
                 floor_mode=PRACTICAL_FLOOR_MODE):
    """Per-**pair** contests with a verdict that can say "indistinguishable".

    For every contest in ``by`` and every unordered algorithm pair present, keeps
    the pairing (unlike :func:`wins`) and reports:

    ``n_paired``
        spectra where both algorithms produced a scoreable retrieval.
    ``wins_a`` / ``ties`` / ``win_frac_a``
        the head-to-head tally **for this pair only**.
    ``delta_mae`` and ``d_lo`` / ``d_hi``
        ``mae(A) − mae(B)`` on the paired spectra (negative favours ``A``) and its
        **paired bootstrap** interval — both in the fractional multiplicative units
        the tables publish, which is also the scale the practical floor is judged
        on. ``d_median`` is the median per-spectrum difference in absolute log
        error, reported for reference.
    ``resolved``
        whether the bootstrap interval excludes 0.
    ``verdict``
        ``None`` (the pair shares no scoreable spectrum — a different fact from an
        unresolved difference), ``'indistinguishable'`` (``|delta_mae|`` is below
        the practical floor, so the difference would not matter even if confirmed),
        ``'underpowered'`` (a *material* point estimate that the interval does not
        resolve, or fewer than :data:`MIN_PAIRED` spectra), or the **winner's
        name** (material and resolved).

    Two thresholds, deliberately separate: the bootstrap answers *can we tell?*
    and the floor answers *would anyone care?* A rank is only ever printed when
    both say yes.
    """
    group_cols = [c for c in by if c in table.columns]
    rows = []
    grouped = table.groupby(group_cols, sort=False) if group_cols \
        else [((), table)]
    for kvals, g in grouped:
        algos = sorted(g[algo_col].dropna().unique())
        for i in range(len(algos)):
            for j in range(i + 1, len(algos)):
                a, b = algos[i], algos[j]
                both = paired_abs_log_errors(g, a, b, algo_col=algo_col)
                if both.empty:
                    err_a = err_b = np.array([])
                else:
                    err_a = both[a].to_numpy(dtype=float)
                    err_b = both[b].to_numpy(dtype=float)
                d = err_a - err_b
                # MAE on the *paired* spectra only, so the difference and its
                # interval describe the same population.
                mae_a = _mae_from_log_err(err_a)
                mae_b = _mae_from_log_err(err_b)
                delta = (mae_a - mae_b) if np.isfinite([mae_a, mae_b]).all() \
                    else np.nan
                lo, hi = _bootstrap_delta_mae(err_a, err_b,
                                              seed=_pair_seed(kvals, a, b))
                resolved = bool(np.isfinite([lo, hi]).all() and (lo > 0 or hi < 0))
                margin = _floor_value(floor, floor_mode, mae_a, mae_b)
                # An interval that lies wholly inside ±margin is the *equivalence*
                # result: the data rule a material difference out. An interval
                # wider than the margin cannot support that claim no matter how
                # small the point estimate is.
                equivalent = bool(np.isfinite([lo, hi]).all()
                                  and abs(lo) < margin and abs(hi) < margin)
                if d.size == 0:
                    # No shared spectra at all is a different fact from "we
                    # cannot resolve the difference"; leave it unstated.
                    verdict = None
                elif not np.isfinite([mae_a, mae_b]).all():
                    # One side is infinite/undefined — a catastrophic loss needs
                    # no statistics, and calling it "underpowered" is backwards.
                    verdict = (b if np.isfinite(mae_b) else
                               (a if np.isfinite(mae_a) else 'underpowered'))
                elif d.size < MIN_PAIRED:
                    # Too few shared spectra to claim anything, in either
                    # direction. Checked *before* the equivalence test: with n=1
                    # every resample is identical, so the interval has zero width
                    # and would otherwise "prove" equivalence.
                    verdict = 'underpowered'
                elif equivalent:
                    verdict = 'indistinguishable'
                elif resolved and abs(delta) >= margin:
                    verdict = a if delta < 0 else b
                else:
                    # Either the interval spans 0, or it excludes 0 but straddles
                    # the margin — a difference may exist and may matter, and this
                    # sample cannot say.
                    verdict = 'underpowered'
                wins_a = float((d < 0).sum() + 0.5 * (d == 0).sum())
                row = dict(zip(group_cols, kvals if isinstance(kvals, tuple)
                               else (kvals,)))
                row.update({
                    'contest': 'pair', 'model_a': a, 'model_b': b,
                    'n_paired': int(d.size), 'wins_a': wins_a,
                    'ties': int((d == 0).sum()),
                    'win_frac_a': (wins_a / d.size) if d.size else np.nan,
                    'mae_a': mae_a, 'mae_b': mae_b, 'delta_mae': delta,
                    'd_median': float(np.median(d)) if d.size else np.nan,
                    'd_lo': lo, 'd_hi': hi, 'resolved': resolved,
                    'practical_floor': float(margin),
                    'floor_mode': floor_mode, 'equivalent': equivalent,
                    'verdict': verdict,
                })
                rows.append(row)
    return pd.DataFrame(rows)


def rankings(metrics_scalar, *, by=('dataset', 'component'),
             algo_col='algorithm',
             lower_is_better=('mae', 'abs_bias', 'rms_log'),
             higher_is_better=('win_frac', 'coverage')):
    """Rank algorithms per variable within each ``by`` group (Erickson Tbl 2).

    For every metric column present in ``metrics_scalar``, adds a
    ``<col>_rank`` column (1 = best): columns in ``lower_is_better`` are ranked
    ascending (e.g. ``mae``, ``|bias|``, ``rms_log``), those in
    ``higher_is_better`` descending (e.g. ``win_frac``, ``coverage``). Ranking
    uses ``method='min'`` so ties share the best rank. ``by`` keys absent from
    the frame are ignored. Returns a copy with the added rank columns.
    """
    df = metrics_scalar.copy()
    group_cols = [c for c in by if c in df.columns]
    grouped = df.groupby(group_cols) if group_cols else None

    def _rank(col, ascending):
        if grouped is None:
            return df[col].rank(method='min', ascending=ascending)
        return grouped[col].rank(method='min', ascending=ascending)

    for col in lower_is_better:
        if col in df.columns:
            df[f'{col}_rank'] = _rank(col, ascending=True)
    for col in higher_is_better:
        if col in df.columns:
            df[f'{col}_rank'] = _rank(col, ascending=False)
    return df


# --------------------------------------------------------------------------- #
# compute() orchestration — read the results tables, emit the metrics tables
# --------------------------------------------------------------------------- #

REF_WAVES = {'absorption': (440, 443), 'backscatter': (555, 670)}
REF_TOL = 3.0                     # nm: ref-band match tolerance (Q19)
ACCURACY_COMPONENTS = ('a', 'bb', 'a_ph', 'a_dg', 'bb_p')
_COMPONENT_REFSET = {'a': 'absorption', 'a_ph': 'absorption',
                     'a_dg': 'absorption', 'bb': 'backscatter',
                     'bb_p': 'backscatter'}
# Derived scalar variables scored vs their truth columns in results_scalar.
SCALAR_VARS = {'Chl': 'Chl_truth', 'a_cdom440': 'a_cdom440_truth',
               'Sdg': 'Sdg_truth'}
# Chl strata (mg m^-3); binning Chl is truth where available else retrieved.
CHL_BINS = [(0.0, 0.1, 'oligotrophic'),
            (0.1, 1.0, 'mesotrophic'),
            (1.0, np.inf, 'eutrophic')]

METRICS_SPECTRAL_FILE = 'metrics_spectral.parquet'
METRICS_SCALAR_FILE = 'metrics_scalar.parquet'
METRICS_PAIRWISE_FILE = 'metrics_pairwise.parquet'

MetricsTables = namedtuple('MetricsTables', ['spectral', 'scalar', 'pairwise'])

_KEYS = ['dataset', 'algorithm', 'fit_method', 'stratum']


def _chl_stratum(chl):
    """Map a Chl value (mg m^-3) to its stratum label (``'unknown'`` if NaN)."""
    if not np.isfinite(chl):
        return 'unknown'
    for lo, hi, label in CHL_BINS:
        if lo <= chl < hi:
            return label
    return 'unknown'


def _strata_map(scalar_df):
    """Per-``(dataset, obs_id)`` stratum from truth Chl (else retrieved Chl)."""
    rows = []
    for (ds, obs), g in scalar_df.groupby(['dataset', 'obs_id']):
        chl = np.nan
        for col in ('Chl_truth', 'Chl'):
            if col in g:
                finite = g[col].to_numpy(dtype=float)
                finite = finite[np.isfinite(finite)]
                if finite.size:
                    chl = float(finite[0])
                    break
        rows.append({'dataset': ds, 'obs_id': obs,
                     'stratum': _chl_stratum(chl)})
    return pd.DataFrame(rows)


def _scoped(df):
    """Duplicate ``df`` with a synthetic ``stratum='all'`` scope prepended.

    Lets a single group-by emit the overall reduction *and* each per-stratum
    reduction (design: every scalar metric computed overall **and** per bin).
    """
    return pd.concat([df.assign(stratum='all'), df], ignore_index=True)


#: Nominal coverage per credible level — what a *calibrated* uncertainty would hit.
NOMINAL_COVERAGE = {'coverage68': 0.68, 'coverage95': 0.95}

#: The value each published metric takes for a perfect retrieval. Kept in one place
#: because the metrics genuinely disagree — the multiplicative errors are perfect at
#: 0, ``median_ratio`` at 1, and the coverages at their **nominal level** — and a
#: figure that draws a "perfect" reference line has to draw the right one. An
#: accuracy-vs-wavelength panel of ``coverage68`` was drawing its reference at 0,
#: which is the *worst* possible value, not the best.
PERFECT_VALUE = {
    'mae': 0.0, 'bias': 0.0, 'abs_bias': 0.0, 'rms_log': 0.0,
    'median_ratio': 1.0, **NOMINAL_COVERAGE,
}


def perfect_value(metric):
    """The perfect value for ``metric``, or ``None`` if we do not know one.

    ``None`` rather than a guess of 0.0: an unrecognised metric with a reference line
    drawn at zero asserts something we have not established.
    """
    return PERFECT_VALUE.get(str(metric))


PROVENANCE_COL = 'provenance_id'


def _stamp_provenance(df, sweep_id):
    """Stamp ``provenance_id`` onto a metrics table (``<sweep_id>#<algorithm>``).

    ``results_scalar`` has carried this since Stage 2 and the metrics tables dropped
    it, so a metrics row could not be traced back to the provenance block that
    produced it without re-deriving the join by hand. It is a pure function of
    ``sweep_id`` and ``algorithm``, so stamping it after the reductions cannot change
    any grouping.

    Pairwise rows naming **two** algorithms (``model_a``/``model_b``) get one id per
    side rather than a single ambiguous one — a contest is not attributable to one
    provenance block.
    """
    if df is None or df.empty:
        return df
    out = df.copy()
    if 'algorithm' in out.columns:
        out[PROVENANCE_COL] = [
            provenance.provenance_id(sweep_id, a) for a in out['algorithm']]
    for side in ('model_a', 'model_b'):
        if side in out.columns:
            suffix = side.split('_')[-1]
            out[f'{PROVENANCE_COL}_{suffix}'] = [
                provenance.provenance_id(sweep_id, a) if isinstance(a, str) and a
                else None for a in out[side]]
    return out


def with_strata(scalar_df):
    """``results_scalar`` plus a ``stratum`` column, for stratified reductions.

    ``stratum`` is **not persisted**: :func:`compute` derives it in memory and writes
    it only onto the ``metrics_*`` tables. So a caller holding ``results_scalar`` —
    which is what :func:`dbic_cdf` takes — cannot group by it, and
    ``dbic_cdf(..., by='stratum')`` raised ``KeyError: 'stratum'`` despite the
    parameter existing. This attaches it using the same truth-Chl-then-retrieved-Chl
    rule the metrics tables use, so a stratified ΔBIC contest bins identically to
    every published per-stratum number.

    Returns the frame unchanged if it already carries ``stratum`` or is empty.
    """
    if scalar_df is None or scalar_df.empty or 'stratum' in scalar_df.columns:
        return scalar_df
    if not {'dataset', 'obs_id'} <= set(scalar_df.columns):
        return scalar_df
    return scalar_df.merge(_strata_map(scalar_df), on=['dataset', 'obs_id'],
                           how='left')


#: Algorithms whose forward model includes **CDOM fluorescence**
#: (``rt.include_CDOM_fl``). Named rather than introspected: :func:`compute`
#: scores a results *table*, which carries algorithm names and no specs, and
#: reading the sweep's provenance to recover the flag would make the metrics
#: layer depend on an artifact it otherwise never opens. Keep in step with
#: :data:`ioptics.algorithms.registry.RT_VARIANT_SEED` (asserted in the tests).
CDOM_FL_ALGORITHMS = frozenset({'expb_pow_hyb_ramflcdom'})

#: Datasets whose truth was generated **without** a CDOM-fluorescence term, so
#: a retrieval that models one is graded against a forward model that does not
#: have it. L23 is HydroLight output: its inelastic realization (``X=4``)
#: carries Raman scattering and chlorophyll fluorescence and nothing else, so
#: any CDOM-fluorescence signal an ``include_CDOM_fl`` fit puts into the
#: ~515 nm region is absorbed by the other free parameters before the IOPs are
#: compared. The numbers are still computed — they are simply not a clean test
#: of the term, which is what the flag says.
NO_CDOM_FL_TRUTH_DATASETS = ('L23',)

#: The caveat strings :func:`_caveat` can emit.
CAVEAT_CDOM_VS_ADG = 'CDOM_vs_adg'
CAVEAT_NO_CDOM_FL_TRUTH = 'no_CDOMfl_truth'


def _caveat(dataset, component, algorithm=None):
    """Truth-mapping caveat flag for one metrics row (``''`` when there is none).

    Two rules, both saying "this row's *truth* does not mean quite what the
    column header implies":

    ``CDOM_vs_adg``
        GLORIA ``a_dg`` rows. GLORIA measures CDOM absorption alone, whereas
        ``a_dg`` is CDOM **+** detritus, so the retrieval is being graded
        against a strictly smaller quantity.
    ``no_CDOMfl_truth``
        a CDOM-fluorescence algorithm (:data:`CDOM_FL_ALGORITHMS`) on a dataset
        whose truth has no such term (:data:`NO_CDOM_FL_TRUTH_DATASETS`).

    ``algorithm`` is optional so the GLORIA rule — which predates it and does
    not depend on the algorithm — behaves identically when it is not supplied.
    """
    if str(dataset).upper().startswith('GLORIA') and component == 'a_dg':
        return CAVEAT_CDOM_VS_ADG
    if algorithm in CDOM_FL_ALGORITHMS and any(
            str(dataset).upper().startswith(d)
            for d in NO_CDOM_FL_TRUTH_DATASETS):
        return CAVEAT_NO_CDOM_FL_TRUTH
    return ''


def _accuracy(M, O):
    """The §1 accuracy block for an aligned ``(M, O)`` as a dict (+``n``)."""
    b = bias(M, O)
    return {'n': n_valid(M, O), 'mae': mae(M, O), 'bias': b,
            'abs_bias': abs(b) if np.isfinite(b) else np.nan,
            'rms_log': rms_log(M, O), 'median_ratio': median_ratio(M, O)}


def _nearest_within(native, target, tol=REF_TOL):
    """Nearest value in ``native`` to ``target`` within ``tol``; else ``None``."""
    native = np.asarray(native, dtype=float)
    if native.size == 0:
        return None
    i = int(np.argmin(np.abs(native - target)))
    return float(native[i]) if abs(native[i] - target) <= tol else None


def _ref_frame(spectral_df, ref_waves, tol=REF_TOL):
    """Slice spectral rows to the ±``tol`` nm ref-band matches per component.

    Returns a long frame (the same spectral columns) restricted to the
    ref-wavelength bands, with ``ref_wave`` (the nominal target) and
    ``ref_match`` (the actual native band used) added. Ref bands with no native
    match within tolerance are omitted (not forced).
    """
    out = []
    for dataset, dsub in spectral_df.groupby('dataset'):
        native = np.unique(dsub['wavelength'].to_numpy(dtype=float))
        for component in ACCURACY_COMPONENTS:
            csub = dsub[dsub['component'] == component]
            if csub.empty:
                continue
            for target in ref_waves[_COMPONENT_REFSET[component]]:
                matched = _nearest_within(native, target, tol)
                if matched is None:
                    continue
                rows = csub[np.isclose(csub['wavelength'], matched)].copy()
                rows['ref_wave'] = float(target)
                rows['ref_match'] = matched
                out.append(rows)
    if not out:
        return spectral_df.iloc[0:0].assign(ref_wave=[], ref_match=[])
    return pd.concat(out, ignore_index=True)


def _spectral_metrics(spec):
    """metrics_spectral: §1 accuracy + §4 coverage per native (key, λ)."""
    keys = _KEYS + ['component', 'wavelength']
    out = []
    for kvals, g in spec.groupby(keys, sort=False):
        row = dict(zip(keys, kvals))
        O = g['truth'].to_numpy(dtype=float)
        row.update(_accuracy(g['value'].to_numpy(dtype=float), O))
        row['coverage68'] = coverage(O, g['lo68'], g['hi68'])
        row['coverage95'] = coverage(O, g['lo95'], g['hi95'])
        row['coverage_n'] = coverage_n(O, g['lo68'], g['hi68'])
        out.append(row)
    return pd.DataFrame(out)


def _ref_accuracy_rows(ref):
    """Ref-band §1 accuracy + coverage rows for metrics_scalar."""
    keys = _KEYS + ['component', 'ref_wave', 'ref_match']
    out = []
    for kvals, g in ref.groupby(keys, sort=False):
        row = dict(zip(keys, kvals))
        O = g['truth'].to_numpy(dtype=float)
        row.update(_accuracy(g['value'].to_numpy(dtype=float), O))
        row['coverage68'] = coverage(O, g['lo68'], g['hi68'])
        row['coverage95'] = coverage(O, g['lo95'], g['hi95'])
        # The trial count coverage was actually measured over — not this row's
        # ``n``, which counts finite-and-positive (retrieved, truth) pairs.
        row['coverage_n'] = coverage_n(O, g['lo68'], g['hi68'])
        row['caveat'] = _caveat(row['dataset'], row['component'],
                                row.get('algorithm'))
        out.append(row)
    return pd.DataFrame(out)


def _scalar_var_rows(scalar):
    """Derived-scalar (Chl/a_cdom440/Sdg) §1 accuracy rows for metrics_scalar."""
    out = []
    for var, truth_col in SCALAR_VARS.items():
        if var not in scalar or truth_col not in scalar:
            continue
        for kvals, g in scalar.groupby(_KEYS, sort=False):
            row = dict(zip(_KEYS, kvals))
            row['component'] = var
            row['ref_wave'] = np.nan
            row['ref_match'] = np.nan
            row['caveat'] = ''
            row.update(_accuracy(g[var].to_numpy(dtype=float),
                                 g[truth_col].to_numpy(dtype=float)))
            out.append(row)
    return pd.DataFrame(out)


def _closure_rows(scalar, *, n_sigma, qc_max=CHI2NU_QC_MAX,
                  score_statuses=SCORE_STATUSES):
    """metrics_scalar §2 closure + **coverage** rows (component='Rrs').

    Fit quality is the noise-weighted reduced χ²ᵥ (from ``run``/BING ``stats``):
    ``chi2_nu_median`` + the dof-scaled ``frac_good/overfit/underfit`` band, and
    ``frac_qc_fail`` = fraction of fits that are non-solutions (χ²ᵥ > ``qc_max``).
    The log-space Rrs MAE is intentionally **not** used here — it is ill-defined
    where ``Rrs`` crosses zero (see :data:`CHI2NU_QC_MAX`).

    Unlike every other reduction, this one is grouped over **all** attempted
    rows, so it is where an algorithm's *coverage* is reported: ``n_attempted``,
    one ``frac_<status>`` per :data:`ioptics.records.STATUSES` value,
    ``frac_qc_fail`` and ``rel_misfit_median_all``. The remaining columns are
    computed from the scored subset (``score_statuses``) and describe ``n`` of
    those ``n_attempted`` spectra. An algorithm that fits nothing therefore
    still gets a row — with ``frac_fit_failed = 1`` — rather than vanishing
    from the table.

    Note the pairing of the two fit-quality measures. ``chi2_nu_median`` is
    noise-weighted, so it answers "does the model agree with the data to within
    the stated uncertainty" and moves whenever that uncertainty is re-stated.
    ``rel_misfit_median`` answers "how far off is it, in fractions of the
    observation" and does not. Read together they separate a misfit from a
    mis-stated error bar; either alone can mislead.
    """
    out = []
    for kvals, g in scalar.groupby(_KEYS, sort=False):
        row = dict(zip(_KEYS, kvals))
        row['component'] = 'Rrs'
        row['ref_wave'] = np.nan
        row['ref_match'] = np.nan
        row['caveat'] = ''
        # Coverage: over every attempted row in this group.
        status = (g['status'] if 'status' in g else
                  pd.Series(['ok'] * len(g), index=g.index)).to_numpy()
        row['n_attempted'] = int(status.size)
        for name in records.STATUSES:
            row[f'frac_{name}'] = (float(np.mean(status == name))
                                   if status.size else np.nan)
        # frac_qc_fail keeps its original meaning -- the share of *attempted*
        # fits that are non-solutions. Computed on the scored subset it would
        # be identically zero, since 'ok' is *defined* by chi2_nu <= qc_max,
        # and a table reading "0% QC fail" beside 10% coverage would be a lie
        # of omission.
        cn_all = g['chi2_nu'].to_numpy(dtype=float)
        row['frac_qc_fail'] = (float(np.mean(cn_all > qc_max))
                               if cn_all.size else np.nan)
        # Relative misfit, reported over **all attempted** fits as well as over
        # the scored ones. Unlike chi-squared it needs no noise model, so it is
        # the one closure number that stays comparable when the assumed error
        # changes -- and the all-attempted figure is the honest one for a
        # dataset most of whose spectra are not solutions.
        if REL_MISFIT_COL in g:
            rm_all = g[REL_MISFIT_COL].to_numpy(dtype=float)
            row['rel_misfit_median_all'] = (float(np.nanmedian(rm_all))
                                            if rm_all.size else np.nan)
        # Closure: over the scored rows only -- these describe the solutions.
        g = g[np.isin(status, list(score_statuses))]
        cn = g['chi2_nu'].to_numpy(dtype=float)
        dof = (g['n_bands'].to_numpy(dtype=float)
               - g['k'].to_numpy(dtype=float))
        labels = np.array([chi2nu_quality(c, d, n_sigma=n_sigma)
                           for c, d in zip(cn, dof)])
        nq = labels.size
        row['n'] = int(nq)
        row['chi2_nu_median'] = float(np.nanmedian(cn)) if nq else np.nan
        row['frac_good'] = float(np.mean(labels == 'good')) if nq else np.nan
        row['frac_overfit'] = float(np.mean(labels == 'overfit')) if nq else np.nan
        row['frac_underfit'] = float(np.mean(labels == 'underfit')) if nq else np.nan
        if REL_MISFIT_COL in g:
            rm = g[REL_MISFIT_COL].to_numpy(dtype=float)
            row['rel_misfit_median'] = (float(np.nanmedian(rm)) if rm.size
                                        else np.nan)
        out.append(row)
    return pd.DataFrame(out)


def _configured_pair(dbic_pair):
    """``dbic_pair`` as an unordered frozenset, or ``None`` if unusable."""
    if not dbic_pair:
        return None
    pair = tuple(dbic_pair)
    return frozenset(pair) if len(pair) == 2 else None


def _pairwise_metrics(ref, scalar, *, dbic_pair):
    """metrics_pairwise: §5 wins (per component/ref) + §3 ΔBIC contest."""
    frames = []
    # §5 wins — per-spectrum head-to-head at each ref band.
    if not ref.empty:
        w = wins(ref, by=('dataset', 'fit_method', 'stratum', 'component',
                          'ref_wave'))
        if not w.empty:
            w = rankings(w, by=('dataset', 'fit_method', 'stratum',
                                'component', 'ref_wave'),
                         lower_is_better=(), higher_is_better=('win_frac',))
            w['contest'] = 'wins'
            frames.append(w)
    # §5 head-to-head: per-**pair** contests with a tie-capable verdict. Kept
    # alongside `wins` (which reports one row per algorithm) because only the
    # paired form can answer "are these two distinguishable at this n".
    if not ref.empty:
        h2h = head_to_head(ref)
        if not h2h.empty:
            frames.append(h2h)

    # §3 ΔBIC contest (like-for-like χ²), overall + per stratum. Run for **every**
    # algorithm pair, not just the configured one: a sweep whose algorithms are
    # not the configured pair used to get no ΔBIC row at all (and a page with a
    # blank panel plus prose about an algorithm that never ran).
    #
    # ``dbic_pair`` therefore does not *select* which contests run — it names the
    # one the sweep exists to answer, and each row records whether it is that one
    # in ``configured``. Before this the parameter was accepted and then read by
    # nobody, so a caller could ask for a contest and get no signal back that the
    # request had landed (the same "apply or reject" failure the per-algorithm
    # overrides had). A sweep whose configured pair does not appear at all —
    # because one of the two algorithms failed everywhere — is then visible as
    # "no row has configured=True" rather than invisible.
    want = _configured_pair(dbic_pair)
    rows = []
    for kvals, g in scalar.groupby(['dataset', 'fit_method', 'stratum'],
                                   sort=False):
        present = sorted(g['algorithm'].dropna().unique())
        pairs = [(a, b) for i, a in enumerate(present) for b in present[i + 1:]]
        for a, b in pairs:
            res = dbic_cdf(g, a, b, fit_method=None)   # fit_method already a key
            if res['n'] == 0:
                continue
            rows.append({
                'dataset': kvals[0], 'fit_method': kvals[1], 'stratum': kvals[2],
                'contest': 'dbic', 'model_a': a, 'model_b': b, 'n': res['n'],
                'frac_favor_a': res['frac_favor_a'],
                'frac_favor_b': res['frac_favor_b'],
                'median_dbic': float(np.median(res['dbic'])),
                'configured': want is not None and frozenset((a, b)) == want,
            })
    if rows:
        frames.append(pd.DataFrame(rows))
    return (pd.concat(frames, ignore_index=True) if frames
            else pd.DataFrame())


_STATUS_KEYS = ['dataset', 'obs_id', 'algorithm', 'fit_method']


def _with_status(spectral_df, scalar_df):
    """Carry each row's ``status`` from the scalar table onto the spectral one.

    ``status`` is a property of the *fit*, so it lives on ``results_scalar``
    (one row per fit) while ``results_spectral`` holds many rows per fit.
    Joining it across lets both tables be filtered by the same rule. Rows with
    no matching scalar row (there should be none) are left ``'ok'`` so a join
    slip cannot silently drop data.
    """
    if 'status' in spectral_df.columns or 'status' not in scalar_df.columns:
        return spectral_df
    out = spectral_df.merge(scalar_df[_STATUS_KEYS + ['status']],
                            on=_STATUS_KEYS, how='left')
    out['status'] = out['status'].fillna('ok')
    return out


def _scored(df, statuses):
    """Rows whose ``status`` is scorable (everything, if there is no column)."""
    if 'status' not in df.columns:
        return df
    return df[df['status'].isin(list(statuses))]


REL_MISFIT_COL = 'rel_misfit'


def _rel_misfit_map(spectral_df):
    """Per-fit :func:`rel_misfit` from the ``Rrs_model`` / ``Rrs_obs`` rows.

    Both live in ``results_spectral`` (``Rrs_obs`` is the observation the fit
    saw, carried there precisely so closure can be scored without re-reading
    the dataset), so this is a pure table reduction. Returns a frame keyed by
    :data:`_STATUS_KEYS` with one :data:`REL_MISFIT_COL` column; empty if the
    sweep predates ``Rrs_obs``.
    """
    need = {'Rrs_model', 'Rrs_obs'}
    if not need <= set(spectral_df.get('component', pd.Series(dtype=str))):
        return pd.DataFrame()
    cols = _STATUS_KEYS + ['wavelength', 'value']
    mod = spectral_df[spectral_df['component'] == 'Rrs_model'][cols]
    obs = (spectral_df[spectral_df['component'] == 'Rrs_obs'][cols]
           .rename(columns={'value': 'obs'}))
    both = mod.merge(obs, on=_STATUS_KEYS + ['wavelength'])
    rows = []
    for kvals, g in both.groupby(_STATUS_KEYS, sort=False):
        row = dict(zip(_STATUS_KEYS, kvals))
        row[REL_MISFIT_COL] = rel_misfit(g['value'].to_numpy(dtype=float),
                                         g['obs'].to_numpy(dtype=float))
        rows.append(row)
    return pd.DataFrame(rows)


def compute(sweep_id, *, root=None, levels=(0.68, 0.95), ref_waves=REF_WAVES,
            ref_tol=REF_TOL, n_sigma=2.0, chi2nu_qc_max=CHI2NU_QC_MAX,
            dbic_pair=('expb_pow', 'giop'), score_statuses=SCORE_STATUSES,
            write=True):
    """Score a sweep: read its results tables and emit the metrics tables.

    Reads ``runs/<sweep_id>/results_{spectral,scalar}.parquet`` via
    :func:`ioptics.io.read_results`, then computes — grouped by ``fit_method``
    (so the χ² population and the MCMC subset are scored separately, and the
    ΔBIC contest stays like-for-like) and over the **intersection** (only
    non-NaN/positive ``(M, O)`` pairs, with ``n`` recorded) — three tidy tables:

    - **metrics_spectral** — per ``(dataset, algorithm, fit_method, stratum,
      component, wavelength)``: §1 accuracy (``mae``/``bias``/``rms_log``/
      ``median_ratio``) + §4 ``coverage68``/``coverage95``, over the native grid.
    - **metrics_scalar** — per ``(dataset, algorithm, fit_method, stratum,
      component, ref_wave)``: the ±``ref_tol`` nm **ref-band** §1 accuracy (the
      matched band recorded in ``ref_match``) for spectral components, the
      derived-scalar accuracy (``Chl``/``a_cdom440``/``Sdg``, ``ref_wave`` NaN),
      and the §2 **closure** row (``component='Rrs'``: χ²ᵥ ``chi2_nu_median`` +
      ``frac_good/overfit/underfit`` + ``frac_qc_fail`` = fraction with
      χ²ᵥ > ``chi2nu_qc_max``, the noise-model-free ``rel_misfit_median`` /
      ``rel_misfit_median_all`` (:func:`rel_misfit`), plus the coverage block
      ``n_attempted`` + ``frac_<status>``); accuracy metrics carry
      cross-algorithm ranks. Rows whose truth does not mean what the column
      header implies are flagged ``caveat`` (see :func:`_caveat`: GLORIA
      ``a_dg``, and a CDOM-fluorescence algorithm on a dataset with no
      CDOM-fluorescence truth).
    - **metrics_pairwise** — §5 ``wins`` head-to-head per ``(dataset,
      fit_method, stratum, component, ref_wave)`` and the §3 ΔBIC contest per
      ``(dataset, fit_method, stratum)``, run over **every** algorithm pair
      present. ``dbic_pair`` (default ``expb_pow`` vs ``giop``) names the
      contest the sweep exists to answer; its rows are marked
      ``configured = True``, so "the pair I asked for was scored" is a table
      lookup rather than an assumption.

    **Only rows whose ``status`` is in ``score_statuses`` are scored**
    (default :data:`SCORE_STATUSES`, i.e. ``'ok'`` alone). The rest are
    reported as coverage on the closure row and otherwise excluded — a
    ``poor_fit`` or ``fit_failed`` retrieval is not a solution, and averaging
    one in makes each algorithm's number a median over its own private subset
    of spectra. Pass ``score_statuses=records.STATUSES`` to score everything.

    Strata are Chl bins (:data:`CHL_BINS`) assigned from truth Chl where
    available (else retrieved); every reduction is emitted for ``stratum='all'``
    **and** each bin. With ``write=True`` the tables are written under
    :func:`ioptics.io.sweep_dir`. Returns a :class:`MetricsTables` namedtuple.
    """
    spectral_df, scalar_df = io.read_results(sweep_id, root=root)
    spectral_df = _with_status(spectral_df, scalar_df)

    # Per-fit relative misfit rides along on the scalar frame, so the closure
    # row can reduce it exactly like chi^2 (per key, scored and attempted).
    # Since 2026-08-12 ``results_scalar`` persists it at fit time (Task-4 A2),
    # so the spectral-table reduction is the fallback: prefer the persisted
    # value, fill anything missing (older sweeps, synthetic fixtures) from the
    # reduction — a plain merge would collide on the shared column name.
    rm = _rel_misfit_map(spectral_df)
    if not rm.empty:
        if REL_MISFIT_COL in scalar_df.columns:
            fallback = rm.rename(columns={REL_MISFIT_COL: '_rm_spectral'})
            scalar_df = scalar_df.merge(fallback, on=_STATUS_KEYS, how='left')
            scalar_df[REL_MISFIT_COL] = scalar_df[REL_MISFIT_COL].fillna(
                scalar_df.pop('_rm_spectral'))
        else:
            scalar_df = scalar_df.merge(rm, on=_STATUS_KEYS, how='left')

    strata = _strata_map(scalar_df)
    spectral_df = spectral_df.merge(strata, on=['dataset', 'obs_id'], how='left')
    scalar_df = scalar_df.merge(strata, on=['dataset', 'obs_id'], how='left')

    # Every reduction below scores solutions only; the closure row is the one
    # exception (it reports the coverage of the rest), so it keeps the full frame.
    scal_all = _scoped(scalar_df)
    spec_scoped = _scored(_scoped(spectral_df), score_statuses)
    scal_scoped = _scored(scal_all, score_statuses)

    # §1 accuracy needs a truth; Rrs_model/Rrs_obs (truth NaN) drop out here.
    acc_spec = spec_scoped[spec_scoped['component'].isin(ACCURACY_COMPONENTS)]
    metrics_spectral = _spectral_metrics(acc_spec)

    ref = _ref_frame(spec_scoped, ref_waves, ref_tol)

    scalar_parts = [p for p in (_ref_accuracy_rows(ref),
                                _scalar_var_rows(scal_scoped)) if not p.empty]
    # A sweep in which *every* fit failed has nothing to score — which is a real
    # state (the GLORIA runs before the iteration budget was raised failed 72 of
    # 100), and `pd.concat([])` raises, so it must not reach the concat.
    scalar_acc = (pd.concat(scalar_parts, ignore_index=True) if scalar_parts
                  else pd.DataFrame())
    if not scalar_acc.empty:
        scalar_acc = rankings(
            scalar_acc,
            by=('dataset', 'fit_method', 'stratum', 'component', 'ref_wave'))

    closure = _closure_rows(scal_all, n_sigma=n_sigma,
                            qc_max=chi2nu_qc_max,
                            score_statuses=score_statuses)

    metrics_scalar = pd.concat(
        [df for df in (scalar_acc, closure) if not df.empty],
        ignore_index=True)

    metrics_pairwise = _pairwise_metrics(ref, scal_scoped, dbic_pair=dbic_pair)

    metrics_spectral = _stamp_provenance(metrics_spectral, sweep_id)
    metrics_scalar = _stamp_provenance(metrics_scalar, sweep_id)
    metrics_pairwise = _stamp_provenance(metrics_pairwise, sweep_id)

    tables = MetricsTables(metrics_spectral, metrics_scalar, metrics_pairwise)
    if write:
        d = io.sweep_dir(sweep_id, root=root, create=True)
        tables.spectral.to_parquet(d / METRICS_SPECTRAL_FILE, index=False)
        tables.scalar.to_parquet(d / METRICS_SCALAR_FILE, index=False)
        tables.pairwise.to_parquet(d / METRICS_PAIRWISE_FILE, index=False)
    return tables

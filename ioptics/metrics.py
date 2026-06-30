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

from collections import namedtuple

import numpy as np
import pandas as pd

from ioptics import io

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

# Default Rrs-closure thresholds (Erickson dual-sided window). Configurable per
# call; ``compute`` records the values it used (Q&A). ``NOISE_FLOOR`` ≈ the ~5%
# measurement-noise level a good fit sits at; ``FIT_NOISE_FACTOR`` × that is the
# "well below the noise floor" over-fitting threshold; ``RRS_QC_MAX`` marks
# non-solutions.
NOISE_FLOOR = 0.05
FIT_NOISE_FACTOR = 0.5
RRS_QC_MAX = 0.25


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
             keys=('dataset', 'obs_id')):
    """Per-spectrum ΔBIC contest between two algorithms, as a CDF.

    Pairs ``model_a`` vs ``model_b`` rows of ``results_scalar`` on the common
    spectrum keys (``dataset``, ``obs_id``) **like-for-like** within a single
    ``fit_method`` (default ``'chisq'``, since ``expb_pow`` is χ²-only), and
    computes ΔBIC = ``BIC(model_a) - BIC(model_b)`` per matched spectrum.

    Returns ``dict(dbic, cdf, n, frac_favor_a, frac_favor_b)`` where ``dbic`` is
    sorted ascending, ``cdf`` is the matching empirical CDF in ``[0, 1]``,
    ``frac_favor_a`` is the fraction with ΔBIC < 0 (model A wins) and
    ``frac_favor_b`` the fraction with ΔBIC > 0 (ties favor neither). If ``by``
    is given (a column name), returns ``{stratum: dict(...)}`` per group.
    """
    if fit_method is not None and 'fit_method' in df.columns:
        df = df[df['fit_method'] == fit_method]

    if by is not None:
        out = {}
        for stratum, sub in df.groupby(by):
            out[stratum] = dbic_cdf(sub, model_a, model_b, by=None,
                                    fit_method=None, bic_col=bic_col,
                                    algo_col=algo_col, keys=keys)
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


def _caveat(dataset, component):
    """GLORIA ``a_dg`` vs ``a_cdom440`` truth-mapping caveat flag (else '')."""
    if str(dataset).upper().startswith('GLORIA') and component == 'a_dg':
        return 'CDOM_vs_adg'
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
        row['caveat'] = _caveat(row['dataset'], row['component'])
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


def _rrs_per_obs(spec, *, noise_floor, fit_noise_factor, qc_max):
    """Per-obs Rrs closure (Rrs_model vs Rrs_obs) for the §2 aggregation."""
    mod = spec[spec['component'] == 'Rrs_model']
    obs = spec[spec['component'] == 'Rrs_obs']
    if mod.empty or obs.empty:
        return pd.DataFrame()
    on = ['dataset', 'obs_id', 'algorithm', 'fit_method', 'stratum',
          'wavelength']
    merged = mod.merge(obs, on=on, suffixes=('_mod', '_obs'))
    out = []
    okeys = ['dataset', 'obs_id', 'algorithm', 'fit_method', 'stratum']
    for kvals, g in merged.groupby(okeys, sort=False):
        c = rrs_closure(g['value_mod'].to_numpy(dtype=float),
                        g['value_obs'].to_numpy(dtype=float),
                        noise_floor=noise_floor,
                        fit_noise_factor=fit_noise_factor, qc_max=qc_max)
        out.append({**dict(zip(okeys, kvals)), **c})
    return pd.DataFrame(out)


def _closure_rows(scalar, rrs_obs, *, n_sigma):
    """metrics_scalar closure rows (component='Rrs'): χ²ᵥ quality + Rrs MAE."""
    out = []
    for kvals, g in scalar.groupby(_KEYS, sort=False):
        row = dict(zip(_KEYS, kvals))
        row['component'] = 'Rrs'
        row['ref_wave'] = np.nan
        row['ref_match'] = np.nan
        row['caveat'] = ''
        cn = g['chi2_nu'].to_numpy(dtype=float)
        dof = (g['n_bands'].to_numpy(dtype=float)
               - g['k'].to_numpy(dtype=float))
        labels = [chi2nu_quality(c, d, n_sigma=n_sigma) for c, d in zip(cn, dof)]
        labels = np.array(labels)
        nq = labels.size
        row['n'] = int(nq)
        row['chi2_nu_median'] = float(np.nanmedian(cn)) if nq else np.nan
        row['frac_good'] = float(np.mean(labels == 'good')) if nq else np.nan
        row['frac_overfit'] = float(np.mean(labels == 'overfit')) if nq else np.nan
        row['frac_underfit'] = float(np.mean(labels == 'underfit')) if nq else np.nan
        if not rrs_obs.empty:
            r = rrs_obs.merge(pd.DataFrame([dict(zip(_KEYS, kvals))]), on=_KEYS)
            if not r.empty:
                row['mae'] = float(np.nanmedian(r['rrs_mae']))
                row['bias'] = float(np.nanmedian(r['rrs_bias']))
                row['frac_fit_noise'] = float(np.mean(r['fit_noise']))
                row['frac_qc_fail'] = float(np.mean(r['qc_fail']))
        out.append(row)
    return pd.DataFrame(out)


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
    # §3 ΔBIC contest (like-for-like χ²), overall + per stratum.
    a, b = dbic_pair
    rows = []
    for kvals, g in scalar.groupby(['dataset', 'fit_method', 'stratum'],
                                   sort=False):
        res = dbic_cdf(g, a, b, fit_method=None)   # fit_method already a key
        if res['n'] == 0:
            continue
        rows.append({
            'dataset': kvals[0], 'fit_method': kvals[1], 'stratum': kvals[2],
            'contest': 'dbic', 'model_a': a, 'model_b': b, 'n': res['n'],
            'frac_favor_a': res['frac_favor_a'],
            'frac_favor_b': res['frac_favor_b'],
            'median_dbic': float(np.median(res['dbic'])),
        })
    if rows:
        frames.append(pd.DataFrame(rows))
    return (pd.concat(frames, ignore_index=True) if frames
            else pd.DataFrame())


def compute(sweep_id, *, root=None, levels=(0.68, 0.95), ref_waves=REF_WAVES,
            ref_tol=REF_TOL, noise_floor=NOISE_FLOOR,
            fit_noise_factor=FIT_NOISE_FACTOR, rrs_qc_max=RRS_QC_MAX,
            n_sigma=2.0, dbic_pair=('expb_pow', 'giop'), write=True):
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
      and the §2 **closure** row (``component='Rrs'``: χ²ᵥ quality fractions +
      Rrs MAE/bias + ``fit_noise``/``qc_fail`` fractions); accuracy metrics carry
      cross-algorithm ranks. GLORIA ``a_dg`` rows are flagged ``caveat``.
    - **metrics_pairwise** — §5 ``wins`` head-to-head per ``(dataset,
      fit_method, stratum, component, ref_wave)`` and the §3 ΔBIC contest
      (``dbic_pair``, default ``expb_pow`` vs ``giop``) per ``(dataset,
      fit_method, stratum)``.

    Strata are Chl bins (:data:`CHL_BINS`) assigned from truth Chl where
    available (else retrieved); every reduction is emitted for ``stratum='all'``
    **and** each bin. With ``write=True`` the tables are written under
    :func:`ioptics.io.sweep_dir`. Returns a :class:`MetricsTables` namedtuple.
    """
    spectral_df, scalar_df = io.read_results(sweep_id, root=root)

    strata = _strata_map(scalar_df)
    spectral_df = spectral_df.merge(strata, on=['dataset', 'obs_id'], how='left')
    scalar_df = scalar_df.merge(strata, on=['dataset', 'obs_id'], how='left')

    spec_scoped = _scoped(spectral_df)
    scal_scoped = _scoped(scalar_df)

    # §1 accuracy needs a truth; Rrs_model/Rrs_obs (truth NaN) drop out here.
    acc_spec = spec_scoped[spec_scoped['component'].isin(ACCURACY_COMPONENTS)]
    metrics_spectral = _spectral_metrics(acc_spec)

    ref = _ref_frame(spec_scoped, ref_waves, ref_tol)

    scalar_parts = [_ref_accuracy_rows(ref), _scalar_var_rows(scal_scoped)]
    # rank the accuracy rows across algorithms within each variable/ref/stratum.
    scalar_acc = pd.concat([p for p in scalar_parts if not p.empty],
                           ignore_index=True)
    if not scalar_acc.empty:
        scalar_acc = rankings(
            scalar_acc,
            by=('dataset', 'fit_method', 'stratum', 'component', 'ref_wave'))

    rrs_obs = _rrs_per_obs(spec_scoped, noise_floor=noise_floor,
                           fit_noise_factor=fit_noise_factor, qc_max=rrs_qc_max)
    closure = _closure_rows(scal_scoped, rrs_obs, n_sigma=n_sigma)

    metrics_scalar = pd.concat(
        [df for df in (scalar_acc, closure) if not df.empty],
        ignore_index=True)

    metrics_pairwise = _pairwise_metrics(ref, scal_scoped, dbic_pair=dbic_pair)

    tables = MetricsTables(metrics_spectral, metrics_scalar, metrics_pairwise)
    if write:
        d = io.sweep_dir(sweep_id, root=root, create=True)
        tables.spectral.to_parquet(d / METRICS_SPECTRAL_FILE, index=False)
        tables.scalar.to_parquet(d / METRICS_SCALAR_FILE, index=False)
        tables.pairwise.to_parquet(d / METRICS_PAIRWISE_FILE, index=False)
    return tables

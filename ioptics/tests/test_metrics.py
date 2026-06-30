"""Tier-1 tests for ``ioptics.metrics`` §1 accuracy primitives and the §2/§3
closure + model-selection functions.

Pure ``(M, O)`` arrays and a tiny hand-built scalar table with hand-computed
answers — no models, no data, no engine. Exercises the log10/multiplicative
forms, the NaN-drop (intersection) rule, the Rrs dual-sided window, and the
ΔBIC per-spectrum contest / CDF.
"""

import numpy as np
import pandas as pd

from ioptics import io, metrics
from ioptics.records import ComponentFit, PreparedRecord, RetrievalResult
from ioptics.tests.conftest import needs_l23


def test_perfect_agreement():
    """M == O: zero error, unit ratio, slope-1 / r2-1 regression."""
    O = np.array([0.1, 0.2, 0.4, 0.8])
    M = O.copy()
    assert metrics.mae(M, O) == 0.0
    assert metrics.bias(M, O) == 0.0
    assert metrics.rms_log(M, O) == 0.0
    assert metrics.median_ratio(M, O) == 1.0
    slope, intercept, r2 = metrics.type2_fit(M, O)
    assert np.isclose(slope, 1.0)
    assert np.isclose(intercept, 0.0)
    assert np.isclose(r2, 1.0)


def test_constant_factor():
    """M = 2 O everywhere: multiplicative MAE/bias = 1.0, rms_log = log10(2)."""
    O = np.array([0.05, 0.1, 0.2, 0.3])
    M = 2.0 * O
    assert np.isclose(metrics.mae(M, O), 1.0)
    assert np.isclose(metrics.bias(M, O), 1.0)
    assert np.isclose(metrics.rms_log(M, O), np.log10(2.0))
    assert np.isclose(metrics.median_ratio(M, O), 2.0)


def test_bias_sign():
    """Under-estimate (M = O/2) gives a negative signed bias."""
    O = np.array([0.1, 0.2, 0.4])
    M = O / 2.0
    assert np.isclose(metrics.bias(M, O), 0.5 - 1.0)   # 10**(-log10 2) - 1
    assert np.isclose(metrics.mae(M, O), 1.0)          # magnitude is symmetric


def test_ratio_hist_buckets():
    """One ratio per bucket -> all-ones count vector (8 RATIO_EDGES bins)."""
    O = np.ones(8)
    M = np.array([0.25, 0.4, 0.6, 0.8, 1.0, 1.5, 2.5, 5.0])
    counts = metrics.ratio_hist(M, O)
    assert counts.tolist() == [1, 1, 1, 1, 1, 1, 1, 1]
    assert counts.sum() == 8


def test_type2_fit_known_line():
    """M = c * O in linear space -> slope 1, intercept log10(c), r2 = 1."""
    O = np.array([0.01, 0.05, 0.1, 0.5, 1.0])
    c = 3.0
    M = c * O
    slope, intercept, r2 = metrics.type2_fit(M, O)
    assert np.isclose(slope, 1.0)
    assert np.isclose(intercept, np.log10(c))
    assert np.isclose(r2, 1.0)


def test_nan_drop_intersection():
    """NaN in either M or O drops that pair before the reduction."""
    M = np.array([1.0, 2.0, np.nan, 4.0])
    O = np.array([1.0, 2.0, 3.0, np.nan])
    assert metrics.n_valid(M, O) == 2
    assert metrics.mae(M, O) == 0.0          # surviving pairs (1,1),(2,2) agree
    assert metrics.median_ratio(M, O) == 1.0


def test_empty_returns_nan():
    """No surviving pairs -> NaN scalars, NaN regression triple."""
    M = np.array([np.nan, np.nan])
    O = np.array([1.0, 2.0])
    assert metrics.n_valid(M, O) == 0
    assert np.isnan(metrics.mae(M, O))
    assert np.isnan(metrics.bias(M, O))
    assert np.isnan(metrics.rms_log(M, O))
    assert np.isnan(metrics.median_ratio(M, O))
    assert all(np.isnan(v) for v in metrics.type2_fit(M, O))


def test_nonpositive_dropped():
    """Zero/negative values in either array are dropped like NaN (log-space)."""
    M = np.array([1.0, 0.0, -2.0, 4.0])
    O = np.array([1.0, 3.0, 5.0, 4.0])
    assert metrics.n_valid(M, O) == 2          # only (1,1) and (4,4) survive
    assert metrics.mae(M, O) == 0.0


def test_shape_mismatch_raises():
    import pytest
    with pytest.raises(ValueError):
        metrics.mae(np.ones(3), np.ones(4))


# --------------------------------------------------------------------------- #
# §2 Rrs closure + fit quality
# --------------------------------------------------------------------------- #

def test_chi2nu_quality_dof_band():
    # dof=8, n_sigma=1 -> half-width sqrt(2/8)=0.5 -> band (0.5, 1.5).
    assert metrics.chi2nu_quality(1.0, dof=8, n_sigma=1) == 'good'
    assert metrics.chi2nu_quality(0.2, dof=8, n_sigma=1) == 'overfit'
    assert metrics.chi2nu_quality(3.0, dof=8, n_sigma=1) == 'underfit'
    assert metrics.chi2nu_quality(0.49, dof=8, n_sigma=1) == 'overfit'
    assert metrics.chi2nu_quality(1.51, dof=8, n_sigma=1) == 'underfit'
    # invalid inputs
    assert metrics.chi2nu_quality(np.nan, dof=8) == 'unknown'
    assert metrics.chi2nu_quality(1.0, dof=0) == 'unknown'


def test_chi2nu_band_tightens_with_dof():
    # A χ²ᵥ of 1.6 is 'good' with few bands (wide band) but 'underfit' with many.
    assert metrics.chi2nu_quality(1.6, dof=2) == 'good'        # half = 2*1.0 = 2
    assert metrics.chi2nu_quality(1.6, dof=200) == 'underfit'  # half = 2*0.1 = 0.2


def test_rrs_window_flags():
    # fit_noise threshold = 0.5 * 0.05 = 0.025; qc_fail at > 0.25.
    assert metrics.rrs_window(0.01) == {'fit_noise': True, 'qc_fail': False}
    assert metrics.rrs_window(0.10) == {'fit_noise': False, 'qc_fail': False}
    assert metrics.rrs_window(0.30) == {'fit_noise': False, 'qc_fail': True}
    assert metrics.rrs_window(np.nan) == {'fit_noise': False, 'qc_fail': False}
    # thresholds are configurable
    assert metrics.rrs_window(0.04, noise_floor=0.1,
                              fit_noise_factor=0.5)['fit_noise'] is True


def test_rrs_closure_perfect():
    """Identical model/obs -> zero MAE/bias, flagged fit_noise (below floor)."""
    Rrs = np.array([0.01, 0.008, 0.006, 0.004])
    out = metrics.rrs_closure(Rrs, Rrs)
    assert out['rrs_mae'] == 0.0
    assert out['rrs_bias'] == 0.0
    assert out['n'] == 4
    assert out['fit_noise'] is True and out['qc_fail'] is False


def test_rrs_closure_qc_fail():
    """A 2x model overshoot (MAE = 1.0) trips the QC-fail flag."""
    Rrs_obs = np.array([0.01, 0.008, 0.006])
    out = metrics.rrs_closure(2.0 * Rrs_obs, Rrs_obs)
    assert np.isclose(out['rrs_mae'], 1.0)
    assert out['qc_fail'] is True


# --------------------------------------------------------------------------- #
# §3 Model selection / ΔBIC
# --------------------------------------------------------------------------- #

def test_delta_bic_sign():
    # A lower BIC than B -> negative -> favors A (the more complex model).
    assert metrics.delta_bic(10.0, 15.0) == -5.0
    np.testing.assert_array_equal(
        metrics.delta_bic([10.0, 20.0], [15.0, 10.0]), [-5.0, 10.0])


def _two_algo_scalar():
    """Three matched spectra: expb_pow beats giop on 2 of 3 by BIC."""
    rows = []
    bics = {'expb_pow': [10.0, 12.0, 20.0], 'giop': [15.0, 15.0, 10.0]}
    for algo, bb in bics.items():
        for obs_id, b in enumerate(bb):
            rows.append({'dataset': 'L23', 'obs_id': obs_id, 'algorithm': algo,
                         'fit_method': 'chisq', 'BIC': b})
    return pd.DataFrame(rows)


def test_dbic_cdf_contest():
    df = _two_algo_scalar()
    out = metrics.dbic_cdf(df, 'expb_pow', 'giop')
    # ΔBIC per spectrum: -5, -3, +10 -> two favor expb_pow (A), one favors giop.
    np.testing.assert_array_equal(out['dbic'], [-5.0, -3.0, 10.0])
    assert out['n'] == 3
    assert np.isclose(out['frac_favor_a'], 2 / 3)
    assert np.isclose(out['frac_favor_b'], 1 / 3)
    # CDF is the empirical step heights.
    np.testing.assert_allclose(out['cdf'], [1 / 3, 2 / 3, 1.0])


def test_dbic_cdf_filters_fit_method():
    """MCMC rows are excluded from the like-for-like χ² contest."""
    df = _two_algo_scalar()
    extra = df[df['algorithm'] == 'expb_pow'].copy()
    extra['fit_method'] = 'mcmc'
    extra['BIC'] = 999.0
    df2 = pd.concat([df, extra], ignore_index=True)
    out = metrics.dbic_cdf(df2, 'expb_pow', 'giop')      # default fit_method='chisq'
    np.testing.assert_array_equal(out['dbic'], [-5.0, -3.0, 10.0])


def test_dbic_cdf_stratified():
    df = _two_algo_scalar()
    df['stratum'] = ['oligotrophic', 'oligotrophic', 'eutrophic'] * 2
    out = metrics.dbic_cdf(df, 'expb_pow', 'giop', by='stratum')
    assert set(out) == {'oligotrophic', 'eutrophic'}
    assert out['oligotrophic']['n'] == 2
    assert out['eutrophic']['n'] == 1


# --------------------------------------------------------------------------- #
# §4 Coverage + detection
# --------------------------------------------------------------------------- #

def test_coverage_levels():
    O = np.array([1.0, 2.0, 3.0, 4.0])
    # all inside a wide band -> 1.0
    assert metrics.coverage(O, np.full(4, 0.0), np.full(4, 5.0)) == 1.0
    # only O=2 lands in [1.5, 2.5] -> 0.25
    assert metrics.coverage(O, np.full(4, 1.5), np.full(4, 2.5)) == 0.25
    # bounds are inclusive
    assert metrics.coverage(np.array([2.0]), np.array([2.0]),
                            np.array([2.0])) == 1.0


def test_coverage_nan_drop():
    O = np.array([1.0, np.nan, 3.0])
    lo = np.array([0.0, 0.0, 0.0])
    hi = np.array([2.0, 2.0, 2.0])      # surviving: O=1 in, O=3 out -> 0.5
    assert metrics.coverage(O, lo, hi) == 0.5
    assert np.isnan(metrics.coverage(np.array([np.nan]), np.array([0.0]),
                                     np.array([1.0])))


def test_detection_upper_limit():
    med = np.array([0.10, 0.05, 0.02])
    lo = np.array([0.02, -0.01, 0.00])   # only the first excludes zero (lo>0)
    hi = np.array([0.20, 0.15, 0.08])
    out = metrics.detection(med, lo, hi)
    np.testing.assert_array_equal(out['detected'], [True, False, False])
    np.testing.assert_array_equal(out['upper_limit'], [np.nan, 0.15, 0.08])


# --------------------------------------------------------------------------- #
# §5 Wins + rankings
# --------------------------------------------------------------------------- #

def _wins_table():
    """Two algorithms, one group, three spectra; truth = 1.0 throughout."""
    rows = []
    vals = {'A': [1.0, 1.0, 10.0], 'B': [2.0, 2.0, 1.0]}
    for algo, vv in vals.items():
        for obs_id, v in enumerate(vv):
            rows.append({'dataset': 'L23', 'component': 'a', 'ref_wave': 440,
                         'obs_id': obs_id, 'algorithm': algo,
                         'value': v, 'truth': 1.0})
    return pd.DataFrame(rows)


def test_wins_head_to_head():
    out = metrics.wins(_wins_table())
    out = out.set_index('algorithm')
    # A is exact on obs 0,1 (wins) but off by 10x on obs 2 (loses) -> 2/3.
    assert out.loc['A', 'wins'] == 2 and out.loc['A', 'contests'] == 3
    assert np.isclose(out.loc['A', 'win_frac'], 2 / 3)
    assert out.loc['B', 'wins'] == 1
    assert np.isclose(out.loc['B', 'win_frac'], 1 / 3)


def test_wins_tie_split():
    """Equal errors split the contest 0.5 / 0.5."""
    df = pd.DataFrame({
        'dataset': ['L23'] * 2, 'component': ['a'] * 2, 'ref_wave': [440] * 2,
        'obs_id': [0, 0], 'algorithm': ['A', 'B'], 'abs_log_err': [0.2, 0.2],
    })
    out = metrics.wins(df).set_index('algorithm')
    assert out.loc['A', 'wins'] == 0.5 and out.loc['B', 'wins'] == 0.5
    assert out.loc['A', 'win_frac'] == 0.5


def test_wins_precomputed_metric():
    """An explicit abs_log_err column is used directly (no value/truth needed)."""
    df = pd.DataFrame({
        'dataset': ['L23'] * 4, 'component': ['a'] * 4, 'ref_wave': [440] * 4,
        'obs_id': [0, 0, 1, 1], 'algorithm': ['A', 'B', 'A', 'B'],
        'abs_log_err': [0.1, 0.2, 0.3, 0.1],
    })
    out = metrics.wins(df).set_index('algorithm')
    assert out.loc['A', 'wins'] == 1 and out.loc['B', 'wins'] == 1


def test_rankings():
    df = pd.DataFrame({
        'dataset': ['L23'] * 3, 'component': ['a'] * 3,
        'algorithm': ['A', 'B', 'C'],
        'mae': [0.1, 0.2, 0.3], 'win_frac': [0.6, 0.3, 0.1],
    })
    out = metrics.rankings(df).set_index('algorithm')
    # mae: lower is better -> A=1, B=2, C=3
    assert out.loc['A', 'mae_rank'] == 1 and out.loc['C', 'mae_rank'] == 3
    # win_frac: higher is better -> A=1, C=3
    assert out.loc['A', 'win_frac_rank'] == 1 and out.loc['C', 'win_frac_rank'] == 3


def test_rankings_ties_share_best():
    df = pd.DataFrame({
        'dataset': ['L23'] * 3, 'component': ['a'] * 3,
        'algorithm': ['A', 'B', 'C'], 'mae': [0.1, 0.1, 0.3],
    })
    out = metrics.rankings(df).set_index('algorithm')
    assert out.loc['A', 'mae_rank'] == 1 and out.loc['B', 'mae_rank'] == 1
    assert out.loc['C', 'mae_rank'] == 3       # method='min' -> next is 3


# --------------------------------------------------------------------------- #
# compute() orchestration — synthetic results table -> metrics tables (Tier-1)
# --------------------------------------------------------------------------- #

_WAVE = np.array([440.0, 443.0, 555.0, 670.0])
_BASE = {'a': 0.2, 'bb': 0.02, 'a_ph': 0.08, 'a_dg': 0.06, 'bb_p': 0.012}
_RRS = np.array([0.010, 0.008, 0.006, 0.004])


class _Spec:
    """Minimal spectral-truth stand-in exposing ``.values`` (like ocpy Spectrum)."""

    def __init__(self, values):
        self.values = np.asarray(values, dtype=float)


def _cf(values):
    med = np.asarray(values, dtype=float)
    return ComponentFit(wave=_WAVE, med=med, lo68=med * 0.9, hi68=med * 1.1,
                        lo95=med * 0.8, hi95=med * 1.2)


def _make_pair(obs_id, algo, factor, chl_truth, bic, *,
               fit_method='chisq', rrs_factor=1.0):
    """One (RetrievalResult, PreparedRecord) for the synthetic sweep.

    ``factor`` scales every retrieved value above truth (1.0 = perfect, 2.0 =
    2x over). ``rrs_factor`` scales the model Rrs above the observed Rrs.
    """
    comps = {c: _cf(np.full(_WAVE.size, factor * b)) for c, b in _BASE.items()}
    comps['Rrs_model'] = _cf(rrs_factor * _RRS)
    k = 5 if algo == 'expb_pow' else 3
    result = RetrievalResult(
        dataset='L23', obs_id=obs_id, algorithm=algo, fit_method=fit_method,
        components=comps,
        scalars={'Chl': (factor * chl_truth, 0.1), 'Sdg': (factor * 0.017, 1e-3),
                 'a_cdom440': (factor * _BASE['a_dg'], 1e-3),
                 'beta': (factor * 1.0, 0.1)},
        stats={'chi2': 10.0, 'chi2_nu': 1.0, 'AIC': 30.0, 'BIC': float(bic),
               'n_bands': 10, 'k': k},
        status='ok', provenance_id='p',
        chain_file=None if fit_method == 'chisq' else 'c.npz')
    truth = {c: _Spec(np.full(_WAVE.size, b)) for c, b in _BASE.items()}
    truth.update({'Chl': chl_truth, 'Sdg': 0.017})
    record = PreparedRecord(
        dataset='L23', obs_id=obs_id, wave=_WAVE, Rrs=_RRS,
        varRrs=np.full(_WAVE.size, 1e-6), Rrs_clean=_RRS,
        truth=truth, truth_interp={}, init={'Chl': 1.0, 'Y': 0.5},
        noise_model='pace', noise_seed=1)
    return result, record


def _synthetic_sweep(tmp_path):
    """expb_pow (perfect) vs giop (2x-high) over 4 obs spanning Chl strata."""
    chl = {0: 0.05, 1: 0.5, 2: 2.0, 3: 0.5}            # oligo/meso/eutro/meso
    bic = {'expb_pow': [10, 10, 10, 20], 'giop': [15, 15, 15, 15]}
    pairs = []
    for obs_id in range(4):
        pairs.append(_make_pair(obs_id, 'expb_pow', 1.0, chl[obs_id],
                                bic['expb_pow'][obs_id], rrs_factor=1.0))
        pairs.append(_make_pair(obs_id, 'giop', 2.0, chl[obs_id],
                                bic['giop'][obs_id], rrs_factor=1.5))
    # one MCMC row to exercise fit_method grouping
    pairs.append(_make_pair(0, 'expb_pow', 1.0, chl[0], 10,
                            fit_method='mcmc'))
    io.write_results('sweep_m', pairs, root=tmp_path)
    return metrics.compute('sweep_m', root=tmp_path)


def test_compute_writes_three_tables(tmp_path):
    tables = _synthetic_sweep(tmp_path)
    d = io.sweep_dir('sweep_m', root=tmp_path)
    for fn in (metrics.METRICS_SPECTRAL_FILE, metrics.METRICS_SCALAR_FILE,
               metrics.METRICS_PAIRWISE_FILE):
        assert (d / fn).is_file()
    assert not tables.spectral.empty and not tables.scalar.empty
    assert not tables.pairwise.empty
    # fit_method is a grouping key: both populations are present.
    assert set(tables.spectral['fit_method']) == {'chisq', 'mcmc'}


def test_compute_spectral_accuracy_and_coverage(tmp_path):
    sp = _synthetic_sweep(tmp_path).spectral
    sp = sp[(sp.stratum == 'all') & (sp.component == 'a')
            & (sp.fit_method == 'chisq')]
    expb = sp[sp.algorithm == 'expb_pow'].iloc[0]
    giop = sp[sp.algorithm == 'giop'].iloc[0]
    assert np.isclose(expb['mae'], 0.0) and expb['coverage68'] == 1.0
    assert expb['n'] == 4                          # 4 obs scored at this band
    assert np.isclose(giop['mae'], 1.0)            # 2x high -> multiplicative 1
    assert giop['coverage68'] == 0.0               # truth below the 2x interval


def test_compute_scalar_closure_and_ranks(tmp_path):
    sc = _synthetic_sweep(tmp_path).scalar
    allc = sc[(sc.stratum == 'all') & (sc.fit_method == 'chisq')]
    # §2 closure row (component='Rrs')
    rrs = allc[allc.component == 'Rrs'].set_index('algorithm')
    assert rrs.loc['expb_pow', 'frac_good'] == 1.0
    assert np.isclose(rrs.loc['expb_pow', 'mae'], 0.0)
    assert rrs.loc['expb_pow', 'frac_fit_noise'] == 1.0
    assert np.isclose(rrs.loc['giop', 'mae'], 0.5)       # Rrs 1.5x -> MAE 0.5
    assert rrs.loc['giop', 'frac_qc_fail'] == 1.0
    # ref-band accuracy ranks: expb_pow (mae 0) beats giop.
    a440 = allc[(allc.component == 'a') & (allc.ref_wave == 440.0)]
    a440 = a440.set_index('algorithm')
    assert a440.loc['expb_pow', 'ref_match'] == 440.0
    assert a440.loc['expb_pow', 'mae_rank'] == 1
    assert a440.loc['giop', 'mae_rank'] == 2


def test_compute_pairwise_wins_and_dbic(tmp_path):
    pw = _synthetic_sweep(tmp_path).pairwise
    # §5 wins at (a, 440) overall: expb_pow closer on every contest.
    w = pw[(pw.contest == 'wins') & (pw.stratum == 'all')
           & (pw.component == 'a') & (pw.ref_wave == 440.0)
           & (pw.fit_method == 'chisq')].set_index('algorithm')
    assert w.loc['expb_pow', 'win_frac'] == 1.0
    assert w.loc['giop', 'win_frac'] == 0.0
    assert w.loc['expb_pow', 'win_frac_rank'] == 1
    # §3 ΔBIC contest overall: expb_pow favored on 3 of 4 spectra.
    db = pw[(pw.contest == 'dbic') & (pw.stratum == 'all')
            & (pw.fit_method == 'chisq')].iloc[0]
    assert db['model_a'] == 'expb_pow' and db['n'] == 4
    assert np.isclose(db['frac_favor_a'], 0.75)


def test_compute_strata_present(tmp_path):
    sc = _synthetic_sweep(tmp_path).scalar
    strata = set(sc['stratum'])
    assert {'all', 'oligotrophic', 'mesotrophic', 'eutrophic'} <= strata


def test_compute_parquet_roundtrip(tmp_path):
    """Exit criterion: the three parquet files re-read and carry ΔBIC + wins."""
    tables = _synthetic_sweep(tmp_path)
    d = io.sweep_dir('sweep_m', root=tmp_path)
    sp = pd.read_parquet(d / metrics.METRICS_SPECTRAL_FILE)
    sc = pd.read_parquet(d / metrics.METRICS_SCALAR_FILE)
    pw = pd.read_parquet(d / metrics.METRICS_PAIRWISE_FILE)
    # persisted == returned
    assert len(sp) == len(tables.spectral) and len(sc) == len(tables.scalar)
    assert len(pw) == len(tables.pairwise)
    # schema spot-checks
    assert {'mae', 'bias', 'coverage68', 'n'} <= set(sp.columns)
    assert {'component', 'ref_wave', 'mae_rank'} <= set(sc.columns)
    # ΔBIC + wins are populated
    assert (pw['contest'] == 'dbic').any() and (pw['contest'] == 'wins').any()
    dbic = pw[pw.contest == 'dbic']
    assert dbic['frac_favor_a'].notna().any()


# --------------------------------------------------------------------
# Tier 2 — confirmatory: compute over a tiny real L23 sweep
# --------------------------------------------------------------------
@needs_l23
def test_compute_over_real_sweep_l23(tmp_path):
    from ioptics import config, run

    cfg = config.loads(
        "sweep_id: sweep_metrics_l23\n"
        "datasets: [L23]\n"
        "noise_model: pace\n"
        "algorithms: [expb_pow, giop]\n"
        "fit_method: chisq\n"
        "mcmc_subset: 0\n"
        "seed: 1234\n")
    run.run_sweep(cfg, obs_ids=range(4), root=tmp_path)

    tables = metrics.compute('sweep_metrics_l23', root=tmp_path)
    d = io.sweep_dir('sweep_metrics_l23', root=tmp_path)
    for fn in (metrics.METRICS_SPECTRAL_FILE, metrics.METRICS_SCALAR_FILE,
               metrics.METRICS_PAIRWISE_FILE):
        assert (d / fn).is_file()
    assert not tables.spectral.empty and not tables.scalar.empty
    # both algorithms scored, and the expb_pow-vs-giop ΔBIC contest populated
    assert {'expb_pow', 'giop'} <= set(tables.spectral['algorithm'])
    dbic = tables.pairwise[tables.pairwise.contest == 'dbic']
    assert dbic['n'].sum() > 0

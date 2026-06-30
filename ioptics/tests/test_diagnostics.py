"""Tier-1 tests for ``ioptics.diagnostics`` figure-data functions.

Hand-built long results tables and a saved chain NPZ with known answers — no
models, no data, no engine. Checks shapes and exact values for the Taylor /
Target / scatter / ratio-histogram / residual / corner / ΔBIC-CDF arrays.
"""

import numpy as np
import pandas as pd

from ioptics import diagnostics


_WAVE_REF = 440.0
_O = np.array([0.1, 0.2, 0.4, 0.8])      # truth across 4 obs


def _spectral_one_band(values_by_algo, component='a', wave=_WAVE_REF):
    """Build a spectral table: one component, one band, several algorithms."""
    rows = []
    for algo, vals in values_by_algo.items():
        for obs_id, (v, o) in enumerate(zip(vals, _O)):
            rows.append({'dataset': 'L23', 'obs_id': obs_id, 'algorithm': algo,
                         'fit_method': 'chisq', 'component': component,
                         'wavelength': wave, 'value': v, 'truth': o,
                         'lo68': v * 0.9, 'hi68': v * 1.1,
                         'lo95': v * 0.8, 'hi95': v * 1.2})
    return pd.DataFrame(rows)


def test_taylor_stats_known():
    table = _spectral_one_band({'good': _O, 'scaled': 2.0 * _O})
    ts = diagnostics.taylor_stats(table, 'a', _WAVE_REF).set_index('algorithm')
    # perfect retrieval -> corr 1, norm_std 1, crmsd 0
    assert np.isclose(ts.loc['good', 'corr'], 1.0)
    assert np.isclose(ts.loc['good', 'norm_std'], 1.0)
    assert np.isclose(ts.loc['good', 'crmsd'], 0.0)
    # a pure log-offset (2x) preserves correlation and spread -> crmsd 0 too
    assert np.isclose(ts.loc['scaled', 'corr'], 1.0)
    assert np.isclose(ts.loc['scaled', 'norm_std'], 1.0)
    assert np.isclose(ts.loc['scaled', 'crmsd'], 0.0)
    assert ts.loc['good', 'n'] == 4
    # Taylor identity holds
    r = ts.loc['good']
    lhs = r['crmsd'] ** 2
    rhs = (r['std_model'] ** 2 + r['std_ref'] ** 2
           - 2 * r['std_model'] * r['std_ref'] * r['corr'])
    assert np.isclose(lhs, rhs, atol=1e-12)


def test_target_stats_known():
    table = _spectral_one_band({'good': _O, 'scaled': 2.0 * _O})
    tg = diagnostics.target_stats(table, 'a', _WAVE_REF).set_index('algorithm')
    assert np.isclose(tg.loc['good', 'bias'], 0.0)
    assert np.isclose(tg.loc['good', 'unbiased_rmsd'], 0.0)
    # 2x high -> log-space bias = log10(2)
    assert np.isclose(tg.loc['scaled', 'bias'], np.log10(2.0))
    assert np.isclose(tg.loc['scaled', 'total_rmsd'], np.log10(2.0))


def test_scatter_data_points_and_guides():
    table = _spectral_one_band({'good': _O, 'scaled': 2.0 * _O})
    sd = diagnostics.scatter_data(table, 'a', _WAVE_REF)
    good = sd['points'][sd['points'].algorithm == 'good']
    np.testing.assert_allclose(good['x'].to_numpy(), _O)
    np.testing.assert_allclose(good['y'].to_numpy(), _O)        # y == x
    lo, hi = sd['lims']
    assert lo == 0.1 and np.isclose(hi, 1.6)                    # scaled y max
    x_line, y_line = sd['guides']['one_to_one']
    np.testing.assert_allclose(x_line, y_line)
    np.testing.assert_allclose(sd['guides']['three_to_one'][1], 3.0 * x_line)


def test_ratio_hist_data_buckets():
    table = _spectral_one_band({'good': _O, 'scaled': 2.0 * _O})
    rh = diagnostics.ratio_hist_data(table, 'a', _WAVE_REF)
    counts = rh['counts']
    assert len(rh['centers']) == len(rh['edges']) - 1
    # ratio 1.0 -> bin [1, 4/3) index 4; ratio 2.0 -> bin [2, 3) index 6
    assert counts.loc['good'].to_numpy()[4] == 4
    assert counts.loc['scaled'].to_numpy()[6] == 4


def test_residual_spectra():
    wave = np.array([440.0, 555.0])
    rows = []
    for comp, vals in (('Rrs_model', [0.011, 0.008]),
                       ('Rrs_obs', [0.010, 0.008])):
        for w, v in zip(wave, vals):
            rows.append({'dataset': 'L23', 'obs_id': 0, 'algorithm': 'good',
                         'fit_method': 'chisq', 'component': comp,
                         'wavelength': w, 'value': v})
    spectral = pd.DataFrame(rows)
    scalar = pd.DataFrame([{'dataset': 'L23', 'obs_id': 0, 'algorithm': 'good',
                            'fit_method': 'chisq', 'chi2_nu': 1.2}])
    out = diagnostics.residual_spectra(spectral, scalar, 0)
    res = out['good']
    np.testing.assert_allclose(res['wave'], wave)
    np.testing.assert_allclose(res['residual'], [-0.001, 0.0], atol=1e-12)
    assert res['chi2_nu'] == 1.2


def test_corner_data(tmp_path):
    path = tmp_path / 'chain.npz'
    rng = np.random.default_rng(0)
    chains = rng.normal(size=(10, 4, 3))      # (nsteps, nwalkers, nparam)
    np.savez(path, chains=chains, Chl=1.5, Y=0.5)
    cd = diagnostics.corner_data(path)
    assert cd['samples'].shape == (40, 3)
    assert cd['labels'] == ['p0', 'p1', 'p2']
    assert cd['Chl'] == 1.5 and cd['Y'] == 0.5


def test_dbic_cdf_data():
    rows = []
    bics = {'expb_pow': [10.0, 12.0, 20.0], 'giop': [15.0, 15.0, 10.0]}
    for algo, bb in bics.items():
        for obs_id, b in enumerate(bb):
            rows.append({'dataset': 'L23', 'obs_id': obs_id, 'algorithm': algo,
                         'fit_method': 'chisq', 'BIC': b})
    scalar = pd.DataFrame(rows)
    out = diagnostics.dbic_cdf_data(scalar, 'expb_pow', 'giop')
    np.testing.assert_array_equal(out['dbic'], [-5.0, -3.0, 10.0])
    assert np.isclose(out['frac_favor_a'], 2 / 3)

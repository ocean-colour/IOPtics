"""Tier-1 smoke tests for ``ioptics.plotting`` static primitives.

Each builder must return a ``matplotlib.figure.Figure`` from the
``diagnostics``/``metrics`` arrays without doing any I/O. We feed small
hand-built inputs (via ``diagnostics`` where natural) and assert a figure with
axes comes back; degenerate/empty inputs still return a figure.
"""

import matplotlib
matplotlib.use('Agg')                       # headless; no display
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import numpy as np
import pandas as pd

from ioptics import diagnostics, plotting


_WAVE = np.array([440.0, 555.0])
_O = np.array([0.1, 0.2, 0.4, 0.8])


def _spectral_one_band(values_by_algo, component='a', wave=440.0):
    rows = []
    for algo, vals in values_by_algo.items():
        for obs_id, (v, o) in enumerate(zip(vals, _O)):
            rows.append({'dataset': 'L23', 'obs_id': obs_id, 'algorithm': algo,
                         'fit_method': 'chisq', 'component': component,
                         'wavelength': wave, 'value': v, 'truth': o,
                         'lo68': v * 0.9, 'hi68': v * 1.1,
                         'lo95': v * 0.8, 'hi95': v * 1.2})
    return pd.DataFrame(rows)


def _is_fig(fig):
    assert isinstance(fig, Figure)
    assert len(fig.axes) >= 1
    plt.close(fig)


def test_scatter_log():
    table = _spectral_one_band({'good': _O, 'scaled': 2.0 * _O})
    _is_fig(plotting.scatter_log(diagnostics.scatter_data(table, 'a', 440.0)))


def test_scatter_log_empty():
    empty = {'points': pd.DataFrame(columns=['algorithm', 'x', 'y']),
             'guides': {}, 'lims': (np.nan, np.nan)}
    _is_fig(plotting.scatter_log(empty))


def test_ratio_hist():
    table = _spectral_one_band({'good': _O, 'scaled': 2.0 * _O})
    _is_fig(plotting.ratio_hist(diagnostics.ratio_hist_data(table, 'a', 440.0)))


def test_spectra_band():
    comp_fit = pd.DataFrame({
        'wavelength': [440.0, 500.0, 555.0, 670.0],
        'value': [0.10, 0.08, 0.06, 0.04],
        'lo68': [0.09, 0.07, 0.05, 0.03], 'hi68': [0.11, 0.09, 0.07, 0.05],
        'lo95': [0.08, 0.06, 0.04, 0.02], 'hi95': [0.12, 0.10, 0.08, 0.06],
        'truth': [0.10, 0.08, 0.06, 0.04],
    })
    _is_fig(plotting.spectra_band(comp_fit, label='a'))


def test_residual_rrs():
    wave = _WAVE
    rows = []
    for comp, vals in (('Rrs_model', [0.011, 0.008]), ('Rrs_obs', [0.010, 0.008])):
        for w, v in zip(wave, vals):
            rows.append({'dataset': 'L23', 'obs_id': 0, 'algorithm': 'good',
                         'fit_method': 'chisq', 'component': comp,
                         'wavelength': w, 'value': v})
    spectral = pd.DataFrame(rows)
    scalar = pd.DataFrame([{'dataset': 'L23', 'obs_id': 0, 'algorithm': 'good',
                            'fit_method': 'chisq', 'chi2_nu': 1.2}])
    _is_fig(plotting.residual_rrs(
        diagnostics.residual_spectra(spectral, scalar, 0)))


def test_taylor_and_target():
    table = _spectral_one_band({'good': _O, 'scaled': 2.0 * _O})
    _is_fig(plotting.taylor(diagnostics.taylor_stats(table, 'a', 440.0)))
    _is_fig(plotting.target(diagnostics.target_stats(table, 'a', 440.0)))


def test_corner(tmp_path):
    path = tmp_path / 'chain.npz'
    rng = np.random.default_rng(0)
    np.savez(path, chains=rng.normal(size=(20, 6, 3)), Chl=1.0, Y=0.5,
             pnames=np.asarray(['Adg', 'Sdg', 'Bnw'], dtype=str))
    fig = plotting.corner(diagnostics.corner_data(path))
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_dbic_cdf():
    rows = []
    bics = {'expb_pow': [10.0, 12.0, 20.0], 'giop': [15.0, 15.0, 10.0]}
    for algo, bb in bics.items():
        for obs_id, b in enumerate(bb):
            rows.append({'dataset': 'L23', 'obs_id': obs_id, 'algorithm': algo,
                         'fit_method': 'chisq', 'BIC': b})
    scalar = pd.DataFrame(rows)
    _is_fig(plotting.dbic_cdf(diagnostics.dbic_cdf_data(scalar, 'expb_pow', 'giop')))


def test_dbic_cdf_stratified():
    rows = []
    bics = {'expb_pow': [10.0, 12.0], 'giop': [15.0, 15.0]}
    strata = ['oligotrophic', 'eutrophic']
    for algo, bb in bics.items():
        for obs_id, (b, s) in enumerate(zip(bb, strata)):
            rows.append({'dataset': 'L23', 'obs_id': obs_id, 'algorithm': algo,
                         'fit_method': 'chisq', 'BIC': b, 'stratum': s})
    scalar = pd.DataFrame(rows)
    curves = diagnostics.dbic_cdf_data(scalar, 'expb_pow', 'giop', by='stratum')
    _is_fig(plotting.dbic_cdf(curves))

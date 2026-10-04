"""Checks on the LS2 coefficient refit (``runs/prototypes/ls2/refit_ab.py``, ls2 task 12).

Tier 1 pins the small helpers.  Tier 2 runs the whole refit on L23 into a
scratch docs root (without touching ocpy's shipped table) and pins the
findings the page rests on, so a change to the data, ``ioptics.kd`` or
``ocpy.ls2.refit`` that would overturn them fails here first.
"""

import importlib.util
import pathlib

import numpy as np
import pandas as pd
import pytest

from ioptics.tests.conftest import needs_l23, needs_l23_profile

HERE = (pathlib.Path(__file__).resolve().parents[1] / 'runs' / 'prototypes'
        / 'ls2')


def _mod():
    spec = importlib.util.spec_from_file_location('ls2_refit_ab',
                                                  HERE / 'refit_ab.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_snell_and_flat_broadcast():
    m = _mod()
    assert m.snell_muw(0.0) == pytest.approx(1.0)
    assert m.snell_muw(60.0) == pytest.approx(0.76310, abs=1e-4)
    D = {'rrs': np.ones((2, 3)), 'sza': np.array([0.0, 30.0])}
    r, s = m._flat(D, 'rrs', 'sza')
    assert r.shape == s.shape == (6,)
    np.testing.assert_array_equal(s, [0, 0, 0, 30, 30, 30])


@needs_l23
@needs_l23_profile
def test_the_refit_and_its_findings(tmp_path):
    m = _mod()
    out = m.build(docs_root=tmp_path, save=False)
    rd = tmp_path / 'reports' / m.SID
    for name in ('refit_selection.csv', 'refit_scores.csv', 'refit_eta_bins.csv',
                 'refit_limiting.csv', 'refit_domain.csv', 'refit_spectral.png',
                 'refit_coefficients.png', f'{m.SID}.rst'):
        assert (rd / name).is_file(), name

    S = pd.read_csv(rd / 'refit_scores.csv').set_index(['version', 'component'])
    # the published table's bias on L23 X=1 reproduces; the refit removes it
    assert S.loc[('published (table)', 'a'), 'median_ratio'] > 1.015
    assert S.loc[('refit (table)', 'a'), 'mae'] < 0.005
    assert S.loc[('refit (table)', 'bb'), 'mae'] < 0.01
    for comp in ('a', 'bb', 'a_nw', 'bb_p'):
        assert (S.loc[('refit (table)', comp), 'mae']
                < S.loc[('published (table)', comp), 'mae']), comp

    # the basis choice: 1/mu_w extrapolates best for a, mu_w for bb
    sel = pd.read_csv(rd / 'refit_selection.csv')
    d2 = sel[sel.eta_degree == 2].set_index(['table', 'muw_basis'])['extrap_60_mae']
    assert d2.loc['a'].idxmin() == 'inv' and d2.loc['bb'].idxmin() == 'lin'

    # every eta bin, the sparse ones included, is better after the refit
    E = pd.read_csv(rd / 'refit_eta_bins.csv')
    assert (E.a_mae_refit < E.a_mae_pub).all() and (E.bb_mae_refit < E.bb_mae_pub).all()

    # the limiting relation is the effective mu_w, not Snell's
    L = pd.read_csv(rd / 'refit_limiting.csv').set_index('theta_s')
    assert abs(L.loc[0, 'refit_c0_eta0.02'] - L.loc[0, 'inv_mu_eff']) < 0.01
    assert L.loc[0, 'refit_c0_eta0.02'] > 1.02

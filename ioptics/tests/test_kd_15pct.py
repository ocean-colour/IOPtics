"""Checks on the 15% diagnostic (``runs/prototypes/ls2/kd_15pct.py``, ls2 task 10).

Tier 1 pins the helpers that put L23 onto a network's bands.  Tier 2 runs the
whole diagnostic on L23 into a scratch docs root and pins the findings the
report rests on, so a change to the data, the networks or ``ioptics.kd`` that
would overturn the recommendation fails here first.
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
    spec = importlib.util.spec_from_file_location('ls2_kd_15pct',
                                                  HERE / 'kd_15pct.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_feed_on_a_linear_spectrum():
    """Linear and cubic are exact on a straight line; a 10 nm band nearly so
    (its weights are sampled on the 5 nm grid, so not perfectly symmetric)."""
    m = _mod()
    wave = np.arange(350.0, 751.0, 5.0)
    rrs = np.vstack([1e-3 + 1e-6 * (wave - 350), 2e-3 - 2e-6 * (wave - 350)])
    bands = np.array([443.0, 488.0, 531.0, 547.0, 667.0])
    truth = np.vstack([1e-3 + 1e-6 * (bands - 350), 2e-3 - 2e-6 * (bands - 350)])
    for how in ('linear', 'cubic', 'gauss10'):
        np.testing.assert_allclose(m.feed(wave, rrs, bands, how), truth,
                                   rtol=1e-9 if how != 'gauss10' else 1e-6,
                                   err_msg=how)
    near = m.feed(wave, rrs, bands, 'nearest')
    np.testing.assert_allclose(near[0], 1e-3 + 1e-6 * (np.array(
        [445.0, 490.0, 530.0, 545.0, 665.0]) - 350))
    with pytest.raises(ValueError):
        m.feed(wave, rrs, bands, 'spline9')


def test_off_grid_band_refuses():
    m = _mod()
    with pytest.raises(ValueError, match='not on the L23 grid'):
        m._col(np.arange(350.0, 751.0, 5.0), 412)


@needs_l23
@needs_l23_profile
def test_the_report_and_its_findings(tmp_path):
    m = _mod()
    out = m.build(docs_root=tmp_path)
    rd = out['page'].parent
    text = out['page'].read_text(encoding='utf-8')
    assert 'Recommendation' in text and 'Candidate 4' in text
    for name in ('kd15_bands.csv', 'kd15_definitions.csv', 'kd15_kd_bins.csv',
                 'kd15_pure_water.csv', 'kd15_interp.csv', 'kd15_domain.csv',
                 'kd15_realizations.csv', 'kd15_ratio_spectrum.png',
                 'kd15_domain.png'):
        assert (rd / name).is_file(), name

    b = pd.read_csv(rd / 'kd15_bands.csv').set_index('network')
    # the planning number reproduces (15-18% blue, 2-4% at 555/670)
    assert 1.13 < b.loc['MODIS_v1.1', '440'] < 1.18
    assert 1.15 < b.loc['MODIS_v1.1', '490'] < 1.21
    assert abs(b.loc['MODIS_v1.1', '555'] - 1) < 0.05
    # ...and is part of a wider swing; PACE agrees, v1.3 halfway
    assert b.loc['MODIS_v1.1', 'vis_min'] < 0.85 < 1.2 < b.loc['MODIS_v1.1', 'vis_max']
    assert b.loc['PACE_v2.3', 'vis_mad'] < 0.03
    assert b.loc['MODIS_v1.3', 'vis_mad'] < b.loc['MODIS_v1.1', 'vis_mad']

    # the definition cannot explain it
    d = pd.read_csv(rd / 'kd15_definitions.csv')
    cols = [str(x) for x in m.BANDS]
    assert max((g[cols].max() - g[cols].min()).max()
               for _, g in d.groupby('network')) < 0.002
    # multiplicative, not additive, for the shipped network
    k = pd.read_csv(rd / 'kd15_kd_bins.csv')
    v11 = k[k.network == 'MODIS_v1.1'].set_index('band')
    assert (v11.loc[[440, 490], 'alpha'] > 1.1).all()
    assert (v11.loc[[440, 490], 'beta_over_median_kd'].abs() < 0.1).all()
    # smooth interpolation is not the cause
    it = pd.read_csv(rd / 'kd15_interp.csv').set_index(['network', 'interp'])
    for net in m.NETWORKS:
        assert abs(it.loc[(net, 'cubic'), '440'] - it.loc[(net, 'linear'), '440']) < 0.01

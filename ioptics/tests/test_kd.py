"""Tests for ``<Kd>_1`` (``ioptics.kd``) and Kd as a record input.

Tier-1 (data-free): the three definitions on synthetic Hydrolight-shaped
profiles, and the prep plumbing -- Kd trimmed like ``Rrs``, an off-grid Kd
aligned without extrapolation, never perturbed, never truth -- through a fake
adapter.

Tier-2 (``@needs_l23_profile``): the measured agreement of the three
definitions on L23 ``X=4, Y=0``, the ``z1_lambda`` inconsistency pinned as a
regression, ``X=2`` loading, and the five empty scenarios of the ``X=2, Y=0``
profile file. ``@needs_pangaea``: a real PANGAEA record carries its ``kd``.
"""

import numpy as np
import pytest
import xarray as xr

from ioptics import datasets, kd, prep
from ioptics.datasets import RawObs
from ioptics.records import PreparedRecord
from ioptics.tests.conftest import needs_l23_profile, needs_pangaea

ZGRID = np.concatenate([[-1.0], np.arange(0., 1., 0.1), np.arange(1., 51., 1.)])


def _profile(K, *, z1_scale=1.0, depth_slope=0.0):
    """A synthetic ``Hydrolight*_profile.nc``-shaped dataset.

    ``K`` is ``(n_scenario, n_lambda)``. ``KEd(z) = K (1 + depth_slope z)``
    and ``Ed`` is its exact integral, so with ``depth_slope=0`` the water is
    homogeneous and every definition must return ``K``. ``z1_lambda`` is the
    true e-folding depth times ``z1_scale``, to mimic L23's wrong stored z1.
    """
    K = np.asarray(K, dtype=float)
    z = ZGRID
    zz = np.clip(z, 0, None)[:, None, None]
    ked = K[None] * (1 + depth_slope * zz)
    ed = np.exp(-K[None] * (zz + 0.5 * depth_slope * zz ** 2))
    if depth_slope == 0:
        z1 = 1.0 / K
    else:   # root of K (z + s z^2 / 2) = 1
        z1 = (-1 + np.sqrt(1 + 2 * depth_slope / K)) / depth_slope
    z1_stored = z1 * z1_scale
    z1_stored = np.where(z1_stored > z[-1], -999., z1_stored)
    ked[0] = np.nan                                 # z = -1: no KEd above water
    return xr.Dataset({
        'Ed_z': (('z', 'IOP_Scenario', 'Lambda'), ed),
        'KEd_z': (('z', 'IOP_Scenario', 'Lambda'), ked),
        'z1_lambda': (('Lambda', 'IOP_Scenario'), z1_stored.T),
    }, coords={'z': z})


# --- the three definitions, synthetic -------------------------------------------

def test_homogeneous_water_every_definition_returns_K():
    K = np.array([[0.04, 0.05, 0.4], [0.1, 0.8, 2.5]])  # 1.77/K stays on the grid
    ds = _profile(K, z1_scale=1.77)                  # stored z1 badly wrong
    for definition in kd.KD1_DEFINITIONS:
        np.testing.assert_allclose(kd.kd1_from_profile(ds, definition), K,
                                   rtol=1e-6, err_msg=definition)
    # ... which is why the stored-z1 error barely matters on L23: in
    # homogeneous water a depth average of KEd does not care where it stops.


def test_stored_z1_definition_diverges_when_kd_varies_with_depth():
    K = np.array([[0.1, 0.4]])
    ds = _profile(K, z1_scale=1.77, depth_slope=0.05)
    c = kd.kd1_from_profile(ds, 'ln_ratio')
    b = kd.kd1_from_profile(ds, 'trapz_ed_z1')
    a = kd.kd1_from_profile(ds, 'trapz_stored_z1')
    # same z1, same answer, up to locating z1 by linear interpolation of a
    # quadratic ln Ed on the 1 m grid (measured 0.23%)
    np.testing.assert_allclose(b, c, rtol=5e-3)
    assert np.all(a > c * 1.01)                      # deeper z1, larger mean KEd


def test_z1_beyond_the_grid_is_nan():
    K = np.array([[0.01, 0.1]])                      # 1/K = 100 m > 50 m grid
    ds = _profile(K)
    for definition in kd.KD1_DEFINITIONS:
        out = kd.kd1_from_profile(ds, definition)
        assert np.isnan(out[0, 0]) and np.isfinite(out[0, 1]), definition


def test_efolding_depth_is_exact_for_exponential_ed():
    K = np.array([[0.05, 0.3, 1.7]])
    zs, ln_ed, _, _ = kd._profile_arrays(_profile(K))
    np.testing.assert_allclose(kd.efolding_depth(zs, ln_ed), 1.0 / K, rtol=1e-9)


def test_unknown_definition_raises():
    with pytest.raises(ValueError, match='definition'):
        kd.kd1_from_profile(_profile(np.array([[0.1]])), 'one_over_z1')


# --- Kd as a record input, through prep ------------------------------------------

WAVE = np.arange(400., 701., 10.)


class _FakeAdapter:
    """Serves one observation whose Kd form is chosen per test."""

    def __init__(self, kd_value):
        self.kd_value = kd_value

    def obs_ids(self, **opts):
        return [0]

    def load_obs(self, obs_id, **opts):
        rrs = 0.004 * np.exp(-0.5 * ((WAVE - 450.) / 80.) ** 2) + 2e-4
        return RawObs(wave=WAVE.copy(), Rrs=rrs,
                      truth={'a': 0.05 + 0 * WAVE}, meta={'dataset': 'KDFAKE'},
                      Kd=self.kd_value)


@pytest.fixture
def fake(monkeypatch):
    def _use(kd_value):
        monkeypatch.setitem(datasets.ADAPTERS, 'KDFAKE', _FakeAdapter(kd_value))
    return _use


def test_kd_defaults_to_none():
    assert RawObs(wave=WAVE, Rrs=WAVE, truth={}).Kd is None
    assert 'Kd' in PreparedRecord.__dataclass_fields__


def test_kd_on_the_grid_survives_a_trim(fake):
    kd_in = 0.02 + 1e-4 * (WAVE - 400.)
    fake(kd_in)
    rec = prep.prep_one('KDFAKE', 0, noise='pct:0.05', add_noise=True, seed=3,
                        wv_min=450., wv_max=650.)
    keep = (WAVE >= 450.) & (WAVE <= 650.)
    np.testing.assert_array_equal(rec.wave, WAVE[keep])
    np.testing.assert_array_equal(rec.Kd, kd_in[keep])   # exact, unperturbed
    assert rec.meta['Kd_interp'] is False
    assert rec.meta['Kd_on_band'].all() and rec.meta['Kd_on_band'].size == keep.sum()
    assert 'Kd' not in rec.truth and 'Kd' not in rec.truth_interp


def test_off_grid_kd_is_aligned_never_extrapolated(fake):
    src = np.array([412., 443., 490., 555., 665.])
    vals = np.array([0.05, 0.04, 0.03, 0.07, 0.45])
    fake((src, vals))
    rec = prep.prep_one('KDFAKE', 0, noise='pct:0.05')
    assert rec.meta['Kd_interp'] is True
    np.testing.assert_allclose(rec.Kd, np.interp(WAVE, src, vals, left=np.nan,
                                                 right=np.nan))
    assert np.all(np.isnan(rec.Kd[(WAVE < 412.) | (WAVE > 665.)]))
    assert np.all(np.isfinite(rec.Kd[(WAVE >= 412.) & (WAVE <= 665.)]))
    # measured-vs-interpolated, per band: of these, only 490 is on the grid
    np.testing.assert_array_equal(rec.meta['Kd_on_band'], WAVE == 490.)


def test_no_kd_stays_none_and_a_misshapen_kd_raises(fake):
    fake(None)
    assert prep.prep_one('KDFAKE', 0, noise='pct:0.05').Kd is None
    fake(np.ones(5))
    with pytest.raises(ValueError, match='Kd'):
        prep.prep_one('KDFAKE', 0, noise='pct:0.05')


# --- L23 profiles (Tier 2) -------------------------------------------------------

@pytest.fixture(scope='module')
def l23_x4():
    """The three definitions on L23 X=4, Y=0, plus the wavelength grid."""
    out = {d: kd.load_l23_kd1(4, 0, d)[1] for d in kd.KD1_DEFINITIONS}
    out['wave'] = kd.load_l23_kd1(4, 0)[0]
    return out


def _rel(l23, definition, lo, hi):
    lam = l23['wave']
    band = (lam >= lo) & (lam <= hi)
    r = l23[definition][:, band] / l23['ln_ratio'][:, band] - 1
    return r[np.isfinite(r)]


@needs_l23_profile
def test_definitions_agree_in_the_blue_and_diverge_in_the_red(l23_x4):
    """Measured 2026-10-03; see the ``ioptics.kd`` docstring."""
    assert l23_x4['ln_ratio'].shape == (3320, 81)
    for definition in ('trapz_stored_z1', 'trapz_ed_z1'):
        blue = _rel(l23_x4, definition, 400, 500)
        assert abs(np.median(blue)) < 3e-4, definition         # < 0.03%
        assert np.percentile(np.abs(blue), 99) < 4e-3, definition
        everything = _rel(l23_x4, definition, 350, 750)
        assert np.abs(everything).max() < 0.016, definition    # Q10's <~1.6%
    # The stored-z1 trapezoid is the one that drifts, and it drifts in the red.
    red_a = _rel(l23_x4, 'trapz_stored_z1', 680, 720)
    red_b = _rel(l23_x4, 'trapz_ed_z1', 680, 720)
    assert np.percentile(red_a, 1) < -1e-3                      # measured -0.20%
    assert np.percentile(red_a, 1) < 3 * np.percentile(red_b, 1)
    assert 0.98 < np.isfinite(l23_x4['ln_ratio']).mean() < 0.995


@needs_l23_profile
def test_z1_lambda_inconsistency_is_pinned():
    """L23's stored z1 disagrees with its own Ed_z -- pinned so it cannot move.

    Measured at X=4, Y=0: 37 039 of 266 067 (scenario, wavelength) pairs are
    off by more than 10%, and at 700 nm the stored z1 is 1.77x the e-folding
    depth of Ed_z.
    """
    with xr.open_dataset(kd.l23_profile_path(4, 0), engine='h5netcdf') as ds:
        lam = ds['Lambda'].values.astype(float)
        zs, ln_ed, _, z1_stored = kd._profile_arrays(ds)
    z1_ed = kd.efolding_depth(zs, ln_ed)
    both = np.isfinite(z1_ed) & np.isfinite(z1_stored)
    ratio = z1_ed[both] / z1_stored[both]
    assert both.sum() == 266067
    assert (np.abs(ratio - 1) > 0.1).sum() == 37039
    j = int(np.argmin(np.abs(lam - 700.)))
    m = both[:, j]
    assert np.median(z1_stored[m, j] / z1_ed[m, j]) == pytest.approx(1.7687,
                                                                     abs=2e-3)


@needs_l23_profile
def test_lifted_function_matches_the_prototype_loop():
    import importlib.util
    import pathlib

    path = (pathlib.Path(kd.__file__).parent / 'runs' / 'prototypes' / 'ls2'
            / 'verify_context.py')
    spec = importlib.util.spec_from_file_location('verify_context', path)
    vc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vc)
    assert vc.mean_kd_first_attenuation_depth is kd.mean_kd_first_attenuation_depth
    with xr.open_dataset(kd.l23_profile_path(4, 0), engine='h5netcdf') as ds:
        sub = ds.isel(IOP_Scenario=slice(0, 50))
        np.testing.assert_allclose(
            kd.mean_kd_first_attenuation_depth(sub),
            kd.kd1_from_profile(sub, 'trapz_stored_z1'), rtol=0, atol=0)


@needs_l23_profile
def test_x2_loads_with_kd_and_its_profile_holes_are_pinned():
    rec = prep.prep_one('L23', 5, X=2, Y=0, kd1='ln_ratio', seed=1,
                        wv_min=400., wv_max=700.)
    assert rec.meta['X'] == 2 and rec.meta['kd1'] == 'ln_ratio'
    wave, kd1 = kd.load_l23_kd1(2, 0)
    keep = (wave >= 400.) & (wave <= 700.)
    np.testing.assert_array_equal(rec.Kd, kd1[5, keep])

    with xr.open_dataset(kd.l23_profile_path(2, 0), engine='h5netcdf') as ds:
        assert kd.empty_profile_rows(ds) == kd.KNOWN_EMPTY_PROFILE_ROWS[(2, 0)]
    assert np.all(np.isnan(kd1[list(kd.KNOWN_EMPTY_PROFILE_ROWS[(2, 0)])]))
    for X in (1, 4):
        with xr.open_dataset(kd.l23_profile_path(X, 0), engine='h5netcdf') as ds:
            assert kd.empty_profile_rows(ds) == ()


@needs_l23_profile
def test_kd1_is_cached_and_opt_in():
    first = kd.load_l23_kd1(4, 0)
    assert kd.load_l23_kd1(4, 0) is first
    assert prep.prep_one('L23', 0, X=4, seed=1).Kd is None   # not asked for


# --- PANGAEA (Tier 2) ------------------------------------------------------------

@needs_pangaea
def test_pangaea_kd_rides_on_the_record():
    from ocpy.insitu import pangaea

    adapter = datasets.get_adapter('PANGAEA')
    iop = adapter._table('iop')
    counts = pangaea.n_spectral(iop, kind='kd')
    ids = set(adapter.obs_ids())
    oid = next(i for i in counts.index[counts > 0] if i in ids)
    raw = adapter.load_obs(oid)
    assert isinstance(raw.Kd, tuple) and len(raw.Kd[0]) > 0
    rec = prep.prep_one('PANGAEA', oid)
    assert rec.Kd is not None and rec.Kd.shape == rec.wave.shape
    assert 'Kd' not in rec.truth
    # every Kd band that falls on the record grid survives exactly
    on_grid = np.isin(raw.Kd[0], rec.wave)
    for w, v in zip(raw.Kd[0][on_grid], raw.Kd[1][on_grid]):
        assert rec.Kd[rec.wave == w][0] == pytest.approx(v)

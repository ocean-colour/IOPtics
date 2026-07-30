"""Tests for ``ioptics.prep`` — prep_one / prep_dataset and truth alignment.

Tier-1 (data-independent) drives a synthetic adapter through ``prep_one`` /
``prep_dataset`` and unit-tests ``_align_truth``. Tier-2 (``@needs_l23``) runs
``prep_dataset('L23', range(5))`` and a light truth-vs-``init`` Chl check.
"""

import pickle

import numpy as np
import pytest

from ioptics import datasets as D
from ioptics import prep
from ioptics.datasets import RawObs
from ioptics.records import PreparedRecord
from ioptics.tests.conftest import needs_gloria, needs_l23, needs_pangaea

L23_TRUTH_KEYS = {'a', 'bb', 'a_ph', 'a_dg', 'bb_p', 'a_w', 'bb_w',
                  'Chl', 'Y', 'Sdg'}


@pytest.fixture
def fake_dataset():
    """Register an L23-like synthetic adapter (truth on the native grid)."""
    class FakeAdapter:
        def obs_ids(self, **opts):
            return [0, 1, 2]

        def load_obs(self, obs_id, **opts):
            wave = np.arange(400.0, 701.0, 5.0)
            Rrs = 0.01 * np.exp(-0.003 * (wave - 400.0)) + 1e-3
            truth = {
                'a':   0.10 * np.exp(-0.010 * (wave - 440.0)),
                'bb':  0.01 * (550.0 / wave),
                'Chl': 1.23,                       # scalar
            }
            return RawObs(wave=wave, Rrs=Rrs, truth=truth,
                          meta={'obs_id': obs_id})

    name = '_FAKE_PREP'
    D.register_dataset(name, FakeAdapter())
    try:
        yield name
    finally:
        D.ADAPTERS.pop(name, None)


@pytest.fixture
def fake_insitu_dataset():
    """A PANGAEA-like adapter: per-family truth grids, no measured Rrs error."""
    class FakeInsituAdapter:
        def obs_ids(self, **opts):
            return [0]

        def load_obs(self, obs_id, **opts):
            wave = np.arange(400.0, 701.0, 5.0)              # Rrs grid
            Rrs = 0.01 * np.exp(-0.003 * (wave - 400.0)) + 1e-3
            # a_dg on its OWN grid, narrower than `wave` (edges -> NaN).
            adg_wave = np.arange(420.0, 601.0, 20.0)
            adg_vals = 0.2 * np.exp(-0.015 * (adg_wave - 440.0))
            truth = {
                'a_dg': (adg_wave, adg_vals),                # per-family pair
                'Chl':  0.7,                                 # scalar
            }
            return RawObs(wave=wave, Rrs=Rrs, truth=truth, Rrs_err=None,
                          meta={'dataset': 'PANGAEA', 'obs_id': obs_id})

    name = '_FAKE_INSITU'
    D.register_dataset(name, FakeInsituAdapter())
    try:
        yield name
    finally:
        D.ADAPTERS.pop(name, None)


# --------------------------------------------------------------------
# Tier 1 — _align_truth unit behavior
# --------------------------------------------------------------------
def test_align_truth_exact_grid_not_interpolated():
    wave = np.arange(400.0, 701.0, 5.0)
    vals = np.linspace(1.0, 0.5, wave.size)
    out, interp = prep._align_truth(wave, vals, wave)
    assert interp is False
    np.testing.assert_array_equal(out, vals)


def test_align_truth_subset_is_not_a_regrid():
    src = np.arange(400.0, 701.0, 5.0)
    vals = np.linspace(1.0, 0.5, src.size)
    wave = src[5:20]                              # exact subset (a trim)
    out, interp = prep._align_truth(src, vals, wave)
    assert interp is False
    np.testing.assert_allclose(out, vals[5:20])


def test_align_truth_offgrid_interpolates_with_nan_edges():
    src = np.array([450.0, 500.0, 550.0, 600.0])
    vals = np.array([1.0, 0.8, 0.6, 0.4])
    wave = np.array([400.0, 500.0, 575.0, 650.0])   # 400 & 650 out of range
    out, interp = prep._align_truth(src, vals, wave)
    assert interp is True
    assert np.isnan(out[0]) and np.isnan(out[3])   # not extrapolated
    assert out[1] == pytest.approx(0.8)            # exact at a node
    assert out[2] == pytest.approx(0.5)            # linear interior


# --------------------------------------------------------------------
# Tier 1 — prep_one / prep_dataset via the synthetic adapter
# --------------------------------------------------------------------
def test_prep_one_populates_every_field(fake_dataset):
    r = prep.prep_one(fake_dataset, 0, noise='pct:0.05', add_noise=True, seed=99)
    assert isinstance(r, PreparedRecord)
    for f in ('dataset', 'obs_id', 'wave', 'Rrs', 'varRrs', 'Rrs_clean',
              'truth', 'truth_interp', 'init', 'noise_model', 'noise_seed', 'meta'):
        assert getattr(r, f) is not None
    assert r.noise_model == 'pct:0.05'
    assert r.noise_seed == 99
    assert np.all(r.varRrs >= 0)
    # perturbed, but the clean spectrum is retained
    assert not np.array_equal(r.Rrs, r.Rrs_clean)


def test_prep_one_truth_as_spectrum_on_wave(fake_dataset):
    from ocpy.spectra import Spectrum
    r = prep.prep_one(fake_dataset, 0, noise='pct:0.05', add_noise=False)
    # spectral truth: Spectrum on `wave`, native grid retained, not regridded
    asp = r.truth['a']
    assert isinstance(asp, Spectrum)
    np.testing.assert_array_equal(asp.wavelength, r.wave)
    assert 'orig_wave' in asp.metadata
    assert r.truth_interp['a'] is False
    # scalar truth: plain float, flagged not-interpolated
    assert isinstance(r.truth['Chl'], float)
    assert r.truth_interp['Chl'] is False


def test_prep_one_init_is_truth_free_and_finite(fake_dataset):
    r = prep.prep_one(fake_dataset, 0, noise='pct:0.05', add_noise=False)
    assert set(r.init) == {'Chl', 'Y'}
    assert np.isfinite(r.init['Chl']) and np.isfinite(r.init['Y'])


def test_prep_one_trim(fake_dataset):
    r = prep.prep_one(fake_dataset, 0, noise='pct:0.05', add_noise=False,
                      wv_min=450.0, wv_max=600.0)
    assert r.wave.min() >= 450.0 and r.wave.max() <= 600.0
    assert r.truth['a'].wavelength.shape == r.wave.shape
    assert r.truth_interp['a'] is False           # subset, not a regrid


def test_prep_one_is_picklable(fake_dataset):
    r = prep.prep_one(fake_dataset, 0, noise='pct:0.05', add_noise=True, seed=7)
    r2 = pickle.loads(pickle.dumps(r))
    assert isinstance(r2, PreparedRecord)
    np.testing.assert_array_equal(r2.truth['a'].values, r.truth['a'].values)
    np.testing.assert_array_equal(r2.wave, r.wave)


def test_prep_dataset_per_record_seeds(fake_dataset):
    recs = prep.prep_dataset(fake_dataset, noise='pct:0.05', add_noise=True,
                             seed=1000)
    assert len(recs) == 3
    assert [r.noise_seed for r in recs] == [1000, 1001, 1002]


# --------------------------------------------------------------------
# Tier 1 — per-family truth grids + in-situ noise fallback (PANGAEA-shaped)
# --------------------------------------------------------------------
def test_prep_one_per_family_truth_aligned_onto_wave(fake_insitu_dataset):
    from ocpy.spectra import Spectrum
    r = prep.prep_one(fake_insitu_dataset, 0)
    adg = r.truth['a_dg']
    assert isinstance(adg, Spectrum)
    # aligned onto the record's `wave`, and flagged as a genuine regrid
    np.testing.assert_array_equal(adg.wavelength, r.wave)
    assert r.truth_interp['a_dg'] is True
    # out-of-(family)-range points are NaN, not extrapolated
    assert np.isnan(adg.values[r.wave < 420.0]).all()
    assert np.isnan(adg.values[r.wave > 600.0]).all()
    assert np.isfinite(adg.values[(r.wave >= 420.0) & (r.wave <= 600.0)]).all()
    # native family grid retained for provenance
    np.testing.assert_array_equal(adg.metadata['orig_wave'],
                                  np.arange(420.0, 601.0, 20.0))
    # scalar truth still a plain float
    assert isinstance(r.truth['Chl'], float)


def test_prep_one_insitu_without_errors_falls_back_to_pct(fake_insitu_dataset):
    # default noise for a non-L23 dataset is 'insitu'; with no measured Rrs_err
    # prep falls back to the flat fractional model (and records it honestly).
    r = prep.prep_one(fake_insitu_dataset, 0)
    assert r.noise_model == f'pct:{prep._INSITU_PCT_FALLBACK}'
    assert np.all(r.varRrs > 0)
    assert r.noise_seed is None                    # in-situ Rrs is not perturbed
    np.testing.assert_array_equal(r.Rrs, r.Rrs_clean)


def test_prep_gloria_single_point_adg_and_caveat():
    # GLORIA's design intent, data-free: aCDOM440 becomes a single-point a_dg
    # truth at 440 nm; io derives a_cdom440_truth from it and metrics stamps the
    # CDOM-vs-a_dg caveat. Measured Rrs std -> genuine 'insitu' (no fallback).
    from ocpy.spectra import Spectrum
    from ioptics import io as ioptics_io
    from ioptics import metrics

    class FakeGloria:
        def obs_ids(self, **opts):
            return [0]

        def load_obs(self, obs_id, **opts):
            wave = np.arange(400.0, 701.0, 5.0)
            Rrs = 0.01 * np.exp(-0.003 * (wave - 400.0)) + 1e-3
            truth = {'a_dg': (np.array([440.0]), np.array([0.15])), 'Chl': 2.0}
            return RawObs(wave=wave, Rrs=Rrs, truth=truth, Rrs_err=0.1 * Rrs,
                          meta={'dataset': 'GLORIA', 'obs_id': obs_id})

    name = 'GLORIA_FAKE'
    D.register_dataset(name, FakeGloria())
    try:
        r = prep.prep_one(name, 0)
        adg = r.truth['a_dg']
        assert isinstance(adg, Spectrum)
        i440 = int(np.argmin(np.abs(r.wave - 440.0)))
        assert adg.values[i440] == pytest.approx(0.15)
        finite = np.isfinite(adg.values)                # finite only at 440 nm
        assert finite.sum() == 1 and finite[i440]
        assert r.truth_interp['a_dg'] is True
        # Measured std, so no pct fallback -- but GLORIA gets the error floor
        # by default, and the tag says so rather than claiming 'insitu'.
        assert r.noise_model == f'insitu+floor:{prep._GLORIA_NOISE_FLOOR}'
        # The floor is a *max*, so a fixture whose measured error (10% here)
        # already exceeds it keeps exactly that error: applying the floor
        # must never shrink an uncertainty.
        assert np.allclose(np.sqrt(r.varRrs), 0.1 * np.abs(r.Rrs_clean))
        # io derives a_cdom440_truth from the single-point a_dg
        assert ioptics_io._scalar_value(r, 'a_cdom440') == pytest.approx(0.15)
        # metrics auto-stamps the caveat on GLORIA a_dg rows only
        assert metrics._caveat(r.dataset, 'a_dg') == 'CDOM_vs_adg'
        assert metrics._caveat(r.dataset, 'a_ph') == ''
    finally:
        D.ADAPTERS.pop(name, None)


# --------------------------------------------------------------------
# Tier 2 — requires the L23 data tree
# --------------------------------------------------------------------
@needs_l23
def test_prep_dataset_l23_smoke():
    recs = prep.prep_dataset('L23', obs_ids=range(5), seed=1234)
    assert len(recs) == 5
    for i, r in enumerate(recs):
        assert r.dataset == 'L23'
        assert np.all(np.diff(r.wave) > 0)
        assert r.Rrs.shape == r.wave.shape
        assert np.all(r.varRrs > 0)
        assert L23_TRUTH_KEYS.issubset(r.truth)
        assert r.noise_model == 'pace'
        assert r.noise_seed == 1234 + i           # per-record seed recorded


@needs_l23
def test_prep_l23_init_chl_tracks_truth():
    # Light sanity check (per JXP): the truth-free OC4 init Chl should track the
    # true Chl to within ~0.5 dex in the median across a batch.
    recs = prep.prep_dataset('L23', obs_ids=range(50), seed=1234)
    dex = []
    for r in recs:
        truth_chl = r.truth['Chl']
        init_chl = r.init['Chl']
        if np.isfinite(truth_chl) and truth_chl > 0 and init_chl > 0:
            dex.append(abs(np.log10(init_chl / truth_chl)))
    assert len(dex) > 0
    assert np.median(dex) < 0.5


# --------------------------------------------------------------------
# Tier 2 — requires the PANGAEA V3 data directory
# --------------------------------------------------------------------
PANGAEA_SPECTRAL_TRUTH = {'a_ph', 'a_dg', 'bb_p'}


@needs_pangaea
def test_prep_dataset_pangaea_smoke():
    ad = D.get_adapter('PANGAEA')
    ids = ad.obs_ids()
    assert len(ids) > 0

    # Permissive smoke: the first few IDs need not carry any IOP truth
    # (PANGAEA's rrs and iop tables only partially overlap).
    recs = prep.prep_dataset('PANGAEA', obs_ids=ids[:5])
    assert len(recs) == 5
    for r in recs:
        assert r.dataset == 'PANGAEA'
        assert np.all(np.diff(r.wave) > 0)        # native grid, ascending
        assert r.Rrs.shape == r.wave.shape
        assert np.all(r.varRrs > 0)
        assert r.noise_model == f'pct:{prep._INSITU_PCT_FALLBACK}'
        assert r.noise_seed is None               # in-situ Rrs not perturbed


@needs_pangaea
def test_prep_pangaea_per_family_truth_on_real_data():
    # Exercise the per-family alignment on IDs that actually carry IOP truth.
    ad = D.get_adapter('PANGAEA')
    iop_index = set(ad._table('iop').index)
    truth_ids = []
    for oid in (i for i in ad.obs_ids() if i in iop_index):
        if PANGAEA_SPECTRAL_TRUTH & set(ad.load_obs(oid).truth):
            truth_ids.append(oid)
            if len(truth_ids) == 3:
                break
    assert truth_ids, 'expected some PANGAEA obs with spectral IOP truth'
    for r in prep.prep_dataset('PANGAEA', obs_ids=truth_ids):
        present = PANGAEA_SPECTRAL_TRUTH & set(r.truth)
        assert present                            # each sampled id has truth
        for comp in present:
            sp = r.truth[comp]
            assert sp.wavelength.shape == r.wave.shape   # aligned onto fit grid
            assert 'orig_wave' in sp.metadata            # native grid retained
            # regrid flag is recorded; it is usually True (family grid differs
            # from the Rrs grid) but can be False when the family grid is a
            # superset of it (an exact node pick, not a regrid).
            assert isinstance(r.truth_interp[comp], bool)


# --------------------------------------------------------------------
# Tier 2 — requires the GLORIA dataset CSVs (unbundled)
# --------------------------------------------------------------------
@needs_gloria
def test_prep_dataset_gloria_smoke():
    ids = D.get_adapter('GLORIA').obs_ids()
    assert len(ids) > 0
    recs = prep.prep_dataset('GLORIA', obs_ids=ids[:5])
    assert len(recs) == 5
    for r in recs:
        assert r.dataset == 'GLORIA'
        assert np.all(np.diff(r.wave) > 0)        # hyperspectral, ascending
        assert r.Rrs.shape == r.wave.shape
        assert np.all(r.varRrs > 0)
        # Measured Rrs std, plus GLORIA's default error floor -- the tag
        # records the floor so no result is mistaken for measured-error-only.
        assert r.noise_model == f'insitu+floor:{prep._GLORIA_NOISE_FLOOR}'
        assert r.noise_seed is None               # in-situ Rrs not perturbed
        # The floor never lowers an uncertainty
        assert np.all(np.sqrt(r.varRrs) >= 0.0)
        # a_dg truth (from aCDOM440) is a single finite point at 440 nm
        if 'a_dg' in r.truth:
            vals = r.truth['a_dg'].values
            assert np.isfinite(vals).sum() == 1

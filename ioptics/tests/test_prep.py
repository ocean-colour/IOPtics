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
from ioptics.tests.conftest import needs_l23

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

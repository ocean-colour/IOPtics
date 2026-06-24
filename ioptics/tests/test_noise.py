"""Tier-1 (data-independent) unit tests for ``ioptics.noise``.

Covers the ``pct`` and ``insitu`` models (no ocpy data needed) and the
reproducibility of the seeded perturbation. The ``pace`` model is exercised
under Tier-2 (it reads ocpy's PACE error table).
"""

import numpy as np
import pytest

from ioptics.noise import attach_noise


def _synthetic():
    wave = np.linspace(400.0, 700.0, 13)
    Rrs = 0.01 * np.exp(-0.003 * (wave - 400.0)) + 1e-3
    return wave, Rrs


def test_pct_variance_and_tag():
    wave, Rrs = _synthetic()
    varRrs, Rrs_out, Rrs_clean, tag, seed_used = attach_noise(
        wave, Rrs, model='pct:0.05', add_noise=False)
    np.testing.assert_allclose(varRrs, (0.05 * Rrs) ** 2)
    assert tag == 'pct:0.05'
    # add_noise=False -> untouched, no seed
    np.testing.assert_array_equal(Rrs_out, Rrs)
    np.testing.assert_array_equal(Rrs_clean, Rrs)
    assert seed_used is None


def test_add_noise_is_reproducible_with_seed():
    wave, Rrs = _synthetic()
    out_a = attach_noise(wave, Rrs, model='pct:0.05', add_noise=True, seed=1234)
    out_b = attach_noise(wave, Rrs, model='pct:0.05', add_noise=True, seed=1234)
    # same seed -> identical realization, seed recorded
    np.testing.assert_array_equal(out_a[1], out_b[1])
    assert out_a[4] == 1234
    # perturbation actually moved Rrs, but Rrs_clean kept the input
    assert not np.array_equal(out_a[1], out_a[2])
    np.testing.assert_array_equal(out_a[2], Rrs)


def test_different_seeds_differ():
    wave, Rrs = _synthetic()
    a = attach_noise(wave, Rrs, model='pct:0.1', add_noise=True, seed=1)[1]
    b = attach_noise(wave, Rrs, model='pct:0.1', add_noise=True, seed=2)[1]
    assert not np.array_equal(a, b)


def test_insitu_uses_measured_errors():
    wave, Rrs = _synthetic()
    err = np.full_like(wave, 2e-4)
    varRrs, Rrs_out, Rrs_clean, tag, seed_used = attach_noise(
        wave, Rrs, model='insitu', add_noise=False, Rrs_err=err)
    np.testing.assert_allclose(varRrs, err ** 2)
    assert tag == 'insitu'
    np.testing.assert_array_equal(Rrs_out, Rrs)


def test_insitu_requires_errors():
    wave, Rrs = _synthetic()
    with pytest.raises(ValueError, match='Rrs_err'):
        attach_noise(wave, Rrs, model='insitu', add_noise=False)


def test_unknown_model_raises():
    wave, Rrs = _synthetic()
    with pytest.raises(ValueError, match='unknown noise model'):
        attach_noise(wave, Rrs, model='bogus')


def test_bad_pct_raises():
    wave, Rrs = _synthetic()
    with pytest.raises(ValueError, match="pct"):
        attach_noise(wave, Rrs, model='pct:abc')

"""Tier-1 (data-independent) unit tests for ``ioptics.noise``.

Covers the ``pct`` and ``insitu`` models (no ocpy data needed) and the
reproducibility of the seeded perturbation. The ``pace`` model is exercised
under Tier-2 (it reads ocpy's PACE error table).
"""

import numpy as np
import pytest

from ioptics.noise import attach_noise
from ioptics.tests.conftest import needs_pace


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


@needs_pace
def test_pace_model_native_grid():
    # The PACE model reads ocpy's bundled PACE_error.csv. Some ocpy installs
    # don't package it (e.g. CI's pip-from-git), so this skips when absent.
    wave, Rrs = _synthetic()
    varRrs, Rrs_out, Rrs_clean, tag, seed_used = attach_noise(
        wave, Rrs, model='pace', add_noise=True, seed=7)
    assert tag == 'pace'
    assert varRrs.shape == wave.shape       # evaluated on the native grid
    assert np.all(varRrs > 0)
    assert seed_used == 7
    assert not np.array_equal(Rrs_out, Rrs_clean)


# --------------------------------------------------------------------
# Inflated-noise floor (GLORIA's default; see prep._GLORIA_NOISE_FLOOR)
# --------------------------------------------------------------------
def test_floor_raises_tight_errors_only_where_needed():
    # GLORIA-like: a quoted error far tighter than any model's misfit.
    wave, Rrs = _synthetic()
    measured = np.full_like(Rrs, 1.5e-4)
    varRrs, _, Rrs_clean, tag, _ = attach_noise(
        wave, Rrs, model='insitu', add_noise=False, Rrs_err=measured,
        floor_frac=0.05)

    sigma = np.sqrt(varRrs)
    expected = np.maximum(measured, 0.05 * np.abs(Rrs_clean))
    assert np.allclose(sigma, expected)
    # It is a max: never below the measured error, and strictly above it
    # wherever 5% of Rrs is the larger of the two.
    assert np.all(sigma >= measured - 1e-15)
    assert np.any(sigma > measured)
    # ... and where Rrs is small the measured error stays in charge
    small = 0.05 * np.abs(Rrs_clean) < measured
    if small.any():
        assert np.allclose(sigma[small], measured[small])


def test_floor_labels_itself_in_the_tag():
    # An inflated-noise result must never look like a measured-error one.
    wave, Rrs = _synthetic()
    _, _, _, plain, _ = attach_noise(wave, Rrs, model='insitu',
                                     add_noise=False, Rrs_err=0.1 * Rrs)
    _, _, _, floored, _ = attach_noise(wave, Rrs, model='insitu',
                                       add_noise=False, Rrs_err=0.1 * Rrs,
                                       floor_frac=0.05)
    assert plain == 'insitu'
    assert floored == 'insitu+floor:0.05'
    assert floored != plain


def test_floor_applies_to_any_base_model():
    wave, Rrs = _synthetic()
    _, _, _, tag, _ = attach_noise(wave, Rrs, model='pct:0.02',
                                   add_noise=False, floor_frac=0.05)
    assert tag == 'pct:0.02+floor:0.05'


def test_floor_feeds_the_perturbation():
    # The realization must be drawn from the *floored* sigma, so the noise a
    # record carries and the weight the fit uses stay consistent.
    wave, Rrs = _synthetic()
    measured = np.full_like(Rrs, 1e-6)          # negligible next to the floor
    var_plain, out_plain, clean, _, _ = attach_noise(
        wave, Rrs, model='insitu', add_noise=True, seed=3, Rrs_err=measured)
    var_floor, out_floor, _, _, _ = attach_noise(
        wave, Rrs, model='insitu', add_noise=True, seed=3, Rrs_err=measured,
        floor_frac=0.05)
    assert np.all(var_floor > var_plain)
    # same seed, bigger sigma -> a bigger departure from the clean spectrum
    assert (np.abs(out_floor - clean).sum()
            > np.abs(out_plain - clean).sum())


def test_bad_floor_raises():
    wave, Rrs = _synthetic()
    with pytest.raises(ValueError, match='floor_frac'):
        attach_noise(wave, Rrs, model='pct:0.05', add_noise=False,
                     floor_frac=0.0)


# --------------------------------------------------------------------
# Missing measured errors. 70% of GLORIA spectra quote no Rrs uncertainty
# at any band; a NaN-propagating floor hands the fitter all-NaN weights and
# scipy refuses to start, which reads as a convergence failure.
# --------------------------------------------------------------------
def test_floor_fills_missing_errors_and_says_so():
    wave, Rrs = _synthetic()
    measured = np.full_like(Rrs, np.nan)        # nothing measured, anywhere
    varRrs, _, Rrs_clean, tag, _ = attach_noise(
        wave, Rrs, model='insitu', add_noise=False, Rrs_err=measured,
        floor_frac=0.05)

    assert np.all(np.isfinite(varRrs))
    assert np.all(varRrs > 0)
    np.testing.assert_allclose(np.sqrt(varRrs), 0.05 * np.abs(Rrs_clean))
    # Wholly imputed weights are a different claim from floored measured ones.
    assert tag == 'insitu+imputed:0.05'


def test_floor_keeps_the_measured_errors_it_has():
    wave, Rrs = _synthetic()
    measured = np.full_like(Rrs, 1e-6)          # tiny, so the floor bites
    measured[::3] = np.nan                      # ... but absent every third band
    varRrs, _, Rrs_clean, tag, _ = attach_noise(
        wave, Rrs, model='insitu', add_noise=False, Rrs_err=measured,
        floor_frac=0.05)

    assert np.all(np.isfinite(varRrs))
    # Partly measured -> still 'floor', not 'imputed': something was measured.
    assert tag == 'insitu+floor:0.05'
    np.testing.assert_allclose(np.sqrt(varRrs), 0.05 * np.abs(Rrs_clean))


def test_floor_never_produces_a_zero_sigma():
    # A band at Rrs == 0 would floor to sigma = 0, i.e. an infinite weight;
    # the spectrum's own scale stands in there.
    wave, Rrs = _synthetic()
    Rrs = Rrs.copy()
    Rrs[4] = 0.0
    varRrs, _, _, _, _ = attach_noise(
        wave, Rrs, model='insitu', add_noise=False,
        Rrs_err=np.full_like(Rrs, np.nan), floor_frac=0.05)
    assert np.all(varRrs > 0)
    assert np.all(np.isfinite(varRrs))


def test_floorless_missing_errors_stay_missing():
    # Without a floor the NaN is *not* invented away: an absent uncertainty is
    # a data gap, and only an explicit floor decides what to do about it.
    wave, Rrs = _synthetic()
    varRrs, _, _, tag, _ = attach_noise(
        wave, Rrs, model='insitu', add_noise=False,
        Rrs_err=np.full_like(Rrs, np.nan))
    assert np.all(~np.isfinite(varRrs))
    assert tag == 'insitu'

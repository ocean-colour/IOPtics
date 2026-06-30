"""Tests for ``ioptics.datasets`` — registry, ``RawObs``, and the L23 adapter.

Tier-1 (data-independent) covers the registry, the ``RawObs`` carrier, the
``Adapter`` protocol, the L23 truth-key mapping, and the ``X=2`` guard. Tier-2
(``@needs_l23``) loads a real L23 row and checks its shape + truth keys.
"""

import numpy as np
import pytest

from ioptics import datasets as D
from ioptics.datasets import Adapter, L23Adapter, RawObs
from ioptics.tests.conftest import needs_l23

L23_TRUTH_KEYS = {'a', 'bb', 'a_ph', 'a_dg', 'bb_p', 'a_w', 'bb_w',
                  'Chl', 'Y', 'Sdg'}


# --------------------------------------------------------------------
# Tier 1 — data-independent
# --------------------------------------------------------------------
def test_registry_seeded_with_l23():
    assert 'L23' in D.available_datasets()
    assert isinstance(D.get_adapter('L23'), L23Adapter)


def test_l23_adapter_satisfies_protocol():
    assert isinstance(D.get_adapter('L23'), Adapter)


def test_register_and_retrieve_roundtrip():
    sentinel = object()
    D.register_dataset('_TMP', sentinel)
    try:
        assert D.get_adapter('_TMP') is sentinel
        assert '_TMP' in D.available_datasets()
    finally:
        D.ADAPTERS.pop('_TMP', None)


def test_rawobs_defaults_independent():
    a = RawObs(wave=np.arange(3.0), Rrs=np.zeros(3), truth={})
    b = RawObs(wave=np.arange(3.0), Rrs=np.zeros(3), truth={})
    assert a.Rrs_err is None
    a.meta['x'] = 1
    assert b.meta == {}            # default_factory -> no shared mutable default


def test_l23_truth_map_keys():
    # the canonical IOPtics truth keys; redundant anw/bbnw intentionally absent
    assert set(D._L23_TRUTH_MAP.values()) == L23_TRUTH_KEYS
    assert 'anw' not in D._L23_TRUTH_MAP.values()
    assert 'bbnw' not in D._L23_TRUTH_MAP.values()


def test_l23_x2_is_guarded():
    # X=2 (Raman-only) is rejected before any data load, so no data needed.
    with pytest.raises(ValueError, match='X=2'):
        L23Adapter().obs_ids(X=2)


# --------------------------------------------------------------------
# Tier 2 — requires the L23 data tree
# --------------------------------------------------------------------
@needs_l23
def test_l23_load_obs_native_grid_and_truth():
    ad = D.get_adapter('L23')
    ids = ad.obs_ids()
    assert len(ids) > 0

    raw = ad.load_obs(ids[0])
    assert isinstance(raw, RawObs)

    # native grid, ascending, Rrs aligned
    assert raw.wave.ndim == 1 and raw.wave.size > 0
    assert np.all(np.diff(raw.wave) > 0)
    assert raw.Rrs.shape == raw.wave.shape

    # full truth: spectral arrays on the native grid + scalar floats
    assert L23_TRUTH_KEYS.issubset(raw.truth)
    for comp in ('a', 'bb', 'a_ph', 'a_dg', 'bb_p', 'a_w', 'bb_w'):
        assert np.asarray(raw.truth[comp]).shape == raw.wave.shape
    for scalar in ('Chl', 'Y', 'Sdg'):
        assert np.ndim(raw.truth[scalar]) == 0

    # provenance metadata
    assert raw.meta['dataset'] == 'L23'
    assert raw.meta['X'] == 1 and raw.meta['Y'] == 0
    assert raw.Rrs_err is None

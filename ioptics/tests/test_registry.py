"""Tier-1 tests for ``ioptics.algorithms.registry`` (data-free).

Checks the in-tandem seeding (expb_pow + giop), the lookup helpers, and the
duplicate-name guard. Seeding imports the *released* ``bing.parameters.standard``
(see the Stage-2 prompt's CI caveat) but builds no models, so it is
data-independent.
"""

import pytest

from ioptics.algorithms import registry
from ioptics.algorithms.spec import AlgorithmSpec


def test_seeded_with_both_in_tandem():
    avail = registry.available()
    assert 'expb_pow' in avail
    assert 'giop' in avail
    assert registry.get('expb_pow').anw_model == 'ExpBricaud'
    assert registry.get('expb_pow').label == 'ExpB_Pow'
    assert registry.get('giop').anw_model == 'GIOP'
    assert registry.get('giop').label == 'GIOP'


def test_available_is_sorted():
    assert registry.available() == sorted(registry.available())


def test_get_unknown_raises():
    with pytest.raises(KeyError, match='unknown algorithm'):
        registry.get('does_not_exist')


def test_register_duplicate_is_guarded():
    dup = registry.get('giop')
    with pytest.raises(ValueError, match='already registered'):
        registry.register(dup)
    # explicit overwrite is allowed
    registry.register(dup, overwrite=True)


def test_register_and_retrieve_new(tmp_path):
    spec = AlgorithmSpec(
        name='_tmp_alg', label='Tmp', anw_model='GIOP', bbnw_model='Lee',
        apriors=[{'flavor': 'log_uniform', 'pmin': -6, 'pmax': 5}],
        bpriors=[{'flavor': 'log_uniform', 'pmin': -6, 'pmax': 5}],
    )
    registry.register(spec)
    try:
        assert registry.get('_tmp_alg') is spec
        assert '_tmp_alg' in registry.available()
    finally:
        registry.REGISTRY.pop('_tmp_alg', None)

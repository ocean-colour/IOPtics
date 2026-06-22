"""Shared pytest fixtures and skip guards for the IOPtics test suite.

Two tiers, mirroring ocpy's ``test_pangaea.py`` pattern (see
``docs/design/IOPtics_implementation.md`` §"Testing & CI"):

- **Tier 1 — data-independent** tests run everywhere (laptop, CI runner) on
  tiny synthetic fixtures.
- **Tier 2 — data-dependent** tests skip automatically when the ``$OS_COLOR``
  data tree (or a specific dataset) is unavailable, so the suite is green and
  fast where no data is mounted.

Tier-2 tests opt in with the markers exported here::

    from ioptics.tests.conftest import needs_l23

    @needs_l23
    def test_prep_l23():
        ...

The availability probes are wrapped in ``try/except`` so test *collection*
never fails — a missing or broken ocpy import simply means the guarded tests
skip rather than erroring the run.
"""

import os

import pytest


def _os_color_available():
    """True if the ``$OS_COLOR`` data tree is set and present on disk."""
    root = os.getenv('OS_COLOR')
    return root is not None and os.path.isdir(root)


def _l23_available():
    """True if the Loisel+2023 Hydrolight data can be resolved via ocpy."""
    try:
        from ocpy.hydrolight import loisel23
        return os.path.isfile(os.path.join(loisel23.l23_path, 'Hydrolight100.nc'))
    except Exception:
        return False


def _pangaea_available():
    """True if the PANGAEA V3 directory can be resolved via ocpy."""
    try:
        from ocpy.insitu import pangaea
        pangaea.pangaea_path()      # raises FileNotFoundError if unavailable
        return True
    except Exception:
        return False


needs_data = pytest.mark.skipif(
    not _os_color_available(), reason='requires the $OS_COLOR data tree')

needs_l23 = pytest.mark.skipif(
    not _l23_available(), reason='requires L23 (Loisel+2023) Hydrolight data')

needs_pangaea = pytest.mark.skipif(
    not _pangaea_available(), reason='requires the PANGAEA V3 data directory')

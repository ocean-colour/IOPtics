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

**Hang guard.** Every test runs under a wall-clock ceiling (see
:func:`_guard_against_hangs`) so a wedged test — a deadlocked
``ProcessPoolExecutor`` batch fit, a blocked data load, an MCMC that never
returns — fails fast with a traceback instead of hanging the whole run. It is
dependency-free (Unix ``SIGALRM``) and defers to ``pytest-timeout`` when that
plugin is installed.
"""

import os
import faulthandler
import signal
import threading

import pytest


# --------------------------------------------------------------------
# Hang guard — a per-test wall-clock ceiling so nothing hangs the run
# --------------------------------------------------------------------
def _pytest_timeout_installed():
    """True if the ``pytest-timeout`` plugin is importable (then defer to it)."""
    try:
        import pytest_timeout       # noqa: F401
        return True
    except Exception:
        return False


def _test_timeout_seconds():
    """Per-test ceiling in seconds; override with ``$IOPTICS_TEST_TIMEOUT``.

    Defaults to 120 s — far above any real test here (the whole suite runs in
    well under a minute) but low enough that a genuine hang is caught quickly.
    Set to ``0`` (or a negative value) to disable the guard.
    """
    raw = os.getenv('IOPTICS_TEST_TIMEOUT', '120')
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 120.0


def pytest_configure(config):
    """Register the ``timeout`` marker (also used by ``pytest-timeout``)."""
    config.addinivalue_line(
        'markers',
        'timeout(seconds): override the per-test hang-guard ceiling '
        '(0 disables it for that test).')


@pytest.fixture(autouse=True)
def _guard_against_hangs(request):
    """Fail a test that exceeds the wall-clock ceiling instead of hanging.

    Uses ``SIGALRM``/``setitimer`` (Unix, main thread only). When
    ``pytest-timeout`` is installed we defer to it — it handles some C-level
    hangs this fixture cannot. A hang dumps all thread tracebacks (via
    ``faulthandler``) before failing, so the culprit is easy to spot.
    """
    # Defer to pytest-timeout when present; skip where SIGALRM is unavailable
    # (non-Unix) or unusable (worker thread — signals only fire on the main one).
    if (_pytest_timeout_installed()
            or not hasattr(signal, 'SIGALRM')
            or threading.current_thread() is not threading.main_thread()):
        yield
        return

    timeout = _test_timeout_seconds()
    marker = request.node.get_closest_marker('timeout')
    if marker is not None and marker.args:
        timeout = float(marker.args[0])
    if timeout <= 0:
        yield
        return

    def _on_alarm(signum, frame):
        faulthandler.dump_traceback()
        raise TimeoutError(
            f'test exceeded the {timeout:g}s hang-guard ceiling '
            f'($IOPTICS_TEST_TIMEOUT); treated as a hang')

    previous = signal.signal(signal.SIGALRM, _on_alarm)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


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


def _gloria_available():
    """True if the GLORIA CSVs are present where ``gloria.load_gloria`` looks.

    Mirrors ocpy's path resolution: ``$OS_COLOR/GLORIA`` when ``$OS_COLOR`` is
    set (the download target — see Stage-6 "Grab GLORIA"), else ocpy's packaged
    ``data/Rrs/GLORIA``. The CSVs are unbundled, so this probes the effective
    location rather than assuming the package tree.
    """
    try:
        from importlib import resources
        from ocpy.insitu import gloria       # noqa: F401 (import guard)
        if os.getenv('OS_COLOR') is not None:
            gloria_dir = os.path.join(os.getenv('OS_COLOR'), 'GLORIA')
        else:
            gloria_dir = os.path.join(resources.files('ocpy'),
                                      'data', 'Rrs', 'GLORIA')
        return os.path.isfile(os.path.join(gloria_dir, 'GLORIA_Rrs.csv'))
    except Exception:
        return False


def _correct_atmosphere_available():
    """True if ``correct_atmosphere`` is importable (Chl-fluorescence ``Ed``).

    The inelastic RT path (L23 X=4) seeds the a-model's downwelling irradiance
    from ``correct_atmosphere.downwelling``; it is a bing-side dependency not on
    PyPI, so the Chl-fluorescence smoke test skips where it is absent.
    """
    try:
        from correct_atmosphere import downwelling      # noqa: F401
        return True
    except Exception:
        return False


def _sphinx_available():
    """True if Sphinx is importable (docs-only dep; not installed in light CI)."""
    try:
        import sphinx        # noqa: F401
        return True
    except Exception:
        return False


def _pace_data_available():
    """True if ocpy ships its PACE error table (``PACE_error.csv``).

    The ``pace`` noise model reads this bundled data file; some ocpy installs
    don't package it, so the dependent test skips rather than failing.
    """
    try:
        import numpy as np
        from ocpy.satellites import pace
        pace.gen_noise_vector(np.array([500.0]))
        return True
    except Exception:
        return False


needs_data = pytest.mark.skipif(
    not _os_color_available(), reason='requires the $OS_COLOR data tree')

needs_l23 = pytest.mark.skipif(
    not _l23_available(), reason='requires L23 (Loisel+2023) Hydrolight data')

needs_pangaea = pytest.mark.skipif(
    not _pangaea_available(), reason='requires the PANGAEA V3 data directory')

needs_gloria = pytest.mark.skipif(
    not _gloria_available(), reason='requires the GLORIA dataset CSVs (unbundled)')

needs_pace = pytest.mark.skipif(
    not _pace_data_available(), reason="requires ocpy's bundled PACE_error.csv")

needs_inelastic = pytest.mark.skipif(
    not _correct_atmosphere_available(),
    reason='requires correct_atmosphere (downwelling Ed for Chl fluorescence)')

needs_sphinx = pytest.mark.skipif(
    not _sphinx_available(), reason='requires Sphinx (docs build; not in light CI)')


def _amt24_available():
    """True if the AMT24 HyperSAS Level-2 tree is mounted under ``$OS_COLOR``."""
    root = os.getenv('OS_COLOR')
    if root is None:
        return False
    return any(os.path.isdir(os.path.join(root, *parts, 'Radiometry', 'level2'))
               for parts in (('AMT', 'AMT24'), ('AMT24',)))


needs_amt24 = pytest.mark.skipif(
    not _amt24_available(),
    reason='requires the AMT24 tree under $OS_COLOR (MOANA track)')

#: Earthdata-credentialled tests (MOANA validation target (iii)) — Q&A #16.
needs_netrc = pytest.mark.skipif(
    not os.path.isfile(os.path.expanduser('~/.netrc')),
    reason='requires Earthdata credentials in ~/.netrc')

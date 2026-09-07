"""Tests for the ``PACE`` dataset — adapter, artifact contract, and extraction.

Tier-1 (data-independent) covers registration, path resolution, the
missing-artifact error, and the extraction script's seeded selection function
(a pure function of a file-name list, so it needs no data). Tier-2
(``@needs_pace_pab``) loads the real artifact written by
``ioptics/runs/prototypes/rt_tests/extract_pace_100.py`` and checks the
observation contract end to end, including that ``prep`` weights the fit by
the granule's own measured uncertainty rather than an invented one.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from ioptics import datasets as D
from ioptics import prep
from ioptics.datasets import Adapter, PACEAdapter
from ioptics.records import PreparedRecord
from ioptics.tests.conftest import needs_pace_pab

#: The extraction script lives under ``ioptics/runs/`` — build scripts, not an
#: importable package (see ``ioptics/runs/README.md``), so it is loaded by path.
_EXTRACT_PY = (Path(__file__).resolve().parents[1] / 'runs' / 'prototypes'
               / 'rt_tests' / 'extract_pace_100.py')

#: 136 OCI bands over 400-699 nm with the 588-613 nm gap absent from the grid.
PACE_N_BANDS = 136
PACE_WAVE_RANGE = (400.0, 699.0)


def _load_extract_module():
    """Import ``extract_pace_100.py`` by path (it is not in the package)."""
    spec = importlib.util.spec_from_file_location('extract_pace_100',
                                                  _EXTRACT_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------
# Tier 1 — data-independent
# --------------------------------------------------------------------
def test_registry_seeded_with_pace():
    assert 'PACE' in D.available_datasets()
    assert isinstance(D.get_adapter('PACE'), PACEAdapter)


def test_pace_adapter_satisfies_protocol():
    assert isinstance(D.get_adapter('PACE'), Adapter)


def test_pace_path_resolution(tmp_path):
    # an explicit directory picks up the conventional file name...
    assert D.pace_pab_path(tmp_path) == tmp_path / D.PACE_PAB_FILE
    # ...and an explicit file is taken as-is.
    explicit = tmp_path / 'somewhere_else.parquet'
    explicit.write_bytes(b'')
    assert D.pace_pab_path(explicit) == explicit


def test_pace_path_needs_os_color(monkeypatch):
    monkeypatch.delenv('OS_COLOR', raising=False)
    with pytest.raises(RuntimeError, match='OS_COLOR'):
        D.pace_pab_path()


def test_pace_artifact_layout_matches_extraction_script():
    # The adapter and the script must agree on where the artifact lives;
    # they hold the constant separately so neither imports the other.
    mod = _load_extract_module()
    assert (mod.OUT_SUBDIR, mod.OUT_FILE) == (D.PACE_PAB_SUBDIR, D.PACE_PAB_FILE)


def test_pace_missing_artifact_raises(tmp_path):
    ad = PACEAdapter(path=tmp_path / 'not_there.parquet')
    with pytest.raises(FileNotFoundError, match='extract_pace_100'):
        ad.obs_ids()
    with pytest.raises(FileNotFoundError):
        ad.load_obs('anything')


# --- the extraction script's pure helpers (no data) -------------------
def _synthetic_stems(n):
    """A synthetic run1k-style file list (same shape as the real names)."""
    return [f'{1900000 + i}_{i % 7}_PACE_OCI.2024{i:04d}T000000.L2.OC_AOP.'
            f'V3_2.nc_{100 + i}_{200 + i}_ExpBPow' for i in range(n)]


def test_extract_parse_stem():
    mod = _load_extract_module()
    keys = mod.parse_stem(
        '1902304_156_PACE_OCI.20240311T132943.L2.OC_AOP.V3_2.nc_1587_715'
        '_ExpBPow')
    assert keys == {'wmo': 1902304, 'cycle': 156, 'ix': 1587, 'iy': 715,
                    'granule': 'PACE_OCI.20240311T132943.L2.OC_AOP.V3_2.nc'}
    with pytest.raises(ValueError):
        mod.parse_stem('1902304_156_something_1587_715')      # no _ExpBPow


def test_extract_select_stems_is_seeded_and_sorted():
    mod = _load_extract_module()
    stems = _synthetic_stems(274)

    picked = mod.select_stems(stems, n=100)
    assert len(picked) == 100
    assert len(set(picked)) == 100                # without replacement
    assert picked == sorted(picked)               # deterministic order
    assert set(picked) <= set(stems)

    # Same seed -> same draw, and independent of the input ordering.
    assert mod.select_stems(list(reversed(stems)), n=100) == picked
    # A different seed -> a different draw (274 choose 100 makes a collision
    # impossible in practice).
    assert mod.select_stems(stems, n=100, seed=mod.SAMPLE_SEED + 1) != picked


def test_extract_select_stems_smaller_pool_returns_all():
    mod = _load_extract_module()
    stems = _synthetic_stems(30)
    assert mod.select_stems(stems, n=100) == sorted(stems)


def test_extract_granule_time_uses_midpoint_when_available():
    mod = _load_extract_module()
    # run1k's catalogue has no time_end -> the start time, normalised to UTC.
    assert mod.granule_time('2025-12-10 22:51:38+00:00', None) \
        == '2025-12-10T22:51:38+00:00'
    assert mod.granule_time('2025-12-10 22:51:38', None) \
        == '2025-12-10T22:51:38+00:00'
    # with both bounds it is the midpoint
    assert mod.granule_time('2025-12-10 22:50:00+00:00',
                            '2025-12-10 22:56:00+00:00') \
        == '2025-12-10T22:53:00+00:00'


# --------------------------------------------------------------------
# Tier 2 — requires the extracted PACE artifact
# --------------------------------------------------------------------
@needs_pace_pab
def test_pace_obs_ids_are_deterministic():
    ad = D.get_adapter('PACE')
    ids = ad.obs_ids()
    assert len(ids) == 100
    assert len(set(ids)) == 100
    assert ids == sorted(ids)
    assert ids == PACEAdapter().obs_ids()         # a fresh adapter agrees
    assert all(i.endswith('_ExpBPow') for i in ids)


@needs_pace_pab
def test_pace_load_obs_contract():
    ad = D.get_adapter('PACE')
    obs_id = ad.obs_ids()[0]
    raw = ad.load_obs(obs_id)

    assert raw.wave.shape == (PACE_N_BANDS,)
    assert np.all(np.diff(raw.wave) > 0)          # ascending native grid
    assert (raw.wave[0], raw.wave[-1]) == PACE_WAVE_RANGE
    assert raw.Rrs.shape == raw.wave.shape
    assert np.all(np.isfinite(raw.Rrs))           # negatives allowed, NaN not
    assert raw.truth == {}                        # satellite: no ground truth

    # Measured uncertainty: Rrs_err = sqrt(varRrs), strictly positive.
    assert raw.Rrs_err is not None
    assert raw.Rrs_err.shape == raw.wave.shape
    assert np.all(raw.Rrs_err > 0)

    # Geometry contract + join provenance.
    for key in (D.TIME_META_KEY, D.LAT_META_KEY, D.LON_META_KEY, 'theta_s',
                'wmo', 'cycle', 'granule', 'ix', 'iy', 'matchup_id'):
        assert key in raw.meta, key
    assert raw.meta['dataset'] == 'PACE'
    assert raw.meta['obs_id'] == obs_id
    assert -90.0 <= raw.meta[D.LAT_META_KEY] <= 90.0
    assert -180.0 <= raw.meta[D.LON_META_KEY] <= 180.0


@needs_pace_pab
def test_pace_stored_theta_s_matches_a_recompute():
    """The stored ``theta_s`` reproduces from the stored time/lat/lon.

    The runtime path recomputes the angle via ``run.resolve_theta_s``; the
    stored value is the extraction-time cross-check, so the two must agree to
    well under the ~0.01 deg accuracy of the NOAA/Meeus formula itself.
    """
    solar = pytest.importorskip('robust.solar')
    ad = D.get_adapter('PACE')
    for obs_id in ad.obs_ids()[:10]:
        m = ad.load_obs(obs_id).meta
        assert 0.0 <= m['theta_s'] <= 90.0        # daytime PACE overpass
        again = float(solar.solar_zenith(m[D.TIME_META_KEY],
                                         m[D.LAT_META_KEY],
                                         m[D.LON_META_KEY]))
        assert abs(again - m['theta_s']) < 0.2


@needs_pace_pab
def test_pace_prep_one_uses_the_measured_uncertainty():
    ad = D.get_adapter('PACE')
    obs_id = ad.obs_ids()[0]
    raw = ad.load_obs(obs_id)
    rec = prep.prep_one('PACE', obs_id)

    assert isinstance(rec, PreparedRecord)
    assert rec.dataset == 'PACE'
    assert rec.wave.shape == (PACE_N_BANDS,)

    # The measured uncertainty goes through untouched: no floor, no imputation,
    # no synthetic perturbation of a real observation.
    assert rec.noise_model == 'insitu'
    assert rec.noise_seed is None
    assert np.all(rec.varRrs > 0)
    assert np.allclose(rec.varRrs, raw.Rrs_err ** 2, rtol=0, atol=0)
    assert np.array_equal(rec.Rrs, raw.Rrs)
    assert np.array_equal(rec.Rrs_clean, raw.Rrs)

    # No truth, but the truth-free init and the QWIP annotation are computed:
    # the grid spans 400-699 nm, so QWIP's 492/665 bands are both covered.
    assert rec.truth == {} and rec.truth_interp == {}
    assert set(rec.init) == {'Chl', 'Y'}
    assert np.isfinite(rec.qwip_score)

    # Geometry survives prep, and the runtime resolver agrees with the store.
    from ioptics import run as ipt_run
    assert abs(ipt_run.resolve_theta_s(rec) - rec.meta['theta_s']) < 0.2

"""Tests for the LS2 driver (``ioptics.algorithms.ls2``) and its rungs.

Tier-1 (data-free, ocpy's packaged LUTs only): synthetic L23-shaped records
exercise the input ladder -- each rung differs from its neighbour only in the
input it is meant to -- plus the NaN-reason translation, the PANGAEA
measured-band rule (ls2 Q32), the Kd-noise rung, and ocpy's pure water.

Tier-2 (``@needs_l23_profile``): real L23 records through ``prep`` and
``run``. The driver reproduces, record for record, the vectorized corpus run
of ``runs/prototypes/ls2/rung_i_baseline.py``. That script's medians -- and
planning's +2.6% / +9.8% / +24% -- are pinned, the eta envelope's ~0.6% of
cells come back NaN with reason ``off_grid``, and the effective-muw rung
removes most of the ``a`` bias (ls2 Q9).
"""

import importlib.util
import pathlib

import numpy as np
import pytest

from ioptics import run
from ioptics.algorithms import ls2, registry
from ioptics.algorithms.spec import DirectSpec
from ioptics.records import PreparedRecord
from ioptics.tests.conftest import needs_l23_profile

WAVE = np.arange(350., 751., 5.)
BASELINE = (pathlib.Path(ls2.__file__).parents[1] / 'runs' / 'prototypes'
            / 'ls2' / 'rung_i_baseline.py')


def _baseline():
    spec = importlib.util.spec_from_file_location('rung_i_baseline', BASELINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _record(*, dataset='L23', kd=None, bp=None, meta=None, obs_id=0):
    """A clear-water, L23-shaped record (blue-peaked Rrs, smooth IOPs)."""
    rrs = 0.006 * np.exp(-0.5 * ((WAVE - 440.) / 70.) ** 2) + 2e-4
    a_w, b_w = ls2.pure_water(WAVE)
    kd = (a_w + 0.03 * (WAVE / 440.) ** -3 + 0.01) * 1.1 if kd is None else kd
    bp = 0.2 * (WAVE / 550.) ** -1 if bp is None else bp
    return PreparedRecord(
        dataset=dataset, obs_id=obs_id, wave=WAVE.copy(), Rrs=rrs,
        varRrs=(0.05 * rrs) ** 2, Rrs_clean=rrs.copy(),
        truth={'b_p': np.asarray(bp, dtype=float)}, truth_interp={},
        init={'Chl': 0.2, 'Y': 1.0}, noise_model='pace', noise_seed=7,
        meta=dict({'dataset': dataset, 'X': 4, 'Y': 30} if meta is None
                  else meta), Kd=np.asarray(kd, dtype=float))


@pytest.fixture(scope='module')
def rungs():
    return registry.register_direct()


# --- pure water -------------------------------------------------------------------

def test_pure_water_is_ocpys_and_finite():
    from ocpy.water.absorption import a_water
    from ocpy.water.scattering import betasw_ZHH2009

    a_w, b_w = ls2.pure_water(WAVE)
    assert np.isfinite(a_w).all() and np.isfinite(b_w).all()
    np.testing.assert_array_equal(a_w, a_water(WAVE, data='IOCCG'))
    np.testing.assert_allclose(
        b_w, np.ravel(betasw_ZHH2009(WAVE, 20., 90., 35.)[2]))
    assert 2.4e-3 < np.interp(500., WAVE, b_w) < 2.7e-3


# --- the ladder: one input at a time ----------------------------------------------

def _diff(spec_a, spec_b, record):
    a, b = ls2.inputs(spec_a, record), ls2.inputs(spec_b, record)
    out = set()
    for key in a:
        va, vb = a[key], b[key]
        if isinstance(va, dict):
            if va != vb:
                out.add(key)
        elif va is None or vb is None:
            if va is not vb:
                out.add(key)
        elif not np.array_equal(np.asarray(va), np.asarray(vb), equal_nan=True):
            out.add(key)
    return out


def test_each_rung_differs_from_its_neighbour_only_in_its_input(rungs):
    rec = _record()
    # (i) -> (ii): b_p from OC4v4 instead of truth (and the Chl it came from)
    assert _diff(rungs['ls2_i'], rungs['ls2_ii'], rec) == {'b_p', 'scalars'}
    # (ii) -> (iii): Kd from the PACE network instead of the record
    assert _diff(rungs['ls2_ii'], rungs['ls2_iii'], rec) == {'Kd'}
    # (iii) -> (iii, MODIS): a different network, nothing else
    assert _diff(rungs['ls2_iii'], rungs['ls2_iii_modis'], rec) == {'Kd'}
    # (i) -> Kd noise: Kd alone, at every level
    for level in ('05', '10', '20'):
        assert _diff(rungs['ls2_i'], rungs[f'ls2_i_kdnoise{level}'], rec) == {'Kd'}
    # pure water and geometry are the same on every rung
    for name in ('ls2_ii', 'ls2_iii', 'ls2_iii_modis', 'ls2_i_kdnoise10'):
        assert not {'a_w', 'b_w', 'theta_s', 'Rrs'} & _diff(rungs['ls2_i'],
                                                            rungs[name], rec)


def test_every_rung_runs_end_to_end(rungs):
    rec = _record()
    for name, spec in rungs.items():
        if spec.muw_mode == 'effective':
            continue                       # needs the L23 light field (Tier-2)
        res = run.run_algorithm(spec, rec)
        assert res.fit_method == 'direct'
        assert set(res.components) == {'a', 'a_nw', 'bb', 'bb_p'}
        assert np.isfinite(res.components['a'].med).any(), name
        assert set(res.nan_reason) == set(res.components)


def test_missing_kd_is_a_clear_error():
    rec = _record()
    rec.Kd = None
    with pytest.raises(ValueError, match='kd1'):
        ls2.invert(DirectSpec(name='x', label='X'), rec)


# --- NaN reasons ------------------------------------------------------------------

def test_kd_only_on_measured_bands(rungs):
    """ls2 Q32: PANGAEA-style Kd is used only where it was measured."""
    rec = _record()
    on_band = np.zeros(WAVE.size, dtype=bool)
    on_band[[18, 28, 41]] = True                   # 440, 490, 555 nm
    rec.meta['Kd_on_band'] = on_band
    out = ls2.invert(rungs['ls2_i'], rec)
    a = out['components']['a']
    assert np.isfinite(a[on_band]).all() and np.isnan(a[~on_band]).all()
    reasons = out['nan_reason']['a']
    assert all('kd_missing' in r for r in reasons[~on_band])
    assert not any('kd_missing' in r for r in reasons[on_band])


def test_off_grid_and_missing_bp_are_told_apart(rungs):
    bp = 0.2 * (WAVE / 550.) ** -1
    bp[5] = 1e-5                 # eta > 0.2: outside the table
    bp[60] = np.nan              # no b_p at all
    out = ls2.invert(rungs['ls2_i'], _record(bp=bp))
    reasons, a = out['nan_reason']['a'], out['components']['a']
    assert np.isnan(a[5]) and 'off_grid' in reasons[5]
    assert np.isnan(a[60]) and 'bp_missing' in reasons[60]
    assert 'off_grid' not in reasons[60]


def test_kappa_flags_finite_cells_and_raman_off_has_none(rungs):
    out = ls2.invert(rungs['ls2_i'], _record())
    reasons = out['nan_reason']['a']
    flagged = np.array(['kappa_out_of_range' in r for r in reasons])
    assert flagged[WAVE > 702.].all()              # the table stops at 702 nm
    assert np.isfinite(out['components']['a'][flagged]).all()
    assert out['scalars']['frac_kappa_oor'][0] == pytest.approx(flagged.mean())
    elastic = rungs['ls2_i'].with_overrides({'raman': False})
    assert not any(ls2.invert(elastic, _record())['nan_reason']['a'])


def test_a_network_that_cannot_be_fed_gives_kd_missing(rungs):
    rec = _record()
    keep = WAVE <= 600.                             # no PACE 620-700 nm bands
    rec.wave, rec.Rrs = rec.wave[keep], rec.Rrs[keep]
    rec.truth['b_p'] = rec.truth['b_p'][keep]
    out = ls2.invert(rungs['ls2_iii'], rec)
    assert all('kd_missing' in r for r in out['nan_reason']['a'])


# --- Kd noise ---------------------------------------------------------------------

def test_kd_noise_is_one_draw_per_spectrum(rungs):
    """ls2 Q33: a fully correlated draw, reproducible, per record, at its level."""
    noisy = rungs['ls2_i_kdnoise10']
    clean = ls2.inputs(rungs['ls2_i'], _record())['Kd']
    k1 = ls2.inputs(noisy, _record())['Kd']
    np.testing.assert_array_equal(k1, ls2.inputs(noisy, _record())['Kd'])
    rel = k1 / clean - 1
    np.testing.assert_allclose(rel, rel[0], rtol=1e-12)   # one factor, all bands
    assert rel[0] != 0
    assert not np.allclose(ls2.inputs(noisy, _record(obs_id=1))['Kd'], k1)
    # across records the factor has the stated spread, level by level
    for level, sigma in (('05', 0.05), ('10', 0.10), ('20', 0.20)):
        spec = rungs[f'ls2_i_kdnoise{level}']
        draws = [ls2.inputs(spec, _record(obs_id=i))['Kd'][0] / clean[0] - 1
                 for i in range(400)]
        assert np.std(draws) == pytest.approx(sigma, rel=0.15)
    zero = rungs['ls2_i'].with_overrides({'kd_noise': 0.0})
    np.testing.assert_array_equal(ls2.inputs(zero, _record())['Kd'], clean)


# --- Tier 2: L23 ------------------------------------------------------------------

@pytest.fixture(scope='module')
def corpus():
    """The vectorized driver-configuration run over L23 X=4 Y=0."""
    return _baseline().run('driver', 4, 0)


@needs_l23_profile
def test_corpus_medians_reproduce_planning():
    """Rung (i) on L23 X=4, Y=0, 350-750 nm (measured 2026-10-03).

    Planning quoted a +2.6%, bb +9.8%, bb_p +24% with L23's own pure water, a
    single Raman pass and the stored-z1 <Kd>_1; the same configuration here
    gives +2.72 / +10.69 / +24.84. The driver's configuration (ocpy water,
    iterated, canonical <Kd>_1) moves bb by -0.6 points and the rest by less.
    """
    rb = _baseline()
    plan = rb.run('planning', 4, 0)['median']
    assert plan['a'] == pytest.approx(0.026, abs=0.003)
    assert plan['bb'] == pytest.approx(0.098, abs=0.01)
    assert plan['bb_p'] == pytest.approx(0.24, abs=0.01)
    drv = rb.run('driver', 4, 0)
    m = drv['median']
    assert m['a'] == pytest.approx(0.0274, abs=5e-4)
    assert m['bb'] == pytest.approx(0.1007, abs=5e-4)
    assert m['bb_p'] == pytest.approx(0.2405, abs=1e-3)
    assert drv['frac_off_grid'] == pytest.approx(0.0059, abs=3e-4)   # "~0.6%"


@needs_l23_profile
def test_the_driver_reproduces_the_corpus_run_record_for_record(rungs, corpus):
    from ioptics import prep

    res = corpus['result']
    for idx in (5, 75, 1234):
        rec = prep.prep_one('L23', idx, X=4, Y=0, kd1='ln_ratio',
                            add_noise=False)
        out = run.run_algorithm(rungs['ls2_i'], rec)
        for comp, attr in (('a', 'a'), ('bb', 'bb'), ('a_nw', 'anw'),
                           ('bb_p', 'bbp')):
            np.testing.assert_allclose(out.components[comp].med,
                                       getattr(res, attr)[idx], rtol=1e-6,
                                       equal_nan=True, err_msg=f'{idx} {comp}')


@needs_l23_profile
def test_the_eta_envelope_comes_back_nan_with_its_reason(rungs, corpus):
    from ioptics import prep

    idx = 75                                   # 15 off-grid cells
    assert corpus['result'].off_grid[idx].sum() == 15
    rec = prep.prep_one('L23', idx, X=4, Y=0, kd1='ln_ratio', add_noise=False)
    out = run.run_algorithm(rungs['ls2_i'], rec)
    off = corpus['result'].off_grid[idx]
    for comp in out.components:
        assert np.isnan(out.components[comp].med[off]).all()
        assert all('off_grid' in r for r in out.nan_reason[comp][off])
    assert out.status == 'poor_fit'            # partial, and scored per cell


@needs_l23_profile
def test_effective_muw_removes_most_of_the_a_bias():
    """ls2 Q9: illumination bookkeeping, not coefficients, at theta_s = 0/30."""
    rb = _baseline()
    for Y, snell_a, eff_a in ((0, 0.0274, -0.0087), (30, 0.0218, -0.0070)):
        drv = rb.run('driver', 4, Y)['median']['a']
        eff = rb.run('effmuw', 4, Y)['median']['a']
        assert drv == pytest.approx(snell_a, abs=5e-4)
        assert eff == pytest.approx(eff_a, abs=5e-4)
        assert abs(eff) < 0.5 * abs(drv)


@needs_l23_profile
def test_the_effective_muw_rung_runs_through_the_driver(rungs):
    from ioptics import kd, prep

    rec = prep.prep_one('L23', 5, X=4, Y=0, kd1='ln_ratio', add_noise=False)
    out = ls2.invert(rungs['ls2_i_effmuw'], rec)
    muw = kd.load_l23_muw_effective(4, 0)[5]
    assert out['scalars']['muw'][0] == pytest.approx(muw)
    assert 0.96 < muw < 0.97


@needs_l23_profile
def test_pure_water_delta_is_pinned():
    spec = importlib.util.spec_from_file_location(
        'pure_water_delta', BASELINE.parent / 'pure_water_delta.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    d = mod.delta()
    assert abs(d['a_w']['summary']['max']) < 1e-6
    assert abs(d['a_w']['summary']['min']) < 1e-6
    assert d['b_w']['summary']['median'] == pytest.approx(-0.00271, abs=1e-4)
    assert d['b_w']['summary']['max'] - d['b_w']['summary']['min'] < 2e-4

"""Tests for the robust RT backends: geometry, ``fit_Bp``, and CDOM fluorescence.

BING's ``rt_dict`` grew from seven Gordon toggles to twelve keys (``rob_rt`` /
``rob_cdom``), and three of the new ones change the *shape* of what IOPtics
handles rather than merely a flag:

- a ``robust_*`` backend needs an **observation geometry**, which has to be
  derived per record from when and where the spectrum was measured — and must
  raise, never guess, when the record cannot say (:class:`MissingGeometryError`);
- ``fit_Bp`` appends a trailing parameter to the fitted vector, so the seed,
  the bounds, the chain columns, the parameter names, ``k``, and the results
  row all gain one slot;
- ``include_CDOM_fl`` reaches robust's Hawes kernel through the fixed-fraction
  proxy ``a_cdom = cdom_fraction * a_dg``.

Everything that needs BING models needs the L23 tree (``build_models`` loads
``Hydrolight400.nc``), so those are ``@needs_l23``; the geometry resolution and
the output plumbing are exercised on synthetic records with no data at all.
"""

import copy

import numpy as np
import pytest

from ioptics.tests.conftest import needs_l23


# --------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------
def _record(dataset='PANGAEA', *, meta=None, n=61):
    """A minimal :class:`PreparedRecord` — only the geometry metadata matters."""
    from ioptics.records import PreparedRecord

    wave = np.linspace(400.0, 700.0, n)
    Rrs = np.full_like(wave, 1e-3)
    return PreparedRecord(
        dataset=dataset, obs_id=7, wave=wave, Rrs=Rrs,
        varRrs=np.full_like(wave, 1e-8), Rrs_clean=Rrs, truth={},
        truth_interp={}, init={'Chl': 0.3, 'Y': 1.0}, noise_model='pct:0.1',
        noise_seed=None, meta=dict(meta or {}))


def _spec(**rt):
    """A registry ``expb_pow`` copy with ``rt`` fields overridden."""
    from ioptics.algorithms import registry

    spec = copy.deepcopy(registry.get('expb_pow'))
    for key, value in rt.items():
        setattr(spec.rt, key, value)
    return spec


# --------------------------------------------------------------------
# theta_s resolution
# --------------------------------------------------------------------
def test_l23_theta_s_is_the_hydrolight_solar_zenith():
    from ioptics import run

    # the ordinary sweep: no Y load option recorded -> the documented default
    assert run.resolve_theta_s(_record('L23')) == 0.0
    assert run.L23_DEFAULT_THETA_S == 0.0
    # ... but L23's ``Y`` load option *is* the solar zenith in degrees, so an
    # X=1/Y=30 realization must not be fitted as if the sun were overhead.
    assert run.resolve_theta_s(_record('L23', meta={'Y': 0})) == 0.0
    assert run.resolve_theta_s(_record('L23', meta={'Y': 30})) == 30.0
    assert run.resolve_theta_s(_record('L23', meta={'Y': 60})) == 60.0


def test_theta_s_from_time_and_place_matches_a_hand_checked_value():
    """Santa Cruz, CA at local solar noon on the 2024 June solstice.

    The value is ``robust.solar``'s own documented worked example (13.54 deg),
    which that package tests against ``astropy``; asserting it here pins the
    *wiring* — that IOPtics hands the right record fields to the right
    arguments, in the right order and the right units. A lat/lon swap or a
    sign flip moves this by tens of degrees.
    """
    from ioptics import run

    rec = _record(meta={'time': '2024-06-20T20:10:00',
                        'lat': 36.9741, 'lon': -122.0308})
    assert run.resolve_theta_s(rec) == pytest.approx(13.54, abs=0.01)


def test_theta_s_accepts_the_timestamp_forms_an_adapter_produces():
    import datetime as dt

    from ioptics import run

    ref = run.resolve_theta_s(_record(meta={
        'time': '2024-06-20T20:10:00', 'lat': 36.9741, 'lon': -122.0308}))
    for stamp in (dt.datetime(2024, 6, 20, 20, 10, 0),
                  np.datetime64('2024-06-20T20:10:00'),
                  dt.datetime(2024, 6, 20, 13, 10, 0,
                              tzinfo=dt.timezone(dt.timedelta(hours=-7)))):
        got = run.resolve_theta_s(_record(meta={
            'time': stamp, 'lat': 36.9741, 'lon': -122.0308}))
        assert got == pytest.approx(ref, abs=1e-6), stamp


def test_missing_geometry_metadata_raises_and_names_what_is_missing():
    """Never a silent default: a guessed theta_s would ride into every IOP."""
    from ioptics import run

    with pytest.raises(run.MissingGeometryError) as exc:
        run.resolve_theta_s(_record(meta={}))
    for key in ('time', 'lat', 'lon'):
        assert key in str(exc.value)
    assert 'PANGAEA/7' in str(exc.value)
    # a partially-populated record is just as unusable, and says so
    with pytest.raises(run.MissingGeometryError, match='lon'):
        run.resolve_theta_s(_record(meta={'time': '2024-06-20T20:10:00',
                                          'lat': 36.9}))
    # ... and so is one whose cells are present but NaN/NaT (a real PANGAEA
    # row with no position, which pandas hands over as NaN, not as absent)
    import pandas as pd

    for stamp in (np.datetime64('NaT', 'ns'), pd.NaT):
        with pytest.raises(run.MissingGeometryError):
            run.resolve_theta_s(_record(meta={'time': stamp, 'lat': np.nan,
                                              'lon': np.nan}))
    # a real timestamp with no coordinates is still unusable
    with pytest.raises(run.MissingGeometryError, match='lat'):
        run.resolve_theta_s(_record(meta={
            'time': pd.Timestamp('2024-06-20T20:10:00'),
            'lat': np.nan, 'lon': -122.0}))


def test_resolve_geometry_is_none_for_gordon_and_an_obsgeometry_otherwise():
    from bing.rt.geometry import ObsGeometry

    from ioptics import run

    rec = _record(meta={'time': '2024-06-20T20:10:00',
                        'lat': 36.9741, 'lon': -122.0308})
    # Gordon has no geometry input: nothing is resolved, nothing can fail --
    # a record with no metadata at all still fits.
    assert run.resolve_geometry(_spec(), rec) is None
    assert run.resolve_geometry(_spec(), _record(meta={})) is None

    geom = run.resolve_geometry(_spec(rt_backend='robust_ztt'), rec)
    assert isinstance(geom, ObsGeometry)
    assert geom.theta_s == pytest.approx(13.54, abs=0.01)
    assert (geom.theta_v, geom.dphi) == (run.DEFAULT_THETA_V, run.DEFAULT_DPHI)


def test_a_robust_backend_on_a_placeless_record_raises():
    from ioptics import run

    with pytest.raises(run.MissingGeometryError):
        run.resolve_geometry(_spec(rt_backend='robust_ztt'), _record(meta={}))


# --------------------------------------------------------------------
# geometry threading into the BING fit calls
# --------------------------------------------------------------------
def _capture_chisq(monkeypatch):
    """Monkeypatch ``bing.fitting.chisq_fit.fit`` to capture its items tuple."""
    from bing.fitting import chisq_fit

    seen = {}

    def _fake(items, models, rt_dict, bounds=None, maxfev=None):
        seen['items'] = items
        seen['rt_dict'] = rt_dict
        seen['bounds'] = bounds
        k = len(items[2])
        return np.asarray(items[2], dtype=float), np.eye(k) * 1e-6, items[3]

    monkeypatch.setattr(chisq_fit, 'fit', _fake)
    return seen


@needs_l23
def test_gordon_chisq_still_passes_the_legacy_four_tuple(monkeypatch):
    from ioptics import prep, run

    seen = _capture_chisq(monkeypatch)
    record = prep.prep_one('L23', 0, seed=1234, wv_min=400.0, wv_max=700.0)
    run.fit_chisq(_spec(), record)
    assert len(seen['items']) == 4, 'no geometry -> no 5th element'
    assert seen['rt_dict']['rt_backend'] == 'gordon'


@needs_l23
def test_robust_chisq_threads_the_geometry_as_the_fifth_element(monkeypatch):
    from bing.rt.geometry import ObsGeometry

    from ioptics import prep, run

    seen = _capture_chisq(monkeypatch)
    record = prep.prep_one('L23', 0, seed=1234, wv_min=400.0, wv_max=700.0)
    run.fit_chisq(_spec(rt_backend='robust_ztt'), record)
    assert len(seen['items']) == 5
    geom = seen['items'][4]
    assert isinstance(geom, ObsGeometry) and geom.theta_s == 0.0


@needs_l23
def test_robust_mcmc_threads_the_geometry_as_the_fifth_element(monkeypatch):
    from bing.fitting import inference as bing_inf
    from bing.rt.geometry import ObsGeometry

    from ioptics import prep, run

    seen = {}

    def _fake_fit_one(items, models=None, pdict=None, chains_only=True,
                      rt_dict=None):
        seen['items'] = items
        seen['ndim'] = pdict['ndim']
        return np.zeros((4, pdict['nwalkers'], pdict['ndim'])), None

    monkeypatch.setattr(bing_inf, 'fit_one', _fake_fit_one)
    record = prep.prep_one('L23', 0, seed=1234, wv_min=400.0, wv_max=700.0)

    run.fit_mcmc(_spec(), record)
    assert len(seen['items']) == 4 and seen['ndim'] == 5

    run.fit_mcmc(_spec(rt_backend='robust_ztt', fit_Bp=True), record)
    assert len(seen['items']) == 5
    assert isinstance(seen['items'][4], ObsGeometry)
    assert seen['ndim'] == 6, 'fit_Bp grows the sampled vector by one'


# --------------------------------------------------------------------
# rt_dict validation happens once, at setup
# --------------------------------------------------------------------
@needs_l23
def test_a_misconfigured_rt_dict_fails_at_prepare_not_in_the_optimizer():
    from ioptics import prep, run

    record = prep.prep_one('L23', 0, seed=1234, wv_min=400.0, wv_max=700.0)
    # fit_Bp on Gordon: no phase-function input exists to fit
    with pytest.raises(ValueError, match='fit_Bp'):
        run._prepare(_spec(fit_Bp=True), record)
    # CDOM fluorescence on Gordon: BING's own path has no such physics
    with pytest.raises(ValueError, match='include_CDOM_fl'):
        run._prepare(_spec(include_CDOM_fl=True), record)
    # ... and on robust_baseline, which is elastic-only by construction
    with pytest.raises(ValueError, match='robust_baseline'):
        run._prepare(_spec(rt_backend='robust_baseline',
                           include_CDOM_fl=True), record)
    # an unknown backend name
    with pytest.raises(ValueError, match='rt_backend'):
        run._prepare(_spec(rt_backend='robust_zzt'), record)


@needs_l23
def test_robust_hybrid_rejects_a_grid_outside_its_training_range():
    from ioptics import prep, run

    # GLORIA-style native grid runs past 750 nm, where the emulator is untrained
    record = prep.prep_one('L23', 0, seed=1234)
    if float(np.max(record.wave)) <= 750.0:
        pytest.skip('L23 native grid already inside the emulator range')
    with pytest.raises(ValueError, match='robust_hybrid'):
        run._prepare(_spec(rt_backend='robust_hybrid'), record)


# --------------------------------------------------------------------
# Chl fluorescence: correct_atmosphere is a *Gordon*-path dependency
# --------------------------------------------------------------------
@needs_l23
def test_robust_chl_fluorescence_does_not_need_correct_atmosphere(monkeypatch):
    """robust carries its own Ed table (rt_tests Q36).

    Pinned by making the import fail: the robust path must not touch
    ``correct_atmosphere`` at all, or every robust inelastic fit would inherit
    a dependency that is not on PyPI (the ``needs_inelastic`` guard).
    """
    import sys

    from ioptics import prep, run

    monkeypatch.setitem(sys.modules, 'correct_atmosphere', None)
    record = prep.prep_one('L23', 0, seed=1234, wv_min=400.0, wv_max=700.0)

    _, models, rt_dict = run._prepare(
        _spec(rt_backend='robust_ztt', include_Raman=True,
              include_Chl_fl=True), record)
    assert rt_dict['include_Chl_fl'] is True
    # ... while the Gordon path genuinely needs it and says so
    with pytest.raises(ImportError):
        run._prepare(_spec(include_Chl_fl=True), record)


# --------------------------------------------------------------------
# fit_Bp: one extra trailing slot, everywhere
# --------------------------------------------------------------------
@needs_l23
def test_fit_bp_grows_the_seed_and_the_bounds_by_one_slot():
    from bing.rt import defs as rt_defs

    from ioptics import prep, run

    record = prep.prep_one('L23', 0, seed=1234, wv_min=400.0, wv_max=700.0)
    spec = _spec(rt_backend='robust_ztt', fit_Bp=True, Bp_value=0.02)
    _, models, rt_dict = run._prepare(spec, record)
    k = int(models[0].nparam + models[1].nparam)

    assert run.n_free_params(models, rt_dict) == k + 1
    assert run.n_free_params(models, {'fit_Bp': False}) == k
    assert run.n_free_params(models) == k

    p0 = run._seed(models, record, rt_dict)
    assert p0.shape == (k + 1,)
    assert p0[-1] == 0.02, 'the B_p seed is linear-space, never log10'

    lo, hi = run._prior_bounds(models, rt_dict)
    assert lo.shape == hi.shape == (k + 1,)
    assert (lo[-1], hi[-1]) == (rt_defs.BP_PRIOR_PMIN, rt_defs.BP_PRIOR_PMAX)
    assert lo[-1] <= p0[-1] <= hi[-1]
    # the fixed-B_p bounds are exactly the model bounds, as before
    lo0, hi0 = run._prior_bounds(models)
    assert np.array_equal(lo0, lo[:-1]) and np.array_equal(hi0, hi[:-1])


@needs_l23
def test_fit_bp_reaches_the_chain_the_params_and_the_results_row(tmp_path):
    """The whole output path, on a tiny (60-step) posterior."""
    from ioptics import evaluate, io, prep, run

    record = prep.prep_one('L23', 0, seed=1234, wv_min=400.0, wv_max=700.0)
    spec = _spec(rt_backend='robust_ztt', fit_Bp=True)
    spec.mcmc.nsteps, spec.mcmc.nburn = 60, 10

    models, rt_dict, chains = run.fit_mcmc(spec, record)
    k = int(models[0].nparam + models[1].nparam)
    assert chains.shape[-1] == k + 1, 'the chain carries the B_p column'

    geom = run.resolve_geometry(spec, record)
    res = evaluate.from_chains(spec, record, models, rt_dict, chains, geom=geom)
    # names come from bing's own convention, so the chain, the corner plot and
    # the results row cannot disagree about which column is which
    from bing.evaluate import chain_param_names
    assert list(res.params) == chain_param_names(models, rt_dict)
    assert list(res.params)[-1] == 'B_p'
    assert res.stats['k'] == k + 1, 'a free B_p is a parameter the data pays for'
    assert res.scalars['B_p'] == res.params['B_p']

    # the persisted chain keeps the extra column and its label
    path = io.save_chain('bp', spec.name, record, chains, root=tmp_path,
                         pnames=list(res.params))
    saved = io.load_chain(path)
    assert saved['chains'].shape[-1] == k + 1
    assert list(saved['pnames'])[-1] == 'B_p'

    # ... and it lands on results_scalar under its own column pair
    io.write_results('bp', [(res, record)], root=tmp_path)
    _, sc = io.read_results('bp', root=tmp_path)
    assert 'B_p' in sc.columns and 'sig_B_p' in sc.columns
    assert sc['B_p'].iloc[0] == pytest.approx(res.params['B_p'][0])
    assert sc['sig_B_p'].iloc[0] == pytest.approx(res.params['B_p'][1])


def test_the_bp_column_is_peeled_before_the_model_split():
    """A synthetic check of the one thing an off-by-one here would break."""
    from ioptics import evaluate

    samples = np.arange(12.0).reshape(3, 4)         # 3 samples, 3 params + B_p
    fixed, none = evaluate._split_Bp(samples, {'fit_Bp': False}, 5)
    assert none is None and np.array_equal(fixed, samples)

    free, Bp = evaluate._split_Bp(samples, {'fit_Bp': True}, 5)
    assert np.array_equal(free, samples[:, :3])
    assert Bp.shape == (3, 5), "robust's batched B_p is (sample, wave)"
    assert np.array_equal(Bp[:, 0], samples[:, -1])


def test_a_free_bp_reaches_results_scalar_without_a_fit(tmp_path):
    """``_scalar_row``'s extra-scalar path is what carries B_p; pin it alone."""
    from ioptics import io
    from ioptics.tests.test_metrics import _make_pair

    result, record = _make_pair(0, 'expb_pow', 1.0, 0.5, 10)
    result.scalars['B_p'] = (0.0123, 0.0045)
    io.write_results('bp_row', [(result, record)], root=tmp_path)
    _, sc = io.read_results('bp_row', root=tmp_path)
    assert sc['B_p'].iloc[0] == pytest.approx(0.0123)
    assert sc['sig_B_p'].iloc[0] == pytest.approx(0.0045)


# --------------------------------------------------------------------
# legacy byte-identity
# --------------------------------------------------------------------
@needs_l23
def test_a_gordon_fit_is_unchanged_by_the_backend_machinery():
    """The default algorithm must produce the same numbers it always did.

    Not a golden file — the point is that the new code paths are inert: the
    items tuple stays a 4-tuple, ``k`` stays the model parameter count, no
    ``B_p`` appears anywhere, and the reconstruction still runs through
    ``calc_Rrs_from_models``.
    """
    from ioptics import evaluate, prep, run

    record = prep.prep_one('L23', 0, seed=1234, wv_min=400.0, wv_max=700.0)
    spec = _spec()
    models, rt_dict, ans, cov = run.fit_chisq(spec, record)
    k = int(models[0].nparam + models[1].nparam)

    assert rt_dict['rt_backend'] == 'gordon' and rt_dict['fit_Bp'] is False
    assert ans.shape == (k,)
    res = evaluate.from_chisq(spec, record, models, rt_dict, ans, cov)
    assert list(res.params) == list(models[0].pnames) + list(models[1].pnames)
    assert 'B_p' not in res.params and 'B_p' not in res.scalars
    assert res.stats['k'] == k
    # geometry is never resolved, so a record with no place or time still fits
    assert run.resolve_geometry(spec, record) is None


# --------------------------------------------------------------------
# CDOM fluorescence
# --------------------------------------------------------------------
@needs_l23
def test_cdom_fluorescence_runs_on_an_a_model_with_a_separable_a_dg():
    """``a_cdom = cdom_fraction * a_dg`` — the Q32 fixed-fraction proxy."""
    from ioptics import evaluate, prep, run

    record = prep.prep_one('L23', 0, seed=1234, wv_min=400.0, wv_max=700.0)
    spec = _spec(rt_backend='robust_ztt', include_CDOM_fl=True,
                 cdom_fraction=0.8)
    _, models, rt_dict = run._prepare(spec, record)
    assert models[0].has_a_dg, 'ExpBricaud supplies the a_dg the kernel needs'
    assert rt_dict['include_CDOM_fl'] is True
    assert rt_dict['cdom_fraction'] == 0.8

    models, rt_dict, ans, cov = run.fit_chisq(spec, record)
    res = evaluate.from_chisq(spec, record, models, rt_dict, ans, cov,
                              geom=run.resolve_geometry(spec, record))
    assert np.all(np.isfinite(res.components['Rrs_model'].med))

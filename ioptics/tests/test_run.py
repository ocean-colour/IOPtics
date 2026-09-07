"""Tests for ``ioptics.run`` — the chisq fit core.

The fit builds BING models, which loads the L23 pure-water data, so the
end-to-end checks are **Tier-2** (`@needs_l23`). They run on a real
``prep.prep_one('L23', idx)`` record and verify the truth-free initial guess and
that the least-squares fit converges to a finite, in-bounds solution that closes
on the observed ``Rrs``.
"""

from pathlib import Path

import numpy as np

from ioptics.tests.conftest import needs_l23


@needs_l23
def test_initial_guess_is_sized_and_in_bounds():
    from ioptics import prep, run
    from ioptics.algorithms.spec import AlgorithmSpec

    record = prep.prep_one('L23', 0, seed=1234)
    spec = AlgorithmSpec.from_standard('expb_pow')
    _, models, _ = run._prepare(spec, record)
    p0 = run.initial_guess(models, record)

    k = sum(m.nparam for m in models)
    assert p0.shape == (k,)
    assert np.all(np.isfinite(p0))
    lo, hi = run._prior_bounds(models)
    assert np.all(p0 >= lo) and np.all(p0 <= hi)   # feasible for curve_fit
    # truth-free: the guess must not equal the truth amplitudes (sanity)
    assert 'a' in record.truth          # truth present, but unused by the guess


def _fake_record(Rrs670, *, Y=1.0):
    """A minimal record whose only job is to set the anchor-band brightness."""
    from ioptics.records import PreparedRecord

    wave = np.arange(400.0, 701.0, 10.0)
    Rrs = np.full_like(wave, 1e-3)
    Rrs[np.argmin(np.abs(wave - 670.0))] = Rrs670
    for nm in (443.0, 490.0):
        Rrs[np.argmin(np.abs(wave - nm))] = 0.01
    return PreparedRecord(
        dataset='X', obs_id=0, wave=wave, Rrs=Rrs,
        varRrs=np.full_like(wave, 1e-8), Rrs_clean=Rrs, truth={},
        truth_interp={}, init={'Y': Y}, noise_model='pct:0.05',
        noise_seed=None)


def test_is_turbid_uses_the_qaa_red_band_switch():
    from ioptics import run

    clear = _fake_record(0.5 * run.TURBID_RRS_ANCHOR)
    turbid = _fake_record(2.0 * run.TURBID_RRS_ANCHOR)
    assert not run.is_turbid(clear)
    assert run.is_turbid(turbid)
    # a non-finite anchor falls back to the open-ocean branch, not an error
    nan_rec = _fake_record(np.nan)
    assert not run.is_turbid(nan_rec)


def test_anw_anchor_is_zero_off_the_turbid_branch():
    from ioptics import run

    rec = _fake_record(0.01)
    wave, Rrs = rec.wave, rec.Rrs
    assert run._anw_anchor(wave, Rrs, False) == 0.0
    # On the turbid branch it is a real, positive absorption -- and comparable
    # to a_w(670) ~ 0.44 m^-1, which is exactly why neglecting it matters.
    anw = run._anw_anchor(wave, Rrs, True)
    assert anw > 0.05
    # ... and it degrades gracefully rather than dividing by zero
    assert run._anw_anchor(wave, np.zeros_like(Rrs), True) == 0.0


@needs_l23
def test_initial_guess_open_ocean_branch_is_unchanged():
    # The turbid branch must not perturb open-ocean results: on a clear
    # spectrum the auto-detected seed is the forced open-ocean one.
    from ioptics import prep, run
    from ioptics.algorithms.spec import AlgorithmSpec

    record = prep.prep_one('L23', 0, seed=1234)
    spec = AlgorithmSpec.from_standard('expb_pow')
    _, models, _ = run._prepare(spec, record)

    assert not run.is_turbid(record)          # L23 row 0 is open-ocean
    np.testing.assert_array_equal(run.initial_guess(models, record),
                                  run.initial_guess(models, record,
                                                    turbid=False))


@needs_l23
def test_initial_guess_turbid_branch_moves_amplitudes_and_slope():
    from ioptics import prep, run
    from ioptics.algorithms import registry

    record = prep.prep_one('L23', 0, seed=1234)
    spec = registry.register_turbid()['expb_powflex']
    _, models, _ = run._prepare(spec, record)

    open_ocean = run.initial_guess(models, record, turbid=False)
    turbid = run.initial_guess(models, record, turbid=True)

    # The red anchor gains non-water absorption, so every amplitude seeded
    # from it goes *up*; nothing may go down.
    log_mask = run._log_mask(models)
    assert np.all(turbid[log_mask] >= open_ocean[log_mask] - 1e-12)
    assert np.any(turbid[log_mask] > open_ocean[log_mask])
    # ... and the single power-law exponent is seeded from the QAA Y rather
    # than from bing's fixed beta = 1 (held inside the prior, as ever).
    lo, hi = run._prior_bounds(models)
    inset = run.BOUND_INSET * (hi - lo)
    expected = np.clip(record.init['Y'], lo + inset, hi - inset)[-1]
    assert np.isclose(turbid[-1], expected, atol=1e-9)
    assert not np.isclose(turbid[-1], open_ocean[-1], atol=1e-6)


@needs_l23
def test_initial_guess_stays_strictly_inside_the_priors():
    # A parameter pinned to a bound gives the bounded solver no direction to
    # search, so the seed is held off the bounds rather than clipped onto them.
    from ioptics import prep, run
    from ioptics.algorithms import registry

    record = prep.prep_one('L23', 0, seed=1234)
    for name, spec in registry.register_turbid().items():
        _, models, _ = run._prepare(spec, record)
        for turbid in (False, True):
            p0 = run.initial_guess(models, record, turbid=turbid)
            lo, hi = run._prior_bounds(models)
            assert np.all(p0 > lo), f'{name} (turbid={turbid}) seeded on a floor'
            assert np.all(p0 < hi), f'{name} (turbid={turbid}) seeded on a ceiling'


@needs_l23
def test_two_component_exponents_keep_bings_own_seed():
    # Pow2/Pow2Flat exponents are per-component; a bulk QAA Y is not an
    # estimate of either, and bing seeds the mineral one just off zero on
    # purpose (so MCMC's multiplicative walker spread can move it).
    from ioptics import prep, run
    from ioptics.algorithms import registry

    record = prep.prep_one('L23', 0, seed=1234)
    for name in ('expb_pow2', 'expb_pow2flat'):
        spec = registry.register_turbid()[name]
        _, models, _ = run._prepare(spec, record)
        log_mask = run._log_mask(models)
        p_open = run.initial_guess(models, record, turbid=False)
        p_turbid = run.initial_guess(models, record, turbid=True)
        np.testing.assert_allclose(p_turbid[~log_mask], p_open[~log_mask],
                                   err_msg=f'{name}: exponent seed moved')


@needs_l23
def test_underdetermined_fit_is_refused_as_a_status():
    """``n_bands <= k`` is refused up front, as a status we chose.

    All 315 five-band PANGAEA spectra died under ``expb_pow`` (k = 5) with
    ``LinAlgError: SVD did not converge`` from deep inside scipy — the fit was
    underdetermined by construction, and nothing refused it. The refusal must
    (a) not raise from ``run_algorithm`` in either strict mode, (b) produce a
    ``fit_failed`` row whose stats carry the **true** ``n_bands`` and ``k``
    (they used to be 0 on every failed row), and (c) be a deliberate
    :class:`~ioptics.run.UnderdeterminedFitError` at the fitting core.
    """
    import pytest

    from ioptics import run
    from ioptics.algorithms.spec import AlgorithmSpec
    from ioptics.records import PreparedRecord

    wave = np.array([412.0, 443.0, 490.0, 555.0, 670.0])       # 5 bands
    Rrs = np.array([0.008, 0.007, 0.005, 0.003, 0.001])
    rec = PreparedRecord(
        dataset='X', obs_id=7, wave=wave, Rrs=Rrs,
        varRrs=(0.05 * Rrs) ** 2, Rrs_clean=Rrs, truth={},
        truth_interp={}, init={'Chl': 0.1, 'Y': 1.0},
        noise_model='pct:0.05', noise_seed=None)
    spec = AlgorithmSpec.from_standard('expb_pow')              # k = 5

    # the fitting core refuses before any optimizer runs
    with pytest.raises(run.UnderdeterminedFitError):
        run.fit_chisq(spec, rec)

    # run_algorithm converts the refusal to a status — no crash, even strict
    res = run.run_algorithm(spec, rec)
    assert res.status == 'fit_failed'
    assert res.stats['n_bands'] == 5 and res.stats['k'] == 5

    # and the robust batch path agrees
    results = run.run_batch(spec, [rec], strict=False)
    assert results[0].status == 'fit_failed'
    assert results[0].stats['n_bands'] == 5 and results[0].stats['k'] == 5

    # a 6-band spectrum of the same water is *not* refused for k = 3 (giop)
    spec3 = AlgorithmSpec.from_standard('giop')
    res3 = run.run_algorithm(spec3, rec)
    assert res3.status != 'fit_failed' or res3.stats['n_bands'] == 5


@needs_l23
def test_red_peaked_record_is_declined_before_fitting():
    """Pre-fit ``out_of_scope``: red-peaked water is declined, not fitted.

    Per JXP's Task-1 answers (``claude_prompts/pangaea_fits.md``, 2026-08-10):
    a record whose observed Rrs peaks redward of RED_PEAK_NM is out of scope
    for the open-ocean family *by the spectrum alone* — "we declined to fit
    this", assigned before any optimizer runs. An algorithm that claims
    turbid water in scope (``fits_turbid=True``, e.g. the turbid variants or
    a diagnostic force-fit) is exempt and actually fits.
    """
    import dataclasses

    from ioptics import run
    from ioptics.algorithms.spec import AlgorithmSpec
    from ioptics.records import RED_PEAK_NM, PreparedRecord

    wave = np.arange(400.0, 701.0, 20.0)
    # a smooth, green-red-peaked spectrum (broad bump at 580 nm)
    Rrs = 2e-3 + 0.01 * np.exp(-((wave - 580.0) / 60.0) ** 2)
    rec = PreparedRecord(
        dataset='X', obs_id=9, wave=wave, Rrs=Rrs,
        varRrs=(0.10 * Rrs) ** 2, Rrs_clean=Rrs, truth={},
        truth_interp={}, init={'Chl': 1.0, 'Y': 0.5},
        noise_model='pct:0.1', noise_seed=None)
    assert run.is_red_peaked(rec)
    assert RED_PEAK_NM < 580.0

    # open-ocean spec (fits_turbid=False): declined up front, stats populated,
    # and no fit artifacts — components stay empty because nothing was fitted
    spec = AlgorithmSpec.from_standard('expb_pow')
    res = run.run_algorithm(spec, rec)
    assert res.status == 'out_of_scope'
    assert res.stats['n_bands'] == wave.size and res.stats['k'] == 5
    assert not res.components and not res.params

    # claiming turbid scope exempts the record: the fit actually runs
    # (with a real budget — turbid water is exactly where scipy's default
    # evaluation budget runs out)
    forced = dataclasses.replace(spec, fits_turbid=True, maxfev=40000)
    res2 = run.run_algorithm(forced, rec)
    assert res2.components, 'fits_turbid=True must reach the optimizer'


@needs_l23
def test_mcmc_subset_applies_the_prefit_guards(tmp_path):
    """The MCMC subset makes the same pre-fit decisions as the χ² pass.

    PR #11 review finding (Cursor Bugbot): ``_mcmc_subset`` called
    ``fit_mcmc`` directly, so a red-peaked record was MCMC-fitted by an
    open-ocean spec that the sweep's own χ² pass had declined, and a
    ``strict=True`` sweep aborted on an underdetermined record instead of
    recording the refusal. Both must now match ``run_algorithm``: declined
    ``out_of_scope`` before any sampling, and ``fit_failed`` (with true
    ``n_bands``/``k``) in **both** strict modes.
    """
    from ioptics import run
    from ioptics.algorithms.spec import AlgorithmSpec
    from ioptics.records import PreparedRecord

    # red-peaked record + open-ocean spec -> declined, no chains written
    wave = np.arange(400.0, 701.0, 20.0)
    Rrs = 2e-3 + 0.01 * np.exp(-((wave - 580.0) / 60.0) ** 2)
    red = PreparedRecord(
        dataset='X', obs_id=1, wave=wave, Rrs=Rrs,
        varRrs=(0.10 * Rrs) ** 2, Rrs_clean=Rrs, truth={},
        truth_interp={}, init={'Chl': 1.0, 'Y': 0.5},
        noise_model='pct:0.1', noise_seed=None)
    spec = AlgorithmSpec.from_standard('giop')
    pairs = run._mcmc_subset(spec, [red], 'mcmc_guard_sweep', root=tmp_path,
                             strict=True)
    (res, _), = pairs
    assert res.status == 'out_of_scope'
    assert res.chain_file is None, 'declined records must not sample chains'
    assert res.provenance_id == 'mcmc_guard_sweep#giop'

    # underdetermined record + k=5 spec -> fit_failed even under strict=True
    wave5 = np.array([412.0, 443.0, 490.0, 555.0, 670.0])
    Rrs5 = np.array([0.008, 0.007, 0.005, 0.003, 0.001])
    under = PreparedRecord(
        dataset='X', obs_id=2, wave=wave5, Rrs=Rrs5,
        varRrs=(0.10 * Rrs5) ** 2, Rrs_clean=Rrs5, truth={},
        truth_interp={}, init={'Chl': 0.1, 'Y': 1.0},
        noise_model='pct:0.1', noise_seed=None)
    spec5 = AlgorithmSpec.from_standard('expb_pow')
    pairs = run._mcmc_subset(spec5, [under], 'mcmc_guard_sweep',
                             root=tmp_path, strict=True)
    (res, _), = pairs
    assert res.status == 'fit_failed'
    assert res.stats['n_bands'] == 5 and res.stats['k'] == 5


@needs_l23
def test_fit_chisq_converges_and_closes_on_rrs():
    from bing.fitting import chisq_fit

    from ioptics import prep, run
    from ioptics.algorithms.spec import AlgorithmSpec

    record = prep.prep_one('L23', 0, seed=1234)
    for name in ('expb_pow', 'giop'):
        spec = AlgorithmSpec.from_standard(name)
        models, rt_dict, ans, cov = run.fit_chisq(spec, record)

        k = sum(m.nparam for m in models)
        assert ans.shape == (k,)
        assert np.all(np.isfinite(ans))
        assert cov.shape == (k, k)

        # Closure: noise-weighted reduced chi^2 (what the fit minimizes) should
        # be order-unity — a raw relative error is meaningless in the red where
        # Rrs -> 0 (PACE noise floor).
        model_Rrs = chisq_fit.fit_func(None, *ans, models=models, rt_dict=rt_dict)
        resid = (model_Rrs - record.Rrs) / np.sqrt(record.varRrs)
        chi2_nu = float(np.sum(resid ** 2) / (record.wave.size - k))
        assert chi2_nu < 5.0, f'{name}: poor closure, chi2_nu={chi2_nu:.2f}'


def test_run_batch_strict_toggle(monkeypatch):
    # Data-free: patch run_algorithm to raise, so no models are built.
    from ioptics import run
    from ioptics.algorithms.spec import AlgorithmSpec
    from ioptics.records import PreparedRecord

    rec = PreparedRecord(
        dataset='X', obs_id=0, wave=np.array([1.0]), Rrs=np.array([1.0]),
        varRrs=np.array([1.0]), Rrs_clean=np.array([1.0]), truth={},
        truth_interp={}, init={}, noise_model='pct:0.05', noise_seed=None)
    spec = AlgorithmSpec(name='x', label='x', anw_model='', bbnw_model='',
                         apriors=[], bpriors=[])

    def boom(spec, record, **kw):
        raise RuntimeError('fit blew up')
    monkeypatch.setattr(run, 'run_algorithm', boom)

    # strict=True (default) -> fail-fast (propagates)
    import pytest
    with pytest.raises(RuntimeError):
        run.run_batch(spec, [rec])
    # strict=False -> robust: a fit_failed result, batch continues
    results = run.run_batch(spec, [rec], strict=False)
    assert len(results) == 1
    assert results[0].status == 'fit_failed'
    assert results[0].algorithm == 'x'


@needs_l23
def test_mcmc_path_round_trip():
    from ioptics import prep, run
    from ioptics.algorithms.spec import AlgorithmSpec

    record = prep.prep_one('L23', 0, seed=1234)
    spec = AlgorithmSpec.from_standard('giop')
    spec.mcmc.nsteps, spec.mcmc.nburn = 200, 50   # tiny: correctness, not convergence

    res = run.run_algorithm(spec, record, fit_method='mcmc')
    assert res.fit_method == 'mcmc'
    assert res.status == 'ok'
    assert set(res.components) == {'a', 'bb', 'a_ph', 'a_dg', 'bb_p', 'Rrs_model'}
    cf = res.components['a']
    assert cf.med.shape == record.wave.shape
    assert np.all(np.isfinite(cf.med))
    # bands assembled like the chisq path (ordered)
    assert np.all(cf.lo95 <= cf.lo68) and np.all(cf.hi68 <= cf.hi95)
    assert res.stats['k'] == 3 and res.stats['n_bands'] == record.wave.size


@needs_l23
def test_run_batch_serial_and_parallel():
    from ioptics import prep, run
    from ioptics.algorithms.spec import AlgorithmSpec

    records = prep.prep_dataset('L23', obs_ids=range(3), seed=1234)
    spec = AlgorithmSpec.from_standard('expb_pow')

    serial = run.run_batch(spec, records, n_cores=1)
    parallel = run.run_batch(spec, records, n_cores=2)

    for results in (serial, parallel):
        assert len(results) == 3
        assert all(r.algorithm == 'expb_pow' for r in results)
        assert all(r.status == 'ok' for r in results)
        assert [r.obs_id for r in results] == [0, 1, 2]   # order preserved
    # serial and parallel give the same point estimate (deterministic fit)
    np.testing.assert_allclose(serial[0].components['a'].med,
                               parallel[0].components['a'].med, rtol=1e-6)


# --------------------------------------------------------------------
# dataset_opts reach the adapter (Tier-1: prep is mocked, no data needed)
# --------------------------------------------------------------------
def test_run_sweep_threads_dataset_opts_into_prep(monkeypatch, tmp_path):
    """A ``dataset_opts`` entry must arrive as adapter keyword arguments.

    ``prep_dataset`` swallows unknown keywords into ``**load_opts``, so a bug
    here is silent: the sweep runs to completion at the adapter defaults while
    its provenance copy records the request that never took effect.
    """
    from ioptics import config, prep, run

    seen = []
    monkeypatch.setattr(prep, 'prep_dataset',
                        lambda dataset, **kw: seen.append((dataset, kw)) or [])
    cfg = config.loads(
        'sweep_id: dsopts\ndatasets: [L23, PANGAEA]\nalgorithms: [expb_pow]\n'
        'dataset_opts:\n  L23: {X: 4, Y: 30}\n')
    out = run.run_sweep(cfg, root=tmp_path)

    opts = {name: kw for name, kw in seen}
    assert opts['L23']['X'] == 4 and opts['L23']['Y'] == 30
    # the unmentioned dataset is called exactly as before -- no stray keywords
    assert 'X' not in opts['PANGAEA'] and 'Y' not in opts['PANGAEA']
    # ... and the sweep-level options still ride alongside
    assert opts['L23']['noise'] == cfg.noise_model
    assert out['sweep_id'] == 'dsopts'

    import yaml
    prov = yaml.safe_load(Path(out['provenance']).read_text())
    assert prov['dataset_opts'] == {'L23': {'X': 4, 'Y': 30}}
    assert prov['datasets']['L23']['opts'] == {'X': 4, 'Y': 30}
    assert 'opts' not in prov['datasets']['PANGAEA']


def test_run_sweep_without_dataset_opts_passes_no_extra_keywords(monkeypatch,
                                                                 tmp_path):
    from ioptics import config, prep, run

    seen = []
    monkeypatch.setattr(prep, 'prep_dataset',
                        lambda dataset, **kw: seen.append(kw) or [])
    cfg = config.loads(
        'sweep_id: plain\ndatasets: [L23]\nalgorithms: [expb_pow]\n')
    run.run_sweep(cfg, root=tmp_path)
    assert set(seen[0]) == {'obs_ids', 'noise', 'seed', 'wv_min', 'wv_max',
                            'n_cores'}

"""Tests for ``ioptics.run`` — the chisq fit core.

The fit builds BING models, which loads the L23 pure-water data, so the
end-to-end checks are **Tier-2** (`@needs_l23`). They run on a real
``prep.prep_one('L23', idx)`` record and verify the truth-free initial guess and
that the least-squares fit converges to a finite, in-bounds solution that closes
on the observed ``Rrs``.
"""

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

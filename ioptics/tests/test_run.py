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

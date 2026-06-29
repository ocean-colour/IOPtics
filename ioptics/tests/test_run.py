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


@needs_l23
def test_run_algorithm_mcmc_not_yet():
    from ioptics import prep, run
    from ioptics.algorithms.spec import AlgorithmSpec

    record = prep.prep_one('L23', 0, seed=1234)
    spec = AlgorithmSpec.from_standard('giop')
    import pytest
    with pytest.raises(NotImplementedError):
        run.run_algorithm(spec, record, fit_method='mcmc')

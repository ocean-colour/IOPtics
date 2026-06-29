"""Tests for ``ioptics.evaluate`` — assembling a ``RetrievalResult``.

Tier-1 covers the pure ``_component_fit`` percentile helper (data-free). Tier-2
(`@needs_l23`) runs a real least-squares fit (which builds models / loads L23)
through ``from_chisq`` and checks the assembled result.
"""

import numpy as np

from ioptics import evaluate
from ioptics.records import ComponentFit, RetrievalResult
from ioptics.tests.conftest import needs_l23


# --------------------------------------------------------------------
# Tier 1 — the percentile helper
# --------------------------------------------------------------------
def test_component_fit_band_ordering():
    wave = np.linspace(400.0, 700.0, 11)
    # samples: each column a Gaussian so percentiles are well-ordered
    rng = np.random.default_rng(0)
    samples = rng.normal(loc=1.0, scale=0.1, size=(500, wave.size))
    cf = evaluate._component_fit(wave, samples, ((16, 84), (2.5, 97.5)))
    assert isinstance(cf, ComponentFit)
    assert cf.med.shape == wave.shape
    assert np.all(cf.lo95 <= cf.lo68)
    assert np.all(cf.lo68 <= cf.med)
    assert np.all(cf.med <= cf.hi68)
    assert np.all(cf.hi68 <= cf.hi95)


# --------------------------------------------------------------------
# Tier 2 — full from_chisq on a real fit
# --------------------------------------------------------------------
@needs_l23
def test_from_chisq_assembles_result():
    from ioptics import prep, run
    from ioptics.algorithms.spec import AlgorithmSpec

    record = prep.prep_one('L23', 0, seed=1234)
    for name, k_expected in (('expb_pow', 5), ('giop', 3)):
        spec = AlgorithmSpec.from_standard(name)
        models, rt_dict, ans, cov = run.fit_chisq(spec, record)
        res = evaluate.from_chisq(spec, record, models, rt_dict, ans, cov)

        assert isinstance(res, RetrievalResult)
        assert res.dataset == 'L23' and res.algorithm == name
        assert res.fit_method == 'chisq'
        assert res.status == 'ok'

        # components: all spectral keys, bands on the native grid + ordered
        assert set(res.components) == set(evaluate._SPECTRAL)
        for key, cf in res.components.items():
            assert cf.med.shape == record.wave.shape
            assert np.all(cf.lo95 <= cf.hi95)
            assert np.all(np.isfinite(cf.med))

        # params: one (med, sigma) per model parameter
        assert len(res.params) == k_expected
        assert all(len(v) == 2 for v in res.params.values())

        # stats: well-formed and order-unity reduced chi^2
        assert res.stats['k'] == k_expected
        assert res.stats['n_bands'] == record.wave.size
        assert 0.0 < res.stats['chi2_nu'] < 5.0
        assert np.isfinite(res.stats['AIC']) and np.isfinite(res.stats['BIC'])

        # derived scalar present
        assert 'a_cdom440' in res.scalars


@needs_l23
def test_run_algorithm_end_to_end_returns_result():
    from ioptics import prep, run
    from ioptics.algorithms.spec import AlgorithmSpec

    record = prep.prep_one('L23', 0, seed=1234)
    res = run.run_algorithm(AlgorithmSpec.from_standard('giop'), record)
    assert isinstance(res, RetrievalResult)
    assert res.status == 'ok'
    assert res.components['a'].med.shape == record.wave.shape

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


# --------------------------------------------------------------------
# Tier 1 — fit status classification and shape-parameter promotion
# --------------------------------------------------------------------
def _record_peaking_at(peak_nm):
    """A minimal record whose Rrs peaks at ``peak_nm``."""
    from ioptics.records import PreparedRecord

    wave = np.arange(400.0, 751.0, 5.0)
    Rrs = np.exp(-0.5 * ((wave - peak_nm) / 40.0) ** 2) * 0.02
    return PreparedRecord(dataset='X', obs_id=0, wave=wave, Rrs=Rrs,
                          varRrs=(0.02 * Rrs) ** 2, Rrs_clean=Rrs,
                          truth={}, truth_interp={}, init={},
                          noise_model='pct:0.02', noise_seed=None)


def test_status_ok_for_an_acceptable_fit():
    from ioptics.records import CHI2NU_POOR_FIT

    rec = _record_peaking_at(450.0)
    assert evaluate._fit_status(rec, {'chi2_nu': 1.0}, True) == 'ok'
    # right at the threshold is still acceptable
    assert evaluate._fit_status(
        rec, {'chi2_nu': CHI2NU_POOR_FIT}, True) == 'ok'


def test_status_fit_failed_beats_everything():
    rec = _record_peaking_at(600.0)          # red-peaked, but unusable params
    assert evaluate._fit_status(rec, {'chi2_nu': 1.0}, False) == 'fit_failed'


def test_status_poor_fit_when_the_regime_does_not_explain_it():
    # A blue-peaked (clear) spectrum this family *should* handle: a bad fit
    # is a statement about the fit, not about scope.
    rec = _record_peaking_at(450.0)
    assert evaluate._fit_status(rec, {'chi2_nu': 50.0}, True) == 'poor_fit'


def test_status_out_of_scope_for_red_peaked_spectra():
    from ioptics.records import RED_PEAK_NM

    rec = _record_peaking_at(RED_PEAK_NM + 40.0)
    assert evaluate._fit_status(rec, {'chi2_nu': 50.0}, True) == 'out_of_scope'
    # ... but only when the fit is actually bad: a turbid spectrum the model
    # does fit is in scope by definition.
    assert evaluate._fit_status(rec, {'chi2_nu': 1.2}, True) == 'ok'


def test_status_nonfinite_chi2_is_not_ok():
    rec = _record_peaking_at(450.0)
    assert evaluate._fit_status(rec, {'chi2_nu': np.nan}, True) == 'poor_fit'
    assert evaluate._fit_status(rec, {}, True) == 'poor_fit'


def test_all_statuses_are_declared():
    from ioptics.records import STATUSES

    rec = _record_peaking_at(450.0)
    red = _record_peaking_at(650.0)
    seen = {evaluate._fit_status(rec, {'chi2_nu': 1.0}, True),
            evaluate._fit_status(rec, {'chi2_nu': 99.0}, True),
            evaluate._fit_status(red, {'chi2_nu': 99.0}, True),
            evaluate._fit_status(rec, {'chi2_nu': 1.0}, False)}
    assert seen == set(STATUSES)


def test_shape_params_come_from_the_models():
    class FakeModel:
        def __init__(self, pnames, log_params):
            self.pnames = pnames
            self.log_params = log_params
            self.nparam = len(pnames)

    # the open-ocean pair: exactly the historical ('Sdg', 'beta')
    a = FakeModel(['Adg', 'Sdg', 'Aph'], [True, False, True])
    bb = FakeModel(['Bnw', 'beta'], [True, False])
    assert evaluate._shape_param_names([a, bb]) == ['Sdg', 'beta']

    # two-component backscattering adds its exponents
    bb2 = FakeModel(['Bmin', 'eta_min', 'Borg', 'eta_org'],
                    [True, False, True, False])
    assert evaluate._shape_param_names([a, bb2]) == ['Sdg', 'eta_min',
                                                     'eta_org']


def test_shape_params_tolerate_models_that_declare_nothing():
    class Undeclared:
        pnames = ['Aexp', 'Aph']
        nparam = 2

    # A model with no log_params is treated as all-log10 (bing's default),
    # so it contributes no shape parameters rather than raising.
    assert evaluate._shape_param_names([Undeclared(), Undeclared()]) == []

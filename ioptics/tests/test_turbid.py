"""Tests for the turbid-water algorithms (BING's two-component ``bb_nw``).

Tier 1 (data-free) covers the opt-in registration and the ``maxfev`` field:
building an :class:`AlgorithmSpec` reads ``bing.parameters.standard`` but
constructs no models, so it needs no data tree.

Tier 2 (``@needs_l23``) runs the turbid algorithms through
:func:`ioptics.run.run_algorithm` on a real L23 spectrum, which is where the
models actually get built.

The turbid models are deliberately **not** in the standard seed -- see
:func:`ioptics.algorithms.registry.register_turbid` -- so a test that wants
them has to opt in, exactly as a sweep config does.
"""

import dataclasses

import numpy as np
import pytest

from ioptics.algorithms import registry
from ioptics.algorithms.spec import AlgorithmSpec
from ioptics.tests.conftest import needs_l23

TURBID_NAMES = ('expb_pow2flat', 'expb_pow2', 'expb_powflex')


@pytest.fixture
def turbid_registered():
    """Opt in, then restore the registry so other tests see the seed only."""
    before = dict(registry.REGISTRY)
    specs = registry.register_turbid()
    yield specs
    registry.REGISTRY.clear()
    registry.REGISTRY.update(before)


# --------------------------------------------------------------------
# Tier 1 — opt-in registration
# --------------------------------------------------------------------
def test_turbid_not_in_standard_seed():
    # The open-ocean leaderboard must not be diluted by models that merely
    # reproduce the single-power-law solution on clear water.
    seeded = dict(registry._STANDARD_SEED)
    for name in TURBID_NAMES:
        assert name not in seeded
        assert name in dict(registry.TURBID_SEED)


def test_lookup_before_opt_in_explains_itself():
    # Whatever else happens, a config naming a turbid algorithm should not
    # get a bare "unknown algorithm" with no way forward. The registry is
    # module state that another test may already have opted in, so restore
    # whatever was there rather than skipping on test order.
    saved = {name: registry.REGISTRY.pop(name)
             for name in TURBID_NAMES if name in registry.REGISTRY}
    try:
        with pytest.raises(KeyError) as exc:
            registry.get('expb_pow2flat')
        assert 'register_turbid' in str(exc.value)
    finally:
        registry.REGISTRY.update(saved)


def test_register_turbid_adds_all_three(turbid_registered):
    avail = registry.available()
    for name in TURBID_NAMES:
        assert name in avail
    # ... and leaves the standard seed in place
    for name in ('expb_pow', 'giop', 'gsm'):
        assert name in avail


def test_turbid_specs_carry_the_right_models(turbid_registered):
    expected = {'expb_pow2flat': ('Pow2Flat', 3),
                'expb_pow2': ('Pow2', 4),
                # the control: ordinary Pow, only the beta prior is widened
                'expb_powflex': ('Pow', 2)}
    for name, (bbnw, n_bpriors) in expected.items():
        spec = registry.get(name)
        assert spec.bbnw_model == bbnw
        assert spec.anw_model == 'ExpBricaud'
        assert len(spec.bpriors) == n_bpriors
        assert spec.label.startswith('ExpB_')


def test_powflex_widens_the_slope_prior(turbid_registered):
    # The whole point of the control algorithm: beta may go negative, so
    # bb_nw can flatten or rise toward the red.
    flex = registry.get('expb_powflex')
    ref = registry.get('expb_pow')
    assert flex.bpriors[1]['pmin'] < 0.0
    assert ref.bpriors[1]['pmin'] == 0.0
    assert flex.bpriors[0] == ref.bpriors[0]        # amplitude unchanged


def test_pow2_exponent_priors_are_disjoint(turbid_registered):
    # Mineral and organic terms are exchangeable unless their exponent
    # ranges are kept apart; overlapping ranges would leave the posterior
    # with a label-switching degeneracy.
    spec = registry.get('expb_pow2')
    eta_min, eta_org = spec.bpriors[1], spec.bpriors[3]
    assert eta_min['pmax'] <= eta_org['pmin']
    # amplitudes stay log-flavored, exponents linear
    flavors = [p['flavor'].startswith('log') for p in spec.bpriors]
    assert flavors == [True, False, True, False]


def test_register_turbid_is_idempotent(turbid_registered):
    # Sweep configs may call it more than once per process
    first = registry.get('expb_pow2flat')
    registry.register_turbid()
    assert registry.get('expb_pow2flat').bbnw_model == first.bbnw_model


# --------------------------------------------------------------------
# Tier 1 — the maxfev field
# --------------------------------------------------------------------
def test_standard_seed_carries_the_default_budget():
    # The registry seeds every open-ocean algorithm at DEFAULT_MAXFEV: at
    # scipy's own default, 30% of expb_pow's PANGAEA rows exhausted the budget
    # and were recorded as crashes (raised from None per JXP, 2026-08-10 —
    # reports/pangaea_fits_report.md). The *spec factory* stays neutral:
    # budgets are registry policy, not part of the algorithm definition.
    for name in ('expb_pow', 'giop', 'gsm'):
        assert registry.get(name).maxfev == registry.DEFAULT_MAXFEV
    assert AlgorithmSpec.from_standard('expb_pow').maxfev is None


def test_turbid_specs_share_the_raised_budget(turbid_registered):
    # These models need it even on clear water: at scipy's default they fail
    # to converge on a substantial fraction of spectra. The budget now equals
    # the standard seed's, so head-to-head contests measure the model, not
    # the budget.
    for name in TURBID_NAMES:
        assert registry.get(name).maxfev == registry.TURBID_MAXFEV
        assert registry.get(name).maxfev == registry.DEFAULT_MAXFEV
        assert registry.get(name).maxfev > 1000


def test_turbid_specs_claim_turbid_scope(turbid_registered):
    # Red-peaked water is these algorithms' purpose: run_algorithm's pre-fit
    # out_of_scope guard must not decline it for them, while the open-ocean
    # seed keeps fits_turbid=False and is declined.
    for name in TURBID_NAMES:
        assert registry.get(name).fits_turbid is True
    for name in ('expb_pow', 'giop', 'gsm'):
        assert registry.get(name).fits_turbid is False


def test_maxfev_is_overridable():
    specs = registry.register_turbid(maxfev=None)
    try:
        assert specs['expb_pow2flat'].maxfev is None
        spec = dataclasses.replace(specs['expb_pow2flat'], maxfev=123)
        assert spec.maxfev == 123
    finally:
        for name in TURBID_NAMES:
            registry.REGISTRY.pop(name, None)


# --------------------------------------------------------------------
# Tier 2 — through the real fitting path
# --------------------------------------------------------------------
@needs_l23
def test_fit_chisq_forwards_maxfev(turbid_registered):
    """``fit_chisq`` must hand the spec's budget to bing, not drop it."""
    from bing.fitting import chisq_fit
    from ioptics import prep, run

    record = prep.prep_one('L23', 0, seed=1234)
    seen = {}
    original = chisq_fit.fit

    def spy(items, models, rt_dict, bounds=None, maxfev=None):
        seen['maxfev'] = maxfev
        return original(items, models, rt_dict, bounds=bounds,
                        maxfev=maxfev)

    chisq_fit.fit = spy
    try:
        run.fit_chisq(registry.get('expb_pow2flat'), record)
        assert seen['maxfev'] == registry.TURBID_MAXFEV
        seen.clear()
        run.fit_chisq(registry.get('expb_pow'), record)
        assert seen['maxfev'] == registry.DEFAULT_MAXFEV   # the seeded budget
        seen.clear()
        import dataclasses
        neutral = dataclasses.replace(registry.get('expb_pow'), maxfev=None)
        run.fit_chisq(neutral, record)
        assert seen['maxfev'] is None      # None still means scipy's default
    finally:
        chisq_fit.fit = original


@needs_l23
@pytest.mark.parametrize('name', TURBID_NAMES)
def test_turbid_algorithm_runs_end_to_end(name, turbid_registered):
    from ioptics import prep, run

    record = prep.prep_one('L23', 0, seed=1234)
    spec = registry.get(name)
    res = run.run_algorithm(spec, record)

    assert res.status == 'ok'
    assert res.algorithm == name
    # Every fitted parameter is reported by name, the new shape parameters
    # included -- that is what keeps them recoverable from a saved fit even
    # though they do not (yet) get their own scalar columns.
    expected_bb = {'expb_pow2flat': {'Bmin', 'Borg', 'eta_org'},
                   'expb_pow2': {'Bmin', 'eta_min', 'Borg', 'eta_org'},
                   'expb_powflex': {'Bnw', 'beta'}}[name]
    assert expected_bb <= set(res.params)
    assert {'Adg', 'Sdg', 'Aph'} <= set(res.params)
    assert np.all(np.isfinite([v[0] for v in res.params.values()]))
    assert res.stats['k'] == len(spec.apriors) + len(spec.bpriors)
    assert np.isfinite(res.stats['chi2_nu'])
    # the spectral components a sweep scores
    for comp in ('a_dg', 'a_ph', 'bb_p', 'Rrs_model'):
        assert comp in res.components


@needs_l23
def test_turbid_models_do_not_regress_clear_water(turbid_registered):
    """On a clear L23 spectrum the extra components must not cost accuracy.

    ``Pow2`` contains ``Pow`` exactly, so its *raw* chi-squared cannot
    legitimately be worse; the reduced value may rise by exactly the
    degrees-of-freedom factor and no more.
    """
    from ioptics import prep, run

    record = prep.prep_one('L23', 0, seed=1234)
    ref = run.run_algorithm(registry.get('expb_pow'), record)
    n_bands = ref.stats['n_bands']

    for name in ('expb_pow2flat', 'expb_pow2'):
        res = run.run_algorithm(registry.get(name), record)
        assert res.stats['chi2'] <= ref.stats['chi2']*1.01
        dof_penalty = ((n_bands - ref.stats['k']) /
                       (n_bands - res.stats['k']))
        assert res.stats['chi2_nu'] <= ref.stats['chi2_nu']*dof_penalty*1.01

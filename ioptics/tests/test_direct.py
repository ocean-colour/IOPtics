"""Tier-1 tests for direct (non-fitting) algorithms: ``DirectSpec`` end to end.

Data-free. The real LS2 driver arrives in ls2 task 7, so the run-stage tests
plug a toy driver in through :func:`ioptics.run.register_direct_driver`; what is
under test here is the integration surface -- spec, registry, config, the
run-stage branch, ``assemble_direct``, provenance and the profile block -- not
LS2's physics.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from ioptics import config, evaluate, provenance, run
from ioptics.algorithms import registry
from ioptics.algorithms.spec import (DIRECT_OUTPUTS, AlgorithmSpec,
                                     DirectSpec, is_direct)
from ioptics.records import PreparedRecord, RetrievalResult

WAVE = np.arange(400., 701., 25.)


def _record(obs_id=0, *, peak_nm=440., dataset='TOY'):
    """A minimal record whose Rrs peaks at ``peak_nm``."""
    rrs = 0.004 * np.exp(-0.5 * ((WAVE - peak_nm) / 60.) ** 2) + 1e-4
    return PreparedRecord(
        dataset=dataset, obs_id=obs_id, wave=WAVE.copy(), Rrs=rrs,
        varRrs=(0.05 * rrs) ** 2, Rrs_clean=rrs.copy(), truth={},
        truth_interp={}, init={'Chl': 0.1, 'Y': 1.0}, noise_model='pace',
        noise_seed=None)


def _toy_values(record, *, poison=None):
    """Positive, smooth spectra for each output; ``poison`` NaNs/negates one."""
    base = 0.02 * (record.wave / 440.) ** -2
    comps = {'a': base + 0.01, 'a_nw': base, 'bb': 0.3 * base + 1e-3,
             'bb_p': 0.3 * base}
    if poison is not None:
        name, idx, value = poison
        comps[name] = comps[name].copy()
        comps[name][idx] = value
    return comps


@pytest.fixture
def toy_driver(monkeypatch):
    """Register a toy driver as method ``'toy'``; yields a call log."""
    calls = []

    def invert(spec, record):
        calls.append((spec.name, record.obs_id))
        poison = record.truth.get('_poison')
        return {'components': _toy_values(record, poison=poison),
                'scalars': {'kappa_frac': (0.5, 0.0)}}

    monkeypatch.setitem(run._DIRECT_DRIVERS, 'toy', invert)
    return calls


def _toy_spec(**kw):
    return DirectSpec(name=kw.pop('name', 'toy_direct'), label='Toy',
                      method='toy', **kw)


# --- spec ----------------------------------------------------------------------

def test_direct_spec_defaults_and_honest_label():
    spec = DirectSpec(name='x', label='X')
    assert spec.fit_method == 'direct' and is_direct(spec)
    assert spec.outputs == DIRECT_OUTPUTS
    assert not is_direct(AlgorithmSpec(name='b', label='B', anw_model='GIOP',
                                       bbnw_model='Lee', apriors=[],
                                       bpriors=[]))
    # none of the BING surface is carried
    for attr in ('rt', 'mcmc', 'apriors', 'build_models', 'to_bing_p'):
        assert not hasattr(spec, attr)


@pytest.mark.parametrize('kw', [
    {'fit_method': 'chisq'}, {'kd_source': 'nn:SeaWiFS'},
    {'bp_source': 'measured'}, {'muw_mode': 'guess'},
    {'outputs': ('a', 'a_ph')}, {'outputs': ()}, {'kd_noise': -0.1},
    {'tol': 0.}])
def test_direct_spec_rejects_bad_values(kw):
    with pytest.raises(ValueError):
        DirectSpec(name='x', label='X', **kw)


def test_with_overrides_applies_copies_and_revalidates():
    spec = DirectSpec(name='x', label='X')
    out = spec.with_overrides({'raman': False, 'kd_source': 'nn:PACE_v2.3'})
    assert out.raman is False and out.kd_source == 'nn:PACE_v2.3'
    assert spec.raman is True and spec.kd_source == 'record'   # untouched
    assert spec.with_overrides({}) is spec
    with pytest.raises(ValueError, match='direct algorithm'):
        spec.with_overrides({'rt': {'include_Raman': True}})    # a BING field
    with pytest.raises(ValueError, match='direct algorithm'):
        spec.with_overrides({'name': 'y'})
    with pytest.raises(ValueError, match='kd_source'):
        spec.with_overrides({'kd_source': 'nope'})              # re-validated


# --- registry ------------------------------------------------------------------

def test_register_direct_is_opt_in_and_hinted(monkeypatch):
    monkeypatch.setattr(registry, 'REGISTRY', dict(registry.REGISTRY))
    for name in registry.DIRECT_SEED:
        registry.REGISTRY.pop(name, None)
    with pytest.raises(KeyError, match='register_direct'):
        registry.get('ls2_i')
    out = registry.register_direct()
    assert list(out) == list(registry.DIRECT_SEED)
    assert all(is_direct(registry.get(n)) for n in out)
    registry.register_direct()                 # repeat calls are harmless


def test_each_rung_differs_from_rung_i_only_in_its_intended_inputs():
    """The ladder's design: adjacent rungs differ in exactly one input."""
    import dataclasses

    specs = registry.register_direct()
    base = dataclasses.asdict(specs['ls2_i'])

    def diff(name):
        d = dataclasses.asdict(specs[name])
        return {k for k in d if k not in ('name', 'label') and d[k] != base[k]}

    assert diff('ls2_ii') == {'bp_source'}
    assert diff('ls2_iii') == {'bp_source', 'kd_source'}
    assert diff('ls2_iii_modis') == {'bp_source', 'kd_source'}
    assert diff('ls2_i_effmuw') == {'muw_mode'}
    for level in ('05', '10', '20'):
        assert diff(f'ls2_i_kdnoise{level}') == {'kd_noise'}
    assert specs['ls2_iii'].kd_source == 'nn:PACE_v2.3'           # Q27
    assert specs['ls2_iii_modis'].kd_source == 'nn:MODIS_v1.3'    # Q30


# --- config --------------------------------------------------------------------

def test_config_accepts_direct_per_algorithm_and_round_trips():
    text = ('sweep_id: ls2_cfg\ndatasets: [L23]\n'
            'algorithms:\n  - expb_pow\n'
            '  - {name: ls2_i, fit_method: direct, raman: false}\n'
            '  - {name: ls2_iii, kd_source: "nn:MODIS_v1.3"}\n')
    cfg = config.loads(text)
    assert cfg.algorithms[1].fit_method == 'direct'
    assert cfg.algorithms[1].overrides == {'raman': False}
    assert config.loads(cfg.dump()) == cfg


def test_config_refuses_direct_as_the_sweep_default():
    with pytest.raises(config.ConfigError, match='direct'):
        config.loads('sweep_id: s\ndatasets: [L23]\nalgorithms: [ls2_i]\n'
                     'fit_method: direct\n')


def test_config_still_rejects_an_unknown_override_key():
    with pytest.raises(config.ConfigError, match='direct algorithms'):
        config.loads('sweep_id: s\ndatasets: [L23]\n'
                     'algorithms:\n  - {name: ls2_i, kd_sorce: record}\n')


# --- run stage and assemble_direct ---------------------------------------------

def test_run_algorithm_direct_result_shape(toy_driver):
    rec = _record()
    res = run.run_algorithm(_toy_spec(), rec)

    assert isinstance(res, RetrievalResult)
    assert res.fit_method == 'direct' and res.status == 'ok'
    assert set(res.components) == set(DIRECT_OUTPUTS)
    assert 'Rrs_model' not in res.components and not res.params
    n = rec.wave.size
    for cf in res.components.values():
        assert cf.med.shape == (n,)
        for bound in (cf.lo68, cf.hi68, cf.lo95, cf.hi95):
            assert bound.shape == (n,) and np.all(np.isnan(bound))
    assert res.stats['n_bands'] == n
    for key in ('chi2', 'chi2_nu', 'AIC', 'BIC', 'k', 'rel_misfit'):
        assert key in res.stats and np.isnan(res.stats[key])
    assert res.scalars == {'kappa_frac': (0.5, 0.0)}
    assert toy_driver == [('toy_direct', 0)]


@pytest.mark.parametrize('poison, status', [
    (('a_nw', 3, np.nan), 'poor_fit'),      # one NaN band
    (('bb_p', 0, -1e-4), 'poor_fit'),       # one negative value
    (None, 'ok')])
def test_direct_status_follows_the_q5_rule(toy_driver, poison, status):
    rec = _record()
    if poison is not None:
        rec.truth['_poison'] = poison
    assert run.run_algorithm(_toy_spec(), rec).status == status


def test_nothing_finite_is_fit_failed():
    spec = _toy_spec(outputs=('a', 'bb'))
    rec = _record()
    nan = np.full(rec.wave.size, np.nan)
    res = evaluate.assemble_direct(spec, rec, {'components': {'a': nan,
                                                              'bb': nan}})
    assert res.status == 'fit_failed'
    assert set(res.components) == {'a', 'bb'}


def test_status_only_judges_the_requested_outputs(toy_driver):
    rec = _record()
    rec.truth['_poison'] = ('a_nw', 2, np.nan)
    assert run.run_algorithm(_toy_spec(outputs=('a', 'bb')), rec).status == 'ok'


def test_assemble_direct_refuses_a_driver_that_skips_an_output():
    spec, rec = _toy_spec(), _record()
    comps = _toy_values(rec)
    del comps['bb_p']
    with pytest.raises(ValueError, match='bb_p'):
        evaluate.assemble_direct(spec, rec, {'components': comps})
    comps = _toy_values(rec)
    comps['a'] = comps['a'][:-1]
    with pytest.raises(ValueError, match='bands'):
        evaluate.assemble_direct(spec, rec, {'components': comps})


def test_fit_method_must_match_the_spec_type(toy_driver):
    rec = _record()
    with pytest.raises(ValueError, match="runs only as fit_method='direct'"):
        run.run_algorithm(_toy_spec(), rec, fit_method='chisq')
    bing = AlgorithmSpec(name='b', label='B', anw_model='GIOP',
                         bbnw_model='Lee', apriors=[], bpriors=[])
    with pytest.raises(ValueError, match='fitted algorithm'):
        run.run_algorithm(bing, rec, fit_method='direct')


def test_red_peaked_record_is_declined_before_the_driver(toy_driver):
    red = _record(peak_nm=650.)
    res = run.run_algorithm(_toy_spec(), red)
    assert res.status == 'out_of_scope' and res.fit_method == 'direct'
    assert res.stats['n_bands'] == red.wave.size and np.isnan(res.stats['k'])
    assert toy_driver == []                       # the driver never ran
    # ... unless the spec claims turbid water in scope
    assert run.run_algorithm(_toy_spec(fits_turbid=True), red).status == 'ok'


def test_driver_failure_becomes_fit_failed_in_robust_mode(monkeypatch):
    def boom(spec, record):
        raise RuntimeError('driver exploded')

    monkeypatch.setitem(run._DIRECT_DRIVERS, 'toy', boom)
    spec, recs = _toy_spec(), [_record(0), _record(1)]
    with pytest.raises(RuntimeError):
        run.run_batch(spec, recs, fit_method='direct', strict=True)
    out = run.run_batch(spec, recs, fit_method='direct', strict=False)
    assert [r.status for r in out] == ['fit_failed', 'fit_failed']
    assert all(r.fit_method == 'direct' and np.isnan(r.stats['k'])
               for r in out)


def test_a_method_without_a_driver_says_so(monkeypatch):
    monkeypatch.setitem(run.DIRECT_DRIVER_MODULES, 'ghost',
                        'ioptics.algorithms._no_such_driver')
    with pytest.raises(NotImplementedError, match='_no_such_driver'):
        run.run_algorithm(DirectSpec(name='g', label='G', method='ghost'),
                          _record())
    with pytest.raises(ValueError, match='no driver'):
        run.run_algorithm(DirectSpec(name='h', label='H', method='unknown'),
                          _record())


# --- run_sweep -----------------------------------------------------------------

def _sweep_setup(monkeypatch, recs):
    from ioptics import prep

    monkeypatch.setattr(prep, 'prep_dataset', lambda dataset, **kw: recs)
    monkeypatch.setattr(registry, 'REGISTRY', dict(registry.REGISTRY))
    registry.register(_toy_spec(name='toy_direct'), overwrite=True)


def test_run_sweep_runs_a_direct_algorithm_once_as_direct(toy_driver,
                                                          monkeypatch,
                                                          tmp_path):
    """Not forced to 'chisq', never sent to the MCMC subset."""
    recs = [_record(i) for i in range(3)]
    _sweep_setup(monkeypatch, recs)
    cfg = config.loads(
        'sweep_id: toy_direct_sweep\ndatasets: [TOY]\n'
        'algorithms:\n  - {name: toy_direct, raman: false}\n'
        'fit_method: mcmc\nmcmc_subset: 2\n')
    out = run.run_sweep(cfg, root=tmp_path)

    assert out['n_results'] == 3 and len(toy_driver) == 3
    scalar = pd.read_parquet(out['scalar'])
    assert set(scalar['fit_method']) == {'direct'}
    assert set(scalar['status']) == {'ok'}
    assert scalar['chain_file'].isna().all()
    assert scalar[['chi2', 'chi2_nu', 'BIC', 'rel_misfit']].isna().all().all()
    spectral = pd.read_parquet(out['spectral'])
    assert 'Rrs_model' not in set(spectral['component'])
    assert set(DIRECT_OUTPUTS) <= set(spectral['component'])

    prov = yaml.safe_load(Path(out['provenance']).read_text())
    (block,) = prov['algorithms']
    assert block['kind'] == 'direct' and block['raman'] is False
    assert block['digest'] == provenance.algorithm_digest(
        _toy_spec(name='toy_direct', raman=False))
    assert 'chains' not in prov


def test_run_sweep_rejects_a_fitted_method_on_a_direct_algorithm(
        toy_driver, monkeypatch, tmp_path):
    _sweep_setup(monkeypatch, [_record()])
    cfg = config.loads('sweep_id: bad\ndatasets: [TOY]\nalgorithms:\n'
                       '  - {name: toy_direct, fit_method: mcmc}\n')
    with pytest.raises(ValueError, match='direct algorithm'):
        run.run_sweep(cfg, root=tmp_path)
    assert toy_driver == []                      # failed before any record


# --- provenance and profiles ---------------------------------------------------

def test_direct_provenance_block_and_digest():
    spec = DirectSpec(name='ls2_x', label='LS2 x')
    block = provenance.algorithm_block(spec)
    assert block['kind'] == 'direct' and block['fit_method'] == 'direct'
    for key in ('rt', 'mcmc', 'apriors', 'maxfev', 'anw_model'):
        assert key not in block
    yaml.safe_load(yaml.safe_dump(block))        # serializable

    digest = provenance.algorithm_digest(spec)
    assert digest == provenance.algorithm_digest(block)
    # identity fields do not move it; configuration does
    assert digest == provenance.algorithm_digest(
        DirectSpec(name='other', label='Other'))
    for change in ({'raman': False}, {'kd_source': 'nn:PACE_v2.3'},
                   {'bp_source': 'oc4v4'}, {'muw_mode': 'effective'},
                   {'kd_noise': 0.05}, {'outputs': ('a', 'bb')}):
        assert provenance.algorithm_digest(spec.with_overrides(change)) != digest


def test_a_mixed_sweep_record_round_trips(tmp_path):
    bing = AlgorithmSpec(
        name='expb_pow', label='ExpB_Pow', anw_model='ExpBricaud',
        bbnw_model='Pow', apriors=[{'flavor': 'log_uniform', 'pmin': -6,
                                    'pmax': 5}], bpriors=[])
    direct = DirectSpec(name='ls2_i', label='LS2 (i)')
    rec = provenance.build('mixed', specs=[bing, direct])
    blocks = {b['name']: b for b in rec['algorithms']}
    assert 'kind' not in blocks['expb_pow']           # BING block unchanged
    assert blocks['ls2_i']['kind'] == 'direct'
    path = provenance.write('mixed', rec, root=tmp_path)
    again = yaml.safe_load(Path(path).read_text())
    assert again['algorithms'] == rec['algorithms']


def test_profile_spec_block_for_a_direct_algorithm():
    from ioptics.report.profiles import _spec_block

    registry.register_direct()
    text = _spec_block('ls2_iii')
    assert 'Kd source' in text and 'nn:PACE_v2.3' in text
    assert 'oc4v4' in text and 'a_nw model' not in text

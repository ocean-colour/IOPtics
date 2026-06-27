"""Tier-1 (data-independent) unit tests for ``ioptics.records``.

Constructs each pipeline contract dataclass from synthetic values and checks
field round-tripping, defaults, and picklability (the records must survive a
``ProcessPoolExecutor`` boundary and on-disk caching between sweep stages).
"""

import pickle

import numpy as np

from ioptics.records import ComponentFit, PreparedRecord, RetrievalResult


def _synthetic_wave():
    return np.linspace(400.0, 700.0, 7)


def test_component_fit_construction():
    wave = _synthetic_wave()
    med = np.full_like(wave, 0.5)
    cf = ComponentFit(
        wave=wave,
        med=med,
        lo68=med - 0.1, hi68=med + 0.1,
        lo95=med - 0.2, hi95=med + 0.2,
    )
    assert cf.wave.shape == wave.shape
    np.testing.assert_allclose(cf.hi95 - cf.lo95, 0.4)
    # 95% interval brackets the 68% interval at every wavelength
    assert np.all(cf.lo95 <= cf.lo68)
    assert np.all(cf.hi95 >= cf.hi68)


def test_prepared_record_construction_and_defaults():
    wave = _synthetic_wave()
    rrs = np.full_like(wave, 0.01)
    rec = PreparedRecord(
        dataset='L23',
        obs_id=0,
        wave=wave,
        Rrs=rrs,
        varRrs=np.full_like(wave, 1e-6),
        Rrs_clean=rrs.copy(),
        truth={'Chl': 1.2},
        truth_interp={'Chl': False},
        init={'Chl': 1.0, 'Y': 0.5},
        noise_model='pace',
        noise_seed=1234,
    )
    assert rec.dataset == 'L23'
    assert rec.obs_id == 0
    assert rec.truth['Chl'] == 1.2
    assert rec.init['Y'] == 0.5
    assert rec.noise_seed == 1234
    # meta defaults to an independent empty dict
    assert rec.meta == {}


def test_prepared_record_meta_default_is_independent():
    wave = _synthetic_wave()
    common = dict(
        wave=wave, Rrs=wave * 0, varRrs=wave * 0 + 1e-6, Rrs_clean=wave * 0,
        truth={}, truth_interp={}, init={}, noise_model='insitu',
        noise_seed=None,
    )
    a = PreparedRecord(dataset='PANGAEA', obs_id='id_a', **common)
    b = PreparedRecord(dataset='PANGAEA', obs_id='id_b', **common)
    a.meta['x'] = 1
    assert b.meta == {}  # default_factory => no shared mutable default


def test_prepared_record_string_obs_id_and_no_noise():
    wave = _synthetic_wave()
    rrs = np.full_like(wave, 0.02)
    rec = PreparedRecord(
        dataset='GLORIA',
        obs_id='GLORIA_00042',
        wave=wave,
        Rrs=rrs,
        varRrs=(0.05 * rrs) ** 2,
        Rrs_clean=rrs,
        truth={},
        truth_interp={},
        init={},
        noise_model='insitu',
        noise_seed=None,
        meta={'source': 'GLORIA'},
    )
    assert isinstance(rec.obs_id, str)
    assert rec.noise_seed is None
    assert rec.truth == {}
    assert rec.meta['source'] == 'GLORIA'


def test_retrieval_result_construction_and_defaults():
    res = RetrievalResult(
        dataset='L23', obs_id=0, algorithm='expb_pow', fit_method='chisq',
    )
    # defaulted containers
    assert res.components == {}
    assert res.params == {}
    assert res.scalars == {}
    assert res.stats == {}
    assert res.status == 'ok'
    assert res.provenance_id == ''


def test_retrieval_result_full_construction():
    wave = _synthetic_wave()
    a = ComponentFit(
        wave=wave, med=np.full_like(wave, 0.3),
        lo68=np.full_like(wave, 0.25), hi68=np.full_like(wave, 0.35),
        lo95=np.full_like(wave, 0.20), hi95=np.full_like(wave, 0.40),
    )
    res = RetrievalResult(
        dataset='L23', obs_id=7, algorithm='giop', fit_method='mcmc',
        components={'a': a},
        params={'Adg': (-1.0, 0.1), 'Aph': (-0.5, 0.05)},
        scalars={'Chl': (1.1, 0.2)},
        stats={'chi2': 3.2, 'chi2_nu': 0.8, 'AIC': 10.0, 'BIC': 12.0,
               'n_bands': 7, 'k': 3},
        status='ok',
        provenance_id='expb_giop_L23_v1#giop',
    )
    assert res.fit_method == 'mcmc'
    assert res.components['a'].med.shape == wave.shape
    assert res.params['Adg'] == (-1.0, 0.1)
    assert res.stats['k'] == 3
    assert res.provenance_id.endswith('giop')


def test_records_are_picklable():
    wave = _synthetic_wave()
    rec = PreparedRecord(
        dataset='L23', obs_id=3, wave=wave, Rrs=wave * 0 + 0.01,
        varRrs=wave * 0 + 1e-6, Rrs_clean=wave * 0 + 0.01,
        truth={'Chl': 0.9}, truth_interp={'Chl': False},
        init={'Chl': 1.0, 'Y': 0.5}, noise_model='pace', noise_seed=42,
        meta={'X': 1, 'Y': 0},
    )
    cf = ComponentFit(
        wave=wave, med=wave * 0, lo68=wave * 0, hi68=wave * 0,
        lo95=wave * 0, hi95=wave * 0,
    )
    res = RetrievalResult(
        dataset='L23', obs_id=3, algorithm='expb_pow', fit_method='chisq',
        components={'a': cf}, stats={'chi2': 1.0},
    )
    for obj in (rec, cf, res):
        round_tripped = pickle.loads(pickle.dumps(obj))
        assert type(round_tripped) is type(obj)

    # spot-check a value survives the round trip
    rt_rec = pickle.loads(pickle.dumps(rec))
    np.testing.assert_array_equal(rt_rec.wave, rec.wave)
    assert rt_rec.meta == {'X': 1, 'Y': 0}

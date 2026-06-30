"""Tier-1 tests for ``ioptics.io`` — long/tidy parquet round-trip + layout.

Uses synthetic ``PreparedRecord`` / ``RetrievalResult`` objects (no models, no
data), so it is data-independent. Writes to a ``tmp_path`` root.
"""

import numpy as np

from ioptics import io
from ioptics.records import ComponentFit, PreparedRecord, RetrievalResult

WAVE = np.linspace(400.0, 700.0, 7)


def _synthetic_record():
    try:
        from ocpy.spectra import Spectrum
        a_dg = Spectrum(WAVE, np.linspace(0.05, 0.01, WAVE.size), units='1/m')
    except Exception:                              # ocpy absent -> plain array
        a_dg = type('S', (), {'values': np.linspace(0.05, 0.01, WAVE.size)})()
    return PreparedRecord(
        dataset='L23', obs_id=7, wave=WAVE, Rrs=np.full(WAVE.size, 0.01),
        varRrs=np.full(WAVE.size, 1e-6), Rrs_clean=np.full(WAVE.size, 0.011),
        truth={'a_dg': a_dg, 'Chl': 1.2, 'Sdg': 0.017},
        truth_interp={'a_dg': False}, init={'Chl': 1.0, 'Y': 0.5},
        noise_model='pace', noise_seed=1234,
    )


def _cf(scale):
    med = np.full(WAVE.size, scale)
    return ComponentFit(wave=WAVE, med=med, lo68=med * 0.9, hi68=med * 1.1,
                        lo95=med * 0.8, hi95=med * 1.2)


def _synthetic_result():
    return RetrievalResult(
        dataset='L23', obs_id=7, algorithm='expb_pow', fit_method='chisq',
        components={'a': _cf(0.1), 'bb': _cf(0.01), 'a_ph': _cf(0.04),
                    'a_dg': _cf(0.06), 'bb_p': _cf(0.007), 'Rrs_model': _cf(0.011)},
        params={'Adg': (-1.0, 0.1), 'Sdg': (0.017, 0.001), 'Aph': (-1.3, 0.1),
                'Bnw': (-2.0, 0.2), 'beta': (1.0, 0.3)},
        scalars={'a_cdom440': (0.06, 0.005), 'Sdg': (0.017, 0.001),
                 'beta': (1.0, 0.3)},
        stats={'chi2': 60.0, 'chi2_nu': 0.8, 'AIC': 70.0, 'BIC': 80.0,
               'n_bands': WAVE.size, 'k': 5},
        status='ok', provenance_id='sweep_v1#expb_pow',
    )


def test_sweep_dir_layout(tmp_path):
    d = io.sweep_dir('sweep_v1', root=tmp_path, create=True)
    assert d == tmp_path / 'sweep_v1'
    assert (d / 'chains').is_dir() and (d / 'figures').is_dir()


def test_write_read_round_trip(tmp_path):
    pairs = [(_synthetic_result(), _synthetic_record())]
    paths = io.write_results('sweep_v1', pairs, root=tmp_path)
    assert paths['spectral'].is_file() and paths['scalar'].is_file()

    spectral, scalar = io.read_results('sweep_v1', root=tmp_path)

    # spectral: one row per component x wavelength (6 model components + Rrs_obs)
    assert len(spectral) == 7 * WAVE.size
    assert set(spectral['component']) == {'a', 'bb', 'a_ph', 'a_dg', 'bb_p',
                                          'Rrs_model', 'Rrs_obs'}
    for col in ('value', 'lo68', 'hi68', 'lo95', 'hi95', 'truth',
                'truth_interp', 'unit', 'wavelength'):
        assert col in spectral.columns
    # a_dg truth came from the record's Spectrum.
    adg = spectral[spectral.component == 'a_dg'].sort_values('wavelength')
    np.testing.assert_allclose(adg['truth'].to_numpy(),
                               np.linspace(0.05, 0.01, WAVE.size))
    # Rrs_model is model-only -> truth NaN
    rrs = spectral[spectral.component == 'Rrs_model']
    assert rrs['truth'].isna().all()
    # Rrs_obs carries the observed Rrs in `value`, no truth / no bounds.
    obs = spectral[spectral.component == 'Rrs_obs']
    np.testing.assert_allclose(obs['value'].to_numpy(), 0.01)   # record.Rrs
    assert obs['truth'].isna().all() and obs['lo68'].isna().all()
    # a component with no truth -> NaN
    assert spectral[spectral.component == 'bb_p']['truth'].isna().all()
    assert spectral['unit'][spectral.component.eq('Rrs_model').idxmax()] == '1/sr'


def test_chain_save_load_round_trip(tmp_path):
    rng = np.random.default_rng(0)
    chains = rng.normal(size=(50, 8, 3))          # (nsteps, nwalkers, nparam)
    record = _synthetic_record()
    path = io.save_chain('sweep_v1', 'giop', record, chains, root=tmp_path)
    assert path == tmp_path / 'sweep_v1' / 'chains' / 'giop_7.npz'
    assert path.is_file()

    loaded = io.load_chain(path)
    np.testing.assert_array_equal(loaded['chains'], chains)
    assert int(loaded['idx']) == 7
    np.testing.assert_array_equal(loaded['wave'], record.wave)
    np.testing.assert_array_equal(loaded['obs_Rrs'], record.Rrs)
    assert float(loaded['Chl']) == record.init['Chl']


def test_chain_file_column_from_result(tmp_path):
    result = _synthetic_result()
    result.fit_method = 'mcmc'
    result.chain_file = '/runs/sweep_v1/chains/giop_7.npz'
    io.write_results('sweep_v1', [(result, _synthetic_record())], root=tmp_path)
    _, scalar = io.read_results('sweep_v1', root=tmp_path)
    assert scalar.iloc[0]['chain_file'] == '/runs/sweep_v1/chains/giop_7.npz'


def test_scalar_table_schema_and_truth(tmp_path):
    pairs = [(_synthetic_result(), _synthetic_record())]
    io.write_results('sweep_v1', pairs, root=tmp_path)
    _, scalar = io.read_results('sweep_v1', root=tmp_path)

    assert len(scalar) == 1
    row = scalar.iloc[0]
    for col in ('chi2', 'chi2_nu', 'AIC', 'BIC', 'n_bands', 'k',
                'Chl', 'sig_Chl', 'a_cdom440', 'sig_a_cdom440',
                'Sdg', 'sig_Sdg', 'beta', 'sig_beta',
                'Chl_truth', 'a_cdom440_truth', 'Sdg_truth', 'beta_truth',
                'status', 'chain_file', 'provenance_id'):
        assert col in scalar.columns
    assert row['k'] == 5
    assert row['a_cdom440'] == 0.06
    assert row['Sdg_truth'] == 0.017          # from record.truth['Sdg']
    i440 = int(np.argmin(np.abs(WAVE - 440.0)))   # a_dg truth at nearest-440 band
    assert row['a_cdom440_truth'] == np.linspace(0.05, 0.01, WAVE.size)[i440]
    assert np.isnan(row['Chl'])               # Chl not yet derived
    assert row['status'] == 'ok'

"""Checks on bringing RT-A over for the LS2 comparison (ls2 task 9b).

``runs/prototypes/ls2/rta_fetch.py`` copies the staged RT-A files and refuses
anything that does not match 9a's ``MANIFEST.txt``.  ``rta_add_anw.py`` derives
the ``a_nw`` rows RT-A predates.  Tier 1 runs both on a tiny synthetic sweep in
RT-A's own (pre-``nan_reason``) schema.  Tier 2 checks the derived truth
against L23's ``anw`` and against what the L23 adapter attaches to ``a_nw``
today.
"""

import importlib.util
import pathlib

import numpy as np
import pandas as pd
import pytest
import yaml

from ioptics.tests.conftest import needs_l23

HERE = (pathlib.Path(__file__).resolve().parents[1] / 'runs' / 'prototypes'
        / 'ls2')
SID = 'rta_tiny_v1'
WAVE = np.array([400.0, 440.0, 555.0, 670.0])


def _load(name):
    spec = importlib.util.spec_from_file_location(f'ls2_{name}',
                                                  HERE / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_truth(rows):
    return rows['obs_id'].to_numpy() * 0.01 + rows['wavelength'].to_numpy() * 1e-5


def _tiny_sweep(root, *, with_nan_reason=False):
    """Two spectra x two algorithms x two fit methods, in RT-A's schema."""
    rng = np.random.default_rng(3)
    rows = []
    for obs in (0, 1):
        for algo in ('expb_pow_hyb_el', 'expb_pow_hyb_ramfl'):
            for fm in ('chisq', 'mcmc'):
                for comp in ('a', 'a_dg', 'a_ph', 'bb', 'Rrs_obs'):
                    for w in WAVE:
                        v = float(rng.uniform(0.01, 0.1))
                        rows.append({
                            'dataset': 'L23', 'obs_id': obs, 'algorithm': algo,
                            'fit_method': fm, 'component': comp,
                            'wavelength': w, 'value': v,
                            'lo68': 0.9 * v, 'hi68': 1.1 * v,
                            'lo95': 0.8 * v, 'hi95': 1.2 * v,
                            'truth': np.nan if comp == 'Rrs_obs' else v,
                            'truth_interp': False,
                            'unit': '1/sr' if comp == 'Rrs_obs' else '1/m'})
    df = pd.DataFrame(rows)
    if with_nan_reason:
        df['nan_reason'] = ''
    d = root / SID
    d.mkdir(parents=True)
    df.to_parquet(d / 'results_spectral.parquet', index=False)
    (d / 'provenance.yaml').write_text(
        'sweep_id: rta_tiny_v1\ndataset_opts:\n  L23:\n    X: 4\n'
        'algorithms:\n- name: expb_pow_hyb_el\n  digest: 6d084fec73da\n')
    return d, df


# --- rta_add_anw ------------------------------------------------------------------

def test_add_anw_adds_the_sum_with_nan_bounds_and_keeps_the_original(tmp_path):
    rta = _load('rta_add_anw')
    d, before = _tiny_sweep(tmp_path)
    prov_before = (d / 'provenance.yaml').read_text()
    out = rta.add_anw(SID, root=tmp_path, truth_fn=_fake_truth)
    after = pd.read_parquet(d / 'results_spectral.parquet')

    assert out['added'] == 2 * 2 * 2 * WAVE.size
    assert len(after) == len(before) + out['added']
    assert list(after.columns) == list(before.columns)   # no nan_reason added
    anw = after[after['component'] == 'a_nw'].set_index(rta.KEYS)
    key = rta.KEYS
    adg = before[before['component'] == 'a_dg'].set_index(key)['value']
    aph = before[before['component'] == 'a_ph'].set_index(key)['value']
    np.testing.assert_allclose(anw['value'], (adg + aph).loc[anw.index])
    assert anw[rta.BOUNDS].isna().all().all()
    np.testing.assert_allclose(anw['truth'], _fake_truth(anw.reset_index()))
    assert (anw['unit'] == '1/m').all() and not anw['truth_interp'].any()
    # the untouched rows are untouched
    pd.testing.assert_frame_equal(after.iloc[:len(before)].reset_index(drop=True),
                                  before)
    # the pristine table is kept, byte-identical in content
    pd.testing.assert_frame_equal(pd.read_parquet(d / rta.ORIG_FILE), before)
    # provenance: appended, original text intact, digest untouched
    prov = (d / 'provenance.yaml').read_text()
    assert prov.startswith(prov_before)
    rec = yaml.safe_load(prov)
    assert rec['algorithms'][0]['digest'] == '6d084fec73da'
    assert rec['derived']['a_nw']['rows_added'] == out['added']
    assert 'X=4' in rec['derived']['a_nw']['truth']


def test_add_anw_is_idempotent(tmp_path):
    rta = _load('rta_add_anw')
    d, _ = _tiny_sweep(tmp_path)
    rta.add_anw(SID, root=tmp_path, truth_fn=_fake_truth)
    once = pd.read_parquet(d / 'results_spectral.parquet')
    prov = (d / 'provenance.yaml').read_text()
    assert rta.add_anw(SID, root=tmp_path, truth_fn=_fake_truth)['added'] == 0
    pd.testing.assert_frame_equal(pd.read_parquet(d / 'results_spectral.parquet'),
                                  once)
    assert (d / 'provenance.yaml').read_text() == prov


def test_add_anw_fills_nan_reason_when_the_table_has_it(tmp_path):
    rta = _load('rta_add_anw')
    d, _ = _tiny_sweep(tmp_path, with_nan_reason=True)
    rta.add_anw(SID, root=tmp_path, truth_fn=_fake_truth)
    after = pd.read_parquet(d / 'results_spectral.parquet')
    assert (after.loc[after['component'] == 'a_nw', 'nan_reason'] == '').all()


def test_unpaired_rows_refuse(tmp_path):
    rta = _load('rta_add_anw')
    _, df = _tiny_sweep(tmp_path)
    parts = df[df['component'].isin(['a_dg', 'a_ph'])].iloc[1:]   # drop one a_dg
    with pytest.raises(ValueError, match='pair one-for-one'):
        rta.derive_anw_rows(parts, _fake_truth, df.columns)


def test_truth_off_the_grid_refuses():
    rta = _load('rta_add_anw')

    class _DS(dict):
        pass
    ds = _DS(Lambda=type('V', (), {'values': np.array([400.0, 405.0])})(),
             anw=type('V', (), {'values': np.ones((2, 2))})())
    truth = rta.l23_anw_truth(4, ds=ds)
    ok = pd.DataFrame({'dataset': ['L23'], 'obs_id': [1], 'wavelength': [405.0]})
    assert truth(ok)[0] == 1.0
    with pytest.raises(ValueError, match='not on'):
        truth(ok.assign(wavelength=402.5))


# --- rta_fetch: the manifest check ------------------------------------------------

def _staged(tmp_path):
    fetch = _load('rta_fetch')
    src = tmp_path / 'drive'
    src.mkdir(parents=True)
    pd.DataFrame({'x': range(5)}).to_parquet(src / 'results_scalar.parquet')
    pd.DataFrame({'y': range(7)}).to_parquet(src / 'results_spectral.parquet')
    (src / 'provenance.yaml').write_text('sweep_id: rt\n')
    lines = ['MANIFEST (test)', '', 'file  bytes  sha256  rows']
    for name in fetch.FILES:
        p = src / name
        rows = fetch.parquet_rows(p) if name.endswith('.parquet') else '-'
        lines.append(f'{name}  {p.stat().st_size}  {fetch.sha256(p)}  {rows}')
    (src / fetch.MANIFEST_FILE).write_text('\n'.join(lines) + '\n')
    return fetch, src


def test_fetch_copies_and_verifies_from_a_local_folder(tmp_path):
    fetch, src = _staged(tmp_path)
    dest = fetch.fetch(tmp_path / 'runs' / 'rt', source=str(src))
    got = fetch.verify_manifest(dest)
    assert got['results_spectral.parquet']['rows'] == 7
    assert got['provenance.yaml']['rows'] is None


def test_manifest_check_refuses_a_tampered_file(tmp_path):
    fetch, src = _staged(tmp_path)
    with open(src / 'provenance.yaml', 'a') as f:
        f.write('# edited\n')
    with pytest.raises(ValueError, match='provenance.yaml: bytes'):
        fetch.verify_manifest(src)
    # same size, different content: caught by the hash
    fetch2, src2 = _staged(tmp_path / 'b')
    q = src2 / 'provenance.yaml'
    q.write_text(q.read_text().replace('rt', 'RT'))
    with pytest.raises(ValueError, match='provenance.yaml: sha256'):
        fetch2.verify_manifest(src2)


def test_manifest_check_refuses_a_missing_file(tmp_path):
    fetch, src = _staged(tmp_path)
    (src / 'results_scalar.parquet').unlink()
    with pytest.raises(ValueError, match='results_scalar.parquet: missing'):
        fetch.verify_manifest(src)


def test_the_real_manifest_parses():
    fetch = _load('rta_fetch')
    text = """MANIFEST for RoB/RT/rt_tests_A_l23_v1/ (LS2 prompt 9a, verified by 9b)
date: 2026-10-04
sweep_git_commit: ioptics 92eea90  (bing bf56f6d, ocpy c3132a6)

file  bytes  sha256  rows
results_scalar.parquet  4525572  f0bc0e87593d6236ba425f5fae0ed5c23e4df1ffbb7cbc55791b8991a822a5df  33200
provenance.yaml  4323  c71583ade95e8e7facfc826f579994b5d47608dff46ba8296a6f302852047e8b  -
"""
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
        f.write(text)
    m = fetch.read_manifest(f.name)
    assert m['results_scalar.parquet'] == {
        'bytes': 4525572, 'rows': 33200,
        'sha256': 'f0bc0e87593d6236ba425f5fae0ed5c23e4df1ffbb7cbc55791b8991a822a5df'}
    assert m['provenance.yaml']['rows'] is None


# --- Tier 2: the derived truth is L23's anw ---------------------------------------

@needs_l23
def test_derived_truth_is_l23_anw_and_the_adapters_a_nw():
    from ocpy.hydrolight import loisel23

    from ioptics import datasets

    rta = _load('rta_add_anw')
    ds = loisel23.load_ds(4, 0)
    truth = rta.l23_anw_truth(4, 0, ds=ds)
    wave = np.arange(400.0, 751.0, 5.0)              # RT-A's window
    for obs in (0, 7, 1234, 3319):
        rows = pd.DataFrame({'dataset': 'L23', 'obs_id': obs, 'wavelength': wave})
        got = truth(rows)
        L = ds['Lambda'].values
        np.testing.assert_array_equal(
            got, ds['anw'].values[obs][np.isin(L, wave)].astype(float))
        raw = datasets.get_adapter('L23').load_obs(obs, X=4, Y=0)
        adapter = np.interp(wave, raw.wave, np.asarray(raw.truth['a_nw'], float))
        np.testing.assert_allclose(got, adapter, rtol=1e-6)

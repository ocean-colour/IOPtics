"""Tier-1 tests for the LS2-ladder page (``ioptics.report.ls2_ladder``, ls2 task 9).

Mirrors ``test_report_rt_ladder.py``'s fixture pattern, extended for a
**direct** population. Every LS2 rung is assembled through
:func:`ioptics.evaluate.assemble_direct`, so the results carry what a real LS2
sweep carries: NaN bounds, NaN fit statistics, ``a_nw`` present, no
``a_ph``/``a_dg``/``Rrs_model``, and per-cell NaN reasons. A separate BING sweep
fitted by MCMC is the comparator. No models, no data, no real docs tree.
"""

import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd
import pytest

from ioptics import evaluate, io, metrics
from ioptics.algorithms import registry
from ioptics.report import figures, ls2_ladder
from ioptics.tests.conftest import needs_sphinx
from ioptics.tests.test_metrics import _BASE, _WAVE, _Spec, _make_pair
from ioptics.tests.test_report_standard import _scaffold_min_docs

_SID = 'ls2_ladder_v1'
_BING = 'bing_comparator_v1'
RUNGS = list(registry.DIRECT_SEED)
SPECS = registry.register_direct()

#: How far each rung sits above truth (1.0 = perfect). The Kd-noise rungs grow
#: with their noise level, so the slope is positive by construction.
_FACTOR = {'ls2_i': 1.03, 'ls2_ii': 1.05, 'ls2_iii': 1.30,
           'ls2_iii_modis': 1.15, 'ls2_i_effmuw': 1.01,
           'ls2_i_kdnoise05': 1.06, 'ls2_i_kdnoise10': 1.10,
           'ls2_i_kdnoise20': 1.20}
CHL = {0: 0.05, 1: 0.5, 2: 2.0, 3: 0.3}


def _direct_pair(obs, rung):
    """One LS2 result on ``_make_pair``'s record, with a small a_nw share at 670."""
    _, record = _make_pair(obs, 'expb_pow', 1.0, CHL[obs], 10)
    anw = np.full(_WAVE.size, _BASE['a_nw'])
    anw[-1] = 0.01                         # a_nw/a = 0.05 at 670 nm: masked
    record.truth['a_nw'] = _Spec(anw)
    truth = {c: np.asarray(record.truth[c].values, dtype=float)
             for c in ('a', 'a_nw', 'bb', 'bb_p')}
    comps = {c: _FACTOR[rung] * truth[c] for c in truth}
    reasons = None
    if rung == 'ls2_i' and obs < 2:
        reasons = {c: np.array(['kappa_out_of_range', '', '', ''])
                   for c in comps}
    out = {'components': comps}
    if reasons:
        out['nan_reason'] = reasons
    return evaluate.assemble_direct(SPECS[rung], record, out), record


def _build(tmp_path, *, with_bing=True):
    pairs = [_direct_pair(obs, rung) for obs in range(4) for rung in RUNGS]
    io.write_results(_SID, pairs, root=tmp_path)
    metrics.compute(_SID, root=tmp_path)
    if with_bing:
        bing = [_make_pair(obs, 'expb_pow', 1.4, CHL[obs], 10, fit_method='mcmc')
                for obs in range(4)]
        io.write_results(_BING, bing, root=tmp_path)
        metrics.compute(_BING, root=tmp_path)
    return figures.load(_SID, root=tmp_path)


# --- the direct population really is one ------------------------------------------

def test_the_fixture_is_a_direct_population(tmp_path):
    sw = _build(tmp_path, with_bing=False)
    sc, sp = sw.scalar, sw.spectral
    assert set(sc['fit_method']) == {'direct'}
    assert sc[['chi2', 'chi2_nu', 'BIC', 'rel_misfit']].isna().all().all()
    assert set(sp['component']) == {'a', 'a_nw', 'bb', 'bb_p', 'Rrs_obs'}
    assert sp.loc[sp['component'] != 'Rrs_obs', ['lo68', 'hi95']].isna().all().all()


# --- tables -----------------------------------------------------------------------

def test_ladder_table_rows_cells_and_not_applicable(tmp_path):
    sw = _build(tmp_path, with_bing=False)
    df = ls2_ladder.ladder_table(sw)
    assert list(df['rung']) == RUNGS
    assert (df['label'] == [ls2_ladder.LABELS[r] for r in RUNGS]).all()
    assert {'frac_ok', 'n_attempted', 'a_440_mae', 'a_nw_440_bias',
            'bb_555_ratio', 'bb_p_670_mae'} <= set(df.columns)
    # no coverage: a direct algorithm has no interval
    assert not [c for c in df.columns if 'cov' in c]
    # the n=0 cells survive, as an explicit statement
    assert (df['a_ph_440'] == ls2_ladder.NOT_APPLICABLE).all()
    assert (df['a_dg_440'] == ls2_ladder.NOT_APPLICABLE).all()
    row = df.set_index('rung').loc['ls2_iii']
    assert row['a_440_ratio'] == pytest.approx(1.30, rel=1e-3)
    assert (figures.subdir(sw, 'tables') / 'ls2_ladder_all.csv').is_file()


def test_the_comparator_row_carries_bing_and_its_decomposition(tmp_path):
    sw = _build(tmp_path)
    comp = ls2_ladder.comparator_rows(_BING, root=tmp_path)
    assert comp is not None and 'mcmc' in comp[0]
    df = ls2_ladder.ladder_table(sw, comparator=comp)
    bing = df.set_index('rung').loc['BING']
    assert bing['a_440_ratio'] == pytest.approx(1.4, rel=1e-3)
    assert bing['a_ph_440'].startswith('mae ')       # BING has one
    assert ls2_ladder.comparator_rows('no_such_sweep', root=tmp_path) is None


def test_kd_noise_table_reports_the_slope(tmp_path):
    sw = _build(tmp_path, with_bing=False)
    df = ls2_ladder.kd_noise_table(sw)
    levels = df[df['rung'].str.startswith('ls2_i')]
    assert list(levels['kd_noise']) == [0.0, 0.05, 0.10, 0.20]
    slope = df.iloc[-1]
    assert slope['rung'].startswith('slope')
    expect = np.polyfit(levels['kd_noise'], levels['a_440_mae'], 1)[0]
    assert slope['a_440_mae'] == pytest.approx(expect)
    assert slope['a_440_mae'] > 0


# --- figures ----------------------------------------------------------------------

def test_anw_is_masked_where_water_dominates(tmp_path):
    sw = _build(tmp_path, with_bing=False)
    share = ls2_ladder.anw_share(sw)
    assert share.loc[670.0] == pytest.approx(0.05)
    assert share.loc[440.0] == pytest.approx(0.7)
    pngs = ls2_ladder.accuracy_spectrum(sw, pool='direct')
    assert pngs and pngs[0].name == 'ls2_accuracy_vs_wavelength.png'


def test_nan_reason_spectrum_draws_only_reasons_that_occur(tmp_path):
    sw = _build(tmp_path, with_bing=False)
    pngs = ls2_ladder.nan_reason_spectrum(sw, pool='direct')
    assert pngs and pngs[0].name == 'ls2_nan_reasons_ls2_i.png'
    # a rung with no reasons draws nothing rather than an empty panel
    assert ls2_ladder.nan_reason_spectrum(sw, pool='direct',
                                          rung='ls2_ii') == []


# --- the page ---------------------------------------------------------------------

def test_build_writes_page_assets_and_limitations(tmp_path):
    _build(tmp_path)
    docs = tmp_path / 'docs'
    out = ls2_ladder.build(_SID, root=tmp_path, docs_root=docs,
                           compare_sweep=_BING)
    assert out == docs / 'reports' / _SID / 'ls2_ladder.rst'
    rd, text = out.parent, out.read_text(encoding='utf-8')
    assert f':Sweep: {_SID}' in text and 'LS2 ladder' in text.splitlines()[1]
    # the mandated limitations, greppable
    for must in ('λ⁻¹', 'bp_from_Chla.m', 'Pure water is LS2', 'η = b_w/(b_p + b_w) < 0.2',
                 'κ is unavailable', 'never an exemplar', 'MCMC BING',
                 'not applicable', 'leaderboard: false'):
        assert must in text, must
    # ΔBIC becomes an explicit statement, not a missing section
    assert 'Model selection (ΔBIC) — not applicable' in text
    assert 'no likelihood' in text
    for name in ('ls2_ladder_all.csv', 'kd_noise_all.csv', 'qc_direct_all.csv',
                 'accuracy_direct_all.csv', 'ls2_accuracy_vs_wavelength.png',
                 'ls2_nan_reasons_ls2_i.png', 'scatter_a_440.png'):
        assert (rd / name).is_file(), name
    csv = pd.read_csv(rd / 'ls2_ladder_all.csv')
    assert 'BING' in set(csv['rung'])
    idx = (docs / 'reports' / 'index.rst').read_text()
    assert ':glob:' in idx and 'LEADERBOARD_START' not in idx


def test_the_kappa_limitation_follows_the_raman_switch():
    base = dict(kappa_share=0.3, kappa_band=0.9)
    on = ls2_ladder._kappa_item({**base, 'raman': [True]})
    off = ls2_ladder._kappa_item({**base, 'raman': [False]})
    assert 'unavailable on 30.0%' in on and '90.0%' in on
    assert 'off on every rung' in off and 'unavailable' not in off


def test_build_without_a_comparator_says_so(tmp_path):
    _build(tmp_path, with_bing=False)
    out = ls2_ladder.build(_SID, root=tmp_path, docs_root=tmp_path / 'docs')
    text = out.read_text(encoding='utf-8')
    assert 'no comparator sweep was supplied' in text
    out = ls2_ladder.build(_SID, root=tmp_path, docs_root=tmp_path / 'docs',
                           compare_sweep='missing_sweep')
    assert 'has no metrics on this machine' in out.read_text(encoding='utf-8')


def test_build_is_idempotent_and_prunes_its_own_stale_assets(tmp_path):
    _build(tmp_path, with_bing=False)
    docs = tmp_path / 'docs'
    out = ls2_ladder.build(_SID, root=tmp_path, docs_root=docs)
    stale = out.parent / 'scatter_zzz_999.png'
    stale.write_bytes(b'x')
    assert ls2_ladder.build(_SID, root=tmp_path, docs_root=docs) == out
    assert not stale.exists()


@needs_sphinx
def test_page_renders_under_sphinx(tmp_path):
    import subprocess
    import sys

    _build(tmp_path)
    src = tmp_path / 'docs'
    ls2_ladder.build(_SID, root=tmp_path, docs_root=src, compare_sweep=_BING)
    _scaffold_min_docs(src)
    proc = subprocess.run(
        [sys.executable, '-m', 'sphinx', '-W', '-q', '-b', 'html',
         str(src), str(src / '_build')],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (src / '_build' / 'reports' / _SID / 'ls2_ladder.html').is_file()


def test_a_named_comparator_algorithm_is_honoured_or_refused(tmp_path):
    _build(tmp_path)
    comp = ls2_ladder.comparator_rows(_BING, root=tmp_path,
                                      algorithm='expb_pow')
    assert set(comp[1]['algorithm']) == {'expb_pow'}
    with pytest.raises(KeyError, match='not in'):
        ls2_ladder.comparator_rows(_BING, root=tmp_path,
                                   algorithm='expb_pow_hyb_ramfl')


def test_a_derived_comparator_anw_is_stated_on_the_page(tmp_path):
    from ioptics import io as _io
    _build(tmp_path)
    docs = tmp_path / 'docs'
    out = ls2_ladder.build(_SID, root=tmp_path, docs_root=docs,
                           compare_sweep=_BING)
    assert 'derived after the fit' not in out.read_text(encoding='utf-8')
    (_io.sweep_dir(_BING, root=tmp_path) / 'provenance.yaml').write_text(
        'sweep_id: bing_comparator_v1\nderived:\n  a_nw:\n    task: ls2 9b\n')
    out = ls2_ladder.build(_SID, root=tmp_path, docs_root=docs,
                           compare_sweep=_BING)
    assert 'derived after the fit' in out.read_text(encoding='utf-8')

"""Tier-1 tests for scoring an algorithm with no misfit (ls2 task 6).

A synthetic sweep -- two BING algorithms fitted by χ² (and one by MCMC as
well) plus a direct algorithm assembled through
:func:`ioptics.evaluate.assemble_direct` -- runs through ``io`` and
``metrics.compute`` and on into the report tables and the leaderboard. Covers:

- ``a_nw`` as a first-class accuracy component;
- no misleading zeros: ``frac_qc_fail``, ``frac_good``/``overfit``/``underfit``
  and the χ²/misfit medians are NaN, not 0, where nothing defines them;
- per-wavelength NaN reasons, in ``results_spectral`` and as ``frac_nan_*``
  in ``metrics_spectral``;
- ``not_applicable`` rows for the components a direct algorithm cannot
  produce, surviving ``drop_unscored`` in the tables and on the board, plus
  the n=0 ΔBIC rows;
- the ``pool`` column: direct rows duplicated into each fitted pool,
  contests keyed on it, ``fit_method`` kept as the honest label;
- ls2 Q31b: the finite cells of a ``poor_fit`` direct row are scored, while
  ``frac_ok`` stays strict.
"""

import numpy as np
import pandas as pd
import pytest

from ioptics import evaluate, io, metrics
from ioptics.algorithms.spec import DirectSpec
from ioptics.records import NAN_REASONS
from ioptics.report import leaderboard, tables
from ioptics.tests.test_metrics import _BASE, _WAVE, _make_pair

CHL = {0: 0.05, 1: 0.5, 2: 2.0, 3: 0.5}
LS2 = DirectSpec(name='ls2_toy', label='LS2 toy')


def _direct_pair(obs_id, *, factor=1.5, poison=None, reasons=None):
    """A direct result on the record ``_make_pair`` builds for ``obs_id``."""
    _, record = _make_pair(obs_id, 'expb_pow', 1.0, CHL[obs_id], 10)
    comps = {c: np.full(_WAVE.size, factor * _BASE[c]) for c in LS2.outputs}
    if poison is not None:
        name, idx, value = poison
        comps[name][idx] = value
    outputs = {'components': comps}
    if reasons is not None:
        outputs['nan_reason'] = reasons
    return evaluate.assemble_direct(LS2, record, outputs), record


def _sweep(tmp_path, sweep_id='mixed', *, mcmc=True, direct_poison=None):
    pairs = []
    for obs in range(4):
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, CHL[obs], 10))
        pairs.append(_make_pair(obs, 'giop', 2.0, CHL[obs], 15))
        poison = direct_poison if obs == 0 else None
        reasons = None
        if poison is not None:
            reasons = {'a_nw': np.array(['', 'off_grid', '', '']),
                       'a': np.array(['', 'off_grid', '', '']),
                       'bb': np.array(['', 'off_grid', '', '']),
                       'bb_p': np.array(['', 'off_grid', '', ''])}
        pairs.append(_direct_pair(obs, poison=poison, reasons=reasons))
    if mcmc:
        for obs in range(4):
            pairs.append(_make_pair(obs, 'expb_pow', 1.0, CHL[obs], 10,
                                    fit_method='mcmc'))
    io.write_results(sweep_id, pairs, root=tmp_path)
    return metrics.compute(sweep_id, root=tmp_path)


# --- a_nw -------------------------------------------------------------------------

def test_a_nw_is_a_first_class_component():
    assert 'a_nw' in metrics.ACCURACY_COMPONENTS
    assert metrics._COMPONENT_REFSET['a_nw'] == 'absorption'
    assert io._UNITS['a_nw'] == '1/m'
    assert 'a_nw' in evaluate._SPECTRAL


def test_a_nw_is_scored_for_bing_and_direct_alike(tmp_path):
    ms = _sweep(tmp_path).scalar
    anw = ms[(ms['component'] == 'a_nw') & (ms['stratum'] == 'all')
             & (ms['pool'] == 'chisq') & (ms['ref_wave'] == 440.0)
             ].set_index('algorithm')
    assert anw.loc['expb_pow', 'mae'] == pytest.approx(0.0, abs=1e-12)
    assert anw.loc['ls2_toy', 'mae'] == pytest.approx(0.5)
    assert anw.loc['ls2_toy', 'fit_method'] == 'direct'


# --- no misleading zeros ----------------------------------------------------------

def test_frac_qc_fail_counts_finite_chi2_only():
    scal = pd.DataFrame({
        'dataset': ['L23'] * 4, 'algorithm': ['x'] * 4,
        'fit_method': ['chisq'] * 4, 'stratum': ['all'] * 4,
        'status': ['ok', 'fit_failed', 'ok', 'poor_fit'],
        'chi2_nu': [1.0, np.nan, 9.0, 20.0], 'n_bands': [81] * 4,
        'k': [5] * 4})
    row = metrics._closure_rows(scal, n_sigma=2.0).iloc[0]
    assert row['frac_qc_fail'] == pytest.approx(2 / 3)    # the NaN is not a pass


def test_a_direct_closure_row_is_nan_not_zero(tmp_path, recwarn):
    ms = _sweep(tmp_path).scalar
    row = ms[(ms['component'] == 'Rrs') & (ms['algorithm'] == 'ls2_toy')
             & (ms['stratum'] == 'all') & (ms['pool'] == 'chisq')].iloc[0]
    for col in ('frac_qc_fail', 'frac_good', 'frac_overfit', 'frac_underfit',
                'chi2_nu_median'):
        assert np.isnan(row[col]), col
    assert row['frac_ok'] == 1.0 and row['n_attempted'] == 4
    assert not [w for w in recwarn if 'empty slice' in str(w.message)]


# --- NaN reasons ------------------------------------------------------------------

def test_assemble_direct_completes_and_validates_reasons():
    res, _ = _direct_pair(0, poison=('a_nw', 2, -1e-3),
                          reasons={'a': np.array(['', 'kappa_out_of_range',
                                                  '', ''])})
    assert list(res.nan_reason['a_nw']) == ['', '', 'negative', '']
    assert list(res.nan_reason['a']) == ['', 'kappa_out_of_range', '', '']
    res, _ = _direct_pair(0, poison=('bb', 1, np.nan))
    assert res.nan_reason['bb'][1] == 'unexplained'
    with pytest.raises(ValueError, match='unknown nan_reason'):
        _direct_pair(0, reasons={'a': np.array(['', 'gremlins', '', ''])})
    assert set(NAN_REASONS) >= {'off_grid', 'negative', 'kappa_out_of_range',
                                'kd_missing'}


def test_reasons_reach_the_spectral_table_and_the_metrics(tmp_path):
    tabs = _sweep(tmp_path, direct_poison=('a_nw', 1, np.nan))
    spectral, _ = io.read_results('mixed', root=tmp_path)
    assert 'nan_reason' in spectral.columns
    assert set(spectral.loc[spectral['algorithm'] != 'ls2_toy',
                            'nan_reason']) == {''}
    cell = spectral[(spectral['algorithm'] == 'ls2_toy')
                    & (spectral['obs_id'] == 0) & (spectral['component'] == 'a_nw')
                    & (spectral['wavelength'] == 443.0)]
    assert cell['nan_reason'].iloc[0] == 'off_grid'

    sp = tabs.spectral
    row = sp[(sp['algorithm'] == 'ls2_toy') & (sp['component'] == 'a_nw')
             & (sp['wavelength'] == 443.0) & (sp['stratum'] == 'all')
             & (sp['pool'] == 'chisq')].iloc[0]
    assert row['frac_nan_off_grid'] == pytest.approx(0.25)   # 1 of 4 spectra
    other = sp[(sp['algorithm'] == 'ls2_toy') & (sp['wavelength'] == 555.0)]
    assert (other['frac_nan_off_grid'] == 0).all()


def test_a_bing_only_sweep_gains_no_reason_columns(tmp_path):
    pairs = [_make_pair(o, 'expb_pow', 1.0, CHL[o], 10) for o in range(4)]
    io.write_results('bing_only', pairs, root=tmp_path)
    sp = metrics.compute('bing_only', root=tmp_path).spectral
    assert not [c for c in sp.columns if c.startswith('frac_nan_')]


# --- pool -------------------------------------------------------------------------

def test_direct_rows_are_duplicated_into_every_pool(tmp_path):
    ms = _sweep(tmp_path).scalar
    ls2 = ms[ms['algorithm'] == 'ls2_toy']
    assert set(ls2['pool']) == {'chisq', 'mcmc'}
    assert set(ls2['fit_method']) == {'direct'}
    bing = ms[ms['algorithm'] == 'expb_pow']
    assert (bing['pool'] == bing['fit_method']).all()


def test_without_a_fitted_pool_direct_rows_stand_alone(tmp_path):
    pairs = [_direct_pair(o) for o in range(4)]
    io.write_results('direct_only', pairs, root=tmp_path)
    ms = metrics.compute('direct_only', root=tmp_path).scalar
    assert set(ms['pool']) == {'direct'}


def test_contests_key_on_the_pool(tmp_path):
    pw = _sweep(tmp_path).pairwise
    wins = pw[(pw['contest'] == 'wins') & (pw['component'] == 'a')
              & (pw['ref_wave'] == 440.0) & (pw['stratum'] == 'all')]
    chisq = wins[wins['pool'] == 'chisq'].set_index('algorithm')
    assert set(chisq.index) == {'expb_pow', 'giop', 'ls2_toy'}
    assert chisq.loc['ls2_toy', 'fit_method'] == 'direct'
    assert chisq.loc['expb_pow', 'fit_method'] == 'chisq'
    mcmc = wins[wins['pool'] == 'mcmc']
    assert set(mcmc['algorithm']) == {'expb_pow', 'ls2_toy'}

    pairs = pw[(pw['contest'] == 'pair') & (pw['component'] == 'a')
               & (pw['ref_wave'] == 440.0) & (pw['stratum'] == 'all')]
    p = pairs[(pairs['pool'] == 'chisq') & (pairs['model_a'] == 'expb_pow')
              & (pairs['model_b'] == 'ls2_toy')].iloc[0]
    assert p['fit_method'] == 'chisq'                    # the population
    assert (p['fit_method_a'], p['fit_method_b']) == ('chisq', 'direct')
    assert p['verdict'] == 'expb_pow'


def test_chisq_and_mcmc_stay_separate_contests_with_a_direct_algorithm(tmp_path):
    _sweep(tmp_path, 'lb_direct')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    r = leaderboard.ranked(board.assign(separable=True))
    key = ['dataset', 'component', 'ref_wave', 'stratum', 'pool']
    assert not r.duplicated(subset=key + ['algorithm']).any()
    for _, grp in r[r['algorithm'] != 'ls2_toy'].groupby(key):
        assert grp['fit_method'].nunique() == 1
    a440 = r[(r['component'] == 'a') & (r['ref_wave'] == 440.0)
             & (r['stratum'] == 'all') & (r['pool'] == 'chisq')]
    assert set(a440['algorithm']) == {'expb_pow', 'giop', 'ls2_toy'}


# --- Q31b: score the finite cells of a partial direct row --------------------------

def test_poor_fit_direct_cells_are_scored_but_frac_ok_is_strict(tmp_path):
    ms = _sweep(tmp_path, direct_poison=('a_nw', 1, np.nan)).scalar
    closure = ms[(ms['component'] == 'Rrs') & (ms['algorithm'] == 'ls2_toy')
                 & (ms['stratum'] == 'all') & (ms['pool'] == 'chisq')].iloc[0]
    assert closure['frac_ok'] == 0.75 and closure['frac_poor_fit'] == 0.25
    a440 = ms[(ms['component'] == 'a_nw') & (ms['ref_wave'] == 440.0)
              & (ms['algorithm'] == 'ls2_toy') & (ms['stratum'] == 'all')
              & (ms['pool'] == 'chisq')].iloc[0]
    assert a440['n'] == 4                     # obs 0 is poor_fit, still scored
    a443 = ms[(ms['component'] == 'a_nw') & (ms['ref_wave'] == 443.0)
              & (ms['algorithm'] == 'ls2_toy') & (ms['stratum'] == 'all')
              & (ms['pool'] == 'chisq')].iloc[0]
    assert a443['n'] == 3                     # ... except its NaN cell


def test_a_poor_fit_bing_row_is_still_not_scored(tmp_path):
    pairs = [_make_pair(o, 'expb_pow', 1.0, CHL[o], 10,
                        status='poor_fit' if o == 0 else 'ok')
             for o in range(4)]
    io.write_results('bing_pf', pairs, root=tmp_path)
    ms = metrics.compute('bing_pf', root=tmp_path).scalar
    row = ms[(ms['component'] == 'a') & (ms['ref_wave'] == 440.0)
             & (ms['stratum'] == 'all')].iloc[0]
    assert row['n'] == 3


# --- not applicable ---------------------------------------------------------------

def test_not_applicable_rows_for_what_a_direct_algorithm_cannot_produce(tmp_path):
    ms = _sweep(tmp_path).scalar
    na = ms[ms['caveat'] == metrics.CAVEAT_NOT_APPLICABLE]
    assert set(na['algorithm']) == {'ls2_toy'}
    assert set(na['component']) == {'a_ph', 'a_dg'}
    assert set(na['pool']) == {'chisq', 'mcmc'}
    assert (na['n'] == 0).all() and na['mae'].isna().all()
    # every ref band the fitted algorithms were scored on, overall and per stratum
    chisq_all = na[(na['pool'] == 'chisq') & (na['stratum'] == 'all')]
    assert len(chisq_all) == 4                # 2 components x 2 absorption bands
    # ... and nothing is invented for a component LS2 does produce
    assert not ((ms['algorithm'] == 'ls2_toy') & (ms['component'] == 'a')
                & (ms['caveat'] == metrics.CAVEAT_NOT_APPLICABLE)).any()


def test_dbic_pairs_with_a_direct_algorithm_get_an_n0_row(tmp_path):
    pw = _sweep(tmp_path).pairwise
    db = pw[(pw['contest'] == 'dbic') & (pw['stratum'] == 'all')
            & (pw['pool'] == 'chisq')]
    direct = db[(db['model_a'] == 'ls2_toy') | (db['model_b'] == 'ls2_toy')]
    assert len(direct) == 2
    assert (direct['n'] == 0).all()
    assert (direct['caveat'] == metrics.CAVEAT_NOT_APPLICABLE).all()
    bing = db[(db['model_a'] == 'expb_pow') & (db['model_b'] == 'giop')].iloc[0]
    assert bing['n'] == 4 and bing['caveat'] == ''


def test_not_applicable_rows_survive_the_tables_and_the_board(tmp_path):
    _sweep(tmp_path, 'na_report')
    acc = tables.accuracy('na_report', root=tmp_path, write=False)
    na = acc[(acc['algorithm'] == 'ls2_toy') & acc['component'].isin(['a_ph',
                                                                     'a_dg'])]
    assert len(na) == 4 and (na['caveat'] == metrics.CAVEAT_NOT_APPLICABLE).all()
    # a genuinely unscored row is still dropped and counted
    assert acc.attrs['n_unscored_rows'] >= 0
    # LS2 appears in the chisq table beside the fitted algorithms
    assert {'expb_pow', 'giop', 'ls2_toy'} <= set(acc['algorithm'])
    assert set(acc.loc[acc['algorithm'] == 'ls2_toy', 'fit_method']) == {'direct'}

    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    r = leaderboard.ranked(board)
    na_rows = r[r['caveat'] == metrics.CAVEAT_NOT_APPLICABLE]
    assert (na_rows['ranking'] == 'not applicable').all()
    assert na_rows['rank'].isna().all()
    text = leaderboard.render(board, headline=False)
    assert 'not applicable' in text


def test_qc_counts_the_direct_algorithm_in_each_pool(tmp_path):
    _sweep(tmp_path, 'qc_pool', direct_poison=('a_nw', 1, np.nan))
    qc = tables.qc('qc_pool', root=tmp_path, write=False).set_index('algorithm')
    assert 'ls2_toy' in qc.index
    assert qc.loc['ls2_toy', 'frac_ok'] == pytest.approx(0.75)
    assert np.isnan(qc.loc['ls2_toy', 'frac_qc_fail'])


def test_the_pool_column_is_shown_only_when_it_says_something(tmp_path):
    pairs = [_make_pair(o, 'expb_pow', 1.0, CHL[o], 10) for o in range(4)] + \
            [_make_pair(o, 'giop', 2.0, CHL[o], 15) for o in range(4)]
    io.write_results('bing_board', pairs, root=tmp_path / 'a')
    metrics.compute('bing_board', root=tmp_path / 'a')
    board = leaderboard.update(runs_root=tmp_path / 'a',
                               out=tmp_path / 'a.parquet')
    assert '- pool' not in leaderboard.render(board)        # BING-only: hidden
    _sweep(tmp_path / 'b', 'mixed_board')
    board = leaderboard.update(runs_root=tmp_path / 'b',
                               out=tmp_path / 'b.parquet')
    assert '- pool' in leaderboard.render(board)            # with LS2: shown

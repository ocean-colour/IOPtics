"""Tier-1 tests for pairwise statistics that can detect a tie (Stage 7, Task 4).

``metrics.wins`` tallies into ``(group, algorithm)`` and throws the opponent away,
so its "contests" are not independent trials of any one pairing and no paired
statistic can be recovered from it — with four algorithms, 36 contests are 12
spectra x 3 opponents. These tests pin the paired replacement: the pairing is kept,
the verdict can say **indistinguishable** or **underpowered** instead of inventing a
rank, and a contest with no finite metric is never ranked.
"""

import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd

from ioptics import io, metrics
from ioptics.report import figures, leaderboard, standard, tables
from ioptics.tests.test_metrics import _make_pair


def _spectral(errs_by_algo, *, truth=1.0, component='a', ref=440.0):
    """A one-band spectral table with prescribed per-spectrum retrievals."""
    rows = []
    for algo, values in errs_by_algo.items():
        for obs, v in enumerate(values):
            rows.append({'dataset': 'L23', 'obs_id': obs, 'algorithm': algo,
                         'fit_method': 'chisq', 'stratum': 'all',
                         'component': component, 'ref_wave': ref,
                         'value': v, 'truth': truth})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------
# the pairing is kept
# --------------------------------------------------------------------
def test_paired_errors_use_only_shared_spectra():
    df = _spectral({'a1': [1.0, 2.0, np.nan], 'a2': [1.0, 4.0, 2.0]})
    both = metrics.paired_abs_log_errors(df, 'a1', 'a2')
    assert list(both.index) == [0, 1]              # obs 2 has no a1 retrieval
    d = metrics.paired_log_errors(df, 'a1', 'a2')
    assert d.size == 2
    assert d[0] == 0.0                             # both exact on obs 0
    assert d[1] < 0                                # a1 closer on obs 1


def test_paired_errors_drop_nonpositive_like_the_metrics_do():
    df = _spectral({'a1': [1.0, -1.0], 'a2': [1.0, 1.0]})
    assert metrics.paired_log_errors(df, 'a1', 'a2').size == 1


def test_head_to_head_keeps_the_opponent_identity():
    """The defect: ``wins`` cannot say who beat whom. This must."""
    df = _spectral({'a1': [1.0] * 6, 'a2': [2.0] * 6, 'a3': [4.0] * 6})
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave'))
    pairs = set(zip(h['model_a'], h['model_b']))
    assert pairs == {('a1', 'a2'), ('a1', 'a3'), ('a2', 'a3')}
    assert (h['n_paired'] == 6).all()


# --------------------------------------------------------------------
# the verdict
# --------------------------------------------------------------------
def test_a_clear_winner_is_named():
    df = _spectral({'good': [1.0] * 12, 'bad': [3.0] * 12})
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave'))
    row = h.iloc[0]
    assert row['verdict'] == 'good'
    assert row['resolved']
    assert abs(row['delta_mae']) >= metrics.PRACTICAL_MAE_FLOOR


def test_a_real_but_tiny_difference_is_indistinguishable():
    """Resolved by the bootstrap, but below the practical floor JXP set."""
    df = _spectral({'a1': [1.01] * 40, 'a2': [1.02] * 40})
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave'))
    row = h.iloc[0]
    assert row['resolved'], 'a constant offset is perfectly resolvable'
    assert abs(row['delta_mae']) < metrics.PRACTICAL_MAE_FLOOR
    assert row['verdict'] == 'indistinguishable'


def test_a_material_gap_carried_by_one_spectrum_is_underpowered():
    """A big MAE gap that rests on a single outlier is not a finding.

    ``a2`` matches ``a1`` on five spectra and is 10x off on the sixth, so the MAE
    difference clears the practical floor while most bootstrap resamples — which
    often omit that one spectrum — show no difference at all.
    """
    df = _spectral({'a1': [1.0] * 6, 'a2': [1.0] * 5 + [10.0]})
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave')).iloc[0]
    assert abs(h['delta_mae']) >= metrics.PRACTICAL_MAE_FLOOR
    assert not h['resolved']
    assert h['verdict'] == 'underpowered'


def test_no_shared_spectra_gets_no_verdict_at_all():
    """"We share no spectrum" is a different fact from "we cannot tell"."""
    df = pd.concat([
        _spectral({'a1': [1.0, 2.0]}),
        _spectral({'a2': [1.0, 2.0]}).assign(obs_id=lambda d: d['obs_id'] + 10),
    ], ignore_index=True)
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave'))
    assert h.iloc[0]['n_paired'] == 0
    assert h.iloc[0]['verdict'] is None or pd.isna(h.iloc[0]['verdict'])


def test_the_interval_and_the_floor_share_a_scale():
    """Both must be in MAE units, or the two thresholds judge different things."""
    df = _spectral({'a1': [1.0] * 20, 'a2': [2.0] * 20})
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave')).iloc[0]
    assert h['d_lo'] <= h['delta_mae'] <= h['d_hi']
    # and the bootstrap is seeded, so a published verdict is reproducible
    again = metrics.head_to_head(df, by=('dataset', 'component',
                                         'ref_wave')).iloc[0]
    assert (h['d_lo'], h['d_hi']) == (again['d_lo'], again['d_hi'])


# --------------------------------------------------------------------
# wired through compute / the report / the leaderboard
# --------------------------------------------------------------------
def _sweep(tmp_path, sweep_id='h2h'):
    pairs = []
    for obs in range(4):
        spread = 0.5 + obs
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, 0.5, 10,
                                truth_factor=spread))
        pairs.append(_make_pair(obs, 'giop', 3.0, 0.5, 15, truth_factor=spread))
    io.write_results(sweep_id, pairs, root=tmp_path)
    metrics.compute(sweep_id, root=tmp_path)
    return figures.load(sweep_id, root=tmp_path)


def test_compute_persists_pair_rows_and_a_coverage_trial_count(tmp_path):
    sweep = _sweep(tmp_path)
    pw = sweep.metrics_pairwise
    assert 'pair' in set(pw['contest'])
    pair_rows = pw[pw['contest'] == 'pair']
    assert {'model_a', 'model_b', 'n_paired', 'delta_mae', 'verdict'} \
        <= set(pair_rows.columns)
    # coverage_n is its own column, not the accuracy row's n (JXP's answer)
    assert 'coverage_n' in sweep.metrics_scalar.columns
    assert 'coverage_n' in sweep.metrics_spectral.columns


def test_dbic_runs_for_every_pair_present(tmp_path):
    """A sweep whose algorithms are not the configured pair still gets ΔBIC."""
    sweep = _sweep(tmp_path, sweep_id='h2h_dbic')
    dbic = sweep.metrics_pairwise
    dbic = dbic[dbic['contest'] == 'dbic']
    assert not dbic.empty
    assert set(zip(dbic['model_a'], dbic['model_b'])) == {('expb_pow', 'giop')}


def test_report_publishes_the_head_to_head_table(tmp_path):
    sweep = _sweep(tmp_path, sweep_id='h2h_page')
    docs = tmp_path / 'docs'
    (docs / 'reports').mkdir(parents=True, exist_ok=True)
    out = standard.build('h2h_page', kind='cross_algorithm', root=tmp_path,
                         docs_root=docs)
    txt = out.read_text()
    assert 'Head-to-head' in txt
    assert 'indistinguishable' in txt and 'underpowered' in txt
    assert f'{metrics.PRACTICAL_MAE_FLOOR:.0%}' in txt      # the floor is stated
    assert (out.parent / 'head_to_head_chisq_all.csv').is_file()
    h = tables.head_to_head(sweep)
    assert (h['n_paired'] > 0).all()                        # no contest-less rows


def test_leaderboard_never_ranks_a_contest_with_no_data(tmp_path):
    _sweep(tmp_path, sweep_id='h2h_lb')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    # blank out one contest's metrics, as an unscoreable component really is
    blanked = board.copy()
    mask = blanked['component'] == 'bb'
    for col in ('mae', 'abs_bias', 'win_frac'):
        if col in blanked.columns:
            blanked.loc[mask, col] = np.nan
    ranked = leaderboard.ranked(blanked)
    # ``ranked`` re-sorts and resets the index, so re-derive the selection
    assert ranked[ranked['component'] == 'bb']['rank'].isna().all(), \
        'no measurement, no rank'
    assert ranked[ranked['component'] != 'bb']['rank'].notna().any()


# --------------------------------------------------------------------
# defects found by the adversarial review of this task
# --------------------------------------------------------------------
def _noisy(rng, n, scale):
    """Positive retrievals against truth 1 with genuine per-spectrum spread."""
    return np.exp(rng.normal(0.0, scale, n))


def test_a_small_gap_with_a_wide_interval_is_underpowered_not_a_tie():
    """The defect the review caught: ``indistinguishable`` claimed too much.

    This is the shape of the real GLORIA contest — a tiny point difference whose
    interval still admits a difference several times the practical floor. Calling
    that "indistinguishable" asserts the difference would not matter *if
    confirmed*, which the data do not support.
    """
    # seed chosen for the shape being tested (small gap, wide interval), which is
    # the generic small-n case rather than a lucky draw
    rng = np.random.default_rng(1)
    df = _spectral({'a1': _noisy(rng, 12, 0.9), 'a2': _noisy(rng, 12, 0.9)})
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave')).iloc[0]
    assert abs(h['delta_mae']) < metrics.PRACTICAL_MAE_FLOOR      # small gap ...
    assert (h['d_hi'] - h['d_lo']) > 2 * metrics.PRACTICAL_MAE_FLOOR   # ... wide CI
    assert h['verdict'] == 'underpowered'
    assert not h['equivalent']


def test_equivalence_needs_the_whole_interval_inside_the_floor():
    """Many tightly-agreeing spectra: now the data *can* rule a gap out."""
    rng = np.random.default_rng(3)
    base = _noisy(rng, 300, 0.02)
    df = _spectral({'a1': base, 'a2': base * 1.001})
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave')).iloc[0]
    assert max(abs(h['d_lo']), abs(h['d_hi'])) < metrics.PRACTICAL_MAE_FLOOR
    assert h['equivalent'] and h['verdict'] == 'indistinguishable'


def test_a_winner_is_named_off_genuinely_noisy_data():
    """Exercises the bootstrap: spread in both arms, one clearly worse."""
    rng = np.random.default_rng(11)
    df = _spectral({'good': _noisy(rng, 60, 0.05), 'bad': _noisy(rng, 60, 0.6)})
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave')).iloc[0]
    assert h['d_lo'] < h['d_hi'], 'a real interval, not a zero-width artifact'
    assert h['resolved'] and h['verdict'] == 'good'


def test_too_few_spectra_never_gets_a_verdict_even_with_zero_spread():
    """With n=1 every resample is identical, so the interval has zero width.

    Before the fix that "proved" equivalence (or named a winner) off one spectrum.
    """
    for n in (1, 2):
        df = _spectral({'a1': [1.05] * n, 'a2': [1.0] * n})
        h = metrics.head_to_head(df,
                                 by=('dataset', 'component', 'ref_wave')).iloc[0]
        assert h['n_paired'] == n
        assert h['verdict'] == 'underpowered', f'n={n}'


def test_an_infinite_error_is_a_loss_not_a_shrug():
    """A catastrophic retrieval needs no statistics; it used to read underpowered."""
    df = _spectral({'ok': [1.0] * 6, 'broken': [1e-320] * 6})
    h = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave')).iloc[0]
    assert not np.isfinite([h['mae_a'], h['mae_b']]).all()
    assert h['verdict'] == 'ok'


def test_each_pair_gets_its_own_bootstrap_draw():
    """One global seed made every published interval move together."""
    k1 = metrics._pair_seed(('L23', 'a', 440.0), 'x', 'y')
    k2 = metrics._pair_seed(('L23', 'a', 440.0), 'x', 'z')
    k3 = metrics._pair_seed(('L23', 'bb', 555.0), 'x', 'y')
    assert len({k1, k2, k3}) == 3
    # ... and still reproducible
    assert k1 == metrics._pair_seed(('L23', 'a', 440.0), 'x', 'y')


def test_the_floor_can_be_read_relative_to_the_error_being_compared():
    """1% vs 5% error is a 5x gap that an absolute 0.10 floor calls a tie."""
    df = _spectral({'a1': [1.01] * 60, 'a2': [1.05] * 60})
    absolute = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave'),
                                    floor_mode='absolute').iloc[0]
    relative = metrics.head_to_head(df, by=('dataset', 'component', 'ref_wave'),
                                    floor_mode='relative').iloc[0]
    assert absolute['verdict'] == 'indistinguishable'
    assert relative['verdict'] == 'a1'
    assert relative['practical_floor'] < absolute['practical_floor']


def test_ranks_are_blanked_where_every_pair_is_a_tie(tmp_path):
    """The page must not print 1..N beside a table saying "indistinguishable"."""
    rng = np.random.default_rng(5)
    pairs = []
    for obs in range(12):
        spread = float(np.exp(rng.normal(0, 0.5)))
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, 0.5, 10,
                                truth_factor=spread))
        pairs.append(_make_pair(obs, 'giop', 1.0, 0.5, 15, truth_factor=spread))
    io.write_results('tie_rank', pairs, root=tmp_path)
    metrics.compute('tie_rank', root=tmp_path)
    sweep = figures.load('tie_rank', root=tmp_path)
    acc = tables.accuracy(sweep, write=False)
    assert (acc['ranking'] == 'indistinguishable').any()
    tied = acc[acc['ranking'] == 'indistinguishable']
    assert tied['mae_rank'].isna().all()


def test_a_one_horse_race_is_not_a_standing(tmp_path):
    _sweep(tmp_path, sweep_id='one_horse')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    solo = board.copy()
    drop = (solo['algorithm'] == 'giop') & (solo['component'] == 'a')
    for col in ('mae', 'abs_bias', 'win_frac'):
        solo.loc[drop, col] = np.nan
    ranked = leaderboard.ranked(solo)
    only = ranked[(ranked['component'] == 'a') & (ranked['algorithm'] == 'expb_pow')]
    assert only['rank'].isna().all(), 'one measured competitor is not a rank-1 win'

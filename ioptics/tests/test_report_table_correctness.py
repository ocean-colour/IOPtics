"""Tier-1 tests for report-table correctness (Stage 7, Task 3).

Three defects are pinned here. The published tables **dropped ``dataset``** and
joined wins without it, so a multi-dataset sweep row-multiplied and handed one
dataset's win fraction to another's rows — and no column told the reader which
dataset a row described. Three different denominators all appeared as some flavour
of ``n`` (on the first GLORIA sweep: 12 surviving pairs, 21 scored spectra, 100
attempted). And ``coverage68/95`` were printed beside metrics whose perfect value is
0, under prose claiming "0 = perfect", when a calibrated coverage is 0.68 / 0.95.
"""

import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd

from ioptics import io, metrics
from ioptics.report import figures, rst, standard, tables
from ioptics.tests.test_metrics import _make_pair


def _two_dataset_sweep(tmp_path, sweep_id='tab_two'):
    """L23 (expb_pow exact) + PANGAEA (giop exact) — the winner flips per dataset.

    So a row that carries the *other* dataset's ``win_frac`` is unmistakable.
    """
    pairs = []
    for obs in range(3):
        spread = 0.5 + obs
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, 0.5, 10, dataset='L23',
                                truth_factor=spread))
        pairs.append(_make_pair(obs, 'giop', 2.0, 0.5, 15, dataset='L23',
                                truth_factor=spread))
        pairs.append(_make_pair(obs, 'expb_pow', 2.0, 0.5, 10, dataset='PANGAEA',
                                truth_factor=spread))
        pairs.append(_make_pair(obs, 'giop', 1.0, 0.5, 15, dataset='PANGAEA',
                                truth_factor=spread))
    io.write_results(sweep_id, pairs, root=tmp_path)
    metrics.compute(sweep_id, root=tmp_path)
    return figures.load(sweep_id, root=tmp_path)


# --------------------------------------------------------------------
# dataset-aware joins
# --------------------------------------------------------------------
def test_accuracy_is_keyed_by_dataset(tmp_path):
    sweep = _two_dataset_sweep(tmp_path)
    acc = tables.accuracy(sweep, write=False)
    assert 'dataset' in acc.columns, 'a row must say which dataset it describes'
    # exactly one row per (dataset, algorithm, component, ref_wave) — no
    # row-multiplication from a dataset-blind merge
    key = ['dataset', 'algorithm', 'component', 'ref_wave']
    assert not acc.duplicated(subset=key).any()
    assert set(acc['dataset']) == {'L23', 'PANGAEA'}


def test_wins_are_not_cross_assigned_between_datasets(tmp_path):
    """The regression test: the winner flips per dataset, so a swap is visible."""
    sweep = _two_dataset_sweep(tmp_path)
    acc = tables.accuracy(sweep, write=False)
    a440 = acc[(acc['component'] == 'a') & (acc['ref_wave'] == 440)]
    got = a440.set_index(['dataset', 'algorithm'])['win_frac']
    assert got[('L23', 'expb_pow')] == 1.0          # exact on L23
    assert got[('L23', 'giop')] == 0.0
    assert got[('PANGAEA', 'giop')] == 1.0          # exact on PANGAEA
    assert got[('PANGAEA', 'expb_pow')] == 0.0


def test_qc_is_per_dataset_and_algorithm(tmp_path):
    sweep = _two_dataset_sweep(tmp_path)
    q = tables.qc(sweep, write=False)
    assert 'dataset' in q.columns
    assert len(q) == 4                               # 2 datasets x 2 algorithms
    assert not q.duplicated(subset=['dataset', 'algorithm']).any()


# --------------------------------------------------------------------
# honest denominators
# --------------------------------------------------------------------
def test_the_three_denominators_are_named_apart(tmp_path):
    sweep = _two_dataset_sweep(tmp_path)
    acc = tables.accuracy(sweep, write=False)
    q = tables.qc(sweep, write=False)
    assert 'n_pairs' in acc.columns and 'n' not in acc.columns
    assert 'n_scored' in q.columns and 'n' not in q.columns
    assert 'n_attempted' in q.columns
    # and they are genuinely different questions, not aliases
    assert (q['n_attempted'] >= q['n_scored']).all()


# --------------------------------------------------------------------
# coverage against its nominal target
# --------------------------------------------------------------------
def test_coverage_is_flagged_against_nominal_not_against_zero(tmp_path):
    sweep = _two_dataset_sweep(tmp_path)
    acc = tables.accuracy(sweep, write=False)
    assert {'coverage68_verdict', 'coverage95_verdict'} <= set(acc.columns)
    a440 = acc[(acc['component'] == 'a') & (acc['ref_wave'] == 440)] \
        .set_index(['dataset', 'algorithm'])
    # the exact retrieval's bands contain truth -> not distinguishable from nominal
    assert a440.loc[('L23', 'expb_pow'), 'coverage68_verdict'] == 'consistent'
    # the 2x-high retrieval's bands never contain truth -> a real, directional miss
    assert a440.loc[('L23', 'giop'), 'coverage68'] == 0.0
    assert a440.loc[('L23', 'giop'), 'coverage68_verdict'] == 'over-confident'


def test_unscored_rows_are_dropped_and_counted(tmp_path):
    """A row with no pairs behind it is the table equivalent of a blank panel."""
    sweep = _two_dataset_sweep(tmp_path, sweep_id='tab_drop')
    ms = sweep.metrics_scalar.copy()
    # make bb unscoreable, as a dataset without bb truth would
    ms.loc[ms['component'] == 'bb', 'n'] = 0
    sweep = sweep._replace(metrics_scalar=ms)

    kept = tables.accuracy(sweep, write=False)
    assert 'bb' not in set(kept['component'])
    assert kept.attrs['n_unscored_rows'] > 0          # the page states this count
    assert (kept['n_pairs'] > 0).all()

    everything = tables.accuracy(sweep, write=False, drop_unscored=False)
    assert 'bb' in set(everything['component'])       # still available on request


def test_coverage_flag_is_na_when_nothing_was_scored():
    df = pd.DataFrame({'n': [0], 'coverage68': [np.nan], 'coverage95': [np.nan]})
    out = tables._coverage_flags(df)
    assert pd.isna(out['coverage68_verdict'].iloc[0])


def test_coverage_miss_needs_more_than_noise():
    """A thin contest is not accused of mis-calibration on noise alone."""
    thin = tables._coverage_flags(pd.DataFrame({'n': [4], 'coverage68': [0.5],
                                                'coverage95': [0.95]}))
    fat = tables._coverage_flags(pd.DataFrame({'n': [400], 'coverage68': [0.5],
                                               'coverage95': [0.95]}))
    assert thin['coverage68_verdict'].iloc[0] == 'consistent'   # 2 s.e. at n=4
    assert fat['coverage68_verdict'].iloc[0] == 'over-confident'   # not at n=400
    # direction matters: too-wide intervals are a different finding
    wide = tables._coverage_flags(pd.DataFrame({'n': [400],
                                               'coverage68': [0.99],
                                               'coverage95': [0.99]}))
    assert wide['coverage68_verdict'].iloc[0] == 'conservative'


# --------------------------------------------------------------------
# publishable formatting
# --------------------------------------------------------------------
def test_published_csv_is_readable(tmp_path):
    sweep = _two_dataset_sweep(tmp_path)
    tables.accuracy(sweep)
    path = figures.subdir(sweep, 'tables') / 'accuracy_chisq_all.csv'
    text = path.read_text()
    # no full-float64 tails, and bands/ranks are not "440.0" / "2.0"
    assert '0.09642020657366057' not in text
    assert ',440,' in text, 'the band must be published as an integer'
    assert ',440.0,' not in text
    for field in text.split():
        for token in field.split(','):
            if token.replace('.', '', 1).replace('-', '', 1).isdigit() \
                    and '.' in token:
                assert len(token.split('.')[1]) <= 4, token


def test_rst_blocks_are_accessible_and_sized():
    fb = rst.figure_block('scatter.png', 'a caption')
    assert ':alt: a caption' in fb                    # screen readers
    ct = rst.csv_table_block('accuracy.csv', 'Accuracy')
    assert ':widths: auto' in ct                      # stop the overflow


# --------------------------------------------------------------------
# the page's own prose
# --------------------------------------------------------------------
def test_page_states_each_metrics_perfect_value(tmp_path):
    sweep = _two_dataset_sweep(tmp_path, sweep_id='tab_prose')
    docs = tmp_path / 'docs'
    (docs / 'reports').mkdir(parents=True, exist_ok=True)
    out = standard.build('tab_prose', kind='cross_algorithm', root=tmp_path,
                         docs_root=docs)
    txt = out.read_text()
    # the old page-wide claim was false for coverage / median_ratio / win_frac
    assert 'All accuracy metrics are log-space / multiplicative (0 = perfect)' \
        not in txt
    assert 'Erickson' in txt and '0.109' in txt        # the named convention
    assert 'median_ratio' in txt and '0.5 = a tie' in txt
    assert 'nominal 0.68 / 0.95' in txt
    assert 'n_pairs' in txt and 'n_scored' in txt and 'n_attempted' in txt


def test_panels_are_totals_plus_the_best_decomposed():
    scored = [('a_ph', 440.0, 30), ('a', 440.0, 20), ('bb', 555.0, 18),
              ('a_dg', 440.0, 10), ('bb_p', 555.0, 5), ('a', 443.0, 4)]
    plan = standard._plan_panels(scored)
    assert [c for c, _, _ in plan] == ['a', 'bb', 'a_ph']
    assert ('a', 440.0, 20) in plan                   # best-covered band per comp
    # a decomposed-only sweep (GLORIA) still gets its panel
    assert standard._plan_panels([('a_dg', 440.0, 12)]) == [('a_dg', 440.0, 12)]
    assert standard._plan_panels([]) == []


# --------------------------------------------------------------------
# defects found by the adversarial review of this task
# --------------------------------------------------------------------
def test_publishable_never_truncates_a_fractional_band():
    """A 442.5 nm band centre must not be published as 442."""
    df = pd.DataFrame({'ref_match': [442.5, 440.0], 'mae': [0.1, 0.2]})
    out = tables._publishable(df)
    assert out['ref_match'].tolist() == [442.5, 440.0]


def test_publishable_survives_a_fractional_band_with_a_gap():
    """``astype('Int64')`` raises on non-integral values; it must not be reached."""
    df = pd.DataFrame({'ref_match': [442.5, np.nan], 'n_pairs': [3, np.nan]})
    out = tables._publishable(df)              # must not raise
    assert out['ref_match'].iloc[0] == 442.5
    assert out['n_pairs'].iloc[0] == 3         # integral column still tidied


def test_leaderboard_fold_is_dataset_aware(tmp_path):
    """The same cross-assignment defect, in the leaderboard rather than the table."""
    from ioptics.report import leaderboard

    _two_dataset_sweep(tmp_path, sweep_id='lb_two')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    key = ['dataset', 'algorithm', 'component', 'ref_wave', 'stratum']
    assert not board.duplicated(subset=key).any(), 'rows were multiplied'
    a440 = board[(board['component'] == 'a') & (board['ref_wave'] == 440)
                 & (board['stratum'] == 'all')].set_index(['dataset', 'algorithm'])
    assert a440.loc[('L23', 'expb_pow'), 'win_frac'] == 1.0
    assert a440.loc[('PANGAEA', 'expb_pow'), 'win_frac'] == 0.0


def test_a_surviving_figure_is_never_given_a_missing_ones_caption(tmp_path):
    """Captions match on file name, because a degenerate figure is not written.

    Pairing captions positionally would label a surviving Target diagram with the
    absent Taylor diagram's caption — and its alt text.
    """
    report_dir = tmp_path / 'rep'
    report_dir.mkdir()
    only_target = tmp_path / 'target_a_440.png'
    only_target.write_bytes(b'png')
    section = standard._fig_section(
        None, report_dir, 'Taylor & Target',
        [only_target],
        caption={'taylor': 'TAYLOR CAPTION', 'target': 'TARGET CAPTION'})
    assert 'TARGET CAPTION' in section
    assert 'TAYLOR CAPTION' not in section

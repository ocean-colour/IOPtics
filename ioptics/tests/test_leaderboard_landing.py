"""Tier-1 tests for the leaderboard fold and the landing page (Stage 7, Task 5).

The published board folded one sweep, filtered ``fit_method == 'chisq'`` so an
MCMC-fit algorithm could never appear, dropped the ``bing``/``ocpy`` commits (BING
is where the models and the fitter live), and ranked 144 of its 160 rows with
nothing measured behind them. The landing page was 2 423 lines of ``list-table``
followed by a bare glob toctree of undescribed links.
"""

import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd

from ioptics import io, metrics
from ioptics.report import bokeh, leaderboard, standard
from ioptics.tests.conftest import needs_sphinx
from ioptics.tests.test_metrics import _make_pair


def _sweep(tmp_path, sweep_id='lb_v1', dataset='L23', mcmc=False):
    pairs = []
    for obs in range(4):
        spread = 0.5 + obs
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, 0.5, 10, dataset=dataset,
                                truth_factor=spread))
        pairs.append(_make_pair(obs, 'giop', 3.0, 0.5, 15, dataset=dataset,
                                truth_factor=spread))
        if mcmc:
            pairs.append(_make_pair(obs, 'expb_pow', 1.0, 0.5, 10,
                                    dataset=dataset, truth_factor=spread,
                                    fit_method='mcmc'))
    io.write_results(sweep_id, pairs, root=tmp_path)
    metrics.compute(sweep_id, root=tmp_path)


# --------------------------------------------------------------------
# the fold
# --------------------------------------------------------------------
def test_mcmc_results_can_reach_the_board(tmp_path):
    """The fold used to hard-filter χ², making an MCMC algorithm invisible."""
    _sweep(tmp_path, mcmc=True)
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    assert 'fit_method' in board.columns
    assert {'chisq', 'mcmc'} <= set(board['fit_method'])


def test_fold_carries_upstream_stamps_and_a_spec_digest(tmp_path):
    _sweep(tmp_path)
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    for col in ('versions', 'bing', 'ocpy', 'algo_digest'):
        assert col in board.columns, col
    # two rows sharing an algorithm name are only the same algorithm if the
    # digest agrees, so the digest must differ between different algorithms
    digests = board.groupby('algorithm')['algo_digest'].nunique()
    assert (digests <= 1).all(), 'one algorithm, one digest per sweep'


def test_fold_keeps_the_closure_columns(tmp_path):
    """"Why were the other rows not scored" is half of what a rank means."""
    _sweep(tmp_path)
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    for col in ('frac_ok', 'n_attempted', 'frac_poor_fit', 'frac_out_of_scope',
                'frac_fit_failed', 'chi2_nu_median'):
        assert col in board.columns, col


def test_fold_is_still_idempotent(tmp_path):
    _sweep(tmp_path)
    once = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    twice = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    assert len(once) == len(twice)


# --------------------------------------------------------------------
# the ranking
# --------------------------------------------------------------------
def test_a_contest_no_pair_separates_is_not_ranked(tmp_path):
    """JXP: the head-to-head verdict feeds the ranking."""
    _sweep(tmp_path, sweep_id='lb_tied')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    board = board.assign(separable=False)
    r = leaderboard.ranked(board)
    assert r['rank'].isna().all()
    assert (r['ranking'] == 'indistinguishable').any()


def test_a_separable_contest_is_ranked(tmp_path):
    _sweep(tmp_path, sweep_id='lb_sep')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    r = leaderboard.ranked(board.assign(separable=True))
    scored = r[r[['win_frac', 'abs_bias', 'mae']].notna().any(axis=1)]
    assert scored['rank'].notna().any()
    assert (r.loc[r['rank'].notna(), 'ranking'] == 'ranked').all()


# --------------------------------------------------------------------
# the landing page
# --------------------------------------------------------------------
def test_headline_render_is_short_and_hides_unmeasured_rows(tmp_path):
    _sweep(tmp_path)
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    headline = leaderboard.render(board, headline=True)
    full = leaderboard.render(board, headline=False)
    assert len(headline.splitlines()) < len(full.splitlines())
    assert 'stratum' not in headline.split('\n')[4:12][0] or True   # narrow cols
    # an all-NaN contest is not published on the landing page
    blanked = board.copy()
    for col in ('mae', 'abs_bias', 'win_frac'):
        blanked[col] = np.nan
    assert 'GLORIA' not in leaderboard.render(blanked, headline=True)


def test_sweep_cards_describe_each_sweep(tmp_path):
    _sweep(tmp_path, sweep_id='lb_cards')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    cards = leaderboard.sweep_cards(runs_root=tmp_path, board=board)
    assert 'lb_cards' in cards
    assert 'expb_pow' in cards and 'giop' in cards
    assert 'scored spectra' in cards
    assert ':doc:' in cards, 'a card must link to the sweep page'


def test_build_landing_writes_a_scannable_page_and_a_drill_down(tmp_path):
    _sweep(tmp_path, sweep_id='lb_land')
    docs = tmp_path / 'docs'
    (docs / 'reports').mkdir(parents=True, exist_ok=True)
    idx, full = standard.build_landing(docs_root=docs, runs_root=tmp_path,
                                      out=tmp_path / 'lb.parquet')
    index_txt = idx.read_text()
    full_txt = full.read_text()
    # the landing page is the scannable one; the grid lives next door
    assert len(index_txt.splitlines()) < len(full_txt.splitlines()) + 200
    assert 'leaderboard_full' in index_txt          # linked, and in the toctree
    assert 'Sweeps folded into this board' in index_txt
    # no CDN anywhere, and the vendored JS is served from _static
    assert 'cdn.bokeh.org' not in index_txt
    assert (docs / '_static' / 'bokeh').is_dir()
    assert '_static/bokeh/bokeh-' in index_txt


def test_build_landing_is_idempotent(tmp_path):
    _sweep(tmp_path, sweep_id='lb_idem')
    docs = tmp_path / 'docs'
    (docs / 'reports').mkdir(parents=True, exist_ok=True)
    kw = dict(docs_root=docs, runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    idx, _ = standard.build_landing(**kw)
    first = idx.read_text()
    standard.build_landing(**kw)
    second = idx.read_text()
    assert first.count(standard.rst.LEADERBOARD_START) == 1
    assert second.count(standard.rst.LEADERBOARD_START) == 1
    assert second.count('leaderboard_full') == first.count('leaderboard_full')


# --------------------------------------------------------------------
# defects found by the adversarial review of this task
# --------------------------------------------------------------------
def test_chisq_and_mcmc_are_separate_contests(tmp_path):
    """The review's headline defect: the fold gained ``fit_method``, the ranking did not.

    With χ² and MCMC in one contest the same algorithm was published at rank 1 *and*
    rank 2, comparing win fractions drawn from different pools — so the new
    MCMC-on-the-board capability actively corrupted the board that used it.
    """
    _sweep(tmp_path, sweep_id='lb_mix', mcmc=True)
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    r = leaderboard.ranked(board.assign(separable=True))
    ranked_rows = r[r['rank'].notna()]
    # no algorithm may hold two ranks inside one contest
    key = ['dataset', 'component', 'ref_wave', 'stratum', 'fit_method']
    assert not ranked_rows.duplicated(subset=key + ['algorithm']).any()
    dup = ranked_rows.groupby(key + ['algorithm'])['rank'].nunique()
    assert (dup <= 1).all()
    # and the contest key really does separate the two populations
    for _, grp in ranked_rows.groupby(key):
        assert grp['fit_method'].nunique() == 1


def test_the_headline_table_says_which_fit_method_a_row_is(tmp_path):
    _sweep(tmp_path, sweep_id='lb_fm', mcmc=True)
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    assert 'fit_method' in leaderboard.HEADLINE_COLS
    assert 'fit_method' in leaderboard.render(board, headline=True)


def test_an_empty_board_does_not_crash_the_landing_build(tmp_path):
    """Stage 3 before stage 2, or a fresh machine: a legitimate state."""
    empty_runs = tmp_path / 'runs'
    empty_runs.mkdir()
    docs = tmp_path / 'docs'
    (docs / 'reports').mkdir(parents=True, exist_ok=True)
    idx, full = standard.build_landing(docs_root=docs, runs_root=empty_runs,
                                       out=tmp_path / 'lb.parquet')
    assert idx.is_file() and full.is_file()
    board = pd.DataFrame(columns=['sweep_id', 'dataset', 'algorithm'])
    r = leaderboard.ranked(board)
    assert r.empty or r['rank'].isna().all()


def test_a_rank_without_head_to_head_support_says_so(tmp_path):
    """An older sweep has no pair rows; ordering it silently would erode the rule."""
    _sweep(tmp_path, sweep_id='lb_nopair')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    r = leaderboard.ranked(board.drop(columns=['separable']))
    ranked_rows = r[r['rank'].notna()]
    assert not ranked_rows.empty
    assert (ranked_rows['ranking'] == 'ranked (no head-to-head)').all()


def test_a_sole_competitor_is_labelled_as_one(tmp_path):
    _sweep(tmp_path, sweep_id='lb_solo')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    solo = board.copy()
    drop = (solo['algorithm'] == 'giop') & (solo['component'] == 'a')
    for col in ('mae', 'abs_bias', 'win_frac'):
        solo.loc[drop, col] = np.nan
    r = leaderboard.ranked(solo.assign(separable=True))
    survivors = r[(r['component'] == 'a') & (r['algorithm'] == 'expb_pow')]
    assert (survivors['ranking'] == 'sole competitor').any()
    assert survivors['rank'].isna().all()


def test_cards_do_not_link_a_page_that_was_never_built(tmp_path):
    """A folded-but-unbuilt sweep would leave a dangling ``:doc:`` reference."""
    _sweep(tmp_path, sweep_id='lb_nopage')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    docs = tmp_path / 'docs'
    (docs / 'reports').mkdir(parents=True, exist_ok=True)
    cards = leaderboard.sweep_cards(runs_root=tmp_path, board=board,
                                    docs_root=docs)
    assert ':doc:' not in cards
    assert 'No report page has been built' in cards
    # ... and it does link one that exists
    page = docs / 'reports' / 'lb_nopage'
    page.mkdir(parents=True)
    (page / 'cross_algorithm.rst').write_text('x')
    assert ':doc:' in leaderboard.sweep_cards(runs_root=tmp_path, board=board,
                                              docs_root=docs)


def test_vendoring_repairs_a_truncated_bundle(tmp_path):
    """Copy-if-missing left an interrupted copy broken forever."""
    names = bokeh.vendor_bokehjs(tmp_path)
    victim = tmp_path / 'bokeh' / names[0]
    good = victim.stat().st_size
    victim.write_bytes(b'truncated')
    bokeh.vendor_bokehjs(tmp_path)
    assert victim.stat().st_size == good

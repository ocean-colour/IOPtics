"""Tier-1 tests for ``ioptics.report.leaderboard``.

Builds synthetic scored sweeps under a ``tmp_path`` runs-root (reusing the
``test_metrics`` helpers), then checks the cross-sweep fold is idempotent,
accumulates across sweeps, and ranks the better algorithm first.
"""

import numpy as np

from ioptics import io, metrics
from ioptics.report import leaderboard
from ioptics.tests.test_metrics import _make_pair


def _mk_sweep(tmp_path, sid):
    """Two-algorithm scored sweep: expb_pow exact vs giop 2x-high, 3 obs."""
    chl = {0: 0.05, 1: 0.5, 2: 2.0}
    pairs = []
    for obs in range(3):
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, chl[obs], 10 + obs))
        pairs.append(_make_pair(obs, 'giop', 2.0, chl[obs], 15))
    io.write_results(sid, pairs, root=tmp_path)
    metrics.compute(sid, root=tmp_path)


def _lb(tmp_path):
    return tmp_path / 'leaderboard.parquet'


def test_update_writes_and_folds(tmp_path):
    _mk_sweep(tmp_path, 'sw_a')
    board = leaderboard.update(runs_root=tmp_path, out=_lb(tmp_path))
    assert _lb(tmp_path).is_file()
    assert set(board['sweep_id']) == {'sw_a'}
    assert set(board['algorithm']) == {'expb_pow', 'giop'}
    # ref-band rows for each component at its ref wavelengths
    assert (board['ref_wave'] == 440.0).any()
    assert 'win_frac' in board.columns


def test_update_idempotent(tmp_path):
    _mk_sweep(tmp_path, 'sw_a')
    b1 = leaderboard.update(runs_root=tmp_path, out=_lb(tmp_path))
    b2 = leaderboard.update(runs_root=tmp_path, out=_lb(tmp_path))
    # re-folding the same sweep replaces its rows -> no growth
    assert len(b1) == len(b2)
    assert (b2['sweep_id'] == 'sw_a').all()


def test_update_accumulates_across_sweeps(tmp_path):
    _mk_sweep(tmp_path, 'sw_a')
    _mk_sweep(tmp_path, 'sw_b')
    # fold only sw_a, then only sw_b -> sw_a preserved
    leaderboard.update(runs_root=tmp_path, out=_lb(tmp_path), sweep_ids=['sw_a'])
    board = leaderboard.update(runs_root=tmp_path, out=_lb(tmp_path),
                               sweep_ids=['sw_b'])
    assert set(board['sweep_id']) == {'sw_a', 'sw_b'}


def test_ranking_better_algorithm_first(tmp_path):
    _mk_sweep(tmp_path, 'sw_a')
    board = leaderboard.update(runs_root=tmp_path, out=_lb(tmp_path))
    rk = leaderboard.ranked(board, stratum='all')
    a440 = rk[(rk.component == 'a') & (rk.ref_wave == 440.0)]
    top = a440[a440['rank'] == 1].iloc[0]
    assert top['algorithm'] == 'expb_pow'          # exact -> wins, mae 0
    assert np.isclose(top['win_frac'], 1.0)
    giop = a440[a440.algorithm == 'giop'].iloc[0]
    assert giop['rank'] == 2


def test_render_rst_and_md(tmp_path):
    _mk_sweep(tmp_path, 'sw_a')
    leaderboard.update(runs_root=tmp_path, out=_lb(tmp_path))
    rst = leaderboard.render(runs_root=tmp_path, out=_lb(tmp_path))
    assert '.. list-table:: Leaderboard' in rst
    assert 'expb_pow' in rst and 'giop' in rst
    md = leaderboard.render(runs_root=tmp_path, out=_lb(tmp_path), fmt='md')
    assert md.startswith('| dataset |')

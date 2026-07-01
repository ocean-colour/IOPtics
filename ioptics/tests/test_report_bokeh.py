"""Tier-1 tests for ``ioptics.report.bokeh`` standalone interactive figures.

Builds a synthetic scored sweep + leaderboard, then checks each builder returns
a self-contained HTML string (inline BokehJS, no external server) carrying the
expected selector titles and data.
"""

from ioptics import io, metrics
from ioptics.report import bokeh, figures, leaderboard
from ioptics.tests.test_metrics import _make_pair

_SID = 'bok_v1'


def _build(tmp_path):
    chl = {0: 0.05, 1: 0.5, 2: 2.0}
    pairs = []
    for obs in range(3):
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, chl[obs], 10 + obs))
        pairs.append(_make_pair(obs, 'giop', 2.0, chl[obs], 15))
    io.write_results(_SID, pairs, root=tmp_path)
    metrics.compute(_SID, root=tmp_path)
    return figures.load(_SID, root=tmp_path)


def _self_contained(html):
    assert isinstance(html, str) and len(html) > 1000
    assert '<html' in html.lower()
    # inline BokehJS (offline / embeddable): the library is inlined as a big
    # <script>, not pulled from the Bokeh CDN.
    assert 'BokehJS' in html or 'Bokeh.' in html
    assert 'cdn.bokeh.org' not in html


def test_interactive_scatter(tmp_path):
    sw = _build(tmp_path)
    html = bokeh.interactive_scatter(sw)
    _self_contained(html)
    for title in ('algorithm', 'component', 'stratum'):
        assert title in html
    assert 'expb_pow' in html and 'giop' in html          # data embedded


def test_interactive_leaderboard(tmp_path):
    sw = _build(tmp_path)
    lb_path = tmp_path / 'leaderboard.parquet'
    leaderboard.update(runs_root=tmp_path, out=lb_path)
    html = bokeh.interactive_leaderboard(out=lb_path)
    _self_contained(html)
    for title in ('dataset', 'component', 'stratum'):
        assert title in html
    assert 'expb_pow' in html and 'giop' in html


def test_interactive_leaderboard_from_board(tmp_path):
    sw = _build(tmp_path)
    board = leaderboard.update(runs_root=tmp_path,
                               out=tmp_path / 'leaderboard.parquet')
    html = bokeh.interactive_leaderboard(board=board)
    _self_contained(html)

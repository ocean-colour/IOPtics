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


def test_scatter_points_downsampled(tmp_path):
    sw = _build(tmp_path)
    full = bokeh._scatter_points(sw, 'chisq', max_points=10 ** 9)
    capped = bokeh._scatter_points(sw, 'chisq', max_points=50)  # force downsample
    assert len(full) > 50 and len(capped) <= 50
    # every selectable (algorithm, component, stratum) combo survives the cap
    combos = lambda df: set(map(tuple,
                                df[['algorithm', 'component', 'stratum']].values))
    assert combos(full) == combos(capped)


def test_scatter_embed(tmp_path):
    sw = _build(tmp_path)
    frag = bokeh.scatter_embed(sw)
    assert isinstance(frag, str) and len(frag) > 500
    # an embeddable fragment (components + **vendored** BokehJS), NOT a document
    assert '<html' not in frag.lower()
    assert '<div' in frag and '<script' in frag          # components div+script
    # no CDN: a published figure must not stop working offline, behind a CSP, or
    # when the CDN moves on (the two committed pages had already drifted versions)
    assert 'cdn.bokeh.org' not in frag
    assert '_static/bokeh/bokeh-' in frag and '.min.js' in frag
    # the obs_id is in the hover, so an outlier can be traced to its spectrum
    assert 'obs_id' in frag


def test_vendored_bokehjs_is_versioned_and_idempotent(tmp_path):
    import bokeh as _bokeh

    names = bokeh.vendor_bokehjs(tmp_path)
    assert names and all(_bokeh.__version__ in n for n in names), \
        'unversioned filenames would re-point every historical page on upgrade'
    files = sorted(p.name for p in (tmp_path / 'bokeh').iterdir())
    again = bokeh.vendor_bokehjs(tmp_path)                # copy-if-missing
    assert sorted(p.name for p in (tmp_path / 'bokeh').iterdir()) == files
    assert again == names
    # only the bundles this figure needs — CDN.render() emits five
    assert not any('bokeh-gl' in n or 'mathjax' in n for n in names)


def test_script_tag_depth_matches_the_page_location():
    deep = bokeh.local_script_tags('../../')             # reports/<sweep>/page
    landing = bokeh.local_script_tags('../')             # reports/index
    assert 'src="../../_static/bokeh/' in deep
    assert 'src="../_static/bokeh/' in landing


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

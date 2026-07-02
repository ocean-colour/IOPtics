"""Tier-1 tests for ``ioptics.report.rst`` + ``ioptics.report.standard``.

Exercises the RST string builders and the on-demand ``standard.build`` on a
synthetic sweep written to a ``tmp_path`` runs root, with the Sphinx tree also
redirected to ``tmp_path`` (so the real docs tree is untouched).
"""

import matplotlib
matplotlib.use('Agg')

from ioptics import io, metrics
from ioptics.report import figures, rst, standard
from ioptics.tests.conftest import needs_l23
from ioptics.tests.test_metrics import _make_pair

_SID = 'std_v1'


def _build_sweep(tmp_path):
    chl = {0: 0.05, 1: 0.5, 2: 2.0}
    pairs = []
    for obs in range(3):
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, chl[obs], 10 + obs))
        pairs.append(_make_pair(obs, 'giop', 2.0, chl[obs], 15, rrs_factor=1.5))
    io.write_results(_SID, pairs, root=tmp_path)
    metrics.compute(_SID, root=tmp_path)


# --------------------------------------------------------------------
# rst string builders
# --------------------------------------------------------------------
def test_rst_blocks():
    assert rst.title('Hi').splitlines()[0] == '=='
    fb = rst.figure_block('scatter_a.png', 'a caption')
    assert '.. figure:: scatter_a.png' in fb and 'a caption' in fb
    ct = rst.csv_table_block('accuracy.csv', 'Accuracy')
    assert '.. csv-table:: Accuracy' in ct and ':file: accuracy.csv' in ct
    assert ':header-rows: 1' in ct
    br = rst.bokeh_raw('scatter.html')
    assert '.. raw:: html' in br and '<iframe src="scatter.html"' in br


def test_provenance_header():
    prov = {'created': '2026-07-01', 'versions': {
        'ioptics': {'version': '0.0.dev0', 'commit': 'abcdef1234'},
        'implementation_doc': 'v1.2'}}
    hdr = rst.provenance_header('sw', prov)
    assert ':Sweep: sw' in hdr
    assert ':ioptics: 0.0.dev0@abcdef12' in hdr
    assert ':implementation_doc: v1.2' in hdr


def test_ensure_glob_toctree_creates_and_upgrades(tmp_path):
    idx = tmp_path / 'reports' / 'index.rst'
    rst.ensure_glob_toctree(idx)                       # create
    assert ':glob:' in idx.read_text() and '*/*' in idx.read_text()
    # existing plain toctree -> upgraded, prose kept
    idx.write_text('Reports\n=======\n\nProse.\n\n.. toctree::\n   :maxdepth: 1\n')
    rst.ensure_glob_toctree(idx)
    txt = idx.read_text()
    assert 'Prose.' in txt and ':glob:' in txt


def test_write_leaderboard_landing_idempotent(tmp_path):
    idx = tmp_path / 'reports' / 'index.rst'
    rst.write_leaderboard_landing(idx, 'TABLE-A')
    rst.write_leaderboard_landing(idx, 'TABLE-B')       # replaces, not appends
    txt = idx.read_text()
    assert txt.count(rst.LEADERBOARD_START) == 1
    assert 'TABLE-B' in txt and 'TABLE-A' not in txt


# --------------------------------------------------------------------
# standard.build
# --------------------------------------------------------------------
def test_build_cross_algorithm(tmp_path):
    _build_sweep(tmp_path)
    docs = tmp_path / 'docs'
    out = standard.build(_SID, kind='cross_algorithm', root=tmp_path,
                         docs_root=docs)
    assert out == docs / 'reports' / _SID / 'cross_algorithm.rst'
    assert out.is_file()
    rd = out.parent
    # assets copied alongside the page
    assert (rd / 'scatter_a_440.png').is_file()
    assert (rd / 'accuracy_chisq_all.csv').is_file()
    assert (rd / 'qc_chisq_all.csv').is_file()
    assert (rd / 'interactive_scatter.html').is_file()
    text = out.read_text()
    assert f':Sweep: {_SID}' in text
    assert '.. figure:: scatter_a_440.png' in text
    assert '.. csv-table::' in text
    assert '<iframe src="interactive_scatter.html"' in text
    # toctree globs the new page in
    assert ':glob:' in (docs / 'reports' / 'index.rst').read_text()


def test_build_other_kinds(tmp_path):
    _build_sweep(tmp_path)
    docs = tmp_path / 'docs'
    for kind in ('per_algorithm', 'per_dataset'):
        out = standard.build(_SID, kind=kind, root=tmp_path, docs_root=docs)
        assert out.is_file() and out.name == f'{kind}.rst'
    # per_algorithm carries per-algorithm spectra
    pa = (docs / 'reports' / _SID / 'per_algorithm.rst').read_text()
    assert 'Spectra' in pa


def test_build_bad_kind(tmp_path):
    import pytest
    _build_sweep(tmp_path)
    with pytest.raises(ValueError):
        standard.build(_SID, kind='nope', root=tmp_path, docs_root=tmp_path / 'd')


def test_generated_page_renders_under_sphinx(tmp_path):
    """The generated report page must build under ``sphinx-build -W``."""
    import subprocess
    import sys

    _build_sweep(tmp_path)
    src = tmp_path / 'docs'
    standard.build(_SID, kind='cross_algorithm', root=tmp_path, docs_root=src)
    (src / 'conf.py').write_text(
        "project = 'test'\nextensions = []\nhtml_theme = 'basic'\n"
        "exclude_patterns = ['_build']\n")
    (src / 'index.rst').write_text(
        'Test\n====\n\n.. toctree::\n   :maxdepth: 2\n\n   reports/index\n')

    proc = subprocess.run(
        [sys.executable, '-m', 'sphinx', '-W', '-q', '-b', 'html',
         str(src), str(src / '_build')],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (src / '_build' / 'reports' / _SID / 'cross_algorithm.html').is_file()


# --------------------------------------------------------------------
# Tier 2 — full report pipeline end-to-end on a tiny real L23 sweep
# --------------------------------------------------------------------
@needs_l23
def test_report_end_to_end_l23(tmp_path):
    import subprocess
    import sys

    from ioptics import config, run
    from ioptics.report import leaderboard

    sid = 'sweep_report_e2e'
    cfg = config.loads(
        f"sweep_id: {sid}\n"
        "datasets: [L23]\n"
        "noise_model: pace\n"
        "algorithms: [expb_pow, giop]\n"
        "fit_method: chisq\n"
        "mcmc_subset: 0\n"
        "seed: 1234\n")
    run.run_sweep(cfg, obs_ids=range(4), root=tmp_path)
    metrics.compute(sid, root=tmp_path)

    src = tmp_path / 'docs'
    out = standard.build(sid, kind='cross_algorithm', root=tmp_path,
                         docs_root=src)
    assert out.is_file()

    # fold the leaderboard + refresh the landing (build-script stage-3 seam)
    lb_path = tmp_path / 'leaderboard.parquet'
    board = leaderboard.update(runs_root=tmp_path, out=lb_path)
    idx = src / 'reports' / 'index.rst'
    rst.write_leaderboard_landing(idx, leaderboard.render(board=board))
    assert lb_path.is_file()
    landing = idx.read_text(encoding='utf-8')
    assert rst.LEADERBOARD_START in landing and 'expb_pow' in landing

    # the whole reports tree (page + landing) builds under sphinx -W
    (src / 'conf.py').write_text(
        "project = 'test'\nextensions = []\nhtml_theme = 'basic'\n"
        "exclude_patterns = ['_build']\n")
    (src / 'index.rst').write_text(
        'Test\n====\n\n.. toctree::\n   :maxdepth: 2\n\n   reports/index\n')
    proc = subprocess.run(
        [sys.executable, '-m', 'sphinx', '-W', '-q', '-b', 'html',
         str(src), str(src / '_build')],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (src / '_build' / 'reports' / sid / 'cross_algorithm.html').is_file()

"""Checks on the "our own LS2" page (``runs/prototypes/ls2/ours_report.py``, ls2 task 14).

Tier 2 only: it needs L23 and the LS2 and RT-A sweeps on disk.  It rebuilds
the page into a scratch docs root and pins the findings the task-14 summary
rests on.
"""

import importlib.util
import os
import pathlib

import pandas as pd
import pytest

from ioptics.tests.conftest import needs_l23, needs_l23_profile

HERE = (pathlib.Path(__file__).resolve().parents[1] / 'runs' / 'prototypes'
        / 'ls2')


def _have(*sweeps):
    root = os.getenv('OS_COLOR')
    if not root:
        return False
    return all((pathlib.Path(root) / 'IOPtics' / 'runs' / s
                / 'metrics_scalar.parquet').is_file() for s in sweeps)


def _mod():
    spec = importlib.util.spec_from_file_location('ls2_ours_report',
                                                  HERE / 'ours_report.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@needs_l23
@needs_l23_profile
@pytest.mark.skipif(not _have('ls2_l23_x4_v1', 'ls2_l23_x4_heldout_v1',
                              'rt_tests_A_l23_v1'),
                    reason='needs the LS2 X=4, held-out and RT-A sweeps')
def test_the_ours_page_and_its_findings(tmp_path):
    m = _mod()
    m.build(docs_root=tmp_path)
    rd = tmp_path / 'reports' / m.SID
    assert (rd / f'{m.SID}.rst').is_file()

    H = pd.read_csv(rd / 'ours_headline.csv').set_index(['theta_s', 'tables'])
    pub, ours = H.loc[(0, 'published')], H.loc[(0, 'our LS2 (refit a/bb + κ)')]
    eff = H.loc[(0, 'published at effective μw')]
    # the published rung-(i) biases reproduce, and ours shrinks every one
    assert pub.a_median_err > 0.02 and pub.bb_median_err > 0.07 and pub.bb_p_median_err > 0.15
    assert abs(ours.a_median_err) < 0.01
    assert ours.bb_median_err < 0.5 * pub.bb_median_err
    assert ours.bb_p_median_err < 0.5 * pub.bb_p_median_err
    # the a bias is illumination: the effective muw alone removes all of it
    assert eff.a_median_err < 0.0 < pub.a_median_err
    # kappa availability
    assert pub.kappa_unavailable > 0.2 and ours.kappa_unavailable < 0.01

    V = pd.read_csv(rd / 'ours_vs_bing_heldout.csv').set_index(
        ['rung', 'component', 'scope'])
    # our LS2 with true inputs beats BING on absorption; BING keeps bb
    for comp in ('a', 'a_nw'):
        r = V.loc[('ls2r_i', comp, '400–750 nm')]
        assert r.mae_ls2 < r.mae_bing, comp
    r = V.loc[('ls2r_i', 'bb', '555 nm')]
    assert r.mae_bing < r.mae_ls2
    # our L23 Kd network takes operational a(440) well below the PACE network's
    lad = pd.read_csv(rd / 'ours_heldout_ladder.csv').set_index('rung')
    assert lad.loc['ls2r_iii_l23', 'a_440_mae'] < 0.5 * lad.loc['ls2_iii', 'a_440_mae']
    # every paired cell compared one truth
    assert (V['max_truth_mismatch'] < 1e-6).all()

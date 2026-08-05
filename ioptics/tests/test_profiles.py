"""Tier-1 tests for the cross-sweep profile pages and coverage matrix (Task 6).

Every other page is keyed by ``sweep_id`` — a question no outside reader arrives
with. These pages are the standing answer, folded across every sweep, and the
coverage matrix is the map that says what has and has not been tried: a missing
leaderboard row cannot distinguish "never run" from "run but unscoreable" from
"run and failed", so the matrix is built by walking the runs tree instead.
"""

import matplotlib
matplotlib.use('Agg')

import pandas as pd

from ioptics import io, metrics
from ioptics.report import leaderboard, profiles, standard
from ioptics.tests.test_metrics import _make_pair


def _sweep(tmp_path, sweep_id, *, dataset='L23', algos=('expb_pow', 'giop'),
           status='ok', n=4):
    pairs = []
    for obs in range(n):
        spread = 0.5 + obs
        for i, algo in enumerate(algos):
            pairs.append(_make_pair(obs, algo, 1.0 + 2.0 * i, 0.5, 10 + 5 * i,
                                    dataset=dataset, truth_factor=spread,
                                    status=status))
    io.write_results(sweep_id, pairs, root=tmp_path)
    metrics.compute(sweep_id, root=tmp_path)


# --------------------------------------------------------------------
# the coverage matrix
# --------------------------------------------------------------------
def test_matrix_distinguishes_the_three_states(tmp_path):
    _sweep(tmp_path, 'm_scored', dataset='L23')
    _sweep(tmp_path, 'm_failed', dataset='PANGAEA', status='fit_failed')
    m = profiles.coverage_matrix(tmp_path)
    by = m.set_index(['algorithm', 'dataset'])['state']
    assert by[('expb_pow', 'L23')] == profiles.SCORED
    assert by[('expb_pow', 'PANGAEA')] == profiles.FAILED
    # a pair nobody ran is absent from the frame and reads "not evaluated" in the
    # rendered grid — not a blank cell, which would be ambiguous
    grid = profiles.render_coverage_matrix(m, algorithms=['gsm'],
                                          datasets=['GLORIA'])
    assert profiles.NOT_EVALUATED in grid
    assert 'gsm' in grid and 'GLORIA' in grid


def test_matrix_sees_an_attempt_the_leaderboard_would_hide(tmp_path):
    """An unscoreable sweep is dropped by the fold but visible in the matrix."""
    _sweep(tmp_path, 'm_notruth', dataset='GLORIA')
    # blank out every scored pair, as a dataset without spectral truth gives
    mpath = tmp_path / 'm_notruth' / metrics.METRICS_SCALAR_FILE
    ms = pd.read_parquet(mpath)
    ms.loc[ms['ref_wave'].notna(), 'n'] = 0
    ms.to_parquet(mpath, index=False)

    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    m = profiles.coverage_matrix(tmp_path)
    assert (m['state'] == profiles.NO_TRUTH).all()
    assert (m['n_attempted'] > 0).all(), 'the attempt itself is still recorded'
    assert (m['n_scored_pairs'] == 0).all()
    # The board still carries rows, but with no pairs behind them — which is
    # exactly the ambiguity the matrix resolves: it can say the attempt happened
    # and there was nothing to score it against.
    assert board['n'].fillna(0).eq(0).all()


def test_matrix_is_empty_not_broken_on_an_empty_tree(tmp_path):
    m = profiles.coverage_matrix(tmp_path / 'nothing')
    assert m.empty
    assert 'nothing to compare' in profiles.render_coverage_matrix(m)


# --------------------------------------------------------------------
# the profile pages
# --------------------------------------------------------------------
def _docs(tmp_path):
    d = tmp_path / 'docs'
    (d / 'reports').mkdir(parents=True, exist_ok=True)
    return d


def test_algorithm_profile_states_numbers_and_its_configuration(tmp_path):
    _sweep(tmp_path, 'p_algo')
    docs = _docs(tmp_path)
    out = profiles.build_algorithm_profile('expb_pow', docs_root=docs,
                                           runs_root=tmp_path)
    txt = out.read_text()
    assert out.parent.name == profiles.ALGORITHM_DIR
    assert 'Algorithm profile — expb_pow' in txt
    assert 'mae' in txt and 'L23' in txt
    assert 'What it parameterizes' in txt and 'a_nw model' in txt   # from the spec
    assert 'Where it has been evaluated' in txt
    assert ':doc:`/reports/glossary`' in txt


def test_dataset_profile_says_what_the_data_can_score(tmp_path):
    _sweep(tmp_path, 'p_data')
    docs = _docs(tmp_path)
    out = profiles.build_dataset_profile('L23', docs_root=docs, runs_root=tmp_path)
    txt = out.read_text()
    assert out.parent.name == profiles.DATASET_DIR
    assert 'Dataset profile — L23' in txt
    assert 'What this dataset can score' in txt
    assert 'Retrieval success' in txt
    assert 'statement about the **models**' in txt


def test_a_never_run_algorithm_gets_a_page_that_says_so(tmp_path):
    """More useful than a missing page — and it is the honest state."""
    _sweep(tmp_path, 'p_none')
    docs = _docs(tmp_path)
    out = profiles.build_algorithm_profile('gsm', docs_root=docs,
                                           runs_root=tmp_path)
    txt = out.read_text()
    assert 'no sweep' in txt and 'coverage matrix' in txt


def test_profiles_pool_sweeps_and_say_when_configs_differed(tmp_path):
    """JXP chose one pooled profile per algorithm — honest only if it says so."""
    _sweep(tmp_path, 'p_one')
    _sweep(tmp_path, 'p_two')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    docs = _docs(tmp_path)
    out = profiles.build_algorithm_profile('expb_pow', docs_root=docs,
                                           runs_root=tmp_path, board=board)
    txt = out.read_text()
    assert 'p_one' in txt or '2 sweep' in txt
    # identical configs → no "what varied" section; differing digests → one
    varied = profiles._what_varied(board.assign(algo_digest='same'), 'expb_pow')
    assert varied == ''
    two = board.copy()
    two['algo_digest'] = two['algo_digest'].astype(object)
    two.loc[two['sweep_id'] == 'p_two', 'algo_digest'] = 'other'
    assert 'What varied between sweeps' in profiles._what_varied(two, 'expb_pow')


def test_hand_written_findings_are_included_never_overwritten(tmp_path):
    _sweep(tmp_path, 'p_find')
    docs = _docs(tmp_path)
    page_dir = docs / 'reports' / profiles.ALGORITHM_DIR
    page_dir.mkdir(parents=True, exist_ok=True)
    findings = page_dir / 'expb_pow_findings.rst'
    findings.write_text('Our conclusion: it works.\n')
    out = profiles.build_algorithm_profile('expb_pow', docs_root=docs,
                                           runs_root=tmp_path)
    assert '.. include:: expb_pow_findings.rst' in out.read_text()
    assert findings.read_text() == 'Our conclusion: it works.\n', 'never clobbered'


def test_build_profiles_covers_every_algorithm_and_dataset(tmp_path):
    _sweep(tmp_path, 'p_all', dataset='L23')
    _sweep(tmp_path, 'p_all2', dataset='GLORIA')
    docs = _docs(tmp_path)
    a_paths, d_paths = profiles.build_profiles(docs_root=docs, runs_root=tmp_path,
                                              algorithms=['gsm'])
    names = {p.stem for p in a_paths}
    assert {'expb_pow', 'giop', 'gsm'} <= names
    assert {p.stem for p in d_paths} == {'L23', 'GLORIA'}


def test_landing_page_carries_the_matrix_and_links_the_profiles(tmp_path):
    _sweep(tmp_path, 'p_land')
    docs = _docs(tmp_path)
    idx, _ = standard.build_landing(docs_root=docs, runs_root=tmp_path,
                                    out=tmp_path / 'lb.parquet')
    txt = idx.read_text()
    assert 'What has been evaluated on what' in txt
    assert profiles.NOT_EVALUATED in txt or profiles.SCORED in txt
    # the profile dirs and the glossary must be in the toctree, or -W fails
    assert 'algorithms/*' in txt and 'datasets/*' in txt and 'glossary' in txt
    assert (docs / 'reports' / profiles.ALGORITHM_DIR / 'expb_pow.rst').is_file()
    assert (docs / 'reports' / profiles.DATASET_DIR / 'L23.rst').is_file()

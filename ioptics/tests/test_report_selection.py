"""Tier-1 tests for data-driven report artifact selection (Stage 7, Task 2).

The published GLORIA page was five blank "no data" panels under captions
explaining how to read them, because the figure set was fixed at ``a(440)`` /
``bb(555)`` / ``expb_pow``-vs-``giop`` while that dataset's only spectral truth is
``a_dg(440)`` and it never ran ``giop``. These tests pin the fix: the figure set is
derived from what the sweep measured, a degenerate figure is never written, and a
section with nothing behind it is omitted rather than published.
"""

import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd

from ioptics import io, metrics, plotting
from ioptics.report import figures, standard
from ioptics.tests.test_metrics import _make_pair

_SID = 'sel_v1'


def _sweep(tmp_path, sweep_id=_SID, dataset='L23', algos=('expb_pow', 'giop'),
           obs_ids=(0, 1, 2)):
    pairs = []
    for obs in obs_ids:
        for i, algo in enumerate(algos):
            pairs.append(_make_pair(obs, algo, 1.0 + 0.5 * i, 0.5, 10 + 5 * i,
                                    dataset=dataset))
    io.write_results(sweep_id, pairs, root=tmp_path)
    metrics.compute(sweep_id, root=tmp_path)
    return figures.load(sweep_id, root=tmp_path)


def _docs(tmp_path):
    d = tmp_path / 'docs'
    (d / 'reports').mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------
# what a sweep can show
# --------------------------------------------------------------------
def test_scored_refs_lists_only_what_carries_truth(tmp_path):
    sweep = _sweep(tmp_path)
    scored = figures.scored_refs(sweep)
    assert scored, 'the synthetic sweep scores several components'
    combos = {(c, r) for c, r, _ in scored}
    # every listed combination really has scored pairs behind it ...
    assert all(n > 0 for _, _, n in scored)
    # ... and is ordered best-covered first
    counts = [n for _, _, n in scored]
    assert counts == sorted(counts, reverse=True)
    # a component the sweep has no truth for is absent
    assert ('Rrs', 440.0) not in combos


def test_scored_refs_skips_components_without_truth(tmp_path):
    """A GLORIA-shaped sweep: truth for one component only."""
    sweep = _sweep(tmp_path, sweep_id='sel_gl')
    ms = sweep.metrics_scalar.copy()
    # blank out every component except a_dg, as GLORIA's truth does
    ms.loc[ms['component'] != 'a_dg', 'n'] = 0
    sweep = sweep._replace(metrics_scalar=ms)
    scored = figures.scored_refs(sweep)
    assert scored and {c for c, _, _ in scored} == {'a_dg'}


def test_scored_refs_falls_back_to_the_results_table(tmp_path):
    """Before metrics.compute has run there is still a defensible figure set."""
    sweep = _sweep(tmp_path, sweep_id='sel_nom')._replace(metrics_scalar=None)
    scored = figures.scored_refs(sweep)
    assert scored
    assert all(r in (440.0, 443.0, 555.0, 670.0) for _, r, _ in scored)


def test_dbic_pair_is_the_k_extremes_or_nothing(tmp_path):
    sweep = _sweep(tmp_path, sweep_id='sel_k')          # expb_pow k=5, giop k=3
    assert figures.dbic_pair(sweep) == ('expb_pow', 'giop')

    # one algorithm -> no contest
    one = _sweep(tmp_path, sweep_id='sel_one', algos=('expb_pow',))
    assert figures.dbic_pair(one) is None

    # several algorithms, all the same k -> ΔBIC is not asking anything
    flat = _sweep(tmp_path, sweep_id='sel_flat')
    sc = flat.scalar.copy()
    sc['k'] = 5
    assert figures.dbic_pair(flat._replace(scalar=sc)) is None


# --------------------------------------------------------------------
# a degenerate figure is never written
# --------------------------------------------------------------------
def test_blank_figures_are_not_saved(tmp_path):
    sweep = _sweep(tmp_path, sweep_id='sel_blank')
    # a component/ref the sweep cannot score at all
    paths = figures.scatter_set(sweep, 'a', ref=412)
    assert paths == []
    figdir = figures.subdir(sweep, 'figures')
    assert not list(figdir.glob('scatter_a_412.*'))
    # ... while a real one is written
    comp, ref, _ = figures.scored_refs(sweep)[0]
    assert figures.scatter_set(sweep, comp, ref=ref)


def test_plotting_marks_degenerate_figures():
    empty = plotting.scatter_log({'points': pd.DataFrame(columns=['algorithm',
                                                                 'x', 'y']),
                                  'lims': (np.nan, np.nan)})
    assert plotting.is_empty(empty)
    real = plotting.scatter_log({'points': pd.DataFrame({'algorithm': ['a'],
                                                         'x': [1.0], 'y': [1.1]}),
                                 'lims': (1.0, 1.1)})
    assert not plotting.is_empty(real)


# --------------------------------------------------------------------
# the page
# --------------------------------------------------------------------
def test_page_sections_follow_the_data(tmp_path):
    sweep = _sweep(tmp_path, sweep_id='sel_page')
    docs = _docs(tmp_path)
    out = standard.build('sel_page', kind='cross_algorithm', root=tmp_path,
                         docs_root=docs)
    txt = out.read_text()
    comp, ref, _ = figures.scored_refs(sweep)[0]
    assert f'Retrieved vs. true — {comp}({ref:g})' in txt
    assert f'Ratio distribution — {comp}({ref:g})' in txt      # paired, per JXP
    assert 'Model selection' in txt
    # nothing blank was published
    assert 'no data' not in txt
    report_dir = out.parent
    assert not list(report_dir.glob('scatter_a_412.png'))
    # the ΔBIC figure names the pair that actually ran
    assert list(report_dir.glob('dbic_cdf_expb_pow_vs_giop.png'))


def test_page_says_what_it_cannot_show(tmp_path):
    """Suppressing a section silently would be its own dishonesty."""
    sweep = _sweep(tmp_path, sweep_id='sel_nodbic', algos=('expb_pow',))
    docs = _docs(tmp_path)
    out = standard.build('sel_nodbic', kind='cross_algorithm', root=tmp_path,
                         docs_root=docs)
    txt = out.read_text()
    assert 'Not shown for this sweep' in txt
    assert 'ΔBIC' in txt.split('Not shown for this sweep')[1]
    assert 'Model selection (ΔBIC)\n---' not in txt          # no empty section


def test_stale_assets_are_pruned(tmp_path):
    docs = _docs(tmp_path)
    _sweep(tmp_path, sweep_id='sel_prune')
    out = standard.build('sel_prune', kind='cross_algorithm', root=tmp_path,
                         docs_root=docs)
    # a figure from a previous figure set that this sweep does not regenerate
    stale = out.parent / 'scatter_a_412.png'
    stale.write_bytes(b'not a real png')
    keep = out.parent / 'findings.rst'                     # hand-written, not ours
    keep.write_text('Our conclusion.\n')
    standard.build('sel_prune', kind='cross_algorithm', root=tmp_path,
                   docs_root=docs)
    assert not stale.exists(), 'orphaned display assets must not stay committed'
    assert keep.exists(), 'hand-written RST is not this builder\'s to delete'


def test_per_algorithm_survives_string_obs_ids(tmp_path):
    """GLORIA's ids are strings; ``int(obs_id.min())`` crashed on them."""
    sweep = _sweep(tmp_path, sweep_id='sel_str', dataset='GLORIA',
                   obs_ids=('GID_7', 'GID_2'))
    docs = _docs(tmp_path)
    out = standard.build('sel_str', kind='per_algorithm', root=tmp_path,
                         docs_root=docs)
    txt = out.read_text()
    assert 'Spectra — expb_pow, obs GID_' in txt
    assert standard._curated_obs(sweep) in ('GID_7', 'GID_2')

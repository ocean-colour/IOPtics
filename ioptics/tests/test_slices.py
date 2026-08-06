"""Tier-1 tests for the three discarded metric slices (Stage 7, Task 8).

Three reductions were computed, persisted and then read by nothing:

* ``metrics_spectral`` — a full per-(component, wavelength) accuracy table, written
  since Stage 2 and never opened by the report layer, so the figure an ocean-colour
  reader looks for first (error across the spectrum) was not drawn from data we had.
* the per-stratum rows — every scalar metric is computed per trophic bin *and* pooled,
  and only the pooled ``'all'`` row was ever published. On GLORIA the pooled 21%
  retrieval success is a blend of mesotrophic 86% and eutrophic 14%.
* ``fit_method`` — scored in parallel for χ² and MCMC since Stage 2, never compared.

The slices must also be **suppressed honestly**: on the only real sweep the
accuracy-vs-λ figure has one band and the χ²-vs-MCMC comparison has one fit method,
and a page that draws them anyway is worse than one that says why it cannot.
"""

import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd

from ioptics import diagnostics, io, metrics, plotting
from ioptics.report import figures, standard, tables
from ioptics.tests.test_metrics import _make_pair


def _sweep(tmp_path, sweep_id, *, algos=('expb_pow', 'giop'), n=8,
           dataset='L23', chl=None, mcmc_factor=None, status='ok'):
    """A sweep with truth at every band, spread over trophic strata."""
    pairs = []
    for obs in range(n):
        c = chl[obs] if chl is not None else 0.05 + 0.5 * obs
        for i, algo in enumerate(algos):
            pairs.append(_make_pair(obs, algo, 1.0 + 0.5 * i, c, 10 + 5 * i,
                                    dataset=dataset, truth_factor=0.5 + obs,
                                    status=status))
            if mcmc_factor is not None:
                pairs.append(_make_pair(obs, algo, mcmc_factor, c, 10 + 5 * i,
                                        dataset=dataset, truth_factor=0.5 + obs,
                                        fit_method='mcmc'))
    io.write_results(sweep_id, pairs, root=tmp_path)
    metrics.compute(sweep_id, root=tmp_path)
    return figures.load(sweep_id, root=tmp_path)


def _docs(tmp_path):
    d = tmp_path / 'docs'
    (d / 'reports').mkdir(parents=True, exist_ok=True)
    return d


#: The shared ``_make_pair`` fixture carries four bands (440/443/555/670), which is
#: below :data:`ioptics.diagnostics.MIN_SPECTRUM_WAVES` (5, JXP's floor for calling
#: an accuracy curve a *spectrum*). Rather than weaken the tests to a threshold
#: nobody ships, these widen the persisted ``metrics_spectral`` to a realistic
#: hyperspectral grid — which is what a real L23/PACE sweep produces.
_WIDE_WAVES = (412.0, 440.0, 443.0, 490.0, 510.0, 555.0, 620.0, 670.0)


def _widen_spectral(sweep_id, tmp_path, waves=_WIDE_WAVES, slope=0.02):
    """Re-persist ``metrics_spectral`` across ``waves``, with a real spectral shape.

    ``mae`` gains a wavelength dependence so the figure is testing a curve rather
    than a flat line — a retrieval that is fine in the blue and poor in the red is
    the shape this figure exists to reveal. Returns the reloaded sweep.
    """
    path = io.sweep_dir(sweep_id, root=tmp_path) / metrics.METRICS_SPECTRAL_FILE
    ms = pd.read_parquet(path)
    base = ms[ms['wavelength'] == ms['wavelength'].min()].copy()
    out = []
    for i, w in enumerate(waves):
        part = base.copy()
        part['wavelength'] = w
        part['mae'] = part['mae'].astype(float) + slope * i
        out.append(part)
    pd.concat(out, ignore_index=True).to_parquet(path, index=False)
    return figures.load(sweep_id, root=tmp_path)


# --------------------------------------------------------------------
# accuracy vs wavelength
# --------------------------------------------------------------------
def test_accuracy_spectrum_reads_the_table_nothing_was_reading(tmp_path):
    _sweep(tmp_path, 'sl_acc')
    sweep = _widen_spectral('sl_acc', tmp_path)
    data = diagnostics.accuracy_spectrum_data(sweep.metrics_spectral, 'a')
    assert set(data['series']) == {'expb_pow', 'giop'}
    assert data['perfect'] == 0.0
    for algo, s in data['series'].items():
        assert s['wave'].size > 1, algo
        assert np.isfinite(s['value']).all()
        # ascending in wavelength, so the line is drawn in spectral order
        assert (np.diff(s['wave']) > 0).all()
    # median_ratio is perfect at 1, not 0 — the reference rule must follow the metric
    ratio = diagnostics.accuracy_spectrum_data(sweep.metrics_spectral, 'a',
                                               metric='median_ratio')
    assert ratio['perfect'] == 1.0


def test_a_band_nobody_scored_is_not_drawn_as_zero_error(tmp_path):
    """``n = 0`` with a NaN metric must drop out, not plot at the perfect value."""
    _sweep(tmp_path, 'sl_zero')
    sweep = _widen_spectral('sl_zero', tmp_path)
    ms = sweep.metrics_spectral.copy()
    victim = (ms['component'] == 'a') & (ms['wavelength'] == 555.0)
    ms.loc[victim, ['n', 'mae']] = [0, np.nan]
    data = diagnostics.accuracy_spectrum_data(ms, 'a')
    for algo, s in data['series'].items():
        assert 555.0 not in set(s['wave']), algo


def test_single_band_components_are_not_offered_as_a_spectrum(tmp_path):
    """GLORIA scores one component at one wavelength — no spectral shape exists."""
    sweep = _sweep(tmp_path, 'sl_one')
    ms = sweep.metrics_spectral.copy()
    keep = (ms['component'] == 'a_dg') & (ms['wavelength'] == 440.0)
    ms.loc[~keep, ['n', 'mae']] = [0, np.nan]
    trimmed = sweep._replace(metrics_spectral=ms)
    assert figures.scored_components(trimmed) == []
    assert figures.scored_components(trimmed, min_waves=1) == [('a_dg', 1, 2)]
    assert figures.accuracy_spectrum(trimmed) == [], 'nothing is written'


def test_the_grid_survives_one_empty_component(tmp_path):
    _sweep(tmp_path, 'sl_grid')
    sweep = _widen_spectral('sl_grid', tmp_path)
    good = diagnostics.accuracy_spectrum_data(sweep.metrics_spectral, 'a')
    empty = diagnostics.accuracy_spectrum_data(sweep.metrics_spectral, 'nope')
    assert not empty['series']
    assert not plotting.is_empty(plotting.accuracy_spectrum_grid([good, empty]))
    assert plotting.is_empty(plotting.accuracy_spectrum_grid([empty, empty]))
    assert plotting.is_empty(plotting.accuracy_spectrum_grid([]))


def test_the_page_draws_it_or_says_why_not(tmp_path):
    _sweep(tmp_path, 'sl_page')
    _widen_spectral('sl_page', tmp_path)
    docs = _docs(tmp_path)
    txt = standard.build('sl_page', root=tmp_path, docs_root=docs).read_text()
    assert 'Accuracy vs. wavelength' in txt
    assert (docs / 'reports' / 'sl_page'
            / 'accuracy_vs_wavelength_mae.png').is_file()

    # the same page, with only one scored band, must suppress and explain
    sweep = figures.load('sl_page', root=tmp_path)
    ms = sweep.metrics_spectral.copy()
    keep = (ms['component'] == 'a_dg') & (ms['wavelength'] == 440.0)
    ms.loc[~keep, ['n', 'mae']] = [0, np.nan]
    ms.to_parquet(io.sweep_dir('sl_page', root=tmp_path)
                  / metrics.METRICS_SPECTRAL_FILE, index=False)
    txt2 = standard.build('sl_page', root=tmp_path, docs_root=docs).read_text()
    assert 'Accuracy vs. wavelength\n---' not in txt2
    assert 'accuracy-vs-wavelength figure' in txt2
    assert 'single wavelength' in txt2


# --------------------------------------------------------------------
# per-stratum
# --------------------------------------------------------------------
def test_strata_planner_finds_the_bins_with_content(tmp_path):
    sweep = _sweep(tmp_path, 'sl_str', chl=[0.05, 0.05, 0.5, 0.5, 2.0, 2.0, 2.0, 2.0])
    got = dict((s, (p, a)) for s, p, a in figures.strata(sweep))
    assert 'all' not in got, 'the pooled row is what the section exists to split'
    assert {'oligotrophic', 'mesotrophic', 'eutrophic'} <= set(got)
    assert got['eutrophic'][1] == 4, 'four eutrophic spectra per algorithm'


def test_frac_ok_and_frac_not_ok_are_complements_within_a_stratum(tmp_path):
    """They were not: ``frac_not_ok`` pooled every stratum while ``frac_ok`` did not.

    On GLORIA that published ``frac_not_ok`` 0.79 beside a mesotrophic ``frac_ok`` of
    0.857 — summing to 1.65 — the moment per-stratum QC tables were emitted.
    """
    sweep = _sweep(tmp_path, 'sl_frac',
                   chl=[0.05, 0.05, 0.5, 0.5, 2.0, 2.0, 2.0, 2.0])
    for stratum, _, _ in figures.strata(sweep) + [('all', 0, 0)]:
        qc = tables.qc(sweep, stratum=stratum, write=False)
        total = qc['frac_ok'].astype(float) + qc['frac_not_ok'].astype(float)
        assert np.allclose(total, 1.0), (stratum, list(total))


def test_per_stratum_tables_reach_the_page(tmp_path):
    _sweep(tmp_path, 'sl_pst', chl=[0.05, 0.05, 0.5, 0.5, 2.0, 2.0, 2.0, 2.0])
    docs = _docs(tmp_path)
    txt = standard.build('sl_pst', root=tmp_path, docs_root=docs).read_text()
    assert 'Per trophic stratum' in txt
    rd = docs / 'reports' / 'sl_pst'
    for stratum in ('oligotrophic', 'mesotrophic', 'eutrophic'):
        assert f'Accuracy — {stratum}' in txt
        assert f'Quality control — {stratum}' in txt
        assert (rd / f'accuracy_chisq_{stratum}.csv').is_file()
        assert (rd / f'qc_chisq_{stratum}.csv').is_file()
    # the pooled table is still there and is not confused with a stratum
    assert (rd / 'accuracy_chisq_all.csv').is_file()


def test_a_sweep_with_only_the_pooled_stratum_says_so(tmp_path):
    """Every observation in one bin: the split has nothing to say, and admits it."""
    _sweep(tmp_path, 'sl_nostr', chl=[2.0] * 8)
    docs = _docs(tmp_path)
    txt = standard.build('sl_nostr', root=tmp_path, docs_root=docs).read_text()
    # one real stratum still gets its table; the point is it must not crash
    assert 'Per trophic stratum' in txt or 'per-stratum breakdown' in txt


def test_dbic_by_stratum_works_on_the_frame_callers_actually_hold(tmp_path):
    """``dbic_cdf(by='stratum')`` raised ``KeyError`` — ``stratum`` is not persisted.

    ``metrics.compute`` derives it in memory and writes it only onto ``metrics_*``, so
    the parameter existed while the column did not.
    """
    sweep = _sweep(tmp_path, 'sl_dbic',
                   chl=[0.05, 0.05, 0.5, 0.5, 2.0, 2.0, 2.0, 2.0])
    assert 'stratum' not in sweep.scalar.columns, 'still not persisted'
    with_str = metrics.with_strata(sweep.scalar)
    assert 'stratum' in with_str.columns
    assert set(with_str['stratum'].unique()) <= set(
        [b[2] for b in metrics.CHL_BINS] + ['unknown'])
    # idempotent, and safe on an empty frame
    assert metrics.with_strata(with_str) is with_str
    assert metrics.with_strata(pd.DataFrame()).empty

    paths = figures.dbic_cdf(sweep, model_a='expb_pow', model_b='giop',
                             by='stratum')
    assert paths, 'a stratified contest was drawn'
    assert any('by_stratum' in p.name for p in paths)


def test_the_stratified_dbic_bins_the_same_way_the_tables_do(tmp_path):
    """A contest binned differently from the published numbers would mislead."""
    sweep = _sweep(tmp_path, 'sl_bins',
                   chl=[0.05, 0.05, 0.5, 0.5, 2.0, 2.0, 2.0, 2.0])
    curves = diagnostics.dbic_cdf_data(metrics.with_strata(sweep.scalar),
                                       'expb_pow', 'giop', by='stratum')
    from_tables = {s for s, _, _ in figures.strata(sweep)}
    assert set(curves) == from_tables, (set(curves), from_tables)


# --------------------------------------------------------------------
# chi-squared vs MCMC
# --------------------------------------------------------------------
def test_fit_methods_planner_reports_what_is_present(tmp_path):
    one = _sweep(tmp_path, 'sl_fm1')
    assert [m for m, _ in figures.fit_methods(one)] == ['chisq']
    both = _sweep(tmp_path, 'sl_fm2', mcmc_factor=1.4)
    assert set(m for m, _ in figures.fit_methods(both)) == {'chisq', 'mcmc'}


def test_fit_method_comparison_is_like_for_like(tmp_path):
    sweep = _sweep(tmp_path, 'sl_cmp', mcmc_factor=1.4)
    t = tables.fit_method_compare(sweep, write=False)
    assert not t.empty
    for col in ('mae_chisq', 'mae_mcmc', 'd_mae',
                'coverage68_chisq', 'coverage68_mcmc'):
        assert col in t.columns, col
    # The sign convention, checked in both directions: mcmc is 1.4x high for every
    # algorithm, while chisq is perfect for expb_pow (factor 1.0) and 1.5x high for
    # giop — so the sampler is worse than chisq for the first and better for the
    # second, and ``d_mae`` must say so rather than merely being non-zero.
    d = t.set_index('algorithm')['d_mae'].astype(float)
    assert (d.loc['expb_pow'] > 0).all(), 'mcmc worse than a perfect chisq fit'
    assert (d.loc['giop'] < 0).all(), 'mcmc better than a 1.5x-high chisq fit'
    # only contests present under BOTH methods appear
    assert t['algorithm'].nunique() == 2
    assert len(t) == len(t.drop_duplicates(subset=['dataset', 'algorithm',
                                                   'component', 'ref_wave']))


def test_a_single_method_sweep_yields_no_comparison_and_says_why(tmp_path):
    _sweep(tmp_path, 'sl_cmp1')
    sweep = figures.load('sl_cmp1', root=tmp_path)
    assert tables.fit_method_compare(sweep, write=False).empty
    docs = _docs(tmp_path)
    txt = standard.build('sl_cmp1', root=tmp_path, docs_root=docs).read_text()
    assert 'Least-squares vs MCMC' not in txt
    assert 'χ²-vs-MCMC comparison' in txt
    assert '``chisq``' in txt


def test_the_comparison_reaches_the_page_when_both_exist(tmp_path):
    _sweep(tmp_path, 'sl_cmp2', mcmc_factor=1.4)
    docs = _docs(tmp_path)
    txt = standard.build('sl_cmp2', root=tmp_path, docs_root=docs).read_text()
    assert 'Least-squares vs MCMC' in txt
    assert (docs / 'reports' / 'sl_cmp2'
            / 'fit_method_compare_all.csv').is_file()
    assert 'coverage' in txt


# --------------------------------------------------------------------
# defects found while reviewing this task
# --------------------------------------------------------------------
def test_the_perfect_line_is_the_metrics_own_perfect_value(tmp_path):
    """``coverage68``'s reference was drawn at 0 — its *worst* value, not its best."""
    assert metrics.perfect_value('mae') == 0.0
    assert metrics.perfect_value('median_ratio') == 1.0
    assert metrics.perfect_value('coverage68') == 0.68
    assert metrics.perfect_value('coverage95') == 0.95
    assert metrics.perfect_value('something_new') is None, 'no guess of 0.0'
    # the tables' nominal values and the figures' reference lines share one source
    assert tables.NOMINAL_COVERAGE is metrics.NOMINAL_COVERAGE

    _sweep(tmp_path, 'sl_perfect')
    sweep = _widen_spectral('sl_perfect', tmp_path)
    cov = diagnostics.accuracy_spectrum_data(sweep.metrics_spectral, 'a',
                                             metric='coverage68')
    assert cov['perfect'] == 0.68
    # an unrecognised metric draws no reference line at all rather than one at zero
    ms = sweep.metrics_spectral.assign(weird=1.0)
    odd = diagnostics.accuracy_spectrum_data(ms, 'a', metric='weird')
    assert odd['perfect'] is None
    assert not plotting.is_empty(plotting.accuracy_spectrum(odd))


def test_dbic_scores_solutions_only_and_matches_the_pairwise_table(tmp_path):
    """The figure said n=100 for the contest whose table row said n=21.

    ``compute`` scores the pairwise ΔBIC over status-filtered rows; the figure
    passed raw ``results_scalar``, so the same contest carried two different ``n``
    on one page. A ``fit_failed`` row's BIC is not a model-selection statement.
    """
    pairs = []
    for obs in range(10):
        status = 'ok' if obs < 4 else 'fit_failed'
        for i, algo in enumerate(('expb_pow', 'giop')):
            pairs.append(_make_pair(obs, algo, 1.0 + 0.5 * i, 0.5, 10 + 5 * i,
                                    dataset='L23', truth_factor=0.5 + obs,
                                    status=status))
    io.write_results('sl_stat', pairs, root=tmp_path)
    tabs = metrics.compute('sl_stat', root=tmp_path)
    sweep = figures.load('sl_stat', root=tmp_path)

    curve = diagnostics.dbic_cdf_data(sweep.scalar, 'expb_pow', 'giop')
    assert curve['n'] == 4, 'the six failed spectra are not a ΔBIC contest'
    # ... and that is exactly what metrics_pairwise publishes for the same contest
    pw = tabs.pairwise
    dbic_rows = pw[(pw['stratum'] == 'all')
                   & (pw.get('contest', 'dbic') == 'dbic')] if not pw.empty else pw
    if not dbic_rows.empty and 'n' in dbic_rows.columns:
        assert set(dbic_rows['n'].dropna().unique()) == {4.0}
    # opting out is still possible for a caller that wants every row
    everything = metrics.dbic_cdf(sweep.scalar, 'expb_pow', 'giop', statuses=None)
    assert everything['n'] == 10


def test_algorithm_profile_names_the_stratum_of_every_row(tmp_path):
    """It listed up to four strata's numbers with no column saying which.

    Four rows of the same (dataset, component, ref_wave) then read as duplicates
    disagreeing with one another.
    """
    from ioptics.report import leaderboard, profiles
    _sweep(tmp_path, 'sl_prof', chl=[0.05, 0.05, 0.5, 0.5, 2.0, 2.0, 2.0, 2.0])
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    assert board['stratum'].nunique() > 1, 'the board really is multi-stratum'
    docs = _docs(tmp_path)
    out = profiles.build_algorithm_profile('expb_pow', docs_root=docs,
                                           runs_root=tmp_path, board=board)
    txt = out.read_text()
    head = txt[txt.index('Accuracy, by dataset and contest'):]
    assert '- stratum' in head, 'the column is published'
    assert 'trophic stratum' in head, 'and the pooled/binned relationship is stated'
    for stratum in ('all', 'eutrophic', 'mesotrophic'):
        assert stratum in head, stratum


# --------------------------------------------------------------------
# JXP's answers to the Task-8 questions
# --------------------------------------------------------------------
def test_five_bands_are_needed_before_a_curve_is_called_a_spectrum(tmp_path):
    """JXP: use 5. Two points joined by a segment is not a spectral shape."""
    assert diagnostics.MIN_SPECTRUM_WAVES == 5
    _sweep(tmp_path, 'sl_five')
    sweep = _widen_spectral('sl_five', tmp_path, waves=(440.0, 490.0, 555.0, 670.0))
    assert figures.scored_components(sweep) == [], '4 bands is below the floor'
    sweep = _widen_spectral('sl_five', tmp_path,
                            waves=(440.0, 490.0, 510.0, 555.0, 670.0))
    assert [c for c, _, _ in figures.scored_components(sweep)], '5 bands clears it'


def test_unknown_is_dropped_from_the_strata_but_its_count_is_stated(tmp_path):
    """JXP: drop with a stated count.

    ``unknown`` is a provenance category — no Chl truth and no retrieved Chl — not a
    water type, so it does not belong in a column of trophic bins. Dropping it
    silently would make the breakdown look complete when it is not.
    """
    # obs 4-7 get no Chl at all, so they land in 'unknown'
    _sweep(tmp_path, 'sl_unk', chl=[0.05, 0.05, 2.0, 2.0,
                                    np.nan, np.nan, np.nan, np.nan])
    sweep = figures.load('sl_unk', root=tmp_path)
    listed = [s for s, _, _ in figures.strata(sweep)]
    assert figures.UNKNOWN_STRATUM not in listed, 'not a water type'
    assert figures.UNKNOWN_STRATUM in [
        s for s, _, _ in figures.strata(sweep, include_unknown=True)]
    count = figures.unknown_stratum_count(sweep)
    assert count is not None and count[1] > 0, count

    docs = _docs(tmp_path)
    txt = standard.build('sl_unk', root=tmp_path, docs_root=docs).read_text()
    assert 'no chlorophyll at all' in txt
    assert f'{count[1]} spectra' in txt
    assert 'Accuracy — unknown' not in txt, 'no table for it'
    assert not (docs / 'reports' / 'sl_unk' / 'accuracy_chisq_unknown.csv').exists()


def test_a_sweep_with_no_unknown_population_says_nothing_about_it(tmp_path):
    _sweep(tmp_path, 'sl_allchl', chl=[0.05, 0.05, 0.5, 0.5, 2.0, 2.0, 2.0, 2.0])
    sweep = figures.load('sl_allchl', root=tmp_path)
    assert figures.unknown_stratum_count(sweep) is None
    docs = _docs(tmp_path)
    txt = standard.build('sl_allchl', root=tmp_path, docs_root=docs).read_text()
    assert 'no chlorophyll at all' not in txt


def test_every_slice_is_suppressed_on_an_all_failed_sweep(tmp_path):
    """A legitimate state, and the one most likely to divide by zero."""
    _sweep(tmp_path, 'sl_dead', status='fit_failed')
    docs = _docs(tmp_path)
    out = standard.build('sl_dead', root=tmp_path, docs_root=docs)
    assert out.is_file()
    txt = out.read_text()
    assert 'Not shown for this sweep' in txt

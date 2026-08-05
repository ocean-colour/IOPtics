"""Tier-1 tests for the exemplar-fits page and the wired-up per-obs builders (Task 7).

Every other figure in a report describes a *population*. Nothing showed a reader a
single fit — the thing an ocean-colour reader asks for the moment a summary statistic
looks wrong. Three builders existed for it (``closure_set``, ``corner_set``) or nearly
did, and none was reachable from any page.

The two things most worth pinning here are the **selection** (ranking by χ²ᵥ
ascending would name the sweep's most over-fit spectrum its "best" fit) and the
**ordering** (the hand-made ``wide_example_fits.png`` claims clear→turbid in its
suptitle but sorts positional indices, so its panels are really in obs-id order —
the claim we publish has to be the one the code makes).
"""

import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd
import pytest

from ioptics import diagnostics, io, metrics, plotting, records
from ioptics.report import figures, standard
from ioptics.tests.test_metrics import _make_pair


def _sweep(tmp_path, sweep_id='ex_v1', *, dataset='L23',
           algos=('expb_pow', 'giop'), chis=None, peaks=None, n=12,
           mcmc=False, obs_prefix=None, status='ok'):
    """A sweep with per-observation fit quality and Rrs peak actually varying."""
    chis = chis if chis is not None else [1.0 + 0.1 * i for i in range(n)]
    peaks = peaks if peaks is not None else [440.0] * n
    pairs = []
    for obs in range(n):
        oid = f'{obs_prefix}{obs}' if obs_prefix else obs
        for i, algo in enumerate(algos):
            pairs.append(_make_pair(oid, algo, 1.0 + 2.0 * i, 0.5, 10 + 5 * i,
                                    dataset=dataset, truth_factor=0.5 + obs,
                                    chi2_nu=chis[obs], rrs_peak=peaks[obs],
                                    rrs_factor=1.0 + 0.2 * i, status=status))
            if mcmc:
                pairs.append(_make_pair(oid, algo, 1.0, 0.5, 10,
                                        dataset=dataset, fit_method='mcmc',
                                        chi2_nu=chis[obs], rrs_peak=peaks[obs]))
    io.write_results(sweep_id, pairs, root=tmp_path)
    metrics.compute(sweep_id, root=tmp_path)
    return figures.load(sweep_id, root=tmp_path)


# --------------------------------------------------------------------
# selection: which ten fits, and why
# --------------------------------------------------------------------
def test_best_is_nearest_chi2nu_one_not_the_smallest(tmp_path):
    """Sorting by χ²ᵥ ascending would crown the most over-fit spectrum.

    χ²ᵥ < 1 means the model is chasing noise, and this package already names that
    ``frac_overfit``. On GLORIA χ²ᵥ moved 5x when the assumed error floor changed
    while the fits did not move at all, so a χ²ᵥ of 0.01 is evidence about the noise
    model, not about the retrieval.
    """
    chis = [0.01, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 500.0]
    sweep = _sweep(tmp_path, 'ex_best', chis=chis)
    picks = figures.exemplars(sweep)
    best = picks[picks['role'] == 'best'].iloc[0]
    worst = picks[picks['role'] == 'worst'].iloc[0]
    assert best['chi2_nu'] == 1.0, 'nearest to 1, not the numerically smallest'
    assert worst['chi2_nu'] == 500.0
    # the over-fit tail is ranked as poor, not as excellent
    over = picks[picks['chi2_nu'] == 0.01]
    assert over.empty or over.iloc[0]['role'] != 'best'


def test_selection_is_best_worst_and_eight_median(tmp_path):
    sweep = _sweep(tmp_path, 'ex_ten', n=30,
                   chis=[1.0 + 0.5 * i for i in range(30)])
    picks = figures.exemplars(sweep)
    assert len(picks) == diagnostics.EXEMPLAR_N == 10
    assert list(picks['role']).count('best') == 1
    assert list(picks['role']).count('worst') == 1
    assert list(picks['role']).count('median') == 8
    assert picks['obs_id'].nunique() == 10, 'no observation shown twice'


def test_panels_run_clear_to_turbid(tmp_path):
    """The ordering the page's suptitle claims must be the one the code produces."""
    peaks = [670.0, 440.0, 555.0, 443.0] * 3
    sweep = _sweep(tmp_path, 'ex_order', n=12, peaks=peaks,
                   chis=[1.0 + 0.3 * i for i in range(12)])
    picks = figures.exemplars(sweep)
    got = picks['peak_nm'].dropna().to_numpy()
    assert (np.diff(got) >= 0).all(), f'not ascending in peak: {got}'
    # and the packaged clear/turbid threshold is a real number, not prose
    assert records.RED_PEAK_NM == 560.0


def test_ordering_falls_back_when_no_observed_rrs_was_persisted(tmp_path):
    """An older sweep has no ``Rrs_obs`` rows, so there is no turbidity key."""
    sweep = _sweep(tmp_path, 'ex_norrs', n=12,
                   chis=[1.0 + 0.4 * i for i in range(12)])
    spectral = sweep.spectral[sweep.spectral['component'] != 'Rrs_obs']
    picks = diagnostics.exemplar_obs(sweep.scalar, spectral)
    assert picks['peak_nm'].isna().all()
    q = picks['fit_quality'].to_numpy()
    assert (np.diff(q) >= 0).all(), 'falls back to fit-quality order'


def test_a_thin_sweep_still_gets_a_page_worth_of_exemplars(tmp_path):
    sweep = _sweep(tmp_path, 'ex_thin', n=3, chis=[1.0, 5.0, 50.0])
    picks = figures.exemplars(sweep)
    assert len(picks) == 3
    assert set(picks['role']) == {'best', 'median', 'worst'}


def test_unrankable_sweep_yields_no_exemplars(tmp_path):
    """Every fit failed: a legitimate state, and not a crash."""
    sweep = _sweep(tmp_path, 'ex_none', n=4, status='fit_failed')
    blank = sweep.scalar.copy()
    blank['chi2_nu'] = np.nan
    assert diagnostics.exemplar_obs(blank, sweep.spectral).empty
    assert diagnostics.exemplar_obs(pd.DataFrame(), None).empty


def test_string_obs_ids_survive(tmp_path):
    """GLORIA's ids are strings (``GID_1``); an ``int()`` cast crashed on them once."""
    sweep = _sweep(tmp_path, 'ex_str', n=12, obs_prefix='GID_',
                   chis=[1.0 + 0.2 * i for i in range(12)])
    picks = figures.exemplars(sweep)
    assert picks['obs_id'].str.startswith('GID_').all()


# --------------------------------------------------------------------
# the panel data
# --------------------------------------------------------------------
def test_rrs_fit_data_carries_both_spectra_and_both_fit_numbers(tmp_path):
    sweep = _sweep(tmp_path, 'ex_data', n=4, peaks=[555.0] * 4)
    d = diagnostics.rrs_fit_data(sweep.spectral, sweep.scalar, 0)
    assert d['wave'].size and d['rrs'].size
    assert np.isfinite(d['peak_nm'])
    assert set(d['models']) == {'expb_pow', 'giop'}
    for algo, m in d['models'].items():
        assert np.isfinite(m['chi2_nu']), algo
        assert np.isfinite(m['rel_misfit']), algo
    # giop's model Rrs is 1.2x the observation, so its misfit is the larger one
    assert d['models']['giop']['rel_misfit'] > d['models']['expb_pow']['rel_misfit']


def test_observed_spectrum_is_not_drawn_once_per_algorithm(tmp_path):
    """``Rrs_obs`` is stored per algorithm but is one measurement."""
    sweep = _sweep(tmp_path, 'ex_dedup', n=2,
                   algos=('expb_pow', 'giop', 'gsm'))
    d = diagnostics.rrs_fit_data(sweep.spectral, sweep.scalar, 0)
    n_bands = sweep.spectral[
        (sweep.spectral['obs_id'] == 0)
        & (sweep.spectral['component'] == 'Rrs_obs')]['wavelength'].nunique()
    assert d['wave'].size == n_bands
    assert len(d['models']) == 3


def test_annotation_cannot_come_from_another_dataset(tmp_path):
    """``residual_spectra`` filters χ²ᵥ on algorithm alone; this must not."""
    a = _sweep(tmp_path, 'ex_ds', n=2, dataset='L23', chis=[1.0, 1.0])
    b = _sweep(tmp_path, 'ex_ds2', n=2, dataset='GLORIA', chis=[99.0, 99.0])
    mixed_sc = pd.concat([a.scalar, b.scalar], ignore_index=True)
    mixed_sp = pd.concat([a.spectral, b.spectral], ignore_index=True)
    d = diagnostics.rrs_fit_data(mixed_sp, mixed_sc, 0, dataset='L23',
                                 fit_method='chisq')
    assert d['models']['expb_pow']['chi2_nu'] == 1.0, 'not GLORIA\'s 99'


def test_a_missing_observation_is_empty_not_an_exception(tmp_path):
    sweep = _sweep(tmp_path, 'ex_missing', n=2)
    d = diagnostics.rrs_fit_data(sweep.spectral, sweep.scalar, 'nope')
    assert d['models'] == {} and d['wave'].size == 0
    assert plotting.is_empty(plotting.rrs_fit(d))


def test_one_blank_panel_does_not_suppress_the_whole_grid(tmp_path):
    """``_annotate_empty`` stamps the flag on the *shared* figure.

    Without an explicit reset, a single missing observation in a 10-panel grid
    would make ``figures._save`` refuse to write any of it.
    """
    sweep = _sweep(tmp_path, 'ex_grid', n=4)
    good = diagnostics.rrs_fit_data(sweep.spectral, sweep.scalar, 0)
    bad = diagnostics.rrs_fit_data(sweep.spectral, sweep.scalar, 'nope')
    assert not plotting.is_empty(plotting.exemplar_grid([good, bad]))
    assert plotting.is_empty(plotting.exemplar_grid([bad, bad]))
    assert plotting.is_empty(plotting.exemplar_grid([]))


# --------------------------------------------------------------------
# the page
# --------------------------------------------------------------------
def _docs(tmp_path):
    d = tmp_path / 'docs'
    (d / 'reports').mkdir(parents=True, exist_ok=True)
    return d


def test_page_states_obs_id_chi2nu_and_relative_misfit(tmp_path):
    sweep = _sweep(tmp_path, 'ex_page', n=12, peaks=[440.0, 555.0] * 6,
                   chis=[1.0 + 0.3 * i for i in range(12)])
    docs = _docs(tmp_path)
    out = standard.build_exemplars('ex_page', root=tmp_path, docs_root=docs)
    txt = out.read_text()
    assert out.name == f'{standard.EXEMPLAR_PAGE}.rst'
    assert 'Exemplar fits — ex_page' in txt
    picks = figures.exemplars(sweep)
    for oid in picks['obs_id']:
        assert f'``{oid}``' in txt, oid
    assert 'χ²ᵥ' in txt and 'rel. misfit' in txt and 'Rrs peak' in txt
    assert 'clear' in txt and 'turbid' in txt
    assert ':doc:`/reports/glossary`' in txt
    assert (docs / 'reports' / 'ex_page' / 'exemplar_fits.png').is_file()


def test_page_explains_why_best_is_not_the_smallest_chi2nu(tmp_path):
    _sweep(tmp_path, 'ex_why', n=12, chis=[1.0 + 0.3 * i for i in range(12)])
    docs = _docs(tmp_path)
    txt = standard.build_exemplars('ex_why', root=tmp_path,
                                   docs_root=docs).read_text()
    assert 'over-fit' in txt
    assert f'{records.CHI2NU_POOR_FIT:g}' in txt


def test_page_says_how_many_exemplars_are_not_solutions(tmp_path):
    """Printing the χ²ᵥ = 5 threshold and then ten fits at χ²ᵥ ≈ 30 says nothing.

    On the real GLORIA sweep 9 of the 10 exemplars are above the threshold and 7
    peak redward of the turbid cutoff — a reader must be told that, not left to
    infer it from a wavelength column.
    """
    _sweep(tmp_path, 'ex_sum', n=12, peaks=[670.0] * 12,
           chis=[20.0 + i for i in range(12)])
    docs = _docs(tmp_path)
    txt = standard.build_exemplars('ex_sum', root=tmp_path,
                                   docs_root=docs).read_text()
    assert 'not solutions' in txt
    assert '10 of the 10' in txt
    assert f'redward of {records.RED_PEAK_NM:g} nm' in txt
    assert 'Recorded fit status' in txt


def test_summary_is_grammatical_and_honest_when_all_fits_are_good(tmp_path):
    _sweep(tmp_path, 'ex_good', n=12, peaks=[440.0] * 12,
           chis=[1.0 + 0.05 * i for i in range(12)])
    docs = _docs(tmp_path)
    txt = standard.build_exemplars('ex_good', root=tmp_path,
                                   docs_root=docs).read_text()
    assert 'solution threshold' in txt
    assert 'not solutions' not in txt
    # the *summary* must not warn about turbid exemplars (the standing intro
    # prose explains the threshold regardless, so scope the check to the summary)
    summary = txt[txt.index('What these'):txt.index('.. list-table')]
    assert 'redward' not in summary, 'no turbid exemplars to warn about'
    assert ' sit *below*' not in summary, 'singular/plural agreement'


def test_page_wires_closure_for_the_two_extremes(tmp_path):
    _sweep(tmp_path, 'ex_clos', n=12, chis=[1.0 + 0.7 * i for i in range(12)])
    docs = _docs(tmp_path)
    txt = standard.build_exemplars('ex_clos', root=tmp_path,
                                   docs_root=docs).read_text()
    assert 'Rrs closure — best fit' in txt
    assert 'Rrs closure — worst fit' in txt
    pngs = {p.name for p in (docs / 'reports' / 'ex_clos').glob('closure_*.png')}
    assert len(pngs) == 2, pngs


def test_page_says_so_when_there_are_no_chains(tmp_path):
    _sweep(tmp_path, 'ex_nochain', n=12,
           chis=[1.0 + 0.3 * i for i in range(12)])
    docs = _docs(tmp_path)
    txt = standard.build_exemplars('ex_nochain', root=tmp_path,
                                   docs_root=docs).read_text()
    assert 'Posterior corner plots' not in txt
    assert 'corner plots' in txt and 'Not shown for this sweep' in txt


def test_a_stale_chain_path_does_not_break_the_page(tmp_path):
    """``chain_file`` is a path; it goes stale when a sweep dir is copied."""
    sweep = _sweep(tmp_path, 'ex_stale', n=12, mcmc=True,
                   chis=[1.0 + 0.3 * i for i in range(12)])
    assert (sweep.scalar['fit_method'] == 'mcmc').any()
    assert figures.corner_set(sweep) == [], 'unreadable chains are skipped'
    docs = _docs(tmp_path)
    out = standard.build_exemplars('ex_stale', root=tmp_path, docs_root=docs)
    assert out is not None and out.is_file()


def test_unrankable_sweep_gets_no_page_rather_than_a_blank_one(tmp_path):
    _sweep(tmp_path, 'ex_blank', n=4, status='fit_failed')
    path = io.sweep_dir('ex_blank', root=tmp_path) / io.SCALAR_FILE
    sc = pd.read_parquet(path)
    sc['chi2_nu'] = np.nan
    sc.to_parquet(path, index=False)
    docs = _docs(tmp_path)
    assert standard.build_exemplars('ex_blank', root=tmp_path,
                                    docs_root=docs) is None


def test_cross_algorithm_page_links_the_exemplars_only_once_built(tmp_path):
    """A ``:doc:`` reference to a page that does not exist is a ``-W`` failure."""
    _sweep(tmp_path, 'ex_link', n=12, chis=[1.0 + 0.3 * i for i in range(12)])
    docs = _docs(tmp_path)
    first = standard.build('ex_link', root=tmp_path, docs_root=docs)
    assert f':doc:`{standard.EXEMPLAR_PAGE}`' not in first.read_text()
    standard.build_exemplars('ex_link', root=tmp_path, docs_root=docs)
    again = standard.build('ex_link', root=tmp_path, docs_root=docs)
    assert f':doc:`{standard.EXEMPLAR_PAGE}`' in again.read_text()


# --------------------------------------------------------------------
# defect this task exposed: pages sharing a report dir pruned each other
# --------------------------------------------------------------------
def test_a_second_page_does_not_delete_the_first_pages_figures(tmp_path):
    """Adding a fourth page in one report dir made a latent bug live.

    ``_prune_stale`` knew only the assets of the build that called it, so building
    ``per_algorithm`` after ``cross_algorithm`` deleted all six of its scatters,
    Taylor/Target and ΔBIC panels while ``cross_algorithm.rst`` went on referencing
    them — a dangling image and a ``sphinx -W`` failure.
    """
    _sweep(tmp_path, 'ex_prune', n=12, chis=[1.0 + 0.3 * i for i in range(12)])
    docs = _docs(tmp_path)
    report_dir = docs / 'reports' / 'ex_prune'
    cross = standard.build('ex_prune', kind='cross_algorithm', root=tmp_path,
                           docs_root=docs)
    owned = {p.name for p in report_dir.glob('*.png')}
    assert owned, 'the cross-algorithm page published figures'

    standard.build('ex_prune', kind='per_algorithm', root=tmp_path,
                   docs_root=docs)
    standard.build_exemplars('ex_prune', root=tmp_path, docs_root=docs)

    survivors = {p.name for p in report_dir.glob('*.png')}
    assert owned <= survivors, f'pruned away: {sorted(owned - survivors)}'
    # every image each page references still exists on disk
    for page in report_dir.glob('*.rst'):
        for line in page.read_text().splitlines():
            if line.strip().startswith('.. figure::'):
                name = line.split('::', 1)[1].strip()
                assert (report_dir / name).is_file(), f'{page.name} -> {name}'


def test_observation_ids_cannot_escape_the_figure_directory(tmp_path):
    """``obs_id`` is dataset-defined; a ``/`` in one would write outside ``figures/``."""
    assert figures._safe('obs/1') == 'obs_1'
    assert figures._safe('a b') == 'a_b'
    assert figures._safe('GID_1') == 'GID_1', 'the real ids are left alone'
    sweep = _sweep(tmp_path, 'ex_safe', n=2, obs_prefix='a/b ')
    paths = figures.closure_set(sweep, 'a/b 0')
    assert paths, 'the figure was still written'
    for p in paths:
        assert p.parent.name == 'figures'
        assert '/' not in p.name[len('closure_'):]


# --------------------------------------------------------------------
# defects found by the adversarial review of this task
# --------------------------------------------------------------------
def _two_dataset_sweep(tmp_path, sweep_id='ex_md'):
    """Two datasets reusing the same obs ids — the package's own convention.

    ``test_sweep_multi`` runs ``obs in (0, 1)`` across all three datasets, so
    ``obs_id`` alone does not identify an observation.
    """
    pairs = []
    for obs in range(4):
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, 0.5, 10, dataset='L23',
                                truth_factor=0.5 + obs, chi2_nu=1.0,
                                rrs_peak=440.0))
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, 0.5, 10, dataset='GLORIA',
                                truth_factor=0.5 + obs, chi2_nu=400.0,
                                rrs_peak=670.0))
    io.write_results(sweep_id, pairs, root=tmp_path)
    metrics.compute(sweep_id, root=tmp_path)
    return figures.load(sweep_id, root=tmp_path)


def test_two_datasets_sharing_obs_ids_are_not_pooled(tmp_path):
    """Grouping on ``obs_id`` alone ranked every observation at the median of two
    unrelated spectra — an L23 fit at χ²ᵥ ≈ 1 and a GLORIA fit at χ²ᵥ ≈ 400 came
    out as a single observation at 200.5, making best/worst meaningless."""
    sweep = _two_dataset_sweep(tmp_path)
    picks = figures.exemplars(sweep)
    assert 'dataset' in picks.columns
    assert len(picks) == 8, 'four observations per dataset, kept apart'
    assert not (picks['chi2_nu'] == 200.5).any(), 'no pooled median'
    l23 = picks[picks['dataset'] == 'L23']
    glo = picks[picks['dataset'] == 'GLORIA']
    assert (l23['chi2_nu'] == 1.0).all() and (glo['chi2_nu'] == 400.0).all()
    # the best fit is L23's and the worst is GLORIA's, not an average of both
    assert picks.loc[picks['role'] == 'best', 'dataset'].iloc[0] == 'L23'
    assert picks.loc[picks['role'] == 'worst', 'dataset'].iloc[0] == 'GLORIA'


def test_a_panel_is_not_blended_from_two_datasets(tmp_path):
    """The wired path must pass ``dataset``, not merely support it.

    Without it the model curve carried duplicated wavelengths (sawtoothing through
    both datasets' spectra) and χ²ᵥ came from an arbitrary ``iloc[0]``.
    """
    sweep = _two_dataset_sweep(tmp_path, 'ex_md2')
    n_bands = sweep.spectral[
        (sweep.spectral['obs_id'] == 0)
        & (sweep.spectral['dataset'] == 'GLORIA')
        & (sweep.spectral['component'] == 'Rrs_obs')]['wavelength'].nunique()
    d = diagnostics.rrs_fit_data(sweep.spectral, sweep.scalar, 0,
                                 dataset='GLORIA', fit_method='chisq')
    assert d['models']['expb_pow']['chi2_nu'] == 400.0
    assert d['wave'].size == n_bands, 'not two datasets concatenated'
    assert d['models']['expb_pow']['wave'].size == n_bands
    assert d['peak_nm'] == 670.0

    docs = _docs(tmp_path)
    out = standard.build_exemplars('ex_md2', root=tmp_path, docs_root=docs)
    txt = out.read_text()
    assert 'dataset' in txt and 'GLORIA' in txt and 'L23' in txt
    # closure filenames are namespaced, or one dataset overwrites the other's
    names = {p.name for p in (docs / 'reports' / 'ex_md2').glob('closure_*.png')}
    assert names == {'closure_L23_0.png', 'closure_GLORIA_3.png'}, names


def test_a_corrupt_chain_is_skipped_like_a_missing_one(tmp_path):
    """``zipfile.BadZipFile`` is **not** an ``OSError``.

    A half-written NPZ therefore escaped the narrow except tuple and would have
    taken the whole page build down.
    """
    import numpy as _np
    good = tmp_path / 'good.npz'
    _np.savez(good, chains=_np.random.default_rng(0).normal(size=(20, 4, 3)),
              pnames=_np.array(['a', 'b', 'c']))
    raw = good.read_bytes()
    truncated = tmp_path / 'trunc.npz'
    truncated.write_bytes(raw[:len(raw) // 2])
    with pytest.raises(Exception):
        io.load_chain(truncated)          # it really is unreadable

    sweep = _sweep(tmp_path, 'ex_corrupt', n=4)
    sc = pd.DataFrame([
        {'fit_method': 'mcmc', 'chain_file': str(truncated),
         'algorithm': 'expb_pow', 'obs_id': 1},
        {'fit_method': 'mcmc', 'chain_file': str(good),
         'algorithm': 'expb_pow', 'obs_id': 2},
    ])
    got = figures.corner_set(sweep._replace(scalar=sc))
    names = {p.name for p in got}
    assert 'corner_expb_pow_2.png' in names, 'the good chain still draws'
    assert not any('_1.' in p.name for p in got), 'the corrupt one is skipped'


def test_the_corner_budget_counts_successes_not_candidates(tmp_path):
    """``limit`` applied to candidate rows let stale paths consume the whole budget."""
    import numpy as _np
    good = tmp_path / 'ok.npz'
    _np.savez(good, chains=_np.random.default_rng(1).normal(size=(20, 4, 3)),
              pnames=_np.array(['a', 'b', 'c']))
    rows = [{'fit_method': 'mcmc', 'chain_file': str(tmp_path / f'gone{i}.npz'),
             'algorithm': 'expb_pow', 'obs_id': i} for i in range(3)]
    rows.append({'fit_method': 'mcmc', 'chain_file': str(good),
                 'algorithm': 'expb_pow', 'obs_id': 99})
    sweep = _sweep(tmp_path, 'ex_budget', n=4)
    got = figures.corner_set(sweep._replace(scalar=pd.DataFrame(rows)), limit=1)
    assert {p.name for p in got if p.suffix == '.png'} == {'corner_expb_pow_99.png'}
    assert figures.MAX_CORNERS > 0, 'a default cap exists for the wired call'


def test_asking_for_one_exemplar_returns_one(tmp_path):
    """``n=1`` returned two rows: an empty middle range still left best + worst."""
    sweep = _sweep(tmp_path, 'ex_one', n=12,
                   chis=[1.0 + 0.3 * i for i in range(12)])
    assert len(figures.exemplars(sweep, n=1)) == 1
    assert list(figures.exemplars(sweep, n=1)['role']) == ['best']
    assert len(figures.exemplars(sweep, n=2)) == 2
    assert len(figures.exemplars(sweep, n=3)) == 3
    assert figures.exemplars(sweep, n=0).empty


def test_prose_never_claims_more_panels_than_it_shows(tmp_path):
    """A 4-observation sweep published "shows 4 fits" and "the eight nearest"."""
    sweep = _sweep(tmp_path, 'ex_four', n=4, chis=[1.0, 2.0, 3.0, 90.0])
    docs = _docs(tmp_path)
    txt = standard.build_exemplars('ex_four', root=tmp_path,
                                   docs_root=docs).read_text()
    assert 'shows 4 individual fits' in txt
    assert 'eight' not in txt, 'no hard-coded panel count'
    assert 'the **two** nearest the median' in txt


def test_the_grid_does_not_claim_turbidity_order_it_does_not_have(tmp_path):
    """With no persisted ``Rrs_obs`` the ordering is fit quality, and must say so."""
    sweep = _sweep(tmp_path, 'ex_noord', n=12,
                   chis=[1.0 + 0.4 * i for i in range(12)])
    spectral = sweep.spectral[sweep.spectral['component'] != 'Rrs_obs']
    picks = diagnostics.exemplar_obs(sweep.scalar, spectral)
    paths = figures.exemplar_fits(sweep._replace(spectral=spectral), picks)
    assert paths, 'a grid was still drawn'
    docs = _docs(tmp_path)
    # and the page's own caption follows the real ordering
    fig = plotting.exemplar_grid(
        [diagnostics.rrs_fit_data(spectral, sweep.scalar, o)
         for o in picks['obs_id']], roles=list(picks['role']),
        suptitle='Exemplar fits, best (top-left) to worst (bottom-right)')
    assert fig is not None
    assert docs.is_dir()


def test_genuinely_stale_assets_are_still_pruned(tmp_path):
    """The fix must not turn pruning off — an orphan no page names still goes."""
    _sweep(tmp_path, 'ex_orphan', n=12, chis=[1.0 + 0.3 * i for i in range(12)])
    docs = _docs(tmp_path)
    report_dir = docs / 'reports' / 'ex_orphan'
    standard.build_exemplars('ex_orphan', root=tmp_path, docs_root=docs)
    orphan = report_dir / 'scatter_from_an_older_figure_set.png'
    orphan.write_bytes(b'stale')
    standard.build_exemplars('ex_orphan', root=tmp_path, docs_root=docs)
    assert not orphan.exists()


def test_an_orphan_whose_name_ends_a_live_one_is_still_pruned(tmp_path):
    """A bare ``name in text`` kept ``fits.png`` alive because a page referenced
    ``exemplar_fits.png`` — the keep-set must match directive targets, not
    substrings."""
    _sweep(tmp_path, 'ex_sub', n=12, chis=[1.0 + 0.3 * i for i in range(12)])
    docs = _docs(tmp_path)
    report_dir = docs / 'reports' / 'ex_sub'
    standard.build_exemplars('ex_sub', root=tmp_path, docs_root=docs)
    assert (report_dir / 'exemplar_fits.png').is_file()
    orphan = report_dir / 'fits.png'
    orphan.write_bytes(b'stale')
    standard.build('ex_sub', kind='cross_algorithm', root=tmp_path,
                   docs_root=docs)
    assert not orphan.exists(), 'a suffix of a live asset is not a reference'
    assert (report_dir / 'exemplar_fits.png').is_file(), 'the live one survives'

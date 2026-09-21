"""Tier-1 tests for the RT-ladder page (``ioptics.report.rt_ladder``, rt_tests task 14).

A synthetic five-rung sweep — every row the same parameterization, the rungs
differing only in how far they sit from truth and in BIC — is written to a
``tmp_path`` runs root with both a χ² and an MCMC population, scored, and the
page built into a ``tmp_path`` docs tree.  No models, no data, no real docs tree.
"""

import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd
import pytest

from ioptics import diagnostics, io, metrics, plotting
from ioptics.algorithms import registry
from ioptics.report import figures, rt_ladder
from ioptics.tests.conftest import needs_sphinx
from ioptics.tests.test_metrics import _make_pair
from ioptics.tests.test_report_standard import _scaffold_min_docs

_SID = 'rt_ladder_v1'
RUNGS = list(registry.RT_VARIANT_SEED)

#: How far each rung sits above truth (1.0 = perfect) and its BIC. The full
#: inelastic stack is the most accurate and the best-supported, the elastic
#: rungs the worst — the shape the real L23 arm has for bb_p.
_FACTOR = {r: f for r, f in zip(RUNGS, (1.6, 1.5, 1.2, 1.05, 1.0))}
_BIC = {r: b for r, b in zip(RUNGS, (30.0, 28.0, 22.0, 15.0, 12.0))}


def _build_sweep(tmp_path, *, n_obs=4):
    chl = {0: 0.05, 1: 0.5, 2: 2.0, 3: 0.3}
    spread = {0: 0.5, 1: 1.0, 2: 2.5, 3: 1.5}
    pairs = []
    for obs in range(n_obs):
        for rung in RUNGS:
            for fm in ('chisq', 'mcmc'):
                pairs.append(_make_pair(
                    obs, rung, _FACTOR[rung], chl[obs], _BIC[rung] + obs,
                    fit_method=fm, truth_factor=spread[obs]))
    io.write_results(_SID, pairs, root=tmp_path)
    metrics.compute(_SID, root=tmp_path, dbic_pair=registry.RT_DBIC_PAIR)
    return figures.load(_SID, root=tmp_path)


# --------------------------------------------------------------------
# diagnostics + plotting primitives
# --------------------------------------------------------------------
def test_fractional_change_data_is_truth_free_and_pairs_by_spectrum(tmp_path):
    sw = _build_sweep(tmp_path)
    a, b = registry.RT_DBIC_PAIR
    got = diagnostics.fractional_change_data(sw.spectral, a, b, ref=443.0)
    assert got['band'] == 443.0
    for comp in ('a_ph', 'a_dg', 'bb_p'):
        vals = got['changes'][comp]
        assert got['n'][comp] == 4 == vals.size
        # every rung is truth × factor, so b/a − 1 is the factor ratio − 1
        expect = _FACTOR[b] / _FACTOR[a] - 1.0
        assert np.allclose(vals, expect)


def test_fractional_change_data_handles_no_common_band(tmp_path):
    sw = _build_sweep(tmp_path)
    a, b = registry.RT_DBIC_PAIR
    got = diagnostics.fractional_change_data(sw.spectral, a, b, ref=900.0)
    assert got['band'] is None and got['changes'] == {}


def test_fractional_change_hist_and_dbic_hist_render_and_flag_empty(tmp_path):
    sw = _build_sweep(tmp_path)
    a, b = registry.RT_DBIC_PAIR
    fig = plotting.fractional_change_hist(
        diagnostics.fractional_change_data(sw.spectral, a, b, ref=443.0))
    assert not plotting.is_empty(fig)
    assert len(fig.axes) == 3
    empty = plotting.fractional_change_hist({'changes': {}})
    assert plotting.is_empty(empty)
    curve = diagnostics.dbic_cdf_data(sw.scalar, b, a, fit_method='mcmc')
    fig2 = plotting.dbic_hist(curve)
    assert not plotting.is_empty(fig2)
    assert plotting.is_empty(plotting.dbic_hist({'dbic': []}))


# --------------------------------------------------------------------
# figure builders and tables
# --------------------------------------------------------------------
def test_rt_figure_builders_write_png_and_pdf(tmp_path):
    sw = _build_sweep(tmp_path)
    a, b = registry.RT_DBIC_PAIR
    fc = figures.rt_fractional_change(sw, model_a=a, model_b=b)
    assert fc and {p.suffix for p in fc} == {'.png', '.pdf'}
    assert fc[0].name.startswith('frac_change_443_')
    h = figures.dbic_hist(sw, model_a=b, model_b=a)
    c = figures.dbic_cdf_method(sw, model_a=b, model_b=a)
    assert h and c and h[0].name.startswith('dbic_hist_') \
        and c[0].name.startswith('dbic_cdf_')
    assert c[0].name.endswith('_mcmc.png')


def test_ladder_table_has_one_row_per_rung_in_ladder_order(tmp_path):
    sw = _build_sweep(tmp_path)
    df = rt_ladder.ladder_table(sw, fit_method='mcmc')
    assert list(df['rung']) == RUNGS
    assert (df['label'] == [rt_ladder.LABELS[r] for r in RUNGS]).all()
    assert {'frac_ok', 'chi2_nu_median', 'a_440_mae', 'bb_p_555_bias',
            'a_ph_440_cov68'} <= set(df.columns)
    # the most accurate rung is the last one, by construction of the fixture
    assert df['a_440_mae'].iloc[-1] < df['a_440_mae'].iloc[0]
    csv = figures.subdir(sw, 'tables') / 'rt_ladder_mcmc_all.csv'
    assert csv.is_file()
    assert len(pd.read_csv(csv)) == len(RUNGS)


def test_dbic_contests_marks_the_configured_pair(tmp_path):
    sw = _build_sweep(tmp_path)
    df = rt_ladder.dbic_contests(sw, fit_method='mcmc')
    assert not df.empty and df['configured'].sum() == 1
    row = df[df['configured']].iloc[0]
    assert {row['model_a'], row['model_b']} == set(registry.RT_DBIC_PAIR)
    # fixture: the inelastic stack has the lower BIC everywhere
    a, b = registry.RT_DBIC_PAIR
    if row['model_a'] == a:
        assert row['frac_favor_b'] == 1.0
    else:
        assert row['frac_favor_a'] == 1.0


# --------------------------------------------------------------------
# the page
# --------------------------------------------------------------------
def test_build_writes_page_assets_and_limitations(tmp_path):
    _build_sweep(tmp_path)
    docs = tmp_path / 'docs'
    out = rt_ladder.build(_SID, root=tmp_path, docs_root=docs)
    assert out == docs / 'reports' / _SID / 'rt_ladder.rst'
    rd = out.parent
    text = out.read_text(encoding='utf-8')
    assert f':Sweep: {_SID}' in text
    assert 'RT ladder' in text.splitlines()[1]
    # the mandated limitations are on the page, verbatim enough to grep
    for must in ('θ_v = 0', 'a_cdom = 0.8 × a_dg', 'ed_l23.npz',
                 'corrections=False', 'single-Gaussian', 'no_CDOMfl_truth',
                 'DomainWarning', 'leaderboard: false'):
        assert must in text, must
    # assets: headline figure, ladder tables, ΔBIC panels, QC + accuracy tables
    assert any(p.name.startswith('frac_change_443_') for p in rd.iterdir())
    for csv in ('rt_ladder_mcmc_all.csv', 'rt_ladder_chisq_all.csv',
                'dbic_contests_mcmc_all.csv', 'qc_mcmc_all.csv',
                'accuracy_mcmc_all.csv', 'head_to_head_mcmc_all.csv'):
        assert (rd / csv).is_file(), csv
    assert any(p.name.startswith('dbic_cdf_') and p.name.endswith('_mcmc.png')
               for p in rd.iterdir())
    assert any(p.name.startswith('dbic_hist_') for p in rd.iterdir())
    assert (rd / 'scatter_a_440.png').is_file()
    # the landing page is only globbed, never rewritten with a leaderboard
    idx = (docs / 'reports' / 'index.rst').read_text()
    assert ':glob:' in idx and 'LEADERBOARD_START' not in idx


def test_build_is_idempotent_and_prunes_its_own_stale_assets(tmp_path):
    _build_sweep(tmp_path)
    docs = tmp_path / 'docs'
    out = rt_ladder.build(_SID, root=tmp_path, docs_root=docs)
    stale = out.parent / 'scatter_zzz_999.png'
    stale.write_bytes(b'x')
    out2 = rt_ladder.build(_SID, root=tmp_path, docs_root=docs)
    assert out2 == out and not stale.exists()


def test_build_without_the_configured_pair_says_so(tmp_path):
    _build_sweep(tmp_path)
    out = rt_ladder.build(_SID, root=tmp_path, docs_root=tmp_path / 'docs',
                          pair=('expb_pow_hyb_el', 'not_a_rung'))
    text = out.read_text(encoding='utf-8')
    assert 'not fully present in this sweep' in text


@needs_sphinx
def test_page_renders_under_sphinx(tmp_path):
    import subprocess
    import sys

    _build_sweep(tmp_path)
    src = tmp_path / 'docs'
    rt_ladder.build(_SID, root=tmp_path, docs_root=src)
    _scaffold_min_docs(src)
    proc = subprocess.run(
        [sys.executable, '-m', 'sphinx', '-W', '-q', '-b', 'html',
         str(src), str(src / '_build')],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (src / '_build' / 'reports' / _SID / 'rt_ladder.html').is_file()


# --------------------------------------------------------------------
# PAB run1k consistency check (rt_tests task 13) and its page section
# --------------------------------------------------------------------
def _load_pab_consistency():
    import importlib.util
    from pathlib import Path
    path = (Path(__file__).resolve().parents[1] / 'runs' / 'prototypes' / 'rt_tests'
            / 'pab_consistency.py')
    spec = importlib.util.spec_from_file_location('pab_consistency', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_chains(rng, medians, names, nstep=200, nwalk=4):
    cols = [rng.normal(medians[n], 0.01, size=(nstep, nwalk)) for n in names]
    return np.stack(cols, axis=-1)


def test_pab_consistency_compare_and_summarise():
    pc = _load_pab_consistency()
    rng = np.random.default_rng(0)
    wave = np.linspace(400, 700, 136)
    rrs = 0.005 + 0.001 * np.sin(wave / 40.0)
    rows = []
    for i in range(6):
        pab_med = {'Adg': -1.5 + 0.1 * i, 'Sdg': 0.015, 'Aph': -1.2 + 0.05 * i,
                   'Bnw': -2.3, 'beta': 1.0}
        ours_med = dict(pab_med)
        ours_med['Aph'] += 0.02          # a small systematic offset
        ours_med['B_p'] = 0.02
        ours = {'chains': _fake_chains(rng, ours_med, pc.SHARED + ('B_p',)),
                'pnames': np.array(pc.SHARED + ('B_p',)), 'wave': wave,
                'obs_Rrs': rrs, 'varRrs': (0.02 * rrs) ** 2}
        theirs = {'chains': _fake_chains(rng, pab_med, pc.SHARED),
                  'param_names': np.array(pc.SHARED), 'wave': wave,
                  'Rrs': rrs, 'varRrs': (0.02 * rrs) ** 2}
        rows.append(pc.compare_pixel(ours, theirs))
    df = pd.DataFrame(rows)
    assert (df['n_bands_common'] == 136).all()
    assert df['max_abs_dRrs'].max() == 0.0 and df['max_abs_dvarRrs'].max() == 0.0
    summ = pc.summarise(df)
    aph = summ[summ.quantity == 'Aph'].iloc[0]
    assert abs(aph['median_diff'] - 0.02) < 0.01 and aph['correlation'] > 0.99
    chl = summ[summ.quantity.str.startswith('Chl')].iloc[0]
    assert abs(chl['median_diff'] - 10 ** 0.02) < 0.02     # ratio = 10**dAph
    assert set(summ['quantity']) >= set(pc.SHARED)


def test_page_carries_the_pab_consistency_section_when_the_table_exists(tmp_path):
    sw = _build_sweep(tmp_path)
    tables = figures.subdir(sw, 'tables')
    pd.DataFrame([{'quantity': 'Aph', 'scale': 'log10', 'n': 99, 'correlation': 0.97,
                   'median_diff': 0.01, 'p16_diff': -0.05, 'p84_diff': 0.08,
                   'median_abs_diff': 0.03}]).to_csv(
        tables / 'pab_consistency_summary.csv', index=False)
    out = rt_ladder.build(_SID, root=tmp_path, docs_root=tmp_path / 'docs')
    text = out.read_text(encoding='utf-8')
    assert 'Consistency with PAB' in text
    assert (out.parent / 'pab_consistency_summary.csv').is_file()

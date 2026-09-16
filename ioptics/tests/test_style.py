"""Tier-1 tests for ``ioptics.style`` — the shared look and the per-algorithm
visual identity.

The identity tests are the important ones. Before this module an algorithm's
colour came from its row order *within one figure*, so the same model was a
different colour on different pages and adding an algorithm reshuffled every other
one. These tests pin the three properties that fixes: an algorithm's style is
independent of what it is plotted alongside, stable across processes (so it cannot
depend on Python's per-process hash salt), and distinct among the algorithms
IOPtics ships.
"""

import subprocess
import sys

import matplotlib
matplotlib.use('Agg')                       # headless; no display
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import pytest

from ioptics import plotting, style


# --------------------------------------------------------------------
# per-algorithm identity
# --------------------------------------------------------------------
def test_algo_style_is_independent_of_the_company_it_keeps():
    """Adding an algorithm must not restyle the others (the original defect)."""
    before = {a: style.algo_style(a) for a in ('expb_pow', 'giop')}
    # ... now a sweep with four more algorithms, queried in a different order
    for a in ('expb_powflex', 'gsm', 'brand_new_model', 'expb_pow2'):
        style.algo_style(a)
    after = {a: style.algo_style(a) for a in ('giop', 'expb_pow')}
    assert after == before


def test_algo_style_is_stable_across_processes():
    """An unregistered name must not depend on Python's per-process hash salt.

    ``hash('x')`` differs between interpreters unless PYTHONHASHSEED is pinned, so
    a hash-derived colour would silently change from run to run — and a reader who
    learned "this model is the teal one" would be misled by the next report.
    """
    code = ('from ioptics import style; '
            "print(style.algo_color('some_unregistered_model'), "
            "style.algo_marker('some_unregistered_model'))")
    out = subprocess.run([sys.executable, '-c', code], capture_output=True,
                         text=True, check=True).stdout.split()
    assert out == [style.algo_color('some_unregistered_model'),
                   style.algo_marker('some_unregistered_model')]


def test_shipped_algorithms_are_visually_distinct():
    """The six algorithms IOPtics ships must not collide with each other."""
    shipped = ('expb_pow', 'giop', 'gsm', 'expb_pow2', 'expb_pow2flat',
               'expb_powflex')
    pairs = [(style.algo_color(a), style.algo_marker(a)) for a in shipped]
    assert len(set(pairs)) == len(shipped)
    # colour alone should also separate them, so a colour legend is unambiguous
    assert len({c for c, _ in pairs}) == len(shipped)


def test_marker_carries_the_same_information_as_colour():
    """Greyscale / colour-blind safety: never rely on colour alone."""
    for a in ('expb_pow', 'giop', 'unknown_thing'):
        st = style.algo_style(a)
        assert st['marker'] in style.SERIES_MARKERS
        assert st['color'] in style.SERIES_COLORS
        assert st['linestyle'] in style.SERIES_LINESTYLES


def test_linestyle_separates_the_curves_that_actually_coincide():
    """Markers separate points; only a linestyle separates overlapping *curves*.

    GLORIA's four turbid variants model nearly identical Rrs, so on the exemplar
    panels three of the four are drawn underneath the fourth.
    """
    shipped = ('expb_pow', 'giop', 'gsm', 'expb_pow2', 'expb_pow2flat',
               'expb_powflex')
    styles = [style.algo_linestyle(a) for a in shipped]
    assert len(set(styles)) == len(shipped), 'every shipped model draws distinctly'
    assert style.algo_linestyle('giop') == style.algo_linestyle('giop')


# --------------------------------------------------------------------
# rcParams plumbing
# --------------------------------------------------------------------
def test_context_does_not_leak_and_use_style_is_idempotent():
    original = mpl.rcParams['font.size']
    with style.context():
        assert mpl.rcParams['axes.grid'] is True
    assert mpl.rcParams['font.size'] == original      # restored

    try:
        style.use_ioptics_style()
        first = dict(mpl.rcParams)
        style.use_ioptics_style()
        assert mpl.rcParams['axes.grid'] == first['axes.grid']
        assert mpl.rcParams['figure.constrained_layout.use'] is True
    finally:
        mpl.rcParams.update(mpl.rcParamsDefault)


def test_importing_ioptics_does_not_mutate_rcparams():
    """Import must be side-effect free — a library does not restyle its caller."""
    code = ('import matplotlib as mpl; before = mpl.rcParams["axes.grid"]; '
            'import ioptics.plotting, ioptics.style; '
            'print(before == mpl.rcParams["axes.grid"])')
    out = subprocess.run([sys.executable, '-c', code], capture_output=True,
                         text=True, check=True).stdout.strip()
    assert out == 'True'


# --------------------------------------------------------------------
# labels and statistics
# --------------------------------------------------------------------
def test_component_label_carries_quantity_and_unit():
    lbl = style.component_label('a', 440, prefix='retrieved')
    assert 'retrieved' in lbl and '(440)' in lbl and 'm$^{-1}$' in lbl
    assert 'sr$^{-1}$' in style.component_label('Rrs')
    # an unknown component degrades gracefully rather than inventing a unit
    assert style.component_label('mystery') == 'mystery'


def test_ratio_and_mpd_match_the_giop_definitions():
    truth = np.array([1.0, 2.0, 4.0])
    ratio, mpd = style.ratio_mpd(truth, truth * 1.1)
    assert ratio == pytest.approx(1.1)
    assert mpd == pytest.approx(10.0)
    # non-finite / non-positive pairs are dropped, not propagated
    ratio, _ = style.ratio_mpd([1.0, np.nan, 0.0], [2.0, 5.0, 5.0])
    assert ratio == pytest.approx(2.0)
    assert np.isnan(style.ratio_mpd([np.nan], [np.nan])[0])


def test_series_label_reports_n_ratio_and_mpd():
    lbl = style.series_label('giop', np.array([1.0, 2.0]), np.array([1.0, 2.0]))
    assert 'giop' in lbl and 'n=2' in lbl and 'ratio 1.00' in lbl and 'MPD' in lbl
    assert style.series_label('giop') == 'giop'       # no data → bare name


# --------------------------------------------------------------------
# tick taming (the published scatters' overprinted labels)
# --------------------------------------------------------------------
@pytest.mark.parametrize('hi,expect_minor_labels', [(1000.0, False), (0.02, True)])
def test_log_ticks_label_minors_only_when_there_is_nothing_else(hi,
                                                                expect_minor_labels):
    fig, ax = plt.subplots()
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(0.01, hi)
    ax.set_ylim(0.01, hi)
    style.log_ticks(ax)
    labelled = [t for t in ax.xaxis.get_minorticklabels() if t.get_text()]
    assert bool(labelled) is expect_minor_labels
    plt.close(fig)


# --------------------------------------------------------------------
# integration with the figure builders
# --------------------------------------------------------------------
def _points(algos):
    rows = []
    for algo in algos:
        for x in (0.1, 0.2, 0.4):
            rows.append({'algorithm': algo, 'x': x, 'y': x * 1.1})
    return {'points': pd.DataFrame(rows), 'lims': (0.1, 0.44)}


def _series_colors(fig):
    """{legend label → RGBA} for the scatter series on a figure."""
    ax = fig.axes[0]
    out = {}
    for coll in ax.collections:
        lbl = coll.get_label()
        if lbl and not lbl.startswith('_'):
            out[lbl.split()[0]] = tuple(np.ravel(coll.get_facecolor())[:3])
    return out


def test_scatter_colour_survives_a_change_of_cast():
    """The regression test for the defect: two figures, different algorithm sets.

    ``expb_pow`` must be the same colour in both, and must not move because
    ``gsm`` and a stranger joined the second figure.
    """
    fig_a = plotting.scatter_log(_points(['expb_pow', 'giop']))
    fig_b = plotting.scatter_log(_points(['brand_new', 'gsm', 'expb_pow']))
    a, b = _series_colors(fig_a), _series_colors(fig_b)
    assert a['expb_pow'] == b['expb_pow']
    assert a['expb_pow'] != a['giop']
    plt.close(fig_a)
    plt.close(fig_b)


def test_scatter_legend_carries_the_in_panel_statistics():
    fig = plotting.scatter_log(_points(['giop']), component='a', ref=440)
    ax = fig.axes[0]
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert any('n=3' in t and 'ratio' in t and 'MPD' in t for t in labels)
    assert 'm$^{-1}$' in ax.get_xlabel() and '(440)' in ax.get_ylabel()
    plt.close(fig)


def test_taylor_azimuth_is_labelled_in_correlation_with_rmsd_arcs():
    stats = pd.DataFrame({'algorithm': ['expb_pow', 'giop'],
                          'corr': [0.98, 0.90], 'norm_std': [1.05, 0.85]})
    fig = plotting.taylor(stats)
    ax = fig.axes[0]
    labels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
    # correlation values, not degrees
    assert '0.9' in labels
    assert not any('°' in t for t in labels)
    # the centred-RMSD arcs are what make it a Taylor diagram rather than a
    # polar scatter: dotted arcs about the reference point
    dotted = [ln for ln in ax.lines if ln.get_linestyle() in (':', (0, (1, 1.65)))]
    assert len(dotted) >= 3
    plt.close(fig)


def test_target_has_constant_rmsd_rings():
    stats = pd.DataFrame({'algorithm': ['expb_pow'], 'bias': [0.1],
                          'signed_unbiased_rmsd': [-0.2]})
    fig = plotting.target(stats)
    ax = fig.axes[0]
    assert len([p for p in ax.patches if isinstance(p, plt.Circle)]) >= 3
    plt.close(fig)

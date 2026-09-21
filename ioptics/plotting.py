"""Low-level static figure primitives (matplotlib), publication-styled.

Each builder takes the **arrays** produced by :mod:`ioptics.diagnostics` /
:mod:`ioptics.metrics` and returns a :class:`matplotlib.figure.Figure` — **no
file I/O and no table reads**. The :mod:`ioptics.report` layer is responsible
for sourcing the data, saving PNG/PDF, and assembling pages.

Unlike :mod:`ioptics.metrics`/:mod:`ioptics.diagnostics` (which are BING/ocpy
free), this module may reuse ``bing.plotting`` and the ``corner`` package where
they fit. Builders accept an optional ``ax`` so the ``report`` layer can compose
panels; when ``ax`` is ``None`` a new single-axes figure is created.

The module does not force a matplotlib backend; in a headless context select a
non-interactive one (e.g. ``matplotlib.use('Agg')``) before importing. No
builder calls ``plt.show``.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import matplotlib.pyplot as plt

from ioptics import metrics, style

# Default retrieved-vs-true guide factors: 1:1, 3:1, 1:3 (the design's "0.3:1").
SCATTER_GUIDES = (1.0, 3.0, 1.0 / 3.0)


def _axes(ax=None, *, figsize=(5, 5), projection=None):
    """Return ``(fig, ax)`` — a fresh single-axes figure if ``ax`` is ``None``."""
    if ax is not None:
        return ax.figure, ax
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection=projection)
    return fig, ax


#: Attribute stamped on a figure whose input was degenerate. The ``report`` layer
#: reads it (:func:`is_empty`) and declines to save or publish the figure, so a
#: blank panel can never reach a page — the first published GLORIA report was five
#: blank panels under captions explaining how to read them.
EMPTY_FLAG = '_ioptics_no_data'


def _annotate_empty(ax, msg='no data'):
    """Place a centered 'no data' note on otherwise-empty axes (degenerate input).

    Also stamps :data:`EMPTY_FLAG` on the figure so callers can tell a degenerate
    figure from a real one without inspecting pixels.
    """
    ax.text(0.5, 0.5, msg, ha='center', va='center', transform=ax.transAxes,
            fontsize=11, color='0.5')
    setattr(ax.figure, EMPTY_FLAG, True)


def is_empty(fig):
    """Whether ``fig`` was built from degenerate input (see :data:`EMPTY_FLAG`)."""
    return bool(getattr(fig, EMPTY_FLAG, False))


@style.styled
def scatter_log(data, *, guides=SCATTER_GUIDES, ax=None, component=None,
                ref=None):
    """Retrieved-vs-true log-log scatter with 1:1 / 3:1 / 1:3 guide lines.

    ``data`` is the dict from :func:`ioptics.diagnostics.scatter_data`
    (``points`` DataFrame ``algorithm/x/y``, ``lims``). One marker series per
    algorithm; ``guides`` are the ``y = g·x`` factors drawn across ``lims``
    (the first, ``1``, is the solid 1:1 line).

    Each algorithm draws in its **fixed** colour and marker
    (:func:`ioptics.style.algo_style`), so it looks the same here as on every
    other page. The legend carries each series' in-panel statistics — ``n``,
    median ratio and MPD — because an IOP inter-comparison scatter is expected to
    show its numbers (IOCCG Report 5, GIOP Table 4). ``component``/``ref`` label
    the axes with the quantity and its unit.
    """
    fig, ax = _axes(ax)
    points = data.get('points')
    lo, hi = data.get('lims', (np.nan, np.nan))
    if points is None or len(points) == 0 or not np.isfinite([lo, hi]).all():
        _annotate_empty(ax)
        return fig
    for algo, g in points.groupby('algorithm', sort=False):
        st = style.algo_style(algo)
        ax.scatter(g['x'], g['y'], s=20, alpha=0.75, linewidths=0,
                   color=st['color'], marker=st['marker'],
                   label=style.series_label(algo, g['x'], g['y']))
    line = np.array([lo, hi])
    for i, factor in enumerate(guides):
        ax.plot(line, factor * line, color=style.GUIDE_COLOR,
                ls='-' if i == 0 else '--', lw=1.0, zorder=0)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(style.component_label(component or 'value', ref,
                                        prefix='truth'))
    ax.set_ylabel(style.component_label(component or 'value', ref,
                                        prefix='retrieved'))
    ax.set_aspect('equal', 'box')
    style.log_ticks(ax)
    ax.legend(loc='upper left')
    return fig


def _ratio_edge_label(edge):
    """Label a ratio-bucket edge as an exact fraction where it is one.

    :data:`metrics.RATIO_EDGES` are thirds and quarters, so ``'%g'`` rendered them
    as ``0.333333`` — a bucket boundary the reader has to decode. ``1/3`` is what
    was meant.
    """
    if not np.isfinite(edge):
        return '∞'
    frac = Fraction(float(edge)).limit_denominator(12)
    if frac.denominator == 1:
        return f'{frac.numerator:d}'
    return f'{frac.numerator:d}/{frac.denominator:d}'


@style.styled
def ratio_hist(data, *, ax=None):
    """Grouped bar chart of M/O ratio counts per :data:`metrics.RATIO_EDGES` bucket.

    ``data`` is the dict from :func:`ioptics.diagnostics.ratio_hist_data`
    (``edges``, ``centers``, ``counts`` DataFrame indexed by algorithm). Bars are
    grouped by bucket with one bar per algorithm; the x tick labels are the
    bucket edges.
    """
    fig, ax = _axes(ax, figsize=(6, 4))
    counts = data.get('counts')
    edges = np.asarray(data.get('edges', metrics.RATIO_EDGES), dtype=float)
    if counts is None or len(counts) == 0:
        _annotate_empty(ax)
        return fig
    nbins = counts.shape[1]
    algos = list(counts.index)
    x = np.arange(nbins)
    width = 0.8 / max(len(algos), 1)
    for i, algo in enumerate(algos):
        ax.bar(x + i * width, counts.loc[algo].to_numpy(), width=width,
               label=str(algo), align='edge', color=style.algo_color(algo))
    labels = [_ratio_edge_label(e) for e in edges]
    ax.set_xticks(x)
    ax.set_xticklabels([f'{labels[i]}–{labels[i + 1]}' for i in range(nbins)],
                       rotation=45, ha='right', fontsize=7)
    ax.axvline(np.searchsorted(edges, 1.0) - 1 + 0.4,
               color=style.GUIDE_COLOR, lw=0.8)
    ax.set_xlabel('M / O')
    ax.set_ylabel('count')
    ax.legend()
    return fig


def _col(comp_fit, name):
    """Pull a column/key as a float array from a DataFrame or mapping (or None)."""
    if comp_fit is None or name not in comp_fit:
        return None
    return np.asarray(comp_fit[name], dtype=float)


@style.styled
def spectra_band(comp_fit, truth=None, *, label='', ax=None, component=None):
    """One component's spectrum with 68%/95% credible bands (and optional truth).

    ``comp_fit`` is a results-table slice for a single component (a DataFrame or
    mapping with ``wavelength``, ``value`` and, where present, ``lo68/hi68/
    lo95/hi95``). ``truth`` overrides ``comp_fit['truth']`` if given. Plotted on a
    log y-axis.

    When ``label`` is an algorithm name the series takes that algorithm's fixed
    colour; ``component`` labels the y-axis with the quantity and its unit.
    """
    fig, ax = _axes(ax, figsize=(6, 4))
    color = style.algo_color(label) if label else style.PALETTE['blue']
    wave = _col(comp_fit, 'wavelength')
    value = _col(comp_fit, 'value')
    if wave is None or value is None or wave.size == 0:
        _annotate_empty(ax)
        return fig
    order = np.argsort(wave)
    wave, value = wave[order], value[order]

    def _band(lo, hi, alpha):
        lo, hi = _col(comp_fit, lo), _col(comp_fit, hi)
        if lo is not None and hi is not None and np.isfinite(lo).any():
            ax.fill_between(wave, lo[order], hi[order], alpha=alpha,
                            color=color, lw=0)

    _band('lo95', 'hi95', 0.18)
    _band('lo68', 'hi68', 0.30)
    ax.plot(wave, value, color=color, lw=1.5, label=label or 'retrieved')
    tr = np.asarray(truth, dtype=float)[order] if truth is not None \
        else _col(comp_fit, 'truth')
    if tr is not None and np.isfinite(tr).any():
        ax.plot(wave, tr, color='k', ls='--', lw=1.2, label='truth')
    ax.set_yscale('log')
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel(style.component_label(component, prefix='') if component
                  else 'value')
    style.log_ticks(ax, which='y')
    ax.legend()
    return fig


@style.styled
def residual_rrs(residuals, *, ax=None):
    """Rrs closure residuals (``Rrs_obs − Rrs_model``) per algorithm.

    ``residuals`` is the dict from :func:`ioptics.diagnostics.residual_spectra`
    (``{algorithm: {wave, residual, chi2_nu}}``). A zero line marks perfect
    closure; each algorithm's χ²ᵥ is shown in the legend.
    """
    fig, ax = _axes(ax, figsize=(6, 4))
    if not residuals:
        _annotate_empty(ax)
        return fig
    for algo, d in residuals.items():
        wave = np.asarray(d['wave'], dtype=float)
        resid = np.asarray(d['residual'], dtype=float)
        cn = d.get('chi2_nu', np.nan)
        lbl = f'{algo}' + (f' (χ²ᵥ={cn:.2f})' if np.isfinite(cn) else '')
        st = style.algo_style(algo)
        ax.plot(wave, resid, marker=st['marker'], ms=3.5, lw=1.0,
                ls=st['linestyle'], color=st['color'], label=lbl)
    ax.axhline(0.0, color=style.GUIDE_COLOR, lw=0.8)
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel(r'$R_{rs}^{obs} - R_{rs}^{model}$ [1/sr]')
    ax.legend()
    return fig


def _has_rrs(data):
    """Whether an exemplar panel's data can actually be drawn."""
    if not data:
        return False
    return bool(np.isfinite(np.asarray(data.get('rrs', []), dtype=float)).any()
                or data.get('models'))


@style.styled
def rrs_fit(data, *, ax=None, role='', legend=True):
    """One exemplar fit: observed Rrs with every algorithm's model laid over it.

    ``data`` is the dict from :func:`ioptics.diagnostics.rrs_fit_data`. The
    observation is black dots (it is the measurement, not a model, so it does not
    take a series colour) and each algorithm its fixed colour. The panel title
    carries the ``obs_id`` and the observed Rrs peak — the clear→turbid ordering
    key — and each legend entry that algorithm's own **χ²ᵥ and relative misfit**,
    so a panel can be judged without reference to a table.

    Rrs is drawn on a **linear** y-axis, unlike the IOP spectra: hyperspectral red
    tails routinely cross zero, which a log axis silently drops.
    """
    fig, ax = _axes(ax, figsize=(5.5, 3.4))
    if not _has_rrs(data):
        _annotate_empty(ax)
        return fig
    wave = np.asarray(data.get('wave', []), dtype=float)
    rrs = np.asarray(data.get('rrs', []), dtype=float)
    if wave.size:
        ax.plot(wave, rrs, 'k.', ms=3.5, label='observed', zorder=3)
    for algo, m in (data.get('models') or {}).items():
        st = style.algo_style(algo)
        bits = []
        cn, rm = m.get('chi2_nu', np.nan), m.get('rel_misfit', np.nan)
        if np.isfinite(cn):
            bits.append(f'χ²ᵥ={cn:.3g}')
        if np.isfinite(rm):
            bits.append(f'Δ={rm:.0%}')
        lbl = algo + (f' ({", ".join(bits)})' if bits else '')
        # linestyle as well as colour: on GLORIA all four turbid variants model
        # nearly the same Rrs, and with one linestyle three of them vanish under
        # the fourth — leaving a reader unable to tell "identical" from "missing".
        ax.plot(np.asarray(m['wave'], dtype=float),
                np.asarray(m['rrs'], dtype=float),
                color=st['color'], lw=1.4, ls=st['linestyle'], label=lbl)
    ax.axhline(0.0, color=style.GUIDE_COLOR, lw=0.6, zorder=0)
    peak = data.get('peak_nm', np.nan)
    head = f"obs {data.get('obs_id', '?')}"
    if role:
        head += f' — {role}'
    if np.isfinite(peak):
        head += f' (peak {peak:.0f} nm)'
    ax.set_title(head, fontsize=9)
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel(r'$R_{rs}$ [1/sr]')
    if legend:
        ax.legend(fontsize=6.5, loc='best', framealpha=0.85)
    return fig


@style.styled
def exemplar_grid(panels, *, ncols=2, roles=(), suptitle=''):
    """A grid of :func:`rrs_fit` panels, in the order given.

    ``panels`` is a list of :func:`ioptics.diagnostics.rrs_fit_data` dicts, already
    ordered by the caller (clear→turbid). Empty panels are annotated individually,
    but the **figure** is only flagged degenerate when *every* panel is empty —
    :func:`_annotate_empty` stamps the flag on the shared figure, so without this a
    single missing observation would suppress the whole grid.
    """
    panels = list(panels or [])
    if not panels:
        fig, ax = _axes(figsize=(6, 4))
        _annotate_empty(ax)
        return fig
    ncols = max(1, int(ncols))
    nrows = -(-len(panels) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.6 * ncols, 3.3 * nrows),
                             squeeze=False)
    flat = axes.ravel()
    drawn = 0
    for i, ax in enumerate(flat):
        if i >= len(panels):
            ax.axis('off')
            continue
        role = roles[i] if i < len(roles) else ''
        rrs_fit(panels[i], ax=ax, role=role)
        drawn += bool(_has_rrs(panels[i]))
    if suptitle:
        fig.suptitle(suptitle, fontsize=11)
    setattr(fig, EMPTY_FLAG, drawn == 0)
    return fig


#: Axis labels for the metrics the accuracy-vs-wavelength figure can draw, with the
#: perfect value named — the same discipline the tables follow, since ``mae`` is
#: perfect at 0 while ``median_ratio`` is perfect at 1.
METRIC_LABELS = {
    'mae': 'MAE (fractional multiplicative, 0 = perfect)',
    'bias': 'bias (fractional multiplicative, 0 = perfect)',
    'abs_bias': '|bias| (fractional multiplicative, 0 = perfect)',
    'median_ratio': 'median retrieved / true (1 = perfect)',
    'rms_log': r'RMS $\log_{10}$ error (0 = perfect)',
    'coverage68': 'coverage of the 68% band (0.68 = nominal)',
    'coverage95': 'coverage of the 95% band (0.95 = nominal)',
}


@style.styled
def accuracy_spectrum(data, *, ax=None, legend=True, title=None):
    """One component's accuracy against wavelength, one line per algorithm.

    ``data`` is the dict from
    :func:`ioptics.diagnostics.accuracy_spectrum_data`. A dashed rule marks the
    metric's perfect value, so a reader can see at a glance which bands a model is
    usable in — the conventional first figure of an IOP-algorithm comparison, and one
    this package had the persisted numbers for but never drew.
    """
    fig, ax = _axes(ax, figsize=(6, 4))
    series = (data or {}).get('series') or {}
    if not series:
        _annotate_empty(ax)
        return fig
    metric = data.get('metric', 'mae')
    for algo, s in series.items():
        st = style.algo_style(algo)
        wave = np.asarray(s['wave'], dtype=float)
        val = np.asarray(s['value'], dtype=float)
        # A single scored band cannot draw a line; show it as a lone marker rather
        # than as an invisible zero-length segment.
        ax.plot(wave, val, color=st['color'], marker=st['marker'],
                ls=st['linestyle'] if wave.size > 1 else 'none',
                ms=4.0, lw=1.4, label=str(algo))
    perfect = data.get('perfect')
    if perfect is not None and np.isfinite(perfect):
        ax.axhline(float(perfect), color=style.GUIDE_COLOR, ls='--', lw=0.9,
                   zorder=0)
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel(METRIC_LABELS.get(metric, metric))
    comp = data.get('component')
    ax.set_title(title if title is not None else
                 (style.component_label(comp, unit=False) if comp else ''),
                 fontsize=10)
    if legend:
        ax.legend(fontsize=7)
    return fig


@style.styled
def accuracy_spectrum_grid(panels, *, ncols=2, titles=()):
    """Small multiples of :func:`accuracy_spectrum`, one panel per component.

    The community reports total ``a``/``bb`` beside the decomposed ``a_ph``/``a_dg``
    precisely so the decomposition's weakness is visible; a shared grid makes that
    comparison in one glance. As in :func:`exemplar_grid`, the figure is only flagged
    degenerate when *every* panel is empty.
    """
    panels = list(panels or [])
    if not panels:
        fig, ax = _axes(figsize=(6, 4))
        _annotate_empty(ax)
        return fig
    ncols = max(1, int(ncols))
    nrows = -(-len(panels) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.6 * ncols, 3.4 * nrows),
                             squeeze=False)
    flat = axes.ravel()
    drawn = 0
    for i, ax in enumerate(flat):
        if i >= len(panels):
            ax.axis('off')
            continue
        t = titles[i] if i < len(titles) else None
        accuracy_spectrum(panels[i], ax=ax, legend=(i == 0), title=t)
        drawn += bool((panels[i] or {}).get('series'))
    setattr(fig, EMPTY_FLAG, drawn == 0)
    return fig


#: Correlation values labelled along a Taylor diagram's azimuth (the convention:
#: the arc is labelled in correlation, never in degrees).
TAYLOR_CORR_TICKS = (0.0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99)

#: Centred-RMSD contours (in units of the reference standard deviation) drawn as
#: arcs about the reference point — what makes a Taylor diagram a Taylor diagram.
TAYLOR_CRMSD_ARCS = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5)


@style.styled
def taylor(stats, *, ax=None, crmsd_arcs=TAYLOR_CRMSD_ARCS):
    """Taylor diagram (Taylor 2001) from :func:`ioptics.diagnostics.taylor_stats`.

    Polar layout: azimuth = ``arccos(corr)``, radius = ``norm_std``; the
    reference field sits at ``(corr=1, norm_std=1)``. One point per algorithm, in
    its fixed colour and marker.

    Two corrections over the first published version, which was a polar scatter
    rather than a Taylor diagram: the azimuth is labelled in **correlation**
    (:data:`TAYLOR_CORR_TICKS`) instead of degrees, and **centred-RMSD arcs** are
    drawn about the reference point (:data:`TAYLOR_CRMSD_ARCS`) so the third leg of
    the Taylor identity — ``crmsd² = σ² + σ_ref² − 2·σ·σ_ref·corr`` — is readable
    off the figure. The radial axis label is placed inside the wedge, where it no
    longer overprints the tick labels.
    """
    rows = stats.dropna(subset=['corr', 'norm_std']) if stats is not None \
        else None
    if rows is None or len(rows) == 0:
        fig, ax = _axes(ax)
        _annotate_empty(ax)
        return fig
    corr = rows['corr'].to_numpy(dtype=float)
    thetamax = np.pi if (corr < 0).any() else np.pi / 2
    fig, ax = _axes(ax, projection='polar')
    ax.set_thetamin(0)
    ax.set_thetamax(np.degrees(thetamax))
    ax.set_theta_zero_location('E')

    # Azimuth labelled in correlation, not degrees.
    ticks = [c for c in TAYLOR_CORR_TICKS if np.arccos(c) <= thetamax + 1e-9]
    ax.set_xticks([np.arccos(c) for c in ticks])
    ax.set_xticklabels([f'{c:g}' for c in ticks])

    rmax = max(1.0, float(np.nanmax(rows['norm_std'].to_numpy(dtype=float)))) * 1.15
    ax.set_rlim(0, rmax)

    # Centred-RMSD arcs about the reference point at (theta=0, r=1).
    phi = np.linspace(0, np.pi, 181)
    for c in crmsd_arcs:
        # Law of cosines: distance c from the reference, as (theta, r) pairs.
        r = np.sqrt(1.0 + c ** 2 - 2.0 * c * np.cos(np.pi - phi))
        with np.errstate(invalid='ignore', divide='ignore'):
            th = np.arccos(np.clip((1.0 + r ** 2 - c ** 2) / (2.0 * r), -1, 1))
        keep = np.isfinite(th) & (r <= rmax) & (th <= thetamax)
        if keep.sum() < 2:
            continue
        ax.plot(th[keep], r[keep], color=style.PALETTE['teal'], lw=0.7,
                ls=':', alpha=0.7, zorder=0)
        # Label at the middle of the *visible* arc, so the label sits on its own
        # curve rather than wherever clipping happened to end.
        mid = np.flatnonzero(keep)[keep.sum() // 2]
        ax.text(th[mid], r[mid], f'{c:g}', fontsize=7, ha='center', va='center',
                color=style.PALETTE['teal'],
                bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='none',
                          alpha=0.75))

    ax.scatter(0.0, 1.0, marker='*', s=140, color='k', label='reference',
               zorder=5)
    for _, r in rows.iterrows():
        st = style.algo_style(r['algorithm'])
        ax.scatter(np.arccos(np.clip(r['corr'], -1, 1)), r['norm_std'], s=45,
                   color=st['color'], marker=st['marker'],
                   label=str(r['algorithm']), zorder=4)
    # Radial labels inside the wedge; both axis roles live in the title, so
    # nothing overprints the tick labels (the original collided).
    ax.set_rlabel_position(np.degrees(thetamax) * 0.5)
    ax.set_xlabel('')
    ax.set_title('correlation (azimuth) · normalized $\\sigma$ (radius)\n'
                 'dotted arcs: centred RMSD from the reference',
                 fontsize=9, pad=12)
    ax.legend(loc='upper right', bbox_to_anchor=(1.32, 1.08))
    return fig


@style.styled
def target(stats, *, ax=None, rings=(0.25, 0.5, 1.0)):
    """Target diagram (Jolliff 2009) from :func:`ioptics.diagnostics.target_stats`.

    Scatters ``(signed_unbiased_rmsd, bias)`` per algorithm with crosshairs at
    the origin; a perfect model sits at the center. Equal aspect so radial
    distance reads as total RMSD, with ``rings`` drawn as constant-RMSD circles so
    that distance is quantifiable rather than merely visible.
    """
    fig, ax = _axes(ax)
    rows = stats.dropna(subset=['bias', 'signed_unbiased_rmsd']) \
        if stats is not None else None
    if rows is None or len(rows) == 0:
        _annotate_empty(ax)
        return fig
    for _, r in rows.iterrows():
        st = style.algo_style(r['algorithm'])
        ax.scatter(r['signed_unbiased_rmsd'], r['bias'], s=45,
                   color=st['color'], marker=st['marker'],
                   label=str(r['algorithm']), zorder=4)
    reach = float(np.nanmax(np.abs(np.concatenate([
        rows['bias'].to_numpy(dtype=float),
        rows['signed_unbiased_rmsd'].to_numpy(dtype=float)]))))
    for rad in rings:
        ax.add_patch(plt.Circle((0, 0), rad, fill=False, ls=':', lw=0.7,
                                color=style.PALETTE['teal'], alpha=0.7,
                                zorder=0))
    lim = max(reach * 1.25, max(rings) * 1.05)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.axhline(0.0, color=style.GUIDE_COLOR, lw=0.8)
    ax.axvline(0.0, color=style.GUIDE_COLOR, lw=0.8)
    ax.set_aspect('equal', 'box')
    ax.set_xlabel('signed unbiased RMSD (log$_{10}$)')
    ax.set_ylabel('bias (log$_{10}$)')
    ax.legend(loc='best')
    return fig


@style.styled
def corner(chain_data, **kwargs):
    """Corner plot of flattened posterior samples (``corner`` package).

    ``chain_data`` is the dict from :func:`ioptics.diagnostics.corner_data`
    (``samples`` ``(N, nparam)``, ``labels``). Uses the persisted ``pnames`` for
    axis labels. (``bing.plotting.corner_plot`` is not reused here: it expects the
    raw 3-D chains and applies a fixed 7000-step burn, whereas ``corner_data``
    already returns flattened samples with our labels — see Q&A.)
    """
    import corner as corner_pkg

    samples = np.asarray(chain_data['samples'], dtype=float)
    labels = list(chain_data.get('labels') or [])
    if samples.ndim != 2 or samples.shape[0] == 0:
        fig, ax = _axes()
        _annotate_empty(ax, 'no samples')
        return fig
    # ``corner`` lays its own grid out with subplots_adjust, which matplotlib
    # refuses to honour under a layout engine — so this one builder opts out of
    # constrained layout rather than emitting a warning per corner plot.
    with style.context(**{'figure.constrained_layout.use': False}):
        return corner_pkg.corner(samples,
                                 labels=labels if len(labels) == samples.shape[1]
                                 else None, **kwargs)


@style.styled
def dbic_cdf(curves, *, ax=None):
    """ΔBIC CDF curve(s) from :func:`ioptics.diagnostics.dbic_cdf_data`.

    ``curves`` is either a single CDF dict (``dbic``/``cdf``/``frac_favor_a``) or
    a ``{stratum: dict}`` mapping (the ``by=`` form) drawn as one step curve each.
    A vertical line at ΔBIC = 0 separates the two models; ``frac_favor_a`` is
    annotated. ΔBIC < 0 favors model A (the more complex model).
    """
    fig, ax = _axes(ax, figsize=(6, 4))
    series = curves if 'dbic' not in curves else {'': curves}
    drew = False
    for label, c in series.items():
        dbic = np.asarray(c.get('dbic', []), dtype=float)
        cdf = np.asarray(c.get('cdf', []), dtype=float)
        if dbic.size == 0:
            continue
        frac = c.get('frac_favor_a', np.nan)
        suffix = f' (favor A={frac:.2f})' if np.isfinite(frac) else ''
        ax.step(dbic, cdf, where='post', label=f'{label}{suffix}'.strip())
        drew = True
    if not drew:
        _annotate_empty(ax)
        return fig
    ax.axvline(0.0, color=style.GUIDE_COLOR, lw=0.8)
    ax.set_xlabel(r'$\Delta$BIC  (<0 favors model A)')
    ax.set_ylabel('cumulative fraction')
    ax.set_ylim(0, 1)
    ax.legend()
    return fig

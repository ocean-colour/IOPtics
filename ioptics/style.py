"""Project-wide figure style: palette, per-algorithm identity, axis labels.

One place decides how an IOPtics figure looks, so the report figures, the
documentation figures under ``docs/figures/`` and the standalone analysis scripts
under ``reports/scripts/`` cannot drift apart (they had: report figures used
matplotlib defaults while the docs figures used the ocean palette).

Two jobs:

**A shared look.** :data:`RC` holds the rcParams (fonts, constrained layout, grid,
spines); :func:`context` applies them around a single figure build (used by
:mod:`ioptics.plotting`, so no import of this module mutates global state), and
:func:`use_ioptics_style` applies them globally for a script that wants them for
everything it draws.

**A stable visual identity per algorithm.** :func:`algo_style` maps an algorithm
*name* to a fixed ``(color, marker)`` pair. This is deliberately **not** a
figure-local colour cycle: previously an algorithm's colour came from its row order
within one figure, so the same model was a different colour on different pages and
adding an algorithm reshuffled every other one. The mapping here is content-derived
(a curated slot for the known algorithms, an MD5-derived slot for anything else — not
:func:`hash`, whose salt changes per process), so it is stable across figures,
sessions and machines, and adding an algorithm never moves an existing one. Marker
shape carries the same information as colour, so the figures survive greyscale
printing and colour-vision deficiency.

The palette is the ocean-colour theme of ``docs/source/_static/custom.css``, ordered
so the first two series (the usual in-tandem pair) are the blue/amber contrast that
is safest for colour-vision deficiency.
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from functools import wraps

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

#: The ocean-colour palette, mirroring the ``--iop-*`` custom properties in
#: ``docs/source/_static/custom.css`` so figures and site chrome agree.
PALETTE = {
    'deep':   '#023e5c',   # deep ocean
    'blue':   '#0b6fa4',   # mid ocean
    'teal':   '#159b8a',   # shelf teal
    'green':  '#1f9e5a',   # productive green
    'sky':    '#6fc3e8',   # dark-mode brand
    'amber':  '#e0a020',   # sun glint
    'coral':  '#d1495b',   # warm contrast
    'violet': '#7b4fb0',   # (matches the docs/figures generators)
    'foam':   '#e8f5f2',   # seafoam fill
}

#: Categorical series colours, in assignment order. Blue/amber lead because that
#: pair stays distinguishable under deuteranopia and in greyscale.
SERIES_COLORS = (PALETTE['blue'], PALETTE['amber'], PALETTE['teal'],
                 PALETTE['coral'], PALETTE['violet'], PALETTE['green'],
                 PALETTE['deep'], PALETTE['sky'])

#: Series markers, cycled independently of :data:`SERIES_COLORS` (7 vs 8, so a
#: (colour, marker) pair does not repeat until 56 series).
SERIES_MARKERS = ('o', 's', '^', 'D', 'v', 'P', 'X')

#: Neutral ink for guides, zero lines and reference marks.
GUIDE_COLOR = '0.45'

#: Curated slots for the algorithms IOPtics ships, so the common comparisons get
#: the leading (most distinguishable) colours. Anything else hashes to a slot.
_CURATED_SLOTS = {
    'expb_pow': 0,
    'giop': 1,
    'gsm': 2,
    'expb_pow2': 3,
    'expb_pow2flat': 4,
    'expb_powflex': 5,
}

#: rcParams for every IOPtics figure. Applied via :func:`context` (per figure) or
#: :func:`use_ioptics_style` (globally, for scripts).
RC = {
    'figure.constrained_layout.use': True,
    'figure.facecolor': 'white',
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'axes.prop_cycle': mpl.cycler(color=list(SERIES_COLORS)),
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'axes.axisbelow': True,
    'grid.color': '0.88',
    'grid.linewidth': 0.6,
    'legend.fontsize': 8,
    'legend.frameon': False,
    'lines.linewidth': 1.5,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'savefig.facecolor': 'white',
}

#: Units per component, for axis labels (``a`` and friends are absorption /
#: backscattering coefficients; ``Rrs`` is a reflectance).
_UNITS = {
    'a': 'm$^{-1}$', 'bb': 'm$^{-1}$', 'a_ph': 'm$^{-1}$', 'a_dg': 'm$^{-1}$',
    'bb_p': 'm$^{-1}$', 'a_w': 'm$^{-1}$', 'bb_w': 'm$^{-1}$',
    'Rrs': 'sr$^{-1}$', 'Rrs_model': 'sr$^{-1}$', 'Rrs_obs': 'sr$^{-1}$',
    'Chl': 'mg m$^{-3}$',
}

#: Pretty maths for the component names that have one.
_PRETTY = {
    'a': '$a$', 'bb': '$b_b$', 'a_ph': '$a_{ph}$', 'a_dg': '$a_{dg}$',
    'bb_p': '$b_{bp}$', 'a_w': '$a_w$', 'bb_w': '$b_{bw}$',
    'Rrs': '$R_{rs}$', 'Rrs_model': '$R_{rs}^{model}$',
    'Rrs_obs': '$R_{rs}^{obs}$', 'Chl': 'Chl',
}


def use_ioptics_style():
    """Apply :data:`RC` globally (for scripts that draw many figures).

    Idempotent. :mod:`ioptics.plotting` does **not** call this — it wraps each
    builder in :func:`context` instead, so importing IOPtics never mutates a
    caller's rcParams.
    """
    mpl.rcParams.update(RC)


@contextmanager
def context(**overrides):
    """Context manager applying :data:`RC` to whatever is created inside it.

    ``overrides`` patch individual rcParams for one builder — e.g. the corner-plot
    builder turns ``figure.constrained_layout.use`` off, because the ``corner``
    package lays its own grid out with ``subplots_adjust`` and matplotlib refuses
    to honour that under a layout engine.
    """
    rc = dict(RC)
    rc.update(overrides)
    with plt.rc_context(rc):
        yield


def styled(func):
    """Decorator running a figure builder inside :func:`context`."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with context():
            return func(*args, **kwargs)
    return wrapper


def _slot(name):
    """Stable palette slot for ``name`` (curated, else MD5-derived).

    MD5 rather than :func:`hash` because Python salts string hashing per process,
    which would make an algorithm's colour change between runs.
    """
    key = str(name)
    if key in _CURATED_SLOTS:
        return _CURATED_SLOTS[key]
    digest = hashlib.md5(key.encode('utf-8')).digest()
    # Offset past the curated slots so a new algorithm rarely collides with the
    # shipped ones; the modulus keeps it inside the palette.
    span = len(SERIES_COLORS) * len(SERIES_MARKERS)
    return len(_CURATED_SLOTS) + (digest[0] % (span - len(_CURATED_SLOTS)))


def algo_color(name):
    """The fixed colour for an algorithm name."""
    return SERIES_COLORS[_slot(name) % len(SERIES_COLORS)]


def algo_marker(name):
    """The fixed marker for an algorithm name."""
    return SERIES_MARKERS[_slot(name) % len(SERIES_MARKERS)]


def algo_style(name):
    """``{'color': ..., 'marker': ...}`` for an algorithm name.

    Stable across figures, processes and machines, and independent of which other
    algorithms appear alongside it.
    """
    return {'color': algo_color(name), 'marker': algo_marker(name)}


def component_label(component, ref=None, *, prefix='', unit=True):
    """Axis label for a component, e.g. ``'retrieved $a$(440) [m$^{-1}$]'``.

    ``ref`` adds the reference wavelength; ``prefix`` prepends a role
    (``'truth'`` / ``'retrieved'``); ``unit`` appends the bracketed unit when one
    is known.
    """
    body = _PRETTY.get(str(component), str(component))
    if ref is not None and np.isfinite(float(ref)):
        body = f'{body}({float(ref):g})'
    label = f'{prefix} {body}'.strip()
    u = _UNITS.get(str(component))
    return f'{label} [{u}]' if (unit and u) else label


def ratio_mpd(truth, retrieved):
    """``(median ratio, MPD%)`` for one series — GIOP's Table-4 statistics.

    ``Ratio = median(M/O)`` (1 = perfect) and ``MPD = median(100·|M/O − 1|)``
    (0 = perfect), which is what the IOP literature tabulates alongside a scatter.
    Non-finite and non-positive pairs are dropped. Returns ``(nan, nan)`` if
    nothing survives.
    """
    o = np.asarray(truth, dtype=float)
    m = np.asarray(retrieved, dtype=float)
    keep = np.isfinite(o) & np.isfinite(m) & (o > 0) & (m > 0)
    if not keep.any():
        return np.nan, np.nan
    r = m[keep] / o[keep]
    return float(np.median(r)), float(np.median(100.0 * np.abs(r - 1.0)))


def series_label(name, truth=None, retrieved=None):
    """Legend label carrying the in-panel statistics for one series.

    ``'giop  n=20, ratio 1.06, MPD 6.2%'`` — the numbers a reader of an IOP
    inter-comparison expects *on* the figure (IOCCG Report 5, GIOP Table 4) rather
    than only in a table. Falls back to the bare name when no data is given.
    """
    if truth is None or retrieved is None:
        return str(name)
    o = np.asarray(truth, dtype=float)
    m = np.asarray(retrieved, dtype=float)
    # Count pairs the same way ``metrics.n_valid`` does — finite **and positive**,
    # since these are log-space statistics. Counting merely-finite pairs here would
    # print a legend ``n`` that disagrees with the table's ``n_pairs``.
    n = int((np.isfinite(o) & np.isfinite(m) & (o > 0) & (m > 0)).sum())
    ratio, mpd = ratio_mpd(truth, retrieved)
    if not np.isfinite(ratio):
        return f'{name}  n={n}'
    return f'{name}  n={n}, ratio {ratio:.2f}, MPD {mpd:.0f}%'


def log_ticks(ax, which='both'):
    """Tame log-axis tick labels so they stop overprinting.

    A narrow log axis spanning well under a decade gets minor ticks labelled at
    every 2, 3, 4, 6 … which collided into an unreadable smear on the published
    scatter plots. Decades are labelled; minors are drawn at 2 and 5 and labelled
    **only** when the axis spans less than ~1.2 decades (i.e. when there would
    otherwise be nothing to read).
    """
    axes = []
    if which in ('both', 'x'):
        axes.append((ax.xaxis, ax.get_xlim()))
    if which in ('both', 'y'):
        axes.append((ax.yaxis, ax.get_ylim()))
    for axis, (lo, hi) in axes:
        if not (np.isfinite(lo) and np.isfinite(hi)) or lo <= 0 or hi <= 0:
            continue
        decades = np.log10(hi) - np.log10(lo)
        axis.set_major_locator(mticker.LogLocator(base=10.0))
        axis.set_major_formatter(mticker.LogFormatterSciNotation())
        axis.set_minor_locator(mticker.LogLocator(base=10.0, subs=(2.0, 5.0)))
        if decades >= 1.2:
            axis.set_minor_formatter(mticker.NullFormatter())
        else:
            axis.set_minor_formatter(mticker.FuncFormatter(
                lambda v, _pos: f'{v:g}'))

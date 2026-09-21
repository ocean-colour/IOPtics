#!/usr/bin/env python
"""Talk-tuned variant of the exemplar-fits figure (16:9, four panels, large type).

The report version (``runs/<sweep>/figures/exemplar_fits.pdf``, built by
:func:`ioptics.report.standard.build_exemplars`) carries **ten** panels at page
proportions, which is right for a document and wrong for a slide: on a projector the
axis labels are unreadable and ten panels of a spectrum are more than an audience can
take in while someone is talking.

This draws the same finding with four panels on a 16:9 canvas — the clearest
spectrum, two from the middle of the fit-quality distribution, and the worst — in the
same clear→turbid order, with the per-algorithm colours/markers/linestyles every other
IOPtics figure uses. Nothing is recomputed: the selection and the spectra come from
the persisted sweep artifacts through the same API the report uses, so the slide and
the report cannot disagree.

Usage::

    python reports/scripts/talk_exemplar_fits.py [sweep_id] [--panels N] [--all]

Writes ``reports/figures/talk_exemplar_fits.{pdf,png}``. ``--all`` keeps every
exemplar instead of subsetting to ``--panels``.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- repo-root import guard -------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, '..', '..'))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)
_FIGDIR = os.path.join(_REPO, 'reports', 'figures')
os.makedirs(_FIGDIR, exist_ok=True)

from ioptics import diagnostics, records, style            # noqa: E402
from ioptics.report import figures as rfigures             # noqa: E402

#: 16:9 at a size that keeps 13-14 pt type legible when scaled to a slide.
TALK_FIGSIZE = (13.33, 7.5)

#: rcParams on top of the house style. Everything is up ~4-5 pt from the report
#: figure, and the legend gains a solid background so it stays readable over data.
TALK_RC = {
    'font.size': 15,
    'axes.titlesize': 17,
    'axes.labelsize': 15,
    'xtick.labelsize': 13,
    'ytick.labelsize': 13,
    'legend.fontsize': 12,
    'legend.framealpha': 0.92,
    'lines.linewidth': 2.4,
    'savefig.dpi': 200,
}


def pick_panels(picks, n_panels):
    """Subset the exemplar selection to ``n_panels``, keeping both extremes.

    Always retains ``best`` and ``worst`` — they are the span the figure is about —
    and spreads the remainder evenly across the middle in the existing clear→turbid
    order, so the slide still reads as a progression rather than two endpoints and
    an arbitrary neighbour.
    """
    if n_panels is None or n_panels >= len(picks):
        return picks
    if n_panels <= 2:
        keep = [0, len(picks) - 1][:max(1, n_panels)]
        return picks.iloc[sorted(set(keep))]
    roles = list(picks['role'])
    first = roles.index('best') if 'best' in roles else 0
    last = roles.index('worst') if 'worst' in roles else len(picks) - 1
    middle = [i for i in range(len(picks)) if i not in (first, last)]
    take = np.linspace(0, len(middle) - 1, n_panels - 2).round().astype(int)
    chosen = sorted({first, last} | {middle[i] for i in dict.fromkeys(take)})
    return picks.iloc[chosen]


def build(sweep_id='gloria_turbid_v3', n_panels=4, ncols=2, root=None):
    """Render the talk figure; returns the written paths."""
    sweep = rfigures.load(sweep_id, root=root)
    picks = rfigures.exemplars(sweep)
    if picks.empty:
        raise SystemExit(f'{sweep_id}: no rankable fit to draw')
    picks = pick_panels(picks, n_panels)

    panels = [diagnostics.rrs_fit_data(sweep.spectral, sweep.scalar, r.obs_id,
                                      dataset=getattr(r, 'dataset', None),
                                      fit_method='chisq')
              for r in picks.itertuples()]
    roles = list(picks['role'])
    nrows = -(-len(panels) // ncols)

    with style.context(**TALK_RC):
        fig, axes = plt.subplots(nrows, ncols, figsize=TALK_FIGSIZE,
                                 squeeze=False)
        for i, ax in enumerate(axes.ravel()):
            if i >= len(panels):
                ax.axis('off')
                continue
            _panel(ax, panels[i], roles[i])
        fig.suptitle('Open-ocean IOP models on turbid water: '
                     'clear (top-left) → turbid (bottom-right)', fontsize=19)
        # One figure-level legend along the bottom. A per-panel legend has to sit
        # somewhere, and on the clear-water panel the only free corner is over the
        # data — which is the one thing a slide cannot afford to cover.
        handles, labels = axes.ravel()[0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, loc='outside lower center',
                       ncols=len(handles), frameon=False, fontsize=14)

    out = []
    for ext in ('pdf', 'png'):
        path = os.path.join(_FIGDIR, f'talk_exemplar_fits.{ext}')
        fig.savefig(path, bbox_inches='tight')
        out.append(path)
    plt.close(fig)
    return out


def _panel(ax, data, role):
    """One exemplar: observed Rrs with every algorithm's model over it."""
    wave = np.asarray(data.get('wave', []), dtype=float)
    rrs = np.asarray(data.get('rrs', []), dtype=float)
    if wave.size:
        ax.plot(wave, rrs, 'k.', ms=4.5, label='observed', zorder=3)
    for algo, m in (data.get('models') or {}).items():
        st = style.algo_style(algo)
        ax.plot(np.asarray(m['wave'], dtype=float),
                np.asarray(m['rrs'], dtype=float),
                color=st['color'], ls=st['linestyle'], label=str(algo))
    ax.axhline(0.0, color=style.GUIDE_COLOR, lw=0.8, zorder=0)

    # The two fit numbers go in the panel as one line of text rather than into
    # four legend entries: on a slide the reader needs the magnitude, not a
    # per-algorithm breakdown they cannot read from the back of the room.
    models = list((data.get('models') or {}).values())
    chi2 = [m.get('chi2_nu', np.nan) for m in models]
    rel = [m.get('rel_misfit', np.nan) for m in models]
    bits = []
    if np.isfinite(chi2).any():
        bits.append(f'χ²ᵥ ≈ {np.nanmedian(chi2):.3g}')
    if np.isfinite(rel).any():
        bits.append(f'misfit ≈ {np.nanmedian(rel):.0%}')
    if bits:
        ax.text(0.97, 0.94, '\n'.join(bits), transform=ax.transAxes,
                ha='right', va='top', fontsize=13,
                bbox=dict(boxstyle='round,pad=0.35', fc='white', ec='0.7',
                          alpha=0.9))

    peak = data.get('peak_nm', np.nan)
    head = f'{role}'
    if np.isfinite(peak):
        head += f' — Rrs peak {peak:.0f} nm'
        if peak > records.RED_PEAK_NM:
            head += ' (out of scope)'
    ax.set_title(head)
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel(r'$R_{rs}$ [sr$^{-1}$]')


def _cli(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('sweep_id', nargs='?', default='gloria_turbid_v3')
    p.add_argument('--panels', type=int, default=4,
                   help='how many panels to keep (default 4; extremes always kept)')
    p.add_argument('--ncols', type=int, default=2)
    p.add_argument('--all', action='store_true', help='keep every exemplar')
    a = p.parse_args(argv)
    for path in build(a.sweep_id, n_panels=None if a.all else a.panels,
                      ncols=a.ncols):
        print(path)


if __name__ == '__main__':
    _cli()

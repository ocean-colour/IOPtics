"""Generate the L23 dataset-overview figure for ``docs/source/datasets.rst``.

Characterizes the Loisel et al. (2023) synthetic dataset used in the first
sweep: the spread of phytoplankton loading across its 3320 scenarios (via the
phytoplankton absorption at 440 nm, a chlorophyll proxy), and example
remote-sensing reflectance spectra spanning clear→turbid waters.

Needs the L23 data ($OS_COLOR / ocpy). The PNG is committed so Read the Docs
(which has no data) serves it directly.

Run:  python docs/figures/make_l23_overview.py
Out:  docs/source/_static/l23_overview.png
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent.parent / 'source' / '_static' / 'l23_overview.png'


def main():
    from ocpy.hydrolight import loisel23

    ds = loisel23.load_ds(1, 0)
    wave = np.asarray(ds['Lambda'], dtype=float)
    rrs = np.asarray(ds['Rrs'], dtype=float)             # (3320, 81)
    aph = np.asarray(ds['aph'], dtype=float)
    i440 = int(np.argmin(np.abs(wave - 440.0)))
    aph440 = aph[:, i440]

    fig, (axh, axr) = plt.subplots(1, 2, figsize=(10, 3.8),
                                   constrained_layout=True)

    # left: distribution of phytoplankton loading (log scale)
    axh.hist(np.log10(aph440[aph440 > 0]), bins=40, color='#178a5a',
             alpha=0.85)
    axh.set_xlabel(r'$\log_{10}\,a_{ph}(440)$  [m$^{-1}$]  (phytoplankton loading)')
    axh.set_ylabel('# of L23 scenarios')
    axh.set_title(f'L23 spans clear→turbid waters (N={rrs.shape[0]})',
                  fontsize=10)

    # right: example Rrs spectra colored low->high phytoplankton loading
    order = np.argsort(aph440)
    picks = order[np.linspace(0, len(order) - 1, 8).astype(int)]
    cmap = plt.cm.viridis
    for j, idx in enumerate(picks):
        axr.plot(wave, rrs[idx], color=cmap(j / (len(picks) - 1)), lw=1.3)
    axr.set_xlabel('wavelength  [nm]')
    axr.set_ylabel(r'$R_{rs}(\lambda)$  [sr$^{-1}$]')
    axr.set_title('Example reflectance spectra (blue→green with loading)',
                  fontsize=10)
    axr.margins(x=0)
    sm = plt.cm.ScalarMappable(cmap=cmap)
    sm.set_array([])
    cb = fig.colorbar(sm, ax=axr, ticks=[0, 1])
    cb.ax.set_yticklabels(['clear', 'turbid'])

    fig.suptitle('The L23 (Loisel+2023) synthetic dataset', fontsize=12)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=140)
    print('wrote', OUT)


if __name__ == '__main__':
    main()

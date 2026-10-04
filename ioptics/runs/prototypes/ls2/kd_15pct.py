"""The 15% question: why the MODIS Kd network disagrees with L23's <Kd>_1 (ls2 task 10).

Planning measured the network ocpy shipped (the authors' MODIS **v1.1**)
against L23's ``<Kd>_1`` and found it **15-18% high at 440 and 490 nm**, but
within 2-4% at 555 and 670 nm, uniformly across Kd bins.  Until that is
explained, we do not know whether L23's ``<Kd>_1`` is the truth to train a
network against (task 11) or the thing that is wrong.  This script tests every
candidate the prompt names, plus two that turned up along the way:

1. **The ``<Kd>_1`` definition** -- the three of ls2 Q10 (``ioptics.kd``).
2. **Pure-water absorption** -- an a_w difference between L23 and the network's
   training RT.  It enters ``Kd`` additively (``dKd ~ da_w / mu_d``), so its
   signature is a gap that shrinks, *relative to Kd*, as Kd grows.  Tested two
   ways: the ratio across Kd quintiles, with a fit ``Kd_NN = alpha*Kd_L23 + beta``;
   and the size of the largest table difference on hand (ocpy's GSFC
   Pope & Fry table vs IOCCG 2018, which is L23's).
3. **Band interpolation** of L23 onto the network's bands: linear (as the LS2
   driver does), cubic, nearest-band, and a 10 nm Gaussian band.
4. **A real network error** -- checked against two further implementations
   by the same authors on the same inputs: MODIS **v1.3** (their current
   retrain) and **PACE v2.3** (12 bands that sit exactly on L23's grid, so no
   interpolation at all).
5. *(new)* **The training domain**: the LUTs store the mean and standard
   deviation of each training input and of the output ``log10 Kd``, so where
   L23 sits in each network's training distribution can be read directly.
6. *(new)* **The inelastic realization and the sun**: X = 1, 2 and 4, and
   theta_s = 0, 30 and 60 degrees, since the network's training RT includes
   whatever inelastic light it includes.

All Rrs are L23's own, noise-free.  Every number on the report page is
computed here; the page, its CSVs and its figures are written into
``docs/source/reports/ls2_kd_15pct/``.

Usage, from the repository root::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \\
        ioptics/runs/prototypes/ls2/kd_15pct.py [--docs-root DIR]

Needs L23 and its profile files (``$OS_COLOR``), and ocpy's three Kd LUTs.
About a minute.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

NETWORKS = ('MODIS_v1.1', 'MODIS_v1.3', 'PACE_v2.3')
LABEL = {'MODIS_v1.1': 'MODIS v1.1 (shipped)', 'MODIS_v1.3': 'MODIS v1.3',
         'PACE_v2.3': 'PACE v2.3'}
#: The realization the planning number (and RT-A, and the X=4 ladder) used.
HEADLINE = (4, 0)
REALIZATIONS = tuple((X, Y) for X in (4, 2, 1) for Y in (0, 30, 60))
#: Bands quoted in the tables: the planning four, plus the three where the
#: shipped network turned out to be furthest off.
BANDS = (410, 440, 490, 510, 520, 555, 580, 600, 670)
#: The networks are recommended for the visible only (authors' README);
#: spectra are computed to 750 nm, and summarised over this window.
VISIBLE = (400.0, 700.0)
INTERP = ('linear', 'cubic', 'nearest', 'gauss10')
SID = 'ls2_kd_15pct'

REPO = Path(__file__).resolve().parents[4]
DEFAULT_DOCS = REPO / 'docs' / 'source'


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #

def l23(X, Y, definition='ln_ratio'):
    """``(wave, Rrs, kd1)`` for one L23 realization (3320 x 81 each)."""
    from ocpy.hydrolight import loisel23

    from ioptics import kd

    ds = loisel23.load_ds(X, Y)
    wave = np.asarray(ds['Lambda'].values, dtype=float)
    rrs = np.asarray(ds['Rrs'].values, dtype=float)
    w, kd1 = kd.load_l23_kd1(X, Y, definition)
    if not np.allclose(w, wave):
        raise ValueError('profile and main L23 grids differ')
    return wave, rrs, kd1


def feed(wave, rrs, bands, how='linear'):
    """L23 ``Rrs`` sampled at a network's ``bands``, ``(N, nb)``."""
    bands = np.asarray(bands, dtype=float)
    if how == 'linear':
        return np.stack([np.interp(bands, wave, r) for r in rrs])
    if how == 'cubic':
        from scipy.interpolate import CubicSpline
        return CubicSpline(wave, rrs, axis=1)(bands)
    if how == 'nearest':
        return rrs[:, [int(np.argmin(np.abs(wave - b))) for b in bands]]
    if how == 'gauss10':                    # a 10 nm FWHM band
        s = 10.0 / 2.3548
        w = np.exp(-0.5 * ((wave[None, :] - bands[:, None]) / s) ** 2)
        return rrs @ (w / w.sum(axis=1, keepdims=True)).T
    raise ValueError(how)


def network_kd(net, wave, rrs, sza, out_wave, how='linear'):
    """A network's ``<Kd>_1`` for every spectrum at ``out_wave``, ``(N, L)``."""
    from ocpy.ls2 import kd_nn
    bands = kd_nn.load_network(net).bands
    return kd_nn.kd_nn(feed(wave, rrs, bands, how), float(sza),
                       np.asarray(out_wave, dtype=float), net)


def _col(wave, lam):
    j = int(np.argmin(np.abs(wave - lam)))
    if abs(wave[j] - lam) > 1e-6:
        raise ValueError(f'{lam} nm not on the L23 grid')
    return j


# --------------------------------------------------------------------------- #
# the tests
# --------------------------------------------------------------------------- #

def ratio_spectra():
    """Median and 16-84% of ``Kd_NN / Kd_L23`` per wavelength, every realization."""
    rows = []
    for X, Y in REALIZATIONS:
        wave, rrs, kd1 = l23(X, Y)
        sel = wave >= 400
        for net in NETWORKS:
            r = network_kd(net, wave, rrs, Y, wave[sel]) / kd1[:, sel]
            q = np.nanpercentile(r, [16, 50, 84], axis=0)
            for i, lam in enumerate(wave[sel]):
                rows.append({'X': X, 'Y': Y, 'network': net, 'wavelength': lam,
                             'p16': q[0, i], 'median': q[1, i], 'p84': q[2, i],
                             'n': int(np.isfinite(r[:, i]).sum())})
    return pd.DataFrame(rows)


def band_table(spectra, X, Y, bands=BANDS):
    """Median ratio at ``bands`` (rows: network), plus the visible-window spread."""
    s = spectra[(spectra.X == X) & (spectra.Y == Y)]
    out = []
    for net in NETWORKS:
        g = s[s.network == net].set_index('wavelength')['median']
        vis = g[(g.index >= VISIBLE[0]) & (g.index <= VISIBLE[1])]
        row = {'network': net}
        row.update({f'{b}': round(float(g.loc[float(b)]), 3) for b in bands})
        row['vis_min'] = round(float(vis.min()), 3)
        row['vis_max'] = round(float(vis.max()), 3)
        row['vis_mad'] = round(float(np.median(np.abs(vis - 1.0))), 3)
        out.append(row)
    return pd.DataFrame(out)


def definition_test(X=HEADLINE[0], Y=HEADLINE[1], bands=BANDS):
    """Median ratio at ``bands`` under each ``<Kd>_1`` definition (ls2 Q10)."""
    from ioptics import kd
    rows = []
    wave, rrs, _ = l23(X, Y)
    nn = {net: network_kd(net, wave, rrs, Y, np.asarray(bands, float))
          for net in NETWORKS}
    for d in kd.KD1_DEFINITIONS:
        _, _, kd1 = l23(X, Y, d)
        cols = [_col(wave, b) for b in bands]
        for net in NETWORKS:
            row = {'definition': d, 'network': net}
            row.update({f'{b}': round(float(np.nanmedian(nn[net][:, i]
                                                         / kd1[:, c])), 4)
                        for i, (b, c) in enumerate(zip(bands, cols))})
            rows.append(row)
    return pd.DataFrame(rows)


def kd_bin_test(X=HEADLINE[0], Y=HEADLINE[1], bands=(440, 490, 555)):
    """Additive or multiplicative?  Ratio per Kd quintile, and a linear fit.

    A pure-water difference adds the same ``dKd`` to every scenario, so the
    ratio falls towards 1 across the quintiles and the fit has ``beta != 0``,
    ``alpha ~ 1``.  A multiplicative error leaves the ratio flat, with
    ``beta ~ 0`` and ``alpha`` = the ratio.  ``beta`` is quoted as a share of
    the median L23 Kd at that band.
    """
    wave, rrs, kd1 = l23(X, Y)
    rows = []
    for net in NETWORKS:
        nn = network_kd(net, wave, rrs, Y, np.asarray(bands, float))
        for i, b in enumerate(bands):
            kt, kn = kd1[:, _col(wave, b)], nn[:, i]
            ok = np.isfinite(kt) & np.isfinite(kn)
            kt, kn = kt[ok], kn[ok]
            edges = np.quantile(kt, np.linspace(0, 1, 6))
            row = {'network': net, 'band': b}
            for q in range(5):
                m = (kt >= edges[q]) & (kt <= edges[q + 1])
                row[f'Q{q + 1}'] = round(float(np.median(kn[m] / kt[m])), 3)
            core = kt <= np.quantile(kt, 0.95)       # the turbid tail would steer OLS
            alpha, beta = np.polyfit(kt[core], kn[core], 1)
            row['alpha'] = round(float(alpha), 3)
            row['beta_over_median_kd'] = round(float(beta / np.median(kt)), 3)
            row['kd_range'] = f'{edges[0]:.3f}-{edges[-1]:.3f}'
            rows.append(row)
    return pd.DataFrame(rows)


def pure_water_test(X=HEADLINE[0], Y=HEADLINE[1], bands=BANDS,
                    net='MODIS_v1.1'):
    """How large a pure-water difference would close the gap, band by band?

    If the whole gap were pure water, ``Kd_NN - Kd_L23 = da_w / mu_d`` for
    every scenario, so ``da_w = median(Kd_NN - Kd_L23) * mu_d``, with ``mu_d``
    the effective cosine at 0- (ls2 Q9, ``ioptics.kd.load_l23_muw_effective``).
    That is quoted as a share of L23's own ``a_w`` (IOCCG 2018) and set
    beside the one alternative table on hand, ocpy's GSFC (Pope & Fry 1997),
    which turns out to be the same data from 440 to 700 nm.
    """
    from ocpy.water import absorption

    from ioptics import kd
    wave, rrs, kd1 = l23(X, Y)
    mud = float(np.nanmedian(kd.load_l23_muw_effective(X, Y)))
    b = np.asarray(bands, dtype=float)
    aw_i = absorption.a_water(b, data='IOCCG')
    aw_g = absorption.a_water(b, data='GSFC')
    nn = network_kd(net, wave, rrs, Y, b)
    rows = []
    for k, lam in enumerate(bands):
        need = float(np.nanmedian(nn[:, k] - kd1[:, _col(wave, lam)])) * mud
        rows.append({'band': lam, 'aw_L23_IOCCG': round(float(aw_i[k]), 5),
                     'aw_GSFC_PopeFry': round(float(aw_g[k]), 5),
                     'tables_differ_pct': round(float(100 * (aw_g[k] / aw_i[k] - 1)), 1),
                     f'daw_needed_{net}': round(need, 5),
                     'daw_needed_pct_of_aw': round(100 * need / float(aw_i[k]), 0)})
    return pd.DataFrame(rows), mud


def interp_test(X=HEADLINE[0], Y=HEADLINE[1], bands=(440, 490, 555, 670)):
    """Median ratio at ``bands`` for each way of putting L23 on the network's bands."""
    wave, rrs, kd1 = l23(X, Y)
    rows = []
    for net in NETWORKS:
        for how in INTERP:
            nn = network_kd(net, wave, rrs, Y, np.asarray(bands, float), how)
            row = {'network': net, 'interp': how}
            row.update({f'{b}': round(float(np.nanmedian(nn[:, i]
                                                         / kd1[:, _col(wave, b)])), 3)
                        for i, b in enumerate(bands)})
            rows.append(row)
    return pd.DataFrame(rows)


def domain_test(X=HEADLINE[0], Y=HEADLINE[1], bands=(440, 490, 555)):
    """Where L23 sits in each network's training distribution of ``log10 Kd``.

    The training output statistics are those of the clear branch (which takes
    98% of L23).  ``z`` = (log10 Kd_L23 - mean) / std, at the median L23
    scenario; ``frac_below_2sd`` = share of L23 scenarios more than 2 sigma
    below the training mean.
    """
    from ocpy.ls2 import kd_nn
    wave, _, kd1 = l23(X, Y)
    rows = []
    for net in NETWORKS:
        lay = kd_nn.load_network(net).clear
        for b in bands:
            lk = np.log10(kd1[:, _col(wave, b)])
            lk = lk[np.isfinite(lk)]
            z = (lk - lay.mu_kd) / lay.std_kd
            rows.append({'network': net, 'band': b,
                         'train_log10kd_mean': round(float(lay.mu_kd), 3),
                         'train_log10kd_std': round(float(lay.std_kd), 3),
                         'train_kd_geomean': round(float(10 ** lay.mu_kd), 3),
                         'l23_kd_median': round(float(10 ** np.median(lk)), 4),
                         'z_median': round(float(np.median(z)), 2),
                         'frac_below_2sd': round(float(np.mean(z < -2)), 3)})
    return pd.DataFrame(rows)


def realization_table(spectra, bands=(440, 490, 555, 670)):
    """Median ratio at ``bands`` for each (X, theta_s) and network."""
    rows = []
    for (X, Y), s in spectra.groupby(['X', 'Y']):
        for net in NETWORKS:
            g = s[s.network == net].set_index('wavelength')['median']
            row = {'X': X, 'theta_s': Y, 'network': net}
            row.update({f'{b}': round(float(g.loc[float(b)]), 3) for b in bands})
            rows.append(row)
    return pd.DataFrame(rows).sort_values(['network', 'X', 'theta_s'])


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #

def fig_ratio_spectrum(spectra, path, X=HEADLINE[0], Y=HEADLINE[1]):
    """Median and 16-84% of the ratio vs wavelength, one line per network."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    s = spectra[(spectra.X == X) & (spectra.Y == Y)]
    for net, c in zip(NETWORKS, ('C3', 'C1', 'C0')):
        g = s[s.network == net]
        ax.fill_between(g.wavelength, g.p16, g.p84, color=c, alpha=0.15, lw=0)
        ax.plot(g.wavelength, g['median'], color=c, lw=1.8, label=LABEL[net])
    ax.axhline(1, color='k', lw=0.8)
    for v in (0.9, 1.1):
        ax.axhline(v, color='k', lw=0.5, ls=':')
    ax.axvspan(VISIBLE[1], 750, color='0.85', alpha=0.5, lw=0)
    ax.set_xlim(400, 750)
    ax.set_ylim(0.5, 1.5)
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel(r'$K_d^{NN}\,/\,\langle K_d\rangle_1^{L23}$')
    ax.set_title(f'L23 X={X}, θs={Y}°: median and 16–84% over 3,320 scenarios',
                 fontsize=10)
    ax.legend(loc='lower left', fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_domain(path, X=HEADLINE[0], Y=HEADLINE[1], bands=(440, 490)):
    """L23's log10 Kd at ``bands`` against each network's training distribution."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from ocpy.ls2 import kd_nn
    wave, _, kd1 = l23(X, Y)
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    grid = np.linspace(-2.6, 1.2, 400)
    for b, ls in zip(bands, ('-', '--')):
        lk = np.log10(kd1[:, _col(wave, b)])
        ax.hist(lk[np.isfinite(lk)], bins=60, density=True, histtype='step',
                color='k', ls=ls, label=f'L23 ⟨Kd⟩₁({b})')
    for net, c, ls in zip(NETWORKS, ('C3', 'C1', 'C0'), ('-', '-', '--')):
        lay = kd_nn.load_network(net).clear
        pdf = np.exp(-0.5 * ((grid - lay.mu_kd) / lay.std_kd) ** 2) \
            / (lay.std_kd * np.sqrt(2 * np.pi))
        ax.plot(grid, pdf, color=c, ls=ls, lw=2.2 if ls == '-' else 1.6,
                label=f'{LABEL[net]} training (all λ)')
    ax.set_xlabel(r'$\log_{10} K_d$ [m$^{-1}$]')
    ax.set_ylabel('density')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# the page
# --------------------------------------------------------------------------- #

def _csv_table(caption, name):
    return (f'.. csv-table:: {caption}\n   :file: {name}\n   :header-rows: 1\n'
            f'   :widths: auto\n')


def build(docs_root=None):
    """Run every test and write the report page, CSVs and figures."""
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS
    out = docs_root / 'reports' / SID
    out.mkdir(parents=True, exist_ok=True)
    X, Y = HEADLINE

    spectra = ratio_spectra()
    bands = band_table(spectra, X, Y)
    defs = definition_test()
    bins = kd_bin_test()
    water, mud = pure_water_test()
    interp = interp_test()
    domain = domain_test()
    real = realization_table(spectra)

    tables = {'kd15_bands.csv': bands, 'kd15_definitions.csv': defs,
              'kd15_kd_bins.csv': bins, 'kd15_pure_water.csv': water,
              'kd15_interp.csv': interp, 'kd15_domain.csv': domain,
              'kd15_realizations.csv': real}
    for name, df in tables.items():
        df.to_csv(out / name, index=False)
    spectra.round(4).to_csv(out / 'kd15_ratio_spectra.csv', index=False)
    fig_ratio_spectrum(spectra, out / 'kd15_ratio_spectrum.png')
    fig_domain(out / 'kd15_domain.png')

    page = _page(spectra, bands, defs, bins, water, mud, interp, domain, real)
    path = out / f'{SID}.rst'
    path.write_text(page, encoding='utf-8')
    print(f'wrote {path}')
    return {'page': path, **{k: v for k, v in tables.items()},
            'spectra': spectra, 'mud': mud}


def _get(df, **kw):
    m = np.ones(len(df), dtype=bool)
    for k, v in kw.items():
        m &= (df[k] == v).to_numpy()
    return df[m].iloc[0]


def _page(spectra, bands, defs, bins, water, mud, interp, domain, real):
    """The report text.  Every number is read from the tables just computed."""
    X, Y = HEADLINE
    b = bands.set_index('network')
    v11, v13, pace = b.loc['MODIS_v1.1'], b.loc['MODIS_v1.3'], b.loc['PACE_v2.3']
    pct = lambda r: f'{100 * (float(r) - 1):+.0f}%'          # noqa: E731
    # definitions: the largest spread across the three, any network, any band
    bandcols = [str(x) for x in BANDS]
    dspread = max(float((g[bandcols].max() - g[bandcols].min()).max())
                  for _, g in defs.groupby('network'))
    # Kd bins for the shipped network
    b440 = _get(bins, network='MODIS_v1.1', band=440)
    b490 = _get(bins, network='MODIS_v1.1', band=490)
    # pure water
    w = water.set_index('band')
    tdiff = float(w.loc[[x for x in BANDS if x >= 440], 'tables_differ_pct'].abs().max())
    need = w['daw_needed_pct_of_aw']
    # interpolation
    it = interp.set_index(['network', 'interp'])
    lin, near = it.loc[('MODIS_v1.1', 'linear')], it.loc[('MODIS_v1.1', 'nearest')]
    smooth = max(float((it.loc[(n, h)][['440', '490', '555', '670']]
                        - it.loc[(n, 'linear')][['440', '490', '555', '670']]).abs().max())
                 for n in NETWORKS for h in ('cubic', 'gauss10'))
    # domain
    dm = domain.set_index(['network', 'band'])
    d11, d13 = dm.loc[('MODIS_v1.1', 440)], dm.loc[('MODIS_v1.3', 440)]
    # realizations
    r = real.set_index(['network', 'X', 'theta_s'])
    p4 = r.loc[('PACE_v2.3', 4, 0)]
    p1 = r.loc[('PACE_v2.3', 1, 0)]
    m60 = r.loc[('MODIS_v1.1', 4, 60)]
    xfrac = ((float(v11['440']) - float(r.loc[('MODIS_v1.1', 1, 0)]['440']))
             / (float(v11['440']) - 1.0))
    b13 = _get(bins, network='MODIS_v1.3', band=490)
    bc = ['440', '490', '555', '670']
    x24 = max(float((r.loc[(n, 4, y)][bc] - r.loc[(n, 2, y)][bc]).abs().max())
              for n in NETWORKS for y in (0, 30, 60))

    return f"""\
.. _ls2_kd_15pct:

==========================================================
The 15% question — Kd networks against L23's ⟨Kd⟩₁
==========================================================

:Task: ls2 task 10 (diagnostic; gates task 11)
:Script: ``ioptics/runs/prototypes/ls2/kd_15pct.py`` (regenerates every number,
   table and figure on this page)
:Data: L23 (Loisel et al. 2023), noise-free ``Rrs``; ⟨Kd⟩₁ from the profile
   files, canonical ``ln_ratio`` definition unless stated
:Networks: the authors' MODIS v1.1 (what ocpy shipped), MODIS v1.3 (their
   current retrain) and PACE v2.3, as ported to ``ocpy.ls2.kd_nn``

Summary
-------

**L23's ⟨Kd⟩₁ is not the thing that is wrong.  The 15% is an error of the
MODIS v1.1 network, and it is part of a larger one.**

* The planning number reproduces.  On L23 X={X}, θs={Y}°, the shipped
  MODIS v1.1 network reads {pct(v11['440'])} at 440 nm and {pct(v11['490'])} at
  490 nm, and {pct(v11['555'])} and {pct(v11['670'])} at 555 and 670 nm.
* But it is not a blue-only offset.  Across 400–700 nm the same network swings
  from {pct(v11['vis_min'])} to {pct(v11['vis_max'])}, a sawtooth in output
  wavelength: {pct(v11['510'])} at 510, {pct(v11['520'])} at 520,
  {pct(v11['580'])} at 580 and {pct(v11['600'])} at 600 nm.  The four
  planning bands happened to sample two high points and two near-crossings.
* The authors' **PACE v2.3** network, a second independent implementation
  whose bands sit exactly on L23's grid, agrees with L23 to a median
  {100 * float(pace['vis_mad']):.1f}% over 400–700 nm (range
  {pct(pace['vis_min'])} to {pct(pace['vis_max'])}).  Their **MODIS v1.3**
  retrain, on the same five bands as v1.1, removes the 440 nm gap
  ({pct(v13['440'])}) but not the 490 nm one ({pct(v13['490'])}).  Its
  median deviation over 400–700 nm is {100 * float(v13['vis_mad']):.1f}%,
  against {100 * float(v11['vis_mad']):.1f}% for v1.1.
* No other candidate comes close.  The ⟨Kd⟩₁ definition moves the ratio by at
  most {100 * dspread:.2f}%, and smooth band interpolation by at most
  {100 * smooth:.1f}%.  The gap scales with Kd (multiplicative), whereas a
  pure-water difference would add a fixed offset; closing it with pure
  water would need ``a_w`` to swing from {need.loc[580]:+.0f}% to
  {need.loc[600]:+.0f}% between 580 and 600 nm.

**Recommendation.**  Use L23's ⟨Kd⟩₁ (X=4, canonical definition) as the
training truth for task 11.  Use PACE v2.3 as the baseline that task 11's
networks must beat.  Flip ``Kd_NN_MODIS``'s default to v1.3, as Q30 agreed once
this report was in, but treat it as a documented alternative only: it is still
{pct(v13['490'])} at 490 nm.

The ratio, wavelength by wavelength
-----------------------------------

.. figure:: kd15_ratio_spectrum.png
   :width: 90%

   ``Kd_NN / ⟨Kd⟩₁(L23)`` on L23 X={X}, θs={Y}°.  Lines are the median over the
   3,320 scenarios, bands the 16–84% range.  Grey: above 700 nm, outside the
   range the authors recommend.  There all three networks fall away together
   (to about 0.3–0.4 at 740 nm), and L23 is not the network's training domain.

{_csv_table(f'Median ratio at selected bands (X={X}, θs={Y}°), with the min, max and median absolute deviation from 1 over 400–700 nm.', 'kd15_bands.csv')}
Candidate 1: the ⟨Kd⟩₁ definition
---------------------------------

The three definitions of ls2 Q10 agree to better than 0.03% in the median
(``ioptics.kd``).  As the denominator of the ratio they move it by at most
{100 * dspread:.2f}% at any quoted band, for any network.  **Ruled out.**

{_csv_table('Median ratio under each ⟨Kd⟩₁ definition.', 'kd15_definitions.csv')}
Candidate 2: pure-water absorption
----------------------------------

A pure-water difference between L23 and the network's training RT adds the
same ``Δa_w / μ_d`` to every scenario.  Its signature is a ratio that falls
towards 1 as Kd grows, and a linear fit ``Kd_NN = α·Kd_L23 + β`` with
``β ≠ 0`` and ``α ≈ 1``.  The shipped network shows the opposite.  At 440 nm
its ratio is {b440['Q1']}, {b440['Q2']}, {b440['Q3']}, {b440['Q4']} and
{b440['Q5']} across the Kd quintiles ({b440['kd_range']} m⁻¹).  At 490 nm it is
{b490['Q1']} → {b490['Q5']}.  The fit gives α = {b440['alpha']} and
{b490['alpha']} at 440 and 490 nm, with β only {100 * b440['beta_over_median_kd']:+.0f}%
and {100 * b490['beta_over_median_kd']:+.0f}% of the median Kd.  The error
scales with Kd: it is multiplicative.

On size: closing the gap with pure water alone would need ``a_w`` to change by
{need.loc[440]:+.0f}% at 440 nm and {need.loc[490]:+.0f}% at 490 nm, then
{need.loc[520]:+.0f}% at 520, {need.loc[580]:+.0f}% at 580 and {need.loc[600]:+.0f}% at
600 nm.  The sign flips three times within 120 nm, and no pure-water table
does that.  (The one alternative table on hand, ocpy's GSFC Pope & Fry, is
L23's own data from 440 to 700 nm, differing by at most {tdiff:.1f}%.)
**Ruled out**, on structure and on size.

{_csv_table('Ratio per Kd quintile and linear fit (X=4, θs=0°; fit on the clearest 95%).', 'kd15_kd_bins.csv')}
{_csv_table('The a_w change that would close the MODIS v1.1 gap on its own, and the tables on hand.', 'kd15_pure_water.csv')}
Candidate 3: band interpolation
-------------------------------

L23 is on a 5 nm grid, and MODIS's bands are not (443, 488, 531, 547, 667 nm).
The LS2 driver interpolates linearly.  Cubic interpolation, or a 10 nm Gaussian
band, changes the median ratio by at most {100 * smooth:.1f}% for any network.
Nearest-band sampling does matter, as planning found: for MODIS v1.1 it takes
440 nm from {pct(lin['440'])} to {pct(near['440'])} and 490 nm from
{pct(lin['490'])} to {pct(near['490'])}.  But that is a 2–3 nm shift of the
inputs, and it shows how sensitive the network is.  It is not a defect of the
linear interpolation.  **Ruled out**, provided interpolation is linear or
better.  PACE v2.3 needs no interpolation, since its bands are on L23's grid.

{_csv_table('Median ratio for four ways of putting L23 on the network bands (X=4, θs=0°).', 'kd15_interp.csv')}
Candidate 4: the network
------------------------

Three implementations by the same authors give three answers on identical
inputs.  The two MODIS releases differ from each other by as much as the gap
itself ({pct(v11['440'])} against {pct(v13['440'])} at 440 nm).  The PACE
network, trained on a different set and architecture, agrees with L23 across
the visible.  If L23's ⟨Kd⟩₁ were wrong, it would have to be wrong in a way
that PACE v2.3 shares and both MODIS releases do not, at different
wavelengths for each.  The economical reading is that the MODIS networks,
v1.1 above all, carry an output-wavelength-dependent error.  Their only
spectral input is five bands, and output wavelength is just another input to
a small MLP.  v1.3's remaining 490 nm gap is a clear-water one: it is
{b13['Q1']} in the clearest Kd quintile and {b13['Q5']} in the most turbid.
**This is the explanation.**

A new candidate: the training domain
------------------------------------

The LUTs store each network's training mean and standard deviation of
``log10 Kd``.  MODIS v1.1 was trained around a geometric-mean Kd of
{d11['train_kd_geomean']} m⁻¹ (σ = {d11['train_log10kd_std']} dex).  MODIS v1.3 and
PACE v2.3 were trained around {d13['train_kd_geomean']} m⁻¹.  L23's median
⟨Kd⟩₁(440) is {d11['l23_kd_median']} m⁻¹, at z = {d11['z_median']} in v1.1's
training distribution, with {100 * d11['frac_below_2sd']:.0f}% of scenarios more
than 2σ below its mean, against z = {d13['z_median']} for v1.3.  L23's clear
blue water is the thin edge of what v1.1 learned, which is where a small
network is least constrained.  This supports Candidate 4; it does not replace
it.  These statistics pool all wavelengths, so they bound the domain loosely.

.. figure:: kd15_domain.png
   :width: 80%

   L23's ⟨Kd⟩₁ at 440 and 490 nm (X=4, θs=0°) against each network's training
   distribution of ``log10 Kd``, drawn as the Gaussian of the stored mean and
   standard deviation.  MODIS v1.3 and PACE v2.3 store the same output
   statistics, so their curves coincide (PACE dashed).  The training
   statistics pool all output wavelengths, red included, which is why even
   the better-placed networks sit above L23's blue values.

{_csv_table('L23 in each network training distribution (clear branch).', 'kd15_domain.csv')}
A new candidate: inelastic light and the sun
--------------------------------------------

L23 comes in three inelastic realizations, and the networks' training RT
includes whatever inelastic light it includes.  At these bands it is Raman that
matters.  X=2 (Raman only) and X=4 (Raman + Chl fluorescence) give the same
ratios to within {100 * x24:.1f}%.  The elastic X=1 lowers every network's
ratio: PACE v2.3 goes from {pct(p4['440'])}, {pct(p4['490'])}, {pct(p4['555'])},
{pct(p4['670'])} at 440/490/555/670 nm on X=4 to {pct(p1['440'])},
{pct(p1['490'])}, {pct(p1['555'])}, {pct(p1['670'])} on X=1, and MODIS v1.1's
440 nm gap shrinks from {pct(v11['440'])} to {pct(r.loc[('MODIS_v1.1', 1, 0)]['440'])}.
So {100 * xfrac:.0f}% of v1.1's 440 nm gap moves with the realization.  PACE v2.3
fits the Raman-on realizations best, consistent with a training RT that included Raman,
as real water does.  Train against X=4 (task 11).  The sun does little:
the shipped network's 440 nm ratio is {pct(v11['440'])} at θs = 0° and
{pct(m60['440'])} at 60°.  This confirms planning's finding that the geometry
is consistent.

{_csv_table('Median ratio at four bands for every L23 realization.', 'kd15_realizations.csv')}
What this page does not settle
------------------------------

* Which network is right *in situ*.  L23 is a model ocean.  PACE v2.3 agreeing
  with it shows two RT-trained products agree, not that either matches the
  sea.  The five-band network of task 11 is validated against PANGAEA for that
  reason.
* The networks' training sets are not described in the distribution.  The
  stored statistics are all that is known of them here.
* Above 700 nm every network falls far below L23.  That is outside the
  authors' recommended range, and LS2's κ is NaN there anyway (ls2 task 1).
"""


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--docs-root', default=None)
    build(p.parse_args().docs_root)

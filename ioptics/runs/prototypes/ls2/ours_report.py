"""Our own LS2 against the published one, and against BING (ls2 task 14).

Tasks 11-13 re-derived LS2's three learned pieces from L23: the Kd network
(``ocpy.ls2.kd_l23``), the a/bb coefficient tables and kappa (both in
``ocpy/data/LS2/LS2_LUT_L23_abk_v1.npz``).  This script writes the page that
puts them together, ``docs/source/reports/ls2_ours/``.  Every number on it is
computed here, from L23 directly or from the LS2 sweeps and RT-A.

1. **The headline** (ls2 task 14): does the re-derivation remove rung (i)'s
   measured biases (planning: ``a`` +2.6%, ``bb`` +9.8%, ``bb_p`` +24%), and
   how much of the ``a`` part was illumination bookkeeping rather than
   coefficients?  Measured exactly as ``rung_i_baseline.py`` measures rung
   (i): noise-free L23 X=4, true ``<Kd>_1`` and ``b_p``, ocpy's pure water,
   Raman iterated.  It is scored on the **498 held-out scenarios**, since the
   tables were fitted on the rest, and per solar zenith, against four table
   configurations: published, published at the effective ``mu_w`` (ls2 Q9),
   refit a/bb with the published kappa, and refit a/bb + refit kappa.
2. **The ladder, held out** (ls2 Q39): every rung of the
   ``ls2_l23_x4_heldout_v1`` sweep (noisy Rrs, as in RT-A), published beside
   re-derived, including ``ls2r_iii_l23`` with Kd from our own network.
3. **LS2 against MCMC BING** on L23 X=4 at matched wavelengths: RT-A's
   ``expb_pow_hyb_ramfl`` (ls2 Q36) paired spectrum by spectrum and band by
   band with LS2 rungs, scored on the cells both returned.  Note that RT-A
   and the LS2 sweeps draw their noise independently (same form, ls2 Q15).

Usage, from the repository root (after ``build_v1.py 1`` and ``2``)::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \\
        ioptics/runs/prototypes/ls2/ours_report.py [--docs-root DIR]
"""

from __future__ import annotations

import warnings
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd

SID = 'ls2_ours'
REPO = Path(__file__).resolve().parents[4]
DEFAULT_DOCS = REPO / 'docs' / 'source'
THETAS = (0, 30, 60)
WAVE_RANGE = (400.0, 750.0)
ANW_SHARE = 0.10
MAIN_SWEEP = 'ls2_l23_x4_v1'
HELDOUT_SWEEP = 'ls2_l23_x4_heldout_v1'
RTA_SWEEP = 'rt_tests_A_l23_v1'
BING_ALGO = 'expb_pow_hyb_ramfl'
#: LS2 rungs set against BING, best case and operational, published and ours.
VS_BING = ('ls2_i', 'ls2r_i', 'ls2_iii', 'ls2r_iii')
VS_BING_HELDOUT = VS_BING + ('ls2r_iii_l23',)
REF = {'a': 440.0, 'a_nw': 440.0, 'bb': 555.0, 'bb_p': 555.0}
PLANNING = {'a': 0.026, 'bb': 0.098, 'bb_p': 0.24}

CONFIGS = (('published', 'published', 'snell'),
           ('published at effective μw', 'published', 'effective'),
           ('refit a/bb + published κ', 'L23_v1', 'snell'),
           ('our LS2 (refit a/bb + κ)', 'L23_abk_v1', 'snell'))


# --------------------------------------------------------------------------- #
# 1. headline
# --------------------------------------------------------------------------- #

def headline(X=4):
    """Rung (i), noise-free, held-out scenarios: median relative errors."""
    from ocpy.hydrolight import loisel23
    from ocpy.ls2.ls2_main import ls2_invert

    from ioptics import kd, kd_net
    from ioptics.algorithms.ls2 import _lut, pure_water

    ids = kd_net.split_scenarios()['test']
    rows = []
    for Y in THETAS:
        ds = loisel23.load_ds(X, Y)
        L = np.asarray(ds['Lambda'].values, float)
        sel = (L >= WAVE_RANGE[0]) & (L <= WAVE_RANGE[1])
        g = lambda v: np.asarray(ds[v].values, float)[ids][:, sel]   # noqa: E731
        R, a, anw, bb, bbnw, bnw = (g(v) for v in ('Rrs', 'a', 'anw', 'bb', 'bbnw', 'bnw'))
        kd1 = kd.load_l23_kd1(X, Y)[1][ids][:, sel]
        a_w, b_w = pure_water(L[sel])
        truth = {'a': a, 'bb': bb, 'bb_p': bbnw, 'a_nw': anw}
        share = anw / a >= ANW_SHARE
        for label, lut, mode in CONFIGS:
            muw = (kd.load_l23_muw_effective(X, Y)[ids][:, None]
                   if mode == 'effective' else None)
            res = ls2_invert(R, kd1, a_w, b_w, bnw, np.full(len(ids), float(Y)),
                             L[sel], _lut(lut), raman=X != 1, clip_negative=False,
                             muw=muw)
            got = {'a': res.a, 'bb': res.bb, 'bb_p': res.bbp, 'a_nw': res.anw}
            row = {'theta_s': Y, 'tables': label}
            for comp in ('a', 'bb', 'bb_p', 'a_nw'):
                with np.errstate(divide='ignore', invalid='ignore'):
                    r = got[comp] / truth[comp] - 1
                if comp == 'a_nw':
                    r = np.where(share, r, np.nan)
                row[f'{comp}_median_err'] = round(float(np.nanmedian(r[np.isfinite(r)])), 4)
            row['kappa_unavailable'] = round(float(res.kappa_out_of_range.mean()), 4)
            row['off_grid'] = round(float(res.off_grid.mean()), 4)
            rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 2. held-out ladder
# --------------------------------------------------------------------------- #

def heldout_tables():
    from ioptics.report import figures, ls2_ladder
    sw = figures.load(HELDOUT_SWEEP)
    lad = ls2_ladder.ladder_table(sw, write=False)
    red = ls2_ladder.rederived_table(sw, write=False)
    return lad, red


# --------------------------------------------------------------------------- #
# 3. against BING
# --------------------------------------------------------------------------- #

def _spectral(sweep_id, algorithms, fit_method=None):
    import pyarrow.parquet as pq

    from ioptics import io
    filt = [('algorithm', 'in', list(algorithms)),
            ('component', 'in', ['a', 'a_nw', 'bb', 'bb_p'])]
    if fit_method:
        filt.append(('fit_method', '==', fit_method))
    t = pq.read_table(io.sweep_dir(sweep_id) / io.SPECTRAL_FILE, filters=filt,
                      columns=['obs_id', 'algorithm', 'component', 'wavelength',
                               'value', 'truth'])
    return t.to_pandas()


def _scalar_ok(sweep_id, algorithms, fit_method=None, statuses=('ok',)):
    from ioptics import io
    _, sc = io.read_results(sweep_id)
    sc = sc[sc['algorithm'].isin(algorithms) & sc['status'].isin(statuses)]
    if fit_method:
        sc = sc[sc['fit_method'] == fit_method]
    return sc[['obs_id', 'algorithm']]


def vs_bing(ls2_sweep, rungs, ids=None):
    """LS2 rungs against BING, paired by (spectrum, band, component)."""
    from ioptics import metrics
    bing = _spectral(RTA_SWEEP, [BING_ALGO], 'mcmc')
    bing = bing.merge(_scalar_ok(RTA_SWEEP, [BING_ALGO], 'mcmc'),
                      on=['obs_id', 'algorithm'])
    ls2 = _spectral(ls2_sweep, rungs)
    ls2 = ls2.merge(_scalar_ok(ls2_sweep, rungs, statuses=('ok', 'poor_fit')),
                    on=['obs_id', 'algorithm'])
    if ids is not None:
        bing = bing[bing['obs_id'].isin(ids)]
        ls2 = ls2[ls2['obs_id'].isin(ids)]
    key = ['obs_id', 'component', 'wavelength']
    # Q34 mask for a_nw: truth a_nw / truth a >= 10%
    ta = bing[bing.component == 'a'][['obs_id', 'wavelength', 'truth']].rename(
        columns={'truth': 'a_truth'})
    rows = []
    for rung in rungs:
        m = ls2[ls2.algorithm == rung].merge(
            bing[key + ['value', 'truth']], on=key, suffixes=('_ls2', '_bing'))
        m = m.merge(ta, on=['obs_id', 'wavelength'], how='left')
        keep = ~((m.component == 'a_nw') & (m.truth_bing / m.a_truth < ANW_SHARE))
        m = m[keep]
        tdiff = np.nanmax(np.abs(m.truth_ls2 / m.truth_bing - 1)) if len(m) else np.nan
        for comp in ('a', 'a_nw', 'bb', 'bb_p'):
            for scope, mm in (('400–750 nm', m[m.component == comp]),
                              (f'{REF[comp]:g} nm', m[(m.component == comp)
                                                      & (m.wavelength == REF[comp])])):
                ok = (np.isfinite(mm.value_ls2) & np.isfinite(mm.value_bing)
                      & (mm.value_ls2 > 0) & (mm.value_bing > 0) & (mm.truth_bing > 0))
                mm = mm[ok]
                if mm.empty:
                    continue
                el = np.abs(np.log(mm.value_ls2 / mm.truth_bing))
                eb = np.abs(np.log(mm.value_bing / mm.truth_bing))
                rows.append({'rung': rung, 'component': comp, 'scope': scope,
                             'n_spectra': int(mm.obs_id.nunique()),
                             'n_cells': int(len(mm)),
                             'mae_ls2': round(metrics.mae(mm.value_ls2, mm.truth_bing), 4),
                             'mae_bing': round(metrics.mae(mm.value_bing, mm.truth_bing), 4),
                             'bias_ls2': round(metrics.bias(mm.value_ls2, mm.truth_bing), 4),
                             'bias_bing': round(metrics.bias(mm.value_bing, mm.truth_bing), 4),
                             'ls2_win_frac': round(float(np.mean(el < eb)), 3),
                             'max_truth_mismatch': float(f'{tdiff:.2g}')})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# page
# --------------------------------------------------------------------------- #

def _tbl(caption, name):
    return (f'.. csv-table:: {caption}\n   :file: {name}\n   :header-rows: 1\n'
            f'   :widths: auto\n')


def build(docs_root=None):
    from ioptics import kd_net
    from ioptics.algorithms import registry
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    registry.register_direct()
    registry.register_direct_l23()
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS
    out = docs_root / 'reports' / SID
    out.mkdir(parents=True, exist_ok=True)

    head = headline()
    lad, red = heldout_tables()
    ids = [int(i) for i in kd_net.split_scenarios()['test']]
    vb_all = vs_bing(MAIN_SWEEP, VS_BING)
    vb_held = vs_bing(HELDOUT_SWEEP, VS_BING_HELDOUT, ids=ids)
    tables = {'ours_headline.csv': head, 'ours_heldout_ladder.csv': lad.round(4),
              'ours_heldout_rederived.csv': red.round(4),
              'ours_vs_bing_all.csv': vb_all, 'ours_vs_bing_heldout.csv': vb_held}
    for nm, df in tables.items():
        df.to_csv(out / nm, index=False)
    (out / f'{SID}.rst').write_text(_page(head, lad, red, vb_all, vb_held),
                                    encoding='utf-8')
    print(f'wrote {out / (SID + ".rst")}')
    return tables


def bing_decomposition():
    """RT-A's MCMC ``a_ph(440)`` and ``a_dg(440)`` mae for :data:`BING_ALGO`."""
    from ioptics.report import figures
    ms = figures.load(RTA_SWEEP).metrics_scalar
    col = 'pool' if 'pool' in ms.columns else 'fit_method'
    g = ms[(ms.algorithm == BING_ALGO) & (ms[col] == 'mcmc') & (ms.stratum == 'all')
           & (ms.ref_wave == 440.0)]
    return tuple(float(g[g.component == c]['mae'].iloc[0]) for c in ('a_ph', 'a_dg'))


def _page(head, lad, red, vb_all, vb_held):
    pc = lambda v: f'{100 * float(v):+.1f}%'                 # noqa: E731
    pu = lambda v: f'{100 * float(v):.1f}%'                  # noqa: E731
    H = head.set_index(['theta_s', 'tables'])
    h = lambda t, c, th=0: H.loc[(th, t)][f'{c}_median_err']  # noqa: E731
    pub, eff = 'published', 'published at effective μw'
    ab, ours = 'refit a/bb + published κ', 'our LS2 (refit a/bb + κ)'
    a_pub, a_eff, a_ours = h(pub, 'a'), h(eff, 'a'), h(ours, 'a')
    shift = a_pub - a_eff
    book_txt = (f'a shift of {100 * shift:.1f} points, **more than the whole '
                f'bias**: the ``a`` bias is entirely illumination bookkeeping, '
                f'and entering at μ_eff overshoots to {pc(a_eff)}'
                if shift >= a_pub else
                f'a shift of {100 * shift:.1f} points, **{pu(shift / a_pub)} of the '
                f'bias**')
    kshare = lambda c: (h(ab, c) - h(ours, c)) / h(ab, c)    # noqa: E731
    b555 = lambda r: V.loc[(r, 'bb', '555 nm')]              # noqa: E731
    L = lad.set_index('rung')
    aph_bing, adg_bing = bing_decomposition()
    V = vb_held.set_index(['rung', 'component', 'scope'])

    def v(rung, comp, scope='400–750 nm'):
        try:
            return V.loc[(rung, comp, scope)]
        except KeyError:
            return None

    def verdict(rung):
        lines = []
        for comp in ('a', 'a_nw', 'bb', 'bb_p'):
            r = v(rung, comp)
            if r is None:
                continue
            who = 'LS2' if r['mae_ls2'] < r['mae_bing'] else 'BING'
            lines.append(f'``{comp}`` {pu(r["mae_ls2"])} vs {pu(r["mae_bing"])} '
                         f'(LS2 closer on {pu(r["ls2_win_frac"])} of cells) → '
                         f'**{who}**')
        return '; '.join(lines)

    def lad_cell(rung, col):
        try:
            return pu(L.loc[rung][col])
        except KeyError:
            return 'n/a'

    return f"""\
.. _ls2_ours:

======================================================
Our own LS2: the re-derived algorithm, and LS2 vs BING
======================================================

:Task: ls2 task 14
:Script: ``ioptics/runs/prototypes/ls2/ours_report.py`` (every number and
   table on this page)
:Pieces: Kd network ``ocpy.ls2.kd_l23`` (task 11, :ref:`ls2_kd_l23`); a/bb
   tables (task 12, :ref:`ls2_refit_ab`); κ (task 13, :ref:`ls2_refit_kappa`);
   together in ``ocpy/data/LS2/LS2_LUT_L23_abk_v1.npz``
:Held out: 498 IOP scenarios no re-derived piece was fitted to (the split of
   ``ioptics.kd_net``); every comparison involving a re-derived piece is
   quoted on them

The headline: rung (i)'s biases
-------------------------------

Rung (i) gives LS2 everything as truth: noise-free L23 X=4 ``Rrs``, true
⟨Kd⟩₁ and ``b_p``.  What error remains is the tables'.  Planning measured
``a`` +2.6%, ``bb`` +9.8%, ``bb_p`` +24% (θs = 0°).  On the held-out
scenarios, at θs = 0° (median relative error, 400–750 nm):

* **published**: ``a`` {pc(h(pub, 'a'))}, ``bb`` {pc(h(pub, 'bb'))}, ``bb_p``
  {pc(h(pub, 'bb_p'))}; κ unavailable on {pu(H.loc[(0, pub)]['kappa_unavailable'])}
  of cells;
* **our LS2**: ``a`` {pc(h(ours, 'a'))}, ``bb`` {pc(h(ours, 'bb'))}, ``bb_p``
  {pc(h(ours, 'bb_p'))}; κ unavailable on
  {pu(H.loc[(0, ours)]['kappa_unavailable'])}.

**The re-derivation removes the ``a`` bias and most of the ``bb`` and
``bb_p`` biases.**  The step through ``refit a/bb + published κ`` (``a``
{pc(h(ab, 'a'))}, ``bb`` {pc(h(ab, 'bb'))}, ``bb_p`` {pc(h(ab, 'bb_p'))}) shows
which piece did what.  The a/bb refit takes out ``a``, and κ then removes
{pu(kshare('bb'))} of what is left in ``bb`` and {pu(kshare('bb_p'))} in
``bb_p``.  What remains is largest at θs = 0° (``bb`` {pc(h(ours, 'bb'))}, ``bb_p``
{pc(h(ours, 'bb_p'))}), which is exactly where task 13 found κ off its pooled
cubic.  At θs = 30° it is {pc(h(ours, 'bb', 30))} and
{pc(h(ours, 'bb_p', 30))}.  X=4's chlorophyll fluorescence, which no κ here
models, is a second candidate; this page does not separate the two.

**How much of the ``a`` bias was illumination bookkeeping.**  Entering the
*published* tables at L23's effective μw (ls2 Q9), with no refit, takes ``a``
from {pc(a_pub)} to {pc(a_eff)} at θs = 0°: {book_txt}.  The refit lands at
{pc(a_ours)}.  At θs = 60°, where
Snell's μw and the effective one nearly agree, the published ``a`` error is
already {pc(h(pub, 'a', 60))}.  The refit's own ``c0`` matches 1/μ_eff rather
than 1/μw (task 12): the bookkeeping is absorbed into the re-derived
coefficients, which is why our LS2 runs at Snell's μw.

{_tbl('Rung (i), noise-free L23 X=4, held-out scenarios: median relative error per table configuration and zenith; a_nw only where a_nw/a ≥ 0.1.', 'ours_headline.csv')}
The ladder on held-out spectra
------------------------------

The same ladder as the sweep pages, with the PACE noise form, run on the 498
held-out scenarios only (sweep ``ls2_l23_x4_heldout_v1``), so a published rung
and its re-derived twin are compared on spectra neither saw.
``ls2r_iii_l23`` takes Kd from our own L23 network and appears only here
(ls2 Q39).  Operational LS2 (rung iii: a Kd network and OC4v4 ``b_p``) has
``a(440)`` mae {lad_cell('ls2_iii', 'a_440_mae')} with the authors' tables and
PACE network, {lad_cell('ls2r_iii', 'a_440_mae')} with our tables and their
network, and {lad_cell('ls2r_iii_l23', 'a_440_mae')} with our tables and our
network.

{_tbl('Held-out ladder (noisy Rrs): one row per rung.', 'ours_heldout_ladder.csv')}
{_tbl('Held-out: each published rung beside its re-derived twin (median ratio and mae per cell).', 'ours_heldout_rederived.csv')}
LS2 against BING
----------------

RT-A's MCMC BING (``{BING_ALGO}``, the rung whose physics matches X=4, ls2
Q36), paired with LS2 cell by cell: same spectrum, same wavelength, both
retrievals finite and positive.  BING spectra with status ``ok``; LS2 spectra
``ok`` or ``poor_fit``, whose finite cells are scored (ls2 Q31).  ``a_nw``
only where ``a_nw/a`` ≥ 0.1.  ``ls2_win_frac`` is the share of paired cells
where LS2 is closer to truth.  The two sweeps used independent noise draws of
the same form (ls2 Q15), so this pairs spectra, not noise realizations.

On the held-out spectra, across 400–750 nm:

* **our operational LS2** (``ls2r_iii_l23``: our network, OC4v4 ``b_p``, our
  tables): {verdict('ls2r_iii_l23')};
* **our LS2 with true inputs** (``ls2r_i``): {verdict('ls2r_i')};
* **published operational LS2** (``ls2_iii``): {verdict('ls2_iii')}.

**Why ``bb`` and ``bb_p`` go to BING.**  LS2 is closed-form band by band, so
the noise in each band's ``Rrs`` goes straight into that band's ``bb``:
PACE noise is about 11% of ``Rrs`` at 555 nm and about 50% at 670 nm.  BING
fits one smooth spectral model to the whole spectrum, which averages the
noise.  At 555 nm, our ``bb`` with true inputs is off by
{pu(b555('ls2r_i')['mae_ls2'])}, against BING's {pu(b555('ls2r_i')['mae_bing'])};
across 400–750 nm the red bands dominate LS2's error.  The noise-free headline
above is where the tables themselves are measured; this is LS2 as it would
run.

**On absorption, our LS2 is competitive.**  With our own Kd network, over
400–750 nm, its ``a`` is {pu(V.loc[('ls2r_iii_l23', 'a', '400–750 nm')]['mae_ls2'])}
against BING's {pu(V.loc[('ls2r_iii_l23', 'a', '400–750 nm')]['mae_bing'])}, and
its ``a_nw`` {pu(V.loc[('ls2r_iii_l23', 'a_nw', '400–750 nm')]['mae_ls2'])} against
{pu(V.loc[('ls2r_iii_l23', 'a_nw', '400–750 nm')]['mae_bing'])}.  At 440 nm it is
ahead on both (``a`` {pu(V.loc[('ls2r_iii_l23', 'a', '440 nm')]['mae_ls2'])}
against {pu(V.loc[('ls2r_iii_l23', 'a', '440 nm')]['mae_bing'])}).  With true
inputs, it beats BING on ``a`` and ``a_nw`` everywhere.  The published
operational LS2 loses everything.

**Where LS2 forfeits, whatever its tables.**  LS2 returns ``a``, ``a_nw``,
``bb`` and ``bb_p``, and nothing else.  It has **no** ``a_ph`` and **no**
``a_dg``: there is no decomposition to score, and that absence is the point
of the comparison, not a gap in it.  BING returns both, though not well:
RT-A's ``a_ph(440)`` mae is {aph_bing:.3f} for this rung, and ``a_dg(440)``
{adg_bing:.3f} (:doc:`/reports/ls2_l23_x4_v1/ls2_ladder`).  LS2 also needs a Kd it cannot get from ``Rrs`` alone, which
is why the operational rungs exist.

{_tbl('Held-out spectra: LS2 rungs against MCMC BING, paired by cell, over 400–750 nm and at the reference band.', 'ours_vs_bing_heldout.csv')}
{_tbl('All 3,320 spectra (re-derived rungs partly in-sample: their tables were fitted on 70% of these scenarios).', 'ours_vs_bing_all.csv')}
Limits
------

* Everything here is L23.  Task 11 found real water (PANGAEA) attenuating
  more than L23 predicts from the same ``Rrs``, and the re-derived tables are
  as transferable as L23 is realistic.
* κ's dependence on the sun (task 13) and Chl fluorescence (X=4) remain.
* ``b/a`` above L23's 14 (turbid water) and θs above 60° are extrapolations
  of the re-derived tables.
"""


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--docs-root', default=None)
    build(p.parse_args().docs_root)

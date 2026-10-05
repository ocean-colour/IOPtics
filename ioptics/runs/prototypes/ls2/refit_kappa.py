"""Re-derive LS2's Raman correction ``kappa`` from the matched L23 pair (ls2 task 13).

``kappa`` turns the observed, Raman-inclusive ``Rrs`` into the elastic one
(``Rrs_elastic = kappa * Rrs``).  It is tabulated per wavelength as a cubic in
``bb/a``, with an admissible ``bb/a`` range per row.  The published table has
three defects on L23 (ls2 Q12):

- it stops at **702 nm**, so κ is NaN above it;
- its ``bb/a`` ranges do not cover L23: **19.1%** of cells fall outside
  (planning's figure);
- its **502 nm row** has a collapsed range ([0.0674, 0.0741]) and coefficients
  of order 1e5, a bad fit that costs about 44% of cells near 490-505 nm.

L23 gives a cleaner κ than the paper had: **X=1 (elastic) and X=2 (Raman only)
are the same water bodies under the same sun**, so ``Rrs(X=1)/Rrs(X=2)`` *is*
κ, cell by cell, with no model in between.  This script refits the table over
**350-750 nm** at L23's 5 nm grid, with each row's range taken from L23
itself, on the training scenarios of the shared split
(``ioptics.kd_net.split_scenarios``).

Steps, every number on the page included:

1. **Form selection.**  Cubic in ``bb/a`` or in ``ln(bb/a)``, with no
   geometry dependence or with a ``mu_w`` term, scored on held-out scenarios
   and by the leave-one-zenith-out check (0/60 -> 30, 0/30 -> 60).
2. **Fit** the chosen form (:func:`ocpy.ls2.refit.fit_kappa`).
3. **κ against truth** on the held-out cells: the published table, the refit,
   and the share of cells each can evaluate.
4. **The NaN rate in an actual inversion** on held-out X=2 and X=4, with true
   ``<Kd>_1`` and true ``eta``: the share of cells where κ is unavailable,
   old against new, overall and per wavelength.
5. **What κ buys**: a/bb accuracy on X=2 and X=4, with no correction, with
   the published κ, and with the refit κ, each on task 12's refit a/bb
   table, against the elastic ceiling (the refit on X=1).

Writes ``ocpy/data/LS2/LS2_LUT_L23_abk_v1.npz`` (task 12's a/bb refit plus
this κ: "our own LS2" for task 14) and ``docs/source/reports/ls2_refit_kappa/``.

Usage, from the repository root::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \\
        ioptics/runs/prototypes/ls2/refit_kappa.py [--docs-root DIR] [--no-save]
"""

from __future__ import annotations

import warnings
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd

SID = 'ls2_refit_kappa'
REPO = Path(__file__).resolve().parents[4]
DEFAULT_DOCS = REPO / 'docs' / 'source'
THETAS = (0, 30, 60)
WAVE_RANGE = (350.0, 750.0)
EVAL_RANGE = (400.0, 750.0)            # the LS2 sweeps' window
QUOTE = (440, 490, 500, 555, 670, 700)
OUT_NAME = 'LS2_LUT_L23_abk_v1.npz'
AB_NAME = 'LS2_LUT_L23_v1.npz'
#: Forms compared: x (bb/a or ln bb/a) and the mu_w basis of the coefficients.
FORMS = (('lin', 'none'), ('log', 'none'), ('lin', 'lin'), ('lin', 'inv'))
PLANNING_NAN_RATE = 0.191
ANW_SHARE = 0.10


def snell_muw(sza):
    return np.cos(np.arcsin(np.sin(np.deg2rad(np.asarray(sza, float))) / 1.34))


def pair_corpus():
    """Matched X=1/X=2 cells on 350-750 nm: true kappa and bb/a per row."""
    from ocpy.hydrolight import loisel23
    K, R, S, Z = [], [], [], []
    for Y in THETAS:
        d1, d2 = loisel23.load_ds(1, Y), loisel23.load_ds(2, Y)
        L = np.asarray(d1['Lambda'].values, float)
        sel = (L >= WAVE_RANGE[0]) & (L <= WAVE_RANGE[1])
        r1 = np.asarray(d1['Rrs'].values, float)[:, sel]
        r2 = np.asarray(d2['Rrs'].values, float)[:, sel]
        with np.errstate(divide='ignore', invalid='ignore'):
            K.append(r1 / r2)
        R.append((np.asarray(d1['bb'].values, float)
                  / np.asarray(d1['a'].values, float))[:, sel])
        n = r1.shape[0]
        S.append(np.arange(n))
        Z.append(np.full(n, float(Y)))
    return {'wave': L[sel], 'kappa': np.concatenate(K), 'ratio': np.concatenate(R),
            'scen': np.concatenate(S), 'sza': np.concatenate(Z)}


def _design(x, m, form, basis):
    xx = np.log(x) if form == 'log' else x
    P = np.stack([xx ** p for p in range(4)], 1)
    G = {'none': np.ones((len(m), 1)),
         'lin': np.stack([np.ones_like(m), m], 1),
         'inv': np.stack([np.ones_like(m), 1 / m], 1)}[basis]
    return (P[:, :, None] * G[:, None, :]).reshape(len(m), -1)


def _fitpred(P, j, trm, tem, form, basis):
    m = snell_muw(P['sza'])
    x, y = P['ratio'][:, j], P['kappa'][:, j]
    ok = trm & np.isfinite(x) & np.isfinite(y)
    b, *_ = np.linalg.lstsq(_design(x[ok], m[ok], form, basis), y[ok], rcond=None)
    return _design(x[tem], m[tem], form, basis) @ b


def form_selection(P, tr, te):
    """Mean |kappa_fit/kappa - 1| per form: held-out, interp-30, extrap-60."""
    rows = []
    for form, basis in FORMS:
        errs = {'test': [], 'interp_30': [], 'extrap_60': []}
        for j in range(P['wave'].size):
            for tag, trm, tem in (('test', tr, te),
                                  ('interp_30', tr & np.isin(P['sza'], (0, 60)),
                                   te & (P['sza'] == 30)),
                                  ('extrap_60', tr & np.isin(P['sza'], (0, 30)),
                                   te & (P['sza'] == 60))):
                pred = _fitpred(P, j, trm, tem, form, basis)
                errs[tag].append(np.nanmean(np.abs(pred / P['kappa'][tem, j] - 1)))
        rows.append({'x': 'bb/a' if form == 'lin' else 'ln(bb/a)',
                     'muw_basis': basis,
                     **{f'{k}_mae': round(float(np.mean(v)), 4) for k, v in errs.items()},
                     'extrap_60_worst_band': round(float(np.max(errs['extrap_60'])), 4)})
    return pd.DataFrame(rows)


def kappa_vs_truth(P, te, published, refit_k):
    """On held-out cells: kappa error and evaluable share, old vs new."""
    from ocpy.ls2 import refit
    out = []
    w = np.broadcast_to(P['wave'], P['ratio'][te].shape)
    for name, tab in (('published', published), ('refit', refit_k)):
        k, use = refit.kappa_eval(tab, w, P['ratio'][te])
        err = np.abs(k / P['kappa'][te] - 1)
        row = {'kappa_table': name,
               'share_evaluable_350_750': round(float(np.mean(use)), 4),
               'share_evaluable_400_750': round(float(np.mean(use[:, P['wave'] >= 400])), 4),
               'mae_where_evaluable': round(float(np.nanmean(np.where(use, err, np.nan))), 4)}
        for lam in QUOTE:
            j = int(np.argmin(np.abs(P['wave'] - lam)))
            row[f'evaluable_{lam}'] = round(float(np.mean(use[:, j])), 3)
        out.append(row)
    return pd.DataFrame(out)


# --------------------------------------------------------------------------- #
# inversions
# --------------------------------------------------------------------------- #

def inversion_set(X, test_ids):
    """Held-out L23 realization ``X`` on 400-750 nm, with true Kd, eta, IOPs."""
    from ocpy.hydrolight import loisel23

    from ioptics import kd
    parts = {k: [] for k in ('rrs', 'kd', 'a', 'bb', 'bp', 'sza')}
    for Y in THETAS:
        ds = loisel23.load_ds(X, Y)
        L = np.asarray(ds['Lambda'].values, float)
        sel = (L >= EVAL_RANGE[0]) & (L <= EVAL_RANGE[1])
        g = lambda v: np.asarray(ds[v].values, float)[test_ids][:, sel]   # noqa: E731
        _, k1 = kd.load_l23_kd1(X, Y)
        b, bnw = g('b'), g('bnw')
        parts['rrs'].append(g('Rrs'))
        parts['kd'].append(k1[test_ids][:, sel])
        parts['a'].append(g('a'))
        parts['bb'].append(g('bb'))
        parts['bp'].append(bnw)
        parts['sza'].append(np.full(len(test_ids), float(Y)))
        aw = (g('a') - g('anw'))[0]
        bw = (b - bnw)[0]
    D = {k: np.concatenate(v) for k, v in parts.items()}
    D.update(wave=L[sel], aw=aw, bw=bw)
    return D


def invert(D, lut, raman):
    from ocpy.ls2 import ls2_main
    return ls2_main.ls2_invert(D['rrs'], D['kd'], D['aw'], D['bw'], D['bp'],
                               D['sza'], D['wave'], lut, raman=raman)


def _lnr(x, t):
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.log(x / t)


def inversion_scores(sets, configs):
    """a, bb, a_nw, bb_p accuracy and the kappa-NaN rate, per set and config."""
    rows, nan_spec = [], {}
    for set_name, (D, lut_cfgs) in sets.items():
        truth = {'a': D['a'], 'bb': D['bb'], 'a_nw': D['a'] - D['aw'],
                 'bb_p': D['bb'] - D['bw'] / 2}
        share = truth['a_nw'] / truth['a'] >= ANW_SHARE
        for cfg in lut_cfgs:
            lut, raman = configs[cfg]
            res = invert(D, lut, raman)
            ret = {'a': res.a, 'bb': res.bb, 'a_nw': res.anw, 'bb_p': res.bbp}
            row = {'set': set_name, 'config': cfg,
                   'kappa_nan_rate': round(float(np.mean(res.kappa_out_of_range)), 4)
                   if raman else 0.0}
            for comp in ('a', 'bb', 'a_nw', 'bb_p'):
                lr = _lnr(ret[comp], truth[comp])
                if comp == 'a_nw':
                    lr = np.where(share, lr, np.nan)
                fin = lr[np.isfinite(lr)]
                row[f'{comp}_median_ratio'] = round(float(np.exp(np.median(fin))), 4)
                row[f'{comp}_mae'] = round(float(np.mean(np.abs(fin))), 4)
            rows.append(row)
            if raman:
                nan_spec[(set_name, cfg)] = np.mean(res.kappa_out_of_range, axis=0)
    return pd.DataFrame(rows), nan_spec


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #

def _plt():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    return plt


def fig_nan(nan_spec, wave, path):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    style = {('X=2', 'refit a/bb + published κ'): ('C3', '-'),
             ('X=2', 'refit a/bb + refit κ'): ('k', '-'),
             ('X=4', 'refit a/bb + published κ'): ('C3', ':'),
             ('X=4', 'refit a/bb + refit κ'): ('k', ':')}
    for key, (c, ls) in style.items():
        if key in nan_spec:
            ax.plot(wave, 100 * nan_spec[key], color=c, ls=ls,
                    label=f'{key[0]}: {key[1]}')
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel('cells with κ unavailable [%]')
    ax.set_ylim(-2, 102)
    ax.legend(fontsize=8)
    ax.set_title('Held-out L23, true ⟨Kd⟩₁ and η', fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_kappa(P, te, published, refit_k, path):
    from ocpy.ls2 import refit
    plt = _plt()
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    for ax, lam in zip(axes, (440, 500, 670)):
        j = int(np.argmin(np.abs(P['wave'] - lam)))
        x, y = P['ratio'][te, j], P['kappa'][te, j]
        for th, c in zip(THETAS, ('C0', 'C2', 'C1')):
            m = P['sza'][te] == th
            ax.plot(x[m], y[m], '.', ms=1.5, color=c, alpha=0.4, label=f'θs={th}°')
        xg = np.linspace(np.nanmin(x), np.nanmax(x), 300)
        for tab, col, lab in ((refit_k, 'k', 'refit'), (published, 'C3', 'published')):
            k, use = refit.kappa_eval(tab, np.full_like(xg, P['wave'][j]), xg)
            ax.plot(xg, np.where(use, k, np.nan), color=col, lw=1.6, label=lab)
        ax.set_title(f'{lam} nm', fontsize=10)
        ax.set_xlabel('bb/a')
    axes[0].set_ylabel('κ = Rrs(X=1) / Rrs(X=2)')
    axes[0].legend(fontsize=7, markerscale=5)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #

def _tbl(caption, name):
    return (f'.. csv-table:: {caption}\n   :file: {name}\n   :header-rows: 1\n'
            f'   :widths: auto\n')


def build(docs_root=None, save=True):
    import json

    from ocpy.ls2 import refit

    from ioptics import kd_net
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS
    out = docs_root / 'reports' / SID
    out.mkdir(parents=True, exist_ok=True)
    ddir = Path(str(resources.files('ocpy'))) / 'data' / 'LS2'
    published = dict(np.load(ddir / 'LS2_LUT.npz'))
    ab_lut, ab_model = refit.load(ddir / AB_NAME)

    P = pair_corpus()
    sp = kd_net.split_scenarios()
    tr, te = np.isin(P['scen'], sp['train']), np.isin(P['scen'], sp['test'])
    sel = form_selection(P, tr, te)
    kap = refit.fit_kappa(P['wave'], P['ratio'][tr], P['kappa'][tr])
    truth_tab = kappa_vs_truth(P, te, published['kappa'], kap)

    configs = {
        'published a/bb + published κ': (published, True),
        'refit a/bb without κ': (ab_lut, False),
        'refit a/bb + published κ': (ab_lut, True),
        'refit a/bb + refit κ': (refit.with_kappa(ab_lut, kap), True),
    }
    test_ids = sp['test']
    sets = {'X=1 (elastic ceiling)': (inversion_set(1, test_ids), ['refit a/bb without κ']),
            'X=2': (inversion_set(2, test_ids), list(configs)),
            'X=4': (inversion_set(4, test_ids), list(configs))}
    inv, nan_spec = inversion_scores(sets, configs)
    nan_spec = {(s.split(' ')[0], c): v for (s, c), v in nan_spec.items()}

    if save:
        full = refit.with_kappa(ab_lut, kap)
        ab_model.meta = {**ab_model.meta,
                         'kappa': 'refit from L23 X=1/X=2 (ioptics ls2 task 13, '
                                  'refit_kappa.py): cubic in bb/a per 5 nm row, '
                                  '350-750 nm, ranges from L23 training cells'}
        refit.save(ab_model, full, ddir / OUT_NAME)
    pd.DataFrame(kap, columns=['wavelength', 'c3', 'c2', 'c1', 'c0',
                               'bb_a_min', 'bb_a_max']).to_csv(
        out / 'kappa_table.csv', index=False, float_format='%.6g')
    tables = {'kappa_forms.csv': sel, 'kappa_vs_truth.csv': truth_tab,
              'kappa_inversions.csv': inv}
    for nm, df in tables.items():
        df.to_csv(out / nm, index=False)
    fig_nan(nan_spec, sets['X=2'][0]['wave'], out / 'kappa_nan.png')
    fig_kappa(P, te, published['kappa'], kap, out / 'kappa_fit.png')
    (out / f'{SID}.rst').write_text(_page(sel, truth_tab, inv, published['kappa']),
                                    encoding='utf-8')
    print(f'wrote {out / (SID + ".rst")}')
    return {'kappa': kap, **tables, 'nan_spec': nan_spec}


def _page(sel, truth_tab, inv, published):
    pc = lambda v: f'{100 * float(v):.1f}%'                  # noqa: E731
    sg = lambda v: f'{100 * (float(v) - 1):+.2f}%'           # noqa: E731
    S = sel.set_index(['x', 'muw_basis'])
    lin_none, log_none = S.loc[('bb/a', 'none')], S.loc[('ln(bb/a)', 'none')]
    lin_lin, lin_inv = S.loc[('bb/a', 'lin')], S.loc[('bb/a', 'inv')]
    T = truth_tab.set_index('kappa_table')
    I = inv.set_index(['set', 'config'])
    g = lambda s, c: I.loc[(s, c)]                           # noqa: E731
    ceil = g('X=1 (elastic ceiling)', 'refit a/bb without κ')
    x2n, x2p, x2r = (g('X=2', c) for c in ('refit a/bb without κ',
                                            'refit a/bb + published κ',
                                            'refit a/bb + refit κ'))
    x2pp = g('X=2', 'published a/bb + published κ')
    x4n, x4p, x4r = (g('X=4', c) for c in ('refit a/bb without κ',
                                            'refit a/bb + published κ',
                                            'refit a/bb + refit κ'))
    r502 = published[np.argmin(np.abs(published[:, 0] - 502))]
    return f"""\
.. _ls2_refit_kappa:

==============================================================
LS2's Raman correction κ, re-derived from the matched L23 pair
==============================================================

:Task: ls2 task 13 (Q12)
:Script: ``ioptics/runs/prototypes/ls2/refit_kappa.py`` (every number, table
   and figure on this page); fitting code ``ocpy.ls2.refit.fit_kappa``
:Table: ``ocpy/data/LS2/{OUT_NAME}`` — task 12's refit ``a``/``bb`` plus
   this κ, in the published ``LS2_LUT`` layout: "our own LS2" for task 14
:Truth: κ = Rrs(X=1) / Rrs(X=2), the same water bodies elastic and with Raman,
   θs = 0/30/60°, 350–750 nm; split by IOP scenario (task 11's split)

Summary
-------

* **The NaN rate.**  In an inversion of held-out X=2 with true ⟨Kd⟩₁ and η,
  κ is unavailable on {pc(x2p['kappa_nan_rate'])} of cells with the published
  table and on {pc(x2r['kappa_nan_rate'])} with the refit.  On X=4 the rates
  are {pc(x4p['kappa_nan_rate'])} and {pc(x4r['kappa_nan_rate'])}.  Planning
  measured {pc(PLANNING_NAN_RATE)} for the published table, on a different
  cell set.  The published table's three defects all show up: the 702 nm
  stop, ranges that do not cover L23, and a broken 502 nm row (range
  [{r502[5]:.4f}, {r502[6]:.4f}], coefficients up to {np.max(np.abs(r502[1:5])):.0f}).
* **κ itself.**  Against the true κ on held-out cells, the refit is off by
  {pc(T.loc['refit']['mae_where_evaluable'])} and evaluates on
  {pc(T.loc['refit']['share_evaluable_350_750'])} of cells (350–750 nm).  The
  published table is off by {pc(T.loc['published']['mae_where_evaluable'])}
  where it evaluates at all, which is on
  {pc(T.loc['published']['share_evaluable_350_750'])} of cells.
* **What κ buys** (held-out X=2, refit a/bb table, mean abs ln ratio):
  ``a`` {pc(x2n['a_mae'])} with no correction, {pc(x2p['a_mae'])} with the
  published κ and {pc(x2r['a_mae'])} with the refit; ``bb``
  {pc(x2n['bb_mae'])} → {pc(x2p['bb_mae'])} → {pc(x2r['bb_mae'])}; ``bb_p``
  {pc(x2n['bb_p_mae'])} → {pc(x2p['bb_p_mae'])} → {pc(x2r['bb_p_mae'])}.  The
  elastic ceiling (the same table on X=1, where no correction is needed) is
  {pc(ceil['a_mae'])}, {pc(ceil['bb_mae'])} and {pc(ceil['bb_p_mae'])}.
* **The form is the published one**: a cubic in ``bb/a`` per wavelength.  κ
  does depend on the sun, but not monotonically in μw on L23's three zeniths,
  so no μw term survives the leave-one-zenith-out check (below).  That
  dependence is the floor the refit cannot get under.

Choosing the form
-----------------

On held-out scenarios a μw term helps a little: {pc(lin_lin['test_mae'])}
against {pc(lin_none['test_mae'])} without.  But it fails the
leave-one-zenith-out check.  Trained on 0°/30° and asked for 60°, it is off by
{pc(lin_lin['extrap_60_mae'])} with ``(1, μw)`` and {pc(lin_inv['extrap_60_mae'])}
with ``(1, 1/μw)``, against {pc(lin_none['extrap_60_mae'])} with no μw term.
κ at θs = 0° differs from 30° and 60°, which agree with each other.  A
dependence that turns over between three samples cannot be fitted with a
low-order term in μw.  A cubic in ln(bb/a) is no better than one in bb/a
({pc(log_none['test_mae'])} against {pc(lin_none['test_mae'])}), so the
published form stands, and the table drops into ``ls2_invert`` unchanged.

{_tbl('κ forms: mean abs relative error of κ, averaged over 350–750 nm, on held-out scenarios and in the two leave-one-zenith-out checks.', 'kappa_forms.csv')}
.. figure:: kappa_fit.png
   :width: 100%

   True κ against ``bb/a`` on held-out cells, coloured by solar zenith, with
   the refit (black) and published (red) cubics drawn over each table's
   admissible range.  The spread between zeniths is the residual neither
   cubic can remove.

κ against truth
---------------

{_tbl('κ from each table, at the true bb/a of held-out cells: the share of cells it can evaluate (overall and per band), and its error where it does.', 'kappa_vs_truth.csv')}
The NaN rate in an inversion
----------------------------

.. figure:: kappa_nan.png
   :width: 90%

   Share of cells where κ is unavailable in ``ls2_invert``, per wavelength,
   on held-out X=2 (solid) and X=4 (dotted).  The published table's gaps are
   the 490–505 nm hole from its 502 nm row, everything above 702 nm, and
   cells whose ``bb/a`` falls outside its rows' ranges.

{_tbl('Inversions on held-out L23 with true ⟨Kd⟩₁ and η: the κ-unavailable share and the accuracy of a, bb, a_nw (where a_nw/a ≥ 0.1) and bb_p.', 'kappa_inversions.csv')}
On X=4, which adds chlorophyll fluorescence near 685 nm, the refit κ corrects
only the Raman part, by construction.  ``bb_p`` there goes from
{pc(x4n['bb_p_mae'])} uncorrected to {pc(x4r['bb_p_mae'])}, against
{pc(x2r['bb_p_mae'])} on X=2.  The gap is consistent with the fluorescence
this κ does not model; separating it from other X=4 effects is not attempted
here.  For reference, the published a/bb and κ together score
``a`` {pc(x2pp['a_mae'])}, ``bb`` {pc(x2pp['bb_mae'])} on X=2.

The table
---------

{_tbl('The refit κ table: one row per 5 nm, 350–750 nm, in the published column order (κ = c3 r³ + c2 r² + c1 r + c0, r = bb/a, valid on [bb_a_min, bb_a_max]).', 'kappa_table.csv')}
Limits
------

* κ's dependence on the sun is real but cannot be modelled from three
  zeniths; it remains as scatter around the cubic.
* The ranges are L23's, which is clear-water dominated.  Turbid ``bb/a``
  beyond them is NaN, by design.
* Chlorophyll fluorescence (X=4) is outside this κ.
"""


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--docs-root', default=None)
    p.add_argument('--no-save', action='store_true')
    a = p.parse_args()
    build(a.docs_root, save=not a.no_save)

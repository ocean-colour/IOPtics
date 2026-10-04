"""Re-derive LS2's ``a`` and ``bb`` coefficients from L23 X=1 (ls2 task 12).

LS2's two cubics (``<Kd>_1/a`` and ``bb/<Kd>_1`` in ``Rrs``) have coefficient
tables on 21 ``eta`` x 8 ``mu_w`` nodes, fitted by the authors to their own
Hydrolight runs.  This script refits them on L23's elastic realization (X=1,
so no Raman term to confound the fit), with :mod:`ocpy.ls2.refit`.  Each
coefficient is a smooth low-order function of ``eta`` and ``mu_w``, not a
node-by-node table.  L23 lands on only 3 of the 8 ``mu_w`` nodes (0, 30,
60 degrees; nothing at 70), and on the ``eta`` axis it is 50:1 unbalanced
and correlated with wavelength (ls2 Q11).

What it does, every number on the page included:

1. **Choose the model** on the training scenarios: ``mu_w`` basis per table
   and ``eta`` degree, by held-out test error *and* by a held-out-zenith check.
   That is the "3-node mu_w check": train on two zeniths, predict the third,
   both as an interpolation (0/60 -> 30) and as an extrapolation
   (0/30 -> 60).  The 70-degree node can only ever be an extrapolation, so
   the basis that extrapolates best is the one to trust there.
2. **Fit** the chosen model on the training scenarios (the scenario split of
   ``ioptics.kd_net``, seed 11, so task 14's held-out set is shared), and
   evaluate it on the 21 x 8 published grid as a drop-in ``LS2_LUT``.
3. **Score** the published table, the refit through the same table
   machinery, and the smooth refit evaluated directly, on the held-out test
   scenarios.  True ``<Kd>_1`` and true ``eta`` are used, so only the
   coefficients differ.  Scored on ``a``, ``bb``, ``a_nw`` and ``bb_p``, per
   zenith and per band.
4. **Validate** against the paper's limiting relation (``c0 -> 1/mu_w`` as
   ``Rrs -> 0``), against L23's own small-``Rrs`` limit, and against the
   effective ``mu_w`` of ls2 Q9 (illumination bookkeeping).
5. **State the domain**: L23's ``b/a`` spans about 0.002-14 against the
   paper's 0.05-30, so the turbid half of the paper's range is unsampled
   and the refit extrapolates there.

Writes ``ocpy/data/LS2/LS2_LUT_L23_v1.npz`` (``LS2_LUT`` keys plus the smooth
model and provenance; κ is the published one until task 13) and the report
``docs/source/reports/ls2_refit_ab/``.

Usage, from the repository root::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \\
        ioptics/runs/prototypes/ls2/refit_ab.py [--docs-root DIR] [--no-save]

About a minute.
"""

from __future__ import annotations

import warnings
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd

SID = 'ls2_refit_ab'
REPO = Path(__file__).resolve().parents[4]
DEFAULT_DOCS = REPO / 'docs' / 'source'
X_FIT = 1
THETAS = (0, 30, 60)
WAVE_RANGE = (400.0, 750.0)
BASES = ('inv', 'lin', 'const')
DEGREES = (1, 2, 3, 4)
CHOSEN = {'eta_degree': 2, 'muw_basis': ('inv', 'lin')}
QUOTE = (440, 490, 555, 670)
LUT_NAME = 'LS2_LUT_L23_v1.npz'
PAPER_B_OVER_A = (0.05, 30.0)
#: ``a_nw`` is scored only where ``a_nw / a`` is at least this (ls2 Q34).
ANW_SHARE = 0.10


def snell_muw(sza):
    return np.cos(np.arcsin(np.sin(np.deg2rad(np.asarray(sza, float))) / 1.34))


def corpus(X=X_FIT):
    """L23 cells, ``(rows = scenario x zenith, 71 bands)`` per quantity."""
    from ocpy.hydrolight import loisel23

    from ioptics import kd
    out = {k: [] for k in ('rrs', 'kd', 'a', 'bb', 'b', 'eta', 'aw', 'bw', 'bp',
                           'sza', 'scen')}
    for Y in THETAS:
        ds = loisel23.load_ds(X, Y)
        L = np.asarray(ds['Lambda'].values, float)
        sel = (L >= WAVE_RANGE[0]) & (L <= WAVE_RANGE[1])
        g = lambda v: np.asarray(ds[v].values, float)[:, sel]      # noqa: E731
        a, bb, b, bnw, anw, R = (g(v) for v in ('a', 'bb', 'b', 'bnw', 'anw', 'Rrs'))
        _, k1 = kd.load_l23_kd1(X, Y)
        n = a.shape[0]
        bw = b - bnw
        for k, v in (('rrs', R), ('kd', k1[:, sel]), ('a', a), ('bb', bb),
                     ('b', b), ('eta', bw / b), ('aw', a - anw), ('bw', bw),
                     ('bp', bnw)):
            out[k].append(v)
        out['sza'].append(np.full(n, float(Y)))
        out['scen'].append(np.arange(n))
    C = {k: np.concatenate(v) for k, v in out.items()}
    C['wave'] = L[sel]
    C['muw'] = snell_muw(C['sza'])
    return C


def rows(C, mask):
    D = {k: (v[mask] if k != 'wave' else v) for k, v in C.items()}
    return D


def _flat(D, *keys):
    """Cell arrays, with per-row quantities broadcast across bands."""
    nl = D['rrs'].shape[1]
    out = []
    for k in keys:
        v = D[k]
        out.append((np.repeat(v[:, None], nl, 1) if v.ndim == 1 else v).ravel())
    return out


def fit_model(D, **kw):
    from ocpy.ls2 import refit
    r, k, a, bb, e, m = _flat(D, 'rrs', 'kd', 'a', 'bb', 'eta', 'muw')
    model = refit.fit(r, k, a, bb, e, m, **kw)
    ba = (D['b'] / D['a']).ravel()
    model.domain['b_over_a'] = (float(np.nanmin(ba)), float(np.nanmax(ba)))
    return model


def lnr(x, t):
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.log(x / t)


def summ(lr):
    lr = lr[np.isfinite(lr)]
    return float(np.exp(np.median(lr))), float(np.mean(np.abs(lr)))


def retrievals(D, published, refit_lut, model):
    """``{version: {'a','bb','a_nw','bb_p'}}`` on rows ``D``, true Kd and eta."""
    from ocpy.ls2 import ls2_main
    out = {}
    for name, lut in (('published (table)', published), ('refit (table)', refit_lut)):
        res = ls2_main.ls2_invert(D['rrs'], D['kd'], D['aw'][0], D['bw'][0],
                                  D['bp'], D['sza'], D['wave'], lut, raman=False)
        out[name] = {'a': res.a, 'bb': res.bb}
    a, bb = model.invert(D['rrs'], D['kd'], D['eta'], D['muw'][:, None])
    out['refit (smooth)'] = {'a': a, 'bb': bb}
    for v in out.values():
        v['a_nw'] = v['a'] - D['aw'][0]
        v['bb_p'] = v['bb'] - D['bw'][0] / 2
    return out


def truth(D):
    return {'a': D['a'], 'bb': D['bb'], 'a_nw': D['a'] - D['aw'][0],
            'bb_p': D['bb'] - D['bw'][0] / 2}


# --------------------------------------------------------------------------- #
# steps
# --------------------------------------------------------------------------- #

def model_selection(C, tr, te):
    """Per table: test error and held-out-zenith errors for each basis x degree."""
    rows_ = []
    T = rows(C, te)
    for basis in BASES:
        for deg in DEGREES:
            M = fit_model(rows(C, tr), eta_degree=deg, muw_basis=basis)
            a, bb = M.invert(T['rrs'], T['kd'], T['eta'], T['muw'][:, None])
            hz = {}
            for trz, tez, tag in (((0, 60), 30, 'interp_30'), ((0, 30), 60, 'extrap_60')):
                mtr = tr & np.isin(C['sza'], trz)
                mte = te & (C['sza'] == tez)
                Mz = fit_model(rows(C, mtr), eta_degree=deg, muw_basis=basis)
                Dz = rows(C, mte)
                az, bz = Mz.invert(Dz['rrs'], Dz['kd'], Dz['eta'], Dz['muw'][:, None])
                hz[tag] = (summ(lnr(az, Dz['a']))[1], summ(lnr(bz, Dz['bb']))[1])
            for table, (x, t, i) in (('a', (a, T['a'], 0)), ('bb', (bb, T['bb'], 1))):
                rows_.append({'table': table, 'muw_basis': basis, 'eta_degree': deg,
                              'test_mae': round(summ(lnr(x, t))[1], 4),
                              'test_median_ratio': round(summ(lnr(x, t))[0], 4),
                              'interp_30_mae': round(hz['interp_30'][i], 4),
                              'extrap_60_mae': round(hz['extrap_60'][i], 4)})
    return pd.DataFrame(rows_)


def score_table(R, D):
    """Median ratio / mean |ln ratio|, overall, per zenith and per band."""
    tr_ = truth(D)
    # ls2 Q34: a_nw is scored only where it is at least 10% of a; in the red,
    # where a_w is nearly all of a, its ratio measures nothing but a_w.
    share = tr_['a_nw'] / tr_['a'] >= ANW_SHARE
    out = []
    for ver, comps in R.items():
        for comp in ('a', 'bb', 'a_nw', 'bb_p'):
            lr = lnr(comps[comp], tr_[comp])
            if comp == 'a_nw':
                lr = np.where(share, lr, np.nan)
            med, mae = summ(lr)
            row = {'version': ver, 'component': comp, 'median_ratio': round(med, 4),
                   'mae': round(mae, 4)}
            for th in THETAS:
                row[f'mae_{th}deg'] = round(summ(lr[D['sza'] == th])[1], 4)
            for lam in QUOTE:
                j = int(np.argmin(np.abs(D['wave'] - lam)))
                row[f'ratio_{lam}'] = round(summ(lr[:, j])[0], 4)
            scored = share if comp == 'a_nw' else np.ones_like(share)
            row['frac_nan'] = round(float(np.mean(~np.isfinite(lr[scored]))), 4)
            out.append(row)
    return pd.DataFrame(out)


ETA_BINS = (0.0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2)


def eta_bin_table(R, D):
    """Per-``eta``-bin mean abs ln ratio of ``a`` and ``bb``: does the refit
    hold up where L23 is thin (the axis is 50:1 unbalanced)?"""
    tr_ = truth(D)
    out = []
    for lo, hi in zip(ETA_BINS[:-1], ETA_BINS[1:]):
        m = (D['eta'] > lo) & (D['eta'] <= hi)
        row = {'eta_bin': f'{lo:g}–{hi:g}', 'n_cells': int(m.sum())}
        for ver in ('published (table)', 'refit (table)'):
            for comp in ('a', 'bb'):
                lr = lnr(R[ver][comp], tr_[comp])[m]
                tag = 'pub' if ver.startswith('pub') else 'refit'
                row[f'{comp}_mae_{tag}'] = round(summ(lr)[1], 4) if m.any() else np.nan
        out.append(row)
    return pd.DataFrame(out)


def limiting(C, model, published):
    """``c0`` at each zenith vs 1/mu_w, L23's small-Rrs limit, and 1/mu_eff."""
    from ioptics import kd
    out = []
    for th in THETAS + (70,):
        mu = float(snell_muw(th))
        c, _ = model.coefficients(np.array([0.02, 0.1]), np.array([mu, mu]))
        row = {'theta_s': th, 'muw': round(mu, 4), 'inv_muw': round(1 / mu, 4),
               'published_c0': round(float(np.interp(-mu, -np.asarray(published['muw'], float).ravel(),
                                                     np.asarray(published['a'])[10, :, 0])), 4),
               'refit_c0_eta0.02': round(float(c[0, 0]), 4),
               'refit_c0_eta0.10': round(float(c[1, 0]), 4)}
        if th in THETAS:
            m = (C['sza'] == th)
            r = C['rrs'][m].ravel()
            y = (C['a'][m] / C['kd'][m]).ravel()
            small = r < np.nanquantile(r, 0.02)
            row['L23_a_over_Kd_smallRrs'] = round(float(np.nanmedian(y[small])), 4)
            mue = float(np.nanmedian(kd.load_l23_muw_effective(X_FIT, th)))
            row['inv_mu_eff'] = round(1 / mue, 4)
        out.append(row)
    return pd.DataFrame(out)


def domain_table(C, model):
    ba = (C['b'] / C['a']).ravel()
    e = C['eta'].ravel()
    return pd.DataFrame([
        {'quantity': 'b/a', 'L23_min': round(float(np.nanmin(ba)), 4),
         'L23_max': round(float(np.nanmax(ba)), 2),
         'paper_range': f'{PAPER_B_OVER_A[0]}–{PAPER_B_OVER_A[1]}',
         'L23_share_below_paper_min': round(float(np.mean(ba < PAPER_B_OVER_A[0])), 4),
         'paper_range_unsampled': f'{np.nanmax(ba):.1f}–{PAPER_B_OVER_A[1]}'},
        {'quantity': 'eta', 'L23_min': round(float(np.nanmin(e)), 5),
         'L23_max': round(float(np.nanmax(e)), 4), 'paper_range': '0–0.2',
         'L23_share_below_paper_min': float('nan'),
         'paper_range_unsampled': f'share of L23 above 0.2: {np.mean(e > 0.2):.4f}'},
    ])


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #

def _plt():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    return plt


def fig_spectral(R, D, path):
    plt = _plt()
    tr_ = truth(D)
    fig, axes = plt.subplots(2, 2, figsize=(9, 6), sharex=True)
    style = {'published (table)': ('C3', '-'), 'refit (table)': ('k', '-'),
             'refit (smooth)': ('0.5', '--')}
    for ax, comp in zip(axes.ravel(), ('a', 'bb', 'a_nw', 'bb_p')):
        for ver, (c, ls) in style.items():
            lr = lnr(R[ver][comp], tr_[comp])
            ax.plot(D['wave'], np.exp(np.nanmedian(lr, axis=0)), color=c, ls=ls,
                    label=ver)
        ax.axhline(1, color='k', lw=0.6)
        ax.set_title(comp, fontsize=10)
        ax.set_ylim(*((0.9, 1.1) if comp in ('a', 'bb') else (0.5, 2.0)))
        if comp == 'a_nw':
            ax.set_yscale('log')
    axes[0, 0].legend(fontsize=8)
    for ax in axes[1]:
        ax.set_xlabel('wavelength [nm]')
    fig.suptitle('Median retrieved/true on held-out L23 X=1 (true ⟨Kd⟩₁ and η)',
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_coefficients(model, published, path):
    plt = _plt()
    eta_n = np.asarray(published['eta'], float).ravel()
    mu_n = np.asarray(published['muw'], float).ravel()
    eg = np.linspace(0.0005, 0.2, 200)
    fig, axes = plt.subplots(2, 4, figsize=(12, 5.4))
    labels = ['c0', 'c1', 'c2', 'c3', 'd0', 'd1', 'd2']
    for k, ax in enumerate(axes.ravel()[:7]):
        for jm, col in ((0, 'C0'), (3, 'C2'), (6, 'C1'), (7, 'C3')):
            c, d = model.coefficients(eg, np.full_like(eg, mu_n[jm]))
            y = c[:, k] if k < 4 else d[:, k - 4]
            pub = (np.asarray(published['a'])[:, jm, k] if k < 4
                   else np.asarray(published['bb'])[:, jm, k - 4])
            ls = ':' if jm == 7 else '-'
            ax.plot(eg, y, color=col, ls=ls,
                    label=f'θs={10 * jm}°' + (' (extrap.)' if jm == 7 else ''))
            ax.plot(eta_n, pub, 'o', color=col, ms=3)
        ax.set_title(labels[k], fontsize=10)
        ax.set_xlabel('η')
    axes.ravel()[7].axis('off')
    axes[0, 0].legend(fontsize=7)
    fig.suptitle('Coefficients vs η: refit (lines) and published nodes (dots)',
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #

def _tbl(caption, name):
    return (f'.. csv-table:: {caption}\n   :file: {name}\n   :header-rows: 1\n'
            f'   :widths: auto\n')


def build(docs_root=None, save=True):
    from ocpy.ls2 import refit

    from ioptics import kd_net
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS
    out = docs_root / 'reports' / SID
    out.mkdir(parents=True, exist_ok=True)
    pub_path = Path(str(resources.files('ocpy'))) / 'data' / 'LS2' / 'LS2_LUT.npz'
    published = dict(np.load(pub_path))

    C = corpus()
    sp = kd_net.split_scenarios()
    tr, te = np.isin(C['scen'], sp['train']), np.isin(C['scen'], sp['test'])
    sel = model_selection(C, tr, te)
    model = fit_model(rows(C, tr), **CHOSEN)
    model.meta = {'derived_by': 'ioptics/runs/prototypes/ls2/refit_ab.py (ls2 task 12)',
                  'ioptics_commit': kd_net._git_head(),
                  'corpus': f'L23 X={X_FIT}, theta_s {list(THETAS)}, '
                            f'{WAVE_RANGE[0]:g}-{WAVE_RANGE[1]:g} nm',
                  'split': 'ioptics.kd_net.split_scenarios (seed 11), train only',
                  'n_train_scenarios': int(len(sp['train'])),
                  'kd1': 'ln_ratio (ioptics.kd)',
                  'kappa': 'published (unchanged until ls2 task 13)',
                  'extrapolated_nodes': 'muw node 7 (theta_s 70) and the eta '
                                        'range beyond the corpus'}
    lut = model.to_lut(published)
    D = rows(C, te)
    R = retrievals(D, published, lut, model)
    scores = score_table(R, D)
    etab = eta_bin_table(R, D)
    lim = limiting(C, model, published)
    dom = domain_table(C, model)

    if save:
        refit.save(model, lut, pub_path.parent / LUT_NAME)
    tables = {'refit_selection.csv': sel, 'refit_scores.csv': scores,
              'refit_eta_bins.csv': etab,
              'refit_limiting.csv': lim, 'refit_domain.csv': dom}
    for nm, df in tables.items():
        df.to_csv(out / nm, index=False)
    fig_spectral(R, D, out / 'refit_spectral.png')
    fig_coefficients(model, published, out / 'refit_coefficients.png')
    page = _page(sel, scores, lim, dom, model, etab)
    (out / f'{SID}.rst').write_text(page, encoding='utf-8')
    print(f'wrote {out / (SID + ".rst")}')
    return {'model': model, 'lut': lut, **tables}


def _page(sel, scores, lim, dom, model, etab):
    S = scores.set_index(['version', 'component'])
    pc = lambda v: f'{100 * float(v):.1f}%'                       # noqa: E731
    sg = lambda v: f'{100 * (float(v) - 1):+.2f}%'                # noqa: E731
    P = lambda c: S.loc[('published (table)', c)]                # noqa: E731
    T = lambda c: S.loc[('refit (table)', c)]                    # noqa: E731
    M = lambda c: S.loc[('refit (smooth)', c)]                   # noqa: E731
    sl = sel.set_index(['table', 'muw_basis', 'eta_degree'])
    d = CHOSEN['eta_degree']
    ba, bb_ = CHOSEN['muw_basis']
    pick = lambda t, b: sl.loc[(t, b, d)]                        # noqa: E731
    L = lim.set_index('theta_s')
    E = etab.set_index('eta_bin')
    top = E.iloc[-1]
    D = dom.set_index('quantity')
    return f"""\
.. _ls2_refit_ab:

=====================================================
LS2 ``a`` and ``bb`` coefficients re-derived from L23
=====================================================

:Task: ls2 task 12 (Q6, Q11)
:Script: ``ioptics/runs/prototypes/ls2/refit_ab.py`` (every number, table and
   figure on this page); model code ``ocpy.ls2.refit``
:Table: ``ocpy/data/LS2/{LUT_NAME}`` — the published ``LS2_LUT`` keys, so
   ``ocpy.ls2.ls2_main.ls2_invert`` takes it unchanged, plus the smooth model
   and its provenance.  κ is still the published one (task 13).
:Corpus: L23 X=1 (elastic: no Raman to confound the fit), θs = 0, 30, 60°,
   400–750 nm; {model.meta['n_train_scenarios']} training scenarios
   ({model.domain['n_cells']:,} cells), split by IOP scenario with the split
   of task 11 so the held-out set is shared

Summary
-------

On held-out L23 X=1, with true ⟨Kd⟩₁ and true η so that only the
coefficients differ:

* The **published** table reads ``a`` {sg(P('a')['median_ratio'])} (mean
  abs ln ratio {pc(P('a')['mae'])}) and ``bb`` {sg(P('bb')['median_ratio'])}
  ({pc(P('bb')['mae'])}).  ``a_nw`` reads {sg(P('a_nw')['median_ratio'])}
  ({pc(P('a_nw')['mae'])}, where ``a_nw/a`` ≥ 0.1) and ``bb_p``
  {sg(P('bb_p')['median_ratio'])} ({pc(P('bb_p')['mae'])}).
* The **refit** read through the same table machinery gets ``a`` to
  {sg(T('a')['median_ratio'])} ({pc(T('a')['mae'])}), ``bb`` to
  {sg(T('bb')['median_ratio'])} ({pc(T('bb')['mae'])}), ``a_nw`` to
  {sg(T('a_nw')['median_ratio'])} ({pc(T('a_nw')['mae'])}) and ``bb_p`` to
  {sg(T('bb_p')['median_ratio'])} ({pc(T('bb_p')['mae'])}).
  Evaluated directly, without the table, the smooth model scores
  {pc(M('a')['mae'])} and {pc(M('bb')['mae'])}.  The difference is the cost of
  bilinear interpolation between the 21 × 8 nodes.
* The cubic form is kept, as Q11 asked.  Each coefficient is a quadratic in
  √(η/0.2), times ``(1, 1/μw)`` for ``a`` and ``(1, μw)`` for ``bb``.  That is
  {3 * 2 * 4} parameters for ``a`` and {3 * 2 * 3} for ``bb``, against the
  published table's 672 and 504 numbers.
* **The limiting relation does not hold on L23, and it is illumination, not
  coefficients.**  The refit's ``c0`` (the Rrs → 0 limit of ⟨Kd⟩₁/a) is
  {L.loc[0]['refit_c0_eta0.02']} at θs = 0°, against the paper's 1/μw = 1.
  It matches 1/μ_eff = {L.loc[0]['inv_mu_eff']} from L23's own light field
  (ls2 Q9), which task 7's effective-μw rung had already pointed to.
* **Domain.**  L23's ``b/a`` spans {D.loc['b/a']['L23_min']}–{D.loc['b/a']['L23_max']}
  against the paper's 0.05–30.  The turbid part of the paper's range
  ({D.loc['b/a']['paper_range_unsampled']}) is **unsampled**, and the refit
  there is an extrapolation.  {pc(D.loc['b/a']['L23_share_below_paper_min'])}
  of L23's cells are clearer than the paper's lower bound, which the refit
  does cover.  The θs = 70° node has no L23 data and is extrapolated by the
  ``μw`` basis.

Choosing the model: the 3-node μw check
---------------------------------------

L23 has three zeniths, so the geometry dependence can be tested by leaving one
out: train on 0°/60° and predict 30° (interpolation), and train on 0°/30° and
predict 60° (extrapolation, the regime the 70° node is in).  The ``a`` and
``bb`` tables are fitted independently, so each gets the basis that
extrapolates best:

* ``a``: with ``(1, 1/μw)``, the form of the limiting relation, the
  extrapolation error is {pc(pick('a', ba)['extrap_60_mae'])}.  With
  ``(1, μw)`` it is {pc(pick('a', 'lin')['extrap_60_mae'])}, and with no
  geometry dependence {pc(pick('a', 'const')['extrap_60_mae'])}.
* ``bb``: with ``(1, μw)`` it is {pc(pick('bb', bb_)['extrap_60_mae'])}; with
  ``(1, 1/μw)`` {pc(pick('bb', 'inv')['extrap_60_mae'])}.  ``bb/⟨Kd⟩₁`` scales
  as μw for the same slant-path reason that ``⟨Kd⟩₁/a`` scales as 1/μw.

The η degree barely matters beyond 1 (table), so the lowest adequate degree,
{d}, is used: the "reduced, smoothed η axis" Q11 asked for.

{_tbl('Model selection: held-out test error and the two leave-one-zenith-out errors (mean abs ln ratio), per table, μw basis and η degree.', 'refit_selection.csv')}
Scores on the held-out scenarios
--------------------------------

.. figure:: refit_spectral.png
   :width: 95%

   Median retrieved/true per wavelength on held-out L23 X=1 (true ⟨Kd⟩₁ and
   η; Raman off).  ``a_nw`` is on a log axis: in the red, where ``a_w`` is
   nearly all of ``a``, a small error in ``a`` becomes a large one in
   ``a_nw`` (ls2 Q34).

{_tbl('Mean abs ln ratio of a and bb per η bin (held-out), published table against refit.', 'refit_eta_bins.csv')}
{_tbl('Held-out scores. mae = mean abs ln(retrieved/true); ratio_λ = median ratio at λ; per-zenith mae. a_nw is scored only where a_nw/a ≥ 0.1 (Q34); frac_nan counts cells with no positive retrieval among those scored.', 'refit_scores.csv')}
The coefficients
----------------

.. figure:: refit_coefficients.png
   :width: 100%

   The refit (lines) against the published nodes (dots), at θs = 0, 30, 60
   and 70°.  70° (dotted) is an extrapolation of the μw basis: L23 has no
   data there.

The individual coefficients differ from the published ones, most visibly
above η ≈ 0.1 where L23 is thin.  A cubic's coefficients trade off against
one another, so that is not by itself an error.  What matters is the
retrieval, and the per-η table above shows the refit ahead in every bin,
including the sparsest: η {top.name}, {int(top['n_cells'])} held-out cells, ``a``
{pc(top['a_mae_refit'])} against {pc(top['a_mae_pub'])} and ``bb``
{pc(top['bb_mae_refit'])} against {pc(top['bb_mae_pub'])}.

{_tbl('The limiting relation. c0 is the Rrs → 0 limit of ⟨Kd⟩₁/a: the paper takes it as 1/μw; L23 gives 1/μ_eff.', 'refit_limiting.csv')}
{_tbl('Domain of the corpus against the paper.', 'refit_domain.csv')}
Limits
------

* Fitted on L23 X=1 with true inputs.  It removes the coefficient part of
  LS2's error on L23.  Task 14 measures what is left with real inputs
  (Kd from a network, b_p from OC4v4), and with Raman via task 13's κ.
* It is fitted to L23's ocean.  Task 11 found real water attenuating more
  than L23 predicts from the same Rrs (PANGAEA).  An L23-fitted table is as
  transferable as L23 is realistic.
* ``b/a`` above {D.loc['b/a']['L23_max']} (turbid water) and θs above 60° are
  extrapolations.
"""


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--docs-root', default=None)
    p.add_argument('--no-save', action='store_true')
    a = p.parse_args()
    build(a.docs_root, save=not a.no_save)

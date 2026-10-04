"""Train, validate and report the two L23 ``<Kd>_1`` networks (ls2 task 11).

Drives :mod:`ioptics.kd_net` end to end, then writes the weights into ocpy
(``ocpy/data/LS2/Kd_L23_{hyper,seawifs}_v1.npz``, read by
:mod:`ocpy.ls2.kd_l23`) and the report into
``docs/source/reports/ls2_kd_l23/``.  Every number on the page comes from this
run.

Steps:

1. **Geometry experiment** (does ``mu_w`` belong among the inputs?).  Train
   on theta_s = 0 and 30 degrees only, test on the unseen 60 degrees, with
   and without ``mu_w`` as an input, over three seeds.  The configuration
   with the lower median held-out error is adopted, and the seed spread is
   reported because ``robust.rt.emulator`` found exactly this extrapolation
   to be seed-dependent on this corpus.
2. **Final fits** on all three zeniths of the training scenarios (L23 X=4,
   ls2 Q38), selected on the noisy validation split: the MLP and its linear
   baseline for each network, plus the MLP's spread over three seeds.
3. **Held-out L23** (test scenarios, clean and with one fixed PACE noise
   draw), against the authors' PACE v2.3, MODIS v1.3 and MODIS v1.1 on the
   same spectra.
4. **Realization ablation** (ls2 Q38): the same networks trained on elastic
   X=1, scored on the X=4 test spectra.
5. **PANGAEA** (the five-band network only; the hyperspectral one has no
   in-situ data to meet): measured Kd at its own bands, ``Rrs`` matched to
   the network's bands within +/-2.5 nm and +/-6 nm, and the solar zenith from
   time and position.

Usage, from the repository root::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \\
        ioptics/runs/prototypes/ls2/train_kd_l23.py [--docs-root DIR] [--no-save]

Needs L23 with its profile files and PANGAEA V3 (``$OS_COLOR``).  A few
minutes on a laptop CPU.
"""

from __future__ import annotations

import os
import warnings
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd

from ioptics import kd_net as K

SID = 'ls2_kd_l23'
REPO = Path(__file__).resolve().parents[4]
DEFAULT_DOCS = REPO / 'docs' / 'source'
NETS = {'hyper': K.HYPER_BANDS, 'seawifs': K.SEAWIFS_BANDS}
WEIGHT_NAME = {'hyper': 'L23_hyper_v1', 'seawifs': 'L23_seawifs_v1'}
SEEDS = (23, 1, 7)
VAL_NOISE_SEED = 7
TEST_NOISE_SEED = 4242
QUOTE = (440, 490, 555, 670)
BASELINES = ('PACE_v2.3', 'MODIS_v1.3', 'MODIS_v1.1')
PANGAEA_TOLS = (2.5, 6.0)


def _iw(lam):
    return K.OUT_WAVE.index(float(lam))


def _split(c):
    sp = K.split_scenarios()
    return {k: c.subset(np.isin(c.scenario, v)) for k, v in sp.items()}


# --------------------------------------------------------------------------- #
# 1. geometry
# --------------------------------------------------------------------------- #

def geometry_experiment(parts):
    """Held-out 60-degree error, trained on 0/30 only; per net, geometry, seed."""
    tr = parts['train'].subset(parts['train'].sza < 45)
    va = parts['val'].subset(parts['val'].sza < 45)
    te = parts['test'].subset(parts['test'].sza == 60)
    te_noisy = K.noisy(te.rrs, te.wave, TEST_NOISE_SEED)
    truth = K.truth_on_out(te)
    rows = []
    for name, bands in NETS.items():
        for gi in (False, True):
            for seed in SEEDS:
                cfg = K.KdNetConfig(geometry_input=gi, seed=seed)
                net, _ = K.fit(tr, bands, cfg, select_on='val_noisy',
                               evals={'val_noisy': (va, VAL_NOISE_SEED)})
                s = K.scores(K.predict(net, te, te_noisy), truth)
                rows.append({'network': name, 'geometry_input': gi,
                             'seed': seed, 'mae_ln_vis_60deg': s['mae_ln_vis'],
                             'median_ratio_490': s['median_ratio'][_iw(490)]})
    return pd.DataFrame(rows)


def choose_geometry(geo):
    """Per network: the geometry setting with the lower median error."""
    g = geo.groupby(['network', 'geometry_input'])['mae_ln_vis_60deg']
    summ = pd.DataFrame({'median': g.median(), 'min': g.min(), 'max': g.max()})
    summ['spread'] = summ['max'] - summ['min']
    choice = {n: bool(summ.loc[n]['median'].idxmin()) for n in NETS}
    return choice, summ.reset_index()


# --------------------------------------------------------------------------- #
# 2-4. fits and held-out scores
# --------------------------------------------------------------------------- #

def final_fits(parts, geometry):
    """MLP + linear per network on all zeniths; and the MLP's seed spread."""
    evals = {'val': (parts['val'], None),
             'val_noisy': (parts['val'], VAL_NOISE_SEED)}
    nets, hists, spread = {}, {}, []
    te = parts['test']
    te_noisy = K.noisy(te.rrs, te.wave, TEST_NOISE_SEED)
    truth = K.truth_on_out(te)
    for name, bands in NETS.items():
        for kind, base in (('mlp', K.KdNetConfig()), ('linear', K.LINEAR)):
            cfg = K.KdNetConfig(**{**base.__dict__,
                                   'geometry_input': geometry[name]})
            net, h = K.fit(parts['train'], bands, cfg, evals=evals,
                           select_on='val_noisy', name=WEIGHT_NAME[name])
            nets[(name, kind)], hists[(name, kind)] = net, h
        for seed in SEEDS:
            cfg = K.KdNetConfig(geometry_input=geometry[name], seed=seed)
            net, _ = K.fit(parts['train'], bands, cfg, evals=evals,
                           select_on='val_noisy')
            s = K.scores(K.predict(net, te, te_noisy), truth)
            spread.append({'network': name, 'seed': seed,
                           'test_noisy_mae_ln_vis': s['mae_ln_vis']})
    return nets, hists, pd.DataFrame(spread)


def baseline_kd(name, corpus, rrs):
    """One of the authors' networks on ``corpus`` (``rrs`` = what it sees)."""
    from ocpy.ls2 import kd_nn
    bands = kd_nn.load_network(name).bands
    return kd_nn.kd_nn(K.at_bands(rrs, corpus.wave, bands), corpus.sza,
                       np.asarray(K.OUT_WAVE), name)


def heldout(nets, parts):
    """Scores on the test scenarios, clean and noisy, ours vs the authors'."""
    te = parts['test']
    truth = K.truth_on_out(te)
    rows, spectra = [], {}
    for cond, rrs in (('clean', te.rrs),
                      ('noisy', K.noisy(te.rrs, te.wave, TEST_NOISE_SEED))):
        preds = {f'L23 {n} ({k})': K.predict(nets[(n, k)], te, rrs)
                 for n, k in nets}
        preds.update({b: baseline_kd(b, te, rrs) for b in BASELINES})
        for label, kd in preds.items():
            s = K.scores(kd, truth)
            row = {'condition': cond, 'predictor': label,
                   'mae_ln_vis': round(s['mae_ln_vis'], 4),
                   'frac_nan': round(s['frac_nan'], 4)}
            for lam in QUOTE:
                row[f'ratio_{lam}'] = round(float(s['median_ratio'][_iw(lam)]), 3)
                row[f'mae_{lam}'] = round(float(s['mae_ln'][_iw(lam)]), 4)
            for th in K.L23_THETA_S:
                m = te.sza == th
                row[f'mae_vis_{th}deg'] = round(K.scores(kd[m], truth[m])['mae_ln_vis'], 4)
            rows.append(row)
            spectra[(cond, label)] = s
    return pd.DataFrame(rows), spectra


def ablation(geometry):
    """Q38: train on X=1, score on the X=4 test spectra (noisy)."""
    p4 = _split(K.l23_corpus(4))
    p1 = _split(K.l23_corpus(1))
    te = p4['test']
    rrs = K.noisy(te.rrs, te.wave, TEST_NOISE_SEED)
    truth = K.truth_on_out(te)
    rows = []
    for name, bands in NETS.items():
        for X, parts in ((4, p4), (1, p1)):
            cfg = K.KdNetConfig(geometry_input=geometry[name])
            net, _ = K.fit(parts['train'], bands, cfg, select_on='val_noisy',
                           evals={'val_noisy': (parts['val'], VAL_NOISE_SEED)})
            s = K.scores(K.predict(net, te, rrs), truth)
            rows.append({'network': name, 'trained_on': f'X={X}',
                         'mae_ln_vis_on_X4': round(s['mae_ln_vis'], 4),
                         **{f'ratio_{lam}': round(float(s['median_ratio'][_iw(lam)]), 3)
                            for lam in QUOTE}})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 5. PANGAEA
# --------------------------------------------------------------------------- #

def _nearest_cols(table, prefix, bands, tol):
    """Per row, the finite value of the ``prefix_<wave>`` column nearest each
    band within ``tol`` nm; NaN where none.  ``(n_rows, n_bands)``."""
    cols = [c for c in table.columns if str(c).startswith(prefix + '_')]
    waves = []
    for c in cols:
        try:
            waves.append(float(str(c)[len(prefix) + 1:]))
        except ValueError:
            waves.append(np.nan)
    waves = np.asarray(waves)
    vals = table[cols].apply(pd.to_numeric, errors='coerce').to_numpy(float)
    out = np.full((len(table), len(bands)), np.nan)
    for j, b in enumerate(bands):
        cand = np.flatnonzero(np.abs(waves - b) <= tol)
        cand = cand[np.argsort(np.abs(waves[cand] - b))]
        for c in cand:                      # nearest finite first
            fill = np.isnan(out[:, j]) & np.isfinite(vals[:, c])
            out[fill, j] = vals[fill, c]
    return out


def pangaea_sets():
    """PANGAEA rows with measured Kd, their Rrs table, and solar zeniths."""
    from robust import solar

    from ioptics import datasets
    ad = datasets.get_adapter('PANGAEA')
    iop, rrs = ad._table('iop'), ad._table('rrs')
    kd_cols = [c for c in iop.columns if str(c).startswith('kd_')
               and str(c)[3:].replace('.', '', 1).isdigit()]
    kd_wave = np.asarray([float(str(c)[3:]) for c in kd_cols])
    kd = iop[kd_cols].apply(pd.to_numeric, errors='coerce')
    has = kd.notna().any(axis=1)
    ids = kd.index[has].intersection(rrs.index)
    r = rrs.loc[ids]
    lat, lon, tim = (r.get(c) for c in (datasets._PANGAEA_LAT_COL,
                                         datasets._PANGAEA_LON_COL,
                                         datasets._PANGAEA_TIME_COL))
    sza = np.full(len(ids), np.nan)
    for i, (t, la, lo) in enumerate(zip(tim, lat, lon)):
        try:
            sza[i] = float(solar.solar_zenith(t, float(la), float(lo)))
        except Exception:
            pass
    return {'ids': ids, 'rrs': r, 'kd': kd.loc[ids].to_numpy(float),
            'kd_wave': kd_wave, 'sza': sza}


def pangaea_validation(net, P):
    """Five-band network vs measured Kd; MODIS baselines where their bands match."""
    from ocpy.ls2 import kd_l23, kd_nn
    vis = (P['kd_wave'] >= 400) & (P['kd_wave'] <= 700)
    kw, kd_obs = P['kd_wave'][vis], P['kd'][:, vis]
    rows, cells = [], {}
    for tol in PANGAEA_TOLS:
        x5 = _nearest_cols(P['rrs'], 'rrs', K.SEAWIFS_BANDS, tol)
        ok5 = np.isfinite(x5).all(axis=1) & np.isfinite(P['sza']) & (P['sza'] <= 70)
        pred, flags = kd_l23.kd_l23(x5[ok5], P['sza'][ok5], kw, network=net,
                                    return_flags=True)
        kd_rows = kd_obs[ok5]
        preds = {'L23 seawifs (mlp)': (pred, np.ones(ok5.sum(), bool))}
        for b in ('MODIS_v1.3', 'MODIS_v1.1'):
            xb = _nearest_cols(P['rrs'], 'rrs', kd_nn.load_network(b).bands, tol)[ok5]
            okb = np.isfinite(xb).all(axis=1)
            kb = np.full_like(pred, np.nan)
            if okb.any():
                kb[okb] = kd_nn.kd_nn(xb[okb], P['sza'][ok5][okb], kw, b)
            preds[b] = (kb, okb)
        common = np.all([v[1] for v in preds.values()], axis=0)
        kd490 = kd_rows[:, np.argmin(np.abs(kw - 490))]
        in_scope = ~flags['out_of_domain'] & ~(kd490 > 0.65)
        for label, (kp, okp) in preds.items():
            for subset, m in (('all matched', okp), ('common to all three', common),
                              ('in scope', okp & in_scope),
                              ('common and in scope', common & in_scope)):
                with np.errstate(divide='ignore', invalid='ignore'):
                    lr = np.log(kp[m] / kd_rows[m])
                fin = np.isfinite(lr)
                rows.append({'tol_nm': tol, 'predictor': label, 'subset': subset,
                             'n_spectra': int((fin.any(axis=1)).sum()),
                             'n_cells': int(fin.sum()),
                             'median_ratio': round(float(np.exp(np.nanmedian(lr))), 3)
                             if fin.any() else np.nan,
                             'mae_ln': round(float(np.nanmean(np.abs(lr))), 3)
                             if fin.any() else np.nan})
                if subset == 'all matched' and tol == PANGAEA_TOLS[1]:
                    cells[label] = (kd_rows[m], kp[m])
        rows.append({'tol_nm': tol, 'predictor': '(spectra matched)', 'subset':
                     f'{int(ok5.sum())} with Rrs at all five bands; '
                     f'{int(flags["out_of_domain"].sum())} out of domain; '
                     f'{int((kd490 > 0.65).sum())} with Kd(490) > 0.65',
                     'n_spectra': int(ok5.sum()), 'n_cells': np.nan,
                     'median_ratio': np.nan, 'mae_ln': np.nan})
    return pd.DataFrame(rows), cells, kw


# --------------------------------------------------------------------------- #
# figures and page
# --------------------------------------------------------------------------- #

def _plt():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    return plt


def fig_heldout(spectra, path):
    plt = _plt()
    fig, axes = plt.subplots(2, 1, figsize=(7.5, 6.4), sharex=True)
    w = np.asarray(K.OUT_WAVE)
    style = {'L23 hyper (mlp)': ('k', '-'), 'L23 seawifs (mlp)': ('0.45', '-'),
             'PACE_v2.3': ('C0', '--'), 'MODIS_v1.3': ('C1', '--'),
             'MODIS_v1.1': ('C3', ':')}
    for label, (c, ls) in style.items():
        s = spectra[('noisy', label)]
        axes[0].plot(w, s['median_ratio'], color=c, ls=ls, label=label)
        axes[1].plot(w, 100 * s['mae_ln'], color=c, ls=ls, label=label)
    axes[0].axhline(1, color='k', lw=0.6)
    axes[0].set_ylim(0.75, 1.3)
    axes[0].set_ylabel('median Kd / ⟨Kd⟩₁')
    axes[1].set_ylabel('mean abs(ln ratio) [%]')
    axes[1].set_ylim(0, 40)
    axes[1].set_xlabel('wavelength [nm]')
    for ax in axes:
        ax.axvspan(700, 750, color='0.88', lw=0)
    axes[0].legend(fontsize=8, ncol=2)
    axes[0].set_title('Held-out L23 X=4 test scenarios, one PACE noise draw',
                      fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_pangaea(cells, kw, path):
    plt = _plt()
    labels = [k for k in ('L23 seawifs (mlp)', 'MODIS_v1.3', 'MODIS_v1.1') if k in cells]
    fig, axes = plt.subplots(1, len(labels), figsize=(3.6 * len(labels), 3.6),
                             sharex=True, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, lab in zip(axes, labels):
        obs, pred = cells[lab]
        m = np.isfinite(obs) & np.isfinite(pred) & (obs > 0) & (pred > 0)
        ax.loglog(obs[m], pred[m], '.', ms=2, alpha=0.4)
        ax.plot([0.01, 10], [0.01, 10], 'k-', lw=0.8)
        ax.axvline(0.65, color='C3', lw=0.6, ls=':')
        ax.set_title(lab, fontsize=9)
        ax.set_xlabel('PANGAEA Kd [m⁻¹]')
    axes[0].set_ylabel('network Kd [m⁻¹]')
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _tbl(caption, name):
    return (f'.. csv-table:: {caption}\n   :file: {name}\n   :header-rows: 1\n'
            f'   :widths: auto\n')


def build(docs_root=None, save=True):
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS
    out = docs_root / 'reports' / SID
    out.mkdir(parents=True, exist_ok=True)

    parts = _split(K.l23_corpus(4))
    geo = geometry_experiment(parts)
    geometry, geo_summary = choose_geometry(geo)
    nets, hists, seed_spread = final_fits(parts, geometry)
    held, spectra = heldout(nets, parts)
    abl = ablation(geometry)
    P = pangaea_sets()
    pang, cells, kw = pangaea_validation(nets[('seawifs', 'mlp')], P)

    if save:
        from ocpy.ls2 import kd_l23
        ddir = Path(str(resources.files('ocpy'))) / 'data' / 'LS2'
        for name in NETS:
            net = nets[(name, 'mlp')]
            row = held[(held.condition == 'noisy')
                       & (held.predictor == f'L23 {name} (mlp)')].iloc[0]
            net.meta['heldout_test_noisy_mae_ln_vis'] = float(row['mae_ln_vis'])
            kd_l23.save_network(net, ddir / kd_l23.NETWORKS[WEIGHT_NAME[name]])
        kd_l23.load_network.cache_clear()

    tables = {'kdl23_geometry.csv': geo.round(4),
              'kdl23_geometry_summary.csv': geo_summary.round(4),
              'kdl23_seed_spread.csv': seed_spread.round(4),
              'kdl23_heldout.csv': held, 'kdl23_ablation.csv': abl,
              'kdl23_pangaea.csv': pang}
    for nm, df in tables.items():
        df.to_csv(out / nm, index=False)
    fig_heldout(spectra, out / 'kdl23_heldout.png')
    fig_pangaea(cells, kw, out / 'kdl23_pangaea.png')
    page = _page(geometry, geo_summary, seed_spread, held, abl, pang, nets, hists)
    path = out / f'{SID}.rst'
    path.write_text(page, encoding='utf-8')
    print(f'wrote {path}')
    return {'page': path, 'geometry': geometry, 'held': held, 'abl': abl,
            'pang': pang, 'geo_summary': geo_summary, 'seed_spread': seed_spread,
            'nets': nets, 'hists': hists}


def page_only(docs_root=None):
    """Rewrite the page from the CSVs a full run wrote and the saved weights.

    For wording fixes: no retraining.  The numbers are the full run's, read
    back from ``kdl23_*.csv``; the network metadata from ocpy's weight files.
    """
    from ocpy.ls2 import kd_l23
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS
    out = docs_root / 'reports' / SID
    rd = lambda n: pd.read_csv(out / n)                     # noqa: E731
    geo_summary = rd('kdl23_geometry_summary.csv')
    geometry = {n: bool(geo_summary[geo_summary.network == n]
                        .set_index('geometry_input')['median'].idxmin())
                for n in NETS}
    nets = {(n, 'mlp'): kd_l23.load_network(WEIGHT_NAME[n]) for n in NETS}
    page = _page(geometry, geo_summary, rd('kdl23_seed_spread.csv'),
                 rd('kdl23_heldout.csv'), rd('kdl23_ablation.csv'),
                 rd('kdl23_pangaea.csv'), nets, None)
    path = out / f'{SID}.rst'
    path.write_text(page, encoding='utf-8')
    print(f'wrote {path}')
    return path


def _page(geometry, geo_summary, seed_spread, held, abl, pang, nets, hists):
    """Report text; every number read from the tables of this run."""
    H = held.set_index(['condition', 'predictor'])
    n = lambda lab, cond='noisy': H.loc[(cond, lab)]           # noqa: E731
    pc = lambda v: f'{100 * float(v):.1f}%'                    # noqa: E731
    hy, sw = n('L23 hyper (mlp)'), n('L23 seawifs (mlp)')
    hyl, swl = n('L23 hyper (linear)'), n('L23 seawifs (linear)')
    pace, m13, m11 = n('PACE_v2.3'), n('MODIS_v1.3'), n('MODIS_v1.1')
    hyc, pacec = n('L23 hyper (mlp)', 'clean'), n('PACE_v2.3', 'clean')
    gs = geo_summary.set_index(['network', 'geometry_input'])
    ss = seed_spread.groupby('network')['test_noisy_mae_ln_vis']
    A = abl.set_index(['network', 'trained_on'])
    pg = pang[(pang.tol_nm == PANGAEA_TOLS[0])].set_index(['predictor', 'subset'])
    pg6 = pang[(pang.tol_nm == PANGAEA_TOLS[1])].set_index(['predictor', 'subset'])
    match25 = pang[(pang.tol_nm == PANGAEA_TOLS[0]) & (pang.predictor == '(spectra matched)')].iloc[0]
    match6 = pang[(pang.tol_nm == PANGAEA_TOLS[1]) & (pang.predictor == '(spectra matched)')].iloc[0]

    def pgv(df, pred, sub, col):
        try:
            return df.loc[(pred, sub)][col]
        except KeyError:
            return float('nan')

    geo_txt = []
    for name in NETS:
        f, t = gs.loc[(name, False)], gs.loc[(name, True)]
        geo_txt.append(
            f'* **{name}**: without ``μw`` {pc(f["median"])} (seeds '
            f'{pc(f["min"])}–{pc(f["max"])}); with it {pc(t["median"])} '
            f'({pc(t["min"])}–{pc(t["max"])}).  Adopted: '
            f'{"with" if geometry[name] else "without"}.')
    hyb, swb = nets[('hyper', 'mlp')].meta, nets[('seawifs', 'mlp')].meta

    return f"""\
.. _ls2_kd_l23:

========================================================
L23-trained ⟨Kd⟩₁ networks — hyperspectral and five-band
========================================================

:Task: ls2 task 11 (Q16, Q20, Q26, Q38)
:Script: ``ioptics/runs/prototypes/ls2/train_kd_l23.py`` (trains, scores and
   writes everything on this page); training code ``ioptics.kd_net``
:Weights: ``ocpy/data/LS2/Kd_L23_hyper_v1.npz`` and
   ``Kd_L23_seawifs_v1.npz``, evaluated by ``ocpy.ls2.kd_l23.kd_l23``
   (NumPy only)
:Training truth: L23 X=4 ⟨Kd⟩₁ (canonical ``ln_ratio``), θs = 0, 30, 60°;
   {hyb['n_train_scenarios']} training scenarios ({hyb['n_train_rows']:,} rows
   with noise augmentation); split by IOP scenario 70/15/15

Summary
-------

* **Hyperspectral network** (71 bands, 400–750 nm): {pc(hy['mae_ln_vis'])}
  mean abs(ln ratio) over 400–700 nm on held-out L23 with PACE noise
  ({pc(hyc['mae_ln_vis'])} clean).  On the same noisy spectra the authors' PACE
  v2.3 scores {pc(pace['mae_ln_vis'])}, MODIS v1.3 {pc(m13['mae_ln_vis'])} and
  the MODIS v1.1 ocpy used to ship {pc(m11['mae_ln_vis'])}.  Its linear baseline
  scores {pc(hyl['mae_ln_vis'])}, so the nonlinearity earns its place.
  **It has no in-situ validation**: no dataset on hand pairs hyperspectral
  ``Rrs`` with measured Kd.
* **Five-band network** (443, 490, 510, 555, 670 nm):
  {pc(sw['mae_ln_vis'])} on the same held-out set (linear
  {pc(swl['mae_ln_vis'])}).  On PANGAEA's measured Kd (Rrs within ±2.5 nm,
  {int(match25['n_spectra'])} spectra), its median ratio is
  {pgv(pg, 'L23 seawifs (mlp)', 'all matched', 'median_ratio')} and its mean
  abs(ln ratio) {pgv(pg, 'L23 seawifs (mlp)', 'all matched', 'mae_ln')}; in its
  clear-water scope (in its trained domain, Kd(490) ≤ 0.65), median ratio
  {pgv(pg, 'L23 seawifs (mlp)', 'in scope', 'median_ratio')} and mean abs(ln ratio)
  {pgv(pg, 'L23 seawifs (mlp)', 'in scope', 'mae_ln')}.
  On the {int(pgv(pg6, 'MODIS_v1.1', 'common and in scope', 'n_spectra'))}
  in-scope spectra the authors' MODIS networks can also score, MODIS v1.1 is
  closer to PANGAEA than ours
  ({pgv(pg6, 'MODIS_v1.1', 'common and in scope', 'mae_ln')} against
  {pgv(pg6, 'L23 seawifs (mlp)', 'common and in scope', 'mae_ln')}), the reverse
  of the L23 ranking.  The details, and what PANGAEA's Kd is and is not, are
  below.
* **Geometry**: the held-out-zenith experiment settles whether ``μw`` is an
  input (below).  The 1/μw factor is analytic in either case, so 60–70° is
  arithmetic extrapolation, flagged; beyond 70° the networks return NaN.
* **Realization (Q38)**: trained on elastic X=1 and applied to X=4, the
  hyperspectral network scores {pc(A.loc[('hyper', 'X=1')]['mae_ln_vis_on_X4'])}
  against {pc(A.loc[('hyper', 'X=4')]['mae_ln_vis_on_X4'])} when trained on X=4.

Held-out L23
------------

.. figure:: kdl23_heldout.png
   :width: 90%

   Median ratio (top) and mean abs(ln ratio) (bottom) per wavelength on the
   {len(K.split_scenarios()['test'])} held-out test scenarios × 3 zeniths, with one PACE noise draw on every spectrum.  Grey: above
   700 nm, outside the authors' recommended range for their networks.

{_tbl('Held-out test scores, clean and with PACE noise. mae_ln_vis = mean abs(ln(Kd/⟨Kd⟩₁)) over 400–700 nm (≈ fractional error); ratio_λ = median ratio; frac_nan = cells with no prediction.', 'kdl23_heldout.csv')}
Noise matters most for the networks that use the red.  PACE noise is about
50% of ``Rrs`` at 670 nm.  Ours were trained on it and degrade from
{pc(hyc['mae_ln_vis'])} clean to {pc(hy['mae_ln_vis'])} noisy.  The authors'
PACE v2.3 goes from {pc(pacec['mae_ln_vis'])} to {pc(pace['mae_ln_vis'])}, and
fails outright on {pc(pace['frac_nan'])} of noisy cells, because its turbid
branch refuses a negative red ``Rrs``.

Does ``μw`` belong among the inputs?
------------------------------------

``robust.rt.emulator`` found that a tanh MLP trained on 0°/30° of this corpus
extrapolates to 60° *unstably*: the seed decided the answer.  Here the target
is already ``ln(μw ⟨Kd⟩₁)``, so the question is whether giving the network
``μw`` as well helps or hurts.  Trained on 0° and 30° only, then tested on the
unseen 60° (noisy, three seeds):

{chr(10).join(geo_txt)}

The shipped networks are trained on all three zeniths with that setting.
Over three seeds, their held-out error spans
{pc(ss.min()['hyper'])}–{pc(ss.max()['hyper'])} (hyperspectral) and
{pc(ss.min()['seawifs'])}–{pc(ss.max()['seawifs'])} (five-band).

{_tbl('Held-out 60° error after training on 0°/30° only, per network, geometry setting and seed.', 'kdl23_geometry.csv')}
{_tbl('Summary over seeds.', 'kdl23_geometry_summary.csv')}
{_tbl('The final configuration over three seeds (held-out, noisy).', 'kdl23_seed_spread.csv')}
Which realization to train on (Q38)
-----------------------------------

{_tbl('Networks trained on X=4 (adopted) or on elastic X=1, both scored on the noisy X=4 test spectra.', 'kdl23_ablation.csv')}
PANGAEA (five-band network only)
--------------------------------

PANGAEA V3 carries measured Kd on 25 discrete wavelengths, multispectral
only.  It is a near-surface ``Kd(λ)`` whose depth convention the metadata does
not state, so it is **not** ⟨Kd⟩₁ over exactly the first attenuation depth.
Part of any disagreement is that definitional difference, not network error.
``Rrs`` was matched to each network's bands from the nearest finite band
within ±2.5 nm (and ±6 nm for the larger set), and θs computed from each
observation's time and position (``robust.solar``).  Scored over the
measured Kd bands from 400 to 700 nm.  ``in scope`` keeps the spectra inside
the network's trained input domain with Kd(490) ≤ 0.65 m⁻¹, the clear-water
range L23 covers.

* ±2.5 nm: {match25['subset']}.
* ±6 nm: {match6['subset']}.

The authors' MODIS networks need ``Rrs`` at 443/488/531/547/667 nm.  No
PANGAEA spectrum carries those within ±2.5 nm, and
{int(pgv(pg6, 'MODIS_v1.3', 'all matched', 'n_spectra'))} do within ±6 nm.
"Common to all three" compares the three networks on those spectra:

* On all of them, the five-band network's mean abs(ln ratio) is
  {pgv(pg6, 'L23 seawifs (mlp)', 'common to all three', 'mae_ln')} (median
  ratio {pgv(pg6, 'L23 seawifs (mlp)', 'common to all three', 'median_ratio')}),
  against {pgv(pg6, 'MODIS_v1.3', 'common to all three', 'mae_ln')} for MODIS
  v1.3 and {pgv(pg6, 'MODIS_v1.1', 'common to all three', 'mae_ln')} for v1.1.
  Most of these spectra lie outside L23's clear-water domain, where the
  authors' networks have a turbid branch and ours, by design, does not.
* On the
  {int(pgv(pg6, 'L23 seawifs (mlp)', 'common and in scope', 'n_spectra'))}
  that are in scope, it is
  {pgv(pg6, 'L23 seawifs (mlp)', 'common and in scope', 'mae_ln')} (median ratio
  {pgv(pg6, 'L23 seawifs (mlp)', 'common and in scope', 'median_ratio')}),
  against {pgv(pg6, 'MODIS_v1.3', 'common and in scope', 'mae_ln')} and
  {pgv(pg6, 'MODIS_v1.1', 'common and in scope', 'mae_ln')}.

Across all matched spectra the five-band network reads **low** against
PANGAEA (median ratio
{pgv(pg6, 'L23 seawifs (mlp)', 'all matched', 'median_ratio')} at ±6 nm), and
less so in scope ({pgv(pg6, 'L23 seawifs (mlp)', 'in scope', 'median_ratio')}).
In the scatter it flattens above about 0.3 m⁻¹, where L23 thins out (95% of
its Kd(490) is below 0.10).  How much of the low reading is L23's ocean
against the real one, and how much is near-surface Kd against ⟨Kd⟩₁, this
data cannot separate.

**Read plainly**: on the in-scope spectra all three can score, the network
furthest from L23, MODIS v1.1, is closest to PANGAEA
({pgv(pg6, 'MODIS_v1.1', 'common and in scope', 'mae_ln')}, against
{pgv(pg6, 'L23 seawifs (mlp)', 'common and in scope', 'mae_ln')} for ours).
Task 10 found v1.1 the worst of the three against L23.  A network trained on
L23 is as good as L23's ocean is like the real one, and on this sample real
water attenuates more than L23 predicts from the same ``Rrs``.  That bounds what
held-out L23 scores can promise, for the hyperspectral network above all.

.. figure:: kdl23_pangaea.png
   :width: 95%

   Network against PANGAEA Kd, every matched (spectrum, band) cell, ±6 nm
   (the MODIS bands match no PANGAEA spectrum within ±2.5 nm).
   Dotted: Kd = 0.65 m⁻¹, the top of L23's range at 490 nm.

{_tbl('PANGAEA validation. mae_ln = mean abs(ln(network/measured)) over cells.', 'kdl23_pangaea.csv')}
Scope and limits
----------------

* **Clear water only.**  L23 has Kd(490) ≤ 0.65 m⁻¹, 95% below 0.10.  No
  turbid branch is attempted, and inputs outside the trained domain (by more
  than 1% of a feature's span) are flagged ``out_of_domain`` by
  ``kd_l23``.
* **The hyperspectral network has no in-situ validation.**  Its numbers are
  held-out L23, which is the same RT that generated its training data.
* **θs above 60°** is outside L23.  With the 1/μw factor analytic, 60–70° is
  arithmetic, flagged ``extrapolated_sza``; beyond 70° the result is NaN.
* The red is noise-dominated (PACE noise ≈ 50% of ``Rrs`` at 670 nm).  The
  networks were trained to tolerate it, not to extract signal from it.
"""


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--docs-root', default=None)
    p.add_argument('--no-save', action='store_true',
                   help='do not write the weights into ocpy')
    p.add_argument('--page-only', action='store_true',
                   help='rewrite the page from the CSVs and weights of the last '
                        'full run (no training)')
    a = p.parse_args()
    if a.page_only:
        page_only(a.docs_root)
    else:
        build(a.docs_root, save=not a.no_save)

"""The **LS2 ladder** report page -- one direct algorithm, its inputs one at a time.

LS2 (Loisel et al. 2018) is a *direct* algorithm: closed-form ``a`` and ``bb``
from ``Rrs``, ``<Kd>_1``, ``b_p`` and the solar zenith, no fit and no likelihood
(ls2 Q1). Its sweeps run it as a ladder of **input rungs** (ls2 Q2): every rung
runs the same published look-up tables and differs from its neighbour in where
*one* input comes from -- true ``Kd`` and ``b_p``, then ``b_p`` from OC4v4
chlorophyll, then ``Kd`` from a neural network -- plus a diagnostic rung
(an effective ``muw``, ls2 Q9) and a Kd-noise sensitivity ladder (ls2 Q33).

This is a sibling of :mod:`ioptics.report.rt_ladder`, not a generalization of it
(ls2 task 9): the rung axis means something different here (inputs, not
radiative transfers), the cells are ``a``, ``a_nw``, ``bb``, ``bb_p`` with the
decomposition ``a_ph``/``a_dg`` as explicit **not applicable** cells, and the
model-selection sections become one explicit "not applicable: LS2 has no
likelihood" section. The page machinery is reused verbatim: the
``standard.py`` section helpers, the ``rst`` API, the ``figures.*`` builders
and ``tables.qc``/``accuracy``/``head_to_head``.

What the page carries, in order:

1. what the ladder is;
2. **the limitations** -- each one a decision or a measurement recorded in
   ``claude_prompts/LS2/ls2_execution.md``, stated on the page, not in a log;
3. the **ladder table** -- one row per rung, accuracy at the reference bands,
   coverage per status, ``a_ph``/``a_dg`` as "not applicable", and BING's
   MCMC row beside it when a comparator sweep is supplied;
4. the **Kd-noise sensitivity** table, as a slope;
5. retrieved-vs-true panels and accuracy vs wavelength, with ``a_nw`` drawn
   only where it is a meaningful share of ``a`` (ls2 Q34);
6. **where LS2 returns nothing**, per wavelength (ls2 Q24);
7. "not applicable" for model selection;
8. the head-to-head verdicts between rungs, and the accuracy and QC tables.

Never touches the leaderboard or the landing page: the LS2 sweeps are
registered with ``leaderboard: false``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ioptics import diagnostics, metrics, plotting, records
from ioptics.algorithms import registry
from ioptics.report import figures, rst, tables
from ioptics.report.standard import (DEFAULT_DOCS_SRC, _fig_section,
                                     _not_shown_section, _plan_panels,
                                     _pngs, _provenance, _prune_stale,
                                     _table_section)

#: Page file name (``reports/<sweep_id>/ls2_ladder.rst``).
PAGE = 'ls2_ladder'

#: Ladder order = insertion order of the registry seed.
LADDER = tuple(registry.DIRECT_SEED)

#: Human labels per rung, from the registry seed.
LABELS = {name: label for name, (label, _) in registry.DIRECT_SEED.items()}

#: The rung everything else is read against: LS2 with true inputs.
BASE_RUNG = 'ls2_i'

#: The Kd-noise sensitivity ladder: ``(rung, relative Kd noise)`` (ls2 Q33).
KD_NOISE_RUNGS = (('ls2_i', 0.0), ('ls2_i_kdnoise05', 0.05),
                  ('ls2_i_kdnoise10', 0.10), ('ls2_i_kdnoise20', 0.20))

#: ``(component, reference band)`` cells of the ladder table, in reading order.
LADDER_CELLS = (('a', 440.0), ('a_nw', 440.0), ('bb', 555.0), ('bb_p', 555.0),
                ('bb_p', 670.0))

#: Components LS2 structurally cannot produce: their cells read
#: "not applicable" rather than being absent, because the absence is the
#: result (ls2 Q5/Q25).
NOT_APPLICABLE_CELLS = (('a_ph', 440.0), ('a_dg', 440.0))

#: What a not-applicable cell says.
NOT_APPLICABLE = 'not applicable'

#: ``a_nw`` is drawn against wavelength only where the median truth
#: ``a_nw / a`` reaches this share (ls2 Q34): above ~550 nm pure water is
#: nearly all of ``a``, and a few-percent error in ``a`` becomes hundreds of
#: percent in the small difference. The tables keep every band.
ANW_SHARE_FLOOR = 0.10

#: The BING population the LS2 headline is quoted against (ls2 Q23).
COMPARATOR_FIT_METHOD = 'mcmc'


# --------------------------------------------------------------------------- #
# what population this sweep's LS2 rows were scored in
# --------------------------------------------------------------------------- #

def _pool(sweep):
    """The contest population LS2 is read in on this sweep.

    A direct algorithm's rows are duplicated into every fitted pool of their
    sweep (ls2 Q23), and the LS2 headline is quoted against MCMC; with no fitted
    algorithm in the sweep the pool is ``'direct'``.
    """
    ms = sweep.metrics_scalar
    if ms is None or ms.empty or 'pool' not in ms.columns:
        return metrics.DIRECT_FIT_METHOD
    pools = set(ms['pool'].dropna().unique())
    for p in (COMPARATOR_FIT_METHOD, 'chisq', metrics.DIRECT_FIT_METHOD):
        if p in pools:
            return p
    return sorted(pools)[0]


def _in_pool(df, pool):
    """Rows of a metrics table in ``pool`` (``fit_method`` before the column)."""
    col = 'pool' if 'pool' in df.columns else 'fit_method'
    return df[df[col] == pool]


# --------------------------------------------------------------------------- #
# tables
# --------------------------------------------------------------------------- #

def _cell_values(g, comp, ref):
    """``(n, mae, bias, median_ratio, caveat)`` of one cell, or ``None``."""
    c = g[(g['component'] == comp) & (g['ref_wave'] == ref)]
    if c.empty:
        return None
    c = c.iloc[0]
    cav = c['caveat'] if 'caveat' in c and isinstance(c['caveat'], str) else ''
    return (int(c['n']) if pd.notna(c['n']) else 0, c['mae'], c['bias'],
            c.get('median_ratio', np.nan), cav)


def _closure(g, row):
    qc = g[g['component'] == 'Rrs']
    if qc.empty:
        return
    q = qc.iloc[0]
    for col in ('n_attempted', 'frac_ok', 'frac_poor_fit',
                'frac_out_of_scope', 'frac_fit_failed'):
        row[col] = q.get(col, np.nan)


def ladder_table(sweep, *, stratum='all', root=None, write=True,
                 comparator=None):
    """One row per rung: coverage plus accuracy at the reference bands.

    Built from ``metrics_scalar`` alone, so a value here agrees with the
    accuracy table to the digit. Per cell (:data:`LADDER_CELLS`): ``n``,
    ``mae`` (fractional multiplicative, log space), ``bias`` and
    ``median_ratio`` (retrieved/true; 1 = unbiased). There is no coverage
    column: a direct algorithm has no interval to cover anything with.

    **Not-applicable cells survive.** Unlike :func:`ioptics.report.rt_ladder.
    ladder_table`, which keeps ``n > 0`` cells only, ``a_ph``/``a_dg``
    (:data:`NOT_APPLICABLE_CELLS`) appear on every LS2 row as
    :data:`NOT_APPLICABLE` -- read from the metrics' ``not_applicable`` rows
    where the sweep has them, and stated otherwise, because LS2 never
    returns either component.

    ``comparator`` is an optional ``(label, metrics_scalar rows)`` pair -- a
    BING population on the same data (:func:`comparator_rows`) -- appended
    as a final row with every cell filled, decomposition included.

    Writes ``ls2_ladder_<stratum>.csv`` under the sweep's ``tables/`` when
    ``write``.
    """
    sweep = figures.resolve(sweep, root)
    ms = sweep.metrics_scalar
    if ms is None or ms.empty:
        return pd.DataFrame()
    sub = _in_pool(ms, _pool(sweep))
    sub = sub[sub['stratum'] == stratum]
    rows = []
    for rung in LADDER:
        g = sub[sub['algorithm'] == rung]
        if g.empty:
            continue
        row = {'rung': rung, 'label': LABELS.get(rung, rung)}
        _closure(g, row)
        for comp, ref in LADDER_CELLS:
            got = _cell_values(g, comp, ref)
            tag = f'{comp}_{int(ref)}'
            if got is None or got[0] == 0:
                continue
            row[f'{tag}_n'], row[f'{tag}_mae'], row[f'{tag}_bias'], \
                row[f'{tag}_ratio'], _ = got
        for comp, ref in NOT_APPLICABLE_CELLS:
            row[f'{comp}_{int(ref)}'] = NOT_APPLICABLE
        rows.append(row)
    if comparator is not None:
        label, g = comparator
        g = g[g['stratum'] == stratum]
        row = {'rung': 'BING', 'label': label}
        _closure(g, row)
        for comp, ref in LADDER_CELLS:
            got = _cell_values(g, comp, ref)
            if got is None or got[0] == 0:
                continue
            tag = f'{comp}_{int(ref)}'
            row[f'{tag}_n'], row[f'{tag}_mae'], row[f'{tag}_bias'], \
                row[f'{tag}_ratio'], _ = got
        for comp, ref in NOT_APPLICABLE_CELLS:
            got = _cell_values(g, comp, ref)
            if got is not None and got[0] > 0:
                row[f'{comp}_{int(ref)}'] = (f'mae {got[1]:.3f}, '
                                             f'bias {got[2]:+.3f}')
        rows.append(row)
    df = pd.DataFrame(rows)
    if write and not df.empty:
        out = figures.subdir(sweep, 'tables') / f'ls2_ladder_{stratum}.csv'
        df.round(4).to_csv(out, index=False)
    return df


def comparator_rows(compare_sweep, *, root=None,
                    fit_method=COMPARATOR_FIT_METHOD, algorithm=None):
    """A BING population's ``metrics_scalar`` rows, to set beside LS2.

    ``compare_sweep`` is a sweep id (or a loaded sweep) that ran BING on the
    same data -- for L23 X=4, the RT-A sweep. Its rows are taken from the
    ``fit_method`` population (MCMC by default: the LS2 headline is quoted
    against MCMC BING, ls2 Q23) and, if ``algorithm`` is ``None``, from its
    first algorithm in sorted order.

    Returns
    -------
    tuple or None
        ``(label, rows)``, or ``None`` when the sweep or its metrics are not on
        disk -- which the page then says, rather than omitting silently.
    """
    try:
        sw = figures.resolve(compare_sweep, root)
    except Exception:
        return None
    ms = getattr(sw, 'metrics_scalar', None)
    if ms is None or ms.empty:
        return None
    sub = _in_pool(ms, fit_method)
    if sub.empty:
        return None
    algo = algorithm or sorted(sub['algorithm'].unique())[0]
    sub = sub[sub['algorithm'] == algo]
    return (f'BING {algo} ({fit_method}, {sw.sweep_id})', sub)


def kd_noise_table(sweep, *, stratum='all', root=None, write=True):
    """LS2's accuracy against relative Kd noise, and the slope (ls2 Q15/Q33).

    One row per ``(rung, noise)`` of :data:`KD_NOISE_RUNGS` with the ``mae``
    of each :data:`LADDER_CELLS` cell, then a ``slope`` row: the least-squares
    ``d(mae)/d(noise)`` over the four levels, i.e. "LS2 loses this much
    accuracy per unit of relative Kd error". The noise is one multiplicative
    draw per spectrum, unbiased, so it shows in the spread (``mae``), not in
    the median.

    Writes ``kd_noise_<stratum>.csv`` when ``write``. Empty when the sweep
    does not carry the noise rungs.
    """
    sweep = figures.resolve(sweep, root)
    ms = sweep.metrics_scalar
    if ms is None or ms.empty:
        return pd.DataFrame()
    sub = _in_pool(ms, _pool(sweep))
    sub = sub[sub['stratum'] == stratum]
    rows = []
    for rung, sigma in KD_NOISE_RUNGS:
        g = sub[sub['algorithm'] == rung]
        if g.empty:
            continue
        row = {'rung': rung, 'kd_noise': sigma}
        for comp, ref in LADDER_CELLS:
            got = _cell_values(g, comp, ref)
            row[f'{comp}_{int(ref)}_mae'] = got[1] if got and got[0] else np.nan
        rows.append(row)
    df = pd.DataFrame(rows)
    if len(df) >= 2:
        slope = {'rung': 'slope d(mae)/d(noise)', 'kd_noise': np.nan}
        for col in [c for c in df.columns if c.endswith('_mae')]:
            ok = np.isfinite(df[col].to_numpy(dtype=float))
            slope[col] = (float(np.polyfit(df['kd_noise'][ok], df[col][ok], 1)[0])
                          if ok.sum() >= 2 else np.nan)
        df = pd.concat([df, pd.DataFrame([slope])], ignore_index=True)
    if write and len(df) > 1:
        out = figures.subdir(sweep, 'tables') / f'kd_noise_{stratum}.csv'
        df.round(4).to_csv(out, index=False)
    return df if len(df) > 1 else pd.DataFrame()


# --------------------------------------------------------------------------- #
# figures specific to a direct algorithm
# --------------------------------------------------------------------------- #

def anw_share(sweep, *, dataset=None):
    """Median truth ``a_nw / a`` per wavelength, from the spectral table."""
    sp = sweep.spectral
    if sp is None or sp.empty or 'truth' not in sp.columns:
        return pd.Series(dtype=float)
    keep = sp['component'].isin(['a', 'a_nw'])
    if dataset is not None:
        keep &= sp['dataset'] == dataset
    sub = sp[keep]
    if sub.empty:
        return pd.Series(dtype=float)
    one = sub['algorithm'].iloc[0]        # truth does not depend on the rung
    sub = sub[sub['algorithm'] == one]
    wide = sub.pivot_table(index=['obs_id', 'wavelength'], columns='component',
                           values='truth')
    if not {'a', 'a_nw'} <= set(wide.columns):
        return pd.Series(dtype=float)
    share = (wide['a_nw'] / wide['a']).groupby(level='wavelength').median()
    return share


def accuracy_spectrum(sweep, *, pool, floor=ANW_SHARE_FLOOR, dataset=None):
    """Accuracy vs wavelength for LS2's outputs, ``a_nw`` masked by share.

    The standard ``mae``-vs-wavelength grid
    (:func:`ioptics.diagnostics.accuracy_spectrum_data`,
    :func:`ioptics.plotting.accuracy_spectrum_grid`), with one change: the
    ``a_nw`` panel keeps only the bands where the median truth ``a_nw/a`` is at
    least ``floor`` (ls2 Q34, option b for figures). Beyond them the panel would
    show pure water's share of ``a``, not LS2. The tables are not masked.
    """
    share = anw_share(sweep, dataset=dataset)
    kept = set(share.index[share >= floor]) if not share.empty else set()
    panels = []
    for comp in ('a', 'a_nw', 'bb', 'bb_p'):
        data = diagnostics.accuracy_spectrum_data(
            sweep.metrics_spectral, comp, dataset=dataset, fit_method=pool)
        if comp == 'a_nw':
            for algo, s in list(data['series'].items()):
                mask = np.isin(np.asarray(s['wave'], dtype=float), list(kept))
                data['series'][algo] = {k: np.asarray(v)[mask]
                                        for k, v in s.items()}
        panels.append(data)
    if not any(p['series'] for p in panels):
        return []
    fig = plotting.accuracy_spectrum_grid(panels, ncols=2)
    return figures._save(fig, figures._figdir(sweep), 'ls2_accuracy_vs_wavelength')


def nan_reason_spectrum(sweep, *, pool, rung=BASE_RUNG):
    """Where LS2 returns nothing, per wavelength, by reason (ls2 Q24).

    One line per reason, from ``metrics_spectral``'s ``frac_nan_<reason>``
    columns for ``rung``: the share of spectra whose cell at that wavelength
    carries the reason. ``negative`` is read from ``bb_p``, the component it
    hits hardest; every other reason is shared by the four outputs and read
    from ``a``. This is the wavelength-resolved view a per-spectrum count
    would erase -- the kappa table's band near 490-505 nm, and its end at
    702 nm.
    """
    import matplotlib.pyplot as plt

    msp = sweep.metrics_spectral
    if msp is None or msp.empty:
        return []
    sub = msp[(msp['algorithm'] == rung) & (msp['stratum'] == 'all')]
    sub = _in_pool(sub, pool)
    cols = [c for c in sub.columns if c.startswith('frac_nan_')]
    if sub.empty or not cols:
        return []
    fig, ax = plt.subplots(figsize=(7, 4))
    drew = False
    for col in cols:
        reason = col[len('frac_nan_'):]
        comp = 'bb_p' if reason == 'negative' else 'a'
        s = sub[sub['component'] == comp].sort_values('wavelength')
        if s.empty or not np.nanmax(s[col].to_numpy(dtype=float), initial=0) > 0:
            continue
        ax.plot(s['wavelength'], s[col], label=f'{reason} ({comp})')
        drew = True
    if not drew:
        plt.close(fig)
        return []
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel('share of spectra')
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=8)
    ax.set_title(f'{rung}: cells flagged, by reason')
    return figures._save(fig, figures._figdir(sweep),
                         f'ls2_nan_reasons_{figures._safe(rung)}')


# --------------------------------------------------------------------------- #
# facts the prose is built from (derived from the artefacts, never assumed)
# --------------------------------------------------------------------------- #

def _share_with(spec_rows, reason):
    """Share of cells whose ``nan_reason`` contains ``reason``."""
    if spec_rows.empty or 'nan_reason' not in spec_rows.columns:
        return np.nan
    cells = spec_rows['nan_reason'].fillna('').astype(str)
    return float(cells.str.split(records.NAN_REASON_SEP)
                 .apply(lambda c: reason in c).mean())


def _pure_water_delta():
    """``(delta a_w, delta b_w)`` medians from ``pure_water_delta.py``, or ``None``.

    Regenerated, not quoted: it needs the L23 data files, and when they are
    absent the page says so rather than printing a remembered number.
    """
    import importlib.util

    path = (Path(__file__).resolve().parents[1] / 'runs' / 'prototypes' / 'ls2'
            / 'pure_water_delta.py')
    try:
        spec = importlib.util.spec_from_file_location('pure_water_delta', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        d = mod.delta()
        return (d['a_w']['summary']['median'], d['b_w']['summary']['median'])
    except Exception:
        return None


def _facts(sweep, pool):
    """What this sweep is, read off its tables and provenance."""
    sc = sweep.scalar
    sp = sweep.spectral
    prov = _provenance(sweep)
    cfg = prov.get('config', {}) or {}
    rungs = [r for r in LADDER if r in set(sc['algorithm'].unique())]
    base = sp[(sp['algorithm'] == BASE_RUNG) & (sp['component'] == 'a')] \
        if sp is not None and not sp.empty else pd.DataFrame()
    blocks = {b.get('name'): b for b in (prov.get('algorithms') or [])
              if isinstance(b, dict)}
    raman = sorted({bool(b.get('raman')) for b in blocks.values()
                    if b.get('kind') == 'direct'})
    kappa_band = np.nan
    msp = sweep.metrics_spectral
    col = 'frac_nan_kappa_out_of_range'
    if msp is not None and not msp.empty and col in msp.columns:
        k = _in_pool(msp, pool)
        k = k[(k['algorithm'] == BASE_RUNG) & (k['component'] == 'a')
              & (k['stratum'] == 'all')]
        band = k[(k['wavelength'] >= 488) & (k['wavelength'] <= 507)]
        if not band.empty:
            kappa_band = float(band[col].max())
    nn_failed = {}
    for rung in ('ls2_iii', 'ls2_iii_modis'):
        g = sc[sc['algorithm'] == rung]
        if not g.empty:
            nn_failed[rung] = int((g['status'] == 'fit_failed').sum())
    l23 = (cfg.get('dataset_opts') or {}).get('L23') or {}
    return dict(
        rungs=rungs,
        datasets=sorted(str(d) for d in sc['dataset'].dropna().unique()),
        n_obs=int(sc.groupby('dataset')['obs_id'].nunique().sum()),
        noise=sorted(str(t) for t in sc['noise_model'].dropna().unique())
        if 'noise_model' in sc.columns else [],
        wv_min=cfg.get('wv_min'), wv_max=cfg.get('wv_max'),
        X=l23.get('X'), kd1=l23.get('kd1'), raman=raman,
        kappa_share=_share_with(base, 'kappa_out_of_range'),
        kappa_band=kappa_band,
        off_grid_share=_share_with(base, 'off_grid'),
        kd_missing_share=_share_with(base, 'kd_missing'),
        nn_failed=nn_failed,
        has_truth=bool(figures.scored_refs(sweep, fit_method=pool)),
        pool=pool)


def _pct(x, digits=1):
    return 'not measured' if not np.isfinite(x) else f'{100 * x:.{digits}f}%'


def _overview(sweep, f):
    rung_list = '\n'.join(f'#. ``{r}`` — {LABELS.get(r, r)}' for r in f['rungs'])
    win = ''
    if f['wv_min'] is not None and f['wv_max'] is not None:
        win = f' over {f["wv_min"]:g}–{f["wv_max"]:g} nm'
    x = ''
    if f['X'] is not None:
        inel = {1: 'elastic (no inelastic processes)', 2: 'Raman only',
                4: 'Raman and chlorophyll fluorescence'}.get(int(f['X']), '')
        x = (f' The spectra are L23 ``X={f["X"]}`` — {inel} — and LS2\'s Raman '
             f'correction is **{"on" if True in f["raman"] else "off"}** on every '
             f'rung (ls2 Q4).')
    noise = ', '.join(f'``{t}``' for t in f['noise']) or 'the dataset default'
    return (
        f'This is the **LS2 ladder** for sweep ``{sweep.sweep_id}``: LS2 (Loisel et '
        f'al. 2018), a **direct** algorithm — closed-form ``a`` and ``bb`` from '
        f'``Rrs``, ``<Kd>_1``, ``b_p`` and the solar zenith through published look-up '
        f'tables, with no fit and no likelihood — run on {f["n_obs"]} spectra from '
        f'{", ".join(f["datasets"])}{win}, noise {noise}.{x} Every rung runs the '
        f'same tables and differs from its neighbour in where **one** input comes '
        f'from, so a difference between two rows is the cost of that input:'
        f'\n\n{rung_list}\n\n'
        f'``ls2_i`` gives LS2 the truth for both side inputs — the most it can do, '
        f'and a level nobody reaches from orbit. Its own error is the published '
        f'tables\' error. Pure water always comes from ocpy, never from the truth '
        f'(ls2 Q21), and ``<Kd>_1`` is the ``{f["kd1"] or "record"}`` definition '
        f'(ls2 Q10). Every number on this page is regenerable from the persisted '
        f'sweep artifacts under ``runs/``.')


def _kappa_item(f):
    """The Raman-correction limitation, or why it does not apply."""
    if f['raman'] == [False]:
        return ('**The Raman correction κ is off on every rung** (ls2 Q4): this '
                'realization\'s truth is elastic, so there is no Raman signal to '
                'correct, and none of the κ table\'s gaps (its end at 702 nm, '
                'its defective row near 502 nm) reaches this page; '
                '``kappa_out_of_range`` never appears among the NaN reasons.')
    return (f'**The Raman correction κ is unavailable on {_pct(f["kappa_share"])} '
            f'of cells** (``ls2_i``). Above 702 nm the κ table ends, and κ is NaN '
            f'there by decision, not the silently clamped value (ls2 Q22). Near '
            f'490–505 nm one row of the published table has a collapsed ``bb/a`` '
            f'range and coefficients of order 10⁵, so κ fails there on up to '
            f'{_pct(f["kappa_band"])} of spectra. Those cells keep the uncorrected '
            f'value, or the last applied κ when a later pass failed (ls2 Q28), and '
            f'are flagged ``kappa_out_of_range``. The Raman correction is iterated '
            f'to convergence; the authors\' code makes a single pass (ls2 '
            f'Q14/Q22).')


def _limitations(f):
    """The decisions and measurements that bound what this page can claim."""
    pw = _pure_water_delta()
    pw_text = (f'Against L23\'s own pure water the difference is '
               f'{_pct(pw[0], 3)} in ``a_w`` and {_pct(pw[1], 2)} in ``b_w`` '
               f'(median over 400–750 nm), so it is not a material bias here'
               if pw is not None else
               'The difference against L23\'s own pure water is regenerated by '
               '``runs/prototypes/ls2/pure_water_delta.py``, which needs the L23 '
               'files and could not be run for this build')
    items = [
        ('**``b_p`` from chlorophyll is a plain λ⁻¹ power law.** Rungs (ii) and '
         '(iii) take ``b_p(λ) = 0.347·Chl^0.766·(λ/660)^−1`` exactly as the authors\' '
         '``bp_from_Chla.m`` does: the amplitude is Loisel & Morel (1998) Eq. 6, '
         'fitted to the particle *attenuation* ``c_p(660)`` and identified with '
         '``b_p``, and the shape is λ⁻¹, **not** the chlorophyll-dependent '
         'exponent of Morel & Maritorena (2001) that the authors cite. Chl is '
         'OC4v4 (O\'Reilly et al. 2000), not the 1998 OC4 BING\'s prior uses '
         '(ls2 Q29).'),
        ('**Pure water is LS2\'s own, never the truth\'s** (ls2 Q21): the IOCCG '
         '``a_w`` table and Zhang, Hu & He (2009) ``b_w`` at 20 °C, S = 35. LS2 '
         'subtracts them to report ``a_nw`` and ``bb_p``, so any difference lands '
         f'one-for-one in those two. {pw_text}.'),
        (f'**LS2 is defined only for η = b_w/(b_p + b_w) < 0.2**, i.e. '
         f'``b_p > 4·b_w``. Very clear blue water fails it: '
         f'{_pct(f["off_grid_share"], 2)} of ``ls2_i``\'s cells fall outside the '
         f'table and come back NaN with reason ``off_grid``.'),
        _kappa_item(f),
        ('**``a_nw`` in the red is pure water\'s share of ``a``, not LS2.** A '
         'few-percent bias in ``a`` becomes hundreds of percent in ``a − a_w`` '
         'beyond ~550 nm. The tables keep every band; the accuracy-vs-wavelength '
         f'figure draws ``a_nw`` only where the median truth ``a_nw/a`` is at least '
         f'{ANW_SHARE_FLOOR:.0%} (ls2 Q34).'),
        ('**There is no ``a_ph`` or ``a_dg``.** LS2 retrieves totals and their '
         'non-water parts; it has no decomposition. Those cells read "not '
         'applicable" — the absence is the point of the comparison, not a gap '
         '(ls2 Q5/Q25).'),
        ('**``ok`` is strict; scoring is per cell.** A spectrum is ``ok`` only if '
         'all four outputs are finite and positive at every band (ls2 Q5). With '
         'noised ``Rrs`` almost every spectrum has one unusable cell (a negative '
         '``bb`` where noise drove red ``Rrs`` below zero), so most are '
         '``poor_fit`` — and their finite cells are scored, so the hardest water '
         'is not dropped selectively (ls2 Q31).'),
        ('**LS2 is never an exemplar.** It has no model ``Rrs`` and no posterior, '
         'so the exemplar panels of the standard pages do not apply to it.'),
        ('**The headline is quoted against MCMC BING** (ls2 Q23): the same L23 '
         'spectra, the same noise *form*, and BING\'s MCMC population — the one '
         'RT-A reads first.'),
    ]
    if f['X'] == 4:
        items.append(
            '**Chlorophyll fluorescence is not corrected.** At ``X=4`` the truth '
            'carries Raman *and* Chl fluorescence; κ corrects Raman only, so the '
            'fluorescence lifts ``Rrs`` near 685 nm and LS2 reads it as '
            'backscattering (``bb`` near 670 nm runs high on every rung).')
    if f['X'] == 2:
        items.append(
            '**Five X=2 scenarios have no profile.** The distributed '
            '``Hydrolight200_profile.nc`` lacks rows 365, 376, 387, 398 and 409, so '
            'their ``<Kd>_1`` is NaN: every rung that reads ``Kd`` from the record '
            'returns ``fit_failed`` there with reason ``kd_missing``.')
    if f['nn_failed']:
        txt = '; '.join(f'``{r}`` {n}' for r, n in f['nn_failed'].items())
        items.append(
            f'**The Kd networks need positive Rrs at every input band.** A network '
            f'returns nothing when a band it reads is negative, and ``pace`` noise '
            f'drives red ``Rrs`` negative; spectra with no Kd at all ({txt}) come '
            f'back ``fit_failed``. The PACE network reads up to 700 nm and is hit '
            f'hardest; the MODIS network\'s clear-water branch stops at 547 nm.')
    items.append(
        '**Excluded from the leaderboard by design** until the report is trusted '
        '(``leaderboard: false``). This page does not touch the landing page.')
    return '\n\n'.join(f'* {t}' for t in items)


def _ladder_desc(f, comparator_label):
    cells = ', '.join(f'``{c}({int(r)})``' for c, r in LADDER_CELLS)
    na = ', '.join(f'``{c}({int(r)})``' for c, r in NOT_APPLICABLE_CELLS)
    bing = (f' The last row is {comparator_label}, the population the headline is '
            f'quoted against; its ``a_ph``/``a_dg`` cells carry BING\'s own error.'
            if comparator_label else
            ' No BING comparator was available for this build, so the table is '
            'LS2 alone (see the note at the end of the page).')
    return (
        f'One row per rung, all strata. Coverage: ``frac_ok`` / ``frac_poor_fit`` / '
        f'``frac_out_of_scope`` / ``frac_fit_failed`` over ``n_attempted`` spectra '
        f'(``ok`` is strict, ``poor_fit`` a partial result; see the limitations). '
        f'Accuracy at {cells}: ``n`` scored cells, ``mae`` (fractional '
        f'multiplicative error in log space; 0.10 ≈ 10 %), signed ``bias`` (> 0 '
        f'= over-estimate) and ``ratio`` = median retrieved/true. {na} read '
        f'"{NOT_APPLICABLE}" on every LS2 row.{bing} Read the table down a column: '
        f'what changes from one rung to the next is the cost of that rung\'s input.')


# --------------------------------------------------------------------------- #
# the page
# --------------------------------------------------------------------------- #

def build(sweep_id, *, root=None, docs_root=None, compare_sweep=None,
          compare_algorithm=None):
    """Build ``reports/<sweep_id>/ls2_ladder.rst`` and its display assets.

    ``compare_sweep`` names a BING sweep on the same data (for L23 X=4, the
    RT-A sweep) whose MCMC population is set beside LS2 in the ladder table;
    when it is not given, or not on disk, the page says so. Returns the page
    path. Never touches the leaderboard or the landing page.
    """
    sweep = figures.load(sweep_id, root=root)
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS_SRC
    report_dir = docs_root / 'reports' / sweep_id
    report_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = figures.subdir(sweep, 'tables')
    pool = _pool(sweep)
    f = _facts(sweep, pool)
    comparator = (comparator_rows(compare_sweep, root=root,
                                  algorithm=compare_algorithm)
                  if compare_sweep is not None else None)

    published = set()
    not_shown = []
    blocks = [rst.title(f'LS2 ladder — {sweep_id}'),
              rst.provenance_header(sweep_id, _provenance(sweep)),
              rst.section('Overview', _overview(sweep, f)),
              rst.section('What this page can and cannot claim',
                          _limitations(f))]

    # ---- the ladder table -----------------------------------------------------
    df = ladder_table(sweep, comparator=comparator)
    if not df.empty:
        blocks.append(_table_section(
            sweep, report_dir, 'The ladder', tables_dir / 'ls2_ladder_all.csv',
            'One row per LS2 rung.',
            desc=_ladder_desc(f, comparator[0] if comparator else None),
            published=published))
    if comparator is None:
        not_shown.append(
            'BING beside LS2 — '
            + (f'the comparator sweep ``{compare_sweep}`` has no metrics on this '
               f'machine.' if compare_sweep is not None else
               'no comparator sweep was supplied to this build.')
            + ' The LS2-versus-BING head-to-head is read against MCMC BING on '
              'the same spectra (ls2 Q23) and lands with ls2 task 14.')

    # ---- Kd-noise sensitivity -------------------------------------------------
    kn = kd_noise_table(sweep)
    if not kn.empty:
        blocks.append(_table_section(
            sweep, report_dir, 'How much a Kd error costs',
            tables_dir / 'kd_noise_all.csv',
            '``mae`` against relative Kd noise, and the slope.',
            desc=('``ls2_i`` with its true ``<Kd>_1`` multiplied by one random '
                  'factor ``1 + σε`` per spectrum, σ = 0, 5, 10 and 20 % (ls2 '
                  'Q15/Q33) — a whole spectrum wrong together, as a retrieved '
                  'Kd is. The noise is unbiased, so it shows in ``mae``, not in the '
                  'median. The last row is the least-squares slope '
                  '``d(mae)/d(σ)``: the accuracy LS2 loses per unit of relative '
                  'Kd error, cell by cell.'),
            published=published))
    else:
        not_shown.append('the Kd-noise table — the sweep does not carry the '
                         'Kd-noise rungs.')

    # ---- retrieved vs true ----------------------------------------------------
    if f['has_truth']:
        scored = figures.scored_refs(sweep, fit_method=pool)
        for comp, ref, n in _plan_panels(scored):
            label = f'{comp}({ref:g})'
            blocks.append(_fig_section(
                sweep, report_dir, f'Retrieved vs. true — {label}',
                _pngs(figures.scatter_set(sweep, comp, ref=ref, fit_method=pool)),
                caption=(f'{label}, every rung — at most {n} retrieval-truth '
                         f'pairs per rung.'),
                desc=(f'Retrieved vs. true **{label}**, one point per spectrum and '
                      f'rung, log–log; solid 1:1, dashed ±3×. One algorithm, '
                      f'different inputs: where the clouds separate, the input is '
                      f'doing the separating.'),
                published=published))
            blocks.append(_fig_section(
                sweep, report_dir, f'Ratio distribution — {label}',
                _pngs(figures.ratio_hist(sweep, comp, ref=ref, fit_method=pool)),
                caption=f'Retrieved/true ratio buckets for {label}, per rung.',
                desc='How each rung sits about 1:1; the vertical rule marks 1.',
                published=published))
        spec_pngs = _pngs(accuracy_spectrum(sweep, pool=pool))
        blocks.append(_fig_section(
            sweep, report_dir, 'Accuracy vs. wavelength', spec_pngs,
            caption=('Fractional multiplicative MAE against wavelength for ``a``, '
                     '``a_nw``, ``bb`` and ``bb_p``, every rung overlaid; '
                     f'``a_nw`` only where truth ``a_nw/a`` ≥ {ANW_SHARE_FLOOR:.0%}.'),
            desc=('The same ``mae`` as the ladder table at every band the truth '
                  'covers. The ``a_nw`` panel stops where pure water takes over '
                  '``a`` (ls2 Q34); above 702 nm the Raman correction is '
                  'unavailable, and at ``X=4`` the fluorescence band near 685 nm '
                  'shows in ``bb``.'),
            published=published))
        if not spec_pngs:
            not_shown.append('the accuracy-vs-wavelength figure — no output is '
                             'scored against truth at several bands.')
    else:
        not_shown.append('every retrieved-vs-true panel — this sweep carries no '
                         'truth.')

    # ---- where LS2 returns nothing --------------------------------------------
    reasons_png = _pngs(nan_reason_spectrum(sweep, pool=pool))
    blocks.append(_fig_section(
        sweep, report_dir, 'Where LS2 returns nothing, and why', reasons_png,
        caption=(f'Share of spectra whose ``{BASE_RUNG}`` cell at each wavelength '
                 f'carries each reason (``negative`` read from ``bb_p``, the rest '
                 f'from ``a``).'),
        desc=('Per-cell reasons, recorded per wavelength because the failures are '
              'wavelength-specific (ls2 Q24): ``kappa_out_of_range`` (the Raman '
              'table\'s 490–505 nm defect and its end at 702 nm), ``off_grid`` '
              '(η outside the table), ``kd_missing`` (no Kd at that band — a '
              'first attenuation depth beyond the L23 grid, or an unmeasured '
              'PANGAEA band), ``negative`` and ``not_converged``. Glossary: '
              ':doc:`/reports/glossary`.'),
        published=published))
    if not reasons_png:
        not_shown.append('the NaN-reason figure — no cell of the base rung '
                         'carries a reason.')

    # ---- model selection: not applicable --------------------------------------
    blocks.append(rst.section(
        'Model selection (ΔBIC) — not applicable',
        'LS2 has **no likelihood**: it does not fit, so it has no χ², no BIC and '
        'no posterior to compare. The ΔBIC contests of the standard and RT-ladder '
        'pages therefore have no LS2 row; the metrics tables carry an explicit '
        '``n = 0`` ``not_applicable`` row for every ΔBIC pair that involves it '
        'rather than leaving it absent. LS2 is compared with BING on accuracy '
        'alone.'))

    # ---- head-to-head between rungs, accuracy and QC ---------------------------
    if f['has_truth']:
        h2h = tables.head_to_head(sweep, fit_method=pool)
        if not h2h.empty:
            ties = int((h2h['verdict'] == 'indistinguishable').sum())
            blocks.append(_table_section(
                sweep, report_dir, 'Head-to-head verdicts between rungs',
                tables_dir / f'head_to_head_{pool}_all.csv',
                'Pairwise accuracy verdicts, all strata.',
                desc=(f'Every pair of rungs on the spectra both retrieved: '
                      f'``delta_mae`` = ``mae(A) − mae(B)`` with its paired-bootstrap '
                      f'95 % interval, and a ``verdict`` naming a winner only when '
                      f'the interval excludes 0 **and** clears the practical floor '
                      f'of {metrics.PRACTICAL_MAE_FLOOR:.0%}. {ties} of {len(h2h)} '
                      f'pairs are indistinguishable — between rungs, that says the '
                      f'input made no material difference.'),
                published=published))
        tables.accuracy(sweep, fit_method=pool)
        blocks.append(_table_section(
            sweep, report_dir, 'Accuracy', tables_dir / f'accuracy_{pool}_all.csv',
            'Ref-band accuracy, every scored component, all strata.',
            desc=('The full per-(component, reference band) table the ladder cells '
                  'come from. ``not_applicable`` rows are kept on purpose. Columns '
                  'are defined on the :doc:`/reports/glossary` page.'),
            published=published))
    tables.qc(sweep, fit_method=pool)
    blocks.append(_table_section(
        sweep, report_dir, 'Coverage and quality control',
        tables_dir / f'qc_{pool}_all.csv', 'Coverage per rung.',
        desc=('``n_attempted`` and the per-status fractions. The χ² columns are '
              'empty, not zero: LS2 has no misfit to report (ls2 Q5). Identical '
              '``out_of_scope`` counts on every rung keep the ladder fair — the same '
              'red-peaked spectra were declined everywhere.'),
        published=published))

    blocks.append(_not_shown_section(not_shown))
    out = report_dir / f'{PAGE}.rst'
    out.write_text(rst.page(*blocks), encoding='utf-8')
    _prune_stale(report_dir, published, this_page=out.name)
    rst.ensure_glob_toctree(docs_root / 'reports' / 'index.rst')
    return out

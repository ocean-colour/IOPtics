"""The **RT ladder** report page — one IOP parameterization, several radiative transfers.

The standard pages (:mod:`ioptics.report.standard`) compare *algorithms*: each
row is a different parameterization of the same physics.  The RT-test sweeps
(``ioptics/runs/prototypes/rt_tests/``) invert that: every row is ``expb_pow``
and only the forward model changes, along a five-rung ladder from the analytic
elastic model to the full inelastic stack.  Read through a cross-algorithm page
that produces five near-clones of one algorithm on every board, a leaderboard
fold that would rank one algorithm against itself, and prose about "which
algorithm wins" when the question is "how much of the error is the physics".
So the ladder gets its own page type (rt_tests task 14), built here.

What the page carries, in order:

1. what the ladder is and what is held fixed;
2. **the limitations** — every one of them is a decision recorded in
   ``rt_tests.md`` and must be on the page, not in a log;
3. the headline **fractional-change** figure (truth-free, so it is the *only*
   population statement possible on the PACE arm, and a useful one elsewhere);
4. the **ladder table** — one row per rung, accuracy against truth where truth
   exists, fit quality everywhere;
5. the standard retrieved-vs-true panels and accuracy-vs-wavelength for the
   MCMC population (the ladder was fitted by MCMC throughout);
6. **model selection** — the configured ΔBIC contest (elastic hybrid against the
   full inelastic stack) as a CDF and as a histogram, plus every pairwise
   contest in one table;
7. the head-to-head verdicts and the QC tables.

Nothing here touches the leaderboard or the landing page: the RT sweeps are
registered with ``leaderboard: false`` and this builder honours it by never
calling :func:`ioptics.report.leaderboard.update`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ioptics import diagnostics, metrics, records
from ioptics.algorithms import registry
from ioptics.report import figures, rst, tables
from ioptics.report.standard import (DEFAULT_DOCS_SRC, _fig_section,
                                     _not_shown_section, _plan_panels,
                                     _pngs, _provenance, _prune_stale,
                                     _table_section)

#: Page file name (``reports/<sweep_id>/rt_ladder.rst``).
PAGE = 'rt_ladder'

#: Ladder order = insertion order of the registry seed.
LADDER = tuple(registry.RT_VARIANT_SEED)

#: Human labels per rung, from the registry seed.
LABELS = {name: label for name, (label, _) in registry.RT_VARIANT_SEED.items()}

#: The ladder was fitted by MCMC on every arm (rt_tests Q13, Q44); MCMC is the
#: primary population on the page and χ² the secondary one.
PRIMARY = 'mcmc'
SECONDARY = 'chisq'

#: The truth-free headline: fractional change of the retrieved decomposition at
#: 443 nm from the elastic hybrid to the full inelastic stack (rt_tests task 14).
HEADLINE_REF = 443.0
HEADLINE_COMPONENTS = ('a_ph', 'a_dg', 'bb_p')

#: (component, reference band) columns of the ladder table, in reading order.
LADDER_CELLS = (('a', 440.0), ('a_ph', 440.0), ('a_dg', 440.0),
                ('bb', 555.0), ('bb_p', 555.0), ('bb_p', 670.0))


# --------------------------------------------------------------------------- #
# the ladder table
# --------------------------------------------------------------------------- #

def ladder_table(sweep, *, fit_method=PRIMARY, stratum='all', root=None,
                 write=True):
    """One row per rung: fit quality plus accuracy at the reference bands.

    Built from ``metrics_scalar`` alone — the same table every other number on the
    site comes from — so a value here agrees with the standard accuracy table to
    the digit.  Accuracy cells are ``mae`` / ``bias`` / ``coverage68`` (fractional
    multiplicative, log space; coverage nominal 0.68) and are blank for a sweep
    with no truth.  Rungs missing from the sweep are omitted rather than shown as
    blank rows.  Writes ``rt_ladder_<fit_method>_<stratum>.csv`` under the
    sweep's ``tables/`` when ``write``.
    """
    sweep = figures.resolve(sweep, root)
    ms = sweep.metrics_scalar
    if ms is None or ms.empty:
        return pd.DataFrame()
    sub = ms[(ms['fit_method'] == fit_method) & (ms['stratum'] == stratum)]
    rows = []
    for rung in LADDER:
        g = sub[sub['algorithm'] == rung]
        if g.empty:
            continue
        row = {'rung': rung, 'label': LABELS.get(rung, rung)}
        qc = g[g['component'] == 'Rrs']
        if not qc.empty:
            q = qc.iloc[0]
            for col in ('n_attempted', 'frac_ok', 'frac_poor_fit',
                        'frac_out_of_scope', 'frac_fit_failed',
                        'chi2_nu_median', 'rel_misfit_median'):
                row[col] = q.get(col, np.nan)
        for comp, ref in LADDER_CELLS:
            c = g[(g['component'] == comp) & (g['ref_wave'] == ref)
                  & g['n'].fillna(0).gt(0)]
            tag = f'{comp}_{int(ref)}'
            if c.empty:
                continue
            c = c.iloc[0]
            row[f'{tag}_n'] = int(c['n'])
            row[f'{tag}_mae'] = c['mae']
            row[f'{tag}_bias'] = c['bias']
            row[f'{tag}_cov68'] = c['coverage68']
            if 'caveat' in c and isinstance(c['caveat'], str) and c['caveat']:
                row[f'{tag}_caveat'] = c['caveat']
        rows.append(row)
    df = pd.DataFrame(rows)
    if write and not df.empty:
        out = figures.subdir(sweep, 'tables') / f'rt_ladder_{fit_method}_{stratum}.csv'
        df.round(4).to_csv(out, index=False)
    return df


def dbic_contests(sweep, *, fit_method=PRIMARY, stratum='all', root=None,
                  write=True):
    """Every pairwise ΔBIC contest in the sweep, one row each, ladder-ordered.

    From the ``metrics_pairwise`` rows that carry ``median_dbic``.  ``configured``
    marks the contest the sweep was built to answer.  Writes
    ``dbic_contests_<fit_method>_<stratum>.csv`` when ``write``.
    """
    sweep = figures.resolve(sweep, root)
    pw = sweep.metrics_pairwise
    if pw is None or pw.empty or 'median_dbic' not in pw.columns:
        return pd.DataFrame()
    sub = pw[pw['median_dbic'].notna() & (pw['fit_method'] == fit_method)]
    if 'stratum' in sub.columns:
        sub = sub[sub['stratum'] == stratum]
    keep = [c for c in ('model_a', 'model_b', 'n', 'frac_favor_a',
                        'frac_favor_b', 'median_dbic', 'configured')
            if c in sub.columns]
    df = sub[keep].drop_duplicates(['model_a', 'model_b']).copy()
    order = {name: i for i, name in enumerate(LADDER)}
    df['_a'] = df['model_a'].map(order).fillna(99)
    df['_b'] = df['model_b'].map(order).fillna(99)
    df = df.sort_values(['_a', '_b']).drop(columns=['_a', '_b'])
    if write and not df.empty:
        out = figures.subdir(sweep, 'tables') / f'dbic_contests_{fit_method}_{stratum}.csv'
        df.round(4).to_csv(out, index=False)
    return df


# --------------------------------------------------------------------------- #
# facts the prose is built from (derived from the artefacts, never assumed)
# --------------------------------------------------------------------------- #

def _facts(sweep):
    """What this sweep is, read off its tables and provenance."""
    sc = sweep.scalar
    prov = _provenance(sweep)
    cfg = prov.get('config', {}) or {}
    rungs = [r for r in LADDER if r in set(sc['algorithm'].unique())]
    datasets = sorted(str(d) for d in sc['dataset'].dropna().unique())
    n_obs = int(sc.groupby('dataset')['obs_id'].nunique().sum())
    methods = sorted(str(m) for m in sc['fit_method'].dropna().unique())
    has_truth = bool(figures.scored_refs(sweep, fit_method=PRIMARY))
    bp_free = bool('B_p' in sc.columns and sc['B_p'].notna().any())
    ks = sorted(int(k) for k in sc['k'].dropna().unique()) if 'k' in sc.columns else []
    noise = sorted(str(t) for t in sc['noise_model'].dropna().unique()) \
        if 'noise_model' in sc.columns else []
    x = ((cfg.get('dataset_opts') or {}).get('L23') or {}).get('X')
    return dict(rungs=rungs, datasets=datasets, n_obs=n_obs, methods=methods,
                has_truth=has_truth, bp_free=bp_free, ks=ks, noise=noise,
                wv_min=cfg.get('wv_min'), wv_max=cfg.get('wv_max'), l23_X=x,
                pace=('PACE' in datasets), l23=('L23' in datasets),
                pangaea=('PANGAEA' in datasets))


def _overview(sweep, f):
    rung_list = '\n'.join(f'#. ``{r}`` — {LABELS.get(r, r)}' for r in f['rungs'])
    bp = ('``B_p`` (the particulate backscattering ratio the robust backends '
          'need) is **free**, a sixth parameter with a uniform prior on '
          '[0.004, 0.05]' if f['bp_free'] else
          '``B_p`` is **fixed at 0.01** (k = 5): the 6–11-band in-situ spectra '
          'cannot afford a sixth parameter (rt_tests Q52)')
    win = ''
    if f['wv_min'] is not None and f['wv_max'] is not None:
        win = f' over {f["wv_min"]:g}–{f["wv_max"]:g} nm'
    noise = (', '.join(f'``{t}``' for t in f['noise']) or 'the dataset default')
    truth = ('This arm has **truth** for every retrieved component, so the '
             'rungs are scored against it.' if f['has_truth'] else
             'This arm has **no truth**: the spectra are real satellite '
             'radiances, so the page cannot say which physics is right, only how '
             'far each rung moves the retrieval and which rung the data prefer.')
    x_note = ''
    if f['l23'] and f['l23_X'] is not None:
        x_note = (f' The L23 spectra are the ``X={f["l23_X"]}`` realization — the '
                  f'HydroLight run **with** Raman scattering and chlorophyll '
                  f'fluorescence — so the elastic rungs are being asked to fit '
                  f'light they do not model.')
    return (
        f"This is the **RT ladder** for sweep ``{sweep.sweep_id}``: one IOP "
        f"parameterization, ``expb_pow`` (exponential CDOM/detrital absorption, "
        f"Bricaud phytoplankton absorption, power-law particulate backscatter), "
        f"fitted to {f['n_obs']} spectra from {', '.join(f['datasets'])}{win} "
        f"under {len(f['rungs'])} radiative-transfer models. Every row differs from "
        f"the next in the **forward model and nothing else** — same parameters, "
        f"same priors, same noise model ({noise}), same spectra — so a difference "
        f"between two rows is the physics. The rungs, from the analytic elastic "
        f"model to the full inelastic stack (all from the ``robust.rt`` package of "
        f"the retrieve-or-bust repository; see :doc:`/models`):\n\n{rung_list}\n\n"
        f"{bp}. Fit methods present: {', '.join(f'``{m}``' for m in f['methods'])}; "
        f"the ladder was sampled by MCMC on every arm, so the MCMC population is "
        f"the one read first below and χ² is shown alongside. {truth}{x_note} "
        f"The header stamps the code and config versions; every number is "
        f"regenerable from the persisted sweep artifacts under ``runs/``.")


def _limitations(f):
    """The decisions recorded in rt_tests.md that bound what the page can claim."""
    items = [
        ('**Viewing geometry is nadir everywhere.** θ_v = 0 and Δφ = 0 for every '
         'spectrum; only the solar zenith varies (0° on L23 by construction, '
         'computed per record from time and position on PANGAEA and PACE). The '
         'emulator was trained at nadir view only (retrieve-or-bust M3), so this '
         'is a stated limitation of the sweep, not a choice the data allowed.'),
        ('**CDOM fluorescence is driven by a proxy.** ``expb_pow`` retrieves the '
         'combined CDOM + detrital absorption ``a_dg``; the Hawes (1992) '
         'fluorescence kernel wants pure CDOM absorption. The last rung feeds it '
         '``a_cdom = 0.8 × a_dg`` — a **fixed CDOM fraction of 0.8** (rt_tests Q32) '
         '— and the kernel amplitude ``scale`` is fixed at 1.0. Nothing in the '
         'fit constrains either number.'),
        ('**The CDOM-fluorescence physics is unvalidated.** The ``robust.rt`` CDOM '
         'term is analytic only, its learned correction head is untrained, and no '
         'HydroLight truth with CDOM fluorescence exists (retrieve-or-bust M5/M6). '
         'The sweeps run on it as-is by decision (rt_tests Q41).'),
        ('**Downwelling irradiance is a packaged sky.** Every inelastic term takes '
         'its ``E_d(λ)`` from the ``ed_l23.npz`` table shipped with '
         '``robust.rt`` (the L23 HydroLight sky at the three tabulated solar '
         'zeniths), not from a per-scene atmosphere.'),
        ('**Learned inelastic corrections are off.** ``robust.rt`` ships trained '
         'δ_R / δ_F correction heads for its Raman and fluorescence terms; BING '
         'calls the forward model with ``corrections=False``, so the inelastic '
         'rungs use the **analytic** Raman and fluorescence terms (≈2 % rRMS '
         'against L23 X4, versus 0.34 % with the heads). The ladder measures the '
         'analytic physics.'),
        ('**The hybrid emulator is evaluated outside its trained ``B_p`` range** '
         'wherever ``B_p`` is free. It was trained on B_p ∈ [0.0103, 0.018]; the '
         'posteriors sit near 0.027 and essentially every hybrid fit raised the '
         'emulator\'s ``DomainWarning``. Accepted with this caveat rather than '
         'narrowing the prior or fixing ``B_p`` (rt_tests Q50, option c). The '
         'analytic ZTT rung is unaffected and is the control for this.'),
    ]
    if f['l23']:
        items.append(
            '**L23 X=4 truth lacks CDOM fluorescence, and its emission line is '
            'single-Gaussian.** HydroLight\'s inelastic run includes Raman and a '
            'single-Gaussian chlorophyll fluorescence line at 685 nm; the fits on '
            'the two fluorescence rungs used BING\'s double-Gaussian emission, and '
            'the last rung adds a CDOM-fluorescence source the truth never had. '
            'Rows of the last rung on L23 therefore carry the ``no_CDOMfl_truth`` '
            'caveat in the metrics tables, and the ``+Chl-fl`` rung is the '
            'like-for-like comparison with the truth\'s physics.')
    if f['pangaea']:
        items.append(
            '**PANGAEA is 6–11-band in-situ radiometry under a flat 10 % error '
            'model** (``insitu``; rt_tests Q53), and ``B_p`` is fixed there. '
            'ΔBIC scales with 1/σ², so the model-selection verdict on this arm is '
            'a statement under that assumed error as much as about the physics.')
    if f['pace']:
        items.append(
            '**PACE has no truth and its red bands are noisy.** The 100 spectra '
            'are real PACE OCI pixels from PAB\'s ``run1k`` matchups, 400–700 nm, '
            'weighted by the per-pixel ``Rrs_unc`` (5–6 % in the blue rising to '
            '30–44 % beyond 613 nm — the region where the inelastic signal lives). '
            'Everything on this page for PACE is model selection and closure, '
            'never accuracy.')
    items.append(
        '**Excluded from the leaderboard by design.** Five rungs of one algorithm '
        'are not five algorithms; folding them into the cross-sweep board would '
        'rank ``expb_pow`` against itself. The sweep is registered with '
        '``leaderboard: false`` and this page does not touch the landing page.')
    return '\n\n'.join(f'* {t}' for t in items)


def _headline_desc(f, pair, band):
    a, b = pair
    lead = ('This is the **headline figure for this arm**: ' if f['pace'] else
            'The truth-free view of the same ladder: ')
    return (
        f'{lead}for every spectrum both rungs retrieved, the fractional change of '
        f'the retrieved **decomposition** — ``a_ph``, ``a_dg`` and ``bb_p`` at '
        f'{band:g} nm — from the elastic hybrid ``{a}`` to the full inelastic stack '
        f'``{b}`` (MCMC posterior medians). Zero means the physics did not move '
        f'the retrieval; the dashed line is the median and the grey band the '
        f'16–84 % span. This needs no truth, so it is the one population '
        f'statement that can be made identically on synthetic, in-situ and '
        f'satellite spectra. It answers "how much does the forward model move a '
        f'retrieval", which is a different question from "which forward model is '
        f'right" — the truth-referenced sections '
        + ('below answer the second.' if f['has_truth'] else
           'cannot be built for this arm.'))


def _ladder_desc(fit_method, f):
    cells = ', '.join(f'``{c}({int(r)})``' for c, r in LADDER_CELLS)
    acc = (f' Accuracy cells are ``mae`` / ``bias`` / ``coverage68`` at {cells}: '
           f'fractional multiplicative errors in log space (0 = perfect; 0.10 ≈ '
           f'10 %), signed bias (> 0 = over-estimate), and the fraction of truths '
           f'inside the 68 % interval (nominal 0.68). A ``_caveat`` column names '
           f'rows whose truth does not contain the physics the rung models.'
           if f['has_truth'] else
           ' There is no truth on this arm, so the table carries fit quality '
           'only.')
    return (
        f'One row per rung, **{fit_method}** population, all strata. ``frac_ok`` '
        f'is the fraction of attempted spectra that produced a solution '
        f'(``poor_fit`` = χ²ᵥ above {records.CHI2NU_POOR_FIT:g}; '
        f'``out_of_scope`` = declined before fitting, red-peaked turbid spectra), '
        f'``chi2_nu_median`` the median reduced χ² of solutions, and '
        f'``rel_misfit_median`` the noise-model-free relative Rrs misfit.{acc} '
        f'Columns are defined on the :doc:`/reports/glossary` page. Read the '
        f'table down a column: a number that changes from rung to rung is the '
        f'physics; one that does not is the parameterization.')


# --------------------------------------------------------------------------- #
# the page
# --------------------------------------------------------------------------- #

def build(sweep_id, *, root=None, docs_root=None, pair=None,
          headline_ref=HEADLINE_REF):
    """Build ``reports/<sweep_id>/rt_ladder.rst`` and its display assets.

    ``pair`` is the ``(model_a, model_b)`` contest the page is read through;
    default :data:`ioptics.algorithms.registry.RT_DBIC_PAIR`.  Returns the page
    path.  Never touches the leaderboard or the landing page.
    """
    sweep = figures.load(sweep_id, root=root)
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS_SRC
    report_dir = docs_root / 'reports' / sweep_id
    report_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = figures.subdir(sweep, 'tables')
    pair = tuple(pair or registry.RT_DBIC_PAIR)
    present = set(sweep.scalar['algorithm'].unique())
    f = _facts(sweep)

    published = set()
    not_shown = []
    blocks = [rst.title(f'RT ladder — {sweep_id}'),
              rst.provenance_header(sweep_id, _provenance(sweep)),
              rst.section('Overview', _overview(sweep, f)),
              rst.section('What is held fixed, and what this page cannot claim',
                          _limitations(f))]

    # ---- headline: fractional change, truth-free ------------------------------
    have_pair = set(pair) <= present
    if have_pair:
        fc = figures.rt_fractional_change(
            sweep, model_a=pair[0], model_b=pair[1], ref=headline_ref,
            components=HEADLINE_COMPONENTS, fit_method=PRIMARY)
        band = headline_ref
        got = diagnostics.fractional_change_data(
            sweep.spectral, pair[0], pair[1], ref=headline_ref,
            components=HEADLINE_COMPONENTS, fit_method=PRIMARY)
        if got.get('band') is not None:
            band = got['band']
        ns = ', '.join(f'{c}: n = {n}' for c, n in got.get('n', {}).items())
        blocks.append(_fig_section(
            sweep, report_dir,
            f'How far the physics moves the retrieval — {band:g} nm',
            _pngs(fc),
            caption=(f'Fractional change in retrieved a_ph, a_dg and bb_p at '
                     f'{band:g} nm from ``{pair[0]}`` to ``{pair[1]}``, MCMC '
                     f'medians, one histogram per component ({ns}).'),
            desc=_headline_desc(f, pair, band), published=published))
        if not fc:
            not_shown.append(
                f'the fractional-change figure — ``{pair[0]}`` and ``{pair[1]}`` '
                f'share no retrieved band within 3 nm of {headline_ref:g} nm.')
    else:
        not_shown.append(
            f'the fractional-change headline — the configured contest '
            f'``{pair[0]}`` vs ``{pair[1]}`` is not fully present in this sweep.')

    # ---- consistency with PAB's Gordon-elastic fits (PACE arm; task 13) --------
    pab_csv = tables_dir / 'pab_consistency_summary.csv'
    if pab_csv.is_file():
        blocks.append(_table_section(
            sweep, report_dir, 'Consistency with PAB\'s fits of the same pixels',
            pab_csv, 'Elastic hybrid rung vs PAB run1k ExpBPow (Gordon), per shared parameter.',
            desc=('These spectra are the pixels PAB fitted in its ``run1k`` run with '
                  'BING\'s ``ExpBPow`` under the **Gordon** elastic forward model. The '
                  'elastic hybrid rung refits them under ``robust_hybrid`` with one '
                  'extra free parameter (``B_p``). Rows: Pearson correlation of the '
                  'posterior medians across pixels, the median and 16–84 % span of '
                  '(ours − PAB) in the parameter\'s own scale (``Adg``, ``Aph``, '
                  '``Bnw`` are log10 amplitudes), the derived-chlorophyll ratio, and '
                  'the largest difference between the observed spectra and variances '
                  'the two fitters were handed (a non-zero value there would mean the '
                  'pipelines did not see the same data). This is a gate, not a result: '
                  'agreement to within the elastic-model swap (``robust_hybrid`` sits '
                  '1.4–3.7 % above Gordon in Rrs on L23) plus the free ``B_p`` says the '
                  'PACE arm stands on the data PAB published from. Produced by '
                  '``ioptics/runs/prototypes/rt_tests/pab_consistency.py``.'),
            published=published))

    # ---- the ladder table -----------------------------------------------------
    for fm in (PRIMARY, SECONDARY):
        if fm not in f['methods']:
            continue
        df = ladder_table(sweep, fit_method=fm)
        if df.empty:
            continue
        blocks.append(_table_section(
            sweep, report_dir, f'The ladder — {fm}',
            tables_dir / f'rt_ladder_{fm}_all.csv',
            f'One row per RT rung ({fm}).', desc=_ladder_desc(fm, f),
            published=published))

    # ---- retrieved vs true, MCMC population -----------------------------------
    if f['has_truth']:
        scored = figures.scored_refs(sweep, fit_method=PRIMARY)
        for comp, ref, n in _plan_panels(scored):
            label = f'{comp}({ref:g})'
            blocks.append(_fig_section(
                sweep, report_dir, f'Retrieved vs. true — {label}',
                _pngs(figures.scatter_set(sweep, comp, ref=ref, fit_method=PRIMARY)),
                caption=(f'{label}, all rungs (MCMC medians) — at most {n} '
                         f'retrieval-truth pairs per rung.'),
                desc=(f'Retrieved vs. true **{label}**, one point per spectrum and '
                      f'rung, log–log. The solid line is 1:1, the dashed lines the '
                      f'±3× envelope. Five colours, one parameterization: where the '
                      f'clouds separate, the forward model is doing the separating.'),
                published=published))
            blocks.append(_fig_section(
                sweep, report_dir, f'Ratio distribution — {label}',
                _pngs(figures.ratio_hist(sweep, comp, ref=ref, fit_method=PRIMARY)),
                caption=f'Retrieved/true ratio buckets for {label}, per rung.',
                desc=('How each rung\'s population sits about 1:1; the vertical '
                      'rule marks ratio = 1.'),
                published=published))
        drew = False
        for ds in figures.sweep_datasets(sweep) or [None]:
            comps = figures.scored_components(sweep, dataset=ds, fit_method=PRIMARY)
            if not comps:
                continue
            drew = True
            names = ', '.join(f'``{c}``' for c, _, _ in comps)
            blocks.append(_fig_section(
                sweep, report_dir, f'Accuracy vs. wavelength — {ds or sweep_id}',
                _pngs(figures.accuracy_spectrum(sweep, dataset=ds, fit_method=PRIMARY)),
                caption=(f'Fractional multiplicative MAE against wavelength, one '
                         f'panel per component ({names}), all rungs overlaid; the '
                         f'dashed rule is 0.'),
                desc=('The same ``mae`` as the ladder table, at every band the '
                      'truth covers rather than at two reference wavelengths. This '
                      'is where a physics term shows its spectral signature: Raman '
                      'fills in from the blue, chlorophyll fluorescence acts near '
                      '685 nm, and a rung that is wrong everywhere is wrong for a '
                      'different reason.'),
                published=published))
        if not drew:
            not_shown.append('the accuracy-vs-wavelength figure — no component is '
                             'scored at five or more bands on this arm.')
    else:
        not_shown.append(
            'every retrieved-vs-true panel and the accuracy-vs-wavelength figure — '
            'this arm carries no truth, by design.')

    # ---- model selection ------------------------------------------------------
    if have_pair:
        a, b = pair
        for fm in (PRIMARY, SECONDARY):
            if fm not in f['methods']:
                continue
            cdf = figures.dbic_cdf_method(sweep, model_a=b, model_b=a, fit_method=fm)
            hist = figures.dbic_hist(sweep, model_a=b, model_b=a, fit_method=fm)
            blocks.append(_fig_section(
                sweep, report_dir, f'Model selection (ΔBIC) — {fm}',
                _pngs(cdf) + _pngs(hist),
                caption={'dbic_cdf': (f'Cumulative distribution of per-spectrum '
                                      f'ΔBIC = BIC(``{b}``) − BIC(``{a}``), {fm}.'),
                         'dbic_hist': (f'The same ΔBIC values as a histogram, {fm}; '
                                       f'the grey band is abs(ΔBIC) < 10.')},
                desc=(f'The contest these sweeps were built to answer: the full '
                      f'inelastic stack ``{b}`` (model A) against the elastic hybrid '
                      f'``{a}`` (model B), like-for-like within the **{fm}** '
                      f'population. Both rungs have the same number of parameters, '
                      f'so ΔBIC is a pure likelihood contest: **ΔBIC < 0 favours the '
                      f'inelastic physics**, and abs(ΔBIC) > 10 is the conventional '
                      f'"strong" threshold. The CDF gives the fraction either side; '
                      f'the histogram says whether that fraction is one population '
                      f'or two.'),
                published=published))
        dc = dbic_contests(sweep, fit_method=PRIMARY)
        if not dc.empty:
            blocks.append(_table_section(
                sweep, report_dir, 'Every pairwise contest',
                tables_dir / f'dbic_contests_{PRIMARY}_all.csv',
                f'Median ΔBIC and the fraction favouring each side, every pair ({PRIMARY}).',
                desc=('Every rung against every other rung, ``median_dbic`` = '
                      'median of BIC(``model_a``) − BIC(``model_b``) over the spectra '
                      'both fitted, and ``frac_favor_a`` the fraction with ΔBIC < 0. '
                      '``configured`` marks the headline contest above. Reading down '
                      'the ladder in order shows **which** physics term earns its '
                      'keep on this arm and which is a wash.'),
                published=published))
    else:
        not_shown.append('the ΔBIC panels — the configured pair is not in this sweep.')

    # ---- head-to-head and QC --------------------------------------------------
    if f['has_truth']:
        h2h = tables.head_to_head(sweep, fit_method=PRIMARY)
        if not h2h.empty:
            ties = int((h2h['verdict'] == 'indistinguishable').sum())
            blocks.append(_table_section(
                sweep, report_dir, f'Head-to-head verdicts — {PRIMARY}',
                tables_dir / f'head_to_head_{PRIMARY}_all.csv',
                f'Pairwise accuracy verdicts ({PRIMARY}, all strata).',
                desc=(f'Every pair of rungs judged on the spectra both retrieved: '
                      f'``delta_mae`` = ``mae(A) − mae(B)`` with its paired-bootstrap '
                      f'95 % interval, and a ``verdict`` that names a winner only '
                      f'when the interval excludes 0 **and** clears the practical '
                      f'floor of {metrics.PRACTICAL_MAE_FLOOR:.0%}. '
                      f'``indistinguishable`` means the data rule a material '
                      f'difference *out* — which for total absorption is the '
                      f'finding. {ties} of {len(h2h)} pairs are indistinguishable.'),
                published=published))
    for fm in (PRIMARY, SECONDARY):
        if fm not in f['methods']:
            continue
        tables.qc(sweep, fit_method=fm)
        if f['has_truth']:
            tables.accuracy(sweep, fit_method=fm)
            blocks.append(_table_section(
                sweep, report_dir, f'Accuracy — {fm}',
                tables_dir / f'accuracy_{fm}_all.csv',
                f'Ref-band accuracy, every scored component ({fm}, all strata).',
                desc=('The full per-(component, reference band) accuracy table the '
                      'ladder cells are drawn from, with ``median_ratio``, '
                      '``coverage95`` and the coverage verdicts. Columns are '
                      'defined on the :doc:`/reports/glossary` page.'),
                published=published))
        blocks.append(_table_section(
            sweep, report_dir, f'Quality control — {fm}',
            tables_dir / f'qc_{fm}_all.csv',
            f'Fit quality / closure per rung ({fm}).',
            desc=('``n_attempted``, the per-status fractions (kept apart on '
                  'purpose: ``out_of_scope`` is "declined before fitting", '
                  '``fit_failed`` is "the fitter returned nothing"), the median '
                  'reduced χ²ᵥ, the noise-model-free ``rel_misfit``, and the χ²ᵥ '
                  'closure split. Identical ``out_of_scope`` counts on every rung '
                  'are what make the ladder fair: the same spectra were declined '
                  'everywhere.'),
            published=published))

    blocks.append(_not_shown_section(not_shown))
    out = report_dir / f'{PAGE}.rst'
    out.write_text(rst.page(*blocks), encoding='utf-8')
    _prune_stale(report_dir, published, this_page=out.name)
    rst.ensure_glob_toctree(docs_root / 'reports' / 'index.rst')
    return out

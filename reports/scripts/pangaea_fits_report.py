"""Why the open-ocean IOP models fail on PANGAEA — the Task-1 diagnostics.

Produces every number and figure in ``reports/pangaea_fits_report.md``:

1. Reproduces the committed ``multi_L23_PANGAEA_v2`` bounded sweep (L23 in
   full + PANGAEA restricted to its 1 593 spectral-truth ids) if its tables
   are not already on disk, and reports the headline retrieval-success rates.
2. Re-scores every fit on statistics that owe nothing to the invented flat-5%
   error bar: chi^2_nu under 10%/15% floors and the median relative misfit.
3. Runs two PANGAEA-only control sweeps with the pipeline defects fixed —
   ``pangaea_fits_base`` (scipy's default evaluation budget) and
   ``pangaea_fits_maxfev`` (``maxfev = 40000``) — and counts exactly which
   rows move between statuses, naming the deterministic ``fit_failed`` floor.
4. Per-subdataset (cruise) coverage, and mean relative residual spectra for
   the 100%-converged-yet-0%-ok cruises against peak/band-matched controls.
5. Refits the red-peaked (>560 nm) PANGAEA subset with the turbid
   backscattering variants (``register_turbid``) at an equalized budget.
6. Prints the per-algorithm attribution table that splits the L23-PANGAEA
   gap into named, disjoint causes.
7. **Round 2** (after JXP's Task-1 answers): runs ``pangaea_fits_v2`` under
   the approved defaults — ``noise='insitu'`` (10% imputed fallback),
   ``maxfev=40000``, pre-fit ``out_of_scope`` — cross-checks the new
   headline against Round 1's prediction, and draws four example fits in
   the exemplar pages' clear→turbid ordering (including two from
   100%-``poor_fit`` cruises).

The Round-1 control sweeps (``pangaea_fits_base``/``_maxfev``) are reused
from disk; when re-created on a fresh machine they carry explicit overrides
(``maxfev``, ``fits_turbid=True``) so they reproduce the Round-1 semantics
under the Round-2 package defaults.

Run (ocean14 interpreter, Agg backend, no network)::

    /home/xavier/miniconda3/envs/ocean14/bin/python \\
        reports/scripts/pangaea_fits_report.py [--n-cores N]

Requires ``$OS_COLOR`` (PANGAEA V3 + L23 on disk) and **bing at or after
``main@f242b0e``** (``chisq_fit.fit(maxfev=...)`` + the ``Pow2``/``Pow2Flat``
turbid models). Sweep outputs land under ``$OS_COLOR/IOPtics/runs/`` and are
reused on re-runs, so the first invocation costs ~15-25 min at 16 cores and
later ones seconds. Figures go to ``reports/figures/*.png``. The script does
not modify any package source and never touches the committed sweep tables
except to create them when absent.
"""

import argparse
import importlib.util
import os
import sys
import time
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, '..', '..'))
sys.path.insert(0, _REPO)
_FIGDIR = os.path.join(_REPO, 'reports', 'figures')
os.makedirs(_FIGDIR, exist_ok=True)

from ioptics import config, io, metrics, run, style      # noqa: E402
from ioptics.algorithms import registry                  # noqa: E402
from ioptics.config import AlgorithmConfig               # noqa: E402
from ioptics.records import CHI2NU_POOR_FIT, RED_PEAK_NM  # noqa: E402

style.use_ioptics_style()

# --- configuration -----------------------------------------------------------
SWEEP_COMMITTED = 'multi_L23_PANGAEA_v2'   # the sweep the headline comes from
SWEEP_BASE      = 'pangaea_fits_base'      # PANGAEA only, defects fixed, default budget
SWEEP_MAXFEV    = 'pangaea_fits_maxfev'    # PANGAEA only, defects fixed, maxfev=40000
SWEEP_V2        = 'pangaea_fits_v2'        # Round 2: JXP-approved defaults —
                                           #   insitu noise (10% imputed),
                                           #   maxfev 40000, pre-fit out_of_scope
MAXFEV          = registry.TURBID_MAXFEV   # 40000 — same budget GLORIA settled on
ALGOS           = ('expb_pow', 'giop', 'gsm')
TURBID_ALGOS    = ('expb_pow', 'expb_pow2', 'expb_pow2flat', 'expb_powflex')
FLOORS          = (0.05, 0.10, 0.15)       # assumed fractional Rrs errors
REL_OK          = 0.10                     # relative-misfit "usable" threshold
FLAT_PCT        = 0.05                     # the sweep's pct:0.05 noise model
MIN_CRUISE_N    = 10                       # smallest subdataset worth a rate

_V2_YAML = os.path.join(_REPO, 'ioptics', 'runs', 'prototypes', 'multi_v2',
                        'run_v2.yaml')


def _load_build_v2():
    """Import the committed sweep driver (it lives outside the package)."""
    path = os.path.join(_REPO, 'ioptics', 'runs', 'prototypes', 'multi_v2',
                        'build_v2.py')
    spec = importlib.util.spec_from_file_location('build_v2', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sweep_done(sweep_id):
    try:
        d = io.sweep_dir(sweep_id)
    except RuntimeError:
        return False
    return (d / io.SCALAR_FILE).exists()


def ensure_committed_sweep(n_cores):
    """Stage-1+2 of ``build_v2 --bounded`` unless the tables already exist.

    **Round-2 note.** The tables this report's Round-1 sections read were
    produced under Round-1 code (registry ``maxfev`` default None, no pre-fit
    ``out_of_scope``, 5% PANGAEA fallback). ``build_v2`` always runs the
    *current* defaults, so a fresh re-run of this sweep on a clean machine
    reflects the Round-2 semantics instead — by design: JXP approved the new
    defaults and the committed sweep is due to be regenerated under them.
    """
    if _sweep_done(SWEEP_COMMITTED):
        print(f'[sweep] {SWEEP_COMMITTED}: tables on disk, reusing')
        return
    print(f'[sweep] {SWEEP_COMMITTED}: running bounded stage 1 (~10 min)')
    _load_build_v2().main(1, n_cores=n_cores, strict=False, bounded=True)
    metrics.compute(SWEEP_COMMITTED)


def ensure_pangaea_sweep(sweep_id, *, maxfev, n_cores, noise=None,
                         force_fit=True):
    """A PANGAEA-only rerun of the committed config, optionally re-budgeted.

    Everything else — the 1 593-id bound, the 400-750 nm trim, the seed — is
    taken verbatim from ``run_v2.yaml``. ``noise`` overrides the sweep noise
    model (Round 2 uses ``'insitu'``, which for PANGAEA falls back to the
    imputed flat fraction — 10% since 2026-08-10). ``force_fit=True`` pins
    ``fits_turbid`` on every algorithm so red-peaked spectra are *fitted*
    rather than declined — the Round-1 behaviour, which the Round-1 sweeps
    (``pangaea_fits_base``/``_maxfev``) need for reproducibility now that the
    package declines them by default, and which the diagnostics here want
    anyway (a declined fit has no residual to study). ``maxfev=None`` is an
    explicit override to scipy's own default budget (the registry now seeds
    40 000).
    """
    if _sweep_done(sweep_id):
        print(f'[sweep] {sweep_id}: tables on disk, reusing')
        return
    ids = _load_build_v2().pangaea_truth_ids()
    cfg = config.load(_V2_YAML)
    cfg.sweep_id = sweep_id
    cfg.datasets = ['PANGAEA']
    if noise is not None:
        cfg.noise_model = noise
    overrides = {'maxfev': int(maxfev) if maxfev else None}
    if force_fit:
        overrides['fits_turbid'] = True
    cfg.algorithms = [AlgorithmConfig(name=n, overrides=dict(overrides))
                      for n in ALGOS]
    print(f'[sweep] {sweep_id}: fitting {len(ids)} PANGAEA ids x {ALGOS} '
          f'(noise={cfg.noise_model}, maxfev={maxfev or "scipy default"}, '
          f'force_fit={force_fit})')
    run.run_sweep(cfg, obs_ids={'PANGAEA': ids}, n_cores=n_cores, strict=False)


# --- per-fit statistics off the spectral table -------------------------------

def rel_misfit_per_fit(spectral):
    """Median |model-obs|/obs per (dataset, algorithm, obs_id) row."""
    cols = ['dataset', 'algorithm', 'obs_id', 'wavelength', 'value']
    mod = spectral.loc[spectral['component'] == 'Rrs_model', cols]
    obs = (spectral.loc[spectral['component'] == 'Rrs_obs', cols]
           .rename(columns={'value': 'obs'}))
    both = mod.merge(obs, on=cols[:4])
    good = (both['obs'] > 0) & np.isfinite(both['value']) & np.isfinite(both['obs'])
    both = both[good]
    rel = (both['value'] - both['obs']).abs() / both['obs']
    return (rel.groupby([both['dataset'], both['algorithm'], both['obs_id']])
               .median().rename('rel_misfit'))


def peak_and_bands_per_obs(spectral):
    """Observed-Rrs peak wavelength + finite band count per (dataset, obs)."""
    obs = spectral[spectral['component'] == 'Rrs_obs']
    # every algorithm persisted the same observation; keep one copy per band
    one = obs.drop_duplicates(subset=['dataset', 'obs_id', 'wavelength'])
    fin = one[np.isfinite(one['value'])]
    grp = fin.groupby(['dataset', 'obs_id'])
    peak = (fin.loc[grp['value'].idxmax()]
            .set_index(['dataset', 'obs_id'])['wavelength'].rename('peak_nm'))
    nb = grp.size().rename('n_bands_obs')
    npos = ((fin['value'] > 0)
            .groupby([fin['dataset'], fin['obs_id']]).sum()
            .rename('n_pos_bands'))
    return pd.concat([peak, nb, npos], axis=1)


def algo_k(sc, algo):
    """The parameter count ``k`` an algorithm ran with, from its scored rows.

    Read from converged rows rather than trusting the failed rows' column —
    the committed sweep predates the ``n_bands``/``k`` fix and carries 0 there.
    """
    g = sc[(sc['algorithm'] == algo) & (sc['status'] != 'fit_failed')]
    return int(g['k'].mode().iloc[0])


def annotate(scalar, spectral):
    """Scalar table + rel_misfit + peak wavelength + observed band counts."""
    sc = scalar[scalar['fit_method'] == 'chisq'].copy()
    rel = rel_misfit_per_fit(spectral)
    sc = sc.merge(rel.reset_index(), on=['dataset', 'algorithm', 'obs_id'],
                  how='left')
    sc = sc.merge(peak_and_bands_per_obs(spectral).reset_index(),
                  on=['dataset', 'obs_id'], how='left')
    return sc


# --- 1a: re-score on noise-model-free statistics ------------------------------

def rescore_table(sc):
    """ok-rates under chi^2_nu floors and the relative-misfit criterion.

    The sweep weighted every fit by an assumed flat ``FLAT_PCT`` error, so
    chi^2_nu under an f-floor is exactly ``chi2_nu * (FLAT_PCT / f)**2`` — no
    refit needed.
    """
    rows = []
    for (ds, algo), g in sc.groupby(['dataset', 'algorithm']):
        n = len(g)
        conv = g['status'] != 'fit_failed'
        row = {'dataset': ds, 'algorithm': algo, 'n': n,
               'frac_converged': conv.mean(),
               'rel_misfit_median_conv': g.loc[conv, 'rel_misfit'].median()}
        for f in FLOORS:
            scaled = g['chi2_nu'] * (FLAT_PCT / f) ** 2
            row[f'ok_chi2_floor{int(f*100):02d}'] = (
                (conv & (scaled <= CHI2NU_POOR_FIT)).mean())
        for thr in (REL_OK, 0.15):
            row[f'ok_rel{int(thr*100):02d}'] = (
                (conv & (g['rel_misfit'] <= thr)).mean())
        rows.append(row)
    return pd.DataFrame(rows)


def fig_rescoring(tab):
    crits = [('ok_chi2_floor05', 'chi2_nu<=5 @ 5% (published)'),
             ('ok_chi2_floor10', 'chi2_nu<=5 @ 10% floor'),
             ('ok_chi2_floor15', 'chi2_nu<=5 @ 15% floor'),
             ('ok_rel10', 'rel misfit <= 10%'),
             ('ok_rel15', 'rel misfit <= 15%')]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, ds in zip(axes, ('L23', 'PANGAEA')):
        sub = tab[tab['dataset'] == ds]
        x = np.arange(len(crits))
        width = 0.26
        for i, algo in enumerate(ALGOS):
            r = sub[sub['algorithm'] == algo].iloc[0]
            vals = [r[c] for c, _ in crits]
            ax.bar(x + (i - 1) * width, vals, width,
                   color=style.algo_color(algo), label=algo)
        ax.set_xticks(x)
        ax.set_xticklabels([lbl for _, lbl in crits], rotation=25, ha='right',
                           fontsize=8)
        ax.set_title(ds)
        ax.set_ylim(0, 1.02)
        ax.axhline(1.0, color='0.8', lw=0.8, zorder=0)
    axes[0].set_ylabel('fraction of attempted spectra "usable"')
    axes[1].legend(frameon=False)
    fig.suptitle('Retrieval success is a statement about the assumed error bar')
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'pangaea_rescoring.png'), dpi=130)
    plt.close(fig)


def fig_misfit_cdf(sc):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for ds, lsty in (('L23', '--'), ('PANGAEA', '-')):
        for algo in ALGOS:
            g = sc[(sc['dataset'] == ds) & (sc['algorithm'] == algo)
                   & (sc['status'] != 'fit_failed')]
            v = np.sort(g['rel_misfit'].dropna().values)
            if not len(v):
                continue
            ax.plot(v, np.arange(1, len(v) + 1) / len(v), lsty,
                    color=style.algo_color(algo),
                    label=f'{ds} {algo} (n={len(v)})')
    ax.axvline(REL_OK, color='0.4', lw=0.8, ls=':')
    ax.text(REL_OK * 1.05, 0.05, '10%', color='0.4')
    # the misfit the published chi2_nu<=5 @ 5% cut corresponds to (~11% RMS)
    ax.axvline(FLAT_PCT * np.sqrt(CHI2NU_POOR_FIT), color='crimson', lw=0.8,
               ls=':')
    ax.set_xscale('log')
    ax.set_xlabel('median relative Rrs misfit per fit')
    ax.set_ylabel('CDF over converged fits')
    ax.set_title('The noise-model-free statistic: how far do fits actually miss?')
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'pangaea_misfit_cdf.png'), dpi=130)
    plt.close(fig)


# --- 1b: defect fixes, budget, and the deterministic floor --------------------

def movement_table(base, fixed):
    """Status transition counts per algorithm between two PANGAEA runs."""
    key = ['algorithm', 'obs_id']
    m = (base[key + ['status']].rename(columns={'status': 'status_base'})
         .merge(fixed[key + ['status']].rename(columns={'status': 'status_maxfev'}),
                on=key))
    return (m.groupby(['algorithm', 'status_base', 'status_maxfev'])
             .size().rename('n').reset_index())


def classify_fit_failed(g, k):
    """Split fit_failed rows into named deterministic causes."""
    under = g['n_bands_obs'] <= k
    nonpos = ~under & (g['n_pos_bands'] < g['n_bands_obs'])
    other = ~under & ~nonpos
    return {'underdetermined (n_bands <= k)': int(under.sum()),
            'has non-positive Rrs bands': int(nonpos.sum()),
            'other': int(other.sum())}


def fig_fit_failed(base, fixed):
    fig, axes = plt.subplots(1, len(ALGOS), figsize=(11, 3.8), sharey=True)
    labels = ['underdetermined (n_bands <= k)', 'has non-positive Rrs bands',
              'other']
    colors = ['#7b3294', '#c2a5cf', '#a6dba0']
    for ax, algo in zip(axes, ALGOS):
        counts = []
        for name, sc in (('default\nbudget', base), ('maxfev\n40000', fixed)):
            k = algo_k(sc, algo)
            ff = sc[(sc['algorithm'] == algo) & (sc['status'] == 'fit_failed')]
            counts.append(classify_fit_failed(ff, k))
        bottoms = np.zeros(2)
        for lbl, c in zip(labels, colors):
            vals = np.array([cnt[lbl] for cnt in counts], dtype=float)
            ax.bar(range(2), vals, 0.6, bottom=bottoms, color=c, label=lbl)
            bottoms += vals
        ax.set_xticks(range(2))
        ax.set_xticklabels(['default\nbudget', 'maxfev\n40000'])
        ax.set_title(algo)
    axes[0].set_ylabel('fit_failed rows (of 1593)')
    axes[-1].legend(frameon=False, fontsize=8)
    fig.suptitle('fit_failed decomposes into a deterministic floor + a budget artifact')
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'pangaea_fitfailed_decomposition.png'),
                dpi=130)
    plt.close(fig)


# --- 1c: cruise-level systematics ---------------------------------------------

def cruise_map():
    """PANGAEA obs_id -> (family, cruise, contributor).

    ``contributor`` is the per-record provenance the tidy tables *do* carry —
    the PI/instrument-group that supplied the spectra (NOMAD inherits it from
    SeaBASS). It is the closest thing to a processing-chain key available
    without going back to the original NOMAD/SeaBASS documentation.
    """
    from ocpy.insitu import pangaea
    rrs = pangaea.load('rrs')
    return rrs[['dataset', 'subdataset', 'contributor']].rename(
        columns={'dataset': 'family', 'subdataset': 'cruise'})


def contributor_table(sc, cmap, *, algo='giop', min_n=20):
    """Coverage per *contributor* (PI / instrument group), across cruises."""
    p = sc[(sc['dataset'] == 'PANGAEA') & (sc['algorithm'] == algo)].merge(
        cmap, left_on='obs_id', right_index=True, how='left')
    p['contributor'] = p['contributor'].astype(str).str.slice(0, 40)
    rows = []
    for contrib, g in p.groupby('contributor'):
        if len(g) < min_n:
            continue
        conv = g['status'] != 'fit_failed'
        rows.append({'contributor': contrib, 'n': len(g),
                     'n_cruises': g['cruise'].nunique(),
                     'frac_converged': conv.mean(),
                     'frac_ok': (g['status'] == 'ok').mean(),
                     'rel_misfit_median': g.loc[conv, 'rel_misfit'].median(),
                     'peak_nm_median': g['peak_nm'].median()})
    return pd.DataFrame(rows).sort_values('frac_ok').reset_index(drop=True)


def cruise_table(sc, cmap):
    p = sc[sc['dataset'] == 'PANGAEA'].merge(
        cmap, left_on='obs_id', right_index=True, how='left')
    rows = []
    for (algo, cruise), g in p.groupby(['algorithm', 'cruise']):
        if len(g) < MIN_CRUISE_N:
            continue
        conv = g['status'] != 'fit_failed'
        rows.append({
            'algorithm': algo, 'cruise': cruise, 'n': len(g),
            'frac_converged': conv.mean(),
            'frac_ok': (g['status'] == 'ok').mean(),
            'frac_poor_fit': (g['status'] == 'poor_fit').mean(),
            'rel_misfit_median': g.loc[conv, 'rel_misfit'].median(),
            'peak_nm_median': g['peak_nm'].median(),
            'n_bands_median': g['n_bands_obs'].median()})
    return pd.DataFrame(rows), p


def fig_cruise_rates(ct):
    """ok-rate per cruise for giop (the most permissive algorithm)."""
    sub = ct[ct['algorithm'] == 'giop'].sort_values('frac_ok')
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(sub) + 1.5))
    y = np.arange(len(sub))
    ax.barh(y, sub['frac_ok'], color='#1b7837', label='ok')
    ax.barh(y, sub['frac_poor_fit'], left=sub['frac_ok'],
            color='#fdb863', label='poor_fit')
    ax.set_yticks(y)
    ax.set_yticklabels([f"{c}  (n={n}, {b:.0f} bands, peak {p:.0f} nm)"
                        for c, n, b, p in zip(sub['cruise'], sub['n'],
                                              sub['n_bands_median'],
                                              sub['peak_nm_median'])],
                       fontsize=7)
    ax.set_xlabel('fraction of cruise spectra (giop)')
    ax.set_xlim(0, 1.02)
    ax.legend(frameon=False, fontsize=8, loc='lower right')
    ax.set_title(f'Per-cruise coverage (subdatasets with n >= {MIN_CRUISE_N})')
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'pangaea_cruise_rates.png'), dpi=130)
    plt.close(fig)


def mean_residual_spectrum(spectral, obs_ids, algo):
    """Mean relative residual (model-obs)/obs vs wavelength over a cruise."""
    sp = spectral[(spectral['dataset'] == 'PANGAEA')
                  & (spectral['algorithm'] == algo)
                  & (spectral['obs_id'].isin(obs_ids))]
    cols = ['obs_id', 'wavelength', 'value']
    mod = sp.loc[sp['component'] == 'Rrs_model', cols]
    obs = (sp.loc[sp['component'] == 'Rrs_obs', cols]
           .rename(columns={'value': 'obs'}))
    both = mod.merge(obs, on=cols[:2])
    both = both[(both['obs'] > 0) & np.isfinite(both['value'])]
    both['rel'] = (both['value'] - both['obs']) / both['obs']
    grp = both.groupby('wavelength')['rel']
    out = pd.DataFrame({'mean': grp.mean(), 'n': grp.size()})
    return out[out['n'] >= max(3, len(obs_ids) // 3)]


def fig_cruise_residuals(spectral, groups, algo='giop'):
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for (label, ids, color, lsty) in groups:
        res = mean_residual_spectrum(spectral, ids, algo)
        if res.empty:
            continue
        ax.plot(res.index, res['mean'], lsty, color=color,
                label=f'{label} (n={len(ids)})')
    ax.axhline(0.0, color='0.6', lw=0.8)
    ax.set_xlabel('wavelength [nm]')
    ax.set_ylabel('mean (Rrs_model - Rrs_obs) / Rrs_obs')
    ax.set_title(f'Cruise-mean relative residual spectra ({algo})')
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'pangaea_cruise_residuals.png'), dpi=130)
    plt.close(fig)


# --- 1d: turbid variants on the red-peaked subset ------------------------------

def turbid_comparison(red_ids, n_cores):
    """Refit the red-peaked subset with the turbid bbp variants.

    Cached as a parquet under the runs root — the ~750 maxfev-40000 refits are
    the script's slowest uncached stage and are fully deterministic.
    """
    from ioptics import prep
    import dataclasses

    cache = io.sweep_dir('pangaea_fits_turbid', create=True) / 'variants.parquet'
    if cache.exists():
        print(f'[1d] reusing cached turbid refits: {cache}')
        return pd.read_parquet(cache)

    registry.register_turbid()
    # Equalize the budget on the baseline too, or the contest measures maxfev
    # — and force-fit: this comparison exists to *study* red-peaked fits, so
    # the pre-fit out_of_scope guard must not decline them for the baseline
    # (the turbid variants claim turbid scope already). The force-fit spec is
    # a LOCAL variable, never registered: the first Round-2 run registered it
    # over 'expb_pow' and the pollution leaked into the pangaea_fits_v2 sweep
    # (its expb_pow force-fitted red-peaked spectra while giop/gsm declined
    # them — caught because its out_of_scope count was 159, not 188, and the
    # sweep's own provenance.yaml recorded `fits_turbid: true`).
    base = registry.get('expb_pow')
    forced = {'expb_pow': dataclasses.replace(base, maxfev=MAXFEV,
                                              fits_turbid=True)}

    cfg = config.load(_V2_YAML)
    records = prep.prep_dataset('PANGAEA', obs_ids=red_ids,
                                noise=cfg.noise_model, seed=cfg.seed,
                                wv_min=cfg.wv_min, wv_max=cfg.wv_max,
                                n_cores=n_cores)
    rows = []
    for name in TURBID_ALGOS:
        spec = forced.get(name) or registry.get(name)
        results = run.run_batch(spec, records, fit_method='chisq',
                                n_cores=n_cores, strict=False)
        for rec, res in zip(records, results):
            row = {'algorithm': name, 'obs_id': rec.obs_id,
                   'status': res.status,
                   'chi2_nu': res.stats.get('chi2_nu', np.nan)}
            comp = res.components.get('Rrs_model')
            if comp is not None:
                row['rel_misfit'] = metrics.rel_misfit(comp.med, rec.Rrs)
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(cache, index=False)
    return out


def fig_turbid(tt):
    piv_chi = tt.pivot(index='obs_id', columns='algorithm', values='chi2_nu')
    piv_rel = tt.pivot(index='obs_id', columns='algorithm', values='rel_misfit')
    common = piv_chi.dropna().index
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))
    x = np.arange(len(TURBID_ALGOS))
    for ax, piv, label in ((axes[0], piv_chi, 'median chi2_nu'),
                           (axes[1], piv_rel, 'median relative misfit')):
        med = piv.loc[common, list(TURBID_ALGOS)].median()
        ax.bar(x, med.values, 0.6,
               color=[style.algo_color(a) for a in TURBID_ALGOS])
        ax.set_xticks(x)
        ax.set_xticklabels(TURBID_ALGOS, rotation=20, ha='right', fontsize=8)
        ax.set_ylabel(label)
        for xi, v in zip(x, med.values):
            ax.text(xi, v, f'{v:.3g}', ha='center', va='bottom', fontsize=8)
    fig.suptitle(f'Turbid bbp variants on the red-peaked PANGAEA subset '
                 f'(paired on {len(common)} commonly-converged spectra)')
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'pangaea_turbid_variants.png'), dpi=130)
    plt.close(fig)


# --- Round 3: the field's operational criterion (GIOP-DC validity) -------------

def giop_dc_validity(spectral, scalar, *, drrs_max=0.33, wv=(400.0, 600.0)):
    """Score every fit with NASA's operational GIOP-DC validity test.

    The NASA standard IOP products accept a Levenberg-Marquardt solution as
    valid when the retrieved components sit within physical bounds and the
    **mean absolute relative Rrs difference over 400-600 nm is <= 33%**
    (GIOP ATBD v1.0, McKinna & Werdell 2024, doi:10.5067/ZGBW3QECROJ2,
    Eqs. 11-15) — a noise-model-free misfit statistic, not a chi-squared
    against an error bar. BING's amplitudes are fit in log10 space, so the
    lower physical bounds (>= -0.05 a_w / b_bw) hold by construction and the
    binding test for our fits is the dRrs criterion on converged rows.

    Returns a DataFrame of per-algorithm validity fractions over all
    attempted PANGAEA rows.
    """
    cols = ['dataset', 'algorithm', 'obs_id', 'wavelength', 'value']
    sp = spectral[(spectral['dataset'] == 'PANGAEA')
                  & spectral['wavelength'].between(*wv)]
    mod = sp.loc[sp['component'] == 'Rrs_model', cols]
    obs = (sp.loc[sp['component'] == 'Rrs_obs', cols]
           .rename(columns={'value': 'obs'}))
    both = mod.merge(obs, on=cols[:4])
    both = both[(both['obs'] > 0) & np.isfinite(both['value'])]
    rel = (both['value'] - both['obs']).abs() / both['obs']
    drrs = (rel.groupby([both['algorithm'], both['obs_id']])
               .mean().rename('dRrs'))

    sc = scalar[(scalar['dataset'] == 'PANGAEA')
                & (scalar['fit_method'] == 'chisq')]
    sc = sc.merge(drrs.reset_index(), on=['algorithm', 'obs_id'], how='left')
    rows = []
    for algo, g in sc.groupby('algorithm'):
        conv = g['status'] != 'fit_failed'
        rows.append({'algorithm': algo, 'n': len(g),
                     'frac_converged': conv.mean(),
                     'dRrs_median': g.loc[conv, 'dRrs'].median(),
                     f'valid_dRrs<={drrs_max:.0%}':
                         (conv & (g['dRrs'] <= drrs_max)).mean()})
    return pd.DataFrame(rows)


# --- example fits (Round 2) ----------------------------------------------------

def pick_example_ids(ann, cmap):
    """Four representative observations, clear -> turbid (deterministic).

    1. a clear, blue-peaked ``ok`` fit (best giop rel. misfit, >= 10 bands);
    2. the *near-miss* face of the scoring artifact: the lowest-misfit
       ``poor_fit`` row of ``nomad_en372`` (100%-converged, never ``ok``);
    3. the uniform-moderate-misfit face: the median-misfit spectrum of
       ``nomad_oceania2000`` (another never-ok cruise, from the prompt);
    4. a red-peaked turbid spectrum: the median-misfit ``nomad_wfs0511`` row.
    """
    g = ann[ann['algorithm'] == 'giop'].merge(
        cmap, left_on='obs_id', right_index=True, how='left')

    clear = g[(g['status'] == 'ok') & (g['peak_nm'] < 500)
              & (g['n_bands_obs'] >= 10)].sort_values('rel_misfit')
    picks = [('clear, scored ok', int(clear['obs_id'].iloc[0]))]

    for label, cruise, which in (
            ('never-ok cruise, near miss', 'nomad_en372', 'best'),
            ('never-ok cruise, moderate miss', 'nomad_oceania2000', 'median'),
            ('turbid (red-peaked)', 'nomad_wfs0511', 'median')):
        sub = g[(g['cruise'] == cruise)
                & (g['status'] != 'fit_failed')].sort_values('rel_misfit')
        row = sub.iloc[0] if which == 'best' else sub.iloc[len(sub) // 2]
        picks.append((f'{label} ({cruise})', int(row['obs_id'])))
    return picks


def fig_example_fits(spectral, scalar, picks):
    from ioptics import diagnostics

    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    for ax, (label, obs_id) in zip(axes.ravel(), picks):
        d = diagnostics.rrs_fit_data(spectral, scalar, obs_id,
                                     dataset='PANGAEA', fit_method='chisq')
        ax.plot(d['wave'], 1e3 * np.asarray(d['rrs']), 'o-', color='0.2',
                ms=4, lw=1.0, label='observed', zorder=5)
        for algo in ALGOS:
            m = d['models'].get(algo)
            if m is None or not len(m['wave']):
                continue
            ax.plot(m['wave'], 1e3 * np.asarray(m['rrs']), '-',
                    color=style.algo_color(algo), lw=1.4,
                    label=f"{algo} (rel {m['rel_misfit']:.0%}, {m['status']})")
        ax.set_title(f"{label} — id {obs_id}, peak {d['peak_nm']:.0f} nm",
                     fontsize=9)
        ax.set_xlabel('wavelength [nm]')
        ax.set_ylabel(r'Rrs [$10^{-3}\,$sr$^{-1}$]')
        ax.legend(frameon=False, fontsize=7)
    fig.suptitle('Example PANGAEA fits, clear -> turbid '
                 '(models from the maxfev-equalized force-fit rerun)')
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'pangaea_example_fits.png'), dpi=130)
    plt.close(fig)


# --- the attribution ----------------------------------------------------------

BUCKETS = ('ok (chi2_nu <= 5 @ 5%)',
           'underdetermined (n_bands <= k)',
           'other fit_failed',
           'out_of_scope (red peak, poor fit)',
           'scoring artifact (poor_fit, rel misfit <= 10%)',
           'genuine misfit (poor_fit, rel misfit > 10%)')


def attribution(sc):
    """Disjoint named causes per algorithm, summing to every attempted row."""
    out = {}
    for algo, g in sc[sc['dataset'] == 'PANGAEA'].groupby('algorithm'):
        k = algo_k(sc, algo)
        ff = g['status'] == 'fit_failed'
        under = ff & (g['n_bands_obs'] <= k)
        near = (g['status'] == 'poor_fit') & (g['rel_misfit'] <= REL_OK)
        buckets = {
            BUCKETS[0]: (g['status'] == 'ok').sum(),
            BUCKETS[1]: under.sum(),
            BUCKETS[2]: (ff & ~under).sum(),
            BUCKETS[3]: (g['status'] == 'out_of_scope').sum(),
            BUCKETS[4]: near.sum(),
            BUCKETS[5]: ((g['status'] == 'poor_fit') & ~near).sum(),
        }
        assert sum(buckets.values()) == len(g)
        out[algo] = {k: int(v) for k, v in buckets.items()}
    return out


def fig_attribution(attr, n_total):
    colors = ['#1b7837', '#7b3294', '#c2a5cf', '#d7301f', '#fdb863', '#8c510a']
    fig, ax = plt.subplots(figsize=(9, 3.6))
    y = np.arange(len(ALGOS))
    for yi, algo in zip(y, ALGOS):
        left = 0.0
        for lbl, c in zip(BUCKETS, colors):
            frac = attr[algo][lbl] / n_total
            ax.barh(yi, frac, 0.6, left=left, color=c,
                    label=lbl if yi == 0 else None)
            if frac > 0.04:
                ax.text(left + frac / 2, yi, f'{frac:.0%}', ha='center',
                        va='center', fontsize=8, color='white')
            left += frac
    ax.set_yticks(y)
    ax.set_yticklabels(ALGOS)
    ax.set_xlim(0, 1)
    ax.set_xlabel(f'fraction of the {n_total} attempted PANGAEA spectra')
    ax.legend(frameon=False, fontsize=7, ncol=2, loc='upper center',
              bbox_to_anchor=(0.5, -0.18))
    ax.set_title('Attribution of the PANGAEA non-retrieval gap '
                 '(maxfev-equalized rerun)')
    fig.tight_layout()
    fig.savefig(os.path.join(_FIGDIR, 'pangaea_attribution.png'), dpi=130)
    plt.close(fig)


# --- driver --------------------------------------------------------------------

def _rule(title):
    print('\n' + '=' * 72 + f'\n{title}\n' + '=' * 72)


def main(n_cores=8):
    t0 = time.time()

    _rule('sweeps')
    ensure_committed_sweep(n_cores)
    ensure_pangaea_sweep(SWEEP_BASE, maxfev=None, n_cores=n_cores)
    ensure_pangaea_sweep(SWEEP_MAXFEV, maxfev=MAXFEV, n_cores=n_cores)

    sp_c, sc_c = io.read_results(SWEEP_COMMITTED)
    sp_b, sc_b = io.read_results(SWEEP_BASE)
    sp_m, sc_m = io.read_results(SWEEP_MAXFEV)

    _rule('headline reproduction (committed sweep, chi2_nu <= 5 @ flat 5%)')
    head = (sc_c.groupby(['dataset', 'algorithm'])['status']
                .value_counts(normalize=True).unstack(fill_value=0.0))
    print(head.round(4).to_string())

    _rule('defect fixes alone move no statuses (base rerun vs committed)')
    key = ['algorithm', 'obs_id']
    both = (sc_c[sc_c['dataset'] == 'PANGAEA'][key + ['status']]
            .rename(columns={'status': 'committed'})
            .merge(sc_b[key + ['status']].rename(columns={'status': 'base'}),
                   on=key))
    moved = both[both['committed'] != both['base']]
    print(f'rows with a different status: {len(moved)} of {len(both)}')
    if len(moved):
        print(moved.groupby(['algorithm', 'committed', 'base']).size())

    # annotate all three runs with the noise-model-free statistics
    ann_c = annotate(sc_c, sp_c)
    ann_b = annotate(sc_b, sp_b)
    ann_m = annotate(sc_m, sp_m)

    _rule('1a: re-scored ok-rates (committed sweep)')
    tab = rescore_table(ann_c)
    print(tab.round(4).to_string(index=False))
    fig_rescoring(tab)
    fig_misfit_cdf(ann_c)

    _rule('1b: status movement, default budget -> maxfev 40000 (PANGAEA)')
    mv = movement_table(ann_b, ann_m)
    print(mv[mv['status_base'] != mv['status_maxfev']].to_string(index=False))
    print('\nnew status rates under maxfev=40000:')
    print(ann_m.groupby('algorithm')['status']
          .value_counts(normalize=True).unstack(fill_value=0.0)
          .round(4).to_string())
    print('\nfit_failed decomposition (default budget):')
    for algo in ALGOS:
        ff = ann_b[(ann_b['algorithm'] == algo)
                   & (ann_b['status'] == 'fit_failed')]
        print(f'  {algo:<10s} {classify_fit_failed(ff, algo_k(ann_b, algo))}')
    print('fit_failed decomposition (maxfev=40000):')
    for algo in ALGOS:
        ff = ann_m[(ann_m['algorithm'] == algo)
                   & (ann_m['status'] == 'fit_failed')]
        print(f'  {algo:<10s} {classify_fit_failed(ff, algo_k(ann_m, algo))}')
    fig_fit_failed(ann_b, ann_m)

    _rule('1c: per-cruise coverage (maxfev rerun)')
    cmap = cruise_map()
    ct, p_ann = cruise_table(ann_m, cmap)
    show = (ct[ct['algorithm'] == 'giop']
            .sort_values('frac_ok')
            [['cruise', 'n', 'frac_converged', 'frac_ok', 'rel_misfit_median',
              'peak_nm_median', 'n_bands_median']])
    print(show.round(3).to_string(index=False))
    fig_cruise_rates(ct)

    # residual spectra: every all-converged-zero-ok cruise vs matched controls
    giop = ct[ct['algorithm'] == 'giop']
    anom = giop[(giop['frac_converged'] >= 0.95) & (giop['frac_ok'] <= 0.05)]
    ctrl = giop[giop['frac_ok'] >= 0.5]
    print('\nanomalous (converged, never ok):', list(anom['cruise']))
    print('controls (>=50% ok):', list(ctrl['cruise']))

    # One level up from cruises: the per-record `contributor` (PI/instrument
    # group, inherited from SeaBASS via NOMAD) is the only processing-chain
    # provenance the tidy tables carry — and coverage stratifies on it.
    print('\nper-contributor coverage (giop, n >= 20):')
    print(contributor_table(ann_m, cmap).round(3).to_string(index=False))
    # A readable subset for the figure: the three cruises the reconnaissance
    # named, plus the purest scoring-artifact case (lowest median misfit among
    # the never-ok cruises) and the worst one, against two high-ok controls.
    named = ['nomad_oceania1998', 'nomad_oceania2000', 'nomad_i8si9n']
    anom_sorted = anom.sort_values('rel_misfit_median')
    pick = [c for c in named if c in set(anom['cruise'])]
    for c in (anom_sorted['cruise'].iloc[0], anom_sorted['cruise'].iloc[-1]):
        if c not in pick:
            pick.append(c)
    groups = []
    palette = plt.get_cmap('tab10')
    pg = p_ann[p_ann['algorithm'] == 'giop']
    for i, cruise in enumerate(pick):
        ids = pg.loc[pg['cruise'] == cruise, 'obs_id']
        groups.append((cruise, list(ids), palette(i), '-'))
    for j, cruise in enumerate(ctrl.sort_values('frac_ok', ascending=False)
                               ['cruise'].head(2)):
        ids = pg.loc[pg['cruise'] == cruise, 'obs_id']
        groups.append((cruise + ' (control)', list(ids), '0.3',
                       ':' if j else '--'))
    fig_cruise_residuals(sp_m, groups)

    _rule('1d: turbid bbp variants on the red-peaked subset')
    red = ann_m[(ann_m['algorithm'] == 'giop')
                & (ann_m['peak_nm'] > RED_PEAK_NM)]
    red_ids = sorted(red['obs_id'].tolist())
    print(f'red-peaked (> {RED_PEAK_NM:.0f} nm) PANGAEA ids: {len(red_ids)} '
          f'of {ann_m["obs_id"].nunique()}')
    tt = turbid_comparison(red_ids, n_cores)
    conv = tt[tt['status'] != 'fit_failed']
    summary = (conv.groupby('algorithm')
               .agg(n_converged=('obs_id', 'size'),
                    chi2_nu_median=('chi2_nu', 'median'),
                    rel_misfit_median=('rel_misfit', 'median'))
               .reindex(list(TURBID_ALGOS)))
    print(summary.round(4).to_string())
    fig_turbid(tt)

    _rule('attribution: every percentage point, named (maxfev rerun)')
    attr = attribution(ann_m)
    n_total = int(ann_m.groupby('algorithm').size().iloc[0])
    hdr = f'{"cause":<46s}' + ''.join(f'{a:>12s}' for a in ALGOS)
    print(hdr)
    for lbl in BUCKETS:
        line = f'{lbl:<46s}'
        for algo in ALGOS:
            line += f'{attr[algo][lbl] / n_total:>12.1%}'
        print(line)
    fig_attribution(attr, n_total)

    # same attribution on the committed (published) sweep for the report
    _rule('attribution on the committed sweep (published numbers)')
    attr_c = attribution(ann_c[ann_c['dataset'] == 'PANGAEA'])
    for lbl in BUCKETS:
        line = f'{lbl:<46s}'
        for algo in ALGOS:
            line += f'{attr_c[algo][lbl] / n_total:>12.1%}'
        print(line)

    # ------------------------------------------------------------------
    # Round 2 (2026-08-10, after JXP's Task-1 answers): the approved
    # defaults — 10% imputed error (noise='insitu' fallback), maxfev 40000,
    # and pre-fit out_of_scope — applied together as one PANGAEA sweep.
    # ------------------------------------------------------------------
    _rule('Round 2: PANGAEA under the approved defaults (pangaea_fits_v2)')
    ensure_pangaea_sweep(SWEEP_V2, maxfev=MAXFEV, n_cores=n_cores,
                         noise='insitu', force_fit=False)
    sp_v2, sc_v2 = io.read_results(SWEEP_V2)
    ann_v2 = annotate(sc_v2, sp_v2)
    print('noise tags:', dict(sc_v2['noise_model'].value_counts()))
    print('\nstatus rates under the approved defaults:')
    print(ann_v2.groupby('algorithm')['status']
          .value_counts(normalize=True).unstack(fill_value=0.0)
          .round(4).to_string())
    # cross-check against Round 1's prediction: rescoring the maxfev run at a
    # 10% floor, minus the red-peaked rows the pre-fit guard now declines
    pred = {}
    for algo, g in ann_m.groupby('algorithm'):
        scaled = g['chi2_nu'] * (FLAT_PCT / 0.10) ** 2
        pred[algo] = float(((g['status'] != 'fit_failed')
                            & (scaled <= CHI2NU_POOR_FIT)
                            & (g['peak_nm'] <= RED_PEAK_NM)).mean())
    print('\npredicted ok-rate (Round-1 rescore @10%, red-peaked excluded):')
    print({k: round(v, 4) for k, v in pred.items()})

    _rule('Round 2: example fits (clear -> turbid)')
    picks = pick_example_ids(ann_m, cmap)
    for label, obs_id in picks:
        row = ann_m[(ann_m['algorithm'] == 'giop')
                    & (ann_m['obs_id'] == obs_id)].iloc[0]
        print(f'  {label:<44s} id {obs_id:>6d}  peak {row["peak_nm"]:.0f} nm  '
              f'{row["n_bands_obs"]:.0f} bands  rel {row["rel_misfit"]:.3f}  '
              f'{row["status"]}')
    fig_example_fits(sp_m, sc_m, picks)

    # ------------------------------------------------------------------
    # Round 3 (Task 3, literature): score our fits with the field's
    # operational criterion — NASA GIOP-DC validity (dRrs <= 33% over
    # 400-600 nm; GIOP ATBD v1.0, doi:10.5067/ZGBW3QECROJ2).
    # ------------------------------------------------------------------
    _rule("Round 3: NASA GIOP-DC operational validity applied to our fits")
    print('force-fitted rerun (pangaea_fits_maxfev — all spectra fitted):')
    print(giop_dc_validity(sp_m, sc_m).round(4).to_string(index=False))
    print('\napproved-defaults rerun (pangaea_fits_v2 — red-peaked declined):')
    print(giop_dc_validity(sp_v2, sc_v2).round(4).to_string(index=False))

    print(f'\n[done] {time.time() - t0:.0f} s; figures in {_FIGDIR}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--n-cores', type=int, default=8)
    main(n_cores=ap.parse_args().n_cores)

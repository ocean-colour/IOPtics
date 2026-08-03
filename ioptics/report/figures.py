"""The standard static figure set, generated uniformly per algorithm/dataset.

Each builder reads the persisted sweep artifacts (results + metrics + chains via
:mod:`ioptics.io`/:mod:`ioptics.diagnostics`), renders with
:mod:`ioptics.plotting`, and writes **PNG + PDF** into
``runs/<sweep_id>/figures/`` — returning the written paths. Nothing re-fits; a
report is fully regenerable from ``runs/<sweep_id>/``.

Builders accept either a ``sweep_id`` string (loaded on the fly, honoring
``root=``) or a pre-loaded :class:`SweepArtifacts` bundle from :func:`load` (load
once, render many). The aggregate figures (``scatter_set``, ``taylor_target``,
``dbic_cdf``) cover the whole population; the per-obs figures (``spectra_set``,
``closure_set``, ``corner_set``) are meant for the curated handful the design
calls for (the MCMC subset + a few exemplars per trophic bin) and take explicit
observation ids selected upstream.
"""

from __future__ import annotations

from collections import namedtuple

import matplotlib.pyplot as plt
import pandas as pd

from ioptics import diagnostics, io, metrics, plotting

# Components carried through the spectra panels (decomposed a_dg / a_ph too).
SPECTRA_COMPONENTS = ('a', 'bb', 'a_dg', 'a_ph', 'bb_p')
FORMATS = ('png', 'pdf')

SweepArtifacts = namedtuple(
    'SweepArtifacts',
    ['sweep_id', 'root', 'spectral', 'scalar',
     'metrics_spectral', 'metrics_scalar', 'metrics_pairwise'])


def load(sweep_id, *, root=None):
    """Load a sweep's results + metrics tables into a :class:`SweepArtifacts`.

    ``results_{spectral,scalar}`` are required; the ``metrics_*`` tables are
    loaded when present (``None`` otherwise, so figure builders that need them
    can raise a clear error).
    """
    d = io.sweep_dir(sweep_id, root=root)
    spectral, scalar = io.read_results(sweep_id, root=root)

    def _opt(fname):
        path = d / fname
        return pd.read_parquet(path) if path.is_file() else None

    return SweepArtifacts(
        sweep_id=sweep_id, root=root, spectral=spectral, scalar=scalar,
        metrics_spectral=_opt(metrics.METRICS_SPECTRAL_FILE),
        metrics_scalar=_opt(metrics.METRICS_SCALAR_FILE),
        metrics_pairwise=_opt(metrics.METRICS_PAIRWISE_FILE))


def resolve(sweep, root=None):
    """Accept a ``sweep_id`` string (loaded) or an already-loaded bundle."""
    return load(sweep, root=root) if isinstance(sweep, str) else sweep


def subdir(sweep, name):
    """A named output subdir under the sweep dir (created): ``figures/``, ``tables/``."""
    d = io.sweep_dir(sweep.sweep_id, root=sweep.root, create=True) / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _figdir(sweep):
    """The sweep's ``figures/`` directory (created)."""
    return subdir(sweep, 'figures')


def _save(fig, figdir, name, *, formats=FORMATS):
    """Write ``fig`` as ``name.<ext>`` for each format, close it, return paths.

    A figure built from degenerate input (:func:`ioptics.plotting.is_empty`) is
    **not written at all** and returns no paths, so an empty panel can neither be
    saved nor copied onto a page. Callers treat an empty path list as "nothing to
    show here" and suppress the section.
    """
    if plotting.is_empty(fig):
        plt.close(fig)
        return []
    paths = []
    for ext in formats:
        p = figdir / f'{name}.{ext}'
        fig.savefig(p, dpi=150, bbox_inches='tight')
        paths.append(p)
    plt.close(fig)
    return paths


# --------------------------------------------------------------------------- #
# what this sweep can actually show (data-driven figure planning)
# --------------------------------------------------------------------------- #

def scored_refs(sweep, *, fit_method='chisq', root=None, components=None):
    """The ``(component, ref_wave, n)`` combinations this sweep can actually score.

    The report's figure set is derived from this rather than fixed, because a fixed
    set publishes blank panels the moment a dataset's truth differs: the first
    GLORIA report asked for ``a(440)`` and ``bb(555)`` when GLORIA's only spectral
    truth is ``a_dg(440)`` (from ``a_cdom440``), so every static figure came out
    blank.

    Prefers ``metrics_scalar`` (already the authority on what was scored, ``n > 0``
    at a matched ``ref_wave``) and falls back to counting finite truth pairs in
    ``results_spectral`` when metrics have not been computed yet. Ordered by
    ``n`` descending, so the best-covered combination leads.
    """
    sweep = resolve(sweep, root)
    keep = tuple(components or metrics.ACCURACY_COMPONENTS)
    ms = sweep.metrics_scalar
    if ms is not None and {'n', 'ref_wave', 'component'} <= set(ms.columns):
        rows = ms[(ms['fit_method'] == fit_method)
                  & (ms.get('stratum', 'all') == 'all')
                  & ms['component'].isin(keep)
                  & ms['ref_wave'].notna()
                  & (ms['n'].fillna(0) > 0)]
        if not rows.empty:
            agg = (rows.groupby(['component', 'ref_wave'])['n'].max()
                       .reset_index().sort_values('n', ascending=False))
            return [(str(r.component), float(r.ref_wave), int(r.n))
                    for r in agg.itertuples()]

    # Fallback: count finite (retrieval, truth) pairs per (component, wavelength).
    sp = sweep.spectral
    if sp is None or sp.empty or 'truth' not in sp.columns:
        return []
    sub = sp[(sp['fit_method'] == fit_method) & sp['component'].isin(keep)]
    sub = sub[sub['truth'].notna() & sub['value'].notna()]
    if sub.empty:
        return []
    agg = (sub.groupby(['component', 'wavelength'])['value'].size()
              .reset_index(name='n').sort_values('n', ascending=False))
    out = []
    for r in agg.itertuples():
        for nominal in (440, 443, 555, 670):
            if abs(float(r.wavelength) - nominal) <= 3.0:
                out.append((str(r.component), float(nominal), int(r.n)))
                break
    # de-duplicate, keeping the best-covered entry per (component, ref)
    best = {}
    for comp, ref, n in out:
        if n > best.get((comp, ref), (0,))[0]:
            best[(comp, ref)] = (n,)
    return sorted(((c, r, n) for (c, r), (n,) in best.items()),
                  key=lambda t: -t[2])


def dbic_pair(sweep, *, fit_method='chisq', root=None):
    """The two algorithms to contest with ΔBIC, or ``None`` if there is no contest.

    ΔBIC compares a *more* against a *less* complex model, so the pair is chosen by
    parameter count: the sweep's highest-``k`` algorithm against its lowest. Fixing
    the pair to ``expb_pow``-vs-``giop`` (the old default) produced a blank panel
    plus prose about ``giop`` on a sweep that never ran it.

    Returns ``(model_a, model_b)`` with ``k(a) > k(b)`` — or ``None`` when fewer
    than two algorithms are present, or when every algorithm has the same ``k``
    (then ΔBIC reduces to a χ² difference and the "does complexity pay" question
    is not being asked).
    """
    sweep = resolve(sweep, root)
    sc = sweep.scalar
    if sc is None or sc.empty or 'k' not in sc.columns:
        return None
    sub = sc[sc['fit_method'] == fit_method] if 'fit_method' in sc.columns else sc
    ks = (sub.groupby('algorithm')['k'].max().dropna().sort_values())
    if len(ks) < 2 or ks.iloc[0] == ks.iloc[-1]:
        return None
    return str(ks.index[-1]), str(ks.index[0])


# --------------------------------------------------------------------------- #
# aggregate figures (whole population)
# --------------------------------------------------------------------------- #

def scatter_set(sweep, component, *, ref=None, fit_method='chisq', root=None):
    """Retrieved-vs-true log-log scatter for one component (optionally at ``ref``)."""
    sweep = resolve(sweep, root)
    data = diagnostics.scatter_data(sweep.spectral, component, ref,
                                    fit_method=fit_method)
    fig = plotting.scatter_log(data, component=component, ref=ref)
    tag = f'{component}' + (f'_{int(ref)}' if ref is not None else '')
    return _save(fig, _figdir(sweep), f'scatter_{tag}')


def ratio_hist(sweep, component, *, ref=None, fit_method='chisq', root=None):
    """Distribution of retrieved/true ratios per accuracy bucket, per algorithm.

    The companion every scatter is conventionally paired with (GIOP Figs. 1-2):
    the scatter shows where the points lie, this shows how the population is
    distributed about 1:1 — central tendency alone hides the spread that decides
    whether a retrieval is usable.
    """
    sweep = resolve(sweep, root)
    data = diagnostics.ratio_hist_data(sweep.spectral, component, ref,
                                       fit_method=fit_method)
    fig = plotting.ratio_hist(data)
    tag = f'{component}' + (f'_{int(ref)}' if ref is not None else '')
    return _save(fig, _figdir(sweep), f'ratio_hist_{tag}')


def taylor_target(sweep, component='a', *, ref=None, fit_method='chisq',
                  root=None):
    """Taylor + Target diagrams (all algorithms) for one component.

    The output names carry the reference band as well as the component: with only
    the component in the name, two reference wavelengths silently overwrote each
    other's file.
    """
    sweep = resolve(sweep, root)
    figdir = _figdir(sweep)
    ts = diagnostics.taylor_stats(sweep.spectral, component, ref,
                                  fit_method=fit_method)
    tg = diagnostics.target_stats(sweep.spectral, component, ref,
                                  fit_method=fit_method)
    tag = f'{component}' + (f'_{int(ref)}' if ref is not None else '')
    paths = _save(plotting.taylor(ts), figdir, f'taylor_{tag}')
    paths += _save(plotting.target(tg), figdir, f'target_{tag}')
    return paths


def dbic_cdf(sweep, *, model_a='expb_pow', model_b='giop', root=None):
    """ΔBIC CDF for the two-model contest (χ²-only, like-for-like)."""
    sweep = resolve(sweep, root)
    data = diagnostics.dbic_cdf_data(sweep.scalar, model_a, model_b)
    fig = plotting.dbic_cdf(data)
    return _save(fig, _figdir(sweep), f'dbic_cdf_{model_a}_vs_{model_b}')


# --------------------------------------------------------------------------- #
# per-observation figures (curated handful)
# --------------------------------------------------------------------------- #

def spectra_set(sweep, obs_id, *, algorithm, fit_method='chisq',
                components=SPECTRA_COMPONENTS, root=None):
    """Per-component spectra (value + 68/95 bands vs truth) for one observation."""
    sweep = resolve(sweep, root)
    figdir = _figdir(sweep)
    sub = sweep.spectral[(sweep.spectral['obs_id'] == obs_id)
                         & (sweep.spectral['algorithm'] == algorithm)
                         & (sweep.spectral['fit_method'] == fit_method)]
    paths = []
    for comp in components:
        cf = sub[sub['component'] == comp]
        if cf.empty:
            continue
        fig = plotting.spectra_band(cf, label=algorithm, component=comp)
        paths += _save(fig, figdir, f'spectra_{algorithm}_{obs_id}_{comp}')
    return paths


def closure_set(sweep, obs_id, *, fit_method='chisq', root=None):
    """Rrs closure residuals (all algorithms) for one observation."""
    sweep = resolve(sweep, root)
    res = diagnostics.residual_spectra(sweep.spectral, sweep.scalar, obs_id,
                                       fit_method=fit_method)
    fig = plotting.residual_rrs(res)
    return _save(fig, _figdir(sweep), f'closure_{obs_id}')


def corner_set(sweep, *, root=None):
    """Corner plots for every MCMC row that saved a chain (the MCMC subset)."""
    sweep = resolve(sweep, root)
    figdir = _figdir(sweep)
    sc = sweep.scalar
    mcmc = sc[(sc['fit_method'] == 'mcmc') & sc['chain_file'].notna()]
    paths = []
    for _, row in mcmc.iterrows():
        data = diagnostics.corner_data(row['chain_file'])
        fig = plotting.corner(data)
        paths += _save(fig, figdir, f"corner_{row['algorithm']}_{row['obs_id']}")
    return paths

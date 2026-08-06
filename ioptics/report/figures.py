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

import re
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


def _safe(part):
    """Make a filename fragment out of a dataset-defined id.

    ``obs_id`` comes from the dataset, not from us: GLORIA's are strings, and nothing
    guarantees another dataset's are free of ``/``, spaces or other characters that
    would send a figure outside its own directory or produce an unreferenceable
    filename. Any character outside ``[A-Za-z0-9._-]`` becomes an underscore.
    """
    return re.sub(r'[^A-Za-z0-9._-]', '_', str(part))


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


def dbic_cdf(sweep, *, model_a='expb_pow', model_b='giop', by=None, root=None):
    """ΔBIC CDF for the two-model contest (χ²-only, like-for-like).

    ``by`` splits the contest by a column (``'stratum'``), drawing one step curve per
    group — "does the extra complexity pay *in turbid water*" is a different question
    from "does it pay overall", and the pooled curve can hide a reversal.
    """
    sweep = resolve(sweep, root)
    scalar = sweep.scalar
    if by == 'stratum':
        # ``stratum`` lives only on the metrics tables, so it must be attached to
        # ``results_scalar`` before grouping — binned by the same rule.
        scalar = metrics.with_strata(scalar)
    data = diagnostics.dbic_cdf_data(scalar, model_a, model_b, by=by)
    fig = plotting.dbic_cdf(data)
    tag = f'dbic_cdf_{model_a}_vs_{model_b}' + (f'_by_{by}' if by else '')
    return _save(fig, _figdir(sweep), tag)


# --------------------------------------------------------------------------- #
# the three slices metrics_spectral / stratum / fit_method make possible
# --------------------------------------------------------------------------- #

def scored_components(sweep, *, metric='mae', fit_method='chisq', stratum='all',
                      min_waves=diagnostics.MIN_SPECTRUM_WAVES, root=None):
    """Planner: components with accuracy at ``min_waves`` or more bands.

    The floor is :data:`ioptics.diagnostics.MIN_SPECTRUM_WAVES` (5, JXP's number)
    because a component scored at one or two wavelengths has no spectral shape to
    show — GLORIA's ``a_dg`` at 440 nm is the only thing that sweep scores — and a
    couple of markers per algorithm under an "accuracy vs wavelength" heading invites
    a reader to see a trend that is not there.
    """
    sweep = resolve(sweep, root)
    ds = _sole_dataset(sweep)
    return diagnostics.scored_components(
        sweep.metrics_spectral, dataset=ds, fit_method=fit_method,
        stratum=stratum, metric=metric, min_waves=min_waves)


def _sole_dataset(sweep):
    """The sweep's dataset when it has exactly one, else ``None`` (do not filter)."""
    sc = sweep.scalar
    if sc is None or sc.empty or 'dataset' not in sc.columns:
        return None
    names = sc['dataset'].dropna().unique()
    return str(names[0]) if len(names) == 1 else None


def accuracy_spectrum(sweep, *, components=None, metric='mae',
                      fit_method='chisq', stratum='all', ncols=2,
                      min_waves=2, root=None):
    """Accuracy vs wavelength, one panel per component, all algorithms overlaid.

    The figure an ocean-colour reader looks for first, and the one
    ``metrics_spectral`` was computed and persisted for since Stage 2 without ever
    being read by the report layer. Returns ``[]`` when no component is scored at
    enough bands to have a spectral shape.
    """
    sweep = resolve(sweep, root)
    ds = _sole_dataset(sweep)
    if components is None:
        components = [c for c, _, _ in scored_components(
            sweep, metric=metric, fit_method=fit_method, stratum=stratum,
            min_waves=min_waves)]
    if not components:
        return []
    panels = [diagnostics.accuracy_spectrum_data(
        sweep.metrics_spectral, c, metric=metric, dataset=ds,
        fit_method=fit_method, stratum=stratum) for c in components]
    fig = plotting.accuracy_spectrum_grid(panels, ncols=ncols)
    tag = f'accuracy_vs_wavelength_{metric}'
    if stratum not in (None, 'all'):
        tag += f'_{stratum}'
    return _save(fig, _figdir(sweep), tag)


#: The stratum name for observations with neither truth nor retrieved Chl. It is a
#: **provenance** category, not a water type, so per JXP it is dropped from the
#: per-stratum tables and its count stated instead — otherwise it sits in the same
#: column as three real trophic bins and reads as a fourth one.
UNKNOWN_STRATUM = 'unknown'


def strata(sweep, *, fit_method='chisq', include_all=False, min_n=1,
           include_unknown=False, root=None):
    """Planner: the strata this sweep actually has scored content for.

    Returns ``[(stratum, n_pairs, n_attempted)]`` ordered by ``n_pairs`` descending.
    ``'all'`` is excluded by default — it is the pooled row every page already shows,
    and the point of a per-stratum section is what the pooling hides.
    :data:`UNKNOWN_STRATUM` is excluded too, per JXP: it is a provenance category
    rather than a water type. Its size is **not** hidden — see
    :func:`unknown_stratum_count`, which the page states so the strata cannot look
    complete when they are not.
    """
    sweep = resolve(sweep, root)
    ms = sweep.metrics_scalar
    if ms is None or getattr(ms, 'empty', True) or 'stratum' not in ms.columns:
        return []
    sub = ms
    if fit_method is not None and 'fit_method' in sub.columns:
        sub = sub[sub['fit_method'] == fit_method]
    out = []
    for stratum, g in sub.groupby('stratum', sort=False):
        if not include_all and stratum == 'all':
            continue
        if not include_unknown and stratum == UNKNOWN_STRATUM:
            continue
        acc = g[g['ref_wave'].notna()] if 'ref_wave' in g else g
        n_pairs = float(acc['n'].fillna(0).max()) if 'n' in acc and not acc.empty else 0.0
        closure = g[g['component'] == 'Rrs'] if 'component' in g else g
        n_att = (float(closure['n_attempted'].fillna(0).max())
                 if 'n_attempted' in closure and not closure.empty else 0.0)
        if max(n_pairs, n_att) >= min_n:
            out.append((str(stratum), int(n_pairs), int(n_att)))
    return sorted(out, key=lambda t: (-t[1], -t[2], t[0]))


def unknown_stratum_count(sweep, *, fit_method='chisq', root=None):
    """``(n_pairs, n_attempted)`` for the dropped :data:`UNKNOWN_STRATUM`, or ``None``.

    Dropping a population silently would make the trophic breakdown look complete. The
    count is what keeps the omission honest, so the page states it in prose.
    """
    got = strata(sweep, fit_method=fit_method, include_unknown=True, root=root)
    for stratum, n_pairs, n_att in got:
        if stratum == UNKNOWN_STRATUM:
            return n_pairs, n_att
    return None


def fit_methods(sweep, *, root=None, min_rows=1):
    """Planner: the fit methods present, with their scored row counts.

    Returns ``[(fit_method, n_rows)]``. A χ²-vs-MCMC comparison needs two, and every
    sweep run so far has exactly one — so the report layer must ask rather than assume.
    """
    sweep = resolve(sweep, root)
    sc = sweep.scalar
    if sc is None or sc.empty or 'fit_method' not in sc.columns:
        return []
    counts = sc['fit_method'].value_counts()
    return [(str(k), int(v)) for k, v in counts.items() if int(v) >= min_rows]


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
        paths += _save(fig, figdir,
                       f'spectra_{_safe(algorithm)}_{_safe(obs_id)}_{comp}')
    return paths


def exemplars(sweep, *, fit_method='chisq', n=diagnostics.EXEMPLAR_N, root=None):
    """The sweep's exemplar observations — planner for :func:`exemplar_fits`.

    Thin wrapper over :func:`ioptics.diagnostics.exemplar_obs`, in the same
    "planner + builder" shape as :func:`scored_refs` / :func:`dbic_pair`: the report
    layer needs the selection itself (for the page's prose and to pick which
    observations get a closure panel), not only the figure.
    """
    sweep = resolve(sweep, root)
    return diagnostics.exemplar_obs(sweep.scalar, sweep.spectral,
                                    fit_method=fit_method, n=n)


def exemplar_fits(sweep, picks=None, *, fit_method='chisq',
                  n=diagnostics.EXEMPLAR_N, ncols=2, root=None,
                  ordered_by_peak=None):
    """Grid of exemplar Rrs fits, ordered clear→turbid. Returns written paths.

    ``picks`` is a selection frame from :func:`exemplars` (recomputed if omitted).
    One asset per sweep rather than ten, which is both how the hand-made
    ``reports/figures/wide_example_fits.png`` presents them and what keeps the page
    from being ten near-identical figure blocks.

    ``ordered_by_peak`` states whether the selection really is in turbidity order;
    the suptitle follows it rather than asserting clear→turbid unconditionally,
    because a sweep with no persisted ``Rrs_obs`` is ordered by fit quality instead.
    Inferred from ``picks`` when not given — which is the whole reason the reference
    figure's title was wrong about its own contents.
    """
    sweep = resolve(sweep, root)
    if picks is None:
        picks = exemplars(sweep, fit_method=fit_method, n=n)
    if picks is None or picks.empty:
        return []
    # ``dataset`` must be passed, not left to default: obs ids are reused across
    # datasets, so without it a panel blends two unrelated spectra and annotates
    # them with whichever row came first.
    panels = [diagnostics.rrs_fit_data(sweep.spectral, sweep.scalar, r.obs_id,
                                       dataset=getattr(r, 'dataset', None),
                                       fit_method=fit_method)
              for r in picks.itertuples()]
    if ordered_by_peak is None:
        ordered_by_peak = bool(picks['peak_nm'].notna().any())
    order = ('clear (top-left) to turbid (bottom-right)' if ordered_by_peak
             else 'best (top-left) to worst (bottom-right) by fit quality')
    fig = plotting.exemplar_grid(
        panels, ncols=ncols, roles=list(picks['role']),
        suptitle=f'Exemplar fits, {order}')
    return _save(fig, _figdir(sweep), 'exemplar_fits')


def closure_set(sweep, obs_id, *, dataset=None, fit_method='chisq', root=None):
    """Rrs closure residuals (all algorithms) for one observation.

    ``dataset`` disambiguates the observation: ids are reused across datasets, so
    without it a multi-dataset sweep merges two unrelated spectra into one panel.
    It also enters the filename, since ``closure_0.png`` would otherwise be claimed
    by whichever dataset was drawn last.
    """
    sweep = resolve(sweep, root)
    res = diagnostics.residual_spectra(sweep.spectral, sweep.scalar, obs_id,
                                       dataset=dataset, fit_method=fit_method)
    fig = plotting.residual_rrs(res)
    tag = _safe(obs_id) if dataset is None else f'{_safe(dataset)}_{_safe(obs_id)}'
    return _save(fig, _figdir(sweep), f'closure_{tag}')


#: Default cap on how many corner plots a page build writes. A sweep with thousands
#: of saved chains would otherwise put thousands of figures into the docs tree.
MAX_CORNERS = 8


def corner_set(sweep, *, root=None, limit=MAX_CORNERS):
    """Corner plots for every MCMC row that saved a chain (the MCMC subset).

    A ``chain_file`` recorded on disk is only a **path**, so it goes stale as soon
    as a sweep dir is copied between machines or the chains are pruned to save
    space. An unreadable chain is therefore **skipped rather than raised**: this
    builder is wired into a page build, and one moved file must not take the whole
    report down. Returns the paths actually written, so a caller can tell how many
    chains survived by comparing against the MCMC row count.

    ``limit`` caps how many are **drawn** (:data:`MAX_CORNERS` by default). It is
    applied to the successful reads rather than to the candidate rows, so a handful
    of stale paths at the head of the table cannot consume the whole budget and
    leave the page with no corner plots at all.
    """
    sweep = resolve(sweep, root)
    figdir = _figdir(sweep)
    sc = sweep.scalar
    if sc is None or sc.empty or 'chain_file' not in sc.columns:
        return []
    mcmc = sc[(sc['fit_method'] == 'mcmc') & sc['chain_file'].notna()]
    paths, drawn = [], 0
    for _, row in mcmc.iterrows():
        if limit is not None and drawn >= int(limit):
            break
        try:
            data = diagnostics.corner_data(row['chain_file'])
            fig = plotting.corner(data)
        except Exception:
            # Any unreadable chain — missing, truncated, a non-NPZ, or a corrupt zip
            # (``zipfile.BadZipFile`` is **not** an ``OSError``, so a narrow except
            # tuple let a half-written chain take the whole page build down).
            continue
        paths += _save(fig, figdir,
                       f"corner_{_safe(row['algorithm'])}_{_safe(row['obs_id'])}")
        drawn += 1
    return paths

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
    """Write ``fig`` as ``name.<ext>`` for each format, close it, return paths."""
    paths = []
    for ext in formats:
        p = figdir / f'{name}.{ext}'
        fig.savefig(p, dpi=150, bbox_inches='tight')
        paths.append(p)
    plt.close(fig)
    return paths


# --------------------------------------------------------------------------- #
# aggregate figures (whole population)
# --------------------------------------------------------------------------- #

def scatter_set(sweep, component, *, ref=None, fit_method='chisq', root=None):
    """Retrieved-vs-true log-log scatter for one component (optionally at ``ref``)."""
    sweep = resolve(sweep, root)
    data = diagnostics.scatter_data(sweep.spectral, component, ref,
                                    fit_method=fit_method)
    fig = plotting.scatter_log(data)
    tag = f'{component}' + (f'_{int(ref)}' if ref is not None else '')
    return _save(fig, _figdir(sweep), f'scatter_{tag}')


def taylor_target(sweep, component='a', *, ref=None, fit_method='chisq',
                  root=None):
    """Taylor + Target diagrams (all algorithms) for one component."""
    sweep = resolve(sweep, root)
    figdir = _figdir(sweep)
    ts = diagnostics.taylor_stats(sweep.spectral, component, ref,
                                  fit_method=fit_method)
    tg = diagnostics.target_stats(sweep.spectral, component, ref,
                                  fit_method=fit_method)
    paths = _save(plotting.taylor(ts), figdir, f'taylor_{component}')
    paths += _save(plotting.target(tg), figdir, f'target_{component}')
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
        fig = plotting.spectra_band(cf, label=comp)
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

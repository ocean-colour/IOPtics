"""Long/tidy parquet results tables and the per-sweep directory layout.

Flattens :class:`~ioptics.records.RetrievalResult` objects (paired with their
source :class:`~ioptics.records.PreparedRecord`, which carries the truth) into
two tidy parquet tables and owns the on-disk layout

::

    $OS_COLOR/IOPtics/runs/<sweep_id>/
        results_spectral.parquet     # one row per (key, component, wavelength)
        results_scalar.parquet       # one row per (key)
        provenance.yaml  chains/  figures/      # written by other modules

The tables store **linear, physical** quantities: the spectral components are
``a``/``bb``/``a_ph``/``a_dg``/``bb_p`` in 1/m and ``Rrs_model``/``Rrs_obs`` in
1/sr (as ``evaluate`` reconstructs the model and ``run``/``prep`` supply the
observation), and the scalar columns (``a_cdom440``, ``Sdg``, ``beta``) are
likewise linear. The fit's log10 amplitude parameters are not surfaced here —
so no fit-space → linear conversion is needed in the tables. ``Rrs_obs`` is the
observed Rrs the fit saw, persisted as its own component so the metrics layer
can close ``Rrs_model`` against it.

This module depends only on pandas/pyarrow (no BING/ocpy).
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

SPECTRAL_FILE = 'results_spectral.parquet'
SCALAR_FILE = 'results_scalar.parquet'

# Components written to the spectral table, with their physical unit.
# ``Rrs_obs`` is the *observed* Rrs the fit saw (from the record, not the model)
# — persisted as its own component so ``metrics`` §2 closure can score
# ``Rrs_model`` against it. Its ``truth`` is NaN (it is the observation, not a
# truth) and it carries no uncertainty bounds.
_UNITS = {'a': '1/m', 'bb': '1/m', 'a_ph': '1/m', 'a_dg': '1/m',
          'bb_p': '1/m', 'Rrs_model': '1/sr', 'Rrs_obs': '1/sr'}


def runs_root(root=None):
    """Resolve the runs root: ``root`` if given, else ``$OS_COLOR/IOPtics/runs``."""
    if root is not None:
        return Path(root)
    osc = os.getenv('OS_COLOR')
    if not osc:
        raise RuntimeError(
            "results root unresolved: set $OS_COLOR or pass root=")
    return Path(osc) / 'IOPtics' / 'runs'


def sweep_dir(sweep_id, *, root=None, create=False):
    """Return ``<runs_root>/<sweep_id>`` (optionally creating it + ``chains``/
    ``figures`` subdirs)."""
    d = runs_root(root) / sweep_id
    if create:
        (d / 'chains').mkdir(parents=True, exist_ok=True)
        (d / 'figures').mkdir(parents=True, exist_ok=True)
    return d


def chain_path(sweep_id, algorithm, obs_id, *, root=None):
    """Path to one MCMC chain NPZ: ``<sweep>/chains/<algorithm>_<obs_id>.npz``."""
    return sweep_dir(sweep_id, root=root) / 'chains' / f'{algorithm}_{obs_id}.npz'


def save_chain(sweep_id, algorithm, record, chains, *, root=None):
    """Save one MCMC posterior chain to its NPZ and return the path.

    Mirrors ``bing.fitting.l23.save_chains``: stores ``chains`` (shape
    ``(nsteps, nwalkers, nparam)``) + ``idx`` and the context needed to
    re-analyze it (``wave``, ``obs_Rrs``, ``varRrs``, ``Chl``, ``Y``). Written
    under the sweep's ``chains/`` dir (created if needed).
    """
    sweep_dir(sweep_id, root=root, create=True)
    path = chain_path(sweep_id, algorithm, record.obs_id, root=root)
    np.savez(
        path,
        chains=np.asarray(chains),
        idx=record.obs_id,
        wave=np.asarray(record.wave, dtype=float),
        obs_Rrs=np.asarray(record.Rrs, dtype=float),
        varRrs=np.asarray(record.varRrs, dtype=float),
        Chl=float(record.init.get('Chl', np.nan)),
        Y=float(record.init.get('Y', np.nan)),
    )
    return path


def load_chain(path):
    """Load a saved chain NPZ into a dict (for ``diagnostics`` / ``report``)."""
    with np.load(path, allow_pickle=False) as npz:
        return {key: npz[key] for key in npz.files}


def _truth_spectrum(record, component):
    """Return truth values on ``record.wave`` for a component (NaN if absent).

    ``Rrs_model`` is a model-only component with no truth in ``record.truth``,
    so it falls through to NaN (closure is scored from the observed/clean Rrs at
    the metrics stage, not via a truth column here).
    """
    n = record.wave.size
    val = record.truth.get(component)
    if val is None:
        return np.full(n, np.nan), False
    # spectral truth is an ocpy Spectrum aligned to record.wave
    values = np.asarray(getattr(val, 'values', val), dtype=float)
    return values, bool(record.truth_interp.get(component, False))


def _spectral_rows(result, record):
    """Tidy rows (one per component × wavelength) for the spectral table."""
    wave = np.asarray(record.wave, dtype=float)
    rows = []
    for component, cf in result.components.items():
        truth, interp = _truth_spectrum(record, component)
        unit = _UNITS.get(component, '')
        for i, lam in enumerate(wave):
            rows.append({
                'dataset': result.dataset, 'obs_id': result.obs_id,
                'algorithm': result.algorithm, 'fit_method': result.fit_method,
                'component': component, 'wavelength': float(lam),
                'value': float(cf.med[i]),
                'lo68': float(cf.lo68[i]), 'hi68': float(cf.hi68[i]),
                'lo95': float(cf.lo95[i]), 'hi95': float(cf.hi95[i]),
                'truth': float(truth[i]), 'truth_interp': interp,
                'unit': unit,
            })
    # Observed Rrs the fit saw — a no-uncertainty, no-truth component so
    # metrics can close Rrs_model against it (the observation, not a truth).
    obs_rrs = np.asarray(record.Rrs, dtype=float)
    for i, lam in enumerate(wave):
        rows.append({
            'dataset': result.dataset, 'obs_id': result.obs_id,
            'algorithm': result.algorithm, 'fit_method': result.fit_method,
            'component': 'Rrs_obs', 'wavelength': float(lam),
            'value': float(obs_rrs[i]),
            'lo68': np.nan, 'hi68': np.nan, 'lo95': np.nan, 'hi95': np.nan,
            'truth': np.nan, 'truth_interp': False, 'unit': _UNITS['Rrs_obs'],
        })
    return rows


def _scalar_value(record, key):
    """Truth scalar for a results_scalar column (NaN if the dataset lacks it)."""
    if key == 'a_cdom440':
        adg = record.truth.get('a_dg')
        if adg is None:
            return np.nan
        i440 = int(np.argmin(np.abs(np.asarray(record.wave) - 440.0)))
        return float(np.asarray(adg.values)[i440])
    val = record.truth.get(key)
    return float(val) if isinstance(val, (int, float, np.floating)) else np.nan


def _scalar_row(result, record):
    """One tidy row for the scalar table."""
    def med_sig(key):
        v = result.scalars.get(key)
        return (float(v[0]), float(v[1])) if v is not None else (np.nan, np.nan)

    chl, sig_chl = med_sig('Chl')
    acdom, sig_acdom = med_sig('a_cdom440')
    sdg, sig_sdg = med_sig('Sdg')
    beta, sig_beta = med_sig('beta')
    st = result.stats
    return {
        'dataset': result.dataset, 'obs_id': result.obs_id,
        'algorithm': result.algorithm, 'fit_method': result.fit_method,
        'chi2': st.get('chi2', np.nan), 'chi2_nu': st.get('chi2_nu', np.nan),
        'AIC': st.get('AIC', np.nan), 'BIC': st.get('BIC', np.nan),
        'n_bands': st.get('n_bands', 0), 'k': st.get('k', 0),
        'Chl': chl, 'sig_Chl': sig_chl,
        'a_cdom440': acdom, 'sig_a_cdom440': sig_acdom,
        'Sdg': sdg, 'sig_Sdg': sig_sdg,
        'beta': beta, 'sig_beta': sig_beta,
        'Chl_truth': _scalar_value(record, 'Chl'),
        'a_cdom440_truth': _scalar_value(record, 'a_cdom440'),
        'Sdg_truth': _scalar_value(record, 'Sdg'),
        'beta_truth': np.nan,                    # beta is a model param, not L23 truth
        'status': result.status,
        'chain_file': getattr(result, 'chain_file', None),  # null for χ² rows
        'provenance_id': result.provenance_id,
    }


def results_to_frames(pairs):
    """Flatten ``[(RetrievalResult, PreparedRecord), ...]`` to two DataFrames."""
    spectral, scalar = [], []
    for result, record in pairs:
        spectral.extend(_spectral_rows(result, record))
        scalar.append(_scalar_row(result, record))
    return pd.DataFrame(spectral), pd.DataFrame(scalar)


def write_results(sweep_id, pairs, *, root=None):
    """Write the two parquet tables under ``<runs_root>/<sweep_id>/``.

    Returns a dict with the ``spectral`` and ``scalar`` paths.
    """
    d = sweep_dir(sweep_id, root=root, create=True)
    spectral_df, scalar_df = results_to_frames(pairs)
    paths = {'spectral': d / SPECTRAL_FILE, 'scalar': d / SCALAR_FILE}
    spectral_df.to_parquet(paths['spectral'], index=False)
    scalar_df.to_parquet(paths['scalar'], index=False)
    return paths


def read_results(sweep_id, *, root=None):
    """Read back ``(spectral_df, scalar_df)`` for a sweep."""
    d = sweep_dir(sweep_id, root=root)
    return (pd.read_parquet(d / SPECTRAL_FILE),
            pd.read_parquet(d / SCALAR_FILE))

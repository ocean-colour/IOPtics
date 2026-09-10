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

from ioptics import noise

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


def chain_path(sweep_id, algorithm, obs_id, *, dataset=None, root=None):
    """Path to one MCMC chain NPZ.

    ``<sweep>/chains/<algorithm>_<dataset>_<obs_id>.npz`` when ``dataset`` is
    given — it must be, for any mixed-dataset subset: ``obs_id`` alone does
    not identify an observation (the package's own convention reuses ids
    across datasets), and with a pooled MCMC pass two same-id records would
    otherwise race on one file. The dataset-less form is kept for reading
    chains written before Stage 7 Task 13.
    """
    stem = (f'{algorithm}_{obs_id}' if dataset is None
            else f'{algorithm}_{dataset}_{obs_id}')
    return sweep_dir(sweep_id, root=root) / 'chains' / f'{stem}.npz'


#: Persistence thinning stride for saved MCMC chains (see :func:`save_chain`).
#: The pipeline consumes posterior *percentiles*, computed at fit time from the
#: full in-memory chain; the persisted NPZ exists for corner plots and
#: re-analysis, for which every 20th step of 16 walkers is ample (~1 950
#: steps per walker at the default 40 000-step spec after its burn discard).
#: At full-L23 scale the stride is what turns ~40 GB of chains into ~2 GB.
#: The stride is recorded in the NPZ (``thin``, beside ``nsteps_total`` and
#: ``nburn_discarded``), so a thinned chain cannot be mistaken for a short one.
CHAIN_THIN = 20


def save_chain(sweep_id, algorithm, record, chains, *, root=None, pnames=None,
               burn=0, thin=1, nburn_sampler=None):
    """Save one MCMC posterior chain to its NPZ and return the path.

    Mirrors ``bing.fitting.l23.save_chains``: stores ``chains`` (shape
    ``(nsteps, nwalkers, nparam)``) + ``idx`` and the context needed to
    re-analyze it (``wave``, ``obs_Rrs``, ``varRrs``, ``Chl``, ``Y``). When
    ``pnames`` (the fit parameter names, in chain-column order) is given they
    are stored too, so ``diagnostics.corner_data`` can label the corner axes.
    Written under the sweep's ``chains/`` dir (created if needed).

    ``burn``/``thin`` control what is *persisted*, not what was sampled: the
    first ``burn`` steps are discarded (capped at half the chain, matching
    :func:`ioptics.evaluate.chain_burn`) and every ``thin``-th remaining step
    is kept. The trim is recorded so a thinned chain cannot be mistaken for a
    short run — and with names that describe the sampler's actual timeline
    (the sampler *also* ran and discarded its own burn-in before the
    production chain this function receives):

    - ``nsteps_production`` — length of the untrimmed production chain;
    - ``nburn_sampler`` — burn-in steps the sampler ran and reset away
      *before* production (pass ``spec.mcmc.nburn``; omitted if ``None``);
    - ``nburn_discarded`` — the second discard applied here, off the head of
      the production chain;
    - ``thin`` — the persistence stride,

    so persisted ``chains[i]`` is sampler step
    ``nburn_sampler + nburn_discarded + i*thin``. The defaults persist the
    chain whole.
    """
    sweep_dir(sweep_id, root=root, create=True)
    path = chain_path(sweep_id, algorithm, record.obs_id,
                      dataset=record.dataset, root=root)
    chains = np.asarray(chains)
    nsteps_production = int(chains.shape[0])
    burn = min(int(burn), max(nsteps_production // 2, 0))
    thin = max(int(thin), 1)
    meta = {} if nburn_sampler is None else {
        'nburn_sampler': int(nburn_sampler)}
    np.savez(
        path,
        chains=chains[burn::thin],
        idx=record.obs_id,
        wave=np.asarray(record.wave, dtype=float),
        obs_Rrs=np.asarray(record.Rrs, dtype=float),
        varRrs=np.asarray(record.varRrs, dtype=float),
        Chl=float(record.init.get('Chl', np.nan)),
        Y=float(record.init.get('Y', np.nan)),
        pnames=np.asarray([] if pnames is None else pnames, dtype=str),
        nsteps_production=nsteps_production,
        nburn_discarded=burn,
        thin=thin,
        **meta,
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


def _meta_str(record, key):
    """A string-valued meta field of the record (None when absent/NaN)."""
    val = getattr(record, 'meta', {}).get(key)
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return str(val)


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
    # Shape parameters beyond the four fixed columns above -- e.g. eta_min /
    # eta_org for the two-component backscattering models. Emitted under their
    # own names so the column set is the union across algorithms; a row from an
    # algorithm without them simply gets NaN.
    extra = {}
    for key, val in result.scalars.items():
        if key in ('Chl', 'a_cdom440', 'Sdg', 'beta'):
            continue                       # already emitted, fixed names
        try:
            extra[key] = float(val[0])
            extra[f'sig_{key}'] = float(val[1])
        except (TypeError, IndexError, ValueError):
            continue
    return {
        'dataset': result.dataset, 'obs_id': result.obs_id,
        'algorithm': result.algorithm, 'fit_method': result.fit_method,
        'chi2': st.get('chi2', np.nan), 'chi2_nu': st.get('chi2_nu', np.nan),
        'AIC': st.get('AIC', np.nan), 'BIC': st.get('BIC', np.nan),
        # The noise-model-free fit quality (median |model-obs|/obs over
        # positive-Rrs bands). NaN on unfitted rows and on sweeps that
        # predate the column (2026-08-12).
        'rel_misfit': st.get('rel_misfit', np.nan),
        # NaN, not 0, when a result carries no stats: a zero band count on a
        # fit_failed row reads as a real (impossible) measurement and poisoned
        # every reader that counted bands on exactly the rows worth diagnosing.
        # (run._failed_result now populates n_bands/k, so this default is a
        # last resort, and it must be visibly missing rather than silently 0.)
        'n_bands': st.get('n_bands', np.nan), 'k': st.get('k', np.nan),
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
        # The noise provenance of the *record this fit saw*, not the sweep-level
        # request. ``attach_noise`` may floor or wholly impute the uncertainty, and
        # the effective tag records which ('<model>+floor:X' / '+imputed:X'). It has
        # to be on disk: χ²ᵥ is a statement about the assumed error as much as about
        # the model, so "70 of these 100 fits were weighted by an invented
        # uncertainty" is not an aside — and until now it survived only as a
        # warning on stderr at prep time, recoverable from no artifact.
        'noise_model': getattr(record, 'noise_model', None),
        'noise_seed': getattr(record, 'noise_seed', None),
        'noise_imputed': noise.is_imputed(getattr(record, 'noise_model', None)),
        # Source provenance (PANGAEA: cruise + PI/instrument group) and the
        # spectral-shape quality annotation — None/NaN for datasets that
        # don't carry them. Added 2026-08-12 (Task-4 B1/B2, approved).
        'subdataset': _meta_str(record, 'subdataset'),
        'contributor': _meta_str(record, 'contributor'),
        'qwip_score': getattr(record, 'qwip_score', np.nan),
        **extra,
    }


def _harmonize_obs_id(*frames):
    """Cast ``obs_id`` to ``str`` — in **every** frame — if any of them is mixed.

    An observation id is whatever its dataset calls one: L23 and PANGAEA number
    them, GLORIA and PACE name them (``'GID_1'``,
    ``'1902304_156_PACE_OCI...._ExpBPow'``). A sweep over one dataset therefore
    gets a clean ``int64`` or ``str`` column and nothing notices. A sweep over
    **both kinds** gets a column of mixed Python objects, and ``to_parquet``
    refuses it outright::

        ArrowInvalid: Could not convert '1902304_156_PACE_OCI...' with type str:
        tried to convert to int64

    — which is how the first {L23, PANGAEA, PACE} sweep died, after every fit had
    already run. Ids are labels, never arithmetic, so ``str`` is a lossless
    common type; casting *all* the frames (not only the offending one) keeps
    ``results_spectral`` and ``results_scalar`` joinable on
    ``(dataset, obs_id)``, which every metric depends on.

    The test is deliberately **named ids vs numbered ids**, not "more than one
    Python type": a mixed ``{int, numpy.int64}`` column is perfectly writable
    (L23 enumerates with plain ints, PANGAEA's index yields ``int64``), and
    stringifying it would gratuitously change the dtype of every existing
    L23+PANGAEA sweep's artifacts. A homogeneous column is left exactly as it
    was.
    """
    frames = [f for f in frames if f is not None and 'obs_id' in f.columns]
    kinds = set()
    for f in frames:
        if f.empty:
            continue
        kinds |= {isinstance(v, str) for v in f['obs_id'].unique()}
    mixed = len(kinds) > 1
    if mixed:
        for f in frames:
            f['obs_id'] = f['obs_id'].astype(str)
    return mixed


def results_to_frames(pairs):
    """Flatten ``[(RetrievalResult, PreparedRecord), ...]`` to two DataFrames."""
    spectral, scalar = [], []
    for result, record in pairs:
        spectral.extend(_spectral_rows(result, record))
        scalar.append(_scalar_row(result, record))
    spectral_df, scalar_df = pd.DataFrame(spectral), pd.DataFrame(scalar)
    _harmonize_obs_id(spectral_df, scalar_df)
    return spectral_df, scalar_df


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

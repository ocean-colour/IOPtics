"""Dataset registry: thin adapters over ocpy loaders (+ bing for L23 truth).

Maps a dataset name (``'L23'`` | ``'PANGAEA'`` | ``'GLORIA'`` | ``'PACE'``) to an adapter
that enumerates observation ids and returns one observation's ``Rrs`` + truth
IOPs on the dataset's **native wavelength grid**. This module reads observations
via ocpy and, for the synthetic L23 dataset, reuses bing's canonical truth
extraction (``bing.fitting.l23.load_one_l23``) rather than re-deriving it.

An adapter returns a lightweight :class:`RawObs` carrier (raw arrays + a truth
dict + metadata). :mod:`ioptics.prep` turns that into the public
:class:`~ioptics.records.PreparedRecord` — attaching ``Rrs`` uncertainty,
pre-aligning spectral truth onto ``wave``, and computing the truth-free
``init`` values. No model/prior/RT work happens here.

Stage 1 implements the **L23** adapter (Loisel et al. 2023 Hydrolight); Stage 6
adds the **PANGAEA** in-situ adapter (GLORIA follows). Stage 7's RT comparison
adds **PACE** — 100 real PACE OCI pixels, which unlike the others is read from
a pre-extracted artifact rather than through ocpy (see :class:`PACEAdapter`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np


@dataclass
class RawObs:
    """One observation as loaded from a dataset, before IOPtics conditioning.

    Internal carrier produced by an :class:`Adapter` and consumed by
    :mod:`ioptics.prep`. Spectral truth values are plain numpy arrays on
    ``wave``; scalar truth values are floats. Prep later wraps the spectral
    components as ocpy ``Spectrum`` objects aligned to ``wave``.

    Parameters
    ----------
    wave : numpy.ndarray
        Native wavelength grid (nm), ascending.
    Rrs : numpy.ndarray
        Remote-sensing reflectance [sr^-1] on ``wave`` (un-perturbed; any
        synthetic noise is added later by :mod:`ioptics.noise`).
    truth : dict
        Truth components keyed by IOPtics name. A **spectral** component
        (``'a'``, ``'bb'``, ``'a_ph'``, ``'a_dg'``, ``'bb_p'``, ``'a_w'``,
        ``'bb_w'``) is either a plain array on ``wave`` (when the dataset
        provides every component on the observation's grid, e.g. L23) **or** a
        ``(src_wave, values)`` pair when the component lives on its own native
        wavelength set (e.g. PANGAEA's per-family ``a_ph``/``a_dg``/``bb_p``);
        :mod:`ioptics.prep` aligns either form onto ``wave``. **Scalar**
        components (``'Chl'``, ``'Y'``, ``'Sdg'``, ``'tss'``) are floats.
        ``{}`` when the dataset provides no truth; missing components are simply
        absent (prep/metrics report per-component coverage).
    Rrs_err : numpy.ndarray or None, optional
        Measured ``Rrs`` uncertainty if the dataset carries it (in-situ
        sources); ``None`` for synthetic datasets such as L23.
    meta : dict, optional
        Free-form metadata (e.g. L23 ``X``/``Y`` load options, ``obs_id``).
    """

    wave:    np.ndarray
    Rrs:     np.ndarray
    truth:   dict
    Rrs_err: np.ndarray | None = None
    meta:    dict = field(default_factory=dict)


# --- registry ---------------------------------------------------------------

# --- observation-geometry metadata contract ---------------------------------
#
# The three ``RawObs.meta`` keys that let :func:`ioptics.run.resolve_theta_s`
# compute a record's solar zenith (and hence its ``bing.rt.geometry``
# ``ObsGeometry``) for a robust RT backend. Named here, and imported by
# :mod:`ioptics.run`, so the adapter side and the consumer side cannot drift
# apart on a spelling. An adapter that knows none of them (L23 is synthetic —
# it has no place and no time) simply omits them, and a robust-backend fit of
# such a record raises rather than assuming an angle.

#: ``meta`` key for the observation's UTC timestamp (anything
#: ``robust.solar.solar_zenith`` accepts: ``datetime``, ISO-8601 string,
#: ``numpy.datetime64``, ``pandas.Timestamp``).
TIME_META_KEY = 'time'
#: ``meta`` key for the observation latitude, degrees north.
LAT_META_KEY = 'lat'
#: ``meta`` key for the observation longitude, degrees east.
LON_META_KEY = 'lon'

ADAPTERS: dict = {}                     # name -> Adapter instance


def register_dataset(name, adapter):
    """Register an :class:`Adapter` under a dataset ``name``."""
    ADAPTERS[name] = adapter


def get_adapter(name):
    """Return the adapter registered for ``name`` (e.g. ``'L23'``)."""
    return ADAPTERS[name]


def available_datasets():
    """Return the sorted list of registered dataset names."""
    return sorted(ADAPTERS)


@runtime_checkable
class Adapter(Protocol):
    """The interface every dataset adapter implements."""

    def obs_ids(self, **opts) -> list:
        """Enumerate the available observation ids."""
        ...

    def load_obs(self, obs_id, **opts) -> RawObs:
        """Load one observation as a :class:`RawObs` on its native grid."""
        ...


# --- L23 adapter ------------------------------------------------------------

# bing's load_one_l23 returns these dict keys; map them onto IOPtics truth keys.
_L23_TRUTH_MAP = {
    'a':    'a',
    'bb':   'bb',
    'aph':  'a_ph',
    'adg':  'a_dg',
    'bbnw': 'bb_p',
    'aw':   'a_w',
    'bbw':  'bb_w',
    'Chl':  'Chl',     # scalar
    'Y':    'Y',       # scalar (Lee 2002 backscatter slope)
    'Sdg':  'Sdg',     # scalar
}


class L23Adapter:
    """Adapter for the Loisel et al. (2023) synthetic Hydrolight dataset.

    Loads the dataset via ``ocpy.hydrolight.loisel23.load_ds(X, Y)`` (cached per
    ``(X, Y)`` so a batch reads the NetCDF once) and extracts each row's ``Rrs``
    + full truth using bing's canonical ``bing.fitting.l23.load_one_l23`` on the
    native Hydrolight grid.

    The ``X``/``Y`` load options (``X``: 1 = elastic first pass, 4 = +Raman/Chl
    fluorescence, never 2; ``Y``: solar-zenith index 00/30/60) are adapter
    options, recorded in ``meta`` for provenance.
    """

    def __init__(self):
        self._cache: dict = {}          # (X, Y) -> xarray.Dataset

    def _load_ds(self, X, Y):
        if X == 2:
            raise ValueError(
                "L23 X=2 (Raman-only) is not used by IOPtics; use X=1 or X=4")
        key = (X, Y)
        if key not in self._cache:
            from ocpy.hydrolight import loisel23
            self._cache[key] = loisel23.load_ds(X, Y)
        return self._cache[key]

    def obs_ids(self, X=1, Y=0, **opts):
        """Row indices ``0 .. N-1`` of the L23 dataset for these ``(X, Y)``."""
        ds = self._load_ds(X, Y)
        return list(range(ds.Rrs.shape[0]))

    def load_obs(self, obs_id, X=1, Y=0, **opts):
        """Load L23 row ``obs_id`` as a :class:`RawObs` on the native grid."""
        from bing.fitting import l23 as bing_l23

        ds = self._load_ds(X, Y)
        idx = int(obs_id)

        # bing's canonical L23 extraction (native grid; full spectral + scalar
        # truth incl. Chl, Lee-2002 Y, and the a_dg slope Sdg).
        odict = bing_l23.load_one_l23(idx, ds=ds)

        truth = {ipt_key: odict[bkey] for bkey, ipt_key in _L23_TRUTH_MAP.items()}
        # scalars as plain floats
        for s in ('Chl', 'Y', 'Sdg'):
            truth[s] = float(truth[s])

        # meta['Y'] is the solar-zenith *load option*, distinct from truth['Y']
        # (the Lee-2002 backscatter slope).
        meta = {'dataset': 'L23', 'obs_id': idx, 'X': X, 'Y': Y}

        return RawObs(wave=np.asarray(odict['wave'], dtype=float),
                      Rrs=np.asarray(odict['Rrs'], dtype=float),
                      truth=truth, Rrs_err=None, meta=meta)


# --- PANGAEA adapter --------------------------------------------------------

# ocpy.insitu.pangaea spectral family ('kind') -> IOPtics truth key.
_PANGAEA_TRUTH_KINDS = {
    'aph':   'a_ph',    # algal pigment absorption [1/m]
    'acdom': 'a_dg',    # CDOM + detrital absorption [1/m] (combined -> a_dg)
    'bbp':   'bb_p',    # particulate backscatter [1/m]
}

# Columns of ocpy's tidy PANGAEA ``rrs`` table that carry the observation's
# place and time. ocpy renames PANGAEA's own ``Date/Time`` / ``Latitude`` /
# ``Longitude`` headers to these friendly names and parses ``date_time`` to
# real timestamps (``ocpy.insitu.pangaea``), so no string parsing happens here.
_PANGAEA_TIME_COL = 'date_time'
_PANGAEA_LAT_COL = 'lat'
_PANGAEA_LON_COL = 'lon'


def _finite(x):
    """True if ``x`` is a real, finite number (guards NaN / None cells)."""
    try:
        return x is not None and np.isfinite(float(x))
    except (TypeError, ValueError):
        return False


class PANGAEAAdapter:
    """Adapter for the PANGAEA V3 (Valente et al. 2022) in-situ compilation.

    Loads the tidy ``rrs`` / ``iop`` / ``chla`` tables via
    :mod:`ocpy.insitu.pangaea` (each cached after first use). An observation is
    a global ``ID``; its ``Rrs`` and each IOP family (``aph``/``acdom``/``bbp``)
    live on their **own** native wavelength set, so spectral truth is returned
    as ``(src_wave, values)`` pairs for :mod:`ioptics.prep` to align onto
    ``wave``. Chlorophyll (HPLC, falling back to fluorometric) is returned as
    the scalar ``Chl`` and total suspended matter as ``tss``.

    Enumeration is **permissive** (design Q12): every ``ID`` whose ``Rrs`` has
    at least ``min_rrs`` finite bands (default 5) is returned, even if it lacks
    some truth components. PANGAEA V3 carries no per-band ``Rrs`` uncertainty,
    so ``Rrs_err`` is ``None`` and :mod:`ioptics.prep` falls back from the
    ``'insitu'`` default to a **flat 10% fractional** noise model for the fit
    weights (see :mod:`ioptics.prep`; 5% until 2026-08-10).
    """

    def __init__(self, path=None):
        self._path = path               # explicit V3 dir; else ocpy resolves it
        self._tables: dict = {}         # catalog key -> DataFrame

    def _table(self, key):
        if key not in self._tables:
            from ocpy.insitu import pangaea
            self._tables[key] = pangaea.load(key, path=self._path)
        return self._tables[key]

    def obs_ids(self, min_rrs=5, **opts):
        """Global ``ID`` values with at least ``min_rrs`` finite ``Rrs`` bands.

        ``min_rrs`` defaults to 5 — permissive (design Q12) yet enough bands to
        seed a fit; pass ``min_rrs=1`` for the fully-permissive set.
        """
        from ocpy.insitu import pangaea
        rrs = self._table('rrs')
        counts = pangaea.n_spectral(rrs, kind='rrs')
        return list(counts.index[counts >= int(min_rrs)])

    def load_obs(self, obs_id, **opts):
        """Load PANGAEA observation ``obs_id`` as a :class:`RawObs`.

        ``Rrs`` is on its native grid; spectral truth components are returned
        as ``(src_wave, values)`` pairs on their own per-family grids (only the
        components actually present for this ``ID``). Scalars ``Chl``/``tss``
        are attached when available.
        """
        from ocpy.insitu import pangaea

        rrs = self._table('rrs')
        rrs_spec = pangaea.spectrum(rrs, obs_id, kind='rrs')
        wave = np.asarray(rrs_spec.index, dtype=float)
        Rrs = np.asarray(rrs_spec.to_numpy(), dtype=float)

        truth: dict = {}
        # Spectral IOP truth on per-family native grids (present ones only).
        iop = self._table('iop')
        if obs_id in iop.index:
            for kind, ipt_key in _PANGAEA_TRUTH_KINDS.items():
                s = pangaea.spectrum(iop, obs_id, kind=kind)
                if len(s) > 0:
                    truth[ipt_key] = (np.asarray(s.index, dtype=float),
                                      np.asarray(s.to_numpy(), dtype=float))
            if 'tss' in iop.columns and _finite(iop.at[obs_id, 'tss']):
                truth['tss'] = float(iop.at[obs_id, 'tss'])

        chl = self._chl(obs_id)
        if chl is not None:
            truth['Chl'] = chl

        meta = {'dataset': 'PANGAEA', 'obs_id': obs_id}
        meta.update(self._ancillary(rrs, obs_id))

        return RawObs(wave=wave, Rrs=Rrs, truth=truth, Rrs_err=None, meta=meta)

    def _chl(self, obs_id):
        """Merged chlorophyll scalar (HPLC preferred, then fluorometric)."""
        chla = self._table('chla')
        if obs_id not in chla.index:
            return None
        row = chla.loc[obs_id]
        for col in ('chla_hplc', 'chla_fluor', 'chla'):
            if col in chla.columns and _finite(row[col]):
                return float(row[col])
        return None

    def _ancillary(self, rrs, obs_id):
        """Best-effort provenance from the rrs table row.

        ``subdataset`` (the cruise, e.g. ``'nomad_en372'``) and
        ``contributor`` (the PI/instrument group, inherited from SeaBASS via
        NOMAD) ride along since 2026-08-12 (PANGAEA investigation Task-4 B2,
        approved by JXP): the investigation found retrieval coverage
        stratifies hard on both — per-cruise ok-rates span 0–100% and
        per-contributor 0–72% at ~100% convergence — and had to join them
        from the source table by hand. Persisting them on ``results_scalar``
        makes per-source coverage a groupby.

        ``date_time`` is emitted **twice**: as ``date`` (the pre-existing
        provenance key) and as :data:`TIME_META_KEY` (``'time'``), the
        observation-geometry contract :func:`ioptics.run.resolve_theta_s`
        reads alongside :data:`LAT_META_KEY` / :data:`LON_META_KEY` to compute
        the solar zenith for a robust RT backend. One name is the record's
        provenance, the other is a fit input; keeping them separate means a
        later change to either cannot silently move the other.
        """
        out: dict = {}
        if obs_id in rrs.index:
            row = rrs.loc[obs_id]
            for col, mkey in ((_PANGAEA_LAT_COL, LAT_META_KEY),
                              (_PANGAEA_LON_COL, LON_META_KEY),
                              ('depth_m', 'depth'),
                              (_PANGAEA_TIME_COL, 'date'),
                              (_PANGAEA_TIME_COL, TIME_META_KEY),
                              ('subdataset', 'subdataset'),
                              ('contributor', 'contributor')):
                if col in rrs.columns:
                    out[mkey] = row[col]
        return out


# --- GLORIA adapter ---------------------------------------------------------

_GLORIA_ID = 'GLORIA_ID'            # per-observation id column in the meta table

# GLORIA meta-table scalar column -> IOPtics scalar truth key. ``aCDOM440`` is
# handled separately (mapped to a single-point ``a_dg`` truth, below).
_GLORIA_SCALARS = {
    'Chla':         'Chl',          # chlorophyll-a [mg m^-3] (scored as Chl)
    'TSS':          'tss',          # total suspended solids [g m^-3]
    'Secchi_depth': 'Secchi',       # Secchi depth [m]
}
_GLORIA_ACDOM = 'aCDOM440'          # CDOM absorption at 440 nm [1/m]


class GLORIAAdapter:
    """Adapter for the GLORIA (Lehmann et al. 2023) hyperspectral in-situ set.

    Loads via ``ocpy.insitu.gloria.load_gloria`` (the CSVs are large and are
    **not** bundled with ocpy — download per its data README; tests are
    ``@needs_gloria`` skip-guarded). ``Rrs`` (mean) and its per-band standard
    deviation are parsed with ``gloria.parse_table`` onto the native 350–900 nm
    grid; the std gives a genuine ``insitu`` fit weight (``varRrs = Rrs_std**2``,
    ``add_noise=False``).

    GLORIA truth is **scalar only** — CDOM absorption at 440 nm (``aCDOM440``),
    chlorophyll (``Chla`` -> ``Chl``), ``TSS`` (-> ``tss``) and ``Secchi``. The
    one IOP it constrains, CDOM at 440 nm, is exposed as a **single-point**
    ``a_dg`` truth at 440 nm (``(array([440.]), array([aCDOM440]))``, ``NaN``
    elsewhere) so the existing machinery grades a retrieved ``a_dg(440)`` against
    it and derives ``a_cdom440_truth``. This assumes 440 nm is on the record grid
    — always true for GLORIA's native 1 nm grid; keep 440 nm inside any
    ``[wv_min, wv_max]`` trim so the comparison survives. Because the dataset is
    named ``GLORIA``,
    :func:`ioptics.metrics._caveat` auto-stamps ``caveat='CDOM_vs_adg'`` on those
    ``a_dg`` rows — GLORIA reports CDOM only, whereas ``a_dg`` is CDOM+detritus.
    """

    def __init__(self):
        self._loaded = None         # (meta_by_id, wave, Rrs, Rrs_std, ids)

    def _load(self):
        if self._loaded is None:
            from ocpy.insitu import gloria
            df_meta, df_rrs, df_rrs_std, _qc = gloria.load_gloria()
            wv, rrs, _ = gloria.parse_table(df_rrs, 'Rrs')
            _, rrs_std, _ = gloria.parse_table(df_rrs_std, 'Rrs_std')
            ids = np.asarray(df_meta[_GLORIA_ID].to_numpy())
            # rows of df_meta align positionally with the parsed spectra columns
            self._loaded = (df_meta.set_index(_GLORIA_ID), np.asarray(wv, float),
                            np.asarray(rrs, float), np.asarray(rrs_std, float),
                            ids)
        return self._loaded

    def obs_ids(self, **opts):
        """Every GLORIA observation id (global ``GLORIA_ID``)."""
        _, _, _, _, ids = self._load()
        return list(ids)

    def load_obs(self, obs_id, **opts):
        """Load GLORIA observation ``obs_id`` as a :class:`RawObs`.

        Hyperspectral ``Rrs`` on the native grid with its measured std as
        ``Rrs_err``; scalar lab truth mapped to IOPtics keys, with ``aCDOM440``
        exposed as a single-point ``a_dg`` truth at 440 nm.
        """
        meta, wv, rrs_all, std_all, ids = self._load()
        j = int(np.flatnonzero(ids == obs_id)[0])

        # native grid, ascending, finite Rrs only (std aligned to the same mask)
        wave = wv.copy()
        rrs = rrs_all[:, j]
        std = std_all[:, j]
        order = np.argsort(wave)
        wave, rrs, std = wave[order], rrs[order], std[order]
        finite = np.isfinite(rrs)
        wave, rrs, std = wave[finite], rrs[finite], std[finite]

        row = meta.loc[obs_id]
        truth: dict = {}
        # CDOM at 440 nm -> single-point a_dg truth (drives the caveat + a_cdom440).
        if _GLORIA_ACDOM in meta.columns and _finite(row[_GLORIA_ACDOM]):
            truth['a_dg'] = (np.array([440.0]),
                             np.array([float(row[_GLORIA_ACDOM])]))
        for col, key in _GLORIA_SCALARS.items():
            if col in meta.columns and _finite(row[col]):
                truth[key] = float(row[col])

        meta_out = {'dataset': 'GLORIA', 'obs_id': obs_id}
        return RawObs(wave=wave, Rrs=rrs, truth=truth,
                      Rrs_err=std, meta=meta_out)


# --- PACE adapter -----------------------------------------------------------

#: Location of the PACE artifact, relative to ``$OS_COLOR/IOPtics``. Kept in
#: sync with ``ioptics/runs/prototypes/rt_tests/extract_pace_100.py``, which
#: writes it (``OUT_SUBDIR`` / ``OUT_FILE`` there).
PACE_PAB_SUBDIR = 'pace_pab_100'
PACE_PAB_FILE = 'pace_pab_100.parquet'

#: Per-spectrum ``meta`` columns of the artifact that ride onto ``RawObs.meta``
#: under the same names. The three geometry-contract keys are named via the
#: ``*_META_KEY`` constants so a rename cannot desync the adapter from
#: :func:`ioptics.run.resolve_theta_s`; the rest are join/provenance columns.
_PACE_META_COLS = (TIME_META_KEY, LAT_META_KEY, LON_META_KEY,
                   'theta_s', 'wmo', 'cycle', 'granule', 'ix', 'iy',
                   'matchup_id', 'distance_km', 'rank', 'flagged')


def pace_pab_path(path=None):
    """Resolve the PACE artifact path.

    ``path`` when given (a file, or a directory holding
    :data:`PACE_PAB_FILE`), else ``$OS_COLOR/IOPtics/pace_pab_100/
    pace_pab_100.parquet``. Raises :class:`RuntimeError` when neither is
    available — the path is *resolved* here, not checked for existence.
    """
    if path is not None:
        path = Path(path)
        return path / PACE_PAB_FILE if path.is_dir() else path
    osc = os.getenv('OS_COLOR')
    if not osc:
        raise RuntimeError(
            'PACE artifact unresolved: set $OS_COLOR or pass path= '
            f'(expected <$OS_COLOR>/IOPtics/{PACE_PAB_SUBDIR}/{PACE_PAB_FILE})')
    return Path(osc) / 'IOPtics' / PACE_PAB_SUBDIR / PACE_PAB_FILE


class PACEAdapter:
    """Adapter for 100 real PACE OCI spectra drawn from the PAB run1k archive.

    Unlike the other adapters this one reads **no** upstream package: the
    spectra, their per-pixel uncertainties and their geolocation were joined
    out of PAB's chain archive and its ``pab.db`` catalogue once, by
    ``ioptics/runs/prototypes/rt_tests/extract_pace_100.py``, into a single
    tidy parquet under ``$OS_COLOR/IOPtics/pace_pab_100/``. IOPtics therefore
    depends on neither ``pab`` (not pip-installed) nor the PACE granules
    themselves (design Q23).

    Each observation is one PACE pixel matched to an Argo BGC profile: 136
    bands over 400-699 nm (the OCI 588-613 nm gap is simply absent from the
    grid), the V3_2 L2 ``Rrs``, and the granule's own per-band ``Rrs_unc**2``
    as ``varRrs`` — PAB's 2%-of-``Rrs`` floor already applied where the
    granule's value was unusable. The adapter hands that back as
    ``Rrs_err = sqrt(varRrs)``, which is the signal
    :func:`ioptics.prep.prep_one` reads as *measured* noise: with the
    in-situ default (``noise='insitu'``, ``add_noise=False``) the record's
    ``varRrs`` is exactly the stored one and the provenance tag is the bare
    ``'insitu'`` — no floor, no imputation, unlike GLORIA.

    There is **no truth** (``truth == {}``): these are satellite observations,
    so a PACE sweep scores model selection and closure, never accuracy
    (design Q26). Negative ``Rrs`` bands are kept, per Q24.

    ``meta`` carries the observation-geometry contract (:data:`TIME_META_KEY`
    / :data:`LAT_META_KEY` / :data:`LON_META_KEY`) so a robust RT backend can
    resolve the solar zenith per pixel (Q17), alongside the ``theta_s``
    computed at extraction time. The two are redundant on purpose: the
    runtime path recomputes via :func:`ioptics.run.resolve_theta_s`, and the
    stored value exists so a test (and a reader) can check the recomputation
    against what the artifact was built with. Viewing geometry is taken as
    nadir (Q37) — neither source stores the sensor angles.

    Parameters
    ----------
    path : str or pathlib.Path or None, optional
        Explicit artifact file (or its directory); ``None`` resolves via
        ``$OS_COLOR`` (:func:`pace_pab_path`).
    """

    def __init__(self, path=None):
        self._path = path
        self._by_obs = None             # obs_id -> DataFrame (wavelength-sorted)

    def _load(self):
        """Read + group the artifact once, keyed by ``obs_id``."""
        if self._by_obs is None:
            import pandas as pd

            path = pace_pab_path(self._path)
            if not Path(path).is_file():
                raise FileNotFoundError(
                    f'PACE artifact not found at {path}. Build it with '
                    'ioptics/runs/prototypes/rt_tests/extract_pace_100.py '
                    '(needs the PAB run1k archive), or pass '
                    'PACEAdapter(path=...).')
            df = pd.read_parquet(path).sort_values(['obs_id', 'wavelength'])
            self._by_obs = {str(oid): grp
                            for oid, grp in df.groupby('obs_id', sort=True)}
        return self._by_obs

    def obs_ids(self, **opts):
        """The sampled observation ids (chain-file stems), sorted."""
        return sorted(self._load())

    def load_obs(self, obs_id, **opts):
        """Load PACE observation ``obs_id`` as a :class:`RawObs`.

        ``Rrs_err`` is ``sqrt(varRrs)`` from the granule, so prep's ``insitu``
        weighting reproduces the stored variance exactly; ``truth`` is empty.
        """
        by_obs = self._load()
        key = str(obs_id)
        if key not in by_obs:
            raise KeyError(
                f'{obs_id!r} is not a PACE observation '
                f'({len(by_obs)} available; ids are run1k chain-file stems)')
        grp = by_obs[key]

        wave = np.asarray(grp['wavelength'].to_numpy(), dtype=float)
        Rrs = np.asarray(grp['Rrs'].to_numpy(), dtype=float)
        varRrs = np.asarray(grp['varRrs'].to_numpy(), dtype=float)

        row = grp.iloc[0]
        meta = {'dataset': 'PACE', 'obs_id': key}
        for col in _PACE_META_COLS:
            if col in grp.columns:
                val = row[col]
                meta[col] = val.item() if hasattr(val, 'item') else val

        return RawObs(wave=wave, Rrs=Rrs, truth={},
                      Rrs_err=np.sqrt(varRrs), meta=meta)


# Seed the registry with the L23 adapter (Stage 1), the PANGAEA + GLORIA
# in-situ adapters (Stage 6), and the PACE satellite adapter (Stage 7).
register_dataset('L23', L23Adapter())
register_dataset('PANGAEA', PANGAEAAdapter())
register_dataset('GLORIA', GLORIAAdapter())
register_dataset('PACE', PACEAdapter())

"""Dataset registry: thin adapters over ocpy loaders (+ bing for L23 truth).

Maps a dataset name (``'L23'`` | ``'PANGAEA'`` | ``'GLORIA'``) to an adapter
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
adds the **PANGAEA** in-situ adapter (GLORIA follows).
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    at least ``min_rrs`` finite bands is returned, even if it lacks some truth
    components. PANGAEA V3 carries no per-band ``Rrs`` uncertainty, so
    ``Rrs_err`` is ``None`` and :mod:`ioptics.prep` falls back from the
    ``'insitu'`` default to a fractional noise model for the fit weights.
    """

    def __init__(self, path=None):
        self._path = path               # explicit V3 dir; else ocpy resolves it
        self._tables: dict = {}         # catalog key -> DataFrame

    def _table(self, key):
        if key not in self._tables:
            from ocpy.insitu import pangaea
            self._tables[key] = pangaea.load(key, path=self._path)
        return self._tables[key]

    def obs_ids(self, min_rrs=1, **opts):
        """Global ``ID``s with at least ``min_rrs`` finite ``Rrs`` bands."""
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
        """Best-effort lat/lon/depth/date provenance from the rrs table row."""
        out: dict = {}
        if obs_id in rrs.index:
            row = rrs.loc[obs_id]
            for col, mkey in (('lat', 'lat'), ('lon', 'lon'),
                              ('depth_m', 'depth'), ('date_time', 'date')):
                if col in rrs.columns:
                    out[mkey] = row[col]
        return out


# Seed the registry with the L23 adapter (Stage 1) and the PANGAEA adapter
# (Stage 6).
register_dataset('L23', L23Adapter())
register_dataset('PANGAEA', PANGAEAAdapter())

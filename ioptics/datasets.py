"""Dataset registry: thin adapters over ocpy loaders.

Maps a dataset name (``'L23'`` | ``'PANGAEA'`` | ``'GLORIA'``) to an adapter
that enumerates observation ids and returns one observation's ``Rrs`` + truth
IOPs on the dataset's **native wavelength grid**. With :mod:`ioptics.noise`,
this is the only module that imports ocpy; nothing downstream of
:mod:`ioptics.prep` imports it.

An adapter returns a lightweight :class:`RawObs` carrier (raw arrays + a truth
dict + metadata). :mod:`ioptics.prep` turns that into the public
:class:`~ioptics.records.PreparedRecord` — attaching ``Rrs`` uncertainty,
pre-aligning spectral truth onto ``wave``, and computing the truth-free
``init`` values. No model/prior/RT work happens here.

Stage 1 implements the **L23** adapter (Loisel et al. 2023 Hydrolight);
PANGAEA and GLORIA are added in Stage 6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import numpy as np

# --- Gordon Rrs <-> rrs relation (Lee et al. 2002 / Gordon et al. 1988) ------
# Mirrors bing.rt.rrs.{A_Rrs, B_Rrs}. Replicated here (rather than importing
# bing) so the data layer stays ocpy-only per the dependency boundary.
A_RRS, B_RRS = 0.52, 1.7


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
        Truth components keyed by IOPtics name. Spectral components
        (``'a'``, ``'bb'``, ``'a_ph'``, ``'a_dg'``, ``'bb_p'``, ``'a_w'``,
        ``'bb_w'``) are arrays on ``wave``; scalars (``'Chl'``, ``'Y'``,
        ``'Sdg'``) are floats. ``{}`` when the dataset provides no truth.
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


# --- truth helpers (replicated from bing, see module note) ------------------

def _lee2002_Y(wave, Rrs):
    """Backscatter spectral slope ``Y`` via the Lee et al. (2002) band ratio.

    Generalizes the prescription in ``bing.fitting.l23.load_one_l23``: convert
    ``Rrs`` to subsurface ``rrs`` (Gordon) and form the 440/555 ratio.
    """
    rrs = Rrs / (A_RRS + B_RRS * Rrs)
    i440 = int(np.argmin(np.abs(wave - 440.)))
    i555 = int(np.argmin(np.abs(wave - 555.)))
    return float(2.2 * (1.0 - 1.2 * np.exp(-0.9 * rrs[i440] / rrs[i555])))


def _fit_Sdg(wave, a_dg, wv_min=400., wv_max=525., pivot=440.):
    """Spectral slope ``Sdg`` of dissolved+detrital absorption.

    Replicates ``bing.models.functions.fit_Sdg``: a least-squares fit of
    ``A * exp(-Sdg * (wave - pivot))`` to ``a_dg`` over ``[wv_min, wv_max]``.
    Returns ``Sdg`` (or ``nan`` if the fit fails).
    """
    from scipy.optimize import curve_fit

    def _exp(x, A, S):
        return A * np.exp(-S * (x - pivot))

    cut = (wave > wv_min) & (wave < wv_max)
    ipiv = int(np.argmin(np.abs(wave - pivot)))
    try:
        ans, _ = curve_fit(_exp, wave[cut], a_dg[cut], p0=[a_dg[ipiv], 0.015])
        return float(ans[1])
    except Exception:
        return float('nan')


# --- L23 adapter ------------------------------------------------------------

class L23Adapter:
    """Adapter for the Loisel et al. (2023) synthetic Hydrolight dataset.

    Wraps ``ocpy.hydrolight.loisel23.load_ds(X, Y)`` and returns each row's
    ``Rrs`` plus full spectral + scalar truth on the native Hydrolight grid.
    The loaded dataset is cached per ``(X, Y)`` so a batch over many rows reads
    the NetCDF once.

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
        ds = self._load_ds(X, Y)
        idx = int(obs_id)

        wave = ds.Lambda.data
        Rrs = ds.Rrs.data[idx]
        a = ds.a.data[idx]
        bb = ds.bb.data[idx]
        aph = ds.aph.data[idx]
        a_dg = ds.ag.data[idx] + ds.ad.data[idx]
        anw = ds.anw.data[idx]
        bbnw = ds.bbnw.data[idx]

        i440 = int(np.argmin(np.abs(wave - 440.)))
        truth = {
            # spectral components (arrays on the native grid)
            'a':    a,
            'bb':   bb,
            'a_ph': aph,
            'a_dg': a_dg,
            'bb_p': bbnw,
            'a_w':  a - anw,
            'bb_w': bb - bbnw,
            # scalar components
            'Chl':  float(aph[i440] / 0.05582),     # L23 convention
            'Y':    _lee2002_Y(wave, Rrs),          # Lee et al. 2002
            'Sdg':  _fit_Sdg(wave, a_dg),           # exp slope of a_dg
        }
        # meta['Y'] is the solar-zenith *load option*, distinct from truth['Y']
        # (the Lee-2002 backscatter slope).
        meta = {'dataset': 'L23', 'obs_id': idx, 'X': X, 'Y': Y}

        return RawObs(wave=np.asarray(wave, dtype=float),
                      Rrs=np.asarray(Rrs, dtype=float),
                      truth=truth, Rrs_err=None, meta=meta)


# Seed the registry with the L23 adapter (Stage 1).
register_dataset('L23', L23Adapter())

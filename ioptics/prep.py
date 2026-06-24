"""Dataset-agnostic prep layer (generalizes ``bing.fitting.l23.prep_one_l23``).

Takes a loaded observation (via a :mod:`ioptics.datasets` adapter), attaches
``Rrs`` uncertainty (:mod:`ioptics.noise`), pre-aligns each spectral truth
component onto the observation's native ``wave``, derives the truth-free
``init`` values from the observed ``Rrs``, and assembles a
:class:`~ioptics.records.PreparedRecord`. It does **no** model/prior/RT work —
that is the algorithm's job at run time (:mod:`ioptics.run`).

Prep is the last layer that touches ocpy/bing on the data side: it wraps
spectral truth as ocpy ``Spectrum`` objects (pre-aligned to ``wave``, with the
original grid kept in ``metadata['orig_wave']``) and seeds ``init`` from
``ocpy.chl.band_ratios`` + the Lee (2002) backscatter-slope prescription.
Everything downstream of a :class:`~ioptics.records.PreparedRecord` is
data-source-agnostic.
"""

from __future__ import annotations

import numpy as np

from ioptics.datasets import get_adapter
from ioptics.noise import attach_noise
from ioptics.records import PreparedRecord


def _align_truth(src_wave, src_vals, wave):
    """Align one spectral truth component from its native grid onto ``wave``.

    Returns ``(values_on_wave, was_interpolated)``. If ``wave`` is the native
    grid (or an exact subset of it, e.g. a trim) the values are taken exactly
    and ``was_interpolated`` is ``False``; otherwise the component is linearly
    interpolated onto ``wave`` with out-of-range points left ``NaN`` (never
    extrapolated) and the flag is ``True``.
    """
    src_wave = np.asarray(src_wave, dtype=float)
    src_vals = np.asarray(src_vals, dtype=float)
    if src_wave.shape == wave.shape and np.allclose(src_wave, wave):
        return src_vals.copy(), False
    aligned = np.interp(wave, src_wave, src_vals, left=np.nan, right=np.nan)
    # An exact subset (a wavelength trim) is not a regrid.
    interpolated = not np.all(np.isin(wave, src_wave))
    return aligned, interpolated


def _build_truth(raw, wave):
    """Build the ``truth`` / ``truth_interp`` dicts for a record on ``wave``.

    Spectral components become ocpy ``Spectrum`` objects pre-aligned to
    ``wave`` (native grid retained in ``metadata['orig_wave']``); scalar
    components become plain floats.
    """
    from ocpy.spectra import Spectrum

    src_wave = np.asarray(raw.wave, dtype=float)
    truth, truth_interp = {}, {}
    for key, val in raw.truth.items():
        arr = np.asarray(val)
        if arr.ndim == 0:                                  # scalar component
            truth[key] = float(val)
            truth_interp[key] = False
        else:                                              # spectral component
            aligned, interpolated = _align_truth(src_wave, arr, wave)
            truth[key] = Spectrum(wave, aligned, units='1/m',
                                  metadata={'orig_wave': src_wave})
            truth_interp[key] = interpolated
    return truth, truth_interp


def _init_from_rrs(wave, Rrs):
    """Truth-free model-init values from the *observed* ``Rrs``.

    ``Chl`` via the OC4 band ratio (``ocpy.chl.band_ratios.oc4``) and ``Y`` via
    bing's Lee (2002) ``bbnw`` model: convert ``Rrs`` to subsurface ``rrs``
    (``bing.rt.rrs.Rrs_to_rrs``) and let ``bbNWLee.compute_Y`` evaluate the
    440/555 backscatter slope, so the prescription stays in lock-step with bing
    (rather than duplicating the formula here). These seed the least-squares
    starting guess at run time without peeking at truth.
    """
    from ocpy.chl import band_ratios
    from bing.rt.rrs import Rrs_to_rrs
    from bing.models import bbnw

    Chl = float(band_ratios.oc4(wave, Rrs))

    rrs = np.asarray(Rrs_to_rrs(Rrs), dtype=float)
    i440 = int(np.argmin(np.abs(wave - 440.)))
    i555 = int(np.argmin(np.abs(wave - 555.)))
    lee = bbnw.init_model('Lee', np.asarray(wave, dtype=float), prior_dicts=None)
    lee.compute_Y(rrs[i440], rrs[i555])      # sets lee.Y (Lee et al. 2002)
    Y = float(lee.Y)

    return {'Chl': Chl, 'Y': Y}


def prep_one(dataset, obs_id, *, noise=None, add_noise=None, seed=None,
             wv_min=None, wv_max=None, **load_opts):
    """Prepare one observation into a :class:`~ioptics.records.PreparedRecord`.

    Loads the observation on its native grid via the dataset adapter, optionally
    trims to ``[wv_min, wv_max]``, attaches ``varRrs`` (and, for synthetic
    datasets, perturbs ``Rrs``), pre-aligns spectral truth onto ``wave``, and
    derives truth-free ``init``. No model/prior/RT work.

    Parameters
    ----------
    dataset : str
        Registered dataset name (e.g. ``'L23'``).
    obs_id : int or str
        Observation identifier for the dataset's adapter.
    noise : str or None, optional
        Noise model passed to :func:`ioptics.noise.attach_noise`. Defaults to
        ``'pace'`` for L23 (synthetic) and ``'insitu'`` otherwise.
    add_noise : bool or None, optional
        Whether to perturb ``Rrs``. Defaults to ``True`` for L23 and ``False``
        for in-situ datasets (their ``Rrs`` is already a real observation).
    seed : int or None, optional
        RNG seed for the perturbation (recorded in ``noise_seed``).
    wv_min, wv_max : float or None, optional
        Optional native-grid wavelength trim.
    **load_opts
        Adapter load options (e.g. L23 ``X``, ``Y``).

    Returns
    -------
    PreparedRecord
    """
    if noise is None:
        noise = 'pace' if dataset == 'L23' else 'insitu'
    if add_noise is None:
        add_noise = (dataset == 'L23')

    raw = get_adapter(dataset).load_obs(obs_id, **load_opts)

    # Native grid + optional trim (applied identically to Rrs and any errors).
    wave_full = np.asarray(raw.wave, dtype=float)
    mask = np.ones(wave_full.shape, dtype=bool)
    if wv_min is not None:
        mask &= wave_full >= wv_min
    if wv_max is not None:
        mask &= wave_full <= wv_max
    wave = wave_full[mask]
    Rrs_in = np.asarray(raw.Rrs, dtype=float)[mask]
    Rrs_err = None if raw.Rrs_err is None else np.asarray(raw.Rrs_err, float)[mask]

    # Uncertainty (+ optional perturbation).
    varRrs, Rrs_out, Rrs_clean, tag, seed_used = attach_noise(
        wave, Rrs_in, model=noise, add_noise=add_noise, seed=seed,
        Rrs_err=Rrs_err)

    # Truth pre-aligned onto `wave`; init from the observed (post-noise) Rrs.
    truth, truth_interp = _build_truth(raw, wave)
    init = _init_from_rrs(wave, Rrs_out)

    return PreparedRecord(
        dataset=dataset, obs_id=obs_id, wave=wave,
        Rrs=Rrs_out, varRrs=varRrs, Rrs_clean=Rrs_clean,
        truth=truth, truth_interp=truth_interp, init=init,
        noise_model=tag, noise_seed=seed_used, meta=dict(raw.meta))


def _prep_one_star(item, dataset, noise, add_noise, wv_min, wv_max, load_opts):
    """Top-level worker for :func:`prep_dataset`'s process pool (picklable)."""
    obs_id, seed = item
    return prep_one(dataset, obs_id, noise=noise, add_noise=add_noise,
                    seed=seed, wv_min=wv_min, wv_max=wv_max, **load_opts)


def prep_dataset(dataset, *, obs_ids=None, noise=None, add_noise=None,
                 seed=None, n_cores=1, wv_min=None, wv_max=None, **load_opts):
    """Prepare many observations into a list of ``PreparedRecord``.

    Maps :func:`prep_one` over ``obs_ids`` (default: every observation the
    adapter enumerates). Per-record seeds derive from ``seed + index`` so each
    realization is independent yet reproducible. Runs in a
    ``ProcessPoolExecutor`` when ``n_cores > 1``.

    Parameters
    ----------
    dataset : str
        Registered dataset name.
    obs_ids : iterable or None, optional
        Observation ids to prepare; ``None`` → all (``adapter.obs_ids``).
    noise, add_noise, wv_min, wv_max, **load_opts
        Forwarded to :func:`prep_one`.
    seed : int or None, optional
        Master seed; record ``i`` uses ``seed + i`` (``None`` → unseeded).
    n_cores : int, optional
        Parallel workers (default 1 = serial).

    Returns
    -------
    list of PreparedRecord
    """
    adapter = get_adapter(dataset)
    if obs_ids is None:
        obs_ids = adapter.obs_ids(**load_opts)
    obs_ids = list(obs_ids)

    def _seed_for(i):
        return None if seed is None else int(seed) + i

    work = [(oid, _seed_for(i)) for i, oid in enumerate(obs_ids)]

    if n_cores and n_cores > 1:
        from concurrent.futures import ProcessPoolExecutor
        from functools import partial
        fn = partial(_prep_one_star, dataset=dataset, noise=noise,
                     add_noise=add_noise, wv_min=wv_min, wv_max=wv_max,
                     load_opts=load_opts)
        with ProcessPoolExecutor(max_workers=n_cores) as ex:
            return list(ex.map(fn, work))

    return [prep_one(dataset, oid, noise=noise, add_noise=add_noise, seed=s,
                     wv_min=wv_min, wv_max=wv_max, **load_opts)
            for oid, s in work]

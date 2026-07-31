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

**In-situ noise fallback.** In-situ datasets use ``noise='insitu'`` (weight the
fit by the dataset's own measured ``Rrs`` error). PANGAEA V3 ships **no**
per-band ``Rrs`` uncertainty, so such a record has no ``Rrs_err`` and prep
falls back to a **flat 5% fractional** model (``varRrs = (0.05 * Rrs)**2``; the
fraction is the module constant ``_INSITU_PCT_FALLBACK``). The record's
``noise_model`` is then
set to the honest tag ``'pct:0.05'`` — **not** ``'insitu'`` — so downstream
provenance and reports show the model that was actually applied.
"""

from __future__ import annotations

import warnings

import numpy as np

from ioptics import noise
from ioptics.datasets import get_adapter
from ioptics.noise import attach_noise
from ioptics.records import PreparedRecord

# In-situ datasets are meant to weight the fit by their own measured Rrs error
# (``noise='insitu'``). PANGAEA V3 ships no per-band Rrs uncertainty, so when an
# ``'insitu'`` record carries no ``Rrs_err`` prep falls back to a flat
# fractional model (design §Noise: "pct fallback otherwise"). The provenance
# tag then honestly records the model actually used (``'pct:0.05'``).
_INSITU_PCT_FALLBACK = 0.05

# GLORIA quotes a per-band Rrs standard deviation so tight (~1.5e-4 sr^-1,
# well under 1% of a turbid Rrs) that it dominates chi-squared: even fits that
# track the spectrum well land many sigma per band away, and the turbid ones
# reach chi2_nu ~ 250. An error floor makes the statistic interpretable
# (median chi2_nu 247 -> 72 at 5%) without pretending the fit improved -- the
# true relative misfit is unchanged at ~48% (reports/gloria_fits_report.md).
# It is applied as a **per-dataset default for GLORIA only**; the resulting
# noise_model tag says so ('insitu+floor:0.05').
_GLORIA_NOISE_FLOOR = 0.05

# ... but only 29% of GLORIA spectra quote an uncertainty at all: 70% quote
# none at any band, and those weights have to be invented outright. An invented
# error deserves less confidence than a measured one that was merely floored,
# so imputation uses a **wider** fraction, and the tag records which happened
# ('insitu+imputed:0.1' vs 'insitu+floor:0.05'). Every such record also raises
# ``noise.ImputedUncertaintyWarning``: results from those fits may not be valid.
_GLORIA_IMPUTED_ERROR = 0.10


def _is_gloria(dataset):
    """Whether ``dataset`` is GLORIA (prefix-tolerant).

    Matches on the prefix, like :func:`ioptics.metrics._caveat`, so a
    ``'GLORIA_FAKE'`` test fixture behaves like the real dataset.
    """
    return str(dataset).upper().startswith('GLORIA')


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
    components become plain floats. A spectral truth value may arrive either as
    a plain array on ``raw.wave`` (L23) or as a ``(src_wave, values)`` pair on
    its own per-family grid (PANGAEA's ``a_ph``/``a_dg``/``bb_p``); both are
    aligned onto ``wave`` (out-of-range points left ``NaN``, regrid flagged).
    """
    from ocpy.spectra import Spectrum

    default_wave = np.asarray(raw.wave, dtype=float)
    truth, truth_interp = {}, {}
    for key, val in raw.truth.items():
        if isinstance(val, tuple):                         # per-family spectrum
            comp_wave, comp_vals = val
            comp_wave = np.asarray(comp_wave, dtype=float)
            aligned, interpolated = _align_truth(comp_wave, comp_vals, wave)
            truth[key] = Spectrum(wave, aligned, units='1/m',
                                  metadata={'orig_wave': comp_wave})
            truth_interp[key] = interpolated
            continue
        arr = np.asarray(val)
        if arr.ndim == 0:                                  # scalar component
            truth[key] = float(val)
            truth_interp[key] = False
        else:                                              # spectral on raw.wave
            aligned, interpolated = _align_truth(default_wave, arr, wave)
            truth[key] = Spectrum(wave, aligned, units='1/m',
                                  metadata={'orig_wave': default_wave})
            truth_interp[key] = interpolated
    return truth, truth_interp


# Gordon Rrs <-> subsurface rrs relation (mirrors bing.rt.rrs A_Rrs / B_Rrs).
_A_RRS, _B_RRS = 0.52, 1.7


def _init_from_rrs(wave, Rrs):
    """Truth-free model-init values from the *observed* ``Rrs``.

    ``Chl`` via the OC4 band ratio (``ocpy.chl.band_ratios.oc4``) and ``Y`` via
    the Lee (2002) backscatter-slope prescription: convert ``Rrs`` to subsurface
    ``rrs`` (Gordon) and apply the 440/555 ratio. These seed the least-squares
    starting guess at run time without peeking at truth.

    The Lee formula matches bing's ``bbNWLee.compute_Y`` exactly, but we apply it
    directly rather than constructing the model: building any ``bbnw`` model runs
    ``bbNWModel.init_bbw``, which loads the L23 ``Hydrolight400.nc`` dataset for
    pure-water backscattering — that would make prep of *any* dataset require the
    L23 tree (and break CI, which has none). The Gordon ``Rrs->rrs`` conversion
    is inlined for the same reason (``bing.rt.rrs.Rrs_to_rrs`` is not in every
    released bing), so prep stays data-free and version-robust.
    """
    from ocpy.chl import band_ratios

    Rrs = np.asarray(Rrs, dtype=float)
    Chl = float(band_ratios.oc4(wave, Rrs))

    rrs = Rrs / (_A_RRS + _B_RRS * Rrs)
    i440 = int(np.argmin(np.abs(wave - 440.)))
    i555 = int(np.argmin(np.abs(wave - 555.)))
    Y = float(2.2 * (1.0 - 1.2 * np.exp(-0.9 * rrs[i440] / rrs[i555])))

    return {'Chl': Chl, 'Y': Y}


def prep_one(dataset, obs_id, *, noise=None, add_noise=None, seed=None,
             wv_min=None, wv_max=None, noise_floor=None, noise_imputed=None,
             **load_opts):
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
        ``'pace'`` for L23 (synthetic) and ``'insitu'`` otherwise; an
        ``'insitu'`` record with no measured ``Rrs_err`` falls back to a flat
        fractional model (``_INSITU_PCT_FALLBACK``).
    add_noise : bool or None, optional
        Whether to perturb ``Rrs``. Defaults to ``True`` for L23 and ``False``
        for in-situ datasets (their ``Rrs`` is already a real observation).
    seed : int or None, optional
        RNG seed for the perturbation (recorded in ``noise_seed``).
    wv_min, wv_max : float or None, optional
        Optional native-grid wavelength trim.
    noise_floor : float, False or None, optional
        Fractional error floor (:func:`ioptics.noise.attach_noise`
        ``floor_frac``). ``None`` applies the dataset's default — GLORIA's
        ``_GLORIA_NOISE_FLOOR``, nothing elsewhere; ``False`` applies **no**
        floor even where a default exists.
    noise_imputed : float, False or None, optional
        Fraction used where the dataset measured no uncertainty at all
        (``impute_frac``). ``None`` applies GLORIA's ``_GLORIA_IMPUTED_ERROR``,
        else falls back to ``noise_floor``; ``False`` leaves missing errors
        missing (the record's ``varRrs`` then carries NaN and cannot be fit).
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
    if _is_gloria(dataset):
        # Per-dataset defaults: GLORIA's quoted errors are too tight for
        # chi-squared to mean anything, and most spectra quote none at all
        # (see _GLORIA_NOISE_FLOOR / _GLORIA_IMPUTED_ERROR).
        if noise_floor is None:
            noise_floor = _GLORIA_NOISE_FLOOR
        if noise_imputed is None:
            noise_imputed = _GLORIA_IMPUTED_ERROR
    # ``False`` (or 0) means *explicitly no floor*, overriding the per-dataset
    # default -- what the analysis scripts need to study the un-floored case.
    # ``None`` is "use the default", which is not the same request.
    noise_floor = noise_floor or None
    noise_imputed = noise_imputed or None

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

    # In-situ weighting needs measured errors; fall back to a fractional model
    # when the dataset carries none (e.g. PANGAEA V3).
    if noise == 'insitu' and Rrs_err is None:
        noise = f'pct:{_INSITU_PCT_FALLBACK}'

    # Uncertainty (+ optional perturbation).
    varRrs, Rrs_out, Rrs_clean, tag, seed_used = attach_noise(
        wave, Rrs_in, model=noise, add_noise=add_noise, seed=seed,
        Rrs_err=Rrs_err, floor_frac=noise_floor,
        impute_frac=noise_imputed)

    # Truth pre-aligned onto `wave`; init from the observed (post-noise) Rrs.
    truth, truth_interp = _build_truth(raw, wave)
    init = _init_from_rrs(wave, Rrs_out)

    return PreparedRecord(
        dataset=dataset, obs_id=obs_id, wave=wave,
        Rrs=Rrs_out, varRrs=varRrs, Rrs_clean=Rrs_clean,
        truth=truth, truth_interp=truth_interp, init=init,
        noise_model=tag, noise_seed=seed_used, meta=dict(raw.meta))


def _prep_one_star(item, dataset, noise, add_noise, wv_min, wv_max, load_opts,
                   noise_floor=None, noise_imputed=None):
    """Top-level worker for :func:`prep_dataset`'s process pool (picklable)."""
    obs_id, seed = item
    return prep_one(dataset, obs_id, noise=noise, add_noise=add_noise,
                    seed=seed, wv_min=wv_min, wv_max=wv_max,
                    noise_floor=noise_floor, noise_imputed=noise_imputed,
                    **load_opts)


def prep_dataset(dataset, *, obs_ids=None, noise=None, add_noise=None,
                 seed=None, n_cores=1, wv_min=None, wv_max=None,
                 noise_floor=None, noise_imputed=None, **load_opts):
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
    noise, add_noise, wv_min, wv_max, noise_floor, noise_imputed, **load_opts
        Forwarded to :func:`prep_one`. ``noise_floor`` / ``noise_imputed`` are
        normally left ``None``, which lets each dataset's default apply (an
        error floor and an imputation fraction for GLORIA, none elsewhere).
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
                     noise_floor=noise_floor, noise_imputed=noise_imputed,
                     load_opts=load_opts)
        with ProcessPoolExecutor(max_workers=n_cores) as ex:
            records = list(ex.map(fn, work))
    else:
        records = [prep_one(dataset, oid, noise=noise, add_noise=add_noise,
                            seed=s, wv_min=wv_min, wv_max=wv_max,
                            noise_floor=noise_floor,
                            noise_imputed=noise_imputed, **load_opts)
                   for oid, s in work]

    _warn_if_imputed(records, dataset)
    return records


def _warn_if_imputed(records, dataset):
    """Raise one :class:`~ioptics.noise.ImputedUncertaintyWarning` per batch.

    Reads the records' own ``noise_model`` tags rather than warning inside
    :func:`ioptics.noise.attach_noise`, which is what makes a single warning
    possible: the per-record site fires ~70 times on a 100-spectrum GLORIA
    batch, and under a process pool those warnings are raised in the workers
    and lost. The count is the actionable part anyway.
    """
    n_imputed = sum(1 for r in records if noise.is_imputed(r.noise_model))
    if n_imputed:
        warnings.warn(
            f'{dataset}: {n_imputed} of {len(records)} records have no '
            f'measured Rrs uncertainty at any band, so their fit weights are '
            f'imputed (noise_model {noise.IMPUTED_TAG!r}). Chi-squared and '
            f'anything derived from it may not be valid for those records.',
            noise.ImputedUncertaintyWarning, stacklevel=3)

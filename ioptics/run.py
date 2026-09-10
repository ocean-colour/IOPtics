"""The run driver — wire BING and fit one record on its native grid.

``run_algorithm(spec, record)`` is where the model/prior/RT configuration that
:mod:`ioptics.prep` deferred actually happens. Given an
:class:`~ioptics.algorithms.spec.AlgorithmSpec` and a
:class:`~ioptics.records.PreparedRecord` it builds the BING models on the
record's native grid, seeds them truth-free, runs the fit, and hands the result
to :mod:`ioptics.evaluate`.

Stage 2 implements the **least-squares (chisq)** path; the MCMC path lands in
Stage 3. Two invariants:

- **Native grid** — models are built on ``record.wave`` (no resampling).
- **Truth-free** — the initial guess and the model internals are seeded from the
  *observed* ``Rrs`` and ``record.init`` (Chl/Y), **never** from ``record.truth``
  (else the benchmark would be circular).

The RT backend (``spec.rt.rt_backend``) decides which forward model runs. The
default ``'gordon'`` path is exactly what it always was — a 4-tuple of items to
BING, no geometry, no extra parameter. A ``robust_*`` backend additionally
needs an observation geometry, resolved per record by :func:`resolve_geometry`
and threaded as the items tuple's optional 5th element, and may fit ``B_p``
(``spec.rt.fit_Bp``), which appends one trailing element to the fitted vector,
the bounds, the seed, and every saved chain.

.. note::

   Building BING models loads the L23 pure-water backscattering data, so the
   functions here require the L23 tree present (they are exercised under Tier-2
   ``@needs_l23`` tests).
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping

import numpy as np

from ioptics.records import RED_PEAK_NM, RetrievalResult

#: Anchor wavelength (nm) for the QAA-style band inversion in
#: :func:`initial_guess` — the red band where the water's own absorption
#: dominates, so ``u`` can be turned into an absolute ``bb``.
ANCHOR_NM = 670.0

#: Observed ``Rrs`` at :data:`ANCHOR_NM` (sr^-1) at or above which a spectrum
#: is treated as **turbid** by :func:`is_turbid`. This is QAA_v6's own
#: reference-wavelength switch (Lee et al. 2002, doi:10.1364/AO.41.005755;
#: QAA_v6 update, ioccg.org/groups/software.html): below it the red band
#: carries too little signal for the turbid branch, above it the red anchor's
#: *non-water* absorption can no longer be neglected.
TURBID_RRS_ANCHOR = 0.0015

#: QAA_v6 Step 2 (turbid branch) coefficients for the non-water absorption at
#: the red anchor, ``a_nw(670) = C * [Rrs(670) / (Rrs(443) + Rrs(490))] ** E``.
#: Note SeaDAS ships different values for this step (0.07 with a
#: ``Rrs(670)/Rrs(440)`` ratio); these are the coefficients in the IOCCG
#: QAA_v6 document.
QAA_ANW_ANCHOR = (0.39, 1.14)

#: Bands (nm) forming the blue-green denominator of that ratio.
QAA_BLUE_NM = (443.0, 490.0)

#: Fraction of each prior's range by which the seed is held **off** its
#: bounds. A parameter seeded exactly on a bound gives the bounded
#: least-squares solver a zero-width search direction, which is a real
#: failure mode for turbid fits (the amplitudes and the backscattering
#: exponent are the ones that clip).
BOUND_INSET = 1e-3


def _prior_bounds(models, rt_dict=None):
    """Lower/upper parameter bounds from the models' priors (a then bb).

    ``rt_dict`` is consulted for one thing only: under ``fit_Bp`` the fitted
    vector carries a trailing ``B_p`` element, so the bounds gain a matching
    trailing slot taken from BING's own ``[BP_PRIOR_PMIN, BP_PRIOR_PMAX]`` —
    the same numbers the MCMC prior uses, so the two fitters cannot disagree
    about the range. ``None`` (the default) is the fixed-``B_p`` case and
    returns exactly the model bounds, as before.
    """
    lows, highs = [], []
    for model in models:
        for prior in model.priors.priors:
            lows.append(prior.pmin)
            highs.append(prior.pmax)
    if rt_dict is not None and rt_dict.get('fit_Bp', False):
        from bing.rt import defs as rt_defs
        lows.append(rt_defs.BP_PRIOR_PMIN)
        highs.append(rt_defs.BP_PRIOR_PMAX)
    return np.array(lows, dtype=float), np.array(highs, dtype=float)


def _log_mask(models):
    """Boolean mask (per concatenated param) of log-flavored priors."""
    mask = []
    for model in models:
        for prior in model.priors.priors:
            mask.append(str(prior.flavor)[:3] == 'log')
    return np.array(mask, dtype=bool)


def is_turbid(record, *, threshold=TURBID_RRS_ANCHOR):
    """Whether the *observed* spectrum is turbid, by QAA_v6's own test.

    ``Rrs`` at the nearest band to :data:`ANCHOR_NM` at or above ``threshold``
    (:data:`TURBID_RRS_ANCHOR`). This is the switch QAA_v6 uses to move its
    reference wavelength into the red, and it is what :func:`initial_guess`
    keys its turbid branch on. Truth-free: it reads ``record.Rrs`` only.

    Parameters
    ----------
    record : PreparedRecord
        The record whose observed ``Rrs`` is tested.
    threshold : float, optional
        Rrs threshold (sr^-1) at the anchor band.

    Returns
    -------
    bool
        ``True`` for a turbid spectrum. A non-finite anchor ``Rrs`` gives
        ``False`` (the conservative, open-ocean branch).
    """
    wave = np.asarray(record.wave, dtype=float)
    Rrs = np.asarray(record.Rrs, dtype=float)
    iref = int(np.argmin(np.abs(wave - ANCHOR_NM)))
    return bool(np.isfinite(Rrs[iref]) and Rrs[iref] >= threshold)


def _anw_anchor(wave, Rrs, turbid):
    """Non-water absorption (m^-1) at the red anchor, QAA_v6 Step 2.

    Zero on the open-ocean branch — that is the ``a(670) ~ a_w(670)``
    approximation, valid where the red band is absorption-dominated by water
    itself. On the turbid branch it is QAA_v6's empirical term,
    ``C * [Rrs(670) / (Rrs(443) + Rrs(490))] ** E``
    (:data:`QAA_ANW_ANCHOR`), which is exactly the quantity that
    approximation throws away: in mineral-rich water ``a_nw(670)`` is
    comparable to (or larger than) ``a_w(670)``, so neglecting it
    under-estimates the anchor ``bb`` — and with it every amplitude seeded
    from it — by that same factor.

    Returns ``0.0`` if the blue bands are unusable (non-finite or a
    non-positive sum), so a bad spectrum degrades to the open-ocean branch
    rather than producing a garbage anchor.
    """
    if not turbid:
        return 0.0
    iref = int(np.argmin(np.abs(wave - ANCHOR_NM)))
    blue = sum(float(Rrs[int(np.argmin(np.abs(wave - nm)))])
               for nm in QAA_BLUE_NM)
    if not np.isfinite(blue) or blue <= 0.0:
        return 0.0
    coeff, expo = QAA_ANW_ANCHOR
    return float(coeff * (Rrs[iref] / blue) ** expo)


def _seed_bb_exponent(model, p0_b, Y, log_mask_b):
    """Seed a *single*-power-law backscattering exponent from the QAA ``Y``.

    ``bbNWPow.init_guess`` returns a fixed ``beta = 1`` — an open-ocean
    particle slope — no matter what the spectrum looks like. For turbid water
    the shape wanted is flat or rising (``beta <= 0``), so the fixed seed
    starts the optimizer on the wrong side of the answer, and for
    ``expb_pow`` (whose ``beta`` prior floors at 0) it starts it hard against
    a bound. ``record.init['Y']`` already holds the Lee/QAA estimate of that
    exponent from the observed blue-to-green ratio, so use it.

    Applied **only** to the one-component power law (``Pow``, i.e.
    ``expb_pow`` / ``expb_powflex``), where the exponent *is* the whole
    spectral shape and ``Y`` estimates precisely that. ``Pow2`` / ``Pow2Flat``
    are left alone: their exponents are per-component (a bulk slope is not an
    estimate of either), and bing seeds them deliberately — the mineral one
    just off zero so MCMC's multiplicative walker spread can move it.

    Returns a copy of ``p0_b``; ``log_mask_b`` marks the log-flavored
    (amplitude) slots, so the exponent is the remaining one.
    """
    if getattr(model, 'name', '') != 'Pow' or not np.isfinite(Y):
        return p0_b
    slots = np.flatnonzero(~np.asarray(log_mask_b, dtype=bool))
    if slots.size != 1:
        return p0_b
    out = np.array(p0_b, dtype=float)
    out[slots[0]] = float(Y)
    return out


def initial_guess(models, record, *, turbid=None):
    """A **truth-free** least-squares starting point from the observed ``Rrs``.

    Performs a QAA-style band inversion of ``record.Rrs`` using BING's Gordon
    coefficients and the models' own pure-water terms (``a_w`` on the a-model,
    ``bb_w`` on the bb-model) to estimate ``a_nw``/``bb_nw``, then seeds each
    model's parameters via its ``init_guess`` (amplitudes log10'd to match the
    log-uniform priors). Never touches ``record.truth``.

    The inversion is anchored at :data:`ANCHOR_NM`, and how that anchor is
    read depends on the water:

    - **open ocean** — ``a(670) ~ a_w(670)``; non-water absorption in the red
      is neglected.
    - **turbid** — ``a(670) = a_w(670) + a_nw(670)`` with QAA_v6's empirical
      red-band term (:func:`_anw_anchor`), and the backscattering exponent of
      a one-component power law seeded from the QAA ``Y`` rather than from
      bing's fixed ``beta = 1`` (:func:`_seed_bb_exponent`).

    Which branch is taken is decided per spectrum by :func:`is_turbid`. On the
    open-ocean branch the returned seed is **identical** to the pre-turbid
    one, save for being held :data:`BOUND_INSET` off the prior bounds instead
    of clipped onto them.

    Parameters
    ----------
    models : list
        ``[a_model, bb_model]`` as built by ``AlgorithmSpec.build_models``.
    record : PreparedRecord
        Supplies ``wave``, the observed ``Rrs``, and ``init`` (``Chl``/``Y``).
    turbid : bool or None, optional
        Force the branch. ``None`` (default) auto-detects with
        :func:`is_turbid`; pass ``False`` to reproduce the open-ocean seed on
        any spectrum (which is how the two are compared).

    Returns
    -------
    numpy.ndarray
        The concatenated ``[a-params, bb-params]`` seed, strictly inside the
        prior bounds.
    """
    from bing.rt import rrs as bing_rrs

    wave = np.asarray(record.wave, dtype=float)
    Rrs = np.asarray(record.Rrs, dtype=float)
    a_w = np.asarray(models[0].a_w, dtype=float)
    bb_w = np.asarray(models[1].bb_w, dtype=float)
    if turbid is None:
        turbid = is_turbid(record)

    # Gordon: rrs = G1 u + G2 u^2, u = bb / (a + bb)  ->  solve for u.
    rrs = Rrs / (bing_rrs.A_Rrs + bing_rrs.B_Rrs * Rrs)
    G1, G2 = bing_rrs.G1_STANDARD, bing_rrs.G2_STANDARD
    disc = np.clip(G1 * G1 + 4.0 * G2 * rrs, 0.0, None)
    u = np.clip((-G1 + np.sqrt(disc)) / (2.0 * G2), 1e-3, 1.0 - 1e-3)

    # Red anchor (~670 nm): total a there is a_w plus, in turbid water, a
    # non-negligible non-water part.
    iref = int(np.argmin(np.abs(wave - ANCHOR_NM)))
    a_ref = a_w[iref] + _anw_anchor(wave, Rrs, turbid)
    bb_ref = u[iref] * a_ref / (1.0 - u[iref])
    bbnw_ref = max(bb_ref - bb_w[iref], 1e-4)

    Y = float(record.init.get('Y', 1.0))
    bb_nw = bbnw_ref * (wave[iref] / wave) ** Y
    bb = bb_w + bb_nw
    a_tot = bb * (1.0 - u) / u
    a_nw = np.clip(a_tot - a_w, 1e-4, None)
    bb_nw = np.clip(bb_nw, 1e-5, None)

    log_mask = _log_mask(models)
    p0_a = np.atleast_1d(models[0].init_guess(a_nw)).astype(float)
    p0_b = np.atleast_1d(models[1].init_guess(bb_nw)).astype(float)
    if turbid:
        p0_b = _seed_bb_exponent(models[1], p0_b, Y, log_mask[p0_a.size:])
    p0 = np.concatenate([p0_a, p0_b])

    # log10 the log-flavored amplitudes (mirrors bing.fitting.l23.prep_one_l23).
    p0[log_mask] = np.log10(np.clip(p0[log_mask], 1e-10, None))

    # Keep the guess feasible w.r.t. the prior bounds — and strictly *inside*
    # them, since a bounded least-squares solver cannot search outward from a
    # parameter pinned to its bound.
    lo, hi = _prior_bounds(models)
    inset = BOUND_INSET * (hi - lo)
    return np.clip(p0, lo + inset, hi - inset)


class MissingGeometryError(ValueError):
    """A robust RT backend was configured for a record with no place or time.

    Raised by :func:`resolve_theta_s`. The robust forward models take a solar
    zenith angle, and BING refuses to invent one
    (``bing.rt.defs.validate_rt_dict``: "theta_s is never silently
    defaulted"). IOPtics refuses one step earlier, naming the record and the
    metadata keys it would have needed — the alternative is a sweep that
    completes and publishes numbers computed at an angle nobody chose.
    """


#: Solar zenith angle (degrees) for an L23 record whose ``meta`` carries no
#: ``Y`` load option. L23 is synthetic: it has no place and no time, but its
#: ``Y`` *is* the Hydrolight solar-zenith index in degrees (00 / 30 / 60), so
#: :func:`resolve_theta_s` reads that when present and falls back here
#: otherwise. The fallback equals the ``Y=0`` default, so an ordinary L23
#: sweep sees ``theta_s = 0``.
L23_DEFAULT_THETA_S = 0.0

#: Sensor zenith / relative azimuth (degrees) assumed for every record.
#: Nadir viewing: none of the datasets IOPtics reads records a sensor
#: geometry, and ``ObsGeometry``'s own defaults are the same pair.
DEFAULT_THETA_V = 0.0
DEFAULT_DPHI = 0.0


def _usable(value):
    """Whether a metadata cell is a real value (not ``None``/NaN/NaT/``''``).

    A missing position is far more often a *present but empty* cell than an
    absent key — a PANGAEA row with no coordinates arrives from pandas as
    ``NaN``, and one with no timestamp as ``NaT`` — so absence has to be tested
    on the value, not on the key. ``pandas.NaT`` needs its own branch because
    it is an instance of :class:`datetime.datetime` that is not a time; the
    ``value == value`` test is what separates it from a real one.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (datetime.datetime, datetime.date)):
        return bool(value == value)
    arr = np.asarray(value)
    if arr.dtype.kind == 'M':                       # datetime64, possibly NaT
        return not bool(np.isnat(arr))
    if arr.dtype.kind in 'fc':
        return bool(np.isfinite(arr))
    if arr.dtype.kind in 'iub':
        return True
    return bool(arr.size)     # a non-numeric, non-empty object: take it as real


def resolve_theta_s(record):
    """Solar zenith angle (degrees) for ``record``, or raise.

    - **L23** (synthetic) — the Hydrolight solar-zenith load option
      ``meta['Y']`` in degrees, defaulting to :data:`L23_DEFAULT_THETA_S`.
      There is no place or time to compute anything from, and none is needed:
      the realization *was* generated at that zenith.
    - **everything else** — computed from the observation's UTC time and
      position with ``robust.solar.solar_zenith`` (the NOAA/Meeus geometric
      zenith, ~0.01° over 1900–2100; no refraction, never clamped at the
      horizon). The three metadata keys are
      :data:`~ioptics.datasets.TIME_META_KEY` /
      :data:`~ioptics.datasets.LAT_META_KEY` /
      :data:`~ioptics.datasets.LON_META_KEY`.

    Raises :class:`MissingGeometryError` when a non-L23 record is missing any
    of the three. That is deliberate and load-bearing: the only alternatives
    are to guess an angle or to drop the record, and a guessed ``theta_s``
    would propagate silently into every retrieved IOP.

    Parameters
    ----------
    record : PreparedRecord
        The observation; ``dataset`` and ``meta`` are read.

    Returns
    -------
    float
        Solar zenith angle in degrees.
    """
    from ioptics import datasets as ipt_datasets

    meta = getattr(record, 'meta', None) or {}
    if str(record.dataset).upper().startswith('L23'):
        y = meta.get('Y')
        return float(y) if _usable(y) else float(L23_DEFAULT_THETA_S)

    keys = (ipt_datasets.TIME_META_KEY, ipt_datasets.LAT_META_KEY,
            ipt_datasets.LON_META_KEY)
    values = [meta.get(k) for k in keys]
    missing = [k for k, v in zip(keys, values) if not _usable(v)]
    if missing:
        raise MissingGeometryError(
            f'{record.dataset}/{record.obs_id}: cannot resolve the solar '
            f'zenith angle — record.meta is missing {missing} (needs '
            f'{list(keys)}). A robust rt_backend requires an observation '
            'geometry and theta_s is never silently defaulted; either use '
            "rt_backend='gordon' or fit a dataset that records when and "
            'where each spectrum was measured')
    from robust import solar

    time, lat, lon = values
    return float(solar.solar_zenith(time, float(lat), float(lon)))


def resolve_geometry(spec, record):
    """Observation geometry for ``(spec, record)``, or ``None`` for Gordon.

    A pure function, so every consumer — the fitters and the reconstruction in
    :mod:`ioptics.evaluate` — derives the *same* geometry from the same record
    without it having to be threaded through every return value.

    Returns ``None`` when ``spec.rt.rt_backend`` is ``'gordon'``: the Gordon
    forward model has no geometry input, so the fit items stay the legacy
    4-tuple and nothing about the legacy path changes (not even an import of
    ``robust``). Otherwise builds a ``bing.rt.geometry.ObsGeometry`` at
    :func:`resolve_theta_s` with nadir viewing
    (:data:`DEFAULT_THETA_V` / :data:`DEFAULT_DPHI`).

    Parameters
    ----------
    spec : AlgorithmSpec
        Supplies ``rt.rt_backend``.
    record : PreparedRecord
        Supplies the dataset and the time/lat/lon metadata.

    Returns
    -------
    bing.rt.geometry.ObsGeometry or None
    """
    if getattr(spec.rt, 'rt_backend', 'gordon') == 'gordon':
        return None
    from bing.rt.geometry import ObsGeometry

    return ObsGeometry(theta_s=resolve_theta_s(record),
                       theta_v=DEFAULT_THETA_V, dphi=DEFAULT_DPHI)


def _prepare(spec, record, *, geom=None):
    """Build ``(p, models, rt_dict)`` for ``record``, models seeded truth-free.

    ``geom`` is the record's :func:`resolve_geometry` result; when omitted it
    is resolved here. It is not returned — it is a pure function of
    ``(spec, record)`` — but it *is* handed to ``validate_rt_dict`` below, so a
    misconfigured RT setup (an unknown backend, ``fit_Bp`` on Gordon, a robust
    backend with no geometry, ``robust_hybrid`` outside 350–750 nm,
    ``include_CDOM_fl`` without a separable ``a_dg``) fails once at setup with
    BING's own message rather than deep inside the optimizer.
    """
    from bing.rt import defs as rt_defs
    from bing.models import utils as model_utils

    if geom is None:
        geom = resolve_geometry(spec, record)
    p = spec.to_bing_p(wv_min=float(np.min(record.wave)),
                       wv_max=float(np.max(record.wave)))
    models = spec.build_models(record.wave)
    # Wavelength-dependent Gordon coefficients live on the a-model (the forward
    # model reads models[0].G1/G2); set them when variable_Gordon is on.
    if spec.rt.variable_Gordon:
        models[0].init_var_gordon(
            include_G0=spec.rt.variable_Gordon_G0,
            include_Gb=spec.rt.variable_Gordon_bbp)
    # Inelastic RT setup (L23 X=4). Raman needs no extra wiring here: both
    # models call ``init_raman()`` in their constructors, so ``wave_ex``/``bb_R``
    # are always set and the forward model's ``eval_a_ex``/``eval_bb_ex`` work.
    # (Raman is numerically unstable blueward of ~400 nm, where the excitation
    # wavelengths fall off the water/Gordon tables — trim the record to
    # ``[400, 700]`` for inelastic fits, as bing's own X=4 path does.)
    # Chl fluorescence, however, needs the downwelling irradiance ``Ed`` seeded
    # on the a-model — mirror ``bing.fitting.l23``. **Gordon backend only**: the
    # robust backends compute their fluorescence from robust's own packaged Ed
    # table (rt_tests Q36), so a robust Chl-fl fit must not import
    # ``correct_atmosphere`` at all — it is a bing-side dependency that is not
    # on PyPI, and requiring it would make the robust path unrunnable wherever
    # the ``needs_inelastic`` guard skips.
    if spec.rt.include_Chl_fl and spec.rt.rt_backend == 'gordon':
        from correct_atmosphere import downwelling
        from bing.rt import chl_fl
        Ed = downwelling.downwelling_irradiance(models[0].wave, 0.)
        Ed_em = downwelling.downwelling_irradiance(chl_fl.LAMBDA_FL_PRIMARY, 0.)
        models[0].init_Chl_fluorescence(Ed=Ed, Ed_em=Ed_em)
    rt_dict = rt_defs.rt_dict_from_p(p)
    # Truth-free model internals (Bricaud a_ph from Chl, Lee bb_p slope from Y),
    # from record.init (derived from the observed Rrs), never from truth.
    # Pass Chl as a numpy scalar: bing's set_aph does `len(Chla.shape)`, which a
    # plain Python float lacks (bing's own L23 path happens to pass np.float64).
    Chl = record.init.get('Chl')
    Chl = None if Chl is None else np.asarray(Chl, dtype=float)
    model_utils.init_other_bits(models, Chl=Chl, Y=record.init.get('Y'),
                                Rrs=record.Rrs)
    # Fail fast, once, with bing's own errors (see the docstring).
    rt_defs.validate_rt_dict(rt_dict, models=models, geom=geom)
    return p, models, rt_dict


def is_red_peaked(record):
    """True when the observed Rrs peaks redward of :data:`RED_PEAK_NM`.

    The spectrum-only predicate behind the **pre-fit** ``out_of_scope``
    assignment: turbid, red-peaked water is outside what the open-ocean
    model family is built for, and as of 2026-08-10 (JXP's Task-1 answers,
    ``claude_prompts/pangaea_fits.md``) the pipeline *declines* such a record
    up front — separating "we declined to fit this" from "we fitted it and it
    failed" — unless the algorithm claims turbid water in scope
    (``AlgorithmSpec.fits_turbid``). The same predicate previously ran only
    post-hoc, inside :func:`ioptics.evaluate._fit_status`, on fits that had
    already gone poorly.
    """
    Rrs = np.asarray(record.Rrs, dtype=float)
    if not np.any(np.isfinite(Rrs)):
        return False
    peak = float(np.asarray(record.wave, dtype=float)[int(np.nanargmax(Rrs))])
    return peak > RED_PEAK_NM


class UnderdeterminedFitError(ValueError):
    """A spectrum with ``n_bands <= k`` cannot constrain the model.

    Raised by :func:`fit_chisq` / :func:`fit_mcmc` **before** any optimizer
    runs, and converted by :func:`run_algorithm` into a ``fit_failed``
    :class:`~ioptics.records.RetrievalResult` whose stats carry the true
    ``n_bands`` and ``k`` — so the refusal is a status we chose, identifiable
    downstream as ``status == 'fit_failed' and n_bands <= k``, rather than a
    ``LinAlgError: SVD did not converge`` surfacing from deep inside scipy
    (which is how all 315 five-band PANGAEA spectra died under ``expb_pow``,
    k = 5; see ``claude_prompts/pangaea_fits.md``).
    """


def n_free_params(models, rt_dict=None):
    """Number of fitted parameters: the models', plus ``B_p`` under ``fit_Bp``.

    The one definition of ``k``, shared by the underdetermined refusal
    (:func:`_refuse_underdetermined`), the ``fit_failed`` / ``out_of_scope``
    stats, and the AIC/BIC/dof in :mod:`ioptics.evaluate` — a free ``B_p`` is a
    parameter the data has to pay for like any other.
    """
    k = int(models[0].nparam + models[1].nparam)
    if rt_dict is not None and rt_dict.get('fit_Bp', False):
        k += 1
    return k


def _refuse_underdetermined(models, record, rt_dict=None):
    """Raise :class:`UnderdeterminedFitError` when ``n_bands <= k``."""
    k = n_free_params(models, rt_dict)
    n_bands = int(np.asarray(record.wave).size)
    if n_bands <= k:
        raise UnderdeterminedFitError(
            f'{record.dataset}/{record.obs_id}: n_bands={n_bands} <= k={k} '
            '-- the fit is underdetermined by construction')


def _seed(models, record, rt_dict):
    """The truth-free initial guess, with the ``B_p`` tail when it is free.

    ``bing.fitting.inference.append_Bp_seed`` is the canonical place that tail
    is defined (a *linear-space* ``Bp_value``, never log10'd); it is imported
    only when ``fit_Bp`` is on, so the Gordon path keeps its import set — and
    its behaviour — exactly as before.
    """
    p0 = initial_guess(models, record)
    if rt_dict.get('fit_Bp', False):
        from bing.fitting import inference as bing_inf
        p0 = bing_inf.append_Bp_seed(p0, rt_dict)
    return p0


def _fit_items(record, p0, idx, geom):
    """The BING items tuple: legacy 4-tuple, or 5-tuple carrying ``geom``.

    BING accepts either, reading a missing 5th element as ``geom=None``.
    Emitting the 4-tuple whenever there is no geometry (i.e. on the Gordon
    backend) keeps the legacy call byte-for-byte what it was.
    """
    base = (np.asarray(record.Rrs, dtype=float),
            np.asarray(record.varRrs, dtype=float), p0, idx)
    return base if geom is None else base + (geom,)


def fit_chisq(spec, record):
    """Least-squares fit of one record; returns ``(models, rt_dict, ans, cov)``.

    The Stage-2 fitting core (used by :func:`run_algorithm` and exercised
    directly by tests). Builds models, seeds a truth-free initial guess, and
    calls ``bing.fitting.chisq_fit.fit`` with prior-derived bounds and the
    spec's ``maxfev`` evaluation budget. Refuses an underdetermined record
    (``n_bands <= k``) up front with :class:`UnderdeterminedFitError` instead
    of letting scipy fail with a ``LinAlgError``.

    Under a robust ``rt_backend`` the record's :func:`resolve_geometry` result
    rides as the items tuple's optional 5th element; the Gordon path passes the
    legacy 4-tuple unchanged. Under ``fit_Bp`` the seed and the bounds each
    gain the trailing ``B_p`` slot.
    """
    from bing.fitting import chisq_fit

    geom = resolve_geometry(spec, record)
    _, models, rt_dict = _prepare(spec, record, geom=geom)
    _refuse_underdetermined(models, record, rt_dict)
    p0 = _seed(models, record, rt_dict)
    bounds = _prior_bounds(models, rt_dict)
    items = _fit_items(record, p0, record.obs_id, geom)
    # spec.maxfev is None for the open-ocean algorithms, which leaves
    # scipy's default budget alone; the turbid models raise it because they
    # otherwise run out of evaluations before converging.
    ans, cov, _ = chisq_fit.fit(items, models, rt_dict, bounds=bounds,
                                maxfev=getattr(spec, 'maxfev', None))
    return models, rt_dict, ans, cov


def fit_mcmc(spec, record):
    """MCMC fit of one record; returns ``(models, rt_dict, chains)``.

    Builds models truth-free (``_prepare``), seeds the walkers from the same
    truth-free :func:`initial_guess`, and runs emcee via
    ``bing.fitting.inference.{init_mcmc, fit_one}``. ``Chl``/``Y`` are passed in
    BING's idx-keyed form (an array indexed by the record's integer ``obs_id``),
    mirroring ``bing.fitting.l23.fit_one``.

    Under a robust ``rt_backend`` the record's :func:`resolve_geometry` result
    rides as the items tuple's optional 5th element. Under ``fit_Bp`` the
    sampled vector grows a trailing ``B_p`` dimension: ``init_mcmc`` sizes
    ``ndim``/``nwalkers`` for it and the seed carries the matching tail, so the
    returned ``chains`` have one extra column.
    """
    from bing.fitting import inference as bing_inf

    geom = resolve_geometry(spec, record)
    _, models, rt_dict = _prepare(spec, record, geom=geom)
    _refuse_underdetermined(models, record, rt_dict)
    p0 = _seed(models, record, rt_dict)

    pdict = bing_inf.init_mcmc(models, nsteps=spec.mcmc.nsteps,
                               nburn=spec.mcmc.nburn, rt_dict=rt_dict)
    # A single record is fit in isolation, so synthesize a positional index of 0
    # with size-1 Chl/Y arrays (BING keys Chl/Y by this idx). This replaces
    # ``int(record.obs_id)``, which fails on non-integer ids (e.g. GLORIA's
    # 'GID_1'); the real obs id still rides on the result via ``record.obs_id``.
    idx = 0
    pdict['Chl'] = np.array([float(record.init.get('Chl', 0.0))])
    pdict['Y'] = np.array([float(record.init.get('Y', 0.0))])

    items = _fit_items(record, p0, idx, geom)
    chains, _ = bing_inf.fit_one(items, models=models, pdict=pdict,
                                 chains_only=True, rt_dict=rt_dict)
    return models, rt_dict, chains


def run_algorithm(spec, record, *, fit_method=None,
                  perc=((16, 84), (2.5, 97.5))):
    """Fit one record with ``spec`` and return a ``RetrievalResult``.

    Dispatches on ``fit_method`` (or ``spec.fit_method``): ``'chisq'``
    (least-squares, default) or ``'mcmc'`` (emcee). Both paths reconstruct the
    same components with 68/95 bands via :mod:`ioptics.evaluate`.

    Two kinds of record are **declined up front**, in both strict modes,
    rather than fitted:

    - a red-peaked (turbid) record when the algorithm does not claim turbid
      water in scope (``spec.fits_turbid`` is False) — returned as
      ``out_of_scope``, per the pre-fit assignment decision
      (``claude_prompts/pangaea_fits.md`` Q&A, 2026-08-10);
    - an underdetermined record (``n_bands <= k``) — returned as
      ``fit_failed`` rather than crashing the batch (strict) or masquerading
      as an optimizer failure (robust).

    Both results carry the true ``n_bands``/``k`` in their stats.
    """
    from ioptics import evaluate

    method = fit_method or spec.fit_method
    declined = _prefit_decline(spec, record, method)
    if declined is not None:
        return declined
    try:
        geom = resolve_geometry(spec, record)
        if method == 'chisq':
            models, rt_dict, ans, cov = fit_chisq(spec, record)
            return evaluate.from_chisq(spec, record, models, rt_dict, ans, cov,
                                       perc=perc, geom=geom)
        if method == 'mcmc':
            models, rt_dict, chains = fit_mcmc(spec, record)
            return evaluate.from_chains(spec, record, models, rt_dict, chains,
                                        perc=perc, geom=geom)
    except UnderdeterminedFitError:
        return _failed_result(spec, record, method)
    raise ValueError(f"unknown fit_method {method!r} (expected 'chisq'|'mcmc')")


def _prefit_decline(spec, record, fit_method):
    """The pre-fit scope decision, shared by every fitting entry point.

    Returns an ``out_of_scope`` :class:`~ioptics.records.RetrievalResult`
    when the record is red-peaked and the spec does not claim turbid water
    in scope, else ``None`` (proceed to fit). Lives in one function so the
    χ² pass (:func:`run_algorithm`) and the MCMC subset
    (:func:`_mcmc_subset`) cannot drift apart — they must agree on which
    records a sweep declines (PR #11 review: the subset originally bypassed
    the guard and could MCMC-fit spectra its own χ² pass had declined).
    """
    if not getattr(spec, 'fits_turbid', False) and is_red_peaked(record):
        return _unfit_result(spec, record, fit_method, 'out_of_scope')
    return None


def _unfit_result(spec, record, fit_method, status):
    """A minimal result for a record that was never fitted.

    Shared by the failure path (``status='fit_failed'``) and the pre-fit
    scope refusal (``status='out_of_scope'``). The stats dict carries the
    observation's true ``n_bands`` (and the spec's ``k`` when the models can
    be built) even though no fit ran. Before this, an empty stats dict made
    :func:`ioptics.io._scalar_row` fill ``n_bands`` with 0 on exactly the
    rows a reader most wants to diagnose — the true band count was only
    recoverable by counting ``Rrs_obs`` rows in the spectral table.
    """
    stats = {'n_bands': int(np.asarray(record.wave).size)}
    try:
        models = spec.build_models(record.wave)
        stats['k'] = n_free_params(
            models, {'fit_Bp': getattr(spec.rt, 'fit_Bp', False)})
    except Exception:
        pass                    # model construction itself failed; omit k
    return RetrievalResult(
        dataset=record.dataset, obs_id=record.obs_id, algorithm=spec.name,
        fit_method=fit_method or spec.fit_method, stats=stats,
        status=status)


def _failed_result(spec, record, fit_method):
    """A minimal ``fit_failed`` result so one bad fit doesn't kill a batch."""
    return _unfit_result(spec, record, fit_method, 'fit_failed')


def _run_one_safe(spec, record, fit_method, perc):
    """``run_algorithm`` wrapped so a fit failure becomes a ``fit_failed`` row."""
    try:
        return run_algorithm(spec, record, fit_method=fit_method, perc=perc)
    except Exception:
        return _failed_result(spec, record, fit_method)


def _run_one_star(record, spec, fit_method, perc, strict):
    """Top-level worker for :func:`run_batch`'s process pool (picklable)."""
    if strict:
        return run_algorithm(spec, record, fit_method=fit_method, perc=perc)
    return _run_one_safe(spec, record, fit_method, perc)


def run_batch(spec, records, *, fit_method=None, n_cores=1, strict=True,
              perc=((16, 84), (2.5, 97.5))):
    """Run one algorithm over many records -> ``list[RetrievalResult]``.

    Mirrors ``bing.fitting.l23.batch_fit``'s parallelism (a
    ``ProcessPoolExecutor`` when ``n_cores > 1``); records are picklable so they
    cross the pool.

    Parameters
    ----------
    spec : AlgorithmSpec
        The algorithm to run.
    records : iterable of PreparedRecord
        The observations to fit.
    fit_method : str or None, optional
        Override the spec's fit method (``'chisq'`` | ``'mcmc'``).
    n_cores : int, optional
        Parallel workers (default 1 = serial).
    strict : bool, optional
        If ``True`` (default), a fit failure **propagates** (fail-fast — the
        development default, so bugs surface with a traceback). If ``False``, a
        failed fit becomes a ``fit_failed`` :class:`RetrievalResult` and the
        batch continues — the intended **production** mode for large sweeps
        (failures show up as ``status='fit_failed'`` rows + reduced coverage).
        *TODO (per JXP): make robust the default for production sweeps.*
    perc : tuple, optional
        Credible/confidence percentiles passed through to ``evaluate``.
    """
    records = list(records)
    if n_cores and n_cores > 1:
        from concurrent.futures import ProcessPoolExecutor
        from functools import partial
        fn = partial(_run_one_star, spec=spec, fit_method=fit_method,
                     perc=perc, strict=strict)
        # Pay the BING/JAX import once per worker at start-up rather than on
        # its first record (see :func:`_warm_fit_imports`).
        with ProcessPoolExecutor(max_workers=n_cores,
                                 initializer=_warm_fit_imports) as ex:
            return list(ex.map(fn, records))
    if strict:
        return [run_algorithm(spec, record, fit_method=fit_method, perc=perc)
                for record in records]
    return [_run_one_safe(spec, record, fit_method, perc) for record in records]


def _tag_pairs(results, records, sweep_id, algorithm):
    """Stamp ``provenance_id`` on each result and pair it with its record."""
    from ioptics import provenance
    pid = provenance.provenance_id(sweep_id, algorithm)
    pairs = []
    for res, rec in zip(results, records):
        res.provenance_id = pid
        pairs.append((res, rec))
    return pairs


#: Checkpoint cadence for the MCMC pass: ``run_sweep`` rewrites the results
#: tables after every this-many MCMC fits, so an interrupted multi-hour pass
#: keeps everything completed so far (the chains are already on disk — this
#: keeps the rows that reference them). ~200 fits ≈ 20-40 min of pooled work
#: between checkpoints at full-L23 scale, against a few seconds per rewrite.
MCMC_CHECKPOINT_EVERY = 200


def _record_seed(seed, algorithm, record):
    """Deterministic per-record seed for the legacy global ``np.random``.

    emcee 3 snapshots the global ``np.random`` state into the sampler at
    construction, and BING's walker init draws from the same global stream —
    so seeding it *per record* (from the sweep seed, the algorithm, and the
    record's identity, never from the worker process) makes each chain
    reproducible regardless of how records are distributed over a process
    pool, and identical between a serial and a pooled run. The algorithm is
    part of the key so two MCMC algorithms in one sweep do not share a
    walker-init stream for the same record. CRC32 rather than ``hash()``
    because the latter is salted per interpreter.
    """
    import zlib
    key = f'{seed}|{algorithm}|{record.dataset}|{record.obs_id}'.encode()
    return zlib.crc32(key)          # 0..2**32-1: valid for np.random.seed


def _warm_fit_imports():
    """Import the fitting stack **before** a per-record seed is set.

    ``bing.fitting.inference`` pulls in ``bing.evaluate``, which imports
    JAX (the robust RT backends, bing 2026-08-30), and importing JAX draws
    from the *legacy global* ``np.random`` stream — the very stream
    :func:`_record_seed` seeds and BING's walker init then draws from.

    That import is lazy (it lives inside :func:`fit_mcmc`), so in a fresh
    process it happens **after** ``np.random.seed(_record_seed(...))``: the
    first record a pool worker touches gets its walkers from a stream
    advanced past the seed, while a serial run — where prepping the records
    already imported BING — does not. Same seed, different chain, purely as
    a function of pool layout, which is exactly what Task 13(a) promises
    cannot happen. (It also splits a *single* worker: only its first record
    pays the import.)

    Warming the import here, ahead of the seed, makes the RNG state at
    walker init a function of the seed alone. Idempotent and ~free once the
    module is in ``sys.modules``.

    Also used as the ``initializer=`` of every fitting process pool
    (:func:`run_batch`, :func:`_mcmc_subset`), which is the belt to this
    braces: a worker then pays the multi-second JAX import **once at start-up**
    instead of on its first record, so the pool's records cost the same as one
    another and a wall-clock-per-fit estimate means something. One import
    reaches both fitters — ``bing.fitting.inference`` pulls in
    ``bing.evaluate``, which is where JAX (and, via it, ``chisq_fit``) comes
    from.
    """
    from bing.fitting import inference  # noqa: F401


def _mcmc_one(record, spec, sweep_id, pid, root, strict, perc, seed):
    """MCMC-fit one record and persist its chain; the pool worker.

    Top-level (picklable) so :func:`_mcmc_subset` can run it under a
    ``ProcessPoolExecutor``. Python 3.14's default start method on Linux is
    ``forkserver``, so callers must be import-safe (guard scripts with
    ``if __name__ == '__main__'``). Seeds the global RNG per record
    (:func:`_record_seed`, restored afterwards so serial callers are not
    left on a fit's stream), fits, evaluates, and saves the chain **from
    inside the worker** — burned per :func:`ioptics.evaluate.chain_burn` and
    thinned by :data:`ioptics.io.CHAIN_THIN` — so the raw 40 000-step chain
    never crosses the pool.

    Console handling: emcee's per-fit output (two tqdm bars + prints per
    record) is redirected to ``/dev/null`` — interleaved across a pool it is
    unreadable, and at full-L23 scale it is ~1 GB of log. Warnings are
    **not** lost to that redirect: they are captured and summarized to one
    ``[mcmc warn]`` line per fit, because on an unattended multi-hour robust
    run a numerical warning (overflow in a model power law, NaN percentiles)
    is the only early sign of a degenerate fit.

    A failure while *persisting* the chain is a storage problem, not a
    science result: under ``strict=False`` the evaluated fit is kept with
    ``chain_file=None`` rather than demoted to ``fit_failed``.
    """
    import contextlib
    import os
    import warnings as _warnings
    from collections import Counter

    from ioptics import evaluate, io

    declined = _prefit_decline(spec, record, 'mcmc')
    if declined is not None:
        declined.provenance_id = pid
        return declined
    # Before the seed, never after: importing the BING/JAX fitting stack
    # consumes global-RNG draws (see _warm_fit_imports).
    _warm_fit_imports()
    rng_state = np.random.get_state()
    np.random.seed(_record_seed(seed, spec.name, record))
    res, chains = None, None
    caught = []
    try:
        with _warnings.catch_warnings(record=True) as caught:
            _warnings.simplefilter('always')
            with open(os.devnull, 'w') as devnull, \
                    contextlib.redirect_stdout(devnull), \
                    contextlib.redirect_stderr(devnull):
                models, rt_dict, chains = fit_mcmc(spec, record)
            res = evaluate.from_chains(spec, record, models, rt_dict, chains,
                                       perc=perc,
                                       geom=resolve_geometry(spec, record))
    except UnderdeterminedFitError:
        # a chosen status in BOTH strict modes, like run_algorithm
        res = _failed_result(spec, record, 'mcmc')
    except Exception:
        if strict:
            raise
        res = _failed_result(spec, record, 'mcmc')
    finally:
        np.random.set_state(rng_state)

    if chains is not None and res is not None and res.components:
        try:
            res.chain_file = str(io.save_chain(
                sweep_id, spec.name, record, chains, root=root,
                pnames=list(res.params),
                burn=evaluate.chain_burn(spec, chains), thin=io.CHAIN_THIN,
                nburn_sampler=spec.mcmc.nburn))
        except Exception:
            if strict:
                raise
            print(f'[mcmc warn] {record.dataset}:{record.obs_id} chain save '
                  f'failed; fit kept without a chain file', flush=True)
    if caught:
        top = Counter(f'{w.category.__name__}: {w.message}'
                      for w in caught).most_common(3)
        gist = '; '.join(f'{msg} (x{n})' for msg, n in top)
        print(f'[mcmc warn] {record.dataset}:{record.obs_id} '
              f'{len(caught)} warnings: {gist}', flush=True)
    res.provenance_id = pid
    return res


def _mcmc_subset(spec, records, sweep_id, *, root=None, strict=True,
                 perc=((16, 84), (2.5, 97.5)), n_cores=1, seed=None,
                 progress_from=0, progress_total=None):
    """MCMC-fit a subset, **saving each posterior chain** to the sweep's
    ``chains/`` dir and stamping the result's ``chain_file`` +
    ``provenance_id``. Returns ``[(result, record), ...]``.

    Pooled over ``n_cores`` (Stage 7, Task 13). This was deliberately serial
    when the subset was small ("the subset is small and the raw chains are
    large"); at the full-L23 scale of 3 320 records × ~140 s that premise
    fails (~5.4 days serial). Each worker persists its own chain — burned +
    thinned, see :func:`_mcmc_one` — so nothing large returns across the
    pool, and the RNG is seeded per **record**, not per process
    (:func:`_record_seed`), so the chains do not depend on the pool layout.

    Applies the same pre-fit decisions as :func:`run_algorithm`, in both
    strict modes: a red-peaked record is declined ``out_of_scope`` (unless
    ``spec.fits_turbid``) and an underdetermined one becomes ``fit_failed``
    — the MCMC subset must agree with its own sweep's χ² pass on which
    records are fit at all (PR #11 review finding).

    ``progress_from``/``progress_total`` only relabel the per-fit progress
    lines, for callers (``run_sweep``) that feed the subset in checkpointed
    chunks but want one running count.
    """
    from ioptics import provenance

    records = list(records)
    pid = provenance.provenance_id(sweep_id, spec.name)
    n = len(records)
    total = progress_total if progress_total is not None else n

    def _progress(i, record, res):
        print(f'[mcmc {progress_from + i + 1}/{total}] '
              f'{record.dataset}:{record.obs_id} {res.status}', flush=True)

    if n_cores and n_cores > 1:
        from concurrent.futures import ProcessPoolExecutor
        from functools import partial
        fn = partial(_mcmc_one, spec=spec, sweep_id=sweep_id, pid=pid,
                     root=root, strict=strict, perc=perc, seed=seed)
        pairs = []
        # Warm the fitting stack at worker start-up; ``_mcmc_one`` calls the
        # same function again before each record's seed, and it is idempotent.
        with ProcessPoolExecutor(max_workers=n_cores,
                                 initializer=_warm_fit_imports) as ex:
            for i, (res, record) in enumerate(zip(ex.map(fn, records),
                                                  records)):
                _progress(i, record, res)
                pairs.append((res, record))
        return pairs

    pairs = []
    for i, record in enumerate(records):
        res = _mcmc_one(record, spec, sweep_id, pid, root, strict, perc, seed)
        _progress(i, record, res)
        pairs.append((res, record))
    return pairs


def run_sweep(cfg, *, obs_ids=None, n_cores=1, strict=True, root=None):
    """Run a full sweep (all algorithms × all records) and write the outputs.

    For each algorithm: a least-squares (χ²) fit over **all** records, then —
    when ``cfg.mcmc_subset`` is set — an MCMC fit over the first ``mcmc_subset``
    records. Every result is stamped with its ``provenance_id``; the results are
    flattened to ``results_{spectral,scalar}.parquet`` and a ``provenance.yaml``
    is written under ``$OS_COLOR/IOPtics/runs/<sweep_id>/`` (or ``root=``).

    Parameters
    ----------
    cfg : SweepConfig
        The sweep config (``sweep_id``, ``datasets``, ``algorithms``,
        ``noise_model``, ``mcmc_subset``, ``seed``, ``dataset_opts``,
        ``leaderboard``, ``results_root``). ``dataset_opts[dataset]`` is
        forwarded verbatim to :func:`ioptics.prep.prep_dataset` as adapter load
        options and recorded under that dataset's provenance block.
    obs_ids : iterable, mapping or None, optional
        Restrict the prep to these observation ids (default: all). An iterable
        applies to **every** dataset; a **mapping** ``{dataset: ids}`` bounds each
        one separately, with a dataset absent from the mapping running in full.

        The mapping form is what makes a mixed-dataset sweep tractable. PANGAEA
        enumerates 64 071 observations of which only ~4 000 carry any truth to score
        against, so an unbounded ``{L23, PANGAEA}`` sweep spends ~95% of its fits
        producing rows no metric can use. Bounding PANGAEA while leaving L23 whole
        is not expressible with a single id list.
    n_cores : int, optional
        Parallel workers for prep and fitting.
    strict : bool, optional
        Fail-fast (default) vs robust ``fit_failed`` — see :func:`run_batch`.
    root : str or None, optional
        Output root override; falls back to ``cfg.results_root`` then ``$OS_COLOR``.

    Returns
    -------
    dict
        ``{sweep_id, n_results, spectral, scalar, provenance}`` paths/counts.
    """
    from ioptics import io, prep, provenance
    from ioptics.algorithms import registry

    out_root = root if root is not None else cfg.results_root

    # Prep records per dataset (native grid, sweep-level noise model + seed).
    is_map = isinstance(obs_ids, Mapping)
    records, datasets_info = [], {}
    dataset_opts = getattr(cfg, 'dataset_opts', None) or {}
    for dataset in cfg.datasets:
        ids = obs_ids.get(dataset) if is_map else obs_ids
        # Per-dataset adapter load options (e.g. ``{'L23': {'X': 4}}``) reach
        # the adapter through ``prep_dataset``'s ``**load_opts`` passthrough.
        # ``config.load`` has already rejected a name outside ``cfg.datasets``,
        # so nothing here can be silently dropped.
        opts = dict(dataset_opts.get(dataset, {}))
        recs = prep.prep_dataset(dataset, obs_ids=ids,
                                 noise=cfg.noise_model, seed=cfg.seed,
                                 wv_min=cfg.wv_min, wv_max=cfg.wv_max,
                                 n_cores=n_cores, **opts)
        records.extend(recs)
        # Record the bound in provenance: "PANGAEA n_obs=3896" is a different claim
        # from "PANGAEA n_obs=3896 out of 64071 because the rest carry no truth",
        # and only the second is reproducible.
        info = {'n_obs': len(recs)}
        if opts:
            # verbatim, beside the count they produced: 3 320 L23 records at
            # X=1 and at X=4 are different data, and the count alone cannot
            # tell them apart.
            info['opts'] = opts
        if ids is not None:
            info['n_requested'] = len(list(ids))
            info['bounded'] = True
        datasets_info[dataset] = info

    # Per-algorithm overrides are **applied** here, not ignored: a config asking for
    # `maxfev: 40000` used to run at the registry default while the provenance file
    # recorded the default too, so nothing revealed that the request had no effect.
    # An unknown key raises (see AlgorithmSpec.with_overrides), and the provenance
    # digest is taken from the overridden spec, so an overridden sweep cannot pool
    # with a default one as "the same algorithm".
    specs = [registry.get(ac.name).with_overrides(ac.overrides)
             for ac in cfg.algorithms]

    pairs = []
    any_mcmc = False
    for ac, spec in zip(cfg.algorithms, specs):
        # χ² over all records (the sweep's fast first pass; every algorithm).
        chisq = run_batch(spec, records, fit_method='chisq', n_cores=n_cores,
                          strict=strict)
        pairs.extend(_tag_pairs(chisq, records, cfg.sweep_id, spec.name))
        # Checkpoint: a multi-hour sweep must not hold hours of results only
        # in memory — a worker crash late in the MCMC pass used to discard
        # the completed χ² pass and orphan every chain already on disk
        # (Task-13 review finding). ``write_results`` rewrites the tables
        # whole, so each checkpoint leaves a consistent pair on disk.
        io.write_results(cfg.sweep_id, pairs, root=out_root)
        # MCMC over the subset — only for algorithms that opt in (effective
        # fit_method == 'mcmc'); not every method uses MCMC.
        uses_mcmc = (ac.fit_method or cfg.fit_method) == 'mcmc'
        if uses_mcmc and cfg.mcmc_subset:
            any_mcmc = True
            subset = records[:int(cfg.mcmc_subset)]
            for lo in range(0, len(subset), MCMC_CHECKPOINT_EVERY):
                chunk = subset[lo:lo + MCMC_CHECKPOINT_EVERY]
                pairs.extend(_mcmc_subset(spec, chunk, cfg.sweep_id,
                                          root=out_root, strict=strict,
                                          n_cores=n_cores, seed=cfg.seed,
                                          progress_from=lo,
                                          progress_total=len(subset)))
                io.write_results(cfg.sweep_id, pairs, root=out_root)

    paths = io.write_results(cfg.sweep_id, pairs, root=out_root)
    prov = provenance.build(cfg.sweep_id, cfg, specs, datasets=datasets_info)
    if any_mcmc:
        # The chain-persistence policy is sweep-level provenance: it changes
        # what is on disk, not what the fit did, so it is recorded here and
        # deliberately kept out of the per-algorithm digest.
        prov['chains'] = {
            'thin': int(io.CHAIN_THIN),
            'burn': 'spec.mcmc.nburn, capped at half the chain '
                    '(evaluate.chain_burn)',
        }
    ppath = provenance.write(cfg.sweep_id, prov, root=out_root)

    return {'sweep_id': cfg.sweep_id, 'n_results': len(pairs),
            'spectral': paths['spectral'], 'scalar': paths['scalar'],
            'provenance': ppath}

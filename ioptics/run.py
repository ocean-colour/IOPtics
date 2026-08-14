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

.. note::

   Building BING models loads the L23 pure-water backscattering data, so the
   functions here require the L23 tree present (they are exercised under Tier-2
   ``@needs_l23`` tests).
"""

from __future__ import annotations

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


def _prior_bounds(models):
    """Lower/upper parameter bounds from the models' priors (a then bb)."""
    lows, highs = [], []
    for model in models:
        for prior in model.priors.priors:
            lows.append(prior.pmin)
            highs.append(prior.pmax)
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


def _prepare(spec, record):
    """Build ``(p, models, rt_dict)`` for ``record``, models seeded truth-free."""
    from bing.rt import defs as rt_defs
    from bing.models import utils as model_utils

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
    # on the a-model — mirror ``bing.fitting.l23``.
    if spec.rt.include_Chl_fl:
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


def _refuse_underdetermined(models, record):
    """Raise :class:`UnderdeterminedFitError` when ``n_bands <= k``."""
    k = int(models[0].nparam + models[1].nparam)
    n_bands = int(np.asarray(record.wave).size)
    if n_bands <= k:
        raise UnderdeterminedFitError(
            f'{record.dataset}/{record.obs_id}: n_bands={n_bands} <= k={k} '
            '-- the fit is underdetermined by construction')


def fit_chisq(spec, record):
    """Least-squares fit of one record; returns ``(models, rt_dict, ans, cov)``.

    The Stage-2 fitting core (used by :func:`run_algorithm` and exercised
    directly by tests). Builds models, seeds a truth-free initial guess, and
    calls ``bing.fitting.chisq_fit.fit`` with prior-derived bounds and the
    spec's ``maxfev`` evaluation budget. Refuses an underdetermined record
    (``n_bands <= k``) up front with :class:`UnderdeterminedFitError` instead
    of letting scipy fail with a ``LinAlgError``.
    """
    from bing.fitting import chisq_fit

    _, models, rt_dict = _prepare(spec, record)
    _refuse_underdetermined(models, record)
    p0 = initial_guess(models, record)
    bounds = _prior_bounds(models)
    items = (np.asarray(record.Rrs, dtype=float),
             np.asarray(record.varRrs, dtype=float), p0, record.obs_id)
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
    """
    from bing.fitting import inference as bing_inf

    _, models, rt_dict = _prepare(spec, record)
    _refuse_underdetermined(models, record)
    p0 = initial_guess(models, record)

    pdict = bing_inf.init_mcmc(models, nsteps=spec.mcmc.nsteps,
                               nburn=spec.mcmc.nburn)
    # A single record is fit in isolation, so synthesize a positional index of 0
    # with size-1 Chl/Y arrays (BING keys Chl/Y by this idx). This replaces
    # ``int(record.obs_id)``, which fails on non-integer ids (e.g. GLORIA's
    # 'GID_1'); the real obs id still rides on the result via ``record.obs_id``.
    idx = 0
    pdict['Chl'] = np.array([float(record.init.get('Chl', 0.0))])
    pdict['Y'] = np.array([float(record.init.get('Y', 0.0))])

    items = (np.asarray(record.Rrs, dtype=float),
             np.asarray(record.varRrs, dtype=float), p0, idx)
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
    if not getattr(spec, 'fits_turbid', False) and is_red_peaked(record):
        return _unfit_result(spec, record, method, 'out_of_scope')
    try:
        if method == 'chisq':
            models, rt_dict, ans, cov = fit_chisq(spec, record)
            return evaluate.from_chisq(spec, record, models, rt_dict, ans, cov,
                                       perc=perc)
        if method == 'mcmc':
            models, rt_dict, chains = fit_mcmc(spec, record)
            return evaluate.from_chains(spec, record, models, rt_dict, chains,
                                        perc=perc)
    except UnderdeterminedFitError:
        return _failed_result(spec, record, method)
    raise ValueError(f"unknown fit_method {method!r} (expected 'chisq'|'mcmc')")


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
        stats['k'] = int(models[0].nparam + models[1].nparam)
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
        with ProcessPoolExecutor(max_workers=n_cores) as ex:
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


def _mcmc_subset(spec, records, sweep_id, *, root=None, strict=True,
                 perc=((16, 84), (2.5, 97.5))):
    """MCMC-fit a subset serially, **saving each posterior chain** to the
    sweep's ``chains/`` dir and stamping the result's ``chain_file`` +
    ``provenance_id``. Returns ``[(result, record), ...]``.

    Serial (not pooled): the subset is small and the raw chains are large, so
    persisting them here avoids shipping chains back across a process pool.
    """
    from ioptics import evaluate, io, provenance

    pid = provenance.provenance_id(sweep_id, spec.name)
    pairs = []
    for record in records:
        try:
            models, rt_dict, chains = fit_mcmc(spec, record)
            res = evaluate.from_chains(spec, record, models, rt_dict, chains,
                                       perc=perc)
            res.chain_file = str(io.save_chain(sweep_id, spec.name, record,
                                               chains, root=root,
                                               pnames=list(res.params)))
        except Exception:
            if strict:
                raise
            res = _failed_result(spec, record, 'mcmc')
        res.provenance_id = pid
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
        ``noise_model``, ``mcmc_subset``, ``seed``, ``results_root``).
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
    for dataset in cfg.datasets:
        ids = obs_ids.get(dataset) if is_map else obs_ids
        recs = prep.prep_dataset(dataset, obs_ids=ids,
                                 noise=cfg.noise_model, seed=cfg.seed,
                                 wv_min=cfg.wv_min, wv_max=cfg.wv_max,
                                 n_cores=n_cores)
        records.extend(recs)
        # Record the bound in provenance: "PANGAEA n_obs=3896" is a different claim
        # from "PANGAEA n_obs=3896 out of 64071 because the rest carry no truth",
        # and only the second is reproducible.
        info = {'n_obs': len(recs)}
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
    for ac, spec in zip(cfg.algorithms, specs):
        # χ² over all records (the sweep's fast first pass; every algorithm).
        chisq = run_batch(spec, records, fit_method='chisq', n_cores=n_cores,
                          strict=strict)
        pairs.extend(_tag_pairs(chisq, records, cfg.sweep_id, spec.name))
        # MCMC over the subset — only for algorithms that opt in (effective
        # fit_method == 'mcmc'); not every method uses MCMC.
        uses_mcmc = (ac.fit_method or cfg.fit_method) == 'mcmc'
        if uses_mcmc and cfg.mcmc_subset:
            subset = records[:int(cfg.mcmc_subset)]
            pairs.extend(_mcmc_subset(spec, subset, cfg.sweep_id,
                                      root=out_root, strict=strict))

    paths = io.write_results(cfg.sweep_id, pairs, root=out_root)
    prov = provenance.build(cfg.sweep_id, cfg, specs, datasets=datasets_info)
    ppath = provenance.write(cfg.sweep_id, prov, root=out_root)

    return {'sweep_id': cfg.sweep_id, 'n_results': len(pairs),
            'spectral': paths['spectral'], 'scalar': paths['scalar'],
            'provenance': ppath}

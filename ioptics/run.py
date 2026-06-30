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

import numpy as np

from ioptics.records import RetrievalResult


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


def initial_guess(models, record):
    """A **truth-free** least-squares starting point from the observed ``Rrs``.

    Performs a QAA-style band inversion of ``record.Rrs`` using BING's Gordon
    coefficients and the models' own pure-water terms (``a_w`` on the a-model,
    ``bb_w`` on the bb-model) to estimate ``a_nw``/``bb_nw``, then seeds each
    model's parameters via its ``init_guess`` (amplitudes log10'd to match the
    log-uniform priors). Never touches ``record.truth``.
    """
    from bing.rt import rrs as bing_rrs

    wave = np.asarray(record.wave, dtype=float)
    Rrs = np.asarray(record.Rrs, dtype=float)
    a_w = np.asarray(models[0].a_w, dtype=float)
    bb_w = np.asarray(models[1].bb_w, dtype=float)

    # Gordon: rrs = G1 u + G2 u^2, u = bb / (a + bb)  ->  solve for u.
    rrs = Rrs / (bing_rrs.A_Rrs + bing_rrs.B_Rrs * Rrs)
    G1, G2 = bing_rrs.G1_STANDARD, bing_rrs.G2_STANDARD
    disc = np.clip(G1 * G1 + 4.0 * G2 * rrs, 0.0, None)
    u = np.clip((-G1 + np.sqrt(disc)) / (2.0 * G2), 1e-3, 1.0 - 1e-3)

    # Red anchor (~670 nm): a ~ a_w there (non-water absorption is small).
    iref = int(np.argmin(np.abs(wave - 670.0)))
    a_ref = a_w[iref]
    bb_ref = u[iref] * a_ref / (1.0 - u[iref])
    bbnw_ref = max(bb_ref - bb_w[iref], 1e-4)

    Y = float(record.init.get('Y', 1.0))
    bb_nw = bbnw_ref * (wave[iref] / wave) ** Y
    bb = bb_w + bb_nw
    a_tot = bb * (1.0 - u) / u
    a_nw = np.clip(a_tot - a_w, 1e-4, None)
    bb_nw = np.clip(bb_nw, 1e-5, None)

    p0_a = np.atleast_1d(models[0].init_guess(a_nw)).astype(float)
    p0_b = np.atleast_1d(models[1].init_guess(bb_nw)).astype(float)
    p0 = np.concatenate([p0_a, p0_b])

    # log10 the log-flavored amplitudes (mirrors bing.fitting.l23.prep_one_l23).
    log_mask = _log_mask(models)
    p0[log_mask] = np.log10(np.clip(p0[log_mask], 1e-10, None))

    # Keep the guess feasible w.r.t. the prior bounds.
    lo, hi = _prior_bounds(models)
    return np.clip(p0, lo, hi)


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


def fit_chisq(spec, record):
    """Least-squares fit of one record; returns ``(models, rt_dict, ans, cov)``.

    The Stage-2 fitting core (used by :func:`run_algorithm` and exercised
    directly by tests). Builds models, seeds a truth-free initial guess, and
    calls ``bing.fitting.chisq_fit.fit`` with prior-derived bounds.
    """
    from bing.fitting import chisq_fit

    _, models, rt_dict = _prepare(spec, record)
    p0 = initial_guess(models, record)
    bounds = _prior_bounds(models)
    items = (np.asarray(record.Rrs, dtype=float),
             np.asarray(record.varRrs, dtype=float), p0, record.obs_id)
    ans, cov, _ = chisq_fit.fit(items, models, rt_dict, bounds=bounds)
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
    p0 = initial_guess(models, record)

    pdict = bing_inf.init_mcmc(models, nsteps=spec.mcmc.nsteps,
                               nburn=spec.mcmc.nburn)
    idx = int(record.obs_id)                       # BING idx-keyed Chl/Y lookup
    pdict['Chl'] = np.zeros(idx + 1)
    pdict['Chl'][idx] = float(record.init.get('Chl', 0.0))
    pdict['Y'] = np.zeros(idx + 1)
    pdict['Y'][idx] = float(record.init.get('Y', 0.0))

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
    """
    from ioptics import evaluate

    method = fit_method or spec.fit_method
    if method == 'chisq':
        models, rt_dict, ans, cov = fit_chisq(spec, record)
        return evaluate.from_chisq(spec, record, models, rt_dict, ans, cov,
                                   perc=perc)
    if method == 'mcmc':
        models, rt_dict, chains = fit_mcmc(spec, record)
        return evaluate.from_chains(spec, record, models, rt_dict, chains,
                                    perc=perc)
    raise ValueError(f"unknown fit_method {method!r} (expected 'chisq'|'mcmc')")


def _failed_result(spec, record, fit_method):
    """A minimal ``fit_failed`` result so one bad fit doesn't kill a batch."""
    return RetrievalResult(
        dataset=record.dataset, obs_id=record.obs_id, algorithm=spec.name,
        fit_method=fit_method or spec.fit_method, status='fit_failed')


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
                                               chains, root=root))
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
    obs_ids : iterable or None, optional
        Restrict the prep to these observation ids (default: all). Handy for
        tests / partial sweeps.
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
    records, datasets_info = [], {}
    for dataset in cfg.datasets:
        recs = prep.prep_dataset(dataset, obs_ids=obs_ids,
                                 noise=cfg.noise_model, seed=cfg.seed,
                                 n_cores=n_cores)
        records.extend(recs)
        datasets_info[dataset] = {'n_obs': len(recs)}

    specs = [registry.get(ac.name) for ac in cfg.algorithms]

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

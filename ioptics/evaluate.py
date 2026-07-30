"""Turn a fit into a :class:`~ioptics.records.RetrievalResult`.

Reconstructs ``a(lambda)`` / ``bb(lambda)`` and the sub-components
(``a_ph``/``a_dg``/``bb_p``) with uncertainty, plus the model ``Rrs`` and the
fit statistics (chi^2, reduced chi^2, AIC, BIC). Uncertainty is produced the
same way for both fit methods so intervals are comparable:

- **least-squares** (:func:`from_chisq`) — draw parameter samples from the
  fitted ``MultivariateNormal(ans, cov)`` and push each through BING's forward
  model, then take percentiles (the covariance-propagated bands).
- **MCMC** (``from_chains``) — same percentiles over the posterior chain
  (arrives in Stage 3).

This module wraps ``bing.evaluate`` / ``bing.stats``; it operates on already-built
models (so it does not itself load L23 data — but its inputs come from
:func:`ioptics.run.fit_chisq`, which does).
"""

from __future__ import annotations

import numpy as np

from ioptics.records import (CHI2NU_POOR_FIT, RED_PEAK_NM,
                             ComponentFit, RetrievalResult)

# Components reconstructed for every retrieval (spectral).
_SPECTRAL = ('a', 'bb', 'a_ph', 'a_dg', 'bb_p', 'Rrs_model')


def _component_fit(wave, samples, perc):
    """Build a :class:`ComponentFit` from ``(n_samples, n_wave)`` draws."""
    (lo1, hi1), (lo2, hi2) = perc
    return ComponentFit(
        wave=np.asarray(wave, dtype=float),
        med=np.median(samples, axis=0),
        lo68=np.percentile(samples, lo1, axis=0),
        hi68=np.percentile(samples, hi1, axis=0),
        lo95=np.percentile(samples, lo2, axis=0),
        hi95=np.percentile(samples, hi2, axis=0),
    )


def _shape_param_names(models):
    """Names of the fitted parameters a model holds in **linear** space.

    These are the shape descriptors -- exponential slopes and power-law
    exponents -- as opposed to the log10 amplitudes. Each bing model
    declares the split in ``log_params``; a model that declares nothing is
    treated as all-log10 (bing's own default) and contributes none.

    Deriving the list per model, rather than hard-coding names, is what lets
    a new model's shape parameters reach the results table without editing
    this function: ``expb_pow`` yields ``Sdg``/``beta`` exactly as before,
    while the two-component backscattering models add ``eta_min``/
    ``eta_org``.

    Parameters
    ----------
    models : list
        ``[a_model, bb_model]``, in parameter order.

    Returns
    -------
    list of str
        Parameter names, in fit order.
    """
    names = []
    for model in models:
        declared = getattr(model, 'log_params', None)
        if declared is None:
            continue
        for pname, is_log in zip(list(model.pnames), list(declared)):
            if not is_log:
                names.append(pname)
    return names


def _fit_status(record, stats, finite):
    """Classify a fit: ``ok`` | ``poor_fit`` | ``out_of_scope`` | ``fit_failed``.

    A converged fit whose reduced chi-squared exceeds
    :data:`ioptics.records.CHI2NU_POOR_FIT` is not a solution. Which of the
    two "bad fit" labels it gets depends on the *spectrum*, not the fit: one
    peaking redward of :data:`ioptics.records.RED_PEAK_NM` is turbid, i.e.
    outside what this model family is built for, so the failure is a
    statement about scope rather than about this algorithm.

    Parameters
    ----------
    record : PreparedRecord
        The observation, for its Rrs peak wavelength.
    stats : dict
        Fit statistics; ``chi2_nu`` is read.
    finite : bool
        Whether the fit produced usable (finite) parameters.

    Returns
    -------
    str
        A member of :data:`ioptics.records.STATUSES`.
    """
    if not finite:
        return 'fit_failed'
    chi2_nu = float(stats.get('chi2_nu', np.nan))
    if np.isfinite(chi2_nu) and chi2_nu <= CHI2NU_POOR_FIT:
        return 'ok'
    Rrs = np.asarray(record.Rrs, dtype=float)
    if np.any(np.isfinite(Rrs)):
        peak = float(np.asarray(record.wave, dtype=float)[int(np.nanargmax(Rrs))])
        if peak > RED_PEAK_NM:
            return 'out_of_scope'
    return 'poor_fit'


def _assemble(spec, record, models, rt_dict, aparams, bparams, point_params,
              fit_method, perc):
    """Build a :class:`RetrievalResult` from posterior **parameter samples**.

    Shared by both fit methods so χ² (covariance draws) and MCMC (chain) yield
    identically-assembled components, params, scalars, and stats. ``aparams`` /
    ``bparams`` are ``(n_samples, nparam)`` draws; ``point_params`` is the
    point-estimate parameter vector used for the fit statistics.
    """
    from bing.evaluate import calc_Rrs_from_models
    from bing import stats as bing_stats

    na = models[0].nparam
    k = na + models[1].nparam
    n_bands = int(record.wave.size)

    # Forward-model every sample, plus the sub-components over the samples.
    Rrs_s, a_s, bb_s = calc_Rrs_from_models(
        models[0], aparams, models[1], bparams, rt_dict, full_return=True)
    a_dg_s, a_ph_s = models[0].eval_anw(aparams, retsub_comps=True)
    bb_p_s = models[1].eval_bbnw(bparams)
    arrays = {'a': a_s, 'bb': bb_s, 'a_ph': a_ph_s, 'a_dg': a_dg_s,
              'bb_p': bb_p_s, 'Rrs_model': Rrs_s}
    components = {key: _component_fit(record.wave, arrays[key], perc)
                  for key in _SPECTRAL}

    # Fit parameters: sample median + 1-sigma (fit space; log10 for amplitudes).
    samples = np.concatenate([np.atleast_2d(aparams), np.atleast_2d(bparams)],
                             axis=1)
    pnames = list(models[0].pnames) + list(models[1].pnames)
    med, std = np.median(samples, axis=0), np.std(samples, axis=0)
    params = {pn: (float(med[i]), float(std[i])) for i, pn in enumerate(pnames)}

    # Derived scalars.
    i440 = int(np.argmin(np.abs(record.wave - 440.0)))
    adg440 = np.asarray(a_dg_s)[:, i440]
    scalars = {'a_cdom440': (float(np.median(adg440)), float(np.std(adg440)))}
    # Promote the model's shape parameters (its linear-space ones). For the
    # open-ocean models this is exactly Sdg and beta, as before.
    for key in _shape_param_names(models):
        if key in params:
            scalars[key] = params[key]

    # Fit statistics at the point estimate (on the native variable-Gordon model).
    pp = np.atleast_2d(np.asarray(point_params, dtype=float))   # (1, k)
    Rrs_pt = calc_Rrs_from_models(models[0], pp[:, :na], models[1], pp[:, na:],
                                  rt_dict, full_return=True)[0]
    Rrs_pt = np.atleast_1d(np.squeeze(np.asarray(Rrs_pt, dtype=float)))
    sigma = np.sqrt(np.asarray(record.varRrs, dtype=float))
    chi2 = float(bing_stats.calc_chisq(Rrs_pt,
                                       np.asarray(record.Rrs, dtype=float),
                                       1.0, noise_term=sigma))
    dof = max(n_bands - k, 1)
    # AIC/BIC per bing.stats.calc_ICs formulas, but on our variable-Gordon
    # model_Rrs (calc_ICs re-derives Rrs without rt_dict, which would mismatch).
    stats = {'chi2': chi2, 'chi2_nu': chi2 / dof, 'AIC': 2.0 * k + chi2,
             'BIC': k * np.log(n_bands) + chi2, 'n_bands': n_bands, 'k': k}

    finite = bool(np.all(np.isfinite(point_params)) and np.all(np.isfinite(Rrs_pt)))
    return RetrievalResult(
        dataset=record.dataset, obs_id=record.obs_id, algorithm=spec.name,
        fit_method=fit_method, components=components, params=params,
        scalars=scalars, stats=stats,
        status=_fit_status(record, stats, finite), provenance_id='')


def from_chisq(spec, record, models, rt_dict, ans, cov, *,
               perc=((16, 84), (2.5, 97.5)), n_samples=1000, seed=1234):
    """Assemble a :class:`RetrievalResult` from a least-squares fit.

    Draws ``n_samples`` from the fitted ``MultivariateNormal(ans, cov)`` and
    pushes them through the forward model (the covariance-propagated bands), then
    delegates to :func:`_assemble` with ``ans`` as the point estimate.
    """
    ans = np.asarray(ans, dtype=float)
    cov = np.asarray(cov, dtype=float)
    na = models[0].nparam
    rng = np.random.default_rng(seed)
    samples = rng.multivariate_normal(ans, cov, size=n_samples,
                                      check_valid='ignore')
    return _assemble(spec, record, models, rt_dict, samples[:, :na],
                     samples[:, na:], ans, 'chisq', perc)


def from_chains(spec, record, models, rt_dict, chains, *,
                perc=((16, 84), (2.5, 97.5))):
    """Assemble a :class:`RetrievalResult` from an MCMC posterior chain.

    Burns/thins the emcee ``chains`` (shape ``(nsteps, nwalkers, nparam)``) to a
    flat ``(n_samples, nparam)`` posterior, then delegates to :func:`_assemble`
    with the posterior median as the point estimate — so the 68/95 bands are
    built exactly as in the χ² path.
    """
    from bing.evaluate import thin_burn_chains

    chains = np.asarray(chains, dtype=float)
    na = models[0].nparam
    # Burn from the spec (capped so a tiny-nsteps run never discards everything).
    burn = min(int(spec.mcmc.nburn), max(chains.shape[0] // 2, 0))
    flat = thin_burn_chains(chains, burn=burn)
    point = np.median(flat, axis=0)
    return _assemble(spec, record, models, rt_dict, flat[:, :na], flat[:, na:],
                     point, 'mcmc', perc)

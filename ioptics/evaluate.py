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

from ioptics.records import ComponentFit, RetrievalResult

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


def from_chisq(spec, record, models, rt_dict, ans, cov, *,
               perc=((16, 84), (2.5, 97.5)), n_samples=1000, seed=1234):
    """Assemble a :class:`RetrievalResult` from a least-squares fit.

    Parameters
    ----------
    spec : AlgorithmSpec
        The algorithm that produced the fit.
    record : PreparedRecord
        The fitted observation.
    models : list
        The built ``[a_nw, bb_nw]`` BING models (already seeded).
    rt_dict : dict
        Radiative-transfer configuration used by the forward model.
    ans, cov : numpy.ndarray
        The least-squares solution and its covariance (from
        ``bing.fitting.chisq_fit.fit``).
    perc : tuple, optional
        ``((lo68, hi68), (lo95, hi95))`` percentiles for the bands.
    n_samples : int, optional
        Number of covariance draws for the bands.
    seed : int, optional
        RNG seed (the bands are reproducible by default).
    """
    from bing.evaluate import calc_Rrs_from_models
    from bing import stats as bing_stats

    ans = np.asarray(ans, dtype=float)
    cov = np.asarray(cov, dtype=float)
    na = models[0].nparam
    k = na + models[1].nparam
    n_bands = int(record.wave.size)

    finite = bool(np.all(np.isfinite(ans)) and np.all(np.isfinite(cov)))

    # --- covariance-propagated samples through the forward model ---
    rng = np.random.default_rng(seed)
    samples = rng.multivariate_normal(ans, cov, size=n_samples,
                                      check_valid='ignore')
    aparams, bparams = samples[:, :na], samples[:, na:]
    Rrs_s, a_s, bb_s = calc_Rrs_from_models(
        models[0], aparams, models[1], bparams, rt_dict, full_return=True)
    a_dg_s, a_ph_s = models[0].eval_anw(aparams, retsub_comps=True)
    bb_p_s = models[1].eval_bbnw(bparams)

    arrays = {'a': a_s, 'bb': bb_s, 'a_ph': a_ph_s, 'a_dg': a_dg_s,
              'bb_p': bb_p_s, 'Rrs_model': Rrs_s}
    components = {key: _component_fit(record.wave, arrays[key], perc)
                  for key in _SPECTRAL}

    # --- fit parameters: median + 1-sigma (in fit space; log10 for amplitudes) ---
    pnames = list(models[0].pnames) + list(models[1].pnames)
    sig = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    params = {pn: (float(ans[i]), float(sig[i])) for i, pn in enumerate(pnames)}

    # --- derived scalars ---
    i440 = int(np.argmin(np.abs(record.wave - 440.0)))
    adg440 = a_dg_s[:, i440]
    scalars = {'a_cdom440': (float(np.median(adg440)), float(np.std(adg440)))}
    for key in ('Sdg', 'beta'):
        if key in params:
            scalars[key] = params[key]

    # --- fit statistics (point estimate, on the native variable-Gordon model) ---
    # Pass params as (1, nparam) so the model evals don't read a 1-D vector as
    # N one-parameter samples; squeeze back to a per-wavelength spectrum.
    Rrs_pt = calc_Rrs_from_models(models[0], ans[None, :na], models[1],
                                  ans[None, na:], rt_dict, full_return=True)[0]
    Rrs_pt = np.atleast_1d(np.squeeze(np.asarray(Rrs_pt, dtype=float)))
    sigma = np.sqrt(np.asarray(record.varRrs, dtype=float))
    chi2 = float(bing_stats.calc_chisq(np.asarray(Rrs_pt, dtype=float),
                                       np.asarray(record.Rrs, dtype=float),
                                       1.0, noise_term=sigma))
    dof = max(n_bands - k, 1)
    # AIC/BIC per bing.stats.calc_ICs, but using our variable-Gordon model_Rrs
    # (calc_ICs re-derives model_Rrs without rt_dict, which would mismatch).
    stats = {
        'chi2': chi2,
        'chi2_nu': chi2 / dof,
        'AIC': 2.0 * k + chi2,
        'BIC': k * np.log(n_bands) + chi2,
        'n_bands': n_bands,
        'k': k,
    }

    status = 'ok' if finite else 'fit_failed'

    return RetrievalResult(
        dataset=record.dataset, obs_id=record.obs_id, algorithm=spec.name,
        fit_method='chisq', components=components, params=params,
        scalars=scalars, stats=stats, status=status, provenance_id='')

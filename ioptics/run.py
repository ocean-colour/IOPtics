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


def run_algorithm(spec, record, *, fit_method=None,
                  perc=((16, 84), (2.5, 97.5))):
    """Fit one record with ``spec`` and return a ``RetrievalResult``.

    Least-squares is the default; the MCMC path arrives in Stage 3.
    """
    from ioptics import evaluate

    method = fit_method or spec.fit_method
    if method == 'chisq':
        models, rt_dict, ans, cov = fit_chisq(spec, record)
        return evaluate.from_chisq(spec, record, models, rt_dict, ans, cov,
                                   perc=perc)
    if method == 'mcmc':
        raise NotImplementedError("the MCMC path lands in Stage 3")
    raise ValueError(f"unknown fit_method {method!r} (expected 'chisq'|'mcmc')")

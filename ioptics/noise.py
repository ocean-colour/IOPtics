"""Rrs-uncertainty attachment for a prepared record.

Builds the ``varRrs`` variance vector that the BING fitters consume as
inverse-variance weights, and (for synthetic datasets) optionally draws a
single noise realization that perturbs the otherwise-noiseless ``Rrs`` so the
fit sees a realistic observation. The chosen model is recorded as a provenance
tag (``noise_model``) and the RNG seed of any perturbation is recorded
(``noise_seed``) so a sweep is reproducible.

Three noise models (design doc §"Noise attachment"):

- ``'pace'``   — PACE per-band ``Rrs`` uncertainty via
  ``ocpy.satellites.pace.gen_noise_vector``, evaluated **on the native grid**
  (no resampling). Used both as the fit weight and to draw the perturbation.
  The L23 first pass uses this with ``add_noise=True``.
- ``'insitu'`` — the dataset's own measured ``Rrs`` errors (``varRrs = err**2``);
  no synthetic perturbation (the in-situ ``Rrs`` is already a real observation).
- ``'pct:X'``  — a flat fractional error, ``varRrs = (X * Rrs)**2`` (e.g.
  ``'pct:0.05'`` for 5%).

With :mod:`ioptics.datasets`, this is one of the only two modules that import
ocpy; nothing downstream of :mod:`ioptics.prep` imports it.
"""

from __future__ import annotations

import numpy as np


def _parse_pct(model):
    """Parse a ``'pct:X'`` model string into the fraction ``X`` (float)."""
    try:
        frac = float(model.split(':', 1)[1])
    except (IndexError, ValueError):
        raise ValueError(
            f"noise model {model!r} must look like 'pct:0.05'")
    if frac <= 0:
        raise ValueError(f"noise model {model!r}: fraction must be > 0")
    return frac


def attach_noise(wave, Rrs, model='pace', *, add_noise=True, seed=None,
                 Rrs_err=None, floor_frac=None):
    """Build ``varRrs`` for a record and optionally perturb ``Rrs``.

    Parameters
    ----------
    wave : numpy.ndarray
        Native wavelength grid (nm).
    Rrs : numpy.ndarray
        Un-perturbed remote-sensing reflectance on ``wave``.
    model : str, optional
        Noise model: ``'pace'`` (default), ``'insitu'``, or ``'pct:X'``.
    add_noise : bool, optional
        If ``True`` (default), draw a single realization
        ``Rrs_out = Rrs + N(0, sqrt(varRrs))`` using ``seed``; otherwise
        ``Rrs_out`` equals the input.
    seed : int or None, optional
        RNG seed for the perturbation (recorded for reproducibility). Ignored
        when ``add_noise`` is ``False``.
    Rrs_err : numpy.ndarray or None, optional
        Measured ``Rrs`` 1-sigma errors on ``wave`` — required for
        ``model='insitu'``. Non-finite entries mean *no measured error at that
        band*, which only ``floor_frac`` can make usable.
    floor_frac : float or None, optional
        Fractional **error floor**: raise each ``sigma`` to at least
        ``floor_frac * |Rrs|``, and supply that value outright where no error
        was measured. ``None`` (default) leaves the variance as the model gave
        it. An inflated-noise result — it makes chi-squared interpretable
        without improving any fit, so it is stamped on ``tag``.

    Returns
    -------
    varRrs : numpy.ndarray
        Variance (sigma^2) on ``wave``.
    Rrs_out : numpy.ndarray
        The (possibly perturbed) ``Rrs`` the fit sees.
    Rrs_clean : numpy.ndarray
        The un-perturbed input ``Rrs`` (a copy).
    tag : str
        Provenance tag for the noise model (``'pace'`` / ``'insitu'`` /
        ``'pct:X'``) — assigned to ``PreparedRecord.noise_model``. With
        ``floor_frac`` it gains ``'+floor:X'``, or ``'+imputed:X'`` when the
        weights come entirely from the floor because nothing was measured.
    seed_used : int or None
        The seed actually used (``None`` if unperturbed) — assigned to
        ``PreparedRecord.noise_seed``.
    """
    wave = np.asarray(wave, dtype=float)
    Rrs = np.asarray(Rrs, dtype=float)
    Rrs_clean = Rrs.copy()

    # --- variance vector + provenance tag, per model ---
    if model == 'pace':
        from ocpy.satellites import pace
        sigma = np.asarray(pace.gen_noise_vector(wave), dtype=float)
        varRrs = sigma ** 2
        tag = 'pace'
    elif model == 'insitu':
        if Rrs_err is None:
            raise ValueError(
                "model='insitu' requires Rrs_err (the dataset's measured "
                "Rrs uncertainty)")
        varRrs = np.asarray(Rrs_err, dtype=float) ** 2
        tag = 'insitu'
    elif model.startswith('pct:'):
        frac = _parse_pct(model)
        varRrs = (frac * Rrs) ** 2
        tag = model
    else:
        raise ValueError(
            f"unknown noise model {model!r} "
            "(expected 'pace', 'insitu', or 'pct:X')")

    # --- optional error floor (inflated noise) ---
    # sigma = max(sigma_measured, floor_frac * |Rrs|), elementwise: the same
    # max-of-measured-or-fractional idea as the PANGAEA percentage fallback,
    # but applied *on top of* a measured error rather than instead of it. The
    # tag gains a '+floor:X' suffix so a result is never mistaken for one
    # weighted by the measured error alone -- an inflated-noise result must
    # announce itself, because the floor makes chi-squared interpretable
    # without improving the fit.
    #
    # Bands whose measured error is **missing** (non-finite) take the floor
    # outright. This is not a detail: 70% of GLORIA spectra carry no measured
    # ``Rrs`` uncertainty at any band, and a plain ``np.maximum`` propagates
    # the NaN, so those records reach the fitter with all-NaN weights and the
    # bounded least-squares solver refuses to start ("Residuals are not finite
    # in the initial point") -- a data gap that reads as a convergence
    # failure. Where **no** band had a measured error the weights are wholly
    # imputed rather than floored, and the tag says so (``+imputed:X``): a
    # chi-squared against an assumed 5% error is a different claim from one
    # against a measured error that was floored at 5%.
    if floor_frac is not None:
        frac = float(floor_frac)
        if frac <= 0:
            raise ValueError(f'floor_frac must be > 0, got {floor_frac!r}')
        sigma_meas = np.sqrt(varRrs)
        measured = np.isfinite(sigma_meas)
        floor = frac * np.abs(Rrs_clean)
        # A band with Rrs == 0 would floor to sigma = 0 (an infinite weight),
        # so fall back there to the same fraction of the spectrum's own scale.
        scale = np.abs(Rrs_clean[np.isfinite(Rrs_clean)])
        scale = float(np.median(scale)) if scale.size else 0.0
        floor = np.where(floor > 0, floor, frac * scale)
        sigma = np.where(measured, np.maximum(sigma_meas, floor), floor)
        varRrs = sigma ** 2
        tag = f'{tag}+floor:{frac}' if measured.any() \
            else f'{tag}+imputed:{frac}'

    # --- optional single noise realization ---
    if add_noise:
        rng = np.random.default_rng(seed)
        Rrs_out = Rrs_clean + rng.normal(0.0, np.sqrt(varRrs))
        seed_used = seed
    else:
        Rrs_out = Rrs_clean.copy()
        seed_used = None

    return varRrs, Rrs_out, Rrs_clean, tag, seed_used

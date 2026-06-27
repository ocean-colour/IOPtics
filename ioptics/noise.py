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
                 Rrs_err=None):
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
        ``model='insitu'``.

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
        ``'pct:X'``) — assigned to ``PreparedRecord.noise_model``.
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

    # --- optional single noise realization ---
    if add_noise:
        rng = np.random.default_rng(seed)
        Rrs_out = Rrs_clean + rng.normal(0.0, np.sqrt(varRrs))
        seed_used = seed
    else:
        Rrs_out = Rrs_clean.copy()
        seed_used = None

    return varRrs, Rrs_out, Rrs_clean, tag, seed_used

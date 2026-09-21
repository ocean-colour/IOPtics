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

import warnings

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


#: Provenance-tag marker for wholly imputed fit weights.
#:
#: :func:`attach_noise` writes ``'<model>+imputed:<frac>'`` when ``impute_frac``
#: had to supply the uncertainty for *every* band, because the dataset quoted
#: none. It is a substring test rather than an equality test so it holds
#: whatever fraction was used.
IMPUTED_TAG = '+imputed:'


class ImputedUncertaintyWarning(UserWarning):
    """Some records' fit weights were **invented**, not measured.

    Anything derived from such a fit — chi-squared above all — is a statement
    about the assumed error as much as about the model, so it warns rather than
    defaulting quietly. Raised **once per batch** by
    :func:`ioptics.prep.prep_dataset` (and so once per sweep), with the count of
    affected records: a per-record warning on a 100-spectrum GLORIA sweep fires
    ~70 identical times, and the count is what a reader can act on anyway. A
    single :func:`ioptics.prep.prep_one` does not warn — its
    ``PreparedRecord.noise_model`` tag carries the fact (see
    :data:`IMPUTED_TAG`), as does every persisted results row.
    """


def is_imputed(noise_model):
    """Whether a ``noise_model`` provenance tag marks wholly imputed weights."""
    return IMPUTED_TAG in str(noise_model)


def error_floor(Rrs, frac):
    """The two-part error floor, ``frac * max(|Rrs|, median|Rrs|)``.

    The single implementation of the floor, shared by :func:`attach_noise` and
    by the analysis scripts under ``reports/scripts`` — two copies of it is how
    the two drifted apart in the first place.

    - The **fractional** part, ``frac * |Rrs|``, is the per-band relative error.
    - The **absolute** part, ``frac * median|Rrs|``, is derived from the *other*
      bands of the same spectrum. A purely fractional floor collapses to ~0
      wherever ``Rrs`` does, handing a dim or negative band an enormous weight;
      real instrument noise is roughly constant in absolute terms, so the
      spectrum's own scale is the right stand-in. It de-weights the dim red
      tail on purpose: that makes chi-squared honest about which bands carry
      information, not the misfit smaller.

    Parameters
    ----------
    Rrs : numpy.ndarray
        Reflectance spectrum (the un-perturbed one, where that distinction
        applies). Non-finite entries are ignored in the median.
    frac : float
        Fraction to apply.

    Returns
    -------
    numpy.ndarray
        The 1-sigma floor per band, same shape as ``Rrs``.
    """
    Rrs = np.abs(np.asarray(Rrs, dtype=float))
    finite = Rrs[np.isfinite(Rrs)]
    scale = float(np.median(finite)) if finite.size else 0.0
    return float(frac) * np.maximum(Rrs, scale)


def attach_noise(wave, Rrs, model='pace', *, add_noise=True, seed=None,
                 Rrs_err=None, floor_frac=None, impute_frac=None):
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
        Fractional **error floor** for bands that *were* measured: raise each
        ``sigma`` to at least ``floor_frac * max(|Rrs|, median|Rrs|)``.
        ``None`` (default) leaves the variance as the model gave it. An
        inflated-noise result — it makes chi-squared interpretable without
        improving any fit, so it is stamped on ``tag``.
    impute_frac : float, False or None, optional
        Fraction used where **nothing** was measured. Defaults to
        ``floor_frac`` when omitted; set it larger to say that an invented
        uncertainty deserves less confidence than a measured one that was
        merely floored. Imputing every band stamps :data:`IMPUTED_TAG` on
        ``tag``; the warning about it is raised once per batch, by
        :func:`ioptics.prep.prep_dataset`. ``False`` (or ``0``) **imputes
        nothing**: un-measured bands keep their non-finite variance, so the
        record announces the data gap instead of hiding it behind an assumed
        error — measured bands are still floored.

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
    # sigma = max(sigma_measured, floor), elementwise: the same
    # max-of-measured-or-fractional idea as the PANGAEA percentage fallback,
    # but applied *on top of* a measured error rather than instead of it. The
    # tag gains a '+floor:X' suffix so a result is never mistaken for one
    # weighted by the measured error alone -- an inflated-noise result must
    # announce itself, because the floor makes chi-squared interpretable
    # without improving the fit.
    #
    # The floor has two parts, ``frac * max(|Rrs|, median|Rrs|)``:
    #
    # * **fractional** -- ``frac * |Rrs|``, the per-band relative error.
    # * **absolute** -- ``frac * median|Rrs|``, a floor derived from the
    #   *other* bands of the same spectrum. A purely fractional floor
    #   collapses to ~0 wherever ``Rrs`` does, handing a dim or negative band
    #   an enormous weight: on GLORIA's GID_5691 the 35 bands with
    #   ``Rrs <= 0`` carried **78% of the entire chi-squared** between them.
    #   Real instrument noise is roughly constant in absolute terms, so the
    #   spectrum's own scale is the right stand-in. Note the consequence:
    #   this de-weights the dim red tail, which is where turbid diagnostics
    #   live -- it makes chi-squared honest about which bands carry
    #   information, not the misfit smaller.
    #
    # Bands whose measured error is **missing** (non-finite) take the floor
    # outright, at ``impute_frac``. This is not a detail: 70% of GLORIA
    # spectra carry no measured ``Rrs`` uncertainty at any band, and a plain
    # ``np.maximum`` propagates the NaN, so those records reach the fitter
    # with all-NaN weights and the bounded least-squares solver refuses to
    # start ("Residuals are not finite in the initial point") -- a data gap
    # that reads as a convergence failure. Where **no** band had a measured
    # error the weights are wholly imputed rather than floored and the tag says
    # so (``+imputed:X``): a chi-squared against an assumed error is a
    # different claim from one against a measured error that was floored.
    # ``prep_dataset`` turns those tags into one warning per batch.
    #
    # ``impute_frac=False`` declines that imputation: the un-measured bands keep
    # their non-finite variance and the record cannot be fit at all, which is
    # the honest outcome when the point is to study the measured errors alone.
    # Floor and imputation are separately switchable on purpose -- flooring the
    # measured bands while inventing nothing is a legitimate request.
    if floor_frac is not None:
        frac = float(floor_frac)
        if frac <= 0:
            raise ValueError(f'floor_frac must be > 0, got {floor_frac!r}')
        if impute_frac is None:
            imp = frac
        elif impute_frac:
            imp = float(impute_frac)
            if imp <= 0:
                raise ValueError(f'impute_frac must be > 0, got {impute_frac!r}')
        else:
            imp = None                      # explicitly: impute nothing

        sigma_meas = np.sqrt(varRrs)
        measured = np.isfinite(sigma_meas)
        floored = np.maximum(sigma_meas, error_floor(Rrs_clean, frac))
        # Where nothing was measured: the imputed floor, or the original
        # non-finite sigma when imputation was declined.
        sigma = np.where(measured, floored,
                         sigma_meas if imp is None
                         else error_floor(Rrs_clean, imp))
        varRrs = sigma ** 2
        if measured.any():
            tag = f'{tag}+floor:{frac}'
        elif imp is not None:
            tag = f'{tag}{IMPUTED_TAG}{imp}'
        # else nothing was measured and nothing invented: the tag stays bare,
        # since neither the floor nor an imputed error touched this record.

    # --- optional single noise realization ---
    if add_noise:
        rng = np.random.default_rng(seed)
        Rrs_out = Rrs_clean + rng.normal(0.0, np.sqrt(varRrs))
        seed_used = seed
    else:
        Rrs_out = Rrs_clean.copy()
        seed_used = None

    return varRrs, Rrs_out, Rrs_clean, tag, seed_used

"""Core data structures that flow through the IOPtics pipeline.

This module defines the two **load-bearing contracts** every later stage
depends on, plus a small helper class:

- :class:`PreparedRecord` — one observation, loaded and conditioned, ready to
  fit. It is the output of :mod:`ioptics.prep` and the input to
  :mod:`ioptics.run`.
- :class:`RetrievalResult` — one algorithm's output for one observation. It is
  the output of :mod:`ioptics.evaluate` and is flattened to the long/tidy
  results tables by :mod:`ioptics.io`.
- :class:`ComponentFit` — the reconstructed value (± credible/confidence
  bounds) of a single IOP component on the fit grid; the building block of
  ``RetrievalResult.components``.

The dataclasses are kept deliberately small so that every dataset and every
algorithm flow through them unchanged (design doc §"Data flow"). They are
plain dataclasses holding numpy arrays, floats, and dicts, so they are
**picklable** and can cross a ``ProcessPoolExecutor`` boundary or be cached to
disk between sweep stages.

See ``docs/design/IOPtics_implementation.md`` §"Data preparation" and
§"Retrieval & run" for the authoritative schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

#: Allowed :class:`RetrievalResult` status values.
#:
#: - ``'ok'`` -- the fit converged and is an acceptable solution.
#: - ``'poor_fit'`` -- the optimiser returned, but the solution is not
#:   acceptable: reduced chi-squared above :data:`CHI2NU_POOR_FIT`. The
#:   parameters are recorded, so the row can be inspected, but it should
#:   not be scored as a success.
#: - ``'out_of_scope'`` -- a poor fit *explained by the regime*: the
#:   spectrum sits outside what the model family is built for (see
#:   :data:`RED_PEAK_NM`). Distinguishing this from ``'poor_fit'`` is the
#:   difference between "this model did badly here" and "no algorithm in
#:   this family should be expected to work here".
#: - ``'fit_failed'`` -- no usable parameters (the optimiser raised, or
#:   produced non-finite values).
STATUSES = ('ok', 'poor_fit', 'out_of_scope', 'fit_failed')

#: Reduced chi-squared above which a converged fit is not a solution.
#: Shared with :data:`ioptics.metrics.CHI2NU_QC_MAX` so the per-row status
#: and the aggregate ``frac_qc_fail`` metric cannot drift apart.
CHI2NU_POOR_FIT = 5.0

#: Rrs peak wavelength (nm) above which a spectrum is treated as turbid,
#: i.e. outside the open-ocean model family's regime. From the GLORIA
#: investigation: clear spectra peak near 400-505 nm and fit well, while
#: the turbid ones peak at 560-750 nm and are missed by 80-91%
#: (``reports/gloria_fits_report.md``).
RED_PEAK_NM = 560.0


@dataclass
class PreparedRecord:
    """One observation, conditioned and ready for retrieval.

    The single common form fed to every algorithm. Produced by
    :func:`ioptics.prep.prep_one` on the dataset's **native wavelength grid**
    (no resampling); it carries the observed ``Rrs`` and its variance, any
    available truth IOPs (pre-aligned onto ``wave``), and truth-free
    initialization values derived from the observed spectrum.

    Parameters
    ----------
    dataset : str
        Dataset name: ``'L23'`` | ``'PANGAEA'`` | ``'GLORIA'``.
    obs_id : int or str
        Observation identifier: an L23 row index, or a PANGAEA/GLORIA global
        ``ID``.
    wave : numpy.ndarray
        Native wavelength grid (nm), ascending. This is the fit grid.
    Rrs : numpy.ndarray
        Observed remote-sensing reflectance [sr^-1] on ``wave``. For L23 this
        is the noise-perturbed spectrum; for in-situ data it is the measured
        spectrum.
    varRrs : numpy.ndarray
        Variance (sigma^2) of ``Rrs`` on ``wave`` — the inverse-variance fit
        weights.
    Rrs_clean : numpy.ndarray
        The un-perturbed ``Rrs`` (equal to ``Rrs`` when no synthetic noise was
        added; for L23 this is the noiseless Hydrolight truth spectrum).
    truth : dict
        Free-form truth dict keyed by component name. Spectral components
        (e.g. ``'a'``, ``'bb'``, ``'a_ph'``, ``'a_dg'``, ``'bb_p'``) are stored
        as ocpy ``Spectrum`` objects pre-aligned onto ``wave``; scalar
        components (e.g. ``'Chl'``, ``'Y'``, ``'Sdg'``, ``'a_cdom440'``) are
        plain floats. ``{}`` when the dataset provides no truth. Each dataset
        fills only the keys it has; metrics score on the intersection with what
        an algorithm retrieves.
    truth_interp : dict
        Maps each ``truth`` component name to a bool: ``True`` if it was
        regridded onto ``wave`` (``False`` if already native, and for all
        scalars).
    init : dict
        **Truth-free** model-init values derived from the *observed* ``Rrs``
        (e.g. ``{'Chl': ..., 'Y': ...}``), used to seed BING model internals
        and the least-squares starting guess at run time. Never sourced from
        ``truth`` so benchmark retrievals stay honest.
    noise_model : str
        Provenance tag for the noise model used:
        ``'pace'`` | ``'insitu'`` | ``'pct:0.05'``.
    noise_seed : int or None
        RNG seed used to perturb ``Rrs`` (``None`` if unperturbed).
    meta : dict, optional
        Free-form metadata (lat/lon/date/source/sensor; L23 ``X``/``Y``; water
        type / trophic bin). Defaults to an empty dict.
    """

    dataset:      str
    obs_id:       int | str
    wave:         np.ndarray
    Rrs:          np.ndarray
    varRrs:       np.ndarray
    Rrs_clean:    np.ndarray
    truth:        dict
    truth_interp: dict
    init:         dict
    noise_model:  str
    noise_seed:   int | None
    meta:         dict = field(default_factory=dict)


@dataclass
class ComponentFit:
    """Reconstructed value of one IOP component on the fit grid.

    Holds the median retrieval plus the 68% and 95% credible (MCMC) or
    confidence (least-squares covariance) bounds at each wavelength. The
    building block of :attr:`RetrievalResult.components`.

    Parameters
    ----------
    wave : numpy.ndarray
        Wavelength grid (nm) — the record's native fit grid.
    med : numpy.ndarray
        Median (point) estimate at each wavelength.
    lo68, hi68 : numpy.ndarray
        Lower/upper 68% interval bounds.
    lo95, hi95 : numpy.ndarray
        Lower/upper 95% interval bounds.
    """

    wave: np.ndarray
    med:  np.ndarray
    lo68: np.ndarray
    hi68: np.ndarray
    lo95: np.ndarray
    hi95: np.ndarray


@dataclass
class RetrievalResult:
    """One algorithm's retrieval for one observation.

    Produced by :func:`ioptics.evaluate.from_chains` /
    :func:`ioptics.evaluate.from_chisq`; flattened to the long/tidy results
    tables by :mod:`ioptics.io`. Uncertainty is a first-class output, produced
    the same way for both fit methods so intervals are comparable.

    Parameters
    ----------
    dataset : str
        Dataset name (matches the source :class:`PreparedRecord`).
    obs_id : int or str
        Observation identifier.
    algorithm : str
        Registry name of the algorithm that produced this result.
    fit_method : str
        ``'chisq'`` (least-squares) | ``'mcmc'``.
    components : dict
        Maps component name to a :class:`ComponentFit`. Includes reconstructed
        IOPs (``'a'``, ``'bb'``, ``'a_ph'``, ``'a_dg'``, ``'bb_p'``) and the
        model spectrum ``'Rrs_model'``. Defaults to an empty dict.
    params : dict
        Fitted model parameters as ``{pname: (med, sigma)}`` (e.g. ``Sdg``,
        ``beta``, ``Adg``, ``Aph``, ``Bnw``). Defaults to an empty dict.
    scalars : dict
        Derived scalars with uncertainty (e.g. ``Chl``, ``a_cdom440``).
        Defaults to an empty dict.
    stats : dict
        Fit-quality / model-selection statistics: ``chi2``, ``chi2_nu``,
        ``AIC``, ``BIC``, ``n_bands``, ``k``. Defaults to an empty dict.
    status : str
        One of :data:`STATUSES`: ``'ok'`` | ``'poor_fit'`` |
        ``'out_of_scope'`` | ``'fit_failed'``. Defaults to ``'ok'``.
        See :data:`STATUSES` for what separates the middle two.
    provenance_id : str
        Link into the sweep's ``provenance.yaml`` (provenance record +
        algorithm block). Defaults to an empty string.
    chain_file : str or None
        Path to the saved MCMC chain NPZ (``None`` for least-squares results).
    """

    dataset:    str
    obs_id:     int | str
    algorithm:  str
    fit_method: str
    components: dict = field(default_factory=dict)
    params:     dict = field(default_factory=dict)
    scalars:    dict = field(default_factory=dict)
    stats:      dict = field(default_factory=dict)
    status:     str  = 'ok'
    provenance_id: str = ''
    chain_file: str | None = None     # path to the saved MCMC chain NPZ (None for chisq)

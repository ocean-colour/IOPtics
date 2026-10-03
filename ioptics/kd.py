"""``<Kd>_1`` -- the diffuse attenuation coefficient LS2 takes as an input.

LS2 (Loisel et al. 2018) inverts ``Rrs`` together with ``<Kd>_1``, the average
attenuation coefficient of downwelling planar irradiance between the surface
and the first attenuation depth ``z1`` (where ``Ed`` has fallen to ``1/e`` of
its value just beneath the surface).  ``Kd`` is an **input** to such an
algorithm, not a truth it is scored against, so it travels on
:attr:`ioptics.records.PreparedRecord.Kd`, never through the truth dict.

For L23 it is derived from the Hydrolight depth profiles
(``Hydrolight{X}{Y}_profile.nc``), and the database contradicts itself about
``z1``: its stored ``z1_lambda`` disagrees with the e-folding depth implied by
its own ``Ed_z`` profile, by 1.77x at 700 nm and by more than 10% on 37 039 of
266 067 (scenario, wavelength) pairs at ``X=4, Y=00``.  Three definitions are
therefore offered (ls2 Q10), selected by name:

``'ln_ratio'`` (canonical)
    ``ln[Ed(0-)/Ed(z1)] / z1`` with ``z1`` the e-folding depth of ``Ed_z``
    itself, located by linear interpolation of ``ln Ed`` between grid depths.
    Computed from ``Ed_z`` alone and closest to the LS1 definition (Loisel &
    Stramski 2000).  With ``z1`` defined this way the log ratio is exactly 1,
    so the value is ``1/z1``.
``'trapz_stored_z1'``
    The depth average of ``KEd_z`` over ``[0, z1_lambda]``, using the
    database's own ``z1``: the status quo of planning prompt 1, lifted from
    ``runs/prototypes/ls2/verify_context.py``.
``'trapz_ed_z1'``
    The same trapezoid over the ``Ed``-derived ``z1``: internally consistent,
    but no longer the database's ``z1``.

Measured on ``X=4, Y=00`` (``ioptics/tests/test_kd.py`` pins it): the three
agree to better than 0.03% in the median across 400-750 nm, and to 0.3% at the
99th percentile.  The disagreement that survives is the stored-``z1``
trapezoid in the red, whose 1st percentile reaches -0.2% at 680-720 nm, and
whose worst cell is 1.5% off.  L23's ocean is vertically homogeneous, so a
depth average of ``KEd`` barely cares which ``z1`` closes it; the stored ``z1``
is wrong, but its effect on ``<Kd>_1`` is small.

One defect of the distributed data is handled rather than hidden: the
``X=2, Y=0`` profile file is missing five scenarios entirely (all-NaN rows
365, 376, 387, 398 and 409, present in the main file), so their ``<Kd>_1`` is
NaN. :data:`KNOWN_EMPTY_PROFILE_ROWS` pins them; the other eight files have
none.

Only the four variables needed are read from the 727 MB profile file, and the
derived ``(3320, 81)`` array is cached per ``(X, Y, definition)``, so a batch
reads each file once.
"""

from __future__ import annotations

import os

import numpy as np

#: The selectable ``<Kd>_1`` definitions, canonical first (ls2 Q10).
KD1_DEFINITIONS = ('ln_ratio', 'trapz_stored_z1', 'trapz_ed_z1')

#: The canonical definition.
KD1_CANONICAL = 'ln_ratio'

#: In-process cache of derived ``<Kd>_1`` arrays: ``(X, Y, definition)`` ->
#: ``(wave, kd1)``.  The profile dataset itself is never cached.
_CACHE: dict = {}


def l23_profile_path(X=4, Y=0):
    """Path of an L23 ``Hydrolight{X}{Y:02d}_profile.nc`` file.

    Resolved through ``ocpy.hydrolight.loisel23.l23_path`` so it follows the
    same ``$OS_COLOR`` convention as :class:`ioptics.datasets.L23Adapter`.

    Parameters
    ----------
    X : int
        Inelastic variant: 1 = elastic, 2 = Raman only, 4 = Raman + Chl
        fluorescence.
    Y : int
        Solar zenith angle in degrees: 0, 30 or 60.
    """
    from ocpy.hydrolight import loisel23

    return os.path.join(loisel23.l23_path, f'Hydrolight{int(X)}{int(Y):02d}_profile.nc')


def _profile_arrays(ds):
    """Pull the below-surface depth grid and the profiles into numpy.

    Returns ``(zs, ln_ed, ked, z1_stored)`` with the depth axis last:
    ``ln_ed`` and ``ked`` are ``(n_scenario, n_lambda, n_z)``.  The ``z=-1`` row
    (above the surface) is dropped, so ``zs[0] = 0`` is ``0-``.  ``z1_lambda``
    is stored transposed as ``(lambda, scenario)``; its ``-999`` fill (``z1``
    deeper than the 50 m grid) becomes NaN.
    """
    z = np.asarray(ds['z'].values, dtype=float)
    keep = z >= 0
    zs = z[keep]
    ed = np.moveaxis(np.asarray(ds['Ed_z'].values, dtype=float)[keep], 0, -1)
    ked = np.moveaxis(np.asarray(ds['KEd_z'].values, dtype=float)[keep], 0, -1)
    z1 = np.asarray(ds['z1_lambda'].values, dtype=float).T
    z1 = np.where(z1 > 0, z1, np.nan)
    with np.errstate(divide='ignore', invalid='ignore'):
        ln_ed = np.log(ed)          # Ed can reach 0 at depth in the red
    return zs, ln_ed, ked, z1


def efolding_depth(zs, ln_ed):
    """Depth at which ``Ed`` falls to ``Ed(0-)/e``, from the profile itself.

    The first grid crossing of ``ln Ed(z) = ln Ed(0-) - 1``, located by linear
    interpolation of ``ln Ed`` between the bracketing depths.

    Parameters
    ----------
    zs : numpy.ndarray
        Depths [m], ascending, ``zs[0] = 0``.
    ln_ed : numpy.ndarray
        ``ln Ed``, depth on the last axis.

    Returns
    -------
    numpy.ndarray
        ``z1`` [m], NaN where ``Ed`` never falls that far within the grid.
    """
    y = ln_ed - (ln_ed[..., :1] - 1.0)          # crosses zero at z1
    below = y <= 0
    found = below.any(axis=-1)
    k = np.argmax(below, axis=-1)
    ok = found & (k > 0)
    k = np.where(ok, k, 1)
    y0 = np.take_along_axis(y, (k - 1)[..., None], axis=-1)[..., 0]
    y1 = np.take_along_axis(y, k[..., None], axis=-1)[..., 0]
    with np.errstate(divide='ignore', invalid='ignore'):
        frac = np.where(np.isfinite(y1), y0 / (y0 - y1), 0.0)
    return np.where(ok, zs[k - 1] + (zs[k] - zs[k - 1]) * frac, np.nan)


def _trapz_to(zs, ked, z1):
    """Depth average of ``ked`` over ``[0, z1]``, vectorized.

    A trapezoid over the grid depths, with the final partial cell closed by
    linear interpolation of ``KEd`` at exactly ``z1``.  NaN where ``z1`` is
    missing, non-positive, beyond the grid, or above the first grid depth.
    """
    usable = np.isfinite(z1) & (z1 > 0) & (z1 <= zs[-1])
    zq = np.where(usable, z1, zs[1])
    j = np.clip(np.searchsorted(zs, zq), 1, zs.size - 1)    # zs[j-1] < z1 <= zs[j]
    cum = np.concatenate(
        [np.zeros(ked.shape[:-1] + (1,)),
         np.cumsum(0.5 * (ked[..., 1:] + ked[..., :-1]) * np.diff(zs), axis=-1)],
        axis=-1)
    za, zb = zs[j - 1], zs[j]
    ka = np.take_along_axis(ked, (j - 1)[..., None], axis=-1)[..., 0]
    kb = np.take_along_axis(ked, j[..., None], axis=-1)[..., 0]
    kz = ka + (kb - ka) * (zq - za) / (zb - za)
    integral = (np.take_along_axis(cum, (j - 1)[..., None], axis=-1)[..., 0]
                + 0.5 * (ka + kz) * (zq - za))
    return np.where(usable, integral / zq, np.nan)


def mean_kd_first_attenuation_depth(ds):
    """Depth-average ``KEd_z`` over the stored first attenuation depth.

    The ``'trapz_stored_z1'`` definition, lifted from
    ``runs/prototypes/ls2/verify_context.py`` (where it was a double loop)
    and vectorized; results agree to rounding.

    Parameters
    ----------
    ds : xarray.Dataset
        An opened ``Hydrolight{X}{Y}_profile.nc`` (lazily is fine).

    Returns
    -------
    numpy.ndarray
        ``<Kd>_1`` [m^-1], ``(n_scenario, n_lambda)``, NaN where undefined.
    """
    zs, _, ked, z1 = _profile_arrays(ds)
    return _trapz_to(zs, ked, z1)


def kd1_from_profile(ds, definition=KD1_CANONICAL):
    """``<Kd>_1`` for every scenario and wavelength of an L23 profile file.

    Parameters
    ----------
    ds : xarray.Dataset
        An opened ``Hydrolight{X}{Y}_profile.nc``.
    definition : str, optional
        One of :data:`KD1_DEFINITIONS`; default :data:`KD1_CANONICAL`.

    Returns
    -------
    numpy.ndarray
        ``<Kd>_1`` [m^-1], ``(n_scenario, n_lambda)``, NaN where undefined
        (chiefly very clear water in the blue, where ``z1`` is deeper than the
        50 m grid: about 1% of pairs).
    """
    if definition not in KD1_DEFINITIONS:
        raise ValueError(f'unknown <Kd>_1 definition {definition!r}; '
                         f'choose from {KD1_DEFINITIONS}')
    zs, ln_ed, ked, z1_stored = _profile_arrays(ds)
    if definition == 'trapz_stored_z1':
        return _trapz_to(zs, ked, z1_stored)
    z1 = efolding_depth(zs, ln_ed)
    if definition == 'trapz_ed_z1':
        return _trapz_to(zs, ked, z1)
    # 'ln_ratio': ln[Ed(0-)/Ed(z1)] / z1, with Ed(z1) interpolated in ln Ed on
    # the same grid that located z1, so the ratio is e and the value 1/z1.
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(np.isfinite(z1) & (z1 > 0), 1.0 / z1, np.nan)


def load_l23_kd1(X=4, Y=0, definition=KD1_CANONICAL, *, check_rows=True):
    """``<Kd>_1`` for an L23 ``(X, Y)`` realization, cached.

    Reads only ``z``, ``Lambda``, ``Ed_z``, ``KEd_z`` and ``z1_lambda`` (plus
    ``IOP_Scenario``/``Rrs`` for the row check) from the profile file, and
    caches the derived array per ``(X, Y, definition)``.

    Parameters
    ----------
    X : int
        Inelastic variant (1, 2 or 4).
    Y : int
        Solar zenith angle in degrees (0, 30 or 60).
    definition : str, optional
        One of :data:`KD1_DEFINITIONS`.
    check_rows : bool, optional
        Verify that the profile file's scenarios, ``Rrs`` and wavelength grid
        are the main ``Hydrolight{X}{Y}.nc``'s, row for row, so a profile row
        index *is* an L23 ``obs_id``.  Default True; done once per
        ``(X, Y)``.

    Returns
    -------
    wave : numpy.ndarray
        ``(81,)`` wavelengths [nm].
    kd1 : numpy.ndarray
        ``(3320, 81)`` ``<Kd>_1`` [m^-1].
    """
    key = (int(X), int(Y), definition)
    if key in _CACHE:
        return _CACHE[key]
    import xarray as xr

    with xr.open_dataset(l23_profile_path(X, Y), engine='h5netcdf') as ds:
        wave = np.asarray(ds['Lambda'].values, dtype=float)
        if check_rows:
            _check_rows(ds, X, Y, wave)
        kd1 = kd1_from_profile(ds, definition)
    _CACHE[key] = (wave, kd1)
    return _CACHE[key]


#: Scenarios entirely missing (all NaN) from a profile file although the main
#: file has them -- a defect of the distributed L23 data, found by ls2 task 5.
#: Their ``<Kd>_1`` is NaN. Pinned so a re-download that fixes or changes it is
#: noticed (``test_kd.py``).
KNOWN_EMPTY_PROFILE_ROWS = {(2, 0): (365, 376, 387, 398, 409)}


def empty_profile_rows(ds):
    """Scenario indices whose profile ``Rrs`` is NaN at every wavelength."""
    rrs = np.asarray(ds['Rrs'].values, dtype=float)
    return tuple(int(i) for i in np.flatnonzero(np.all(np.isnan(rrs), axis=1)))


def _check_rows(ds, X, Y, wave):
    """Raise unless the profile file is row-aligned with the main L23 file.

    Compares scenario ids, the wavelength grid, and ``Rrs`` on every row the
    profile file actually populates. A row that is entirely NaN in the profile
    file is a hole, not a misalignment (``X=2, Y=0`` has five: see
    :data:`KNOWN_EMPTY_PROFILE_ROWS`); any *other* difference raises.
    """
    import xarray as xr
    from ocpy.hydrolight import loisel23

    main = os.path.join(loisel23.l23_path, f'Hydrolight{int(X)}{int(Y):02d}.nc')
    with xr.open_dataset(main, engine='h5netcdf') as m:
        rrs_p = np.asarray(ds['Rrs'].values)
        rrs_m = np.asarray(m['Rrs'].values)
        filled = ~np.all(np.isnan(rrs_p), axis=1)
        same = (np.array_equal(ds['IOP_Scenario'].values, m['IOP_Scenario'].values)
                and np.array_equal(wave, np.asarray(m['Lambda'].values, float))
                and np.array_equal(rrs_p[filled], rrs_m[filled]))
    if not same:
        raise ValueError(f'L23 X={X} Y={Y}: the profile file is not row-aligned '
                         'with the main file, so its <Kd>_1 rows cannot be '
                         'matched to obs_ids')


#: Wavelength [nm] at which :func:`load_l23_muw_effective` reads the light
#: field: the longest L23 band, where water absorbs ~2.85 m^-1 and in-water
#: scattering barely redistributes the downwelling light.
MUW_EFFECTIVE_WAVE = 750.0


def load_l23_muw_effective(X=4, Y=0):
    """An *effective* ``muw`` per L23 scenario, from the RT's own light field.

    LS2's tables are entered at ``muw``, the cosine of the refracted direct
    solar beam (Snell). Hydrolight's sky is not a direct beam alone: L23's
    ``a/<Kd>_1`` tends to 0.9694 as ``Rrs -> 0`` at ``theta_s = 0``, not 1
    (ls2 Q9). The diagnostic rung therefore enters the tables at the mean
    cosine of the downwelling light just beneath the surface, ``md_z`` at
    ``z = 0-``, taken at :data:`MUW_EFFECTIVE_WAVE`. There, in-water scattering
    contributes almost nothing, so the value describes the illumination
    entering the water and not the diffusion LS2's tables already model
    through ``Rrs``. A cosine averaged over the first attenuation depth, or
    taken in the blue, would count that scattering twice.

    Measured (X=4): 0.9654, 0.9016 and 0.7595 at ``theta_s`` = 0, 30 and 60
    degrees, against Snell's 1, 0.9278 and 0.7631. The values are nearly
    scenario-independent (1st-99th percentile span below 0.001), as an
    illumination property should be.

    Returns
    -------
    numpy.ndarray
        ``(n_scenario,)`` effective ``muw``; NaN for a scenario missing from
        the profile file (:data:`KNOWN_EMPTY_PROFILE_ROWS`).
    """
    key = ('muw_eff', int(X), int(Y))
    if key in _CACHE:
        return _CACHE[key]
    import xarray as xr

    with xr.open_dataset(l23_profile_path(X, Y), engine='h5netcdf') as ds:
        z = np.asarray(ds['z'].values, dtype=float)
        lam = np.asarray(ds['Lambda'].values, dtype=float)
        j = int(np.argmin(np.abs(lam - MUW_EFFECTIVE_WAVE)))
        i0 = int(np.flatnonzero(z == 0.0)[0])
        md0 = np.asarray(ds['md_z'].values[i0, :, j], dtype=float)
    _CACHE[key] = md0
    return md0


def clear_cache():
    """Drop every cached ``<Kd>_1`` array."""
    _CACHE.clear()

"""Regenerate every number quoted in the LS2 Context section.

Planning prompt 1 of ``claude_prompts/LS2/ls2_prompts.md`` asks for the Context
to be *verified in situ* rather than trusted.  This script is the reproducible
half of that answer: it recomputes, from the data and the code themselves, each
figure that the corrected Context and its 2026-09-21 log entry quote.  Nothing
here writes to a repository; it only prints.

Four independent checks, selectable by name::

    python verify_context.py lut      # LS2_LUT.npz keys, grids, kappa table
    python verify_context.py raman    # the stale-corner defect in LS2_main
    python verify_context.py kd1      # <Kd>_1 over L23 X=4 (the feasibility numbers)
    python verify_context.py z1       # z1_lambda against the Ed_z e-folding depth
    python verify_context.py all      # all four (default)

``kd1`` and ``z1`` need the L23 profile files (~700 MB each) and take a couple
of minutes; ``lut`` and ``raman`` need only the ``ocpy`` package data and run in
seconds.

Run it with the ``ocean14`` interpreter directly --- ``conda activate`` fails
non-interactively::

    /Users/xavier/miniforge3/envs/ocean14/bin/python verify_context.py all
"""

from __future__ import annotations

import sys
import warnings

import numpy as np

# Reference wavelengths the Context quotes <Kd>_1 medians at.
KD1_WAVES = (440., 490., 555., 670.)

# The paper's solar-zenith grid (degrees) and the water refractive index used
# to turn it into mu_w (Loisel et al. 2018, Table 1, Step 1).
SZA_GRID = np.arange(0., 71., 10.)
N_WATER = 1.34


def l23_profile_path(X: int = 4, Y: str = '00') -> str:
    """Return the path of an L23 ``Hydrolight{X}{Y}_profile.nc`` file.

    Resolved through ``ocpy`` so this script inherits the same ``$OS_COLOR``
    convention as the dataset adapters.

    Parameters
    ----------
    X : int
        Inelastic variant: 1 = elastic, 2 = Raman only, 4 = Raman + fluorescence.
    Y : str
        Two-digit solar zenith angle in degrees (``'00'``, ``'30'``, ``'60'``).
    """
    import os

    from ocpy.hydrolight import loisel23

    return os.path.join(loisel23.l23_path, f'Hydrolight{X}{Y}_profile.nc')


def mean_kd_first_attenuation_depth(ds) -> np.ndarray:
    """Depth-average ``KEd_z`` over the first attenuation depth ``z1_lambda``.

    ``<Kd>_1`` is the quantity LS2 takes as its second observable.  L23 stores a
    profile of the diffuse attenuation coefficient and, separately, the depth
    ``z1`` at which downwelling irradiance falls to 1/e of its surface value, so
    the average is a trapezoid over ``[0, z1]`` with the final partial cell
    closed by linear interpolation of ``KEd`` inside the bracketing pair.

    The ``z=-1`` row (above water) is dropped; the fill value ``-999`` in
    ``z1_lambda`` (``z1`` deeper than the 50 m grid, i.e. very clear water in the
    blue) propagates to NaN.

    Parameters
    ----------
    ds : xarray.Dataset
        An opened ``Hydrolight{X}{Y}_profile.nc``.

    Returns
    -------
    numpy.ndarray
        ``<Kd>_1`` with shape ``(n_scenario, n_lambda)``, NaN where undefined.
    """
    z = ds['z'].values.astype(float)
    keep = z >= 0
    zs = z[keep]
    # (z, scenario, lambda) -> (scenario, lambda, z)
    ked = np.moveaxis(ds['KEd_z'].values[keep].astype(float), 0, -1)
    # z1_lambda is stored transposed, as (lambda, scenario)
    z1 = ds['z1_lambda'].values.astype(float).T
    z1 = np.where(z1 > 0, z1, np.nan)

    n_s, n_l = z1.shape
    out = np.full((n_s, n_l), np.nan)
    for i in range(n_s):
        for j in range(n_l):
            zt = z1[i, j]
            if not np.isfinite(zt) or zt > zs[-1]:
                continue
            k = int(np.searchsorted(zs, zt))
            if k == 0:
                continue
            # Close the partial cell: interpolate KEd at exactly z1.
            kd_at = np.interp(zt, zs[k - 1:k + 1], ked[i, j, k - 1:k + 1])
            zz = np.concatenate([zs[:k], [zt]])
            kk = np.concatenate([ked[i, j, :k], [kd_at]])
            out[i, j] = np.trapezoid(kk, zz) / zt
    return out


def check_lut() -> None:
    """Report the shipped ``LS2_LUT.npz`` keys, grids and kappa table."""
    from ocpy.ls2 import io as ls2_io

    print('=' * 72)
    print('LUT  --  ocpy/data/LS2/LS2_LUT.npz')
    print('=' * 72)
    lut = ls2_io.load_LUT()
    print(f'container type: {type(lut).__name__}')
    for key in sorted(lut.files):
        arr = lut[key]
        print(f'  {key:<6} shape {str(arr.shape):<12} dtype {arr.dtype}')

    eta = lut['eta'].flatten()
    muw = lut['muw'].flatten()
    print(f'\neta  n={eta.size}  min={eta.min()} max={eta.max()}')
    print(f'  values: {eta.tolist()}')
    print(f'  unique steps: {sorted(set(np.round(np.diff(eta), 6).tolist()))}')
    print(f'muw  n={muw.size}  min={muw.min():.6f} max={muw.max():.6f}')
    print(f'  values: {np.round(muw, 6).tolist()}')

    expected = np.cos(np.arcsin(np.sin(np.radians(SZA_GRID)) / N_WATER))
    print('\nmuw vs cos[asin(sin(theta_s)/1.34)] for theta_s = 0,10,...,70 deg:')
    print(f'  expected: {np.round(expected, 6).tolist()}')
    print(f'  max |diff| = {np.abs(np.sort(muw) - np.sort(expected)).max():.2e}')

    kap = lut['kappa']
    lam = kap[:, 0]
    print(f'\nkappa shape {kap.shape}: lambda {lam.min():g}-{lam.max():g} nm, '
          f'steps {np.unique(np.diff(lam)).tolist()}')
    print('  columns are [lambda, c3, c2, c1, c0, (bb/a)_min, (bb/a)_max]:')
    uv = lam <= 326
    print(f'  rows with lambda <= 326 nm: c3..c1 all zero = '
          f'{np.allclose(kap[uv, 1:4], 0)}, c0 all one = {np.allclose(kap[uv, 4], 1)}')
    print(f'  (bb/a) range spans {kap[:, 5].min():.4f} to {kap[:, 6].max():.4f}')


def _a_all_corners(lut, idx_eta, idx_muw, Kd, Rrs, eta, muw):
    """Interpolate ``a`` from all four LUT corners at the given ``Rrs``.

    This is what ``LS2_main``'s Raman branch *should* do; it recomputes only the
    ``a00`` corner there.  See :func:`check_raman_corners`.
    """
    from scipy import interpolate

    def corner(i, j):
        c = lut['a'][i, j]
        return Kd / (c[0] + c[1] * Rrs + c[2] * Rrs ** 2 + c[3] * Rrs ** 3)

    grid = np.array([[corner(idx_eta, idx_muw), corner(idx_eta, idx_muw + 1)],
                     [corner(idx_eta + 1, idx_muw), corner(idx_eta + 1, idx_muw + 1)]])
    f = interpolate.RegularGridInterpolator(
        (lut['eta'][idx_eta:idx_eta + 2].flatten(),
         lut['muw'][idx_muw:idx_muw + 2].flatten()), grid)
    return f([eta, muw]).item()


def check_raman_corners() -> None:
    """Show that ``LS2_main``'s Raman branch leaves three ``a`` corners stale.

    ``ls2_main.py`` recomputes only ``a00`` after scaling ``Rrs`` by kappa --- the
    line where ``a01``, ``a10`` and ``a11`` should follow is a placeholder
    comment --- so the bilinear interpolation mixes one corrected corner with
    three pre-correction ones.  ``bb`` has all four corners and is unaffected.

    The test is against the authors' own reference vector, which the ``ocpy``
    tests ship but only check for ``bb`` at 412 nm.
    """
    import os

    import pandas as pd

    from ocpy.ls2 import io as ls2_io
    from ocpy.ls2.ls2_main import LS2_main, LS2_seek_pos

    print('=' * 72)
    print('RAMAN  --  stale corners in the a recalculation')
    print('=' * 72)
    lut = ls2_io.load_LUT()
    import ocpy
    csv = os.path.join(os.path.dirname(ocpy.__file__), 'tests', 'files',
                       'LS2_test_run.csv')
    df = pd.read_csv(csv)
    print(f'reference vector: {csv}')
    print(f'  {len(df)} rows, wavelengths {sorted(df["Input wavelength [nm]"].unique())}')

    cols = {c.strip(): c for c in df.columns}
    rows = []
    for _, r in df.iterrows():
        sza = float(r[cols['Input sza [deg]']])
        lam = float(r[cols['Input wavelength [nm]']])
        Rrs = float(r[cols['Input Rrs [1/sr]']])
        Kd = float(r[cols['Input Kd [1/m]']])
        aw = float(r[cols['Input aw [1/m]']])
        bw = float(r[cols['Input bw [1/m]']])
        bp = float(r[cols['Input bp [1/m]']])
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            got = LS2_main(sza, lam, Rrs, Kd, aw, bw, bp, lut, True)
        if got is None:
            continue
        a_port, anw_port, bb_port, bbp_port, kappa = got
        if not np.isfinite(kappa):
            continue
        # Redo the Raman branch with all four corners.
        muw = np.cos(np.arcsin(np.sin(np.radians(sza)) / N_WATER))
        eta = bw / (bp + bw)
        i_e = LS2_seek_pos(eta, lut['eta'], 'eta')
        i_m = LS2_seek_pos(muw, lut['muw'], 'muw')
        a_fix = _a_all_corners(lut, i_e, i_m, Kd, Rrs * kappa, eta, muw)
        a_ref = float(r[cols['Ouput a [1/m]']])
        rows.append((lam, a_port, a_fix, a_ref,
                     abs(a_port - a_ref) / a_ref, abs(a_fix - a_ref) / a_ref))

    arr = np.array(rows)
    print(f'\n{len(arr)} cells with a finite kappa (Raman actually applied)')
    print(f'  max relative |a_port  - a_reference| = {arr[:, 4].max():.3e}')
    print(f'  max relative |a_4corner - a_reference| = {arr[:, 5].max():.3e}')
    print('\nworst cell per wavelength (port vs reference):')
    for lam in sorted(set(arr[:, 0])):
        sub = arr[arr[:, 0] == lam]
        k = int(np.argmax(sub[:, 4]))
        print(f'  {lam:5.0f} nm  a_port {sub[k, 1]:.7f}  a_4corner {sub[k, 2]:.7f}  '
              f'a_ref {sub[k, 3]:.7f}  err_port {100 * sub[k, 4]:6.3f}%')


def check_kd1(X: int = 4, Y: str = '00') -> None:
    """Recompute the ``<Kd>_1`` feasibility numbers over an L23 corpus."""
    import xarray as xr

    path = l23_profile_path(X, Y)
    print('=' * 72)
    print(f'KD1  --  <Kd>_1 over L23 X={X} Y={Y}')
    print('=' * 72)
    print(f'file: {path}')
    ds = xr.load_dataset(path, engine='h5netcdf')
    lam = ds['Lambda'].values.astype(float)
    print(f'  scenarios {ds.sizes["IOP_Scenario"]}, bands {ds.sizes["Lambda"]} '
          f'({lam.min():g}-{lam.max():g} nm, step {np.unique(np.diff(lam)).tolist()}), '
          f'depths {ds.sizes["z"]}')

    kd1 = mean_kd_first_attenuation_depth(ds)
    fin = np.isfinite(kd1)
    print(f'\nfinite (scenario, wavelength) pairs: {fin.sum()} / {fin.size} '
          f'({100 * fin.mean():.2f}%)')
    print(f'scenarios with a complete spectrum: {fin.all(axis=1).sum()} / {kd1.shape[0]}')
    print('\nmedian <Kd>_1 [m^-1]:')
    for w in KD1_WAVES:
        j = int(np.argmin(np.abs(lam - w)))
        col = kd1[np.isfinite(kd1[:, j]), j]
        print(f'  {lam[j]:5.0f} nm  median {np.median(col):.4f}  '
              f'p5 {np.percentile(col, 5):.4f}  p95 {np.percentile(col, 95):.4f}  n {col.size}')

    missing = (~fin).sum(axis=0)
    hit = {int(l): int(n) for l, n in zip(lam, missing) if n}
    print(f'\nnon-finite pairs by wavelength: {hit}')
    print('  (these are the -999 fills of z1_lambda: z1 deeper than the 50 m grid)')


def check_z1(X: int = 4, Y: str = '00') -> None:
    """Compare ``z1_lambda`` with the e-folding depth implied by ``Ed_z``.

    ``z1_lambda`` is documented as the depth where Ed falls to 36.8% of its
    surface value, so it should equal the e-folding depth of the stored ``Ed_z``
    profile.  It does not, at the red end.  The trapezoid average of
    :func:`mean_kd_first_attenuation_depth` is nearly insensitive to this
    because L23's ocean is homogeneous, but ``1/z1`` as a shortcut for
    ``<Kd>_1`` is not.
    """
    import xarray as xr

    path = l23_profile_path(X, Y)
    print('=' * 72)
    print(f'Z1  --  z1_lambda vs the Ed_z e-folding depth (X={X} Y={Y})')
    print('=' * 72)
    ds = xr.load_dataset(path, engine='h5netcdf')
    z = ds['z'].values.astype(float)
    lam = ds['Lambda'].values.astype(float)
    keep = z >= 0
    zs = z[keep]
    lned = np.log(np.moveaxis(ds['Ed_z'].values[keep].astype(float), 0, -1))
    z1 = ds['z1_lambda'].values.astype(float).T
    z1 = np.where(z1 > 0, z1, np.nan)

    n_s, n_l = z1.shape
    efold = np.full((n_s, n_l), np.nan)
    for i in range(n_s):
        for j in range(n_l):
            y = lned[i, j] - (lned[i, j, 0] - 1.0)   # zero crossing at Ed = Ed(0-)/e
            k = np.where(y <= 0)[0]
            if k.size == 0 or k[0] == 0:
                continue
            k = k[0]
            efold[i, j] = zs[k - 1] + (zs[k] - zs[k - 1]) * y[k - 1] / (y[k - 1] - y[k])

    ok = np.isfinite(z1) & np.isfinite(efold)
    ratio = efold[ok] / z1[ok]
    print(f'z1_efold / z1_lambda over {ok.sum()} pairs: median {np.median(ratio):.4f}, '
          f'p1 {np.percentile(ratio, 1):.4f}, p99 {np.percentile(ratio, 99):.4f}')
    print(f'  pairs off by more than 10%: {(np.abs(ratio - 1) > 0.1).sum()}')

    print('\nmedian ratio by wavelength (only those off by >5%):')
    for j in range(n_l):
        m = ok[:, j]
        if not m.any():
            continue
        r = np.median(efold[m, j] / z1[m, j])
        if abs(r - 1) > 0.05:
            print(f'  {lam[j]:5.0f} nm  z1_efold/z1_lambda = {r:.3f}')

    kd1 = mean_kd_first_attenuation_depth(ds)
    inv = 1.0 / z1
    both = np.isfinite(kd1) & np.isfinite(inv)
    r = kd1[both] / inv[both]
    print(f'\n<Kd>_1 (trapezoid) / (1/z1_lambda): median {np.median(r):.4f}, '
          f'p1 {np.percentile(r, 1):.4f}, p99 {np.percentile(r, 99):.4f}')
    for w in (440., 700.):
        j = int(np.argmin(np.abs(lam - w)))
        m = both[:, j]
        print(f'  {lam[j]:5.0f} nm  median <Kd>_1 {np.median(kd1[m, j]):.4f}  '
              f'vs median 1/z1 {np.median(inv[m, j]):.4f}')


CHECKS = {'lut': check_lut, 'raman': check_raman_corners,
          'kd1': check_kd1, 'z1': check_z1}


def main(argv) -> int:
    """Run the requested checks (default: all four)."""
    which = argv[1:] if len(argv) > 1 else ['all']
    if which == ['all']:
        which = list(CHECKS)
    for name in which:
        if name not in CHECKS:
            print(f'unknown check {name!r}; choose from {list(CHECKS)} or "all"')
            return 2
        CHECKS[name]()
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

"""Regenerate LS2's rung-(i) accuracy on L23, the numbers the ladder starts from.

Rung (i) gives LS2 everything as truth -- ``<Kd>_1``, ``b_p`` -- on
noiseless Rrs, so whatever error remains is the published look-up tables'
own (ls2 Q2, Q9). Planning measured it once with LS2's scalar oracle and L23's
*own* pure water: median relative error **a +2.6%, bb +9.8%, bb_p +24%**. This
script reproduces that configuration and then the one the IOPtics driver
actually runs, so the difference between the two is on the record:

``planning``
    L23's own ``a_w``/``b_w``, a single Raman pass (``max_iter=1``, the
    authors' oracle) and the stored-z1 trapezoid ``<Kd>_1``.
``driver``
    ocpy's pure water (ls2 Q21), the Raman correction iterated to
    convergence (Q14/Q22), and the canonical ``ln_ratio`` ``<Kd>_1`` (Q10).
``effmuw``
    ``driver`` with the tables entered at L23's effective ``muw``
    (:func:`ioptics.kd.load_l23_muw_effective`) instead of Snell's -- the Q9
    diagnostic rung. If the ``a`` bias is illumination bookkeeping, it
    shrinks here with no refit.

Planning's figures were taken over **350-750 nm**; this script reproduces
them there (a +2.72%, bb +10.69%, bb_p +24.84%, 0.60% off-grid at X=4 Y=0).

Also reported: the share of cells outside the ``eta < 0.2`` envelope
(``b_p < 4 b_w``), which come back NaN with reason ``off_grid``.

Vectorized over the whole corpus with :func:`ocpy.ls2.ls2_main.ls2_invert`
(about a second per configuration), so it is not routed through
``prep``/``run``; ``ioptics/tests/test_ls2_driver.py`` checks that the driver
reproduces these numbers on individual records.

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \
        ioptics/runs/prototypes/ls2/rung_i_baseline.py [X] [Y]

(from the repository root; ``PYTHONPATH`` is needed unless ``pip install -e .``
has been run).
"""

from __future__ import annotations

import os
import sys

import numpy as np

#: The wavelength range the medians are taken over: L23's full grid, which is
#: the range planning measured on and the range the LS2 sweep sees by default.
WAVE_RANGE = (350.0, 750.0)


def load_l23(X=4, Y=0):
    """The L23 arrays rung (i) needs, as ``(n_scenario, n_lambda)``."""
    import xarray as xr
    from ocpy.hydrolight import loisel23

    path = os.path.join(loisel23.l23_path, f'Hydrolight{X}{Y:02d}.nc')
    with xr.open_dataset(path, engine='h5netcdf') as ds:
        get = {k: ds[k].values.astype(float)
               for k in ('Rrs', 'a', 'anw', 'b', 'bnw', 'bb', 'bbnw')}
        get['wave'] = ds['Lambda'].values.astype(float)
    return get


def run(config, X=4, Y=0, wave_range=WAVE_RANGE):
    """Rung (i) over the L23 corpus under ``config`` ('planning' | 'driver').

    Returns
    -------
    dict
        ``median`` relative error per component (``a``, ``a_nw``, ``bb``,
        ``bb_p``), ``frac_off_grid``, ``frac_kappa_oor``, ``n_cells`` and the
        raw ``LS2Result``.
    """
    from ocpy.ls2.io import load_LUT
    from ocpy.ls2.ls2_main import ls2_invert

    from ioptics import kd
    from ioptics.algorithms.ls2 import pure_water

    d = load_l23(X, Y)
    wave = d['wave']
    keep = (wave >= wave_range[0]) & (wave <= wave_range[1])
    if config == 'planning':
        a_w = d['a'][0] - d['anw'][0]
        b_w = d['b'][0] - d['bnw'][0]
        kd_def, max_iter = 'trapz_stored_z1', 1
    elif config in ('driver', 'effmuw'):
        a_w, b_w = pure_water(wave)
        kd_def, max_iter = 'ln_ratio', 10
    else:
        raise ValueError(f'unknown config {config!r}')
    kd1 = kd.load_l23_kd1(X, Y, kd_def)[1]
    lut = load_LUT()
    raman = X != 1
    muw = None
    if config == 'effmuw':
        muw = kd.load_l23_muw_effective(X, Y)[:, None]
    res = ls2_invert(d['Rrs'][:, keep], kd1[:, keep], a_w[keep], b_w[keep],
                     d['bnw'][:, keep], np.full(d['Rrs'].shape[0], float(Y)),
                     wave[keep], {k: np.asarray(lut[k]) for k in lut.files},
                     raman=raman, max_iter=max_iter, clip_negative=False,
                     muw=muw)
    truth = {'a': d['a'][:, keep], 'a_nw': d['anw'][:, keep],
             'bb': d['bb'][:, keep], 'bb_p': d['bbnw'][:, keep]}
    got = {'a': res.a, 'a_nw': res.anw, 'bb': res.bb, 'bb_p': res.bbp}
    med = {}
    for k in got:
        with np.errstate(divide='ignore', invalid='ignore'):
            r = got[k] / truth[k] - 1
        med[k] = float(np.nanmedian(r[np.isfinite(r)]))
    return {'median': med, 'frac_off_grid': float(res.off_grid.mean()),
            'frac_kappa_oor': float(res.kappa_out_of_range.mean()),
            'n_cells': int(res.a.size), 'result': res}


def main(argv):
    X = int(argv[1]) if len(argv) > 1 else 4
    Y = int(argv[2]) if len(argv) > 2 else 0
    print(f'LS2 rung (i) on L23 X={X} Y={Y}, {WAVE_RANGE[0]:g}-{WAVE_RANGE[1]:g} nm')
    for config in ('planning', 'driver', 'effmuw'):
        out = run(config, X, Y)
        m = out['median']
        print(f'  {config:8s}  a {100 * m["a"]:+.2f}%  a_nw {100 * m["a_nw"]:+.2f}%  '
              f'bb {100 * m["bb"]:+.2f}%  bb_p {100 * m["bb_p"]:+.2f}%  '
              f'off-grid {100 * out["frac_off_grid"]:.2f}%  '
              f'kappa-oor {100 * out["frac_kappa_oor"]:.1f}%  '
              f'({out["n_cells"]} cells)')


if __name__ == '__main__':
    main(sys.argv)

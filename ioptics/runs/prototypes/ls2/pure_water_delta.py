"""Regenerate the pure-water delta LS2 inherits (ls2 Q21, task 7).

LS2 returns ``a_nw = a - a_w`` and ``bb_p = bb - b_w/2``, and it must bring
its own pure water rather than read L23's from truth. So any difference
``delta = (ours - L23's)`` lands one-for-one in ``a_nw`` and ``bb_p``, and it
matters most where those are smallest (``a_w`` is ~99% of ``a`` at 670 nm).
This script measures it across 400-750 nm with the pure water the LS2 driver
actually uses (:func:`ioptics.algorithms.ls2.pure_water`).

L23 stores no pure water directly; it is ``a - anw`` and ``b - bnw`` (and
``bb - bbnw``, which is exactly ``b_w/2``). These are identical across all
3320 scenarios to float32 precision, so scenario 0 is used.

Run from the repository root with the ocean14 interpreter (``PYTHONPATH``
is needed unless ``pip install -e .`` has been run)::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \
        ioptics/runs/prototypes/ls2/pure_water_delta.py

Measured 2026-10-03: ``a_w`` delta 0 at every band (ocpy's IOCCG table *is*
L23's); ``b_w`` delta -0.27% (-0.275% to -0.267%) with ZHH2009 at 20 degC,
S = 35.
"""

from __future__ import annotations

import os

import numpy as np

#: Wavelength range [nm] the delta is reported over (the LS2 sweep's range).
WAVE_RANGE = (400.0, 750.0)


def l23_pure_water(X=4, Y=0):
    """L23's own ``(wave, a_w, b_w, bb_w)``, scenario 0."""
    import xarray as xr
    from ocpy.hydrolight import loisel23

    path = os.path.join(loisel23.l23_path, f'Hydrolight{X}{Y:02d}.nc')
    with xr.open_dataset(path, engine='h5netcdf') as ds:
        wave = ds['Lambda'].values.astype(float)
        a_w = (ds['a'] - ds['anw']).values[0].astype(float)
        b_w = (ds['b'] - ds['bnw']).values[0].astype(float)
        bb_w = (ds['bb'] - ds['bbnw']).values[0].astype(float)
    return wave, a_w, b_w, bb_w


def delta(X=4, Y=0, wave_range=WAVE_RANGE):
    """Relative and absolute ``(ours - L23)`` for ``a_w``, ``b_w`` and ``bb_w``.

    Returns
    -------
    dict
        ``wave`` plus, per quantity, ``rel`` and ``abs`` arrays over
        ``wave_range`` and a ``summary`` of median/min/max relative delta.
    """
    from ioptics.algorithms.ls2 import pure_water

    wave, a_w, b_w, bb_w = l23_pure_water(X, Y)
    keep = (wave >= wave_range[0]) & (wave <= wave_range[1])
    ours_a, ours_b = pure_water(wave)
    out = {'wave': wave[keep]}
    for name, ours, theirs in (('a_w', ours_a, a_w), ('b_w', ours_b, b_w),
                               ('bb_w', ours_b / 2, bb_w)):
        rel = (ours / theirs - 1)[keep]
        out[name] = {'rel': rel, 'abs': (ours - theirs)[keep],
                     'summary': {'median': float(np.median(rel)),
                                 'min': float(rel.min()),
                                 'max': float(rel.max())}}
    return out


def main():
    d = delta()
    print(f'pure-water delta, ocpy vs L23, {WAVE_RANGE[0]:g}-{WAVE_RANGE[1]:g} nm')
    for name in ('a_w', 'b_w', 'bb_w'):
        s = d[name]['summary']
        print(f'  {name:5s} median {100 * s["median"]:+.3f}%  '
              f'min {100 * s["min"]:+.3f}%  max {100 * s["max"]:+.3f}%')
    print('  per band (a_w abs, b_w rel):')
    for w in (400, 443, 490, 555, 670, 700, 750):
        j = int(np.argmin(np.abs(d['wave'] - w)))
        print(f'    {d["wave"][j]:5.0f} nm  a_w {d["a_w"]["abs"][j]:+.2e} m^-1  '
              f'b_w {100 * d["b_w"]["rel"][j]:+.3f}%')


if __name__ == '__main__':
    main()

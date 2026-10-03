"""The LS2 driver: one record through ocpy's ``ls2_invert``, rung by rung.

LS2 (Loisel et al. 2018) is a direct algorithm: closed-form ``a`` and ``bb``
from ``Rrs``, ``<Kd>_1``, ``b_p`` and the solar zenith angle, through
published look-up tables. The physics lives upstream in
:func:`ocpy.ls2.ls2_main.ls2_invert` (ls2 Q14); this module only assembles a
:class:`~ioptics.algorithms.spec.DirectSpec`'s inputs for one
:class:`~ioptics.records.PreparedRecord` and translates ocpy's flags into the
per-cell NaN reasons of :data:`ioptics.records.NAN_REASONS`. It is the
``'ls2'`` entry of :data:`ioptics.run.DIRECT_DRIVER_MODULES`.

The inputs, one at a time, which is what makes the ladder a ladder (ls2 Q2):

``theta_s``
    :func:`ioptics.run.resolve_theta_s`, spec-independent and correct for
    every dataset. ``muw`` is its refracted cosine (``muw_mode='snell'``) or,
    for the Q9 diagnostic rung, an effective cosine from L23's own light
    field (``'effective'``, :func:`ioptics.kd.load_l23_muw_effective`).
``Kd``
    ``kd_source='record'``: the record's own ``Kd`` -- L23's ``<Kd>_1``
    (prep with ``dataset_opts: {L23: {kd1: ln_ratio}}``) or PANGAEA's measured
    ``kd``, used **only on the bands where it was measured** (ls2 Q32; the
    others come back NaN with reason ``kd_missing``). ``'nn:<network>'``: one
    of ocpy's Kd networks (:mod:`ocpy.ls2.kd_nn`) applied to the record's
    observed Rrs, linearly interpolated onto the network's bands. An optional
    multiplicative Kd noise -- one draw per spectrum, fully correlated across
    bands -- is the Q15/Q33 sensitivity ladder (5, 10, 20%).
``b_p``
    ``bp_source='truth'``: the record's truth ``b_p`` (rung i, "nobody could
    reach this from orbit"). ``'oc4v4'``: OC4v4 chlorophyll from the observed
    Rrs, then :func:`ocpy.iop.scattering.bp_from_chla` (rungs ii, iii).
pure water
    **Always ocpy's, never the record's truth** (ls2 Q21): the IOCCG ``a_w``
    table (:func:`ocpy.water.absorption.a_water`) and Zhang, Hu & He (2009)
    ``b_w`` at :data:`PURE_WATER_TC` / :data:`PURE_WATER_S`
    (:func:`ocpy.water.scattering.betasw_ZHH2009`). Against L23's own pure
    water this differs by 0 in ``a_w`` and by -0.27% in ``b_w`` over 400-750 nm
    -- the delta that ``runs/prototypes/ls2/pure_water_delta.py`` regenerates
    and the ladder page reports, since it biases ``a_nw``/``bb_p`` directly.

The Raman correction iterates to ``|d(bb/a)|/(bb/a) < spec.tol`` with a cap
of ``spec.max_iter`` (ls2 Q14/Q22), and ``spec.raman`` turns it off for an
elastic (L23 ``X=1``) sweep (ls2 Q4). Negative outputs are returned as they
are and flagged ``negative``, never clipped, because a benchmark needs to see
the sign of the failure.
"""

from __future__ import annotations

import functools
import zlib

import numpy as np

#: Temperature [degC] and salinity [PSU] of the pure seawater whose
#: scattering LS2 subtracts. With these, ZHH2009 matches L23's own ``b_w`` to
#: -0.27% across 400-750 nm (``pure_water_delta.py``).
PURE_WATER_TC = 20.0
PURE_WATER_S = 35.0

#: ``a_w`` table: ocpy's IOCCG (2018) compilation, identical to L23's ``a_w``
#: at every band from 400 to 750 nm. ocpy's default GSFC table is 44% higher at
#: 400 nm.
PURE_WATER_AW_TABLE = 'IOCCG'


@functools.lru_cache(maxsize=1)
def _lut():
    """The LS2 look-up tables, materialised once per process."""
    from ocpy.ls2.io import load_LUT

    npz = load_LUT()
    return {key: np.asarray(npz[key]) for key in npz.files}


def pure_water(wave):
    """Pure-seawater ``(a_w, b_w)`` [m^-1] on ``wave``, from ocpy (ls2 Q21).

    Parameters
    ----------
    wave : array_like
        Wavelengths [nm].

    Returns
    -------
    a_w, b_w : numpy.ndarray
        Absorption and *total* scattering; LS2 subtracts ``b_w / 2`` from
        ``bb``.
    """
    from ocpy.water.absorption import a_water
    from ocpy.water.scattering import betasw_ZHH2009

    wave = np.asarray(wave, dtype=float)
    a_w = np.asarray(a_water(wave, data=PURE_WATER_AW_TABLE), dtype=float)
    b_w = np.ravel(betasw_ZHH2009(wave, PURE_WATER_TC, 90.0, PURE_WATER_S)[2])
    return a_w, b_w


def _rng(spec, record):
    """A per-(algorithm, record) generator for the Kd-noise rung.

    Seeded from the record's own noise seed, its id and the algorithm name, so
    the draw is reproducible and independent of run order or pool layout.
    """
    key = f'{spec.name}|{record.dataset}|{record.obs_id}|{record.noise_seed}'
    return np.random.default_rng(zlib.crc32(key.encode('utf-8')))


def _kd(spec, record, theta_s):
    """``Kd`` on the record grid, plus a mask of the bands where it is missing."""
    wave = np.asarray(record.wave, dtype=float)
    if spec.kd_source == 'record':
        if record.Kd is None:
            raise ValueError(
                f'{spec.name}: kd_source="record" but {record.dataset}/'
                f'{record.obs_id} carries no Kd. For L23 prep with the kd1 '
                'load option, e.g. dataset_opts: {L23: {kd1: ln_ratio}}')
        kd = np.asarray(record.Kd, dtype=float).copy()
        on_band = (record.meta or {}).get('Kd_on_band')
        if on_band is not None:
            # ls2 Q32: only measured Kd, never one interpolated between bands
            kd = np.where(np.asarray(on_band, dtype=bool), kd, np.nan)
    else:
        from ocpy.ls2 import kd_nn

        network = spec.kd_source.split(':', 1)[1]
        bands = np.asarray(kd_nn.load_network(network).bands, dtype=float)
        if bands.min() < wave.min() or bands.max() > wave.max():
            kd = np.full(wave.shape, np.nan)       # cannot feed the network
        else:
            rrs_bands = np.interp(bands, wave, np.asarray(record.Rrs, float))
            kd = kd_nn.kd_nn(rrs_bands, theta_s, wave, network)[0]
    if spec.kd_noise:
        # One draw per spectrum (ls2 Q33): a Kd retrieval's error is a bad
        # spectrum, not independent bad bands, which would average down.
        kd = kd * (1.0 + spec.kd_noise * _rng(spec, record).standard_normal())
    return kd, ~np.isfinite(kd) | (kd <= 0)


def _bp(spec, record):
    """``b_p`` on the record grid, plus a mask of the bands where it is missing.

    Returns ``(b_p, missing, scalars)``; ``scalars`` carries the OC4v4
    chlorophyll when that side chain ran.
    """
    wave = np.asarray(record.wave, dtype=float)
    scalars = {}
    if spec.bp_source == 'truth':
        val = record.truth.get('b_p')
        if val is None:
            raise ValueError(f'{spec.name}: bp_source="truth" but '
                             f'{record.dataset}/{record.obs_id} has no b_p truth')
        bp = np.asarray(getattr(val, 'values', val), dtype=float)
    else:
        from ocpy.chl.band_ratios import oc4v4
        from ocpy.iop.scattering import bp_from_chla

        try:
            chl = float(oc4v4(wave, np.asarray(record.Rrs, dtype=float)))
        except ValueError:                         # an OC4 band is missing
            chl = np.nan
        bp = np.asarray(bp_from_chla(wave, chl), dtype=float)
        scalars['Chl_oc4v4'] = (chl, np.nan)
    return bp, ~np.isfinite(bp) | (bp <= 0), scalars


def _muw(spec, record):
    """The effective ``muw`` for the diagnostic rung, or ``None`` for Snell."""
    if spec.muw_mode == 'snell':
        return None
    from ioptics import kd as kd_mod

    if not str(record.dataset).upper().startswith('L23'):
        raise ValueError(f'{spec.name}: muw_mode="effective" needs the L23 '
                         'light field; it is a diagnostic for L23 only')
    meta = record.meta or {}
    muw = kd_mod.load_l23_muw_effective(meta.get('X', 1), meta.get('Y', 0))
    return float(muw[int(record.obs_id)])


def inputs(spec, record):
    """Every input LS2 will see for ``record`` under ``spec``.

    Separate from :func:`invert` so a test can check that two rungs differ
    only in the input they are meant to (ls2 Q2).

    Returns
    -------
    dict
        ``wave``, ``Rrs``, ``theta_s``, ``muw`` (``None`` = Snell), ``Kd``,
        ``kd_missing``, ``b_p``, ``bp_missing``, ``a_w``, ``b_w`` and
        ``scalars``.
    """
    from ioptics import run

    theta_s = run.resolve_theta_s(record)
    kd, kd_missing = _kd(spec, record, theta_s)
    bp, bp_missing, scalars = _bp(spec, record)
    a_w, b_w = pure_water(record.wave)
    return {'wave': np.asarray(record.wave, dtype=float),
            'Rrs': np.asarray(record.Rrs, dtype=float), 'theta_s': theta_s,
            'muw': _muw(spec, record), 'Kd': kd, 'kd_missing': kd_missing,
            'b_p': bp, 'bp_missing': bp_missing, 'a_w': a_w, 'b_w': b_w,
            'scalars': scalars}


def invert(spec, record):
    """Run LS2 on one record; the direct-driver contract of :mod:`ioptics.run`.

    Returns
    -------
    dict
        ``components`` (``a``, ``a_nw``, ``bb``, ``bb_p`` on ``record.wave``,
        restricted to ``spec.outputs``), ``nan_reason`` (per cell, see
        :func:`_reasons`) and ``scalars`` (``theta_s``, the ``muw`` used, the
        share of cells whose Raman correction failed, and ``Chl_oc4v4`` for
        the Chl side chain).
    """
    from ocpy.ls2.ls2_main import ls2_invert

    x = inputs(spec, record)
    muw = None if x['muw'] is None else np.full((1, x['wave'].size), x['muw'])
    res = ls2_invert(x['Rrs'][None, :], x['Kd'][None, :], x['a_w'], x['b_w'],
                     x['b_p'][None, :], np.array([x['theta_s']]), x['wave'],
                     _lut(), raman=bool(spec.raman), tol=spec.tol,
                     max_iter=int(spec.max_iter), clip_negative=False, muw=muw)
    values = {'a': res.a[0], 'a_nw': res.anw[0], 'bb': res.bb[0],
              'bb_p': res.bbp[0]}
    reasons = _reasons(res, x)
    used_muw = (x['muw'] if x['muw'] is not None
                else float(np.cos(np.arcsin(np.sin(np.deg2rad(x['theta_s']))
                                            / 1.34))))
    scalars = {'theta_s': (float(x['theta_s']), np.nan),
               'muw': (used_muw, np.nan),
               'frac_kappa_oor': (float(np.mean(res.kappa_out_of_range[0])),
                                  np.nan)}
    scalars.update(x['scalars'])
    return {'components': {k: values[k] for k in spec.outputs},
            'nan_reason': {k: reasons for k in spec.outputs},
            'scalars': scalars}


def _reasons(res, x):
    """Per-cell reason codes from ocpy's flags, shared by all four outputs.

    ``kd_missing`` and ``bp_missing`` say *why* an input was absent; an absent
    ``b_p`` also makes ``eta`` undefined, which ocpy reports as off-grid, so
    ``off_grid`` is kept only where ``b_p`` was present. ``kappa_out_of_range``
    and ``not_converged`` flag finite cells (the value is uncorrected, or the
    last applied correction; ls2 Q28). ``negative`` is per output and is added
    by :func:`ioptics.evaluate.assemble_direct`.
    """
    n = x['wave'].size
    out = []
    for j in range(n):
        codes = []
        if x['kd_missing'][j]:
            codes.append('kd_missing')
        if x['bp_missing'][j]:
            codes.append('bp_missing')
        elif res.off_grid[0, j]:
            codes.append('off_grid')
        if res.kappa_out_of_range[0, j]:
            codes.append('kappa_out_of_range')
        if res.not_converged[0, j] and not res.kappa_out_of_range[0, j] \
                and np.isfinite(res.a[0, j]):
            codes.append('not_converged')
        out.append(';'.join(codes))
    return np.array(out, dtype=object)

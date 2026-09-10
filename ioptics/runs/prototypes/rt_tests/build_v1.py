"""Staged sweep driver for the RT tests — one IOP model, five radiative transfers.

The question these sweeps exist to answer: **how much of a retrieval's error is
the radiative transfer?** Every IOPtics result so far was produced by BING's own
Gordon (1988) relation. Here the absorption/backscattering parameterization is
frozen at ``expb_pow`` and the RT is varied along a five-rung ladder — analytic
robust, hybrid (robust + learned emulator), and then the three inelastic
processes switched on one at a time — so a difference between two rows is the
forward model and nothing else:

- ``expb_pow_ztt_el``          robust_ztt, elastic
- ``expb_pow_hyb_el``          robust_hybrid, elastic
- ``expb_pow_hyb_ram``         robust_hybrid + Raman
- ``expb_pow_hyb_ramfl``       ... + chlorophyll fluorescence
- ``expb_pow_hyb_ramflcdom``   ... + CDOM fluorescence

All five fit ``B_p`` free, so ``k = 6``.

Two arms, because the two questions need different data:

- **arm A** (``run_rta.yaml``) — L23 X=4 + PANGAEA-97: graded against IOP truth.
- **arm B** (``run_rtb.yaml``) — 100 real PACE OCI pixels: no truth, so it scores
  model selection (ΔBIC) and closure on real hyperspectral radiance.

Usage (one stage per call, mirroring ``build_v2.py`` / ``build_v3.py``)::

    python build_v1.py <flg> [--n-cores N] [--strict BOOL] [--config NAME]

    1  run     arm A -> results_{spectral,scalar}.parquet + provenance
    2  metrics arm A -> metrics_{spectral,scalar,pairwise}
    3  run     arm B
    4  metrics arm B
    5  report  (both arms; see the stage-5 stub)

``0`` is a no-op. ``--config smoke`` redirects stages **1** and **2** onto
``run_smoke.yaml`` (16 records, all three datasets) — the end-to-end gate that
must pass before either real arm is launched::

    python build_v1.py 1 --config smoke --n-cores 8 --strict false
    python build_v1.py 2 --config smoke

Two things differ from the other prototype drivers:

1. The five RT variants are **opt-in** — they are one algorithm under five
   physics packages, not five competing retrievals, so seeding them would put
   five near-clones of ``expb_pow`` on every cross-algorithm board. Every stage
   that resolves an algorithm name therefore calls
   :func:`ioptics.algorithms.registry.register_rt_variants` first
   (:func:`_register`), exactly as ``build_v3.py`` calls ``register_turbid()``.
2. The metrics stages pass ``dbic_pair=registry.RT_DBIC_PAIR`` — the elastic
   hybrid against the full inelastic stack. ΔBIC is computed for every pair
   regardless; this names the one the sweeps exist to answer, and marks its rows
   ``configured=True``.

The YAMLs beside this file are the source of truth. Paths derive from
``$OS_COLOR`` + the sweep id (see ``ioptics.io``).
"""

import os

from ioptics import config, run

HERE = os.path.dirname(os.path.abspath(__file__))

#: Arm A: L23 (X=4) + PANGAEA-97, graded against IOP truth.
CONFIG_RTA = os.path.join(HERE, 'run_rta.yaml')

#: Arm B: 100 real PACE OCI pixels, scored on model selection + closure.
CONFIG_RTB = os.path.join(HERE, 'run_rtb.yaml')

#: The 16-record, three-dataset end-to-end smoke (``--config smoke``).
CONFIG_SMOKE = os.path.join(HERE, 'run_smoke.yaml')

CONFIGS = {'rta': CONFIG_RTA, 'rtb': CONFIG_RTB, 'smoke': CONFIG_SMOKE}

#: Which config each stage operates on by default. ``--config`` overrides it.
STAGE_CONFIG = {1: 'rta', 2: 'rta', 3: 'rtb', 4: 'rtb'}

#: The frozen PANGAEA population (see ``derive_pangaea97.py``).
PANGAEA_IDS_CSV = os.path.join(HERE, 'pangaea97_ids.csv')

#: The frozen PACE population (see ``extract_pace_100.py``).
PACE_IDS_CSV = os.path.join(HERE, 'pace100_ids.csv')


def read_ids_csv(path, cast=str):
    """Read a frozen id list: one id per line, ``#`` comments and blanks skipped.

    The two CSVs beside this file are the *citable definitions* of their
    populations — deriving the ids again at run time would let an upstream table
    revision (PANGAEA) or an archive change (PACE) silently move which spectra a
    published number describes. ``cast`` is :class:`int` for PANGAEA's global
    ``ID`` and :class:`str` for PACE's chain-file stems.
    """
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith('#'):
                out.append(cast(line))
    return out


def pangaea97_ids():
    """The 97 frozen PANGAEA ids, as integers."""
    return read_ids_csv(PANGAEA_IDS_CSV, cast=int)


def pace100_ids():
    """The 100 frozen PACE ids (run1k chain-file stems), as strings."""
    return read_ids_csv(PACE_IDS_CSV, cast=str)


#: Per-dataset id bounds for the smoke sweep. ``obs_ids`` is a run-time argument
#: to :func:`ioptics.run.run_sweep`, not a config key, so it lives here rather
#: than in ``run_smoke.yaml``.
#:
#: The PANGAEA four are chosen, not sampled: ``20933``/``20965`` are 11-band
#: (fittable at ``k = 6``) and ``10685``/``10771`` are 6-band, so the smoke
#: exercises both a real fit and the ``n_bands <= k`` underdetermined refusal
#: that 74 of arm A's 97 PANGAEA records will hit. The L23 eight and the PACE
#: four are simply the first of each population, which keeps them stable.
SMOKE_PANGAEA_IDS = [20933, 20965, 10685, 10771]
SMOKE_N_L23 = 8
SMOKE_N_PACE = 4


def bounded_obs_ids(config_name='rta'):
    """The per-dataset ``{dataset: [ids]}`` bound for one config, or ``None``.

    Arm A bounds **PANGAEA alone** to its 97 frozen ids; L23 is absent from the
    mapping and therefore runs in full (all 3 320 X=4 spectra carry the complete
    truth decomposition, so there is nothing to bound away). Arm B needs no
    bound at all — the PACE dataset *is* the 100 frozen spectra — so it returns
    ``None``, which :func:`ioptics.run.run_sweep` reads as "everything". The
    smoke bounds all three.

    Parameters
    ----------
    config_name : str, optional
        One of :data:`CONFIGS`.

    Returns
    -------
    dict or None
        ``{dataset: ids}`` for :func:`ioptics.run.run_sweep`'s ``obs_ids``.
    """
    if config_name == 'rta':
        return {'PANGAEA': pangaea97_ids()}
    if config_name == 'rtb':
        return None
    if config_name == 'smoke':
        from ioptics import datasets
        return {
            'L23': list(datasets.get_adapter('L23').obs_ids(X=4))[:SMOKE_N_L23],
            'PANGAEA': list(SMOKE_PANGAEA_IDS),
            'PACE': pace100_ids()[:SMOKE_N_PACE],
        }
    raise KeyError(f'unknown config {config_name!r}; known: {sorted(CONFIGS)}')


def _register():
    """Opt into the five RT variants; returns ``{name: AlgorithmSpec}``.

    Called at the top of **every** stage that resolves an algorithm name — the
    run stages (``run_sweep`` looks each name up in the registry) and the report
    stage (labels). The metrics stages read tables and need no registry, but
    calling it there too costs nothing and keeps the rule "if the stage says
    ``expb_pow_hyb_*``, it registered them first" simple enough to not get wrong.
    """
    from ioptics.algorithms import registry
    return registry.register_rt_variants()


def _dbic_pair():
    """The ΔBIC contest these sweeps are read through."""
    from ioptics.algorithms import registry
    return registry.RT_DBIC_PAIR


def _run(config_name, *, n_cores, strict, obs_ids=None):
    """Stage-1-style run of one config: prep + chi-squared + MCMC + provenance."""
    _register()
    cfg = config.load(CONFIGS[config_name])
    if obs_ids is None:
        obs_ids = bounded_obs_ids(config_name)
    if obs_ids:
        bound = ', '.join(f'{k}={len(v)}' for k, v in sorted(obs_ids.items()))
        print(f'[{config_name}] bounded: {bound}; '
              f'datasets not listed run in full')
    return run.run_sweep(cfg, obs_ids=obs_ids, n_cores=n_cores, strict=strict)


def _metrics(config_name):
    """Stage-2-style scoring of one config, with the configured ΔBIC pair."""
    from ioptics import metrics

    _register()
    cfg = config.load(CONFIGS[config_name])
    pair = _dbic_pair()
    print(f'[{config_name}] metrics; dbic_pair={pair}')
    return metrics.compute(cfg.sweep_id, dbic_pair=pair)


def main(flg, *, n_cores=1, strict=True, obs_ids=None, config_name=None):
    """Run one stage. ``config_name`` overrides the stage's default config."""
    flg = int(flg)

    if config_name is not None and flg in (3, 4):
        raise SystemExit(
            f'--config {config_name} redirects stages 1 (run) and 2 (metrics) '
            f'only; stage {flg} is arm B and already has its own config. Use '
            f'stage 1/2 with --config {config_name}, or drop --config.')
    name = config_name or STAGE_CONFIG.get(flg)

    if flg in (1, 3):
        _run(name, n_cores=n_cores, strict=strict, obs_ids=obs_ids)

    elif flg in (2, 4):
        _metrics(name)

    elif flg == 5:
        # Stage numbering is kept stable so the run notes and the shell history
        # do not have to be rewritten when the report lands.
        raise SystemExit(
            'stage 5 (report) is task 13: the RT ladder needs its own page '
            '(five rows that are one algorithm, a leaderboard that must stay '
            'out of it, and the no_CDOMfl_truth / CDOM-fraction caveats in the '
            'prose). Run stages 1-4 now; regenerate 5 when task 13 lands.')


def _cli(argv=None):
    """CLI: ``build_v1.py <flg> [--n-cores N] [--strict BOOL] [--config NAME]``."""
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('flg', nargs='?', type=int, default=0,
                   help='stage: 1 run A, 2 metrics A, 3 run B, 4 metrics B, '
                        '5 report (0 = no-op)')
    p.add_argument('--n-cores', type=int, default=1,
                   help='parallel workers for prep + chi^2 + MCMC (run stages)')
    p.add_argument('--strict', default='false',
                   help='true = fail-fast; false = robust fit_failed rows '
                        '(false by default here: 74 of the 97 PANGAEA records '
                        'are underdetermined at k=6 and are *expected* to fail)')
    p.add_argument('--config', default=None, choices=sorted(CONFIGS),
                   help="redirect stages 1/2 onto another config "
                        "(mainly '--config smoke')")
    a = p.parse_args(argv)

    strict = str(a.strict).strip().lower() not in ('false', '0', 'no', 'f')
    main(a.flg, n_cores=a.n_cores, strict=strict, config_name=a.config)


if __name__ == '__main__':
    _cli()

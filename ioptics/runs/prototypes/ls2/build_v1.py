"""Staged sweep driver for LS2 on L23 -- the input ladder, three realizations.

LS2 (Loisel et al. 2018) is the first **direct** algorithm in IOPtics: no
fit, so a sweep is one pass per rung, and the cost is in preparing the records,
not in the algorithm. The rungs differ in one input each (ls2 Q2; see
``ioptics.algorithms.registry.DIRECT_SEED``), and the sweep is run on each of
L23's three inelastic realizations (ls2 Q4), one sweep each, because a sweep
carries one ``dataset_opts``:

- ``run_ls2_l23_x4.yaml`` -- Raman + Chl fluorescence; kappa on.
- ``run_ls2_l23_x2.yaml`` -- Raman only; kappa on. The matched partner of X=1.
- ``run_ls2_l23_x1.yaml`` -- elastic; kappa **off** on every rung.

Usage (one stage per call)::

    PYTHONPATH=. python ioptics/runs/prototypes/ls2/build_v1.py <flg> \\
        [--n-cores N] [--strict BOOL] [--config NAME]

    1  run     the L23 sweeps (X=4, then X=2, then X=1) -> results + provenance
    2  metrics the L23 sweeps                          -> metrics parquets
    3  report  the ls2_ladder page, one per sweep (ls2 task 9)
    9  summary of a sweep that has run (status, NaN reasons, kappa) -- printed
       automatically after stage 1, and callable on its own

``0`` is a no-op. ``--config smoke`` redirects stages 1, 2 and 9 onto
``run_smoke.yaml`` (16 L23 records, all eight rungs), the gate that must pass
before the real sweeps are launched::

    python build_v1.py 1 --config smoke
    python build_v1.py 2 --config smoke

``--config x4`` (or ``x2``, ``x1``) runs one realization.

The rungs are **opt-in** (they are one algorithm with different inputs, not
competing retrievals), so every stage that resolves a name calls
:func:`ioptics.algorithms.registry.register_direct` first (:func:`_register`),
as ``rt_tests/build_v1.py`` calls ``register_rt_variants``. ``PYTHONPATH=.``
from the repository root is needed unless ``pip install -e .`` has been run.
"""

import collections
import os
import time
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))

CONFIGS = {
    'x4': os.path.join(HERE, 'run_ls2_l23_x4.yaml'),
    'x2': os.path.join(HERE, 'run_ls2_l23_x2.yaml'),
    'x1': os.path.join(HERE, 'run_ls2_l23_x1.yaml'),
    'smoke': os.path.join(HERE, 'run_smoke.yaml'),
}

#: Default config(s) per stage; a tuple runs each in order. X=4 first: it is
#: the realization the BING comparison (RT-A) used, and the one the smoke
#: mirrors, so a problem shows up on the sweep that matters most.
STAGE_CONFIG = {1: ('x4', 'x2', 'x1'), 2: ('x4', 'x2', 'x1'),
                3: ('x4', 'x2', 'x1'), 9: ('x4', 'x2', 'x1')}

#: BING sweep each LS2 sweep is set beside on its page (ls2 Q23: the headline
#: is quoted against MCMC BING on the same spectra). RT-A ran BING on L23 X=4
#: only; the X=2 and X=1 pages have no comparator and say so.
COMPARATOR = {'x4': 'rt_tests_A_l23_v1'}

#: The smoke's L23 records: the first 15 plus record 75, which has 15 cells
#: outside the ``eta < 0.2`` envelope, so the ``off_grid`` path is exercised.
#: ``obs_ids`` is a run-time argument to ``run_sweep``, not a config key, so it
#: lives here.
SMOKE_L23_IDS = list(range(15)) + [75]


def bounded_obs_ids(config_name):
    """``{dataset: ids}`` for ``run_sweep``, or ``None`` to run in full."""
    if config_name == 'smoke':
        return {'L23': list(SMOKE_L23_IDS)}
    if config_name in CONFIGS:
        return None
    raise KeyError(f'unknown config {config_name!r}; known: {sorted(CONFIGS)}')


def _register():
    """Opt into the LS2 rungs; returns ``{name: DirectSpec}``."""
    from ioptics.algorithms import registry
    return registry.register_direct()


def _run(config_name, *, n_cores, strict):
    """Stage 1 for one config: prep + LS2 + results + provenance, timed.

    Warnings raised during the sweep are captured and summarized (one line per
    distinct message, with counts). On an unattended run a domain warning --
    a network evaluated far outside its training data, an off-table input --
    is often the first sign of trouble, and it must not scroll away.
    """
    from ioptics import config, run

    _register()
    cfg = config.load(CONFIGS[config_name])
    obs_ids = bounded_obs_ids(config_name)
    if obs_ids:
        bound = ', '.join(f'{k}={len(v)}' for k, v in sorted(obs_ids.items()))
        print(f'[{config_name}] bounded: {bound}')
    t0 = time.time()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        out = run.run_sweep(cfg, obs_ids=obs_ids, n_cores=n_cores,
                            strict=strict)
    elapsed = time.time() - t0
    print(f'[{config_name}] {cfg.sweep_id}: {out["n_results"]} results in '
          f'{elapsed:.1f} s ({elapsed / max(out["n_results"], 1) * 1e3:.1f} '
          f'ms per result, prep included)')
    if caught:
        top = collections.Counter(f'{w.category.__name__}: {w.message}'
                                  for w in caught).most_common(8)
        print(f'[{config_name}] {len(caught)} warnings during the sweep:')
        for msg, n in top:
            print(f'    x{n:<6d} {msg[:150]}')
    else:
        print(f'[{config_name}] no warnings during the sweep')
    summary(cfg.sweep_id)
    return out


def summary(sweep_id):
    """Print what a sweep produced: statuses, NaN reasons and kappa, per rung.

    Returns
    -------
    dict
        ``{'status': DataFrame, 'reasons': DataFrame, 'kappa': Series}`` --
        what was printed, for a test or a notebook.
    """
    import pandas as pd

    from ioptics import io
    from ioptics.records import NAN_REASON_SEP, NAN_REASONS

    spectral, scalar = io.read_results(sweep_id)
    status = (scalar.groupby('algorithm')['status'].value_counts()
              .unstack(fill_value=0))
    print(f'\n[{sweep_id}] status per rung (records):')
    print(status.to_string())

    # NaN reasons per rung, in cells of the 'a' component (the reasons are
    # shared by the four outputs except 'negative', which is per output).
    rows = []
    for algo, g in spectral[spectral['component'].isin(['a', 'a_nw', 'bb',
                                                        'bb_p'])].groupby(
            ['algorithm', 'component']):
        codes = collections.Counter()
        for cell in g['nan_reason'].fillna(''):
            codes.update(c for c in str(cell).split(NAN_REASON_SEP) if c)
        row = {'algorithm': algo[0], 'component': algo[1], 'cells': len(g)}
        row.update({r: codes.get(r, 0) for r in NAN_REASONS})
        rows.append(row)
    reasons = pd.DataFrame(rows)
    print(f'\n[{sweep_id}] NaN-reason cell counts per rung and component:')
    print(reasons.loc[:, (reasons != 0).any(axis=0)].to_string(index=False))

    kappa = (scalar.groupby('algorithm')['frac_kappa_oor'].median()
             if 'frac_kappa_oor' in scalar.columns else pd.Series(dtype=float))
    if not kappa.empty:
        print(f'\n[{sweep_id}] median share of cells losing kappa per rung:')
        print(kappa.round(3).to_string())
    return {'status': status, 'reasons': reasons, 'kappa': kappa}


def _metrics(config_name):
    """Stage 2 for one config: the metrics tables."""
    from ioptics import config, metrics

    _register()
    cfg = config.load(CONFIGS[config_name])
    t0 = time.time()
    tables = metrics.compute(cfg.sweep_id)
    print(f'[{config_name}] metrics for {cfg.sweep_id} in '
          f'{time.time() - t0:.1f} s: {len(tables.spectral)} spectral, '
          f'{len(tables.scalar)} scalar, {len(tables.pairwise)} pairwise rows')
    return tables


def _report(config_name):
    """Stage 3: the ``ls2_ladder`` page for one sweep (ls2 task 9).

    Written into the docs tree (``docs/source/reports/<sweep_id>/``); never
    touches the leaderboard or the landing page. The comparator BING sweep
    (:data:`COMPARATOR`) is used when its metrics are on this machine; the page
    states it when they are not.
    """
    from ioptics import config, io
    from ioptics.report import ls2_ladder

    _register()
    cfg = config.load(CONFIGS[config_name])
    if not (io.sweep_dir(cfg.sweep_id) / 'results_scalar.parquet').is_file():
        print(f'[{config_name}] no results for {cfg.sweep_id}; skipping the page')
        return None
    out = ls2_ladder.build(cfg.sweep_id,
                           compare_sweep=COMPARATOR.get(config_name))
    print(f'[{config_name}] wrote {out}')
    return out


def main(flg, *, n_cores=1, strict=False, config_name=None):
    """Run one stage. ``config_name`` overrides the stage's default config(s)."""
    flg = int(flg)
    default = STAGE_CONFIG.get(flg, ())
    names = (config_name,) if config_name is not None else default
    for name in names:
        if flg == 1:
            _run(name, n_cores=n_cores, strict=strict)
        elif flg == 2:
            _metrics(name)
        elif flg == 3:
            _report(name)
        elif flg == 9:
            from ioptics import config
            summary(config.load(CONFIGS[name]).sweep_id)


def _cli(argv=None):
    """CLI: ``build_v1.py <flg> [--n-cores N] [--strict BOOL] [--config NAME]``."""
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('flg', nargs='?', type=int, default=0,
                   help='stage: 1 run, 2 metrics, 3 report, 9 summary (0 = no-op)')
    p.add_argument('--n-cores', type=int, default=1,
                   help='parallel workers for prep and the LS2 pass')
    p.add_argument('--strict', default='false',
                   help='true = fail-fast; false (default) = a record that '
                        'cannot be run becomes a fit_failed row (e.g. the five '
                        'X=2 scenarios missing from their profile file)')
    p.add_argument('--config', default=None, choices=sorted(CONFIGS),
                   help="run one config instead of the stage's default "
                        "(mainly '--config smoke')")
    a = p.parse_args(argv)
    strict = str(a.strict).strip().lower() not in ('false', '0', 'no', 'f')
    main(a.flg, n_cores=a.n_cores, strict=strict, config_name=a.config)


if __name__ == '__main__':
    _cli()

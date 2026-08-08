"""Staged sweep driver for the in-tandem L23 ``expb_pow``/``giop`` comparison.

Usage::

    python build_v1.py <flg>

``<flg>`` is the stage number to (re-)run (one stage per call), so the long
parts (the sweep / MCMC) need not be repeated to regenerate a report:

    1  run     -> prep + retrieve -> results_{spectral,scalar}.parquet + provenance
    2  metrics -> score the results table -> metrics_{spectral,scalar,pairwise}
    3  report  -> standard.build (figures/tables/bokeh/rst) + leaderboard

Run the stages in order (``1`` then ``2`` then ``3``); ``0`` is a no-op.

Stage 1 accepts run knobs: ``n_cores`` (pool the chi^2 population; the MCMC
subset is serial regardless), ``strict`` (``False`` = robust — failed fits
become ``status='fit_failed'`` rows instead of aborting the sweep), and
``obs_ids`` (restrict to a subset, e.g. a smoke run).

The single ``run_v1.yaml`` beside this file is the source of truth (sweep id,
datasets, algorithms, noise model, fit method, MCMC subset). Paths derive from
``$OS_COLOR`` + the sweep id (see ``ioptics.io``).
"""

import os

from ioptics import config, run

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, 'run_v1.yaml')

#: The 20-spectrum smoke variant (``run_test20.yaml``). Selected with
#: ``--config test20``. It is the sweep behind the published
#: ``reports/expb_giop_L23_test20/`` page, which had no committed config until
#: Stage 7 Task 11 and so could not be regenerated when it went stale.
CONFIG_TEST20 = os.path.join(HERE, 'run_test20.yaml')

#: The full-L23 MCMC variant (``run_l23_mcmc_full.yaml``), selected with
#: ``--config l23_mcmc_full``. **Prepared, not run** — see Stage 7 Task 13 for the
#: measured cost (~5.4 days serial, ~40 GB of chains as the code stands) and the two
#: changes that make it an overnight job.
CONFIG_L23_MCMC = os.path.join(HERE, 'run_l23_mcmc_full.yaml')

CONFIGS = {'v1': CONFIG, 'test20': CONFIG_TEST20,
           'l23_mcmc_full': CONFIG_L23_MCMC}


def main(flg, *, n_cores=1, strict=True, obs_ids=None, config_name='v1'):
    flg = int(flg)
    cfg = config.load(CONFIGS[config_name])

    if flg == 1:
        # prep + retrieve -> tables + provenance
        run.run_sweep(cfg, obs_ids=obs_ids, n_cores=n_cores, strict=strict)

    elif flg == 2:
        from ioptics import metrics
        metrics.compute(cfg.sweep_id)           # score the results table

    elif flg == 3:
        from ioptics import report
        # standard report page (figures + tables + bokeh, provenance-stamped)
        report.standard.build(cfg.sweep_id, kind='cross_algorithm')
        # fold this sweep into the cross-sweep leaderboard, then rebuild the
        # landing page (headline board + sweep cards + interactive widget) and
        # its full-grid drill-down.
        report.standard.build_landing()


def _cli(argv=None):
    """CLI: ``build_v1.py <flg> [--n-cores N] [--strict BOOL] [--obs-ids A:B]``."""
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('flg', nargs='?', type=int, default=0,
                   help='stage: 1 run, 2 metrics, 3 report (0 = no-op)')
    p.add_argument('--n-cores', type=int, default=1,
                   help='parallel workers for prep + chi^2 (stage 1)')
    p.add_argument('--strict', default='true',
                   help='true = fail-fast; false = robust fit_failed rows (stage 1)')
    p.add_argument('--config', default='v1', choices=sorted(CONFIGS),
                   help="which sweep config: 'v1' (full L23) or 'test20' (smoke)")
    p.add_argument('--obs-ids', default=None,
                   help="restrict prep to a range 'A:B' (stage 1; default all)")
    a = p.parse_args(argv)

    strict = str(a.strict).strip().lower() not in ('false', '0', 'no', 'f')
    obs_ids = None
    if a.obs_ids:
        lo, hi = (int(x) for x in a.obs_ids.split(':'))
        obs_ids = range(lo, hi)
    main(a.flg, n_cores=a.n_cores, strict=strict, obs_ids=obs_ids,
         config_name=a.config)


if __name__ == '__main__':
    _cli()

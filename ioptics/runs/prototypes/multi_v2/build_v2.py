"""Staged sweep driver for the Stage-6 multi-everything comparison.

The broad run the architecture was built for: **two datasets × three
algorithms**, χ² — L23 (X=1, elastic) and PANGAEA in-situ, each fit by
``expb_pow``, ``giop`` and ``gsm`` — folded into the cross-sweep leaderboard.

Usage (one stage per call, mirroring ``build_v1.py``)::

    python build_v2.py <flg>

    1  run     -> prep + retrieve -> results_{spectral,scalar}.parquet + provenance
    2  metrics -> score the results table -> metrics_{spectral,scalar,pairwise}
    3  report  -> standard.build (figures/tables/bokeh/rst) + leaderboard

Run the stages in order (``1`` then ``2`` then ``3``); ``0`` is a no-op.

The leaderboard **accumulates across sweeps** (``report.leaderboard.update``),
so the GLORIA scalar sweep (scalar-only, ``noise='insitu'``) and native
per-dataset-noise sweeps fold into the *same* leaderboard as this one — the
design's "multi-dataset is a group-by / accumulate across sweeps." A single
sweep carries one ``noise_model`` (here ``pct:0.05``, uniform across L23 +
PANGAEA); compare native noise models (L23 ``pace`` vs PANGAEA ``insitu``) by
running them as separate sweeps and folding both.

``run_v2.yaml`` beside this file is the source of truth. Paths derive from
``$OS_COLOR`` + the sweep id (see ``ioptics.io``).
"""

import os

from ioptics import config, run

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, 'run_v2.yaml')


def main(flg, *, n_cores=1, strict=True, obs_ids=None):
    flg = int(flg)
    cfg = config.load(CONFIG)

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
        # fold this sweep into the cross-sweep leaderboard + refresh the landing
        # (the fold now carries the GLORIA CDOM-vs-a_dg caveat through, so the
        # accumulated leaderboard surfaces it once a GLORIA sweep is folded)
        board = report.leaderboard.update()
        idx = report.standard.DEFAULT_DOCS_SRC / 'reports' / 'index.rst'
        report.rst.write_leaderboard_landing(
            idx, report.leaderboard.render(board=board))


def _cli(argv=None):
    """CLI: ``build_v2.py <flg> [--n-cores N] [--strict BOOL] [--obs-ids A:B]``.

    Note: ``--obs-ids`` restricts *every* dataset to the same ids, which only
    makes sense for integer-id datasets (L23). A mixed L23/PANGAEA sweep with a
    subset isn't expressible today (PANGAEA ids are strings) — run the full
    sweep (``obs_ids=None``) or one dataset at a time (see Task-7 Q&A).
    """
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('flg', nargs='?', type=int, default=0,
                   help='stage: 1 run, 2 metrics, 3 report (0 = no-op)')
    p.add_argument('--n-cores', type=int, default=1,
                   help='parallel workers for prep + chi^2 (stage 1)')
    p.add_argument('--strict', default='true',
                   help='true = fail-fast; false = robust fit_failed rows (stage 1)')
    p.add_argument('--obs-ids', default=None,
                   help="restrict prep to a range 'A:B' (stage 1; L23-only)")
    a = p.parse_args(argv)

    strict = str(a.strict).strip().lower() not in ('false', '0', 'no', 'f')
    obs_ids = None
    if a.obs_ids:
        lo, hi = (int(x) for x in a.obs_ids.split(':'))
        obs_ids = range(lo, hi)
    main(a.flg, n_cores=a.n_cores, strict=strict, obs_ids=obs_ids)


if __name__ == '__main__':
    _cli()

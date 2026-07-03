"""Staged sweep driver for the in-tandem L23 ``expb_pow``/``giop`` comparison.

Usage::

    python build_v1.py <flg>

``<flg>`` is the stage number to (re-)run (one stage per call), so the long
parts (the sweep / MCMC) need not be repeated to regenerate a report:

    1  run     -> prep + retrieve -> results_{spectral,scalar}.parquet + provenance
    2  metrics -> score the results table -> metrics_{spectral,scalar,pairwise}
    3  report  -> standard.build (figures/tables/bokeh/rst) + leaderboard

Run the stages in order (``1`` then ``2`` then ``3``); ``0`` is a no-op.

The single ``run_v1.yaml`` beside this file is the source of truth (sweep id,
datasets, algorithms, noise model, fit method, MCMC subset). Paths derive from
``$OS_COLOR`` + the sweep id (see ``ioptics.io``).
"""

import os
import sys

from ioptics import config, run

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, 'run_v1.yaml')


def main(flg):
    flg = int(flg)
    cfg = config.load(CONFIG)

    if flg == 1:
        run.run_sweep(cfg)                      # prep + retrieve -> tables + provenance

    elif flg == 2:
        from ioptics import metrics
        metrics.compute(cfg.sweep_id)           # score the results table

    elif flg == 3:
        from ioptics import report
        # standard report page (figures + tables + bokeh, provenance-stamped)
        report.standard.build(cfg.sweep_id, kind='cross_algorithm')
        # fold this sweep into the cross-sweep leaderboard + refresh the landing
        board = report.leaderboard.update()
        idx = report.standard.DEFAULT_DOCS_SRC / 'reports' / 'index.rst'
        report.rst.write_leaderboard_landing(
            idx, report.leaderboard.render(board=board))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 0)

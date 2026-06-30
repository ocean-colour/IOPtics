"""Staged sweep driver for the in-tandem L23 ``expb_pow``/``giop`` comparison.

Usage::

    python build_v1.py <flg>

``<flg>`` is an integer bitmask selecting the stage(s) to (re-)run, so the long
parts (the sweep / MCMC) need not be repeated to regenerate a figure:

    1  (2**0)  run     -> prep + retrieve -> results_{spectral,scalar}.parquet + provenance
    2  (2**1)  metrics -> score the results table          (Stage 4 — stub here)
    4  (2**2)  report  -> figures / tables / leaderboard   (Stage 5 — stub here)

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

    if flg & 2 ** 0:
        run.run_sweep(cfg)                      # prep + retrieve -> tables + provenance

    if flg & 2 ** 1:
        # from ioptics import metrics; metrics.compute(cfg.sweep_id)   # Stage 4
        pass

    if flg & 2 ** 2:
        # from ioptics import report; report.standard.build(cfg.sweep_id)  # Stage 5
        pass


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 0)

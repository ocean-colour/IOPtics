"""MOANA: reimplementation of the NASA PACE picophytoplankton algorithm.

A separate track from the IOP work (Q&A #3): empirical PC regression from
hyperspectral Rrs (+SST) to Prochlorococcus / Synechococcus / picoeukaryote
cell abundances. Design: ``docs/design/moana_design.md``; background:
``reports/MOANA_Claude_Report.md``.

Public surface:

- :func:`ioptics.moana.algorithm.run_moana` — the retrieval;
- :func:`ioptics.moana.io.load_luts` — the vendored NASA constants;
- :func:`ioptics.moana.pipeline.process_cruise` /
  :func:`ioptics.moana.pipeline.build_training_matrix` — AMT24 Level-2 →
  training matrix;
- :func:`ioptics.moana.train.train_moana` — retraining + basis comparison.
"""

from ioptics.moana.algorithm import run_moana
from ioptics.moana.io import load_luts
from ioptics.moana.pipeline import (DEFAULT_PIPELINE, build_training_matrix,
                                    process_cruise, process_day)
from ioptics.moana.train import compare_loadings, train_moana

__all__ = ['run_moana', 'load_luts', 'process_day', 'process_cruise',
           'build_training_matrix', 'train_moana', 'compare_loadings',
           'DEFAULT_PIPELINE']

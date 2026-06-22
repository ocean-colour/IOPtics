"""The run/sweep driver: run_algorithm / run_batch / run_sweep.

Wires BING on a record's native grid and runs a fit: least-squares
(``bing.fitting.chisq_fit``) by default, MCMC (``bing.fitting.inference``) for
a flagged subset. Builds models per record via ``init_model`` and the
``rt_dict`` via ``rt.defs``, then hands chains/params to :mod:`ioptics.evaluate`.

Stub — implemented in a later stage (see
``docs/design/IOPtics_implementation.md`` §"Retrieval & run").
"""

from __future__ import annotations

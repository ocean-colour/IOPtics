"""Turn a fit into a :class:`ioptics.records.RetrievalResult`.

Reconstructs ``a(lambda)`` / ``bb(lambda)`` and components with uncertainty
(MCMC percentiles or least-squares covariance), and computes fit stats
(chi^2, reduced chi^2, AIC, BIC) by wrapping ``bing.evaluate`` and
``bing.stats``.

Stub — implemented in a later stage (see
``docs/design/IOPtics_implementation.md`` §"Retrieval & run").
"""

from __future__ import annotations

"""Build / stamp / write the YAML/JSON provenance record for a sweep.

Assembles the provenance record (model config, RT options, fit method, noise
model, and — for MCMC — priors) and stamps versions (design-doc, registry
entry, dataset, ocpy/bing/ioptics commits). Written beside the results table.

Stub — implemented in a later stage (see
``docs/design/IOPtics_implementation.md`` §"Retrieval & run" / provenance).
"""

from __future__ import annotations

"""Long/tidy parquet results tables and the sweep-directory layout.

Reads/writes the per-sweep tables (``results_spectral.parquet``,
``results_scalar.parquet``) and owns the directory layout
``$OS_COLOR/IOPtics/runs/<sweep_id>/{..., provenance.yaml, chains/, figures/}``;
saves/loads MCMC chain NPZs.

Stub — implemented in a later stage (see
``docs/design/IOPtics_implementation.md`` §"Retrieval & run" / results-table
schema).
"""

from __future__ import annotations

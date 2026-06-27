"""IOPtics: testing and evaluating IOP (inherent optical property) algorithms."""

__version__ = '0.0.dev0'

# Lightweight top-level re-exports of the load-bearing pipeline contracts.
# (records.py depends only on numpy + dataclasses, so this stays import-cheap.)
from ioptics.records import ComponentFit, PreparedRecord, RetrievalResult

__all__ = ['__version__', 'PreparedRecord', 'RetrievalResult', 'ComponentFit']

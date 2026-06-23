"""Rrs-uncertainty attachment (PACE etc. via ocpy).

Builds the ``varRrs`` variance vector for a record; the choice is recorded as
``noise_model`` for provenance. Thin wrapper over ``ocpy.satellites.pace``
(L23 first pass), the dataset's own measured errors (in-situ), or a percentage
fallback. With :mod:`ioptics.datasets`, the only module that imports ocpy.

Stub — implemented in a later stage (see
``docs/design/IOPtics_implementation.md`` §"Data preparation").
"""

from __future__ import annotations

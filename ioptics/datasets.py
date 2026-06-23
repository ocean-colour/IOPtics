"""Dataset registry: thin adapters over ocpy loaders.

Maps a dataset name (``'L23'`` | ``'PANGAEA'`` | ``'GLORIA'``) to an adapter
that enumerates observation ids and returns one observation's ``Rrs`` + truth
on the **native grid**. With :mod:`ioptics.noise`, this is the only module
that imports ocpy.

Stub — implemented in a later stage (see
``docs/design/IOPtics_implementation.md`` §"Data preparation").
"""

from __future__ import annotations

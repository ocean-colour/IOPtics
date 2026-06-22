"""Dataset-agnostic prep layer (generalizes ``bing.fitting.l23.prep_one_l23``).

Takes a loaded observation, attaches ``Rrs`` uncertainty, pre-aligns spectral
truth onto the native grid, and assembles a :class:`ioptics.records.PreparedRecord`.
Does **no** model/prior/RT work — that is the algorithm's job at run time
(:mod:`ioptics.run`).

Stub — implemented in a later stage (see
``docs/design/IOPtics_implementation.md`` §"Data preparation").
"""

from __future__ import annotations

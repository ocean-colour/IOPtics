"""``AlgorithmSpec`` — declarative, serializable mirror of a BING parameter set.

Describes one algorithm (a_nw + bb_nw model names, priors, RT toggles incl.
Raman/Chl-fl, fit method, noise model). ``.to_bing_p()`` emits the BING
parameter namedtuple; ``.from_standard(name)`` seeds from
``bing.parameters.standard``; ``.build_models(wave)`` builds the model list
``run`` uses.

Stub — implemented in Stage 2 (see
``docs/design/IOPtics_implementation.md`` §"Algorithm registry").
"""

from __future__ import annotations

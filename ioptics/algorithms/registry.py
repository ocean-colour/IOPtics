"""Name -> :class:`~ioptics.algorithms.spec.AlgorithmSpec` registry.

The growing catalog of algorithms IOPtics can run. **Seeded with ``expb_pow``
and ``giop`` side by side** (the design's "develop the two in tandem"), so the
comparison tooling is exercised on a genuine two-way contest from day one;
``register()`` adds more (e.g. ``gsm``) in one line.

``config`` resolves a sweep's algorithm *names* against this registry into
``AlgorithmSpec`` objects.
"""

from __future__ import annotations

from ioptics.algorithms.spec import AlgorithmSpec

REGISTRY: dict = {}


def register(spec, *, overwrite=False):
    """Register ``spec`` under ``spec.name``.

    Raises :class:`ValueError` if the name is already registered (the
    duplicate-name guard) unless ``overwrite=True``.
    """
    if spec.name in REGISTRY and not overwrite:
        raise ValueError(
            f"algorithm {spec.name!r} is already registered "
            "(pass overwrite=True to replace it)")
    REGISTRY[spec.name] = spec
    return spec


def get(name):
    """Return the :class:`AlgorithmSpec` registered under ``name``."""
    if name not in REGISTRY:
        raise KeyError(
            f"unknown algorithm {name!r}; available: {available()}")
    return REGISTRY[name]


def available():
    """Return the sorted list of registered algorithm names."""
    return sorted(REGISTRY)


# --- seed the in-tandem pair (expb_pow + giop) ------------------------------
# Seeding calls AlgorithmSpec.from_standard, which imports bing. It is wrapped
# so a mocked/absent bing (e.g. the Sphinx docs build, which mocks bing) does
# not break `import ioptics.algorithms.registry`; with bing present the registry
# seeds normally and the Tier-1 tests assert it.
_STANDARD_SEED = [('expb_pow', 'ExpB_Pow'), ('giop', 'GIOP')]


def _seed_standard():
    for name, label in _STANDARD_SEED:
        try:
            register(AlgorithmSpec.from_standard(name, label=label),
                     overwrite=True)
        except Exception:
            pass


_seed_standard()

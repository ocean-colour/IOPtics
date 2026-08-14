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
        hint = ''
        if name in dict(TURBID_SEED):
            hint = (f"; {name!r} is a turbid-water algorithm -- call "
                    "ioptics.algorithms.registry.register_turbid() first")
        raise KeyError(
            f"unknown algorithm {name!r}; available: {available()}{hint}")
    return REGISTRY[name]


def available():
    """Return the sorted list of registered algorithm names."""
    return sorted(REGISTRY)


# --- seed the in-tandem pair (expb_pow + giop) ------------------------------
# Seeding calls AlgorithmSpec.from_standard, which imports bing. It is wrapped
# so a mocked/absent bing (e.g. the Sphinx docs build, which mocks bing) does
# not break `import ioptics.algorithms.registry`; with bing present the registry
# seeds normally and the Tier-1 tests assert it.
_STANDARD_SEED = [('expb_pow', 'ExpB_Pow'), ('giop', 'GIOP'), ('gsm', 'GSM')]

#: Default optimizer evaluation budget for **every** seeded algorithm. At
#: scipy's own default, 30% of ``expb_pow``'s PANGAEA rows "crashed" with the
#: budget exhausted; at 40 000 the ``fit_failed`` residue is a fully-named
#: deterministic floor (underdetermined + non-positive-Rrs spectra), and only
#: 7 of the 442 recovered rows changed their verdict to ``ok`` — the budget
#: governs whether Levenberg-Marquardt returns, not how well the model fits
#: (``reports/pangaea_fits_report.md``; raised from None per JXP's Task-1
#: answers in ``claude_prompts/pangaea_fits.md``, 2026-08-10).
DEFAULT_MAXFEV = 40000


def _seed_standard():
    import dataclasses

    for name, label in _STANDARD_SEED:
        try:
            spec = AlgorithmSpec.from_standard(name, label=label)
            register(dataclasses.replace(spec, maxfev=DEFAULT_MAXFEV),
                     overwrite=True)
        except Exception:
            pass


_seed_standard()


# --- turbid-water algorithms: opt-in, not seeded ----------------------------
# BING's two-component backscattering models (a near-flat mineral term plus a
# steeper organic one) exist for turbid, mineral-dominated water, where a
# single decreasing power law cannot supply the shape the red end needs. They
# are deliberately **not** in _STANDARD_SEED: on open-ocean data they simply
# reproduce the single-power-law solution, so seeding them would dilute the
# cross-algorithm leaderboard with near-duplicate rows. A turbid sweep opts in
# by calling :func:`register_turbid` before resolving its algorithm names.
TURBID_SEED = [
    # (standard-factory name, leaderboard label)
    ('expb_pow2flat', 'ExpB_Pow2Flat'),   # 3 bb params, eta_min fixed at 0
    ('expb_pow2', 'ExpB_Pow2'),           # 4 bb params, eta_min free
    ('expb_powflex', 'ExpB_PowFlex'),     # 1-component control, beta may be <0
]

# Evaluation budget for the turbid specs. The two-component models need it:
# at scipy's default budget they fail to converge on a substantial fraction of
# spectra (5 of 8 and 6 of 8 clear L23 spectra in bing's own benchmark,
# dev/turbid_bbp), versus 8 of 8 with a raised budget. The standard seed now
# runs at the same budget (:data:`DEFAULT_MAXFEV`); the alias is kept because
# sweep drivers and tests reference it by this name.
TURBID_MAXFEV = DEFAULT_MAXFEV


def register_turbid(*, overwrite=True, maxfev=TURBID_MAXFEV):
    """Register the turbid-water algorithms and return their specs.

    Opt-in counterpart to the standard seed. Call this before running a
    sweep whose config names ``expb_pow2flat``, ``expb_pow2`` or
    ``expb_powflex``.

    ``expb_pow2flat`` is the one to reach for first: fixing the mineral
    exponent removes a degenerate direction that makes the 4-parameter
    ``expb_pow2`` badly conditioned under chi-squared. ``expb_powflex`` is
    the single-component control -- it widens the ordinary power law's
    slope prior without adding a component, so a fit that fails with it
    too implicates the functional form rather than the prior range.

    Parameters
    ----------
    overwrite : bool, optional
        Replace an existing registration of the same name (default True,
        so repeat calls are harmless).
    maxfev : int or None, optional
        Optimizer evaluation budget stamped onto each spec; see
        :data:`TURBID_MAXFEV` for why the default is not None.

    Returns
    -------
    dict
        ``{name: AlgorithmSpec}`` for the algorithms registered.
    """
    import dataclasses

    out = {}
    for name, label in TURBID_SEED:
        spec = AlgorithmSpec.from_standard(name, label=label)
        # Red-peaked water is these algorithms' purpose, so it is in scope:
        # run_algorithm's pre-fit out_of_scope guard must not decline it.
        spec = dataclasses.replace(spec, fits_turbid=True)
        if maxfev is not None:
            spec = dataclasses.replace(spec, maxfev=maxfev)
        register(spec, overwrite=overwrite)
        out[name] = spec
    return out

"""Name -> :class:`~ioptics.algorithms.spec.AlgorithmSpec` registry.

The growing catalog of algorithms IOPtics can run. **Seeded with ``expb_pow``
and ``giop`` side by side** (the design's "develop the two in tandem"), so the
comparison tooling is exercised on a genuine two-way contest from day one;
``register()`` adds more (e.g. ``gsm``) in one line.

``config`` resolves a sweep's algorithm *names* against this registry into
``AlgorithmSpec`` objects.

Three families are **opt-in** rather than seeded, because none belongs on a
cross-algorithm leaderboard beside the standard three by default: the
turbid-water models (:func:`register_turbid`), which merely reproduce the
single-power-law solution on open-ocean water; the RT-test variants
(:func:`register_rt_variants`), which are one algorithm under five different
forward models; and the direct (non-fitting) algorithms
(:func:`register_direct`), LS2's input ladder, whose rungs differ only in where
their inputs come from. A sweep that names them calls the corresponding
function before its names are resolved; :func:`get` says which one when the
lookup fails.
"""

from __future__ import annotations

from ioptics.algorithms.spec import AlgorithmSpec, DirectSpec

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
        elif name in RT_VARIANT_SEED:
            hint = (f"; {name!r} is an RT-test variant -- call "
                    "ioptics.algorithms.registry.register_rt_variants() first")
        elif name in DIRECT_SEED:
            hint = (f"; {name!r} is a direct (non-fitting) algorithm -- call "
                    "ioptics.algorithms.registry.register_direct() first")
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


# --- RT-test variants: opt-in, not seeded ------------------------------------
# The five-point ladder the RT tests walk (``claude_prompts/rt_tests.md``): one
# absorption/backscattering parameterization (``expb_pow``) held fixed while the
# **radiative transfer** is varied, so any difference between two rows is the RT
# and nothing else. Rung by rung:
#
#   1. robust_ztt, elastic          — the analytic robust forward model
#   2. robust_hybrid, elastic       — + the learned emulator correction
#   3. robust_hybrid + Raman        — the first inelastic process
#   4. ... + chlorophyll fluorescence
#   5. ... + CDOM fluorescence      — the full robust inelastic stack
#
# Every rung fits ``B_p`` (the phase-function / backscattering-ratio parameter
# the robust forward models take) as a free trailing parameter: it is an input
# the Gordon path never had, leaving it at a fixed 0.01 would hide the RT
# comparison behind one un-chosen constant, and its prior is bing's own linear
# uniform over [0.004, 0.05].
#
# Like :func:`register_turbid` these are **opt-in**. They are not alternative
# *algorithms* in the leaderboard's sense — they are the same algorithm under
# five different physics packages — so seeding them would put five near-clones
# of ``expb_pow`` on every cross-algorithm board. An RT sweep opts in by calling
# :func:`register_rt_variants` before resolving its algorithm names.
#
# ``{name: (label, rt-field overrides)}``, insertion order = ladder order.
# Everything not named here is inherited from ``expb_pow`` unchanged, so the
# table *is* the diff.
RT_VARIANT_SEED = {
    'expb_pow_ztt_el': ('ExpB_Pow ZTT elastic', {
        'rt_backend': 'robust_ztt'}),
    'expb_pow_hyb_el': ('ExpB_Pow hybrid elastic', {
        'rt_backend': 'robust_hybrid'}),
    'expb_pow_hyb_ram': ('ExpB_Pow hybrid +Raman', {
        'rt_backend': 'robust_hybrid', 'include_Raman': True}),
    'expb_pow_hyb_ramfl': ('ExpB_Pow hybrid +Raman +Chl-fl', {
        'rt_backend': 'robust_hybrid', 'include_Raman': True,
        'include_Chl_fl': True}),
    'expb_pow_hyb_ramflcdom': ('ExpB_Pow hybrid +Raman +Chl-fl +CDOM-fl', {
        'rt_backend': 'robust_hybrid', 'include_Raman': True,
        'include_Chl_fl': True, 'include_CDOM_fl': True}),
}

#: The standard combo every RT variant is derived from. Fixing the IOP
#: parameterization is the whole design: the variants differ in RT alone.
RT_VARIANT_BASE = 'expb_pow'

#: ΔBIC contest the RT sweeps are read through: the elastic hybrid against the
#: full inelastic stack — "does adding Raman + both fluorescences pay for its
#: parameters?". Both rungs use the same backend, so the contest is about the
#: inelastic physics rather than about the forward model.
RT_DBIC_PAIR = ('expb_pow_hyb_el', 'expb_pow_hyb_ramflcdom')


def register_rt_variants(*, overwrite=True, maxfev=DEFAULT_MAXFEV,
                         fit_method='mcmc'):
    """Register the five RT-test variants and return their specs.

    Opt-in counterpart to the standard seed, mirroring
    :func:`register_turbid`. Call this before running (or resolving the
    algorithm names of) a sweep whose config names any of
    :data:`RT_VARIANT_SEED`.

    Each spec is :meth:`AlgorithmSpec.from_standard`
    (:data:`RT_VARIANT_BASE`) with **only** the RT fields in
    :data:`RT_VARIANT_SEED` changed, plus ``fit_Bp=True`` on all five. The
    priors, the models (``ExpBricaud`` / ``Pow``), ``set_Sdg``/``sSdg``/
    ``beta`` and the MCMC settings are therefore identical across the ladder
    and identical to ``expb_pow`` — which is what makes a difference between
    two of these rows attributable to the radiative transfer.

    Fields deliberately left at their defaults, and why:

    ``phi_C = 0.02`` / ``double_gaussian = True``
        the fluorescence quantum yield and emission shape are held fixed so
        rung 4 differs from rung 3 by *whether* chlorophyll fluoresces, not
        by how much.
    ``cdom_fraction = 0.8``
        the ``a_cdom = 0.8 x a_dg`` proxy (a project decision, not a
        measurement — see :class:`ioptics.algorithms.spec.RTOptions`), so
        every rung-5 number inherits that assumption.
    ``variable_Gordon = True``
        inherited from ``expb_pow`` and **inert here**: the Gordon
        coefficients are an input to BING's own forward model, which no
        robust backend calls. It is left as-is rather than switched off so
        the field diff from ``expb_pow`` stays exactly the RT selection;
        flipping an inert flag would only add noise to the provenance
        digest.

    Parameters
    ----------
    overwrite : bool, optional
        Replace an existing registration of the same name (default True, so
        repeat calls are harmless — the same reason
        :func:`register_turbid` defaults that way).
    maxfev : int or None, optional
        Optimizer evaluation budget stamped onto each spec
        (:data:`DEFAULT_MAXFEV`, as for every seeded algorithm). It governs
        the χ² first pass only; the MCMC path ignores it.
    fit_method : str, optional
        Fit method on the spec (default ``'mcmc'`` — these variants exist to
        be sampled; the sweep still χ²-fits every record first, and a sweep
        config may override this per algorithm).

    Returns
    -------
    dict
        ``{name: AlgorithmSpec}`` for the five algorithms registered, in
        ladder order.
    """
    import dataclasses

    base = AlgorithmSpec.from_standard(RT_VARIANT_BASE)
    out = {}
    for name, (label, rt_fields) in RT_VARIANT_SEED.items():
        # fit_Bp is universal across the ladder (see the module comment), so it
        # is applied here rather than repeated in all five table rows.
        rt = dataclasses.replace(base.rt, fit_Bp=True, **rt_fields)
        spec = dataclasses.replace(base, name=name, label=label, rt=rt,
                                   fit_method=fit_method, maxfev=maxfev)
        register(spec, overwrite=overwrite)
        out[name] = spec
    return out


# --- direct algorithms: opt-in, not seeded -----------------------------------
# LS2 (Loisel et al. 2018) as a ladder that separates the algorithm's accuracy
# from the accuracy of its inputs (ls2 Q2): every rung runs the same published
# look-up tables, and two adjacent rungs differ in exactly one input.
#
#   ls2_i            Kd from the record    + b_p from truth     -- LS2 alone
#   ls2_ii           Kd from the record    + b_p from OC4v4 Chl -- + the Chl chain
#   ls2_iii          Kd from the PACE NN   + b_p from OC4v4 Chl -- satellite mode
#   ls2_iii_modis    Kd from the MODIS NN  + b_p from OC4v4 Chl -- 2nd Kd network
#   ls2_i_effmuw     ls2_i at an effective muw from the RT's own light field --
#                    the Q9 diagnostic: is the a bias illumination bookkeeping?
#   ls2_i_kdnoise    ls2_i with 10% multiplicative Kd noise -- the Q15
#                    sensitivity rung: how much does LS2 lose per unit of Kd
#                    error? (The level is a placeholder pending ls2 Q33.)
#
# Rung (iii) uses the authors' PACE network, with their current MODIS network
# (v1.3) as the documented alternative run beside it (ls2 Q27, Q30).
#
# The Raman correction is on in every seed. An L23 X=1 sweep, whose truth is
# elastic, switches it off per algorithm with ``raman: false`` (ls2 Q4).
#
# ``{name: (label, DirectSpec field overrides)}``, insertion order = ladder
# order; everything not named takes the DirectSpec default, so the table *is*
# the diff between rungs.
DIRECT_SEED = {
    'ls2_i': ('LS2 (i) Kd record, b_p truth', {
        'kd_source': 'record', 'bp_source': 'truth'}),
    'ls2_ii': ('LS2 (ii) Kd record, b_p OC4v4', {
        'kd_source': 'record', 'bp_source': 'oc4v4'}),
    'ls2_iii': ('LS2 (iii) Kd PACE-NN, b_p OC4v4', {
        'kd_source': 'nn:PACE_v2.3', 'bp_source': 'oc4v4'}),
    'ls2_iii_modis': ('LS2 (iii) Kd MODIS-NN v1.3, b_p OC4v4', {
        'kd_source': 'nn:MODIS_v1.3', 'bp_source': 'oc4v4'}),
    'ls2_i_effmuw': ('LS2 (i) effective muw (diagnostic)', {
        'kd_source': 'record', 'bp_source': 'truth',
        'muw_mode': 'effective'}),
    'ls2_i_kdnoise': ('LS2 (i) + 10% Kd noise (sensitivity)', {
        'kd_source': 'record', 'bp_source': 'truth', 'kd_noise': 0.10}),
}


def register_direct(*, overwrite=True):
    """Register the direct (non-fitting) algorithms and return their specs.

    Opt-in counterpart to the standard seed, mirroring
    :func:`register_turbid` and :func:`register_rt_variants`. Call this before
    running (or resolving the algorithm names of) a sweep whose config names
    any of :data:`DIRECT_SEED`.

    Registration needs neither BING nor ocpy: a :class:`DirectSpec` is pure
    configuration, and its driver is imported only when a record is run
    (:func:`ioptics.run.run_direct`).

    Parameters
    ----------
    overwrite : bool, optional
        Replace an existing registration of the same name (default True, so
        repeat calls are harmless).

    Returns
    -------
    dict
        ``{name: DirectSpec}`` for the algorithms registered, in ladder order.
    """
    out = {}
    for name, (label, fields) in DIRECT_SEED.items():
        spec = DirectSpec(name=name, label=label, **fields)
        register(spec, overwrite=overwrite)
        out[name] = spec
    return out

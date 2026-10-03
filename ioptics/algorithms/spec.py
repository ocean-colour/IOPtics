"""``AlgorithmSpec`` — declarative, serializable mirror of a BING parameter set.

An IOPtics "algorithm" is a configuration, not code: a choice of a_nw / bb_nw
models, their priors, the RT toggles, the fit method, and (for provenance) the
noise model. :class:`AlgorithmSpec` is a plain dataclass mirror of exactly the
fields BING's ``parameters.p_ntuple`` namedtuple carries, so an algorithm
round-trips losslessly to a BING ``p`` and back:

- :meth:`AlgorithmSpec.to_bing_p` emits the BING parameter namedtuple
  (``bing.parameters.p_ntuple.gen``).
- :meth:`AlgorithmSpec.from_standard` seeds a spec from a shipped combo
  (``bing.parameters.standard.<name>``) — the lossless inverse for those combos.
- :meth:`AlgorithmSpec.build_models` builds the ``[a_nw, bb_nw]`` model list
  (on the record's native grid) that :mod:`ioptics.run` fits.

:class:`DirectSpec` is the second spec type (ls2 Q1): a **direct**, non-fitting
algorithm such as LS2, which turns ``Rrs`` plus side inputs into IOPs in closed
form.  It carries none of the BING fields; :func:`is_direct` is how the run,
provenance and report code tell the two apart.

BING is imported lazily inside the methods so importing this module stays cheap
(and the docs build, which mocks bing, still imports it).

.. note::

   :meth:`build_models` constructs BING models, and building any BING model
   loads the L23 ``Hydrolight400.nc`` dataset for pure-water backscattering — so
   it requires the L23 data tree. :meth:`to_bing_p` / :meth:`from_standard` are
   model-free (data-free).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RTOptions:
    """Radiative-transfer options — the full BING ``rt_dict`` surface.

    The twelve keys ``bing.rt.defs.rt_dict_from_p`` reads: the seven legacy
    Gordon-path toggles, plus the five that select and configure the
    ``robust.rt`` backends (BING's ``rob_rt``/``rob_cdom`` integration). Every
    field here maps 1:1 through :meth:`AlgorithmSpec.to_bing_p`, so
    ``rt_dict_from_p(spec.to_bing_p())`` reproduces this object exactly.

    All five new fields default to the values that reproduce the pre-existing
    Gordon behaviour, so an untouched spec is byte-for-byte the algorithm it
    was.

    Parameters
    ----------
    variable_Gordon : bool
        Use wavelength-dependent Gordon coefficients (``G1``/``G2``).
    variable_Gordon_G0 : bool
        Also apply the constant offset ``G0(lambda)``.
    variable_Gordon_bbp : bool
        Also apply the ``bbp``-dependent Gordon coefficients.
    include_Raman : bool
        Include the Raman-scattering term (L23 ``X=4``; elastic-only at
        ``X=1``).
    include_Chl_fl : bool
        Include chlorophyll fluorescence. On the ``'gordon'`` backend this
        additionally needs the downwelling irradiance ``Ed`` seeded on the
        a-model, which :func:`ioptics.run._prepare` takes from
        ``correct_atmosphere``; the robust backends carry their own packaged
        ``Ed`` table and need no such wiring.
    phi_C : float
        Fluorescence quantum yield.
    double_gaussian : bool
        Use the double-Gaussian fluorescence emission model.
    rt_backend : str
        Which forward model turns ``(a, bb)`` into ``Rrs``: ``'gordon'``
        (default — BING's own Gordon 1988 relation, unchanged), or one of
        retrieve-or-bust's ``'robust_ztt'`` / ``'robust_hybrid'`` /
        ``'robust_baseline'``. Every ``robust_*`` value **requires** an
        observation geometry (:func:`ioptics.run.resolve_geometry`); the solar
        zenith is never silently defaulted. ``'robust_hybrid'`` is additionally
        valid only over 350–750 nm. See ``bing.rt.defs.RT_BACKENDS``.
    fit_Bp : bool
        Make ``B_p`` — the backscattering-ratio / phase-function parameter the
        robust forward models take — a **free** parameter, appended as the
        trailing element of the fitted vector (and of every saved chain).
        Illegal with ``rt_backend='gordon'``, which has no phase-function
        input. Its prior is a linear uniform over ``[0.004, 0.05]``
        (``bing.rt.defs.BP_PRIOR_PMIN``/``BP_PRIOR_PMAX``).
    Bp_value : float
        Fixed value of ``B_p`` when ``fit_Bp`` is ``False``, and the walker
        seed when it is ``True``. Default 0.01.
    include_CDOM_fl : bool
        Include robust's CDOM-fluorescence term (the Hawes et al. 1992 kernel,
        ``robust.rt.cdom_fl``) as a third inelastic process. Robust backends
        only, and not ``'robust_baseline'`` (elastic-only); it also requires an
        a-model with a separable ``a_dg`` component (the ExpBricaud family,
        GIOP, GSM, ExpNMF).
    cdom_fraction : float
        The **fixed-fraction CDOM proxy**::

            a_cdom(lambda) = cdom_fraction * a_dg(lambda)

        The Hawes kernel's emission source term is *pure CDOM* absorption, but
        every BING a-model with a separable exponential term lumps dissolved
        and detrital absorption together into one ``a_dg`` — there is no free
        parameter that splits them. The default 0.8 is therefore a **project
        decision** (JXP, 2026-09-05; ``claude_prompts/rt_tests.md`` Q32), *not*
        a measured or retrieved quantity, and any result that depends on the
        CDOM-fluorescence term inherits that assumption. Consulted only when
        ``include_CDOM_fl`` is ``True``; carried (and ignored) otherwise.
    """

    variable_Gordon:     bool = True
    variable_Gordon_G0:  bool = False
    variable_Gordon_bbp: bool = False
    include_Raman:       bool = False     # elastic-only first pass (L23 X=1)
    include_Chl_fl:      bool = False     # turned on with L23 X=4
    phi_C:               float = 0.02
    double_gaussian:     bool = True
    # --- robust.rt backend selection (bing rob_rt / rob_cdom) ---------------
    rt_backend:          str = 'gordon'
    fit_Bp:              bool = False
    Bp_value:            float = 0.01
    include_CDOM_fl:     bool = False
    cdom_fraction:       float = 0.8      # a_cdom = 0.8 x a_dg (proxy, Q32)


@dataclass
class MCMCOptions:
    """MCMC chain settings (used by the Stage-3 MCMC path)."""

    nsteps: int = 40000
    nburn:  int = 1000
    nMC:    int | None = None


#: Spec fields a sweep config may override per algorithm.
#:
#: Deliberately a **whitelist**, so a typo is an error rather than a silently
#: ignored request. Excluded and why:
#:
#: * ``name`` / ``label`` — they *identify* the algorithm; renaming it in a sweep
#:   config would make two sweeps' rows uncomparable for no benefit.
#: * ``noise_model`` — sweep-level, and :func:`ioptics.config.load` already rejects
#:   it per algorithm ("compare two noise models with two separate sweeps").
#: * ``fit_method`` — carried on :class:`~ioptics.config.AlgorithmConfig` itself,
#:   since the runner needs it before the spec is resolved.
#:
#: ``anw_model``/``bbnw_model`` *are* overridable: swapping the model family is the
#: main reason to override anything, and the digest records that it happened.
OVERRIDABLE_FIELDS = frozenset({
    'anw_model', 'bbnw_model', 'apriors', 'bpriors', 'othera_priors',
    'rt', 'set_Sdg', 'sSdg', 'beta', 'mcmc', 'maxfev', 'fits_turbid',
})

#: Overridable fields that are themselves dataclasses, so a partial mapping merges
#: into the existing options rather than replacing them wholesale.
_NESTED_FIELDS = frozenset({'rt', 'mcmc'})


@dataclass
class AlgorithmSpec:
    """Declarative description of one retrieval algorithm.

    Parameters
    ----------
    name : str
        Registry key (e.g. ``'expb_pow'``).
    label : str
        Human-readable label (e.g. ``'ExpB_Pow'``).
    anw_model, bbnw_model : str
        BING a_nw / bb_nw model names (e.g. ``'ExpBricaud'`` / ``'Pow'``).
    apriors, bpriors : list of dict
        BING prior dicts, one per a / bb model parameter.
    othera_priors : list of dict or None
        Extra priors appended to the a-model (``None`` for most combos).
    rt : RTOptions
        Radiative-transfer toggles.
    set_Sdg : bool
        Whether ``Sdg`` is fixed.
    sSdg : float
        The fixed/used ``Sdg`` slope.
    beta : float or None
        Fixed bb slope, if any.
    fit_method : str
        ``'chisq'`` (default) | ``'mcmc'``.
    mcmc : MCMCOptions
        MCMC settings.
    maxfev : int or None
        Optimizer evaluation budget handed to ``bing.fitting.chisq_fit.fit``
        for the ``'chisq'`` method. ``None`` leaves scipy's own
        default in place. It governs *whether* the fit converges, not how
        well the model can fit, and parameter-rich models need it -- the
        two-component turbid backscattering models fail to converge on a
        substantial fraction of spectra at the default budget. Ignored by
        the MCMC path, which seeds from :func:`ioptics.run.initial_guess`
        rather than a least-squares pre-fit. The registry seeds every
        algorithm at :data:`ioptics.algorithms.registry.DEFAULT_MAXFEV`.
    fits_turbid : bool
        Whether red-peaked (turbid) spectra are **in scope** for this
        algorithm. ``False`` (default, and the right value for the
        open-ocean parameterisations): :func:`ioptics.run.run_algorithm`
        declines a record whose observed Rrs peaks redward of
        :data:`ioptics.records.RED_PEAK_NM` *before* fitting, returning an
        ``out_of_scope`` result — "we declined to fit this" rather than "we
        fitted it and it failed" (the PANGAEA investigation's Q&A decision,
        2026-08-10). The turbid variants set ``True`` — fitting that water
        is their purpose — and a diagnostic script can override it to
        force-fit red-peaked spectra with an open-ocean model.
    """

    name:          str
    label:         str
    anw_model:     str
    bbnw_model:    str
    apriors:       list
    bpriors:       list
    othera_priors: list | None = None
    rt:            RTOptions = field(default_factory=RTOptions)
    set_Sdg:       bool = False
    sSdg:          float = 0.002
    beta:          float | None = None
    fit_method:    str = 'chisq'
    mcmc:          MCMCOptions = field(default_factory=MCMCOptions)
    # No ``noise_model`` here. It used to sit on the spec as a "descriptive only"
    # tag defaulting to 'pace', which produced a three-way disagreement on the one
    # real sweep: the algorithm blocks said ``pace``, the sweep config said
    # ``insitu``, and the uncertainty actually attached was
    # ``insitu+imputed:0.1``. Noise is a property of the *record*, applied
    # sweep-wide by ``prep``, and is now persisted per record on
    # ``results_scalar`` (``noise_model`` / ``noise_seed`` / ``noise_imputed``).
    maxfev:        int | None = None
    fits_turbid:   bool = False

    # --- BING interop -------------------------------------------------
    def to_bing_p(self, **overrides):
        """Build the BING parameter namedtuple via ``p_ntuple.gen``.

        Maps the spec fields onto the ``def_dict`` keys (``model_names``,
        ``apriors``/``bpriors``/``othera_priors``, the RT flags,
        ``set_Sdg``/``sSdg``/``beta``, ``nsteps``/``nburn``/``nMC``).
        ``overrides`` (e.g. ``wv_min=``, ``wv_max=``, ``satellite=``) pass
        through to ``gen``.

        All twelve :class:`RTOptions` fields are emitted, so
        ``bing.rt.defs.rt_dict_from_p`` on the result reproduces the spec's RT
        configuration exactly. ``p_ntuple.gen`` builds its namedtuple from the
        merged key set, so the five backend fields simply become extra
        attributes of ``p`` — they are absent from BING's ``def_dict``, which is
        why ``rt_dict_from_p`` reads them with defaults.
        """
        from bing.parameters import p_ntuple

        params = dict(
            model_names=[self.anw_model, self.bbnw_model],
            apriors=self.apriors,
            bpriors=self.bpriors,
            othera_priors=self.othera_priors,
            variable_Gordon=self.rt.variable_Gordon,
            variable_Gordon_G0=self.rt.variable_Gordon_G0,
            variable_Gordon_bbp=self.rt.variable_Gordon_bbp,
            include_Raman=self.rt.include_Raman,
            include_Chl_fl=self.rt.include_Chl_fl,
            phi_C=self.rt.phi_C,
            double_gaussian=self.rt.double_gaussian,
            rt_backend=self.rt.rt_backend,
            fit_Bp=self.rt.fit_Bp,
            Bp_value=self.rt.Bp_value,
            include_CDOM_fl=self.rt.include_CDOM_fl,
            cdom_fraction=self.rt.cdom_fraction,
            set_Sdg=self.set_Sdg,
            sSdg=self.sSdg,
            beta=self.beta,
            nsteps=self.mcmc.nsteps,
            nburn=self.mcmc.nburn,
            nMC=self.mcmc.nMC,
        )
        params.update(overrides)
        return p_ntuple.gen(**params)

    @classmethod
    def from_standard(cls, name, *, label=None, **overrides):
        """Seed a spec from ``bing.parameters.standard.<name>()``.

        Reads back the model names, priors, RT flags, and MCMC settings from the
        shipped combo (applying any ``overrides`` the factory accepts). The
        lossless inverse of :meth:`to_bing_p` for BING's shipped combos.

        The five backend fields are read with :func:`getattr` defaults: BING's
        shipped combos are built from ``p_ntuple.def_dict``, which does not
        carry them, so a standard combo always seeds the Gordon configuration.
        """
        from bing.parameters import standard

        p = getattr(standard, name)(**overrides)
        anw_model, bbnw_model = p.model_names
        _rt_defaults = RTOptions()
        rt = RTOptions(
            variable_Gordon=p.variable_Gordon,
            variable_Gordon_G0=p.variable_Gordon_G0,
            variable_Gordon_bbp=p.variable_Gordon_bbp,
            include_Raman=p.include_Raman,
            include_Chl_fl=p.include_Chl_fl,
            phi_C=p.phi_C,
            double_gaussian=p.double_gaussian,
            rt_backend=getattr(p, 'rt_backend', _rt_defaults.rt_backend),
            fit_Bp=getattr(p, 'fit_Bp', _rt_defaults.fit_Bp),
            Bp_value=getattr(p, 'Bp_value', _rt_defaults.Bp_value),
            include_CDOM_fl=getattr(p, 'include_CDOM_fl',
                                    _rt_defaults.include_CDOM_fl),
            cdom_fraction=getattr(p, 'cdom_fraction',
                                  _rt_defaults.cdom_fraction),
        )
        mcmc = MCMCOptions(nsteps=p.nsteps, nburn=p.nburn, nMC=p.nMC)
        return cls(
            name=name,
            label=label or name,
            anw_model=anw_model,
            bbnw_model=bbnw_model,
            apriors=p.apriors,
            bpriors=p.bpriors,
            othera_priors=p.othera_priors,
            rt=rt,
            set_Sdg=bool(p.set_Sdg),
            sSdg=p.sSdg if p.sSdg is not None else 0.002,
            beta=p.beta,
            mcmc=mcmc,
        )

    def with_overrides(self, overrides):
        """A **copy** of this spec with ``overrides`` applied, or a clear error.

        ``AlgorithmConfig.overrides`` was parsed and then read by nobody: a sweep
        config could ask for ``maxfev: 40000`` or a different prior and the run would
        silently use the registry default, so the provenance file and the fit
        disagreed. This is the "apply" half of Stage 7 Task 9's *apply or reject* —
        anything outside :data:`OVERRIDABLE_FIELDS` raises rather than being ignored.

        ``rt`` and ``mcmc`` accept a **partial mapping**, merged into the existing
        options (``{'mcmc': {'nsteps': 100}}`` leaves ``nburn`` alone). Overriding
        anything here yields a genuinely different algorithm, which is why the
        provenance digest is taken *after* this is applied — two sweeps that
        overrode differently must not pool as the same algorithm.
        """
        import copy

        if not overrides:
            return self
        unknown = [k for k in overrides if k not in OVERRIDABLE_FIELDS]
        if unknown:
            raise ValueError(
                f"{self.name}: cannot override {sorted(unknown)} — overridable "
                f"fields are {sorted(OVERRIDABLE_FIELDS)}. 'name'/'label' identify "
                f"the algorithm, 'noise_model' is sweep-level, and anything else is "
                f"not a field of AlgorithmSpec (check for a typo: an ignored "
                f"override is how a sweep silently runs a different configuration "
                f"from the one its config asked for)")
        out = copy.deepcopy(self)
        for key, value in overrides.items():
            current = getattr(out, key)
            if key in _NESTED_FIELDS:
                if not isinstance(value, dict):
                    raise ValueError(
                        f"{self.name}: '{key}' override must be a mapping of "
                        f"{key} options, got {type(value).__name__}")
                allowed = set(current.__dataclass_fields__)
                bad = [k for k in value if k not in allowed]
                if bad:
                    raise ValueError(
                        f"{self.name}: unknown {key} option(s) {sorted(bad)}; "
                        f"allowed: {sorted(allowed)}")
                for k, v in value.items():
                    setattr(current, k, v)
            else:
                setattr(out, key, value)
        return out

    def build_models(self, wave):
        """Build the ``[a_nw, bb_nw]`` BING model list on ``wave``.

        Follows BING's canonical pattern (cf. ``bing.fitting.l23.prep_one_l23``):
        ``models.utils.init`` then ``priors.set_standard_priors`` then append any
        ``othera_priors``. **Requires the L23 data tree** (building a bb_nw model
        loads ``Hydrolight400.nc`` for pure-water backscattering).
        """
        import numpy as np
        from bing.models import utils as model_utils
        from bing.priors import priors as bing_priors

        wave = np.asarray(wave, dtype=float)
        models = model_utils.init([self.anw_model, self.bbnw_model], wave)
        p = self.to_bing_p(wv_min=float(wave.min()), wv_max=float(wave.max()))
        bing_priors.set_standard_priors(models, p)
        if self.othera_priors is not None:
            for prior_dict in self.othera_priors:
                models[0].priors.add_prior(prior_dict)
        return models


# --- direct (non-fitting) algorithms -----------------------------------------

#: Fields a sweep config may override on a :class:`DirectSpec`.
#:
#: A whitelist for the same reason as :data:`OVERRIDABLE_FIELDS`: a typo must be
#: an error, never a silently ignored request.  ``name``/``label`` identify the
#: algorithm, ``method`` selects which driver runs it (changing it is a
#: different algorithm, not an override), and ``fit_method`` is always
#: ``'direct'``.
DIRECT_OVERRIDABLE_FIELDS = frozenset({
    'kd_source', 'bp_source', 'raman', 'muw_mode', 'kd_noise', 'tol',
    'max_iter', 'fits_turbid', 'outputs',
})

#: ``kd_source`` values: the ``Kd`` carried on the record (for L23 the
#: ``<Kd>_1`` derived from its own profile, for PANGAEA the measured value), or
#: one of ocpy's neural networks (``ocpy.ls2.kd_nn.NETWORKS``) applied to the
#: record's Rrs.
KD_SOURCES = ('record', 'nn:MODIS_v1.1', 'nn:MODIS_v1.3', 'nn:PACE_v2.3')

#: ``bp_source`` values: the particulate scattering coefficient from the
#: record's truth (input rung i), or ``b_p`` from chlorophyll via OC4v4 and
#: ``ocpy.iop.scattering.bp_from_chla`` (rungs ii and iii).
BP_SOURCES = ('truth', 'oc4v4')

#: ``muw_mode`` values: ``'snell'`` refracts the record's solar zenith angle
#: (the published algorithm); ``'effective'`` uses an effective cosine derived
#: from the radiative transfer's own light field -- the diagnostic rung of
#: ls2 Q9, which asks whether LS2's ``a`` bias is illumination bookkeeping.
MUW_MODES = ('snell', 'effective')

#: Components a direct algorithm may be asked to return.  LS2 produces totals
#: and their non-water parts only; it has no ``a_ph``/``a_dg`` decomposition,
#: and that absence is reported, not hidden (ls2 Q5/Q25).
DIRECT_OUTPUTS = ('a', 'a_nw', 'bb', 'bb_p')


@dataclass
class DirectSpec:
    """Declarative description of a **direct** (non-fitting) algorithm.

    The second spec type beside :class:`AlgorithmSpec` (ls2 Q1).  A direct
    algorithm computes IOPs from ``Rrs`` and side inputs in closed form: there
    is no fit, no likelihood, no posterior and no model ``Rrs``, so none of
    the BING machinery (priors, RT toggles, MCMC settings, ``build_models``)
    applies, and none of it is carried.  ``fit_method`` is the honest label
    ``'direct'``; the contest code pools direct rows with each fitted pool
    (ls2 Q13/Q23) rather than this spec pretending to be a χ² fit.

    The configuration fields are LS2's input ladder (ls2 Q2/Q4/Q9/Q15): where
    ``Kd`` comes from, where ``b_p`` comes from, whether the Raman correction
    runs, and which ``muw`` the look-up tables are entered at.

    Parameters
    ----------
    name : str
        Registry key (e.g. ``'ls2_i'``).
    label : str
        Human-readable label.
    method : str
        Which direct driver computes the result (``'ls2'``); see
        :func:`ioptics.run.run_direct`.
    fit_method : str
        Always ``'direct'``.  Present so code that reads ``spec.fit_method``
        works on either spec type.
    kd_source : str
        One of :data:`KD_SOURCES`.
    bp_source : str
        One of :data:`BP_SOURCES`.
    raman : bool
        Apply LS2's Raman correction ``kappa``.  Off for L23 ``X=1`` (elastic
        truth), on for ``X=2`` and ``X=4`` (ls2 Q4).
    muw_mode : str
        One of :data:`MUW_MODES`.
    kd_noise : float or None
        Relative 1-sigma noise added to ``Kd`` -- the Kd-noise sensitivity
        rung of ls2 Q15.  ``None`` (default): no Kd noise.
    tol, max_iter : float, int
        Raman iteration criterion, ``|d(bb/a)|/(bb/a) < tol`` with a cap of
        ``max_iter`` passes (ls2 Q14/Q22; ``ocpy.ls2.ls2_main.ls2_invert``).
    fits_turbid : bool
        Whether red-peaked spectra are in scope; the same pre-fit
        ``out_of_scope`` guard as :attr:`AlgorithmSpec.fits_turbid`.
    outputs : tuple of str
        Components the algorithm returns, a subset of :data:`DIRECT_OUTPUTS`.
        The result's ``ok`` status requires every one of them to be finite and
        positive at every wavelength (ls2 Q5).
    """

    name:        str
    label:       str
    method:      str = 'ls2'
    fit_method:  str = 'direct'
    kd_source:   str = 'record'
    bp_source:   str = 'truth'
    raman:       bool = True
    muw_mode:    str = 'snell'
    kd_noise:    float | None = None
    tol:         float = 1.0e-3
    max_iter:    int = 10
    fits_turbid: bool = False
    outputs:     tuple = DIRECT_OUTPUTS

    def __post_init__(self):
        self.outputs = tuple(self.outputs)
        self.validate()

    def validate(self):
        """Raise :class:`ValueError` on any field outside its allowed values."""
        if self.fit_method != 'direct':
            raise ValueError(f"{self.name}: a DirectSpec's fit_method is always "
                             f"'direct', got {self.fit_method!r}")
        for field_name, value, allowed in (
                ('kd_source', self.kd_source, KD_SOURCES),
                ('bp_source', self.bp_source, BP_SOURCES),
                ('muw_mode', self.muw_mode, MUW_MODES)):
            if value not in allowed:
                raise ValueError(f"{self.name}: {field_name} must be one of "
                                 f"{allowed}, got {value!r}")
        bad = [o for o in self.outputs if o not in DIRECT_OUTPUTS]
        if bad or not self.outputs:
            raise ValueError(f"{self.name}: outputs must be a non-empty subset "
                             f"of {DIRECT_OUTPUTS}, got {self.outputs!r}")
        if self.kd_noise is not None and not self.kd_noise >= 0:
            raise ValueError(f"{self.name}: kd_noise must be None or >= 0, "
                             f"got {self.kd_noise!r}")
        if not (self.tol > 0 and int(self.max_iter) >= 0):
            raise ValueError(f"{self.name}: need tol > 0 and max_iter >= 0")

    def with_overrides(self, overrides):
        """A **copy** with ``overrides`` applied, or a clear error.

        Mirrors :meth:`AlgorithmSpec.with_overrides`: anything outside
        :data:`DIRECT_OVERRIDABLE_FIELDS` raises -- including every BING field
        (``apriors``, ``rt``, ``mcmc``, ...), which a direct algorithm does not
        have -- and the result is re-validated, so an override cannot smuggle in
        a value the constructor would reject.
        """
        import dataclasses

        if not overrides:
            return self
        unknown = [k for k in overrides if k not in DIRECT_OVERRIDABLE_FIELDS]
        if unknown:
            raise ValueError(
                f"{self.name}: cannot override {sorted(unknown)} on a direct "
                f"algorithm -- overridable fields are "
                f"{sorted(DIRECT_OVERRIDABLE_FIELDS)}. A DirectSpec has no "
                f"priors, RT toggles or MCMC settings, and 'name'/'label'/"
                f"'method' identify the algorithm")
        return dataclasses.replace(self, **overrides)


def is_direct(spec):
    """``True`` for a :class:`DirectSpec`, the one test every branch point uses."""
    return isinstance(spec, DirectSpec)

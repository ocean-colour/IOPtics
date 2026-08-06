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
    """Radiative-transfer toggles (mirror of the ``p_ntuple`` RT fields)."""

    variable_Gordon:     bool = True
    variable_Gordon_G0:  bool = False
    variable_Gordon_bbp: bool = False
    include_Raman:       bool = False     # elastic-only first pass (L23 X=1)
    include_Chl_fl:      bool = False     # turned on with L23 X=4
    phi_C:               float = 0.02
    double_gaussian:     bool = True


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
    'rt', 'set_Sdg', 'sSdg', 'beta', 'mcmc', 'maxfev',
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
        for the ``'chisq'`` method. ``None`` (default) leaves scipy's own
        default in place. It governs *whether* the fit converges, not how
        well the model can fit, and parameter-rich models need it -- the
        two-component turbid backscattering models fail to converge on a
        substantial fraction of spectra at the default budget. Ignored by
        the MCMC path, which seeds from :func:`ioptics.run.initial_guess`
        rather than a least-squares pre-fit.
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

    # --- BING interop -------------------------------------------------
    def to_bing_p(self, **overrides):
        """Build the BING parameter namedtuple via ``p_ntuple.gen``.

        Maps the spec fields onto the ``def_dict`` keys (``model_names``,
        ``apriors``/``bpriors``/``othera_priors``, the RT flags,
        ``set_Sdg``/``sSdg``/``beta``, ``nsteps``/``nburn``/``nMC``).
        ``overrides`` (e.g. ``wv_min=``, ``wv_max=``, ``satellite=``) pass
        through to ``gen``.
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
        """
        from bing.parameters import standard

        p = getattr(standard, name)(**overrides)
        anw_model, bbnw_model = p.model_names
        rt = RTOptions(
            variable_Gordon=p.variable_Gordon,
            variable_Gordon_G0=p.variable_Gordon_G0,
            variable_Gordon_bbp=p.variable_Gordon_bbp,
            include_Raman=p.include_Raman,
            include_Chl_fl=p.include_Chl_fl,
            phi_C=p.phi_C,
            double_gaussian=p.double_gaussian,
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

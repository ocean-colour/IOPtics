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
    noise_model : str
        Provenance tag for the (sweep-level) noise model. The fit always uses
        ``record.varRrs``; this field is descriptive only.
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
    noise_model:   str = 'pace'

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

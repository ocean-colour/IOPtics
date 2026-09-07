"""Tier-1 tests for ``ioptics.algorithms.spec`` (data-free).

Round-trips ``AlgorithmSpec`` against BING's shipped combos
(``bing.parameters.standard.{expb_pow,giop}``) and checks parameter counts. No
models are built here (``build_models`` needs the L23 data tree), so these are
data-independent — but they do import the *released* ``bing.parameters.standard``
(see the Stage-2 prompt's CI caveat).
"""

from bing.parameters import standard

from ioptics.algorithms.spec import AlgorithmSpec, MCMCOptions, RTOptions


def test_from_standard_expb_pow():
    spec = AlgorithmSpec.from_standard('expb_pow', label='ExpB_Pow')
    assert spec.name == 'expb_pow'
    assert spec.label == 'ExpB_Pow'
    assert spec.anw_model == 'ExpBricaud'
    assert spec.bbnw_model == 'Pow'
    assert len(spec.apriors) == 3       # Adg, Sdg, Aph
    assert len(spec.bpriors) == 2       # Bnw, beta
    assert len(spec.apriors) + len(spec.bpriors) == 5     # free params k
    assert spec.set_Sdg is False
    assert spec.sSdg == 0.002
    assert spec.fit_method == 'chisq'   # IOPtics default
    assert spec.rt.variable_Gordon is True
    assert spec.rt.include_Raman is False


def test_from_standard_giop():
    spec = AlgorithmSpec.from_standard('giop', label='GIOP')
    assert spec.anw_model == 'GIOP'
    assert spec.bbnw_model == 'Lee'
    assert len(spec.apriors) == 2       # Adg, Aph
    assert len(spec.bpriors) == 1       # Bnw
    assert len(spec.apriors) + len(spec.bpriors) == 3     # free params k


def test_from_standard_gsm():
    spec = AlgorithmSpec.from_standard('gsm', label='GSM')
    assert spec.name == 'gsm'
    assert spec.label == 'GSM'
    assert spec.anw_model == 'GSM'
    assert spec.bbnw_model == 'GSM'
    assert len(spec.apriors) == 2       # Adg, Aph
    assert len(spec.bpriors) == 1       # Bbp
    assert len(spec.apriors) + len(spec.bpriors) == 3     # free params k
    assert spec.othera_priors is None
    assert spec.fit_method == 'chisq'   # IOPtics default (gsm is chisq-first)


def test_label_defaults_to_name():
    spec = AlgorithmSpec.from_standard('giop')
    assert spec.label == 'giop'


def test_to_bing_p_round_trips_priors_and_models():
    # from_standard -> to_bing_p reproduces the shipped combo's key fields.
    for name in ('expb_pow', 'giop'):
        ref = getattr(standard, name)()
        p = AlgorithmSpec.from_standard(name).to_bing_p()
        assert p.model_names == ref.model_names
        assert p.apriors == ref.apriors          # verbatim priors
        assert p.bpriors == ref.bpriors
        assert p.set_Sdg == ref.set_Sdg
        assert p.sSdg == ref.sSdg
        assert p.variable_Gordon == ref.variable_Gordon
        assert p.include_Raman == ref.include_Raman
        assert p.nsteps == ref.nsteps and p.nburn == ref.nburn


def test_to_bing_p_overrides_pass_through():
    spec = AlgorithmSpec.from_standard('expb_pow')
    p = spec.to_bing_p(wv_min=410.0, wv_max=690.0)
    assert p.wv_min == 410.0 and p.wv_max == 690.0


def test_priors_match_standard_verbatim():
    spec = AlgorithmSpec.from_standard('expb_pow')
    ref = standard.expb_pow()
    # the Sdg prior is the uniform[0.01, 0.02] one, mirrored exactly
    assert spec.apriors[1] == dict(flavor='uniform', pmin=0.01, pmax=0.02)
    assert spec.apriors == ref.apriors
    assert spec.bpriors == ref.bpriors


def test_rt_and_mcmc_defaults():
    rt = RTOptions()
    assert (rt.variable_Gordon, rt.include_Raman, rt.double_gaussian) == (True, False, True)
    assert rt.phi_C == 0.02
    mc = MCMCOptions()
    assert (mc.nsteps, mc.nburn, mc.nMC) == (40000, 1000, None)


# --------------------------------------------------------------------
# RTOptions: the full 12-key rt_dict surface (rt-tests, 2026-09-05)
# --------------------------------------------------------------------
#: What ``bing.rt.defs.rt_dict_from_p`` must produce for an untouched spec.
#: Hard-coded on purpose: this is the legacy Gordon configuration, and the
#: whole point of widening ``RTOptions`` is that it does not move. A change to
#: any value here is a change to every pre-existing algorithm.
LEGACY_GORDON_RT_DICT = {
    'variable_Gordon': True,
    'variable_Gordon_G0': False,
    'variable_Gordon_bbp': False,
    'include_Raman': False,
    'include_Chl_fl': False,
    'phi_C': 0.02,
    'double_gaussian': True,
    'rt_backend': 'gordon',
    'fit_Bp': False,
    'Bp_value': 0.01,
    'include_CDOM_fl': False,
    'cdom_fraction': 0.8,
}


def test_rt_backend_defaults_are_the_legacy_gordon_configuration():
    rt = RTOptions()
    assert rt.rt_backend == 'gordon'
    assert rt.fit_Bp is False
    assert rt.Bp_value == 0.01
    assert rt.include_CDOM_fl is False
    assert rt.cdom_fraction == 0.8


def test_to_bing_p_round_trips_the_twelve_key_rt_dict():
    from bing.rt import defs as rt_defs

    spec = AlgorithmSpec.from_standard('expb_pow')
    rt_dict = rt_defs.rt_dict_from_p(spec.to_bing_p())
    assert len(rt_dict) == 12
    assert rt_dict == LEGACY_GORDON_RT_DICT


def test_a_configured_backend_reaches_the_rt_dict_verbatim():
    from bing.rt import defs as rt_defs

    spec = AlgorithmSpec.from_standard('expb_pow')
    spec.rt.rt_backend = 'robust_ztt'
    spec.rt.fit_Bp = True
    spec.rt.Bp_value = 0.02
    spec.rt.include_CDOM_fl = True
    spec.rt.cdom_fraction = 0.65
    rt_dict = rt_defs.rt_dict_from_p(spec.to_bing_p())
    assert rt_dict == {**LEGACY_GORDON_RT_DICT,
                       'rt_backend': 'robust_ztt', 'fit_Bp': True,
                       'Bp_value': 0.02, 'include_CDOM_fl': True,
                       'cdom_fraction': 0.65}


def test_from_standard_seeds_the_gordon_backend():
    """BING's shipped combos predate the backend fields; they must default."""
    for name in ('expb_pow', 'giop', 'gsm'):
        rt = AlgorithmSpec.from_standard(name).rt
        assert rt.rt_backend == 'gordon', name
        assert rt.fit_Bp is False, name
        assert rt.include_CDOM_fl is False, name


def test_rt_override_accepts_the_new_keys():
    """The nested-merge machinery must reach the backend fields too."""
    spec = AlgorithmSpec.from_standard('expb_pow')
    out = spec.with_overrides({'rt': {'rt_backend': 'robust_hybrid',
                                      'fit_Bp': True}})
    assert out.rt.rt_backend == 'robust_hybrid'
    assert out.rt.fit_Bp is True
    # a partial mapping leaves the rest alone, and the source spec is untouched
    assert out.rt.variable_Gordon is True and out.rt.cdom_fraction == 0.8
    assert spec.rt.rt_backend == 'gordon' and spec.rt.fit_Bp is False


def test_an_rt_typo_is_still_rejected():
    import pytest

    spec = AlgorithmSpec.from_standard('expb_pow')
    with pytest.raises(ValueError, match='unknown rt option'):
        spec.with_overrides({'rt': {'rt_backends': 'robust_ztt'}})


def test_yaml_rt_override_of_a_backend_key_reaches_the_rt_dict():
    """End to end: sweep YAML -> AlgorithmConfig -> spec -> rt_dict."""
    from bing.rt import defs as rt_defs

    from ioptics import config

    cfg = config.loads(
        'sweep_id: s\ndatasets: [L23]\nalgorithms:\n'
        '  - name: expb_pow\n'
        '    rt: {rt_backend: robust_ztt, cdom_fraction: 0.5}\n')
    assert cfg.algorithms[0].overrides == {
        'rt': {'rt_backend': 'robust_ztt', 'cdom_fraction': 0.5}}
    spec = AlgorithmSpec.from_standard('expb_pow').with_overrides(
        cfg.algorithms[0].overrides)
    rt_dict = rt_defs.rt_dict_from_p(spec.to_bing_p())
    assert rt_dict['rt_backend'] == 'robust_ztt'
    assert rt_dict['cdom_fraction'] == 0.5

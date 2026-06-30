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

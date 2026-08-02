"""Stage-2 end-to-end micro-test — the first real two-way comparison.

One L23 spectrum fit by **both** ``expb_pow`` and ``giop`` via least-squares →
two ``RetrievalResult``s → rows in ``results_{spectral,scalar}.parquet`` +
``provenance.yaml``, asserting the planted IOPs are recovered within tolerance
and the tables/provenance are well-formed.

Tier-2 (`@needs_l23`): building the BING models loads ``Hydrolight400.nc``, so
this can't be data-free. The model-free surface (spec / io / provenance
round-trips) is covered by the separate Tier-1 tests so CI still exercises it.
"""

import numpy as np
import yaml

from ioptics.tests.conftest import needs_inelastic, needs_l23

SWEEP_ID = 'expb_giop_L23_micro'


@needs_l23
def test_two_way_comparison_end_to_end(tmp_path):
    from ioptics import config, io, prep, provenance, run
    from ioptics.algorithms.spec import AlgorithmSpec

    record = prep.prep_one('L23', 0, seed=1234)
    specs = [AlgorithmSpec.from_standard('expb_pow', label='ExpB_Pow'),
             AlgorithmSpec.from_standard('giop', label='GIOP')]

    i440 = int(np.argmin(np.abs(record.wave - 440.0)))
    i555 = int(np.argmin(np.abs(record.wave - 555.0)))

    # --- run both algorithms (chisq), stamp provenance_id ---
    pairs = []
    for spec in specs:
        res = run.run_algorithm(spec, record)
        res.provenance_id = provenance.provenance_id(SWEEP_ID, spec.name)
        pairs.append((res, record))

        # well-formed result
        assert res.status == 'ok'
        assert set(res.components) >= {'a', 'bb', 'a_ph', 'a_dg', 'bb_p'}
        assert res.components['a'].med.shape == record.wave.shape
        assert 0.0 < res.stats['chi2_nu'] < 5.0

        # recovers planted (truth) IOPs within tolerance
        a_ratio = res.components['a'].med[i440] / record.truth['a'].values[i440]
        bb_ratio = res.components['bb'].med[i555] / record.truth['bb'].values[i555]
        assert 0.5 < a_ratio < 2.0, f'{spec.name}: a(440) ratio {a_ratio:.2f}'
        assert 0.5 < bb_ratio < 2.0, f'{spec.name}: bb(555) ratio {bb_ratio:.2f}'

    # --- write the results tables ---
    io.write_results(SWEEP_ID, pairs, root=tmp_path)
    spectral, scalar = io.read_results(SWEEP_ID, root=tmp_path)

    # two-way: a scalar row per algorithm; spectral covers both × 7 components
    # (6 model components + Rrs_obs)
    assert sorted(scalar['algorithm']) == ['expb_pow', 'giop']
    assert set(spectral['algorithm']) == {'expb_pow', 'giop'}
    assert len(spectral) == 2 * 7 * record.wave.size
    # provenance_id stamped through to the table
    assert set(scalar['provenance_id']) == {f'{SWEEP_ID}#expb_pow',
                                            f'{SWEEP_ID}#giop'}

    # --- write + reload provenance.yaml ---
    cfg = config.loads(
        f"sweep_id: {SWEEP_ID}\n"
        "datasets: [L23]\n"
        "noise_model: pace\n"
        "algorithms: [expb_pow, giop]\n"
        "fit_method: chisq\n")
    rec_prov = provenance.build(SWEEP_ID, cfg, specs,
                                datasets={'L23': {'X': 1, 'Y': 0}})
    ppath = provenance.write(SWEEP_ID, rec_prov, root=tmp_path)
    loaded = yaml.safe_load(ppath.read_text())

    assert loaded['sweep_id'] == SWEEP_ID
    assert [a['name'] for a in loaded['algorithms']] == ['expb_pow', 'giop']
    assert loaded['config'] == cfg.to_dict()
    assert 'ioptics' in loaded['versions']


@needs_l23
def test_gsm_chisq_fit_recovers_iops():
    """gsm round-trips through run_algorithm unchanged and fits an L23 spectrum.

    The registered ``gsm`` spec (one ``_STANDARD_SEED`` entry, no core changes)
    drives the standard χ² path to a well-formed result recovering the planted
    IOPs — the Stage-6 "register + a tiny χ² fit" check.
    """
    from ioptics import prep, run
    from ioptics.algorithms import registry

    record = prep.prep_one('L23', 0, seed=1234)
    spec = registry.get('gsm')          # from the registry, not rebuilt

    res = run.run_algorithm(spec, record)
    assert res.status == 'ok'
    assert set(res.components) >= {'a', 'bb', 'a_ph', 'a_dg', 'bb_p'}
    assert res.components['a'].med.shape == record.wave.shape
    assert 0.0 < res.stats['chi2_nu'] < 5.0

    i440 = int(np.argmin(np.abs(record.wave - 440.0)))
    i555 = int(np.argmin(np.abs(record.wave - 555.0)))
    a_ratio = res.components['a'].med[i440] / record.truth['a'].values[i440]
    bb_ratio = res.components['bb'].med[i555] / record.truth['bb'].values[i555]
    assert 0.5 < a_ratio < 2.0, f'gsm: a(440) ratio {a_ratio:.2f}'
    assert 0.5 < bb_ratio < 2.0, f'gsm: bb(555) ratio {bb_ratio:.2f}'


@needs_l23
def test_fit_mcmc_accepts_string_obs_id():
    """MCMC fits a record with a non-integer obs_id (e.g. GLORIA 'GID_1').

    ``fit_mcmc`` synthesizes a positional index instead of ``int(record.obs_id)``
    — regression guard for the crash on GLORIA's string ids. Uses L23 water
    models + a tiny chain for speed; only completion (not fit quality) matters.
    """
    import copy
    from ioptics import prep, run
    from ioptics.algorithms import registry

    record = prep.prep_one('L23', 0, wv_min=400, wv_max=750)
    record.obs_id = 'GID_str'                       # non-integer id, as GLORIA gives
    spec = copy.deepcopy(registry.get('giop'))
    spec.mcmc.nsteps, spec.mcmc.nburn = 120, 30

    res = run.run_algorithm(spec, record, fit_method='mcmc')
    # Completion, not quality: a 120-step chain seeded from BING's global-RNG
    # walker init cannot be relied on to land inside the chi^2_nu <= 5 that
    # 'ok' requires, so asserting 'ok' here made the test order-dependent.
    assert res.status != 'fit_failed'
    assert res.obs_id == 'GID_str'                  # real id preserved on the result
    assert 'a' in res.components
    assert np.all(np.isfinite(res.components['a'].med))


@needs_l23
@needs_inelastic
def test_l23_x4_inelastic_rt_shifts_rrs_model():
    """L23 X=4: the include_Raman/include_Chl_fl toggles reach the forward model.

    Fits one L23 **X=4** spectrum (trimmed to 400-700 nm, where Raman is
    numerically stable — bing's own X=4 convention) with an elastic spec and
    with both inelastic toggles on. Both fits complete and the inelastic
    ``Rrs_model`` differs measurably from the elastic one (Raman + the ~685 nm
    fluorescence peak) — the Stage-6 X=4 smoke.
    """
    import copy
    from ioptics import prep, run
    from ioptics.algorithms.spec import AlgorithmSpec

    record = prep.prep_one('L23', 0, seed=1234, X=4, wv_min=400, wv_max=700)
    assert record.wave.size > 0 and record.meta['X'] == 4

    elastic = AlgorithmSpec.from_standard('expb_pow', label='ExpB_Pow')
    inelastic = copy.deepcopy(elastic)
    inelastic.rt.include_Raman = True
    inelastic.rt.include_Chl_fl = True

    res_el = run.run_algorithm(elastic, record)
    res_x4 = run.run_algorithm(inelastic, record)
    assert res_el.status == 'ok' and res_x4.status == 'ok'

    m_el = res_el.components['Rrs_model'].med
    m_x4 = res_x4.components['Rrs_model'].med
    assert np.isfinite(m_el).all() and np.isfinite(m_x4).all()
    rel = np.max(np.abs(m_x4 - m_el)) / np.max(np.abs(m_el))
    assert rel > 1e-3, f'X=4 Rrs_model barely differs from elastic (rel {rel:.1e})'

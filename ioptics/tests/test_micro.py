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

from ioptics.tests.conftest import needs_l23

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

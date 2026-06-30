"""Tests for ``run.run_sweep`` + the ``build_v1.py`` skeleton.

Tier-1 (data-free): the build script's ``run_v1.yaml`` parses and ``main(0)``
dispatches no stages. Tier-2 (`@needs_l23`): a small real χ² sweep over both
algorithms writes the full sweep directory (tables + provenance).
"""

import importlib.util
from pathlib import Path

from ioptics.tests.conftest import needs_l23

BUILD = (Path(__file__).resolve().parent.parent / 'runs' / 'prototypes'
         / 'expb_giop' / 'build_v1.py')


def _load_build_module():
    spec = importlib.util.spec_from_file_location('iop_build_v1', BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------
# Tier 1 — build-script skeleton (data-free)
# --------------------------------------------------------------------
def test_build_v1_config_and_flag_dispatch():
    from ioptics import config

    mod = _load_build_module()
    cfg = config.load(mod.CONFIG)              # run_v1.yaml parses + validates
    assert cfg.sweep_id == 'expb_giop_L23_v1'
    assert cfg.datasets == ['L23']
    assert [a.name for a in cfg.algorithms] == ['expb_pow', 'giop']
    # flag 0 runs no stages (no data needed) -> no error
    mod.main(0)


# --------------------------------------------------------------------
# Tier 2 — a small real sweep
# --------------------------------------------------------------------
@needs_l23
def test_run_sweep_small_chisq(tmp_path):
    from ioptics import config, io, run

    cfg = config.loads(
        "sweep_id: sweep_smoke\n"
        "datasets: [L23]\n"
        "noise_model: pace\n"
        "algorithms: [expb_pow, giop]\n"
        "fit_method: chisq\n"
        "mcmc_subset: 0\n"
        "seed: 1234\n")

    out = run.run_sweep(cfg, obs_ids=range(3), root=tmp_path)

    # 2 algorithms x 3 records = 6 χ² results
    assert out['n_results'] == 6
    assert out['provenance'].is_file()

    spectral, scalar = io.read_results('sweep_smoke', root=tmp_path)
    assert sorted(scalar['algorithm'].unique()) == ['expb_pow', 'giop']
    assert len(scalar) == 6
    # 6 results x 7 components (6 model + Rrs_obs) x nwave
    assert len(spectral) == 6 * 7 * spectral['wavelength'].nunique()
    # provenance_id stamped through to the table
    assert set(scalar['provenance_id']) == {'sweep_smoke#expb_pow',
                                            'sweep_smoke#giop'}
    assert (scalar['status'] == 'ok').all()


@needs_l23
def test_run_sweep_with_mcmc_subset_saves_chains(tmp_path):
    from ioptics import config, io, run
    from ioptics.algorithms import registry

    # tiny MCMC so the subset is fast (correctness, not convergence)
    registry.get('giop').mcmc.nsteps = 200
    registry.get('giop').mcmc.nburn = 50

    cfg = config.loads(
        "sweep_id: sweep_mcmc\n"
        "datasets: [L23]\n"
        "noise_model: pace\n"
        "algorithms:\n"
        "  - expb_pow\n"
        "  - name: giop\n"
        "    fit_method: mcmc\n"
        "fit_method: chisq\n"
        "mcmc_subset: 2\n"
        "seed: 1234\n")

    run.run_sweep(cfg, obs_ids=range(3), root=tmp_path)
    spectral, scalar = io.read_results('sweep_mcmc', root=tmp_path)

    # expb_pow: 3 χ² rows; giop: 3 χ² + 2 MCMC rows
    by_method = scalar.groupby(['algorithm', 'fit_method']).size()
    assert by_method[('expb_pow', 'chisq')] == 3
    assert by_method[('giop', 'chisq')] == 3
    assert by_method[('giop', 'mcmc')] == 2

    # the spectral table tags fit_method too: giop's MCMC rows are full
    # (2 records x 6 components x nwave)
    giop_mcmc = spectral[(spectral.algorithm == 'giop')
                         & (spectral.fit_method == 'mcmc')]
    assert len(giop_mcmc) == 2 * 7 * spectral['wavelength'].nunique()
    assert set(giop_mcmc['component']) == {'a', 'bb', 'a_ph', 'a_dg', 'bb_p',
                                           'Rrs_model', 'Rrs_obs'}

    # the 2 MCMC rows carry a saved chain file; χ² rows do not
    mcmc_rows = scalar[scalar.fit_method == 'mcmc']
    assert mcmc_rows['chain_file'].notna().all()
    for cf in mcmc_rows['chain_file']:
        assert (tmp_path / 'sweep_mcmc' / 'chains').as_posix() in cf
        chain = io.load_chain(cf)
        assert chain['chains'].ndim == 3          # (nsteps, nwalkers, nparam)
        # parameter names persisted, one per chain column (for corner labels)
        assert chain['pnames'].size == chain['chains'].shape[-1]
    assert scalar[scalar.fit_method == 'chisq']['chain_file'].isna().all()

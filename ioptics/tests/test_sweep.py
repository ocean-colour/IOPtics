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
    assert len(spectral) == 6 * 6 * spectral['wavelength'].nunique()
    # provenance_id stamped through to the table
    assert set(scalar['provenance_id']) == {'sweep_smoke#expb_pow',
                                            'sweep_smoke#giop'}
    assert (scalar['status'] == 'ok').all()

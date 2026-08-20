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


def test_build_v1_stage_dispatch(monkeypatch):
    """Each stage number wires the right stage (1 run / 2 metrics / 3 report)."""
    from ioptics import metrics, run
    from ioptics.report import leaderboard, rst, standard

    calls = []
    run_kw = {}

    def _run(cfg, **k):
        calls.append('run')
        run_kw.update(k)
    monkeypatch.setattr(run, 'run_sweep', _run)
    monkeypatch.setattr(metrics, 'compute', lambda sid, **k: calls.append('metrics'))
    monkeypatch.setattr(standard, 'build', lambda sid, **k: calls.append('report'))
    monkeypatch.setattr(standard, 'build_exemplars',
                        lambda sid, **k: calls.append('exemplars'))
    monkeypatch.setattr(leaderboard, 'update', lambda **k: calls.append('lb') or None)
    # stage 3 delegates the whole landing page (headline board + sweep cards +
    # interactive widget + full-grid drill-down) to standard.build_landing
    monkeypatch.setattr(standard, 'build_landing',
                        lambda **k: calls.append('landing') or (None, None))

    mod = _load_build_module()
    mod.main(0)
    assert calls == []                          # no-op
    mod.main(1)
    assert calls == ['run']
    calls.clear()
    mod.main(2)
    assert calls == ['metrics']
    calls.clear()
    mod.main(3)
    # the fold now happens inside standard.build_landing, so stage 3 is
    # three calls: the exemplar page first (the cross-algorithm page only
    # links it when the file exists), the sweep's own page, then the landing
    assert calls == ['exemplars', 'report', 'landing']

    # stage-1 run knobs thread through to run_sweep
    calls.clear()
    mod.main(1, n_cores=10, strict=False, obs_ids=range(20))
    assert calls == ['run']
    assert run_kw['n_cores'] == 10 and run_kw['strict'] is False
    assert list(run_kw['obs_ids']) == list(range(20))


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

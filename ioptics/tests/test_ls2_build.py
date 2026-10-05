"""Tier-1 checks on the LS2 sweep configs and build script (ls2 task 8).

The YAMLs beside ``runs/prototypes/ls2/build_v1.py`` are the source of truth
for the three L23 sweeps and the smoke, so their invariants are pinned here:
every rung named is a registered direct algorithm, the elastic sweep turns
Raman off on every rung (ls2 Q4), the sweeps share RT-A's window and noise form
(ls2 Q15), none reaches the leaderboard, and the smoke covers every rung plus
the off-grid record.
"""

import importlib.util
import pathlib

import pytest

from ioptics import config
from ioptics.algorithms import registry
from ioptics.algorithms.spec import is_direct

HERE = (pathlib.Path(__file__).resolve().parents[1] / 'runs' / 'prototypes'
        / 'ls2')


def _build():
    spec = importlib.util.spec_from_file_location('ls2_build_v1',
                                                  HERE / 'build_v1.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize('name', ['x4', 'x2', 'x1', 'smoke'])
def test_every_config_loads_and_resolves_to_direct_specs(name):
    build = _build()
    cfg = config.load(build.CONFIGS[name])
    registry.register_direct()
    registry.register_direct_l23()
    for ac in cfg.algorithms:
        spec = registry.get(ac.name).with_overrides(ac.overrides)
        assert is_direct(spec)
    assert cfg.datasets == ['L23']
    assert cfg.dataset_opts['L23']['kd1'] == 'ln_ratio'      # ls2 Q10
    assert cfg.noise_model == 'pace'                          # ls2 Q15
    assert (cfg.wv_min, cfg.wv_max) == (400.0, 750.0)         # RT-A's window
    assert cfg.leaderboard is False
    # every published rung is run, then (not in the smoke) the re-derived twins
    # of ls2 task 14 -- without ls2r_iii_l23, which is held-out only (Q39), and
    # without ls2r_i_ab on the elastic sweep, where kappa is off and it would
    # duplicate ls2r_i
    twins = [n for n in registry.DIRECT_SEED_L23 if n != 'ls2r_iii_l23'
             and not (name == 'x1' and n == 'ls2r_i_ab')]
    expect = list(registry.DIRECT_SEED) + ([] if name == 'smoke' else twins)
    assert [a.name for a in cfg.algorithms] == expect


def test_the_three_realizations_and_raman():
    build = _build()
    xs = {}
    for name in ('x1', 'x2', 'x4'):
        cfg = config.load(build.CONFIGS[name])
        xs[name] = cfg
        assert cfg.dataset_opts['L23']['X'] == int(name[1])
    assert all(ac.overrides == {'raman': False} for ac in xs['x1'].algorithms)
    for name in ('x2', 'x4'):
        assert all('raman' not in ac.overrides for ac in xs[name].algorithms)
    assert len({c.sweep_id for c in xs.values()}) == 3


def test_the_smoke_bound_includes_the_off_grid_record():
    build = _build()
    ids = build.bounded_obs_ids('smoke')['L23']
    assert len(ids) == 16 and 75 in ids
    assert build.bounded_obs_ids('x4') is None
    with pytest.raises(KeyError):
        build.bounded_obs_ids('nope')


def test_every_comparator_names_its_bing_rung():
    """A comparator sweep with several BING rungs must name one (ls2 task 9b)."""
    build = _build()
    assert set(build.COMPARATOR_ALGORITHM) == set(build.COMPARATOR)
    registry.register_rt_variants()
    for name in build.COMPARATOR_ALGORITHM.values():
        registry.get(name)                      # a registered RT-A rung


def test_the_l23_network_rung_runs_only_on_held_out_spectra():
    """ls2 Q39: 70% of L23 trained the Kd network, so ls2r_iii_l23 may appear
    in the held-out sweep only, and that sweep is bounded to the test split."""
    from ioptics import kd_net
    build = _build()
    registry.register_direct()
    registry.register_direct_l23()
    for name in ('x4', 'x2', 'x1', 'smoke'):
        names = [ac.name for ac in config.load(build.CONFIGS[name]).algorithms]
        assert 'ls2r_iii_l23' not in names, name
    held = config.load(build.CONFIGS['heldout'])
    assert 'ls2r_iii_l23' in [ac.name for ac in held.algorithms]
    assert held.dataset_opts['L23']['X'] == 4
    ids = build.bounded_obs_ids('heldout')['L23']
    assert ids == [int(i) for i in kd_net.split_scenarios()['test']]
    assert not set(ids) & set(kd_net.split_scenarios()['train'])


def test_every_config_resolves_heldout_included():
    build = _build()
    registry.register_direct()
    registry.register_direct_l23()
    cfg = config.load(build.CONFIGS['heldout'])
    for ac in cfg.algorithms:
        assert is_direct(registry.get(ac.name).with_overrides(ac.overrides))

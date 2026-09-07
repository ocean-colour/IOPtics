"""Tier-1 (data-independent) unit tests for ``ioptics.config``.

Exercises the YAML <-> Python sweep-config surface: round-trip, file load,
required-field validation, and the per-algorithm override rules (``fit_method``
overridable, ``noise_model`` not).
"""

import pytest

from ioptics import config
from ioptics.config import AlgorithmConfig, ConfigError, SweepConfig

# The headline sweep YAML from the implementation doc.
SAMPLE_YAML = """\
sweep_id: expb_giop_L23_v1
datasets: [L23]
noise_model: pace
algorithms:
  - expb_pow
  - name: giop
    fit_method: mcmc
    mcmc: {nsteps: 40000, nburn: 1000}
fit_method: chisq
mcmc_subset: 200
"""


def test_loads_parses_all_fields():
    cfg = config.loads(SAMPLE_YAML)
    assert isinstance(cfg, SweepConfig)
    assert cfg.sweep_id == 'expb_giop_L23_v1'
    assert cfg.datasets == ['L23']
    assert cfg.noise_model == 'pace'
    assert cfg.fit_method == 'chisq'
    assert cfg.mcmc_subset == 200
    assert len(cfg.algorithms) == 2

    # bare string -> defaults (sweep fit_method, no overrides)
    expb = cfg.algorithms[0]
    assert expb.name == 'expb_pow'
    assert expb.fit_method is None
    assert expb.overrides == {}

    # mapping -> per-algorithm fit_method override + passthrough overrides
    giop = cfg.algorithms[1]
    assert giop.name == 'giop'
    assert giop.fit_method == 'mcmc'
    assert giop.overrides == {'mcmc': {'nsteps': 40000, 'nburn': 1000}}


def test_round_trip_via_dump():
    cfg = config.loads(SAMPLE_YAML)
    text = config.dump(cfg)
    reloaded = config.loads(text)
    assert reloaded == cfg
    # the bare-string algorithm stays a bare string in the canonical dump
    assert cfg.to_dict()['algorithms'][0] == 'expb_pow'
    assert reloaded.algorithms[0].to_entry() == 'expb_pow'


def test_load_from_file(tmp_path):
    p = tmp_path / 'run_v1.yaml'
    p.write_text(SAMPLE_YAML)
    cfg = config.load(p)
    assert cfg.sweep_id == 'expb_giop_L23_v1'
    assert cfg.source_path == str(p)
    # source_path is excluded from identity, so a from-string load still equals it
    assert config.loads(SAMPLE_YAML) == cfg


def test_dump_to_file_round_trips(tmp_path):
    cfg = config.loads(SAMPLE_YAML)
    out = tmp_path / 'provenance_config.yaml'
    text = cfg.dump(out)
    assert out.read_text() == text
    assert config.load(out) == cfg


def test_missing_sweep_id_raises():
    bad = "datasets: [L23]\nalgorithms: [expb_pow]\n"
    with pytest.raises(ConfigError, match='sweep_id'):
        config.loads(bad)


def test_missing_datasets_raises():
    bad = "sweep_id: s1\nalgorithms: [expb_pow]\n"
    with pytest.raises(ConfigError, match='datasets'):
        config.loads(bad)


def test_missing_algorithms_raises():
    bad = "sweep_id: s1\ndatasets: [L23]\n"
    with pytest.raises(ConfigError, match='algorithms'):
        config.loads(bad)


def test_per_algorithm_noise_model_is_forbidden():
    bad = """\
sweep_id: s1
datasets: [L23]
algorithms:
  - name: giop
    noise_model: insitu
"""
    with pytest.raises(ConfigError, match='noise_model'):
        config.loads(bad)


def test_per_algorithm_fit_method_override_is_allowed():
    text = """\
sweep_id: s1
datasets: [L23]
fit_method: chisq
algorithms:
  - expb_pow
  - name: giop
    fit_method: mcmc
"""
    cfg = config.loads(text)
    assert cfg.fit_method == 'chisq'              # sweep-level unchanged
    assert cfg.algorithms[0].fit_method is None   # inherits sweep default
    assert cfg.algorithms[1].fit_method == 'mcmc'  # per-algorithm override


def test_bad_sweep_fit_method_raises():
    bad = "sweep_id: s1\ndatasets: [L23]\nalgorithms: [expb_pow]\nfit_method: bogus\n"
    with pytest.raises(ConfigError, match='fit_method'):
        config.loads(bad)


def test_bad_per_algorithm_fit_method_raises():
    bad = """\
sweep_id: s1
datasets: [L23]
algorithms:
  - name: giop
    fit_method: bogus
"""
    with pytest.raises(ConfigError, match='fit_method'):
        config.loads(bad)


def test_bad_mcmc_subset_raises():
    bad = "sweep_id: s1\ndatasets: [L23]\nalgorithms: [expb_pow]\nmcmc_subset: -5\n"
    with pytest.raises(ConfigError, match='mcmc_subset'):
        config.loads(bad)


def test_extra_top_level_keys_preserved_and_round_trip():
    text = SAMPLE_YAML + "seed: 1234\nresults_root: /tmp/runs\nnote: first pass\n"
    cfg = config.loads(text)
    assert cfg.seed == 1234
    assert cfg.results_root == '/tmp/runs'
    assert cfg.extra == {'note': 'first pass'}
    assert config.loads(config.dump(cfg)) == cfg


def test_from_dict_python_api():
    cfg = SweepConfig(
        sweep_id='s1', datasets=['L23'],
        algorithms=[AlgorithmConfig('expb_pow'),
                    AlgorithmConfig('giop', fit_method='mcmc')],
    )
    # the Python-built object round-trips through YAML identically
    assert config.loads(config.dump(cfg)) == cfg


# --------------------------------------------------------------------
# dataset_opts — per-dataset adapter load options (rt-tests, 2026-09-05)
# --------------------------------------------------------------------
DATASET_OPTS_YAML = """\
sweep_id: l23_x4_v1
datasets: [L23, PANGAEA]
algorithms: [expb_pow]
dataset_opts:
  L23: {X: 4, Y: 30}
"""


def test_dataset_opts_parse_and_round_trip():
    cfg = config.loads(DATASET_OPTS_YAML)
    assert cfg.dataset_opts == {'L23': {'X': 4, 'Y': 30}}
    # PANGAEA simply runs at the adapter defaults
    assert 'PANGAEA' not in cfg.dataset_opts
    assert config.loads(config.dump(cfg)) == cfg
    assert cfg.to_dict()['dataset_opts'] == {'L23': {'X': 4, 'Y': 30}}


def test_dataset_opts_default_is_empty_and_unemitted():
    cfg = config.loads(SAMPLE_YAML)
    assert cfg.dataset_opts == {}
    # an ordinary sweep's canonical config is unchanged by the key existing
    assert 'dataset_opts' not in cfg.to_dict()


def test_dataset_opts_rejects_a_dataset_the_sweep_does_not_run():
    """A typo here would run the whole sweep at the adapter defaults.

    ``prep_dataset`` takes ``**load_opts``, so an option addressed to a dataset
    outside the sweep reaches nothing and raises nowhere — exactly the
    silently-ignored-request failure the per-algorithm override whitelist
    exists to prevent.
    """
    bad = ("sweep_id: s1\ndatasets: [L23]\nalgorithms: [expb_pow]\n"
           "dataset_opts:\n  L32: {X: 4}\n")
    with pytest.raises(ConfigError, match="dataset_opts.*L32"):
        config.loads(bad)


def test_dataset_opts_must_be_mappings():
    for bad in ("dataset_opts: 4\n", "dataset_opts:\n  L23: 4\n",
                "dataset_opts:\n  L23: [X, 4]\n"):
        text = "sweep_id: s1\ndatasets: [L23]\nalgorithms: [expb_pow]\n" + bad
        with pytest.raises(ConfigError, match='dataset_opts'):
            config.loads(text)


# --------------------------------------------------------------------
# leaderboard — the publish/withhold flag
# --------------------------------------------------------------------
def test_leaderboard_defaults_true_and_is_unemitted():
    cfg = config.loads(SAMPLE_YAML)
    assert cfg.leaderboard is True
    assert 'leaderboard' not in cfg.to_dict()


def test_leaderboard_false_round_trips():
    text = SAMPLE_YAML + 'leaderboard: false\n'
    cfg = config.loads(text)
    assert cfg.leaderboard is False
    assert cfg.to_dict()['leaderboard'] is False
    assert config.loads(config.dump(cfg)) == cfg


def test_leaderboard_must_be_a_boolean():
    text = ("sweep_id: s1\ndatasets: [L23]\nalgorithms: [expb_pow]\n"
            "leaderboard: maybe\n")
    with pytest.raises(ConfigError, match='leaderboard'):
        config.loads(text)

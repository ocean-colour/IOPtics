"""Tests for the RT-test prototype: variants, frozen populations, configs.

Tier 1 (data-free) covers everything the RT sweeps are *configured* by — the
opt-in registration and its field diffs, the two committed id lists, the three
sweep YAMLs, and the build script's stage/bound wiring. Building an
:class:`~ioptics.algorithms.spec.AlgorithmSpec` reads
``bing.parameters.standard`` but constructs no models, and the id lists are
committed text, so none of it needs a data tree.

Tier 2 (``@needs_l23`` / ``@needs_pangaea`` / ``@needs_pace_pab``) checks the
frozen populations against the datasets they name.

The five RT variants are deliberately **not** in the standard seed — see
:func:`ioptics.algorithms.registry.register_rt_variants` — so a test that wants
them has to opt in, exactly as a sweep config does.
"""

import dataclasses
import importlib.util

import pytest

from ioptics import config, provenance
from ioptics.algorithms import registry
from ioptics.tests.conftest import needs_l23, needs_pace_pab, needs_pangaea

RT_NAMES = ('expb_pow_ztt_el', 'expb_pow_hyb_el', 'expb_pow_hyb_ram',
            'expb_pow_hyb_ramfl', 'expb_pow_hyb_ramflcdom')

#: The prototype directory (not an importable package — loaded by path below).
PROTO = (__import__('pathlib').Path(__file__).resolve().parent.parent
         / 'runs' / 'prototypes' / 'rt_tests')


def _load(name):
    """Import a module from the prototype directory by file path."""
    spec = importlib.util.spec_from_file_location(f'_rt_{name}',
                                                  PROTO / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def rt_registered():
    """Opt in, then restore the registry so other tests see the seed only."""
    before = dict(registry.REGISTRY)
    specs = registry.register_rt_variants()
    yield specs
    registry.REGISTRY.clear()
    registry.REGISTRY.update(before)


# --------------------------------------------------------------------
# Tier 1 — opt-in registration
# --------------------------------------------------------------------
def test_rt_variants_are_not_in_the_standard_seed():
    # Five near-clones of expb_pow on every cross-algorithm board is exactly
    # what opting in exists to prevent.
    seeded = dict(registry._STANDARD_SEED)
    for name in RT_NAMES:
        assert name not in seeded
        assert name in registry.RT_VARIANT_SEED


def test_rt_variants_absent_from_available_before_the_call():
    saved = {n: registry.REGISTRY.pop(n)
             for n in RT_NAMES if n in registry.REGISTRY}
    try:
        avail = registry.available()
        assert not (set(RT_NAMES) & set(avail))
        assert 'expb_pow' in avail          # ... and the seed is untouched
    finally:
        registry.REGISTRY.update(saved)


def test_lookup_before_opt_in_explains_itself():
    saved = {n: registry.REGISTRY.pop(n)
             for n in RT_NAMES if n in registry.REGISTRY}
    try:
        with pytest.raises(KeyError) as exc:
            registry.get('expb_pow_hyb_ramflcdom')
        assert 'register_rt_variants' in str(exc.value)
    finally:
        registry.REGISTRY.update(saved)


def test_register_rt_variants_adds_all_five(rt_registered):
    avail = registry.available()
    for name in RT_NAMES:
        assert name in avail
    assert list(rt_registered) == list(RT_NAMES)         # ladder order
    for name in ('expb_pow', 'giop', 'gsm'):             # seed left in place
        assert name in avail


def test_register_rt_variants_is_idempotent(rt_registered):
    # overwrite=True by default, like register_turbid: a build script that
    # calls _register() in every stage must not explode on the second one.
    again = registry.register_rt_variants()
    assert set(again) == set(RT_NAMES)


def test_one_register_call_per_variant(monkeypatch):
    """The project convention: one ``register(...)`` per spec, no core changes."""
    calls = []
    real = registry.register

    def _spy(spec, **kw):
        calls.append(spec.name)
        return real(spec, **kw)

    before = dict(registry.REGISTRY)
    monkeypatch.setattr(registry, 'register', _spy)
    try:
        registry.register_rt_variants()
    finally:
        registry.REGISTRY.clear()
        registry.REGISTRY.update(before)
    assert calls == list(RT_NAMES)


def test_rt_variant_labels_are_distinct_and_named(rt_registered):
    labels = [s.label for s in rt_registered.values()]
    assert len(set(labels)) == len(labels)
    for label in labels:
        assert label.startswith('ExpB_Pow')


def test_rt_variant_field_diffs_from_expb_pow(rt_registered):
    """The ladder differs from ``expb_pow`` in the RT — and *only* in the RT."""
    base = registry.get('expb_pow')
    expected_rt = {
        'expb_pow_ztt_el': {'rt_backend': 'robust_ztt', 'fit_Bp': True},
        'expb_pow_hyb_el': {'rt_backend': 'robust_hybrid', 'fit_Bp': True},
        'expb_pow_hyb_ram': {'rt_backend': 'robust_hybrid', 'fit_Bp': True,
                             'include_Raman': True},
        'expb_pow_hyb_ramfl': {'rt_backend': 'robust_hybrid', 'fit_Bp': True,
                               'include_Raman': True, 'include_Chl_fl': True},
        'expb_pow_hyb_ramflcdom': {'rt_backend': 'robust_hybrid',
                                   'fit_Bp': True, 'include_Raman': True,
                                   'include_Chl_fl': True,
                                   'include_CDOM_fl': True},
    }
    for name, spec in rt_registered.items():
        rt_diff = {f.name: getattr(spec.rt, f.name)
                   for f in dataclasses.fields(spec.rt)
                   if getattr(spec.rt, f.name) != getattr(base.rt, f.name)}
        assert rt_diff == expected_rt[name], name
        # everything outside name/label/rt/fit_method is inherited verbatim —
        # the models, the priors, Sdg, beta and the MCMC settings are what make
        # the ladder a controlled comparison.
        other = {f.name for f in dataclasses.fields(spec)} - {
            'name', 'label', 'rt', 'fit_method'}
        for field in sorted(other):
            assert getattr(spec, field) == getattr(base, field), (name, field)


def test_rt_variants_hold_the_shared_defaults(rt_registered):
    for name, spec in rt_registered.items():
        assert spec.rt.fit_Bp is True                  # k = 6 on every rung
        assert spec.rt.Bp_value == 0.01
        assert spec.rt.phi_C == 0.02
        assert spec.rt.double_gaussian is True
        assert spec.rt.cdom_fraction == 0.8
        assert spec.rt.variable_Gordon is True         # inert, kept as inherited
        assert spec.rt.rt_backend != 'gordon'
        assert spec.fit_method == 'mcmc'
        assert spec.maxfev == registry.DEFAULT_MAXFEV
        assert spec.anw_model == 'ExpBricaud' and spec.bbnw_model == 'Pow'


def test_only_the_last_rung_switches_cdom_fluorescence_on(rt_registered):
    on = {n for n, s in rt_registered.items() if s.rt.include_CDOM_fl}
    assert on == {'expb_pow_hyb_ramflcdom'}


def test_rt_variant_digests_are_distinct(rt_registered):
    digests = {n: provenance.algorithm_digest(s)
               for n, s in rt_registered.items()}
    assert len(set(digests.values())) == len(RT_NAMES)
    # ... and distinct from the algorithm they derive from
    assert provenance.algorithm_digest(registry.get('expb_pow')) \
        not in set(digests.values())


def test_rt_dbic_pair_names_registered_variants(rt_registered):
    a, b = registry.RT_DBIC_PAIR
    assert a in rt_registered and b in rt_registered
    # the elastic hybrid vs the full inelastic stack: same backend, so the
    # contest is about the inelastic physics
    assert rt_registered[a].rt.rt_backend == rt_registered[b].rt.rt_backend
    assert not rt_registered[a].rt.include_Raman
    assert rt_registered[b].rt.include_CDOM_fl


# --------------------------------------------------------------------
# Tier 1 — the frozen populations
# --------------------------------------------------------------------
def test_pangaea97_csv_is_committed_and_well_formed():
    derive = _load('derive_pangaea97')
    ids = derive.read_ids()
    assert len(ids) == derive.EXPECTED_N == 97
    assert all(isinstance(i, int) for i in ids)
    assert ids == sorted(set(ids))                     # sorted, no duplicates
    text = derive.IDS_CSV.read_text()
    assert text.startswith('#') and 'derive_pangaea97.py' in text
    assert f'Count: {len(ids)}' in text


def test_pace100_csv_is_committed_and_well_formed():
    extract = _load('extract_pace_100')
    ids = extract.read_ids()
    assert len(ids) == extract.N_SAMPLE == 100
    assert ids == sorted(set(ids))
    assert all(i.endswith(extract.NPZ_SUFFIX) for i in ids)
    text = extract.IDS_CSV.read_text()
    assert text.startswith('#') and 'extract_pace_100.py' in text
    assert str(extract.SAMPLE_SEED) in text


def test_pace_extraction_cross_checks_against_the_frozen_list(tmp_path):
    """The hook that stops a changed archive silently moving the population."""
    extract = _load('extract_pace_100')
    frozen = extract.read_ids()
    assert extract.check_ids(frozen) == ([], [])       # agreement
    added, removed = extract.check_ids(frozen[:-1] + ['NEW_ExpBPow'])
    assert added == ['NEW_ExpBPow'] and removed == [frozen[-1]]
    # ... and no frozen list at all is "first extraction", not "drift"
    assert extract.check_ids(frozen, tmp_path / 'absent.csv') is None


def test_id_csv_round_trips(tmp_path):
    derive = _load('derive_pangaea97')
    path = tmp_path / 'ids.csv'
    derive.write_ids([3, 1, 2], path)                  # written as given
    assert derive.read_ids(path) == [3, 1, 2]
    assert path.read_text().splitlines()[0].startswith('#')


# --------------------------------------------------------------------
# Tier 1 — the sweep configs
# --------------------------------------------------------------------
@pytest.mark.parametrize('name', ['rta_l23', 'rta_pangaea', 'rtb', 'smoke'])
def test_config_parses_and_validates(name):
    build = _load('build_v1')
    cfg = config.load(build.CONFIGS[name])
    assert [a.name for a in cfg.algorithms] == list(RT_NAMES)
    assert cfg.fit_method == 'mcmc'
    assert cfg.seed == 20260907                        # Q49: explicit, shared
    assert cfg.leaderboard is False                    # never a standing
    assert cfg.mcmc_subset and cfg.mcmc_subset > 0
    assert cfg.wv_min == 400.0 and 700.0 <= cfg.wv_max <= 750.0
    # round-trips through the provenance copy
    assert config.loads(config.dump(cfg)) == cfg


def test_pangaea_arm_fixes_Bp_on_every_rung():
    # Q52: NOMAD's 6-band spectra are underdetermined at k=6, so the PANGAEA
    # sweep overrides fit_Bp off on all five rungs (k=5). The L23 arm keeps
    # B_p free (Q51) — no rt override at all.
    build = _load('build_v1')
    cfg = config.load(build.CONFIGS['rta_pangaea'])
    for ac in cfg.algorithms:
        assert ac.overrides['rt'] == {'fit_Bp': False}
    cfg_l23 = config.load(build.CONFIGS['rta_l23'])
    for ac in cfg_l23.algorithms:
        assert 'rt' not in ac.overrides


def test_arm_a_split_uses_each_datasets_own_noise_model():
    # Q53: one noise model per sweep — L23 under its `pace` convention,
    # PANGAEA under its `insitu` convention. Never pooled.
    build = _load('build_v1')
    assert config.load(build.CONFIGS['rta_l23']).noise_model == 'pace'
    assert config.load(build.CONFIGS['rta_pangaea']).noise_model == 'insitu'


def test_config_windows_respect_the_hybrid_emulator_domain():
    from bing.rt import defs as rt_defs

    build = _load('build_v1')
    for name in build.CONFIGS:
        cfg = config.load(build.CONFIGS[name])
        assert cfg.wv_min >= rt_defs.ROBUST_HYBRID_WAVE_MIN
        assert cfg.wv_max <= rt_defs.ROBUST_HYBRID_WAVE_MAX


def test_arm_a_sweeps_the_inelastic_l23_realization():
    build = _load('build_v1')
    for name in ('rta_l23', 'smoke'):
        cfg = config.load(build.CONFIGS[name])
        assert cfg.dataset_opts['L23'] == {'X': 4}


def test_arm_a_mcmc_subset_covers_the_whole_population():
    # ``run_sweep`` takes ``records[:mcmc_subset]``, so the value has to be at
    # least the population or the sweep quietly samples a prefix of it.
    build = _load('build_v1')
    cfg = config.load(build.CONFIGS['rta_l23'])
    assert cfg.mcmc_subset >= 3320
    cfg_p = config.load(build.CONFIGS['rta_pangaea'])
    assert cfg_p.mcmc_subset >= len(build.pangaea97_ids())
    cfg_b = config.load(build.CONFIGS['rtb'])
    assert cfg_b.mcmc_subset >= len(build.pace100_ids())


def test_config_algorithm_names_resolve_after_opt_in(rt_registered):
    build = _load('build_v1')
    for name in build.CONFIGS:
        cfg = config.load(build.CONFIGS[name])
        for ac in cfg.algorithms:
            assert registry.get(ac.name).name == ac.name


# --------------------------------------------------------------------
# Tier 1 — the build script's wiring
# --------------------------------------------------------------------
def test_bounded_obs_ids_bounds_pangaea_only_for_arm_a():
    build = _load('build_v1')
    bound = build.bounded_obs_ids('rta_pangaea')
    assert set(bound) == {'PANGAEA'}
    assert len(bound['PANGAEA']) == 97
    assert build.bounded_obs_ids('rta_l23') is None    # L23 runs in full
    assert build.bounded_obs_ids('rtb') is None        # PACE *is* the 100


def test_bounded_obs_ids_rejects_an_unknown_config():
    build = _load('build_v1')
    with pytest.raises(KeyError):
        build.bounded_obs_ids('nope')


def test_smoke_pangaea_ids_are_a_subset_of_the_frozen_97():
    build = _load('build_v1')
    assert set(build.SMOKE_PANGAEA_IDS) <= set(build.pangaea97_ids())


def test_stage_five_is_a_stub_with_stable_numbering():
    build = _load('build_v1')
    with pytest.raises(SystemExit, match='task 13'):
        build.main(5)
    assert build.STAGE_CONFIG == {1: ('rta_pangaea', 'rta_l23'),
                                  2: ('rta_pangaea', 'rta_l23'),
                                  3: 'rtb', 4: 'rtb'}


def test_config_override_refuses_the_arm_b_stages():
    build = _load('build_v1')
    for flg in (3, 4):
        with pytest.raises(SystemExit, match='arm B'):
            build.main(flg, config_name='smoke')


def test_stage_zero_is_a_noop():
    build = _load('build_v1')
    assert build.main(0) is None


# --------------------------------------------------------------------
# Tier 1 — Q47a: the process pools warm the fitting stack at start-up
# --------------------------------------------------------------------
class _FakePool:
    """A ``ProcessPoolExecutor`` stand-in that records its kwargs, runs serially."""

    seen = []

    def __init__(self, max_workers=None, initializer=None, **kw):
        _FakePool.seen.append({'max_workers': max_workers,
                               'initializer': initializer})
        self._initializer = initializer

    def __enter__(self):
        if self._initializer is not None:
            self._initializer()
        return self

    def __exit__(self, *exc):
        return False

    def map(self, fn, items):
        return [fn(i) for i in items]


@pytest.fixture
def fake_pool(monkeypatch):
    import concurrent.futures

    _FakePool.seen = []
    monkeypatch.setattr(concurrent.futures, 'ProcessPoolExecutor', _FakePool)
    return _FakePool


def test_chisq_pool_warms_the_fitting_imports(fake_pool, monkeypatch):
    from ioptics import run

    monkeypatch.setattr(run, '_run_one_star',
                        lambda record, **kw: f'fit:{record}')
    out = run.run_batch(object(), ['a', 'b'], n_cores=2, strict=False)
    assert out == ['fit:a', 'fit:b']
    assert fake_pool.seen == [{'max_workers': 2,
                               'initializer': run._warm_fit_imports}]


def test_mcmc_pool_warms_the_fitting_imports(fake_pool, monkeypatch):
    from ioptics import run

    class _Spec:
        name = 'alg'

    class _Rec:
        dataset, obs_id = 'L23', 0

    monkeypatch.setattr(run, '_mcmc_one',
                        lambda record, **kw: type('R', (), {'status': 'ok'})())
    run._mcmc_subset(_Spec(), [_Rec(), _Rec()], 'sw', n_cores=2, strict=False)
    assert fake_pool.seen == [{'max_workers': 2,
                               'initializer': run._warm_fit_imports}]


def test_warm_fit_imports_is_picklable_and_idempotent():
    import pickle

    from ioptics import run

    # a pool initializer crosses the process boundary by reference
    assert pickle.loads(pickle.dumps(run._warm_fit_imports)) \
        is run._warm_fit_imports
    run._warm_fit_imports()
    run._warm_fit_imports()


# --------------------------------------------------------------------
# Tier 1 — mixed named/numbered obs ids in one sweep
# --------------------------------------------------------------------
def _obs_id_frames(ids):
    import pandas as pd

    return (pd.DataFrame({'dataset': ['D'] * len(ids), 'obs_id': list(ids)}),
            pd.DataFrame({'dataset': ['D'] * len(ids), 'obs_id': list(ids)}))


def test_mixed_named_and_numbered_obs_ids_are_stringified():
    from ioptics import io

    spec, scal = _obs_id_frames([0, 1, 'GID_1', 'PACE_..._ExpBPow'])
    assert io._harmonize_obs_id(spec, scal) is True
    assert list(spec['obs_id']) == ['0', '1', 'GID_1', 'PACE_..._ExpBPow']
    assert list(scal['obs_id']) == list(spec['obs_id'])   # still joinable


def test_homogeneous_obs_ids_keep_their_dtype():
    import numpy as np

    from ioptics import io

    # int and numpy.int64 together is NOT "mixed": L23 enumerates with plain
    # ints and PANGAEA's index yields int64, and every existing L23+PANGAEA
    # sweep's artifacts must keep their integer obs_id column.
    spec, scal = _obs_id_frames([0, np.int64(1), 2])
    assert io._harmonize_obs_id(spec, scal) is False
    assert not isinstance(spec['obs_id'].iloc[0], str)
    spec, scal = _obs_id_frames(['GID_1', 'GID_2'])
    assert io._harmonize_obs_id(spec, scal) is False


def test_mixed_obs_ids_survive_a_parquet_round_trip(tmp_path):
    """The regression: the first {L23, PANGAEA, PACE} sweep died writing this."""
    import numpy as np

    from ioptics import io
    from ioptics.records import PreparedRecord, RetrievalResult

    wave = np.array([450.0, 550.0])
    pairs = []
    for dataset, obs_id in (('L23', 0), ('PANGAEA', 10685),
                            ('PACE', 'a_ExpBPow')):
        result = RetrievalResult(
            dataset=dataset, obs_id=obs_id, algorithm='expb_pow_hyb_el',
            fit_method='chisq', components={}, scalars={},
            stats={'n_bands': 2, 'k': 6}, status='ok')
        record = PreparedRecord(
            dataset=dataset, obs_id=obs_id, wave=wave,
            Rrs=np.full(2, 0.003), varRrs=np.full(2, 1e-8),
            Rrs_clean=np.full(2, 0.003), truth={}, truth_interp={},
            init={'Chl': 1.0, 'Y': 0.5}, noise_model='pace', noise_seed=1)
        pairs.append((result, record))
    io.write_results('mixed_ids', pairs, root=tmp_path)
    _, scal = io.read_results('mixed_ids', root=tmp_path)
    assert set(scal['obs_id']) == {'0', '10685', 'a_ExpBPow'}


# --------------------------------------------------------------------
# Tier 1 — Q48: provenance readers tolerate a top-level ``notes`` list
# --------------------------------------------------------------------
def test_provenance_readers_tolerate_a_notes_key(tmp_path):
    import yaml

    from ioptics import io
    from ioptics.report import leaderboard

    rec = provenance.build('notes_sweep', None, ())
    d = io.sweep_dir('notes_sweep', root=tmp_path, create=True)
    path = d / 'provenance.yaml'
    path.write_text(provenance.dump(rec))
    with path.open('a') as fh:
        fh.write(yaml.safe_dump({'notes': ['chains not bit-reproducible: ...']},
                                sort_keys=False))
    back = yaml.safe_load(path.read_text())
    assert back['sweep_id'] == 'notes_sweep' and len(back['notes']) == 1
    assert leaderboard._provenance(d)['notes'] == back['notes']


# --------------------------------------------------------------------
# Tier 2 — the frozen populations against their datasets
# --------------------------------------------------------------------
@needs_pangaea
def test_pangaea97_matches_a_fresh_derivation():
    derive = _load('derive_pangaea97')
    assert derive.derive_ids() == derive.read_ids()


@needs_pangaea
def test_pangaea97_ids_are_all_usable_observations():
    from ioptics import datasets

    derive = _load('derive_pangaea97')
    usable = set(datasets.get_adapter('PANGAEA').obs_ids())
    assert set(derive.read_ids()) <= usable


@needs_pace_pab
def test_pace100_csv_matches_the_artifact():
    from ioptics import datasets

    extract = _load('extract_pace_100')
    assert sorted(datasets.get_adapter('PACE').obs_ids()) == extract.read_ids()


@needs_l23
def test_smoke_bound_covers_all_three_datasets():
    build = _load('build_v1')
    bound = build.bounded_obs_ids('smoke')
    assert set(bound) == {'L23', 'PANGAEA', 'PACE'}
    assert len(bound['L23']) == build.SMOKE_N_L23
    assert len(bound['PACE']) == build.SMOKE_N_PACE
    assert len(bound['PANGAEA']) == len(build.SMOKE_PANGAEA_IDS)

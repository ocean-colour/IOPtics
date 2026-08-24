"""Tier-1 tests for provenance hardening (Stage 7, Task 9).

Five things were wrong, and each was invisible in a different way:

* ``maxfev`` and the ``mcmc`` block were **not recorded**, so a sweep's provenance
  could not distinguish "converged at the default budget" from "converged only
  because the budget was raised" — and ``gloria_turbid_v3`` really did raise it.
* ``AlgorithmSpec.noise_model`` was a per-algorithm field for a **sweep-level**
  property, defaulting to ``'pace'``, so the one real sweep's blocks said ``pace``
  while its config said ``insitu`` and the uncertainty actually attached was
  ``insitu+imputed:0.1``.
* the per-record noise tag was **never persisted**, so "68 of these 100 fits were
  weighted by an invented uncertainty" survived only as a warning on stderr.
* ``AlgorithmConfig.overrides`` was parsed and **read by nobody**: a config could ask
  for a raised budget or a different prior and the run would silently use the
  registry default, while writing the ignored request into the provenance copy.
* ``provenance_id`` stopped at ``results_scalar``, so no metrics row or leaderboard
  row could be traced back to the block that produced it.
"""

import matplotlib
matplotlib.use('Agg')

import copy

import numpy as np
import pandas as pd
import pytest
import yaml

from ioptics import config, io, metrics, provenance
from ioptics.algorithms import registry
from ioptics.algorithms.spec import OVERRIDABLE_FIELDS, AlgorithmSpec
from ioptics.report import leaderboard, profiles
from ioptics.tests.test_metrics import _make_pair


# --------------------------------------------------------------------
# the algorithm block
# --------------------------------------------------------------------
def test_the_block_records_what_governs_convergence():
    """``maxfev`` decides *whether* a fit converges; it has to be on disk."""
    block = provenance.algorithm_block(registry.get('expb_pow'))
    assert 'maxfev' in block
    assert block['mcmc'] == {'nsteps': 40000, 'nburn': 1000, 'nMC': None}


def test_the_block_no_longer_claims_a_per_algorithm_noise_model():
    """It was 'descriptive only' and disagreed with both the config and reality."""
    block = provenance.algorithm_block(registry.get('expb_pow'))
    assert 'noise_model' not in block
    # and the field itself is gone from the spec, not merely unemitted
    assert not hasattr(registry.get('expb_pow'), 'noise_model')


def test_the_digest_moves_with_anything_that_changes_the_fit():
    spec = registry.get('expb_pow')
    base = provenance.algorithm_digest(spec)
    # maxfev uses a non-default value: the registry now seeds at DEFAULT_MAXFEV
    # (=40000), so 40000 would be a no-op here. fits_turbid decides whether a
    # red-peaked record is fitted at all — it must move the digest too.
    for field, value in (('maxfev', 12345), ('set_Sdg', True), ('sSdg', 0.5),
                         ('beta', 1.5), ('anw_model', 'Chl'),
                         ('fits_turbid', True)):
        other = copy.deepcopy(spec)
        setattr(other, field, value)
        assert provenance.algorithm_digest(other) != base, field
    mcmc = copy.deepcopy(spec)
    mcmc.mcmc.nsteps = 123
    assert provenance.algorithm_digest(mcmc) != base, 'mcmc'


def test_the_digest_ignores_what_only_names_the_algorithm():
    """Renaming an algorithm does not change it."""
    spec = registry.get('expb_pow')
    renamed = copy.deepcopy(spec)
    renamed.label = 'Something Else'
    renamed.name = 'other_name'
    assert provenance.algorithm_digest(renamed) == provenance.algorithm_digest(spec)


def test_the_digest_survives_the_schema_change(tmp_path):
    """An old block and its re-run must agree when the configuration is the same.

    Otherwise re-running a sweep would change every digest for byte-identical
    configurations, and the profile pages' "what varied" section would report
    schema versioning as configuration drift.
    """
    # the factory spec, not the registry's: a schema-1 block could only have
    # described the then-defaults (maxfev None, fits_turbid False), and the
    # registry now seeds maxfev=DEFAULT_MAXFEV — a real configuration change
    # that *should* digest differently from any schema-1 era block.
    spec = AlgorithmSpec.from_standard('expb_pow')
    new = provenance.algorithm_block(spec)
    new['schema'] = provenance.PROVENANCE_SCHEMA
    new['digest'] = provenance.algorithm_digest(new)
    # a schema-1 block: no maxfev/mcmc/fits_turbid/schema/digest, but with the
    # old noise_model
    old = {k: v for k, v in new.items()
           if k not in ('maxfev', 'mcmc', 'fits_turbid', 'schema', 'digest')}
    old['noise_model'] = 'pace'
    assert provenance.algorithm_digest(old) == provenance.algorithm_digest(new)
    # ... while a genuinely raised budget still separates them
    raised = copy.deepcopy(spec)
    raised.maxfev = 40000
    assert provenance.algorithm_digest(raised) != provenance.algorithm_digest(new)


def test_the_record_stamps_a_schema_and_a_digest_per_algorithm():
    specs = [registry.get('expb_pow'), registry.get('giop')]
    rec = provenance.build('s1', cfg=None, specs=specs)
    assert rec['schema'] == provenance.PROVENANCE_SCHEMA
    digests = [b['digest'] for b in rec['algorithms']]
    assert len(set(digests)) == 2, 'two different algorithms, two digests'
    for block in rec['algorithms']:
        assert block['schema'] == provenance.PROVENANCE_SCHEMA
    # and it still round-trips through YAML
    assert yaml.safe_load(provenance.dump(rec))['algorithms'][0]['digest'] \
        == digests[0]


# --------------------------------------------------------------------
# the per-record noise tag
# --------------------------------------------------------------------
def test_the_noise_tag_is_on_disk(tmp_path):
    """χ²ᵥ is a statement about the assumed error as much as about the model."""
    io.write_results('pn', [_make_pair(0, 'expb_pow', 1.0, 0.5, 10)], root=tmp_path)
    _, sc = io.read_results('pn', root=tmp_path)
    for col in ('noise_model', 'noise_seed', 'noise_imputed'):
        assert col in sc.columns, col
    assert sc['noise_model'].iloc[0] == 'pace'
    assert bool(sc['noise_imputed'].iloc[0]) is False


def test_the_imputed_fraction_is_now_recoverable_from_the_table(tmp_path):
    """The ~68%-imputed fact survived only as a warning on stderr.

    A reader who has the artifacts but not the console must be able to count it.
    """
    from ioptics import noise
    pairs = []
    for obs in range(10):
        result, record = _make_pair(obs, 'expb_pow', 1.0, 0.5, 10)
        if obs < 7:                      # 7 of 10 wholly imputed
            record.noise_model = 'insitu+imputed:0.1'
        pairs.append((result, record))
    io.write_results('pn2', pairs, root=tmp_path)
    _, sc = io.read_results('pn2', root=tmp_path)
    assert sc['noise_imputed'].sum() == 7
    assert sc['noise_imputed'].mean() == pytest.approx(0.7)
    # the derived flag agrees with the tag it came from
    assert all(noise.is_imputed(t) == bool(f) for t, f
               in zip(sc['noise_model'], sc['noise_imputed']))


# --------------------------------------------------------------------
# overrides: apply or reject, never ignore
# --------------------------------------------------------------------
def test_overrides_are_applied_and_leave_the_registry_spec_alone():
    spec = registry.get('expb_pow')
    out = spec.with_overrides({'maxfev': 20000, 'mcmc': {'nsteps': 500},
                               'set_Sdg': True})
    assert out.maxfev == 20000
    assert out.mcmc.nsteps == 500
    assert out.mcmc.nburn == spec.mcmc.nburn, 'a partial mapping merges'
    assert out.set_Sdg is True
    # the registry's own object must not be mutated for every later caller
    assert spec.maxfev == registry.DEFAULT_MAXFEV
    assert spec.mcmc.nsteps == 40000
    assert spec.set_Sdg is False
    assert registry.get('expb_pow').maxfev == registry.DEFAULT_MAXFEV


def test_an_unknown_override_is_rejected_not_ignored():
    spec = registry.get('expb_pow')
    for bad in ({'maxfev_typo': 1}, {'noise_model': 'pace'}, {'name': 'x'},
                {'fit_method': 'mcmc'}):
        with pytest.raises(ValueError, match='cannot override'):
            spec.with_overrides(bad)
    with pytest.raises(ValueError, match='unknown mcmc option'):
        spec.with_overrides({'mcmc': {'nsteps_typo': 1}})
    with pytest.raises(ValueError, match='must be a mapping'):
        spec.with_overrides({'rt': 5})


def test_no_overrides_is_a_no_op():
    spec = registry.get('expb_pow')
    assert spec.with_overrides({}) is spec
    assert spec.with_overrides(None) is spec


def test_an_overridden_sweep_cannot_pool_as_the_default_one():
    """The digest is taken after overrides, so pooling stays honest."""
    spec = registry.get('expb_pow')
    # 40000 would be a no-op now that the registry seeds at DEFAULT_MAXFEV
    raised = spec.with_overrides({'maxfev': 12345})
    assert provenance.algorithm_digest(raised) != provenance.algorithm_digest(spec)


def test_a_typo_fails_at_config_load_not_after_a_three_hour_sweep(tmp_path):
    text = ('sweep_id: s\ndatasets: [L23]\nalgorithms:\n'
            '  - name: expb_pow\n    maxfev_typo: 5\n')
    path = tmp_path / 'c.yaml'
    path.write_text(text)
    with pytest.raises(config.ConfigError, match='cannot override'):
        config.load(path)
    # a real override loads and is carried
    ok = tmp_path / 'ok.yaml'
    ok.write_text('sweep_id: s\ndatasets: [L23]\nalgorithms:\n'
                  '  - name: expb_pow\n    maxfev: 40000\n')
    cfg = config.load(ok)
    assert cfg.algorithms[0].overrides == {'maxfev': 40000}
    assert set(cfg.algorithms[0].overrides) <= OVERRIDABLE_FIELDS


# --------------------------------------------------------------------
# provenance_id reaches the metrics tables and the board
# --------------------------------------------------------------------
def _sweep(tmp_path, sweep_id='pv', algos=('expb_pow', 'giop')):
    pairs = []
    for obs in range(4):
        for i, algo in enumerate(algos):
            pairs.append(_make_pair(obs, algo, 1.0 + 0.5 * i, 0.5 + obs,
                                    10 + 5 * i, truth_factor=0.5 + obs))
    io.write_results(sweep_id, pairs, root=tmp_path)
    return metrics.compute(sweep_id, root=tmp_path)


def test_every_metrics_table_carries_provenance_id(tmp_path):
    tabs = _sweep(tmp_path, 'pv1')
    for name in ('spectral', 'scalar', 'pairwise'):
        df = getattr(tabs, name)
        assert metrics.PROVENANCE_COL in df.columns, name
    assert set(tabs.scalar[metrics.PROVENANCE_COL].dropna()) == {
        'pv1#expb_pow', 'pv1#giop'}


def test_a_two_algorithm_contest_gets_one_id_per_side(tmp_path):
    """A pairwise row is not attributable to a single provenance block."""
    tabs = _sweep(tmp_path, 'pv2')
    pw = tabs.pairwise
    assert 'provenance_id_a' in pw.columns and 'provenance_id_b' in pw.columns
    pairs = pw[pw['model_a'].notna()] if 'model_a' in pw.columns else pw
    if not pairs.empty:
        assert (pairs['provenance_id_a'] != pairs['provenance_id_b']).all()


def test_stamping_provenance_does_not_change_any_grouping(tmp_path):
    """It is a pure function of sweep_id + algorithm, so row counts must be equal."""
    tabs = _sweep(tmp_path, 'pv3')
    raw = metrics._stamp_provenance(tabs.scalar.drop(
        columns=[metrics.PROVENANCE_COL]), 'pv3')
    assert len(raw) == len(tabs.scalar)
    assert metrics._stamp_provenance(pd.DataFrame(), 'pv3').empty


def test_the_board_carries_provenance_id_and_the_schema(tmp_path):
    _sweep(tmp_path, 'pv4')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    assert 'provenance_id' in board.columns
    assert set(board['provenance_id'].dropna()) == {'pv4#expb_pow', 'pv4#giop'}
    assert 'prov_schema' in board.columns
    for col in ('provenance_id', 'prov_schema'):
        assert col in leaderboard.FULL_COLS, col


def test_the_board_prefers_the_digest_the_sweep_recorded(tmp_path):
    """Two definitions of "digest" must not coexist on disk.

    The fold hashed the whole block including ``name``/``label`` at 8 characters
    while provenance recorded 12 over the block without them, so ``algo_digest``
    could never equal the digest the sweep itself wrote down.
    """
    _sweep(tmp_path, 'pv5')
    d = io.sweep_dir('pv5', root=tmp_path)
    rec = provenance.build('pv5', cfg=None, specs=[registry.get('expb_pow'),
                                                   registry.get('giop')])
    provenance.write('pv5', rec, root=tmp_path)
    got = leaderboard._algorithm_digests(d)
    recorded = {b['name']: b['digest'] for b in rec['algorithms']}
    assert got == recorded, (got, recorded)
    assert leaderboard._algorithm_schemas(d) == {
        'expb_pow': provenance.PROVENANCE_SCHEMA,
        'giop': provenance.PROVENANCE_SCHEMA}


def test_an_unstamped_block_still_gets_a_digest_and_reads_as_schema_zero(tmp_path):
    """The real GLORIA sweep predates all of this; it must not simply go blank."""
    _sweep(tmp_path, 'pv6')
    # An unstamped (pre-schema) block could only describe the then-defaults —
    # maxfev None, fits_turbid False — i.e. the factory spec, not today's
    # registry seed (which really runs a raised budget and must digest apart).
    spec = AlgorithmSpec.from_standard('expb_pow', label='ExpB_Pow')
    block = provenance.algorithm_block(spec)
    for key in ('maxfev', 'mcmc', 'fits_turbid'):
        block.pop(key)
    block['noise_model'] = 'pace'
    d = io.sweep_dir('pv6', root=tmp_path)
    (d / 'provenance.yaml').write_text(
        yaml.safe_dump({'sweep_id': 'pv6', 'algorithms': [block]}))
    assert leaderboard._algorithm_digests(d)['expb_pow'] \
        == provenance.algorithm_digest(spec), \
        'an old block hashes as the equivalent new one'
    assert leaderboard._algorithm_schemas(d) == {'expb_pow': 0}


def test_mixed_schemas_are_flagged_as_such_not_as_configuration_drift(tmp_path):
    """A digest difference is not always a configuration difference."""
    _sweep(tmp_path, 'pv7')
    board = leaderboard.update(runs_root=tmp_path, out=tmp_path / 'lb.parquet')
    mixed = pd.concat([
        board.assign(sweep_id='old', algo_digest='aaa', prov_schema=0),
        board.assign(sweep_id='new', algo_digest='bbb',
                     prov_schema=provenance.PROVENANCE_SCHEMA),
    ], ignore_index=True)
    out = profiles._what_varied(mixed, 'expb_pow')
    assert 'What varied between sweeps' in out
    assert 'different provenance schemas' in out
    assert 'prov_schema' in out
    # same schema on both sides: a real configuration difference, no schema caveat
    same = pd.concat([
        board.assign(sweep_id='a', algo_digest='aaa',
                     prov_schema=provenance.PROVENANCE_SCHEMA),
        board.assign(sweep_id='b', algo_digest='bbb',
                     prov_schema=provenance.PROVENANCE_SCHEMA),
    ], ignore_index=True)
    plain = profiles._what_varied(same, 'expb_pow')
    assert 'What varied between sweeps' in plain
    assert 'different provenance schemas' not in plain

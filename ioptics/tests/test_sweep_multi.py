"""Tier-1 tests for the Stage-6 multi-everything sweep.

Two data-free checks (the task's "Tier-1 on a synthetic multi-dataset results
table where possible", since a real mixed L23/PANGAEA sweep can't be subset —
PANGAEA ids are strings):

- ``build_v2.py`` parses its ``run_v2.yaml`` and dispatches the same staged
  pipeline as ``build_v1`` (run / metrics / report + leaderboard + landing).
- a synthetic **{L23, PANGAEA, GLORIA} × {expb_pow, giop, gsm}** results table
  scores through ``metrics.compute`` + ``leaderboard.update`` with correct
  per-dataset/component coverage, and the **GLORIA CDOM-vs-a_dg caveat**
  surfaces in the accumulated leaderboard (folded + rendered).
"""

import importlib.util
from pathlib import Path

from ioptics import io, metrics
from ioptics.report import leaderboard
from ioptics.tests.test_metrics import _make_pair

BUILD = (Path(__file__).resolve().parent.parent / 'runs' / 'prototypes'
         / 'multi_v2' / 'build_v2.py')

DATASETS = ['L23', 'PANGAEA', 'GLORIA']
ALGOS = ['expb_pow', 'giop', 'gsm']


def _load_build_module():
    spec = importlib.util.spec_from_file_location('iop_build_v2', BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------
# Tier 1 — build-script skeleton (data-free)
# --------------------------------------------------------------------
def test_build_v2_config_and_flag_dispatch():
    from ioptics import config

    mod = _load_build_module()
    cfg = config.load(mod.CONFIG)               # run_v2.yaml parses + validates
    assert cfg.sweep_id == 'multi_L23_PANGAEA_v2'
    assert cfg.datasets == ['L23', 'PANGAEA']
    assert [a.name for a in cfg.algorithms] == ALGOS
    assert cfg.fit_method == 'chisq'
    assert cfg.noise_model == 'pct:0.05'        # uniform across datasets
    mod.main(0)                                 # no-op, no data needed


def test_build_v2_stage_dispatch(monkeypatch):
    """Each stage wires the right step (mirrors build_v1's dispatch test)."""
    from ioptics import metrics as m, run
    from ioptics.report import leaderboard as lb, rst, standard

    calls = []
    monkeypatch.setattr(run, 'run_sweep', lambda cfg, **k: calls.append('run'))
    monkeypatch.setattr(m, 'compute', lambda sid, **k: calls.append('metrics'))
    monkeypatch.setattr(standard, 'build', lambda sid, **k: calls.append('report'))
    monkeypatch.setattr(lb, 'update', lambda **k: calls.append('lb') or None)
    monkeypatch.setattr(standard, 'build_landing',
                        lambda **k: calls.append('landing') or (None, None))

    mod = _load_build_module()
    mod.main(0)
    assert calls == []
    mod.main(1)
    assert calls == ['run']
    calls.clear()
    mod.main(2)
    assert calls == ['metrics']
    calls.clear()
    mod.main(3)
    # the fold now happens inside standard.build_landing, so stage 3 is
    # two calls: the sweep's own page, then the landing rebuild
    assert calls == ['report', 'landing']


# --------------------------------------------------------------------
# Tier 1 — synthetic multi-dataset table: coverage + GLORIA caveat
# --------------------------------------------------------------------
def _make_multi_sweep(tmp_path, sid='multi_synth'):
    """3 datasets × 3 algorithms × 2 obs; expb_pow exact, others 2x-high."""
    chl = {0: 0.1, 1: 1.0}
    pairs = []
    for dataset in DATASETS:
        for obs in (0, 1):
            for algo in ALGOS:
                factor = 1.0 if algo == 'expb_pow' else 2.0
                pairs.append(_make_pair(obs, algo, factor, chl[obs], 10 + obs,
                                        dataset=dataset))
    io.write_results(sid, pairs, root=tmp_path)
    metrics.compute(sid, root=tmp_path)
    return sid


def test_multi_dataset_coverage_and_caveat(tmp_path):
    sid = _make_multi_sweep(tmp_path)
    board = leaderboard.update(runs_root=tmp_path,
                               out=tmp_path / 'leaderboard.parquet')

    # per-dataset / per-algorithm coverage accounting
    assert set(board['dataset']) == set(DATASETS)
    assert set(board['algorithm']) == set(ALGOS)
    # every dataset is scored on the full accuracy-component set
    for dataset in DATASETS:
        comps = set(board[board['dataset'] == dataset]['component'])
        assert set(metrics.ACCURACY_COMPONENTS).issubset(comps), \
            f'{dataset} missing components: ' \
            f'{set(metrics.ACCURACY_COMPONENTS) - comps}'

    # the GLORIA CDOM-vs-a_dg caveat is stamped on GLORIA a_dg rows only
    assert 'caveat' in board.columns
    gl_adg = board[(board['dataset'] == 'GLORIA') & (board['component'] == 'a_dg')]
    assert not gl_adg.empty
    assert (gl_adg['caveat'] == 'CDOM_vs_adg').all()
    # genuine a_dg elsewhere carries no caveat
    other_adg = board[(board['dataset'] != 'GLORIA')
                      & (board['component'] == 'a_dg')]
    assert (other_adg['caveat'].fillna('') == '').all()
    # non-a_dg GLORIA rows are not flagged
    gl_other = board[(board['dataset'] == 'GLORIA')
                     & (board['component'] != 'a_dg')]
    assert (gl_other['caveat'].fillna('') == '').all()

    # the caveat surfaces in the rendered leaderboard table (the exit criterion)
    rst = leaderboard.render(board=board)
    assert 'CDOM_vs_adg' in rst


def test_obs_ids_can_bound_each_dataset_separately(monkeypatch):
    """A mixed sweep needs a per-dataset bound, not one id list for all of them.

    PANGAEA enumerates 64 071 observations of which ~4 000 carry any truth, so an
    unbounded ``{L23, PANGAEA}`` sweep spends ~95% of its fits producing rows no
    metric can score. Bounding PANGAEA while leaving L23 whole is not expressible
    with a single ``obs_ids`` iterable — which is what ``build_v2``'s own docstring
    said made the bounded run impossible.
    """
    from ioptics import config, prep, provenance, run
    from ioptics.algorithms import registry

    seen = {}

    def _fake_prep(dataset, *, obs_ids=None, **kw):
        seen[dataset] = None if obs_ids is None else list(obs_ids)
        return []

    monkeypatch.setattr(prep, 'prep_dataset', _fake_prep)
    monkeypatch.setattr(registry, 'get', lambda name: _Spec(name))
    monkeypatch.setattr(run, 'run_batch', lambda *a, **k: [])
    monkeypatch.setattr(provenance, 'write', lambda *a, **k: 'prov.yaml')
    monkeypatch.setattr(provenance, 'build', lambda *a, **k: {})

    written = {}

    def _fake_write(sweep_id, pairs, **kw):
        written['n'] = len(pairs)
        return {'spectral': 's', 'scalar': 'c'}

    from ioptics import io
    monkeypatch.setattr(io, 'write_results', _fake_write)

    cfg = config.load(_load_build_module().CONFIG)
    run.run_sweep(cfg, obs_ids={'PANGAEA': [1, 2, 3]})
    assert seen['PANGAEA'] == [1, 2, 3], 'PANGAEA bounded'
    assert seen['L23'] is None, 'a dataset absent from the mapping runs in full'

    # the plain iterable form still applies to every dataset
    seen.clear()
    run.run_sweep(cfg, obs_ids=range(4))
    assert seen['L23'] == [0, 1, 2, 3] and seen['PANGAEA'] == [0, 1, 2, 3]


class _Spec:
    """Minimal stand-in for an AlgorithmSpec (the fit is monkeypatched away)."""

    def __init__(self, name):
        self.name = name

    def with_overrides(self, overrides):
        return self

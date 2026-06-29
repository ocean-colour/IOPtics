"""Tier-1 tests for ``ioptics.provenance`` (data-free).

Builds ``AlgorithmSpec`` objects directly (no BING import) and a ``SweepConfig``,
then checks the assembled record, the ``provenance_id`` format, and a YAML
write/read round-trip under a ``tmp_path`` root.
"""

import yaml

from ioptics import config, provenance
from ioptics.algorithms.spec import AlgorithmSpec, RTOptions

LOG = {'flavor': 'log_uniform', 'pmin': -6, 'pmax': 5}
UNIF_SDG = {'flavor': 'uniform', 'pmin': 0.01, 'pmax': 0.02}
UNIF_BETA = {'flavor': 'uniform', 'pmin': 0.0, 'pmax': 2.0}


def _specs():
    expb = AlgorithmSpec(
        name='expb_pow', label='ExpB_Pow', anw_model='ExpBricaud',
        bbnw_model='Pow', apriors=[LOG, UNIF_SDG, LOG], bpriors=[LOG, UNIF_BETA])
    giop = AlgorithmSpec(
        name='giop', label='GIOP', anw_model='GIOP', bbnw_model='Lee',
        apriors=[LOG, LOG], bpriors=[LOG], fit_method='mcmc')
    return [expb, giop]


def _cfg():
    return config.loads(
        "sweep_id: expb_giop_L23_v1\n"
        "datasets: [L23]\n"
        "noise_model: pace\n"
        "algorithms: [expb_pow, giop]\n"
        "fit_method: chisq\n"
        "mcmc_subset: 200\n"
        "seed: 1234\n")


def test_provenance_id_format():
    assert provenance.provenance_id('sweep_v1', 'giop') == 'sweep_v1#giop'


def test_versions_stamp_shape():
    v = provenance.versions()
    assert v['ioptics']['version']           # ioptics version present
    assert 'bing' in v and 'ocpy' in v
    assert 'design_doc' in v and 'implementation_doc' in v


def test_algorithm_block_is_serializable():
    block = provenance.algorithm_block(_specs()[0])
    assert block['name'] == 'expb_pow'
    assert block['anw_model'] == 'ExpBricaud' and block['bbnw_model'] == 'Pow'
    assert block['apriors'] == [LOG, UNIF_SDG, LOG]
    assert block['rt']['variable_Gordon'] is True
    assert block['fit_method'] == 'chisq'
    yaml.safe_dump(block)                     # must be YAML-serializable


def test_build_record_structure():
    cfg = _cfg()
    rec = provenance.build('expb_giop_L23_v1', cfg, _specs(),
                           datasets={'L23': {'X': 1, 'Y': 0, 'n_obs': 3320}},
                           created='2026-06-29T00:00:00Z')
    assert rec['sweep_id'] == 'expb_giop_L23_v1'
    assert rec['created'] == '2026-06-29T00:00:00Z'
    assert rec['config'] == cfg.to_dict()     # verbatim config copy
    assert rec['datasets']['L23']['n_obs'] == 3320
    assert [a['name'] for a in rec['algorithms']] == ['expb_pow', 'giop']
    assert rec['algorithms'][1]['fit_method'] == 'mcmc'


def test_write_read_round_trip(tmp_path):
    rec = provenance.build('sweep_v1', _cfg(), _specs(),
                           created='2026-06-29T00:00:00Z')
    path = provenance.write('sweep_v1', rec, root=tmp_path)
    assert path == tmp_path / 'sweep_v1' / 'provenance.yaml'
    loaded = yaml.safe_load(path.read_text())
    assert loaded == rec                      # full round-trip

"""Tier-1 checks on the LS2 report verifier (``runs/prototypes/ls2/verify_reports.py``)."""

import importlib.util
import pathlib

import pandas as pd

HERE = (pathlib.Path(__file__).resolve().parents[1] / 'runs' / 'prototypes'
        / 'ls2')


def _mod():
    spec = importlib.util.spec_from_file_location('ls2_verify_reports',
                                                  HERE / 'verify_reports.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_compare_csv_counts_cells(tmp_path):
    m = _mod()
    a, b = tmp_path / 'a.csv', tmp_path / 'b.csv'
    pd.DataFrame({'x': [1.0, 2.0], 'y': ['p', 'q']}).to_csv(a, index=False)
    pd.DataFrame({'x': [1.0, 2.0 + 1e-12], 'y': ['p', 'q']}).to_csv(b, index=False)
    assert m.compare_csv(a, b) == 0                       # within 1e-9 relative
    pd.DataFrame({'x': [1.0, 2.1], 'y': ['p', 'r']}).to_csv(b, index=False)
    assert m.compare_csv(a, b) == 2
    pd.DataFrame({'x': [1.0]}).to_csv(b, index=False)
    assert m.compare_csv(a, b) >= 1                       # shape mismatch


def test_every_ls2_page_has_a_generator():
    m = _mod()
    committed = {p.name for p in m.COMMITTED.iterdir()
                 if p.is_dir() and (p.name.startswith('ls2_'))}
    covered = {'ls2_l23_x4_v1', 'ls2_l23_x2_v1', 'ls2_l23_x1_v1',
               'ls2_l23_x4_heldout_v1', 'ls2_kd_15pct', 'ls2_kd_l23',
               'ls2_refit_ab', 'ls2_refit_kappa', 'ls2_ours', 'ls2_debrief'}
    assert committed <= covered, committed - covered
    assert {'x4', 'x2', 'x1', 'heldout', 'kd_15pct', 'kd_l23', 'refit_ab',
            'refit_kappa', 'ours', 'debrief', 'rta'} == set(m.PAGES)

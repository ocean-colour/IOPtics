"""Checks on the κ refit (``runs/prototypes/ls2/refit_kappa.py``, ls2 task 13).

Tier 2 runs the whole refit on the matched L23 X=1/X=2 pair into a scratch
docs root (without touching ocpy's shipped table) and pins the findings: the
NaN rate collapses, κ is more accurate where both evaluate, the correction
moves X=2 toward the elastic ceiling, and no μw term survives the
leave-one-zenith-out check.
"""

import importlib.util
import pathlib

import pandas as pd

from ioptics.tests.conftest import needs_l23, needs_l23_profile

HERE = (pathlib.Path(__file__).resolve().parents[1] / 'runs' / 'prototypes'
        / 'ls2')


def _mod():
    spec = importlib.util.spec_from_file_location('ls2_refit_kappa',
                                                  HERE / 'refit_kappa.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_design_shapes():
    import numpy as np
    m = _mod()
    x, mu = np.array([0.1, 0.2]), np.array([1.0, 0.8])
    assert m._design(x, mu, 'lin', 'none').shape == (2, 4)
    assert m._design(x, mu, 'log', 'lin').shape == (2, 8)


@needs_l23
@needs_l23_profile
def test_the_kappa_refit_and_its_findings(tmp_path):
    m = _mod()
    out = m.build(docs_root=tmp_path, save=False)
    rd = tmp_path / 'reports' / m.SID
    for name in ('kappa_forms.csv', 'kappa_vs_truth.csv', 'kappa_inversions.csv',
                 'kappa_table.csv', 'kappa_nan.png', 'kappa_fit.png', f'{m.SID}.rst'):
        assert (rd / name).is_file(), name
    assert out['kappa'].shape == (81, 7)

    inv = pd.read_csv(rd / 'kappa_inversions.csv').set_index(['set', 'config'])
    for X in ('X=2', 'X=4'):
        old = inv.loc[(X, 'refit a/bb + published κ')]
        new = inv.loc[(X, 'refit a/bb + refit κ')]
        none = inv.loc[(X, 'refit a/bb without κ')]
        assert old.kappa_nan_rate > 0.15 and new.kappa_nan_rate < 0.01
        assert new.bb_mae < old.bb_mae < none.bb_mae
        assert new.bb_p_mae < old.bb_p_mae
    ceil = inv.loc[('X=1 (elastic ceiling)', 'refit a/bb without κ')]
    assert ceil.bb_mae < inv.loc[('X=2', 'refit a/bb + refit κ')].bb_mae

    T = pd.read_csv(rd / 'kappa_vs_truth.csv').set_index('kappa_table')
    assert T.loc['refit', 'share_evaluable_350_750'] > 0.99
    assert T.loc['published', 'evaluable_500'] < 0.5            # the 502 nm row
    assert T.loc['refit', 'mae_where_evaluable'] < T.loc['published', 'mae_where_evaluable']

    F = pd.read_csv(rd / 'kappa_forms.csv').set_index(['x', 'muw_basis'])
    assert F.loc[('bb/a', 'none'), 'extrap_60_mae'] < F.loc[('bb/a', 'lin'), 'extrap_60_mae']

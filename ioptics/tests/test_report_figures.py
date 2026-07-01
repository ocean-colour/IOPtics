"""Tier-1 tests for ``ioptics.report.figures`` + ``ioptics.report.tables``.

Builds a synthetic two-algorithm sweep (reusing the ``test_metrics`` helpers),
runs ``metrics.compute``, then exercises every standard figure/table builder:
figures land as PNG+PDF under ``runs/<sweep_id>/figures/`` and the tables carry
the expected columns/rows. No models, no data.
"""

import matplotlib
matplotlib.use('Agg')

import numpy as np

from ioptics import io, metrics
from ioptics.report import figures, tables
from ioptics.tests.test_metrics import _make_pair

_SID = 'rep_v1'


def _build_sweep(tmp_path):
    """expb_pow (perfect) vs giop (2x-high) over 3 obs + one giop MCMC chain."""
    chl = {0: 0.05, 1: 0.5, 2: 2.0}                # oligo / meso / eutro
    pairs = []
    for obs in range(3):
        pairs.append(_make_pair(obs, 'expb_pow', 1.0, chl[obs], 10 + obs))
        pairs.append(_make_pair(obs, 'giop', 2.0, chl[obs], 15, rrs_factor=1.5))
    # one giop MCMC row with a real saved chain (for corner_set)
    res, rec = _make_pair(0, 'giop', 2.0, chl[0], 15, fit_method='mcmc')
    chains = np.random.default_rng(0).normal(size=(20, 6, 3))
    res.chain_file = str(io.save_chain(_SID, 'giop', rec, chains, root=tmp_path,
                                       pnames=['Adg', 'Sdg', 'Bnw']))
    pairs.append((res, rec))

    io.write_results(_SID, pairs, root=tmp_path)
    metrics.compute(_SID, root=tmp_path)
    return figures.load(_SID, root=tmp_path)


def _exists(paths):
    assert paths, 'no figure paths returned'
    for p in paths:
        assert p.is_file(), f'missing {p}'


def test_scatter_set(tmp_path):
    sw = _build_sweep(tmp_path)
    paths = figures.scatter_set(sw, 'a', ref=440)
    _exists(paths)
    assert {p.suffix for p in paths} == {'.png', '.pdf'}
    assert (figures._figdir(sw) / 'scatter_a_440.png').is_file()


def test_taylor_target(tmp_path):
    sw = _build_sweep(tmp_path)
    paths = figures.taylor_target(sw, 'a', ref=440)
    _exists(paths)
    assert (figures._figdir(sw) / 'taylor_a.png').is_file()
    assert (figures._figdir(sw) / 'target_a.png').is_file()


def test_dbic_cdf(tmp_path):
    sw = _build_sweep(tmp_path)
    _exists(figures.dbic_cdf(sw))
    assert (figures._figdir(sw) / 'dbic_cdf_expb_pow_vs_giop.png').is_file()


def test_spectra_set(tmp_path):
    sw = _build_sweep(tmp_path)
    paths = figures.spectra_set(sw, 0, algorithm='expb_pow')
    _exists(paths)
    assert (figures._figdir(sw) / 'spectra_expb_pow_0_a.png').is_file()


def test_closure_set(tmp_path):
    sw = _build_sweep(tmp_path)
    _exists(figures.closure_set(sw, 0))
    assert (figures._figdir(sw) / 'closure_0.png').is_file()


def test_corner_set(tmp_path):
    sw = _build_sweep(tmp_path)
    paths = figures.corner_set(sw)
    _exists(paths)                                  # the one giop MCMC chain
    assert (figures._figdir(sw) / 'corner_giop_0.png').is_file()


def test_tables_accuracy(tmp_path):
    sw = _build_sweep(tmp_path)
    df = tables.accuracy(sw)
    assert {'algorithm', 'component', 'ref_wave', 'mae', 'win_frac'} <= set(df.columns)
    # expb_pow is exact -> mae ~ 0 and rank 1 at (a, 440)
    a440 = df[(df.component == 'a') & (df.ref_wave == 440.0)].set_index('algorithm')
    assert np.isclose(a440.loc['expb_pow', 'mae'], 0.0)
    assert a440.loc['expb_pow', 'mae_rank'] == 1
    assert a440.loc['expb_pow', 'win_frac'] == 1.0
    assert (figures._figdir(sw) / 'accuracy_chisq_all.csv').is_file()


def test_tables_qc(tmp_path):
    sw = _build_sweep(tmp_path)
    df = tables.qc(sw).set_index('algorithm')
    assert 'frac_not_ok' in df.columns and 'frac_fit_noise' in df.columns
    assert df.loc['expb_pow', 'frac_not_ok'] == 0.0        # all 'ok'
    # giop model Rrs is 1.5x -> closure QC-fail flagged
    assert df.loc['giop', 'frac_qc_fail'] == 1.0
    assert (figures._figdir(sw) / 'qc_chisq_all.csv').is_file()

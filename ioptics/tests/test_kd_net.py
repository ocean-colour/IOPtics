"""Checks on ``ioptics.kd_net``, the L23 Kd-network trainer (ls2 task 11).

Tier 1 runs the trainer on a small synthetic corpus whose ``<Kd>_1`` is a known
function of ``Rrs``, so the contract (split by scenario, train-only
standardisation, the ``ln(mu_w Kd)`` target, selection on validation, a saved
network evaluated by ocpy agreeing with the trained one) is pinned without
data.  Tier 2 checks the shipped weights against held-out L23.
"""

import numpy as np
import pytest

from ioptics import kd_net as K
from ioptics.tests.conftest import needs_l23, needs_l23_profile

pytest.importorskip('flax')
pytest.importorskip('optax')


def _toy_corpus(n_scen=60, seed=0):
    """Synthetic corpus: Kd(λ) = (a0 + a1 / Rrs_blue_green) / mu_w."""
    rng = np.random.default_rng(seed)
    wave = np.arange(350.0, 751.0, 5.0)
    chl = 10 ** rng.uniform(-1.5, 0.5, n_scen)
    rows, kd, sza, scen = [], [], [], []
    for th in (0.0, 30.0, 60.0):
        for i, c in enumerate(chl):
            r = 0.01 * np.exp(-((wave - 420 - 60 * np.log10(c + 1)) / 120) ** 2) + 1e-4
            rows.append(r)
            k = (0.02 + 0.05 * c ** 0.6 * np.exp(-((wave - 440) / 80) ** 2)
                 + 0.4 * np.exp((wave - 750) / 60)) / K.muw(th)
            kd.append(k)
            sza.append(th)
            scen.append(i)
    return K.Corpus(wave, np.array(rows), np.array(kd), np.array(sza),
                    np.array(scen), X=4)


def test_the_split_is_by_scenario_disjoint_and_fixed():
    a, b = K.split_scenarios(), K.split_scenarios()
    for k in a:
        np.testing.assert_array_equal(a[k], b[k])
    allv = np.concatenate(list(a.values()))
    assert np.unique(allv).size == allv.size == 3320
    assert len(a['train']) == 2324 and len(a['val']) == 498


def test_target_is_ln_muw_kd():
    c = _toy_corpus(5)
    y = K.target(c)
    j = list(c.wave).index(440.0)
    np.testing.assert_allclose(y[:, K.OUT_WAVE.index(440.0)],
                               np.log(c.kd1[:, j] * K.muw(c.sza)))


def test_augmentation_keeps_the_clean_copy_first():
    c = _toy_corpus(4)
    cfg = K.KdNetConfig(n_noise=2)
    x, y = K.augmented(c, K.SEAWIFS_BANDS, cfg)
    assert x.shape == (3 * len(c.sza), 5) and y.shape == (3 * len(c.sza), 71)
    np.testing.assert_allclose(x[:len(c.sza)], K.at_bands(c.rrs, c.wave,
                                                         K.SEAWIFS_BANDS))
    assert not np.allclose(x[len(c.sza):2 * len(c.sza)], x[:len(c.sza)])


def test_fit_learns_selects_on_val_and_ocpy_reproduces_it(tmp_path):
    from ocpy.ls2 import kd_l23

    c = _toy_corpus(80)
    tr = c.subset(c.scenario < 60)
    va = c.subset(c.scenario >= 60)
    cfg = K.KdNetConfig(hidden=(16,), steps=400, eval_every=50, n_noise=1)
    net, h = K.fit(tr, K.SEAWIFS_BANDS, cfg, evals={'val': (va, None)})
    assert h.evals['val'][-1] < 0.5 * h.evals['val'][0]
    assert h.best_step == h.step[int(np.argmin(h.evals['val']))]
    # standardisation came from the training rows only
    x_tr, _ = K.augmented(tr, K.SEAWIFS_BANDS, cfg)
    np.testing.assert_allclose(net.x_mean, x_tr.mean(axis=0))
    # round trip through ocpy's file format and NumPy evaluator
    p = tmp_path / 'n.npz'
    kd_l23.save_network(net, p)
    back = kd_l23.from_npz(p)
    np.testing.assert_allclose(K.predict(back, va), K.predict(net, va), rtol=1e-12)
    s = K.scores(K.predict(net, va), K.truth_on_out(va))
    assert s['mae_ln_vis'] < 0.2 and s['frac_nan'] == 0.0
    assert net.meta['n_train_scenarios'] == 60 and net.theta_s_trained == (0.0, 60.0)


def test_fit_refuses_to_select_on_a_missing_set():
    c = _toy_corpus(5)
    with pytest.raises(ValueError, match='select_on'):
        K.fit(c, K.SEAWIFS_BANDS, K.KdNetConfig(steps=1), evals={})


def test_the_linear_baseline_has_one_layer():
    c = _toy_corpus(20)
    net, _ = K.fit(c, K.SEAWIFS_BANDS, K.KdNetConfig(hidden=(), steps=10,
                                                     eval_every=5, n_noise=0),
                   evals={'val': (c, None)})
    assert len(net.layers) == 1


@needs_l23
@needs_l23_profile
@pytest.mark.parametrize('name', ['L23_hyper_v1', 'L23_seawifs_v1'])
def test_shipped_weights_reproduce_their_heldout_score(name):
    """The weights in ocpy score on held-out L23 X=4 what their meta says."""
    from ocpy.ls2 import kd_l23

    net = kd_l23.load_network(name)
    c = K.l23_corpus(4)
    te = c.subset(np.isin(c.scenario, K.split_scenarios()['test']))
    s = K.scores(K.predict(net, te, K.noisy(te.rrs, te.wave, 4242)),
                 K.truth_on_out(te))
    assert s['mae_ln_vis'] == pytest.approx(net.meta['heldout_test_noisy_mae_ln_vis'],
                                            abs=2e-4)
    assert not set(np.unique(te.scenario)) & set(K.split_scenarios()['train'])

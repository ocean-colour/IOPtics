"""Train ``<Kd>_1`` networks on L23 (ls2 task 11).

LS2 needs ``<Kd>_1``, and in remote-sensing use it comes from a network fed by
``Rrs``.  Task 10 established that L23's ``<Kd>_1`` is a sound training truth:
the authors' shipped MODIS v1.1 network is what disagreed with it, and their
PACE v2.3 network agrees with it to 1.8%.  This module trains our own pair
(ls2 Q16, Q20, Q26) on L23 X=4 (ls2 Q38):

- a **hyperspectral** network, ``Rrs`` at every L23 band 400-750 nm, for
  PACE/OCI -- with **no in-situ validation possible** (no dataset pairs
  hyperspectral ``Rrs`` with measured Kd), so held-out L23 is its only test;
- a **five-band** SeaWiFS-like sibling (443, 490, 510, 555, 670 nm), which
  can be checked against PANGAEA's measured Kd.

The pattern is ``robust.rt.emulator``'s (retrieve-or-bust M3), whose lessons
are taken as measurements rather than tastes:

- **A small tanh MLP, full-batch and unshuffled Adam**, so a fit is
  reproducible from its seed; a **linear** model (``hidden=()``) is trained
  by the same code as the baseline the MLP must beat.
- **Standardisation from the training split only**, stored with the weights,
  as is the trained input **domain** that :func:`ocpy.ls2.kd_l23.kd_l23`
  flags against.
- **The target is ``ln(mu_w <Kd>_1)``**, not ``<Kd>_1``.  L23's ``<Kd>_1``
  scales as ``1/mu_w`` to within ~1%, so this is nearly geometry-free and the
  1/mu_w is put back analytically.  The emulator found a tanh MLP
  extrapolating *unstably* to an unseen solar zenith -- the init decided the
  answer -- and this corpus is the same one.  So whether ``mu_w`` is also an
  input is decided by a held-out-geometry experiment (train 0/30, test 60,
  several seeds), not assumed (:func:`geometry_experiment`).
- **Splits are by IOP scenario, never by row.**  The 3,320 scenarios are the
  effective sample: the three solar zeniths of a scenario are RT replicates
  of one water body and always land in the same split.
- **Noise augmentation in the ``pace`` form**: each training spectrum is
  seen clean and with ``n_noise`` independent PACE noise draws (sigma from
  ``ocpy.satellites.pace.gen_noise_vector``, about 50% of ``Rrs`` at 670 nm),
  so the network learns not to lean on the red bands.  Held-out scores are
  quoted both clean and with one fixed noise draw.

One structural departure from the emulator: the network maps the input
spectrum to all 71 output wavelengths at once (one head per wavelength),
rather than pointwise with wavelength as an input.  ``<Kd>_1(lambda)`` depends
on the whole spectrum, the output grid is fixed (L23's), and a joint head is
two orders of magnitude cheaper to train.  :func:`ocpy.ls2.kd_l23.kd_l23`
interpolates in ``ln Kd`` for other wavelengths.

``flax`` and ``optax`` are imported inside the functions that use them.
"""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path

import numpy as np

#: Input bands of the five-band sibling (ls2 Q16).
SEAWIFS_BANDS = (443.0, 490.0, 510.0, 555.0, 670.0)
#: The output grid, and the hyperspectral input bands: L23 400-750 nm.
OUT_WAVE = tuple(float(w) for w in np.arange(400.0, 751.0, 5.0))
HYPER_BANDS = OUT_WAVE
#: Solar zeniths L23 provides; and the span the networks accept (ls2 Q16:
#: operational 0-70 degrees; 60-70 is flagged as arithmetic extrapolation).
L23_THETA_S = (0, 30, 60)
SANCTIONED_THETA_S = (0.0, 70.0)
#: Scenario split fractions (train, val, test) and its seed.
SPLIT_FRACS = (0.70, 0.15, 0.15)
SPLIT_SEED = 11


@dataclass(frozen=True)
class KdNetConfig:
    """Architecture and training hyper-parameters.

    Attributes
    ----------
    hidden : tuple of int
        Hidden widths; ``()`` is the linear baseline.
    geometry_input : bool
        Append ``mu_w`` to the inputs.
    learning_rate : float
        Adam step size.
    steps : int
        Full-batch steps.
    seed : int
        Parameter-initialisation seed (the only stochastic input of a fit,
        given the data).
    eval_every : int
        Steps between recorded history points; the parameters with the best
        validation loss at those points are the ones returned.
    n_noise : int
        PACE noise draws per training spectrum (plus the clean one).
    noise_seed : int
        Seed of the augmentation draws.
    """

    hidden: tuple = (64, 64)
    geometry_input: bool = False
    learning_rate: float = 3e-3
    steps: int = 6000
    seed: int = 23
    eval_every: int = 200
    n_noise: int = 8
    noise_seed: int = 20261004


LINEAR = KdNetConfig(hidden=())


def muw(sza):
    """Cosine of the refracted solar beam (Snell, n_w = 1.34)."""
    from ocpy.ls2.kd_l23 import muw as _muw
    return _muw(sza)


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #

@dataclass
class Corpus:
    """L23 spectra and their ``<Kd>_1``, one row per (scenario, solar zenith).

    Attributes
    ----------
    wave : numpy.ndarray
        ``(81,)`` L23 grid [nm].
    rrs : numpy.ndarray
        ``(S, 81)`` clean ``Rrs``.
    kd1 : numpy.ndarray
        ``(S, 81)`` ``<Kd>_1`` (canonical ``ln_ratio``), NaN where undefined.
    sza : numpy.ndarray
        ``(S,)`` solar zenith [deg].
    scenario : numpy.ndarray
        ``(S,)`` IOP scenario index (the L23 row).
    X : int
        Inelastic realization.
    """

    wave: np.ndarray
    rrs: np.ndarray
    kd1: np.ndarray
    sza: np.ndarray
    scenario: np.ndarray
    X: int

    def subset(self, mask):
        m = np.asarray(mask, dtype=bool)
        return Corpus(self.wave, self.rrs[m], self.kd1[m], self.sza[m],
                      self.scenario[m], self.X)


def l23_corpus(X=4, thetas=L23_THETA_S):
    """Stack L23 realization ``X`` at each solar zenith in ``thetas``."""
    from ocpy.hydrolight import loisel23

    from ioptics import kd

    parts = []
    for Y in thetas:
        ds = loisel23.load_ds(X, Y)
        wave = np.asarray(ds['Lambda'].values, dtype=float)
        rrs = np.asarray(ds['Rrs'].values, dtype=float)
        w, k1 = kd.load_l23_kd1(X, Y)
        if not np.allclose(w, wave):
            raise ValueError('L23 profile and main grids differ')
        n = rrs.shape[0]
        parts.append((wave, rrs, k1, np.full(n, float(Y)), np.arange(n)))
    wave = parts[0][0]
    return Corpus(wave, *(np.concatenate([p[i] for p in parts]) for i in range(1, 5)),
                  X=int(X))


def split_scenarios(n_scenario=3320, fracs=SPLIT_FRACS, seed=SPLIT_SEED):
    """``{'train', 'val', 'test'}`` -> sorted scenario ids; a fixed permutation."""
    perm = np.random.default_rng(seed).permutation(n_scenario)
    n_tr = int(round(fracs[0] * n_scenario))
    n_va = int(round(fracs[1] * n_scenario))
    return {'train': np.sort(perm[:n_tr]),
            'val': np.sort(perm[n_tr:n_tr + n_va]),
            'test': np.sort(perm[n_tr + n_va:])}


def pace_sigma(wave):
    """PACE 1-sigma ``Rrs`` noise on ``wave`` (the ``pace`` noise form)."""
    from ocpy.satellites import pace
    return np.asarray(pace.gen_noise_vector(np.asarray(wave, float)), dtype=float)


def noisy(rrs, wave, seed):
    """One PACE noise draw on every spectrum of ``rrs`` (``(S, W)``)."""
    rng = np.random.default_rng(seed)
    return rrs + rng.standard_normal(rrs.shape) * pace_sigma(wave)


def at_bands(rrs, wave, bands):
    """``Rrs`` linearly interpolated onto ``bands`` (exact on L23's grid)."""
    bands = np.asarray(bands, dtype=float)
    return np.stack([np.interp(bands, wave, r) for r in rrs])


def features(corpus_rrs, wave, sza, bands, geometry_input):
    """Raw features ``(S, F)``: ``Rrs`` at ``bands`` (+ ``mu_w``)."""
    x = at_bands(corpus_rrs, wave, bands)
    return np.column_stack([x, muw(sza)]) if geometry_input else x


def target(corpus):
    """``ln(mu_w <Kd>_1)`` on :data:`OUT_WAVE`, ``(S, 71)``, NaN kept."""
    j = [int(np.argmin(np.abs(corpus.wave - w))) for w in OUT_WAVE]
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.log(corpus.kd1[:, j] * muw(corpus.sza)[:, None])


def augmented(corpus, bands, cfg):
    """Training rows: each spectrum clean, then ``cfg.n_noise`` noisy copies."""
    xs, ys = [], []
    y = target(corpus)
    for k in range(cfg.n_noise + 1):
        r = corpus.rrs if k == 0 else noisy(corpus.rrs, corpus.wave,
                                            cfg.noise_seed + k)
        xs.append(features(r, corpus.wave, corpus.sza, bands, cfg.geometry_input))
        ys.append(y)
    return np.concatenate(xs), np.concatenate(ys)


# --------------------------------------------------------------------------- #
# the network
# --------------------------------------------------------------------------- #

def _module(hidden, n_out):
    from flax import linen as nn

    class KdMLP(nn.Module):
        """tanh MLP -> one linear output per output wavelength."""

        hidden: tuple
        n_out: int

        @nn.compact
        def __call__(self, x):
            h = x
            for width in self.hidden:
                h = nn.tanh(nn.Dense(width)(h))
            return nn.Dense(self.n_out)(h)

    return KdMLP(hidden=tuple(hidden), n_out=int(n_out))


@dataclass
class History:
    """Training trace: step, train loss and each held-out loss (RMS ln ratio)."""

    step: list = field(default_factory=list)
    train: list = field(default_factory=list)
    evals: dict = field(default_factory=dict)
    best_step: int = 0


def _git_head():
    try:
        return subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                              cwd=Path(__file__).resolve().parent,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return 'unknown'


def fit(train, bands, cfg=None, *, evals=None, name='L23_kd', select_on='val'):
    """Train one network; return ``(ocpy KdL23Network, History)``.

    Parameters
    ----------
    train : Corpus
        Training rows (whole scenarios only: the caller splits).
    bands : sequence of float
        Input ``Rrs`` wavelengths.
    cfg : KdNetConfig
    evals : dict, optional
        ``name -> (Corpus, noise_seed or None)``: held-out sets scored every
        ``eval_every`` steps (clean when the seed is ``None``).
    select_on : str
        Which ``evals`` entry picks the returned parameters (lowest loss).
        It must not be a test set.

    Returns
    -------
    net : ocpy.ls2.kd_l23.KdL23Network
    history : History
    """
    import jax
    import jax.numpy as jnp
    import optax
    from ocpy.ls2.kd_l23 import KdL23Network

    cfg = cfg or KdNetConfig()
    evals = evals or {}
    if select_on not in evals:
        raise ValueError(f'select_on={select_on!r} is not one of the eval sets')
    x, y = augmented(train, bands, cfg)
    valid = np.isfinite(y)
    xm, xs = x.mean(axis=0), np.maximum(x.std(axis=0), 1e-12)
    ym = np.nanmean(y, axis=0)
    ysd = np.maximum(np.nanstd(y, axis=0), 1e-12)
    domain = np.stack([x.min(axis=0), x.max(axis=0)])

    def prep(xr, yr):
        v = np.isfinite(yr)
        return (jnp.asarray((xr - xm) / xs, jnp.float32),
                jnp.asarray(np.where(v, (yr - ym) / ysd, 0.0), jnp.float32),
                jnp.asarray(v, jnp.float32))

    tr = prep(x, y)
    ev = {}
    for k, (c, seed) in evals.items():
        r = c.rrs if seed is None else noisy(c.rrs, c.wave, seed)
        ev[k] = prep(features(r, c.wave, c.sza, bands, cfg.geometry_input),
                     target(c))
    ysd_j = jnp.asarray(ysd, jnp.float32)

    model = _module(cfg.hidden, len(OUT_WAVE))
    params = model.init(jax.random.key(cfg.seed), tr[0][:1])

    def loss_fn(p, xb, yb, vb):
        # mean squared ln-ratio over valid cells: residual in ln units
        r = (model.apply(p, xb) - yb) * ysd_j * vb
        return jnp.sum(r ** 2) / jnp.sum(vb)

    tx = optax.adam(cfg.learning_rate)
    opt = tx.init(params)
    grad = jax.value_and_grad(loss_fn)

    @partial(jax.jit, static_argnums=2)
    def chunk(p, o, n):
        def one(carry, _):
            p, o = carry
            _, g = grad(p, *tr)
            u, o = tx.update(g, o, p)
            return (optax.apply_updates(p, u), o), None
        (p, o), _ = jax.lax.scan(one, (p, o), None, length=n)
        return p, o

    score = jax.jit(lambda p, d: jnp.sqrt(loss_fn(p, *d)))
    hist = History(evals={k: [] for k in ev})
    best, best_params = np.inf, params

    def record(step, p):
        nonlocal best, best_params
        hist.step.append(step)
        hist.train.append(float(score(p, tr)))
        for k, d in ev.items():
            hist.evals[k].append(float(score(p, d)))
        if hist.evals[select_on][-1] < best:
            best, best_params = hist.evals[select_on][-1], p
            hist.best_step = step

    record(0, params)
    done = 0
    while done < cfg.steps:
        n = min(cfg.eval_every, cfg.steps - done)
        params, opt = chunk(params, opt, n)
        done += n
        record(done, params)

    layers = []
    names = sorted(best_params['params'], key=lambda s: int(s.split('_')[-1]))
    for nm in names:
        layer = best_params['params'][nm]
        layers.append((np.asarray(layer['kernel'], dtype=float),
                       np.asarray(layer['bias'], dtype=float)))
    # Fold the output standardisation into nothing: keep it explicit.
    tmin = float(np.min(train.sza))
    tmax = float(np.max(train.sza))
    net = KdL23Network(
        name=name, layers=tuple(layers), x_mean=xm, x_std=xs, y_mean=ym,
        y_std=ysd, bands=np.asarray(bands, dtype=float),
        out_wave=np.asarray(OUT_WAVE), geometry_input=cfg.geometry_input,
        domain=domain, theta_s_trained=(tmin, tmax),
        theta_s_sanctioned=SANCTIONED_THETA_S,
        meta={'trained_by': 'ioptics.kd_net.fit (ls2 task 11)',
              'ioptics_commit': _git_head(), 'config': asdict(cfg),
              'L23_X': int(train.X),
              'theta_s': sorted({float(t) for t in train.sza}),
              'n_train_scenarios': int(np.unique(train.scenario).size),
              'n_train_rows': int(x.shape[0]),
              'target': 'ln(mu_w <Kd>_1), <Kd>_1 = ln_ratio (ioptics.kd)',
              'best_step': int(hist.best_step), 'select_on': select_on,
              'scope': 'clear water (L23: Kd(490) <= 0.65 1/m)'})
    return net, hist


# --------------------------------------------------------------------------- #
# evaluation
# --------------------------------------------------------------------------- #

def predict(net, corpus, rrs=None):
    """``<Kd>_1`` on :data:`OUT_WAVE` for every row of ``corpus``."""
    from ocpy.ls2.kd_l23 import kd_l23
    r = corpus.rrs if rrs is None else rrs
    return kd_l23(at_bands(r, corpus.wave, net.bands), corpus.sza, network=net)


def truth_on_out(corpus):
    """``<Kd>_1`` on :data:`OUT_WAVE`."""
    j = [int(np.argmin(np.abs(corpus.wave - w))) for w in OUT_WAVE]
    return corpus.kd1[:, j]


def scores(kd_pred, kd_true):
    """Per-wavelength median ratio and mean |ln ratio|, plus the summaries.

    Returns ``{'median_ratio': (71,), 'mae_ln': (71,), 'mae_ln_vis': float,
    'frac_nan': float}``; ``mae_ln_vis`` is over 400-700 nm (the networks'
    recommended range), the number quoted as "fractional error".
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        lr = np.log(kd_pred / kd_true)
    ok = np.isfinite(kd_true)
    lr = np.where(ok, lr, np.nan)
    vis = np.asarray(OUT_WAVE) <= 700.0
    return {'median_ratio': np.exp(np.nanmedian(lr, axis=0)),
            'mae_ln': np.nanmean(np.abs(lr), axis=0),
            'mae_ln_vis': float(np.nanmean(np.abs(lr[:, vis]))),
            'frac_nan': float(np.mean(~np.isfinite(lr[ok])))}

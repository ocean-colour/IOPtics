"""Stage 7 Task 13: the MCMC subset at full-L23 scale.

Covers the two changes that turn the full-L23 MCMC sweep from ~5.4 serial
days / ~40 GB of chains into an overnight, ~2 GB job:

(a) ``run._mcmc_subset`` pools over ``n_cores``, with the RNG seeded per
    **record and algorithm** (``run._record_seed``), not per process, so a
    pooled run writes chains identical to a serial one — in any order;
(b) ``io.save_chain`` persists a burned + thinned chain, recording
    ``nsteps_production``/``nburn_sampler``/``nburn_discarded``/``thin`` so
    a thinned chain cannot be mistaken for a short run.

The seed/persistence tests are Tier-1 (synthetic chains, no data); the
serial-vs-pooled equivalence is Tier-2 (``@needs_l23``) because it runs real
(tiny) emcee fits.
"""

from types import SimpleNamespace

import numpy as np

from ioptics.tests.conftest import needs_l23


def _fake_record(obs_id=7, dataset='L23', nwave=5):
    """The minimal record surface ``save_chain``/``_record_seed`` touch."""
    wave = np.linspace(400.0, 700.0, nwave)
    rrs = np.full(nwave, 1e-3)
    return SimpleNamespace(dataset=dataset, obs_id=obs_id, wave=wave,
                           Rrs=rrs, varRrs=(0.1 * rrs) ** 2,
                           init={'Chl': 0.5, 'Y': 1.0})


# ---------------------------------------------------------------------------
# (a) per-record seeding
# ---------------------------------------------------------------------------

def test_record_seed_is_deterministic_and_record_keyed():
    from ioptics import run

    rec = _fake_record(obs_id=7, dataset='L23')
    # Pinned literal (crc32 of b'1234|giop|L23|7'): the seed must be stable
    # across interpreters and runs — hash() is salted, which is exactly the
    # bug this function exists to avoid.
    assert run._record_seed(1234, 'giop', rec) == 823164743
    assert (run._record_seed(1234, 'giop', rec)
            == run._record_seed(1234, 'giop', rec))

    # distinct along every identity axis — including the algorithm, so two
    # MCMC algorithms in one sweep do not share a walker-init stream
    seeds = {run._record_seed(1234, 'giop', rec),
             run._record_seed(4321, 'giop', rec),
             run._record_seed(1234, 'expb_pow', rec),
             run._record_seed(1234, 'giop', _fake_record(obs_id=8)),
             run._record_seed(1234, 'giop', _fake_record(dataset='PANGAEA'))}
    assert len(seeds) == 5
    state = np.random.get_state()
    try:
        for s in seeds:
            assert 0 <= s < 2 ** 32
            np.random.seed(s)      # must be acceptable as-is
    finally:
        np.random.set_state(state)  # do not leak RNG state into the suite

    # seed=None (a sweep with no seed) is still deterministic
    assert (run._record_seed(None, 'giop', rec)
            == run._record_seed(None, 'giop', _fake_record(obs_id=7)))


# ---------------------------------------------------------------------------
# (b) burned + thinned persistence
# ---------------------------------------------------------------------------

def test_save_chain_thins_and_records_the_trim(tmp_path):
    from ioptics import io

    chains = np.arange(100 * 4 * 3, dtype=np.float32).reshape(100, 4, 3)
    path = io.save_chain('sw', 'giop', _fake_record(), chains,
                         root=tmp_path, burn=10, thin=5, nburn_sampler=30)
    data = io.load_chain(path)

    assert np.array_equal(data['chains'], chains[10::5])
    assert data['chains'].shape == (18, 4, 3)
    assert int(data['nsteps_production']) == 100
    assert int(data['nburn_sampler']) == 30
    assert int(data['nburn_discarded']) == 10
    assert int(data['thin']) == 5
    # the chain filename carries the dataset: obs_id alone does not identify
    # an observation, and a pooled mixed-dataset subset must not race
    assert path.name == 'giop_L23_7.npz'


def test_save_chain_defaults_persist_the_whole_chain(tmp_path):
    from ioptics import io

    chains = np.zeros((50, 4, 2), dtype=np.float32)
    path = io.save_chain('sw', 'giop', _fake_record(), chains, root=tmp_path)
    data = io.load_chain(path)

    assert data['chains'].shape == (50, 4, 2)
    assert int(data['nsteps_production']) == 50
    assert int(data['nburn_discarded']) == 0
    assert int(data['thin']) == 1
    assert 'nburn_sampler' not in data      # unknown is omitted, not invented


def test_save_chain_caps_burn_like_chain_burn(tmp_path):
    """A burn beyond half the chain is capped, never an empty NPZ.

    Mirrors :func:`ioptics.evaluate.chain_burn`'s cap so a tiny-``nsteps``
    run cannot persist zero samples.
    """
    from ioptics import io

    chains = np.zeros((40, 4, 2), dtype=np.float32)
    path = io.save_chain('sw', 'giop', _fake_record(), chains,
                         root=tmp_path, burn=1000, thin=1)
    data = io.load_chain(path)

    assert int(data['nburn_discarded']) == 20        # capped at nsteps // 2
    assert data['chains'].shape[0] == 20


def test_chain_burn_matches_the_evaluate_discard():
    from ioptics import evaluate

    spec = SimpleNamespace(mcmc=SimpleNamespace(nburn=1000))
    assert evaluate.chain_burn(spec, np.zeros((40000, 16, 5))) == 1000
    # capped at half for tiny chains, so nothing discards everything
    assert evaluate.chain_burn(spec, np.zeros((100, 16, 5))) == 50


# ---------------------------------------------------------------------------
# pooled pre-fit decisions (no data needed: declined before any fit)
# ---------------------------------------------------------------------------

def test_mcmc_subset_pooled_declines_red_records(tmp_path):
    """The pool path makes the same pre-fit decisions as the serial one.

    Red-peaked records are declined ``out_of_scope`` inside the worker,
    before any sampling — so this exercises pickling, the pool, and the
    guard without needing the L23 tree.
    """
    from ioptics import run
    from ioptics.algorithms.spec import AlgorithmSpec
    from ioptics.records import PreparedRecord

    wave = np.arange(400.0, 701.0, 20.0)
    rrs = 2e-3 + 0.01 * np.exp(-((wave - 580.0) / 60.0) ** 2)
    reds = [PreparedRecord(
        dataset='X', obs_id=i, wave=wave, Rrs=rrs,
        varRrs=(0.10 * rrs) ** 2, Rrs_clean=rrs, truth={},
        truth_interp={}, init={'Chl': 1.0, 'Y': 0.5},
        noise_model='pct:0.1', noise_seed=None) for i in (1, 2)]
    spec = AlgorithmSpec.from_standard('giop')

    pairs = run._mcmc_subset(spec, reds, 'sw_pool_decline', root=tmp_path,
                             strict=True, n_cores=2, seed=9)
    assert [r.status for r, _ in pairs] == ['out_of_scope', 'out_of_scope']
    assert all(r.chain_file is None for r, _ in pairs)
    chains_dir = tmp_path / 'sw_pool_decline' / 'chains'
    assert not chains_dir.exists() or not list(chains_dir.glob('*.npz'))


# ---------------------------------------------------------------------------
# serial vs pooled equivalence (real, tiny, emcee fits)
# ---------------------------------------------------------------------------

@needs_l23
def test_mcmc_subset_pooled_and_reordered_match_serial(tmp_path):
    """``n_cores=2`` and a reversed record order both reproduce the serial
    chains exactly.

    This is the reproducibility contract of Task 13(a): emcee 3 snapshots the
    global ``np.random`` state at sampler construction and BING's walker init
    draws from the same stream, so the per-record seed makes the whole chain
    a function of (sweep seed, algorithm, record identity) — not of pool
    scheduling or of visit order. The reversed-order serial run is the cheap
    guard against the other failure mode (seed once, let the stream advance),
    which a 2-worker pool can miss.
    """
    import copy

    from ioptics import io, prep, run
    from ioptics.algorithms import registry

    records = [prep.prep_one('L23', i, wv_min=400, wv_max=750)
               for i in (0, 1)]
    spec = copy.deepcopy(registry.get('giop'))
    spec.mcmc.nsteps, spec.mcmc.nburn = 120, 30

    serial = run._mcmc_subset(spec, records, 'sw_ser',
                              root=tmp_path / 'ser', strict=True, seed=77)
    pooled = run._mcmc_subset(spec, records, 'sw_par',
                              root=tmp_path / 'par', strict=True, seed=77,
                              n_cores=2)
    rev = run._mcmc_subset(spec, list(reversed(records)), 'sw_rev',
                           root=tmp_path / 'rev', strict=True, seed=77)
    rev = {r.obs_id: r for r, _ in rev}

    assert [r.status for r, _ in serial] == [r.status for r, _ in pooled]
    for (rs, rec), (rp, _) in zip(serial, pooled):
        assert rs.chain_file and rp.chain_file
        cs = io.load_chain(rs.chain_file)
        cp = io.load_chain(rp.chain_file)
        cr = io.load_chain(rev[rs.obs_id].chain_file)
        assert np.array_equal(cs['chains'], cp['chains'])
        assert np.array_equal(cs['chains'], cr['chains'])
        # persisted burned + thinned, and the trim is recorded
        assert int(cs['nsteps_production']) == 120
        assert int(cs['nburn_sampler']) == 30
        assert int(cs['nburn_discarded']) == 30
        assert int(cs['thin']) == io.CHAIN_THIN
        assert cs['chains'].shape[0] == len(range(30, 120, io.CHAIN_THIN))
        # the evaluated result is likewise identical
        assert np.array_equal(rs.components['a'].med, rp.components['a'].med)

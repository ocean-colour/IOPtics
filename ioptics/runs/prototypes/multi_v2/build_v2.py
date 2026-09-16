"""Staged sweep driver for the Stage-6 multi-everything comparison.

The broad run the architecture was built for: **two datasets × three
algorithms**, χ² — L23 (X=1, elastic) and PANGAEA in-situ, each fit by
``expb_pow``, ``giop`` and ``gsm`` — folded into the cross-sweep leaderboard.

Usage (one stage per call, mirroring ``build_v1.py``)::

    python build_v2.py <flg>

    1  run     -> prep + retrieve -> results_{spectral,scalar}.parquet + provenance
    2  metrics -> score the results table -> metrics_{spectral,scalar,pairwise}
    3  report  -> standard.build (figures/tables/bokeh/rst) + leaderboard

Run the stages in order (``1`` then ``2`` then ``3``); ``0`` is a no-op.

The leaderboard **accumulates across sweeps** (``report.leaderboard.update``),
so the GLORIA scalar sweep (scalar-only, ``noise='insitu'``) and native
per-dataset-noise sweeps fold into the *same* leaderboard as this one — the
design's "multi-dataset is a group-by / accumulate across sweeps." A single
sweep carries one ``noise_model`` (here ``pct:0.05``, uniform across L23 +
PANGAEA); compare native noise models (L23 ``pace`` vs PANGAEA ``insitu``) by
running them as separate sweeps and folding both.

``run_v2.yaml`` beside this file is the source of truth. Paths derive from
``$OS_COLOR`` + the sweep id (see ``ioptics.io``).
"""

import os

from ioptics import config, run

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, 'run_v2.yaml')

#: PANGAEA spectral-truth families, as ``ocpy.insitu.pangaea`` names them.
_PANGAEA_SPECTRAL = ('aph', 'acdom', 'bbp')


def pangaea_truth_ids(*, spectral_only=True):
    """PANGAEA observation ids that carry **any truth a metric can score**.

    PANGAEA enumerates **64 071** observations with usable ``Rrs``, and the vast
    majority carry no truth at all — fitting them produces rows that every accuracy
    reduction then drops, at ~95% of the sweep's cost. This is the bound that makes
    the mixed ``{L23, PANGAEA}`` run tractable, and it is computed from the tidy
    tables directly (a set intersection) rather than by prepping 64 071 records to
    find out.

    **Default: spectral truth only** (JXP's choice) — an id qualifies if it carries a
    spectral IOP family (``a_ph`` / ``a_dg`` / ``bb_p``), which is **1 593** ids.
    ``spectral_only=False`` also admits ids whose only truth is chlorophyll (a derived
    scalar the metrics do score), which widens it to **3 896**. The narrower bound
    keeps the sweep to observations that can be scored on an *IOP retrieval* rather
    than on a single downstream scalar, and halves the cost.

    (The Stage-7 prompt cited "3 247 truth-carrying ids"; no definition here
    reproduces that number. The two the tables actually support are 1 593 and 3 896.)

    Returns a sorted list of ids.
    """
    from ocpy.insitu import pangaea

    from ioptics import datasets as D

    adapter = D.get_adapter('PANGAEA')
    with_rrs = set(adapter.obs_ids())

    iop = adapter._table('iop')
    ids = set()
    for kind in _PANGAEA_SPECTRAL:
        counts = pangaea.n_spectral(iop, kind=kind)
        ids |= set(counts.index[counts > 0])

    if not spectral_only:
        import numpy as np
        chla = adapter._table('chla')
        for col in ('chla_hplc', 'chla_fluor'):
            if col in chla.columns:
                vals = chla[col].astype(float).to_numpy()
                ids |= set(chla.index[np.isfinite(vals)])

    return sorted(ids & with_rrs)


def bounded_obs_ids(*, spectral_only=True):
    """The per-dataset ``obs_ids`` mapping for the bounded run.

    L23 is absent from the mapping and therefore runs **in full** — every one of its
    3 320 synthetic spectra carries the complete truth decomposition, so there is
    nothing to bound away. Only PANGAEA is restricted.
    """
    return {'PANGAEA': pangaea_truth_ids(spectral_only=spectral_only)}


def main(flg, *, n_cores=1, strict=True, obs_ids=None, bounded=False):
    flg = int(flg)
    cfg = config.load(CONFIG)

    if flg == 1:
        if bounded and obs_ids is None:
            obs_ids = bounded_obs_ids()
            n_pang = len(obs_ids['PANGAEA'])
            print(f'[bounded] PANGAEA restricted to {n_pang} truth-carrying ids '
                  f'(of 64071); L23 runs in full')
        # prep + retrieve -> tables + provenance
        run.run_sweep(cfg, obs_ids=obs_ids, n_cores=n_cores, strict=strict)

    elif flg == 2:
        from ioptics import metrics
        metrics.compute(cfg.sweep_id)           # score the results table

    elif flg == 3:
        from ioptics import report
        # standard report page (figures + tables + bokeh, provenance-stamped)
        report.standard.build(cfg.sweep_id, kind='cross_algorithm')
        # fold this sweep into the cross-sweep leaderboard + refresh the landing
        # (the fold now carries the GLORIA CDOM-vs-a_dg caveat through, so the
        # accumulated leaderboard surfaces it once a GLORIA sweep is folded)
        # rebuild the landing page (headline board + sweep cards + interactive
        # widget) and its full-grid drill-down from the refreshed fold
        report.standard.build_landing()


def _cli(argv=None):
    """CLI: ``build_v2.py <flg> [--n-cores N] [--strict BOOL] [--obs-ids A:B]``.

    ``--obs-ids A:B`` restricts *every* dataset to the same id range, which is only
    meaningful when the datasets share an id space. For the real bounded run use
    ``--bounded``, which restricts **PANGAEA alone** to its truth-carrying ids
    (:func:`pangaea_truth_ids`) and leaves L23 whole.

    (An earlier note here said a bounded mixed sweep "isn't expressible today
    (PANGAEA ids are strings)". PANGAEA ids are integers, and ``run_sweep`` now
    accepts a per-dataset mapping — so it is.)
    """
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('flg', nargs='?', type=int, default=0,
                   help='stage: 1 run, 2 metrics, 3 report (0 = no-op)')
    p.add_argument('--n-cores', type=int, default=1,
                   help='parallel workers for prep + chi^2 (stage 1)')
    p.add_argument('--strict', default='true',
                   help='true = fail-fast; false = robust fit_failed rows (stage 1)')
    p.add_argument('--obs-ids', default=None,
                   help="restrict every dataset to the range 'A:B' (stage 1)")
    p.add_argument('--bounded', action='store_true',
                   help='restrict PANGAEA to its truth-carrying ids (stage 1)')
    a = p.parse_args(argv)

    strict = str(a.strict).strip().lower() not in ('false', '0', 'no', 'f')
    obs_ids = None
    if a.obs_ids:
        lo, hi = (int(x) for x in a.obs_ids.split(':'))
        obs_ids = range(lo, hi)
    main(a.flg, n_cores=a.n_cores, strict=strict, obs_ids=obs_ids,
         bounded=a.bounded)


if __name__ == '__main__':
    _cli()

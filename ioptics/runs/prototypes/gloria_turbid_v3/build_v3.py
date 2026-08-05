"""Staged sweep driver for the Stage-6 turbid-water comparison.

The question this sweep exists to answer: **do BING's two-component
backscattering models fix GLORIA?** The GLORIA investigation
(``reports/gloria_fits_report.md``) traced the failure of open-ocean models
on turbid inland water to the backscattering *form* — a single decreasing
power law cannot supply what the red end needs. ``Pow2``/``Pow2Flat`` were
built in response. But bing's own benchmark (``dev/turbid_bbp``) then found
that a single power law is statistically adequate against a *two-component
truth* unless the noise is 4-11x tighter than GLORIA's, so the two-component
form may not be what closes the ~48% misfit on real spectra. Only real
GLORIA data settles it.

Four algorithms on the same spectra:

- ``expb_pow``      open-ocean baseline (the model that fails today)
- ``expb_powflex``  same single power law, slope prior widened to allow
                    beta < 0 — the **control**: if it does no better than
                    ``expb_pow``, the prior *range* was never the problem
- ``expb_pow2flat`` two components, mineral exponent fixed (the recommended
                    turbid model — the 4-parameter version is degenerate
                    under chi-squared)
- ``expb_pow2``     two components, mineral exponent free

Usage (one stage per call, mirroring ``build_v2.py``)::

    python build_v3.py <flg> [--n-sample N]

    1  run     -> prep + retrieve -> results_{spectral,scalar}.parquet + provenance
    2  metrics -> score the results table -> metrics_{spectral,scalar,pairwise}
    3  report  -> standard.build (figures/tables/bokeh/rst) + leaderboard

Run the stages in order (``1`` then ``2`` then ``3``); ``0`` is a no-op.

Two things differ from ``build_v2.py``:

1. The turbid algorithms are **opt-in** (they would otherwise dilute the
   open-ocean leaderboard with near-duplicate rows), so stage 1 calls
   ``registry.register_turbid()`` before running the sweep — and gives the
   ``expb_pow`` baseline the same ``maxfev``, so the four algorithms are
   compared on the model rather than on the optimizer budget.
2. GLORIA ids are strings (``'GID_1'``), so ``--obs-ids A:B`` is useless
   here. ``--n-sample N`` takes a deterministic even spread across the
   catalogue instead, which keeps clear and turbid spectra both represented.

Note the noise model: GLORIA's quoted per-band error is so tight that
chi-squared is uninterpretable, so ``prep`` applies a 5% error **floor** for
this dataset (tag ``'insitu+floor:0.05'``). Every number from this sweep is
therefore an *inflated-noise* result — the floor makes chi-squared readable,
it does not improve any fit. And for ~70% of the catalogue the floor is the
*only* uncertainty there is: those spectra quote none, so their weights are
wholly imputed and the tag says ``'insitu+imputed:0.05'``. Before that case
was handled they reached the fitter with all-NaN weights and could not be
fit at all, which is what the earlier "convergence failure" on GLORIA was.

``run_v3.yaml`` beside this file is the source of truth. Paths derive from
``$OS_COLOR`` + the sweep id (see ``ioptics.io``).
"""

import os

from ioptics import config, run

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, 'run_v3.yaml')

#: Default number of GLORIA spectra to fit. The catalogue holds ~7.5k; a
#: deterministic spread of 100 compares four algorithms across the
#: clear-to-turbid range with enough spectra to read a per-status rate off the
#: result, while keeping a stage-1 run to ~tens of minutes. ``0`` runs all of
#: them (hours).
DEFAULT_N_SAMPLE = 100


def sample_obs_ids(dataset='GLORIA', n_sample=DEFAULT_N_SAMPLE):
    """A deterministic even spread of ``n_sample`` observation ids.

    GLORIA ids are strings, so the ``A:B`` range form cannot subset them.
    Taking every ``len/n``-th id (rather than the first ``n``) keeps the
    clear-to-turbid range represented, which is the axis that matters here.

    Parameters
    ----------
    dataset : str, optional
        Registered dataset name (default ``'GLORIA'``).
    n_sample : int or None, optional
        How many ids to return; ``None`` or 0 → all of them.

    Returns
    -------
    list
        Observation ids, or ``None`` when every observation is wanted (which
        is what :func:`ioptics.run.run_sweep` expects for "all").
    """
    import numpy as np

    from ioptics import datasets

    if not n_sample:
        return None
    ids = list(datasets.get_adapter(dataset).obs_ids())
    if n_sample >= len(ids):
        return None
    idx = np.linspace(0, len(ids) - 1, int(n_sample)).astype(int)
    return [ids[i] for i in idx]


def main(flg, *, n_cores=1, strict=True, obs_ids=None,
         n_sample=DEFAULT_N_SAMPLE):
    flg = int(flg)
    cfg = config.load(CONFIG)

    if flg == 1:
        import dataclasses

        from ioptics.algorithms import registry

        # The turbid models are not in the standard seed; opt in before the
        # sweep resolves its algorithm names. This also stamps the raised
        # optimizer budget (registry.TURBID_MAXFEV) onto their specs, without
        # which they run out of evaluations on a large share of spectra.
        registry.register_turbid()
        # ... and the baseline needs the *same* budget, or the contest measures
        # the budget instead of the model: on 100 GLORIA spectra expb_pow at
        # scipy's default failed 72 of 100 while the turbid specs failed none.
        # A raised budget governs whether a fit returns, not how well it fits,
        # so equalizing it is what makes the comparison like-for-like.
        base = registry.get('expb_pow')
        registry.register(dataclasses.replace(base,
                                              maxfev=registry.TURBID_MAXFEV),
                          overwrite=True)
        if obs_ids is None:
            obs_ids = sample_obs_ids(cfg.datasets[0], n_sample)
        run.run_sweep(cfg, obs_ids=obs_ids, n_cores=n_cores, strict=strict)

    elif flg == 2:
        from ioptics import metrics
        metrics.compute(cfg.sweep_id)           # score the results table

    elif flg == 3:
        from ioptics import report
        # GLORIA carries no spectral a/bb truth (only a_cdom440 at 440 nm),
        # so the per-dataset page is the informative one here.
        # exemplars first: the cross-algorithm page links this one, and only
        # links it when the file already exists (a dangling :doc: fails -W).
        report.standard.build_exemplars(cfg.sweep_id)
        report.standard.build(cfg.sweep_id, kind='cross_algorithm')
        # rebuild the landing page (headline board + sweep cards + interactive
        # widget) and its full-grid drill-down from the refreshed fold
        report.standard.build_landing()


def _cli(argv=None):
    """CLI: ``build_v3.py <flg> [--n-cores N] [--strict BOOL] [--n-sample N]``."""
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('flg', nargs='?', type=int, default=0,
                   help='stage: 1 run, 2 metrics, 3 report (0 = no-op)')
    p.add_argument('--n-cores', type=int, default=1,
                   help='parallel workers for prep + chi^2 (stage 1)')
    p.add_argument('--strict', default='false',
                   help='true = fail-fast; false = robust fit_failed rows '
                        '(stage 1; false by default here because turbid fits '
                        'are expected to fail on some spectra)')
    p.add_argument('--n-sample', type=int, default=DEFAULT_N_SAMPLE,
                   help=f'GLORIA spectra to fit, evenly spread over the '
                        f'catalogue (default {DEFAULT_N_SAMPLE}; 0 = all)')
    args = p.parse_args(argv)
    main(args.flg, n_cores=args.n_cores,
         strict=str(args.strict).lower() in ('1', 'true', 'yes'),
         n_sample=args.n_sample)


if __name__ == '__main__':
    _cli()

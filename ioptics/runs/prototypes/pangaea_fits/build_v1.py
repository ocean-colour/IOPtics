"""Report driver for the PANGAEA investigation's approved-defaults sweep.

``pangaea_fits_v2`` (2026-08-10) is the PANGAEA half of the regeneration the
investigation asked for (``claude_prompts/pangaea_fits.md`` D1): the 1,593
spectral-truth ids under the **approved defaults** — native ``insitu`` noise
(10 % imputed where the compilation quotes none), ``maxfev = 40000``, red-peaked
spectra declined *before* fitting — after Round 1 showed the committed
``multi_L23_PANGAEA_v2`` page understated every algorithm through a scoring
artefact (5 % flat noise plus post-hoc ``out_of_scope``).  The sweep was run by
``reports/scripts/pangaea_fits_report.py`` (Round 2); this driver gives it the
same stage-2/stage-3 treatment every other published sweep has, so it sits on
the site as its own page beside the mixed sweep rather than replacing it (the
investigation's recommendation, and the qualifying-exam prompt 8 decision).

Usage (one stage per call, mirroring ``expb_giop/build_v1.py``)::

    python build_v1.py <flg>

    2  metrics -> metrics parquets for the sweep
    3  report  -> exemplar page + cross-algorithm page, fold into the
                  leaderboard, rebuild the landing page

There is no stage 1: the sweep exists and re-running it is the report
script's job.  ``--sweep`` overrides the sweep id (default ``pangaea_fits_v2``).
"""

from __future__ import annotations

import argparse

#: The sweep this driver publishes.
SWEEP_ID = 'pangaea_fits_v2'


def main(flg, *, sweep_id=SWEEP_ID, landing=True):
    """Run one stage for ``sweep_id``.  Returns what the stage produced."""
    flg = int(flg)
    if flg == 2:
        from ioptics import metrics
        return metrics.compute(sweep_id)
    if flg == 3:
        from ioptics import report
        # exemplars first: the cross-algorithm page links this one only when
        # the file already exists (a dangling :doc: fails sphinx -W).
        ex = report.standard.build_exemplars(sweep_id)
        page = report.standard.build(sweep_id, kind='cross_algorithm')
        if landing:
            # fold into the cross-sweep leaderboard and rebuild the landing page
            # (headline board + sweep cards + interactive widget + full grid).
            report.standard.build_landing()
        return ex, page
    if flg == 0:
        return None
    raise SystemExit(f'unknown stage {flg}; use 2 (metrics) or 3 (report)')


def _cli(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('flg', nargs='?', type=int, default=0,
                   help='stage: 2 metrics, 3 report (0 = no-op)')
    p.add_argument('--sweep', default=SWEEP_ID)
    p.add_argument('--no-landing', action='store_true',
                   help='stage 3: build the pages but do not touch the landing page')
    a = p.parse_args(argv)
    out = main(a.flg, sweep_id=a.sweep, landing=not a.no_landing)
    if out is not None:
        print(out)


if __name__ == '__main__':
    _cli()

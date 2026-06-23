=======
Reports
=======

This is the single **accumulating** report site for IOPtics. As sweeps are run,
each one contributes a provenance-stamped report page under this section, and
the persistent **leaderboard** (ranking algorithms across all sweeps) becomes
the landing page (design doc §Reporting).

Report pages are generated **on demand** by a sweep's build script
(``ioptics/runs/prototypes/<name>/build_vN.py``, stage flag 3) via
:func:`ioptics.report.standard.build`, then committed into this tree so Read the
Docs builds them directly. The heavy artifacts (parquet tables, raw MCMC
chains) stay under ``$OS_COLOR/IOPtics/runs/`` and are not committed.

.. note::

   No sweeps have been published yet (the run/metrics/report layers arrive in
   Stages 2–5). As each ``<sweep_id>.rst`` page is generated it is linked from
   the toctree below — :mod:`ioptics.report.rst` (Stage 5) will switch this to a
   glob so new pages are picked up automatically.

.. toctree::
   :maxdepth: 1

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

Reading the leaderboard
-----------------------

The table below is the **persistent, cross-sweep leaderboard**: every sweep's
accuracy at the diagnostic reference wavelengths (e.g. 440, 555 nm) is folded
into one ranked store (:func:`ioptics.report.leaderboard.update`), so the
standing comparison grows as algorithms and datasets accumulate. (The fold is
idempotent — re-running a sweep just replaces its rows.) Each row is one
algorithm's score for one contest — a ``(dataset, component, reference
wavelength, trophic stratum)`` combination:

- **rank** — 1 = best in that contest. The default ordering is by **wins**,
  breaking ties by :math:`|\text{bias}|` then MAE (see below).
- **win_frac** — the head-to-head win fraction: for each individual spectrum,
  the algorithm whose retrieval is *closer to the true value* wins; ``win_frac``
  is the share of spectra it wins. 0.5 = a tie, 1.0 = always closest.
- **mae** — *mean absolute error*, computed on :math:`\log_{10}` values so it
  reads as a **multiplicative** (fractional) error: ``0`` is perfect, ``0.1`` ≈
  “typically off by ~10 %”, ``0.3`` ≈ ~2× off. (Log space is used because IOPs
  span orders of magnitude.)
- **bias** — the *signed* version of MAE: positive = the algorithm systematically
  over-estimates, negative = under-estimates (again multiplicative; 0 =
  unbiased).
- **coverage68 / coverage95** — a **calibration** check on the reported
  uncertainties: the fraction of truth values that fall inside the retrieval's
  68 % / 95 % confidence interval. Well-calibrated error bars land near 0.68 /
  0.95; much lower means the stated uncertainties are too tight (over-confident).

Each sweep also gets its own provenance-stamped page (linked below) with the
figures and tables behind these numbers.

.. LEADERBOARD_START (auto-generated; do not edit)

Leaderboard
-----------

.. list-table:: Leaderboard
   :header-rows: 1

   * - dataset
     - component
     - ref_wave
     - stratum
     - rank
     - algorithm
     - win_frac
     - bias
     - mae
     - coverage68
     - coverage95
     - frac_ok
     - caveat
   * - GLORIA
     - a
     - 440
     - all
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a
     - 440
     - all
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a
     - 440
     - all
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a
     - 440
     - all
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a
     - 440
     - eutrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a
     - 440
     - eutrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a
     - 440
     - eutrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a
     - 440
     - eutrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a
     - 440
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a
     - 440
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a
     - 440
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a
     - 440
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a
     - 440
     - unknown
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a
     - 440
     - unknown
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a
     - 440
     - unknown
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a
     - 440
     - unknown
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a
     - 443
     - all
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a
     - 443
     - all
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a
     - 443
     - all
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a
     - 443
     - all
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a
     - 443
     - eutrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a
     - 443
     - eutrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a
     - 443
     - eutrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a
     - 443
     - eutrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a
     - 443
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a
     - 443
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a
     - 443
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a
     - 443
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a
     - 443
     - unknown
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a
     - 443
     - unknown
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a
     - 443
     - unknown
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a
     - 443
     - unknown
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a_dg
     - 440
     - all
     - 1
     - expb_pow2flat
     - 0.611
     - 0.442
     - 1.31
     - 0.5
     - 0.833
     - 0.1
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - all
     - 2
     - expb_pow
     - 0.5
     - 0.136
     - 1.86
     - 0.5
     - 0.667
     - 0.1
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - all
     - 3
     - expb_powflex
     - 0.5
     - -0.627
     - 6.49
     - 0.333
     - 0.667
     - 0.1
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - all
     - 4
     - expb_pow2
     - 0.389
     - 0.302
     - 1.36
     - 0.833
     - 0.833
     - 0.1
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - eutrophic
     - 1
     - expb_pow2flat
     - 0.667
     - 0.406
     - 1.84
     - 0.5
     - 0.75
     - 0.0909
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - eutrophic
     - 2
     - expb_powflex
     - 0.583
     - -0.787
     - 14.7
     - 0.5
     - 0.5
     - 0.0909
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - eutrophic
     - 3
     - expb_pow2
     - 0.5
     - 0.303
     - 1.89
     - 0.75
     - 0.75
     - 0.0909
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - eutrophic
     - 4
     - expb_pow
     - 0.25
     - -0.00451
     - 2.98
     - 0.5
     - 0.5
     - 0.0909
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - unknown
     - 1
     - expb_pow
     - 1
     - 0.479
     - 0.479
     - 0.5
     - 1
     - 0.111
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - unknown
     - 2
     - expb_pow2flat
     - 0.5
     - 0.515
     - 0.515
     - 0.5
     - 1
     - 0.111
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - unknown
     - 3
     - expb_powflex
     - 0.333
     - 0.145
     - 0.702
     - 0
     - 1
     - 0.111
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - unknown
     - 4
     - expb_pow2
     - 0.167
     - 0.299
     - 0.575
     - 1
     - 1
     - 0.111
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - all
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - all
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - all
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - all
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - eutrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - eutrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - eutrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - eutrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - unknown
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - unknown
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - unknown
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 443
     - unknown
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - CDOM_vs_adg
   * - GLORIA
     - a_ph
     - 440
     - all
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a_ph
     - 440
     - all
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a_ph
     - 440
     - all
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a_ph
     - 440
     - all
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a_ph
     - 440
     - eutrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a_ph
     - 440
     - eutrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a_ph
     - 440
     - eutrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a_ph
     - 440
     - eutrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a_ph
     - 440
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a_ph
     - 440
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a_ph
     - 440
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a_ph
     - 440
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a_ph
     - 440
     - unknown
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a_ph
     - 440
     - unknown
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a_ph
     - 440
     - unknown
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a_ph
     - 440
     - unknown
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a_ph
     - 443
     - all
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a_ph
     - 443
     - all
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a_ph
     - 443
     - all
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a_ph
     - 443
     - all
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - a_ph
     - 443
     - eutrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a_ph
     - 443
     - eutrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a_ph
     - 443
     - eutrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a_ph
     - 443
     - eutrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - a_ph
     - 443
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a_ph
     - 443
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a_ph
     - 443
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a_ph
     - 443
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - a_ph
     - 443
     - unknown
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a_ph
     - 443
     - unknown
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a_ph
     - 443
     - unknown
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - a_ph
     - 443
     - unknown
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb
     - 555
     - all
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb
     - 555
     - all
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb
     - 555
     - all
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb
     - 555
     - all
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb
     - 555
     - eutrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb
     - 555
     - eutrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb
     - 555
     - eutrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb
     - 555
     - eutrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb
     - 555
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb
     - 555
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb
     - 555
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb
     - 555
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb
     - 555
     - unknown
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb
     - 555
     - unknown
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb
     - 555
     - unknown
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb
     - 555
     - unknown
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb
     - 670
     - all
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb
     - 670
     - all
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb
     - 670
     - all
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb
     - 670
     - all
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb
     - 670
     - eutrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb
     - 670
     - eutrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb
     - 670
     - eutrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb
     - 670
     - eutrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb
     - 670
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb
     - 670
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb
     - 670
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb
     - 670
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb
     - 670
     - unknown
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb
     - 670
     - unknown
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb
     - 670
     - unknown
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb
     - 670
     - unknown
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb_p
     - 555
     - all
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb_p
     - 555
     - all
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb_p
     - 555
     - all
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb_p
     - 555
     - all
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb_p
     - 555
     - eutrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb_p
     - 555
     - eutrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb_p
     - 555
     - eutrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb_p
     - 555
     - eutrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb_p
     - 555
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb_p
     - 555
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb_p
     - 555
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb_p
     - 555
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb_p
     - 555
     - unknown
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb_p
     - 555
     - unknown
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb_p
     - 555
     - unknown
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb_p
     - 555
     - unknown
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb_p
     - 670
     - all
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb_p
     - 670
     - all
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb_p
     - 670
     - all
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb_p
     - 670
     - all
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.1
     - 
   * - GLORIA
     - bb_p
     - 670
     - eutrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb_p
     - 670
     - eutrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb_p
     - 670
     - eutrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb_p
     - 670
     - eutrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.0909
     - 
   * - GLORIA
     - bb_p
     - 670
     - mesotrophic
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb_p
     - 670
     - mesotrophic
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb_p
     - 670
     - mesotrophic
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb_p
     - 670
     - mesotrophic
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.143
     - 
   * - GLORIA
     - bb_p
     - 670
     - unknown
     - 1
     - expb_pow
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb_p
     - 670
     - unknown
     - 2
     - expb_powflex
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb_p
     - 670
     - unknown
     - 3
     - expb_pow2flat
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 
   * - GLORIA
     - bb_p
     - 670
     - unknown
     - 4
     - expb_pow2
     - nan
     - nan
     - nan
     - nan
     - nan
     - 0.111
     - 


.. LEADERBOARD_END
.. toctree::
   :maxdepth: 1
   :glob:

   */*

=================================
Algorithm profile — expb_pow2flat
=================================

In one paragraph
----------------

``expb_pow2flat`` has scoreable results on **GLORIA** across 1 sweep(s). Its best contest is a_dg(440) on GLORIA, at mae 0.657 (65.7% multiplicative error); its worst is a_dg(440) on GLORIA at 1.39. It produced a usable fit for 14%-86% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

What it parameterizes
---------------------

Read from the registry entry that sweeps actually run, so it cannot drift from the configuration behind the numbers below.

Not in the registry.

Where it has been evaluated
---------------------------

.. list-table:: What has been evaluated on what
   :header-rows: 1
   :stub-columns: 1
   :widths: auto

   * - algorithm
     - GLORIA
   * - ``expb_pow2flat``
     - scored (n=12)

Accuracy, by dataset and contest
--------------------------------

One row per contest **and trophic stratum** — ``all`` is the pooled population, the others its Chl bins (:data:`ioptics.metrics.CHL_BINS`), so a pooled row and its bins are not independent results. This algorithm has rows in 4 strata.

.. list-table:: expb_pow2flat — scored contests
   :header-rows: 1
   :widths: auto

   * - dataset
     - component
     - ref_wave
     - stratum
     - fit_method
     - rank
     - ranking
     - mae
     - bias
     - win_frac
     - frac_ok
     - caveat
   * - GLORIA
     - a_dg
     - 440
     - all
     - chisq
     - —
     - sole competitor
     - 1
     - 0.301
     - 0.361
     - 0.21
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.945
     - 0.523
     - 0.333
     - 0.136
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 1.39
     - -0.11
     - 0.333
     - 0.857
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - unknown
     - chisq
     - —
     - sole competitor
     - 0.657
     - 0.657
     - 0.444
     - 0.222
     - CDOM_vs_adg

Are its uncertainties honest?
-----------------------------

A retrieval can be the most accurate and still be over-confident: the verdict compares empirical coverage with its nominal 0.68 / 0.95 target, and *consistent* means "not distinguishable from nominal at this sample size" rather than "calibrated".

.. list-table:: expb_pow2flat — interval calibration
   :header-rows: 1
   :widths: auto

   * - dataset
     - component
     - ref_wave
     - stratum
     - coverage68
     - coverage95
     - coverage_n
   * - GLORIA
     - a_dg
     - 440
     - all
     - 0.417
     - 0.917
     - 12
   * - GLORIA
     - a_dg
     - 440
     - eutrophic
     - 0.6
     - 1
     - 5
   * - GLORIA
     - a_dg
     - 440
     - mesotrophic
     - 0
     - 0.75
     - 4
   * - GLORIA
     - a_dg
     - 440
     - unknown
     - 0.667
     - 1
     - 3

Head-to-head against the others
-------------------------------

.. list-table:: expb_pow2flat — pairwise verdicts
   :header-rows: 1
   :widths: auto

   * - sweep_id
     - dataset
     - component
     - ref_wave
     - model_a
     - model_b
     - n_paired
     - delta_mae
     - d_lo
     - d_hi
     - verdict
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow
     - expb_pow2flat
     - 12
     - -0.00101
     - -0.0309
     - 0.0217
     - indistinguishable
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow2
     - expb_pow2flat
     - 12
     - 0.00502
     - -0.111
     - 0.182
     - underpowered
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow2flat
     - expb_powflex
     - 12
     - -0.057
     - -0.392
     - 0.182
     - underpowered
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow
     - expb_pow2flat
     - 3
     - -0.0367
     - -0.0853
     - 0.0043
     - indistinguishable
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow2
     - expb_pow2flat
     - 3
     - -0.0361
     - -0.085
     - 0.00991
     - indistinguishable
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow2flat
     - expb_powflex
     - 3
     - -0.0962
     - -0.328
     - 0.123
     - underpowered
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow
     - expb_pow2flat
     - 5
     - 0.0133
     - -0.00257
     - 0.0344
     - indistinguishable
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow2
     - expb_pow2flat
     - 5
     - 0.0403
     - -0.217
     - 0.457
     - underpowered
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow2flat
     - expb_powflex
     - 5
     - -0.0555
     - -0.881
     - 0.399
     - underpowered
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow
     - expb_pow2flat
     - 4
     - 0.0163
     - -0.000303
     - 0.036
     - indistinguishable
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow2
     - expb_pow2flat
     - 4
     - -0.00375
     - -0.00815
     - -1.73e-05
     - indistinguishable
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow2flat
     - expb_powflex
     - 4
     - -0.0162
     - -0.0358
     - 0.000303
     - indistinguishable

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

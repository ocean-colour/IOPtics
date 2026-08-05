=============================
Algorithm profile — expb_pow2
=============================

In one paragraph
----------------

``expb_pow2`` has scoreable results on **GLORIA** across 1 sweep(s). Its best contest is a_dg(440) on GLORIA, at mae 0.621 (62.1% multiplicative error); its worst is a_dg(440) on GLORIA at 1.39. It produced a usable fit for 14%-86% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

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
   * - ``expb_pow2``
     - scored (n=12)

Accuracy, by dataset and contest
--------------------------------

.. list-table:: expb_pow2 — scored contests
   :header-rows: 1
   :widths: auto

   * - dataset
     - component
     - ref_wave
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
     - chisq
     - —
     - sole competitor
     - 1.01
     - 0.194
     - 0.639
     - 0.21
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - sole competitor
     - 0.985
     - 0.327
     - 0.6
     - 0.136
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - sole competitor
     - 1.39
     - -0.108
     - 0.667
     - 0.857
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - sole competitor
     - 0.621
     - 0.479
     - 0.667
     - 0.222
     - CDOM_vs_adg

Are its uncertainties honest?
-----------------------------

A retrieval can be the most accurate and still be over-confident: the verdict compares empirical coverage with its nominal 0.68 / 0.95 target, and *consistent* means "not distinguishable from nominal at this sample size" rather than "calibrated".

.. list-table:: expb_pow2 — interval calibration
   :header-rows: 1
   :widths: auto

   * - dataset
     - component
     - ref_wave
     - coverage68
     - coverage95
     - coverage_n
   * - GLORIA
     - a_dg
     - 440
     - 0.5
     - 0.917
     - 12
   * - GLORIA
     - a_dg
     - 440
     - 0.6
     - 1
     - 5
   * - GLORIA
     - a_dg
     - 440
     - 0
     - 0.75
     - 4
   * - GLORIA
     - a_dg
     - 440
     - 1
     - 1
     - 3

Head-to-head against the others
-------------------------------

.. list-table:: expb_pow2 — pairwise verdicts
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
     - expb_pow2
     - 12
     - -0.00603
     - -0.174
     - 0.108
     - underpowered
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
     - expb_pow2
     - expb_powflex
     - 12
     - -0.052
     - -0.237
     - 0.084
     - underpowered
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow
     - expb_pow2
     - 3
     - -0.000549
     - -0.134
     - 0.0849
     - underpowered
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
     - expb_pow2
     - expb_powflex
     - 3
     - -0.132
     - -0.413
     - 0.132
     - underpowered
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow
     - expb_pow2
     - 5
     - -0.027
     - -0.423
     - 0.222
     - underpowered
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
     - expb_pow2
     - expb_powflex
     - 5
     - -0.0152
     - -0.424
     - 0.192
     - underpowered
   * - gloria_turbid_v3
     - GLORIA
     - a_dg
     - 440
     - expb_pow
     - expb_pow2
     - 4
     - 0.02
     - -0.00031
     - 0.0441
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
     - expb_pow2
     - expb_powflex
     - 4
     - -0.02
     - -0.044
     - 0.000285
     - indistinguishable

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

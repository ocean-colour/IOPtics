============================
Algorithm profile — expb_pow
============================

In one paragraph
----------------

``expb_pow`` has scoreable results on **GLORIA** across 1 sweep(s). Its best contest is a_dg(440) on GLORIA, at mae 0.62 (62.0% multiplicative error); its worst is a_dg(440) on GLORIA at 1.41. It produced a usable fit for 14%-86% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

What it parameterizes
---------------------

Read from the registry entry that sweeps actually run, so it cannot drift from the configuration behind the numbers below.

.. list-table::
   :stub-columns: 1
   :widths: auto

   * - a_nw model
     - ExpBricaud
   * - bb_nw model
     - Pow
   * - fit method
     - chisq
   * - sSdg
     - 0.002
   * - RT toggles
     - ``double_gaussian``, ``phi_C``, ``variable_Gordon``

Where it has been evaluated
---------------------------

.. list-table:: What has been evaluated on what
   :header-rows: 1
   :stub-columns: 1
   :widths: auto

   * - algorithm
     - GLORIA
   * - ``expb_pow``
     - scored (n=12)

Accuracy, by dataset and contest
--------------------------------

.. list-table:: expb_pow — scored contests
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
     - 1
     - 0.289
     - 0.431
     - 0.21
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - sole competitor
     - 0.958
     - 0.519
     - 0.4
     - 0.136
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - sole competitor
     - 1.41
     - -0.116
     - 0.375
     - 0.857
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - sole competitor
     - 0.62
     - 0.62
     - 0.556
     - 0.222
     - CDOM_vs_adg

Are its uncertainties honest?
-----------------------------

A retrieval can be the most accurate and still be over-confident: the verdict compares empirical coverage with its nominal 0.68 / 0.95 target, and *consistent* means "not distinguishable from nominal at this sample size" rather than "calibrated".

.. list-table:: expb_pow — interval calibration
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
     - 0.417
     - 0.75
     - 12
   * - GLORIA
     - a_dg
     - 440
     - 0.6
     - 0.6
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
     - 0.667
     - 1
     - 3

Head-to-head against the others
-------------------------------

.. list-table:: expb_pow — pairwise verdicts
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
     - expb_pow
     - expb_powflex
     - 12
     - -0.058
     - -0.36
     - 0.191
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
     - expb_pow
     - expb_powflex
     - 3
     - -0.133
     - -0.328
     - 0.000739
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
     - expb_pow
     - expb_powflex
     - 5
     - -0.0422
     - -0.847
     - 0.402
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
     - expb_pow
     - expb_powflex
     - 4
     - 6.36e-05
     - 3.9e-09
     - 0.00014
     - indistinguishable

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

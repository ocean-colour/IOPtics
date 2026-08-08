============================
Algorithm profile — expb_pow
============================

In one paragraph
----------------

``expb_pow`` has scoreable results on **GLORIA, L23, PANGAEA** across 3 sweep(s). Its best contest is bb(555) on L23, at mae 0.0133 (1.3% multiplicative error); its worst is a_ph(440) on L23 at 4.36. It produced a usable fit for 12%-100% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

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
     - L23
     - PANGAEA
   * - ``expb_pow``
     - scored (n=12)
     - scored (n=3334)
     - scored (n=243)

Accuracy, by dataset and contest
--------------------------------

One row per contest **and trophic stratum** — ``all`` is the pooled population, the others its Chl bins (:data:`ioptics.metrics.CHL_BINS`), so a pooled row and its bins are not independent results. This algorithm has rows in 5 strata.

.. list-table:: expb_pow — scored contests
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
     - 0.289
     - 0.431
     - 0.21
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - eutrophic
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
     - mesotrophic
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
     - unknown
     - chisq
     - —
     - sole competitor
     - 0.62
     - 0.62
     - 0.556
     - 0.222
     - CDOM_vs_adg
   * - L23
     - a
     - 440
     - all
     - chisq
     - 1
     - ranked
     - 0.0546
     - 0.0225
     - 0.847
     - 0.998
     - 
   * - L23
     - a
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - 0.0624
     - 0.00518
     - 0.7
     - 1
     - 
   * - L23
     - a
     - 440
     - all
     - mcmc
     - —
     - sole competitor
     - 0.042
     - -0.0318
     - —
     - 1
     - 
   * - L23
     - a
     - 440
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.48
     - 0.478
     - 0.412
     - 0.966
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - chisq
     - 1
     - ranked
     - 0.0381
     - 0.00207
     - 0.885
     - 1
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0641
     - -0.0209
     - 0.615
     - 1
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - mcmc
     - —
     - sole competitor
     - 0.0609
     - -0.0574
     - —
     - 1
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0591
     - 0.0554
     - 0.857
     - 1
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - chisq
     - 2
     - ranked
     - 0.0248
     - 0.00243
     - 0.804
     - 1
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - mcmc
     - —
     - sole competitor
     - 0.0234
     - -0.00558
     - —
     - 1
     - 
   * - L23
     - a
     - 443
     - all
     - chisq
     - 1
     - ranked
     - 0.0526
     - 0.0227
     - 0.874
     - 0.998
     - 
   * - L23
     - a
     - 443
     - all
     - chisq
     - —
     - indistinguishable
     - 0.0595
     - 0.00797
     - 0.7
     - 1
     - 
   * - L23
     - a
     - 443
     - all
     - mcmc
     - —
     - sole competitor
     - 0.0417
     - -0.0257
     - —
     - 1
     - 
   * - L23
     - a
     - 443
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.451
     - 0.449
     - 0.468
     - 0.966
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - chisq
     - 1
     - ranked
     - 0.037
     - 0.00315
     - 0.912
     - 1
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0592
     - -0.0178
     - 0.615
     - 1
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - mcmc
     - —
     - sole competitor
     - 0.0564
     - -0.0534
     - —
     - 1
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0601
     - 0.0576
     - 0.857
     - 1
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - chisq
     - 2
     - ranked
     - 0.0243
     - 0.0047
     - 0.825
     - 1
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - mcmc
     - —
     - sole competitor
     - 0.0272
     - 0.00278
     - —
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - 0.222
     - 0.0294
     - 0.391
     - 0.998
     - 
   * - L23
     - a_dg
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - 0.184
     - -0.00475
     - 0.35
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - all
     - mcmc
     - —
     - sole competitor
     - 0.246
     - 0.162
     - —
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.601
     - 0.382
     - 0.354
     - 0.966
     - 
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.204
     - 0.0237
     - 0.397
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.184
     - -0.0143
     - 0.308
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - mcmc
     - —
     - sole competitor
     - 0.345
     - 0.181
     - —
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.185
     - 0.0132
     - 0.429
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.205
     - -0.0271
     - 0.377
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - mcmc
     - —
     - sole competitor
     - 0.154
     - 0.144
     - —
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - all
     - chisq
     - —
     - indistinguishable
     - 0.235
     - 0.0177
     - 0.379
     - 0.998
     - 
   * - L23
     - a_dg
     - 443
     - all
     - chisq
     - —
     - indistinguishable
     - 0.201
     - -0.0171
     - 0.3
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - all
     - mcmc
     - —
     - sole competitor
     - 0.253
     - 0.157
     - —
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.597
     - 0.361
     - 0.334
     - 0.966
     - 
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.217
     - 0.0135
     - 0.385
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.198
     - -0.0226
     - 0.308
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - mcmc
     - —
     - sole competitor
     - 0.363
     - 0.181
     - —
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.222
     - -0.0423
     - 0.365
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.207
     - -0.00679
     - 0.286
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - mcmc
     - —
     - sole competitor
     - 0.152
     - 0.133
     - —
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - all
     - chisq
     - 1
     - ranked
     - 0.419
     - -0.122
     - 0.617
     - 0.998
     - 
   * - L23
     - a_ph
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - 1.17
     - -0.384
     - 0.4
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - all
     - mcmc
     - —
     - sole competitor
     - 1.64
     - -0.613
     - —
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.516
     - 0.46
     - 0.584
     - 0.966
     - 
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - chisq
     - 1
     - ranked
     - 0.414
     - -0.164
     - 0.623
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 1.62
     - -0.545
     - 0.538
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - mcmc
     - —
     - sole competitor
     - 4.36
     - -0.805
     - —
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - chisq
     - 1
     - ranked
     - 0.417
     - -0.0692
     - 0.601
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - chisq
     - 2
     - ranked
     - 0.531
     - 0.0793
     - 0.143
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - mcmc
     - —
     - sole competitor
     - 0.296
     - -0.228
     - —
     - 1
     - 
   * - L23
     - a_ph
     - 443
     - all
     - chisq
     - 1
     - ranked
     - 0.402
     - -0.105
     - 0.675
     - 0.998
     - 
   * - L23
     - a_ph
     - 443
     - all
     - chisq
     - —
     - indistinguishable
     - 1.15
     - -0.362
     - 0.4
     - 1
     - 
   * - L23
     - a_ph
     - 443
     - all
     - mcmc
     - —
     - sole competitor
     - 1.5
     - -0.588
     - —
     - 1
     - 
   * - L23
     - a_ph
     - 443
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.481
     - 0.425
     - 0.669
     - 0.966
     - 
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - chisq
     - 1
     - ranked
     - 0.394
     - -0.149
     - 0.686
     - 1
     - 
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 1.57
     - -0.529
     - 0.538
     - 1
     - 

(64 further rows are on the :doc:`/reports/leaderboard_full` page.)

Are its uncertainties honest?
-----------------------------

A retrieval can be the most accurate and still be over-confident: the verdict compares empirical coverage with its nominal 0.68 / 0.95 target, and *consistent* means "not distinguishable from nominal at this sample size" rather than "calibrated".

.. list-table:: expb_pow — interval calibration
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
     - 0.75
     - 12
   * - GLORIA
     - a_dg
     - 440
     - eutrophic
     - 0.6
     - 0.6
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
   * - L23
     - a
     - 440
     - all
     - 0.558
     - 0.807
     - 3.3e+03
   * - L23
     - a
     - 440
     - all
     - 0.421
     - 1
     - 19
   * - L23
     - a
     - 440
     - all
     - 0.875
     - 1
     - 8
   * - L23
     - a
     - 440
     - eutrophic
     - 0.0351
     - 0.076
     - 171
   * - L23
     - a
     - 440
     - mesotrophic
     - 0.616
     - 0.859
     - 2.48e+03
   * - L23
     - a
     - 440
     - mesotrophic
     - 0.5
     - 1
     - 12
   * - L23
     - a
     - 440
     - mesotrophic
     - 0.75
     - 1
     - 4
   * - L23
     - a
     - 440
     - oligotrophic
     - 0.286
     - 1
     - 7
   * - L23
     - a
     - 440
     - oligotrophic
     - 0.471
     - 0.802
     - 647
   * - L23
     - a
     - 440
     - oligotrophic
     - 1
     - 1
     - 4
   * - L23
     - a
     - 443
     - all
     - 0.538
     - 0.801
     - 3.3e+03
   * - L23
     - a
     - 443
     - all
     - 0.368
     - 1
     - 19
   * - L23
     - a
     - 443
     - all
     - 0.75
     - 1
     - 8
   * - L23
     - a
     - 443
     - eutrophic
     - 0.0351
     - 0.105
     - 171
   * - L23
     - a
     - 443
     - mesotrophic
     - 0.6
     - 0.856
     - 2.48e+03
   * - L23
     - a
     - 443
     - mesotrophic
     - 0.5
     - 1
     - 12
   * - L23
     - a
     - 443
     - mesotrophic
     - 0.75
     - 1
     - 4
   * - L23
     - a
     - 443
     - oligotrophic
     - 0.143
     - 1
     - 7
   * - L23
     - a
     - 443
     - oligotrophic
     - 0.437
     - 0.773
     - 647
   * - L23
     - a
     - 443
     - oligotrophic
     - 0.75
     - 1
     - 4
   * - L23
     - a_dg
     - 440
     - all
     - 0.758
     - 0.909
     - 3.31e+03
   * - L23
     - a_dg
     - 440
     - all
     - 1
     - 1
     - 20
   * - L23
     - a_dg
     - 440
     - all
     - 0.375
     - 1
     - 8
   * - L23
     - a_dg
     - 440
     - eutrophic
     - 0.374
     - 0.573
     - 171
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 0.748
     - 0.913
     - 2.5e+03
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 1
     - 1
     - 13
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 0
     - 1
     - 4
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 1
     - 1
     - 7
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 0.897
     - 0.983
     - 648
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 0.75
     - 1
     - 4
   * - L23
     - a_dg
     - 443
     - all
     - 0.766
     - 0.913
     - 3.31e+03
   * - L23
     - a_dg
     - 443
     - all
     - 1
     - 1
     - 20
   * - L23
     - a_dg
     - 443
     - all
     - 0.375
     - 1
     - 8
   * - L23
     - a_dg
     - 443
     - eutrophic
     - 0.398
     - 0.596
     - 171
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 0.756
     - 0.917
     - 2.5e+03
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 1
     - 1
     - 13
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 0
     - 1
     - 4
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 0.903
     - 0.985
     - 648
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 1
     - 1
     - 7
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 0.75
     - 1
     - 4
   * - L23
     - a_ph
     - 440
     - all
     - 0.775
     - 0.954
     - 3.3e+03
   * - L23
     - a_ph
     - 440
     - all
     - 1
     - 1
     - 19
   * - L23
     - a_ph
     - 440
     - all
     - 0.5
     - 0.875
     - 8
   * - L23
     - a_ph
     - 440
     - eutrophic
     - 0.181
     - 0.544
     - 171
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 0.767
     - 0.97
     - 2.48e+03
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 1
     - 1
     - 12
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 0.25
     - 0.75
     - 4
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 0.964
     - 1
     - 647
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 1
     - 1
     - 7
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 0.75
     - 1
     - 4
   * - L23
     - a_ph
     - 443
     - all
     - 0.788
     - 0.956
     - 3.3e+03
   * - L23
     - a_ph
     - 443
     - all
     - 1
     - 1
     - 19
   * - L23
     - a_ph
     - 443
     - all
     - 0.625
     - 0.875
     - 8
   * - L23
     - a_ph
     - 443
     - eutrophic
     - 0.216
     - 0.561
     - 171
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - 0.781
     - 0.971
     - 2.48e+03
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - 1
     - 1
     - 12

(64 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
   * - expb_giop_L23_test20
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 20
     - -0.0102
     - -0.0341
     - 0.0103
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 7
     - -0.0113
     - -0.0181
     - -0.00322
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 13
     - -0.00956
     - -0.0442
     - 0.02
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 20
     - -0.0124
     - -0.0337
     - 0.00722
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 7
     - -0.0133
     - -0.0193
     - -0.00662
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 13
     - -0.0119
     - -0.0426
     - 0.0183
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 20
     - 0.00292
     - -0.00944
     - 0.0186
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 7
     - 0.00271
     - -0.00128
     - 0.0074
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 13
     - 0.00303
     - -0.0177
     - 0.0262
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 20
     - -0.0345
     - -0.0739
     - 0.0101
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 7
     - -0.0272
     - -0.0431
     - -0.00931
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 13
     - -0.0385
     - -0.0946
     - 0.0304
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - a_ph
     - 440
     - expb_pow
     - giop
     - 20
     - 0.845
     - -0.0951
     - 4.31
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - a_ph
     - 440
     - expb_pow
     - giop
     - 7
     - 0.194
     - 0.0392
     - 0.359
     - giop
   * - expb_giop_L23_test20
     - L23
     - a_ph
     - 440
     - expb_pow
     - giop
     - 13
     - 1.3
     - -0.255
     - 9.25
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - a_ph
     - 443
     - expb_pow
     - giop
     - 20
     - 0.795
     - -0.142
     - 4.08
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - a_ph
     - 443
     - expb_pow
     - giop
     - 7
     - 0.136
     - 0.0146
     - 0.245
     - giop
   * - expb_giop_L23_test20
     - L23
     - a_ph
     - 443
     - expb_pow
     - giop
     - 13
     - 1.24
     - -0.268
     - 9.75
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - a_dg
     - 440
     - expb_pow
     - giop
     - 20
     - 0.0588
     - -0.0229
     - 0.146
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - a_dg
     - 440
     - expb_pow
     - giop
     - 7
     - 0.0738
     - -0.0384
     - 0.206
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - a_dg
     - 440
     - expb_pow
     - giop
     - 13
     - 0.0507
     - -0.053
     - 0.168
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - a_dg
     - 443
     - expb_pow
     - giop
     - 20
     - 0.0648
     - -0.0276
     - 0.155
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - a_dg
     - 443
     - expb_pow
     - giop
     - 7
     - 0.0835
     - -0.054
     - 0.217
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - a_dg
     - 443
     - expb_pow
     - giop
     - 13
     - 0.0547
     - -0.0681
     - 0.182
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - bb_p
     - 555
     - expb_pow
     - giop
     - 20
     - 0.0119
     - -0.0206
     - 0.0528
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - bb_p
     - 555
     - expb_pow
     - giop
     - 7
     - 0.00597
     - -0.00408
     - 0.0181
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - bb_p
     - 555
     - expb_pow
     - giop
     - 13
     - 0.0151
     - -0.0319
     - 0.0762
     - indistinguishable
   * - expb_giop_L23_test20
     - L23
     - bb_p
     - 670
     - expb_pow
     - giop
     - 20
     - -0.0541
     - -0.116
     - 0.0421
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - bb_p
     - 670
     - expb_pow
     - giop
     - 7
     - -0.062
     - -0.1
     - -0.0241
     - underpowered
   * - expb_giop_L23_test20
     - L23
     - bb_p
     - 670
     - expb_pow
     - giop
     - 13
     - -0.0498
     - -0.146
     - 0.0751
     - underpowered
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
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 3.28e+03
     - -0.131
     - -0.135
     - -0.128
     - expb_pow
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 440
     - expb_pow
     - gsm
     - 3.28e+03
     - -0.0426
     - -0.0452
     - -0.0402
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 637
     - -0.108
     - -0.112
     - -0.105
     - expb_pow
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 440
     - expb_pow
     - gsm
     - 648
     - -0.0103
     - -0.0126
     - -0.00786
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 2.49e+03
     - -0.153
     - -0.155
     - -0.15
     - expb_pow
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 440
     - expb_pow
     - gsm
     - 2.49e+03
     - -0.0522
     - -0.0552
     - -0.0495
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 159
     - 0.16
     - 0.12
     - 0.204
     - giop
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 440
     - expb_pow
     - gsm
     - 149
     - -0.0155
     - -0.0526
     - 0.0233
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 3.28e+03
     - -0.129
     - -0.132
     - -0.126
     - expb_pow
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - gsm
     - 3.28e+03
     - -0.0586
     - -0.0614
     - -0.056
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 637
     - -0.108
     - -0.112
     - -0.105
     - expb_pow
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - gsm
     - 648
     - -0.0146
     - -0.017
     - -0.0123
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 2.49e+03
     - -0.15
     - -0.153
     - -0.147
     - expb_pow
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - gsm
     - 2.49e+03
     - -0.0688
     - -0.0718
     - -0.0657
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 159
     - 0.161
     - 0.119
     - 0.204
     - giop
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - gsm
     - 149
     - -0.0946
     - -0.131
     - -0.0565
     - underpowered
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 3.28e+03
     - -0.0267
     - -0.0284
     - -0.0251
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - expb_pow
     - gsm
     - 3.28e+03
     - 8.57e-05
     - -0.00127
     - 0.00147
     - indistinguishable

(97 further rows are on the :doc:`/reports/leaderboard_full` page.)

What varied between sweeps
--------------------------

This profile pools every sweep that ran ``expb_pow``. The runs were **not**
identically configured — each row below is one distinct persisted
algorithm block (``algo_digest``), so numbers from different rows are
not strictly like-for-like:

.. list-table:: Configurations pooled here
   :header-rows: 1
   :widths: auto

   * - sweep_id
     - algo_digest
     - prov_schema
     - versions
     - bing
     - ocpy
   * - expb_giop_L23_test20
     - 75f63215deaf
     - 2
     - 0.0.dev0@61c83e0
     - 0.0.dev0@f242b0e
     - 0.1.0@3aed28a
   * - gloria_turbid_v3
     - 75f63215deaf
     - 0
     - 0.0.dev0@c70040c
     - 0.0.dev0@f242b0e
     - da6dff9
   * - multi_L23_PANGAEA_v2
     - 75f63215deaf
     - 2
     - 0.0.dev0@61c83e0
     - 0.0.dev0@f242b0e
     - 0.1.0@3aed28a


.. note::

   These sweeps were recorded under **different provenance schemas** (0, 2; current is 2). A block written under an earlier schema could not record ``maxfev`` or the MCMC settings, so a digest difference here may reflect what was *written down* rather than what was configured — and, in the other direction, two blocks can agree while one of them silently ran a raised iteration budget.

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

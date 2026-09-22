============================
Algorithm profile — expb_pow
============================

In one paragraph
----------------

``expb_pow`` has scoreable results on **GLORIA, L23, PANGAEA** across 5 sweep(s). Its best contest is bb(555) on L23, at mae 0.0133 (1.3% multiplicative error); its worst is a_ph(440) on L23 at 4.36. It produced a usable fit for 12%-100% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

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
   * - maxfev
     - 40000
   * - RT toggles
     - ``Bp_value``, ``cdom_fraction``, ``double_gaussian``, ``phi_C``, ``rt_backend``, ``variable_Gordon``

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
     - scored (n=6639)
     - scored (n=773)

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
     - 0.0548
     - 0.0227
     - 0.846
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
     - chisq
     - —
     - indistinguishable
     - 0.0987
     - 0.0411
     - 0.575
     - 0.995
     - 
   * - L23
     - a
     - 440
     - all
     - mcmc
     - 1
     - ranked (no head-to-head)
     - 0.0681
     - 0.0178
     - —
     - 0.995
     - 
   * - L23
     - a
     - 440
     - all
     - mcmc
     - 2
     - ranked (no head-to-head)
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
     - 1
     - ranked
     - 0.482
     - 0.481
     - 0.41
     - 0.972
     - 
   * - L23
     - a
     - 440
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.541
     - 0.535
     - 0.28
     - 0.91
     - 
   * - L23
     - a
     - 440
     - eutrophic
     - mcmc
     - —
     - sole competitor
     - 0.458
     - 0.458
     - —
     - 0.91
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
     - chisq
     - —
     - indistinguishable
     - 0.0865
     - 0.0191
     - 0.555
     - 1
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - mcmc
     - 1
     - ranked (no head-to-head)
     - 0.055
     - -0.000367
     - —
     - 1
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - mcmc
     - 2
     - ranked (no head-to-head)
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
     - chisq
     - —
     - indistinguishable
     - 0.0547
     - 0.0264
     - 0.737
     - 1
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - mcmc
     - 1
     - ranked (no head-to-head)
     - 0.037
     - -0.00209
     - —
     - 1
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - mcmc
     - 2
     - ranked (no head-to-head)
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
     - 0.0528
     - 0.0229
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
     - chisq
     - —
     - indistinguishable
     - 0.0949
     - 0.0401
     - 0.585
     - 0.995
     - 
   * - L23
     - a
     - 443
     - all
     - mcmc
     - 1
     - ranked (no head-to-head)
     - 0.0655
     - 0.0175
     - —
     - 0.995
     - 
   * - L23
     - a
     - 443
     - all
     - mcmc
     - 2
     - ranked (no head-to-head)
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
     - 1
     - ranked
     - 0.453
     - 0.452
     - 0.465
     - 0.972
     - 
   * - L23
     - a
     - 443
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.505
     - 0.497
     - 0.28
     - 0.91
     - 
   * - L23
     - a
     - 443
     - eutrophic
     - mcmc
     - —
     - sole competitor
     - 0.424
     - 0.424
     - —
     - 0.91
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
     - chisq
     - —
     - indistinguishable
     - 0.0837
     - 0.0192
     - 0.559
     - 1
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - mcmc
     - 1
     - ranked (no head-to-head)
     - 0.0533
     - 7.8e-05
     - —
     - 1
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - mcmc
     - 2
     - ranked (no head-to-head)
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
     - chisq
     - —
     - indistinguishable
     - 0.0527
     - 0.0271
     - 0.771
     - 1
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - mcmc
     - 1
     - ranked (no head-to-head)
     - 0.0362
     - 0.000129
     - —
     - 1
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - mcmc
     - 2
     - ranked (no head-to-head)
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
     - 0.0296
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
     - chisq
     - 3
     - ranked
     - 0.32
     - 0.052
     - 0.306
     - 0.995
     - 
   * - L23
     - a_dg
     - 440
     - all
     - mcmc
     - 1
     - ranked (no head-to-head)
     - 0.274
     - 0.129
     - —
     - 0.995
     - 
   * - L23
     - a_dg
     - 440
     - all
     - mcmc
     - 2
     - ranked (no head-to-head)
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
     - 1
     - ranked
     - 0.826
     - 0.415
     - 0.354
     - 0.91
     - 
   * - L23
     - a_dg
     - 440
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.604
     - 0.386
     - 0.352
     - 0.972
     - 
   * - L23
     - a_dg
     - 440
     - eutrophic
     - mcmc
     - —
     - sole competitor
     - 1.21
     - 0.147
     - —
     - 0.91
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
     - chisq
     - 3
     - ranked
     - 0.31
     - 0.045
     - 0.306
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - mcmc
     - 1
     - ranked (no head-to-head)
     - 0.252
     - 0.133
     - —
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - mcmc
     - 2
     - ranked (no head-to-head)
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
     - chisq
     - 3
     - ranked
     - 0.255
     - 0.00261
     - 0.294
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - mcmc
     - 1
     - ranked (no head-to-head)
     - 0.19
     - 0.112
     - —
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - mcmc
     - 2
     - ranked (no head-to-head)
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
     - 0.018
     - 0.379
     - 0.998
     - 
   * - L23
     - a_dg
     - 443
     - all
     - chisq
     - 2
     - ranked
     - 0.338
     - 0.0397
     - 0.302
     - 0.995
     - 

(184 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
     - 0.557
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
     - 0.455
     - 0.93
     - 3.19e+03
   * - L23
     - a
     - 440
     - all
     - 0.691
     - 0.927
     - 3.3e+03
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
     - 0.0349
     - 0.0756
     - 172
   * - L23
     - a
     - 440
     - eutrophic
     - 0.138
     - 0.465
     - 159
   * - L23
     - a
     - 440
     - eutrophic
     - 0.0683
     - 0.311
     - 161
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
     - 0.51
     - 0.956
     - 2.39e+03
   * - L23
     - a
     - 440
     - mesotrophic
     - 0.731
     - 0.96
     - 2.5e+03
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
     - 0.804
     - 647
   * - L23
     - a
     - 440
     - oligotrophic
     - 0.325
     - 0.949
     - 633
   * - L23
     - a
     - 440
     - oligotrophic
     - 0.694
     - 0.957
     - 648
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
     - 0.442
     - 0.929
     - 3.19e+03
   * - L23
     - a
     - 443
     - all
     - 0.692
     - 0.927
     - 3.3e+03
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
     - 0.0349
     - 0.105
     - 172
   * - L23
     - a
     - 443
     - eutrophic
     - 0.145
     - 0.484
     - 159
   * - L23
     - a
     - 443
     - eutrophic
     - 0.106
     - 0.329
     - 161
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
     - 0.498
     - 0.957
     - 2.39e+03
   * - L23
     - a
     - 443
     - mesotrophic
     - 0.728
     - 0.957
     - 2.5e+03
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
     - 0.302
     - 0.937
     - 633
   * - L23
     - a
     - 443
     - oligotrophic
     - 0.696
     - 0.958
     - 648
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
     - 3.32e+03
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
     - 0.936
     - 0.991
     - 3.3e+03
   * - L23
     - a_dg
     - 440
     - all
     - 0.628
     - 0.909
     - 3.3e+03
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
     - 0.745
     - 0.857
     - 161
   * - L23
     - a_dg
     - 440
     - eutrophic
     - 0.372
     - 0.57
     - 172
   * - L23
     - a_dg
     - 440
     - eutrophic
     - 0.441
     - 0.739
     - 161
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
     - 0.938
     - 0.998
     - 2.5e+03
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 0.633
     - 0.916
     - 2.5e+03
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
     - 0.977
     - 1
     - 648
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 0.657
     - 0.923
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
     - 3.32e+03
   * - L23
     - a_dg
     - 443
     - all
     - 0.935
     - 0.992
     - 3.3e+03

(184 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
   * - expb_giop_L23_mcmc_full
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 3.27e+03
     - 0.00335
     - 0.000236
     - 0.00696
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 616
     - -0.0137
     - -0.0169
     - -0.0104
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 2.49e+03
     - -0.00213
     - -0.00502
     - 0.00075
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - a
     - 440
     - expb_pow
     - giop
     - 161
     - 0.203
     - 0.151
     - 0.258
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 3.27e+03
     - 0.00261
     - -0.000508
     - 0.00583
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 616
     - -0.0158
     - -0.0188
     - -0.0126
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 2.49e+03
     - -0.00232
     - -0.00512
     - 0.000802
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - a
     - 443
     - expb_pow
     - giop
     - 161
     - 0.195
     - 0.151
     - 0.246
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 3.27e+03
     - 0.00302
     - 0.00158
     - 0.00461
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 616
     - 0.00551
     - 0.00361
     - 0.00729
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 2.49e+03
     - -0.00236
     - -0.00385
     - -0.000616
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 161
     - 0.0851
     - 0.0682
     - 0.103
     - underpowered
   * - expb_giop_L23_mcmc_full
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 3.27e+03
     - -0.0413
     - -0.045
     - -0.0379
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 616
     - 0.0116
     - 0.00485
     - 0.019
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 2.49e+03
     - -0.0568
     - -0.0609
     - -0.0529
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 161
     - -0.00822
     - -0.0174
     - 0.00192
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - a_ph
     - 440
     - expb_pow
     - giop
     - 3.27e+03
     - 0.709
     - 0.589
     - 0.836
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_ph
     - 440
     - expb_pow
     - giop
     - 616
     - 0.478
     - 0.288
     - 0.697
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_ph
     - 440
     - expb_pow
     - giop
     - 2.49e+03
     - 0.83
     - 0.677
     - 0.974
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_ph
     - 440
     - expb_pow
     - giop
     - 161
     - -0.413
     - -1.22
     - 0.0446
     - underpowered
   * - expb_giop_L23_mcmc_full
     - L23
     - a_ph
     - 443
     - expb_pow
     - giop
     - 3.27e+03
     - 0.656
     - 0.545
     - 0.788
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_ph
     - 443
     - expb_pow
     - giop
     - 616
     - 0.428
     - 0.256
     - 0.627
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_ph
     - 443
     - expb_pow
     - giop
     - 2.49e+03
     - 0.773
     - 0.642
     - 0.918
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_ph
     - 443
     - expb_pow
     - giop
     - 161
     - -0.426
     - -1.08
     - 0.0351
     - underpowered
   * - expb_giop_L23_mcmc_full
     - L23
     - a_dg
     - 440
     - expb_pow
     - giop
     - 3.27e+03
     - 0.13
     - 0.121
     - 0.14
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_dg
     - 440
     - expb_pow
     - giop
     - 616
     - 0.107
     - 0.0915
     - 0.121
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_dg
     - 440
     - expb_pow
     - giop
     - 2.49e+03
     - 0.129
     - 0.119
     - 0.14
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_dg
     - 440
     - expb_pow
     - giop
     - 161
     - 0.27
     - 0.15
     - 0.404
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_dg
     - 443
     - expb_pow
     - giop
     - 3.27e+03
     - 0.138
     - 0.127
     - 0.149
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_dg
     - 443
     - expb_pow
     - giop
     - 616
     - 0.116
     - 0.1
     - 0.133
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_dg
     - 443
     - expb_pow
     - giop
     - 2.49e+03
     - 0.137
     - 0.125
     - 0.15
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - a_dg
     - 443
     - expb_pow
     - giop
     - 161
     - 0.253
     - 0.134
     - 0.38
     - giop
   * - expb_giop_L23_mcmc_full
     - L23
     - bb_p
     - 555
     - expb_pow
     - giop
     - 3.27e+03
     - 0.00262
     - -0.00041
     - 0.00543
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb_p
     - 555
     - expb_pow
     - giop
     - 616
     - 0.0174
     - 0.012
     - 0.0228
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb_p
     - 555
     - expb_pow
     - giop
     - 2.49e+03
     - -0.00669
     - -0.00979
     - -0.00365
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb_p
     - 555
     - expb_pow
     - giop
     - 161
     - 0.0999
     - 0.0798
     - 0.122
     - underpowered
   * - expb_giop_L23_mcmc_full
     - L23
     - bb_p
     - 670
     - expb_pow
     - giop
     - 3.27e+03
     - -0.0654
     - -0.0712
     - -0.0591
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb_p
     - 670
     - expb_pow
     - giop
     - 616
     - 0.0287
     - 0.0127
     - 0.0446
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb_p
     - 670
     - expb_pow
     - giop
     - 2.49e+03
     - -0.0923
     - -0.0995
     - -0.0852
     - indistinguishable
   * - expb_giop_L23_mcmc_full
     - L23
     - bb_p
     - 670
     - expb_pow
     - giop
     - 161
     - -0.00863
     - -0.0203
     - 0.00251
     - indistinguishable
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

(217 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
   * - expb_giop_L23_mcmc_full
     - 7b92d31846e5
     - 3
     - 0.0.dev0@dd4e162
     - 0.0.dev0@850000b
     - da6dff9
   * - expb_giop_L23_test20
     - 75f63215deaf
     - 2
     - 0.0.dev0@61c83e0
     - 0.0.dev0@f242b0e
     - 0.1.0@3aed28a
   * - gloria_turbid_v3
     - 8a40c7a35bde
     - 0
     - 0.0.dev0@c70040c
     - 0.0.dev0@f242b0e
     - da6dff9
   * - multi_L23_PANGAEA_v2
     - 75f63215deaf
     - 2
     - 0.0.dev0@4ea86db
     - 0.0.dev0
     - da6dff9
   * - pangaea_fits_v2
     - 7b92d31846e5
     - 3
     - 0.0.dev0@039c2b2
     - 0.0.dev0@f242b0e
     - da6dff9


.. note::

   These sweeps were recorded under **different provenance schemas** (0, 2, 3; current is 4). A block written under an earlier schema could not record ``maxfev`` or the MCMC settings, so a digest difference here may reflect what was *written down* rather than what was configured — and, in the other direction, two blocks can agree while one of them silently ran a raised iteration budget.

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

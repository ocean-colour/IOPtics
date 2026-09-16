============================
Algorithm profile — expb_pow
============================

In one paragraph
----------------

``expb_pow`` has scoreable results on **L23, PANGAEA** across 2 sweep(s). Its best contest is a(443) on L23, at mae 0.0243 (2.4% multiplicative error); its worst is bb_p(670) on PANGAEA at 1.91. It produced a usable fit for 12%-100% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

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
     - ``double_gaussian``, ``phi_C``, ``variable_Gordon``

Where it has been evaluated
---------------------------

.. list-table:: What has been evaluated on what
   :header-rows: 1
   :stub-columns: 1
   :widths: auto

   * - algorithm
     - L23
     - PANGAEA
   * - ``expb_pow``
     - scored (n=6619)
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
     - —
     - sole competitor
     - 0.0681
     - 0.0178
     - —
     - 0.995
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
     - —
     - sole competitor
     - 0.055
     - -0.000367
     - —
     - 1
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - chisq
     - 1
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
     - —
     - sole competitor
     - 0.037
     - -0.00209
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
     - —
     - sole competitor
     - 0.0655
     - 0.0175
     - —
     - 0.995
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
     - —
     - sole competitor
     - 0.0533
     - 7.8e-05
     - —
     - 1
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - chisq
     - 1
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
     - —
     - sole competitor
     - 0.0362
     - 0.000129
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
     - 2
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
     - —
     - sole competitor
     - 0.274
     - 0.129
     - —
     - 0.995
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
     - 2
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
     - —
     - sole competitor
     - 0.252
     - 0.133
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
     - 2
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
     - —
     - sole competitor
     - 0.19
     - 0.112
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
   * - L23
     - a_dg
     - 443
     - all
     - mcmc
     - —
     - sole competitor
     - 0.28
     - 0.126
     - —
     - 0.995
     - 
   * - L23
     - a_dg
     - 443
     - eutrophic
     - chisq
     - 1
     - ranked
     - 0.817
     - 0.385
     - 0.373
     - 0.91
     - 
   * - L23
     - a_dg
     - 443
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.6
     - 0.365
     - 0.332
     - 0.972
     - 
   * - L23
     - a_dg
     - 443
     - eutrophic
     - mcmc
     - —
     - sole competitor
     - 1.2
     - 0.129
     - —
     - 0.91
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
     - 2
     - ranked
     - 0.328
     - 0.0341
     - 0.302
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - mcmc
     - —
     - sole competitor
     - 0.259
     - 0.13
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
     - 2
     - ranked
     - 0.276
     - -0.0112
     - 0.282
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - mcmc
     - —
     - sole competitor
     - 0.197
     - 0.109
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
     - -0.121
     - 0.617
     - 0.998
     - 
   * - L23
     - a_ph
     - 440
     - all
     - chisq
     - 2
     - ranked
     - 1.07
     - -0.345
     - 0.455
     - 0.995
     - 
   * - L23
     - a_ph
     - 440
     - all
     - mcmc
     - —
     - sole competitor
     - 1.25
     - -0.481
     - —
     - 0.995
     - 
   * - L23
     - a_ph
     - 440
     - eutrophic
     - chisq
     - 1
     - ranked
     - 0.518
     - 0.462
     - 0.581
     - 0.972
     - 
   * - L23
     - a_ph
     - 440
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - 0.878
     - 0.338
     - 0.484
     - 0.91
     - 
   * - L23
     - a_ph
     - 440
     - eutrophic
     - mcmc
     - —
     - sole competitor
     - 1.45
     - -0.119
     - —
     - 0.91
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
     - 2
     - ranked
     - 1.16
     - -0.408
     - 0.453
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - mcmc
     - —
     - sole competitor
     - 1.29
     - -0.506
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
     - 0.831
     - -0.192
     - 0.453
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - mcmc
     - —
     - sole competitor
     - 1.06
     - -0.449
     - —
     - 1
     - 

(90 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
     - 443
     - all
     - 0.538
     - 0.801
     - 3.3e+03
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
   * - L23
     - a_dg
     - 443
     - all
     - 0.642
     - 0.919
     - 3.3e+03
   * - L23
     - a_dg
     - 443
     - eutrophic
     - 0.745
     - 0.863
     - 161
   * - L23
     - a_dg
     - 443
     - eutrophic
     - 0.395
     - 0.593
     - 172
   * - L23
     - a_dg
     - 443
     - eutrophic
     - 0.453
     - 0.739
     - 161
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
     - 0.937
     - 0.998
     - 2.5e+03
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 0.647
     - 0.927
     - 2.5e+03
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
     - 0.977
     - 1
     - 648
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 0.668
     - 0.932
     - 648
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
     - 0.968
     - 0.995
     - 3.19e+03
   * - L23
     - a_ph
     - 440
     - all
     - 0.578
     - 0.881
     - 3.3e+03
   * - L23
     - a_ph
     - 440
     - eutrophic
     - 0.18
     - 0.541
     - 172
   * - L23
     - a_ph
     - 440
     - eutrophic
     - 0.686
     - 0.931
     - 159
   * - L23
     - a_ph
     - 440
     - eutrophic
     - 0.447
     - 0.745
     - 161
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
     - 0.981
     - 0.997
     - 2.39e+03
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 0.57
     - 0.879
     - 2.5e+03
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
     - 0.992
     - 1
     - 633
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 0.642
     - 0.92
     - 648

(90 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
     - 3.29e+03
     - -0.0425
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
     - 160
     - 0.164
     - 0.122
     - 0.207
     - giop
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 440
     - expb_pow
     - gsm
     - 150
     - -0.013
     - -0.0515
     - 0.0271
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
     - -0.125
     - expb_pow
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - gsm
     - 3.29e+03
     - -0.0586
     - -0.0615
     - -0.0559
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
     - 160
     - 0.165
     - 0.122
     - 0.206
     - giop
   * - multi_L23_PANGAEA_v2
     - L23
     - a
     - 443
     - expb_pow
     - gsm
     - 150
     - -0.0922
     - -0.128
     - -0.055
     - underpowered
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 3.28e+03
     - -0.0266
     - -0.0282
     - -0.0252
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - expb_pow
     - gsm
     - 3.29e+03
     - 0.000162
     - -0.0012
     - 0.00155
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 637
     - -0.0474
     - -0.0489
     - -0.0459
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - expb_pow
     - gsm
     - 648
     - 0.00155
     - -7.74e-05
     - 0.0032
     - indistinguishable

(115 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
   * - multi_L23_PANGAEA_v2
     - 75f63215deaf
     - 2
     - 0.0.dev0@4ea86db
     - 0.0.dev0
     - da6dff9


.. note::

   These sweeps were recorded under **different provenance schemas** (2, 3; current is 3). A block written under an earlier schema could not record ``maxfev`` or the MCMC settings, so a digest difference here may reflect what was *written down* rather than what was configured — and, in the other direction, two blocks can agree while one of them silently ran a raised iteration budget.

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

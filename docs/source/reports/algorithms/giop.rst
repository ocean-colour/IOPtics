========================
Algorithm profile — giop
========================

In one paragraph
----------------

``giop`` has scoreable results on **L23, PANGAEA** across 4 sweep(s). Its best contest is bb(555) on L23, at mae 0.0278 (2.8% multiplicative error); its worst is a_dg(440) on PANGAEA at 7.21. It produced a usable fit for 22%-100% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

What it parameterizes
---------------------

Read from the registry entry that sweeps actually run, so it cannot drift from the configuration behind the numbers below.

.. list-table::
   :stub-columns: 1
   :widths: auto

   * - a_nw model
     - GIOP
   * - bb_nw model
     - Lee
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
     - L23
     - PANGAEA
   * - ``giop``
     - scored (n=6576)
     - scored (n=1020)

Accuracy, by dataset and contest
--------------------------------

One row per contest **and trophic stratum** — ``all`` is the pooled population, the others its Chl bins (:data:`ioptics.metrics.CHL_BINS`), so a pooled row and its bins are not independent results. This algorithm has rows in 5 strata.

.. list-table:: giop — scored contests
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
     - —
     - indistinguishable
     - 0.0958
     - 0.0901
     - 0.425
     - 0.985
     - 
   * - L23
     - a
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - 0.0725
     - 0.0693
     - 0.3
     - 1
     - 
   * - L23
     - a
     - 440
     - all
     - chisq
     - 3
     - ranked
     - 0.183
     - 0.183
     - 0.0744
     - 0.989
     - 
   * - L23
     - a
     - 440
     - eutrophic
     - chisq
     - 1
     - ranked
     - 0.276
     - 0.276
     - 0.843
     - 0.904
     - 
   * - L23
     - a
     - 440
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.338
     - 0.335
     - 0.72
     - 0.91
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0886
     - 0.0824
     - 0.445
     - 1
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0737
     - 0.0686
     - 0.385
     - 1
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - chisq
     - 3
     - ranked
     - 0.191
     - 0.191
     - 0.0447
     - 0.997
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.068
     - 0.0641
     - 0.263
     - 0.951
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0705
     - 0.0705
     - 0.143
     - 1
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - chisq
     - 3
     - ranked
     - 0.133
     - 0.133
     - 0.00942
     - 0.983
     - 
   * - L23
     - a
     - 443
     - all
     - chisq
     - —
     - indistinguishable
     - 0.0927
     - 0.0871
     - 0.415
     - 0.985
     - 
   * - L23
     - a
     - 443
     - all
     - chisq
     - —
     - indistinguishable
     - 0.0719
     - 0.0699
     - 0.3
     - 1
     - 
   * - L23
     - a
     - 443
     - all
     - chisq
     - 3
     - ranked
     - 0.179
     - 0.179
     - 0.0905
     - 0.989
     - 
   * - L23
     - a
     - 443
     - eutrophic
     - chisq
     - 1
     - ranked
     - 0.249
     - 0.249
     - 0.837
     - 0.904
     - 
   * - L23
     - a
     - 443
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.31
     - 0.307
     - 0.72
     - 0.91
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.086
     - 0.0798
     - 0.441
     - 1
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.071
     - 0.068
     - 0.385
     - 1
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - chisq
     - 3
     - ranked
     - 0.187
     - 0.187
     - 0.0664
     - 0.997
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0682
     - 0.0648
     - 0.229
     - 0.951
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0735
     - 0.0735
     - 0.143
     - 1
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - chisq
     - 3
     - ranked
     - 0.132
     - 0.132
     - 0.00863
     - 0.983
     - 
   * - L23
     - a_dg
     - 440
     - all
     - chisq
     - 1
     - ranked
     - 0.19
     - -0.0282
     - 0.694
     - 0.985
     - 
   * - L23
     - a_dg
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - 0.126
     - -0.0505
     - 0.65
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - 0.166
     - -0.023
     - 0.524
     - 0.989
     - 
   * - L23
     - a_dg
     - 440
     - eutrophic
     - chisq
     - 1
     - ranked
     - 0.283
     - -0.103
     - 0.727
     - 0.904
     - 
   * - L23
     - a_dg
     - 440
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.556
     - -0.0329
     - 0.646
     - 0.91
     - 
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - chisq
     - 1
     - ranked
     - 0.181
     - -0.0294
     - 0.694
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.134
     - -0.059
     - 0.692
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.163
     - -0.0184
     - 0.515
     - 0.997
     - 
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - chisq
     - 1
     - ranked
     - 0.146
     - -0.0222
     - 0.706
     - 0.951
     - 
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.111
     - -0.0345
     - 0.571
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.149
     - -0.0198
     - 0.514
     - 0.983
     - 
   * - L23
     - a_dg
     - 443
     - all
     - chisq
     - —
     - indistinguishable
     - 0.137
     - -0.0727
     - 0.7
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - all
     - chisq
     - 2
     - ranked
     - 0.2
     - -0.0507
     - 0.698
     - 0.985
     - 
   * - L23
     - a_dg
     - 443
     - all
     - chisq
     - —
     - indistinguishable
     - 0.177
     - -0.0454
     - 0.507
     - 0.989
     - 
   * - L23
     - a_dg
     - 443
     - eutrophic
     - chisq
     - 1
     - ranked
     - 0.301
     - -0.126
     - 0.693
     - 0.904
     - 
   * - L23
     - a_dg
     - 443
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.564
     - -0.0576
     - 0.627
     - 0.91
     - 
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - chisq
     - 1
     - ranked
     - 0.191
     - -0.0518
     - 0.698
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.143
     - -0.0794
     - 0.692
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.174
     - -0.041
     - 0.495
     - 0.997
     - 
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - chisq
     - 1
     - ranked
     - 0.157
     - -0.044
     - 0.718
     - 0.951
     - 
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.124
     - -0.0602
     - 0.714
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.159
     - -0.0416
     - 0.512
     - 0.983
     - 
   * - L23
     - a_ph
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - 0.325
     - 0.305
     - 0.6
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - all
     - chisq
     - 2
     - ranked
     - 0.369
     - 0.264
     - 0.545
     - 0.985
     - 
   * - L23
     - a_ph
     - 440
     - all
     - chisq
     - 3
     - ranked
     - 0.599
     - 0.594
     - 0.157
     - 0.989
     - 
   * - L23
     - a_ph
     - 440
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - 1.29
     - 0.142
     - 0.516
     - 0.91
     - 
   * - L23
     - a_ph
     - 440
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.664
     - 0.635
     - 0.46
     - 0.904
     - 
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - chisq
     - 1
     - ranked
     - 0.326
     - 0.262
     - 0.547
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.319
     - 0.288
     - 0.462
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - chisq
     - 3
     - ranked
     - 0.592
     - 0.59
     - 0.144
     - 0.997
     - 
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - chisq
     - 1
     - ranked
     - 0.338
     - 0.338
     - 0.857
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - chisq
     - 2
     - ranked
     - 0.363
     - 0.305
     - 0.547
     - 0.951
     - 
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - chisq
     - 3
     - ranked
     - 0.61
     - 0.599
     - 0.14
     - 0.983
     - 
   * - L23
     - a_ph
     - 443
     - all
     - chisq
     - —
     - indistinguishable
     - 0.355
     - 0.346
     - 0.6
     - 1
     - 
   * - L23
     - a_ph
     - 443
     - all
     - chisq
     - 2
     - ranked
     - 0.386
     - 0.29
     - 0.516
     - 0.985
     - 
   * - L23
     - a_ph
     - 443
     - all
     - chisq
     - 3
     - ranked
     - 0.63
     - 0.626
     - 0.142
     - 0.989
     - 
   * - L23
     - a_ph
     - 443
     - eutrophic
     - chisq
     - 1
     - ranked
     - 0.625
     - 0.593
     - 0.62
     - 0.904
     - 
   * - L23
     - a_ph
     - 443
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - 1.26
     - 0.115
     - 0.503
     - 0.91
     - 

(110 further rows are on the :doc:`/reports/leaderboard_full` page.)

Are its uncertainties honest?
-----------------------------

A retrieval can be the most accurate and still be over-confident: the verdict compares empirical coverage with its nominal 0.68 / 0.95 target, and *consistent* means "not distinguishable from nominal at this sample size" rather than "calibrated".

.. list-table:: giop — interval calibration
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
     - 0.215
     - 0.441
     - 3.27e+03
   * - L23
     - a
     - 440
     - all
     - 0.2
     - 0.65
     - 20
   * - L23
     - a
     - 440
     - all
     - 0.000609
     - 0.00244
     - 3.28e+03
   * - L23
     - a
     - 440
     - eutrophic
     - 0
     - 0
     - 160
   * - L23
     - a
     - 440
     - eutrophic
     - 0.0318
     - 0.14
     - 157
   * - L23
     - a
     - 440
     - mesotrophic
     - 0.227
     - 0.452
     - 2.49e+03
   * - L23
     - a
     - 440
     - mesotrophic
     - 0.154
     - 0.692
     - 13
   * - L23
     - a
     - 440
     - mesotrophic
     - 0
     - 0.00121
     - 2.49e+03
   * - L23
     - a
     - 440
     - oligotrophic
     - 0.211
     - 0.474
     - 616
   * - L23
     - a
     - 440
     - oligotrophic
     - 0.286
     - 0.571
     - 7
   * - L23
     - a
     - 440
     - oligotrophic
     - 0.00314
     - 0.00785
     - 637
   * - L23
     - a
     - 443
     - all
     - 0.214
     - 0.442
     - 3.27e+03
   * - L23
     - a
     - 443
     - all
     - 0.2
     - 0.6
     - 20
   * - L23
     - a
     - 443
     - all
     - 0.000609
     - 0.00274
     - 3.28e+03
   * - L23
     - a
     - 443
     - eutrophic
     - 0
     - 0.00625
     - 160
   * - L23
     - a
     - 443
     - eutrophic
     - 0.051
     - 0.166
     - 157
   * - L23
     - a
     - 443
     - mesotrophic
     - 0.227
     - 0.456
     - 2.49e+03
   * - L23
     - a
     - 443
     - mesotrophic
     - 0.231
     - 0.692
     - 13
   * - L23
     - a
     - 443
     - mesotrophic
     - 0
     - 0.00121
     - 2.49e+03
   * - L23
     - a
     - 443
     - oligotrophic
     - 0.203
     - 0.456
     - 616
   * - L23
     - a
     - 443
     - oligotrophic
     - 0.143
     - 0.429
     - 7
   * - L23
     - a
     - 443
     - oligotrophic
     - 0.00314
     - 0.00785
     - 637
   * - L23
     - a_dg
     - 440
     - all
     - 0.361
     - 0.646
     - 3.27e+03
   * - L23
     - a_dg
     - 440
     - all
     - 0.35
     - 0.75
     - 20
   * - L23
     - a_dg
     - 440
     - all
     - 0.356
     - 0.635
     - 3.28e+03
   * - L23
     - a_dg
     - 440
     - eutrophic
     - 0.237
     - 0.388
     - 160
   * - L23
     - a_dg
     - 440
     - eutrophic
     - 0.565
     - 0.826
     - 161
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 0.367
     - 0.66
     - 2.49e+03
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 0.385
     - 0.769
     - 13
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 0.357
     - 0.642
     - 2.49e+03
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 0.284
     - 0.542
     - 616
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 0.286
     - 0.714
     - 7
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 0.38
     - 0.67
     - 637
   * - L23
     - a_dg
     - 443
     - all
     - 0.35
     - 0.65
     - 20
   * - L23
     - a_dg
     - 443
     - all
     - 0.337
     - 0.607
     - 3.27e+03
   * - L23
     - a_dg
     - 443
     - all
     - 0.337
     - 0.611
     - 3.28e+03
   * - L23
     - a_dg
     - 443
     - eutrophic
     - 0.194
     - 0.369
     - 160
   * - L23
     - a_dg
     - 443
     - eutrophic
     - 0.522
     - 0.832
     - 161
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 0.346
     - 0.622
     - 2.49e+03
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 0.385
     - 0.692
     - 13
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 0.342
     - 0.617
     - 2.49e+03
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 0.253
     - 0.484
     - 616
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 0.286
     - 0.571
     - 7
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 0.356
     - 0.647
     - 637
   * - L23
     - a_ph
     - 440
     - all
     - 0.3
     - 0.5
     - 20
   * - L23
     - a_ph
     - 440
     - all
     - 0.283
     - 0.513
     - 3.27e+03
   * - L23
     - a_ph
     - 440
     - all
     - 0.0341
     - 0.107
     - 3.28e+03
   * - L23
     - a_ph
     - 440
     - eutrophic
     - 0.217
     - 0.369
     - 157
   * - L23
     - a_ph
     - 440
     - eutrophic
     - 0.0187
     - 0.0625
     - 160
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 0.292
     - 0.529
     - 2.49e+03
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 0.385
     - 0.538
     - 13
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 0.0301
     - 0.0993
     - 2.49e+03
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 0.143
     - 0.429
     - 7
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 0.263
     - 0.484
     - 616
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 0.0534
     - 0.146
     - 637
   * - L23
     - a_ph
     - 443
     - all
     - 0.3
     - 0.4
     - 20
   * - L23
     - a_ph
     - 443
     - all
     - 0.27
     - 0.483
     - 3.27e+03
   * - L23
     - a_ph
     - 443
     - all
     - 0.0244
     - 0.0834
     - 3.28e+03
   * - L23
     - a_ph
     - 443
     - eutrophic
     - 0.0187
     - 0.075
     - 160
   * - L23
     - a_ph
     - 443
     - eutrophic
     - 0.248
     - 0.369
     - 157

(110 further rows are on the :doc:`/reports/leaderboard_full` page.)

Head-to-head against the others
-------------------------------

.. list-table:: giop — pairwise verdicts
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

(205 further rows are on the :doc:`/reports/leaderboard_full` page.)

What varied between sweeps
--------------------------

This profile pools every sweep that ran ``giop``. The runs were **not**
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
     - 3a2b4a921aeb
     - 3
     - 0.0.dev0@dd4e162
     - 0.0.dev0@850000b
     - da6dff9
   * - expb_giop_L23_test20
     - 62edb76d1b93
     - 2
     - 0.0.dev0@61c83e0
     - 0.0.dev0@f242b0e
     - 0.1.0@3aed28a
   * - multi_L23_PANGAEA_v2
     - 62edb76d1b93
     - 2
     - 0.0.dev0@4ea86db
     - 0.0.dev0
     - da6dff9
   * - pangaea_fits_v2
     - 3a2b4a921aeb
     - 3
     - 0.0.dev0@039c2b2
     - 0.0.dev0@f242b0e
     - da6dff9


.. note::

   These sweeps were recorded under **different provenance schemas** (2, 3; current is 4). A block written under an earlier schema could not record ``maxfev`` or the MCMC settings, so a digest difference here may reflect what was *written down* rather than what was configured — and, in the other direction, two blocks can agree while one of them silently ran a raised iteration budget.

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

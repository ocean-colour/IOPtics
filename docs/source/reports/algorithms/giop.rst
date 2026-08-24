========================
Algorithm profile — giop
========================

In one paragraph
----------------

``giop`` has scoreable results on **L23, PANGAEA** across 2 sweep(s). Its best contest is bb(670) on L23, at mae 0.0357 (3.6% multiplicative error); its worst is a_dg(440) on PANGAEA at 6.11. It produced a usable fit for 22%-100% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

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
   * - ``giop``
     - scored (n=6556)
     - scored (n=361)

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
     - 2
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
     - 2
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
     - 2
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
     - 2
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
     - 2
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
     - 2
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
     - 1
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
     - 1
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
     - 2
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
     - 2
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
     - 2
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
     - 1
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
     - 2
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
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - chisq
     - 1
     - ranked
     - 0.34
     - 0.287
     - 0.519
     - 1
     - 
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - chisq
     - 2
     - ranked
     - 0.621
     - 0.619
     - 0.123
     - 0.997
     - 
   * - L23
     - a_ph
     - 443
     - oligotrophic
     - chisq
     - 1
     - ranked
     - 0.399
     - 0.354
     - 0.505
     - 0.951
     - 
   * - L23
     - a_ph
     - 443
     - oligotrophic
     - chisq
     - 2
     - ranked
     - 0.668
     - 0.658
     - 0.104
     - 0.983
     - 
   * - L23
     - bb
     - 555
     - all
     - chisq
     - —
     - indistinguishable
     - 0.0521
     - -0.0223
     - 0.504
     - 0.985
     - 
   * - L23
     - bb
     - 555
     - all
     - chisq
     - —
     - indistinguishable
     - 0.061
     - 0.0605
     - 0.231
     - 0.989
     - 
   * - L23
     - bb
     - 555
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - 0.127
     - 0.0816
     - 0.72
     - 0.91
     - 
   * - L23
     - bb
     - 555
     - eutrophic
     - chisq
     - 2
     - ranked
     - 0.0614
     - 0.0573
     - 0.593
     - 0.904
     - 
   * - L23
     - bb
     - 555
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0507
     - -0.0361
     - 0.466
     - 1
     - 
   * - L23
     - bb
     - 555
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0577
     - 0.0573
     - 0.255
     - 0.997
     - 
   * - L23
     - bb
     - 555
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0392
     - 0.00868
     - 0.599
     - 0.951
     - 
   * - L23
     - bb
     - 555
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0741
     - 0.0741
     - 0.0518
     - 0.983
     - 
   * - L23
     - bb
     - 670
     - all
     - chisq
     - —
     - indistinguishable
     - 0.0388
     - -0.00487
     - 0.466
     - 0.989
     - 
   * - L23
     - bb
     - 670
     - all
     - chisq
     - —
     - indistinguishable
     - 0.127
     - -0.0958
     - 0.272
     - 0.985
     - 
   * - L23
     - bb
     - 670
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - 0.0859
     - 0.0855
     - 0.47
     - 0.904
     - 
   * - L23
     - bb
     - 670
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - 0.143
     - 0.115
     - 0.391
     - 0.91
     - 

(50 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
     - 0.38
     - 0.67
     - 637
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
     - 0.356
     - 0.647
     - 637
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
     - 0.0301
     - 0.0993
     - 2.49e+03
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
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - 0.284
     - 0.504
     - 2.49e+03
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - 0.0221
     - 0.0764
     - 2.49e+03
   * - L23
     - a_ph
     - 443
     - oligotrophic
     - 0.221
     - 0.429
     - 616
   * - L23
     - a_ph
     - 443
     - oligotrophic
     - 0.0345
     - 0.113
     - 637
   * - L23
     - bb
     - 555
     - all
     - 0.433
     - 0.729
     - 3.27e+03
   * - L23
     - bb
     - 555
     - all
     - 0.0298
     - 0.0642
     - 3.28e+03
   * - L23
     - bb
     - 555
     - eutrophic
     - 0.217
     - 0.441
     - 161
   * - L23
     - bb
     - 555
     - eutrophic
     - 0.113
     - 0.25
     - 160
   * - L23
     - bb
     - 555
     - mesotrophic
     - 0.429
     - 0.727
     - 2.49e+03
   * - L23
     - bb
     - 555
     - mesotrophic
     - 0.0318
     - 0.0679
     - 2.49e+03
   * - L23
     - bb
     - 555
     - oligotrophic
     - 0.503
     - 0.812
     - 616
   * - L23
     - bb
     - 555
     - oligotrophic
     - 0.00157
     - 0.00314
     - 637
   * - L23
     - bb
     - 670
     - all
     - 0.188
     - 0.338
     - 3.28e+03
   * - L23
     - bb
     - 670
     - all
     - 0.151
     - 0.315
     - 3.27e+03
   * - L23
     - bb
     - 670
     - eutrophic
     - 0.0563
     - 0.125
     - 160
   * - L23
     - bb
     - 670
     - eutrophic
     - 0.23
     - 0.453
     - 161

(50 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
     - giop
     - gsm
     - 3.26e+03
     - 0.088
     - 0.0852
     - 0.0907
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
     - giop
     - gsm
     - 637
     - 0.098
     - 0.0949
     - 0.101
     - underpowered
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
     - giop
     - gsm
     - 2.48e+03
     - 0.1
     - 0.0981
     - 0.103
     - gsm
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
     - giop
     - gsm
     - 140
     - -0.24
     - -0.256
     - -0.224
     - giop
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
     - giop
     - gsm
     - 3.26e+03
     - 0.0699
     - 0.0668
     - 0.073
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
     - giop
     - gsm
     - 637
     - 0.0933
     - 0.0904
     - 0.0959
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
     - giop
     - gsm
     - 2.48e+03
     - 0.0813
     - 0.0786
     - 0.0838
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
     - giop
     - gsm
     - 140
     - -0.316
     - -0.334
     - -0.3
     - giop
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
     - giop
     - gsm
     - 3.26e+03
     - 0.0263
     - 0.0249
     - 0.0276
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
     - giop
     - gsm
     - 637
     - 0.0487
     - 0.0465
     - 0.0509
     - indistinguishable

(115 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
   * - multi_L23_PANGAEA_v2
     - 62edb76d1b93
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

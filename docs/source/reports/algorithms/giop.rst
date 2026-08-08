========================
Algorithm profile — giop
========================

In one paragraph
----------------

``giop`` has scoreable results on **L23, PANGAEA** across 2 sweep(s). Its best contest is bb(555) on L23, at mae 0.0278 (2.8% multiplicative error); its worst is a_dg(443) on PANGAEA at 6.11. It produced a usable fit for 22%-100% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

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
     - scored (n=3305)
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
     - 2
     - ranked
     - 0.183
     - 0.183
     - 0.0743
     - 0.989
     - 
   * - L23
     - a
     - 440
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.276
     - 0.276
     - 0.843
     - 0.904
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
     - 2
     - ranked
     - 0.179
     - 0.179
     - 0.0903
     - 0.989
     - 
   * - L23
     - a
     - 443
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.249
     - 0.249
     - 0.836
     - 0.904
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
     - —
     - sole competitor
     - 0.283
     - -0.103
     - 0.726
     - 0.904
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
     - —
     - sole competitor
     - 0.301
     - -0.126
     - 0.692
     - 0.904
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
     - sole competitor
     - 0.664
     - 0.635
     - 0.458
     - 0.904
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
     - —
     - sole competitor
     - 0.625
     - 0.593
     - 0.619
     - 0.904
     - 
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.33
     - 0.317
     - 0.462
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
     - 0.402
     - 0.402
     - 0.857
     - 1
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
     - 0.0351
     - -0.0151
     - 0.55
     - 1
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
     - sole competitor
     - 0.0614
     - 0.0573
     - 0.592
     - 0.904
     - 
   * - L23
     - bb
     - 555
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0391
     - -0.0248
     - 0.462
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
     - 0.0278
     - 0.00322
     - 0.714
     - 1
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
     - 0.106
     - -0.0901
     - 0.25
     - 1
     - 
   * - L23
     - bb
     - 670
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.0859
     - 0.0855
     - 0.468
     - 0.904
     - 
   * - L23
     - bb
     - 670
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0357
     - -0.0178
     - 0.384
     - 0.997
     - 
   * - L23
     - bb
     - 670
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.117
     - -0.103
     - 0.308
     - 1
     - 
   * - L23
     - bb
     - 670
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0395
     - 0.0246
     - 0.785
     - 0.983
     - 
   * - L23
     - bb
     - 670
     - oligotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0856
     - -0.0658
     - 0.143
     - 1
     - 
   * - L23
     - bb_p
     - 555
     - all
     - chisq
     - —
     - indistinguishable
     - 0.0774
     - -0.0221
     - 0.55
     - 1
     - 
   * - L23
     - bb_p
     - 555
     - all
     - chisq
     - —
     - indistinguishable
     - 0.132
     - 0.132
     - 0.238
     - 0.989
     - 
   * - L23
     - bb_p
     - 555
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.0741
     - 0.0689
     - 0.592
     - 0.904
     - 
   * - L23
     - bb_p
     - 555
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - 0.0786
     - -0.0384
     - 0.462
     - 1
     - 

(30 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
     - 0.0341
     - 0.107
     - 3.28e+03
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
     - mesotrophic
     - 0.385
     - 0.385
     - 13
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
     - 0.143
     - 0.429
     - 7
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
     - 0.6
     - 0.9
     - 20
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
     - 0.113
     - 0.25
     - 160
   * - L23
     - bb
     - 555
     - mesotrophic
     - 0.462
     - 0.846
     - 13
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
     - 0.857
     - 1
     - 7
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
     - 0.2
     - 0.4
     - 20
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
     - mesotrophic
     - 0.19
     - 0.345
     - 2.49e+03
   * - L23
     - bb
     - 670
     - mesotrophic
     - 0.308
     - 0.308
     - 13
   * - L23
     - bb
     - 670
     - oligotrophic
     - 0.212
     - 0.361
     - 637
   * - L23
     - bb
     - 670
     - oligotrophic
     - 0
     - 0.571
     - 7
   * - L23
     - bb_p
     - 555
     - all
     - 0.6
     - 0.9
     - 20
   * - L23
     - bb_p
     - 555
     - all
     - 0.0298
     - 0.0642
     - 3.28e+03
   * - L23
     - bb_p
     - 555
     - eutrophic
     - 0.113
     - 0.25
     - 160
   * - L23
     - bb_p
     - 555
     - mesotrophic
     - 0.462
     - 0.846
     - 13

(30 further rows are on the :doc:`/reports/leaderboard_full` page.)

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
     - 159
     - 0.16
     - 0.12
     - 0.204
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
     - -0.126
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
     - 159
     - 0.161
     - 0.119
     - 0.204
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
     - -0.0267
     - -0.0284
     - -0.0251
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
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 2.49e+03
     - -0.0287
     - -0.0301
     - -0.0273
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - giop
     - gsm
     - 2.48e+03
     - 0.0213
     - 0.0196
     - 0.023
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - expb_pow
     - giop
     - 159
     - 0.0929
     - 0.0767
     - 0.111
     - underpowered
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 555
     - giop
     - gsm
     - 140
     - 0.0131
     - 0.0074
     - 0.0183
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 3.28e+03
     - -0.00467
     - -0.00556
     - -0.00378
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 670
     - giop
     - gsm
     - 3.26e+03
     - 0.00608
     - 0.00533
     - 0.00688
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 637
     - 0.01
     - 0.00856
     - 0.0115
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 670
     - giop
     - gsm
     - 637
     - -0.00893
     - -0.0103
     - -0.0075
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 670
     - expb_pow
     - giop
     - 2.49e+03
     - -0.00941
     - -0.0105
     - -0.00842
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 670
     - giop
     - gsm
     - 2.48e+03
     - 0.00755
     - 0.00676
     - 0.00843
     - indistinguishable

(85 further rows are on the :doc:`/reports/leaderboard_full` page.)

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

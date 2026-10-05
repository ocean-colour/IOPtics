===========================
Algorithm profile — ls2_iii
===========================

In one paragraph
----------------

``ls2_iii`` has scoreable results on **L23** across 1 sweep(s). Its best contest is a(443) on L23, at mae 0.131 (13.1% multiplicative error); its worst is bb_p(670) on L23 at 1.3. It produced a usable fit for 0%-0% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

What it parameterizes
---------------------

Read from the registry entry that sweeps actually run, so it cannot drift from the configuration behind the numbers below.

.. list-table::
   :stub-columns: 1
   :widths: auto

   * - method
     - ls2
   * - fit method
     - direct
   * - Kd source
     - nn:PACE_v2.3
   * - b_p source
     - oc4v4
   * - Raman correction
     - on
   * - mu_w
     - snell
   * - outputs
     - ``a``, ``a_nw``, ``bb``, ``bb_p``

Where it has been evaluated
---------------------------

.. list-table:: What has been evaluated on what
   :header-rows: 1
   :stub-columns: 1
   :widths: auto

   * - algorithm
     - L23
   * - ``ls2_iii``
     - scored (n=3031)

Accuracy, by dataset and contest
--------------------------------

One row per contest **and trophic stratum** — ``all`` is the pooled population, the others its Chl bins (:data:`ioptics.metrics.CHL_BINS`), so a pooled row and its bins are not independent results. This algorithm has rows in 4 strata.

.. list-table:: ls2_iii — scored contests
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
     - direct
     - —
     - sole competitor
     - 0.169
     - 0.00398
     - 0.34
     - 0
     - 
   * - L23
     - a
     - 440
     - eutrophic
     - direct
     - —
     - sole competitor
     - 0.274
     - 0.0559
     - 0.699
     - 0
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - direct
     - —
     - sole competitor
     - 0.17
     - 0.00124
     - 0.326
     - 0
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - direct
     - —
     - sole competitor
     - 0.132
     - 4.44e-05
     - 0.289
     - 0
     - 
   * - L23
     - a
     - 443
     - all
     - direct
     - —
     - sole competitor
     - 0.162
     - -0.00468
     - 0.336
     - 0
     - 
   * - L23
     - a
     - 443
     - eutrophic
     - direct
     - —
     - sole competitor
     - 0.25
     - 0.0522
     - 0.699
     - 0
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - direct
     - —
     - sole competitor
     - 0.163
     - -0.00622
     - 0.319
     - 0
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - direct
     - —
     - sole competitor
     - 0.131
     - -0.0153
     - 0.295
     - 0
     - 
   * - L23
     - a_nw
     - 440
     - all
     - direct
     - —
     - sole competitor
     - 0.225
     - -0.0031
     - 0.337
     - 0
     - 
   * - L23
     - a_nw
     - 440
     - eutrophic
     - direct
     - —
     - sole competitor
     - 0.285
     - 0.056
     - 0.699
     - 0
     - 
   * - L23
     - a_nw
     - 440
     - mesotrophic
     - direct
     - —
     - sole competitor
     - 0.22
     - -0.00527
     - 0.323
     - 0
     - 
   * - L23
     - a_nw
     - 440
     - oligotrophic
     - direct
     - —
     - sole competitor
     - 0.228
     - -0.0117
     - 0.284
     - 0
     - 
   * - L23
     - a_nw
     - 443
     - all
     - direct
     - —
     - sole competitor
     - 0.233
     - -0.0193
     - 0.33
     - 0
     - 
   * - L23
     - a_nw
     - 443
     - eutrophic
     - direct
     - —
     - sole competitor
     - 0.262
     - 0.0525
     - 0.69
     - 0
     - 
   * - L23
     - a_nw
     - 443
     - mesotrophic
     - direct
     - —
     - sole competitor
     - 0.225
     - -0.0179
     - 0.314
     - 0
     - 
   * - L23
     - a_nw
     - 443
     - oligotrophic
     - direct
     - —
     - sole competitor
     - 0.257
     - -0.0471
     - 0.288
     - 0
     - 
   * - L23
     - bb
     - 555
     - all
     - direct
     - —
     - sole competitor
     - 0.145
     - -0.034
     - 0.233
     - 0
     - 
   * - L23
     - bb
     - 555
     - eutrophic
     - direct
     - —
     - sole competitor
     - 0.143
     - -0.0946
     - 0.542
     - 0
     - 
   * - L23
     - bb
     - 555
     - mesotrophic
     - direct
     - —
     - sole competitor
     - 0.139
     - -0.0322
     - 0.227
     - 0
     - 
   * - L23
     - bb
     - 555
     - oligotrophic
     - direct
     - —
     - sole competitor
     - 0.173
     - -0.0223
     - 0.163
     - 0
     - 
   * - L23
     - bb
     - 670
     - all
     - direct
     - —
     - sole competitor
     - 0.691
     - -0.143
     - 0.159
     - 0
     - 
   * - L23
     - bb
     - 670
     - eutrophic
     - direct
     - —
     - sole competitor
     - 0.277
     - -0.172
     - 0.422
     - 0
     - 
   * - L23
     - bb
     - 670
     - mesotrophic
     - direct
     - —
     - sole competitor
     - 0.682
     - -0.143
     - 0.152
     - 0
     - 
   * - L23
     - bb
     - 670
     - oligotrophic
     - direct
     - —
     - sole competitor
     - 0.917
     - -0.131
     - 0.0957
     - 0
     - 
   * - L23
     - bb_p
     - 555
     - all
     - direct
     - —
     - sole competitor
     - 0.34
     - -0.0775
     - 0.236
     - 0
     - 
   * - L23
     - bb_p
     - 555
     - eutrophic
     - direct
     - —
     - sole competitor
     - 0.184
     - -0.117
     - 0.539
     - 0
     - 
   * - L23
     - bb_p
     - 555
     - mesotrophic
     - direct
     - —
     - sole competitor
     - 0.298
     - -0.0649
     - 0.23
     - 0
     - 
   * - L23
     - bb_p
     - 555
     - oligotrophic
     - direct
     - —
     - sole competitor
     - 0.603
     - -0.118
     - 0.163
     - 0
     - 
   * - L23
     - bb_p
     - 670
     - all
     - direct
     - —
     - sole competitor
     - 0.956
     - -0.0605
     - 0.181
     - 0
     - 
   * - L23
     - bb_p
     - 670
     - eutrophic
     - direct
     - —
     - sole competitor
     - 0.315
     - -0.187
     - 0.421
     - 0
     - 
   * - L23
     - bb_p
     - 670
     - mesotrophic
     - direct
     - —
     - sole competitor
     - 0.962
     - -0.0958
     - 0.172
     - 0
     - 
   * - L23
     - bb_p
     - 670
     - oligotrophic
     - direct
     - —
     - sole competitor
     - 1.3
     - 0.219
     - 0.12
     - 0
     - 

Are its uncertainties honest?
-----------------------------

A retrieval can be the most accurate and still be over-confident: the verdict compares empirical coverage with its nominal 0.68 / 0.95 target, and *consistent* means "not distinguishable from nominal at this sample size" rather than "calibrated".

.. list-table:: ls2_iii — interval calibration
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
     - —
     - —
     - 0
   * - L23
     - a
     - 440
     - eutrophic
     - —
     - —
     - 0
   * - L23
     - a
     - 440
     - mesotrophic
     - —
     - —
     - 0
   * - L23
     - a
     - 440
     - oligotrophic
     - —
     - —
     - 0
   * - L23
     - a
     - 443
     - all
     - —
     - —
     - 0
   * - L23
     - a
     - 443
     - eutrophic
     - —
     - —
     - 0
   * - L23
     - a
     - 443
     - mesotrophic
     - —
     - —
     - 0
   * - L23
     - a
     - 443
     - oligotrophic
     - —
     - —
     - 0
   * - L23
     - a_nw
     - 440
     - all
     - —
     - —
     - 0
   * - L23
     - a_nw
     - 440
     - eutrophic
     - —
     - —
     - 0
   * - L23
     - a_nw
     - 440
     - mesotrophic
     - —
     - —
     - 0
   * - L23
     - a_nw
     - 440
     - oligotrophic
     - —
     - —
     - 0
   * - L23
     - a_nw
     - 443
     - all
     - —
     - —
     - 0
   * - L23
     - a_nw
     - 443
     - eutrophic
     - —
     - —
     - 0
   * - L23
     - a_nw
     - 443
     - mesotrophic
     - —
     - —
     - 0
   * - L23
     - a_nw
     - 443
     - oligotrophic
     - —
     - —
     - 0
   * - L23
     - bb
     - 555
     - all
     - —
     - —
     - 0
   * - L23
     - bb
     - 555
     - eutrophic
     - —
     - —
     - 0
   * - L23
     - bb
     - 555
     - mesotrophic
     - —
     - —
     - 0
   * - L23
     - bb
     - 555
     - oligotrophic
     - —
     - —
     - 0
   * - L23
     - bb
     - 670
     - all
     - —
     - —
     - 0
   * - L23
     - bb
     - 670
     - eutrophic
     - —
     - —
     - 0
   * - L23
     - bb
     - 670
     - mesotrophic
     - —
     - —
     - 0
   * - L23
     - bb
     - 670
     - oligotrophic
     - —
     - —
     - 0
   * - L23
     - bb_p
     - 555
     - all
     - —
     - —
     - 0
   * - L23
     - bb_p
     - 555
     - eutrophic
     - —
     - —
     - 0
   * - L23
     - bb_p
     - 555
     - mesotrophic
     - —
     - —
     - 0
   * - L23
     - bb_p
     - 555
     - oligotrophic
     - —
     - —
     - 0
   * - L23
     - bb_p
     - 670
     - all
     - —
     - —
     - 0
   * - L23
     - bb_p
     - 670
     - eutrophic
     - —
     - —
     - 0
   * - L23
     - bb_p
     - 670
     - mesotrophic
     - —
     - —
     - 0
   * - L23
     - bb_p
     - 670
     - oligotrophic
     - —
     - —
     - 0

Head-to-head against the others
-------------------------------

.. list-table:: ls2_iii — pairwise verdicts
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
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 440
     - expb_pow
     - ls2_iii
     - 3.02e+03
     - -0.0663
     - -0.0729
     - -0.0594
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 440
     - giop
     - ls2_iii
     - 3.01e+03
     - -0.0685
     - -0.0741
     - -0.0624
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 440
     - expb_pow
     - ls2_iii
     - 527
     - -0.0793
     - -0.0894
     - -0.0693
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 440
     - giop
     - ls2_iii
     - 518
     - -0.0649
     - -0.075
     - -0.0537
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 440
     - expb_pow
     - ls2_iii
     - 2.32e+03
     - -0.0844
     - -0.0909
     - -0.0778
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 440
     - giop
     - ls2_iii
     - 2.32e+03
     - -0.0795
     - -0.0858
     - -0.0736
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 440
     - expb_pow
     - ls2_iii
     - 166
     - 0.309
     - 0.232
     - 0.389
     - ls2_iii
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 440
     - giop
     - ls2_iii
     - 166
     - 0.0995
     - 0.0502
     - 0.148
     - underpowered
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 443
     - expb_pow
     - ls2_iii
     - 3.02e+03
     - -0.0638
     - -0.0703
     - -0.0574
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 443
     - giop
     - ls2_iii
     - 3.01e+03
     - -0.0656
     - -0.0711
     - -0.06
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 443
     - expb_pow
     - ls2_iii
     - 528
     - -0.0806
     - -0.0898
     - -0.0708
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 443
     - giop
     - ls2_iii
     - 518
     - -0.0642
     - -0.074
     - -0.0543
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 443
     - expb_pow
     - ls2_iii
     - 2.32e+03
     - -0.0805
     - -0.0868
     - -0.0734
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 443
     - giop
     - ls2_iii
     - 2.32e+03
     - -0.0756
     - -0.0818
     - -0.0692
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 443
     - expb_pow
     - ls2_iii
     - 166
     - 0.294
     - 0.22
     - 0.37
     - ls2_iii
   * - ls2_l23_x1_board_v1
     - L23
     - a
     - 443
     - giop
     - ls2_iii
     - 166
     - 0.0917
     - 0.0446
     - 0.136
     - underpowered
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 440
     - expb_pow
     - ls2_iii
     - 3.02e+03
     - -0.099
     - -0.107
     - -0.0898
     - underpowered
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 440
     - giop
     - ls2_iii
     - 3.01e+03
     - -0.0975
     - -0.105
     - -0.0889
     - underpowered
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 440
     - expb_pow
     - ls2_iii
     - 527
     - -0.139
     - -0.156
     - -0.122
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 440
     - giop
     - ls2_iii
     - 518
     - -0.113
     - -0.132
     - -0.0958
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 440
     - expb_pow
     - ls2_iii
     - 2.32e+03
     - -0.114
     - -0.123
     - -0.106
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 440
     - giop
     - ls2_iii
     - 2.32e+03
     - -0.107
     - -0.115
     - -0.0975
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 440
     - expb_pow
     - ls2_iii
     - 166
     - 0.318
     - 0.238
     - 0.399
     - ls2_iii
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 440
     - giop
     - ls2_iii
     - 166
     - 0.102
     - 0.0447
     - 0.153
     - ls2_iii
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 443
     - expb_pow
     - ls2_iii
     - 3.02e+03
     - -0.106
     - -0.115
     - -0.0972
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 443
     - giop
     - ls2_iii
     - 3.01e+03
     - -0.103
     - -0.11
     - -0.0945
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 443
     - expb_pow
     - ls2_iii
     - 528
     - -0.163
     - -0.183
     - -0.145
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 443
     - giop
     - ls2_iii
     - 518
     - -0.131
     - -0.152
     - -0.11
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 443
     - expb_pow
     - ls2_iii
     - 2.32e+03
     - -0.118
     - -0.126
     - -0.109
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 443
     - giop
     - ls2_iii
     - 2.32e+03
     - -0.109
     - -0.117
     - -0.101
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 443
     - expb_pow
     - ls2_iii
     - 166
     - 0.305
     - 0.233
     - 0.379
     - ls2_iii
   * - ls2_l23_x1_board_v1
     - L23
     - a_nw
     - 443
     - giop
     - ls2_iii
     - 166
     - 0.095
     - 0.045
     - 0.141
     - underpowered
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 555
     - expb_pow
     - ls2_iii
     - 3.03e+03
     - -0.0895
     - -0.0946
     - -0.0848
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 555
     - giop
     - ls2_iii
     - 3.01e+03
     - -0.0914
     - -0.0959
     - -0.0868
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 555
     - expb_pow
     - ls2_iii
     - 542
     - -0.128
     - -0.141
     - -0.116
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 555
     - giop
     - ls2_iii
     - 518
     - -0.124
     - -0.135
     - -0.113
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 555
     - expb_pow
     - ls2_iii
     - 2.32e+03
     - -0.0915
     - -0.0964
     - -0.0868
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 555
     - giop
     - ls2_iii
     - 2.32e+03
     - -0.0889
     - -0.0935
     - -0.084
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 555
     - expb_pow
     - ls2_iii
     - 166
     - 0.0746
     - 0.0435
     - 0.111
     - underpowered
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 555
     - giop
     - ls2_iii
     - 166
     - -0.0209
     - -0.0467
     - 0.00343
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 670
     - expb_pow
     - ls2_iii
     - 2.79e+03
     - -0.603
     - -0.643
     - -0.571
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 670
     - giop
     - ls2_iii
     - 2.77e+03
     - -0.56
     - -0.597
     - -0.525
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 670
     - expb_pow
     - ls2_iii
     - 471
     - -0.825
     - -0.948
     - -0.714
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 670
     - giop
     - ls2_iii
     - 449
     - -0.846
     - -0.993
     - -0.734
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 670
     - expb_pow
     - ls2_iii
     - 2.15e+03
     - -0.599
     - -0.643
     - -0.557
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 670
     - giop
     - ls2_iii
     - 2.15e+03
     - -0.542
     - -0.589
     - -0.503
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 670
     - expb_pow
     - ls2_iii
     - 166
     - -0.128
     - -0.194
     - -0.0762
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb
     - 670
     - giop
     - ls2_iii
     - 166
     - -0.126
     - -0.197
     - -0.0726
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 555
     - expb_pow
     - ls2_iii
     - 3.01e+03
     - -0.234
     - -0.251
     - -0.219
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 555
     - giop
     - ls2_iii
     - 2.99e+03
     - -0.228
     - -0.244
     - -0.214
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 555
     - expb_pow
     - ls2_iii
     - 531
     - -0.471
     - -0.546
     - -0.401
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 555
     - giop
     - ls2_iii
     - 514
     - -0.437
     - -0.5
     - -0.383
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 555
     - expb_pow
     - ls2_iii
     - 2.31e+03
     - -0.207
     - -0.221
     - -0.193
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 555
     - giop
     - ls2_iii
     - 2.31e+03
     - -0.2
     - -0.214
     - -0.187
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 555
     - expb_pow
     - ls2_iii
     - 166
     - 0.074
     - 0.0352
     - 0.111
     - underpowered
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 555
     - giop
     - ls2_iii
     - 166
     - -0.0388
     - -0.0731
     - -0.00596
     - indistinguishable
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 670
     - expb_pow
     - ls2_iii
     - 2.5e+03
     - -0.816
     - -0.869
     - -0.762
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 670
     - giop
     - ls2_iii
     - 2.48e+03
     - -0.746
     - -0.806
     - -0.692
     - giop
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 670
     - expb_pow
     - ls2_iii
     - 380
     - -1.11
     - -1.26
     - -0.96
     - expb_pow
   * - ls2_l23_x1_board_v1
     - L23
     - bb_p
     - 670
     - giop
     - ls2_iii
     - 363
     - -1.15
     - -1.32
     - -0.992
     - giop

(4 further rows are on the :doc:`/reports/leaderboard_full` page.)

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

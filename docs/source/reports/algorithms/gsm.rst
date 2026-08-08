=======================
Algorithm profile — gsm
=======================

In one paragraph
----------------

``gsm`` has scoreable results on **L23, PANGAEA** across 1 sweep(s). Its best contest is bb(555) on L23, at mae 0.0255 (2.6% multiplicative error); its worst is a_ph(443) on PANGAEA at 36. It produced a usable fit for 1%-100% of the spectra it was given, depending on the dataset — read that together with the accuracy, since a good score over few spectra is not a better algorithm than a fair score over all of them.

What it parameterizes
---------------------

Read from the registry entry that sweeps actually run, so it cannot drift from the configuration behind the numbers below.

.. list-table::
   :stub-columns: 1
   :widths: auto

   * - a_nw model
     - GSM
   * - bb_nw model
     - GSM
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
   * - ``gsm``
     - scored (n=3286)
     - scored (n=50)

Accuracy, by dataset and contest
--------------------------------

One row per contest **and trophic stratum** — ``all`` is the pooled population, the others its Chl bins (:data:`ioptics.metrics.CHL_BINS`), so a pooled row and its bins are not independent results. This algorithm has rows in 5 strata.

.. list-table:: gsm — scored contests
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
     - sole competitor
     - 0.0958
     - 0.0913
     - 0.578
     - 0.99
     - 
   * - L23
     - a
     - 440
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.528
     - 0.528
     - 0.239
     - 0.847
     - 
   * - L23
     - a
     - 440
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.0902
     - 0.0869
     - 0.57
     - 0.997
     - 
   * - L23
     - a
     - 440
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.035
     - 0.0253
     - 0.682
     - 1
     - 
   * - L23
     - a
     - 443
     - all
     - chisq
     - —
     - sole competitor
     - 0.11
     - 0.107
     - 0.534
     - 0.99
     - 
   * - L23
     - a
     - 443
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.576
     - 0.576
     - 0.187
     - 0.847
     - 
   * - L23
     - a
     - 443
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.106
     - 0.104
     - 0.522
     - 0.997
     - 
   * - L23
     - a
     - 443
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.0389
     - 0.0322
     - 0.662
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - all
     - chisq
     - —
     - sole competitor
     - 0.156
     - 0.0759
     - 0.585
     - 0.99
     - 
   * - L23
     - a_dg
     - 440
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.46
     - 0.458
     - 0.422
     - 0.847
     - 
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.146
     - 0.0688
     - 0.589
     - 0.997
     - 
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.132
     - 0.0286
     - 0.609
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - all
     - chisq
     - —
     - sole competitor
     - 0.153
     - 0.0376
     - 0.614
     - 0.99
     - 
   * - L23
     - a_dg
     - 443
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.409
     - 0.403
     - 0.478
     - 0.847
     - 
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.143
     - 0.0307
     - 0.62
     - 0.997
     - 
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.138
     - -0.00727
     - 0.623
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - all
     - chisq
     - —
     - sole competitor
     - 0.278
     - 0.195
     - 0.725
     - 0.99
     - 
   * - L23
     - a_ph
     - 440
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.687
     - 0.687
     - 0.453
     - 0.847
     - 
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.268
     - 0.193
     - 0.733
     - 0.997
     - 
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.236
     - 0.11
     - 0.756
     - 1
     - 
   * - L23
     - a_ph
     - 443
     - all
     - chisq
     - —
     - sole competitor
     - 0.343
     - 0.296
     - 0.682
     - 0.99
     - 
   * - L23
     - a_ph
     - 443
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.849
     - 0.849
     - 0.197
     - 0.847
     - 
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.335
     - 0.295
     - 0.691
     - 0.997
     - 
   * - L23
     - a_ph
     - 443
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.277
     - 0.198
     - 0.756
     - 1
     - 
   * - L23
     - bb
     - 555
     - all
     - chisq
     - —
     - sole competitor
     - 0.0352
     - -0.0215
     - 0.582
     - 0.99
     - 
   * - L23
     - bb
     - 555
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.0562
     - 0.0367
     - 0.768
     - 0.847
     - 
   * - L23
     - bb
     - 555
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.0365
     - -0.03
     - 0.531
     - 0.997
     - 
   * - L23
     - bb
     - 555
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.0255
     - -0.0017
     - 0.737
     - 1
     - 
   * - L23
     - bb
     - 670
     - all
     - chisq
     - —
     - sole competitor
     - 0.0326
     - 0.0108
     - 0.538
     - 0.99
     - 
   * - L23
     - bb
     - 670
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.0355
     - 0.017
     - 0.896
     - 0.847
     - 
   * - L23
     - bb
     - 670
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.0282
     - 0.0011
     - 0.554
     - 0.997
     - 
   * - L23
     - bb
     - 670
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.0492
     - 0.0472
     - 0.394
     - 1
     - 
   * - L23
     - bb_p
     - 555
     - all
     - chisq
     - —
     - sole competitor
     - 0.0696
     - -0.0319
     - 0.577
     - 0.99
     - 
   * - L23
     - bb_p
     - 555
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.066
     - 0.0402
     - 0.768
     - 0.847
     - 
   * - L23
     - bb_p
     - 555
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.0681
     - -0.0482
     - 0.525
     - 0.997
     - 
   * - L23
     - bb_p
     - 555
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.0762
     - 0.0164
     - 0.735
     - 1
     - 
   * - L23
     - bb_p
     - 670
     - all
     - chisq
     - —
     - sole competitor
     - 0.061
     - 0.0313
     - 0.537
     - 0.99
     - 
   * - L23
     - bb_p
     - 670
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.0389
     - 0.0176
     - 0.893
     - 0.847
     - 
   * - L23
     - bb_p
     - 670
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.0477
     - 0.0112
     - 0.554
     - 0.997
     - 
   * - L23
     - bb_p
     - 670
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.119
     - 0.116
     - 0.394
     - 1
     - 
   * - PANGAEA
     - a_dg
     - 443
     - all
     - chisq
     - —
     - sole competitor
     - 0.431
     - -0.175
     - 0.728
     - 0.0503
     - 
   * - PANGAEA
     - a_dg
     - 443
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.209
     - 0.209
     - 0.5
     - 0.0115
     - 
   * - PANGAEA
     - a_dg
     - 443
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.338
     - -0.143
     - 0.726
     - 0.0908
     - 
   * - PANGAEA
     - a_dg
     - 443
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 1.18
     - -0.448
     - 0.7
     - 0.0926
     - 
   * - PANGAEA
     - a_dg
     - 443
     - unknown
     - chisq
     - —
     - sole competitor
     - 0.514
     - -0.0883
     - 0.857
     - 0.015
     - 
   * - PANGAEA
     - a_ph
     - 443
     - all
     - chisq
     - —
     - sole competitor
     - 1.06
     - -0.453
     - 0.253
     - 0.0503
     - 
   * - PANGAEA
     - a_ph
     - 443
     - eutrophic
     - chisq
     - —
     - sole competitor
     - 0.199
     - -0.166
     - 0.25
     - 0.0115
     - 
   * - PANGAEA
     - a_ph
     - 443
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.611
     - -0.272
     - 0.264
     - 0.0908
     - 
   * - PANGAEA
     - a_ph
     - 443
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.668
     - -0.4
     - 0.0833
     - 0.0926
     - 
   * - PANGAEA
     - a_ph
     - 443
     - unknown
     - chisq
     - —
     - sole competitor
     - 36
     - -0.973
     - 0.429
     - 0.015
     - 
   * - PANGAEA
     - bb_p
     - 555
     - all
     - chisq
     - —
     - sole competitor
     - 0.354
     - -0.0279
     - 0.692
     - 0.0503
     - 
   * - PANGAEA
     - bb_p
     - 555
     - mesotrophic
     - chisq
     - —
     - sole competitor
     - 0.3
     - -0.183
     - 0.556
     - 0.0908
     - 
   * - PANGAEA
     - bb_p
     - 555
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.501
     - 0.501
     - 1
     - 0.0926
     - 
   * - PANGAEA
     - bb_p
     - 670
     - all
     - chisq
     - —
     - sole competitor
     - 0.431
     - 0.431
     - 0
     - 0.0503
     - 
   * - PANGAEA
     - bb_p
     - 670
     - oligotrophic
     - chisq
     - —
     - sole competitor
     - 0.431
     - 0.431
     - 0
     - 0.0926
     - 

Are its uncertainties honest?
-----------------------------

A retrieval can be the most accurate and still be over-confident: the verdict compares empirical coverage with its nominal 0.68 / 0.95 target, and *consistent* means "not distinguishable from nominal at this sample size" rather than "calibrated".

.. list-table:: gsm — interval calibration
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
     - 0.166
     - 0.317
     - 3.29e+03
   * - L23
     - a
     - 440
     - eutrophic
     - 0
     - 0
     - 150
   * - L23
     - a
     - 440
     - mesotrophic
     - 0.138
     - 0.265
     - 2.49e+03
   * - L23
     - a
     - 440
     - oligotrophic
     - 0.315
     - 0.591
     - 648
   * - L23
     - a
     - 443
     - all
     - 0.137
     - 0.268
     - 3.29e+03
   * - L23
     - a
     - 443
     - eutrophic
     - 0
     - 0
     - 150
   * - L23
     - a
     - 443
     - mesotrophic
     - 0.105
     - 0.214
     - 2.49e+03
   * - L23
     - a
     - 443
     - oligotrophic
     - 0.292
     - 0.539
     - 648
   * - L23
     - a_dg
     - 440
     - all
     - 0.194
     - 0.36
     - 3.29e+03
   * - L23
     - a_dg
     - 440
     - eutrophic
     - 0.0267
     - 0.0467
     - 150
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 0.192
     - 0.368
     - 2.49e+03
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 0.239
     - 0.4
     - 648
   * - L23
     - a_dg
     - 443
     - all
     - 0.182
     - 0.358
     - 3.29e+03
   * - L23
     - a_dg
     - 443
     - eutrophic
     - 0.0333
     - 0.107
     - 150
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 0.189
     - 0.367
     - 2.49e+03
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 0.193
     - 0.381
     - 648
   * - L23
     - a_ph
     - 440
     - all
     - 0.223
     - 0.405
     - 3.29e+03
   * - L23
     - a_ph
     - 440
     - eutrophic
     - 0.00667
     - 0.0267
     - 150
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 0.21
     - 0.389
     - 2.49e+03
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 0.321
     - 0.556
     - 648
   * - L23
     - a_ph
     - 443
     - all
     - 0.181
     - 0.332
     - 3.29e+03
   * - L23
     - a_ph
     - 443
     - eutrophic
     - 0
     - 0.00667
     - 150
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - 0.169
     - 0.312
     - 2.49e+03
   * - L23
     - a_ph
     - 443
     - oligotrophic
     - 0.269
     - 0.485
     - 648
   * - L23
     - bb
     - 555
     - all
     - 0.131
     - 0.243
     - 3.29e+03
   * - L23
     - bb
     - 555
     - eutrophic
     - 0.22
     - 0.4
     - 150
   * - L23
     - bb
     - 555
     - mesotrophic
     - 0.115
     - 0.217
     - 2.49e+03
   * - L23
     - bb
     - 555
     - oligotrophic
     - 0.17
     - 0.306
     - 648
   * - L23
     - bb
     - 670
     - all
     - 0.233
     - 0.417
     - 3.29e+03
   * - L23
     - bb
     - 670
     - eutrophic
     - 0.413
     - 0.687
     - 150
   * - L23
     - bb
     - 670
     - mesotrophic
     - 0.245
     - 0.445
     - 2.49e+03
   * - L23
     - bb
     - 670
     - oligotrophic
     - 0.145
     - 0.248
     - 648
   * - L23
     - bb_p
     - 555
     - all
     - 0.131
     - 0.243
     - 3.29e+03
   * - L23
     - bb_p
     - 555
     - eutrophic
     - 0.22
     - 0.4
     - 150
   * - L23
     - bb_p
     - 555
     - mesotrophic
     - 0.115
     - 0.217
     - 2.49e+03
   * - L23
     - bb_p
     - 555
     - oligotrophic
     - 0.17
     - 0.306
     - 648
   * - L23
     - bb_p
     - 670
     - all
     - 0.233
     - 0.417
     - 3.29e+03
   * - L23
     - bb_p
     - 670
     - eutrophic
     - 0.413
     - 0.687
     - 150
   * - L23
     - bb_p
     - 670
     - mesotrophic
     - 0.245
     - 0.445
     - 2.49e+03
   * - L23
     - bb_p
     - 670
     - oligotrophic
     - 0.145
     - 0.248
     - 648
   * - PANGAEA
     - a_dg
     - 443
     - all
     - 0.262
     - 0.405
     - 42
   * - PANGAEA
     - a_dg
     - 443
     - eutrophic
     - 0
     - 1
     - 1
   * - PANGAEA
     - a_dg
     - 443
     - mesotrophic
     - 0.312
     - 0.469
     - 32
   * - PANGAEA
     - a_dg
     - 443
     - oligotrophic
     - 0
     - 0
     - 5
   * - PANGAEA
     - a_dg
     - 443
     - unknown
     - 0.25
     - 0.25
     - 4
   * - PANGAEA
     - a_ph
     - 443
     - all
     - 0.347
     - 0.816
     - 49
   * - PANGAEA
     - a_ph
     - 443
     - eutrophic
     - 1
     - 1
     - 2
   * - PANGAEA
     - a_ph
     - 443
     - mesotrophic
     - 0.324
     - 0.811
     - 37
   * - PANGAEA
     - a_ph
     - 443
     - oligotrophic
     - 0.429
     - 0.857
     - 7
   * - PANGAEA
     - a_ph
     - 443
     - unknown
     - 0
     - 0.667
     - 3
   * - PANGAEA
     - bb_p
     - 555
     - all
     - 0.286
     - 0.429
     - 7
   * - PANGAEA
     - bb_p
     - 555
     - mesotrophic
     - 0.4
     - 0.6
     - 5
   * - PANGAEA
     - bb_p
     - 555
     - oligotrophic
     - 0
     - 0
     - 2
   * - PANGAEA
     - bb_p
     - 670
     - all
     - 0
     - 0
     - 2
   * - PANGAEA
     - bb_p
     - 670
     - oligotrophic
     - 0
     - 0
     - 2

Head-to-head against the others
-------------------------------

.. list-table:: gsm — pairwise verdicts
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
     - gsm
     - 149
     - -0.0155
     - -0.0526
     - 0.0233
     - indistinguishable
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
     - gsm
     - 149
     - -0.0946
     - -0.131
     - -0.0565
     - underpowered
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
     - gsm
     - 3.28e+03
     - 8.57e-05
     - -0.00127
     - 0.00147
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
     - gsm
     - 648
     - 0.00155
     - -7.74e-05
     - 0.0032
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
     - gsm
     - 2.49e+03
     - -0.00744
     - -0.00839
     - -0.00644
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
     - gsm
     - 149
     - 0.129
     - 0.111
     - 0.146
     - gsm
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
     - gsm
     - 3.28e+03
     - 0.00165
     - 0.000969
     - 0.00234
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
     - gsm
     - 648
     - 0.00106
     - 0.000702
     - 0.0014
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
     - gsm
     - 2.49e+03
     - -0.00195
     - -0.00252
     - -0.00145
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
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 670
     - expb_pow
     - gsm
     - 149
     - 0.0667
     - 0.0593
     - 0.0741
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - bb
     - 670
     - giop
     - gsm
     - 140
     - 0.0483
     - 0.0417
     - 0.0548
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 440
     - expb_pow
     - gsm
     - 3.28e+03
     - 0.141
     - 0.11
     - 0.174
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 440
     - giop
     - gsm
     - 3.26e+03
     - 0.32
     - 0.313
     - 0.329
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 440
     - expb_pow
     - gsm
     - 648
     - 0.181
     - 0.128
     - 0.241
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 440
     - giop
     - gsm
     - 637
     - 0.373
     - 0.351
     - 0.396
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 440
     - expb_pow
     - gsm
     - 2.49e+03
     - 0.146
     - 0.109
     - 0.188
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 440
     - giop
     - gsm
     - 2.48e+03
     - 0.324
     - 0.315
     - 0.333
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 440
     - expb_pow
     - gsm
     - 149
     - -0.159
     - -0.224
     - -0.0919
     - expb_pow
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 440
     - giop
     - gsm
     - 140
     - -0.0298
     - -0.0698
     - 0.00846
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 443
     - expb_pow
     - gsm
     - 3.28e+03
     - 0.0592
     - 0.0294
     - 0.0949
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 443
     - giop
     - gsm
     - 3.26e+03
     - 0.288
     - 0.28
     - 0.295
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 443
     - expb_pow
     - gsm
     - 648
     - 0.133
     - 0.0824
     - 0.192
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 443
     - giop
     - gsm
     - 637
     - 0.389
     - 0.369
     - 0.409
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 443
     - expb_pow
     - gsm
     - 2.49e+03
     - 0.06
     - 0.023
     - 0.0974
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 443
     - giop
     - gsm
     - 2.48e+03
     - 0.286
     - 0.278
     - 0.293
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 443
     - expb_pow
     - gsm
     - 149
     - -0.356
     - -0.427
     - -0.285
     - expb_pow
   * - multi_L23_PANGAEA_v2
     - L23
     - a_ph
     - 443
     - giop
     - gsm
     - 140
     - -0.23
     - -0.272
     - -0.186
     - giop
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 440
     - expb_pow
     - gsm
     - 3.28e+03
     - 0.0644
     - 0.0568
     - 0.0716
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 440
     - giop
     - gsm
     - 3.26e+03
     - 0.00957
     - 0.00449
     - 0.0148
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 440
     - expb_pow
     - gsm
     - 648
     - 0.0735
     - 0.0578
     - 0.0894
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 440
     - giop
     - gsm
     - 637
     - 0.0195
     - 0.0116
     - 0.0278
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 440
     - expb_pow
     - gsm
     - 2.49e+03
     - 0.0587
     - 0.0507
     - 0.0668
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 440
     - giop
     - gsm
     - 2.48e+03
     - 0.0167
     - 0.0114
     - 0.0224
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 440
     - expb_pow
     - gsm
     - 149
     - 0.135
     - 0.0561
     - 0.219
     - gsm
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 440
     - giop
     - gsm
     - 140
     - -0.191
     - -0.248
     - -0.126
     - giop
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 443
     - expb_pow
     - gsm
     - 3.28e+03
     - 0.0797
     - 0.0721
     - 0.0875
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 443
     - giop
     - gsm
     - 3.26e+03
     - 0.0226
     - 0.0176
     - 0.0276
     - indistinguishable
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 443
     - expb_pow
     - gsm
     - 648
     - 0.0845
     - 0.0686
     - 0.101
     - underpowered
   * - multi_L23_PANGAEA_v2
     - L23
     - a_dg
     - 443
     - giop
     - gsm
     - 637
     - 0.0237
     - 0.0158
     - 0.0315
     - indistinguishable

(50 further rows are on the :doc:`/reports/leaderboard_full` page.)

Per-spectrum behaviour
----------------------

Exemplar fits (best / worst / median) live on each sweep's own page; the accuracy-vs-wavelength view is built per sweep as well. Both are linked from the contributing sweeps listed on :doc:`/reports/index`.

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

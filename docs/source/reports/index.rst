=======
Reports
=======

This is the single **accumulating** report site for IOPtics. As sweeps are run,
each one contributes a provenance-stamped report page under this section, and
the persistent **leaderboard** (ranking algorithms across all sweeps) becomes
the landing page (design doc §Reporting).

Report pages are generated **on demand** by a sweep's build script
(``ioptics/runs/prototypes/<name>/build_vN.py``, stage flag 3) via
:func:`ioptics.report.standard.build`, then committed into this tree so Read the
Docs builds them directly. The heavy artifacts (parquet tables, raw MCMC
chains) stay under ``$OS_COLOR/IOPtics/runs/`` and are not committed.

Reading the leaderboard
-----------------------

The table below is the **persistent, cross-sweep leaderboard**: every sweep's
accuracy at the diagnostic reference wavelengths (e.g. 440, 555 nm) is folded
into one ranked store (:func:`ioptics.report.leaderboard.update`), so the
standing comparison grows as algorithms and datasets accumulate. (The fold is
idempotent — re-running a sweep just replaces its rows.) Each row is one
algorithm's score for one contest — a ``(dataset, component, reference
wavelength, trophic stratum)`` combination:

- **rank** — 1 = best in that contest. The default ordering is by **wins**,
  breaking ties by :math:`|\text{bias}|` then MAE (see below).
- **win_frac** — the head-to-head win fraction: for each individual spectrum,
  the algorithm whose retrieval is *closer to the true value* wins; ``win_frac``
  is the share of spectra it wins. 0.5 = a tie, 1.0 = always closest.
- **mae** — *mean absolute error*, computed on :math:`\log_{10}` values so it
  reads as a **multiplicative** (fractional) error: ``0`` is perfect, ``0.1`` ≈
  “typically off by ~10 %”, ``0.3`` ≈ ~2× off. (Log space is used because IOPs
  span orders of magnitude.)
- **bias** — the *signed* version of MAE: positive = the algorithm systematically
  over-estimates, negative = under-estimates (again multiplicative; 0 =
  unbiased).
- **coverage68 / coverage95** — a **calibration** check on the reported
  uncertainties: the fraction of truth values that fall inside the retrieval's
  68 % / 95 % confidence interval. Well-calibrated error bars land near 0.68 /
  0.95; much lower means the stated uncertainties are too tight (over-confident).

Each sweep also gets its own provenance-stamped page (linked below) with the
figures and tables behind these numbers.

.. LEADERBOARD_START (auto-generated; do not edit)

Leaderboard
-----------

.. list-table:: Leaderboard
   :header-rows: 1
   :widths: auto

   * - dataset
     - component
     - ref_wave
     - fit_method
     - rank
     - ranking
     - algorithm
     - win_frac
     - mae
     - bias
     - frac_ok
     - coverage68
     - caveat
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - indistinguishable
     - expb_pow2
     - 0.639
     - 1.01
     - 0.194
     - 0.21
     - 0.5
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - indistinguishable
     - expb_powflex
     - 0.569
     - 1.06
     - 0.0989
     - 0.21
     - 0.333
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.431
     - 1
     - 0.289
     - 0.21
     - 0.417
     - CDOM_vs_adg
   * - GLORIA
     - a_dg
     - 440
     - chisq
     - —
     - indistinguishable
     - expb_pow2flat
     - 0.361
     - 1
     - 0.301
     - 0.21
     - 0.417
     - CDOM_vs_adg
   * - L23
     - a
     - 440
     - chisq
     - 1
     - ranked
     - expb_pow
     - 0.846
     - 0.0548
     - 0.0227
     - 0.998
     - 0.557
     - 
   * - L23
     - a
     - 440
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.7
     - 0.0624
     - 0.00518
     - 1
     - 0.421
     - 
   * - L23
     - a
     - 440
     - chisq
     - 3
     - ranked
     - gsm
     - 0.578
     - 0.0958
     - 0.0913
     - 0.99
     - 0.166
     - 
   * - L23
     - a
     - 440
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.575
     - 0.0987
     - 0.0411
     - 0.995
     - 0.455
     - 
   * - L23
     - a
     - 440
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.425
     - 0.0958
     - 0.0901
     - 0.985
     - 0.215
     - 
   * - L23
     - a
     - 440
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.3
     - 0.0725
     - 0.0693
     - 1
     - 0.2
     - 
   * - L23
     - a
     - 440
     - chisq
     - 7
     - ranked
     - giop
     - 0.0744
     - 0.183
     - 0.183
     - 0.989
     - 0.000609
     - 
   * - L23
     - a
     - 440
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.0681
     - 0.0178
     - 0.995
     - 0.691
     - 
   * - L23
     - a
     - 440
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.042
     - -0.0318
     - 1
     - 0.875
     - 
   * - L23
     - a
     - 443
     - chisq
     - 1
     - ranked
     - expb_pow
     - 0.874
     - 0.0528
     - 0.0229
     - 0.998
     - 0.538
     - 
   * - L23
     - a
     - 443
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.7
     - 0.0595
     - 0.00797
     - 1
     - 0.368
     - 
   * - L23
     - a
     - 443
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.585
     - 0.0949
     - 0.0401
     - 0.995
     - 0.442
     - 
   * - L23
     - a
     - 443
     - chisq
     - 4
     - ranked
     - gsm
     - 0.535
     - 0.11
     - 0.107
     - 0.99
     - 0.137
     - 
   * - L23
     - a
     - 443
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.415
     - 0.0927
     - 0.0871
     - 0.985
     - 0.214
     - 
   * - L23
     - a
     - 443
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.3
     - 0.0719
     - 0.0699
     - 1
     - 0.2
     - 
   * - L23
     - a
     - 443
     - chisq
     - 7
     - ranked
     - giop
     - 0.0905
     - 0.179
     - 0.179
     - 0.989
     - 0.000609
     - 
   * - L23
     - a
     - 443
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.0655
     - 0.0175
     - 0.995
     - 0.692
     - 
   * - L23
     - a
     - 443
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.0417
     - -0.0257
     - 1
     - 0.75
     - 
   * - L23
     - a_dg
     - 440
     - chisq
     - 1
     - ranked
     - giop
     - 0.694
     - 0.19
     - -0.0282
     - 0.985
     - 0.361
     - 
   * - L23
     - a_dg
     - 440
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.65
     - 0.126
     - -0.0505
     - 1
     - 0.35
     - 
   * - L23
     - a_dg
     - 440
     - chisq
     - —
     - indistinguishable
     - gsm
     - 0.586
     - 0.156
     - 0.0759
     - 0.99
     - 0.194
     - 
   * - L23
     - a_dg
     - 440
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.524
     - 0.166
     - -0.023
     - 0.989
     - 0.356
     - 
   * - L23
     - a_dg
     - 440
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.391
     - 0.222
     - 0.0296
     - 0.998
     - 0.758
     - 
   * - L23
     - a_dg
     - 440
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.35
     - 0.184
     - -0.00475
     - 1
     - 1
     - 
   * - L23
     - a_dg
     - 440
     - chisq
     - 7
     - ranked
     - expb_pow
     - 0.306
     - 0.32
     - 0.052
     - 0.995
     - 0.936
     - 
   * - L23
     - a_dg
     - 440
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.274
     - 0.129
     - 0.995
     - 0.628
     - 
   * - L23
     - a_dg
     - 440
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.246
     - 0.162
     - 1
     - 0.375
     - 
   * - L23
     - a_dg
     - 443
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.7
     - 0.137
     - -0.0727
     - 1
     - 0.35
     - 
   * - L23
     - a_dg
     - 443
     - chisq
     - 2
     - ranked
     - giop
     - 0.698
     - 0.2
     - -0.0507
     - 0.985
     - 0.337
     - 
   * - L23
     - a_dg
     - 443
     - chisq
     - —
     - indistinguishable
     - gsm
     - 0.614
     - 0.153
     - 0.0376
     - 0.99
     - 0.182
     - 
   * - L23
     - a_dg
     - 443
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.507
     - 0.177
     - -0.0454
     - 0.989
     - 0.337
     - 
   * - L23
     - a_dg
     - 443
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.379
     - 0.235
     - 0.018
     - 0.998
     - 0.766
     - 
   * - L23
     - a_dg
     - 443
     - chisq
     - 6
     - ranked
     - expb_pow
     - 0.302
     - 0.338
     - 0.0397
     - 0.995
     - 0.935
     - 
   * - L23
     - a_dg
     - 443
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.3
     - 0.201
     - -0.0171
     - 1
     - 1
     - 
   * - L23
     - a_dg
     - 443
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.28
     - 0.126
     - 0.995
     - 0.642
     - 
   * - L23
     - a_dg
     - 443
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.253
     - 0.157
     - 1
     - 0.375
     - 
   * - L23
     - a_ph
     - 440
     - chisq
     - 1
     - ranked
     - gsm
     - 0.725
     - 0.278
     - 0.195
     - 0.99
     - 0.223
     - 
   * - L23
     - a_ph
     - 440
     - chisq
     - 2
     - ranked
     - expb_pow
     - 0.617
     - 0.419
     - -0.121
     - 0.998
     - 0.775
     - 
   * - L23
     - a_ph
     - 440
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.6
     - 0.325
     - 0.305
     - 1
     - 0.3
     - 
   * - L23
     - a_ph
     - 440
     - chisq
     - 4
     - ranked
     - giop
     - 0.545
     - 0.369
     - 0.264
     - 0.985
     - 0.283
     - 
   * - L23
     - a_ph
     - 440
     - chisq
     - 5
     - ranked
     - expb_pow
     - 0.455
     - 1.07
     - -0.345
     - 0.995
     - 0.968
     - 
   * - L23
     - a_ph
     - 440
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.4
     - 1.17
     - -0.384
     - 1
     - 1
     - 
   * - L23
     - a_ph
     - 440
     - chisq
     - 7
     - ranked
     - giop
     - 0.157
     - 0.599
     - 0.594
     - 0.989
     - 0.0341
     - 
   * - L23
     - a_ph
     - 440
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 1.25
     - -0.481
     - 0.995
     - 0.578
     - 
   * - L23
     - a_ph
     - 440
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 1.64
     - -0.613
     - 1
     - 0.5
     - 
   * - L23
     - a_ph
     - 443
     - chisq
     - 1
     - ranked
     - gsm
     - 0.682
     - 0.343
     - 0.296
     - 0.99
     - 0.181
     - 
   * - L23
     - a_ph
     - 443
     - chisq
     - 2
     - ranked
     - expb_pow
     - 0.675
     - 0.402
     - -0.105
     - 0.998
     - 0.787
     - 
   * - L23
     - a_ph
     - 443
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.6
     - 0.355
     - 0.346
     - 1
     - 0.3
     - 
   * - L23
     - a_ph
     - 443
     - chisq
     - 4
     - ranked
     - giop
     - 0.516
     - 0.386
     - 0.29
     - 0.985
     - 0.27
     - 
   * - L23
     - a_ph
     - 443
     - chisq
     - 5
     - ranked
     - expb_pow
     - 0.484
     - 1.04
     - -0.329
     - 0.995
     - 0.969
     - 
   * - L23
     - a_ph
     - 443
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.4
     - 1.15
     - -0.362
     - 1
     - 1
     - 
   * - L23
     - a_ph
     - 443
     - chisq
     - 7
     - ranked
     - giop
     - 0.142
     - 0.63
     - 0.626
     - 0.989
     - 0.0244
     - 
   * - L23
     - a_ph
     - 443
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 1.19
     - -0.465
     - 0.995
     - 0.59
     - 
   * - L23
     - a_ph
     - 443
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 1.5
     - -0.588
     - 1
     - 0.625
     - 
   * - L23
     - bb
     - 555
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.686
     - 0.0359
     - -0.001
     - 0.998
     - 0.43
     - 
   * - L23
     - bb
     - 555
     - chisq
     - —
     - indistinguishable
     - gsm
     - 0.582
     - 0.0352
     - -0.0215
     - 0.99
     - 0.131
     - 
   * - L23
     - bb
     - 555
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.55
     - 0.0351
     - -0.0151
     - 1
     - 0.6
     - 
   * - L23
     - bb
     - 555
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.504
     - 0.0521
     - -0.0223
     - 0.985
     - 0.433
     - 
   * - L23
     - bb
     - 555
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.496
     - 0.0551
     - 0.00799
     - 0.995
     - 0.813
     - 
   * - L23
     - bb
     - 555
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.45
     - 0.038
     - 0.00215
     - 1
     - 0.9
     - 
   * - L23
     - bb
     - 555
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.231
     - 0.061
     - 0.0605
     - 0.989
     - 0.0298
     - 
   * - L23
     - bb
     - 555
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.0356
     - 0.00368
     - 1
     - 0.625
     - 
   * - L23
     - bb
     - 555
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.0468
     - 0.00743
     - 0.995
     - 0.595
     - 
   * - L23
     - bb
     - 670
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.75
     - 0.0713
     - 0.0218
     - 1
     - 0.9
     - 
   * - L23
     - bb
     - 670
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.728
     - 0.0861
     - 0.0256
     - 0.995
     - 0.777
     - 
   * - L23
     - bb
     - 670
     - chisq
     - —
     - indistinguishable
     - gsm
     - 0.538
     - 0.0326
     - 0.0108
     - 0.99
     - 0.233
     - 
   * - L23
     - bb
     - 670
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.496
     - 0.035
     - 0.0239
     - 0.998
     - 0.227
     - 
   * - L23
     - bb
     - 670
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.466
     - 0.0388
     - -0.00487
     - 0.989
     - 0.188
     - 
   * - L23
     - bb
     - 670
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.272
     - 0.127
     - -0.0958
     - 0.985
     - 0.151
     - 
   * - L23
     - bb
     - 670
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.25
     - 0.106
     - -0.0901
     - 1
     - 0.2
     - 
   * - L23
     - bb
     - 670
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.0684
     - 0.0375
     - 0.995
     - 0.656
     - 
   * - L23
     - bb
     - 670
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.0554
     - 0.0554
     - 1
     - 0.75
     - 
   * - L23
     - bb_p
     - 555
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.684
     - 0.0692
     - 0.00365
     - 0.998
     - 0.43
     - 
   * - L23
     - bb_p
     - 555
     - chisq
     - —
     - indistinguishable
     - gsm
     - 0.577
     - 0.0696
     - -0.0319
     - 0.99
     - 0.131
     - 
   * - L23
     - bb_p
     - 555
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.55
     - 0.0774
     - -0.0221
     - 1
     - 0.6
     - 
   * - L23
     - bb_p
     - 555
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.502
     - 0.105
     - -0.0388
     - 0.985
     - 0.433
     - 
   * - L23
     - bb_p
     - 555
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.498
     - 0.109
     - 0.0184
     - 0.995
     - 0.813
     - 
   * - L23
     - bb_p
     - 555
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.45
     - 0.0893
     - 0.0221
     - 1
     - 0.9
     - 
   * - L23
     - bb_p
     - 555
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.238
     - 0.132
     - 0.132
     - 0.989
     - 0.0298
     - 
   * - L23
     - bb_p
     - 555
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.0947
     - 0.0189
     - 0.995
     - 0.595
     - 
   * - L23
     - bb_p
     - 555
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.0872
     - 0.0217
     - 1
     - 0.625
     - 
   * - L23
     - bb_p
     - 670
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.75
     - 0.127
     - 0.0415
     - 1
     - 0.9
     - 
   * - L23
     - bb_p
     - 670
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.736
     - 0.145
     - 0.0477
     - 0.995
     - 0.777
     - 
   * - L23
     - bb_p
     - 670
     - chisq
     - —
     - indistinguishable
     - gsm
     - 0.537
     - 0.061
     - 0.0313
     - 0.99
     - 0.233
     - 
   * - L23
     - bb_p
     - 670
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.497
     - 0.0644
     - 0.0491
     - 0.998
     - 0.227
     - 
   * - L23
     - bb_p
     - 670
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.466
     - 0.0661
     - 0.00326
     - 0.989
     - 0.188
     - 
   * - L23
     - bb_p
     - 670
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.264
     - 0.21
     - -0.147
     - 0.985
     - 0.151
     - 
   * - L23
     - bb_p
     - 670
     - chisq
     - —
     - indistinguishable
     - giop
     - 0.25
     - 0.181
     - -0.142
     - 1
     - 0.2
     - 
   * - L23
     - bb_p
     - 670
     - mcmc
     - 1
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.118
     - 0.0706
     - 0.995
     - 0.656
     - 
   * - L23
     - bb_p
     - 670
     - mcmc
     - 2
     - ranked (no head-to-head)
     - expb_pow
     - —
     - 0.112
     - 0.112
     - 1
     - 0.75
     - 
   * - PANGAEA
     - a_dg
     - 440
     - chisq
     - 1
     - ranked
     - gsm
     - 0.728
     - 0.431
     - -0.175
     - 0.0339
     - 0.262
     - 
   * - PANGAEA
     - a_dg
     - 440
     - chisq
     - 2
     - ranked
     - gsm
     - 0.656
     - 0.453
     - -0.0991
     - 0.376
     - 0.413
     - 
   * - PANGAEA
     - a_dg
     - 440
     - chisq
     - 3
     - ranked
     - expb_pow
     - 0.483
     - 0.72
     - -0.162
     - 0.195
     - 0.934
     - 
   * - PANGAEA
     - a_dg
     - 440
     - chisq
     - 4
     - ranked
     - expb_pow
     - 0.451
     - 1.05
     - -0.329
     - 0.432
     - 0.97
     - 
   * - PANGAEA
     - a_dg
     - 440
     - chisq
     - 5
     - ranked
     - giop
     - 0.439
     - 2.23
     - -0.647
     - 0.266
     - 0.243
     - 
   * - PANGAEA
     - a_dg
     - 440
     - chisq
     - 6
     - ranked
     - giop
     - 0.405
     - 2.14
     - -0.634
     - 0.526
     - 0.373
     - 
   * - PANGAEA
     - a_dg
     - 443
     - chisq
     - 1
     - ranked
     - gsm
     - 0.728
     - 0.431
     - -0.175
     - 0.0339
     - 0.262
     - 
   * - PANGAEA
     - a_dg
     - 443
     - chisq
     - 2
     - ranked
     - gsm
     - 0.656
     - 0.453
     - -0.0991
     - 0.376
     - 0.413
     - 
   * - PANGAEA
     - a_dg
     - 443
     - chisq
     - 3
     - ranked
     - expb_pow
     - 0.483
     - 0.72
     - -0.162
     - 0.195
     - 0.934
     - 
   * - PANGAEA
     - a_dg
     - 443
     - chisq
     - 4
     - ranked
     - expb_pow
     - 0.451
     - 1.05
     - -0.329
     - 0.432
     - 0.97
     - 
   * - PANGAEA
     - a_dg
     - 443
     - chisq
     - 5
     - ranked
     - giop
     - 0.439
     - 2.23
     - -0.647
     - 0.266
     - 0.243
     - 
   * - PANGAEA
     - a_dg
     - 443
     - chisq
     - 6
     - ranked
     - giop
     - 0.405
     - 2.14
     - -0.634
     - 0.526
     - 0.373
     - 
   * - PANGAEA
     - a_ph
     - 440
     - chisq
     - 1
     - ranked
     - expb_pow
     - 0.616
     - 0.932
     - -0.126
     - 0.432
     - 0.941
     - 
   * - PANGAEA
     - a_ph
     - 440
     - chisq
     - 2
     - ranked
     - giop
     - 0.578
     - 0.579
     - 0.242
     - 0.266
     - 0.346
     - 
   * - PANGAEA
     - a_ph
     - 440
     - chisq
     - 3
     - ranked
     - giop
     - 0.519
     - 1.1
     - -0.159
     - 0.526
     - 0.479
     - 
   * - PANGAEA
     - a_ph
     - 440
     - chisq
     - 4
     - ranked
     - expb_pow
     - 0.507
     - 1.03
     - -0.167
     - 0.195
     - 0.882
     - 
   * - PANGAEA
     - a_ph
     - 440
     - chisq
     - 5
     - ranked
     - gsm
     - 0.362
     - 1.21
     - -0.338
     - 0.376
     - 0.52
     - 
   * - PANGAEA
     - a_ph
     - 440
     - chisq
     - 6
     - ranked
     - gsm
     - 0.253
     - 1.06
     - -0.453
     - 0.0339
     - 0.347
     - 
   * - PANGAEA
     - a_ph
     - 443
     - chisq
     - 1
     - ranked
     - expb_pow
     - 0.616
     - 0.932
     - -0.126
     - 0.432
     - 0.941
     - 
   * - PANGAEA
     - a_ph
     - 443
     - chisq
     - 2
     - ranked
     - giop
     - 0.578
     - 0.579
     - 0.242
     - 0.266
     - 0.346
     - 
   * - PANGAEA
     - a_ph
     - 443
     - chisq
     - 3
     - ranked
     - giop
     - 0.519
     - 1.1
     - -0.159
     - 0.526
     - 0.479
     - 
   * - PANGAEA
     - a_ph
     - 443
     - chisq
     - 4
     - ranked
     - expb_pow
     - 0.507
     - 1.03
     - -0.167
     - 0.195
     - 0.882
     - 
   * - PANGAEA
     - a_ph
     - 443
     - chisq
     - 5
     - ranked
     - gsm
     - 0.362
     - 1.21
     - -0.338
     - 0.376
     - 0.52
     - 
   * - PANGAEA
     - a_ph
     - 443
     - chisq
     - 6
     - ranked
     - gsm
     - 0.253
     - 1.06
     - -0.453
     - 0.0339
     - 0.347
     - 
   * - PANGAEA
     - bb_p
     - 555
     - chisq
     - 1
     - ranked
     - giop
     - 0.757
     - 0.449
     - 0.333
     - 0.266
     - 0.131
     - 
   * - PANGAEA
     - bb_p
     - 555
     - chisq
     - 2
     - ranked
     - gsm
     - 0.741
     - 0.458
     - -0.0108
     - 0.376
     - 0.509
     - 
   * - PANGAEA
     - bb_p
     - 555
     - chisq
     - 3
     - ranked
     - gsm
     - 0.692
     - 0.354
     - -0.0279
     - 0.0339
     - 0.286
     - 
   * - PANGAEA
     - bb_p
     - 555
     - chisq
     - 4
     - ranked
     - giop
     - 0.527
     - 0.88
     - 0.408
     - 0.526
     - 0.137
     - 
   * - PANGAEA
     - bb_p
     - 555
     - chisq
     - 5
     - ranked
     - expb_pow
     - 0.262
     - 1.39
     - 1.06
     - 0.432
     - 0.638
     - 
   * - PANGAEA
     - bb_p
     - 555
     - chisq
     - 6
     - ranked
     - expb_pow
     - 0.216
     - 0.778
     - 0.708
     - 0.195
     - 0.578
     - 
   * - PANGAEA
     - bb_p
     - 670
     - chisq
     - 1
     - ranked
     - giop
     - 0.952
     - 1.13
     - 1.13
     - 0.266
     - 0.0435
     - 
   * - PANGAEA
     - bb_p
     - 670
     - chisq
     - 2
     - ranked
     - gsm
     - 0.766
     - 0.659
     - 0.581
     - 0.376
     - 0.125
     - 
   * - PANGAEA
     - bb_p
     - 670
     - chisq
     - 3
     - ranked
     - giop
     - 0.762
     - 1.24
     - 1.21
     - 0.526
     - 0.0506
     - 
   * - PANGAEA
     - bb_p
     - 670
     - chisq
     - 4
     - ranked
     - expb_pow
     - 0.143
     - 1.54
     - 1.54
     - 0.195
     - 0
     - 
   * - PANGAEA
     - bb_p
     - 670
     - chisq
     - 5
     - ranked
     - expb_pow
     - 0.0762
     - 2.94
     - 2.88
     - 0.432
     - 0.138
     - 
   * - PANGAEA
     - bb_p
     - 670
     - chisq
     - 6
     - ranked
     - gsm
     - 0
     - 0.431
     - 0.431
     - 0.0339
     - 0
     - 

What has been evaluated on what
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A blank cell would be ambiguous, so every pair states its state explicitly — and the profile pages below carry the detail.

.. list-table:: What has been evaluated on what
   :header-rows: 1
   :stub-columns: 1
   :widths: auto

   * - algorithm
     - GLORIA
     - L23
     - PACE
     - PANGAEA
   * - ``expb_pow``
     - scored (n=12)
     - scored (n=6639)
     - not evaluated
     - scored (n=773)
   * - ``expb_pow2``
     - scored (n=12)
     - not evaluated
     - not evaluated
     - not evaluated
   * - ``expb_pow2flat``
     - scored (n=12)
     - not evaluated
     - not evaluated
     - not evaluated
   * - ``expb_powflex``
     - scored (n=12)
     - not evaluated
     - not evaluated
     - not evaluated
   * - ``giop``
     - not evaluated
     - scored (n=6576)
     - not evaluated
     - scored (n=1020)
   * - ``gsm``
     - not evaluated
     - scored (n=3286)
     - not evaluated
     - scored (n=565)


Every contest, stratum and provenance column is on the :doc:`/reports/leaderboard_full` page; the table above is the ``stratum="all"`` headline.

.. raw:: html

   <script src="../_static/bokeh/bokeh-3.9.1.min.js"></script>
   <script src="../_static/bokeh/bokeh-widgets-3.9.1.min.js"></script>
   <script src="../_static/bokeh/bokeh-tables-3.9.1.min.js"></script>
   <div id="b38552cf-b3e4-4640-aa84-9b6300a4d733" data-root-id="p1061" style="display: contents;"></div>
   <script>
   (function() {
     const fn = function() {
       Bokeh.safely(function() {
         (function(root) {
           function embed_document(root) {
           const docs_json = '{"4d5bbd45-8fc0-424e-8729-2bfbd8bf38f4":{"version":"3.9.1","title":"Bokeh Application","config":{"type":"object","name":"DocumentConfig","id":"p1062","attributes":{"notifications":{"type":"object","name":"Notifications","id":"p1063"}}},"roots":[{"type":"object","name":"Column","id":"p1061","attributes":{"children":[{"type":"object","name":"Select","id":"p1057","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"type":"object","name":"CustomJS","id":"p1060","attributes":{"args":{"type":"map","entries":[["full",{"type":"object","name":"ColumnDataSource","id":"p1006","attributes":{"selected":{"type":"object","name":"Selection","id":"p1007","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1008"},"data":{"type":"map","entries":[["rank",[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,null,3,null,null,null,7,1,2,1,2,3,4,5,null,1,null,3,null,null,null,7,1,2,null,2,null,4,null,null,7,1,2,1,null,null,4,null,null,7,1,2,1,2,3,4,5,null,1,null,null,4,null,null,7,1,2,null,2,null,4,null,null,7,1,2,1,null,null,null,null,null,7,1,2,1,2,3,4,5,null,1,null,null,null,null,null,7,1,2,1,null,null,null,null,null,7,1,2,null,2,null,null,null,6,null,1,2,1,2,3,4,5,null,1,null,null,null,null,null,7,1,2,1,null,null,null,null,null,7,1,2,1,2,null,4,5,null,7,1,2,1,null,null,4,5,null,1,2,3,null,null,6,7,1,2,1,2,3,4,5,6,7,1,2,1,2,null,4,5,null,7,1,2,1,2,null,null,5,null,1,2,null,4,5,null,7,1,2,1,2,3,4,5,6,7,1,2,null,null,null,null,null,null,null,1,2,1,null,3,null,5,null,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,1,2,1,null,3,null,5,null,null,null,null,null,null,null,null,1,2,1,null,3,null,null,null,7,1,2,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6,1,null,3,null,null,6,1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6,1,null,3,null,null,6,1,2,3,4,5,6,1,2,3,4,5,6,null,null,null,null,null,null,1,2,3,4,5,6,1,2,3,4,5,6,null,null,null,null,null,null,1,2,3,4,5,6,null,null,null,null,null,null,1,2,3,4,5,6,1,2,3,4,5,6,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,4,5,6,1,2,3,4,5,null,1,2,3,4,5,6,1,null,null,4,5,null,1,2,3,4,5,null,1,2,3,4,5,6,null,2,3,4,null,1,2,3,4,5,null,null,null,null,null,null,null,1,2,3,4,5,null]],["ranking",["not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","indistinguishable","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","indistinguishable","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","ranked","indistinguishable","ranked","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","indistinguishable","ranked","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","indistinguishable","indistinguishable","ranked","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","ranked","indistinguishable","ranked","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","indistinguishable","ranked","ranked","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","indistinguishable","ranked","ranked","sole competitor","ranked","ranked","ranked","indistinguishable","indistinguishable","ranked","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","indistinguishable","ranked","ranked","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","indistinguishable","ranked","ranked","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","ranked","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","ranked","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","not scored","ranked","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","ranked","ranked","indistinguishable","ranked","ranked","ranked","ranked","ranked","not scored","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","ranked","ranked","ranked","indistinguishable","ranked","ranked","ranked","ranked","ranked","not scored","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","not scored"]],["dataset",["GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA"]],["component",["a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p"]],["ref_wave",[440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0]],["stratum",["all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","unknown","unknown","unknown"]],["fit_method",["chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq"]],["algorithm",["expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow2","expb_powflex","expb_pow","expb_pow2flat","expb_powflex","expb_pow2","expb_pow","expb_pow2flat","expb_pow2","expb_powflex","expb_pow","expb_pow2flat","expb_pow2","expb_pow","expb_pow2flat","expb_powflex","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_pow","gsm","expb_pow","giop","giop","giop","expb_pow","expb_pow","giop","giop","expb_pow","expb_pow","gsm","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","giop","expb_pow","expb_pow","giop","giop","expb_pow","expb_pow","gsm","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","giop","expb_pow","expb_pow","giop","giop","gsm","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","giop","giop","gsm","expb_pow","expb_pow","expb_pow","giop","giop","gsm","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","giop","gsm","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","giop","giop","gsm","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","giop","giop","gsm","expb_pow","expb_pow","expb_pow","giop","giop","gsm","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","giop","giop","gsm","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","expb_pow","giop","expb_pow","giop","gsm","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","giop","gsm","expb_pow","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","expb_pow","giop","giop","expb_pow","gsm","expb_pow","gsm","expb_pow","expb_pow","giop","expb_pow","giop","giop","expb_pow","expb_pow","giop","gsm","expb_pow","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","giop","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","giop","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","giop","expb_pow","expb_pow","expb_pow","giop","expb_pow","giop","gsm","expb_pow","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","giop","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","giop","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","giop","expb_pow","expb_pow","expb_pow","giop","expb_pow","giop","gsm","expb_pow","giop","expb_pow","expb_pow","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","gsm","gsm","expb_pow","expb_pow","giop","giop","expb_pow","gsm","expb_pow","gsm","giop","giop","gsm","gsm","giop","giop","expb_pow","expb_pow","gsm","giop","giop","expb_pow","gsm","expb_pow","gsm","gsm","giop","expb_pow","giop","expb_pow","gsm","gsm","expb_pow","expb_pow","giop","giop","expb_pow","gsm","expb_pow","gsm","giop","giop","gsm","gsm","giop","giop","expb_pow","expb_pow","gsm","giop","giop","expb_pow","gsm","expb_pow","gsm","gsm","giop","expb_pow","giop","expb_pow","expb_pow","giop","giop","expb_pow","gsm","gsm","giop","gsm","giop","expb_pow","expb_pow","gsm","expb_pow","expb_pow","giop","giop","gsm","gsm","expb_pow","expb_pow","giop","giop","gsm","gsm","expb_pow","expb_pow","giop","gsm","giop","gsm","expb_pow","giop","giop","expb_pow","gsm","gsm","giop","gsm","giop","expb_pow","expb_pow","gsm","expb_pow","expb_pow","giop","giop","gsm","gsm","expb_pow","expb_pow","giop","giop","gsm","gsm","expb_pow","expb_pow","giop","gsm","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","giop","gsm","gsm","giop","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","gsm","giop","gsm","gsm","giop","expb_pow","expb_pow","gsm","gsm","expb_pow","expb_pow","giop","giop","giop","gsm","giop","expb_pow","expb_pow","gsm","giop","gsm","giop","expb_pow","expb_pow","gsm","giop","giop","gsm","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","gsm","gsm","gsm","giop","giop","expb_pow","expb_pow","gsm"]],["win_frac",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6388888888888888,0.5694444444444444,0.4305555555555556,0.3611111111111111,0.6666666666666666,0.6,0.4,0.3333333333333333,0.6666666666666666,0.625,0.375,0.3333333333333333,0.6666666666666666,0.5555555555555556,0.4444444444444444,0.3333333333333333,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8464465073809162,0.7,0.5777574091047968,0.5753592173647203,0.4246407826352797,0.3,0.0744079449961803,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8433333333333334,0.7204968944099379,0.4096774193548387,0.2795031055900621,0.2413793103448276,{"type":"number","value":"nan"},0.8846463022508039,0.6153846153846154,0.5703077851538926,0.5545308740978349,0.4454691259021652,0.38461538461538464,0.04465902232951117,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8571428571428571,0.8038910505836576,0.737012987012987,0.6824902723735409,0.262987012987013,0.14285714285714285,0.009419152276295133,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8735352305585147,0.7,0.5851421583613574,0.5345249007027192,0.41485784163864264,0.3,0.09045072574484339,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8366666666666667,0.7204968944099379,0.4645161290322581,0.2795031055900621,0.1896551724137931,{"type":"number","value":"nan"},0.9115755627009646,0.6153846153846154,0.5589414595028067,0.5216254274793805,0.4410585404971933,0.38461538461538464,0.0663850331925166,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8571428571428571,0.8249027237354085,0.7711038961038961,0.6622568093385214,0.2288961038961039,0.14285714285714285,0.008634222919937205,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6939773769489452,0.65,0.5855484265200123,0.5242169595110772,0.3906559123421093,0.35,0.3060226230510547,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7266666666666667,0.6459627329192547,0.4241379310344828,0.35403726708074534,0.35161290322580646,{"type":"number","value":"nan"},0.694065757818765,0.6923076923076923,0.5888151277408972,0.5145845906256287,0.3967041800643087,0.3076923076923077,0.30593424218123494,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7061688311688312,0.6093385214007782,0.5714285714285714,0.5141287284144427,0.42857142857142855,0.37665369649805447,0.29383116883116883,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7,0.6982574136349741,0.6144210204705164,0.5072574484339191,0.3787855729721504,0.301742586365026,0.3,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6933333333333334,0.6273291925465838,0.4793103448275862,0.37267080745341613,0.33225806451612905,{"type":"number","value":"nan"},0.6980753809141941,0.6923076923076923,0.619995976664655,0.4948702474351237,0.3852491961414791,0.3076923076923077,0.3019246190858059,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7175324675324676,0.7142857142857143,0.6233463035019455,0.5117739403453689,0.3649805447470817,0.2857142857142857,0.2824675324675325,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7254812098991751,0.6166489118855577,0.6,0.5453989605625191,0.45460103943748087,0.4,0.1573720397249809,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.5806451612903226,0.515527950310559,0.484472049689441,0.46,0.45517241379310347,{"type":"number","value":"nan"},0.7332528666264333,0.6229903536977492,0.5469125902165196,0.5384615384615384,0.46153846153846156,0.45308740978348033,0.1436330718165359,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8571428571428571,0.756420233463035,0.6007782101167315,0.547077922077922,0.45292207792207795,0.14285714285714285,0.13971742543171115,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.681790406355026,0.6752396895449704,0.6,0.5157444206664629,0.48425557933353713,0.4,0.14224598930481283,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.667741935483871,0.62,0.5031055900621118,0.4968944099378882,0.19655172413793104,{"type":"number","value":"nan"},0.6908066787366727,0.6858922829581994,0.5384615384615384,0.5192461908580593,0.48075380914194066,0.46153846153846156,0.12311406155703078,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8571428571428571,0.756420233463035,0.6357976653696498,0.5048701298701299,0.49512987012987014,0.14285714285714285,0.1043956043956044,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6860447420483945,0.5821875954781546,0.55,0.5035157444206665,0.4964842555793335,0.45,0.23101604278074866,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7689655172413793,0.7204968944099379,0.5933333333333334,0.2795031055900621,0.15806451612903225,{"type":"number","value":"nan"},0.7134244372990354,0.5384615384615384,0.5340817963111467,0.5312814323073828,0.4659182036888532,0.46153846153846156,0.25507946087306377,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7369649805447471,0.7142857142857143,0.7073929961089495,0.599025974025974,0.400974025974026,0.2857142857142857,0.05180533751962323,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.75,0.7282176704371752,0.5375802016498625,0.4961193121290519,0.4663101604278075,0.27178232956282483,0.25,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.896551724137931,0.6086956521739131,0.47,0.391304347826087,0.15806451612903225,{"type":"number","value":"nan"},0.7846832397754611,0.6923076923076923,0.5616961414790996,0.5538121102393885,0.38442969221484613,0.3076923076923077,0.21531676022453888,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8571428571428571,0.7849293563579278,0.5308441558441559,0.46915584415584416,0.39377431906614785,0.3237354085603113,0.14285714285714285,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6839141683153249,0.576993583868011,0.55,0.5019871598899419,0.4980128401100581,0.45,0.23834988540870894,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7689655172413793,0.7204968944099379,0.5933333333333334,0.2795031055900621,0.15806451612903225,{"type":"number","value":"nan"},0.7108118971061094,0.5384615384615384,0.5360866078588613,0.5250452625226313,0.46391339214113875,0.46153846153846156,0.263930798632066,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7346303501945526,0.7142857142857143,0.7066147859922179,0.599025974025974,0.400974025974026,0.2857142857142857,0.054945054945054944,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.75,0.7361663099969429,0.5374274366025054,0.4968802313194339,0.46569900687547744,0.2638336900030572,0.25,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8931034482758621,0.6086956521739131,0.47333333333333333,0.391304347826087,0.15806451612903225,{"type":"number","value":"nan"},0.7919005613472334,0.6923076923076923,0.5622990353697749,0.5538121102393885,0.38382619191309597,0.3076923076923077,0.20809943865276664,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8571428571428571,0.783359497645212,0.5438311688311688,0.45616883116883117,0.39377431906614785,0.32529182879377433,0.14285714285714285,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7283950617283951,0.6558363417569194,0.4831932773109244,0.4509132420091324,0.4388185654008439,0.4046306504961411,0.7926829268292683,0.7165354330708661,0.5784313725490197,0.5,0.2484076433121019,0.2073170731707317,0.7258064516129032,0.6410256410256411,0.5819672131147541,0.48132780082987553,0.3771551724137931,0.30327868852459017,0.7,0.6923076923076923,0.6,0.4166666666666667,0.38461538461538464,0.2,0.8571428571428571,0.6385542168674698,0.4588235294117647,0.4583333333333333,0.43478260869565216,0.4024390243902439,0.7283950617283951,0.6558363417569194,0.4831932773109244,0.4509132420091324,0.4388185654008439,0.4046306504961411,0.7926829268292683,0.7165354330708661,0.5784313725490197,0.5,0.2484076433121019,0.2073170731707317,0.7258064516129032,0.6410256410256411,0.5819672131147541,0.48132780082987553,0.3771551724137931,0.30327868852459017,0.7,0.6923076923076923,0.6,0.4166666666666667,0.38461538461538464,0.2,0.8571428571428571,0.6385542168674698,0.4588235294117647,0.4583333333333333,0.43478260869565216,0.4024390243902439,0.6155419222903885,0.5781818181818181,0.5187680461982676,0.5072992700729927,0.3624091381100727,0.25263157894736843,0.6595744680851063,0.5503597122302158,0.5162241887905604,0.44108761329305135,0.35106382978723405,0.25,0.7042801556420234,0.5652173913043478,0.5579710144927537,0.5302752293577981,0.2711864406779661,0.2638888888888889,0.8181818181818182,0.7741935483870968,0.6153846153846154,0.46808510638297873,0.3541666666666667,0.08333333333333333,0.6862745098039216,0.6129032258064516,0.49074074074074076,0.42857142857142855,0.4,0.330188679245283,0.6155419222903885,0.5781818181818181,0.5187680461982676,0.5072992700729927,0.3624091381100727,0.25263157894736843,0.6595744680851063,0.5503597122302158,0.5162241887905604,0.44108761329305135,0.35106382978723405,0.25,0.7042801556420234,0.5652173913043478,0.5579710144927537,0.5302752293577981,0.2711864406779661,0.2638888888888889,0.8181818181818182,0.7741935483870968,0.6153846153846154,0.46808510638297873,0.3541666666666667,0.08333333333333333,0.6862745098039216,0.6129032258064516,0.49074074074074076,0.42857142857142855,0.4,0.330188679245283,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7572815533980582,0.7414330218068536,0.6923076923076923,0.526595744680851,0.2615803814713896,0.21568627450980393,0.8478260869565217,0.7622950819672131,0.5827338129496403,0.18705035971223022,0.15217391304347827,{"type":"number","value":"nan"},0.7105263157894737,0.7019867549668874,0.5555555555555556,0.4779874213836478,0.32,0.2702702702702703,1.0,1.0,0.6,0.5,0.0,0.0,0.8571428571428571,0.7631578947368421,0.6029411764705882,0.25,0.14285714285714285,{"type":"number","value":"nan"},0.9523809523809523,0.765625,0.7619047619047619,0.14285714285714285,0.0761904761904762,0.0,1.0,0.8235294117647058,0.6,0.11764705882352941,0.0,1.0,0.9666666666666667,0.6,0.0,0.0,{"type":"number","value":"nan"},1.0,1.0,0.5,0.4,0.0,0.0,1.0,0.8571428571428571,0.813953488372093,0.14285714285714285,0.023255813953488372,{"type":"number","value":"nan"}]],["bias",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.19394492888049908,0.09886371818849926,0.288862042419904,0.3005822645880072,0.1804630035332635,0.32654522895203475,0.5189438542698914,0.5233745334396707,-0.10845006689893011,-0.11579312979635004,-0.11581554902506785,-0.10984403824118738,0.47867540345539616,0.620064735722645,0.6567310742953156,0.3030153227405923,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.02266567142585174,0.005180993911545473,0.09129407359552766,0.0411265791157569,0.09012714756461837,0.0692786104387304,0.18318792890917734,0.01784794066608586,-0.03184215087854214,0.27639945265432764,0.33531680250651674,0.4811265174267405,0.5347960988073202,0.5278661405921801,0.45809991444061415,0.002071540820445472,-0.020884628999368382,0.08689952383583033,0.019131237907968446,0.08237625640267687,0.06864464474726195,0.19053845225259436,-0.00036726408807419286,-0.05740987756608518,0.055443551243207434,0.0024297735759313266,0.026437190518024734,0.02527560574823151,0.06413238699843338,0.07045697326796385,0.1331210189399581,-0.002085131007105945,-0.005580900428750368,0.022879549123382192,0.007968858826222558,0.04008664873655876,0.10696067719753533,0.08710989715358819,0.0698744564780649,0.17894864267848343,0.017470073175136047,-0.02569045807804904,0.24877784150695614,0.3067735715313853,0.45160989772157323,0.4974925180396377,0.5760621385162512,0.42431737025852057,0.003151332270580731,-0.01776992602128158,0.019224667006860763,0.10354729505842686,0.07977897711464066,0.0679511021084438,0.18680570315777234,7.799416540388293e-05,-0.053351214738347585,0.05757225516999953,0.00470401514941865,0.027119982922795494,0.03219825733120274,0.06483154109237521,0.07345559501493626,0.13227170734122673,0.00012904506587729792,0.0027785365168797593,-0.02824372122163399,-0.05046092020190751,0.0759318402071556,-0.022966016215410057,0.02963104249708781,-0.004749392020864995,0.05195327083972345,0.12939816755683875,0.1624613194200335,-0.10310515507279716,-0.03289047062386097,0.4577776297219174,0.4145639968106827,0.38631682825277447,0.14700625970521353,-0.02941892783032707,-0.058969307766015944,0.0688480469911319,-0.018390191738186235,0.023695388538180095,-0.014291504469593486,0.04499650354959228,0.13274820883495209,0.18093385155404507,-0.02224694945943584,0.028645159278585464,-0.034455004281410795,-0.019788654843712394,0.013217420235868804,-0.02711715620410582,0.002613386980742982,0.11230809319218915,0.1442777403404143,-0.07273103516274504,-0.05066185095354836,0.03761375520768495,-0.04544919140118875,0.017970981515703865,0.03970046106176994,-0.017119016933146214,0.12554850766601944,0.15686232067411865,-0.12574079438061037,-0.057576461098000076,0.40327386116781705,0.38451931253061233,0.36498286223769627,0.12864952428436105,-0.05184596148016474,-0.07938292380874967,0.030702800843453115,-0.04102723455280599,0.013520197796915268,-0.022638508730816964,0.03405752060759104,0.1296896388835156,0.18126853817276967,-0.04402783546280076,-0.060249750409343106,-0.007272152008664268,-0.041606508545695364,-0.042257797821531384,-0.006785701667962329,-0.01121275173853209,0.10898678145339002,0.13296036061849814,0.1946277789564208,-0.12130701221827689,0.3051960813391781,0.2636709643268458,-0.34508716515875826,-0.3844621696390337,0.5935313956678809,-0.4807259341008219,-0.6125205400077165,0.46152981275955574,0.14213453540765353,0.3375709852391371,0.634970270727115,0.6873938313507193,-0.11896127182826155,0.1926145075231882,-0.16420317013778074,0.26196816675836465,-0.5450860110382908,0.28810004466814454,-0.4077352288091698,0.589582947179788,-0.5057453450042434,-0.8054257003439286,0.33755013444548987,0.11000937280371215,-0.06915686716359792,0.30461748041214287,-0.19227688979156143,0.07930672904304403,0.5987053219719771,-0.22836504008340808,-0.4492879756926208,0.29593307653922896,-0.10473882302481219,0.3462132569006531,0.28987605131743854,-0.3287801944959503,-0.3615427272791508,0.6255106879321721,-0.46535450093166997,-0.5882944028801769,0.42730369396763446,0.592720034597237,0.11545391285245166,0.3087769890492891,0.8494943847864687,-0.13079866680567342,0.2947374767626463,-0.14858512783156008,-0.5293670147292769,0.286566255652164,-0.3925549828707864,0.31686071887789624,0.6193624129053217,-0.4912650922916436,-0.7938282399468781,0.4024719551651448,0.19774568627916178,-0.04026441954047466,0.3538068413488116,-0.16487219879107773,0.1248883963321501,0.6582153357902727,-0.1778626779141982,-0.42628526045012916,-0.001004627587986917,-0.02152669320545819,-0.015078667274009638,-0.022328329406208547,0.007993996252034341,0.0021479991830903877,0.06051217397711306,0.0036801007901456906,0.007433917999180251,0.036727142922037714,0.08160670791638802,0.057342613479907545,0.17602410058430973,0.15875084692370023,0.15374472800945727,-0.015911725756809325,-0.006613763414296425,-0.0071292708068845245,-0.0300139958802651,-0.03614662492364196,-0.024790606859999897,0.05726479706517473,0.0010482159254798784,-0.00739483199942248,-0.0016977737182239938,0.0032151246004301637,0.01766039228700822,0.008682903378073092,0.028252796544524506,0.018625388010305555,0.07409887558170802,0.0063189052195542494,0.0312887749541062,0.021756864502924467,0.02561278785544574,0.010753138601125922,0.02386538163403773,-0.004873481515720202,-0.09576901597920506,-0.09006766815705458,0.03749474255998009,0.0553501076683216,0.017031567035251882,0.12507862788637025,0.08548912429922595,0.1145288141584353,0.1081870449014315,0.12335565579923746,0.014297587284121116,0.042251145432925075,0.012039829429049798,0.0010985786213577597,-0.017785838389446695,-0.10285648347778475,-0.11840845068747241,0.021961683929327513,0.07590156782735291,-0.015240799837705432,0.02459263566228298,0.046035737780673935,-0.051300630686292426,0.04719269447242236,0.04844508647387791,-0.06583137575269804,0.03519121363922095,0.07802999484520723,0.0036462855660914784,-0.031922943694958406,-0.02211530519918614,-0.03883198483574779,0.018352012573667142,0.02205560725880429,0.13171053464156923,0.018890801046546057,0.021670350974372532,0.04018861842111354,0.09057666225673677,0.06890685911199501,0.20191053114386692,0.18032793556540017,0.17832107476458225,-0.023310011025589383,0.006001416919308333,-0.010932464278539222,-0.048249809312583714,-0.06506674006278723,-0.03836754899624939,0.11582132678518775,-0.010660949210975934,0.03181688198977506,0.016364439346610915,0.008799676946568136,0.06761400040785714,0.040211958314995355,0.09346899521123908,0.05255334247170218,0.21324309213152204,0.0116235974422072,0.10067119864967133,0.04145880705148941,0.04774043388194227,0.0313116962626796,0.04906418974583926,0.003264084710685511,-0.14714467088026617,-0.14177616306519447,0.07063016745079054,0.1118149913434201,0.017580629800867387,0.13884573620165197,0.0965505623668439,0.12467433390963567,0.12059724808995864,0.13712995599621425,0.026997111243493688,0.07679398201969101,0.02713595958171533,0.011240457706096274,-0.018855212667296617,-0.1519295111489971,-0.17721951738193165,0.04058755892423571,0.16057058597507523,-0.02111623423965514,0.07036804165801369,0.10839542391182233,-0.0825191196895586,0.11560269104090626,0.11820473147104615,-0.12259633941004644,0.06510762026370776,0.17687485555621918,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},-0.17531152419022256,-0.09911008003473842,-0.1624748200098547,-0.3287546093478896,-0.646848157817382,-0.6338449803440545,-0.15294824843510058,0.09838068593858185,-0.4897228528378914,0.2087340238734765,-0.8653464894422308,-0.8526082600585422,-0.14304861373480604,-0.17815918974700007,-0.2152489071762308,-0.24616029670763162,-0.1961276267100336,-0.16819196991429564,-0.44847025712769617,-0.43294481936329277,-0.4004264565055373,-0.49105035234190597,-0.4454998550171261,-0.4944561895141041,-0.088302264468334,-0.03963875986579357,-0.47909114078651216,-0.06805829356204118,-0.5027116575279458,-0.1381589799827615,-0.17531152419022256,-0.09911008003473842,-0.1624748200098547,-0.3287546093478896,-0.646848157817382,-0.6338449803440545,-0.15294824843510058,0.09838068593858185,-0.4897228528378914,0.2087340238734765,-0.8653464894422308,-0.8526082600585422,-0.14304861373480604,-0.17815918974700007,-0.2152489071762308,-0.24616029670763162,-0.1961276267100336,-0.16819196991429564,-0.44847025712769617,-0.43294481936329277,-0.4004264565055373,-0.49105035234190597,-0.4454998550171261,-0.4944561895141041,-0.088302264468334,-0.03963875986579357,-0.47909114078651216,-0.06805829356204118,-0.5027116575279458,-0.1381589799827615,-0.1256933946151948,0.24161566898788278,-0.1587023121477017,-0.16661366698818436,-0.3383639244463661,-0.45272225500639984,0.5264977291112234,0.014563830248398801,0.34876144342494797,0.3057384181787135,0.028895694662704585,-0.16562634575467783,-0.28310121140065203,-0.2989386350871214,0.05928914320582934,-0.2990185308653843,-0.4239352208726491,-0.27215712583611307,-0.2065228886770406,-0.4169439168032887,0.2184859927499414,-0.2790535488014093,-0.2522435056224833,-0.40039904971335327,-0.40406268949223234,-0.18958789721752145,-0.60861463677343,-0.9729722500435539,0.07054216822246318,-0.592253751465599,-0.1256933946151948,0.24161566898788278,-0.1587023121477017,-0.16661366698818436,-0.3383639244463661,-0.45272225500639984,0.5264977291112234,0.014563830248398801,0.34876144342494797,0.3057384181787135,0.028895694662704585,-0.16562634575467783,-0.28310121140065203,-0.2989386350871214,0.05928914320582934,-0.2990185308653843,-0.4239352208726491,-0.27215712583611307,-0.2065228886770406,-0.4169439168032887,0.2184859927499414,-0.2790535488014093,-0.2522435056224833,-0.40039904971335327,-0.40406268949223234,-0.18958789721752145,-0.60861463677343,-0.9729722500435539,0.07054216822246318,-0.592253751465599,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.3334146471667454,-0.010771264403590441,-0.027940911331577167,0.4084459522242334,1.0553032844487866,0.7075293902124413,0.24281024136687446,0.06397338392654905,0.4922411994854037,0.9372511558246188,0.5541243963144635,{"type":"number","value":"nan"},0.25226400641375935,-0.04958427355366657,-0.18297892414371852,0.1640126153334598,0.34271686871107865,0.5359987734908522,0.46280094140286665,0.5008634413712496,0.8178294171208307,0.672197771043227,0.7135608412417429,0.8571859124819834,0.8802844767156273,-0.16397485020607028,0.7765798442018081,2.9721541444687305,1.4958279728530184,{"type":"number","value":"nan"},1.1294644085393197,0.5810777994397205,1.20501872519992,1.53992359392684,2.882066022360361,0.4306942757208201,0.1682473869783263,1.1532425140244427,-0.07491525939791088,3.3478613219584554,1.9145519150866819,1.276582724929321,0.8352938764229918,1.1712011361349277,1.3073395884134258,1.4082682969814568,{"type":"number","value":"nan"},0.4149830993182593,0.4606319964604759,0.4314058080608809,0.4808878791069082,0.4306942757208201,0.5003651987677549,0.7487113888604167,1.3965186169084483,1.379306014880651,1.8352764116491467,4.275482912744457,{"type":"number","value":"nan"}]],["mae",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},1.0075849512908923,1.0595904781624736,1.0015542193310938,1.0025673704840696,1.0006914750576792,0.9854606870494542,0.9584605680433718,0.9452019903717741,1.390206696853852,1.4101706771094538,1.4102342899173532,1.3939579156540054,0.6206141532256673,0.620064735722645,0.6567310742953156,0.7529097937472238,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.054769080538987325,0.06235482839114259,0.09584660172393078,0.09871241867612568,0.09575374905206946,0.07253578717339071,0.18319324845823037,0.06812803815758861,0.04198654715433081,0.27639945265432764,0.33762530560125725,0.4823445556448247,0.5410672352517423,0.5278661405921801,0.45809991444061415,0.03805722809866263,0.06409289816851427,0.09019668900604239,0.08646775239816296,0.08862349546615267,0.07365682015058939,0.19053845225259436,0.054954074970261946,0.06090651302163441,0.05913451286204685,0.02478984036052756,0.05467000586431481,0.035042285033667575,0.06795359161996872,0.07045697326796385,0.13314729119692714,0.03703437921860009,0.023403995662399923,0.05275200541259317,0.059502198578262666,0.09492478712146557,0.1099886861576207,0.09268707950958133,0.07188497539522998,0.17895651029667037,0.06548887222982147,0.041658267198884325,0.24877784150695614,0.3102072064532664,0.4534368903702719,0.5051131156230468,0.5760621385162512,0.4243602218292317,0.03696074338657329,0.05916091044378868,0.08368499401694374,0.10566216342851154,0.08602735092872815,0.07104020920453613,0.18680570315777234,0.05331721004602108,0.05635798151222615,0.06013631118760365,0.024281869950421475,0.052701963459945045,0.03893072862457281,0.06816487120251424,0.07345559501493626,0.13231067470356406,0.036186130735147426,0.02716310627054619,0.18988702245481504,0.12561439287669107,0.1555926808567767,0.165966669788558,0.22238712612003209,0.18445629890662318,0.31993981233603863,0.2741273377164275,0.24555748601487148,0.28340752712942274,0.5555642712228259,0.4604306145001922,0.8256958359062241,0.6040586567858957,1.2120815005963048,0.1805093804006832,0.13370900963132848,0.14566395163256995,0.16321222210892028,0.20416221994645678,0.18443198025007934,0.30965110329660095,0.251668656781457,0.3449583616516485,0.14551330641317595,0.13150719185425896,0.11073455423759548,0.14876029739842744,0.1845014634506228,0.2050449898487543,0.2549842783486125,0.18966090392160906,0.15350295979609752,0.13656803192080447,0.20035260703745505,0.15315823880656176,0.17679597278602532,0.23524830552396936,0.33790258844932897,0.20137099101847045,0.28044987214812034,0.25279678524532767,0.30082539333743963,0.5644213265738678,0.4089867983733029,0.8172983917712555,0.6003631717683005,1.1958927091476417,0.19081983646856693,0.1434295166624402,0.14333531935400923,0.17370922941963984,0.2167632241405837,0.19810589459375394,0.32809012557956163,0.2585967305215826,0.3626589224601442,0.1568047151707559,0.12393432529797166,0.13765534577315153,0.15937959641722133,0.22212378387578213,0.20745836707989618,0.2755237113355984,0.1965938858667169,0.15179210237544494,0.27819114162769676,0.4194828735134113,0.32541320674817587,0.369326117401916,1.0736096370231119,1.1705928154767133,0.5991490163318072,1.2515209983888917,1.636576723552225,0.5178494616024001,1.2913936900860148,0.8782182229068549,0.6636317050017955,0.6874844941192546,1.4529088253732216,0.26811157756016724,0.4137078384089772,0.3261096633613154,1.6191208158938823,0.3189236180479136,1.155472548819776,0.5924173341564358,1.2902328151783533,4.364048834824655,0.33755013444548987,0.23557885101631681,0.41652226858185104,0.3628747679390958,0.8308850205687863,0.5313621221729654,0.6096529542740265,0.2959495771265892,1.064076552811446,0.34291882509361216,0.4017874842692315,0.35461077336893965,0.3864231828730822,1.0377345346615616,1.14935801798591,0.6302632315580203,1.19425382801077,1.4956532088412042,0.4827011325009676,0.6249338659161132,1.262654983437665,0.837071136111299,0.8494943847864687,1.3930743521033926,0.33463114264107907,0.39431781689790735,1.573670763889223,0.3403142739440024,1.1132518576459423,0.32951948993963254,0.6211797141793025,1.2314462528964292,4.073319804169112,0.4024719551651448,0.277013894319311,0.4097674406937195,0.3988461018108429,0.8175425705109849,0.5381477481346351,0.6676029245629505,0.22765470721580927,1.012899453761869,0.03585421782633236,0.03521517492991966,0.03509021841849291,0.052108461395650396,0.05512146130375739,0.03800668532156992,0.061034130521833596,0.03559666386848681,0.04677850120031368,0.05620217535048577,0.1266325650135991,0.06141659318290027,0.21177098533969807,0.17543994609853475,0.1689928110226302,0.029141398160382304,0.04208940126485361,0.04830908606600093,0.036502911239251645,0.050670434175635215,0.03906155962301994,0.05769029266526493,0.05834811978574228,0.03988238941750666,0.025510240074303914,0.027755096371739896,0.027064293807622652,0.03919549537372524,0.045194311820189625,0.03046688766465233,0.07409887558170802,0.013334299145969508,0.044701276650262356,0.0713062955120305,0.08613965328905526,0.03260437458237986,0.03501626501499855,0.03880883771283061,0.12747778182915237,0.10576677941733448,0.06840892976447033,0.0553501076683216,0.035460481580826375,0.13504814826631417,0.08593264189848715,0.14327090098042916,0.1081870449014315,0.1322004600006108,0.08174604237148042,0.07828482419077765,0.026258306377548113,0.028162287984156764,0.035665128861088746,0.11676449918378484,0.1385202929553706,0.05912020675169272,0.07590156782735291,0.05846577257103558,0.039530612943991184,0.09121654709890548,0.07992048044187361,0.04916779913544267,0.05022515774113456,0.08562897056794472,0.03519121363922095,0.08913389750593459,0.0691613275931311,0.0696128166176353,0.07744603943784334,0.10541124682164682,0.10898132624646761,0.08934948997619951,0.13247812287894134,0.09469582763584228,0.08720258497243671,0.06598689604625152,0.1527133303277659,0.0741341860296576,0.25265106957871986,0.20467583677607815,0.19965222078113354,0.05560712317315164,0.09370329496160212,0.09341031763100127,0.06812914038449414,0.10005473994651748,0.07858261752742601,0.1164703617347509,0.07820991930760979,0.14649867241045844,0.07617415731042931,0.07533842815062441,0.08798020041394938,0.11508711918082515,0.1361205257072846,0.08130978161171387,0.21324309213152204,0.030973248565242972,0.13445799829487126,0.1271970543109675,0.14524393310893147,0.06098212888515642,0.06444164008201181,0.06610883430286019,0.20976976159449912,0.18131984934450007,0.11777281239835613,0.1118149913434201,0.03894437240876947,0.15071614952927948,0.09708360043391684,0.15934895595412124,0.12059724808995864,0.14765697855173476,0.13207495593280427,0.1343513485501553,0.04648883340718357,0.04774228561324234,0.05680199564594668,0.18415740365511035,0.2243731798256119,0.09602727061208904,0.16057058597507523,0.1140300028853185,0.09534353280805852,0.19597757809189686,0.16529757444808157,0.11881252699452771,0.12108511751895423,0.17606813284389977,0.06510762026370776,0.19772776985428342,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.43106034044788455,0.45294530181809844,0.7199674602546717,1.0452742206118875,2.226921381913499,2.1419622243205425,0.8947269394642836,0.3921127490319094,1.92891359918652,0.2087340238734765,7.214562231387847,6.10538785115244,0.33751319334378627,0.4269795738066051,0.5144470728908179,0.5363604441772338,0.5737029457829106,0.5455950769955771,1.1807623784630206,1.1345641177753283,1.0153010592225074,1.185519589452627,1.1818086272400548,1.4622943170269007,0.5141911985859402,0.6086878914655116,1.4885085366683781,0.7766093537925074,1.7841859717711208,0.8609760344695654,0.43106034044788455,0.45294530181809844,0.7199674602546717,1.0452742206118875,2.226921381913499,2.1419622243205425,0.8947269394642836,0.3921127490319094,1.92891359918652,0.2087340238734765,7.214562231387847,6.10538785115244,0.33751319334378627,0.4269795738066051,0.5144470728908179,0.5363604441772338,0.5737029457829106,0.5455950769955771,1.1807623784630206,1.1345641177753283,1.0153010592225074,1.185519589452627,1.1818086272400548,1.4622943170269007,0.5141911985859402,0.6086878914655116,1.4885085366683781,0.7766093537925074,1.7841859717711208,0.8609760344695654,0.9322116020275655,0.5793428237145932,1.1013378355977443,1.0314270691920142,1.2147046622034505,1.0561067971980354,0.6690201176329018,0.7733218126112376,0.8589496699721237,0.9139497674636374,1.3447605239992346,0.1985038057133819,0.850388335420263,0.8255088702856528,0.49427059780939464,1.0555387029209715,1.3503029103684763,0.6114758207985114,0.2879075443748258,0.729106837847141,0.71631966495296,1.349043931862154,1.0658631487678911,0.6677758758086316,1.5839593108960224,1.0896116064692234,2.4447804685540526,35.999010336097186,0.5158282595334056,2.044801345603197,0.9322116020275655,0.5793428237145932,1.1013378355977443,1.0314270691920142,1.2147046622034505,1.0561067971980354,0.6690201176329018,0.7733218126112376,0.8589496699721237,0.9139497674636374,1.3447605239992346,0.1985038057133819,0.850388335420263,0.8255088702856528,0.49427059780939464,1.0555387029209715,1.3503029103684763,0.6114758207985114,0.2879075443748258,0.729106837847141,0.71631966495296,1.349043931862154,1.0658631487678911,0.6677758758086316,1.5839593108960224,1.0896116064692234,2.4447804685540526,35.999010336097186,0.5158282595334056,2.044801345603197,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.44899868532119314,0.458071693652625,0.35445744742257057,0.8804904020307422,1.3917154743015412,0.7776135648508153,0.32256920643415565,0.2290694825288453,0.8559070850648327,1.0187614654366475,0.6354549989089653,{"type":"number","value":"nan"},0.4499643127521502,0.5397448774297555,0.2999751187296109,0.657441019047807,0.65229187141732,0.6167579234971567,0.46280094140286665,0.5008634413712496,0.8178294171208307,0.672197771043227,0.7135608412417429,0.8571859124819834,0.8802844767156273,1.0043566105050763,1.430004674550049,4.03781148496168,1.503039412717468,{"type":"number","value":"nan"},1.1338354536365571,0.659463295464614,1.2416548330896138,1.53992359392684,2.9404907783008856,0.4306942757208201,0.1682473869783263,1.3530189129012071,0.2608799642359214,3.7085560323147932,1.9145519150866819,1.2873450313143877,0.8352938764229918,1.1770960455867074,1.312290558771346,1.4082682969814568,{"type":"number","value":"nan"},0.4149830993182593,0.4606319964604759,0.4314058080608809,0.4808878791069082,0.4306942757208201,0.5003651987677549,0.7487113888604167,1.3965186169084483,1.379306014880651,1.8352764116491467,4.275482912744457,{"type":"number","value":"nan"}]],["coverage68",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.5,0.3333333333333333,0.4166666666666667,0.4166666666666667,0.6,0.6,0.6,0.6,0.0,0.0,0.0,0.0,1.0,0.6666666666666666,0.6666666666666666,0.3333333333333333,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.5574068464101787,0.42105263157894735,0.1664637857577602,0.45511613308223475,0.21494182486221677,0.2,0.0006088280060882801,0.6912832929782082,0.875,0.0,0.03184713375796178,0.03488372093023256,0.13836477987421383,0.0,0.06832298136645963,0.6160354552780016,0.5,0.13786173633440515,0.5104427736006684,0.22743682310469315,0.15384615384615385,0.0,0.7306613226452906,0.75,0.2857142857142857,0.4714064914992272,0.325434439178515,0.3148148148148148,0.21103896103896103,0.2857142857142857,0.0031397174254317113,0.6944444444444444,1.0,0.5383217206906998,0.3684210526315789,0.4416195856873823,0.13724893487522824,0.2140232700551133,0.2,0.0006088280060882801,0.6915859564164649,0.75,0.0,0.050955414012738856,0.03488372093023256,0.14465408805031446,0.0,0.10559006211180125,0.5995165189363416,0.5,0.49832915622389307,0.10530546623794212,0.22703569995988768,0.23076923076923078,0.0,0.7282565130260521,0.75,0.14285714285714285,0.437403400309119,0.30173775671406006,0.2916666666666667,0.20292207792207792,0.14285714285714285,0.0031397174254317113,0.6959876543209876,0.75,0.36105166615713846,0.35,0.1938527084601339,0.35555555555555557,0.7577677224736048,1.0,0.9361380145278451,0.6283292978208233,0.375,0.2375,0.5652173913043478,0.02666666666666667,0.7453416149068323,0.37209302325581395,0.4409937888198758,0.3668805132317562,0.38461538461538464,0.19212218649517684,0.35691318327974275,0.7482965931863728,1.0,0.9378757515030061,0.6328657314629259,0.0,0.2840909090909091,0.23919753086419754,0.2857142857142857,0.37990580847723704,1.0,0.8966049382716049,0.9768518518518519,0.6574074074074074,0.75,0.35,0.3369000305716906,0.182288496652465,0.33729071537290717,0.7656108597285067,0.9352300242130751,1.0,0.6419491525423728,0.375,0.19375,0.5217391304347826,0.03333333333333333,0.7453416149068323,0.3953488372093023,0.453416149068323,0.34562951082598237,0.38461538461538464,0.1885048231511254,0.34163987138263663,0.7555110220440882,1.0,0.9366733466933868,0.6472945891783567,0.0,0.2532467532467532,0.2857142857142857,0.19290123456790123,0.3563579277864992,0.9027777777777778,1.0,0.9768518518518519,0.6682098765432098,0.75,0.22276323797930614,0.7752196304150257,0.3,0.28291488058787506,0.9682988072818581,1.0,0.03409436834094368,0.5777845036319612,0.5,0.18023255813953487,0.21656050955414013,0.6855345911949685,0.01875,0.006666666666666667,0.4472049689440994,0.2102090032154341,0.7671232876712328,0.29201764941837144,1.0,0.38461538461538464,0.9807852965747702,0.03014469453376206,0.5695390781563127,0.25,0.14285714285714285,0.32098765432098764,0.964451313755796,0.262987012987013,0.9921011058451816,1.0,0.05337519623233909,0.75,0.6419753086419753,0.18076688983566647,0.7873371705543775,0.3,0.27036129822412736,0.9686126804770873,1.0,0.0243531202435312,0.5898910411622276,0.625,0.21511627906976744,0.01875,0.2484076433121019,0.6981132075471698,0.0,0.4472049689440994,0.16881028938906753,0.7808219178082192,1.0,0.28399518652226236,0.981203007518797,0.38461538461538464,0.022106109324758844,0.5803607214428858,0.25,0.14285714285714285,0.26851851851851855,0.964451313755796,0.22077922077922077,0.9889415481832543,1.0,0.03453689167974882,1.0,0.6620370370370371,0.4301659125188537,0.13055386488131468,0.6,0.4328951391011923,0.812953995157385,0.9,0.029832572298325723,0.625,0.5950363196125908,0.22,0.21739130434782608,0.1125,0.453416149068323,0.19186046511627908,0.32298136645962733,0.4452905811623247,0.9230769230769231,0.87374749498998,0.11495176848874598,0.4294306335204491,0.46153846153846156,0.0317524115755627,0.25,0.6360721442885772,0.1697530864197531,0.8571428571428571,0.4351851851851852,0.5032467532467533,0.6682098765432098,0.8571428571428571,0.0015698587127158557,1.0,0.5046296296296297,0.9,0.7772397094430993,0.2328058429701765,0.22745098039215686,0.1878234398782344,0.15071843472944055,0.2,0.6558716707021792,0.75,0.41333333333333333,0.33540372670807456,0.05625,0.22981366459627328,0.011627906976744186,0.30434782608695654,0.7963927855711422,0.8461538461538461,0.26733466933867733,0.2447749196141479,0.19011254019292603,0.3076923076923077,0.11106655974338413,0.7182364729458918,0.5,1.0,0.2119309262166405,0.8132716049382716,0.2905844155844156,0.14506172839506173,0.13117283950617284,0.0,1.0,0.5030864197530864,0.4301659125188537,0.13055386488131468,0.6,0.4328951391011923,0.812953995157385,0.9,0.029832572298325723,0.5950363196125908,0.625,0.22,0.21739130434782608,0.1125,0.453416149068323,0.19186046511627908,0.32298136645962733,0.4452905811623247,0.9230769230769231,0.87374749498998,0.11495176848874598,0.4294306335204491,0.46153846153846156,0.0317524115755627,0.6360721442885772,0.25,0.1697530864197531,0.8571428571428571,0.4351851851851852,0.5032467532467533,0.6682098765432098,0.8571428571428571,0.0015698587127158557,1.0,0.5046296296296297,0.9,0.7772397094430993,0.2328058429701765,0.22745098039215686,0.1878234398782344,0.15071843472944055,0.2,0.6558716707021792,0.75,0.41333333333333333,0.33540372670807456,0.05625,0.22981366459627328,0.011627906976744186,0.30434782608695654,0.7963927855711422,0.8461538461538461,0.26733466933867733,0.2447749196141479,0.19011254019292603,0.3076923076923077,0.11106655974338413,0.7182364729458918,0.5,1.0,0.2119309262166405,0.8132716049382716,0.2905844155844156,0.14506172839506173,0.13117283950617284,0.0,1.0,0.5030864197530864,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.2619047619047619,0.4133949191685912,0.9339622641509434,0.9701492537313433,0.24295774647887325,0.37316176470588236,0.9058823529411765,0.5338345864661654,0.9542857142857143,0.0,0.34673366834170855,0.225,0.3125,0.38271604938271603,0.2846153846153846,0.4172661870503597,0.9833333333333333,0.9603960396039604,0.0,0.125,0.0,1.0,0.0,1.0,0.25,0.3488372093023256,0.3137254901960784,0.9047619047619048,0.18518518518518517,0.9523809523809523,0.2619047619047619,0.4133949191685912,0.9339622641509434,0.9701492537313433,0.24295774647887325,0.37316176470588236,0.9058823529411765,0.5338345864661654,0.9542857142857143,0.0,0.34673366834170855,0.225,0.3125,0.38271604938271603,0.2846153846153846,0.4172661870503597,0.9833333333333333,0.9603960396039604,0.0,0.125,0.0,1.0,0.0,1.0,0.25,0.3488372093023256,0.3137254901960784,0.9047619047619048,0.18518518518518517,0.9523809523809523,0.9407265774378585,0.3462603878116344,0.47913446676970634,0.8818565400843882,0.5196850393700787,0.3469387755102041,0.23129251700680273,0.5138888888888888,0.3541666666666667,0.882051282051282,0.7872340425531915,1.0,0.9770992366412213,0.9545454545454546,0.4117647058823529,0.5530546623794212,0.4981949458483754,0.32432432432432434,1.0,1.0,0.5217391304347826,0.6764705882352942,0.7272727272727273,0.42857142857142855,0.96,0.8888888888888888,0.4838709677419355,0.0,0.42105263157894735,0.5185185185185185,0.9407265774378585,0.3462603878116344,0.47913446676970634,0.8818565400843882,0.5196850393700787,0.3469387755102041,0.23129251700680273,0.5138888888888888,0.3541666666666667,0.882051282051282,0.7872340425531915,1.0,0.9770992366412213,0.9545454545454546,0.4117647058823529,0.5530546623794212,0.4981949458483754,0.32432432432432434,1.0,1.0,0.5217391304347826,0.6764705882352942,0.7272727272727273,0.42857142857142855,0.96,0.8888888888888888,0.4838709677419355,0.0,0.42105263157894735,0.5185185185185185,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.13114754098360656,0.509090909090909,0.2857142857142857,0.13692946058091288,0.6379310344827587,0.5775862068965517,0.15789473684210525,0.6557377049180327,0.15294117647058825,0.6626506024096386,0.6730769230769231,{"type":"number","value":"nan"},0.1111111111111111,0.425,0.4,0.15463917525773196,0.7195121951219512,0.5526315789473685,0.0,0.0,0.0,0.4,0.0,0.0,0.11764705882352941,0.5263157894736842,0.09259259259259259,0.5161290322580645,0.4782608695652174,{"type":"number","value":"nan"},0.043478260869565216,0.125,0.05063291139240506,0.0,0.13829787234042554,0.0,0.0,0.07142857142857142,0.4,0.11764705882352941,0.0,0.1,0.13333333333333333,0.09090909090909091,0.17391304347826086,0.0,{"type":"number","value":"nan"},0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.02631578947368421,0.0,0.14285714285714285,{"type":"number","value":"nan"}]],["coverage95",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.9166666666666666,0.75,0.75,0.9166666666666666,0.6,1.0,0.6,1.0,0.75,0.75,0.75,0.75,1.0,1.0,1.0,1.0,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.807028173280824,1.0,0.3174071819841753,0.9303201506591338,0.44090630740967546,0.65,0.0024353120243531205,0.927360774818402,1.0,0.0,0.14012738853503184,0.0755813953488372,0.46540880503144655,0.0,0.3105590062111801,0.8585817888799355,1.0,0.2652733118971061,0.956140350877193,0.45166466105094266,0.6923076923076923,0.0012057877813504824,0.9595190380761524,1.0,1.0,0.80370942812983,0.9494470774091627,0.5910493827160493,0.474025974025974,0.5714285714285714,0.007849293563579277,0.9567901234567902,1.0,0.8006664647076643,1.0,0.9290646578782172,0.2681071211199026,0.44243723208818125,0.6,0.0027397260273972603,0.9267554479418886,1.0,0.00625,0.16560509554140126,0.10465116279069768,0.48427672955974843,0.0,0.32919254658385094,0.8561643835616438,1.0,0.9565580618212197,0.21382636655948553,0.4564781387886081,0.6923076923076923,0.0012057877813504824,0.9571142284569139,1.0,1.0,0.7727975270479135,0.9368088467614534,0.5385802469135802,0.45616883116883117,0.42857142857142855,0.007849293563579277,0.9583333333333334,1.0,0.6456741057780495,0.75,0.3597078514911747,0.6350076103500761,0.9092006033182504,1.0,0.9912227602905569,0.9085956416464891,1.0,0.3875,0.8260869565217391,0.04666666666666667,0.8571428571428571,0.5697674418604651,0.7391304347826086,0.6595829991980754,0.7692307692307693,0.36816720257234725,0.6418810289389068,0.9134268537074148,1.0,0.9975951903807615,0.9158316633266533,1.0,0.5422077922077922,0.39969135802469136,0.7142857142857143,0.6703296703296703,1.0,0.9830246913580247,1.0,0.9228395061728395,1.0,0.65,0.606542341791501,0.35818624467437615,0.6109589041095891,0.9131221719457013,0.9915254237288136,1.0,0.9185835351089588,1.0,0.36875,0.8322981366459627,0.10666666666666667,0.8633540372670807,0.5930232558139535,0.7391304347826086,0.6222935044105854,0.6923076923076923,0.36736334405144694,0.617363344051447,0.9166332665330661,1.0,0.9975951903807615,0.9266533066132264,1.0,0.4837662337662338,0.5714285714285714,0.38117283950617287,0.6467817896389325,0.9845679012345679,1.0,1.0,0.9320987654320988,1.0,0.40505173463177113,0.9536504089669797,0.5,0.5128597672994488,0.9946641556811049,1.0,0.106544901065449,0.8807506053268765,0.875,0.5406976744186046,0.36942675159235666,0.9308176100628931,0.0625,0.02666666666666667,0.7453416149068323,0.38866559485530544,0.9701853344077357,0.5290814279983955,1.0,0.5384615384615384,0.9974937343358395,0.0992765273311897,0.8793587174348697,0.75,0.42857142857142855,0.5555555555555556,1.0,0.4837662337662338,1.0,1.0,0.14599686028257458,1.0,0.9197530864197531,0.33201460742544125,0.9554680399878824,0.4,0.4834660134721372,0.9946641556811049,1.0,0.08340943683409437,0.8925544794188862,0.875,0.5581395348837209,0.075,0.36942675159235666,0.9308176100628931,0.006666666666666667,0.7329192546583851,0.31189710610932475,0.9713940370668815,1.0,0.5042117930204573,0.9974937343358395,0.38461538461538464,0.07636655948553055,0.894188376753507,0.75,0.42857142857142855,0.4845679012345679,1.0,0.42857142857142855,1.0,1.0,0.1130298273155416,1.0,0.9259259259259259,0.73815987933635,0.24254412659768715,0.9,0.728829104249465,0.9633777239709443,1.0,0.06423135464231354,1.0,0.8798426150121066,0.4,0.4409937888198758,0.25,0.7577639751552795,0.38372093023255816,0.5714285714285714,0.7751503006012024,1.0,0.9887775551102205,0.21663987138263666,0.726944667201283,0.8461538461538461,0.06792604501607717,1.0,0.9198396793587175,0.3055555555555556,1.0,0.6898148148148148,0.8116883116883117,0.9166666666666666,1.0,0.0031397174254317113,1.0,0.8024691358024691,1.0,0.9600484261501211,0.4169202678027998,0.41206636500754146,0.3375951293759513,0.315194130235402,0.4,0.9013317191283293,1.0,0.6866666666666666,0.5590062111801242,0.125,0.453416149068323,0.05813953488372093,0.4409937888198758,0.9819639278557114,1.0,0.4833667334669339,0.4445337620578778,0.3452572347266881,0.3076923076923077,0.24899759422614273,0.958316633266533,1.0,1.0,0.36106750392464676,0.9753086419753086,0.547077922077922,0.24845679012345678,0.23148148148148148,0.5714285714285714,1.0,0.7962962962962963,0.73815987933635,0.24254412659768715,0.9,0.728829104249465,0.9633777239709443,1.0,0.06423135464231354,0.8798426150121066,1.0,0.4,0.4409937888198758,0.25,0.7577639751552795,0.38372093023255816,0.5714285714285714,0.7751503006012024,1.0,0.9887775551102205,0.21663987138263666,0.726944667201283,0.8461538461538461,0.06792604501607717,0.9198396793587175,1.0,0.3055555555555556,1.0,0.6898148148148148,0.8116883116883117,0.9166666666666666,1.0,0.0031397174254317113,1.0,0.8024691358024691,1.0,0.9600484261501211,0.4169202678027998,0.41206636500754146,0.3375951293759513,0.315194130235402,0.4,0.9013317191283293,1.0,0.6866666666666666,0.5590062111801242,0.125,0.453416149068323,0.05813953488372093,0.4409937888198758,0.9819639278557114,1.0,0.4833667334669339,0.4445337620578778,0.3452572347266881,0.3076923076923077,0.24899759422614273,0.958316633266533,1.0,1.0,0.36106750392464676,0.9753086419753086,0.547077922077922,0.24845679012345678,0.23148148148148148,0.5714285714285714,1.0,0.7962962962962963,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.40476190476190477,0.6651270207852193,0.9764150943396226,0.9893390191897654,0.5915492957746479,0.7040441176470589,0.9647058823529412,0.7744360902255639,0.9828571428571429,1.0,0.7638190954773869,0.6583333333333333,0.46875,0.6666666666666666,0.5846153846153846,0.7014388489208633,0.9958333333333333,0.9900990099009901,0.0,0.5625,0.2857142857142857,1.0,0.14285714285714285,1.0,0.25,0.4883720930232558,0.5294117647058824,0.9523809523809523,0.4074074074074074,0.9761904761904762,0.40476190476190477,0.6651270207852193,0.9764150943396226,0.9893390191897654,0.5915492957746479,0.7040441176470589,0.9647058823529412,0.7744360902255639,0.9828571428571429,1.0,0.7638190954773869,0.6583333333333333,0.46875,0.6666666666666666,0.5846153846153846,0.7014388489208633,0.9958333333333333,0.9900990099009901,0.0,0.5625,0.2857142857142857,1.0,0.14285714285714285,1.0,0.25,0.4883720930232558,0.5294117647058824,0.9523809523809523,0.4074074074074074,0.9761904761904762,0.9751434034416826,0.6371191135734072,0.7650695517774343,0.9493670886075949,0.9192913385826772,0.8163265306122449,0.4489795918367347,0.8888888888888888,0.6083333333333333,0.958974358974359,0.925531914893617,1.0,0.9847328244274809,0.9727272727272728,0.803921568627451,0.8842443729903537,0.927797833935018,0.8108108108108109,1.0,1.0,0.6086956521739131,0.7352941176470589,0.9696969696969697,0.8571428571428571,0.98,0.9259259259259259,0.7903225806451613,0.6666666666666666,0.7105263157894737,0.9259259259259259,0.9751434034416826,0.6371191135734072,0.7650695517774343,0.9493670886075949,0.9192913385826772,0.8163265306122449,0.4489795918367347,0.8888888888888888,0.6083333333333333,0.958974358974359,0.925531914893617,1.0,0.9847328244274809,0.9727272727272728,0.803921568627451,0.8842443729903537,0.927797833935018,0.8108108108108109,1.0,1.0,0.6086956521739131,0.7352941176470589,0.9696969696969697,0.8571428571428571,0.98,0.9259259259259259,0.7903225806451613,0.6666666666666666,0.7105263157894737,0.9259259259259259,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.32786885245901637,0.7515151515151515,0.42857142857142855,0.34854771784232363,0.8268398268398268,0.8362068965517241,0.38596491228070173,0.8524590163934426,0.36470588235294116,0.8433734939759037,0.8653846153846154,{"type":"number","value":"nan"},0.35555555555555557,0.7,0.6,0.422680412371134,0.9146341463414634,0.8421052631578947,0.2,0.0,0.3333333333333333,0.6,0.0,0.0,0.11764705882352941,0.7894736842105263,0.2222222222222222,0.7049180327868853,0.8260869565217391,{"type":"number","value":"nan"},0.08695652173913043,0.34375,0.25316455696202533,0.08333333333333333,0.2765957446808511,0.0,1.0,0.35714285714285715,0.4,0.17647058823529413,0.0,0.1,0.3333333333333333,0.22727272727272727,0.21739130434782608,0.0,{"type":"number","value":"nan"},0.0,0.0,0.2,0.0,0.0,0.0,0.5714285714285714,0.0,0.2631578947368421,0.1875,0.3469387755102041,{"type":"number","value":"nan"}]]]}}}],["src",{"type":"object","name":"ColumnDataSource","id":"p1009","attributes":{"selected":{"type":"object","name":"Selection","id":"p1010","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1011"},"data":{"type":"map","entries":[["rank",[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,null,3,null,null,null,7,1,2,1,null,null,4,null,null,7,1,2,1,null,null,null,null,null,7,1,2,null,2,null,null,null,6,null,1,2,1,2,null,4,5,null,7,1,2,1,2,null,4,5,null,7,1,2,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,1,2,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,4,5,6,1,2,3,4,5,6]],["ranking",["not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","indistinguishable","indistinguishable","indistinguishable","indistinguishable","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","indistinguishable","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","indistinguishable","ranked","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","indistinguishable","ranked","ranked","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","ranked","ranked","indistinguishable","ranked","ranked","indistinguishable","ranked","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","ranked (no head-to-head)","ranked (no head-to-head)","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked"]],["dataset",["GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA"]],["component",["a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p"]],["ref_wave",[440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0]],["stratum",["all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all"]],["fit_method",["chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq"]],["algorithm",["expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow2","expb_powflex","expb_pow","expb_pow2flat","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_pow","gsm","expb_pow","giop","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","giop","expb_pow","expb_pow","giop","giop","gsm","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","giop","giop","gsm","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","giop","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","giop","giop","expb_pow","expb_pow","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","gsm","gsm","expb_pow","expb_pow","giop","giop","gsm","gsm","expb_pow","expb_pow","giop","giop","expb_pow","giop","giop","expb_pow","gsm","gsm","expb_pow","giop","giop","expb_pow","gsm","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","giop","gsm","gsm","giop","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","gsm"]],["win_frac",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6388888888888888,0.5694444444444444,0.4305555555555556,0.3611111111111111,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8464465073809162,0.7,0.5777574091047968,0.5753592173647203,0.4246407826352797,0.3,0.0744079449961803,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8735352305585147,0.7,0.5851421583613574,0.5345249007027192,0.41485784163864264,0.3,0.09045072574484339,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6939773769489452,0.65,0.5855484265200123,0.5242169595110772,0.3906559123421093,0.35,0.3060226230510547,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7,0.6982574136349741,0.6144210204705164,0.5072574484339191,0.3787855729721504,0.301742586365026,0.3,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7254812098991751,0.6166489118855577,0.6,0.5453989605625191,0.45460103943748087,0.4,0.1573720397249809,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.681790406355026,0.6752396895449704,0.6,0.5157444206664629,0.48425557933353713,0.4,0.14224598930481283,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6860447420483945,0.5821875954781546,0.55,0.5035157444206665,0.4964842555793335,0.45,0.23101604278074866,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.75,0.7282176704371752,0.5375802016498625,0.4961193121290519,0.4663101604278075,0.27178232956282483,0.25,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6839141683153249,0.576993583868011,0.55,0.5019871598899419,0.4980128401100581,0.45,0.23834988540870894,{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.75,0.7361663099969429,0.5374274366025054,0.4968802313194339,0.46569900687547744,0.2638336900030572,0.25,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7283950617283951,0.6558363417569194,0.4831932773109244,0.4509132420091324,0.4388185654008439,0.4046306504961411,0.7283950617283951,0.6558363417569194,0.4831932773109244,0.4509132420091324,0.4388185654008439,0.4046306504961411,0.6155419222903885,0.5781818181818181,0.5187680461982676,0.5072992700729927,0.3624091381100727,0.25263157894736843,0.6155419222903885,0.5781818181818181,0.5187680461982676,0.5072992700729927,0.3624091381100727,0.25263157894736843,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7572815533980582,0.7414330218068536,0.6923076923076923,0.526595744680851,0.2615803814713896,0.21568627450980393,0.9523809523809523,0.765625,0.7619047619047619,0.14285714285714285,0.0761904761904762,0.0]],["bias",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.19394492888049908,0.09886371818849926,0.288862042419904,0.3005822645880072,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.02266567142585174,0.005180993911545473,0.09129407359552766,0.0411265791157569,0.09012714756461837,0.0692786104387304,0.18318792890917734,0.01784794066608586,-0.03184215087854214,0.022879549123382192,0.007968858826222558,0.04008664873655876,0.10696067719753533,0.08710989715358819,0.0698744564780649,0.17894864267848343,0.017470073175136047,-0.02569045807804904,-0.02824372122163399,-0.05046092020190751,0.0759318402071556,-0.022966016215410057,0.02963104249708781,-0.004749392020864995,0.05195327083972345,0.12939816755683875,0.1624613194200335,-0.07273103516274504,-0.05066185095354836,0.03761375520768495,-0.04544919140118875,0.017970981515703865,0.03970046106176994,-0.017119016933146214,0.12554850766601944,0.15686232067411865,0.1946277789564208,-0.12130701221827689,0.3051960813391781,0.2636709643268458,-0.34508716515875826,-0.3844621696390337,0.5935313956678809,-0.4807259341008219,-0.6125205400077165,0.29593307653922896,-0.10473882302481219,0.3462132569006531,0.28987605131743854,-0.3287801944959503,-0.3615427272791508,0.6255106879321721,-0.46535450093166997,-0.5882944028801769,-0.001004627587986917,-0.02152669320545819,-0.015078667274009638,-0.022328329406208547,0.007993996252034341,0.0021479991830903877,0.06051217397711306,0.0036801007901456906,0.007433917999180251,0.021756864502924467,0.02561278785544574,0.010753138601125922,0.02386538163403773,-0.004873481515720202,-0.09576901597920506,-0.09006766815705458,0.03749474255998009,0.0553501076683216,0.0036462855660914784,-0.031922943694958406,-0.02211530519918614,-0.03883198483574779,0.018352012573667142,0.02205560725880429,0.13171053464156923,0.018890801046546057,0.021670350974372532,0.04145880705148941,0.04774043388194227,0.0313116962626796,0.04906418974583926,0.003264084710685511,-0.14714467088026617,-0.14177616306519447,0.07063016745079054,0.1118149913434201,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},-0.17531152419022256,-0.09911008003473842,-0.1624748200098547,-0.3287546093478896,-0.646848157817382,-0.6338449803440545,-0.17531152419022256,-0.09911008003473842,-0.1624748200098547,-0.3287546093478896,-0.646848157817382,-0.6338449803440545,-0.1256933946151948,0.24161566898788278,-0.1587023121477017,-0.16661366698818436,-0.3383639244463661,-0.45272225500639984,-0.1256933946151948,0.24161566898788278,-0.1587023121477017,-0.16661366698818436,-0.3383639244463661,-0.45272225500639984,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.3334146471667454,-0.010771264403590441,-0.027940911331577167,0.4084459522242334,1.0553032844487866,0.7075293902124413,1.1294644085393197,0.5810777994397205,1.20501872519992,1.53992359392684,2.882066022360361,0.4306942757208201]],["mae",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},1.0075849512908923,1.0595904781624736,1.0015542193310938,1.0025673704840696,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.054769080538987325,0.06235482839114259,0.09584660172393078,0.09871241867612568,0.09575374905206946,0.07253578717339071,0.18319324845823037,0.06812803815758861,0.04198654715433081,0.05275200541259317,0.059502198578262666,0.09492478712146557,0.1099886861576207,0.09268707950958133,0.07188497539522998,0.17895651029667037,0.06548887222982147,0.041658267198884325,0.18988702245481504,0.12561439287669107,0.1555926808567767,0.165966669788558,0.22238712612003209,0.18445629890662318,0.31993981233603863,0.2741273377164275,0.24555748601487148,0.13656803192080447,0.20035260703745505,0.15315823880656176,0.17679597278602532,0.23524830552396936,0.33790258844932897,0.20137099101847045,0.28044987214812034,0.25279678524532767,0.27819114162769676,0.4194828735134113,0.32541320674817587,0.369326117401916,1.0736096370231119,1.1705928154767133,0.5991490163318072,1.2515209983888917,1.636576723552225,0.34291882509361216,0.4017874842692315,0.35461077336893965,0.3864231828730822,1.0377345346615616,1.14935801798591,0.6302632315580203,1.19425382801077,1.4956532088412042,0.03585421782633236,0.03521517492991966,0.03509021841849291,0.052108461395650396,0.05512146130375739,0.03800668532156992,0.061034130521833596,0.03559666386848681,0.04677850120031368,0.0713062955120305,0.08613965328905526,0.03260437458237986,0.03501626501499855,0.03880883771283061,0.12747778182915237,0.10576677941733448,0.06840892976447033,0.0553501076683216,0.0691613275931311,0.0696128166176353,0.07744603943784334,0.10541124682164682,0.10898132624646761,0.08934948997619951,0.13247812287894134,0.09469582763584228,0.08720258497243671,0.1271970543109675,0.14524393310893147,0.06098212888515642,0.06444164008201181,0.06610883430286019,0.20976976159449912,0.18131984934450007,0.11777281239835613,0.1118149913434201,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.43106034044788455,0.45294530181809844,0.7199674602546717,1.0452742206118875,2.226921381913499,2.1419622243205425,0.43106034044788455,0.45294530181809844,0.7199674602546717,1.0452742206118875,2.226921381913499,2.1419622243205425,0.9322116020275655,0.5793428237145932,1.1013378355977443,1.0314270691920142,1.2147046622034505,1.0561067971980354,0.9322116020275655,0.5793428237145932,1.1013378355977443,1.0314270691920142,1.2147046622034505,1.0561067971980354,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.44899868532119314,0.458071693652625,0.35445744742257057,0.8804904020307422,1.3917154743015412,0.7776135648508153,1.1338354536365571,0.659463295464614,1.2416548330896138,1.53992359392684,2.9404907783008856,0.4306942757208201]],["coverage68",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.5,0.3333333333333333,0.4166666666666667,0.4166666666666667,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.5574068464101787,0.42105263157894735,0.1664637857577602,0.45511613308223475,0.21494182486221677,0.2,0.0006088280060882801,0.6912832929782082,0.875,0.5383217206906998,0.3684210526315789,0.4416195856873823,0.13724893487522824,0.2140232700551133,0.2,0.0006088280060882801,0.6915859564164649,0.75,0.36105166615713846,0.35,0.1938527084601339,0.35555555555555557,0.7577677224736048,1.0,0.9361380145278451,0.6283292978208233,0.375,0.35,0.3369000305716906,0.182288496652465,0.33729071537290717,0.7656108597285067,0.9352300242130751,1.0,0.6419491525423728,0.375,0.22276323797930614,0.7752196304150257,0.3,0.28291488058787506,0.9682988072818581,1.0,0.03409436834094368,0.5777845036319612,0.5,0.18076688983566647,0.7873371705543775,0.3,0.27036129822412736,0.9686126804770873,1.0,0.0243531202435312,0.5898910411622276,0.625,0.4301659125188537,0.13055386488131468,0.6,0.4328951391011923,0.812953995157385,0.9,0.029832572298325723,0.625,0.5950363196125908,0.9,0.7772397094430993,0.2328058429701765,0.22745098039215686,0.1878234398782344,0.15071843472944055,0.2,0.6558716707021792,0.75,0.4301659125188537,0.13055386488131468,0.6,0.4328951391011923,0.812953995157385,0.9,0.029832572298325723,0.5950363196125908,0.625,0.9,0.7772397094430993,0.2328058429701765,0.22745098039215686,0.1878234398782344,0.15071843472944055,0.2,0.6558716707021792,0.75,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.2619047619047619,0.4133949191685912,0.9339622641509434,0.9701492537313433,0.24295774647887325,0.37316176470588236,0.2619047619047619,0.4133949191685912,0.9339622641509434,0.9701492537313433,0.24295774647887325,0.37316176470588236,0.9407265774378585,0.3462603878116344,0.47913446676970634,0.8818565400843882,0.5196850393700787,0.3469387755102041,0.9407265774378585,0.3462603878116344,0.47913446676970634,0.8818565400843882,0.5196850393700787,0.3469387755102041,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.13114754098360656,0.509090909090909,0.2857142857142857,0.13692946058091288,0.6379310344827587,0.5775862068965517,0.043478260869565216,0.125,0.05063291139240506,0.0,0.13829787234042554,0.0]],["coverage95",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.9166666666666666,0.75,0.75,0.9166666666666666,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.807028173280824,1.0,0.3174071819841753,0.9303201506591338,0.44090630740967546,0.65,0.0024353120243531205,0.927360774818402,1.0,0.8006664647076643,1.0,0.9290646578782172,0.2681071211199026,0.44243723208818125,0.6,0.0027397260273972603,0.9267554479418886,1.0,0.6456741057780495,0.75,0.3597078514911747,0.6350076103500761,0.9092006033182504,1.0,0.9912227602905569,0.9085956416464891,1.0,0.65,0.606542341791501,0.35818624467437615,0.6109589041095891,0.9131221719457013,0.9915254237288136,1.0,0.9185835351089588,1.0,0.40505173463177113,0.9536504089669797,0.5,0.5128597672994488,0.9946641556811049,1.0,0.106544901065449,0.8807506053268765,0.875,0.33201460742544125,0.9554680399878824,0.4,0.4834660134721372,0.9946641556811049,1.0,0.08340943683409437,0.8925544794188862,0.875,0.73815987933635,0.24254412659768715,0.9,0.728829104249465,0.9633777239709443,1.0,0.06423135464231354,1.0,0.8798426150121066,1.0,0.9600484261501211,0.4169202678027998,0.41206636500754146,0.3375951293759513,0.315194130235402,0.4,0.9013317191283293,1.0,0.73815987933635,0.24254412659768715,0.9,0.728829104249465,0.9633777239709443,1.0,0.06423135464231354,0.8798426150121066,1.0,1.0,0.9600484261501211,0.4169202678027998,0.41206636500754146,0.3375951293759513,0.315194130235402,0.4,0.9013317191283293,1.0,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.40476190476190477,0.6651270207852193,0.9764150943396226,0.9893390191897654,0.5915492957746479,0.7040441176470589,0.40476190476190477,0.6651270207852193,0.9764150943396226,0.9893390191897654,0.5915492957746479,0.7040441176470589,0.9751434034416826,0.6371191135734072,0.7650695517774343,0.9493670886075949,0.9192913385826772,0.8163265306122449,0.9751434034416826,0.6371191135734072,0.7650695517774343,0.9493670886075949,0.9192913385826772,0.8163265306122449,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.32786885245901637,0.7515151515151515,0.42857142857142855,0.34854771784232363,0.8268398268398268,0.8362068965517241,0.08695652173913043,0.34375,0.25316455696202533,0.08333333333333333,0.2765957446808511,0.0]]]}}}],["selD",{"id":"p1057"}],["selC",{"type":"object","name":"Select","id":"p1058","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"id":"p1060"}]]]},"title":"component","options":["","a","a_dg","a_ph","bb","bb_p"]}}],["selS",{"type":"object","name":"Select","id":"p1059","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"id":"p1060"}]]]},"title":"stratum","options":["","all","eutrophic","mesotrophic","oligotrophic","unknown"],"value":"all"}}]]},"code":"\\n    const d = full.data;\\n    const o = {&#x27;rank&#x27;: [], &#x27;ranking&#x27;: [], &#x27;dataset&#x27;: [], &#x27;component&#x27;: [], &#x27;ref_wave&#x27;: [], &#x27;stratum&#x27;: [], &#x27;fit_method&#x27;: [], &#x27;algorithm&#x27;: [], &#x27;win_frac&#x27;: [], &#x27;bias&#x27;: [], &#x27;mae&#x27;: [], &#x27;coverage68&#x27;: [], &#x27;coverage95&#x27;: []};\\n    for (let i = 0; i &lt; d[&#x27;algorithm&#x27;].length; i++) {\\n      if ((selD.value === &#x27;&#x27; || String(d[&#x27;dataset&#x27;][i]) === selD.value)\\n          &amp;&amp; (selC.value === &#x27;&#x27; || String(d[&#x27;component&#x27;][i]) === selC.value)\\n          &amp;&amp; (selS.value === &#x27;&#x27; || String(d[&#x27;stratum&#x27;][i]) === selS.value)) {\\n    o[&#x27;rank&#x27;].push(d[&#x27;rank&#x27;][i]);\\n    o[&#x27;ranking&#x27;].push(d[&#x27;ranking&#x27;][i]);\\n    o[&#x27;dataset&#x27;].push(d[&#x27;dataset&#x27;][i]);\\n    o[&#x27;component&#x27;].push(d[&#x27;component&#x27;][i]);\\n    o[&#x27;ref_wave&#x27;].push(d[&#x27;ref_wave&#x27;][i]);\\n    o[&#x27;stratum&#x27;].push(d[&#x27;stratum&#x27;][i]);\\n    o[&#x27;fit_method&#x27;].push(d[&#x27;fit_method&#x27;][i]);\\n    o[&#x27;algorithm&#x27;].push(d[&#x27;algorithm&#x27;][i]);\\n    o[&#x27;win_frac&#x27;].push(d[&#x27;win_frac&#x27;][i]);\\n    o[&#x27;bias&#x27;].push(d[&#x27;bias&#x27;][i]);\\n    o[&#x27;mae&#x27;].push(d[&#x27;mae&#x27;][i]);\\n    o[&#x27;coverage68&#x27;].push(d[&#x27;coverage68&#x27;][i]);\\n    o[&#x27;coverage95&#x27;].push(d[&#x27;coverage95&#x27;][i]);\\n      }\\n    }\\n    src.data = o;\\n    src.change.emit();\\n    "}}]]]},"title":"dataset","options":["","GLORIA","L23","PANGAEA"]}},{"id":"p1058"},{"id":"p1059"},{"type":"object","name":"DataTable","id":"p1051","attributes":{"width":820,"height":420,"source":{"id":"p1009"},"view":{"type":"object","name":"CDSView","id":"p1055","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1056"}}},"columns":[{"type":"object","name":"TableColumn","id":"p1012","attributes":{"field":"rank","title":"rank","formatter":{"type":"object","name":"StringFormatter","id":"p1013"},"editor":{"type":"object","name":"StringEditor","id":"p1014"}}},{"type":"object","name":"TableColumn","id":"p1015","attributes":{"field":"ranking","title":"ranking","formatter":{"type":"object","name":"StringFormatter","id":"p1016"},"editor":{"type":"object","name":"StringEditor","id":"p1017"}}},{"type":"object","name":"TableColumn","id":"p1018","attributes":{"field":"dataset","title":"dataset","formatter":{"type":"object","name":"StringFormatter","id":"p1019"},"editor":{"type":"object","name":"StringEditor","id":"p1020"}}},{"type":"object","name":"TableColumn","id":"p1021","attributes":{"field":"component","title":"component","formatter":{"type":"object","name":"StringFormatter","id":"p1022"},"editor":{"type":"object","name":"StringEditor","id":"p1023"}}},{"type":"object","name":"TableColumn","id":"p1024","attributes":{"field":"ref_wave","title":"ref_wave","formatter":{"type":"object","name":"StringFormatter","id":"p1025"},"editor":{"type":"object","name":"StringEditor","id":"p1026"}}},{"type":"object","name":"TableColumn","id":"p1027","attributes":{"field":"stratum","title":"stratum","formatter":{"type":"object","name":"StringFormatter","id":"p1028"},"editor":{"type":"object","name":"StringEditor","id":"p1029"}}},{"type":"object","name":"TableColumn","id":"p1030","attributes":{"field":"fit_method","title":"fit_method","formatter":{"type":"object","name":"StringFormatter","id":"p1031"},"editor":{"type":"object","name":"StringEditor","id":"p1032"}}},{"type":"object","name":"TableColumn","id":"p1033","attributes":{"field":"algorithm","title":"algorithm","formatter":{"type":"object","name":"StringFormatter","id":"p1034"},"editor":{"type":"object","name":"StringEditor","id":"p1035"}}},{"type":"object","name":"TableColumn","id":"p1036","attributes":{"field":"win_frac","title":"win_frac","formatter":{"type":"object","name":"StringFormatter","id":"p1037"},"editor":{"type":"object","name":"StringEditor","id":"p1038"}}},{"type":"object","name":"TableColumn","id":"p1039","attributes":{"field":"bias","title":"bias","formatter":{"type":"object","name":"StringFormatter","id":"p1040"},"editor":{"type":"object","name":"StringEditor","id":"p1041"}}},{"type":"object","name":"TableColumn","id":"p1042","attributes":{"field":"mae","title":"mae","formatter":{"type":"object","name":"StringFormatter","id":"p1043"},"editor":{"type":"object","name":"StringEditor","id":"p1044"}}},{"type":"object","name":"TableColumn","id":"p1045","attributes":{"field":"coverage68","title":"coverage68","formatter":{"type":"object","name":"StringFormatter","id":"p1046"},"editor":{"type":"object","name":"StringEditor","id":"p1047"}}},{"type":"object","name":"TableColumn","id":"p1048","attributes":{"field":"coverage95","title":"coverage95","formatter":{"type":"object","name":"StringFormatter","id":"p1049"},"editor":{"type":"object","name":"StringEditor","id":"p1050"}}}]}}]}}]}}';
           const render_items = [{"docid":"4d5bbd45-8fc0-424e-8729-2bfbd8bf38f4","roots":{"p1061":"b38552cf-b3e4-4640-aa84-9b6300a4d733"},"root_ids":["p1061"]}];
           root.Bokeh.embed.embed_items(docs_json, render_items);
           }
           if (root.Bokeh !== undefined) {
             embed_document(root);
           } else {
             let attempts = 0;
             const timer = setInterval(function(root) {
               if (root.Bokeh !== undefined) {
                 clearInterval(timer);
                 embed_document(root);
               } else {
                 attempts++;
                 if (attempts > 100) {
                   clearInterval(timer);
                   console.log("Bokeh: ERROR: Unable to run BokehJS code because BokehJS library is missing");
                 }
               }
             }, 10, root)
           }
         })(window);
       });
     };
     if (document.readyState != "loading") fn();
     else document.addEventListener("DOMContentLoaded", fn);
   })();
   </script>

Sweeps folded into this board
-----------------------------

* **expb_giop_L23_mcmc_full** — 2026-08-20
  L23; 2 algorithm(s): ``expb_pow``, ``giop``.
  Up to 3304 scored spectra per contest; at least one pair separated.
  See :doc:`/reports/expb_giop_L23_mcmc_full/cross_algorithm`.

* **expb_giop_L23_test20** — 2026-08-07
  L23; 2 algorithm(s): ``expb_pow``, ``giop``.
  Up to 20 scored spectra per contest; at least one pair separated.
  See :doc:`/reports/expb_giop_L23_test20/cross_algorithm`.

* **gloria_turbid_v3** — 2026-07-31
  GLORIA; 4 algorithm(s): ``expb_pow``, ``expb_pow2``, ``expb_pow2flat``, ``expb_powflex``.
  Up to 12 scored spectra per contest; no pair separated — see the head-to-head table.
  See :doc:`/reports/gloria_turbid_v3/cross_algorithm`.

* **multi_L23_PANGAEA_v2** — 2026-08-10
  L23, PANGAEA; 3 algorithm(s): ``expb_pow``, ``giop``, ``gsm``.
  Up to 3315 scored spectra per contest; at least one pair separated.
  See :doc:`/reports/multi_L23_PANGAEA_v2/cross_algorithm`.

* **pangaea_fits_v2** — 2026-08-10
  PANGAEA; 3 algorithm(s): ``expb_pow``, ``giop``, ``gsm``.
  Up to 659 scored spectra per contest; at least one pair separated.
  See :doc:`/reports/pangaea_fits_v2/cross_algorithm`.



.. LEADERBOARD_END
.. toctree::
   :maxdepth: 1
   :glob:

   leaderboard_full
   glossary
   algorithms/*
   datasets/*
   gloria_investigation
   */*

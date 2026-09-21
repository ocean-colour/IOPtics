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
     - 2
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
     - 5
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
     - —
     - sole competitor
     - expb_pow
     - —
     - 0.0681
     - 0.0178
     - 0.995
     - 0.691
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
     - 3
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
     - 5
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
     - —
     - sole competitor
     - expb_pow
     - —
     - 0.0655
     - 0.0175
     - 0.995
     - 0.692
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
     - 5
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
     - —
     - sole competitor
     - expb_pow
     - —
     - 0.274
     - 0.129
     - 0.995
     - 0.628
     - 
   * - L23
     - a_dg
     - 443
     - chisq
     - 1
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
     - 5
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
     - mcmc
     - —
     - sole competitor
     - expb_pow
     - —
     - 0.28
     - 0.126
     - 0.995
     - 0.642
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
     - 3
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
     - 4
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
     - 5
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
     - —
     - sole competitor
     - expb_pow
     - —
     - 1.25
     - -0.481
     - 0.995
     - 0.578
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
     - 3
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
     - 4
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
     - 5
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
     - —
     - sole competitor
     - expb_pow
     - —
     - 1.19
     - -0.465
     - 0.995
     - 0.59
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
     - —
     - sole competitor
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
     - mcmc
     - —
     - sole competitor
     - expb_pow
     - —
     - 0.0684
     - 0.0375
     - 0.995
     - 0.656
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
     - —
     - sole competitor
     - expb_pow
     - —
     - 0.0947
     - 0.0189
     - 0.995
     - 0.595
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
     - mcmc
     - —
     - sole competitor
     - expb_pow
     - —
     - 0.118
     - 0.0706
     - 0.995
     - 0.656
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
     - 3
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
     - 3
     - ranked
     - giop
     - 0.439
     - 2.23
     - -0.647
     - 0.266
     - 0.243
     - 
   * - PANGAEA
     - a_ph
     - 440
     - chisq
     - 1
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
     - 2
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
     - 3
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
     - 2
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
     - 3
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
     - 3
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
     - 3
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
     - PANGAEA
   * - ``expb_pow``
     - not evaluated
     - scored (n=6619)
     - scored (n=243)
   * - ``giop``
     - not evaluated
     - scored (n=6556)
     - scored (n=361)
   * - ``gsm``
     - not evaluated
     - scored (n=3286)
     - scored (n=50)


Every contest, stratum and provenance column is on the :doc:`/reports/leaderboard_full` page; the table above is the ``stratum="all"`` headline.

.. raw:: html

   <script src="../_static/bokeh/bokeh-3.9.1.min.js"></script>
   <script src="../_static/bokeh/bokeh-widgets-3.9.1.min.js"></script>
   <script src="../_static/bokeh/bokeh-tables-3.9.1.min.js"></script>
   <div id="af6ca07a-fa51-4eb2-9926-e3b913eff4f8" data-root-id="p1127" style="display: contents;"></div>
   <script>
   (function() {
     const fn = function() {
       Bokeh.safely(function() {
         (function(root) {
           function embed_document(root) {
           const docs_json = '{"accac5dd-2bae-4809-ba8b-1b9149e94575":{"version":"3.9.1","title":"Bokeh Application","config":{"type":"object","name":"DocumentConfig","id":"p1128","attributes":{"notifications":{"type":"object","name":"Notifications","id":"p1129"}}},"roots":[{"type":"object","name":"Column","id":"p1127","attributes":{"children":[{"type":"object","name":"Select","id":"p1123","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"type":"object","name":"CustomJS","id":"p1126","attributes":{"args":{"type":"map","entries":[["full",{"type":"object","name":"ColumnDataSource","id":"p1072","attributes":{"selected":{"type":"object","name":"Selection","id":"p1073","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1074"},"data":{"type":"map","entries":[["rank",[1,2,null,null,5,null,1,2,3,4,5,null,1,2,null,null,5,null,1,null,3,null,5,null,1,null,3,null,5,null,1,2,3,4,5,null,1,null,3,null,5,null,1,null,3,null,5,null,1,null,null,null,5,null,1,2,3,4,5,null,1,null,null,null,5,null,1,null,null,null,5,null,1,null,null,null,5,null,1,2,3,4,5,null,1,null,null,null,5,null,1,null,null,null,5,null,1,2,3,4,5,null,1,null,null,4,5,null,1,2,3,4,5,null,1,2,3,4,5,null,1,2,3,4,5,null,1,2,null,null,5,null,1,2,3,4,5,null,1,2,3,4,5,null,null,null,null,null,null,null,1,null,3,null,5,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,null,3,null,5,null,null,null,null,null,null,null,1,2,null,null,5,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,null,null,null,1,2,3,1,2,3,null,null,null,1,2,3,null,null,null,1,2,3,1,2,3,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,1,2,null,1,2,3,null,null,null,1,2,null,1,2,3,null,null,1,2,null,null,null,null,1,2,null]],["ranking",["ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","indistinguishable","indistinguishable","ranked","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","not scored","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","not scored","ranked","ranked","ranked","indistinguishable","indistinguishable","ranked","ranked","not scored","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","not scored"]],["dataset",["L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA"]],["component",["a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p"]],["ref_wave",[440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0]],["stratum",["all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown"]],["fit_method",["chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq"]],["algorithm",["expb_pow","gsm","expb_pow","giop","giop","expb_pow","giop","giop","expb_pow","expb_pow","gsm","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","giop","giop","expb_pow","expb_pow","gsm","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","giop","gsm","expb_pow","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","giop","gsm","expb_pow","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","giop","expb_pow","giop","gsm","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","giop","giop","expb_pow","gsm","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","giop","expb_pow","giop","gsm","expb_pow","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","giop","expb_pow","giop","gsm","expb_pow","expb_pow","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","gsm","expb_pow","giop","expb_pow","gsm","giop","gsm","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","gsm","expb_pow","giop","expb_pow","gsm","giop","gsm","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","gsm","giop","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","gsm","giop","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","giop","gsm","expb_pow","giop","expb_pow","gsm","giop","gsm","expb_pow","gsm","expb_pow","giop","giop","expb_pow","gsm","giop","expb_pow","gsm","giop","expb_pow","giop","expb_pow","gsm","giop","expb_pow","gsm","giop","expb_pow","gsm"]],["win_frac",[0.8464465073809162,0.5777574091047968,0.5753592173647203,0.4246407826352797,0.0744079449961803,{"type":"number","value":"nan"},0.8433333333333334,0.7204968944099379,0.4096774193548387,0.2795031055900621,0.2413793103448276,{"type":"number","value":"nan"},0.8846463022508039,0.5703077851538926,0.5545308740978349,0.4454691259021652,0.04465902232951117,{"type":"number","value":"nan"},0.8038910505836576,0.737012987012987,0.6824902723735409,0.262987012987013,0.009419152276295133,{"type":"number","value":"nan"},0.8735352305585147,0.5851421583613574,0.5345249007027192,0.41485784163864264,0.09045072574484339,{"type":"number","value":"nan"},0.8366666666666667,0.7204968944099379,0.4645161290322581,0.2795031055900621,0.1896551724137931,{"type":"number","value":"nan"},0.9115755627009646,0.5589414595028067,0.5216254274793805,0.4410585404971933,0.0663850331925166,{"type":"number","value":"nan"},0.8249027237354085,0.7711038961038961,0.6622568093385214,0.2288961038961039,0.008634222919937205,{"type":"number","value":"nan"},0.6939773769489452,0.5855484265200123,0.5242169595110772,0.3906559123421093,0.3060226230510547,{"type":"number","value":"nan"},0.7266666666666667,0.6459627329192547,0.4241379310344828,0.35403726708074534,0.35161290322580646,{"type":"number","value":"nan"},0.694065757818765,0.5888151277408972,0.5145845906256287,0.3967041800643087,0.30593424218123494,{"type":"number","value":"nan"},0.7061688311688312,0.6093385214007782,0.5141287284144427,0.37665369649805447,0.29383116883116883,{"type":"number","value":"nan"},0.6982574136349741,0.6144210204705164,0.5072574484339191,0.3787855729721504,0.301742586365026,{"type":"number","value":"nan"},0.6933333333333334,0.6273291925465838,0.4793103448275862,0.37267080745341613,0.33225806451612905,{"type":"number","value":"nan"},0.6980753809141941,0.619995976664655,0.4948702474351237,0.3852491961414791,0.3019246190858059,{"type":"number","value":"nan"},0.7175324675324676,0.6233463035019455,0.5117739403453689,0.3649805447470817,0.2824675324675325,{"type":"number","value":"nan"},0.7254812098991751,0.6166489118855577,0.5453989605625191,0.45460103943748087,0.1573720397249809,{"type":"number","value":"nan"},0.5806451612903226,0.515527950310559,0.484472049689441,0.46,0.45517241379310347,{"type":"number","value":"nan"},0.7332528666264333,0.6229903536977492,0.5469125902165196,0.45308740978348033,0.1436330718165359,{"type":"number","value":"nan"},0.756420233463035,0.6007782101167315,0.547077922077922,0.45292207792207795,0.13971742543171115,{"type":"number","value":"nan"},0.681790406355026,0.6752396895449704,0.5157444206664629,0.48425557933353713,0.14224598930481283,{"type":"number","value":"nan"},0.667741935483871,0.62,0.5031055900621118,0.4968944099378882,0.19655172413793104,{"type":"number","value":"nan"},0.6908066787366727,0.6858922829581994,0.5192461908580593,0.48075380914194066,0.12311406155703078,{"type":"number","value":"nan"},0.756420233463035,0.6357976653696498,0.5048701298701299,0.49512987012987014,0.1043956043956044,{"type":"number","value":"nan"},0.6860447420483945,0.5821875954781546,0.5035157444206665,0.4964842555793335,0.23101604278074866,{"type":"number","value":"nan"},0.7689655172413793,0.7204968944099379,0.5933333333333334,0.2795031055900621,0.15806451612903225,{"type":"number","value":"nan"},0.7134244372990354,0.5340817963111467,0.5312814323073828,0.4659182036888532,0.25507946087306377,{"type":"number","value":"nan"},0.7369649805447471,0.7073929961089495,0.599025974025974,0.400974025974026,0.05180533751962323,{"type":"number","value":"nan"},0.7282176704371752,0.5375802016498625,0.4961193121290519,0.4663101604278075,0.27178232956282483,{"type":"number","value":"nan"},0.896551724137931,0.6086956521739131,0.47,0.391304347826087,0.15806451612903225,{"type":"number","value":"nan"},0.7846832397754611,0.5616961414790996,0.5538121102393885,0.38442969221484613,0.21531676022453888,{"type":"number","value":"nan"},0.7849293563579278,0.5308441558441559,0.46915584415584416,0.39377431906614785,0.3237354085603113,{"type":"number","value":"nan"},0.6839141683153249,0.576993583868011,0.5019871598899419,0.4980128401100581,0.23834988540870894,{"type":"number","value":"nan"},0.7689655172413793,0.7204968944099379,0.5933333333333334,0.2795031055900621,0.15806451612903225,{"type":"number","value":"nan"},0.7108118971061094,0.5360866078588613,0.5250452625226313,0.46391339214113875,0.263930798632066,{"type":"number","value":"nan"},0.7346303501945526,0.7066147859922179,0.599025974025974,0.400974025974026,0.054945054945054944,{"type":"number","value":"nan"},0.7361663099969429,0.5374274366025054,0.4968802313194339,0.46569900687547744,0.2638336900030572,{"type":"number","value":"nan"},0.8931034482758621,0.6086956521739131,0.47333333333333333,0.391304347826087,0.15806451612903225,{"type":"number","value":"nan"},0.7919005613472334,0.5622990353697749,0.5538121102393885,0.38382619191309597,0.20809943865276664,{"type":"number","value":"nan"},0.783359497645212,0.5438311688311688,0.45616883116883117,0.39377431906614785,0.32529182879377433,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7283950617283951,0.4831932773109244,0.4388185654008439,0.7926829268292683,0.5,0.2073170731707317,0.7258064516129032,0.5819672131147541,0.30327868852459017,0.7,0.6,0.2,0.8571428571428571,0.4583333333333333,0.43478260869565216,0.7283950617283951,0.4831932773109244,0.4388185654008439,0.7926829268292683,0.5,0.2073170731707317,0.7258064516129032,0.5819672131147541,0.30327868852459017,0.7,0.6,0.2,0.8571428571428571,0.4583333333333333,0.43478260869565216,0.5781818181818181,0.5072992700729927,0.25263157894736843,0.6595744680851063,0.35106382978723405,0.25,0.5652173913043478,0.5579710144927537,0.2638888888888889,0.8181818181818182,0.6153846153846154,0.08333333333333333,0.6129032258064516,0.42857142857142855,0.4,0.5781818181818181,0.5072992700729927,0.25263157894736843,0.6595744680851063,0.35106382978723405,0.25,0.5652173913043478,0.5579710144927537,0.2638888888888889,0.8181818181818182,0.6153846153846154,0.08333333333333333,0.6129032258064516,0.42857142857142855,0.4,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7572815533980582,0.6923076923076923,0.21568627450980393,0.8478260869565217,0.15217391304347827,{"type":"number","value":"nan"},0.7105263157894737,0.5555555555555556,0.2702702702702703,1.0,0.6,0.0,0.8571428571428571,0.14285714285714285,{"type":"number","value":"nan"},0.9523809523809523,0.14285714285714285,0.0,1.0,0.0,1.0,0.0,{"type":"number","value":"nan"},1.0,0.4,0.0,0.8571428571428571,0.14285714285714285,{"type":"number","value":"nan"}]],["bias",[0.02266567142585174,0.09129407359552766,0.0411265791157569,0.09012714756461837,0.18318792890917734,0.01784794066608586,0.27639945265432764,0.33531680250651674,0.4811265174267405,0.5347960988073202,0.5278661405921801,0.45809991444061415,0.002071540820445472,0.08689952383583033,0.019131237907968446,0.08237625640267687,0.19053845225259436,-0.00036726408807419286,0.0024297735759313266,0.026437190518024734,0.02527560574823151,0.06413238699843338,0.1331210189399581,-0.002085131007105945,0.022879549123382192,0.04008664873655876,0.10696067719753533,0.08710989715358819,0.17894864267848343,0.017470073175136047,0.24877784150695614,0.3067735715313853,0.45160989772157323,0.4974925180396377,0.5760621385162512,0.42431737025852057,0.003151332270580731,0.019224667006860763,0.10354729505842686,0.07977897711464066,0.18680570315777234,7.799416540388293e-05,0.00470401514941865,0.027119982922795494,0.03219825733120274,0.06483154109237521,0.13227170734122673,0.00012904506587729792,-0.02824372122163399,0.0759318402071556,-0.022966016215410057,0.02963104249708781,0.05195327083972345,0.12939816755683875,-0.10310515507279716,-0.03289047062386097,0.4577776297219174,0.4145639968106827,0.38631682825277447,0.14700625970521353,-0.02941892783032707,0.0688480469911319,-0.018390191738186235,0.023695388538180095,0.04499650354959228,0.13274820883495209,-0.02224694945943584,0.028645159278585464,-0.019788654843712394,-0.02711715620410582,0.002613386980742982,0.11230809319218915,-0.05066185095354836,0.03761375520768495,-0.04544919140118875,0.017970981515703865,0.03970046106176994,0.12554850766601944,-0.12574079438061037,-0.057576461098000076,0.40327386116781705,0.38451931253061233,0.36498286223769627,0.12864952428436105,-0.05184596148016474,0.030702800843453115,-0.04102723455280599,0.013520197796915268,0.03405752060759104,0.1296896388835156,-0.04402783546280076,-0.007272152008664268,-0.041606508545695364,-0.042257797821531384,-0.01121275173853209,0.10898678145339002,0.1946277789564208,-0.12130701221827689,0.2636709643268458,-0.34508716515875826,0.5935313956678809,-0.4807259341008219,0.46152981275955574,0.14213453540765353,0.3375709852391371,0.634970270727115,0.6873938313507193,-0.11896127182826155,0.1926145075231882,-0.16420317013778074,0.26196816675836465,-0.4077352288091698,0.589582947179788,-0.5057453450042434,0.11000937280371215,-0.06915686716359792,0.30461748041214287,-0.19227688979156143,0.5987053219719771,-0.4492879756926208,0.29593307653922896,-0.10473882302481219,0.28987605131743854,-0.3287801944959503,0.6255106879321721,-0.46535450093166997,0.42730369396763446,0.592720034597237,0.11545391285245166,0.3087769890492891,0.8494943847864687,-0.13079866680567342,0.2947374767626463,-0.14858512783156008,0.286566255652164,-0.3925549828707864,0.6193624129053217,-0.4912650922916436,0.19774568627916178,-0.04026441954047466,0.3538068413488116,-0.16487219879107773,0.6582153357902727,-0.42628526045012916,-0.001004627587986917,-0.02152669320545819,-0.022328329406208547,0.007993996252034341,0.06051217397711306,0.007433917999180251,0.036727142922037714,0.08160670791638802,0.057342613479907545,0.17602410058430973,0.15875084692370023,0.15374472800945727,-0.015911725756809325,-0.0071292708068845245,-0.0300139958802651,-0.03614662492364196,0.05726479706517473,-0.00739483199942248,-0.0016977737182239938,0.01766039228700822,0.008682903378073092,0.028252796544524506,0.07409887558170802,0.0312887749541062,0.02561278785544574,0.010753138601125922,0.02386538163403773,-0.004873481515720202,-0.09576901597920506,0.03749474255998009,0.017031567035251882,0.12507862788637025,0.08548912429922595,0.1145288141584353,0.1081870449014315,0.12335565579923746,0.014297587284121116,0.012039829429049798,0.0010985786213577597,-0.017785838389446695,-0.11840845068747241,0.021961683929327513,0.02459263566228298,0.046035737780673935,-0.051300630686292426,0.04719269447242236,0.04844508647387791,0.07802999484520723,0.0036462855660914784,-0.031922943694958406,-0.03883198483574779,0.018352012573667142,0.13171053464156923,0.018890801046546057,0.04018861842111354,0.09057666225673677,0.06890685911199501,0.20191053114386692,0.18032793556540017,0.17832107476458225,-0.023310011025589383,-0.010932464278539222,-0.048249809312583714,-0.06506674006278723,0.11582132678518775,-0.010660949210975934,0.016364439346610915,0.06761400040785714,0.040211958314995355,0.09346899521123908,0.21324309213152204,0.10067119864967133,0.04774043388194227,0.0313116962626796,0.04906418974583926,0.003264084710685511,-0.14714467088026617,0.07063016745079054,0.017580629800867387,0.13884573620165197,0.0965505623668439,0.12467433390963567,0.12059724808995864,0.13712995599621425,0.026997111243493688,0.02713595958171533,0.011240457706096274,-0.018855212667296617,-0.17721951738193165,0.04058755892423571,0.07036804165801369,0.10839542391182233,-0.0825191196895586,0.11560269104090626,0.11820473147104615,0.17687485555621918,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},-0.17531152419022256,-0.1624748200098547,-0.646848157817382,-0.15294824843510058,0.2087340238734765,-0.8526082600585422,-0.14304861373480604,-0.2152489071762308,-0.16819196991429564,-0.44847025712769617,-0.4004264565055373,-0.4944561895141041,-0.088302264468334,-0.06805829356204118,-0.5027116575279458,-0.17531152419022256,-0.1624748200098547,-0.646848157817382,-0.15294824843510058,0.2087340238734765,-0.8526082600585422,-0.14304861373480604,-0.2152489071762308,-0.16819196991429564,-0.44847025712769617,-0.4004264565055373,-0.4944561895141041,-0.088302264468334,-0.06805829356204118,-0.5027116575279458,0.24161566898788278,-0.16661366698818436,-0.45272225500639984,0.5264977291112234,0.028895694662704585,-0.16562634575467783,-0.2989386350871214,0.05928914320582934,-0.27215712583611307,-0.2065228886770406,0.2184859927499414,-0.40039904971335327,-0.18958789721752145,-0.9729722500435539,0.07054216822246318,0.24161566898788278,-0.16661366698818436,-0.45272225500639984,0.5264977291112234,0.028895694662704585,-0.16562634575467783,-0.2989386350871214,0.05928914320582934,-0.27215712583611307,-0.2065228886770406,0.2184859927499414,-0.40039904971335327,-0.18958789721752145,-0.9729722500435539,0.07054216822246318,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.3334146471667454,-0.027940911331577167,0.7075293902124413,0.24281024136687446,0.5541243963144635,{"type":"number","value":"nan"},0.25226400641375935,-0.18297892414371852,0.5359987734908522,0.5008634413712496,0.8178294171208307,0.8571859124819834,0.8802844767156273,1.4958279728530184,{"type":"number","value":"nan"},1.1294644085393197,1.53992359392684,0.4306942757208201,0.1682473869783263,1.9145519150866819,1.276582724929321,1.4082682969814568,{"type":"number","value":"nan"},0.4606319964604759,0.4808878791069082,0.4306942757208201,1.3965186169084483,1.8352764116491467,{"type":"number","value":"nan"}]],["mae",[0.054769080538987325,0.09584660172393078,0.09871241867612568,0.09575374905206946,0.18319324845823037,0.06812803815758861,0.27639945265432764,0.33762530560125725,0.4823445556448247,0.5410672352517423,0.5278661405921801,0.45809991444061415,0.03805722809866263,0.09019668900604239,0.08646775239816296,0.08862349546615267,0.19053845225259436,0.054954074970261946,0.02478984036052756,0.05467000586431481,0.035042285033667575,0.06795359161996872,0.13314729119692714,0.03703437921860009,0.05275200541259317,0.09492478712146557,0.1099886861576207,0.09268707950958133,0.17895651029667037,0.06548887222982147,0.24877784150695614,0.3102072064532664,0.4534368903702719,0.5051131156230468,0.5760621385162512,0.4243602218292317,0.03696074338657329,0.08368499401694374,0.10566216342851154,0.08602735092872815,0.18680570315777234,0.05331721004602108,0.024281869950421475,0.052701963459945045,0.03893072862457281,0.06816487120251424,0.13231067470356406,0.036186130735147426,0.18988702245481504,0.1555926808567767,0.165966669788558,0.22238712612003209,0.31993981233603863,0.2741273377164275,0.28340752712942274,0.5555642712228259,0.4604306145001922,0.8256958359062241,0.6040586567858957,1.2120815005963048,0.1805093804006832,0.14566395163256995,0.16321222210892028,0.20416221994645678,0.30965110329660095,0.251668656781457,0.14551330641317595,0.13150719185425896,0.14876029739842744,0.2050449898487543,0.2549842783486125,0.18966090392160906,0.20035260703745505,0.15315823880656176,0.17679597278602532,0.23524830552396936,0.33790258844932897,0.28044987214812034,0.30082539333743963,0.5644213265738678,0.4089867983733029,0.8172983917712555,0.6003631717683005,1.1958927091476417,0.19081983646856693,0.14333531935400923,0.17370922941963984,0.2167632241405837,0.32809012557956163,0.2585967305215826,0.1568047151707559,0.13765534577315153,0.15937959641722133,0.22212378387578213,0.2755237113355984,0.1965938858667169,0.27819114162769676,0.4194828735134113,0.369326117401916,1.0736096370231119,0.5991490163318072,1.2515209983888917,0.5178494616024001,1.2913936900860148,0.8782182229068549,0.6636317050017955,0.6874844941192546,1.4529088253732216,0.26811157756016724,0.4137078384089772,0.3261096633613154,1.155472548819776,0.5924173341564358,1.2902328151783533,0.23557885101631681,0.41652226858185104,0.3628747679390958,0.8308850205687863,0.6096529542740265,1.064076552811446,0.34291882509361216,0.4017874842692315,0.3864231828730822,1.0377345346615616,0.6302632315580203,1.19425382801077,0.4827011325009676,0.6249338659161132,1.262654983437665,0.837071136111299,0.8494943847864687,1.3930743521033926,0.33463114264107907,0.39431781689790735,0.3403142739440024,1.1132518576459423,0.6211797141793025,1.2314462528964292,0.277013894319311,0.4097674406937195,0.3988461018108429,0.8175425705109849,0.6676029245629505,1.012899453761869,0.03585421782633236,0.03521517492991966,0.052108461395650396,0.05512146130375739,0.061034130521833596,0.04677850120031368,0.05620217535048577,0.1266325650135991,0.06141659318290027,0.21177098533969807,0.17543994609853475,0.1689928110226302,0.029141398160382304,0.04830908606600093,0.036502911239251645,0.050670434175635215,0.05769029266526493,0.03988238941750666,0.025510240074303914,0.027064293807622652,0.03919549537372524,0.045194311820189625,0.07409887558170802,0.044701276650262356,0.08613965328905526,0.03260437458237986,0.03501626501499855,0.03880883771283061,0.12747778182915237,0.06840892976447033,0.035460481580826375,0.13504814826631417,0.08593264189848715,0.14327090098042916,0.1081870449014315,0.1322004600006108,0.08174604237148042,0.026258306377548113,0.028162287984156764,0.035665128861088746,0.1385202929553706,0.05912020675169272,0.039530612943991184,0.09121654709890548,0.07992048044187361,0.04916779913544267,0.05022515774113456,0.08913389750593459,0.0691613275931311,0.0696128166176353,0.10541124682164682,0.10898132624646761,0.13247812287894134,0.09469582763584228,0.06598689604625152,0.1527133303277659,0.0741341860296576,0.25265106957871986,0.20467583677607815,0.19965222078113354,0.05560712317315164,0.09341031763100127,0.06812914038449414,0.10005473994651748,0.1164703617347509,0.07820991930760979,0.07617415731042931,0.08798020041394938,0.11508711918082515,0.1361205257072846,0.21324309213152204,0.13445799829487126,0.14524393310893147,0.06098212888515642,0.06444164008201181,0.06610883430286019,0.20976976159449912,0.11777281239835613,0.03894437240876947,0.15071614952927948,0.09708360043391684,0.15934895595412124,0.12059724808995864,0.14765697855173476,0.13207495593280427,0.04648883340718357,0.04774228561324234,0.05680199564594668,0.2243731798256119,0.09602727061208904,0.09534353280805852,0.19597757809189686,0.16529757444808157,0.11881252699452771,0.12108511751895423,0.19772776985428342,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.43106034044788455,0.7199674602546717,2.226921381913499,0.8947269394642836,0.2087340238734765,6.10538785115244,0.33751319334378627,0.5144470728908179,0.5455950769955771,1.1807623784630206,1.0153010592225074,1.4622943170269007,0.5141911985859402,0.7766093537925074,1.7841859717711208,0.43106034044788455,0.7199674602546717,2.226921381913499,0.8947269394642836,0.2087340238734765,6.10538785115244,0.33751319334378627,0.5144470728908179,0.5455950769955771,1.1807623784630206,1.0153010592225074,1.4622943170269007,0.5141911985859402,0.7766093537925074,1.7841859717711208,0.5793428237145932,1.0314270691920142,1.0561067971980354,0.6690201176329018,1.3447605239992346,0.1985038057133819,0.8255088702856528,0.49427059780939464,0.6114758207985114,0.2879075443748258,0.71631966495296,0.6677758758086316,1.0896116064692234,35.999010336097186,0.5158282595334056,0.5793428237145932,1.0314270691920142,1.0561067971980354,0.6690201176329018,1.3447605239992346,0.1985038057133819,0.8255088702856528,0.49427059780939464,0.6114758207985114,0.2879075443748258,0.71631966495296,0.6677758758086316,1.0896116064692234,35.999010336097186,0.5158282595334056,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.44899868532119314,0.35445744742257057,0.7776135648508153,0.32256920643415565,0.6354549989089653,{"type":"number","value":"nan"},0.4499643127521502,0.2999751187296109,0.6167579234971567,0.5008634413712496,0.8178294171208307,0.8571859124819834,0.8802844767156273,1.503039412717468,{"type":"number","value":"nan"},1.1338354536365571,1.53992359392684,0.4306942757208201,0.1682473869783263,1.9145519150866819,1.2873450313143877,1.4082682969814568,{"type":"number","value":"nan"},0.4606319964604759,0.4808878791069082,0.4306942757208201,1.3965186169084483,1.8352764116491467,{"type":"number","value":"nan"}]],["coverage68",[0.5574068464101787,0.1664637857577602,0.45511613308223475,0.21494182486221677,0.0006088280060882801,0.6912832929782082,0.0,0.03184713375796178,0.03488372093023256,0.13836477987421383,0.0,0.06832298136645963,0.6160354552780016,0.13786173633440515,0.5104427736006684,0.22743682310469315,0.0,0.7306613226452906,0.4714064914992272,0.325434439178515,0.3148148148148148,0.21103896103896103,0.0031397174254317113,0.6944444444444444,0.5383217206906998,0.4416195856873823,0.13724893487522824,0.2140232700551133,0.0006088280060882801,0.6915859564164649,0.0,0.050955414012738856,0.03488372093023256,0.14465408805031446,0.0,0.10559006211180125,0.5995165189363416,0.49832915622389307,0.10530546623794212,0.22703569995988768,0.0,0.7282565130260521,0.437403400309119,0.30173775671406006,0.2916666666666667,0.20292207792207792,0.0031397174254317113,0.6959876543209876,0.36105166615713846,0.1938527084601339,0.35555555555555557,0.7577677224736048,0.9361380145278451,0.6283292978208233,0.2375,0.5652173913043478,0.02666666666666667,0.7453416149068323,0.37209302325581395,0.4409937888198758,0.3668805132317562,0.19212218649517684,0.35691318327974275,0.7482965931863728,0.9378757515030061,0.6328657314629259,0.2840909090909091,0.23919753086419754,0.37990580847723704,0.8966049382716049,0.9768518518518519,0.6574074074074074,0.3369000305716906,0.182288496652465,0.33729071537290717,0.7656108597285067,0.9352300242130751,0.6419491525423728,0.19375,0.5217391304347826,0.03333333333333333,0.7453416149068323,0.3953488372093023,0.453416149068323,0.34562951082598237,0.1885048231511254,0.34163987138263663,0.7555110220440882,0.9366733466933868,0.6472945891783567,0.2532467532467532,0.19290123456790123,0.3563579277864992,0.9027777777777778,0.9768518518518519,0.6682098765432098,0.22276323797930614,0.7752196304150257,0.28291488058787506,0.9682988072818581,0.03409436834094368,0.5777845036319612,0.18023255813953487,0.21656050955414013,0.6855345911949685,0.01875,0.006666666666666667,0.4472049689440994,0.2102090032154341,0.7671232876712328,0.29201764941837144,0.9807852965747702,0.03014469453376206,0.5695390781563127,0.32098765432098764,0.964451313755796,0.262987012987013,0.9921011058451816,0.05337519623233909,0.6419753086419753,0.18076688983566647,0.7873371705543775,0.27036129822412736,0.9686126804770873,0.0243531202435312,0.5898910411622276,0.21511627906976744,0.01875,0.2484076433121019,0.6981132075471698,0.0,0.4472049689440994,0.16881028938906753,0.7808219178082192,0.28399518652226236,0.981203007518797,0.022106109324758844,0.5803607214428858,0.26851851851851855,0.964451313755796,0.22077922077922077,0.9889415481832543,0.03453689167974882,0.6620370370370371,0.4301659125188537,0.13055386488131468,0.4328951391011923,0.812953995157385,0.029832572298325723,0.5950363196125908,0.22,0.21739130434782608,0.1125,0.453416149068323,0.19186046511627908,0.32298136645962733,0.4452905811623247,0.87374749498998,0.11495176848874598,0.4294306335204491,0.0317524115755627,0.6360721442885772,0.1697530864197531,0.4351851851851852,0.5032467532467533,0.6682098765432098,0.0015698587127158557,0.5046296296296297,0.7772397094430993,0.2328058429701765,0.22745098039215686,0.1878234398782344,0.15071843472944055,0.6558716707021792,0.41333333333333333,0.33540372670807456,0.05625,0.22981366459627328,0.011627906976744186,0.30434782608695654,0.7963927855711422,0.26733466933867733,0.2447749196141479,0.19011254019292603,0.11106655974338413,0.7182364729458918,0.2119309262166405,0.8132716049382716,0.2905844155844156,0.14506172839506173,0.13117283950617284,0.5030864197530864,0.4301659125188537,0.13055386488131468,0.4328951391011923,0.812953995157385,0.029832572298325723,0.5950363196125908,0.22,0.21739130434782608,0.1125,0.453416149068323,0.19186046511627908,0.32298136645962733,0.4452905811623247,0.87374749498998,0.11495176848874598,0.4294306335204491,0.0317524115755627,0.6360721442885772,0.1697530864197531,0.4351851851851852,0.5032467532467533,0.6682098765432098,0.0015698587127158557,0.5046296296296297,0.7772397094430993,0.2328058429701765,0.22745098039215686,0.1878234398782344,0.15071843472944055,0.6558716707021792,0.41333333333333333,0.33540372670807456,0.05625,0.22981366459627328,0.011627906976744186,0.30434782608695654,0.7963927855711422,0.26733466933867733,0.2447749196141479,0.19011254019292603,0.11106655974338413,0.7182364729458918,0.2119309262166405,0.8132716049382716,0.2905844155844156,0.14506172839506173,0.13117283950617284,0.5030864197530864,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.2619047619047619,0.9339622641509434,0.24295774647887325,0.9058823529411765,0.0,0.225,0.3125,0.2846153846153846,0.9603960396039604,0.0,0.0,1.0,0.25,0.9047619047619048,0.18518518518518517,0.2619047619047619,0.9339622641509434,0.24295774647887325,0.9058823529411765,0.0,0.225,0.3125,0.2846153846153846,0.9603960396039604,0.0,0.0,1.0,0.25,0.9047619047619048,0.18518518518518517,0.3462603878116344,0.8818565400843882,0.3469387755102041,0.23129251700680273,0.7872340425531915,1.0,0.9545454545454546,0.4117647058823529,0.32432432432432434,1.0,0.5217391304347826,0.42857142857142855,0.8888888888888888,0.0,0.42105263157894735,0.3462603878116344,0.8818565400843882,0.3469387755102041,0.23129251700680273,0.7872340425531915,1.0,0.9545454545454546,0.4117647058823529,0.32432432432432434,1.0,0.5217391304347826,0.42857142857142855,0.8888888888888888,0.0,0.42105263157894735,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.13114754098360656,0.2857142857142857,0.5775862068965517,0.15789473684210525,0.6730769230769231,{"type":"number","value":"nan"},0.1111111111111111,0.4,0.5526315789473685,0.0,0.0,0.0,0.11764705882352941,0.4782608695652174,{"type":"number","value":"nan"},0.043478260869565216,0.0,0.0,0.0,0.0,0.1,0.0,{"type":"number","value":"nan"},0.0,0.0,0.0,0.0,0.0,{"type":"number","value":"nan"}]],["coverage95",[0.807028173280824,0.3174071819841753,0.9303201506591338,0.44090630740967546,0.0024353120243531205,0.927360774818402,0.0,0.14012738853503184,0.0755813953488372,0.46540880503144655,0.0,0.3105590062111801,0.8585817888799355,0.2652733118971061,0.956140350877193,0.45166466105094266,0.0012057877813504824,0.9595190380761524,0.80370942812983,0.9494470774091627,0.5910493827160493,0.474025974025974,0.007849293563579277,0.9567901234567902,0.8006664647076643,0.9290646578782172,0.2681071211199026,0.44243723208818125,0.0027397260273972603,0.9267554479418886,0.00625,0.16560509554140126,0.10465116279069768,0.48427672955974843,0.0,0.32919254658385094,0.8561643835616438,0.9565580618212197,0.21382636655948553,0.4564781387886081,0.0012057877813504824,0.9571142284569139,0.7727975270479135,0.9368088467614534,0.5385802469135802,0.45616883116883117,0.007849293563579277,0.9583333333333334,0.6456741057780495,0.3597078514911747,0.6350076103500761,0.9092006033182504,0.9912227602905569,0.9085956416464891,0.3875,0.8260869565217391,0.04666666666666667,0.8571428571428571,0.5697674418604651,0.7391304347826086,0.6595829991980754,0.36816720257234725,0.6418810289389068,0.9134268537074148,0.9975951903807615,0.9158316633266533,0.5422077922077922,0.39969135802469136,0.6703296703296703,0.9830246913580247,1.0,0.9228395061728395,0.606542341791501,0.35818624467437615,0.6109589041095891,0.9131221719457013,0.9915254237288136,0.9185835351089588,0.36875,0.8322981366459627,0.10666666666666667,0.8633540372670807,0.5930232558139535,0.7391304347826086,0.6222935044105854,0.36736334405144694,0.617363344051447,0.9166332665330661,0.9975951903807615,0.9266533066132264,0.4837662337662338,0.38117283950617287,0.6467817896389325,0.9845679012345679,1.0,0.9320987654320988,0.40505173463177113,0.9536504089669797,0.5128597672994488,0.9946641556811049,0.106544901065449,0.8807506053268765,0.5406976744186046,0.36942675159235666,0.9308176100628931,0.0625,0.02666666666666667,0.7453416149068323,0.38866559485530544,0.9701853344077357,0.5290814279983955,0.9974937343358395,0.0992765273311897,0.8793587174348697,0.5555555555555556,1.0,0.4837662337662338,1.0,0.14599686028257458,0.9197530864197531,0.33201460742544125,0.9554680399878824,0.4834660134721372,0.9946641556811049,0.08340943683409437,0.8925544794188862,0.5581395348837209,0.075,0.36942675159235666,0.9308176100628931,0.006666666666666667,0.7329192546583851,0.31189710610932475,0.9713940370668815,0.5042117930204573,0.9974937343358395,0.07636655948553055,0.894188376753507,0.4845679012345679,1.0,0.42857142857142855,1.0,0.1130298273155416,0.9259259259259259,0.73815987933635,0.24254412659768715,0.728829104249465,0.9633777239709443,0.06423135464231354,0.8798426150121066,0.4,0.4409937888198758,0.25,0.7577639751552795,0.38372093023255816,0.5714285714285714,0.7751503006012024,0.9887775551102205,0.21663987138263666,0.726944667201283,0.06792604501607717,0.9198396793587175,0.3055555555555556,0.6898148148148148,0.8116883116883117,0.9166666666666666,0.0031397174254317113,0.8024691358024691,0.9600484261501211,0.4169202678027998,0.41206636500754146,0.3375951293759513,0.315194130235402,0.9013317191283293,0.6866666666666666,0.5590062111801242,0.125,0.453416149068323,0.05813953488372093,0.4409937888198758,0.9819639278557114,0.4833667334669339,0.4445337620578778,0.3452572347266881,0.24899759422614273,0.958316633266533,0.36106750392464676,0.9753086419753086,0.547077922077922,0.24845679012345678,0.23148148148148148,0.7962962962962963,0.73815987933635,0.24254412659768715,0.728829104249465,0.9633777239709443,0.06423135464231354,0.8798426150121066,0.4,0.4409937888198758,0.25,0.7577639751552795,0.38372093023255816,0.5714285714285714,0.7751503006012024,0.9887775551102205,0.21663987138263666,0.726944667201283,0.06792604501607717,0.9198396793587175,0.3055555555555556,0.6898148148148148,0.8116883116883117,0.9166666666666666,0.0031397174254317113,0.8024691358024691,0.9600484261501211,0.4169202678027998,0.41206636500754146,0.3375951293759513,0.315194130235402,0.9013317191283293,0.6866666666666666,0.5590062111801242,0.125,0.453416149068323,0.05813953488372093,0.4409937888198758,0.9819639278557114,0.4833667334669339,0.4445337620578778,0.3452572347266881,0.24899759422614273,0.958316633266533,0.36106750392464676,0.9753086419753086,0.547077922077922,0.24845679012345678,0.23148148148148148,0.7962962962962963,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.40476190476190477,0.9764150943396226,0.5915492957746479,0.9647058823529412,1.0,0.6583333333333333,0.46875,0.5846153846153846,0.9900990099009901,0.0,0.2857142857142857,1.0,0.25,0.9523809523809523,0.4074074074074074,0.40476190476190477,0.9764150943396226,0.5915492957746479,0.9647058823529412,1.0,0.6583333333333333,0.46875,0.5846153846153846,0.9900990099009901,0.0,0.2857142857142857,1.0,0.25,0.9523809523809523,0.4074074074074074,0.6371191135734072,0.9493670886075949,0.8163265306122449,0.4489795918367347,0.925531914893617,1.0,0.9727272727272728,0.803921568627451,0.8108108108108109,1.0,0.6086956521739131,0.8571428571428571,0.9259259259259259,0.6666666666666666,0.7105263157894737,0.6371191135734072,0.9493670886075949,0.8163265306122449,0.4489795918367347,0.925531914893617,1.0,0.9727272727272728,0.803921568627451,0.8108108108108109,1.0,0.6086956521739131,0.8571428571428571,0.9259259259259259,0.6666666666666666,0.7105263157894737,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.32786885245901637,0.42857142857142855,0.8362068965517241,0.38596491228070173,0.8653846153846154,{"type":"number","value":"nan"},0.35555555555555557,0.6,0.8421052631578947,0.0,0.3333333333333333,0.0,0.11764705882352941,0.8260869565217391,{"type":"number","value":"nan"},0.08695652173913043,0.08333333333333333,0.0,1.0,0.0,0.1,0.0,{"type":"number","value":"nan"},0.0,0.0,0.0,0.0,0.1875,{"type":"number","value":"nan"}]]]}}}],["src",{"type":"object","name":"ColumnDataSource","id":"p1075","attributes":{"selected":{"type":"object","name":"Selection","id":"p1076","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1077"},"data":{"type":"map","entries":[["rank",[1,2,null,null,5,null,1,null,3,null,5,null,1,null,null,null,5,null,1,null,null,null,5,null,1,2,3,4,5,null,1,2,3,4,5,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,1,2,3,1,2,3,1,2,3,null,null,null,null,null,null,1,2,3,1,2,3]],["ranking",["ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","sole competitor","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked"]],["dataset",["L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA"]],["component",["a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p"]],["ref_wave",[440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,443.0,443.0,443.0,440.0,440.0,440.0,443.0,443.0,443.0,440.0,440.0,440.0,443.0,443.0,443.0,555.0,555.0,555.0,670.0,670.0,670.0,555.0,555.0,555.0,670.0,670.0,670.0]],["stratum",["all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all"]],["fit_method",["chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq"]],["algorithm",["expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","giop","gsm","expb_pow","giop","gsm","gsm","expb_pow","giop","gsm","expb_pow","giop","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","giop","gsm","expb_pow","giop","expb_pow","gsm"]],["win_frac",[0.8464465073809162,0.5777574091047968,0.5753592173647203,0.4246407826352797,0.0744079449961803,{"type":"number","value":"nan"},0.8735352305585147,0.5851421583613574,0.5345249007027192,0.41485784163864264,0.09045072574484339,{"type":"number","value":"nan"},0.6939773769489452,0.5855484265200123,0.5242169595110772,0.3906559123421093,0.3060226230510547,{"type":"number","value":"nan"},0.6982574136349741,0.6144210204705164,0.5072574484339191,0.3787855729721504,0.301742586365026,{"type":"number","value":"nan"},0.7254812098991751,0.6166489118855577,0.5453989605625191,0.45460103943748087,0.1573720397249809,{"type":"number","value":"nan"},0.681790406355026,0.6752396895449704,0.5157444206664629,0.48425557933353713,0.14224598930481283,{"type":"number","value":"nan"},0.6860447420483945,0.5821875954781546,0.5035157444206665,0.4964842555793335,0.23101604278074866,{"type":"number","value":"nan"},0.7282176704371752,0.5375802016498625,0.4961193121290519,0.4663101604278075,0.27178232956282483,{"type":"number","value":"nan"},0.6839141683153249,0.576993583868011,0.5019871598899419,0.4980128401100581,0.23834988540870894,{"type":"number","value":"nan"},0.7361663099969429,0.5374274366025054,0.4968802313194339,0.46569900687547744,0.2638336900030572,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7283950617283951,0.4831932773109244,0.4388185654008439,0.7283950617283951,0.4831932773109244,0.4388185654008439,0.5781818181818181,0.5072992700729927,0.25263157894736843,0.5781818181818181,0.5072992700729927,0.25263157894736843,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7572815533980582,0.6923076923076923,0.21568627450980393,0.9523809523809523,0.14285714285714285,0.0]],["bias",[0.02266567142585174,0.09129407359552766,0.0411265791157569,0.09012714756461837,0.18318792890917734,0.01784794066608586,0.022879549123382192,0.04008664873655876,0.10696067719753533,0.08710989715358819,0.17894864267848343,0.017470073175136047,-0.02824372122163399,0.0759318402071556,-0.022966016215410057,0.02963104249708781,0.05195327083972345,0.12939816755683875,-0.05066185095354836,0.03761375520768495,-0.04544919140118875,0.017970981515703865,0.03970046106176994,0.12554850766601944,0.1946277789564208,-0.12130701221827689,0.2636709643268458,-0.34508716515875826,0.5935313956678809,-0.4807259341008219,0.29593307653922896,-0.10473882302481219,0.28987605131743854,-0.3287801944959503,0.6255106879321721,-0.46535450093166997,-0.001004627587986917,-0.02152669320545819,-0.022328329406208547,0.007993996252034341,0.06051217397711306,0.007433917999180251,0.02561278785544574,0.010753138601125922,0.02386538163403773,-0.004873481515720202,-0.09576901597920506,0.03749474255998009,0.0036462855660914784,-0.031922943694958406,-0.03883198483574779,0.018352012573667142,0.13171053464156923,0.018890801046546057,0.04774043388194227,0.0313116962626796,0.04906418974583926,0.003264084710685511,-0.14714467088026617,0.07063016745079054,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},-0.17531152419022256,-0.1624748200098547,-0.646848157817382,-0.17531152419022256,-0.1624748200098547,-0.646848157817382,0.24161566898788278,-0.16661366698818436,-0.45272225500639984,0.24161566898788278,-0.16661366698818436,-0.45272225500639984,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.3334146471667454,-0.027940911331577167,0.7075293902124413,1.1294644085393197,1.53992359392684,0.4306942757208201]],["mae",[0.054769080538987325,0.09584660172393078,0.09871241867612568,0.09575374905206946,0.18319324845823037,0.06812803815758861,0.05275200541259317,0.09492478712146557,0.1099886861576207,0.09268707950958133,0.17895651029667037,0.06548887222982147,0.18988702245481504,0.1555926808567767,0.165966669788558,0.22238712612003209,0.31993981233603863,0.2741273377164275,0.20035260703745505,0.15315823880656176,0.17679597278602532,0.23524830552396936,0.33790258844932897,0.28044987214812034,0.27819114162769676,0.4194828735134113,0.369326117401916,1.0736096370231119,0.5991490163318072,1.2515209983888917,0.34291882509361216,0.4017874842692315,0.3864231828730822,1.0377345346615616,0.6302632315580203,1.19425382801077,0.03585421782633236,0.03521517492991966,0.052108461395650396,0.05512146130375739,0.061034130521833596,0.04677850120031368,0.08613965328905526,0.03260437458237986,0.03501626501499855,0.03880883771283061,0.12747778182915237,0.06840892976447033,0.0691613275931311,0.0696128166176353,0.10541124682164682,0.10898132624646761,0.13247812287894134,0.09469582763584228,0.14524393310893147,0.06098212888515642,0.06444164008201181,0.06610883430286019,0.20976976159449912,0.11777281239835613,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.43106034044788455,0.7199674602546717,2.226921381913499,0.43106034044788455,0.7199674602546717,2.226921381913499,0.5793428237145932,1.0314270691920142,1.0561067971980354,0.5793428237145932,1.0314270691920142,1.0561067971980354,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.44899868532119314,0.35445744742257057,0.7776135648508153,1.1338354536365571,1.53992359392684,0.4306942757208201]],["coverage68",[0.5574068464101787,0.1664637857577602,0.45511613308223475,0.21494182486221677,0.0006088280060882801,0.6912832929782082,0.5383217206906998,0.4416195856873823,0.13724893487522824,0.2140232700551133,0.0006088280060882801,0.6915859564164649,0.36105166615713846,0.1938527084601339,0.35555555555555557,0.7577677224736048,0.9361380145278451,0.6283292978208233,0.3369000305716906,0.182288496652465,0.33729071537290717,0.7656108597285067,0.9352300242130751,0.6419491525423728,0.22276323797930614,0.7752196304150257,0.28291488058787506,0.9682988072818581,0.03409436834094368,0.5777845036319612,0.18076688983566647,0.7873371705543775,0.27036129822412736,0.9686126804770873,0.0243531202435312,0.5898910411622276,0.4301659125188537,0.13055386488131468,0.4328951391011923,0.812953995157385,0.029832572298325723,0.5950363196125908,0.7772397094430993,0.2328058429701765,0.22745098039215686,0.1878234398782344,0.15071843472944055,0.6558716707021792,0.4301659125188537,0.13055386488131468,0.4328951391011923,0.812953995157385,0.029832572298325723,0.5950363196125908,0.7772397094430993,0.2328058429701765,0.22745098039215686,0.1878234398782344,0.15071843472944055,0.6558716707021792,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.2619047619047619,0.9339622641509434,0.24295774647887325,0.2619047619047619,0.9339622641509434,0.24295774647887325,0.3462603878116344,0.8818565400843882,0.3469387755102041,0.3462603878116344,0.8818565400843882,0.3469387755102041,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.13114754098360656,0.2857142857142857,0.5775862068965517,0.043478260869565216,0.0,0.0]],["coverage95",[0.807028173280824,0.3174071819841753,0.9303201506591338,0.44090630740967546,0.0024353120243531205,0.927360774818402,0.8006664647076643,0.9290646578782172,0.2681071211199026,0.44243723208818125,0.0027397260273972603,0.9267554479418886,0.6456741057780495,0.3597078514911747,0.6350076103500761,0.9092006033182504,0.9912227602905569,0.9085956416464891,0.606542341791501,0.35818624467437615,0.6109589041095891,0.9131221719457013,0.9915254237288136,0.9185835351089588,0.40505173463177113,0.9536504089669797,0.5128597672994488,0.9946641556811049,0.106544901065449,0.8807506053268765,0.33201460742544125,0.9554680399878824,0.4834660134721372,0.9946641556811049,0.08340943683409437,0.8925544794188862,0.73815987933635,0.24254412659768715,0.728829104249465,0.9633777239709443,0.06423135464231354,0.8798426150121066,0.9600484261501211,0.4169202678027998,0.41206636500754146,0.3375951293759513,0.315194130235402,0.9013317191283293,0.73815987933635,0.24254412659768715,0.728829104249465,0.9633777239709443,0.06423135464231354,0.8798426150121066,0.9600484261501211,0.4169202678027998,0.41206636500754146,0.3375951293759513,0.315194130235402,0.9013317191283293,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.40476190476190477,0.9764150943396226,0.5915492957746479,0.40476190476190477,0.9764150943396226,0.5915492957746479,0.6371191135734072,0.9493670886075949,0.8163265306122449,0.6371191135734072,0.9493670886075949,0.8163265306122449,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.32786885245901637,0.42857142857142855,0.8362068965517241,0.08695652173913043,0.08333333333333333,0.0]]]}}}],["selD",{"id":"p1123"}],["selC",{"type":"object","name":"Select","id":"p1124","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"id":"p1126"}]]]},"title":"component","options":["","a","a_dg","a_ph","bb","bb_p"]}}],["selS",{"type":"object","name":"Select","id":"p1125","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"id":"p1126"}]]]},"title":"stratum","options":["","all","eutrophic","mesotrophic","oligotrophic","unknown"],"value":"all"}}]]},"code":"\\n    const d = full.data;\\n    const o = {&#x27;rank&#x27;: [], &#x27;ranking&#x27;: [], &#x27;dataset&#x27;: [], &#x27;component&#x27;: [], &#x27;ref_wave&#x27;: [], &#x27;stratum&#x27;: [], &#x27;fit_method&#x27;: [], &#x27;algorithm&#x27;: [], &#x27;win_frac&#x27;: [], &#x27;bias&#x27;: [], &#x27;mae&#x27;: [], &#x27;coverage68&#x27;: [], &#x27;coverage95&#x27;: []};\\n    for (let i = 0; i &lt; d[&#x27;algorithm&#x27;].length; i++) {\\n      if ((selD.value === &#x27;&#x27; || String(d[&#x27;dataset&#x27;][i]) === selD.value)\\n          &amp;&amp; (selC.value === &#x27;&#x27; || String(d[&#x27;component&#x27;][i]) === selC.value)\\n          &amp;&amp; (selS.value === &#x27;&#x27; || String(d[&#x27;stratum&#x27;][i]) === selS.value)) {\\n    o[&#x27;rank&#x27;].push(d[&#x27;rank&#x27;][i]);\\n    o[&#x27;ranking&#x27;].push(d[&#x27;ranking&#x27;][i]);\\n    o[&#x27;dataset&#x27;].push(d[&#x27;dataset&#x27;][i]);\\n    o[&#x27;component&#x27;].push(d[&#x27;component&#x27;][i]);\\n    o[&#x27;ref_wave&#x27;].push(d[&#x27;ref_wave&#x27;][i]);\\n    o[&#x27;stratum&#x27;].push(d[&#x27;stratum&#x27;][i]);\\n    o[&#x27;fit_method&#x27;].push(d[&#x27;fit_method&#x27;][i]);\\n    o[&#x27;algorithm&#x27;].push(d[&#x27;algorithm&#x27;][i]);\\n    o[&#x27;win_frac&#x27;].push(d[&#x27;win_frac&#x27;][i]);\\n    o[&#x27;bias&#x27;].push(d[&#x27;bias&#x27;][i]);\\n    o[&#x27;mae&#x27;].push(d[&#x27;mae&#x27;][i]);\\n    o[&#x27;coverage68&#x27;].push(d[&#x27;coverage68&#x27;][i]);\\n    o[&#x27;coverage95&#x27;].push(d[&#x27;coverage95&#x27;][i]);\\n      }\\n    }\\n    src.data = o;\\n    src.change.emit();\\n    "}}]]]},"title":"dataset","options":["","L23","PANGAEA"]}},{"id":"p1124"},{"id":"p1125"},{"type":"object","name":"DataTable","id":"p1117","attributes":{"width":820,"height":420,"source":{"id":"p1075"},"view":{"type":"object","name":"CDSView","id":"p1121","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1122"}}},"columns":[{"type":"object","name":"TableColumn","id":"p1078","attributes":{"field":"rank","title":"rank","formatter":{"type":"object","name":"StringFormatter","id":"p1079"},"editor":{"type":"object","name":"StringEditor","id":"p1080"}}},{"type":"object","name":"TableColumn","id":"p1081","attributes":{"field":"ranking","title":"ranking","formatter":{"type":"object","name":"StringFormatter","id":"p1082"},"editor":{"type":"object","name":"StringEditor","id":"p1083"}}},{"type":"object","name":"TableColumn","id":"p1084","attributes":{"field":"dataset","title":"dataset","formatter":{"type":"object","name":"StringFormatter","id":"p1085"},"editor":{"type":"object","name":"StringEditor","id":"p1086"}}},{"type":"object","name":"TableColumn","id":"p1087","attributes":{"field":"component","title":"component","formatter":{"type":"object","name":"StringFormatter","id":"p1088"},"editor":{"type":"object","name":"StringEditor","id":"p1089"}}},{"type":"object","name":"TableColumn","id":"p1090","attributes":{"field":"ref_wave","title":"ref_wave","formatter":{"type":"object","name":"StringFormatter","id":"p1091"},"editor":{"type":"object","name":"StringEditor","id":"p1092"}}},{"type":"object","name":"TableColumn","id":"p1093","attributes":{"field":"stratum","title":"stratum","formatter":{"type":"object","name":"StringFormatter","id":"p1094"},"editor":{"type":"object","name":"StringEditor","id":"p1095"}}},{"type":"object","name":"TableColumn","id":"p1096","attributes":{"field":"fit_method","title":"fit_method","formatter":{"type":"object","name":"StringFormatter","id":"p1097"},"editor":{"type":"object","name":"StringEditor","id":"p1098"}}},{"type":"object","name":"TableColumn","id":"p1099","attributes":{"field":"algorithm","title":"algorithm","formatter":{"type":"object","name":"StringFormatter","id":"p1100"},"editor":{"type":"object","name":"StringEditor","id":"p1101"}}},{"type":"object","name":"TableColumn","id":"p1102","attributes":{"field":"win_frac","title":"win_frac","formatter":{"type":"object","name":"StringFormatter","id":"p1103"},"editor":{"type":"object","name":"StringEditor","id":"p1104"}}},{"type":"object","name":"TableColumn","id":"p1105","attributes":{"field":"bias","title":"bias","formatter":{"type":"object","name":"StringFormatter","id":"p1106"},"editor":{"type":"object","name":"StringEditor","id":"p1107"}}},{"type":"object","name":"TableColumn","id":"p1108","attributes":{"field":"mae","title":"mae","formatter":{"type":"object","name":"StringFormatter","id":"p1109"},"editor":{"type":"object","name":"StringEditor","id":"p1110"}}},{"type":"object","name":"TableColumn","id":"p1111","attributes":{"field":"coverage68","title":"coverage68","formatter":{"type":"object","name":"StringFormatter","id":"p1112"},"editor":{"type":"object","name":"StringEditor","id":"p1113"}}},{"type":"object","name":"TableColumn","id":"p1114","attributes":{"field":"coverage95","title":"coverage95","formatter":{"type":"object","name":"StringFormatter","id":"p1115"},"editor":{"type":"object","name":"StringEditor","id":"p1116"}}}]}}]}}]}}';
           const render_items = [{"docid":"accac5dd-2bae-4809-ba8b-1b9149e94575","roots":{"p1127":"af6ca07a-fa51-4eb2-9926-e3b913eff4f8"},"root_ids":["p1127"]}];
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

* **multi_L23_PANGAEA_v2** — 2026-08-10
  L23, PANGAEA; 3 algorithm(s): ``expb_pow``, ``giop``, ``gsm``.
  Up to 3315 scored spectra per contest; at least one pair separated.
  See :doc:`/reports/multi_L23_PANGAEA_v2/cross_algorithm`.



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

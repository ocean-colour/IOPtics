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
     - 0.847
     - 0.0546
     - 0.0225
     - 0.998
     - 0.558
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
     - 5
     - ranked
     - giop
     - 0.0743
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
     - 0.0526
     - 0.0227
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
     - 3
     - ranked
     - gsm
     - 0.534
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
     - 5
     - ranked
     - giop
     - 0.0903
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
     - 0.0417
     - -0.0257
     - 1
     - 0.75
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
     - 0.585
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
     - 0.0294
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
     - mcmc
     - —
     - sole competitor
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
     - 0.0177
     - 0.998
     - 0.766
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
     - —
     - sole competitor
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
     - -0.122
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
     - 0.788
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
     - 0.0358
     - -0.00111
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
     - —
     - sole competitor
     - expb_pow
     - —
     - 0.0356
     - 0.00368
     - 1
     - 0.625
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
     - 0.0238
     - 0.998
     - 0.228
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
     - —
     - sole competitor
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
     - 0.0691
     - 0.00353
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
     - —
     - sole competitor
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
     - 0.049
     - 0.998
     - 0.228
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
     - —
     - sole competitor
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
     - scored (n=12)
     - scored (n=3334)
     - scored (n=243)
   * - ``expb_pow2``
     - scored (n=12)
     - not evaluated
     - not evaluated
   * - ``expb_pow2flat``
     - scored (n=12)
     - not evaluated
     - not evaluated
   * - ``expb_powflex``
     - scored (n=12)
     - not evaluated
     - not evaluated
   * - ``giop``
     - not evaluated
     - scored (n=3305)
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
   <div id="fdeac443-d3a3-4250-a15a-2894cccfb8b2" data-root-id="p1127" style="display: contents;"></div>
   <script>
   (function() {
     const fn = function() {
       Bokeh.safely(function() {
         (function(root) {
           function embed_document(root) {
           const docs_json = '{"827fd414-90cf-433e-adca-750ddd04ce15":{"version":"3.9.1","title":"Bokeh Application","config":{"type":"object","name":"DocumentConfig","id":"p1128","attributes":{"notifications":{"type":"object","name":"Notifications","id":"p1129"}}},"roots":[{"type":"object","name":"Column","id":"p1127","attributes":{"children":[{"type":"object","name":"Select","id":"p1123","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"type":"object","name":"CustomJS","id":"p1126","attributes":{"args":{"type":"map","entries":[["full",{"type":"object","name":"ColumnDataSource","id":"p1072","attributes":{"selected":{"type":"object","name":"Selection","id":"p1073","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1074"},"data":{"type":"map","entries":[["rank",[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,null,3,null,5,null,1,2,3,1,null,3,null,5,null,null,2,3,null,5,null,1,null,3,null,5,null,1,2,3,1,null,3,null,5,null,null,2,3,null,5,null,null,null,null,null,null,null,1,2,3,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,null,null,null,null,null,null,null,null,null,null,null,null,1,2,null,null,5,null,1,2,3,1,2,null,null,5,null,1,2,3,4,5,null,1,2,null,null,5,null,1,2,3,1,2,null,null,5,null,1,2,3,4,5,null,null,null,null,null,null,null,1,2,3,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,null,null,null,null,null,null,1,null,3,null,5,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,null,null,null,1,2,3,1,2,3,null,null,null,1,2,3,null,null,null,1,2,3,1,2,3,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,1,2,null,1,2,3,null,null,null,1,2,null,1,2,3,null,null,1,2,null,null,null,null,1,2,null]],["ranking",["not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","indistinguishable","ranked","ranked","indistinguishable","ranked","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","indistinguishable","ranked","ranked","indistinguishable","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","ranked","ranked","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","ranked","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","not scored","ranked","ranked","ranked","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","not scored","ranked","ranked","ranked","indistinguishable","indistinguishable","ranked","ranked","not scored","indistinguishable","indistinguishable","indistinguishable","ranked","ranked","not scored"]],["dataset",["GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA"]],["component",["a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p"]],["ref_wave",[440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0,670.0]],["stratum",["all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","eutrophic","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","unknown","unknown","unknown","unknown","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","oligotrophic","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown","all","all","all","eutrophic","eutrophic","mesotrophic","mesotrophic","mesotrophic","oligotrophic","oligotrophic","oligotrophic","unknown","unknown","unknown"]],["fit_method",["chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq"]],["algorithm",["expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow2","expb_powflex","expb_pow","expb_pow2flat","expb_powflex","expb_pow2","expb_pow","expb_pow2flat","expb_pow2","expb_powflex","expb_pow","expb_pow2flat","expb_pow2","expb_pow","expb_pow2flat","expb_powflex","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_pow","gsm","giop","giop","expb_pow","giop","expb_pow","gsm","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","giop","expb_pow","gsm","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","gsm","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","gsm","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","giop","gsm","gsm","expb_pow","expb_pow","giop","giop","expb_pow","giop","gsm","expb_pow","expb_pow","giop","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","giop","gsm","gsm","expb_pow","expb_pow","giop","giop","expb_pow","giop","gsm","expb_pow","expb_pow","giop","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","gsm","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","gsm","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","gsm","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","giop","gsm","expb_pow","giop","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","gsm","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","gsm","giop","expb_pow","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","gsm","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","giop","gsm","expb_pow","giop","expb_pow","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","gsm","expb_pow","giop","expb_pow","gsm","giop","gsm","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","gsm","expb_pow","giop","expb_pow","gsm","giop","gsm","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","gsm","giop","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","gsm","giop","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","expb_pow","giop","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","giop","gsm","expb_pow","giop","expb_pow","gsm","giop","gsm","expb_pow","gsm","expb_pow","giop","giop","expb_pow","gsm","giop","expb_pow","gsm","giop","expb_pow","giop","expb_pow","gsm","giop","expb_pow","gsm","giop","expb_pow","gsm"]],["win_frac",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6388888888888888,0.5694444444444444,0.4305555555555556,0.3611111111111111,0.6666666666666666,0.6,0.4,0.3333333333333333,0.6666666666666666,0.625,0.375,0.3333333333333333,0.6666666666666666,0.5555555555555556,0.4444444444444444,0.3333333333333333,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8467042167757649,0.7,0.5776928953399542,0.3,0.07426650366748166,{"type":"number","value":"nan"},0.842809364548495,0.41233766233766234,0.23875432525951557,0.8846463022508039,0.6153846153846154,0.5703077851538926,0.38461538461538464,0.04465902232951117,{"type":"number","value":"nan"},0.8571428571428571,0.8038910505836576,0.6824902723735409,0.14285714285714285,0.009419152276295133,{"type":"number","value":"nan"},0.8738011873953417,0.7,0.534453781512605,0.3,0.09031173594132029,{"type":"number","value":"nan"},0.8361204013377926,0.4675324675324675,0.18685121107266436,0.9115755627009646,0.6153846153846154,0.5216254274793805,0.38461538461538464,0.0663850331925166,{"type":"number","value":"nan"},0.8571428571428571,0.8249027237354085,0.6622568093385214,0.14285714285714285,0.008634222919937205,{"type":"number","value":"nan"},0.65,0.585485103132162,0.5241442542787286,0.3907748515755823,0.35,{"type":"number","value":"nan"},0.725752508361204,0.42214532871972316,0.3538961038961039,0.6923076923076923,0.5888151277408972,0.5145845906256287,0.3967041800643087,0.3076923076923077,{"type":"number","value":"nan"},0.6093385214007782,0.5714285714285714,0.5141287284144427,0.42857142857142855,0.37665369649805447,{"type":"number","value":"nan"},0.7,0.6143621084797556,0.5071821515892421,0.3789008981580149,0.3,{"type":"number","value":"nan"},0.6923076923076923,0.47750865051903113,0.3344155844155844,0.6923076923076923,0.619995976664655,0.4948702474351237,0.3852491961414791,0.3076923076923077,{"type":"number","value":"nan"},0.7142857142857143,0.6233463035019455,0.5117739403453689,0.3649805447470817,0.2857142857142857,{"type":"number","value":"nan"},0.7254392666157372,0.6168366570254225,0.6,0.4,0.1572432762836186,{"type":"number","value":"nan"},0.5844155844155844,0.45819397993311034,0.4532871972318339,0.7332528666264333,0.6229903536977492,0.5384615384615384,0.46153846153846156,0.1436330718165359,{"type":"number","value":"nan"},0.8571428571428571,0.756420233463035,0.6007782101167315,0.14285714285714285,0.13971742543171115,{"type":"number","value":"nan"},0.681894576012223,0.6752930430811387,0.6,0.4,0.14211491442542787,{"type":"number","value":"nan"},0.6688311688311688,0.6187290969899666,0.1972318339100346,0.6908066787366727,0.6858922829581994,0.5384615384615384,0.46153846153846156,0.12311406155703078,{"type":"number","value":"nan"},0.8571428571428571,0.756420233463035,0.6357976653696498,0.14285714285714285,0.1043956043956044,{"type":"number","value":"nan"},0.6862536154665855,0.5821237585943468,0.55,0.45,0.23089853300733496,{"type":"number","value":"nan"},0.7681660899653979,0.5919732441471572,0.1590909090909091,0.7134244372990354,0.5384615384615384,0.5312814323073828,0.46153846153846156,0.25507946087306377,{"type":"number","value":"nan"},0.7369649805447471,0.7142857142857143,0.7073929961089495,0.2857142857142857,0.05180533751962323,{"type":"number","value":"nan"},0.75,0.5375095492742552,0.4962703607855077,0.4662286063569682,0.25,{"type":"number","value":"nan"},0.8961937716262975,0.4682274247491639,0.1590909090909091,0.6923076923076923,0.5616961414790996,0.5538121102393885,0.38442969221484613,0.3076923076923077,{"type":"number","value":"nan"},0.8571428571428571,0.7849293563579278,0.39377431906614785,0.3237354085603113,0.14285714285714285,{"type":"number","value":"nan"},0.6841223930583041,0.5769289533995416,0.55,0.45,0.23823349633251834,{"type":"number","value":"nan"},0.7681660899653979,0.5919732441471572,0.1590909090909091,0.7108118971061094,0.5384615384615384,0.5250452625226313,0.46153846153846156,0.263930798632066,{"type":"number","value":"nan"},0.7346303501945526,0.7142857142857143,0.7066147859922179,0.2857142857142857,0.054945054945054944,{"type":"number","value":"nan"},0.75,0.5373567608861727,0.49703151164560816,0.4656173594132029,0.25,{"type":"number","value":"nan"},0.8927335640138409,0.47157190635451507,0.1590909090909091,0.6923076923076923,0.5622990353697749,0.5538121102393885,0.38382619191309597,0.3076923076923077,{"type":"number","value":"nan"},0.8571428571428571,0.783359497645212,0.39377431906614785,0.32529182879377433,0.14285714285714285,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7283950617283951,0.4831932773109244,0.4388185654008439,0.7926829268292683,0.5,0.2073170731707317,0.7258064516129032,0.5819672131147541,0.30327868852459017,0.7,0.6,0.2,0.8571428571428571,0.4583333333333333,0.43478260869565216,0.7283950617283951,0.4831932773109244,0.4388185654008439,0.7926829268292683,0.5,0.2073170731707317,0.7258064516129032,0.5819672131147541,0.30327868852459017,0.7,0.6,0.2,0.8571428571428571,0.4583333333333333,0.43478260869565216,0.5781818181818181,0.5072992700729927,0.25263157894736843,0.6595744680851063,0.35106382978723405,0.25,0.5652173913043478,0.5579710144927537,0.2638888888888889,0.8181818181818182,0.6153846153846154,0.08333333333333333,0.6129032258064516,0.42857142857142855,0.4,0.5781818181818181,0.5072992700729927,0.25263157894736843,0.6595744680851063,0.35106382978723405,0.25,0.5652173913043478,0.5579710144927537,0.2638888888888889,0.8181818181818182,0.6153846153846154,0.08333333333333333,0.6129032258064516,0.42857142857142855,0.4,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7572815533980582,0.6923076923076923,0.21568627450980393,0.8478260869565217,0.15217391304347827,{"type":"number","value":"nan"},0.7105263157894737,0.5555555555555556,0.2702702702702703,1.0,0.6,0.0,0.8571428571428571,0.14285714285714285,{"type":"number","value":"nan"},0.9523809523809523,0.14285714285714285,0.0,1.0,0.0,1.0,0.0,{"type":"number","value":"nan"},1.0,0.4,0.0,0.8571428571428571,0.14285714285714285,{"type":"number","value":"nan"}]],["bias",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.19394492888049908,0.09886371818849926,0.288862042419904,0.3005822645880072,0.1804630035332635,0.32654522895203475,0.5189438542698914,0.5233745334396707,-0.10845006689893011,-0.11579312979635004,-0.11581554902506785,-0.10984403824118738,0.47867540345539616,0.620064735722645,0.6567310742953156,0.3030153227405923,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.022456556153234608,0.005180993911545473,0.0912940736145409,0.0692786104387304,0.18318792889518165,-0.03184215087854214,0.276399452738628,0.47846701933115354,0.5278661404919569,0.0020715393414838523,-0.020884628999368382,0.08689952385352995,0.06864464474726195,0.19053845223326604,-0.05740987756608518,0.055443551243207434,0.002429770801430031,0.0252756057902781,0.07045697326796385,0.13312101892389094,-0.005580900428750368,0.022676010422415294,0.007968858826222558,0.10696067721981084,0.0698744564780649,0.1789486426626241,-0.02569045807804904,0.24877784159187355,0.44898538698343815,0.5760621384337925,0.0031513307307995397,-0.01776992602128158,0.10354729507892624,0.0679511021084438,0.1868057031341932,-0.053351214738347585,0.05757225516999953,0.004704011962228805,0.03219825737541426,0.07345559501493626,0.13227170733120297,0.0027785365168797593,-0.05046092020190751,0.07593184016007082,-0.022966016134179035,0.02939077533333423,-0.004749392020864995,0.1624613194200335,-0.10310515502775919,0.4577776294861162,0.382464539042247,-0.058969307766015944,0.06884804695510183,-0.0183901915957686,0.023695375158929277,-0.014291504469593486,0.18093385155404507,0.028645159221962535,-0.034455004281410795,-0.01978865499127025,0.013217420235868804,-0.027117311195364202,0.1442777403404143,-0.07273103516274504,0.037613755162277274,-0.04544919132182701,0.017734758411037888,-0.017119016933146214,0.15686232067411865,-0.12574079433670904,0.40327386094083195,0.3611914541906489,-0.07938292380874967,0.030702800808708908,-0.04102723441367262,0.013520183771248195,-0.022638508730816964,0.18126853817276967,-0.060249750409343106,-0.00727215206331,-0.041606508689968846,-0.04225796495461254,-0.006785701667962329,0.13296036061849814,0.19462777914440554,-0.12150103141770263,0.3051960813391781,-0.3844621696390337,0.593531395821645,-0.6125205400077165,0.45960721028438867,0.6349702715871159,0.6873938315957209,0.1926145076476451,-0.16420254899502773,-0.5450860110382908,0.28810004466814454,0.5895829469751528,-0.8054257003439286,0.33755013444548987,0.11000937320739612,-0.06915655569942225,0.07930672904304403,0.5987053233601409,-0.22836504008340808,0.29593307674315494,-0.10492906307439764,0.3462132569006531,-0.3615427272791508,0.6255106880890218,-0.5882944028801769,0.425302764518918,0.592720035435014,0.8494943850550063,0.2947374768977602,-0.1485845075628709,-0.5293670147292769,0.31686071887789624,0.6193624126968531,-0.7938282399468781,0.4024719551651448,0.19774568671475312,-0.04026410474308406,0.1248883963321501,0.6582153372301092,-0.1778626779141982,-0.0011099531280225339,-0.021526693205334735,-0.015078667274009638,0.0021479991830903877,0.0605121739761989,0.0036801007901456906,0.03672714289486678,0.05734261352810588,0.15738916994408658,-0.01591172697137211,-0.006613763414296425,-0.03001399587940501,-0.024790606859999897,0.057264797061826744,0.0010482159254798784,-0.0016977737149269645,0.0032151246004301637,0.017660387613441353,0.018625388010305555,0.07409887557792083,0.0063189052195542494,0.021756864502924467,0.010753138601695023,0.023827290969925752,-0.004873481516935341,-0.09006766815705458,0.0553501076683216,0.017031567006387416,0.0854891243523015,0.10790095910762787,0.042251145432925075,0.012039829201542451,0.0010985786226560545,-0.017785838393082787,-0.10285648347778475,0.07590156782735291,-0.015240799837705432,0.024592635658062356,0.047192694477077746,0.048445084825191165,-0.06583137575269804,0.03519121363922095,0.0035296684282339896,-0.031922943692624495,-0.02211530519918614,0.02205560725880429,0.13171053463838844,0.021670350974372532,0.040188618388008246,0.06890685916926631,0.17879022583373816,-0.02331001281820244,0.006001416919308333,-0.04824980930979306,-0.03836754899624939,0.11582132677892498,0.03181688198977506,0.01636443935508214,0.008799676946568136,0.067613985005748,0.05255334247170218,0.21324309212420567,0.0116235974422072,0.04145880705148941,0.031311696265165834,0.04902968564977339,0.0032640847078657664,-0.14177616306519447,0.1118149913434201,0.017580629768481737,0.09655056242559668,0.12031527229707106,0.07679398201969101,0.02713595928485124,0.011240457709061236,-0.018855212672803323,-0.1519295111489971,0.16057058597507523,-0.02111623423965514,0.07036804165155908,0.1156026910502046,0.11820472749569033,-0.12259633941004644,0.06510762026370776,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},-0.1753115252771431,-0.16247394514551128,-0.6468481702170642,-0.1529455113053929,0.20873401965376726,-0.8526082712648578,-0.14304861471986385,-0.21524890811765174,-0.1681919652671101,-0.448470258182465,-0.400426458319582,-0.4944561895491022,-0.08830226572604649,-0.06806077716061265,-0.5027116598912698,-0.1753115252771431,-0.16247394514551128,-0.6468481702170642,-0.1529455113053929,0.20873401965376726,-0.8526082712648578,-0.14304861471986385,-0.21524890811765174,-0.1681919652671101,-0.448470258182465,-0.400426458319582,-0.4944561895491022,-0.08830226572604649,-0.06806077716061265,-0.5027116598912698,0.2416156662796629,-0.16661291833318104,-0.4527222459905792,0.5264977301631184,0.02889753929580774,-0.16562635057208597,-0.2989386476549166,0.05928913594833585,-0.27215711605113346,-0.2065228859377275,0.21848599656559542,-0.400399020315083,-0.1895865549210648,-0.9729722500799373,0.07054217068784352,0.2416156662796629,-0.16661291833318104,-0.4527222459905792,0.5264977301631184,0.02889753929580774,-0.16562635057208597,-0.2989386476549166,0.05928913594833585,-0.27215711605113346,-0.2065228859377275,0.21848599656559542,-0.400399020315083,-0.1895865549210648,-0.9729722500799373,0.07054217068784352,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.33341464690253764,-0.027940911769632093,0.7075294005064681,0.24281024033196674,0.5541244344817158,{"type":"number","value":"nan"},0.25226400554599504,-0.1829789246325476,0.5359987626510831,0.5008634412489352,0.8178294110930349,0.8571859108319513,0.8802844830355583,1.495827940340667,{"type":"number","value":"nan"},1.1294644065110933,1.5399236002098928,0.43069427560422424,0.1682473868810228,1.91455191100043,1.276582720374166,1.408268291055062,{"type":"number","value":"nan"},0.460631995162766,0.48088788268618265,0.43069427560422424,1.3965186171350137,1.835276432807758,{"type":"number","value":"nan"}]],["mae",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},1.0075849512908923,1.0595904781624736,1.0015542193310938,1.0025673704840696,1.0006914750576792,0.9854606870494542,0.9584605680433718,0.9452019903717741,1.390206696853852,1.4101706771094538,1.4102342899173532,1.3939579156540054,0.6206141532256673,0.620064735722645,0.6567310742953156,0.7529097937472238,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.05456323794438611,0.06235482839114259,0.09584660173311188,0.07253578717339071,0.18319324844161478,0.04198654715433081,0.276399452738628,0.479689983872156,0.5278661404919569,0.038057226887677764,0.06409289816851427,0.09019668901015576,0.07365682015058939,0.19053845223326604,0.06090651302163441,0.05913451286204685,0.024789843593289174,0.03504228507836338,0.07045697326796385,0.13314729116792012,0.023403995662399923,0.05255166666183975,0.059502198578262666,0.10998868616489754,0.07188497539522998,0.17895651027744486,0.041658267198884325,0.24877784159187355,0.45081974824677773,0.5760621384337925,0.03696074200289767,0.05916091044378868,0.10566216342712909,0.07104020920453613,0.1868057031341932,0.05635798151222615,0.06013631118760365,0.02428187358953693,0.03893072867668135,0.07345559501493626,0.13231067467686808,0.02716310627054619,0.12561439287669107,0.15559268082627886,0.16596666971398322,0.2221652433753174,0.18445629890662318,0.24555748601487148,0.28340752736963104,0.4604306142823731,0.6009665683696588,0.13370900963132848,0.14566395163523893,0.1632122220431238,0.20416220919558636,0.18443198025007934,0.3449583616516485,0.13150719173177294,0.11073455423759548,0.1487602972193116,0.1845014634506228,0.20504518368715074,0.15350295979609752,0.13656803192080447,0.15315823877965506,0.17679597268767888,0.23503384680963402,0.20137099101847045,0.25279678524532767,0.30082539327483415,0.40898679826101847,0.5974034054595265,0.1434295166624402,0.14333531935663246,0.17370922932796562,0.21676321326262915,0.19810589459375394,0.3626589224601442,0.12393432529797166,0.1376553456495071,0.15937959628526244,0.2221239988258943,0.20745836707989618,0.15179210237544494,0.2781911414463789,0.4193732777317454,0.32541320674817587,1.1705928154767133,0.5991490158874946,1.636576723552225,0.5161879914468572,0.6636317039695709,0.687484494400195,0.2681115774754155,0.4137068060654008,1.6191208158938823,0.3189236180479136,0.5924173339962706,4.364048834824655,0.33755013444548987,0.23557885039694937,0.4165227682054966,0.5313621221729654,0.6096529528508667,0.2959495771265892,0.3429188250292581,0.40167772625303244,0.35461077336893965,1.14935801798591,0.6302632310799077,1.4956532088412042,0.48095228735586004,0.624933864907899,0.8494943850550063,0.33463114260462623,0.3943168190647839,1.573670763889223,0.32951948993963254,0.6211797139951363,4.073319804169112,0.4024719551651448,0.277013894099986,0.4097679291697993,0.5381477481346351,0.6676029230406659,0.22765470721580927,0.03575633055978211,0.03521517493074433,0.03509021841849291,0.03800668532156992,0.061034130519401764,0.03559666386848681,0.056202175355658524,0.06141659320207116,0.17415684142645005,0.029141397394843116,0.04208940126485361,0.036502911240135605,0.03906155962301994,0.0576902926617906,0.05834811978574228,0.02551024007392444,0.027755096371739896,0.027064290551180425,0.03046688766465233,0.07409887557792083,0.013334299145969508,0.0713062955120305,0.032604374590094354,0.0349811426893778,0.038808837713063316,0.10576677941733448,0.0553501076683216,0.03546048160854198,0.08593264195554773,0.10790095910762787,0.07828482419077765,0.026258306550115407,0.028162287992711477,0.035665128858189954,0.11676449918378484,0.07590156782735291,0.05846577257103558,0.03953061294283611,0.04916779913517155,0.05022515587858867,0.08562897056794472,0.03519121363922095,0.06905749804781935,0.06961281661911367,0.07744603943784334,0.08934948997619951,0.13247812287383653,0.08720258497243671,0.06598689605443431,0.07413418605227862,0.2032500706739786,0.05560712233510601,0.09370329496160212,0.06812914038561924,0.07858261752742601,0.11647036172831782,0.14649867241045844,0.07617415731170696,0.07533842815062441,0.08798018787918438,0.08130978161171387,0.21324309212420567,0.030973248565242972,0.1271970543109675,0.060982128897421495,0.06441130438725962,0.06610883430105541,0.18131984934450007,0.1118149913434201,0.038944372441379826,0.09708360049765896,0.12031527229707106,0.1343513485501553,0.04648883361021583,0.047742285626964476,0.056801995640027636,0.18415740365511035,0.16057058597507523,0.1140300028853185,0.09534353280647334,0.11881252699572564,0.12108511319023196,0.17606813284389977,0.06510762026370776,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.4310603414258616,0.7199648419040046,2.2269214899241057,0.8947210511749475,0.20873401965376726,6.105388401556664,0.3375131942038303,0.5144470696557626,0.5455950167658867,1.180762379500635,1.0153010598935017,1.4622943208628496,0.5141912020829527,0.7766048646567492,1.7841859621633676,0.4310603414258616,0.7199648419040046,2.2269214899241057,0.8947210511749475,0.20873401965376726,6.105388401556664,0.3375131942038303,0.5144470696557626,0.5455950167658867,1.180762379500635,1.0153010598935017,1.4622943208628496,0.5141912020829527,0.7766048646567492,1.7841859621633676,0.579342821237731,1.0314289305146,1.0561067653594365,0.6690201179295365,1.34476470537198,0.19850381263316175,0.8255089262942614,0.4942705948230115,0.6114758012879526,0.28790753014401904,0.7163196562604168,0.6677757940380413,1.0896150620636527,35.99901038590335,0.5158282527515914,0.579342821237731,1.0314289305146,1.0561067653594365,0.6690201179295365,1.34476470537198,0.19850381263316175,0.8255089262942614,0.4942705948230115,0.6114758012879526,0.28790753014401904,0.7163196562604168,0.6677757940380413,1.0896150620636527,35.99901038590335,0.5158282527515914,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.4489986851693022,0.35445744704531834,0.7776135770685051,0.32256920547776335,0.6354550409925013,{"type":"number","value":"nan"},0.44996431191296304,0.2999751182650796,0.616757912221386,0.5008634412489352,0.8178294110930349,0.8571859108319513,0.8802844830355583,1.5030393837894303,{"type":"number","value":"nan"},1.133835451698539,1.5399236002098928,0.43069427560422424,0.1682473868810228,1.91455191100043,1.2873450269703683,1.408268291055062,{"type":"number","value":"nan"},0.460631995162766,0.48088788268618265,0.43069427560422424,1.3965186171350137,1.835276432807758,{"type":"number","value":"nan"}]],["coverage68",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.5,0.3333333333333333,0.4166666666666667,0.4166666666666667,0.6,0.6,0.6,0.6,0.0,0.0,0.0,0.0,1.0,0.6666666666666666,0.6666666666666666,0.3333333333333333,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.5575757575757576,0.42105263157894735,0.1664637857577602,0.2,0.0006088280060882801,0.875,0.0,0.03508771929824561,0.0,0.6160354552780016,0.5,0.13786173633440515,0.15384615384615385,0.0,0.75,0.2857142857142857,0.4714064914992272,0.3148148148148148,0.2857142857142857,0.0031397174254317113,1.0,0.5384848484848485,0.3684210526315789,0.13724893487522824,0.2,0.0006088280060882801,0.75,0.0,0.03508771929824561,0.0,0.5995165189363416,0.5,0.10530546623794212,0.23076923076923078,0.0,0.75,0.14285714285714285,0.437403400309119,0.2916666666666667,0.14285714285714285,0.0031397174254317113,0.75,0.35,0.1938527084601339,0.35555555555555557,0.7579963789981895,1.0,0.375,0.2375,0.02666666666666667,0.3742690058479532,0.38461538461538464,0.19212218649517684,0.35691318327974275,0.7482965931863728,1.0,0.0,0.23919753086419754,0.2857142857142857,0.37990580847723704,1.0,0.8966049382716049,0.75,0.35,0.182288496652465,0.33729071537290717,0.7658418829209415,1.0,0.375,0.19375,0.03333333333333333,0.39766081871345027,0.38461538461538464,0.1885048231511254,0.34163987138263663,0.7555110220440882,1.0,0.0,0.2857142857142857,0.19290123456790123,0.3563579277864992,0.9027777777777778,1.0,0.75,0.22276323797930614,0.7754545454545455,0.3,1.0,0.03409436834094368,0.5,0.18128654970760233,0.01875,0.006666666666666667,0.2102090032154341,0.7671232876712328,1.0,0.38461538461538464,0.03014469453376206,0.25,0.14285714285714285,0.32098765432098764,0.964451313755796,1.0,0.05337519623233909,0.75,0.18076688983566647,0.7875757575757576,0.3,1.0,0.0243531202435312,0.625,0.21637426900584794,0.01875,0.0,0.16881028938906753,0.7808219178082192,1.0,0.38461538461538464,0.022106109324758844,0.25,0.14285714285714285,0.26851851851851855,0.964451313755796,1.0,0.03453689167974882,1.0,0.4302957151478576,0.13055386488131468,0.6,0.9,0.029832572298325723,0.625,0.22,0.1125,0.19298245614035087,0.4452905811623247,0.9230769230769231,0.11495176848874598,0.46153846153846156,0.0317524115755627,0.25,0.1697530864197531,0.8571428571428571,0.4351851851851852,0.8571428571428571,0.0015698587127158557,1.0,0.9,0.2328058429701765,0.2275196137598069,0.1878234398782344,0.2,0.75,0.41333333333333333,0.05625,0.011695906432748537,0.8461538461538461,0.26733466933867733,0.2447749196141479,0.19011254019292603,0.3076923076923077,0.5,1.0,0.2119309262166405,0.14506172839506173,0.13117283950617284,0.0,1.0,0.4302957151478576,0.13055386488131468,0.6,0.9,0.029832572298325723,0.625,0.22,0.1125,0.19298245614035087,0.4452905811623247,0.9230769230769231,0.11495176848874598,0.46153846153846156,0.0317524115755627,0.25,0.1697530864197531,0.8571428571428571,0.4351851851851852,0.8571428571428571,0.0015698587127158557,1.0,0.9,0.2328058429701765,0.2275196137598069,0.1878234398782344,0.2,0.75,0.41333333333333333,0.05625,0.011695906432748537,0.8461538461538461,0.26733466933867733,0.2447749196141479,0.19011254019292603,0.3076923076923077,0.5,1.0,0.2119309262166405,0.14506172839506173,0.13117283950617284,0.0,1.0,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.2619047619047619,0.9339622641509434,0.24295774647887325,0.9058823529411765,0.0,0.225,0.3125,0.2846153846153846,0.9603960396039604,0.0,0.0,1.0,0.25,0.9047619047619048,0.18518518518518517,0.2619047619047619,0.9339622641509434,0.24295774647887325,0.9058823529411765,0.0,0.225,0.3125,0.2846153846153846,0.9603960396039604,0.0,0.0,1.0,0.25,0.9047619047619048,0.18518518518518517,0.3462603878116344,0.8818565400843882,0.3469387755102041,0.23129251700680273,0.7872340425531915,1.0,0.9545454545454546,0.4117647058823529,0.32432432432432434,1.0,0.5217391304347826,0.42857142857142855,0.8888888888888888,0.0,0.42105263157894735,0.3462603878116344,0.8818565400843882,0.3469387755102041,0.23129251700680273,0.7872340425531915,1.0,0.9545454545454546,0.4117647058823529,0.32432432432432434,1.0,0.5217391304347826,0.42857142857142855,0.8888888888888888,0.0,0.42105263157894735,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.13114754098360656,0.2857142857142857,0.5775862068965517,0.15789473684210525,0.6730769230769231,{"type":"number","value":"nan"},0.1111111111111111,0.4,0.5526315789473685,0.0,0.0,0.0,0.11764705882352941,0.4782608695652174,{"type":"number","value":"nan"},0.043478260869565216,0.0,0.0,0.0,0.0,0.1,0.0,{"type":"number","value":"nan"},0.0,0.0,0.0,0.0,0.0,{"type":"number","value":"nan"}]],["coverage95",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.9166666666666666,0.75,0.75,0.9166666666666666,0.6,1.0,0.6,1.0,0.75,0.75,0.75,0.75,1.0,1.0,1.0,1.0,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.806969696969697,1.0,0.3174071819841753,0.65,0.0024353120243531205,1.0,0.0,0.07602339181286549,0.0,0.8585817888799355,1.0,0.2652733118971061,0.6923076923076923,0.0012057877813504824,1.0,1.0,0.8021638330757341,0.5910493827160493,0.5714285714285714,0.007849293563579277,1.0,0.8009090909090909,1.0,0.2684114424832623,0.6,0.0027397260273972603,1.0,0.00625,0.10526315789473684,0.0,0.8561643835616438,1.0,0.2142282958199357,0.6923076923076923,0.0012057877813504824,1.0,1.0,0.7727975270479135,0.5385802469135802,0.42857142857142855,0.007849293563579277,1.0,0.75,0.3597078514911747,0.6350076103500761,0.9094749547374774,1.0,1.0,0.3875,0.04666666666666667,0.5730994152046783,0.7692307692307693,0.36816720257234725,0.6418810289389068,0.9134268537074148,1.0,1.0,0.39969135802469136,0.7142857142857143,0.6703296703296703,1.0,0.9830246913580247,1.0,0.65,0.35818624467437615,0.6109589041095891,0.9133977066988533,1.0,1.0,0.36875,0.10666666666666667,0.5964912280701754,0.6923076923076923,0.36736334405144694,0.617363344051447,0.9166332665330661,1.0,1.0,0.5714285714285714,0.38117283950617287,0.6467817896389325,0.9845679012345679,1.0,1.0,0.40505173463177113,0.953939393939394,0.5,1.0,0.106544901065449,0.875,0.543859649122807,0.0625,0.02666666666666667,0.38866559485530544,0.9701853344077357,1.0,0.5384615384615384,0.0992765273311897,0.75,0.42857142857142855,0.5555555555555556,1.0,1.0,0.14599686028257458,1.0,0.33201460742544125,0.9557575757575758,0.4,1.0,0.08340943683409437,0.875,0.5614035087719298,0.075,0.006666666666666667,0.31189710610932475,0.9713940370668815,1.0,0.38461538461538464,0.07636655948553055,0.75,0.42857142857142855,0.4845679012345679,1.0,1.0,0.1130298273155416,1.0,0.7383826191913095,0.24254412659768715,0.9,1.0,0.06423135464231354,1.0,0.4,0.25,0.38596491228070173,0.7751503006012024,1.0,0.21663987138263666,0.8461538461538461,0.06792604501607717,1.0,0.3055555555555556,1.0,0.6898148148148148,1.0,0.0031397174254317113,1.0,1.0,0.4169202678027998,0.412190706095353,0.3375951293759513,0.4,1.0,0.6866666666666666,0.125,0.05847953216374269,1.0,0.4833667334669339,0.4445337620578778,0.3452572347266881,0.3076923076923077,1.0,1.0,0.36106750392464676,0.24845679012345678,0.23148148148148148,0.5714285714285714,1.0,0.7383826191913095,0.24254412659768715,0.9,1.0,0.06423135464231354,1.0,0.4,0.25,0.38596491228070173,0.7751503006012024,1.0,0.21663987138263666,0.8461538461538461,0.06792604501607717,1.0,0.3055555555555556,1.0,0.6898148148148148,1.0,0.0031397174254317113,1.0,1.0,0.4169202678027998,0.412190706095353,0.3375951293759513,0.4,1.0,0.6866666666666666,0.125,0.05847953216374269,1.0,0.4833667334669339,0.4445337620578778,0.3452572347266881,0.3076923076923077,1.0,1.0,0.36106750392464676,0.24845679012345678,0.23148148148148148,0.5714285714285714,1.0,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.40476190476190477,0.9764150943396226,0.5915492957746479,0.9647058823529412,1.0,0.6583333333333333,0.46875,0.5846153846153846,0.9900990099009901,0.0,0.2857142857142857,1.0,0.25,0.9523809523809523,0.4074074074074074,0.40476190476190477,0.9764150943396226,0.5915492957746479,0.9647058823529412,1.0,0.6583333333333333,0.46875,0.5846153846153846,0.9900990099009901,0.0,0.2857142857142857,1.0,0.25,0.9523809523809523,0.4074074074074074,0.6371191135734072,0.9493670886075949,0.8163265306122449,0.4489795918367347,0.925531914893617,1.0,0.9727272727272728,0.803921568627451,0.8108108108108109,1.0,0.6086956521739131,0.8571428571428571,0.9259259259259259,0.6666666666666666,0.7105263157894737,0.6371191135734072,0.9493670886075949,0.8163265306122449,0.4489795918367347,0.925531914893617,1.0,0.9727272727272728,0.803921568627451,0.8108108108108109,1.0,0.6086956521739131,0.8571428571428571,0.9259259259259259,0.6666666666666666,0.7105263157894737,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.32786885245901637,0.42857142857142855,0.8362068965517241,0.38596491228070173,0.8653846153846154,{"type":"number","value":"nan"},0.35555555555555557,0.6,0.8421052631578947,0.0,0.3333333333333333,0.0,0.11764705882352941,0.8260869565217391,{"type":"number","value":"nan"},0.08695652173913043,0.08333333333333333,0.0,1.0,0.0,0.1,0.0,{"type":"number","value":"nan"},0.0,0.0,0.0,0.0,0.1875,{"type":"number","value":"nan"}]]]}}}],["src",{"type":"object","name":"ColumnDataSource","id":"p1075","attributes":{"selected":{"type":"object","name":"Selection","id":"p1076","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1077"},"data":{"type":"map","entries":[["rank",[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,null,3,null,5,null,1,null,3,null,5,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,null,null,5,null,1,2,null,null,5,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,1,2,3,1,2,3,1,2,3,1,2,3,null,null,null,null,null,null,1,2,3,1,2,3]],["ranking",["not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","indistinguishable","indistinguishable","indistinguishable","indistinguishable","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","not scored","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","ranked","indistinguishable","ranked","indistinguishable","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","ranked","ranked","indistinguishable","indistinguishable","ranked","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","indistinguishable","indistinguishable","indistinguishable","indistinguishable","indistinguishable","sole competitor","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","ranked","not scored","not scored","not scored","not scored","not scored","not scored","ranked","ranked","ranked","ranked","ranked","ranked"]],["dataset",["GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","L23","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA","PANGAEA"]],["component",["a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p","a","a","a","a","a","a","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_ph","a_ph","a_ph","a_ph","a_ph","a_ph","bb","bb","bb","bb","bb","bb","bb_p","bb_p","bb_p","bb_p","bb_p","bb_p"]],["ref_wave",[440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,440.0,440.0,440.0,440.0,440.0,440.0,443.0,443.0,443.0,443.0,443.0,443.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,555.0,555.0,555.0,555.0,555.0,555.0,670.0,670.0,670.0,670.0,670.0,670.0,440.0,440.0,440.0,443.0,443.0,443.0,440.0,440.0,440.0,443.0,443.0,443.0,440.0,440.0,440.0,443.0,443.0,443.0,555.0,555.0,555.0,670.0,670.0,670.0,555.0,555.0,555.0,670.0,670.0,670.0]],["stratum",["all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all","all"]],["fit_method",["chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","mcmc","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq","chisq"]],["algorithm",["expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow2","expb_powflex","expb_pow","expb_pow2flat","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_powflex","expb_pow2flat","expb_pow2","expb_pow","expb_pow","gsm","giop","giop","expb_pow","expb_pow","expb_pow","gsm","giop","giop","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","giop","gsm","giop","expb_pow","expb_pow","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","gsm","expb_pow","giop","expb_pow","giop","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","gsm","giop","expb_pow","giop","expb_pow","expb_pow","gsm","expb_pow","giop","giop","expb_pow","expb_pow","giop","gsm","expb_pow","giop","gsm","gsm","expb_pow","giop","gsm","expb_pow","giop","giop","expb_pow","gsm","giop","expb_pow","gsm","expb_pow","giop","gsm","expb_pow","giop","gsm","giop","gsm","expb_pow","giop","expb_pow","gsm"]],["win_frac",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.6388888888888888,0.5694444444444444,0.4305555555555556,0.3611111111111111,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.8467042167757649,0.7,0.5776928953399542,0.3,0.07426650366748166,{"type":"number","value":"nan"},0.8738011873953417,0.7,0.534453781512605,0.3,0.09031173594132029,{"type":"number","value":"nan"},0.65,0.585485103132162,0.5241442542787286,0.3907748515755823,0.35,{"type":"number","value":"nan"},0.7,0.6143621084797556,0.5071821515892421,0.3789008981580149,0.3,{"type":"number","value":"nan"},0.7254392666157372,0.6168366570254225,0.6,0.4,0.1572432762836186,{"type":"number","value":"nan"},0.681894576012223,0.6752930430811387,0.6,0.4,0.14211491442542787,{"type":"number","value":"nan"},0.6862536154665855,0.5821237585943468,0.55,0.45,0.23089853300733496,{"type":"number","value":"nan"},0.75,0.5375095492742552,0.4962703607855077,0.4662286063569682,0.25,{"type":"number","value":"nan"},0.6841223930583041,0.5769289533995416,0.55,0.45,0.23823349633251834,{"type":"number","value":"nan"},0.75,0.5373567608861727,0.49703151164560816,0.4656173594132029,0.25,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7283950617283951,0.4831932773109244,0.4388185654008439,0.7283950617283951,0.4831932773109244,0.4388185654008439,0.5781818181818181,0.5072992700729927,0.25263157894736843,0.5781818181818181,0.5072992700729927,0.25263157894736843,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.7572815533980582,0.6923076923076923,0.21568627450980393,0.9523809523809523,0.14285714285714285,0.0]],["bias",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.19394492888049908,0.09886371818849926,0.288862042419904,0.3005822645880072,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.022456556153234608,0.005180993911545473,0.0912940736145409,0.0692786104387304,0.18318792889518165,-0.03184215087854214,0.022676010422415294,0.007968858826222558,0.10696067721981084,0.0698744564780649,0.1789486426626241,-0.02569045807804904,-0.05046092020190751,0.07593184016007082,-0.022966016134179035,0.02939077533333423,-0.004749392020864995,0.1624613194200335,-0.07273103516274504,0.037613755162277274,-0.04544919132182701,0.017734758411037888,-0.017119016933146214,0.15686232067411865,0.19462777914440554,-0.12150103141770263,0.3051960813391781,-0.3844621696390337,0.593531395821645,-0.6125205400077165,0.29593307674315494,-0.10492906307439764,0.3462132569006531,-0.3615427272791508,0.6255106880890218,-0.5882944028801769,-0.0011099531280225339,-0.021526693205334735,-0.015078667274009638,0.0021479991830903877,0.0605121739761989,0.0036801007901456906,0.021756864502924467,0.010753138601695023,0.023827290969925752,-0.004873481516935341,-0.09006766815705458,0.0553501076683216,0.0035296684282339896,-0.031922943692624495,-0.02211530519918614,0.02205560725880429,0.13171053463838844,0.021670350974372532,0.04145880705148941,0.031311696265165834,0.04902968564977339,0.0032640847078657664,-0.14177616306519447,0.1118149913434201,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},-0.1753115252771431,-0.16247394514551128,-0.6468481702170642,-0.1753115252771431,-0.16247394514551128,-0.6468481702170642,0.2416156662796629,-0.16661291833318104,-0.4527222459905792,0.2416156662796629,-0.16661291833318104,-0.4527222459905792,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.33341464690253764,-0.027940911769632093,0.7075294005064681,1.1294644065110933,1.5399236002098928,0.43069427560422424]],["mae",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},1.0075849512908923,1.0595904781624736,1.0015542193310938,1.0025673704840696,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.05456323794438611,0.06235482839114259,0.09584660173311188,0.07253578717339071,0.18319324844161478,0.04198654715433081,0.05255166666183975,0.059502198578262666,0.10998868616489754,0.07188497539522998,0.17895651027744486,0.041658267198884325,0.12561439287669107,0.15559268082627886,0.16596666971398322,0.2221652433753174,0.18445629890662318,0.24555748601487148,0.13656803192080447,0.15315823877965506,0.17679597268767888,0.23503384680963402,0.20137099101847045,0.25279678524532767,0.2781911414463789,0.4193732777317454,0.32541320674817587,1.1705928154767133,0.5991490158874946,1.636576723552225,0.3429188250292581,0.40167772625303244,0.35461077336893965,1.14935801798591,0.6302632310799077,1.4956532088412042,0.03575633055978211,0.03521517493074433,0.03509021841849291,0.03800668532156992,0.061034130519401764,0.03559666386848681,0.0713062955120305,0.032604374590094354,0.0349811426893778,0.038808837713063316,0.10576677941733448,0.0553501076683216,0.06905749804781935,0.06961281661911367,0.07744603943784334,0.08934948997619951,0.13247812287383653,0.08720258497243671,0.1271970543109675,0.060982128897421495,0.06441130438725962,0.06610883430105541,0.18131984934450007,0.1118149913434201,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.4310603414258616,0.7199648419040046,2.2269214899241057,0.4310603414258616,0.7199648419040046,2.2269214899241057,0.579342821237731,1.0314289305146,1.0561067653594365,0.579342821237731,1.0314289305146,1.0561067653594365,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.4489986851693022,0.35445744704531834,0.7776135770685051,1.133835451698539,1.5399236002098928,0.43069427560422424]],["coverage68",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.5,0.3333333333333333,0.4166666666666667,0.4166666666666667,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.5575757575757576,0.42105263157894735,0.1664637857577602,0.2,0.0006088280060882801,0.875,0.5384848484848485,0.3684210526315789,0.13724893487522824,0.2,0.0006088280060882801,0.75,0.35,0.1938527084601339,0.35555555555555557,0.7579963789981895,1.0,0.375,0.35,0.182288496652465,0.33729071537290717,0.7658418829209415,1.0,0.375,0.22276323797930614,0.7754545454545455,0.3,1.0,0.03409436834094368,0.5,0.18076688983566647,0.7875757575757576,0.3,1.0,0.0243531202435312,0.625,0.4302957151478576,0.13055386488131468,0.6,0.9,0.029832572298325723,0.625,0.9,0.2328058429701765,0.2275196137598069,0.1878234398782344,0.2,0.75,0.4302957151478576,0.13055386488131468,0.6,0.9,0.029832572298325723,0.625,0.9,0.2328058429701765,0.2275196137598069,0.1878234398782344,0.2,0.75,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.2619047619047619,0.9339622641509434,0.24295774647887325,0.2619047619047619,0.9339622641509434,0.24295774647887325,0.3462603878116344,0.8818565400843882,0.3469387755102041,0.3462603878116344,0.8818565400843882,0.3469387755102041,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.13114754098360656,0.2857142857142857,0.5775862068965517,0.043478260869565216,0.0,0.0]],["coverage95",[{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.9166666666666666,0.75,0.75,0.9166666666666666,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.806969696969697,1.0,0.3174071819841753,0.65,0.0024353120243531205,1.0,0.8009090909090909,1.0,0.2684114424832623,0.6,0.0027397260273972603,1.0,0.75,0.3597078514911747,0.6350076103500761,0.9094749547374774,1.0,1.0,0.65,0.35818624467437615,0.6109589041095891,0.9133977066988533,1.0,1.0,0.40505173463177113,0.953939393939394,0.5,1.0,0.106544901065449,0.875,0.33201460742544125,0.9557575757575758,0.4,1.0,0.08340943683409437,0.875,0.7383826191913095,0.24254412659768715,0.9,1.0,0.06423135464231354,1.0,1.0,0.4169202678027998,0.412190706095353,0.3375951293759513,0.4,1.0,0.7383826191913095,0.24254412659768715,0.9,1.0,0.06423135464231354,1.0,1.0,0.4169202678027998,0.412190706095353,0.3375951293759513,0.4,1.0,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.40476190476190477,0.9764150943396226,0.5915492957746479,0.40476190476190477,0.9764150943396226,0.5915492957746479,0.6371191135734072,0.9493670886075949,0.8163265306122449,0.6371191135734072,0.9493670886075949,0.8163265306122449,{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},{"type":"number","value":"nan"},0.32786885245901637,0.42857142857142855,0.8362068965517241,0.08695652173913043,0.08333333333333333,0.0]]]}}}],["selD",{"id":"p1123"}],["selC",{"type":"object","name":"Select","id":"p1124","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"id":"p1126"}]]]},"title":"component","options":["","a","a_dg","a_ph","bb","bb_p"]}}],["selS",{"type":"object","name":"Select","id":"p1125","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"id":"p1126"}]]]},"title":"stratum","options":["","all","eutrophic","mesotrophic","oligotrophic","unknown"],"value":"all"}}]]},"code":"\\n    const d = full.data;\\n    const o = {&#x27;rank&#x27;: [], &#x27;ranking&#x27;: [], &#x27;dataset&#x27;: [], &#x27;component&#x27;: [], &#x27;ref_wave&#x27;: [], &#x27;stratum&#x27;: [], &#x27;fit_method&#x27;: [], &#x27;algorithm&#x27;: [], &#x27;win_frac&#x27;: [], &#x27;bias&#x27;: [], &#x27;mae&#x27;: [], &#x27;coverage68&#x27;: [], &#x27;coverage95&#x27;: []};\\n    for (let i = 0; i &lt; d[&#x27;algorithm&#x27;].length; i++) {\\n      if ((selD.value === &#x27;&#x27; || String(d[&#x27;dataset&#x27;][i]) === selD.value)\\n          &amp;&amp; (selC.value === &#x27;&#x27; || String(d[&#x27;component&#x27;][i]) === selC.value)\\n          &amp;&amp; (selS.value === &#x27;&#x27; || String(d[&#x27;stratum&#x27;][i]) === selS.value)) {\\n    o[&#x27;rank&#x27;].push(d[&#x27;rank&#x27;][i]);\\n    o[&#x27;ranking&#x27;].push(d[&#x27;ranking&#x27;][i]);\\n    o[&#x27;dataset&#x27;].push(d[&#x27;dataset&#x27;][i]);\\n    o[&#x27;component&#x27;].push(d[&#x27;component&#x27;][i]);\\n    o[&#x27;ref_wave&#x27;].push(d[&#x27;ref_wave&#x27;][i]);\\n    o[&#x27;stratum&#x27;].push(d[&#x27;stratum&#x27;][i]);\\n    o[&#x27;fit_method&#x27;].push(d[&#x27;fit_method&#x27;][i]);\\n    o[&#x27;algorithm&#x27;].push(d[&#x27;algorithm&#x27;][i]);\\n    o[&#x27;win_frac&#x27;].push(d[&#x27;win_frac&#x27;][i]);\\n    o[&#x27;bias&#x27;].push(d[&#x27;bias&#x27;][i]);\\n    o[&#x27;mae&#x27;].push(d[&#x27;mae&#x27;][i]);\\n    o[&#x27;coverage68&#x27;].push(d[&#x27;coverage68&#x27;][i]);\\n    o[&#x27;coverage95&#x27;].push(d[&#x27;coverage95&#x27;][i]);\\n      }\\n    }\\n    src.data = o;\\n    src.change.emit();\\n    "}}]]]},"title":"dataset","options":["","GLORIA","L23","PANGAEA"]}},{"id":"p1124"},{"id":"p1125"},{"type":"object","name":"DataTable","id":"p1117","attributes":{"width":820,"height":420,"source":{"id":"p1075"},"view":{"type":"object","name":"CDSView","id":"p1121","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1122"}}},"columns":[{"type":"object","name":"TableColumn","id":"p1078","attributes":{"field":"rank","title":"rank","formatter":{"type":"object","name":"StringFormatter","id":"p1079"},"editor":{"type":"object","name":"StringEditor","id":"p1080"}}},{"type":"object","name":"TableColumn","id":"p1081","attributes":{"field":"ranking","title":"ranking","formatter":{"type":"object","name":"StringFormatter","id":"p1082"},"editor":{"type":"object","name":"StringEditor","id":"p1083"}}},{"type":"object","name":"TableColumn","id":"p1084","attributes":{"field":"dataset","title":"dataset","formatter":{"type":"object","name":"StringFormatter","id":"p1085"},"editor":{"type":"object","name":"StringEditor","id":"p1086"}}},{"type":"object","name":"TableColumn","id":"p1087","attributes":{"field":"component","title":"component","formatter":{"type":"object","name":"StringFormatter","id":"p1088"},"editor":{"type":"object","name":"StringEditor","id":"p1089"}}},{"type":"object","name":"TableColumn","id":"p1090","attributes":{"field":"ref_wave","title":"ref_wave","formatter":{"type":"object","name":"StringFormatter","id":"p1091"},"editor":{"type":"object","name":"StringEditor","id":"p1092"}}},{"type":"object","name":"TableColumn","id":"p1093","attributes":{"field":"stratum","title":"stratum","formatter":{"type":"object","name":"StringFormatter","id":"p1094"},"editor":{"type":"object","name":"StringEditor","id":"p1095"}}},{"type":"object","name":"TableColumn","id":"p1096","attributes":{"field":"fit_method","title":"fit_method","formatter":{"type":"object","name":"StringFormatter","id":"p1097"},"editor":{"type":"object","name":"StringEditor","id":"p1098"}}},{"type":"object","name":"TableColumn","id":"p1099","attributes":{"field":"algorithm","title":"algorithm","formatter":{"type":"object","name":"StringFormatter","id":"p1100"},"editor":{"type":"object","name":"StringEditor","id":"p1101"}}},{"type":"object","name":"TableColumn","id":"p1102","attributes":{"field":"win_frac","title":"win_frac","formatter":{"type":"object","name":"StringFormatter","id":"p1103"},"editor":{"type":"object","name":"StringEditor","id":"p1104"}}},{"type":"object","name":"TableColumn","id":"p1105","attributes":{"field":"bias","title":"bias","formatter":{"type":"object","name":"StringFormatter","id":"p1106"},"editor":{"type":"object","name":"StringEditor","id":"p1107"}}},{"type":"object","name":"TableColumn","id":"p1108","attributes":{"field":"mae","title":"mae","formatter":{"type":"object","name":"StringFormatter","id":"p1109"},"editor":{"type":"object","name":"StringEditor","id":"p1110"}}},{"type":"object","name":"TableColumn","id":"p1111","attributes":{"field":"coverage68","title":"coverage68","formatter":{"type":"object","name":"StringFormatter","id":"p1112"},"editor":{"type":"object","name":"StringEditor","id":"p1113"}}},{"type":"object","name":"TableColumn","id":"p1114","attributes":{"field":"coverage95","title":"coverage95","formatter":{"type":"object","name":"StringFormatter","id":"p1115"},"editor":{"type":"object","name":"StringEditor","id":"p1116"}}}]}}]}}]}}';
           const render_items = [{"docid":"827fd414-90cf-433e-adca-750ddd04ce15","roots":{"p1127":"fdeac443-d3a3-4250-a15a-2894cccfb8b2"},"root_ids":["p1127"]}];
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

* **expb_giop_L23_test20** — 2026-08-07
  L23; 2 algorithm(s): ``expb_pow``, ``giop``.
  Up to 20 scored spectra per contest; at least one pair separated.
  See :doc:`/reports/expb_giop_L23_test20/cross_algorithm`.

* **gloria_turbid_v3** — 2026-07-31
  GLORIA; 4 algorithm(s): ``expb_pow``, ``expb_pow2``, ``expb_pow2flat``, ``expb_powflex``.
  Up to 12 scored spectra per contest; no pair separated — see the head-to-head table.
  See :doc:`/reports/gloria_turbid_v3/cross_algorithm`.

* **multi_L23_PANGAEA_v2** — 2026-08-08
  L23, PANGAEA; 3 algorithm(s): ``expb_pow``, ``giop``, ``gsm``.
  Up to 3314 scored spectra per contest; at least one pair separated.
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

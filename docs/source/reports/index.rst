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

.. note::

   No sweeps have been published yet (the run/metrics/report layers arrive in
   Stages 2–5). As each ``<sweep_id>.rst`` page is generated it is linked from
   the toctree below — :mod:`ioptics.report.rst` (Stage 5) will switch this to a
   glob so new pages are picked up automatically.

.. LEADERBOARD_START (auto-generated; do not edit)

Leaderboard
-----------

.. list-table:: Leaderboard
   :header-rows: 1

   * - dataset
     - component
     - ref_wave
     - stratum
     - rank
     - algorithm
     - win_frac
     - bias
     - mae
     - coverage68
     - coverage95
   * - L23
     - a
     - 440
     - all
     - 1
     - giop
     - 0.85
     - 0.0579
     - 0.0617
     - 0.45
     - 0.65
   * - L23
     - a
     - 440
     - all
     - 2
     - expb_pow
     - 0.15
     - 0.0964
     - 0.109
     - 0.65
     - 1
   * - L23
     - a
     - 440
     - mesotrophic
     - 1
     - giop
     - 0.846
     - 0.0682
     - 0.0721
     - 0.462
     - 0.615
   * - L23
     - a
     - 440
     - mesotrophic
     - 2
     - expb_pow
     - 0.154
     - 0.116
     - 0.134
     - 0.615
     - 1
   * - L23
     - a
     - 440
     - oligotrophic
     - 1
     - giop
     - 0.857
     - 0.0391
     - 0.0426
     - 0.429
     - 0.714
   * - L23
     - a
     - 440
     - oligotrophic
     - 2
     - expb_pow
     - 0.143
     - 0.0616
     - 0.0634
     - 0.714
     - 1
   * - L23
     - a
     - 443
     - all
     - 1
     - giop
     - 0.8
     - 0.0578
     - 0.0624
     - 0.45
     - 0.6
   * - L23
     - a
     - 443
     - all
     - 2
     - expb_pow
     - 0.2
     - 0.0986
     - 0.109
     - 0.65
     - 1
   * - L23
     - a
     - 443
     - mesotrophic
     - 1
     - giop
     - 0.846
     - 0.0654
     - 0.0696
     - 0.462
     - 0.538
   * - L23
     - a
     - 443
     - mesotrophic
     - 2
     - expb_pow
     - 0.154
     - 0.116
     - 0.132
     - 0.615
     - 1
   * - L23
     - a
     - 443
     - oligotrophic
     - 1
     - giop
     - 0.714
     - 0.0439
     - 0.0491
     - 0.429
     - 0.714
   * - L23
     - a
     - 443
     - oligotrophic
     - 2
     - expb_pow
     - 0.286
     - 0.0666
     - 0.0666
     - 0.714
     - 1
   * - L23
     - a_dg
     - 440
     - all
     - 1
     - giop
     - 0.8
     - -0.00278
     - 0.116
     - 0.35
     - 0.4
   * - L23
     - a_dg
     - 440
     - all
     - 2
     - expb_pow
     - 0.2
     - 0.169
     - 0.299
     - 0.65
     - 0.9
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 1
     - giop
     - 0.769
     - 0.0138
     - 0.126
     - 0.231
     - 0.231
   * - L23
     - a_dg
     - 440
     - mesotrophic
     - 2
     - expb_pow
     - 0.231
     - 0.165
     - 0.334
     - 0.692
     - 0.923
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 1
     - giop
     - 0.857
     - -0.0328
     - 0.0972
     - 0.571
     - 0.714
   * - L23
     - a_dg
     - 440
     - oligotrophic
     - 2
     - expb_pow
     - 0.143
     - 0.176
     - 0.238
     - 0.571
     - 0.857
   * - L23
     - a_dg
     - 443
     - all
     - 1
     - giop
     - 0.8
     - -0.0262
     - 0.124
     - 0.25
     - 0.35
   * - L23
     - a_dg
     - 443
     - all
     - 2
     - expb_pow
     - 0.2
     - 0.17
     - 0.312
     - 0.7
     - 0.9
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 1
     - giop
     - 0.769
     - -0.0082
     - 0.134
     - 0.154
     - 0.231
   * - L23
     - a_dg
     - 443
     - mesotrophic
     - 2
     - expb_pow
     - 0.231
     - 0.165
     - 0.347
     - 0.769
     - 0.923
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 1
     - giop
     - 0.857
     - -0.0587
     - 0.106
     - 0.429
     - 0.571
   * - L23
     - a_dg
     - 443
     - oligotrophic
     - 2
     - expb_pow
     - 0.143
     - 0.177
     - 0.249
     - 0.571
     - 0.857
   * - L23
     - a_ph
     - 440
     - all
     - 1
     - giop
     - 0.75
     - 0.186
     - 0.25
     - 0.25
     - 0.6
   * - L23
     - a_ph
     - 440
     - all
     - 2
     - expb_pow
     - 0.25
     - -0.332
     - 0.702
     - 0.9
     - 1
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 1
     - giop
     - 0.769
     - 0.177
     - 0.257
     - 0.231
     - 0.538
   * - L23
     - a_ph
     - 440
     - mesotrophic
     - 2
     - expb_pow
     - 0.231
     - -0.29
     - 0.612
     - 0.846
     - 1
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 1
     - giop
     - 0.714
     - 0.202
     - 0.237
     - 0.286
     - 0.714
   * - L23
     - a_ph
     - 440
     - oligotrophic
     - 2
     - expb_pow
     - 0.286
     - -0.402
     - 0.883
     - 1
     - 1
   * - L23
     - a_ph
     - 443
     - all
     - 1
     - giop
     - 0.7
     - 0.225
     - 0.278
     - 0.3
     - 0.5
   * - L23
     - a_ph
     - 443
     - all
     - 2
     - expb_pow
     - 0.3
     - -0.308
     - 0.669
     - 0.9
     - 1
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - 1
     - giop
     - 0.769
     - 0.204
     - 0.264
     - 0.385
     - 0.538
   * - L23
     - a_ph
     - 443
     - mesotrophic
     - 2
     - expb_pow
     - 0.231
     - -0.272
     - 0.591
     - 0.846
     - 1
   * - L23
     - a_ph
     - 443
     - oligotrophic
     - 1
     - giop
     - 0.571
     - 0.265
     - 0.303
     - 0.143
     - 0.429
   * - L23
     - a_ph
     - 443
     - oligotrophic
     - 2
     - expb_pow
     - 0.429
     - -0.37
     - 0.825
     - 1
     - 1
   * - L23
     - bb
     - 555
     - all
     - 1
     - expb_pow
     - 0.55
     - 0.02
     - 0.0354
     - 0.8
     - 1
   * - L23
     - bb
     - 555
     - all
     - 2
     - giop
     - 0.45
     - -0.0259
     - 0.0345
     - 0.6
     - 0.9
   * - L23
     - bb
     - 555
     - mesotrophic
     - 1
     - expb_pow
     - 0.538
     - 0.015
     - 0.0334
     - 0.846
     - 1
   * - L23
     - bb
     - 555
     - mesotrophic
     - 2
     - giop
     - 0.462
     - -0.0301
     - 0.0381
     - 0.462
     - 0.846
   * - L23
     - bb
     - 555
     - oligotrophic
     - 1
     - expb_pow
     - 0.571
     - 0.0294
     - 0.039
     - 0.714
     - 1
   * - L23
     - bb
     - 555
     - oligotrophic
     - 2
     - giop
     - 0.429
     - -0.0181
     - 0.0278
     - 0.857
     - 1
   * - L23
     - bb
     - 670
     - all
     - 1
     - expb_pow
     - 0.7
     - 0.0325
     - 0.0787
     - 0.85
     - 1
   * - L23
     - bb
     - 670
     - all
     - 2
     - giop
     - 0.3
     - -0.103
     - 0.117
     - 0.1
     - 0.45
   * - L23
     - bb
     - 670
     - mesotrophic
     - 1
     - expb_pow
     - 0.846
     - 0.0197
     - 0.0708
     - 0.846
     - 1
   * - L23
     - bb
     - 670
     - mesotrophic
     - 2
     - giop
     - 0.154
     - -0.109
     - 0.127
     - 0.0769
     - 0.385
   * - L23
     - bb
     - 670
     - oligotrophic
     - 1
     - giop
     - 0.571
     - -0.0908
     - 0.0999
     - 0.143
     - 0.571
   * - L23
     - bb
     - 670
     - oligotrophic
     - 2
     - expb_pow
     - 0.429
     - 0.0567
     - 0.0936
     - 0.857
     - 1
   * - L23
     - bb_p
     - 555
     - all
     - 1
     - expb_pow
     - 0.55
     - 0.0499
     - 0.0807
     - 0.8
     - 1
   * - L23
     - bb_p
     - 555
     - all
     - 2
     - giop
     - 0.45
     - -0.0492
     - 0.0735
     - 0.6
     - 0.9
   * - L23
     - bb_p
     - 555
     - mesotrophic
     - 1
     - expb_pow
     - 0.538
     - 0.0367
     - 0.0732
     - 0.846
     - 1
   * - L23
     - bb_p
     - 555
     - mesotrophic
     - 2
     - giop
     - 0.462
     - -0.0508
     - 0.0757
     - 0.462
     - 0.846
   * - L23
     - bb_p
     - 555
     - oligotrophic
     - 1
     - expb_pow
     - 0.571
     - 0.0748
     - 0.0949
     - 0.714
     - 1
   * - L23
     - bb_p
     - 555
     - oligotrophic
     - 2
     - giop
     - 0.429
     - -0.0461
     - 0.0695
     - 0.857
     - 1
   * - L23
     - bb_p
     - 670
     - all
     - 1
     - expb_pow
     - 0.75
     - 0.0667
     - 0.141
     - 0.85
     - 1
   * - L23
     - bb_p
     - 670
     - all
     - 2
     - giop
     - 0.25
     - -0.166
     - 0.206
     - 0.1
     - 0.45
   * - L23
     - bb_p
     - 670
     - mesotrophic
     - 1
     - expb_pow
     - 0.846
     - 0.0411
     - 0.121
     - 0.846
     - 1
   * - L23
     - bb_p
     - 670
     - mesotrophic
     - 2
     - giop
     - 0.154
     - -0.163
     - 0.206
     - 0.0769
     - 0.385
   * - L23
     - bb_p
     - 670
     - oligotrophic
     - 1
     - expb_pow
     - 0.571
     - 0.116
     - 0.18
     - 0.857
     - 1
   * - L23
     - bb_p
     - 670
     - oligotrophic
     - 2
     - giop
     - 0.429
     - -0.171
     - 0.207
     - 0.143
     - 0.571


.. LEADERBOARD_END

.. toctree::
   :maxdepth: 1
   :glob:

   */*

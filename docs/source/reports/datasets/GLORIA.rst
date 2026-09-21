========================
Dataset profile — GLORIA
========================

In one paragraph
----------------

**GLORIA** has been fitted by 4 algorithm(s): ``expb_pow``, ``expb_pow2``, ``expb_pow2flat``, ``expb_powflex``. It scores a_dg at the reference bands. No pair of algorithms separated on any contest here, so the page reports them as indistinguishable rather than ranking them — see the head-to-head table on the sweep pages.

What this dataset can score
---------------------------

A dataset can only score what it carries truth for; a component with no truth here is absent rather than failing.

.. list-table:: What this dataset can score
   :header-rows: 1
   :widths: auto

   * - algorithm
     - state
     - attempted
     - fits ok
     - scored pairs
   * - ``expb_pow``
     - scored
     - 100
     - 21
     - 12
   * - ``expb_pow2``
     - scored
     - 100
     - 21
     - 12
   * - ``expb_pow2flat``
     - scored
     - 100
     - 21
     - 12
   * - ``expb_powflex``
     - scored
     - 100
     - 21
     - 12

Ranked contests
---------------

Where no pair of algorithms separated, the ``ranking`` column says *indistinguishable* instead of printing an order the data do not support.

.. list-table:: GLORIA — who leads where
   :header-rows: 1
   :widths: auto

   * - component
     - ref_wave
     - stratum
     - fit_method
     - rank
     - ranking
     - algorithm
     - mae
     - bias
     - win_frac
     - caveat
   * - a_dg
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - expb_pow2
     - 1.01
     - 0.194
     - 0.639
     - CDOM_vs_adg
   * - a_dg
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - expb_powflex
     - 1.06
     - 0.0989
     - 0.569
     - CDOM_vs_adg
   * - a_dg
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 1
     - 0.289
     - 0.431
     - CDOM_vs_adg
   * - a_dg
     - 440
     - all
     - chisq
     - —
     - indistinguishable
     - expb_pow2flat
     - 1
     - 0.301
     - 0.361
     - CDOM_vs_adg
   * - a_dg
     - 440
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - expb_powflex
     - 1
     - 0.18
     - 0.667
     - CDOM_vs_adg
   * - a_dg
     - 440
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - expb_pow2
     - 0.985
     - 0.327
     - 0.6
     - CDOM_vs_adg
   * - a_dg
     - 440
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.958
     - 0.519
     - 0.4
     - CDOM_vs_adg
   * - a_dg
     - 440
     - eutrophic
     - chisq
     - —
     - indistinguishable
     - expb_pow2flat
     - 0.945
     - 0.523
     - 0.333
     - CDOM_vs_adg
   * - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - expb_pow2
     - 1.39
     - -0.108
     - 0.667
     - CDOM_vs_adg
   * - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - expb_powflex
     - 1.41
     - -0.116
     - 0.625
     - CDOM_vs_adg
   * - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 1.41
     - -0.116
     - 0.375
     - CDOM_vs_adg
   * - a_dg
     - 440
     - mesotrophic
     - chisq
     - —
     - indistinguishable
     - expb_pow2flat
     - 1.39
     - -0.11
     - 0.333
     - CDOM_vs_adg
   * - a_dg
     - 440
     - unknown
     - chisq
     - —
     - indistinguishable
     - expb_pow2
     - 0.621
     - 0.479
     - 0.667
     - CDOM_vs_adg
   * - a_dg
     - 440
     - unknown
     - chisq
     - —
     - indistinguishable
     - expb_pow
     - 0.62
     - 0.62
     - 0.556
     - CDOM_vs_adg
   * - a_dg
     - 440
     - unknown
     - chisq
     - —
     - indistinguishable
     - expb_pow2flat
     - 0.657
     - 0.657
     - 0.444
     - CDOM_vs_adg
   * - a_dg
     - 440
     - unknown
     - chisq
     - —
     - indistinguishable
     - expb_powflex
     - 0.753
     - 0.303
     - 0.333
     - CDOM_vs_adg

Retrieval success
-----------------

The gap between spectra attempted and spectra scored is a statement about the **models**, not about the data or the software: ``frac_out_of_scope`` means the spectrum sits outside the model family's regime.

.. list-table:: GLORIA — why rows were or were not scored
   :header-rows: 1
   :widths: auto

   * - algorithm
     - fit_method
     - n_attempted
     - frac_ok
     - frac_poor_fit
     - frac_out_of_scope
     - frac_fit_failed
     - chi2_nu_median
     - rel_misfit_median_all
   * - expb_pow2
     - chisq
     - 100
     - 0.21
     - 0.16
     - 0.63
     - 0
     - 0.463
     - 0.595
   * - expb_powflex
     - chisq
     - 100
     - 0.21
     - 0.16
     - 0.63
     - 0
     - 0.46
     - 0.595
   * - expb_pow
     - chisq
     - 100
     - 0.21
     - 0.16
     - 0.63
     - 0
     - 0.46
     - 0.594
   * - expb_pow2flat
     - chisq
     - 100
     - 0.21
     - 0.16
     - 0.63
     - 0
     - 0.462
     - 0.595

By water type
-------------

.. list-table:: GLORIA — per trophic stratum
   :header-rows: 1
   :widths: auto

   * - stratum
     - component
     - ref_wave
     - algorithm
     - rank
     - mae
     - win_frac
     - frac_ok
   * - eutrophic
     - a_dg
     - 440
     - expb_powflex
     - —
     - 1
     - 0.667
     - 0.136
   * - eutrophic
     - a_dg
     - 440
     - expb_pow2
     - —
     - 0.985
     - 0.6
     - 0.136
   * - eutrophic
     - a_dg
     - 440
     - expb_pow
     - —
     - 0.958
     - 0.4
     - 0.136
   * - eutrophic
     - a_dg
     - 440
     - expb_pow2flat
     - —
     - 0.945
     - 0.333
     - 0.136
   * - mesotrophic
     - a_dg
     - 440
     - expb_pow2
     - —
     - 1.39
     - 0.667
     - 0.857
   * - mesotrophic
     - a_dg
     - 440
     - expb_powflex
     - —
     - 1.41
     - 0.625
     - 0.857
   * - mesotrophic
     - a_dg
     - 440
     - expb_pow
     - —
     - 1.41
     - 0.375
     - 0.857
   * - mesotrophic
     - a_dg
     - 440
     - expb_pow2flat
     - —
     - 1.39
     - 0.333
     - 0.857
   * - unknown
     - a_dg
     - 440
     - expb_pow2
     - —
     - 0.621
     - 0.667
     - 0.222
   * - unknown
     - a_dg
     - 440
     - expb_pow
     - —
     - 0.62
     - 0.556
     - 0.222
   * - unknown
     - a_dg
     - 440
     - expb_pow2flat
     - —
     - 0.657
     - 0.444
     - 0.222
   * - unknown
     - a_dg
     - 440
     - expb_powflex
     - —
     - 0.753
     - 0.333
     - 0.222

Head-to-head
------------

.. list-table:: GLORIA — pairwise verdicts
   :header-rows: 1
   :widths: auto

   * - component
     - ref_wave
     - model_a
     - model_b
     - n_paired
     - delta_mae
     - d_lo
     - d_hi
     - verdict
   * - a_dg
     - 440
     - expb_pow
     - expb_pow2
     - 12
     - -0.00603
     - -0.174
     - 0.108
     - underpowered
   * - a_dg
     - 440
     - expb_pow
     - expb_pow2flat
     - 12
     - -0.00101
     - -0.0309
     - 0.0217
     - indistinguishable
   * - a_dg
     - 440
     - expb_pow
     - expb_powflex
     - 12
     - -0.058
     - -0.36
     - 0.191
     - underpowered
   * - a_dg
     - 440
     - expb_pow2
     - expb_pow2flat
     - 12
     - 0.00502
     - -0.111
     - 0.182
     - underpowered
   * - a_dg
     - 440
     - expb_pow2
     - expb_powflex
     - 12
     - -0.052
     - -0.237
     - 0.084
     - underpowered
   * - a_dg
     - 440
     - expb_pow2flat
     - expb_powflex
     - 12
     - -0.057
     - -0.392
     - 0.182
     - underpowered
   * - a_dg
     - 440
     - expb_pow
     - expb_pow2
     - 3
     - -0.000549
     - -0.134
     - 0.0849
     - underpowered
   * - a_dg
     - 440
     - expb_pow
     - expb_pow2flat
     - 3
     - -0.0367
     - -0.0853
     - 0.0043
     - indistinguishable
   * - a_dg
     - 440
     - expb_pow
     - expb_powflex
     - 3
     - -0.133
     - -0.328
     - 0.000739
     - underpowered
   * - a_dg
     - 440
     - expb_pow2
     - expb_pow2flat
     - 3
     - -0.0361
     - -0.085
     - 0.00991
     - indistinguishable
   * - a_dg
     - 440
     - expb_pow2
     - expb_powflex
     - 3
     - -0.132
     - -0.413
     - 0.132
     - underpowered
   * - a_dg
     - 440
     - expb_pow2flat
     - expb_powflex
     - 3
     - -0.0962
     - -0.328
     - 0.123
     - underpowered
   * - a_dg
     - 440
     - expb_pow
     - expb_pow2
     - 5
     - -0.027
     - -0.423
     - 0.222
     - underpowered
   * - a_dg
     - 440
     - expb_pow
     - expb_pow2flat
     - 5
     - 0.0133
     - -0.00257
     - 0.0344
     - indistinguishable
   * - a_dg
     - 440
     - expb_pow
     - expb_powflex
     - 5
     - -0.0422
     - -0.847
     - 0.402
     - underpowered
   * - a_dg
     - 440
     - expb_pow2
     - expb_pow2flat
     - 5
     - 0.0403
     - -0.217
     - 0.457
     - underpowered
   * - a_dg
     - 440
     - expb_pow2
     - expb_powflex
     - 5
     - -0.0152
     - -0.424
     - 0.192
     - underpowered
   * - a_dg
     - 440
     - expb_pow2flat
     - expb_powflex
     - 5
     - -0.0555
     - -0.881
     - 0.399
     - underpowered
   * - a_dg
     - 440
     - expb_pow
     - expb_pow2
     - 4
     - 0.02
     - -0.00031
     - 0.0441
     - indistinguishable
   * - a_dg
     - 440
     - expb_pow
     - expb_pow2flat
     - 4
     - 0.0163
     - -0.000303
     - 0.036
     - indistinguishable
   * - a_dg
     - 440
     - expb_pow
     - expb_powflex
     - 4
     - 6.36e-05
     - 3.9e-09
     - 0.00014
     - indistinguishable
   * - a_dg
     - 440
     - expb_pow2
     - expb_pow2flat
     - 4
     - -0.00375
     - -0.00815
     - -1.73e-05
     - indistinguishable
   * - a_dg
     - 440
     - expb_pow2
     - expb_powflex
     - 4
     - -0.02
     - -0.044
     - 0.000285
     - indistinguishable
   * - a_dg
     - 440
     - expb_pow2flat
     - expb_powflex
     - 4
     - -0.0162
     - -0.0358
     - 0.000303
     - indistinguishable

See also
--------

Every column on this page is defined on the :doc:`/reports/glossary` page — including which value counts as *perfect* for each metric, the three different ``n`` denominators, and what the tie and calibration verdicts do and do not claim. For what the models are (rather than how they scored) see :doc:`/models`; for the data and its truth see :doc:`/datasets`.

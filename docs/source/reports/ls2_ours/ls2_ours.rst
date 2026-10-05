.. _ls2_ours:

======================================================
Our own LS2: the re-derived algorithm, and LS2 vs BING
======================================================

:Task: ls2 task 14
:Script: ``ioptics/runs/prototypes/ls2/ours_report.py`` (every number and
   table on this page)
:Pieces: Kd network ``ocpy.ls2.kd_l23`` (task 11, :ref:`ls2_kd_l23`); a/bb
   tables (task 12, :ref:`ls2_refit_ab`); κ (task 13, :ref:`ls2_refit_kappa`);
   together in ``ocpy/data/LS2/LS2_LUT_L23_abk_v1.npz``
:Held out: 498 IOP scenarios no re-derived piece was fitted to (the split of
   ``ioptics.kd_net``); every comparison involving a re-derived piece is
   quoted on them

The headline: rung (i)'s biases
-------------------------------

Rung (i) gives LS2 everything as truth: noise-free L23 X=4 ``Rrs``, true
⟨Kd⟩₁ and ``b_p``.  What error remains is the tables'.  Planning measured
``a`` +2.6%, ``bb`` +9.8%, ``bb_p`` +24% (θs = 0°).  On the held-out
scenarios, at θs = 0° (median relative error, 400–750 nm):

* **published**: ``a`` +2.9%, ``bb`` +8.9%, ``bb_p``
  +20.4%; κ unavailable on 25.3%
  of cells;
* **our LS2**: ``a`` -0.4%, ``bb`` +3.9%, ``bb_p``
  +7.0%; κ unavailable on
  0.2%.

**The re-derivation removes the ``a`` bias and most of the ``bb`` and
``bb_p`` biases.**  The step through ``refit a/bb + published κ`` (``a``
-0.5%, ``bb`` +7.0%, ``bb_p`` +14.2%) shows
which piece did what.  The a/bb refit takes out ``a``, and κ then removes
44.9% of what is left in ``bb`` and 50.2% in
``bb_p``.  What remains is largest at θs = 0° (``bb`` +3.9%, ``bb_p``
+7.0%), which is exactly where task 13 found κ off its pooled
cubic.  At θs = 30° it is -0.8% and
-1.2%.  X=4's chlorophyll fluorescence, which no κ here
models, is a second candidate; this page does not separate the two.

**How much of the ``a`` bias was illumination bookkeeping.**  Entering the
*published* tables at L23's effective μw (ls2 Q9), with no refit, takes ``a``
from +2.9% to -0.8% at θs = 0°: a shift of 3.6 points, **more than the whole bias**: the ``a`` bias is entirely illumination bookkeeping, and entering at μ_eff overshoots to -0.8%.  The refit lands at
-0.4%.  At θs = 60°, where
Snell's μw and the effective one nearly agree, the published ``a`` error is
already -0.5%.  The refit's own ``c0`` matches 1/μ_eff rather
than 1/μw (task 12): the bookkeeping is absorbed into the re-derived
coefficients, which is why our LS2 runs at Snell's μw.

.. csv-table:: Rung (i), noise-free L23 X=4, held-out scenarios: median relative error per table configuration and zenith; a_nw only where a_nw/a ≥ 0.1.
   :file: ours_headline.csv
   :header-rows: 1
   :widths: auto

The ladder on held-out spectra
------------------------------

The same ladder as the sweep pages, with the PACE noise form, run on the 498
held-out scenarios only (sweep ``ls2_l23_x4_heldout_v1``), so a published rung
and its re-derived twin are compared on spectra neither saw.
``ls2r_iii_l23`` takes Kd from our own L23 network and appears only here
(ls2 Q39).  Operational LS2 (rung iii: a Kd network and OC4v4 ``b_p``) has
``a(440)`` mae 15.2% with the authors' tables and
PACE network, 14.8% with our tables and their
network, and 4.1% with our tables and our
network.

.. csv-table:: Held-out ladder (noisy Rrs): one row per rung.
   :file: ours_heldout_ladder.csv
   :header-rows: 1
   :widths: auto

.. csv-table:: Held-out: each published rung beside its re-derived twin (median ratio and mae per cell).
   :file: ours_heldout_rederived.csv
   :header-rows: 1
   :widths: auto

LS2 against BING
----------------

RT-A's MCMC BING (``expb_pow_hyb_ramfl``, the rung whose physics matches X=4, ls2
Q36), paired with LS2 cell by cell: same spectrum, same wavelength, both
retrievals finite and positive.  BING spectra with status ``ok``; LS2 spectra
``ok`` or ``poor_fit``, whose finite cells are scored (ls2 Q31).  ``a_nw``
only where ``a_nw/a`` ≥ 0.1.  ``ls2_win_frac`` is the share of paired cells
where LS2 is closer to truth.  The two sweeps used independent noise draws of
the same form (ls2 Q15), so this pairs spectra, not noise realizations.

On the held-out spectra, across 400–750 nm:

* **our operational LS2** (``ls2r_iii_l23``: our network, OC4v4 ``b_p``, our
  tables): ``a`` 2.5% vs 2.3% (LS2 closer on 29.7% of cells) → **BING**; ``a_nw`` 10.0% vs 10.8% (LS2 closer on 57.6% of cells) → **LS2**; ``bb`` 34.2% vs 6.7% (LS2 closer on 23.0% of cells) → **BING**; ``bb_p`` 54.7% vs 13.3% (LS2 closer on 23.4% of cells) → **BING**;
* **our LS2 with true inputs** (``ls2r_i``): ``a`` 0.9% vs 2.3% (LS2 closer on 48.4% of cells) → **LS2**; ``a_nw`` 3.5% vs 10.8% (LS2 closer on 82.3% of cells) → **LS2**; ``bb`` 33.5% vs 6.7% (LS2 closer on 25.5% of cells) → **BING**; ``bb_p`` 52.5% vs 13.3% (LS2 closer on 26.1% of cells) → **BING**;
* **published operational LS2** (``ls2_iii``): ``a`` 19.3% vs 2.3% (LS2 closer on 12.8% of cells) → **BING**; ``a_nw`` 32.4% vs 10.7% (LS2 closer on 25.1% of cells) → **BING**; ``bb`` 37.4% vs 6.6% (LS2 closer on 14.7% of cells) → **BING**; ``bb_p`` 67.0% vs 13.0% (LS2 closer on 15.0% of cells) → **BING**.

**Why ``bb`` and ``bb_p`` go to BING.**  LS2 is closed-form band by band, so
the noise in each band's ``Rrs`` goes straight into that band's ``bb``:
PACE noise is about 11% of ``Rrs`` at 555 nm and about 50% at 670 nm.  BING
fits one smooth spectral model to the whole spectrum, which averages the
noise.  At 555 nm, our ``bb`` with true inputs is off by
11.2%, against BING's 4.7%;
across 400–750 nm the red bands dominate LS2's error.  The noise-free headline
above is where the tables themselves are measured; this is LS2 as it would
run.

**On absorption, our LS2 is competitive.**  With our own Kd network, over
400–750 nm, its ``a`` is 2.5%
against BING's 2.3%, and
its ``a_nw`` 10.0% against
10.8%.  At 440 nm it is
ahead on both (``a`` 4.1%
against 5.8%).  With true
inputs, it beats BING on ``a`` and ``a_nw`` everywhere.  The published
operational LS2 loses everything.

**Where LS2 forfeits, whatever its tables.**  LS2 returns ``a``, ``a_nw``,
``bb`` and ``bb_p``, and nothing else.  It has **no** ``a_ph`` and **no**
``a_dg``: there is no decomposition to score, and that absence is the point
of the comparison, not a gap in it.  BING returns both, though not well:
RT-A's ``a_ph(440)`` mae is 0.846 for this rung, and ``a_dg(440)``
0.261 (:doc:`/reports/ls2_l23_x4_v1/ls2_ladder`).  LS2 also needs a Kd it cannot get from ``Rrs`` alone, which
is why the operational rungs exist.

.. csv-table:: Held-out spectra: LS2 rungs against MCMC BING, paired by cell, over 400–750 nm and at the reference band.
   :file: ours_vs_bing_heldout.csv
   :header-rows: 1
   :widths: auto

.. csv-table:: All 3,320 spectra (re-derived rungs partly in-sample: their tables were fitted on 70% of these scenarios).
   :file: ours_vs_bing_all.csv
   :header-rows: 1
   :widths: auto

Limits
------

* Everything here is L23.  Task 11 found real water (PANGAEA) attenuating
  more than L23 predicts from the same ``Rrs``, and the re-derived tables are
  as transferable as L23 is realistic.
* κ's dependence on the sun (task 13) and Chl fluorescence (X=4) remain.
* ``b/a`` above L23's 14 (turbid water) and θs above 60° are extrapolations
  of the re-derived tables.

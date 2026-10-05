.. _ls2_debrief:

=============
LS2 — debrief
=============

:Task: ls2 task 15
:Script: ``ioptics/runs/prototypes/ls2/debrief.py`` (every number on this page)
:Built on: :ref:`ls2_ours` (task 14), the held-out X=4 ladder
   (``ls2_l23_x4_heldout_v1``), and RT-A's MCMC BING

LS2 (Loisel et al. 2018) was brought into IOPtics as the first **direct**
algorithm.  It has no fit, no likelihood, and returns totals only.  It was run
as a ladder of inputs, so that what LS2 costs could be separated from what
its inputs cost, and then rebuilt from L23 to see how much of its error was
avoidable.

1. Totals against decomposition
-------------------------------

LS2 returns the totals ``a`` and ``bb`` and their non-water parts ``a_nw``
and ``bb_p``.  It returns **no** ``a_ph`` and **no** ``a_dg``.  BING returns
all six.  On L23 X=4 (held-out spectra, MCMC BING ``expb_pow_hyb_ramfl``):

* **Absorption totals: LS2 is as good or better.**  At 440 nm, our LS2 with
  true inputs has ``a`` mae 1.2% against BING's
  5.9%.  Operationally, with our L23 Kd network,
  it is 4.1% against
  5.8%.
* **Backscattering totals: BING is better by far.**  At 555 nm ``bb`` mae is
  11.2% (LS2, true inputs) against
  4.7%.  LS2 inverts band by band and
  inherits each band's Rrs noise; BING fits one model to the whole spectrum.
* **The decomposition.**  BING's ``a_ph(440)`` mae is 84.6% and
  its ``a_dg(440)`` 26.1%, against 5.9% for its own
  total ``a(440)``.  The split is where BING's error lives.  An algorithm that
  declines to split, as LS2 does, gives up those two numbers and their large
  errors.  Its ``a_nw`` is in effect BING's ``a_dg + a_ph`` without the split:
  1.6% for LS2 against
  7.4% for BING at 440 nm.

So the trade is real and one-sided per component.  For totals of absorption,
LS2 (with a good Kd) is competitive or better.  For backscattering, the
full-spectrum fit wins.  For the decomposition, LS2 has nothing to offer and
says so, as an explicit "not applicable", not a missing row.

2. What the two side chains cost
--------------------------------

Measured on the held-out X=4 spectra (PACE noise), as the change in mae when
one true input is replaced by its operational estimate.

* **The Chl/b_p chain is cheap in absolute terms.**  ``b_p`` enters LS2 only
  through η = b_w/(b_p + b_w), which picks the table row.  Replacing true
  ``b_p`` with OC4v4 chlorophyll and ``bp_from_chla`` costs ``a(440)``
  -0.1 pp and ``bb(555)`` +0.8 pp
  with the published tables, and +1.1 pp and
  +1.5 pp with ours.  Against our much smaller error
  with true inputs, that takes ``a(440)`` from
  1.2% to 2.3%: the
  re-derived tables are more sensitive to a wrong η than the published ones,
  whose error elsewhere dwarfs it.
* **The Kd chain is the expensive one, and how expensive depends entirely on
  the network.**  Replacing true ⟨Kd⟩₁ costs ``a(440)``:
  +13.2 pp with the authors' PACE v2.3 network,
  +6.3 pp with their MODIS v1.3, and
  +1.8 pp with our L23-trained network.  ``a`` scales
  as Kd, so a Kd error is an ``a`` error.  The Kd-noise ladder on the sweep
  pages gives the slope.

.. csv-table:: Side-chain costs on the held-out X=4 spectra: mae before and after each replacement, per cell, and the cost in percentage points.
   :file: debrief_side_chains.csv
   :header-rows: 1
   :widths: auto

3. What the re-derivation changed
---------------------------------

Tasks 10–13 rebuilt LS2's three learned pieces from L23: the Kd network, the
a/bb tables and κ.

* **Rung (i), noise-free, θs = 0°, held-out**: ``a`` +2.9%
  → -0.4%; ``bb`` +8.9% →
  +3.9%; ``bb_p`` +20.4% →
  +7.0%.  The ``a`` bias was illumination bookkeeping:
  L23's sky is not a Snell beam.  Of ``bb``'s, the a/bb refit removed
  1.9 points and κ 3.2, and 3.9
  remain at θs = 0° (κ's sun dependence or X=4 fluorescence; not separated).
* **κ availability**: unavailable on 25.3% of cells with
  the published table, 0.2% with ours.
* **Operational ``a(440)``**: 15.2% published
  (PACE network, published tables), 14.8% with our
  tables and the same network, 4.1% with our
  tables and our network.  Almost all of the gain is the Kd network.
* **What it did not change**: the band-by-band noise sensitivity of ``bb``
  and ``bb_p``, which is structural, and the absence of a decomposition,
  which is the design.

Caveats
-------

* Everything is L23.  The re-derived pieces were fitted on L23 and scored on
  held-out L23 scenarios.  Real water (PANGAEA) attenuates more than L23
  predicts from the same Rrs (task 11), so our operational numbers are L23
  numbers.  The leaderboard therefore carries only the published operational
  LS2 (ls2 Q41).
* κ's sun dependence and Chl fluorescence (X=4) remain uncorrected.

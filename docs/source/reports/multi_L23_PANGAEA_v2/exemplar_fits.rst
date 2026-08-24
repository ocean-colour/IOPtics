====================================
Exemplar fits — multi_L23_PANGAEA_v2
====================================

:Sweep: multi_L23_PANGAEA_v2
:Generated: 2026-08-08T10:18:43Z
:ioptics: 0.0.dev0@e0e6729
:bing: 0.0.dev0@f242b0e
:ocpy: 0.1.0@3aed28a
:design_doc: 0.16
:implementation_doc: 0.23

Overview
--------

Every other figure in this report describes a **population** of retrievals. This page shows 10 individual fits from sweep ``multi_L23_PANGAEA_v2`` — the question an ocean-colour reader asks as soon as a summary statistic looks wrong: *show me a spectrum where it failed*.

**How they were chosen.** Fit quality is ranked by distance from :math:`\chi^2_\nu = 1` in log space, and the page carries the **best** (the fit nearest χ²ᵥ = 1), the **worst** (the *largest* χ²ᵥ, i.e. the most under-fit) and the **eight** nearest the median. Ranking the *selection* by χ²ᵥ ascending would name the most **over-fit** spectrum in the sweep its best one: χ²ᵥ below 1 means the model is chasing noise, and on GLORIA χ²ᵥ moved by a factor of 5 when the assumed error floor changed while the fits themselves did not move at all. So both tails count as worse than the middle for *choosing* the exemplars — but "worst" names the under-fit tail specifically, because that is what the word conveys. Every panel prints its own χ²ᵥ (above 5 a fit is not considered a solution at all). Where several algorithms fit the same observation it is ranked by their median χ²ᵥ, because the panel shows all of them at once.

**How they are ordered.** Panels run left-to-right, top-to-bottom by observed Rrs peak wavelength — clear water peaks in the blue, turbid water in the green-red (the packaged clear/turbid threshold is 560 nm — a poor fit whose peak sits redward of it is recorded as ``out_of_scope`` rather than as a failure, because the model family does not claim that water). Reading the grid in order therefore shows how the retrieval degrades as the water gets more turbid, which is the failure axis of every open-ocean parameterization applied to the coast. The relative misfit ``Δ`` beside each χ²ᵥ is :math:`\mathrm{median}(|M-O|/O)` — it owes nothing to the assumed noise model, so it is the number to trust when χ²ᵥ and it disagree. Both are defined on the :doc:`/reports/glossary` page.

Exemplar fits
-------------

Observed Rrs with every algorithm's modelled Rrs laid over it, one panel per exemplar observation. Rrs is on a **linear** axis (unlike the IOP spectra elsewhere) because hyperspectral red tails routinely cross zero, which a log axis would silently drop — the grey rule marks zero.

.. figure:: exemplar_fits.png
   :width: 90%
   :alt: 10 exemplar fits, clear (top-left) to turbid (bottom-right). Black dots are the observed Rrs; each coloured line is one algorithm's modelled Rrs, its legend entry carrying that fit's own χ²ᵥ and relative misfit.

   10 exemplar fits, clear (top-left) to turbid (bottom-right). Black dots are the observed Rrs; each coloured line is one algorithm's modelled Rrs, its legend entry carrying that fit's own χ²ᵥ and relative misfit.

The exemplars
-------------

**What these 10 fits are.** 1 of the 10 has a median χ²ᵥ above 5, so by this package's own threshold it is **not a solution** — the exemplars are not a gallery of successes, and on a dataset the model family struggles with, the median fit is expected to be one of the failures. Recorded fit status across these observations and algorithms: ``ok`` 27, ``poor_fit`` 3.

.. list-table:: The exemplar observations, clear → turbid
   :header-rows: 1
   :widths: auto

   * - dataset
     - obs_id
     - role
     - χ²ᵥ (median)
     - rel. misfit
     - Rrs peak [nm]
   * - L23
     - ``1586``
     - best
     - 1
     - 3%
     - 400
   * - L23
     - ``647``
     - median
     - 1.66
     - 4%
     - 400
   * - L23
     - ``1122``
     - median
     - 1.66
     - 4%
     - 400
   * - L23
     - ``1904``
     - median
     - 1.66
     - 4%
     - 400
   * - L23
     - ``2429``
     - median
     - 1.66
     - 4%
     - 405
   * - L23
     - ``1553``
     - median
     - 1.66
     - 4%
     - 405
   * - L23
     - ``1246``
     - median
     - 1.66
     - 5%
     - 405
   * - PANGAEA
     - ``16285``
     - worst
     - 436
     - 76%
     - 411
   * - L23
     - ``825``
     - median
     - 1.66
     - 4%
     - 425
   * - L23
     - ``1838``
     - median
     - 1.66
     - 5%
     - 430

Rrs closure — best fit (obs 1586 of L23)
----------------------------------------

Closure residuals for the same fit as above, which is the view that shows *where* in the spectrum the model fails rather than by how much overall: a residual that is flat but offset is a different fault from one that swings sign across the green.

.. figure:: closure_L23_1586.png
   :width: 90%
   :alt: ``Rrs_obs − Rrs_model`` for observation ``1586``, per algorithm, with each algorithm's χ²ᵥ in the legend.

   ``Rrs_obs − Rrs_model`` for observation ``1586``, per algorithm, with each algorithm's χ²ᵥ in the legend.

Rrs closure — worst fit (obs 16285 of PANGAEA)
----------------------------------------------

Closure residuals for the same fit as above, which is the view that shows *where* in the spectrum the model fails rather than by how much overall: a residual that is flat but offset is a different fault from one that swings sign across the green.

.. figure:: closure_PANGAEA_16285.png
   :width: 90%
   :alt: ``Rrs_obs − Rrs_model`` for observation ``16285``, per algorithm, with each algorithm's χ²ᵥ in the legend.

   ``Rrs_obs − Rrs_model`` for observation ``16285``, per algorithm, with each algorithm's χ²ᵥ in the legend.

Not shown for this sweep
------------------------

The figure set is derived from what this sweep actually measured, so a panel with no data behind it is omitted rather than published blank. For the record, this page leaves out:

* the posterior corner plots — they need an MCMC fit with a saved chain, and this sweep has none (χ² fits carry a covariance, not a chain).

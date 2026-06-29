.. IOPtics documentation master file

==========================================
IOPtics: comparing IOP retrieval methods
==========================================

**IOPtics** is a Python package for testing and evaluating a wide range of
**inherent optical property (IOP)** retrieval algorithms. It drives the
retrieval engine (`BING <https://github.com/ocean-colour/bing>`_) over common
datasets loaded through `ocpy <https://github.com/ocean-colour/ocpy>`_, then
generates uniform metrics, diagnostics, and reports to share with the ocean
optics community.

.. note::

   IOPtics is in active development. Through **Stage 2** the vertical slice runs
   end to end: the data contracts (:class:`~ioptics.records.PreparedRecord`,
   :class:`~ioptics.records.RetrievalResult`,
   :class:`~ioptics.records.ComponentFit`) and YAML sweep config
   (:mod:`ioptics.config`); the dataset-agnostic prep over L23
   (:mod:`ioptics.datasets`, :mod:`ioptics.noise`, :mod:`ioptics.prep`); the
   declarative algorithm registry (:mod:`ioptics.algorithms`, seeded with
   ``expb_pow`` and ``giop``); the least-squares run/evaluate engine wrapping
   BING (:mod:`ioptics.run`, :mod:`ioptics.evaluate`); and the long/tidy results
   tables + provenance (:mod:`ioptics.io`, :mod:`ioptics.provenance`). The MCMC
   subset, metrics, diagnostics, and reporting layers are next.

What IOPtics does
-----------------

* **Uniform data prep** — generalizes BING's L23 prep to any dataset (L23,
  PANGAEA, GLORIA) on its native wavelength grid, attaching ``Rrs`` uncertainty
  and truth IOPs where available.
* **A declarative algorithm registry** — each algorithm is a serializable
  configuration (``a_nw``/``bb_nw`` models, priors, RT toggles, fit method),
  seeded with ``expb_pow`` and ``giop`` in tandem.
* **A run/sweep driver** — least-squares across the full sweep, MCMC on a
  subset, with reconstructed ``a``/``bb`` ± uncertainty.
* **Uniform metrics & diagnostics** — log-space accuracy, ``Rrs`` closure,
  AIC/BIC/ΔBIC, coverage, wins; Taylor/Target/corner/residual figures.
* **Reporting** — a standard figure/table set, a persistent leaderboard, and
  this accumulating documentation site, all provenance-stamped.

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   installation
   reports/index
   api/index

Indices and tables
-------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

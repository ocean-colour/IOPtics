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

   IOPtics is in early development (**Stage 0** — scaffolding & contracts). The
   package skeleton, the load-bearing data contracts
   (:class:`~ioptics.records.PreparedRecord`,
   :class:`~ioptics.records.RetrievalResult`,
   :class:`~ioptics.records.ComponentFit`), and the YAML sweep-config surface
   (:mod:`ioptics.config`) are in place; the data, retrieval, metrics, and
   reporting layers are being built out stage by stage.

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

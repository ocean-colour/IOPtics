==========
IOP models
==========

Each **algorithm** in IOPtics is a declarative :class:`~ioptics.algorithms.spec.AlgorithmSpec`
(:mod:`ioptics.algorithms`): a choice of non-water **absorption** (:math:`a_{nw}`)
and **backscatter** (:math:`b_{b,nw}`) parameterization, their priors, radiative-
transfer toggles, and a fit method. The forward model reconstructs
:math:`R_{rs}(\lambda)` from the parameters through the engine
(`BING <https://github.com/ocean-colour/bing>`_) and the fit adjusts the
parameters to match the observed :math:`R_{rs}`. All amplitudes are fit in
:math:`\log_{10}` space; the reported IOPs are physical (1/m).

The first sweep runs two algorithms **in tandem** — a full 5-parameter BING model
and a leaner 3-parameter GIOP-style model — so the reports contrast a more
flexible model against a more parsimonious one (the ΔBIC contest below).

``expb_pow`` — the standard 5-parameter BING model
==================================================

The canonical BING parameterization (**k = 5**): an *exponential* CDOM+detritus
absorption plus a *Bricaud* phytoplankton absorption (``ExpBricaud``), and a
*power-law* particulate backscatter (``Pow``).

.. list-table::
   :header-rows: 1
   :widths: 12 20 68

   * - Parameter
     - Controls
     - Meaning
   * - ``Adg``
     - :math:`a_{dg}` amplitude
     - CDOM + detrital absorption magnitude (at the reference wavelength)
   * - ``Sdg``
     - :math:`a_{dg}` slope
     - exponential spectral slope of :math:`a_{dg}(\lambda)`
   * - ``Aph``
     - :math:`a_{ph}` amplitude
     - phytoplankton absorption magnitude (Bricaud spectral shape)
   * - ``Bnw``
     - :math:`b_{bp}` amplitude
     - particulate backscatter magnitude
   * - ``beta``
     - :math:`b_{bp}` slope
     - power-law spectral slope of :math:`b_{bp}(\lambda)`

Because it fits both the amplitude **and** the spectral slope of each component,
``expb_pow`` is the more flexible model — expected to fit :math:`R_{rs}` well,
at the cost of two extra parameters that BIC penalizes. It is the algorithm run
with **MCMC** on a subset, so its posteriors also drive the coverage/uncertainty
diagnostics.

``giop`` — the 3-parameter contrast
====================================

A leaner GIOP-style model (**k = 3**): a ``GIOP`` non-water absorption (a single
exponential-shape amplitude ``Aexp`` for the combined CDOM+detritus term plus a
phytoplankton amplitude ``Aph``) and a ``Lee`` backscatter (amplitude ``Bnw``,
with the spectral slope fixed rather than fit).

.. list-table::
   :header-rows: 1
   :widths: 12 20 68

   * - Parameter
     - Controls
     - Meaning
   * - ``Aexp``
     - :math:`a_{dg}` amplitude
     - combined CDOM+detritus absorption magnitude (fixed slope)
   * - ``Aph``
     - :math:`a_{ph}` amplitude
     - phytoplankton absorption magnitude
   * - ``Bnw``
     - :math:`b_{bp}` amplitude
     - particulate backscatter magnitude (fixed slope, Lee shape)

With fixed spectral slopes, ``giop`` has fewer degrees of freedom — more
parsimonious, and favored by BIC when the extra flexibility of ``expb_pow`` is
not warranted by the data. It is fit by **least squares (LM/χ²)** only.

Why compare them?
=================

The two models span the flexibility/parsimony trade-off central to IOP
inversion. The reports quantify it three ways: **retrieval accuracy** against the
L23 truth (log-space MAE/bias at reference wavelengths), **head-to-head wins**
(which model is closer to truth per spectrum), and **model selection** (ΔBIC —
does the extra flexibility of ``expb_pow`` earn its two parameters?). See
:doc:`reports/index`.

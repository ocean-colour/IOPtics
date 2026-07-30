========
Datasets
========

IOPtics scores IOP-retrieval algorithms against a growing set of ocean-colour
datasets. Each observation is a measured (or simulated) **remote-sensing
reflectance** :math:`R_{rs}(\lambda)` — the spectrum of sunlight leaving the sea
surface (see :doc:`models`). A dataset is *useful for benchmarking* when it also
carries **truth**: the inherent optical properties (IOPs) that actually produced
that reflectance, so a retrieval can be graded against a known answer.

Every dataset is loaded through a small **adapter** (:mod:`ioptics.datasets`)
that returns each observation's :math:`R_{rs}` on the dataset's **native
wavelength grid** (no resampling), its available truth IOPs, and a model for the
:math:`R_{rs}` measurement uncertainty. The metrics layer then compares each
algorithm's retrieval against that truth on the intersection of available bands
and components.

.. list-table:: Datasets in IOPtics
   :header-rows: 1
   :widths: 14 12 20 38 16

   * - Dataset
     - Type
     - Grid
     - Truth available
     - Status
   * - **L23**
     - synthetic
     - Hydrolight, 81 bands (400–700 nm)
     - full spectral IOPs: :math:`a`, :math:`b_b`, :math:`a_{ph}`,
       :math:`a_{dg}`, :math:`b_{bp}`; scalars ``Chl``, ``Sdg``
     - **active** (first sweep)
   * - PANGAEA
     - in situ
     - per-family native λ
     - :math:`a_{ph}`, :math:`a_{dg}` (from ``acdom``), :math:`b_{bp}`
       (from ``bbp``); scalars ``Chl`` (from ``chla``), ``tss``
     - **active** (Stage 6)
   * - GLORIA
     - in situ
     - hyperspectral (350–900 nm @ 1 nm)
     - scalar only: ``a_cdom440`` (as :math:`a_{dg}(440)`), ``Chl`` (from
       ``Chla``), ``TSS``, ``Secchi``
     - **active** (Stage 6)

L23 — Loisel et al. (2023)
==========================

The **L23** dataset is a *synthetic* benchmark: a physics-based radiative-
transfer model (Hydrolight) was run for 3320 hypothetical water bodies spanning
clear open ocean to turbid coastal water, and the resulting reflectance spectra
were recorded on an **81-band, 400–700 nm** grid. Because the water's properties
were *prescribed* rather than measured, L23 provides **exact, noise-free truth**
for every IOP — the ideal first-pass benchmark. IOPtics loads it via
``ocpy.hydrolight.loisel23``.

.. figure:: _static/l23_overview.png
   :width: 100%

   **Left:** the range of phytoplankton loading across the 3320 L23 scenarios,
   shown as the phytoplankton absorption at 440 nm (a stand-in for chlorophyll
   concentration) on a log scale — the dataset spans roughly three orders of
   magnitude, from clear to productive/turbid water. **Right:** eight example
   reflectance spectra; clear water peaks in the blue, and the peak shifts toward
   the green as phytoplankton and particles increase.

- **Scope of the first sweep.** All **3320** L23 spectra (the ``X=1`` elastic
  scenario; ``X=4`` adds Raman + fluorescence, deferred to Stage 6).
- **Truth.** The full spectral decomposition — total absorption :math:`a`, total
  backscatter :math:`b_b`, and the components :math:`a_{ph}` (phytoplankton),
  :math:`a_{dg}` (CDOM + detritus), :math:`b_{bp}` (particulate backscatter) —
  plus scalar chlorophyll ``Chl`` and the :math:`a_{dg}` spectral slope ``Sdg``.
  These are what the accuracy metrics grade against.
- **Noise.** A realistic **PACE** satellite per-band :math:`R_{rs}` uncertainty
  (``ocpy.satellites.pace``) is attached as the fit weight and used to perturb
  the otherwise-perfect spectrum once, so each fit sees a realistic “measurement.”
  (This is why :math:`R_{rs}` dips slightly negative in the red, where the true
  signal is near zero — hence the closure statistics use noise-weighted
  :math:`\chi^2_\nu` rather than a raw reflectance error.)
- **Trophic strata.** Reports also break results out by productivity, binned from
  the truth chlorophyll: **oligotrophic** (low, Chl < 0.1), **mesotrophic**
  (0.1–1.0), and **eutrophic** (high, > 1.0 mg m\ :sup:`-3`) — so one can see
  whether an algorithm does better in clear vs. productive water.

PANGAEA (in situ)
=================

**PANGAEA** is the Valente et al. (2022) V3 compilation of global bio-optical
in-situ data, loaded via ``ocpy.insitu.pangaea``. Each observation is a real,
already-noisy measured :math:`R_{rs}`, so it is **not** perturbed
(``add_noise=False``). Its measured spectral truth — :math:`a_{ph}`,
:math:`a_{dg}` (from measured CDOM+detrital absorption ``acdom``) and
:math:`b_{bp}` (from ``bbp``) — arrives on **each family's own native
wavelength set** and is interpolated onto the :math:`R_{rs}` grid by prep
(flagged in ``truth_interp``). The chlorophyll scalar (HPLC, falling back to
fluorometric) is exposed as ``Chl`` so it is scored alongside L23; ``tss`` is
carried for provenance.

.. note::

   **PANGAEA has no per-band** :math:`R_{rs}` **uncertainty.** The V3 tables
   report no measurement error, so the ``'insitu'`` weighting has nothing to
   build
   ``varRrs`` from. IOPtics therefore falls back to a **flat 5% fractional
   error** (``varRrs = (0.05 · Rrs)²``) and records the honest provenance tag
   ``noise_model='pct:0.05'`` — never ``'insitu'`` — so this assumption is
   explicit in every prepared record, provenance file, and report rather than
   silently masquerading as a measured error.

Enumeration is **permissive**: every observation with at least a handful of
finite :math:`R_{rs}` bands is kept (``min_rrs=5`` by default), even if it lacks
some truth components; the metrics layer then reports per-component coverage.

GLORIA (in situ)
================

**GLORIA** (Lehmann et al. 2023) is a globally representative **hyperspectral**
in-situ dataset (:math:`R_{rs}` on a 350–900 nm, 1 nm grid), loaded via
``ocpy.insitu.gloria``. Unlike PANGAEA it ships a per-band :math:`R_{rs}`
standard deviation, so it uses ``noise='insitu'`` weighting
(``varRrs = Rrs_std²``); the in-situ spectrum is not perturbed.

.. warning::

   **Most GLORIA spectra quote no uncertainty at all.** Only **29%** (2208 of
   7572) carry a finite ``Rrs_std`` at their finite-:math:`R_{rs}` bands;
   **70%** (5338) carry none at any band, and 26 are partial. A fit weighted
   by an all-NaN variance cannot even be started — the bounded least-squares
   solver rejects the initial point — so those spectra are unusable without an
   assumed error. This is what the GLORIA **error floor** below is for, and it
   is why the provenance tag distinguishes a *floored* measured error from a
   wholly *imputed* one.

GLORIA carries **scalar-only** lab truth: CDOM absorption at 440 nm
(``aCDOM440``), chlorophyll (``Chla`` → ``Chl``), total suspended solids
(``TSS`` → ``tss``) and ``Secchi`` depth. There is no measured IOP *spectrum*.
The one IOP comparison GLORIA supports is CDOM at 440 nm, so the adapter exposes
``aCDOM440`` as a single-point :math:`a_{dg}` truth **at 440 nm** (NaN at every
other wavelength). That lets the existing machinery grade a retrieved
:math:`a_{dg}(440)` against it directly and derive ``a_cdom440_truth`` — with one
important qualification:

.. note::

   **CDOM vs.** :math:`a_{dg}` **caveat.** GLORIA reports CDOM absorption only
   (``aCDOM440``), whereas a retrieval's :math:`a_{dg}` is the *combined* CDOM +
   detrital absorption. Comparing the two mixes slightly different quantities.
   Because the dataset is named ``GLORIA``, the metrics layer automatically
   stamps a ``caveat='CDOM_vs_adg'`` on its :math:`a_{dg}` rows
   (``metrics._caveat``), so reports surface the definitional mismatch instead
   of hiding it. PANGAEA's :math:`a_{dg}` (from ``acdom``, which already includes
   detritus) is genuine and carries **no** caveat.

GLORIA error floor
------------------

Where GLORIA does quote an uncertainty it is far tighter than any model's
misfit, which makes :math:`\chi^2_\nu` uninterpretable (thousands, not units).
:mod:`ioptics.prep` therefore applies a **5% fractional error floor** to this
dataset by default (``prep._GLORIA_NOISE_FLOOR``), i.e.
:math:`\sigma \ge 0.05\,|R_{rs}|` at every band, filling in outright where
nothing was measured. The floor makes :math:`\chi^2_\nu` readable; it does
**not** improve any fit, so it announces itself in the record's
``noise_model`` provenance tag:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tag
     - Meaning
   * - ``insitu``
     - measured errors, used as-is (no floor requested)
   * - ``insitu+floor:0.05``
     - at least one band had a measured error; the floor raised the tight ones
   * - ``insitu+imputed:0.05``
     - **nothing** was measured; every weight comes from the 5% assumption

A :math:`\chi^2_\nu` computed against an imputed error is a statement about an
assumed 5%, not about GLORIA's measured uncertainty — the two must not be
pooled without saying so.

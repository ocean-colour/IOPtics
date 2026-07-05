========
Datasets
========

IOPtics scores IOP-retrieval algorithms against a growing set of ocean-colour
datasets. Every dataset is loaded through a small **adapter**
(:mod:`ioptics.datasets`) that returns each observation's remote-sensing
reflectance :math:`R_{rs}(\lambda)` on the dataset's **native wavelength grid**
(no resampling), together with whatever *truth* inherent optical properties
(IOPs) it carries and a noise model for the :math:`R_{rs}` uncertainty. The
metrics layer then compares each algorithm's retrieval against that truth on the
intersection of available bands and components.

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
       (from ``bbp``); scalars ``chla``, ``tss``
     - planned (Stage 6)
   * - GLORIA
     - in situ
     - hyperspectral
     - scalar only: ``a_cdom440``, ``Chla``, ``TSS``, ``Secchi``
     - planned (Stage 6)

L23 — Loisel et al. (2023)
==========================

The **L23** synthetic dataset (Loisel et al., 2023) is a Hydrolight radiative-
transfer simulation spanning a wide range of water types, used here as the
first-pass benchmark because it provides **exact, noise-free truth** for every
IOP component. IOPtics loads it via ``ocpy.hydrolight.loisel23`` on its native
**81-band 400–700 nm** grid.

- **Scope of the first sweep.** All **3320** L23 spectra (the ``X=1`` elastic
  scenario).
- **Truth.** The full spectral decomposition — total absorption :math:`a`, total
  backscatter :math:`b_b`, and the components :math:`a_{ph}` (phytoplankton),
  :math:`a_{dg}` (CDOM + detritus), :math:`b_{bp}` (particulate backscatter) —
  plus scalar chlorophyll ``Chl`` and the :math:`a_{dg}` slope ``Sdg``. This is
  what the accuracy metrics score against.
- **Noise.** A **PACE** per-band :math:`R_{rs}` uncertainty
  (``ocpy.satellites.pace``) is attached as the fit weight and used to draw a
  single realization that perturbs the otherwise-noiseless spectrum, so the fit
  sees a realistic observation. (This is why :math:`R_{rs}` goes slightly
  negative in the red, where the signal is near zero — see the closure
  diagnostics.)
- **Stratification.** Reports bin L23 by trophic state from the truth
  chlorophyll: **oligotrophic** (Chl < 0.1), **mesotrophic** (0.1–1.0), and
  **eutrophic** (> 1.0 mg m\ :sup:`-3`).

PANGAEA & GLORIA (planned)
==========================

Two in-situ datasets extend the comparison beyond synthetic data (Stage 6):

- **PANGAEA** — measured :math:`R_{rs}` with its own reported uncertainty
  (``noise='insitu'``) and spectral truth for :math:`a_{ph}`, :math:`a_{dg}`
  (mapped from measured ``acdom``) and :math:`b_{bp}` (from ``bbp``), plus
  ``chla``/``tss`` scalars.
- **GLORIA** — hyperspectral :math:`R_{rs}` with **scalar-only** truth
  (``a_cdom440``, ``Chla``, ``TSS``, ``Secchi``). Because GLORIA reports CDOM
  absorption at 440 nm rather than the combined :math:`a_{dg}`, the comparison of
  a retrieved :math:`a_{dg}(440)` against ``a_cdom440`` is flagged with a
  ``caveat`` (``CDOM_vs_adg``) so reports surface the definitional mismatch.

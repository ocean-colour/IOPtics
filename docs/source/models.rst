==========
IOP models
==========

**What is being retrieved.** Ocean colour is the spectrum of sunlight that
leaves the sea surface, quantified as the *remote-sensing reflectance*
:math:`R_{rs}(\lambda)` (units sr\ :sup:`-1`) — the ratio of water-leaving
radiance to downwelling irradiance at each wavelength :math:`\lambda`. Its shape
and magnitude are set by the water's **inherent optical properties (IOPs)**: how
strongly the water and its constituents **absorb** light (absorption
:math:`a(\lambda)`, m\ :sup:`-1`) and **scatter it backward** toward a satellite
(backscattering :math:`b_b(\lambda)`, m\ :sup:`-1`). An *IOP retrieval* is the
inverse problem — infer :math:`a` and :math:`b_b` (and their constituents) from
the measured :math:`R_{rs}`.

**The forward model.** To a good approximation reflectance depends on the single
ratio :math:`u = b_b/(a+b_b)` (Gordon et al.):

.. math::

   R_{rs}(\lambda) \;\approx\; g_1\,u(\lambda) + g_2\,u(\lambda)^2 ,
   \qquad u(\lambda)=\frac{b_b(\lambda)}{a(\lambda)+b_b(\lambda)} .

The water itself contributes known :math:`a_w,\,b_{bw}`, so a model only has to
describe the **non-water** parts. Total absorption and backscatter split into
physically distinct constituents:

.. math::

   a(\lambda) = a_w(\lambda) + \underbrace{a_{ph}(\lambda)}_{\text{phytoplankton}}
              + \underbrace{a_{dg}(\lambda)}_{\text{CDOM + detritus}},
   \qquad
   b_b(\lambda) = b_{bw}(\lambda) + \underbrace{b_{bp}(\lambda)}_{\text{particles}} .

- :math:`a_{ph}` — absorption by **phytoplankton** (chlorophyll & accessory
  pigments), with characteristic peaks near 440 nm (blue) and 675 nm (red).
- :math:`a_{dg}` — combined absorption by **coloured dissolved organic matter
  (CDOM, “gelbstoff”)** and non-living **detritus**; both decay smoothly from
  blue to red.
- :math:`b_{bp}` — **particulate backscatter**, a smooth power-law decline with
  wavelength.

An *algorithm* is a specific parameterization of these three curves. IOPtics
runs two side by side — a flexible 5-parameter **BING** model and a leaner
3-parameter **GIOP**-style model — and scores each retrieval against known truth.

.. figure:: _static/model_components.png
   :width: 100%

   The three spectral building blocks. Each algorithm fits an **amplitude**
   (vertical scale) and, for the more flexible model, a **slope** (how fast the
   curve falls with wavelength) of each component, then combines them through the
   forward model above to predict :math:`R_{rs}`.

``expb_pow`` — the standard 5-parameter BING model
==================================================

The canonical BING parameterization (**k = 5** free parameters): an
*exponential* CDOM+detritus term plus a *Bricaud* phytoplankton term
(``ExpBricaud``), and a *power-law* particulate backscatter (``Pow``):

.. math::

   a_{dg}(\lambda) &= A_{dg}\,\exp\!\big[-S_{dg}\,(\lambda-\lambda_0)\big], \\
   a_{ph}(\lambda) &= A_{ph}\,a^{*}_{ph}(\lambda), \\
   b_{bp}(\lambda) &= B_{nw}\,\left(\lambda_0/\lambda\right)^{\eta},

with reference wavelength :math:`\lambda_0` (≈ 440 nm for absorption, 550 nm for
backscatter) and :math:`a^{*}_{ph}` the tabulated Bricaud chlorophyll-specific
absorption shape.

.. list-table::
   :header-rows: 1
   :widths: 12 20 68

   * - Parameter
     - Symbol / controls
     - Meaning
   * - ``Adg``
     - :math:`A_{dg}` — :math:`a_{dg}` amplitude
     - how much CDOM + detritus absorption there is
   * - ``Sdg``
     - :math:`S_{dg}` — :math:`a_{dg}` slope
     - how steeply that absorption falls from blue to red
   * - ``Aph``
     - :math:`A_{ph}` — :math:`a_{ph}` amplitude
     - phytoplankton (≈ chlorophyll) absorption magnitude
   * - ``Bnw``
     - :math:`B_{nw}` — :math:`b_{bp}` amplitude
     - particle backscatter magnitude (roughly, turbidity)
   * - ``beta``
     - :math:`\eta` — :math:`b_{bp}` slope
     - spectral steepness of particle backscatter

Because it fits **both** the amplitude and the slope of the dissolved and
particulate terms, ``expb_pow`` is the more flexible model — expected to
reproduce :math:`R_{rs}` closely, at the cost of two extra parameters. It is the
algorithm run with **MCMC** on a subset, so its posterior samples also drive the
uncertainty / coverage diagnostics.

``giop`` — the 3-parameter contrast
====================================

A leaner GIOP-style model (**k = 3**): the same physical decomposition, but with
the **slopes fixed** rather than fit — a ``GIOP`` non-water absorption and a
``Lee`` backscatter:

.. math::

   a_{dg}(\lambda) &= A_{exp}\,\exp\!\big[-S_{0}\,(\lambda-\lambda_0)\big]
                      \quad (S_0\ \text{fixed}), \\
   a_{ph}(\lambda) &= A_{ph}\,a^{*}_{ph}(\lambda), \\
   b_{bp}(\lambda) &= B_{nw}\,\left(\lambda_0/\lambda\right)^{\eta_0}
                      \quad (\eta_0\ \text{fixed, Lee 2002}).

.. list-table::
   :header-rows: 1
   :widths: 12 20 68

   * - Parameter
     - Symbol / controls
     - Meaning
   * - ``Aexp``
     - :math:`A_{exp}` — :math:`a_{dg}` amplitude
     - combined CDOM + detritus magnitude (fixed slope)
   * - ``Aph``
     - :math:`A_{ph}` — :math:`a_{ph}` amplitude
     - phytoplankton absorption magnitude
   * - ``Bnw``
     - :math:`B_{nw}` — :math:`b_{bp}` amplitude
     - particle backscatter magnitude (fixed Lee slope)

With the slopes pinned to literature values, ``giop`` has fewer knobs — more
parsimonious, and harder to over-fit. It is fit by **least squares** only (see
below).

Fitting and how the two are judged
==================================

Both models are fit by **least squares** — adjusting the parameters to minimize
the mismatch between predicted and observed reflectance, weighted by the
measurement noise :math:`\sigma(\lambda)`:

.. math::

   \chi^2 = \sum_\lambda
     \frac{\big[R_{rs}^{\text{obs}}(\lambda)-R_{rs}^{\text{model}}(\lambda)\big]^2}
          {\sigma(\lambda)^2},
   \qquad
   \chi^2_\nu = \chi^2/(n-k) .

The **reduced** :math:`\chi^2_\nu` divides by the degrees of freedom
(:math:`n` bands minus :math:`k` parameters): :math:`\chi^2_\nu\approx1` means the
fit matches the data to within the noise, :math:`>1` under-fits, :math:`<1`
over-fits.

A better-fitting model is not automatically better — extra parameters can fit
noise. The **Bayesian Information Criterion** penalizes complexity,

.. math::  \mathrm{BIC} = \chi^2 + k\,\ln n ,

and the per-spectrum difference :math:`\Delta\mathrm{BIC}=\mathrm{BIC}_{\text{expb\_pow}}
-\mathrm{BIC}_{\text{giop}}` asks whether ``expb_pow``'s two extra parameters
*earn their keep*: :math:`\Delta\mathrm{BIC}<0` favours the flexible model,
:math:`>0` the parsimonious one. The reports quantify the trade-off three ways —
**retrieval accuracy** against truth, **head-to-head wins**, and this
**model-selection** contest. See :doc:`reports/index`.

# IOPtics Context Reference

**Version:** 0.1
**Date:** 2026-06-15
**Authors:** JXP and Claude

## Purpose

This is a *reduced reference* distilled from the primary source materials for IOPtics
(see [References](#references)). It captures the scientific concepts, algorithm families,
datasets, uncertainty issues, and validation practices needed to design and build IOPtics —
a package for testing and evaluating a wide range of IOP (inherent optical property)
algorithms and sharing metrics/diagnostics with the ocean-optics community.

Sources reduced here:

- **The Oceanic Optics Book** (Mobley, ed., 2022, IOCCG) — foundational optical-oceanography
  definitions and radiative-transfer theory.
- **Werdell et al. (2013)** — the Generalized IOP (GIOP) model framework (Applied Optics).
- **Werdell et al. (2018)** — review of approaches and challenges for retrieving marine IOPs
  from ocean color (Progress in Oceanography).
- **The BING repository** (`~/Oceanography/python/bing`) — an existing Python implementation
  of Bayesian semi-analytical IOP retrieval, a reference design for IOPtics' architecture.

---

## 1. Foundational concepts (Mobley)

Hydrologic optics quantifies how light interacts with natural waters. Three layers of
quantities, connected by the radiative transfer equation (RTE):

### Inherent Optical Properties (IOPs)
Properties of the medium itself, **independent of the ambient light field**:

| Symbol | Quantity | Units | Notes |
|---|---|---|---|
| `a(λ)` | absorption coefficient | m⁻¹ | conservative: sum of components |
| `b(λ)` | total scattering coefficient | m⁻¹ | `b = ∫ β(ψ) dΩ` over all angles |
| `bb(λ)` | backscattering coefficient | m⁻¹ | `bb = ∫ β(ψ) dΩ` over back hemisphere |
| `c(λ)` | beam attenuation | m⁻¹ | `c = a + b` |
| `β(ψ,λ)` | volume scattering function (VSF) | m⁻¹ sr⁻¹ | angular scattering |
| `β̃(ψ)` | scattering phase function | sr⁻¹ | `β̃ = β / b` |
| `ω₀` | single-scattering albedo | — | `ω₀ = b / c` |

### Apparent Optical Properties (AOPs)
Depend on both IOPs **and** the light field, but are stable enough to characterize a water body:

- `Rrs(θ,φ,λ) = Lw / Ed` — **remote-sensing reflectance** (sr⁻¹); the central satellite observable.
- `R = Eu / Ed` — irradiance reflectance.
- `Kd, Ku, KL` — diffuse attenuation coefficients.
- Average cosines `μ̄d, μ̄u`.

### Radiometric variables
Radiance distribution `L(z,θ,φ,λ)`; downwelling/upwelling plane and scalar irradiances
(`Ed, Eu, Eod, Eou`); PAR.

The **RTE** ties IOPs + boundary conditions (sky radiance, sea state, bottom BRDF, internal
sources) to the radiometric field, from which AOPs are derived. IOPtics largely operates in
the **AOP → IOP inverse direction**.

---

## 2. The forward problem: relating Rrs to IOPs

### Subsurface conversion
Above- to below-surface reflectance (Lee et al. 2002):

```
rrs(λ, 0⁻) = Rrs(λ) / (0.52 + 1.7·Rrs(λ))
```

### Gordon quadratic (QSSA; Gordon et al. 1988)
The workhorse semi-analytical relation:

```
rrs(λ, 0⁻) = G₁(λ)·u(λ) + G₂(λ)·u(λ)²        where  u(λ) = bb(λ) / (a(λ) + bb(λ))
```

- Standard spectrally-flat coefficients: **G₁ = 0.0949, G₂ = 0.0794** (Gordon et al. 1988).
- Alternatives: Morel et al. (2002) LUT for `G(λ)` (varies with solar/sensor geometry and Cₐ;
  G₂ = 0); Lee et al. (2002) `gw/gp` formulation. The choice of `G(λ)` is a known, poorly
  constrained source of uncertainty (geometry, sea state, VSF shape).
- Most algorithms first solve for `u(λ)`, then decompose into component IOPs.

### Other QSSA / RT approximations
Jerome et al. (1996), Morel & Gentili (1993, with `f/Q`), Albert & Mobley (2003, Hydrolight
fit), Park & Ruddick (2005). Full **scalar/vector radiative transfer** (Hydrolight, etc.) is
more accurate, captures multiple scattering, inelastic processes, vertical structure, and
polarization (scalar RT can differ ≤50% from vector RT), but is computationally expensive and
needs accurate inputs.

### Inelastic / additional processes (opt-in)
- **Raman scattering** by water (wavelength-redistributing).
- **Chlorophyll fluorescence** (~683 nm emission) and CDOM fluorescence.
- Standard QSSA is purely **elastic**; only a subset of inversion methods include inelastic terms.

---

## 3. IOP component decomposition

Absorption is conservative — the sum of constituent contributions:

```
a(λ) = a_w(λ) + Σ a_ph,i(λ) + Σ a_nap,i(λ) + Σ a_cdom,i(λ)
```

- `a_w` — pure seawater absorption (assumed known; Pope & Fry 1997, Mason et al. 2016, T/S-dependent).
- `a_ph` — phytoplankton (often `= A_ph · a*_ph(λ)`, with Bricaud 1995 chlorophyll-specific shapes).
- `a_nap` — non-algal particles (detritus).
- `a_cdom` — colored dissolved organic matter (gelbstoff).
- NAP and CDOM share an exponential shape, so are usually combined as **`a_dg`** (dissolved + detrital):

```
a*_dg(λ) = exp(−S_dg·(λ − λ₀)),   S_dg ≈ 0.01–0.02 nm⁻¹  (GIOP-DC fixes S_dg = 0.018)
```

> Caveat: NAP and CDOM have different physical/biogeochemical origins and residence times;
> combining them limits biogeochemical interpretation. Retrieving `S_cdom` separately is desirable.

Backscattering = water + particles (usually a single particulate term):

```
bb(λ) = bb_w(λ) + Σ B_bp,i · b*_bp,i(λ),     b*_bp(λ) = (λ₀/λ)^{S_bp}   (power law)
```

- `bb_w` — pure-seawater backscattering (Zhang et al. 2009 is current state of the art,
  T/S/pressure-dependent; depolarization ratio δ ≈ 0.039 recommended but uncertain ≥50%).
- `S_bp` typically 0–3 (varies with particle size). Power-law validity is debated.

**Well-posedness:** the number of unknown IOP variables must not exceed the number of
independent spectral bands. Multispectral sensors give 5–8 usable VIS bands; hyperspectral
(PACE) gives many more but with correlated information — fewer *independent* parameters than
bands, though with lower per-parameter uncertainty.

---

## 4. The inverse problem & algorithm families

Deriving IOPs from `Rrs` is a (often ill-posed) inverse problem: different IOP combinations can
produce the same `Rrs`. A forward model `F` (`Rrs = F[IOP]`) is built, then inverted.

Three pathways (Werdell 2018, Fig. 1):
1. **Top-of-atmosphere radiance → IOPs** (coupled atmosphere-ocean).
2. **Rrs → IOPs** (the standard NASA/ESA path after atmospheric correction).
3. **Lt → IOPs / biogeochemical proxy** (avoids atmospheric correction).

### Semi-analytical algorithm (SAA) solution classes
1. **Non-linear spectral optimization** — assume spectral shapes (eigenvectors) for components,
   solve simultaneously for amplitudes via Levenberg–Marquardt / Nelder–Mead / particle swarm /
   genetic / simulated annealing. (Roesler & Perry 1995, Garver–Siegel 1997, GSM Maritorena 2002.)
2. **Direct linear matrix inversion** — linearize and solve in one step (Hoge & Lyon 1996, Wang 2005).
   Classes (1) and (2) are the *simultaneous* solution: overdetermined when N_bands > N_unknowns.
3. **Spectral deconvolution** — step-wise/algebraic; solve total `a` and `bb` first, then
   decompose `a` (e.g. **QAA**, Lee et al. 2002; Smyth et al. 2006). Always reports ΔRrs = 0.
4. **Bulk inversion** — derive IOPs at each wavelength independently, no predefined shapes
   (LAS, Loisel & Stramski 2000; uses Kd).

### Other approaches
- **GIOP** (Werdell 2013): a *framework*, not a single algorithm — constructs any SAA at runtime
  by selecting eigenvectors and inversion method. GIOP-DC is its default community configuration.
  GIOP-DC optimizes `(B_bp, A_dg, A_ph)` with LM over 400–700 nm; ran successfully on ~90% of
  NOMAD/IOCCG stations.
- **Look-up-table (LUT)** methods (Hedley 2009, Mobley 2005, Liu & Miller 2008): pre-compute
  forward `Rrs`/`Lt` spectra, match observed to nearest entry. Can return a *suite* of solutions
  → natural uncertainty estimate; easily include inelastic processes; but expensive to build and
  search and may not reflect covariances.
- **Empirical / machine-learning** (MLR, PCR/EOF, ANN, random forests, SVM, gene expression
  programming): data-driven, need large representative training sets, often region-specific.

### Eigenvectors / shape parameterizations are the key differentiator
Most SAAs differ only in: (a) choice of eigenvectors (`a*_ph`, `a*_dg`, `b*_bp`), (b) `G(λ)`,
(c) inversion/optimization method, (d) number of bands. GIOP sensitivity analysis hierarchy:
**`S_dg` is the most critical** eigenvector choice (controls a_dg/a_ph split); `S_bp` is the
least critical (retrievals fairly insensitive). Dynamically-evolving `S_dg` (Lee 2002 form,
Eq. 15) beats static. OWT (optical water type) classification can dynamically assign eigenvectors.

---

## 5. Uncertainty sources & quantification

### Where uncertainty enters
1. Input `Rrs` uncertainty (sensor noise, atmospheric correction error, BRDF).
2. Forward-model formulation/parameterization and its assumptions (`G(λ)`, fixed shapes).
3. Inverse solution method (ill-posedness, non-uniqueness).

### IOP *measurement* uncertainties (for ground truth)
- `a/c` via WET Labs ac-meters: ~0.005–0.01 m⁻¹ (a), 0.01–0.015 m⁻¹ (c); largest near 400 nm and
  in clear water / NIR; scattering-correction of `a` is a major open issue.
- Filter-pad / spectrophotometric absorption; partitioning a_ph vs a_nap (Kishino 1985 method).
- VSF/backscattering: MASCOT, MVSM, ECO-BB, HydroScat; conversion factor χ; NIR scattering
  correction. Pure-water `bb_w`: Zhang et al. 2009.
- **Closure experiments** (RT + in-situ) typically agree to within 20–30%.

### Methods to quantify *derived* IOP uncertainty
- **Gradient-based** (variance–covariance from the Jacobian of the χ² fit; GIOP's approach) —
  ignores sensor/AC error not captured in spectral disagreement; underestimates true uncertainty.
- **Ensemble / Monte Carlo** (perturb inputs m times; Wang 2005, ANN ensembles) — powerful but
  expensive (1000s of perturbations/pixel) and ignores correlated errors.
- **Bayesian** (Frouin & Pelletier 2015) — full posterior, confidence domains. *(BING's MCMC route.)*
- **Satellite-to-in-situ match-ups** and **sensor co-location** (Mélin) — empirical product uncertainty.

A reliable per-pixel `Rrs` uncertainty budget (instrument + AC) remains a community need. There is
**no community consensus** on how uncertainty should be defined/computed.

---

## 6. Performance metrics & validation

Validation compares retrieved IOPs against "truth": synthesized `Rrs`↔IOP pairs, in-situ
match-ups, or time-series/population statistics.

Common metrics (note: *no consensus* on the single best metric — IOPtics should report several):
- `r²`, Type-II regression slope & intercept.
- **Ratio** = median(X̂/X); **MPD** = median percent difference = median(100·|X̂/X − 1|).
- **ΔRrs** (mean relative `Rrs` difference, Eq. 10) — internal closure metric; thresholds:
  Boss & Roesler 33%/Werdell 33% (400–600 nm) ⇒ non-solution above this.
- **ΔIOP** (Eq. 13) — relative IOP difference vs. truth.
- **Taylor diagrams** (correlation, normalized σ) and **Target diagrams** (bias vs. unbiased RMSD).
- RMS / unbiased RMS; report on **log-transformed** quantities where appropriate (Cₐ, IOPs are
  ~log-normally distributed; means vs. medians matter for non-normal data).

### Quality control / physical constraints
After inversion, enforce realistic ranges (GIOP-DC, Eq. 19), e.g.:
```
−0.05·bb_w ≤ bb_p ≤ 0.05 ;  −0.05·a_w ≤ a_ph ≤ 5 ;  −0.05·a_w ≤ a_dg ≤ 5  (m⁻¹) ;  ΔRrs ≤ 33%
```
Slightly negative values allowed (statistically ≈ 0). Out-of-range ⇒ flag as non-solution.
Stratify validation by trophic level (oligo- / meso- / eutrophic; by Cₐ thresholds 0.1, 1 mg m⁻³).

### Key insight for IOPtics
GIOP's central thesis: a **consolidated software framework** that constructs/compares SAAs at
runtime advances the field by enabling controlled evaluation, regional tuning, OWT-based dynamic
parameterization, and ensemble modeling. **This is essentially the IOPtics mission**, broadened
to all algorithm families (SAA, LUT, empirical/ML) with rigorous, shared metrics.

---

## 7. Datasets

### Loisel et al. (2023) — "L23" (first IOPtics dataset)
- Hydrolight radiative-transfer **synthetic** dataset spanning a wide range of water types, with
  **known true IOPs** → ideal for algorithm validation.
- Provides `wave, Rrs, a, bb, Chl, Sdg, Y` per spectrum.
- In BING, loaded via `ocpy.hydrolight.loisel23`; fit through `bing.fitting.l23`.
- Reference paper "Assessment of Standard Ocean Color Semi-analytical Algorithms" (Remote Sens.
  Environ.) is itself a model for the kind of inter-algorithm comparison IOPtics targets.

### NOMAD (NASA bio-Optical Marine Algorithm Dataset)
In-situ `Rrs`, IOPs, Cₐ match-ups. Real-world but suffers imperfect radiometric closure
(different instruments/methods), uneven trophic-level sampling.

### IOCCG synthetic dataset
Forward-modeled `Rrs`↔IOP with optical closure by design (but simple optics — no Raman/fluorescence).

### Satellite match-ups
SeaWiFS, MODIS-Aqua, MERIS, VIIRS; +3 h temporal, 5×5 box filtered-median spatial criteria
(Bailey & Werdell 2006). Limited by sub-pixel/depth scale gaps vs. point in-situ measurements.

---

## 8. BING package — architecture reference

BING (Bayesian INferences with Gordon coefficients) is an existing, mature implementation that
IOPtics can draw on. Core data flow:

```
Rrs  →  [models: a(λ)=a_w+a_nw, bb(λ)=bb_w+bb_nw]  →  [rt: Gordon (+Raman/fluorescence)]
     →  [fitting: chisq (least-squares) → MCMC (emcee)]  →  [evaluate: stats, reconstruct a,bb ± unc]
```

Key design patterns worth carrying into IOPtics:
- **Two-model architecture**: always fit a pair `[absorption_model, backscattering_model]`;
  split parameter array by `models[0].nparam`.
- **log10 parameter space** for amplitudes (numerical stability); slopes/exponents stay linear.
- **Shape contract**: `eval_anw`/`eval_bbnw` always return `(nsample, nwave)`.
- **Water components** (`a_w`, `bb_w`) computed once at init from IOCCG/Zhang reference data.
- **Pluggable model registry**: `init_model(name, wave, prior_dicts)` for both absorption
  (`Cst, Exp, Bricaud, ExpBricaud, GIOP, GSM, ExpNMF, Chase, ...`) and backscattering
  (`Cst, Pow, GSM, Lee, ...`) — IOPtics needs the same extensibility across *all* algorithm types.
- **Prior system** (`LogUniform/Uniform/Gaussian/Ratio`) for Bayesian inference.
- **Standard configurations** (`standard.expb_pow`, `.giop`, `.gsm`) — pre-wired model combos.
- **Satellite noise models** (PACE/MODIS/SeaWiFS/SBG) via the sibling `ocpy` package — keep the
  satellite-band/noise data boundary external.
- **Gordon coefficient tables** in `bing/data/RT/` (including wavelength-dependent G₁/G₂ and G₀/Gb).

---

## 9. Knowledge gaps & forward look (relevant to IOPtics scope)

- **PACE (launched 2024)**: hyperspectral OCI (~350–900 nm, ~5 nm) + multi-angle polarimetry.
  Enables UV absorption (better a_cdom/a_nap separation since S_cdom > S_nap), pigment/community
  discrimination via derivative analysis, and polarized retrievals. IOPtics should be
  wavelength-agnostic and ready for hyperspectral input.
- **Absorption gaps**: UV absorption of dissolved inorganics; MAAs; phytoplankton `a*_ph` in UV.
- **Backscattering gaps**: spectral shape parameterization beyond power-law; multi-component bbp;
  pure-water depolarization ratio.
- **Inelastic processes**: Raman/fluorescence; T/S corrections inside inversions.
- **Optically shallow waters**: bottom reflectance contamination → biased retrievals.
- **Non-conventional / coupled atmosphere-ocean** and **ML** approaches deserve first-class support.
- **Computation**: LUT/ANN/coupled methods are expensive; GPUs and open-source sharing recommended.
- **Community recommendations**: share algorithm code openly; assemble public in-situ/synthetic
  hyperspectral datasets; build decision-support/validation metrics on *all* wavelengths;
  quantify full uncertainty budgets.

---

## References

1. Mobley, C. D. (ed.), 2022. *The Oceanic Optics Book*, IOCCG, 924 pp. DOI: 10.25607/OBP-1710.
2. Werdell, P. J., et al., 2013. "Generalized ocean color inversion model for retrieving marine
   inherent optical properties." *Applied Optics* 52(10), 2019–2037.
3. Werdell, P. J., et al., 2018. "An overview of approaches and challenges for retrieving marine
   inherent optical properties from ocean color remote sensing." *Progress in Oceanography* 160,
   186–212.
4. Gordon, H. R., et al., 1988. "A semianalytic radiance model of ocean color." *JGR* 93, 10909.
5. Lee, Z.-P., et al., 2002. "Deriving inherent optical properties from water color: QAA."
   *Applied Optics* 41, 5755–5772.
6. Bricaud, A., et al., 1995. Phytoplankton absorption parameterization. *JGR* 100, 13321.
7. Maritorena, S., et al., 2002. GSM semi-analytical model. *Applied Optics* 41, 2705.
8. Loisel, H., et al., 2023. "Assessment of Standard Ocean Color Semi-analytical Algorithms."
   *Remote Sensing of Environment* (the "L23" Hydrolight synthetic dataset).
9. Zhang, X., Hu, L., He, M.-X., 2009. Scattering by pure seawater. *Optics Express* 17, 5698.
10. BING repository: `~/Oceanography/python/bing` (local); Bayesian Gordon-coefficient IOP retrieval.

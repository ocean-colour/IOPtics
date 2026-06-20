# IOPtics

Analysis of IOP algorithms. For the community. Hopefully by the community.

**IOPtics** is a Python package for testing and evaluating a wide range of IOP
(inherent optical property) algorithms. It provides the ocean-optics community
with a common, reproducible framework for running these algorithms on
remote-sensing reflectance (Rrs) spectra, quantifying the retrieved IOPs and
their uncertainties, and comparing the results against ground truth using uniform
metrics and diagnostics.

## What it does

- Runs a range of IOP algorithms on Rrs spectra (retrieval engine: the
  [BING](https://github.com/ocean-colour/bing) package).
- Computes absorption `a(λ)` and backscattering `bb(λ)` and their components
  (`a_ph`, `a_dg`, `bb_p`) with uncertainties.
- Compares retrievals against ground truth — synthetic (Loisel et al. 2023) and
  in-situ (PANGAEA / Valente et al. 2022, GLORIA / Lehmann et al. 2023).
- Produces uniform metrics, diagnostics, figures, and reproducible reports.

See the [design document](docs/design/IOPtics_design.md) for the full plan and
[`docs/context.md`](docs/context.md) for the scientific background.

## Installation

IOPtics targets Python ≥ 3.12 and is developed against the `ocean14` conda
environment. It depends on the sibling packages
[ocpy](https://github.com/ocean-colour/ocpy) and
[BING](https://github.com/ocean-colour/bing), which are not on PyPI.

```bash
git clone https://github.com/ocean-colour/IOPtics.git
cd IOPtics
pip install -r requirements.txt   # pulls ocpy + BING from GitHub
pip install -e .
```

The datasets are large and are not packaged; they are resolved from
`$OS_COLOR` (e.g. `$OS_COLOR/Loisel2023`, `$OS_COLOR/PANGAEA/V3`).

## Status

Early development. The design is captured in
[`docs/design/IOPtics_design.md`](docs/design/IOPtics_design.md); code is being
built out incrementally (first algorithm: `expb_pow`).

## Authors

J. Xavier Prochaska (UC Santa Cruz) and Claude.

## License

BSD.

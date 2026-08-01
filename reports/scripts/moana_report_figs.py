"""Generate the figures for ``reports/MOANA_Claude_Report.md``.

Everything here is derived from the two vendored MOANA reference tables in
``ioptics/data/moana/`` -- no satellite or in-situ data is needed, so this script
runs anywhere the repo is checked out.

Run with::

    python reports/scripts/moana_report_figs.py

Outputs (written to ``reports/figures/``):
    moana_pc_loadings.png   -- loadings of the principal components MOANA actually
                               uses, annotated with which taxa use each one.
"""

import json
import os

import h5py
import numpy as np
import matplotlib

matplotlib.use("Agg")  # headless-safe; no display needed
import matplotlib.pyplot as plt

# Repo-relative paths, resolved from this script's location so the working
# directory does not matter.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir))
DATA_DIR = os.path.join(_REPO, "ioptics", "data", "moana")
FIG_DIR = os.path.join(_REPO, "reports", "figures")


def load_moana_tables(data_dir=DATA_DIR):
    """Load the MOANA PCA loadings and regression coefficients.

    Inputs
    ------
    data_dir : str
        Directory holding ``pca_picophyto.h5`` and ``picophyt.json``.

    Outputs
    -------
    wave : ndarray, shape (124,)
        Wavelengths of the algorithm's grid [nm], 414 to 660 in 2 nm steps.
    loadings : ndarray, shape (124, 45)
        Loading matrix ``V[lambda, i]``; columns are orthonormal.
    coefs : dict
        ``{'npc': int, 'pro': list, 'syn': list, 'apeuk': list}`` -- the raw
        zero-padded coefficient vectors exactly as OCSSW reads them.
    """
    with h5py.File(os.path.join(data_dir, "pca_picophyto.h5"), "r") as h5:
        loadings = h5["component"][:]
        wave = h5["wavelength"][:]

    with open(os.path.join(data_dir, "picophyt.json")) as fh:
        raw = json.load(fh)

    coefs = {
        "npc": int(raw["npc"]),
        "pro": [float(x) for x in raw["pro_coef"].split(",")],
        "syn": [float(x) for x in raw["syn_coef"].split(",")],
        "apeuk": [float(x) for x in raw["apeuk_coef"].split(",")],
    }
    return wave, loadings, coefs


def pcs_used_by_taxon(coefs):
    """Map each taxon to the 1-based principal components it actually uses.

    Replicates the indexing in OCSSW ``get_Cpicophyt.c``: for i in 0..npc-1,
    ``pro_coef[i+2]``, ``syn_coef[i+1]`` and ``apeuk_coef[i+1]`` each multiply
    score ``U_(i+1)``. Zero-valued slots mean the PC is unused.

    Inputs
    ------
    coefs : dict
        As returned by :func:`load_moana_tables`.

    Outputs
    -------
    dict
        ``{taxon: {pc_number: coefficient}}`` for the three taxa.
    """
    npc = coefs["npc"]
    # offset of the first PC coefficient within each vector
    offsets = {"pro": 2, "syn": 1, "apeuk": 1}
    used = {}
    for taxon, off in offsets.items():
        vec = coefs[taxon]
        used[taxon] = {
            i + 1: vec[i + off] for i in range(npc) if vec[i + off] != 0.0
        }
    return used


def plot_pc_loadings(wave, loadings, used, n_show=6, outfile=None):
    """Plot the loadings of the leading principal components.

    Inputs
    ------
    wave : ndarray
        Wavelength grid [nm].
    loadings : ndarray, shape (n_wave, n_pc)
        Loading matrix.
    used : dict
        Output of :func:`pcs_used_by_taxon`, used to annotate which taxa
        depend on each component.
    n_show : int
        How many leading components to draw.
    outfile : str or None
        Path to write the PNG to. If None, nothing is written.

    Outputs
    -------
    matplotlib.figure.Figure
        The figure, so a caller can further customise or save it.
    """
    labels = {"pro": "Pro", "syn": "Syn", "apeuk": "picoeuk"}

    fig, axes = plt.subplots(2, 3, figsize=(13, 6.5), sharex=True)
    for k, ax in enumerate(axes.ravel()[:n_show]):
        pc = k + 1
        ax.axhline(0.0, color="0.8", lw=0.8, zorder=0)
        ax.plot(wave, loadings[:, k], color="C0", lw=1.8)

        # Which taxa use this component, and with what sign?
        consumers = [
            f"{labels[t]} ({used[t][pc]:+.3g})" for t in ("pro", "syn", "apeuk")
            if pc in used[t]
        ]
        subtitle = "; ".join(consumers) if consumers else "unused by all three taxa"
        ax.set_title(f"PC{pc}\n{subtitle}", fontsize=9)
        ax.tick_params(labelsize=8)

    for ax in axes[-1]:
        ax.set_xlabel("wavelength [nm]", fontsize=9)
    for ax in axes[:, 0]:
        ax.set_ylabel("loading", fontsize=9)

    # Note: no '$...$' anywhere in the title -- matplotlib would interpret it as
    # mathtext and mangle the underscores in the filename.
    fig.suptitle(
        "MOANA PCA loadings (pca_picophyto.h5): the fixed basis onto which "
        "every standardised spectrum is projected",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    if outfile is not None:
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        fig.savefig(outfile, dpi=150)
        print(f"wrote {outfile}")
    return fig


def main():
    """Build every report figure and print a short summary of the tables."""
    wave, loadings, coefs = load_moana_tables()
    used = pcs_used_by_taxon(coefs)

    # Sanity checks worth printing: these are the invariants the report relies on.
    gram = loadings.T @ loadings
    offdiag = np.abs(gram - np.diag(np.diag(gram))).max()
    print(f"loadings shape      : {loadings.shape}")
    print(f"wavelengths         : {wave.min()}-{wave.max()} nm, step {np.diff(wave)[0]}")
    print(f"max |offdiag(V^T V)|: {offdiag:.2e}  (columns orthonormal)")
    print(f"||Rrs'||_2 for any standardised spectrum: {np.sqrt(len(wave) - 1):.3f}")
    for taxon in ("pro", "syn", "apeuk"):
        print(f"  {taxon:6s} uses PCs {sorted(used[taxon])}")

    plot_pc_loadings(
        wave, loadings, used,
        outfile=os.path.join(FIG_DIR, "moana_pc_loadings.png"),
    )


if __name__ == "__main__":
    main()

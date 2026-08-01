"""Generate the figures for ``reports/MOANA_Claude_Report.md``.

Two groups of figures:

* The PCA-basis figure is derived purely from the vendored MOANA reference tables
  in ``ioptics/data/moana/``, so it runs anywhere the repo is checked out.
* The product figures need one PACE MOANA granule under ``$OS_COLOR/PACE/``. They
  are skipped with a message if it is absent, mirroring the repo's convention of
  letting data-dependent work opt out rather than fail.

Run with::

    python reports/scripts/moana_report_figs.py

Outputs (written to ``reports/figures/``):
    moana_pc_loadings.png     -- loadings of the principal components MOANA uses,
                                 annotated with which taxa use each one.
    moana_product_masks.png   -- maps of the three products with the land-254
                                 sentinel and the unflagged clipped zeros exposed.
    moana_clipping.png        -- how often each product is clipped to zero, and the
                                 abundance distributions of what survives.

Colours follow the house data-viz palette: a single-hue blue sequential ramp for
magnitude, the first three categorical slots for taxon identity (that subset is
validated all-pairs for colour-vision deficiency), the reserved ``critical`` red
for the clipped-zero defect, and recessive greys for chrome.
"""

import json
import os

import h5py
import numpy as np
import matplotlib

matplotlib.use("Agg")  # headless-safe; no display needed
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

# Repo-relative paths, resolved from this script's location so the working
# directory does not matter.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir))
DATA_DIR = os.path.join(_REPO, "ioptics", "data", "moana")
FIG_DIR = os.path.join(_REPO, "reports", "figures")

# One PACE MOANA granule; see the prompt-3 report for how it was obtained.
GRANULE = os.path.join(
    os.environ.get("OS_COLOR", ""), "PACE",
    "PACE_OCI.20250701.L4m.DAY.MOANA.V3_2.0p1deg.nc",
)

# --- palette (house data-viz reference instance, light surface) ---------------
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
# Categorical slots 1-3: identity of the three taxa. This subset validates
# all-pairs in both light and dark modes, so it is safe for map/scatter forms.
TAXON_COLOR = {"pro": "#2a78d6", "syn": "#eb6834", "apeuk": "#1baf7a"}
# Reserved status colour, used ONLY for the clipped-zero defect -- never as a series.
CRITICAL = "#d03b3b"
LAND_GREY = "#c3c2b7"
# Single-hue sequential ramp (blue 100 -> 700) for continuous magnitude.
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SEQ_CMAP = LinearSegmentedColormap.from_list("moana_blue", BLUE_RAMP)

# Sentinels used by the MOANA products.
LAND, FILL, I32MIN = 254, -32767, -2147483648

# Display order and labels for the three taxa.
TAXA = [
    ("pro", "prococcus_moana", "Prochlorococcus"),
    ("syn", "syncoccus_moana", "Synechococcus"),
    ("apeuk", "picoeuk_moana", "picoeukaryotes"),
]


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


def _style_axes(ax):
    """Apply the recessive chrome the house style calls for.

    Inputs
    ------
    ax : matplotlib.axes.Axes
        Axes to restyle in place.

    Outputs
    -------
    None
    """
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASELINE)
    ax.tick_params(colors=INK_MUTED, labelsize=8)


def load_granule(path=GRANULE):
    """Read the three MOANA fields and their coordinates from a PACE granule.

    Values are returned exactly as stored (int32 with sentinels intact), because
    the sentinels are the subject of two of the figures.

    Inputs
    ------
    path : str
        Path to a ``*.L4m.*.MOANA.*.nc`` file.

    Outputs
    -------
    fields : dict
        ``{short_key: {'data': ndarray, 'valid_max': int}}`` per taxon.
    lat, lon : ndarray
        Coordinate vectors [degrees].
    """
    import xarray as xr  # imported here so the basis figure needs no xarray

    ds = xr.open_dataset(path, mask_and_scale=False)
    fields = {}
    for key, var, _label in TAXA:
        fields[key] = {
            "data": np.asarray(ds[var].values),
            "valid_max": int(ds[var].attrs["valid_max"]),
        }
    lat = np.asarray(ds["lat"].values)
    lon = np.asarray(ds["lon"].values)
    return fields, lat, lon


def summarize_product(fields):
    """Compute the ocean-only statistics the report quotes.

    Inputs
    ------
    fields : dict
        Output of :func:`load_granule`.

    Outputs
    -------
    dict
        ``{key: {...}}`` with pixel counts, the percentage of real retrievals that
        are exactly zero, the percentage exceeding ``valid_max``, and the positive
        values themselves (for the distribution panel).
    """
    stats = {}
    for key, _var, label in TAXA:
        d = fields[key]["data"]
        vmax = fields[key]["valid_max"]
        # "Real" = anything that is not land, not fill, and not the int32 underflow.
        ocean = (d != LAND) & (d != FILL) & (d != I32MIN)
        vals = d[ocean].astype("int64")
        stats[key] = {
            "label": label,
            "n_ocean": vals.size,
            "n_land": int((d == LAND).sum()),
            "n_fill": int((d == FILL).sum()),
            "n_i32min": int((d == I32MIN).sum()),
            "pct_zero": 100.0 * (vals == 0).mean(),
            "pct_over": 100.0 * (vals > vmax).mean(),
            "valid_max": vmax,
            "positive": vals[vals > 0],
        }
    return stats


def plot_product_masks(fields, lat, lon, outfile=None):
    """Map each product with the land sentinel and the clipped zeros exposed.

    The point of the figure: land is stored as 254 cells/mL, *inside* the declared
    valid range, and pixels clipped to zero carry no flag. Both are drawn in their
    own colours so the reader can see how much of the field they occupy.

    Inputs
    ------
    fields, lat, lon
        As returned by :func:`load_granule`.
    outfile : str or None
        Path to write the PNG to.

    Outputs
    -------
    matplotlib.figure.Figure
    """
    # lat runs north -> south in the file, which is what origin='upper' expects.
    assert lat[0] > lat[-1], "expected descending latitudes"
    extent = [lon.min() - 0.05, lon.max() + 0.05, lat.min() - 0.05, lat.max() + 0.05]

    fig, axes = plt.subplots(1, 3, figsize=(14, 5.6), facecolor=SURFACE)
    for ax, (key, _var, label) in zip(axes, TAXA):
        d = fields[key]["data"]
        ocean = (d != LAND) & (d != FILL) & (d != I32MIN)

        # Layer 1: magnitude, log10 of the positive retrievals only.
        pos = ocean & (d > 0)
        mag = np.full(d.shape, np.nan)
        mag[pos] = np.log10(d[pos].astype("float64"))
        im = ax.imshow(mag, extent=extent, origin="upper", cmap=SEQ_CMAP,
                       interpolation="nearest")

        # Layer 2: land, recessive grey.
        ax.imshow(np.where(d == LAND, 1.0, np.nan), extent=extent, origin="upper",
                  cmap=LinearSegmentedColormap.from_list("l", [LAND_GREY, LAND_GREY]),
                  interpolation="nearest", vmin=0, vmax=1)

        # Layer 3: the defect -- retrievals clipped to exactly zero, drawn last so
        # they are never hidden underneath anything else.
        ax.imshow(np.where(ocean & (d == 0), 1.0, np.nan), extent=extent,
                  origin="upper",
                  cmap=LinearSegmentedColormap.from_list("c", [CRITICAL, CRITICAL]),
                  interpolation="nearest", vmin=0, vmax=1)

        pct = 100.0 * (d[ocean] == 0).mean()
        ax.set_title(f"{label}\n{pct:.1f}% of retrievals clipped to zero",
                     fontsize=9.5, color=INK_PRIMARY)
        ax.set_facecolor(SURFACE)
        _style_axes(ax)
        # No axis labels: the degree ticks are self-explanatory on a map, and a
        # "longitude" label collides with the horizontal colorbar below it.

        cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.06, fraction=0.045)
        cb.set_label("log$_{10}$(cells mL$^{-1}$)", fontsize=8, color=INK_MUTED)
        cb.ax.tick_params(labelsize=7, colors=INK_MUTED)
        cb.outline.set_edgecolor(BASELINE)

    # (no y-axis label either, for the same reason as the x-axis)

    # Legend names every non-data colour, so nothing is carried by colour alone.
    fig.legend(
        handles=[
            Patch(facecolor=CRITICAL, label="clipped to 0 — unflagged"),
            Patch(facecolor=LAND_GREY, label="land, stored as 254 cells mL$^{-1}$"),
            Patch(facecolor=SURFACE, edgecolor=BASELINE, label="no retrieval (fill)"),
        ],
        loc="lower center", ncol=3, frameon=False, fontsize=9,
        bbox_to_anchor=(0.5, -0.01),
    )
    fig.suptitle(
        "PACE MOANA, 2025-07-01 daily 0.1°: the two traps a naive reader walks into",
        fontsize=11, color=INK_PRIMARY,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))

    if outfile is not None:
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        fig.savefig(outfile, dpi=150, facecolor=SURFACE)
        print(f"wrote {outfile}")
    return fig


def plot_clipping(stats, outfile=None):
    """Quantify the clipping, and show the distribution of what survives it.

    Inputs
    ------
    stats : dict
        Output of :func:`summarize_product`.
    outfile : str or None
        Path to write the PNG to.

    Outputs
    -------
    matplotlib.figure.Figure
    """
    fig, (ax_bar, ax_hist) = plt.subplots(1, 2, figsize=(12.5, 4.6), facecolor=SURFACE)

    # --- left: how often each product is exactly zero -------------------------
    keys = [k for k, _v, _l in TAXA]
    ypos = np.arange(len(keys))[::-1]  # first taxon at the top
    for y, key in zip(ypos, keys):
        s = stats[key]
        ax_bar.barh(y, s["pct_zero"], height=0.55, color=TAXON_COLOR[key],
                    zorder=3)
        # Direct labels: required for the aqua slot, and good practice for all.
        ax_bar.text(s["pct_zero"] + 0.4, y, f"{s['pct_zero']:.1f}%",
                    va="center", fontsize=9, color=INK_PRIMARY)
    ax_bar.set_yticks(ypos)
    ax_bar.set_yticklabels([stats[k]["label"] for k in keys], fontsize=9,
                           color=INK_PRIMARY)
    ax_bar.set_xlabel("share of real ocean retrievals equal to exactly 0 [%]",
                      fontsize=9, color=INK_MUTED)
    ax_bar.set_xlim(0, max(s["pct_zero"] for s in stats.values()) * 1.25 + 1)
    ax_bar.xaxis.grid(True, color=GRIDLINE, lw=0.8, zorder=0)
    ax_bar.set_axisbelow(True)
    ax_bar.set_facecolor(SURFACE)
    _style_axes(ax_bar)
    ax_bar.set_title("Silent clipping", fontsize=9, color=INK_PRIMARY)
    # The valid_max exceedances are 1-3 orders of magnitude smaller than the clipping
    # rates, so a second bar series would be invisible; annotate instead. Placed in
    # the empty lower-right of the panel rather than the title, which overflowed.
    note = "\n".join(
        f"{stats[k]['label']}: {stats[k]['pct_over']:.2f}% exceed valid_max"
        for k in keys
    )
    ax_bar.text(0.98, 0.06, note, transform=ax_bar.transAxes, ha="right", va="bottom",
                fontsize=8, color=INK_MUTED, linespacing=1.5)

    # --- right: distribution of the surviving positive values ------------------
    for key, _var, label in TAXA:
        vals = stats[key]["positive"]
        if vals.size == 0:
            continue
        ax_hist.hist(np.log10(vals), bins=60, histtype="step", lw=2.0,
                     color=TAXON_COLOR[key], label=label, zorder=3)
    ax_hist.set_xlabel("log$_{10}$(cells mL$^{-1}$)", fontsize=9, color=INK_MUTED)
    ax_hist.set_ylabel("pixels", fontsize=9, color=INK_MUTED)
    ax_hist.yaxis.grid(True, color=GRIDLINE, lw=0.8, zorder=0)
    ax_hist.set_axisbelow(True)
    ax_hist.set_facecolor(SURFACE)
    ax_hist.legend(frameon=False, fontsize=9, labelcolor=INK_PRIMARY)
    ax_hist.set_title("Abundance of what survives clipping", fontsize=9,
                      color=INK_PRIMARY)
    _style_axes(ax_hist)

    fig.tight_layout()
    if outfile is not None:
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        fig.savefig(outfile, dpi=150, facecolor=SURFACE)
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

    # --- data-dependent figures: skip cleanly if the granule is not present ----
    if not os.path.isfile(GRANULE):
        print(f"\nskipping product figures: granule not found at {GRANULE}")
        return
    print(f"\nreading {os.path.basename(GRANULE)}")
    fields, lat, lon = load_granule()
    stats = summarize_product(fields)
    for key, _var, label in TAXA:
        s = stats[key]
        print(f"  {label:16s} n_ocean={s['n_ocean']:>8,d}  zero={s['pct_zero']:5.1f}%  "
              f"over valid_max={s['pct_over']:5.2f}%")
    plot_product_masks(fields, lat, lon,
                       outfile=os.path.join(FIG_DIR, "moana_product_masks.png"))
    plot_clipping(stats, outfile=os.path.join(FIG_DIR, "moana_clipping.png"))


if __name__ == "__main__":
    main()

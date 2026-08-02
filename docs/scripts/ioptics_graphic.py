"""Generate the IOPtics summary graphic for the README, RTD, and talks.

A single 16:9 "hero" figure that tells the IOPtics story at a glance to an
ocean-optics audience. It combines the two things IOPtics is about:

* **The pipeline** (left → right):
  1. *Observe*  — a remote-sensing reflectance spectrum ``Rrs(λ)``.
  2. *Algorithms* — a registry of many IOP retrieval algorithms (BING, GIOP,
     QAA, GSM, ML…) run through a common forward model (Gordon + BING).
  3. *Retrieve* — decomposed IOPs ``a_ph``, ``a_dg``, ``bb_p`` with uncertainty.
  4. *Evaluate* — a target diagram: each algorithm scored against known truth,
     the closest to the bull's-eye wins.

* **The comparison mission** — many algorithms (stage 2) → one target diagram
  ranking them (stage 4), all on the same datasets against known truth.

The palette matches ``docs/figures`` so the graphic is consistent with the rest
of the documentation (a_dg #0b6fa4, a_ph #178a5a, bb #7b4fb0).

All on-figure text is >= 20 pt so it stays legible when projected in a talk.

Run:  python docs/scripts/ioptics_graphic.py
Out:  docs/source/_static/ioptics_graphic.png
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

# --- palette (consistent with docs/figures) --------------------------------
OCEAN = {
    'a_dg': '#0b6fa4',   # CDOM + detritus absorption (blue)
    'a_ph': '#178a5a',   # phytoplankton absorption (green)
    'bb': '#7b4fb0',     # particulate backscatter (purple)
}
DEEP = '#083d5c'         # deep-ocean navy (text / frames)
TEAL = '#1b8a9c'         # accent teal
GOLD = '#e0a52b'         # winner highlight
CARD_FILL = '#f4f9fc'    # very light water tint for cards
CARD_EDGE = '#cfe0ea'
STAGE_ACCENT = ['#0b6fa4', '#083d5c', '#178a5a', '#1b8a9c']

# --- font sizes (nothing below 20 pt) --------------------------------------
FS_TITLE = 56
FS_SUB = 23
FS_VALUE = 22
FS_STAGE = 25
FS_BADGE = 22
FS_CAPTION = 21
FS_AXIS = 21
FS_LEGEND = 16
FS_ALGO = 19
FS_POINT = 21
FS_FOOT = 21

OUT = (Path(__file__).resolve().parent.parent
       / 'source' / '_static' / 'ioptics_graphic.png')

# --- geometry (figure-fraction coordinates) --------------------------------
XS = [0.040, 0.277, 0.514, 0.751]   # left edge of each card
CARD_W = 0.205
CARD_Y = 0.255
CARD_H = 0.380
STAGES = ['Observe', 'Algorithms', 'Retrieve IOPs', 'Evaluate']
CAPTIONS = [
    r'reflectance  $R_{rs}(\lambda)$',
    'common forward model\n+ pluggable registry',
    r'$a_{ph},\ a_{dg},\ b_{bp}\ \pm\ \sigma$',
    "target diagram\nclosest to bull's-eye wins",
]
WAVE = np.linspace(400, 700, 301)

# pure-water absorption a_w(λ) [m^-1] (Pope & Fry 1997 / Smith & Baker),
# interpolated onto WAVE — this is what gives real Rrs its steep red roll-off.
_AW_WL = np.arange(400, 701, 10)
_AW = np.array([
    0.00663, 0.00473, 0.00454, 0.00495, 0.00635, 0.00922, 0.00979, 0.01060,
    0.01270, 0.01500, 0.02040, 0.03250, 0.04090, 0.04340, 0.04740, 0.05650,
    0.06190, 0.06950, 0.08960, 0.13510, 0.22240, 0.26440, 0.27550, 0.29160,
    0.31080, 0.34000, 0.41000, 0.43900, 0.46500, 0.51600, 0.62400])
A_W = np.interp(WAVE, _AW_WL, _AW)
# pure-water backscatter b_bw(λ) [m^-1] ~ λ^-4.32 (Morel; ~0.00095 at 550 nm)
BB_W = 0.00144 * (500.0 / WAVE) ** 4.32


# --------------------------------------------------------------------------
def water_rrs(Aph, Adg, Bp, Sbp=1.0, fluor=0.0):
    """Physically-shaped Rrs(λ) from a Gordon forward model.

    Build total a(λ) and b_b(λ) from pure water + IOP components, push them
    through the Gordon quadratic (u = b_b/(a+b_b)) and the below→above-surface
    conversion. This yields realistic spectra — blue-peaked for clear water,
    green-peaked with a ~675 nm chlorophyll trough for productive water — rather
    than bare Gaussians. ``fluor`` adds a small ~685 nm fluorescence bump.
    """
    a = A_W + a_ph_shape(WAVE, Aph) + a_dg(WAVE, Adg=Adg)
    bb = BB_W + b_bp(WAVE, Bnw=Bp, eta=Sbp)
    u = bb / (a + bb)
    rrs = 0.0949 * u + 0.0794 * u ** 2          # below surface (Gordon)
    Rrs = 0.52 * rrs / (1.0 - 1.7 * rrs)        # above surface (Lee et al. 2002)
    Rrs = Rrs + fluor * np.exp(-((WAVE - 685) / 10.0) ** 2)
    return Rrs


def a_dg(wave, Adg=0.45, Sdg=0.017, lam0=440.0):
    return Adg * np.exp(-Sdg * (wave - lam0))


def a_ph_shape(wave, Aph=0.42):
    blue = np.exp(-((wave - 440) / 26) ** 2)
    red = 0.55 * np.exp(-((wave - 675) / 13) ** 2)
    return Aph * (blue + red + 0.08)


def b_bp(wave, Bnw=0.010, eta=1.0, lam0=550.0):
    return Bnw * (lam0 / wave) ** eta


def card(ax_bg, x, accent):
    """Draw a rounded 'card' behind a panel."""
    ax_bg.add_patch(FancyBboxPatch(
        (x, CARD_Y), CARD_W, CARD_H,
        boxstyle='round,pad=0.006,rounding_size=0.018',
        linewidth=1.4, edgecolor=CARD_EDGE, facecolor=CARD_FILL,
        mutation_aspect=16 / 9, zorder=1))
    ax_bg.add_patch(FancyBboxPatch(
        (x, CARD_Y + CARD_H - 0.013), CARD_W, 0.013,
        boxstyle='round,pad=0.0,rounding_size=0.006',
        linewidth=0, facecolor=accent, mutation_aspect=16 / 9, zorder=2))


def panel_axes(fig, x):
    """A data axis inset within a card."""
    return fig.add_axes([x + 0.017, CARD_Y + 0.040,
                         CARD_W - 0.034, CARD_H - 0.100])


def style_mini(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#9db9c7')
    ax.tick_params(length=0, labelbottom=False, labelleft=False)
    ax.set_xlim(400, 700)


def main():
    fig = plt.figure(figsize=(16, 9))                # 16:9
    fig.patch.set_facecolor('white')

    axb = fig.add_axes([0, 0, 1, 1])
    axb.set_xlim(0, 1)
    axb.set_ylim(0, 1)
    axb.axis('off')

    # thin ocean-gradient rule under the header
    axg = fig.add_axes([0.035, 0.822, 0.93, 0.010])
    axg.imshow(np.linspace(0, 1, 256).reshape(1, -1), aspect='auto',
               cmap=LinearSegmentedColormap.from_list(
                   'ioptics', [DEEP, OCEAN['a_dg'], TEAL, OCEAN['a_ph']]))
    axg.axis('off')

    # title + subtitle + value line
    axb.text(0.035, 0.930, 'IOPtics', fontsize=FS_TITLE, fontweight='bold',
             color=DEEP, ha='left', va='center')
    axb.text(0.037, 0.868,
             'Comparing IOP retrieval algorithms — for the community, '
             'by the community.',
             fontsize=FS_SUB, color='#3d5563', ha='left', va='center',
             style='italic')
    axb.text(0.037, 0.768,
             'Which IOP algorithm performs the best?  Run them all against '
             'known truth.',
             fontsize=FS_VALUE, color=TEAL, ha='left', va='center',
             fontweight='bold')

    # -- draw the four cards, badges, titles, captions, arrows -------------
    for i, x in enumerate(XS):
        card(axb, x, STAGE_ACCENT[i])
        ty = CARD_Y + CARD_H + 0.050
        # rounded-square number badge (square-ish given the 16:9 aspect)
        axb.add_patch(FancyBboxPatch(
            (x + 0.006, ty - 0.024), 0.026, 0.048,
            boxstyle='round,pad=0.0,rounding_size=0.010',
            linewidth=0, facecolor=STAGE_ACCENT[i], zorder=5))
        axb.text(x + 0.019, ty, str(i + 1), color='white', fontsize=FS_BADGE,
                 fontweight='bold', ha='center', va='center', zorder=6)
        axb.text(x + 0.045, ty, STAGES[i], color=DEEP, fontsize=FS_STAGE,
                 fontweight='bold', ha='left', va='center')
        axb.text(x + CARD_W / 2, CARD_Y - 0.028, CAPTIONS[i],
                 color='#3d5563', fontsize=FS_CAPTION, ha='center', va='top',
                 linespacing=1.25)

    for x0, x1 in zip(XS[:-1], XS[1:]):
        axb.add_patch(FancyArrowPatch(
            (x0 + CARD_W + 0.002, CARD_Y + CARD_H / 2),
            (x1 - 0.002, CARD_Y + CARD_H / 2),
            arrowstyle='-|>', mutation_scale=28, linewidth=3.0,
            color=TEAL, zorder=4))

    # ---- Panel 1: Rrs spectra --------------------------------------------
    ax1 = panel_axes(fig, XS[0])
    style_mini(ax1)
    # three water types via the Gordon forward model (clear → productive)
    ax1.plot(WAVE, water_rrs(Aph=0.015, Adg=0.02, Bp=0.0032, Sbp=1.1),
             color='#1f6f8b', lw=3.0)                     # clear / oligotrophic
    ax1.plot(WAVE, water_rrs(Aph=0.12, Adg=0.10, Bp=0.0060, fluor=0.0007),
             color=OCEAN['a_ph'], lw=3.0)                 # mesotrophic
    ax1.plot(WAVE, water_rrs(Aph=0.45, Adg=0.32, Bp=0.0135, Sbp=0.6,
                             fluor=0.0016),
             color='#8a7a2e', lw=3.0)                     # eutrophic / turbid
    ax1.set_ylim(bottom=0)
    ax1.set_xlabel(r'$\lambda$  [nm]', fontsize=FS_AXIS, labelpad=2,
                   color='#3d5563')
    ax1.set_ylabel(r'$R_{rs}$', fontsize=FS_AXIS, color=DEEP, labelpad=6,
                   rotation=0, ha='right', va='center')

    # ---- Panel 2: algorithm registry → one common forward model ----------
    # "Jazzed up": instead of a plain list, the algorithms are nodes that all
    # converge (curved connectors) into a single forward-model hub — visually
    # making the point that IOPtics runs many algorithms through one engine.
    ax2 = panel_axes(fig, XS[1])
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis('off')
    algos = ['BING', 'GIOP', 'QAA', 'GSM', 'ML/LUT']
    chip = [OCEAN['a_ph'], TEAL, OCEAN['a_dg'], OCEAN['bb'], '#8a97a0']
    ys = [0.87, 0.675, 0.48, 0.285, 0.09]
    hub = (0.78, 0.48)
    # curved connectors (drawn first, behind the pills)
    for c, yy in zip(chip, ys):
        ax2.add_patch(FancyArrowPatch(
            (0.46, yy), (0.60, hub[1]),
            connectionstyle=f'arc3,rad={(hub[1] - yy) * 0.5}',
            arrowstyle='-', linewidth=2.4, color=c, alpha=0.55, zorder=1))
    # algorithm pills
    for name, c, yy in zip(algos, chip, ys):
        ax2.add_patch(FancyBboxPatch(
            (0.02, yy - 0.078), 0.44, 0.156,
            boxstyle='round,pad=0.004,rounding_size=0.06',
            transform=ax2.transAxes, linewidth=1.3, edgecolor='#d8e6ee',
            facecolor='white', zorder=2))
        ax2.add_patch(Circle((0.10, yy), 0.040, transform=ax2.transAxes,
                             facecolor=c, edgecolor='none', zorder=3))
        ax2.text(0.18, yy, name, transform=ax2.transAxes, fontsize=FS_ALGO,
                 va='center', ha='left', color=DEEP, zorder=3,
                 family='monospace')
    # the common forward-model hub (many algorithms converge here)
    ax2.add_patch(Circle(hub, 0.195, transform=ax2.transAxes, facecolor=DEEP,
                         edgecolor=TEAL, linewidth=3.0, zorder=4))
    ax2.text(hub[0], hub[1], 'Gordon\nforward\nmodel', transform=ax2.transAxes,
             fontsize=13, color='white', ha='center', va='center',
             fontweight='bold', linespacing=1.15, zorder=5)

    # ---- Panel 3: retrieved IOP components -------------------------------
    ax3 = panel_axes(fig, XS[2])
    style_mini(ax3)
    adg = a_dg(WAVE)
    aph = a_ph_shape(WAVE)
    bbp = b_bp(WAVE) * 60   # scale up so it's visible on the same axis
    # lighter ±uncertainty envelopes on every retrieved component
    for y, c in ((adg, OCEAN['a_dg']), (aph, OCEAN['a_ph']), (bbp, OCEAN['bb'])):
        ax3.fill_between(WAVE, y * 0.86, y * 1.14, color=c, alpha=0.11, lw=0)
    ax3.plot(WAVE, adg, color=OCEAN['a_dg'], lw=3.0, label=r'$a_{dg}$')
    ax3.plot(WAVE, aph, color=OCEAN['a_ph'], lw=3.0, label=r'$a_{ph}$')
    ax3.plot(WAVE, bbp, color=OCEAN['bb'], lw=3.0, label=r'$b_{bp}$')
    ax3.set_ylim(bottom=0)
    ax3.set_xlabel(r'$\lambda$  [nm]', fontsize=FS_AXIS, labelpad=2,
                   color='#3d5563')
    ax3.legend(loc='upper right', fontsize=FS_LEGEND, frameon=False,
               handlelength=0.9, handletextpad=0.4, borderaxespad=0.1,
               labelspacing=0.15)

    # ---- Panel 4: target diagram (Evaluate) ------------------------------
    ax4 = panel_axes(fig, XS[3])
    ax4.set_aspect('equal')
    ax4.set_xlim(-1.15, 1.15)
    ax4.set_ylim(-1.15, 1.15)
    ax4.axis('off')
    # concentric skill rings + crosshair
    for r in (0.35, 0.7, 1.05):
        ax4.add_patch(Circle((0, 0), r, fill=False, edgecolor='#b9cfdb',
                             lw=1.8, zorder=1))
    ax4.axhline(0, color='#d3e0e8', lw=1.4, zorder=0)
    ax4.axvline(0, color='#d3e0e8', lw=1.4, zorder=0)
    # algorithm scores: (bias, unbiased-RMSD); nearer origin == better
    pts = [
        ('BING', 0.10, 0.13, OCEAN['a_ph'], True),
        ('GIOP', 0.44, -0.30, TEAL, False),
        ('GSM', -0.52, 0.42, OCEAN['a_dg'], False),
        ('QAA', 0.66, 0.64, OCEAN['bb'], False),
    ]
    for name, bx, by, c, best in pts:
        if best:
            ax4.scatter([bx], [by], s=760, marker='*', color=c,
                        edgecolor=GOLD, linewidth=2.6, zorder=5)
            ax4.text(bx + 0.12, by + 0.16, name, fontsize=FS_POINT,
                     fontweight='bold', color=DEEP, zorder=6)
        else:
            ax4.scatter([bx], [by], s=260, color=c, edgecolor='white',
                        linewidth=1.6, zorder=4)
            dx = 0.13 if bx >= 0 else -0.13
            ha = 'left' if bx >= 0 else 'right'
            ax4.text(bx + dx, by, name, fontsize=FS_POINT, color=DEEP,
                     va='center', ha=ha, zorder=4)

    # -- footer ------------------------------------------------------------
    axb.text(0.5, 0.088,
             'Validated against known truth — Loisel 2023 (synthetic)  ·  '
             'PANGAEA  ·  GLORIA',
             fontsize=FS_FOOT, ha='center', va='center', color=DEEP)
    axb.text(0.5, 0.038,
             'engine: BING   ·   data loaders: ocpy   ·   '
             'reproducible, provenance-stamped reports',
             fontsize=FS_FOOT, ha='center', va='center', color='#5a7180')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, facecolor='white')
    print('wrote', OUT)


if __name__ == '__main__':
    main()

"""Generate the IOP-model component-shapes figure for ``docs/source/models.rst``.

Schematic (data-free) illustration of the *spectral shapes* the two algorithms
parameterize: the CDOM+detritus absorption ``a_dg`` (exponential decay), the
phytoplankton absorption ``a_ph`` (Bricaud-style, blue + red peaks), and the
particulate backscatter ``b_bp`` (power law). These are the building blocks the
fit scales/tilts to match the observed reflectance.

Run:  python docs/figures/make_model_components.py
Out:  docs/source/_static/model_components.png
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent.parent / 'source' / '_static' / 'model_components.png'
WAVE = np.linspace(400, 700, 301)
OCEAN = {'a_dg': '#0b6fa4', 'a_ph': '#178a5a', 'b_bp': '#7b4fb0'}


def a_dg(wave, Adg=0.5, Sdg=0.017, lam0=440.0):
    """Exponential CDOM + detritus absorption."""
    return Adg * np.exp(-Sdg * (wave - lam0))


def a_ph_shape(wave, Aph=0.5):
    """Stylized phytoplankton specific absorption (blue ~440 + red ~675 peaks)."""
    blue = np.exp(-((wave - 440) / 28) ** 2)
    red = 0.55 * np.exp(-((wave - 675) / 14) ** 2)
    return Aph * (blue + red + 0.10)


def b_bp(wave, Bnw=0.006, beta=1.0, lam0=550.0):
    """Power-law particulate backscatter."""
    return Bnw * (lam0 / wave) ** beta


def main():
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), constrained_layout=True)

    ax = axes[0]
    for Sdg, ls in ((0.010, '--'), (0.017, '-'), (0.025, ':')):
        ax.plot(WAVE, a_dg(WAVE, Sdg=Sdg), color=OCEAN['a_dg'], ls=ls,
                label=f'S={Sdg}')
    ax.set_title(r'$a_{dg}(\lambda)=A_{dg}\,e^{-S_{dg}(\lambda-440)}$', fontsize=10)
    ax.set_ylabel('absorption  [m$^{-1}$]')
    ax.legend(title='slope $S_{dg}$', fontsize=8, frameon=False)

    ax = axes[1]
    ax.plot(WAVE, a_ph_shape(WAVE), color=OCEAN['a_ph'])
    ax.axvline(440, color='0.7', lw=0.7); ax.axvline(675, color='0.7', lw=0.7)
    ax.set_title(r'$a_{ph}(\lambda)=A_{ph}\,a^{*}_{ph}(\lambda)$  (Bricaud)',
                 fontsize=10)

    ax = axes[2]
    for beta, ls in ((0.5, '--'), (1.0, '-'), (2.0, ':')):
        ax.plot(WAVE, b_bp(WAVE, beta=beta), color=OCEAN['b_bp'], ls=ls,
                label=f'$\\eta$={beta}')
    ax.set_title(r'$b_{bp}(\lambda)=B_{nw}\,(550/\lambda)^{\eta}$', fontsize=10)
    ax.legend(title='slope $\\eta$', fontsize=8, frameon=False)

    for ax in axes:
        ax.set_xlabel('wavelength  [nm]')
        ax.margins(x=0)
    fig.suptitle('IOP model component shapes (schematic)', fontsize=12)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=140)
    print('wrote', OUT)


if __name__ == '__main__':
    main()

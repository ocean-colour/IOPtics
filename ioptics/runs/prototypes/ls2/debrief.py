"""The LS2 debrief page (ls2 task 15).

Three questions, answered from the sweeps and the task-14 tables, so every
number on ``docs/source/reports/ls2_debrief/`` is regenerated here:

1. **Totals against decomposition.**  LS2 returns ``a``, ``a_nw``, ``bb``,
   ``bb_p`` and no ``a_ph``/``a_dg``; BING returns all six.  How do the
   totals compare, and what does BING's decomposition amount to?
2. **What the two side chains cost.**  The Chl/b_p chain is rung (i) to (ii):
   true ``b_p`` replaced by OC4v4 chlorophyll and ``bp_from_chla``.  The Kd
   chain is rung (ii) to (iii): true ``<Kd>_1`` replaced by a network.  Both
   are measured on the held-out X=4 sweep, so the L23-trained network can
   take part, with the published and re-derived tables side by side.
3. **What the re-derivation changed** (tasks 10-13): the rung (i) headline,
   κ availability, and operational accuracy.

Usage, from the repository root (after ``build_v1.py`` 1-2 and
``ours_report.py``)::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \\
        ioptics/runs/prototypes/ls2/debrief.py [--docs-root DIR]
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

SID = 'ls2_debrief'
REPO = Path(__file__).resolve().parents[4]
DEFAULT_DOCS = REPO / 'docs' / 'source'
HELDOUT = 'ls2_l23_x4_heldout_v1'
CELLS = (('a', 440), ('a_nw', 440), ('bb', 555), ('bb_p', 555))
#: ``(chain, tables, from rung, to rung)``
CHAINS = (('Chl/b_p', 'published', 'ls2_i', 'ls2_ii'),
          ('Chl/b_p', 're-derived', 'ls2r_i', 'ls2r_ii'),
          ('Kd (PACE v2.3)', 'published', 'ls2_ii', 'ls2_iii'),
          ('Kd (MODIS v1.3)', 'published', 'ls2_ii', 'ls2_iii_modis'),
          ('Kd (PACE v2.3)', 're-derived', 'ls2r_ii', 'ls2r_iii'),
          ('Kd (our L23 network)', 're-derived', 'ls2r_ii', 'ls2r_iii_l23'))


def side_chains():
    """mae before and after each side chain, per ladder cell (held-out X=4)."""
    from ioptics.algorithms import registry
    from ioptics.report import figures, ls2_ladder
    registry.register_direct()
    registry.register_direct_l23()
    lad = ls2_ladder.ladder_table(figures.load(HELDOUT), write=False).set_index('rung')
    rows = []
    for chain, tables, r0, r1 in CHAINS:
        row = {'side_chain': chain, 'tables': tables, 'from': r0, 'to': r1}
        for comp, ref in CELLS:
            col = f'{comp}_{ref}_mae'
            m0, m1 = float(lad.loc[r0, col]), float(lad.loc[r1, col])
            row[f'{comp}_{ref}_mae_before'] = round(m0, 4)
            row[f'{comp}_{ref}_mae_after'] = round(m1, 4)
            row[f'{comp}_{ref}_cost_pp'] = round(100 * (m1 - m0), 2)
        rows.append(row)
    return pd.DataFrame(rows)


def _ours_tables(docs_root):
    d = docs_root / 'reports' / 'ls2_ours'
    return (pd.read_csv(d / 'ours_headline.csv'),
            pd.read_csv(d / 'ours_vs_bing_heldout.csv'))


def _tbl(caption, name):
    return (f'.. csv-table:: {caption}\n   :file: {name}\n   :header-rows: 1\n'
            f'   :widths: auto\n')


def build(docs_root=None):
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS
    out = docs_root / 'reports' / SID
    out.mkdir(parents=True, exist_ok=True)
    sc = side_chains()
    sc.to_csv(out / 'debrief_side_chains.csv', index=False)
    src = docs_root / 'reports' / 'ls2_ours'
    if not (src / 'ours_headline.csv').is_file():         # a scratch docs root
        src = DEFAULT_DOCS / 'reports' / 'ls2_ours'
    head = pd.read_csv(src / 'ours_headline.csv')
    vb = pd.read_csv(src / 'ours_vs_bing_heldout.csv')
    bing = _bing_decomposition()
    (out / f'{SID}.rst').write_text(_page(sc, head, vb, bing), encoding='utf-8')
    print(f'wrote {out / (SID + ".rst")}')
    return sc


def _bing_decomposition():
    from ioptics.report import figures
    ms = figures.load('rt_tests_A_l23_v1').metrics_scalar
    col = 'pool' if 'pool' in ms.columns else 'fit_method'
    g = ms[(ms.algorithm == 'expb_pow_hyb_ramfl') & (ms[col] == 'mcmc')
           & (ms.stratum == 'all') & (ms.ref_wave == 440.0)]
    return {c: float(g[g.component == c]['mae'].iloc[0])
            for c in ('a', 'a_ph', 'a_dg', 'a_nw') if (g.component == c).any()}


def _page(sc, head, vb, bing):
    pu = lambda v: f'{100 * float(v):.1f}%'                  # noqa: E731
    pp = lambda v: f'{float(v):+.1f} pp'                     # noqa: E731
    pc = lambda v: f'{100 * float(v):+.1f}%'                 # noqa: E731
    S = sc.set_index(['side_chain', 'tables'])
    H = head.set_index(['theta_s', 'tables'])
    V = vb.set_index(['rung', 'component', 'scope'])
    hp, ho = H.loc[(0, 'published')], H.loc[(0, 'our LS2 (refit a/bb + κ)')]
    hab = H.loc[(0, 'refit a/bb + published κ')]
    ab_pts = 100 * (hp['bb_median_err'] - hab['bb_median_err'])
    k_pts = 100 * (hab['bb_median_err'] - ho['bb_median_err'])
    bp_pub, bp_red = S.loc[('Chl/b_p', 'published')], S.loc[('Chl/b_p', 're-derived')]
    kd_pace = S.loc[('Kd (PACE v2.3)', 'published')]
    kd_modis = S.loc[('Kd (MODIS v1.3)', 'published')]
    kd_ours = S.loc[('Kd (our L23 network)', 're-derived')]
    v = lambda r, c, s='440 nm': V.loc[(r, c, s)]           # noqa: E731
    return f"""\
.. _ls2_debrief:

=============
LS2 — debrief
=============

:Task: ls2 task 15
:Script: ``ioptics/runs/prototypes/ls2/debrief.py`` (every number on this page)
:Built on: :ref:`ls2_ours` (task 14), the held-out X=4 ladder
   (``ls2_l23_x4_heldout_v1``), and RT-A's MCMC BING

LS2 (Loisel et al. 2018) was brought into IOPtics as the first **direct**
algorithm.  It has no fit, no likelihood, and returns totals only.  It was run
as a ladder of inputs, so that what LS2 costs could be separated from what
its inputs cost, and then rebuilt from L23 to see how much of its error was
avoidable.

1. Totals against decomposition
-------------------------------

LS2 returns the totals ``a`` and ``bb`` and their non-water parts ``a_nw``
and ``bb_p``.  It returns **no** ``a_ph`` and **no** ``a_dg``.  BING returns
all six.  On L23 X=4 (held-out spectra, MCMC BING ``expb_pow_hyb_ramfl``):

* **Absorption totals: LS2 is as good or better.**  At 440 nm, our LS2 with
  true inputs has ``a`` mae {pu(v('ls2r_i', 'a')['mae_ls2'])} against BING's
  {pu(v('ls2r_i', 'a')['mae_bing'])}.  Operationally, with our L23 Kd network,
  it is {pu(v('ls2r_iii_l23', 'a')['mae_ls2'])} against
  {pu(v('ls2r_iii_l23', 'a')['mae_bing'])}.
* **Backscattering totals: BING is better by far.**  At 555 nm ``bb`` mae is
  {pu(v('ls2r_i', 'bb', '555 nm')['mae_ls2'])} (LS2, true inputs) against
  {pu(v('ls2r_i', 'bb', '555 nm')['mae_bing'])}.  LS2 inverts band by band and
  inherits each band's Rrs noise; BING fits one model to the whole spectrum.
* **The decomposition.**  BING's ``a_ph(440)`` mae is {pu(bing['a_ph'])} and
  its ``a_dg(440)`` {pu(bing['a_dg'])}, against {pu(bing['a'])} for its own
  total ``a(440)``.  The split is where BING's error lives.  An algorithm that
  declines to split, as LS2 does, gives up those two numbers and their large
  errors.  Its ``a_nw`` is in effect BING's ``a_dg + a_ph`` without the split:
  {pu(v('ls2r_i', 'a_nw')['mae_ls2'])} for LS2 against
  {pu(v('ls2r_i', 'a_nw')['mae_bing'])} for BING at 440 nm.

So the trade is real and one-sided per component.  For totals of absorption,
LS2 (with a good Kd) is competitive or better.  For backscattering, the
full-spectrum fit wins.  For the decomposition, LS2 has nothing to offer and
says so, as an explicit "not applicable", not a missing row.

2. What the two side chains cost
--------------------------------

Measured on the held-out X=4 spectra (PACE noise), as the change in mae when
one true input is replaced by its operational estimate.

* **The Chl/b_p chain is cheap in absolute terms.**  ``b_p`` enters LS2 only
  through η = b_w/(b_p + b_w), which picks the table row.  Replacing true
  ``b_p`` with OC4v4 chlorophyll and ``bp_from_chla`` costs ``a(440)``
  {pp(bp_pub['a_440_cost_pp'])} and ``bb(555)`` {pp(bp_pub['bb_555_cost_pp'])}
  with the published tables, and {pp(bp_red['a_440_cost_pp'])} and
  {pp(bp_red['bb_555_cost_pp'])} with ours.  Against our much smaller error
  with true inputs, that takes ``a(440)`` from
  {pu(bp_red['a_440_mae_before'])} to {pu(bp_red['a_440_mae_after'])}: the
  re-derived tables are more sensitive to a wrong η than the published ones,
  whose error elsewhere dwarfs it.
* **The Kd chain is the expensive one, and how expensive depends entirely on
  the network.**  Replacing true ⟨Kd⟩₁ costs ``a(440)``:
  {pp(kd_pace['a_440_cost_pp'])} with the authors' PACE v2.3 network,
  {pp(kd_modis['a_440_cost_pp'])} with their MODIS v1.3, and
  {pp(kd_ours['a_440_cost_pp'])} with our L23-trained network.  ``a`` scales
  as Kd, so a Kd error is an ``a`` error.  The Kd-noise ladder on the sweep
  pages gives the slope.

{_tbl('Side-chain costs on the held-out X=4 spectra: mae before and after each replacement, per cell, and the cost in percentage points.', 'debrief_side_chains.csv')}
3. What the re-derivation changed
---------------------------------

Tasks 10–13 rebuilt LS2's three learned pieces from L23: the Kd network, the
a/bb tables and κ.

* **Rung (i), noise-free, θs = 0°, held-out**: ``a`` {pc(hp['a_median_err'])}
  → {pc(ho['a_median_err'])}; ``bb`` {pc(hp['bb_median_err'])} →
  {pc(ho['bb_median_err'])}; ``bb_p`` {pc(hp['bb_p_median_err'])} →
  {pc(ho['bb_p_median_err'])}.  The ``a`` bias was illumination bookkeeping:
  L23's sky is not a Snell beam.  Of ``bb``'s, the a/bb refit removed
  {ab_pts:.1f} points and κ {k_pts:.1f}, and {100 * ho['bb_median_err']:.1f}
  remain at θs = 0° (κ's sun dependence or X=4 fluorescence; not separated).
* **κ availability**: unavailable on {pu(hp['kappa_unavailable'])} of cells with
  the published table, {pu(ho['kappa_unavailable'])} with ours.
* **Operational ``a(440)``**: {pu(v('ls2_iii', 'a')['mae_ls2'])} published
  (PACE network, published tables), {pu(v('ls2r_iii', 'a')['mae_ls2'])} with our
  tables and the same network, {pu(v('ls2r_iii_l23', 'a')['mae_ls2'])} with our
  tables and our network.  Almost all of the gain is the Kd network.
* **What it did not change**: the band-by-band noise sensitivity of ``bb``
  and ``bb_p``, which is structural, and the absence of a decomposition,
  which is the design.

Caveats
-------

* Everything is L23.  The re-derived pieces were fitted on L23 and scored on
  held-out L23 scenarios.  Real water (PANGAEA) attenuates more than L23
  predicts from the same Rrs (task 11), so our operational numbers are L23
  numbers.  The leaderboard therefore carries only the published operational
  LS2 (ls2 Q41).
* κ's sun dependence and Chl fluorescence (X=4) remain uncorrected.
"""


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--docs-root', default=None)
    build(p.parse_args().docs_root)

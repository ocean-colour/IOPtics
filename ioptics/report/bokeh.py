"""Standalone/static BokehJS interactive figures.

Self-contained BokehJS HTML (no Bokeh server): a ``ColumnDataSource`` holds the
full data and ``Select`` widgets drive ``CustomJS`` callbacks that repopulate a
visible source — so a reader can pick algorithm / component / stratum and
inspect retrieved-vs-true scatter (hover/pan/zoom) or filter the leaderboard.
Rendered via :func:`bokeh.embed.file_html` with **inline** resources, so the
``.html`` works offline and embeds directly in the readthedocs site.

Consumes only persisted artifacts (results + metrics + leaderboard); no
re-fitting. Returns HTML **strings** — the ``report`` layer writes them out.
"""

from __future__ import annotations

import numpy as np

from bokeh.embed import file_html
from bokeh.layouts import column
from bokeh.models import (ColumnDataSource, CustomJS, DataTable, HoverTool,
                          Select, TableColumn)
from bokeh.plotting import figure
from bokeh.resources import INLINE

from ioptics import metrics
from ioptics.report import figures

# Fields carried in the scatter data source (all filterable keys + coords).
_SCATTER_FIELDS = ['x', 'y', 'algorithm', 'component', 'stratum', 'wavelength']


def _scatter_points(sweep, fit_method):
    """Long retrieved-vs-true points (+ per-obs stratum, incl. an 'all' scope)."""
    import pandas as pd

    sp = sweep.spectral
    sp = sp[(sp['fit_method'] == fit_method)
            & sp['component'].isin(metrics.ACCURACY_COMPONENTS)]
    strata = metrics._strata_map(sweep.scalar)
    sp = sp.merge(strata, on=['dataset', 'obs_id'], how='left')
    sp = sp[np.isfinite(sp['value']) & np.isfinite(sp['truth'])
            & (sp['value'] > 0) & (sp['truth'] > 0)]
    pts = pd.DataFrame({
        'x': sp['truth'].to_numpy(dtype=float),
        'y': sp['value'].to_numpy(dtype=float),
        'algorithm': sp['algorithm'].astype(str).to_numpy(),
        'component': sp['component'].astype(str).to_numpy(),
        'stratum': sp['stratum'].astype(str).to_numpy(),
        'wavelength': sp['wavelength'].to_numpy(dtype=float),
    })
    # add an 'all' stratum scope (mirrors the metrics `_scoped` union)
    return pd.concat([pts.assign(stratum='all'), pts], ignore_index=True)


def _filter_js(fields):
    """CustomJS that rebuilds ``src`` from ``full`` where the three Selects match."""
    pushes = '\n'.join(f"    o['{f}'].push(d['{f}'][i]);" for f in fields)
    init = ', '.join(f"'{f}': []" for f in fields)
    return CustomJS(code=f"""
    const d = full.data;
    const o = {{{init}}};
    for (let i = 0; i < d['algorithm'].length; i++) {{
      if (d['algorithm'][i] === selA.value
          && d['component'][i] === selC.value
          && d['stratum'][i] === selS.value) {{
{pushes}
      }}
    }}
    src.data = o;
    src.change.emit();
    """)


def interactive_scatter(sweep, *, root=None, fit_method='chisq',
                        title='IOPtics — retrieved vs. true'):
    """Self-contained HTML: retrieved-vs-true scatter with algorithm/component/
    stratum selectors (hover/pan/zoom, log-log, 1:1 guide).

    ``sweep`` is a ``sweep_id`` or a :class:`~ioptics.report.figures.SweepArtifacts`
    bundle. Returns the standalone HTML string.
    """
    sweep = figures.resolve(sweep, root)
    pts = _scatter_points(sweep, fit_method)

    algos = sorted(pts['algorithm'].unique())
    comps = sorted(pts['component'].unique())
    strata = sorted(pts['stratum'].unique())
    a0 = algos[0] if algos else ''
    c0 = 'a' if 'a' in comps else (comps[0] if comps else '')
    s0 = 'all' if 'all' in strata else (strata[0] if strata else '')

    full = ColumnDataSource({f: pts[f].tolist() for f in _SCATTER_FIELDS})
    init = pts[(pts.algorithm == a0) & (pts.component == c0)
               & (pts.stratum == s0)]
    src = ColumnDataSource({f: init[f].tolist() for f in _SCATTER_FIELDS})

    fig = figure(title=title, x_axis_type='log', y_axis_type='log',
                 x_axis_label='truth', y_axis_label='retrieved',
                 width=560, height=520, tools='pan,box_zoom,wheel_zoom,reset,save')
    fig.scatter('x', 'y', source=src, size=6, alpha=0.6)
    if len(pts):
        lo = float(min(pts['x'].min(), pts['y'].min()))
        hi = float(max(pts['x'].max(), pts['y'].max()))
        fig.line([lo, hi], [lo, hi], color='gray', line_dash='dashed')
    fig.add_tools(HoverTool(tooltips=[('algorithm', '@algorithm'),
                                      ('component', '@component'),
                                      ('λ', '@wavelength'),
                                      ('truth', '@x'), ('retrieved', '@y')]))

    sel_a = Select(title='algorithm', value=a0, options=algos)
    sel_c = Select(title='component', value=c0, options=comps)
    sel_s = Select(title='stratum', value=s0, options=strata)
    cb = _filter_js(_SCATTER_FIELDS)
    cb.args = {'full': full, 'src': src, 'selA': sel_a, 'selC': sel_c,
               'selS': sel_s}
    for sel in (sel_a, sel_c, sel_s):
        sel.js_on_change('value', cb)

    layout = column(sel_a, sel_c, sel_s, fig)
    return file_html(layout, INLINE, title)


def interactive_leaderboard(runs_root=None, *, root=None, out=None, board=None,
                            title='IOPtics — leaderboard'):
    """Self-contained HTML: the ranked leaderboard as a filterable table.

    Reads the persisted ``leaderboard.parquet`` (or an in-memory ``board``),
    ranks it, and renders a Bokeh ``DataTable`` with dataset/component/stratum
    selectors. Returns the standalone HTML string.
    """
    import pandas as pd
    from pathlib import Path

    from ioptics import io
    from ioptics.report import leaderboard as lb

    if board is None:
        if out is not None:
            path = Path(out)
        else:
            runs = Path(runs_root) if runs_root is not None \
                else io.runs_root(root)
            path = lb._default_out(runs)
        board = pd.read_parquet(path)
    df = lb.ranked(board)

    cols = [c for c in ['rank', 'dataset', 'component', 'ref_wave', 'stratum',
                        'algorithm', 'win_frac', 'bias', 'mae', 'coverage68',
                        'coverage95'] if c in df.columns]
    df = df[cols]
    full = ColumnDataSource({c: df[c].astype(object).tolist() for c in cols})
    init = df[df['stratum'] == 'all'] if 'stratum' in df else df
    src = ColumnDataSource({c: init[c].astype(object).tolist() for c in cols})

    table = DataTable(source=src,
                      columns=[TableColumn(field=c, title=c) for c in cols],
                      width=820, height=420)

    def _opts(col):
        return sorted(str(v) for v in df[col].unique()) if col in df else []

    sel_d = Select(title='dataset', value='', options=[''] + _opts('dataset'))
    sel_c = Select(title='component', value='', options=[''] + _opts('component'))
    sel_s = Select(title='stratum', value='all', options=[''] + _opts('stratum'))
    pushes = '\n'.join(f"    o['{c}'].push(d['{c}'][i]);" for c in cols)
    init_js = ', '.join(f"'{c}': []" for c in cols)
    cb = CustomJS(args={'full': full, 'src': src, 'selD': sel_d, 'selC': sel_c,
                        'selS': sel_s},
                  code=f"""
    const d = full.data;
    const o = {{{init_js}}};
    for (let i = 0; i < d['algorithm'].length; i++) {{
      if ((selD.value === '' || String(d['dataset'][i]) === selD.value)
          && (selC.value === '' || String(d['component'][i]) === selC.value)
          && (selS.value === '' || String(d['stratum'][i]) === selS.value)) {{
{pushes}
      }}
    }}
    src.data = o;
    src.change.emit();
    """)
    for sel in (sel_d, sel_c, sel_s):
        sel.js_on_change('value', cb)

    layout = column(sel_d, sel_c, sel_s, table)
    return file_html(layout, INLINE, title)

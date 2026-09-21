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

from bokeh.embed import components, file_html
from bokeh.layouts import column
from bokeh.models import (ColumnDataSource, CustomJS, DataTable, HoverTool,
                          Select, TableColumn)
from bokeh.plotting import figure
from bokeh.resources import CDN, INLINE

from ioptics import metrics
from ioptics.report import figures

# Fields carried in the scatter data source (all filterable keys + coords).
_SCATTER_FIELDS = ['x', 'y', 'dataset', 'algorithm', 'component', 'stratum',
                   'wavelength', 'obs_id']
# Cap on points serialized into the interactive scatter: the whole cloud is
# baked into the page (self-contained HTML / inline embed), so an un-capped
# full sweep (~5M points) would be hundreds of MB. Downsample to keep the
# artifact light; the static PNG scatters already summarize the full population.
SCATTER_MAX_POINTS = 3000
SCATTER_SEED = 1234


def _downsample(pts, max_points=SCATTER_MAX_POINTS, seed=SCATTER_SEED):
    """Cap ``pts`` near ``max_points``, stratified by algorithm/component/stratum.

    Each ``(algorithm, component, stratum)`` group is capped at
    ``max_points // n_groups`` (seeded) so every selectable combination keeps a
    representative sample and the total never exceeds ``max_points``.
    """
    if len(pts) <= max_points:
        return pts
    by = ['algorithm', 'component', 'stratum']
    per = max(1, max_points // max(pts.groupby(by).ngroups, 1))
    # shuffle (seeded) then take the first `per` of each group -> a random,
    # reproducible per-group cap that keeps every group and all columns.
    shuffled = pts.sample(frac=1, random_state=seed)
    return (shuffled.groupby(by, group_keys=False, sort=False)
                    .head(per).reset_index(drop=True))


def _scatter_points(sweep, fit_method, *, max_points=SCATTER_MAX_POINTS,
                    with_total=False):
    """Long retrieved-vs-true points (+ per-obs stratum, incl. an 'all' scope).

    Downsampled to ``max_points`` (stratified) so the interactive figure stays
    light when baked into the page (see :data:`SCATTER_MAX_POINTS`).
    ``with_total=True`` also returns the pre-downsample count, so the figure can
    state what fraction of the population a reader is actually looking at.
    """
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
        'dataset': sp['dataset'].astype(str).to_numpy(),
        'algorithm': sp['algorithm'].astype(str).to_numpy(),
        'component': sp['component'].astype(str).to_numpy(),
        'stratum': sp['stratum'].astype(str).to_numpy(),
        'wavelength': sp['wavelength'].to_numpy(dtype=float),
        # as str: obs ids are dataset-defined (GLORIA's are 'GID_1')
        'obs_id': sp['obs_id'].astype(str).to_numpy(),
    })
    # add an 'all' stratum scope (mirrors the metrics `_scoped` union)
    pts = pd.concat([pts.assign(stratum='all'), pts], ignore_index=True)
    n_total = len(pts)
    out = _downsample(pts, max_points=max_points)
    return (out, n_total) if with_total else out


def _filter_js(fields):
    """CustomJS that rebuilds ``src`` from ``full`` where the four Selects match."""
    pushes = '\n'.join(f"    o['{f}'].push(d['{f}'][i]);" for f in fields)
    init = ', '.join(f"'{f}': []" for f in fields)
    return CustomJS(code=f"""
    const d = full.data;
    const o = {{{init}}};
    for (let i = 0; i < d['algorithm'].length; i++) {{
      if (d['dataset'][i] === selD.value
          && d['algorithm'][i] === selA.value
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
    bundle. Returns the standalone HTML string (BokehJS inlined). For embedding
    inside a Sphinx page use :func:`scatter_embed` instead.
    """
    sweep = figures.resolve(sweep, root)
    layout = _scatter_layout(sweep, fit_method, title)
    return file_html(layout, INLINE, title)


def _scatter_layout(sweep, fit_method, title):
    """Build the interactive scatter Bokeh layout (selectors + figure).

    The subtitle states the sampling fraction: the cloud is downsampled to keep the
    page small, and a reader who is not told assumes they are seeing everything.
    """
    pts, n_total = _scatter_points(sweep, fit_method, with_total=True)

    datasets = sorted(pts['dataset'].unique())
    algos = sorted(pts['algorithm'].unique())
    comps = sorted(pts['component'].unique())
    strata = sorted(pts['stratum'].unique())
    d0 = datasets[0] if datasets else ''
    a0 = algos[0] if algos else ''
    c0 = 'a' if 'a' in comps else (comps[0] if comps else '')
    s0 = 'all' if 'all' in strata else (strata[0] if strata else '')

    full = ColumnDataSource({f: pts[f].tolist() for f in _SCATTER_FIELDS})
    init = pts[(pts.dataset == d0) & (pts.algorithm == a0)
               & (pts.component == c0) & (pts.stratum == s0)]
    src = ColumnDataSource({f: init[f].tolist() for f in _SCATTER_FIELDS})

    shown = len(pts)
    if n_total and shown < n_total:
        title = (f'{title}  ({shown:,} of {n_total:,} points shown — '
                 f'{shown / n_total:.0%}, stratified sample)')
    elif n_total:
        title = f'{title}  ({shown:,} points — all of them)'
    fig = figure(title=title, x_axis_type='log', y_axis_type='log',
                 x_axis_label='truth', y_axis_label='retrieved',
                 width=560, height=520, tools='pan,box_zoom,wheel_zoom,reset,save')
    fig.scatter('x', 'y', source=src, size=6, alpha=0.6)
    if len(pts):
        lo = float(min(pts['x'].min(), pts['y'].min()))
        hi = float(max(pts['x'].max(), pts['y'].max()))
        fig.line([lo, hi], [lo, hi], color='gray', line_dash='dashed')
    # ``obs_id`` is the point of the hover: without it a reader can see an outlier
    # but cannot go and look at that spectrum.
    fig.add_tools(HoverTool(tooltips=[('obs_id', '@obs_id'),
                                      ('algorithm', '@algorithm'),
                                      ('component', '@component'),
                                      ('λ', '@wavelength'),
                                      ('truth', '@x'), ('retrieved', '@y')]))

    sel_d = Select(title='dataset', value=d0, options=datasets)
    sel_a = Select(title='algorithm', value=a0, options=algos)
    sel_c = Select(title='component', value=c0, options=comps)
    sel_s = Select(title='stratum', value=s0, options=strata)
    cb = _filter_js(_SCATTER_FIELDS)
    cb.args = {'full': full, 'src': src, 'selD': sel_d, 'selA': sel_a,
               'selC': sel_c, 'selS': sel_s}
    for sel in (sel_d, sel_a, sel_c, sel_s):
        sel.js_on_change('value', cb)
    return column(sel_d, sel_a, sel_c, sel_s, fig)


# --------------------------------------------------------------------------- #
# vendored BokehJS (no CDN at view time)
# --------------------------------------------------------------------------- #
#: BokehJS bundles a report page actually needs. ``CDN.render()`` emits five
#: unconditionally; the scatter uses ``Select`` widgets and a hover, so ``bokeh`` +
#: ``bokeh-widgets`` cover it, and the leaderboard's ``DataTable`` adds
#: ``bokeh-tables``. Dropping ``bokeh-gl``/``bokeh-mathjax`` is free.
SCATTER_BUNDLES = ('bokeh', 'bokeh-widgets')
TABLE_BUNDLES = ('bokeh', 'bokeh-widgets', 'bokeh-tables')

#: Where the vendored JS lands under the Sphinx source tree.
VENDOR_SUBDIR = 'bokeh'


def _bundle_filename(name, version):
    """Versioned vendored filename, e.g. ``bokeh-widgets-3.9.1.min.js``.

    Versioned on purpose: report fragments are **committed and never regenerated**,
    so an unversioned ``bokeh.min.js`` would silently re-point every historical page
    at a newer BokehJS the moment the environment is upgraded. Old pages keep
    working because their own version stays on disk.
    """
    return f'{name}-{version}.min.js'


def vendor_bokehjs(static_dir, *, bundles=SCATTER_BUNDLES):
    """Copy the needed BokehJS bundles into ``<static_dir>/bokeh/`` (idempotent).

    Sourced from the **installed** bokeh — the same one that serialized the
    figure's ``docs_json`` — so the JS and the data format cannot drift apart at
    generation time. Returns the list of copied/existing file names.

    Vendoring rather than loading ``cdn.bokeh.org`` is what makes a published page
    work offline, behind a restrictive CSP, and years from now when the CDN has
    moved on. It costs ~1.6 MB in the repo **once**, against ~1.6 MB added to every
    committed page if BokehJS were inlined instead.
    """
    import shutil
    from pathlib import Path

    import bokeh as _bokeh
    from bokeh.resources import Resources

    dest = Path(static_dir) / VENDOR_SUBDIR
    dest.mkdir(parents=True, exist_ok=True)
    srcs = Resources(mode='absolute', minified=True,
                     components=list(bundles)).js_files
    names = []
    for src in srcs:
        src = Path(src)
        stem = src.name.replace('.min.js', '')
        name = _bundle_filename(stem, _bokeh.__version__)
        target = dest / name
        # Copy-if-missing is not enough: an interrupted copy would leave a
        # truncated bundle in place forever and every figure would silently fail.
        if not target.is_file() or target.stat().st_size != src.stat().st_size:
            shutil.copy2(src, target)
        names.append(name)
    return names


def local_script_tags(static_prefix, *, bundles=SCATTER_BUNDLES):
    """``<script src=...>`` tags pointing at the vendored bundles.

    ``static_prefix`` is the path from the **page** to ``_static`` — ``'../../'``
    for ``reports/<sweep>/<kind>.html``, ``'../'`` for ``reports/index.html``.
    Hand-built because no ``bokeh.resources`` mode emits a clean arbitrary relative
    prefix (``'relative'`` points into the Python environment; ``'server'``
    hard-codes a ``static/js/`` infix).

    NOTE: the depth is baked into the committed page, so switching Sphinx to the
    ``dirhtml`` builder (which adds a directory level per page) would break every
    generated fragment.
    """
    import bokeh as _bokeh

    version = _bokeh.__version__
    return '\n'.join(
        f'<script src="{static_prefix}_static/{VENDOR_SUBDIR}/'
        f'{_bundle_filename(b, version)}"></script>' for b in bundles)


def scatter_embed(sweep, *, root=None, fit_method='chisq',
                  title='Retrieved vs. true', static_prefix='../../'):
    """Embeddable interactive scatter for a **Sphinx page** (no separate file).

    Returns an HTML fragment — ``<script>`` tags for the **vendored** BokehJS plus
    the ``bokeh.embed.components`` ``<div>``+``<script>`` — to drop straight into a
    page via ``.. raw:: html``. Unlike :func:`interactive_scatter` (a standalone
    file), this renders inline so it survives a Sphinx/RTD build without needing
    the HTML file copied into the output tree, and the component ``script``/``div``
    are pre-generated so RTD needs no Bokeh install.

    The scripts point at ``<static_prefix>_static/bokeh/`` (see
    :func:`vendor_bokehjs`), **not** at ``cdn.bokeh.org``: a CDN dependency makes a
    published figure fail offline, behind a strict CSP, and eventually when the CDN
    version moves — the two committed pages had already drifted to different pinned
    versions.
    """
    sweep = figures.resolve(sweep, root)
    layout = _scatter_layout(sweep, fit_method, title)
    script, div = components(layout)
    tags = local_script_tags(static_prefix, bundles=SCATTER_BUNDLES)
    return f'{tags}\n{div}\n{script}'


def leaderboard_embed(runs_root=None, *, root=None, out=None, board=None,
                      title='Leaderboard', static_prefix='../'):
    """Embeddable interactive leaderboard fragment (for the landing page).

    The filterable ``DataTable`` counterpart of :func:`scatter_embed` — the widget
    existed but nothing ever put it on a page, so the landing page carried a
    2 400-line static table instead.
    """
    layout = _leaderboard_layout(runs_root=runs_root, root=root, out=out,
                                 board=board)
    script, div = components(layout)
    tags = local_script_tags(static_prefix, bundles=TABLE_BUNDLES)
    return f'{tags}\n{div}\n{script}'


def interactive_leaderboard(runs_root=None, *, root=None, out=None, board=None,
                            title='IOPtics — leaderboard'):
    """Self-contained HTML: the ranked leaderboard as a filterable table.

    Reads the persisted ``leaderboard.parquet`` (or an in-memory ``board``),
    ranks it, and renders a Bokeh ``DataTable`` with dataset/component/stratum
    selectors. Returns the standalone HTML string. For embedding the same widget
    **inside** a Sphinx page use :func:`leaderboard_embed`.
    """
    layout = _leaderboard_layout(runs_root=runs_root, root=root, out=out,
                                 board=board)
    return file_html(layout, INLINE, title)


def _leaderboard_layout(*, runs_root=None, root=None, out=None, board=None):
    """Build the filterable-leaderboard Bokeh layout (selectors + DataTable)."""
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

    cols = [c for c in ['rank', 'ranking', 'dataset', 'component', 'ref_wave',
                        'stratum', 'fit_method', 'algorithm', 'win_frac', 'bias',
                        'mae', 'coverage68', 'coverage95'] if c in df.columns]
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

    return column(sel_d, sel_c, sel_s, table)

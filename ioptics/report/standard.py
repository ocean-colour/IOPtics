"""The on-demand "standard report" orchestration, version/provenance-stamped.

:func:`build` assembles one of the design's three report types from the standard
figures/tables/bokeh, writing a reStructuredText page + its **lightweight
display assets** (figure PNGs, CSV tables, the standalone Bokeh HTML) into the
accumulating Sphinx tree ``docs/source/reports/<sweep_id>/`` — each page
header-stamped with the sweep's provenance versions. Heavy artifacts (parquet,
chains) stay under ``runs/`` and are not copied.

Reports are built **on demand** (e.g. stage 3 of a ``runs/.../build_vN.py``),
never by CI. Everything derives from the persisted sweep artifacts, so a page is
fully regenerable.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

import ioptics
from ioptics import io
from ioptics.report import bokeh, figures, rst, tables

KINDS = ('per_algorithm', 'cross_algorithm', 'per_dataset')
KIND_TITLES = {
    'cross_algorithm': 'Cross-algorithm comparison',
    'per_algorithm': 'Per-algorithm report',
    'per_dataset': 'Per-dataset report',
}

# Default Sphinx source tree (…/IOPtics/docs/source), overridable for tests.
DEFAULT_DOCS_SRC = (Path(ioptics.__file__).resolve().parent.parent
                    / 'docs' / 'source')

# Representative reference bands per component for the aggregate figures.
_REP_REFS = [('a', 440), ('bb', 555)]


def _provenance(sweep):
    """Parsed ``provenance.yaml`` for the sweep (``{}`` if absent/unreadable)."""
    path = io.sweep_dir(sweep.sweep_id, root=sweep.root) / 'provenance.yaml'
    if not path.is_file():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    except Exception:
        return {}


def _pngs(paths):
    """Keep only the PNG display assets (drop the manuscript PDFs)."""
    return [p for p in paths if p.suffix == '.png']


def _copy(src, dstdir):
    """Copy ``src`` into ``dstdir``; return the destination path."""
    dst = dstdir / Path(src).name
    shutil.copy2(src, dst)
    return dst


def _fig_section(sweep, report_dir, heading, png_paths, caption=''):
    """Copy PNGs into the report dir and format a figure RST section."""
    blocks = []
    for p in png_paths:
        name = _copy(p, report_dir).name
        blocks.append(rst.figure_block(name, caption))
    return rst.section(heading, '\n'.join(blocks)) if blocks else ''


def _table_section(sweep, report_dir, heading, csv_path, title_text):
    """Copy a CSV into the report dir and format a csv-table RST section."""
    if not Path(csv_path).is_file():
        return ''
    name = _copy(csv_path, report_dir).name
    return rst.section(heading, rst.csv_table_block(name, title_text))


def build(sweep_id, *, kind='cross_algorithm', root=None, docs_root=None):
    """Build the standard ``<kind>.rst`` report page for a sweep.

    Loads the sweep, (re)generates the standard figures/tables + a standalone
    Bokeh scatter, copies the display assets into
    ``<docs_root>/reports/<sweep_id>/``, assembles the provenance-stamped RST
    page, and ensures the reports toctree globs it in. Returns the ``.rst`` path.

    ``kind`` ∈ :data:`KINDS`. ``root`` locates the sweep's ``runs`` dir;
    ``docs_root`` the Sphinx source tree (default :data:`DEFAULT_DOCS_SRC`).
    """
    if kind not in KINDS:
        raise ValueError(f'kind must be one of {KINDS}; got {kind!r}')
    sweep = figures.load(sweep_id, root=root)
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS_SRC
    report_dir = docs_root / 'reports' / sweep_id
    report_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = figures.subdir(sweep, 'tables')

    blocks = [rst.title(f'{KIND_TITLES[kind]} — {sweep_id}'),
              rst.provenance_header(sweep_id, _provenance(sweep))]

    # aggregate accuracy scatter (cross/per_dataset framings)
    if kind in ('cross_algorithm', 'per_dataset'):
        for comp, ref in _REP_REFS:
            blocks.append(_fig_section(
                sweep, report_dir, f'Retrieved vs. true — {comp}({ref})',
                _pngs(figures.scatter_set(sweep, comp, ref=ref)),
                f'{comp} at {ref} nm, all algorithms.'))

    if kind == 'cross_algorithm':
        blocks.append(_fig_section(
            sweep, report_dir, 'Taylor & Target — a(440)',
            _pngs(figures.taylor_target(sweep, 'a', ref=440))))
        blocks.append(_fig_section(
            sweep, report_dir, 'Model selection (ΔBIC)',
            _pngs(figures.dbic_cdf(sweep))))

    # per-algorithm spectra for a curated observation
    if kind == 'per_algorithm':
        obs0 = int(sweep.spectral['obs_id'].min())
        for algo in sorted(sweep.spectral['algorithm'].unique()):
            blocks.append(_fig_section(
                sweep, report_dir, f'Spectra — {algo}, obs {obs0}',
                _pngs(figures.spectra_set(sweep, obs0, algorithm=algo)),
                f'{algo}: retrieved components ± 68/95% bands vs truth.'))

    # tables (all kinds)
    tables.accuracy(sweep)
    tables.qc(sweep)
    blocks.append(_table_section(
        sweep, report_dir, 'Accuracy', tables_dir / 'accuracy_chisq_all.csv',
        'Ref-band accuracy + wins (χ², all strata).'))
    blocks.append(_table_section(
        sweep, report_dir, 'Quality control', tables_dir / 'qc_chisq_all.csv',
        'Non-solution rate + Rrs-closure fractions (χ²).'))

    # standalone interactive scatter
    html = bokeh.interactive_scatter(sweep)
    (report_dir / 'interactive_scatter.html').write_text(html, encoding='utf-8')
    blocks.append(rst.section('Interactive',
                              rst.bokeh_raw('interactive_scatter.html')))

    out = report_dir / f'{kind}.rst'
    out.write_text(rst.page(*blocks), encoding='utf-8')
    rst.ensure_glob_toctree(docs_root / 'reports' / 'index.rst')
    return out

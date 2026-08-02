"""The on-demand "standard report" orchestration, version/provenance-stamped.

:func:`build` assembles one of the design's three report types from the standard
figures/tables/bokeh, writing a reStructuredText page + its **lightweight
display assets** (figure PNGs, CSV tables; the interactive Bokeh figure is
embedded inline in the page via CDN, not a separate file) into the
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


def _fig_section(sweep, report_dir, heading, png_paths, caption='', desc=''):
    """Copy PNGs into the report dir and format a figure RST section.

    ``desc`` is an explanatory paragraph placed above the figure(s); ``caption``
    is the per-figure caption under each image.
    """
    if not png_paths:
        return ''
    blocks = [desc] if desc else []
    for p in png_paths:
        name = _copy(p, report_dir).name
        blocks.append(rst.figure_block(name, caption))
    return rst.section(heading, '\n\n'.join(b for b in blocks if b))


def _table_section(sweep, report_dir, heading, csv_path, title_text, desc=''):
    """Copy a CSV into the report dir and format a csv-table RST section."""
    if not Path(csv_path).is_file():
        return ''
    name = _copy(csv_path, report_dir).name
    body = ((desc + '\n\n') if desc else '') + rst.csv_table_block(name, title_text)
    return rst.section(heading, body)


def _intro(sweep, kind):
    """A prose intro paragraph — what this report is and how to read it."""
    algos = sorted(sweep.scalar['algorithm'].unique())
    datasets = sorted(sweep.scalar['dataset'].unique())
    return (
        f"This is the **{KIND_TITLES[kind]}** for sweep ``{sweep.sweep_id}`` — "
        f"a uniform comparison of the IOP-retrieval algorithms "
        f"{', '.join(f'``{a}``' for a in algos)} on "
        f"{', '.join(datasets)}. Each algorithm inverts the observed "
        f"remote-sensing reflectance :math:`R_{{rs}}(\\lambda)` for the inherent "
        f"optical properties (absorption :math:`a`, backscatter :math:`b_b`, and "
        f"their phytoplankton / CDOM-detritus / particulate components), and the "
        f"retrieval is scored against the dataset's truth. The figures and tables "
        f"below show **retrieval accuracy vs. truth**, **fit quality / closure**, "
        f"and **model selection** between the algorithms; the interactive scatter "
        f"lets you drill into any component or trophic stratum. See "
        f":doc:`/models` for what each algorithm parameterizes and "
        f":doc:`/datasets` for the data + truth. All accuracy metrics are "
        f"log-space / multiplicative (0 = perfect). The header above stamps the "
        f"exact code + config versions, so every number is reproducible from the "
        f"persisted sweep artifacts.")


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
              rst.provenance_header(sweep_id, _provenance(sweep)),
              rst.section('Overview', _intro(sweep, kind))]

    # aggregate accuracy scatter (cross/per_dataset framings)
    if kind in ('cross_algorithm', 'per_dataset'):
        for comp, ref in _REP_REFS:
            blocks.append(_fig_section(
                sweep, report_dir, f'Retrieved vs. true — {comp}({ref})',
                _pngs(figures.scatter_set(sweep, comp, ref=ref)),
                caption=f'{comp} at {ref} nm, all algorithms.',
                desc=(f'Retrieved vs. true **{comp}** at {ref} nm, one point per '
                      f'observation and algorithm on log–log axes. Points on the '
                      f'solid **1:1** line are perfect; the dashed **3:1** and '
                      f'**1:3** guides mark the ±3× envelope. Tight, unbiased '
                      f'scatter along 1:1 is the goal; systematic offset above/'
                      f'below it is over-/under-estimation.')))

    if kind == 'cross_algorithm':
        blocks.append(_fig_section(
            sweep, report_dir, 'Taylor & Target — a(440)',
            _pngs(figures.taylor_target(sweep, 'a', ref=440)),
            desc=('**Taylor** (left/first) and **Target** (right/second) diagrams '
                  'for :math:`a(440)`, computed in log space. The Taylor diagram '
                  'places each algorithm by its correlation with truth (azimuth) '
                  'and normalized standard deviation (radius) — the reference '
                  'star sits at correlation 1, norm-std 1. The Target diagram '
                  'plots bias (y) against the sign-carrying unbiased RMSD (x); '
                  'the closer to the origin, the better.')))
        blocks.append(_fig_section(
            sweep, report_dir, 'Model selection (ΔBIC)',
            _pngs(figures.dbic_cdf(sweep)),
            desc=('Cumulative distribution of **ΔBIC** per spectrum for the '
                  'in-tandem pair. ΔBIC < 0 favors the more complex model '
                  '(``expb_pow``, k=5); ΔBIC > 0 favors the parsimonious one '
                  '(``giop``, k=3). The curve shows what fraction of spectra fall '
                  'either side — i.e. whether the extra two parameters earn their '
                  'keep. See :doc:`/models`.')))

    # per-algorithm spectra for a curated observation
    if kind == 'per_algorithm':
        obs0 = int(sweep.spectral['obs_id'].min())
        for algo in sorted(sweep.spectral['algorithm'].unique()):
            blocks.append(_fig_section(
                sweep, report_dir, f'Spectra — {algo}, obs {obs0}',
                _pngs(figures.spectra_set(sweep, obs0, algorithm=algo)),
                caption=f'{algo}: retrieved components ± 68/95% bands vs truth.',
                desc=(f'Retrieved IOP spectra for **{algo}** on observation '
                      f'{obs0}: the posterior median (line) with 68% / 95% '
                      f'credible bands, overlaid on the L23 truth (dashed). One '
                      f'panel per component.')))

    # tables (all kinds)
    tables.accuracy(sweep)
    tables.qc(sweep)
    blocks.append(_table_section(
        sweep, report_dir, 'Accuracy', tables_dir / 'accuracy_chisq_all.csv',
        'Ref-band accuracy + wins (χ², all strata).',
        desc=('Per-(component, reference wavelength) retrieval accuracy for the '
              'χ² population: multiplicative **mae**/**bias** and **coverage** '
              '(0 = perfect; ``mae`` 0.1 ≈ 10%), the cross-algorithm ranks '
              '(``*_rank``, 1 = best), and the head-to-head **win_frac**. '
              '``ref_match`` is the native band actually used (±3 nm).')))
    blocks.append(_table_section(
        sweep, report_dir, 'Quality control', tables_dir / 'qc_chisq_all.csv',
        'Fit quality / closure (χ²).',
        desc=('Fit-quality summary per algorithm: ``frac_not_ok`` (retrievals '
              'flagged as failures/QC), the median reduced **χ²ᵥ**, and the '
              'χ²ᵥ-based closure fractions (``frac_good`` ≈ 1, ``frac_overfit`` '
              '< 1, ``frac_underfit`` > 1, ``frac_qc_fail`` = non-solutions).')))

    # interactive scatter — embedded inline (CDN + components) so it renders on
    # RTD without copying a separate HTML file into the build output.
    blocks.append(rst.section(
        'Interactive',
        ('Retrieved vs. true, **interactive**: pick the dataset, algorithm, '
         'component and trophic stratum, and hover any point for its wavelength '
         'and values. (Downsampled for the web; the static panels above '
         'summarize the full population.)\n\n'
         + rst.bokeh_embed(bokeh.scatter_embed(sweep)))))

    out = report_dir / f'{kind}.rst'
    out.write_text(rst.page(*blocks), encoding='utf-8')
    rst.ensure_glob_toctree(docs_root / 'reports' / 'index.rst')
    return out

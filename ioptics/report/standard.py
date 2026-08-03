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

# How many (component, ref-λ) panels a page shows, best-covered first. The set
# itself is **derived from the sweep** (figures.scored_refs), never fixed: a fixed
# set publishes blank panels as soon as a dataset's truth differs.
MAX_REF_PANELS = 3

# Display assets this builder owns in a report dir — anything matching these that
# it did not regenerate is stale and gets pruned.
_OWNED_SUFFIXES = ('.png', '.csv')


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


def _fig_section(sweep, report_dir, heading, png_paths, caption='', desc='',
                 published=None):
    """Copy PNGs into the report dir and format a figure RST section.

    ``desc`` is an explanatory paragraph placed above the figure(s); ``caption``
    is the per-figure caption under each image. An empty ``png_paths`` means the
    underlying data was degenerate (:func:`ioptics.report.figures._save` declines
    to write a blank figure), so **the section is omitted entirely** rather than
    published as an empty panel with a confident caption. ``published`` collects
    the filenames actually placed in the report dir, for stale-asset pruning.
    """
    if not png_paths:
        return ''
    blocks = [desc] if desc else []
    for p in png_paths:
        name = _copy(p, report_dir).name
        if published is not None:
            published.add(name)
        blocks.append(rst.figure_block(name, caption))
    return rst.section(heading, '\n\n'.join(b for b in blocks if b))


def _not_shown_section(reasons):
    """A short, honest note listing what this sweep could not show, and why."""
    if not reasons:
        return ''
    items = '\n'.join(f'* {r}' for r in reasons)
    return rst.section(
        'Not shown for this sweep',
        'The figure set is derived from what this sweep actually measured, so a '
        'panel with no data behind it is omitted rather than published blank. '
        'For the record, this page leaves out:\n\n' + items)


def _curated_obs(sweep, *, fit_method='chisq'):
    """One representative observation id, or ``None``.

    Picks the median-χ²ᵥ ``ok`` fit — a typical fit rather than a flattering or
    pathological one. Deliberately does **no** ``int()`` cast: observation ids are
    dataset-defined and GLORIA's are strings (``GID_1``), which is what made the
    old ``int(obs_id.min())`` choice crash on that sweep.
    """
    sc = sweep.scalar
    if sc is None or sc.empty:
        return None
    sub = sc[sc['fit_method'] == fit_method] if 'fit_method' in sc.columns else sc
    if 'status' in sub.columns and (sub['status'] == 'ok').any():
        sub = sub[sub['status'] == 'ok']
    if sub.empty:
        return None
    if 'chi2_nu' in sub.columns and sub['chi2_nu'].notna().any():
        ranked = sub.dropna(subset=['chi2_nu']).sort_values('chi2_nu')
        return ranked.iloc[len(ranked) // 2]['obs_id']
    return sorted(sub['obs_id'].unique())[0]


def _prune_stale(report_dir, published):
    """Delete display assets in ``report_dir`` this build did not (re)generate.

    Without this, changing the figure set leaves orphaned PNGs and CSVs committed
    in the docs tree forever — the report dir stops describing the report.
    """
    removed = []
    for path in sorted(report_dir.iterdir()):
        if path.is_file() and path.suffix in _OWNED_SUFFIXES \
                and path.name not in published:
            path.unlink()
            removed.append(path.name)
    return removed


def _table_section(sweep, report_dir, heading, csv_path, title_text, desc='',
                   published=None):
    """Copy a CSV into the report dir and format a csv-table RST section."""
    if not Path(csv_path).is_file():
        return ''
    name = _copy(csv_path, report_dir).name
    if published is not None:
        published.add(name)
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

    published = set()          # display assets this build owns
    not_shown = []             # what the data could not support, and why

    blocks = [rst.title(f'{KIND_TITLES[kind]} — {sweep_id}'),
              rst.provenance_header(sweep_id, _provenance(sweep)),
              rst.section('Overview', _intro(sweep, kind))]

    # What can this sweep actually show? Derived, not assumed.
    scored = figures.scored_refs(sweep)
    panels = scored[:MAX_REF_PANELS]
    if not scored:
        not_shown.append(
            'the retrieved-vs-true scatters, Taylor/Target diagrams and ratio '
            'distributions — this sweep has no spectral truth at any reference '
            'wavelength to score against (its dataset may carry scalar truth only).')

    # aggregate accuracy scatter + its ratio distribution (cross/per_dataset)
    if kind in ('cross_algorithm', 'per_dataset'):
        for comp, ref, n in panels:
            label = f'{comp}({ref:g})'
            blocks.append(_fig_section(
                sweep, report_dir, f'Retrieved vs. true — {label}',
                _pngs(figures.scatter_set(sweep, comp, ref=ref)),
                caption=f'{label}, all algorithms (n={n} scored per algorithm).',
                desc=(f'Retrieved vs. true **{label}**, one point per observation '
                      f'and algorithm on log–log axes. Points on the solid **1:1** '
                      f'line are perfect; the dashed **3:1** and **1:3** guides '
                      f'mark the ±3× envelope. Each legend entry carries that '
                      f'algorithm\'s scored ``n``, its median ratio (1 = perfect) '
                      f'and MPD (median absolute percent difference, 0 = perfect), '
                      f'so the panel can be read without the table below.'),
                published=published))
            blocks.append(_fig_section(
                sweep, report_dir, f'Ratio distribution — {label}',
                _pngs(figures.ratio_hist(sweep, comp, ref=ref)),
                caption=f'Retrieved/true ratio buckets for {label}.',
                desc=('How the population is distributed about 1:1, per accuracy '
                      'bucket — the companion a scatter is conventionally paired '
                      'with (GIOP Figs. 1-2), because central tendency alone hides '
                      'the spread that decides whether a retrieval is usable. The '
                      'vertical rule marks ratio = 1.'),
                published=published))

    if kind == 'cross_algorithm':
        if panels:
            comp, ref, _ = panels[0]
            blocks.append(_fig_section(
                sweep, report_dir, f'Taylor & Target — {comp}({ref:g})',
                _pngs(figures.taylor_target(sweep, comp, ref=ref)),
                desc=(f'**Taylor** (first) and **Target** (second) diagrams for '
                      f':math:`{comp}({ref:g})`, computed in log space and drawn '
                      f'for the sweep\'s best-covered component. The Taylor diagram '
                      f'places each algorithm by its correlation with truth '
                      f'(azimuth, labelled in correlation) and normalized standard '
                      f'deviation (radius); the reference star sits at correlation '
                      f'1, norm-σ 1, and the dotted arcs are centred-RMSD contours '
                      f'about it. The Target diagram plots bias (y) against the '
                      f'sign-carrying unbiased RMSD (x), with dotted constant-RMSD '
                      f'rings — the closer to the origin, the better.'),
                published=published))

        pair = figures.dbic_pair(sweep)
        if pair is None:
            not_shown.append(
                'the ΔBIC model-selection panel — it contrasts a more against a '
                'less complex model, and this sweep has fewer than two algorithms '
                'or no spread in parameter count ``k`` to contest.')
        else:
            a, b = pair
            ks = sweep.scalar.groupby('algorithm')['k'].max()
            blocks.append(_fig_section(
                sweep, report_dir, 'Model selection (ΔBIC)',
                _pngs(figures.dbic_cdf(sweep, model_a=a, model_b=b)),
                desc=(f'Cumulative distribution of **ΔBIC** per spectrum for this '
                      f'sweep\'s complexity contest — ``{a}`` (k={ks.get(a, "?"):g}) '
                      f'against ``{b}`` (k={ks.get(b, "?"):g}), chosen as its '
                      f'highest- and lowest-parameter algorithms. ΔBIC < 0 favours '
                      f'the more complex model ``{a}``; ΔBIC > 0 favours the '
                      f'parsimonious ``{b}``. The curve shows what fraction of '
                      f'spectra fall either side — i.e. whether the extra '
                      f'parameters earn their keep. See :doc:`/models`.'),
                published=published))

    # per-algorithm spectra for a curated observation
    if kind == 'per_algorithm':
        obs0 = _curated_obs(sweep)
        if obs0 is None:
            not_shown.append('the per-algorithm spectra — no successful fit to show.')
        else:
            for algo in sorted(sweep.spectral['algorithm'].unique()):
                blocks.append(_fig_section(
                    sweep, report_dir, f'Spectra — {algo}, obs {obs0}',
                    _pngs(figures.spectra_set(sweep, obs0, algorithm=algo)),
                    caption=f'{algo}: retrieved components ± 68/95% bands vs truth.',
                    desc=(f'Retrieved IOP spectra for **{algo}** on observation '
                          f'``{obs0}`` — a median-χ²ᵥ fit, i.e. typical rather than '
                          f'flattering: the posterior median (line) with 68% / 95% '
                          f'credible bands, overlaid on truth (dashed) where the '
                          f'dataset carries it. One panel per component.'),
                    published=published))

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
              '``ref_match`` is the native band actually used (±3 nm).'),
        published=published))
    blocks.append(_table_section(
        sweep, report_dir, 'Quality control', tables_dir / 'qc_chisq_all.csv',
        'Fit quality / closure (χ²).',
        desc=('Fit-quality summary per algorithm: ``frac_not_ok`` (retrievals '
              'flagged as failures/QC), the median reduced **χ²ᵥ**, and the '
              'χ²ᵥ-based closure fractions (``frac_good`` ≈ 1, ``frac_overfit`` '
              '< 1, ``frac_underfit`` > 1, ``frac_qc_fail`` = non-solutions).'),
        published=published))

    # interactive scatter — embedded inline (CDN + components) so it renders on
    # RTD without copying a separate HTML file into the build output.
    blocks.append(rst.section(
        'Interactive',
        ('Retrieved vs. true, **interactive**: pick the dataset, algorithm, '
         'component and trophic stratum, and hover any point for its wavelength '
         'and values. (Downsampled for the web; the static panels above '
         'summarize the full population.)\n\n'
         + rst.bokeh_embed(bokeh.scatter_embed(sweep)))))

    blocks.append(_not_shown_section(not_shown))

    out = report_dir / f'{kind}.rst'
    out.write_text(rst.page(*blocks), encoding='utf-8')
    _prune_stale(report_dir, published)
    rst.ensure_glob_toctree(docs_root / 'reports' / 'index.rst')
    return out

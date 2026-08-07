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

import re
import shutil
from pathlib import Path

import numpy as np
import yaml

import ioptics
from ioptics import diagnostics, io, metrics, records
from ioptics.report import (bokeh, figures, leaderboard, profiles, rst,
                            tables)

KINDS = ('per_algorithm', 'cross_algorithm', 'per_dataset')
KIND_TITLES = {
    'cross_algorithm': 'Cross-algorithm comparison',
    'per_algorithm': 'Per-algorithm report',
    'per_dataset': 'Per-dataset report',
}

# Default Sphinx source tree (…/IOPtics/docs/source), overridable for tests.
DEFAULT_DOCS_SRC = (Path(ioptics.__file__).resolve().parent.parent
                    / 'docs' / 'source')

# Which (component, ref-λ) panels a page shows. The candidate set is **derived
# from the sweep** (figures.scored_refs), never fixed: a fixed set publishes blank
# panels as soon as a dataset's truth differs. From the candidates we take every
# TOTAL component plus the best-covered DECOMPOSED one — the community reports
# total a/bb separately from the decomposed a_dg/a_ph/bb_p, which are consistently
# the weaker retrievals, and an aggregate that blurs the two is distrusted.
TOTAL_COMPONENTS = ('a', 'bb')

# Ceiling on the plan, since each panel costs two figures (scatter + ratio
# distribution). With two totals plus one decomposed component the plan is 3 by
# construction; the cap is a guard for a future TOTAL_COMPONENTS, not live today.
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
    # ``caption`` may be one string for every figure, or a {keyword: caption}
    # mapping matched against the file name. A section holding two different
    # diagrams needs two captions, or nothing on the page says which image is
    # which (and the alt text falls back to the file path, which is no use to a
    # screen reader). Matching by **name** rather than by position matters
    # because a degenerate figure is not written at all: pairing positionally
    # would caption a surviving Target diagram as the missing Taylor one.
    def _caption_for(path):
        if isinstance(caption, str):
            return caption
        for key, text in caption.items():
            if key in path.name:
                return text
        return ''

    blocks = [desc] if desc else []
    for p in png_paths:
        cap = _caption_for(p)
        name = _copy(p, report_dir).name
        if published is not None:
            published.add(name)
        blocks.append(rst.figure_block(name, cap))
    return rst.section(heading, '\n\n'.join(b for b in blocks if b))


def _plan_panels(scored):
    """Choose the ``(component, ref, n)`` panels from what the sweep can score.

    Every **total** component (:data:`TOTAL_COMPONENTS`) that was scored, at its
    best-covered reference band, plus the single best-covered **decomposed**
    component — the total-vs-decomposed split the IOP literature reports (IOCCG
    Report 5, GIOP), rather than an arbitrary top-N of a mixed list. A sweep that
    only scores a decomposed component (GLORIA scores ``a_dg`` alone) still gets its
    panel.
    """
    if not scored:
        return []
    best = {}                    # component -> best-covered (comp, ref, n)
    for comp, ref, n in scored:  # scored is already best-covered first
        best.setdefault(comp, (comp, ref, n))
    totals = [best[c] for c in TOTAL_COMPONENTS if c in best]
    decomposed = [v for c, v in best.items() if c not in TOTAL_COMPONENTS]
    decomposed.sort(key=lambda t: -t[2])
    return (totals + decomposed[:1])[:MAX_REF_PANELS]


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


def _referenced_elsewhere(report_dir, this_page):
    """Asset names referenced by the *other* ``.rst`` pages in ``report_dir``.

    Several pages share one report dir (``cross_algorithm.rst``,
    ``per_algorithm.rst``, ``exemplar_fits.rst``, …), and each build knows only its
    own assets. Pruning on that knowledge alone deletes the siblings' figures:
    building ``per_algorithm`` after ``cross_algorithm`` removed all six of its
    scatters, Taylor/Target and ΔBIC panels while ``cross_algorithm.rst`` went on
    referencing them — a dangling image, and a ``sphinx -W`` failure. So an asset
    survives if *any* surviving page still names it.
    """
    keep = set()
    for page in sorted(report_dir.glob('*.rst')):
        if page.name == this_page:
            continue
        try:
            text = page.read_text(encoding='utf-8')
        except OSError:
            continue
        # Match the **directive target**, not any substring: a plain
        # ``name in text`` kept an orphaned ``fits.png`` alive purely because a
        # sibling page referenced ``exemplar_fits.png``.
        keep.update(_ASSET_REF.findall(text))
    return keep


#: Asset references in a report page: the target of a ``figure``/``image``
#: directive, or the file of a ``csv-table``. Anchored on the directive so the
#: match is a whole filename rather than a fragment of a longer one.
_ASSET_REF = re.compile(
    r'^\s*(?:\.\.\s+(?:figure|image)::\s*|:file:\s*)([^\s:]+)\s*$', re.MULTILINE)


def _prune_stale(report_dir, published, *, this_page=None):
    """Delete display assets in ``report_dir`` no surviving page references.

    Without this, changing the figure set leaves orphaned PNGs and CSVs committed
    in the docs tree forever — the report dir stops describing the report. Assets
    still referenced by a *sibling* page are kept (see
    :func:`_referenced_elsewhere`).
    """
    keep = set(published) | _referenced_elsewhere(report_dir, this_page)
    removed = []
    for path in sorted(report_dir.iterdir()):
        if path.is_file() and path.suffix in _OWNED_SUFFIXES \
                and path.name not in keep:
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
        f":doc:`/datasets` for the data + truth. The header above stamps the "
        f"exact code + config versions, so every number is reproducible from the "
        f"persisted sweep artifacts.\n\n" + _CONVENTIONS)


#: What "good" looks like, per metric. The previous page-wide claim that "all
#: accuracy metrics are log-space / multiplicative (0 = perfect)" was false for
#: three columns of the very next table, so each metric now states its own perfect
#: value. The accuracy form is Erickson (2023)'s fractional multiplicative one
#: (JXP's decision) — note that Seegers (2018) publishes the un-subtracted factor,
#: so the convention has to be named rather than assumed.
_CONVENTIONS = (
    "**Reading the numbers.** ``mae`` and ``bias`` are **fractional "
    "multiplicative** errors in log space, following Erickson (2023): "
    ":math:`\\mathrm{mae} = 10^{\\langle|\\log_{10} M/O|\\rangle} - 1`, so "
    "**0 = perfect** and ``0.109`` means 10.9% (Seegers 2018 publishes the "
    "un-subtracted factor, ``1.109``, for the same fit — the forms differ by one). "
    "``bias`` is signed, > 0 = over-estimate. The other columns have **different** "
    "perfect values, which is why they are read separately: ``median_ratio`` and "
    "GIOP's ``Ratio`` are perfect at **1**; ``win_frac`` is a head-to-head share, "
    "so **0.5 = a tie**; and ``coverage68`` / ``coverage95`` are perfect at their "
    "**nominal 0.68 / 0.95** — an algorithm can be the most accurate and still be "
    "over-confident about its uncertainty, which the ``*_verdict`` columns name "
    "(``over-confident`` / ``consistent`` / ``conservative``; *consistent* means "
    "not distinguishable from nominal at this ``n_pairs``, which on a thin contest "
    "is a weak statement). Three "
    "different denominators appear and are named apart: ``n_pairs`` (surviving "
    "retrieval-truth pairs), ``n_scored`` (spectra that produced a usable fit) and "
    "``n_attempted`` (spectra the sweep tried).")


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
    panels = _plan_panels(scored)
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
                caption=(f'{label}, all algorithms — at most {n} '
                         f'retrieval-truth pairs per algorithm; each legend entry '
                         f'states its own.'),
                desc=(f'Retrieved vs. true **{label}**, one point per observation '
                      f'and algorithm on log–log axes. Points on the solid **1:1** '
                      f'line are perfect; the dashed **3:1** and **1:3** guides '
                      f'mark the ±3× envelope. Each legend entry carries that '
                      f'algorithm\'s own ``n_pairs``, its median ratio '
                      f'(1 = perfect) '
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
                caption={'taylor': f'Taylor diagram — {comp}({ref:g}): '
                                   f'correlation (azimuth) vs normalized standard '
                                   f'deviation (radius), with centred-RMSD arcs '
                                   f'about the reference star.',
                         'target': f'Target diagram — {comp}({ref:g}): bias vs '
                                   f'signed unbiased RMSD, with constant-RMSD '
                                   f'rings; the origin is a perfect retrieval.'},
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
                caption=(f'Per-spectrum ΔBIC, ``{a}`` vs ``{b}``: the fraction of '
                         f'spectra either side of 0 says whether the extra '
                         f'parameters earn their keep.'),
                desc=(f'Cumulative distribution of **ΔBIC** per spectrum for this '
                      f'sweep\'s complexity contest — ``{a}`` (k={ks.get(a, "?"):g}) '
                      f'against ``{b}`` (k={ks.get(b, "?"):g}), chosen as its '
                      f'highest- and lowest-parameter algorithms. ΔBIC < 0 favours '
                      f'the more complex model ``{a}``; ΔBIC > 0 favours the '
                      f'parsimonious ``{b}``. The curve shows what fraction of '
                      f'spectra fall either side — i.e. whether the extra '
                      f'parameters earn their keep. See :doc:`/models`.'),
                published=published))

    # ---- accuracy as a function of wavelength (cross/per_dataset) --------------
    # metrics_spectral has been computed and persisted since Stage 2 and read by
    # nothing; this is the figure an ocean-colour reader looks for first.
    if kind in ('cross_algorithm', 'per_dataset'):
        spectral_comps = figures.scored_components(sweep)
        if spectral_comps:
            names = ', '.join(f'``{c}``' for c, _, _ in spectral_comps)
            bands = max(w for _, w, _ in spectral_comps)
            blocks.append(_fig_section(
                sweep, report_dir, 'Accuracy vs. wavelength',
                _pngs(figures.accuracy_spectrum(sweep)),
                caption=('Fractional multiplicative MAE against wavelength, one '
                         'panel per component, all algorithms overlaid. The dashed '
                         'rule is the perfect value (0).'),
                desc=(f'How each algorithm\'s error varies **across the spectrum**, '
                      f'for the {len(spectral_comps)} component(s) this sweep scores '
                      f'at more than one band ({names}; up to {bands} bands). A '
                      f'retrieval can be accurate in the blue and useless in the red, '
                      f'which a single reference-band number cannot show — this is '
                      f'the per-band view of the same ``mae`` the accuracy table '
                      f'reports at its reference wavelengths. Each algorithm keeps '
                      f'its colour, marker and linestyle from every other figure.'),
                published=published))
        else:
            single = figures.scored_components(sweep, min_waves=1)
            why = (f'only {", ".join(f"``{c}``" for c, _, _ in single)} is scored, and '
                   f'at a single wavelength'
                   if single else 'no component carries spectral truth')
            not_shown.append(
                f'the accuracy-vs-wavelength figure — {why}, so there is no spectral '
                f'shape to draw. One marker per algorithm under that heading would '
                f'invite a reader to see a trend that is not there. (GLORIA\'s only '
                f'spectral truth is ``a_cdom440`` at 440 nm; a dataset like L23, with '
                f'truth across the band set, fills this in.)')

    # ---- per-stratum slices ---------------------------------------------------
    # The pooled 'all' row is what every other section shows; the point of this one
    # is what pooling hides — on GLORIA, mesotrophic water fits 86% of the time and
    # eutrophic 14%, which the single pooled 21% says nothing about.
    strata = figures.strata(sweep)
    if kind in ('cross_algorithm', 'per_dataset'):
        if not strata:
            not_shown.append(
                'the per-stratum breakdown — this sweep resolves only the pooled '
                '``all`` stratum, which needs Chl truth (or a retrieved Chl) to bin '
                'observations by trophic state.')
        else:
            listed = ', '.join(f'``{s}`` (n_attempted {a})' for s, _, a in strata)
            # The dropped 'unknown' population is stated rather than hidden: it is a
            # provenance category, not a water type, so it does not belong in a table
            # of trophic bins — but omitting it silently would make the breakdown
            # look complete when it is not.
            unk = figures.unknown_stratum_count(sweep)
            unk_note = ''
            if unk:
                unk_pairs, unk_att = unk
                unk_note = (
                    f' A further **{unk_att} spectra ({unk_pairs} scored pair(s)) '
                    f'have no chlorophyll at all** — neither truth nor a retrieved '
                    f'value — so they cannot be binned and are left out of the '
                    f'tables below rather than shown as a fourth water type. They '
                    f'are still counted in the pooled numbers above.')
            blocks.append(rst.section(
                'Per trophic stratum',
                f'Observations are binned by chlorophyll into '
                f'{metrics.CHL_BINS[0][2]} / {metrics.CHL_BINS[1][2]} / '
                f'{metrics.CHL_BINS[2][2]} '
                f'(<{metrics.CHL_BINS[0][1]:g}, <{metrics.CHL_BINS[1][1]:g}, '
                f'≥{metrics.CHL_BINS[1][1]:g} mg m⁻³), preferring truth Chl over '
                f'retrieved. This sweep resolves {listed}.{unk_note} Every table '
                f'above pools these together, and pooling is what hides a regime '
                f'change — an algorithm can be usable in one trophic state and not '
                f'in the next, which is the whole question for a coastal dataset.'))
            for stratum, n_pairs, n_att in strata:
                tables.accuracy(sweep, stratum=stratum)
                tables.qc(sweep, stratum=stratum)
                blocks.append(_table_section(
                    sweep, report_dir, f'Accuracy — {stratum}',
                    tables_dir / f'accuracy_chisq_{stratum}.csv',
                    f'Ref-band accuracy, {stratum} only.',
                    desc=(f'The same accuracy columns as the pooled table, over the '
                          f'``{stratum}`` stratum alone — at most {n_pairs} '
                          f'retrieval-truth pair(s), from {n_att} attempted spectra. '
                          f'Columns are defined on the :doc:`/reports/glossary` '
                          f'page.'),
                    published=published))
                blocks.append(_table_section(
                    sweep, report_dir, f'Quality control — {stratum}',
                    tables_dir / f'qc_chisq_{stratum}.csv',
                    f'Fit quality / closure, {stratum} only.',
                    desc=(f'Retrieval success within ``{stratum}``. ``frac_ok`` and '
                          f'``frac_not_ok`` are complements over this stratum\'s '
                          f'{n_att} attempted spectra, so they can be read directly '
                          f'against the other strata.'),
                    published=published))

    # ΔBIC split by stratum — "does the extra complexity pay" is a different
    # question in turbid water than overall, and the pooled curve can hide a reversal.
    if kind == 'cross_algorithm' and strata:
        pair2 = figures.dbic_pair(sweep)
        if pair2 is not None:
            a2, b2 = pair2
            blocks.append(_fig_section(
                sweep, report_dir, 'Model selection by stratum (ΔBIC)',
                _pngs(figures.dbic_cdf(sweep, model_a=a2, model_b=b2,
                                       by='stratum')),
                caption=(f'Per-spectrum ΔBIC, ``{a2}`` vs ``{b2}``, one curve per '
                         f'trophic stratum.'),
                desc=(f'The same contest as above, split by trophic stratum. '
                      f'ΔBIC < 0 favours the more complex ``{a2}``. A pooled curve '
                      f'can hide a reversal — extra parameters that pay in turbid '
                      f'water and cost in clear water average out to "no '
                      f'difference".'),
                published=published))

    # ---- χ² vs MCMC, where both exist ----------------------------------------
    methods = figures.fit_methods(sweep)
    if kind in ('cross_algorithm', 'per_dataset'):
        fm = tables.fit_method_compare(sweep)
        if fm.empty:
            have = ', '.join(f'``{m}`` ({n} rows)' for m, n in methods) or 'none'
            not_shown.append(
                f'the χ²-vs-MCMC comparison — it needs the same algorithm fitted '
                f'both ways on the same spectra, and this sweep carries {have}. '
                f'``metrics_*`` has scored the two populations in parallel since '
                f'Stage 2, so the comparison appears here as soon as one sweep runs '
                f'both.')
        else:
            blocks.append(_table_section(
                sweep, report_dir, 'Least-squares vs MCMC',
                tables_dir / 'fit_method_compare_all.csv',
                'The same contests fitted both ways.',
                desc=('For the contests present under **both** fit methods. '
                      '``d_mae`` is ``mae(mcmc) − mae(chisq)``, so negative means the '
                      'sampler is more accurate. The columns worth reading first are '
                      'the **coverage** pair: χ² reports the curvature of the '
                      'likelihood at a single point while MCMC samples the posterior, '
                      'so the question is not only which is more accurate but whether '
                      'the sampler\'s wider intervals are also the more honest ones — '
                      'a coverage nearer the nominal 0.68 / 0.95.'),
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
    acc_df = tables.accuracy(sweep)
    tables.qc(sweep)
    n_unscored = int(acc_df.attrs.get('n_unscored_rows', 0))
    unscored_note = (
        f' {n_unscored} further (component, band) rows are omitted because '
        f'this sweep scored no retrieval-truth pairs for them.'
        if n_unscored else '')
    blocks.append(_table_section(
        sweep, report_dir, 'Accuracy', tables_dir / 'accuracy_chisq_all.csv',
        'Ref-band accuracy + wins (χ², all strata).',
        desc=('Per-(dataset, component, reference wavelength) retrieval accuracy '
              'for the χ² population: fractional multiplicative **mae**/**bias** '
              '(0 = perfect, ``mae`` 0.1 ≈ 10%), **median_ratio** (1 = perfect), '
              '**coverage68/95** against their nominal 0.68/0.95 with a '
              '``*_verdict`` of over-confident / consistent / conservative '
              '(a real miss being more than 2 binomial standard errors; at small '
              '``n_pairs`` only a gross miss is detectable, so *consistent* means '
              '"not distinguishable from nominal here", not "calibrated"), '
              'the cross-algorithm ranks (``*_rank``, 1 = best) and the '
              'head-to-head **win_frac** (0.5 = tie). ``n_pairs`` counts surviving '
              'retrieval-truth pairs; ``ref_match`` is the native band actually '
              'used (±3 nm). Every column is defined on the '
              ':doc:`/reports/glossary` page.' + unscored_note),
        published=published))
    h2h = tables.head_to_head(sweep)
    if h2h.empty:
        not_shown.append(
            'the head-to-head table — a pairwise verdict needs at least two '
            'algorithms scored on a shared set of spectra.')
    else:
        ties = int((h2h['verdict'] == 'indistinguishable').sum())
        weak = int((h2h['verdict'] == 'underpowered').sum())
        blocks.append(_table_section(
            sweep, report_dir, 'Head-to-head',
            tables_dir / 'head_to_head_chisq_all.csv',
            'Pairwise verdicts (χ², all strata).',
            desc=(f'Every algorithm pair, judged on the spectra **both** of them '
                  f'retrieved. ``delta_mae`` is ``mae(A) − mae(B)`` on those shared '
                  f'spectra (negative favours A) and ``d_lo``/``d_hi`` are its '
                  f'paired-bootstrap 95% interval, after the round-robin practice '
                  f'of resampling the data to put uncertainty on a ranking. The '
                  f'``verdict`` names a winner only when the interval excludes 0 '
                  f'**and** the difference clears a practical floor of '
                  f'{metrics.PRACTICAL_MAE_FLOOR:.0%}. It reads '
                  f'``indistinguishable`` only when the **whole interval** lies '
                  f'inside that floor — i.e. the data rule a material difference '
                  f'out — and ``underpowered`` when the interval is too wide to '
                  f'say either way at this ``n_paired``. Here '
                  f'{ties} pair(s) are indistinguishable and {weak} are '
                  f'underpowered, out of {len(h2h)}.'
                  + (f' A further {h2h.attrs["n_unscored_rows"]} pair(s) share no '
                     f'scoreable spectrum and are omitted.'
                     if h2h.attrs.get('n_unscored_rows') else '')),
            published=published))

    blocks.append(_table_section(
        sweep, report_dir, 'Quality control', tables_dir / 'qc_chisq_all.csv',
        'Fit quality / closure (χ²).',
        desc=('Fit-quality summary per dataset and algorithm. ``n_attempted`` is '
              'what the sweep tried and ``n_scored`` what produced a usable fit — '
              'the gap is explained by the per-status fractions, which are kept '
              'apart on purpose: ``frac_out_of_scope`` (spectrum outside the model '
              'family\'s regime) and ``frac_fit_failed`` (the fitter returned '
              'nothing) are the same ``frac_not_ok`` and entirely different '
              'findings. Also the median reduced **χ²ᵥ**, the noise-model-free '
              '**rel_misfit** (GIOP\'s ΔRrs), and the χ²ᵥ closure split '
              '(``frac_good`` ≈ 1, ``frac_overfit`` < 1, ``frac_underfit`` > 1, '
              '``frac_qc_fail`` = non-solutions).'),
        published=published))

    # interactive scatter — embedded inline (components + **vendored** BokehJS) so
    # it renders on RTD without copying a separate HTML file into the build output
    # and without depending on cdn.bokeh.org at view time.
    bokeh.vendor_bokehjs(docs_root / '_static')
    blocks.append(rst.section(
        'Interactive',
        ('Retrieved vs. true, **interactive**: pick the dataset, algorithm, '
         'component and trophic stratum, and hover any point for its '
         '``obs_id``, wavelength and values — so an outlier can be traced back to '
         'a spectrum. The figure title states what fraction of the population is '
         'plotted (the cloud is downsampled to keep the page small; the static '
         'panels above summarize all of it).\n\n'
         + rst.bokeh_embed(bokeh.scatter_embed(
             sweep, static_prefix='../../')))))

    # Link the exemplar page when it has been built — conditionally, because a
    # ``:doc:`` reference to a page that does not exist is a ``sphinx -W`` failure.
    if (report_dir / f'{EXEMPLAR_PAGE}.rst').is_file():
        blocks.append(rst.section(
            'Individual fits',
            f'The figures above describe the population. For {sweep_id}\'s best, '
            f'worst and median **individual fits** — observed Rrs with every '
            f'algorithm\'s model laid over it — see :doc:`{EXEMPLAR_PAGE}`.'))

    blocks.append(_not_shown_section(not_shown))

    out = report_dir / f'{kind}.rst'
    out.write_text(rst.page(*blocks), encoding='utf-8')
    _prune_stale(report_dir, published, this_page=out.name)
    rst.ensure_glob_toctree(docs_root / 'reports' / 'index.rst')
    return out


#: Page name for the exemplar report (a sibling of the ``KINDS`` pages in the same
#: ``reports/<sweep_id>/`` dir, built by :func:`build_exemplars`).
EXEMPLAR_PAGE = 'exemplar_fits'

#: Hand-written pages under ``reports/`` that :func:`build_landing` must keep in the
#: toctree. The landing page is **regenerated**, so a toctree entry added by hand
#: would be silently dropped on the next build — and a page in no toctree is a
#: ``sphinx -W`` failure. Listed here, they survive regeneration; each is included
#: only if the file actually exists, so this cannot create a dangling reference.
CURATED_REPORT_PAGES = ('gloria_investigation',)

_SPELLED = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
            'eight', 'nine', 'ten')


def _spell(k):
    """Small counts as words, so the prose reads like prose ("the eight nearest")."""
    return _SPELLED[k] if 0 <= k < len(_SPELLED) else str(k)


def _exemplar_table(picks, *, ordered_by_peak=True, multi_dataset=False):
    """A ``list-table`` of the exemplar selection, so the figure has a key.

    ``dataset`` is only a column when the sweep has more than one, because obs ids
    are reused across datasets and ``0`` alone would not identify a row.
    """
    caption = ('The exemplar observations, clear → turbid' if ordered_by_peak
               else 'The exemplar observations, by fit quality')
    cols = (['dataset'] if multi_dataset else []) + [
        'obs_id', 'role', 'χ²ᵥ (median)', 'rel. misfit', 'Rrs peak [nm]']
    header = (f'.. list-table:: {caption}\n'
              '   :header-rows: 1\n   :widths: auto\n\n'
              + '   * - ' + '\n     - '.join(cols) + '\n')
    def _num(v, fmt):
        """Format a metric, or an em dash — guarding NaN, ±inf and non-numbers.

        A cell that raises takes the whole page down, and an unguarded ``-inf``
        would publish the literal string ``-inf`` under a χ²ᵥ heading.
        """
        try:
            x = float(v)
        except (TypeError, ValueError):
            return '—'
        return format(x, fmt) if np.isfinite(x) else '—'

    rows = []
    for r in picks.itertuples():
        lead = (f'   * - {getattr(r, "dataset", "")}\n     - ``{r.obs_id}``\n'
                if multi_dataset else f'   * - ``{r.obs_id}``\n')
        rows.append(f'{lead}     - {r.role}\n'
                    f'     - {_num(r.chi2_nu, ".3g")}\n'
                    f'     - {_num(r.rel_misfit, ".0%")}\n'
                    f'     - {_num(r.peak_nm, ".0f")}\n')
    return header + ''.join(rows)


def _exemplar_summary(sweep, picks, *, fit_method='chisq'):
    """What the selected exemplars *are*, in numbers — stated, not left implied.

    Without this the page prints "above χ²ᵥ = 5 a fit is not a solution" and then a
    table of ten fits, eight of them at χ²ᵥ ≈ 30, and never connects the two. On
    ``gloria_turbid_v3`` most exemplars are also redward of the turbid threshold, so
    they are spectra the model family does not claim — which a reader has to be told
    rather than left to infer from a wavelength column.
    """
    n_total = len(picks)
    chi2 = picks['chi2_nu'].to_numpy(dtype=float)
    n_bad = int((chi2 > records.CHI2NU_POOR_FIT).sum())
    n_over = int((chi2 < 1.0).sum())
    peaks = picks['peak_nm'].to_numpy(dtype=float)
    n_red = int((peaks > records.RED_PEAK_NM).sum())

    # the status the sweep itself recorded for these observations — matched on
    # (dataset, obs_id), since an obs_id alone can name a row in another dataset
    sc = sweep.scalar
    if sc is not None and not sc.empty and 'status' in sc.columns:
        keys = [k for k in diagnostics.OBS_KEYS
                if k in sc.columns and k in picks.columns]
        wanted = set(map(tuple, picks[keys].to_numpy()))
        sub = sc[sc[keys].apply(tuple, axis=1).isin(wanted)]
        if fit_method is not None and 'fit_method' in sub.columns:
            sub = sub[sub['fit_method'] == fit_method]
        counts = sub['status'].value_counts()
        breakdown = ', '.join(f'``{s}`` {int(c)}' for s, c in counts.items())
    else:
        breakdown = ''

    bits = [f'**What these {n_total} fits are.** ']
    if n_bad:
        bits.append(
            f'{n_bad} of the {n_total} {"has" if n_bad == 1 else "have"} a median '
            f'χ²ᵥ above {records.CHI2NU_POOR_FIT:g}, so by this package\'s own '
            f'threshold {"it is" if n_bad == 1 else "they are"} **not '
            f'{"a solution" if n_bad == 1 else "solutions"}** — the exemplars are '
            f'not a gallery of successes, and on a dataset the model family '
            f'struggles with, the median fit is expected to be one of the '
            f'failures. ')
    else:
        bits.append(f'All {n_total} sit at or below the χ²ᵥ = '
                    f'{records.CHI2NU_POOR_FIT:g} solution threshold. ')
    if n_over:
        bits.append(f'{n_over} {"sits" if n_over == 1 else "sit"} *below* '
                    f'χ²ᵥ = 1, i.e. over-fit relative to the assumed noise. ')
    if n_red:
        one = n_red == 1
        bits.append(
            f'{n_red} {"peaks" if one else "peak"} redward of '
            f'{records.RED_PEAK_NM:g} nm and {"is" if one else "are"} therefore '
            f'outside the regime these open-ocean parameterizations claim at all; '
            f'their misfit is a statement about **scope**, not about the fitter. ')
    if breakdown:
        bits.append(f'Recorded fit status across these observations and algorithms: '
                    f'{breakdown}.')
    return ''.join(bits)


def build_exemplars(sweep_id, *, root=None, docs_root=None, fit_method='chisq',
                    n=None):
    """Build the ``exemplar_fits.rst`` page: exemplar fits + closure + corners.

    The aggregate figures say how a population of retrievals behaves; none of them
    shows a reader a *single fit*, which is what an ocean-colour reader asks for
    when a summary statistic looks wrong ("show me a spectrum where it failed").
    This page answers that with the sweep's **best, worst and the rest drawn from
    around the median** by fit quality, laid out clear→turbid, plus the Rrs closure
    residuals for the two extremes and the posterior corner plots wherever a chain
    was saved.

    Returns the ``.rst`` path, or ``None`` when the sweep has no rankable fit.
    """
    sweep = figures.load(sweep_id, root=root)
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS_SRC
    report_dir = docs_root / 'reports' / sweep_id
    report_dir.mkdir(parents=True, exist_ok=True)

    picks = figures.exemplars(sweep, fit_method=fit_method,
                              **({'n': n} if n is not None else {}))
    if picks.empty:
        return None

    published, not_shown = set(), []
    # Every claim below is derived from the selection, not hard-coded: a thin sweep
    # yields fewer than ten panels, and a sweep with no persisted ``Rrs_obs`` is not
    # ordered by turbidity at all — prose asserting either would simply be false.
    by_peak = bool(picks['peak_nm'].notna().any())
    n_mid = int((picks['role'] == 'median').sum())
    multi_ds = 'dataset' in picks.columns and picks['dataset'].nunique() > 1
    ordered = ('by observed Rrs peak wavelength — clear water peaks in the blue, '
               'turbid water in the green-red' if by_peak else
               'by fit quality, because this sweep persisted no observed Rrs '
               'spectrum to derive a turbidity ordering from')
    middle = (f'the **{_spell(n_mid)}** nearest the median' if n_mid
              else 'nothing in between (the sweep has too few rankable fits)')
    grid_order = ('clear (top-left) to turbid (bottom-right)' if by_peak
                  else 'best (top-left) to worst (bottom-right) by fit quality')

    blocks = [rst.title(f'Exemplar fits — {sweep_id}'),
              rst.provenance_header(sweep_id, _provenance(sweep)),
              rst.section('Overview', _EXEMPLAR_INTRO.format(
                  sweep_id=sweep_id, n=len(picks), ordered=ordered,
                  middle=middle, chi2_max=records.CHI2NU_POOR_FIT,
                  red_peak=records.RED_PEAK_NM))]

    blocks.append(_fig_section(
        sweep, report_dir, 'Exemplar fits',
        _pngs(figures.exemplar_fits(sweep, picks, fit_method=fit_method,
                                    ordered_by_peak=by_peak)),
        caption=(f'{len(picks)} exemplar fits, {grid_order}. Black dots are the '
                 f'observed Rrs; each coloured line is one algorithm\'s modelled '
                 f'Rrs, its legend entry carrying that fit\'s own χ²ᵥ and relative '
                 f'misfit.'),
        desc=('Observed Rrs with every algorithm\'s modelled Rrs laid over it, one '
              'panel per exemplar observation. Rrs is on a **linear** axis (unlike '
              'the IOP spectra elsewhere) because hyperspectral red tails routinely '
              'cross zero, which a log axis would silently drop — the grey rule '
              'marks zero.'),
        published=published))

    blocks.append(rst.section(
        'The exemplars',
        _exemplar_summary(sweep, picks, fit_method=fit_method) + '\n\n'
        + _exemplar_table(picks, ordered_by_peak=by_peak,
                          multi_dataset=multi_ds)))

    # Rrs closure for the two extremes — the residual view of the same two fits
    extremes = [(r.role, r.obs_id, getattr(r, 'dataset', None))
                for r in picks.itertuples() if r.role in ('best', 'worst')]
    for role, obs_id, ds in extremes:
        where = f'obs {obs_id}' + (f' of {ds}' if multi_ds and ds else '')
        blocks.append(_fig_section(
            sweep, report_dir, f'Rrs closure — {role} fit ({where})',
            _pngs(figures.closure_set(sweep, obs_id, dataset=ds,
                                      fit_method=fit_method)),
            caption=(f'``Rrs_obs − Rrs_model`` for observation ``{obs_id}``, per '
                     f'algorithm, with each algorithm\'s χ²ᵥ in the legend.'),
            desc=('Closure residuals for the same fit as above, which is the view '
                  'that shows *where* in the spectrum the model fails rather than '
                  'by how much overall: a residual that is flat but offset is a '
                  'different fault from one that swings sign across the green.'),
            published=published))
    if not extremes:
        not_shown.append(
            'the Rrs closure residuals — this sweep produced too few rankable fits '
            'to have a distinct best and worst.')

    # posterior corner plots, where chains exist
    corner_paths = _pngs(figures.corner_set(sweep))
    if corner_paths:
        blocks.append(_fig_section(
            sweep, report_dir, 'Posterior corner plots',
            corner_paths,
            caption='Marginal and joint posteriors for one MCMC fit.',
            desc=('For the MCMC subset only. A corner plot is the one figure that '
                  'shows whether a parameter is *constrained* or merely *fitted*: '
                  'a banana-shaped joint posterior means the two parameters trade '
                  'off and neither is individually determined, which a χ² fit '
                  'reports as a confident number with a small error bar.'),
            published=published))
    else:
        not_shown.append(
            'the posterior corner plots — they need an MCMC fit with a saved chain, '
            'and this sweep has none (χ² fits carry a covariance, not a chain).')

    blocks.append(_not_shown_section(not_shown))

    out = report_dir / f'{EXEMPLAR_PAGE}.rst'
    out.write_text(rst.page(*blocks), encoding='utf-8')
    _prune_stale(report_dir, published, this_page=out.name)
    rst.ensure_glob_toctree(docs_root / 'reports' / 'index.rst')
    return out


_EXEMPLAR_INTRO = (
    'Every other figure in this report describes a **population** of retrievals. '
    'This page shows {n} individual fits from sweep ``{sweep_id}`` — the question an '
    'ocean-colour reader asks as soon as a summary statistic looks wrong: *show me a '
    'spectrum where it failed*.\n\n'
    '**How they were chosen.** Fit quality is ranked by distance from '
    ':math:`\\chi^2_\\nu = 1` in log space, and the page carries the **best** (the '
    'fit nearest χ²ᵥ = 1), the **worst** (the *largest* χ²ᵥ, i.e. the most '
    'under-fit) and {middle}. Ranking the *selection* by χ²ᵥ ascending would name '
    'the most **over-fit** spectrum in the sweep its best one: χ²ᵥ below 1 means the '
    'model is chasing noise, and on GLORIA χ²ᵥ moved by a factor of 5 when the '
    'assumed error floor changed while the fits themselves did not move at all. So '
    'both tails count as worse than the middle for *choosing* the exemplars — but '
    '"worst" names the under-fit tail specifically, because that is what the word '
    'conveys. Every panel prints its own χ²ᵥ (above {chi2_max:g} a fit is not '
    'considered a solution at all). Where several algorithms fit the same '
    'observation it is ranked by their median χ²ᵥ, because the panel shows all of '
    'them at once.\n\n'
    '**How they are ordered.** Panels run left-to-right, top-to-bottom {ordered} '
    '(the packaged clear/turbid threshold is {red_peak:g} nm — a poor fit whose peak '
    'sits redward of it is recorded as ``out_of_scope`` rather than as a failure, '
    'because the model family does not claim that water). Reading the grid in order '
    'therefore shows how the retrieval degrades as the water gets more turbid, which '
    'is the failure axis of every open-ocean parameterization applied to the coast. '
    'The relative misfit ``Δ`` beside each χ²ᵥ is '
    ':math:`\\mathrm{{median}}(|M-O|/O)` — it owes nothing to the assumed noise '
    'model, so it is the number to trust when χ²ᵥ and it disagree. Both are defined '
    'on the :doc:`/reports/glossary` page.')


def build_landing(*, docs_root=None, runs_root=None, root=None, board=None,
                  out=None):
    """Write the reports landing page: headline board, cards, drill-down, widget.

    Replaces a landing page that was 2 423 lines of ``list-table`` (with every
    accuracy cell ``nan``) followed by a bare ``:glob:`` toctree of undescribed
    links. Now: the ``stratum='all'`` headline table, one summary card per folded
    sweep, the interactive leaderboard, and a link to a **full grid** page carrying
    every stratum, fit method and provenance column.

    Returns ``(index_path, full_grid_path)``.
    """
    docs_root = Path(docs_root) if docs_root is not None else DEFAULT_DOCS_SRC
    if board is None:
        board = leaderboard.update(runs_root=runs_root, root=root, out=out)
    reports_dir = docs_root / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)

    # the drill-down page (its own doc, so the landing page stays scannable)
    full_grid = reports_dir / 'leaderboard_full.rst'
    full_grid.write_text(rst.page(
        rst.title('Leaderboard — full grid'),
        rst.section('Every contest, stratum and provenance column',
                    'The landing page shows the ``stratum="all"`` headline. This is '
                    'the complete fold: every stratum and fit method, the closure '
                    'columns that say *why* rows were not scored, and the '
                    'per-algorithm provenance digest plus the ``bing``/``ocpy`` '
                    'commits — because two rows sharing an algorithm name are not '
                    'necessarily the same algorithm.\n\n'
                    + leaderboard.render(board, headline=False))),
        encoding='utf-8')

    # cross-sweep profile pages: the site's standing answer, keyed by algorithm
    # and by dataset rather than by sweep id
    try:
        from ioptics.algorithms import registry
        known = registry.available()
    except Exception:
        known = ()
    try:
        from ioptics import datasets as _datasets
        known_datasets = _datasets.available_datasets()
    except Exception:
        known_datasets = ()
    # Every registered algorithm and dataset gets a page, even one nothing has been
    # run on: a page saying "not evaluated here" is more use to a reader than a
    # missing page, and it is the honest state of the comparison.
    profiles.build_profiles(docs_root=docs_root, runs_root=runs_root, root=root,
                            board=board, algorithms=known,
                            datasets=known_datasets)

    bokeh.vendor_bokehjs(docs_root / '_static', bundles=bokeh.TABLE_BUNDLES)
    try:
        widget = bokeh.leaderboard_embed(board=board, static_prefix='../')
    except Exception:                       # a widget is not worth failing a build
        widget = ''

    # "what has been evaluated on what" — including the cells nobody has tried.
    # Built by walking the runs tree, since a missing leaderboard row cannot tell
    # "never run" from "run but unscoreable".
    matrix = profiles.coverage_matrix(runs_root)
    board_rst = (leaderboard.render(board, headline=True)
                 + '\n' + rst.section(
                     'What has been evaluated on what',
                     'A blank cell would be ambiguous, so every pair states its '
                     'state explicitly — and the profile pages below carry the '
                     'detail.\n\n'
                     + profiles.render_coverage_matrix(
                         matrix, algorithms=known, datasets=known_datasets),
                     char='~'))
    # Hand-written pages that live under reports/ but are not generated: they must
    # be named in the toctree or ``sphinx -W`` fails on them, and named only when
    # present or it fails on the dangling reference instead.
    curated = tuple(name for name in CURATED_REPORT_PAGES
                    if (reports_dir / f'{name}.rst').is_file())
    rst.write_leaderboard_landing(
        reports_dir / 'index.rst',
        board_rst,
        cards_rst=leaderboard.sweep_cards(runs_root=runs_root, root=root,
                                          board=board, docs_root=docs_root),
        interactive_html=widget,
        full_grid_doc='/reports/leaderboard_full',
        extra_docs=('glossary',) + curated
                   + (f'{profiles.ALGORITHM_DIR}/*', f'{profiles.DATASET_DIR}/*'))
    return reports_dir / 'index.rst', full_grid

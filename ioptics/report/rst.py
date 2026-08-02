"""Assemble ``.rst`` pages for the single accumulating readthedocs site.

Small string builders that turn copied display assets (figure PNGs, CSV tables,
the standalone Bokeh HTML) into reStructuredText, plus the toctree/landing-page
plumbing. The heavy lifting (loading, rendering, copying) is in
:mod:`ioptics.report.standard`; here we only format RST, so every function is a
pure ``str``/path in → ``str`` out (except the two site-file updaters, which are
idempotent in-place edits).

All directives use paths **relative to the page**, so a report dir is
self-contained and RTD builds it directly.
"""

from __future__ import annotations

from pathlib import Path

# Sentinels bounding the rendered leaderboard on the landing page (idempotent).
LEADERBOARD_START = '.. LEADERBOARD_START (auto-generated; do not edit)'
LEADERBOARD_END = '.. LEADERBOARD_END'


def _underline(text, char='='):
    return f'{text}\n{char * len(text)}'


def title(text):
    """A top-level RST title (over/underlined)."""
    bar = '=' * len(text)
    return f'{bar}\n{text}\n{bar}\n'


def provenance_header(sweep_id, provenance):
    """A field-list header stamping the sweep + code/doc versions.

    ``provenance`` is the parsed ``provenance.yaml`` dict (or ``{}``); missing
    fields are simply omitted so a report without provenance still renders.
    """
    lines = [f':Sweep: {sweep_id}']
    if provenance.get('created'):
        lines.append(f":Generated: {provenance['created']}")
    versions = provenance.get('versions', {}) or {}
    for pkg in ('ioptics', 'bing', 'ocpy'):
        blk = versions.get(pkg) or {}
        ver, commit = blk.get('version'), (blk.get('commit') or '')
        if ver or commit:
            lines.append(f':{pkg}: {ver or ""}@{commit[:8]}')
    for doc in ('design_doc', 'implementation_doc'):
        if versions.get(doc):
            lines.append(f':{doc}: {versions[doc]}')
    return '\n'.join(lines) + '\n'


def section(heading, body, char='-'):
    """A sub-section: underlined heading + body."""
    return f'{_underline(heading, char)}\n\n{body}\n'


def figure_block(relpath, caption='', *, width='90%'):
    """A ``.. figure::`` directive (path relative to the page)."""
    out = [f'.. figure:: {relpath}', f'   :width: {width}', '']
    if caption:
        out.append(f'   {caption}')
        out.append('')
    return '\n'.join(out)


def csv_table_block(relpath, title_text=''):
    """A ``.. csv-table::`` reading a copied CSV (header row assumed)."""
    return '\n'.join([f'.. csv-table:: {title_text}'.rstrip(),
                      f'   :file: {relpath}',
                      '   :header-rows: 1', ''])


def bokeh_raw(relpath, *, height=560):
    """Embed a standalone Bokeh HTML file via a ``raw:: html`` ``<iframe>``."""
    return '\n'.join([
        '.. raw:: html', '',
        f'   <iframe src="{relpath}" width="100%" height="{height}" '
        'frameborder="0"></iframe>', ''])


def bokeh_embed(fragment):
    """Inline a pre-rendered Bokeh HTML fragment (CDN + components) via ``raw:: html``.

    ``fragment`` is the BokehJS CDN ``<script>`` tags + the ``components``
    ``<div>``/``<script>`` (from :func:`ioptics.report.bokeh.scatter_embed`). The
    figure renders **inside** the page — no separate file to copy — so it
    survives a Sphinx/RTD build. Every line is indented into the directive body.
    """
    body = '\n'.join('   ' + line for line in fragment.splitlines())
    return '.. raw:: html\n\n' + body + '\n'


def page(*blocks):
    """Join RST blocks with a blank line between each (+ trailing newline).

    The blank-line separator is required: consecutive directives / field lists
    without one trip ``docutils`` "explicit markup ends without a blank line".
    """
    return '\n\n'.join(b.rstrip('\n') for b in blocks if b) + '\n'


# --------------------------------------------------------------------------- #
# site plumbing (idempotent in-place edits)
# --------------------------------------------------------------------------- #

def ensure_glob_toctree(reports_index):
    """Ensure ``reports/index.rst`` has a ``:glob:`` toctree over ``*/*``.

    Creates a minimal index if absent; otherwise upgrades the trailing plain
    toctree to a glob one (leaving the curated prose intact). Idempotent.
    """
    reports_index = Path(reports_index)
    glob_block = ('.. toctree::\n   :maxdepth: 1\n   :glob:\n\n   */*\n')
    if not reports_index.is_file():
        reports_index.parent.mkdir(parents=True, exist_ok=True)
        reports_index.write_text(title('Reports') + '\n' + glob_block, encoding='utf-8')
        return reports_index
    text = reports_index.read_text(encoding='utf-8')
    if ':glob:' in text:
        return reports_index
    plain = '.. toctree::\n   :maxdepth: 1\n'
    if plain in text:
        text = text.replace(plain, glob_block, 1)
    else:
        text = text.rstrip() + '\n\n' + glob_block
    reports_index.write_text(text, encoding='utf-8')
    return reports_index


def write_leaderboard_landing(reports_index, table_rst):
    """Insert/replace the rendered leaderboard between sentinels on the landing page.

    Idempotent: re-rendering replaces the block; the surrounding prose and
    toctree are untouched. Creates the index (with a glob toctree) if absent.
    """
    reports_index = Path(reports_index)
    ensure_glob_toctree(reports_index)
    text = reports_index.read_text(encoding='utf-8')
    block = (f'{LEADERBOARD_START}\n\n'
             + section('Leaderboard', table_rst)
             + f'\n{LEADERBOARD_END}\n')
    if LEADERBOARD_START in text and LEADERBOARD_END in text:
        pre = text[:text.index(LEADERBOARD_START)]
        post = text[text.index(LEADERBOARD_END) + len(LEADERBOARD_END):]
        text = pre + block + post.lstrip('\n')
    else:
        # insert before the first toctree so the board sits above the page list
        anchor = '.. toctree::'
        i = text.index(anchor) if anchor in text else len(text)
        text = text[:i] + block + '\n' + text[i:]
    reports_index.write_text(text, encoding='utf-8')
    return reports_index

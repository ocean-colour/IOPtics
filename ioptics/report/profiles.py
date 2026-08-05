"""Cross-sweep **profile** pages: one per algorithm, one per dataset.

Every other page on the site is keyed by ``sweep_id``, which only answers "what did
this run do" — a question no outside reader arrives with. These pages answer the two
they do arrive with:

* *How does this model do, everywhere?* → :func:`build_algorithm_profile`
* *Which model should I use on this data?* → :func:`build_dataset_profile`

They are **folded across every sweep** in the runs tree, so they are the site's
standing answer and a stable URL a paper can cite, while the per-sweep pages remain
the provenance-stamped audit trail behind them.

Hybrid by design (JXP's decision): the tables and figures are generated, and each
page ``.. include::`` s a hand-written ``findings.rst`` beside it if one exists — a
generated page can state what the metrics say, but not what they mean.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ioptics import io, metrics
from ioptics.report import figures, leaderboard, rst, tables

#: Where profile pages live under the Sphinx source tree. Chosen so the *results*
#: pages sit beside the sweeps under ``reports/`` and cannot be confused with the
#: reference pages ``models.rst`` / ``datasets.rst``, which describe the models and
#: data themselves rather than any measurement of them.
ALGORITHM_DIR = 'algorithms'
DATASET_DIR = 'datasets'

#: The states a cell of the coverage matrix can be in. The distinction matters: a
#: reader must be able to tell "nobody has tried this" from "it was tried and there
#: was nothing to score it against" from "it was tried and it failed", and the
#: leaderboard alone cannot — a missing row conflates all three.
NOT_EVALUATED = 'not evaluated'
NO_TRUTH = 'no scoreable truth'
FAILED = 'all fits failed'
SCORED = 'scored'


def _sweep_dirs(runs_root):
    """Every sweep directory that carries a results table (not just metrics)."""
    runs_root = Path(runs_root)
    if not runs_root.is_dir():
        return []
    return sorted(p for p in runs_root.iterdir()
                  if (p / io.SCALAR_FILE).is_file())


def coverage_matrix(runs_root=None, *, root=None):
    """``(algorithm, dataset) → state`` over the whole runs tree.

    Built by **walking the runs tree**, not by reading the leaderboard: the fold
    drops a sweep whose metrics are missing or whose accuracy slice is empty, so
    absence of a leaderboard row cannot distinguish "never run" from "run but not
    scoreable". Here every attempted ``(algorithm, dataset)`` is visible because
    ``results_scalar`` records the attempt itself.

    Returns a tidy frame with one row per pair: ``state`` (one of
    :data:`SCORED`, :data:`NO_TRUTH`, :data:`FAILED`, :data:`NOT_EVALUATED`),
    ``n_attempted``, ``n_ok``, ``n_scored_pairs`` and the contributing ``sweeps``.
    """
    runs_root = Path(runs_root) if runs_root is not None else io.runs_root(root)
    rows = {}
    for d in _sweep_dirs(runs_root):
        scalar = pd.read_parquet(d / io.SCALAR_FILE)
        mpath = d / metrics.METRICS_SCALAR_FILE
        ms = pd.read_parquet(mpath) if mpath.is_file() else None
        for (dataset, algo), g in scalar.groupby(['dataset', 'algorithm']):
            key = (str(algo), str(dataset))
            rec = rows.setdefault(key, {'algorithm': str(algo),
                                        'dataset': str(dataset),
                                        'n_attempted': 0, 'n_ok': 0,
                                        'n_scored_pairs': 0, 'sweeps': []})
            rec['n_attempted'] += int(len(g))
            rec['n_ok'] += int((g['status'] == 'ok').sum())
            rec['sweeps'].append(d.name)
            if ms is not None:
                sub = ms[(ms['dataset'] == dataset) & (ms['algorithm'] == algo)
                         & ms['component'].isin(metrics.ACCURACY_COMPONENTS)
                         & ms['ref_wave'].notna()]
                if not sub.empty and 'n' in sub.columns:
                    rec['n_scored_pairs'] += int(sub['n'].fillna(0).max())
    out = []
    for rec in rows.values():
        if rec['n_scored_pairs'] > 0:
            state = SCORED
        elif rec['n_ok'] == 0:
            state = FAILED
        else:
            state = NO_TRUTH
        rec['state'] = state
        rec['sweeps'] = ', '.join(sorted(set(rec['sweeps'])))
        out.append(rec)
    cols = ['algorithm', 'dataset', 'state', 'n_attempted', 'n_ok',
            'n_scored_pairs', 'sweeps']
    return (pd.DataFrame(out, columns=cols)
              .sort_values(['algorithm', 'dataset']).reset_index(drop=True)
            if out else pd.DataFrame(columns=cols))


def render_coverage_matrix(matrix, *, algorithms=None, datasets=None):
    """The matrix as an RST grid — algorithms down, datasets across.

    Empty cells read **not evaluated** rather than being left blank, because "we
    have not tried this" is information a reader needs before any ranking matters.
    ``algorithms``/``datasets`` extend the axes with names that were never run at
    all (e.g. a registered algorithm no sweep has used).
    """
    algos = sorted(set(matrix['algorithm']) | set(algorithms or ()))
    dsets = sorted(set(matrix['dataset']) | set(datasets or ()))
    if not algos or not dsets:
        return 'No sweep artifacts were found, so there is nothing to compare yet.\n'
    lookup = {(r.algorithm, r.dataset): r for r in matrix.itertuples()}

    def _cell(algo, dataset):
        rec = lookup.get((algo, dataset))
        if rec is None:
            return NOT_EVALUATED
        if rec.state == SCORED:
            return f'{SCORED} (n={rec.n_scored_pairs})'
        if rec.state == FAILED:
            return f'{FAILED} ({rec.n_attempted} attempted)'
        return f'{NO_TRUTH} ({rec.n_ok}/{rec.n_attempted} fits ok)'

    lines = ['.. list-table:: What has been evaluated on what',
             '   :header-rows: 1', '   :stub-columns: 1', '   :widths: auto', '']
    lines.append('   * - algorithm')
    lines.extend(f'     - {d}' for d in dsets)
    for algo in algos:
        lines.append(f'   * - ``{algo}``')
        lines.extend(f'     - {_cell(algo, d)}' for d in dsets)
    return '\n'.join(lines) + '\n'


def _spec_block(name):
    """What an algorithm parameterizes, read from its registry entry.

    Generated from the ``AlgorithmSpec`` rather than written by hand, so it cannot
    drift from what actually ran. Returns ``''`` for an algorithm the registry does
    not know (a sweep may carry results for one that was later removed).
    """
    try:
        from ioptics.algorithms import registry
        spec = registry.get(name)
    except Exception:
        return ''
    rows = [('a_nw model', spec.anw_model), ('bb_nw model', spec.bbnw_model),
            ('fit method', spec.fit_method or 'chisq')]
    for label, attr in (('set_Sdg', 'set_Sdg'), ('sSdg', 'sSdg'),
                        ('beta', 'beta'), ('maxfev', 'maxfev')):
        val = getattr(spec, attr, None)
        if val not in (None, False):
            rows.append((label, val))
    rt = {k: v for k, v in (getattr(spec, 'rt', None).__dict__.items()
                            if getattr(spec, 'rt', None) is not None else [])
          if v}
    if rt:
        rows.append(('RT toggles', ', '.join(f'``{k}``' for k in sorted(rt))))
    lines = ['.. list-table::', '   :stub-columns: 1', '   :widths: auto', '']
    for label, val in rows:
        lines.append(f'   * - {label}')
        lines.append(f'     - {val}')
    return '\n'.join(lines) + '\n'


def _findings_include(page_dir, stem):
    """An ``.. include::`` for a hand-written ``<stem>_findings.rst``, if present.

    The hybrid seam: a generated page can report what the metrics say, but only a
    person can say what it means. The builder never writes or overwrites this file.
    """
    if (Path(page_dir) / f'{stem}_findings.rst').is_file():
        return rst.section('What we found',
                           f'.. include:: {stem}_findings.rst\n')
    return ''


def _algorithm_summary(board, name):
    """A prose paragraph with numbers: where this algorithm stands, and on what."""
    mine = board[board['algorithm'] == name]
    if mine.empty:
        return (f'``{name}`` is registered but no sweep in this runs tree has '
                f'produced a scoreable result for it yet — see the coverage matrix '
                f'on :doc:`/reports/index`.')
    scored = mine[mine['mae'].notna()] if 'mae' in mine.columns else mine
    datasets = sorted(mine['dataset'].dropna().unique())
    sweeps = sorted(mine['sweep_id'].dropna().unique()) \
        if 'sweep_id' in mine.columns else []
    if scored.empty:
        return (f'``{name}`` has been run on {", ".join(datasets)} across '
                f'{len(sweeps)} sweep(s), but no contest yielded a scoreable '
                f'retrieval-truth pair, so there is no accuracy to report — the '
                f'per-sweep pages say why.')
    best = scored.loc[scored['mae'].idxmin()]
    worst = scored.loc[scored['mae'].idxmax()]
    parts = [
        f'``{name}`` has scoreable results on **{", ".join(datasets)}** across '
        f'{len(sweeps)} sweep(s). Its best contest is '
        f'{best["component"]}({best["ref_wave"]:g}) on {best["dataset"]}, at '
        f'mae {best["mae"]:.3g} ({best["mae"]:.1%} multiplicative error); its '
        f'worst is {worst["component"]}({worst["ref_wave"]:g}) on '
        f'{worst["dataset"]} at {worst["mae"]:.3g}.']
    if 'frac_ok' in mine.columns and mine['frac_ok'].notna().any():
        parts.append(f'It produced a usable fit for '
                     f'{mine["frac_ok"].dropna().min():.0%}-'
                     f'{mine["frac_ok"].dropna().max():.0%} of the spectra it was '
                     f'given, depending on the dataset — read that together with '
                     f'the accuracy, since a good score over few spectra is not a '
                     f'better algorithm than a fair score over all of them.')
    return ' '.join(parts)


def _dataset_summary(board, name):
    """A prose paragraph with numbers: what this data can score, and who leads."""
    mine = board[board['dataset'] == name]
    if mine.empty:
        return (f'No sweep in this runs tree has produced a scoreable result on '
                f'**{name}** yet.')
    scored = mine[mine['mae'].notna()] if 'mae' in mine.columns else mine
    algos = sorted(mine['algorithm'].dropna().unique())
    comps = sorted(scored['component'].dropna().unique()) if not scored.empty \
        else []
    parts = [f'**{name}** has been fitted by {len(algos)} algorithm(s): '
             f'{", ".join(f"``{a}``" for a in algos)}.']
    if not comps:
        parts.append('None of them could be scored against spectral truth here — '
                     'this dataset carries truth for no reference band in the '
                     'sweeps folded so far, so the comparison rests on fit quality '
                     'rather than accuracy.')
        return ' '.join(parts)
    parts.append(f'It scores {", ".join(comps)} at the reference bands.')
    ranked = leaderboard.ranked(mine)
    lead = ranked[ranked['rank'] == 1]
    if not lead.empty:
        row = lead.iloc[0]
        parts.append(f'The leading entry is ``{row["algorithm"]}`` on '
                     f'{row["component"]}({row["ref_wave"]:g}).')
    elif (ranked['ranking'] == 'indistinguishable').any():
        parts.append('No pair of algorithms separated on any contest here, so the '
                     'page reports them as indistinguishable rather than ranking '
                     'them — see the head-to-head table on the sweep pages.')
    return ' '.join(parts)


def _truth_matrix(matrix, dataset):
    """Which components/algorithms this dataset can actually score."""
    mine = matrix[matrix['dataset'] == dataset]
    if mine.empty:
        return ''
    lines = ['.. list-table:: What this dataset can score',
             '   :header-rows: 1', '   :widths: auto', '',
             '   * - algorithm', '     - state', '     - attempted',
             '     - fits ok', '     - scored pairs']
    for r in mine.itertuples():
        lines += [f'   * - ``{r.algorithm}``', f'     - {r.state}',
                  f'     - {r.n_attempted}', f'     - {r.n_ok}',
                  f'     - {r.n_scored_pairs}']
    return '\n'.join(lines) + '\n'


def _list_table(df, cols, title='', *, max_rows=60):
    """A DataFrame as an RST ``list-table`` (empty string if nothing to show)."""
    cols = [c for c in cols if c in df.columns]
    if df.empty or not cols:
        return ''
    view = df[cols].head(max_rows)

    def _cell(v):
        if v is None or v is pd.NA or (isinstance(v, float) and pd.isna(v)):
            return '—'
        if isinstance(v, float):
            return f'{v:.3g}'
        return str(v)

    lines = [f'.. list-table:: {title}'.rstrip(), '   :header-rows: 1',
             '   :widths: auto', '']
    lines.append('   * - ' + cols[0])
    lines.extend('     - ' + c for c in cols[1:])
    for _, row in view.iterrows():
        lines.append('   * - ' + _cell(row[cols[0]]))
        lines.extend('     - ' + _cell(row[c]) for c in cols[1:])
    note = ('' if len(df) <= max_rows
            else f'\n({len(df) - max_rows} further rows are on the '
                 f':doc:`/reports/leaderboard_full` page.)\n')
    return '\n'.join(lines) + '\n' + note


def _pair_rows(runs_root, *, algorithm=None, dataset=None):
    """Head-to-head verdict rows from every sweep, optionally filtered."""
    frames = []
    for d in _sweep_dirs(runs_root):
        path = d / metrics.METRICS_PAIRWISE_FILE
        if not path.is_file():
            continue
        pw = pd.read_parquet(path)
        if 'contest' not in pw.columns:
            continue
        rows = pw[pw['contest'] == 'pair'].copy()
        if rows.empty:
            continue
        rows['sweep_id'] = d.name
        frames.append(rows)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    if 'n_paired' in out.columns:
        out = out[out['n_paired'].fillna(0) > 0]
    if algorithm is not None:
        out = out[(out['model_a'] == algorithm) | (out['model_b'] == algorithm)]
    if dataset is not None and 'dataset' in out.columns:
        out = out[out['dataset'] == dataset]
    return out.reset_index(drop=True)


def _what_varied(board, name):
    """Whether one algorithm ran under more than one configuration, and where.

    JXP's decision was to pool sweeps into a single profile (option (a)), which is
    only honest if the page says when the pooled runs were **not** configured
    identically. The ``algo_digest`` is a hash of each sweep's persisted algorithm
    block, so differing digests mean differing configurations.
    """
    mine = board[board['algorithm'] == name]
    if mine.empty or 'algo_digest' not in mine.columns:
        return ''
    cfg_cols = [c for c in ('algo_digest', 'versions', 'bing', 'ocpy')
                if c in mine.columns]
    combos = (mine[['sweep_id'] + cfg_cols].drop_duplicates()
                  .dropna(subset=['sweep_id']))
    # Two sweeps that ran the *same* configuration are pooled silently — that is
    # the point of pooling. The warning is only for genuinely different configs,
    # so count distinct configurations rather than distinct (sweep, config) rows.
    if combos[cfg_cols].drop_duplicates().shape[0] <= 1:
        return ''
    body = ('This profile pools every sweep that ran ``%s``. The runs were **not**\n'
            'identically configured — each row below is one distinct persisted\n'
            'algorithm block (``algo_digest``), so numbers from different rows are\n'
            'not strictly like-for-like:\n\n' % name)
    return rst.section('What varied between sweeps',
                       body + _list_table(combos,
                                          ['sweep_id', 'algo_digest', 'versions',
                                           'bing', 'ocpy'],
                                          'Configurations pooled here'))


_SEE_ALSO = (
    'Every column on this page is defined on the :doc:`/reports/glossary` page — '
    'including which value counts as *perfect* for each metric, the three different '
    '``n`` denominators, and what the tie and calibration verdicts do and do not '
    'claim. For what the models are (rather than how they scored) see '
    ':doc:`/models`; for the data and its truth see :doc:`/datasets`.')


def build_algorithm_profile(name, *, docs_root=None, runs_root=None, root=None,
                            board=None):
    """Write ``reports/algorithms/<name>.rst`` — one algorithm, every dataset."""
    docs_root, runs_root, board = _resolve(docs_root, runs_root, root, board)
    page_dir = docs_root / 'reports' / ALGORITHM_DIR
    page_dir.mkdir(parents=True, exist_ok=True)
    matrix = coverage_matrix(runs_root)
    mine = board[board['algorithm'] == name] if not board.empty else board
    ranked = leaderboard.ranked(mine) if not mine.empty else mine
    scored = (ranked[ranked['mae'].notna()] if 'mae' in getattr(ranked, 'columns', [])
              else ranked)
    pairs = _pair_rows(runs_root, algorithm=name)

    blocks = [
        rst.title(f'Algorithm profile — {name}'),
        rst.section('In one paragraph', _algorithm_summary(board, name)),
        rst.section('What it parameterizes',
                    'Read from the registry entry that sweeps actually run, so it '
                    'cannot drift from the configuration behind the numbers '
                    'below.\n\n' + (_spec_block(name) or 'Not in the registry.\n')),
        rst.section('Where it has been evaluated',
                    render_coverage_matrix(matrix[matrix['algorithm'] == name])),
    ]
    if not scored.empty:
        blocks.append(rst.section(
            'Accuracy, by dataset and contest',
            _list_table(scored, ['dataset', 'component', 'ref_wave', 'fit_method',
                                 'rank', 'ranking', 'mae', 'bias', 'win_frac',
                                 'frac_ok', 'caveat'],
                        f'{name} — scored contests')))
        blocks.append(rst.section(
            'Are its uncertainties honest?',
            'A retrieval can be the most accurate and still be over-confident: '
            'the verdict compares empirical coverage with its nominal 0.68 / 0.95 '
            'target, and *consistent* means "not distinguishable from nominal at '
            'this sample size" rather than "calibrated".\n\n'
            + _list_table(scored, ['dataset', 'component', 'ref_wave',
                                   'coverage68', 'coverage95', 'coverage_n'],
                          f'{name} — interval calibration')))
    if not pairs.empty:
        blocks.append(rst.section(
            'Head-to-head against the others',
            _list_table(pairs, ['sweep_id', 'dataset', 'component', 'ref_wave',
                                'model_a', 'model_b', 'n_paired', 'delta_mae',
                                'd_lo', 'd_hi', 'verdict'],
                        f'{name} — pairwise verdicts')))
    blocks.append(_what_varied(board, name))
    blocks.append(rst.section(
        'Per-spectrum behaviour',
        'Exemplar fits (best / worst / median) live on each sweep\'s own page; the '
        'accuracy-vs-wavelength view is built per sweep as well. Both are linked '
        'from the contributing sweeps listed on :doc:`/reports/index`.'))
    blocks.append(_findings_include(page_dir, name))
    blocks.append(rst.section('See also', _SEE_ALSO))

    out = page_dir / f'{name}.rst'
    out.write_text(rst.page(*[b for b in blocks if b]), encoding='utf-8')
    return out


def build_dataset_profile(name, *, docs_root=None, runs_root=None, root=None,
                          board=None):
    """Write ``reports/datasets/<name>.rst`` — one dataset, every algorithm."""
    docs_root, runs_root, board = _resolve(docs_root, runs_root, root, board)
    page_dir = docs_root / 'reports' / DATASET_DIR
    page_dir.mkdir(parents=True, exist_ok=True)
    matrix = coverage_matrix(runs_root)
    mine = board[board['dataset'] == name] if not board.empty else board
    ranked = leaderboard.ranked(mine) if not mine.empty else mine
    scored = (ranked[ranked['mae'].notna()] if 'mae' in getattr(ranked, 'columns', [])
              else ranked)
    pairs = _pair_rows(runs_root, dataset=name)

    blocks = [
        rst.title(f'Dataset profile — {name}'),
        rst.section('In one paragraph', _dataset_summary(board, name)),
        rst.section('What this dataset can score',
                    'A dataset can only score what it carries truth for; a '
                    'component with no truth here is absent rather than '
                    'failing.\n\n' + (_truth_matrix(matrix, name)
                                      or 'No attempts recorded.\n')),
    ]
    if not scored.empty:
        blocks.append(rst.section(
            'Ranked contests',
            'Where no pair of algorithms separated, the ``ranking`` column says '
            '*indistinguishable* instead of printing an order the data do not '
            'support.\n\n'
            + _list_table(scored.sort_values(['component', 'ref_wave', 'rank'],
                                             na_position='last'),
                          ['component', 'ref_wave', 'stratum', 'fit_method',
                           'rank', 'ranking', 'algorithm', 'mae', 'bias',
                           'win_frac', 'caveat'],
                          f'{name} — who leads where')))
        blocks.append(rst.section(
            'Retrieval success',
            'The gap between spectra attempted and spectra scored is a statement '
            'about the **models**, not about the data or the software: '
            '``frac_out_of_scope`` means the spectrum sits outside the model '
            'family\'s regime.\n\n'
            + _list_table(scored.drop_duplicates(['algorithm', 'fit_method']),
                          ['algorithm', 'fit_method', 'n_attempted', 'frac_ok',
                           'frac_poor_fit', 'frac_out_of_scope',
                           'frac_fit_failed', 'chi2_nu_median',
                           'rel_misfit_median_all'],
                          f'{name} — why rows were or were not scored')))
        by_stratum = scored[scored['stratum'] != 'all'] \
            if 'stratum' in scored.columns else pd.DataFrame()
        if not by_stratum.empty:
            blocks.append(rst.section(
                'By water type',
                _list_table(by_stratum.sort_values(['stratum', 'component']),
                            ['stratum', 'component', 'ref_wave', 'algorithm',
                             'rank', 'mae', 'win_frac', 'frac_ok'],
                            f'{name} — per trophic stratum')))
        methods = sorted(scored['fit_method'].dropna().unique()) \
            if 'fit_method' in scored.columns else []
        if len(methods) > 1:
            blocks.append(rst.section(
                'Least-squares vs MCMC',
                f'Both fit methods scored here ({", ".join(methods)}). They are '
                f'ranked as separate contests — a win fraction from one pool cannot '
                f'be compared with one from the other.\n\n'
                + _list_table(scored.sort_values(['fit_method', 'component']),
                              ['fit_method', 'component', 'ref_wave', 'algorithm',
                               'mae', 'coverage68', 'frac_ok'],
                              f'{name} — by fit method')))
    if not pairs.empty:
        blocks.append(rst.section(
            'Head-to-head',
            _list_table(pairs, ['component', 'ref_wave', 'model_a', 'model_b',
                                'n_paired', 'delta_mae', 'd_lo', 'd_hi',
                                'verdict'],
                        f'{name} — pairwise verdicts')))
    blocks.append(_findings_include(page_dir, name))
    blocks.append(rst.section('See also', _SEE_ALSO))

    out = page_dir / f'{name}.rst'
    out.write_text(rst.page(*[b for b in blocks if b]), encoding='utf-8')
    return out


def _resolve(docs_root, runs_root, root, board):
    """Default the docs tree, the runs tree and the folded board."""
    from ioptics.report import standard

    docs_root = Path(docs_root) if docs_root is not None \
        else standard.DEFAULT_DOCS_SRC
    runs_root = Path(runs_root) if runs_root is not None else io.runs_root(root)
    if board is None:
        board = leaderboard.update(runs_root=runs_root, root=root)
    return docs_root, runs_root, board


def build_profiles(*, docs_root=None, runs_root=None, root=None, board=None,
                   algorithms=None, datasets=None):
    """Write a profile page for every algorithm and dataset with any results.

    ``algorithms``/``datasets`` add names that have no results yet — a registered
    algorithm nobody has run still gets a page saying so, which is more useful than
    a missing page. Returns ``(algorithm_paths, dataset_paths)``.
    """
    docs_root, runs_root, board = _resolve(docs_root, runs_root, root, board)
    matrix = coverage_matrix(runs_root)
    algos = sorted(set(matrix['algorithm']) | set(algorithms or ()))
    dsets = sorted(set(matrix['dataset']) | set(datasets or ()))
    a_paths = [build_algorithm_profile(a, docs_root=docs_root,
                                       runs_root=runs_root, board=board)
               for a in algos]
    d_paths = [build_dataset_profile(d, docs_root=docs_root, runs_root=runs_root,
                                     board=board) for d in dsets]
    return a_paths, d_paths

"""The persistent leaderboard, aggregated across sweep directories.

The headline deliverable: a leaderboard that **accumulates across sweeps**
rather than living inside one. :func:`update` scans the runs root, folds every
sweep's ref-band `metrics_scalar` (+ the `metrics_pairwise` wins and the
`provenance.yaml` version stamp) into a single append-only
``leaderboard.parquet``, and is **idempotent** — re-folding a sweep replaces its
rows, other sweeps are untouched. :func:`render` produces the ranked RST table
for the site landing page.

Default ranking (design Q23): **wins** first, then ``|bias|`` and log-space
**MAE** at the reference wavelengths, per ``(dataset, component, ref_wave)``;
MAE / bias / coverage ride along as adjacent columns.

The ranked numbers come from :mod:`ioptics.metrics`, which scores **solutions
only** (``status == 'ok'``), so each entry also carries ``frac_ok`` — the share
of attempted spectra that produced one. Read the two together: a top rank over
10% of the spectra is not a better algorithm than a lower rank over all of
them. The GLORIA
``CDOM_vs_adg`` **caveat** is folded through and shown in the rendered table, so
the accumulated leaderboard surfaces the CDOM-vs-``a_dg`` truth-mapping mismatch
on GLORIA ``a_dg`` rows.

Consumes only persisted artifacts (no re-fitting, no BING/ocpy).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ioptics import io, metrics, provenance

LEADERBOARD_FILE = 'leaderboard.parquet'

# Columns folded from each sweep's ref-band accuracy rows (+ win_frac).
_VALUE_COLS = ['n', 'coverage_n', 'bias', 'abs_bias', 'mae', 'rms_log',
               'coverage68', 'coverage95']
#: ``fit_method`` is a key, not a filter. The fold used to hard-select ``chisq``,
#: which made an MCMC-fit algorithm invisible on the board no matter how well it
#: performed — and silently, since the column was not carried either.
_KEY_COLS = ['sweep_id', 'dataset', 'algorithm', 'fit_method', 'stratum',
             'component', 'ref_wave']

#: Closure columns folded alongside accuracy. Without them the board cannot answer
#: "why were the other 79% not scored", which is half of what a rank means.
_CLOSURE_COLS = ['frac_ok', 'n_attempted', 'frac_overfit', 'frac_poor_fit',
                 'frac_out_of_scope', 'frac_fit_failed', 'chi2_nu_median',
                 'rel_misfit_median', 'rel_misfit_median_all']
# Sort within each (dataset, component, ref_wave, stratum) contest.
_RANK_BY = ['win_frac', 'abs_bias', 'mae']

#: Landing-page columns — what a reader scans before drilling in. ``frac_ok`` rides
#: with the accuracy numbers because a top rank over a tenth of the spectra is not a
#: better algorithm than a lower rank over all of them (Brewin's eta, promoted from a
#: trailing column to a scored one).
HEADLINE_COLS = ['dataset', 'component', 'ref_wave', 'fit_method', 'rank',
                 'ranking', 'algorithm', 'win_frac', 'mae', 'bias', 'frac_ok',
                 'coverage68', 'caveat']

#: The full drill-down grid.
FULL_COLS = ['dataset', 'component', 'ref_wave', 'stratum', 'fit_method', 'rank',
             'ranking', 'algorithm', 'win_frac', 'bias', 'mae', 'coverage68',
             'coverage95', 'coverage_n', 'frac_ok', 'n_attempted',
             'frac_overfit', 'frac_poor_fit', 'frac_out_of_scope',
             'frac_fit_failed', 'chi2_nu_median', 'rel_misfit_median',
             'rel_misfit_median_all', 'caveat', 'versions', 'bing', 'ocpy',
             'algo_digest', 'prov_schema', 'provenance_id']
_RANK_ASC = [False, True, True]


def _default_out(runs_root):
    """Leaderboard path: sibling of the runs root (``…/IOPtics/leaderboard.parquet``)."""
    return runs_root.parent / LEADERBOARD_FILE


def _provenance(sweep_dir):
    """Parsed ``provenance.yaml`` for a sweep dir (``{}`` if absent/unreadable)."""
    path = sweep_dir / 'provenance.yaml'
    if not path.is_file():
        return {}
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _version_stamps(sweep_dir):
    """``{'ioptics': 'v@commit', 'bing': 'commit', 'ocpy': 'commit'}``.

    The fold used to keep the ``ioptics`` stamp alone, but **BING** is where the
    model forms and the fitter live and **ocpy** is where the data loaders do, so a
    row stamped only with an ioptics commit does not identify what produced it.
    """
    versions = _provenance(sweep_dir).get('versions', {}) or {}

    def _one(name):
        entry = versions.get(name) or {}
        if not isinstance(entry, dict):
            return str(entry)
        commit = (entry.get('commit') or '')[:8]
        ver = entry.get('version') or ''
        return f'{ver}@{commit}' if commit and ver else (commit or ver)

    return {'ioptics': _one('ioptics'), 'bing': _one('bing'),
            'ocpy': _one('ocpy')}


def _algorithm_digests(sweep_dir):
    """``{algorithm: digest}`` over each sweep's persisted algorithm block.

    Two rows sharing an algorithm *name* are not necessarily the same algorithm —
    the turbid GLORIA sweep ran ``expb_pow`` with a raised iteration budget while its
    recorded block was byte-identical to the default, because ``maxfev`` was not
    recorded at all before Task 9.

    Prefers the digest the **sweep itself** recorded (``block['digest']``, computed at
    run time from the resolved spec, after any config overrides), falling back to
    :func:`ioptics.provenance.algorithm_digest` over the block. Both paths now use the
    same definition — previously this hashed the whole block *including* ``name`` and
    ``label`` at 8 characters while provenance recorded 12 over the block without
    them, so the board's ``algo_digest`` could never equal the recorded one and two
    incompatible "digests" coexisted on disk.
    """
    blocks = _provenance(sweep_dir).get('algorithms') or []
    out = {}
    for block in blocks:
        if not isinstance(block, dict):
            continue
        name = block.get('name')
        if not name:
            continue
        recorded = block.get('digest')
        out[name] = (str(recorded) if recorded
                     else provenance.algorithm_digest(block))
    return out


def _algorithm_schemas(sweep_dir):
    """``{algorithm: provenance schema version}`` for each block (0 if unstamped).

    A pre-Task-9 block could not record ``maxfev`` or the MCMC settings, so its digest
    is a claim about what was *written down*, not about what ran. Carrying the schema
    lets the profile pages distinguish "these sweeps were configured differently" from
    "one of these sweeps predates the field that would have shown it".
    """
    blocks = _provenance(sweep_dir).get('algorithms') or []
    return {b['name']: int(b.get('schema', 0))
            for b in blocks if isinstance(b, dict) and b.get('name')}


def _separable(sweep_dir):
    """Per contest: whether any algorithm pair was actually separable.

    Read from the ``contest='pair'`` head-to-head verdicts. A contest where no pair
    resolves to a winner cannot be ranked 1..N honestly — JXP's decision is that the
    pairwise verdict feeds the ranking, so the fold carries it.
    """
    path = sweep_dir / metrics.METRICS_PAIRWISE_FILE
    if not path.is_file():
        return pd.DataFrame()
    pw = pd.read_parquet(path)
    if 'contest' not in pw.columns:
        return pd.DataFrame()
    pairs = pw[pw['contest'] == 'pair']
    if pairs.empty:
        return pd.DataFrame()
    keys = [c for c in ('dataset', 'fit_method', 'stratum', 'component',
                        'ref_wave') if c in pairs.columns]
    names = set(pairs['model_a']) | set(pairs['model_b'])
    pairs = pairs.assign(_decided=pairs['verdict'].isin(names))
    return (pairs.groupby(keys, sort=False)['_decided'].any()
                 .rename('separable').reset_index())


def _coverage(ms):
    """Per-(dataset, algorithm, stratum) coverage from the closure rows.

    ``metrics`` scores only ``'ok'`` rows, so a leaderboard entry says nothing
    about *how many* spectra an algorithm actually solved — which is half the
    story when algorithms differ in what they can fit. The closure row carries
    that: ``frac_ok`` over ``n_attempted`` spectra, plus ``frac_overfit`` (the
    share of the solved ones that agree with the data *better* than its stated
    uncertainty, which on an inflated-noise dataset is most of them) and the
    noise-model-free ``rel_misfit_median_all``. Returns an empty frame if the
    sweep predates the coverage block.
    """
    cov = ms[ms['component'] == 'Rrs']
    cols = [c for c in _CLOSURE_COLS if c in cov.columns]
    if cov.empty or not cols:
        return pd.DataFrame()
    keys = [c for c in ('dataset', 'algorithm', 'fit_method', 'stratum')
            if c in cov.columns]
    return cov[keys + cols]


def _fold_sweep(sweep_id, runs_root):
    """Ref-band accuracy rows (+ win_frac + coverage + version) for one sweep.

    Uses the χ² population at all strata (the shared, like-for-like set); returns
    ``None`` if the sweep has no ``metrics_scalar`` yet.
    """
    d = runs_root / sweep_id
    mpath = d / metrics.METRICS_SCALAR_FILE
    if not mpath.is_file():
        return None
    ms = pd.read_parquet(mpath)
    acc = ms[ms['component'].isin(metrics.ACCURACY_COMPONENTS)
             & ms['ref_wave'].notna()].copy()
    if acc.empty:
        return None
    acc['sweep_id'] = sweep_id
    keep = _KEY_COLS + ['ref_match'] + [c for c in _VALUE_COLS if c in acc]
    # Carry the GLORIA CDOM-vs-a_dg caveat through the fold so the accumulated
    # leaderboard surfaces it (metrics stamps it on GLORIA a_dg rows only).
    if 'caveat' in acc.columns:
        keep = keep + ['caveat']
    out = acc[keep]

    pw_path = d / metrics.METRICS_PAIRWISE_FILE
    if pw_path.is_file():
        pw = pd.read_parquet(pw_path)
        if 'contest' in pw.columns:
            wins = pw[pw['contest'] == 'wins']
            if not wins.empty:
                # ``dataset`` MUST be a merge key: wins rows are per-dataset, so
                # without it a multi-dataset sweep row-multiplies and hands one
                # dataset's win fraction to another's rows (reproduced on a
                # two-dataset fixture: 80 rows became 160, with ('L23',
                # 'expb_pow') carrying both its own 1.0 and PANGAEA's 0.0).
                # Same defect as the one fixed in report.tables.
                on = [c for c in ('dataset', 'fit_method', 'stratum',
                                  'component', 'ref_wave', 'algorithm')
                      if c in wins.columns and c in out.columns]
                out = out.merge(wins[on + ['win_frac']], on=on, how='left')
    if 'win_frac' not in out.columns:
        out['win_frac'] = float('nan')
    cov = _coverage(ms)
    if not cov.empty:
        on = [c for c in ('dataset', 'algorithm', 'fit_method', 'stratum')
              if c in cov.columns and c in out.columns]
        out = out.merge(cov, on=on, how='left')

    # The pairwise verdicts decide whether a contest can be ranked at all
    # (JXP: "feed the leaderboard's ranking").
    sep = _separable(d)
    if sep.empty:
        out = out.assign(separable=pd.NA)
    else:
        on = [c for c in ('dataset', 'fit_method', 'stratum', 'component',
                          'ref_wave') if c in out.columns and c in sep.columns]
        out = out.merge(sep, on=on, how='left')

    stamps = _version_stamps(d)
    out['versions'] = stamps['ioptics']
    out['bing'] = stamps['bing']
    out['ocpy'] = stamps['ocpy']
    if 'algorithm' in out.columns:
        out['algo_digest'] = out['algorithm'].map(_algorithm_digests(d))
        # The schema the digest was computed under, so a cross-sweep comparison can
        # tell a configuration difference from a provenance-schema difference.
        out['prov_schema'] = out['algorithm'].map(_algorithm_schemas(d))
        out['provenance_id'] = [provenance.provenance_id(sweep_id, a)
                                for a in out['algorithm']]
    else:
        out['algo_digest'] = ''
    return out


def update(runs_root=None, *, root=None, out=None, sweep_ids=None):
    """Fold sweeps' ``metrics_scalar`` into the cross-sweep ``leaderboard.parquet``.

    Scans ``runs_root`` (default :func:`ioptics.io.runs_root`, honoring ``root``)
    for sweep dirs that carry a ``metrics_scalar.parquet`` and folds each into
    ``out`` (default the runs-root sibling ``leaderboard.parquet``). **Idempotent:**
    rows for a folded ``sweep_id`` replace any existing rows for it; sweeps not
    folded this call are preserved. Pass ``sweep_ids`` to fold a subset. Returns
    the full leaderboard DataFrame.
    """
    runs_root = Path(runs_root) if runs_root is not None else io.runs_root(root)
    out = Path(out) if out is not None else _default_out(runs_root)

    if sweep_ids is None:
        sweep_ids = sorted(p.name for p in runs_root.iterdir()
                           if (p / metrics.METRICS_SCALAR_FILE).is_file())
    folded = [f for f in (_fold_sweep(sid, runs_root) for sid in sweep_ids)
              if f is not None]

    existing = pd.read_parquet(out) if out.is_file() else None
    frames = []
    if existing is not None:
        done = {f['sweep_id'].iloc[0] for f in folded}
        frames.append(existing[~existing['sweep_id'].isin(done)])
    frames.extend(folded)
    board = (pd.concat(frames, ignore_index=True) if frames
             else pd.DataFrame(columns=_KEY_COLS))
    out.parent.mkdir(parents=True, exist_ok=True)
    board.to_parquet(out, index=False)
    return board


#: What counts as one contest. ``fit_method`` **must** be here: it became a folded
#: key so MCMC results could reach the board at all, and without it a χ² row and an
#: MCMC row of the same algorithm land in one ranking — comparing win fractions drawn
#: from different pools, and publishing the same algorithm at rank 1 and rank 2.
_CONTEST = ['dataset', 'component', 'ref_wave', 'stratum', 'fit_method']


def ranked(board, *, stratum=None):
    """Add a per-contest ``rank`` (1 = best) within ``(dataset, component, ref_wave, stratum)``.

    Ranking order is wins → ``|bias|`` → MAE (design Q23). ``stratum`` filters to
    one bin (default ``None`` keeps **all** strata, each ranked independently).
    Returns a sorted copy.
    """
    df = board if stratum is None else board[board['stratum'] == stratum]
    # An empty or un-scored board is a legitimate state (stage 3 before stage 2, a
    # fresh machine), not a crash: the sort keys simply do not exist yet.
    missing = [c for c in _CONTEST + _RANK_BY if c not in df.columns]
    if df.empty or missing:
        out = df.copy()
        out['rank'] = pd.Series(pd.NA, index=out.index, dtype='Int64')
        out['ranking'] = 'not scored'
        return out
    df = df.sort_values(_CONTEST + _RANK_BY,
                        ascending=[True] * len(_CONTEST) + _RANK_ASC) \
           .reset_index(drop=True)
    df['rank'] = df.groupby(_CONTEST).cumcount() + 1
    # A contest with no finite metric has no ranking. Previously every row was
    # ranked by position, so 144 of the 160 published rows carried a rank of 1-4
    # with nothing measured behind them — a reader saw a standing where no
    # comparison had happened.
    scored = [c for c in _RANK_BY if c in df.columns]
    if scored:
        measured = df[scored].notna().any(axis=1)
        df.loc[~measured, 'rank'] = pd.NA
        # A contest with a single measured competitor is not a standing either —
        # "rank 1" over a one-horse race reads as a win.
        n_measured = measured.groupby([df[c] for c in _CONTEST]).transform('sum')
        df.loc[measured & (n_measured < 2), 'rank'] = pd.NA
        # And a contest whose pairwise verdicts separate nobody is not a standing:
        # printing 1..N there asserts an order the data do not support (JXP's
        # answer: the head-to-head verdict feeds the ranking).
        if 'separable' in df.columns:
            tied = df['separable'].eq(False)
            df.loc[tied, 'rank'] = pd.NA
            # A contest with no pairwise verdict (an older sweep, or a fit method
            # whose pairs were never computed) is still ordered, but the ordering
            # has no head-to-head support and must not pretend otherwise.
            unsupported = df['separable'].isna()
        else:
            # No verdicts at all — every rank here is unsupported, and saying so is
            # the point of the rule.
            unsupported = pd.Series(True, index=df.index)
        df['rank'] = df['rank'].astype('Int64')
        df['ranking'] = np.select(
            [df['rank'].notna() & ~unsupported,
             df['rank'].notna() & unsupported,
             measured & (n_measured < 2),
             df[scored].notna().any(axis=1)],
            ['ranked', 'ranked (no head-to-head)', 'sole competitor',
             'indistinguishable'],
            default='not scored')
    return df


def render(board=None, *, runs_root=None, root=None, out=None, fmt='rst',
           stratum=None, headline=True, drop_unscored=True):
    """Render the ranked leaderboard as an RST (``fmt='rst'``) or Markdown table.

    ``board`` may be a DataFrame; if ``None`` the persisted ``leaderboard.parquet``
    is read (from ``out`` or the ``runs_root`` sibling default). ``stratum``
    defaults to ``None`` (**all** strata, each ranked independently).

    ``headline=True`` renders the **landing-page** view: the ``stratum='all'``
    contests only, with the narrow set of columns a reader scans, because the full
    grid was 2 400 lines of ``list-table`` on the landing page and nobody reads
    that. Pass ``headline=False`` for the complete drill-down table.
    ``drop_unscored`` hides rows with nothing measured behind them (144 of the 160
    published rows were all-NaN).
    """
    if board is None:
        runs_root = Path(runs_root) if runs_root is not None \
            else io.runs_root(root)
        out = Path(out) if out is not None else _default_out(runs_root)
        board = pd.read_parquet(out)
    df = ranked(board, stratum=stratum)
    if 'caveat' in df.columns:
        # rows from sweeps folded before caveat-carrying (or non-GLORIA) → ''
        df['caveat'] = df['caveat'].fillna('')

    scored = [c for c in _RANK_BY if c in df.columns]
    if drop_unscored and scored:
        df = df[df[scored].notna().any(axis=1)]
    if headline:
        if 'stratum' in df.columns:
            df = df[df['stratum'] == 'all']
        cols = HEADLINE_COLS
    else:
        cols = FULL_COLS
    cols = [c for c in cols if c in df.columns]

    def _cell(v):
        if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA:
            return '—'
        if isinstance(v, float):
            return f'{v:.3g}'
        return str(v)

    header = cols
    rows = [[_cell(r[c]) for c in cols] for _, r in df.iterrows()]
    if fmt == 'md':
        lines = ['| ' + ' | '.join(header) + ' |',
                 '| ' + ' | '.join('---' for _ in header) + ' |']
        lines += ['| ' + ' | '.join(row) + ' |' for row in rows]
        return '\n'.join(lines) + '\n'
    # default: RST list-table (renders under sphinx -W)
    title = 'Leaderboard' if headline else 'Leaderboard (full grid)'
    lines = [f'.. list-table:: {title}',
             '   :header-rows: 1',
             '   :widths: auto', '']
    for row in [header] + rows:
        lines.append('   * - ' + row[0])
        lines.extend('     - ' + cell for cell in row[1:])
    return '\n'.join(lines) + '\n'


def sweep_cards(runs_root=None, *, root=None, board=None, out=None, fmt='rst',
                docs_root=None):
    """One summary card per folded sweep: date, datasets, algorithms, n, verdict.

    The landing page linked its sweeps through a bare ``:glob: */*`` toctree, so a
    reader saw undescribed links and had to open each page to learn what it was.
    Each card states what the sweep compared, on how much data, and — from the
    pairwise verdicts — whether anything separated.
    """
    runs_root = Path(runs_root) if runs_root is not None else io.runs_root(root)
    if board is None:
        out = Path(out) if out is not None else _default_out(runs_root)
        board = pd.read_parquet(out) if out.is_file() else pd.DataFrame()
    if board.empty or 'sweep_id' not in board.columns:
        return ''
    lines = []
    for sweep_id, g in board.groupby('sweep_id', sort=True):
        created = (_provenance(runs_root / sweep_id).get('created') or '')[:10]
        datasets = ', '.join(sorted(g['dataset'].dropna().unique()))
        algos = sorted(g['algorithm'].dropna().unique())
        scored = [c for c in _RANK_BY if c in g.columns]
        measured = g[g[scored].notna().any(axis=1)] if scored else g
        n = int(measured['n'].max()) if 'n' in measured.columns \
            and measured['n'].notna().any() else 0
        if 'separable' in g.columns and g['separable'].notna().any():
            verdict = ('at least one pair separated'
                       if bool(g['separable'].fillna(False).any())
                       else 'no pair separated — see the head-to-head table')
        else:
            verdict = 'no pairwise verdict recorded'
        lines += [f'* **{sweep_id}**' + (f' — {created}' if created else ''),
                  f'  {datasets or "?"}; {len(algos)} algorithm(s): '
                  f'{", ".join(f"``{a}``" for a in algos)}.',
                  f'  Up to {n} scored spectra per contest; {verdict}.']
        # Only link a page that exists: ``update`` folds every sweep dir with
        # metrics, while pages are built per sweep on demand, so a folded-but-
        # unbuilt sweep would leave a dangling ``:doc:`` (a Sphinx warning and a
        # broken link).
        page = None
        if docs_root is not None:
            cand = Path(docs_root) / 'reports' / sweep_id / 'cross_algorithm.rst'
            page = f'/reports/{sweep_id}/cross_algorithm' if cand.is_file() else None
        elif docs_root is None:
            page = f'/reports/{sweep_id}/cross_algorithm'
        lines += ([f'  See :doc:`{page}`.'] if page
                  else ['  No report page has been built for this sweep yet.'])
        lines += ['']
    if fmt == 'md':
        return '\n'.join(lines).replace('``', '`') + '\n'
    return '\n'.join(lines) + '\n'

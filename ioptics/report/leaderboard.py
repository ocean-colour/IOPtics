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

Consumes only persisted artifacts (no re-fitting, no BING/ocpy).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from ioptics import io, metrics

LEADERBOARD_FILE = 'leaderboard.parquet'

# Columns folded from each sweep's ref-band accuracy rows (+ win_frac).
_VALUE_COLS = ['n', 'bias', 'abs_bias', 'mae', 'rms_log',
               'coverage68', 'coverage95']
_KEY_COLS = ['sweep_id', 'dataset', 'algorithm', 'stratum', 'component',
             'ref_wave']
# Sort within each (dataset, component, ref_wave, stratum) contest.
_RANK_BY = ['win_frac', 'abs_bias', 'mae']
_RANK_ASC = [False, True, True]


def _default_out(runs_root):
    """Leaderboard path: sibling of the runs root (``…/IOPtics/leaderboard.parquet``)."""
    return runs_root.parent / LEADERBOARD_FILE


def _version_stamp(sweep_dir):
    """Compact ``ioptics`` version@commit from a sweep's ``provenance.yaml`` (or '')."""
    path = sweep_dir / 'provenance.yaml'
    if not path.is_file():
        return ''
    try:
        rec = yaml.safe_load(path.read_text())
        iop = rec.get('versions', {}).get('ioptics', {})
        commit = (iop.get('commit') or '')[:8]
        ver = iop.get('version') or ''
        return f'{ver}@{commit}' if commit else ver
    except Exception:
        return ''


def _fold_sweep(sweep_id, runs_root):
    """Ref-band accuracy rows (+ win_frac + version) for one sweep, or ``None``.

    Uses the χ² population at all strata (the shared, like-for-like set); returns
    ``None`` if the sweep has no ``metrics_scalar`` yet.
    """
    d = runs_root / sweep_id
    mpath = d / metrics.METRICS_SCALAR_FILE
    if not mpath.is_file():
        return None
    ms = pd.read_parquet(mpath)
    acc = ms[(ms['fit_method'] == 'chisq')
             & ms['component'].isin(metrics.ACCURACY_COMPONENTS)
             & ms['ref_wave'].notna()].copy()
    if acc.empty:
        return None
    acc['sweep_id'] = sweep_id
    keep = _KEY_COLS + ['ref_match'] + [c for c in _VALUE_COLS if c in acc]
    out = acc[keep]

    pw_path = d / metrics.METRICS_PAIRWISE_FILE
    if pw_path.is_file():
        pw = pd.read_parquet(pw_path)
        if 'contest' in pw.columns:
            wins = pw[(pw['contest'] == 'wins') & (pw['fit_method'] == 'chisq')]
            if not wins.empty:
                out = out.merge(
                    wins[['stratum', 'component', 'ref_wave', 'algorithm',
                          'win_frac']],
                    on=['stratum', 'component', 'ref_wave', 'algorithm'],
                    how='left')
    if 'win_frac' not in out.columns:
        out['win_frac'] = float('nan')
    out['versions'] = _version_stamp(d)
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


_CONTEST = ['dataset', 'component', 'ref_wave', 'stratum']


def ranked(board, *, stratum=None):
    """Add a per-contest ``rank`` (1 = best) within ``(dataset, component, ref_wave, stratum)``.

    Ranking order is wins → ``|bias|`` → MAE (design Q23). ``stratum`` filters to
    one bin (default ``None`` keeps **all** strata, each ranked independently).
    Returns a sorted copy.
    """
    df = board if stratum is None else board[board['stratum'] == stratum]
    df = df.sort_values(_CONTEST + _RANK_BY,
                        ascending=[True] * len(_CONTEST) + _RANK_ASC) \
           .reset_index(drop=True)
    df['rank'] = df.groupby(_CONTEST).cumcount() + 1
    return df


def render(board=None, *, runs_root=None, root=None, out=None, fmt='rst',
           stratum=None):
    """Render the ranked leaderboard as an RST (``fmt='rst'``) or Markdown table.

    ``board`` may be a DataFrame; if ``None`` the persisted ``leaderboard.parquet``
    is read (from ``out`` or the ``runs_root`` sibling default). ``stratum``
    defaults to ``None`` (**all** strata, each ranked independently). Returns the
    table as a string, ready to drop into the site landing page.
    """
    if board is None:
        runs_root = Path(runs_root) if runs_root is not None \
            else io.runs_root(root)
        out = Path(out) if out is not None else _default_out(runs_root)
        board = pd.read_parquet(out)
    df = ranked(board, stratum=stratum)

    cols = ['dataset', 'component', 'ref_wave', 'stratum', 'rank', 'algorithm',
            'win_frac', 'bias', 'mae', 'coverage68', 'coverage95']
    cols = [c for c in cols if c in df.columns]

    def _cell(v):
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
    lines = ['.. list-table:: Leaderboard',
             '   :header-rows: 1', '']
    for i, row in enumerate([header] + rows):
        bullet = '   * - ' + row[0]
        lines.append(bullet)
        lines.extend('     - ' + cell for cell in row[1:])
    return '\n'.join(lines) + '\n'

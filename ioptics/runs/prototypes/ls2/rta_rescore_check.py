"""Does re-scoring RT-A reproduce its published numbers? (ls2 task 9b)

RT-A's page (``docs/source/reports/rt_tests_A_l23_v1/``) was built on
2026-09-17 by the metrics layer of the time.  Task 9b re-scores the same
results with today's layer, after ``rta_add_anw.py`` has added ``a_nw``, and
this script checks that every number already published is reproduced.  It
rebuilds the RT-A page into a scratch docs root (so the committed page is
untouched), then compares each published CSV with its rebuilt twin, cell by
cell, on the columns and rows they share.

What is expected to differ, and is reported separately rather than counted as
a mismatch:

- the ``frac_qc_fail`` family, whose definition changed in ls2 task 6 (Q32);
- rows or columns that exist only in the rebuilt table (``a_nw``, ``pool``):
  additions, not changes.

Anything else that differs is a finding.

Usage, from the repository root::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \\
        ioptics/runs/prototypes/ls2/rta_rescore_check.py [--out DIR]
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

SWEEP_ID = 'rt_tests_A_l23_v1'
REPO = Path(__file__).resolve().parents[4]
PUBLISHED = REPO / 'docs' / 'source' / 'reports' / SWEEP_ID
#: Columns whose definition changed on purpose since RT-A was published.
CHANGED_BY_DESIGN = ('frac_qc_fail', 'frac_not_ok')
#: Relative tolerance: the CSVs are rounded to 4 significant decimals.
RTOL, ATOL = 1e-3, 1.5e-4


#: The columns that identify a row, in whichever of them a table has.
KEY_COLUMNS = ('dataset', 'rung', 'algorithm', 'component', 'ref_wave',
               'model_a', 'model_b', 'stratum')


def _keys(df):
    """The identifying columns of a published table."""
    keys = [c for c in KEY_COLUMNS if c in df.columns]
    if not keys or df.duplicated(keys).any():
        raise ValueError(f'rows are not unique on {keys}')
    return keys


def compare(pub, new):
    """Cell-level comparison of two versions of one table.

    Returns ``(n_cells, mismatches, by_design, only_new_rows, only_new_cols)``.
    ``mismatches`` is a DataFrame of ``key…, column, published, rebuilt``.
    """
    keys = _keys(pub)
    for k in keys:
        pub[k] = pub[k].astype(str)
        new[k] = new[k].astype(str)
    if new.duplicated(keys).any():
        raise ValueError(f'rebuilt rows are not unique on {keys}')
    p, n = pub.set_index(keys), new.set_index(keys)
    rows = p.index.intersection(n.index)
    cols = [c for c in p.columns if c in n.columns]
    out, by_design, ncell = [], [], 0
    for c in cols:
        a, b = p.loc[rows, c], n.loc[rows, c]
        num_a = pd.to_numeric(a, errors='coerce')
        num_b = pd.to_numeric(b, errors='coerce')
        numeric = (num_a.notna() | num_b.notna()).to_numpy()
        same = np.zeros(len(rows), dtype=bool)
        same[numeric] = np.isclose(num_a.to_numpy()[numeric],
                                   num_b.to_numpy()[numeric],
                                   rtol=RTOL, atol=ATOL, equal_nan=True)
        sa = a.fillna('').astype(str).to_numpy()
        sb = b.fillna('').astype(str).to_numpy()
        same[~numeric] = sa[~numeric] == sb[~numeric]
        ncell += len(rows)
        for idx in rows[~same]:
            rec = dict(zip(keys, idx if isinstance(idx, tuple) else (idx,)))
            rec.update(column=c, published=a.loc[idx], rebuilt=b.loc[idx])
            (by_design if c in CHANGED_BY_DESIGN else out).append(rec)
    missing = p.index.difference(n.index)
    for idx in missing:
        rec = dict(zip(keys, idx if isinstance(idx, tuple) else (idx,)))
        rec.update(column='<row>', published='present', rebuilt='MISSING')
        out.append(rec)
    return (ncell, pd.DataFrame(out), pd.DataFrame(by_design),
            len(n.index.difference(p.index)),
            [c for c in n.columns if c not in p.columns])


def main(out=None):
    """Rebuild into ``out`` (default: a temp dir) and report per CSV."""
    from ioptics.algorithms import registry
    from ioptics.report import rt_ladder

    registry.register_rt_variants()
    out = Path(out) if out else Path(tempfile.mkdtemp(prefix='rta_rescore_'))
    page = rt_ladder.build(SWEEP_ID, docs_root=out, pair=registry.RT_DBIC_PAIR)
    rebuilt = page.parent
    total_bad = 0
    report = {}
    for f in sorted(PUBLISHED.glob('*.csv')):
        twin = rebuilt / f.name
        if not twin.is_file():
            print(f'{f.name:34s} NOT REBUILT')
            total_bad += 1
            continue
        n, bad, design, new_rows, new_cols = compare(pd.read_csv(f),
                                                     pd.read_csv(twin))
        total_bad += len(bad)
        report[f.name] = (bad, design)
        extra = (f'; +{new_rows} new rows' if new_rows else '') + (
            f'; new cols {new_cols}' if new_cols else '')
        print(f'{f.name:34s} {n:6d} cells, {len(bad):3d} differ, '
              f'{len(design):3d} by design{extra}')
    for name, (bad, design) in report.items():
        if len(bad):
            print(f'\n--- {name}: differences ---')
            print(bad.to_string(index=False, max_rows=40))
        if len(design):
            print(f'\n--- {name}: changed by design ({", ".join(CHANGED_BY_DESIGN)}) ---')
            print(design.to_string(index=False, max_rows=20))
    print(f'\nrebuilt page: {page}')
    print('ALL PUBLISHED NUMBERS REPRODUCED' if total_bad == 0 else
          f'{total_bad} published cells NOT reproduced')
    return report


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--out', default=None, help='scratch docs root')
    main(p.parse_args().out)

"""Give the RT-A sweep the ``a_nw`` rows BING has emitted only since ls2 task 6.

RT-A (``rt_tests_A_l23_v1``, BING on L23 X=4) was run before
:func:`ioptics.evaluate` assembled ``a_nw`` for BING, so its spectral table has
``a``, ``a_ph``, ``a_dg``, ``bb``, ``bb_p``, ``Rrs_model`` and ``Rrs_obs`` but
no ``a_nw``.  LS2 returns ``a_nw`` and not its split, so ``a_nw`` is the one
absorption product the LS2 ladder page can put beside BING component for
component (ls2 task 9b).  This script derives those rows, without refitting
anything:

- **value** = ``a_dg + a_ph`` from the same ``(dataset, obs_id, algorithm,
  fit_method, wavelength)`` row.  Both are the fit's point-estimate curves,
  so this is exactly the central value ``evaluate`` writes today, where
  ``a_nw`` is the point-estimate ``a_dg + a_ph``.
- **lo68 … hi95** are **NaN**.  A sum of two marginal intervals is not the
  interval of the sum: ``a_dg`` and ``a_ph`` are correlated through the fit
  (they trade off against each other in the blue), so neither adding the
  bounds nor adding them in quadrature is right.  ``evaluate`` gets the true
  interval by summing on the same posterior draws, and that needs the chains,
  which were not copied (prompt 9a).  So ``a_nw`` gets no coverage score on
  RT-A, and the metrics layer treats NaN bounds as "no interval", as it does
  for a direct algorithm.
- **truth** = L23 ``anw`` for that scenario and wavelength, read from the
  dataset at the sweep's own ``X``/``Y`` (``provenance.yaml``).  This is the
  truth ``ioptics.datasets.L23Adapter`` attaches to ``a_nw`` today.  The RT-A
  grid (400–750 nm, 5 nm) is a subset of L23's native grid, so this is a
  lookup with no interpolation (``truth_interp`` = False).  A wavelength not on
  the grid raises.
- ``nan_reason`` = ``''`` if the table has that column.  RT-A predates it
  (ls2 Q24), and the metrics layer fills it in on read, so the column is not
  added.

Files.  ``results_spectral.parquet`` is rewritten in place (through a
temporary file and an atomic rename), after the pristine table is kept as
``results_spectral.orig.parquet``.  The derivation is recorded in
``provenance.yaml`` under a new top-level ``derived`` key, **appended** to the
file, so the original text, the algorithm blocks and their digests, is left
byte for byte.  The script is idempotent: if ``a_nw`` rows are already present
it does nothing.

Usage, from the repository root (after ``rta_fetch.py``)::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \\
        ioptics/runs/prototypes/ls2/rta_add_anw.py

Then re-score::

    metrics.compute('rt_tests_A_l23_v1', dbic_pair=registry.RT_DBIC_PAIR)
"""

from __future__ import annotations

import datetime as _dt
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

SWEEP_ID = 'rt_tests_A_l23_v1'
ORIG_FILE = 'results_spectral.orig.parquet'
#: The row key ``a_dg`` and ``a_ph`` are paired on.
KEYS = ['dataset', 'obs_id', 'algorithm', 'fit_method', 'wavelength']
BOUNDS = ['lo68', 'hi68', 'lo95', 'hi95']


def l23_anw_truth(X, Y=0, ds=None):
    """A truth function: ``rows -> L23 anw`` at each row's scenario and wavelength.

    ``ds`` is a loaded L23 dataset; by default it is read with
    ``ocpy.hydrolight.loisel23.load_ds(X, Y)``.  The returned callable takes
    a DataFrame with ``dataset``, ``obs_id`` and ``wavelength`` columns and
    returns a float array.  It raises if a row is not L23, or if a wavelength is
    not on the native grid.
    """
    if ds is None:
        from ocpy.hydrolight import loisel23
        ds = loisel23.load_ds(X, Y)
    grid = np.asarray(ds['Lambda'].values, dtype=float)
    anw = np.asarray(ds['anw'].values, dtype=float)

    def truth(rows):
        if set(rows['dataset'].unique()) - {'L23'}:
            raise ValueError('l23_anw_truth: rows from a dataset other than L23')
        wave = rows['wavelength'].to_numpy(dtype=float)
        iw = np.clip(np.searchsorted(grid, wave), 0, grid.size - 1)
        off = ~np.isclose(grid[iw], wave, rtol=0, atol=1e-3)
        if off.any():
            raise ValueError(f'l23_anw_truth: {np.unique(wave[off])} nm not on '
                             f'the L23 grid')
        return anw[rows['obs_id'].to_numpy(dtype=int), iw]

    return truth


def derive_anw_rows(parts, truth_fn, columns):
    """The ``a_nw`` rows for a spectral frame holding ``a_dg`` and ``a_ph``.

    ``parts`` is the ``a_dg``/``a_ph`` subset of a results table (other
    components are ignored), ``truth_fn`` maps rows to their ``a_nw`` truth
    (:func:`l23_anw_truth`), and ``columns`` is the output column order (the
    table's).  Every ``a_dg`` row must have exactly one ``a_ph`` partner and
    vice versa; anything else raises rather than dropping rows silently.
    """
    adg = parts[parts['component'] == 'a_dg'].set_index(KEYS)
    aph = parts[parts['component'] == 'a_ph'].set_index(KEYS)
    for name, df in (('a_dg', adg), ('a_ph', aph)):
        if not df.index.is_unique:
            raise ValueError(f'{name} rows are not unique on {KEYS}')
    if len(adg) != len(aph) or not adg.index.isin(aph.index).all():
        raise ValueError(f'a_dg ({len(adg)}) and a_ph ({len(aph)}) rows do not '
                         f'pair one-for-one on {KEYS}')
    rows = adg.join(aph[['value']], rsuffix='_ph').reset_index()
    rows['value'] = rows['value'] + rows.pop('value_ph')
    rows['component'] = 'a_nw'
    for b in BOUNDS:
        rows[b] = np.nan
    rows['truth'] = np.asarray(truth_fn(rows), dtype=float)
    rows['truth_interp'] = False
    rows['unit'] = '1/m'
    if 'nan_reason' in columns:
        rows['nan_reason'] = ''
    return rows[list(columns)]


def _sha256(path, *, chunk=1 << 22):
    """Hex SHA-256 of a file (as ``rta_fetch.sha256``; kept local so the
    module imports on its own)."""
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(chunk), b''):
            h.update(block)
    return h.hexdigest()


def _git_head():
    """The repository's short HEAD (read-only), or ``'unknown'``."""
    try:
        out = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                             cwd=Path(__file__).resolve().parent,
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return 'unknown'


def _record_provenance(path, block):
    """Append ``derived: {a_nw: block}`` to ``provenance.yaml``, once.

    Appending leaves the original text untouched, algorithm digests included.
    If a ``derived`` key already exists the file is left alone and ``False``
    is returned: a second derivation is a decision for a person, not
    something to merge automatically.
    """
    import yaml

    text = Path(path).read_text(encoding='utf-8')
    if 'derived' in (yaml.safe_load(text) or {}):
        return False
    add = yaml.safe_dump({'derived': {'a_nw': block}}, sort_keys=False,
                         default_flow_style=False, allow_unicode=True)
    sep = '' if text.endswith('\n') else '\n'
    Path(path).write_text(text + sep + add, encoding='utf-8')
    return True


def add_anw(sweep_id=SWEEP_ID, *, root=None, truth_fn=None):
    """Add the derived ``a_nw`` rows to a sweep's spectral table, in place.

    ``truth_fn`` defaults to :func:`l23_anw_truth` at the sweep's own L23
    ``X``/``Y`` (from ``provenance.yaml``'s ``dataset_opts``, defaulting to
    the adapter's X=1, Y=0).  Returns a summary dict: ``added`` (rows; 0 for
    the no-op), ``total`` and ``orig`` (the kept pristine table's path).
    """
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    import yaml

    from ioptics import io

    d = io.sweep_dir(sweep_id, root=root)
    spath, orig = d / io.SPECTRAL_FILE, d / ORIG_FILE
    ppath = d / 'provenance.yaml'

    comp = pq.read_table(spath, columns=['component'])['component']
    if pc.any(pc.equal(comp, 'a_nw')).as_py():
        print(f'[{sweep_id}] a_nw already present: nothing to do')
        return {'added': 0, 'total': len(comp), 'orig': orig}

    prov = yaml.safe_load(ppath.read_text(encoding='utf-8')) if ppath.is_file() else {}
    opts = ((prov or {}).get('dataset_opts') or {}).get('L23') or {}
    X, Y = int(opts.get('X', 1)), int(opts.get('Y', 0))
    if truth_fn is None:
        truth_fn = l23_anw_truth(X, Y)

    table = pq.read_table(spath)
    mask = pc.is_in(table['component'], value_set=pa.array(['a_dg', 'a_ph']))
    parts = table.filter(mask).to_pandas()
    rows = derive_anw_rows(parts, truth_fn, table.column_names)
    new = pa.Table.from_pandas(rows, schema=table.schema, preserve_index=False)

    if not orig.is_file():                 # a crash after this step keeps it
        shutil.copy2(spath, orig)
    out = pa.concat_tables([table, new])
    tmp = spath.with_suffix('.parquet.tmp')
    pq.write_table(out, tmp)
    os.replace(tmp, spath)

    block = {
        'task': 'ls2 9b',
        'script': 'ioptics/runs/prototypes/ls2/rta_add_anw.py',
        'ioptics_commit': _git_head(),
        'date': _dt.date.today().isoformat(),
        'value': 'a_dg + a_ph, point estimates, paired on '
                 '(dataset, obs_id, algorithm, fit_method, wavelength)',
        'bounds': 'NaN: a sum of two marginal intervals is not the interval '
                  'of the sum, and the chains that would give it were not copied',
        'truth': f'L23 anw at X={X}, Y={Y}, native grid (no interpolation)',
        'rows_added': int(new.num_rows),
        'original_table': f'{ORIG_FILE} (sha256 {_sha256(orig)})',
    }
    recorded = _record_provenance(ppath, block) if ppath.is_file() else False
    print(f'[{sweep_id}] added {new.num_rows:,} a_nw rows '
          f'({out.num_rows:,} total); pristine table kept as {ORIG_FILE}; '
          f'provenance {"updated" if recorded else "NOT updated"}')
    return {'added': int(new.num_rows), 'total': int(out.num_rows), 'orig': orig}


if __name__ == '__main__':
    add_anw()

"""Bring the RT-A comparator sweep onto this machine and verify it (ls2 task 9b).

The LS2 ladder on L23 X=4 is quoted against MCMC BING on the same spectra
(ls2 Q23), and that population is the RT-A sweep ``rt_tests_A_l23_v1``, which
was run on JXP's workstation.  Prompt 9a staged exactly three of its files,
plus a ``MANIFEST.txt``, on the ``RoB`` Shared Drive under
``RT/rt_tests_A_l23_v1/``:

- ``results_scalar.parquet`` and ``results_spectral.parquet`` -- the results;
- ``provenance.yaml`` -- config, versions and algorithm digests.

No chains, metrics or figures: the metrics are regenerated here (RT-A was
scored before ``a_nw`` and ``pool`` existed), and nothing downstream needs a
chain.

This script copies those files into ``$OS_COLOR/IOPtics/runs/<sweep_id>/``
and checks every byte size, SHA-256 and parquet row count against the
manifest, refusing on any mismatch.  It only ever **reads** from the Drive:
``rclone copy`` runs with the Drive as its source.

Fetching goes through ``rclone`` and the laptop's ``RoB`` remote, which points at
the same Shared Drive as the workstation's.  The Drive for Desktop mount does
not show the ``RoB`` Shared Drive on this laptop (checked 2026-10-04), so
``--from`` can point at a mounted folder instead if it ever appears there.

Usage, from the repository root::

    PYTHONPATH=. /Users/xavier/miniforge3/envs/ocean14/bin/python \\
        ioptics/runs/prototypes/ls2/rta_fetch.py [--verify-only] [--from SRC]

The verification is only meaningful on the files as fetched.
``rta_add_anw.py`` then rewrites ``results_spectral.parquet`` and appends to
``provenance.yaml``, so after that step those two no longer match the
manifest, by design (the pristine spectral table is kept as
``results_spectral.orig.parquet``, which still does).
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

SWEEP_ID = 'rt_tests_A_l23_v1'
MANIFEST_FILE = 'MANIFEST.txt'
#: The rclone source: the ``RoB`` Shared Drive (``team_drive`` 0AAeT_zUSejhNUk9PVA).
DRIVE_SOURCE = 'RoB:RT/rt_tests_A_l23_v1/'
#: What 9a staged, and so what 9b copies; anything else in the folder is ignored.
FILES = ('results_scalar.parquet', 'results_spectral.parquet',
         'provenance.yaml')


def read_manifest(path):
    """Parse a 9a ``MANIFEST.txt`` into ``{file: {'bytes', 'sha256', 'rows'}}``.

    The file table is the block of whitespace-separated lines after the
    ``file  bytes  sha256  rows`` header; ``rows`` is ``None`` where the
    manifest gives ``-`` (``provenance.yaml``).
    """
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    try:
        start = next(i for i, ln in enumerate(lines)
                     if ln.split()[:4] == ['file', 'bytes', 'sha256', 'rows'])
    except StopIteration:
        raise ValueError(f'{path}: no "file bytes sha256 rows" table') from None
    out = {}
    for ln in lines[start + 1:]:
        parts = ln.split()
        if not parts:
            continue
        if len(parts) != 4:
            raise ValueError(f'{path}: malformed manifest line {ln!r}')
        name, nbytes, sha, rows = parts
        out[name] = {'bytes': int(nbytes), 'sha256': sha.lower(),
                     'rows': None if rows == '-' else int(rows)}
    if not out:
        raise ValueError(f'{path}: the manifest lists no files')
    return out


def sha256(path, *, chunk=1 << 22):
    """Hex SHA-256 of a file, read in 4 MiB chunks."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(chunk), b''):
            h.update(block)
    return h.hexdigest()


def parquet_rows(path):
    """Row count from a parquet footer, without reading the data."""
    import pyarrow.parquet as pq
    return pq.ParquetFile(path).metadata.num_rows


def verify_manifest(directory, manifest=None, *, files=FILES):
    """Check ``files`` in ``directory`` against the manifest; raise on any mismatch.

    ``manifest`` is a parsed manifest (:func:`read_manifest`) or ``None`` to
    read ``directory/MANIFEST.txt``.  Every listed file must be present and
    match in size, SHA-256 and (for a parquet) row count.  All mismatches are
    collected and reported together.

    Returns
    -------
    dict
        ``{file: {'bytes', 'sha256', 'rows'}}`` as measured, when all match.

    Raises
    ------
    ValueError
        Naming every file that is missing or differs, and how.
    """
    directory = Path(directory)
    if manifest is None:
        manifest = read_manifest(directory / MANIFEST_FILE)
    problems, measured = [], {}
    for name in files:
        want = manifest.get(name)
        if want is None:
            problems.append(f'{name}: not in the manifest')
            continue
        path = directory / name
        if not path.is_file():
            problems.append(f'{name}: missing')
            continue
        got = {'bytes': path.stat().st_size, 'sha256': sha256(path),
               'rows': parquet_rows(path) if name.endswith('.parquet') else None}
        for key in ('bytes', 'sha256', 'rows'):
            if want[key] is not None and got[key] != want[key]:
                problems.append(f'{name}: {key} {got[key]} != manifest {want[key]}')
        measured[name] = got
    if problems:
        raise ValueError('RT-A files do not match MANIFEST.txt:\n  '
                         + '\n  '.join(problems))
    return measured


def fetch(dest=None, *, source=DRIVE_SOURCE, root=None):
    """Copy the staged RT-A files to ``dest`` and verify them; return ``dest``.

    ``dest`` defaults to ``<runs_root>/rt_tests_A_l23_v1``.  ``source`` is an
    rclone path (``remote:folder/``) or a local directory, such as a Drive
    for Desktop mount.  Only the manifest and :data:`FILES` are copied, and the
    source is never written to.
    """
    from ioptics import io

    dest = Path(dest) if dest is not None else io.sweep_dir(SWEEP_ID, root=root)
    dest.mkdir(parents=True, exist_ok=True)
    names = (MANIFEST_FILE,) + FILES
    if Path(source).is_dir():
        for name in names:
            shutil.copy2(Path(source) / name, dest / name)
    else:
        cmd = ['rclone', 'copy', source, str(dest)]
        for name in names:
            cmd += ['--include', name]
        subprocess.run(cmd, check=True)
    measured = verify_manifest(dest)
    for name, got in measured.items():
        rows = '' if got['rows'] is None else f', {got["rows"]:,} rows'
        print(f'  ok  {name}: {got["bytes"]:,} bytes{rows}, '
              f'sha256 {got["sha256"][:12]}…')
    return dest


def _cli(argv=None):
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--verify-only', action='store_true',
                   help='check the files already on disk; copy nothing')
    p.add_argument('--from', dest='source', default=DRIVE_SOURCE,
                   help=f'rclone path or local directory (default {DRIVE_SOURCE})')
    a = p.parse_args(argv)
    if a.verify_only:
        from ioptics import io
        d = io.sweep_dir(SWEEP_ID)
        verify_manifest(d)
        print(f'{d}: all files match {MANIFEST_FILE}')
    else:
        print(f'fetched and verified: {fetch(source=a.source)}')


if __name__ == '__main__':
    _cli()

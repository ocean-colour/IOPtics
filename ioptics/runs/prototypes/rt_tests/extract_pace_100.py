"""One-time extraction of 100 real PACE OCI spectra for the ``PACE`` dataset.

Builds the single artifact that :class:`ioptics.datasets.PACEAdapter` reads, so
IOPtics can fit real satellite spectra without depending on the ``pab`` package
(PAB is not pip-installed, and IOPtics' data layer imports only ocpy).

Provenance
----------
The source is the **PAB run1k fit archive** — the 274 per-pixel BING
``ExpBPow`` MCMC fits under ``<PAB_RUN>/fit_chains/*.npz`` (route (a) of
``claude_prompts/rt_tests.md`` Q22, chosen by JXP). Each NPZ carries the real
V3_2 L2 ``Rrs`` of one PACE OCI pixel matched to an Argo BGC profile, together
with the granule's own per-pixel ``Rrs_unc**2`` (``varRrs``; PAB already
applied its 2%-of-Rrs floor where the granule's uncertainty was bad), on the
136-band 400-699 nm PACE grid with the 588-613 nm OCI gap. That window is
final for IOPtics (Q24/Q35: 400-700 nm, no re-extraction of the 700-719 nm
bands). Negative ``Rrs`` bands are **kept** — Q24 explicitly declines that
screen.

Each pixel's place and time come from the run's SQLite catalogue
``<PAB_RUN>/pab.db``. The NPZ file name encodes the join keys::

    {wmo}_{cycle}_{granule_basename}_{ix}_{iy}_ExpBPow.npz

so ``(wmo, cycle)`` identifies the Argo profile, the granule basename *is*
``granules.granule_id``, and ``(matchup_id, ix, iy)`` identifies the pixel row
that carries its geolocation. The observation time is the granule time, from
which ``robust.solar.solar_zenith`` gives the per-pixel solar zenith angle
(Q17: compute ``theta_s`` per record for the real datasets; Q37: viewing
geometry is taken as nadir, ``theta_v = dphi = 0``, since neither the NPZs nor
``pab.db`` store the sensor geometry).

Reproducibility
---------------
The population is enumerated by sorting the NPZ file names, keeping only those
that resolve in ``pab.db`` (see :func:`eligible_stems`), and 100 are drawn
without replacement by ``numpy.random.default_rng(20260906)``
(:data:`SAMPLE_SEED`). The draw is a pure function of the sorted name list
(:func:`select_stems`), so re-running this script on the same archive rewrites
a byte-comparable artifact, and the selection is unit-tested against a
synthetic file list.

**The committed id list is the definition.** ``pace100_ids.csv`` beside this
script (:data:`IDS_CSV`) freezes the 100 selected ``obs_id`` values, and it —
not the seed, not the archive — is what a published PACE number refers to. The
archive lives outside the repo and outside ``$OS_COLOR``'s versioning, so a
file added to or removed from ``fit_chains/`` would silently move the draw
while every parameter here stayed the same. This script therefore
**cross-checks** its selection against the CSV whenever the file exists and
refuses to write a drifted artifact (``--allow-drift`` to override,
``--freeze-ids`` to re-freeze deliberately).

Usage
-----
::

    python extract_pace_100.py [--pab-run DIR] [--out-dir DIR] [--n 100]
                               [--freeze-ids] [--allow-drift]

Writes ``pace_pab_100.parquet`` (tidy long: one row per spectrum x wavelength,
with the per-spectrum metadata denormalised onto every row, following the
``ioptics.io`` results-table convention) under
``$OS_COLOR/IOPtics/pace_pab_100/``.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

#: RNG seed for the 100-of-274 draw. Fixed forever: changing it silently
#: changes which spectra every published PACE number refers to.
SAMPLE_SEED = 20260906

#: Number of spectra in the sample (Q22: "100 random PACE spectra").
N_SAMPLE = 100

#: Default PAB run directory (holds ``fit_chains/`` and ``pab.db``).
DEFAULT_PAB_RUN = Path(
    os.getenv('PAB_RUN1K', '/home/xavier/Oceanography/data/Color/PAB/run1k'))

#: Suffix every run1k chain file carries (the fitted model pair).
NPZ_SUFFIX = '_ExpBPow'

#: Artifact name + its subdirectory under ``$OS_COLOR/IOPtics``. Kept in sync
#: with :mod:`ioptics.datasets` (``PACE_PAB_SUBDIR`` / ``PACE_PAB_FILE``).
OUT_SUBDIR = 'pace_pab_100'
OUT_FILE = 'pace_pab_100.parquet'

#: Per-spectrum metadata columns, in artifact order. The adapter reads these
#: off the first row of each spectrum's group.
META_COLUMNS = ('lat', 'lon', 'time', 'theta_s', 'wmo', 'cycle', 'granule',
                'ix', 'iy', 'matchup_id', 'distance_km', 'rank', 'flagged')

#: The committed, citable id list (see "Reproducibility" above).
IDS_CSV = Path(__file__).resolve().parent / 'pace100_ids.csv'


# --------------------------------------------------------------------
# The frozen id list
# --------------------------------------------------------------------
def read_ids(path=IDS_CSV):
    """Read a frozen id list, ignoring ``#`` comment lines and blank lines.

    PACE observation ids are the run1k chain-file **stems** (strings), so
    they are returned verbatim.
    """
    out = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            out.append(line)
    return out


def write_ids(ids, path=IDS_CSV, *, seed=SAMPLE_SEED):
    """Write the frozen id list with a provenance header. Returns the path."""
    header = [
        '# PACE OCI observation ids for the IOPtics PACE dataset '
        '(rt_tests_B_v1 / rt_tests_smoke).',
        '# Generated by ioptics/runs/prototypes/rt_tests/extract_pace_100.py '
        '-- do not hand-edit.',
        f'# Selection: {len(ids)} stems drawn without replacement from the '
        f'pab.db-resolvable run1k fit_chains, numpy default_rng({seed}).',
        '# Source: PAB run1k fit archive (PACE OCI V3_2 L2 Rrs, 136 bands '
        '400-699 nm) matched to Argo BGC profiles.',
        f'# Count: {len(ids)}',
        '# One observation id (run1k chain-file stem) per line.',
    ]
    text = '\n'.join(header + list(ids)) + '\n'
    Path(path).write_text(text)
    return Path(path)


def check_ids(stems, path=IDS_CSV):
    """Compare a fresh selection against the frozen list.

    Returns ``(added, removed)`` — both empty when they agree — or ``None``
    when there is no frozen list to check against (the first extraction).
    """
    path = Path(path)
    if not path.is_file():
        return None
    frozen = read_ids(path)
    return (sorted(set(stems) - set(frozen)), sorted(set(frozen) - set(stems)))


# --------------------------------------------------------------------
# Filename parsing + the seeded draw (pure functions; unit-tested)
# --------------------------------------------------------------------
def parse_stem(stem):
    """Split a run1k chain-file stem into its ``pab.db`` join keys.

    ``{wmo}_{cycle}_{granule}_{ix}_{iy}_ExpBPow`` -> a dict with ``wmo``,
    ``cycle``, ``granule``, ``ix``, ``iy``. The granule basename itself
    contains underscores (``PACE_OCI.<t>.L2.OC_AOP.V3_2.nc``), so it is
    recovered as *everything between* the two leading and the two trailing
    fields rather than by a fixed field count.

    Raises
    ------
    ValueError
        If ``stem`` does not carry the ``_ExpBPow`` suffix or has too few
        fields to parse.
    """
    if not stem.endswith(NPZ_SUFFIX):
        raise ValueError(f'{stem!r}: not a run1k chain stem '
                         f'(expected the {NPZ_SUFFIX!r} suffix)')
    parts = stem[:-len(NPZ_SUFFIX)].split('_')
    if len(parts) < 5:
        raise ValueError(f'{stem!r}: too few underscore-separated fields')
    return {'wmo': int(parts[0]), 'cycle': int(parts[1]),
            'granule': '_'.join(parts[2:-2]),
            'ix': int(parts[-2]), 'iy': int(parts[-1])}


def select_stems(stems, n=N_SAMPLE, seed=SAMPLE_SEED):
    """Draw ``n`` stems without replacement, deterministically.

    The input is sorted first so the draw depends only on the *set* of names,
    not on the order the filesystem happened to list them in; the result is
    returned sorted as well, which fixes ``obs_ids()`` order for the adapter.

    Parameters
    ----------
    stems : iterable of str
        Candidate observation ids (chain-file stems).
    n : int, optional
        Sample size (default :data:`N_SAMPLE`). ``n >= len(stems)`` returns
        every stem — a smaller archive is a smaller sample, never an error.
    seed : int, optional
        RNG seed (default :data:`SAMPLE_SEED`).

    Returns
    -------
    list of str
        The selected stems, sorted.
    """
    pool = sorted(stems)
    if n >= len(pool):
        return pool
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(pool), size=int(n), replace=False)
    return sorted(pool[i] for i in idx)


# --------------------------------------------------------------------
# pab.db join
# --------------------------------------------------------------------
#: One pixel row per chain file. ``granules.granule_id`` is the granule
#: basename, which is exactly what the file name embeds.
_PIXEL_SQL = """
    SELECT mp.latitude, mp.longitude, mp.distance_km, mp.rank, mp.flagged,
           m.matchup_id, g.time_start, g.time_end
      FROM profiles p
      JOIN matchups m ON m.profile_id = p.profile_id
      JOIN granules g ON g.granule_id = m.granule_id
      JOIN matchup_pixels mp
             ON mp.matchup_id = m.matchup_id AND mp.ix = ? AND mp.iy = ?
     WHERE p.wmo = ? AND p.cycle = ? AND g.granule_id = ?
"""


def lookup_pixel(conn, keys):
    """Return the ``pab.db`` pixel row for one parsed stem, or ``None``.

    ``None`` means the archive and the catalogue disagree — the profile, the
    granule or the pixel is absent (see :func:`eligible_stems`). A join that
    matches more than one row would make the geolocation ambiguous and is
    treated the same way.
    """
    rows = conn.execute(_PIXEL_SQL, (keys['ix'], keys['iy'], keys['wmo'],
                                     keys['cycle'], keys['granule'])).fetchall()
    if len(rows) != 1:
        return None
    (lat, lon, distance_km, rank, flagged,
     matchup_id, time_start, time_end) = rows[0]
    return {'lat': lat, 'lon': lon, 'distance_km': distance_km,
            'rank': rank, 'flagged': flagged, 'matchup_id': matchup_id,
            'time': granule_time(time_start, time_end)}


def granule_time(time_start, time_end):
    """The observation instant for a granule, as an ISO-8601 UTC string.

    The granule *mid*-time when the catalogue has both bounds; PAB's run1k
    ``granules`` table populates ``time_start`` only (``time_end`` is NULL for
    all 2 734 rows), so in practice this returns the start time. The
    difference is bounded by a PACE OCI L2 granule's ~5-minute span, i.e. at
    most ~0.6 deg of hour angle and well under a degree of solar zenith —
    negligible against the RT comparison this feeds, but recorded here rather
    than hidden.
    """
    t0 = pd.Timestamp(time_start)
    if t0.tzinfo is None:
        t0 = t0.tz_localize('UTC')
    else:
        t0 = t0.tz_convert('UTC')
    if time_end:
        t1 = pd.Timestamp(time_end)
        t1 = t1.tz_localize('UTC') if t1.tzinfo is None else t1.tz_convert('UTC')
        t0 = t0 + (t1 - t0) / 2
    return t0.isoformat()


def eligible_stems(chain_dir, db_path):
    """Sorted stems of every chain NPZ that resolves in ``pab.db``.

    Returns ``(eligible, orphans)``. An *orphan* is a chain file whose
    ``(wmo, cycle)`` profile, granule, or pixel is missing from the
    catalogue — run1k's archive carries one such leftover from an earlier
    pass. Orphans are excluded from the population **before** the draw rather
    than dropped after it: a spectrum with no geolocation has no ``theta_s``,
    and a robust RT backend refuses to fit it
    (``ioptics.run.MissingGeometryError``), so sampling it would silently
    shrink the delivered set below 100.
    """
    stems = sorted(p.stem for p in Path(chain_dir).glob(f'*{NPZ_SUFFIX}.npz'))
    eligible, orphans = [], []
    with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as conn:
        for stem in stems:
            keys = parse_stem(stem)
            (eligible if lookup_pixel(conn, keys) is not None
             else orphans).append(stem)
    return eligible, orphans


# --------------------------------------------------------------------
# Table build
# --------------------------------------------------------------------
def build_table(stems, chain_dir, db_path):
    """Build the tidy long DataFrame for ``stems``.

    One row per (spectrum, wavelength) with the per-spectrum metadata
    (:data:`META_COLUMNS`) repeated on every row of the group — the same
    denormalised shape ``ioptics.io`` uses for its results tables, which keeps
    the artifact a single self-describing parquet file.
    """
    from robust import solar

    chain_dir, frames = Path(chain_dir), []
    with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as conn:
        for stem in stems:
            keys = parse_stem(stem)
            pixel = lookup_pixel(conn, keys)
            if pixel is None:                    # pre-filtered; belt and braces
                raise RuntimeError(f'{stem}: no pab.db pixel row')
            with np.load(chain_dir / f'{stem}.npz', allow_pickle=False) as npz:
                wave = np.asarray(npz['wave'], dtype=float)
                Rrs = np.asarray(npz['Rrs'], dtype=float)
                varRrs = np.asarray(npz['varRrs'], dtype=float)
            theta_s = float(solar.solar_zenith(pixel['time'], pixel['lat'],
                                               pixel['lon']))
            frames.append(pd.DataFrame({
                'obs_id': stem, 'wavelength': wave,
                'Rrs': Rrs, 'varRrs': varRrs,
                'lat': float(pixel['lat']), 'lon': float(pixel['lon']),
                'time': pixel['time'], 'theta_s': theta_s,
                'wmo': keys['wmo'], 'cycle': keys['cycle'],
                'granule': keys['granule'], 'ix': keys['ix'], 'iy': keys['iy'],
                'matchup_id': pixel['matchup_id'],
                'distance_km': pixel['distance_km'],
                'rank': pixel['rank'], 'flagged': pixel['flagged'],
            }))
    return pd.concat(frames, ignore_index=True)


def default_out_dir():
    """``$OS_COLOR/IOPtics/pace_pab_100`` (raises if ``$OS_COLOR`` is unset)."""
    osc = os.getenv('OS_COLOR')
    if not osc:
        raise RuntimeError('set $OS_COLOR (or pass --out-dir)')
    return Path(osc) / 'IOPtics' / OUT_SUBDIR


def main(argv=None):
    """Extract, join, and write the artifact; print a one-screen summary."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--pab-run', type=Path, default=DEFAULT_PAB_RUN,
                    help='PAB run directory holding fit_chains/ and pab.db')
    ap.add_argument('--out-dir', type=Path, default=None,
                    help='output directory (default $OS_COLOR/IOPtics/'
                         f'{OUT_SUBDIR})')
    ap.add_argument('--n', type=int, default=N_SAMPLE, help='sample size')
    ap.add_argument('--seed', type=int, default=SAMPLE_SEED, help='draw seed')
    ap.add_argument('--ids-csv', type=Path, default=IDS_CSV,
                    help=f'frozen id list to check against (default '
                         f'{IDS_CSV.name} beside this script)')
    ap.add_argument('--freeze-ids', action='store_true',
                    help='(re)write the frozen id list from this selection')
    ap.add_argument('--allow-drift', action='store_true',
                    help='extract even if the selection differs from the '
                         'frozen list (records the drift, does not fix it)')
    args = ap.parse_args(argv)

    chain_dir = args.pab_run / 'fit_chains'
    db_path = args.pab_run / 'pab.db'
    out_dir = args.out_dir or default_out_dir()

    eligible, orphans = eligible_stems(chain_dir, db_path)
    stems = select_stems(eligible, n=args.n, seed=args.seed)

    # Cross-check against the committed definition before doing any work. A
    # drifted archive changes *which spectra* every published PACE number
    # describes, and nothing else here would reveal it: the seed, the sample
    # size and the artifact path are all unchanged.
    drift = check_ids(stems, args.ids_csv)
    if drift is None:
        print(f'no frozen id list at {args.ids_csv} — pass --freeze-ids to '
              'create one')
    elif any(drift):
        added, removed = drift
        msg = (f'selection drifted from {args.ids_csv}: '
               f'+{len(added)} / -{len(removed)}\n'
               f'    added  : {added[:10]}\n'
               f'    removed: {removed[:10]}\n'
               '  The run1k archive is not versioned with this repo, so a '
               'file added to or removed from fit_chains/ silently moves the '
               'draw. Re-freeze deliberately (--freeze-ids) or override '
               '(--allow-drift); do not do either without saying so in the '
               'run notes.')
        if not (args.allow_drift or args.freeze_ids):
            raise SystemExit(f'ERROR: {msg}')
        print(f'WARNING: {msg}')
    else:
        print(f'id cross-check OK: {len(stems)} stems match {args.ids_csv}')

    if args.freeze_ids:
        print(f'froze ids -> {write_ids(stems, args.ids_csv, seed=args.seed)}')

    df = build_table(stems, chain_dir, db_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / OUT_FILE
    df.to_parquet(out_path, index=False)

    per_obs = df.groupby('obs_id', sort=True).first()
    print(f'wrote {out_path} ({out_path.stat().st_size / 1e6:.2f} MB)')
    print(f'  spectra      : {per_obs.shape[0]} of {len(eligible)} eligible '
          f'({len(eligible) + len(orphans)} chain NPZs, '
          f'{len(orphans)} orphaned in pab.db)')
    if orphans:
        print(f'  orphans      : {", ".join(orphans)}')
    print(f'  bands        : {df.groupby("obs_id").size().unique().tolist()} '
          f'@ {df.wavelength.min():.0f}-{df.wavelength.max():.0f} nm')
    print(f'  theta_s      : {per_obs.theta_s.min():.2f} - '
          f'{per_obs.theta_s.max():.2f} deg '
          f'(median {per_obs.theta_s.median():.2f})')
    print(f'  lat / lon    : {per_obs.lat.min():.2f} - {per_obs.lat.max():.2f} '
          f'/ {per_obs.lon.min():.2f} - {per_obs.lon.max():.2f}')
    print(f'  time         : {per_obs.time.min()} .. {per_obs.time.max()}')
    print(f'  negative Rrs : {int((df.Rrs < 0).sum())} bands '
          f'in {int((df.Rrs < 0).groupby(df.obs_id).any().sum())} spectra '
          '(kept, per Q24)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

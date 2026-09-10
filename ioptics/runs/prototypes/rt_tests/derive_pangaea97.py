"""Derive (and freeze) the PANGAEA population the RT tests fit.

The RT-test sweeps compare five radiative-transfer variants on the *same*
spectra, and the comparison is only readable where the retrieval can be graded
against a full IOP decomposition. PANGAEA V3 (Valente et al. 2022) enumerates
64 071 observations with usable ``Rrs``; **97** of them satisfy all three
criteria below, and those 97 are the RT population.

Criteria (all three, intersected)
---------------------------------
1. **Usable Rrs** — at least :data:`MIN_RRS_BANDS` finite ``Rrs`` bands, which
   is exactly ``PANGAEAAdapter.obs_ids()``'s own enumeration rule (design Q12).
2. **Complete spectral truth** — a non-empty ``aph`` *and* ``acdom`` *and*
   ``bbp`` spectrum in the ``iop`` table. ``multi_v2``'s
   ``pangaea_truth_ids()`` takes the **union** of the three families (1 593
   ids) because any one of them is scorable on its own; the RT tests take the
   **intersection** instead, because a variant that moves ``a_ph`` by
   redistributing absorption into ``a_dg`` is indistinguishable from one that
   is simply better unless both are graded on the same spectrum.
3. **NOMAD provenance** — the observation's ``subdataset`` (the cruise tag the
   ``rrs`` table carries, e.g. ``'nomad_en372'``) begins with
   :data:`NOMAD_PREFIX`. NOMAD is the one parent compilation in V3 whose
   ``aph``/``acdom``/``bbp`` come from a single documented measurement protocol
   per cruise, so the three families are mutually consistent rather than
   merely co-present. Dropping this criterion admits 166 further ids (160
   MERMAID, 6 SeaBASS) and mixes protocols across the population.

Why freeze it
-------------
The result is written to :data:`IDS_CSV` (``pangaea97_ids.csv``, beside this
script) and **committed**. That file — not this script, and not the number 97 —
is the citable definition of the population: ocpy's PANGAEA tables are an
external dependency that can be revised, and every RT-test number refers to a
specific set of spectra. Re-running this script rewrites the CSV; a diff there
is a change of population and must be read as one.

Usage
-----
::

    python derive_pangaea97.py [--out PATH] [--check] [--no-nomad]

``--check`` derives the set and compares it against the committed CSV without
writing (exit 1 on drift) — the form for CI or a pre-run sanity check.
"""

from __future__ import annotations

import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent

#: The frozen id list this script writes and the build script reads.
IDS_CSV = HERE / 'pangaea97_ids.csv'

#: Minimum finite ``Rrs`` bands for an observation to be usable. Matches
#: ``ioptics.datasets.PANGAEAAdapter.obs_ids``'s default.
MIN_RRS_BANDS = 5

#: The three spectral IOP families, as ``ocpy.insitu.pangaea`` names them. All
#: three are required (see the module docstring, criterion 2).
TRUTH_KINDS = ('aph', 'acdom', 'bbp')

#: ``subdataset`` prefix identifying the NOMAD parent compilation.
NOMAD_PREFIX = 'nomad'

#: Expected size of the population. Not enforced — a mismatch is reported, not
#: raised, because an upstream table revision is real news rather than a bug.
EXPECTED_N = 97


def derive_ids(*, min_rrs=MIN_RRS_BANDS, nomad_only=True, path=None):
    """The RT-test PANGAEA population, as a sorted list of observation ids.

    A pure set intersection over ocpy's tidy ``rrs`` / ``iop`` tables — no
    record is prepped and no spectrum is loaded, so it is cheap enough to run
    as a check before a sweep.

    Parameters
    ----------
    min_rrs : int, optional
        Minimum finite ``Rrs`` bands (:data:`MIN_RRS_BANDS`).
    nomad_only : bool, optional
        Restrict to the NOMAD parent compilation (default ``True``; see the
        module docstring, criterion 3).
    path : str or pathlib.Path or None, optional
        Explicit PANGAEA V3 directory; ``None`` lets ocpy resolve it.

    Returns
    -------
    list
        Sorted observation ids.
    """
    from ocpy.insitu import pangaea

    rrs = pangaea.load('rrs', path=path)
    iop = pangaea.load('iop', path=path)

    counts = pangaea.n_spectral(rrs, kind='rrs')
    ids = set(counts.index[counts >= int(min_rrs)])

    for kind in TRUTH_KINDS:
        c = pangaea.n_spectral(iop, kind=kind)
        ids &= set(c.index[c > 0])

    if nomad_only:
        sub = rrs['subdataset'].astype(str)
        ids &= set(rrs.index[sub.str.startswith(NOMAD_PREFIX)])

    return sorted(ids)


def read_ids(path=IDS_CSV):
    """Read a frozen id list, ignoring ``#`` comment lines and blanks.

    Ids are returned as :class:`int` — PANGAEA's global ``ID`` is an integer,
    and the adapter indexes on it, so a list of strings would silently match
    nothing.
    """
    out = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            out.append(int(line))
    return out


def write_ids(ids, path=IDS_CSV, *, nomad_only=True, min_rrs=MIN_RRS_BANDS):
    """Write the frozen id list with a provenance header. Returns the path."""
    header = [
        '# PANGAEA observation ids for the IOPtics RT tests '
        '(rt_tests_A_v1 / rt_tests_smoke).',
        '# Generated by ioptics/runs/prototypes/rt_tests/derive_pangaea97.py '
        '-- do not hand-edit.',
        f'# Criteria: >= {min_rrs} finite Rrs bands AND non-empty '
        f'{" AND ".join(TRUTH_KINDS)} spectral truth'
        + (f' AND subdataset starts with {NOMAD_PREFIX!r}.'
           if nomad_only else ' (parent compilation unrestricted).'),
        '# Source: PANGAEA V3 (Valente et al. 2022) via ocpy.insitu.pangaea.',
        f'# Count: {len(ids)}',
        '# One observation id per line.',
    ]
    text = '\n'.join(header + [str(i) for i in ids]) + '\n'
    Path(path).write_text(text)
    return Path(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, default=IDS_CSV,
                    help=f'output CSV (default {IDS_CSV.name} beside this script)')
    ap.add_argument('--check', action='store_true',
                    help='compare against the committed CSV instead of writing')
    ap.add_argument('--no-nomad', action='store_true',
                    help='drop the NOMAD restriction (diagnostic; widens the set)')
    ap.add_argument('--pangaea-path', default=None,
                    help='explicit PANGAEA V3 directory (default: ocpy resolves)')
    args = ap.parse_args(argv)

    ids = derive_ids(nomad_only=not args.no_nomad, path=args.pangaea_path)
    print(f'derived {len(ids)} ids (expected {EXPECTED_N})')
    if len(ids) != EXPECTED_N:
        print(f'  NOTE: population differs from the expected {EXPECTED_N} — '
              'the upstream tables or the criteria changed; read the diff '
              'before publishing anything against it')

    if args.check:
        frozen = read_ids(args.out)
        if frozen == ids:
            print(f'  {args.out} is up to date ({len(frozen)} ids)')
            return 0
        added = sorted(set(ids) - set(frozen))
        removed = sorted(set(frozen) - set(ids))
        print(f'  DRIFT vs {args.out}: +{len(added)} / -{len(removed)}')
        print(f'    added  : {added[:20]}')
        print(f'    removed: {removed[:20]}')
        return 1

    write_ids(ids, args.out, nomad_only=not args.no_nomad)
    print(f'wrote {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Build / stamp / write the per-sweep ``provenance.yaml`` record.

Captures everything needed to reproduce a sweep end to end (design doc
§"Provenance"): version stamps (ioptics/bing/ocpy commits + the design-doc /
implementation-doc versions), a **verbatim copy of the sweep config**, the
dataset options, and a **per-algorithm block** carrying the full model choices,
priors, RT options, fit method, and noise model. Written beside the results
tables under ``$OS_COLOR/IOPtics/runs/<sweep_id>/``.

Each results row's ``provenance_id`` is ``"<sweep_id>#<algorithm>"`` — see
:func:`provenance_id` — so any row traces back to its algorithm block here.

Depends only on the standard library + PyYAML (it reads ``AlgorithmSpec`` /
``SweepConfig`` attributes and introspects package versions).
"""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml


def provenance_id(sweep_id, algorithm):
    """The id linking a results row to its algorithm block: ``sweep#algo``."""
    return f"{sweep_id}#{algorithm}"


def _now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _git_commit(repo_path):
    """Short HEAD hash of the git repo at ``repo_path`` (None if unavailable)."""
    try:
        out = subprocess.run(
            ['git', '-C', str(repo_path), 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def _repo_of(module):
    """Best-guess repo root for an installed package (its dir's parent)."""
    return Path(module.__file__).resolve().parent.parent


def _doc_version(filename):
    """Parse ``**Version:** X`` from a design doc beside the ioptics repo."""
    try:
        import ioptics
        path = (_repo_of(ioptics) / 'docs' / 'design' / filename)
        for line in path.read_text().splitlines():
            if line.startswith('**Version:**'):
                return line.split('**Version:**', 1)[1].strip()
    except Exception:
        pass
    return None


def versions():
    """Version stamp: ioptics/bing/ocpy commits + versions, and doc versions."""
    import ioptics

    v = {'ioptics': {'commit': _git_commit(_repo_of(ioptics)),
                     'version': ioptics.__version__}}
    for name in ('bing', 'ocpy'):
        try:
            mod = importlib.import_module(name)
            v[name] = {'commit': _git_commit(_repo_of(mod)),
                       'version': getattr(mod, '__version__', None)}
        except Exception:
            v[name] = {'commit': None, 'version': None}
    v['design_doc'] = _doc_version('IOPtics_design.md')
    v['implementation_doc'] = _doc_version('IOPtics_implementation.md')
    return v


def algorithm_block(spec):
    """Serializable provenance block for one :class:`AlgorithmSpec`.

    Everything that changes what the fit does, and nothing that does not.

    Two fields were missing and both govern the result: **``maxfev``**, the
    optimizer's evaluation budget, which decides *whether* a fit converges at all
    (the turbid two-component models fail on a large fraction of spectra at scipy's
    default, so `TURBID_MAXFEV` is the difference between a result and a wall of
    ``fit_failed``); and the **``mcmc``** block, whose ``nsteps``/``nburn`` decide
    whether a posterior is sampled or merely started.

    ``spec.noise_model`` is deliberately **not** here. Its own docstring calls it
    "descriptive only" — the noise applied is the *sweep-level* ``cfg.noise_model``
    handed to :func:`ioptics.prep.prep_dataset`, and the fit always uses
    ``record.varRrs``. Emitting it per algorithm asserted a per-algorithm noise
    model that never existed and could silently disagree with the sweep's. The real,
    per-record tag (which records the imputation actually applied) is persisted onto
    ``results_scalar`` instead, where it can be counted.
    """
    return {
        'name': spec.name,
        'label': spec.label,
        'anw_model': spec.anw_model,
        'bbnw_model': spec.bbnw_model,
        'apriors': spec.apriors,
        'bpriors': spec.bpriors,
        'othera_priors': spec.othera_priors,
        'rt': {
            'variable_Gordon': spec.rt.variable_Gordon,
            'variable_Gordon_G0': spec.rt.variable_Gordon_G0,
            'variable_Gordon_bbp': spec.rt.variable_Gordon_bbp,
            'include_Raman': spec.rt.include_Raman,
            'include_Chl_fl': spec.rt.include_Chl_fl,
            'phi_C': spec.rt.phi_C,
            'double_gaussian': spec.rt.double_gaussian,
            # Schema 4: the RT-backend selection. Which forward model turned
            # (a, bb) into Rrs is not a detail — 'gordon' and 'robust_ztt' are
            # different physics — and ``cdom_fraction`` records the value of
            # the a_cdom = f x a_dg proxy any CDOM-fluorescence result rests
            # on (a project decision, not a measurement; rt_tests Q32).
            'rt_backend': spec.rt.rt_backend,
            'fit_Bp': spec.rt.fit_Bp,
            'Bp_value': spec.rt.Bp_value,
            'include_CDOM_fl': spec.rt.include_CDOM_fl,
            'cdom_fraction': spec.rt.cdom_fraction,
        },
        'set_Sdg': spec.set_Sdg,
        'sSdg': spec.sSdg,
        'beta': spec.beta,
        'fit_method': spec.fit_method,
        'maxfev': spec.maxfev,
        'fits_turbid': spec.fits_turbid,
        'mcmc': {
            'nsteps': spec.mcmc.nsteps,
            'nburn': spec.mcmc.nburn,
            'nMC': spec.mcmc.nMC,
        },
    }


#: Version of the algorithm-block schema. Bumped when a field is **added** to
#: :func:`algorithm_block`, so a reader can tell "this sweep ran the default" from
#: "this sweep predates the field being recorded at all" — the two are not the same
#: claim, and on ``gloria_turbid_v3`` they differ: it really ran ``expb_pow`` at
#: ``maxfev=40000`` (patched into the registry by its build script) while its
#: provenance block, written before Task 9, records no ``maxfev`` whatsoever.
#: Schema 3 adds ``fits_turbid`` (the pre-fit ``out_of_scope`` scope claim,
#: 2026-08-10) — it decides whether a red-peaked record is fitted at all, so
#: two sweeps differing on it are not running the same algorithm.
#: Schema 4 (2026-09-05) widens the ``rt`` sub-block from BING's seven legacy
#: Gordon toggles to the twelve keys of today's ``rt_dict``, adding
#: ``rt_backend`` / ``fit_Bp`` / ``Bp_value`` / ``include_CDOM_fl`` /
#: ``cdom_fraction``; the sweep-level record additionally carries
#: ``dataset_opts`` and the ``leaderboard`` flag.
PROVENANCE_SCHEMA = 4

#: Keys added after schema 1, with the value that means "as the default"
#: (schema 2: ``maxfev``/``mcmc``; schema 3: ``fits_turbid``). Digesting fills
#: these in when absent, so blocks from different schema eras describing the
#: *same* configuration produce the **same** digest. Without this, re-running an
#: old sweep would change every digest for byte-identical configurations, and the
#: profile pages' "what varied between sweeps" section would report schema
#: versioning as configuration drift.
_SCHEMA_FIELD_DEFAULTS = {
    'maxfev': None,
    'mcmc': {'nsteps': 40000, 'nburn': 1000, 'nMC': None},
    'fits_turbid': False,
}

#: The same idea one level down, for keys added *inside* an existing sub-block.
#: :data:`_SCHEMA_FIELD_DEFAULTS` cannot express schema 4's change, because the
#: five new RT keys did not appear beside ``rt`` — they appeared *within* it, so
#: filling a missing top-level key would never fire and every pre-existing
#: algorithm's digest would move the moment the block got wider.
#:
#: The normalization is the mirror image: for each listed sub-key, a value equal
#: to its schema-4 default is **dropped** from the digest payload. An
#: old seven-key ``rt`` block therefore hashes identically to a new twelve-key
#: one that is configured the Gordon way, while any non-default value (a robust
#: backend, a free ``B_p``, a CDOM fraction other than 0.8) survives into the
#: payload and moves the digest, which is exactly the discrimination a digest
#: is for.
#:
#: The cost, stated honestly: ``Bp_value`` only matters when ``fit_Bp`` is on
#: and ``cdom_fraction`` only when ``include_CDOM_fl`` is, so a block that
#: carries a non-default value for one of them with its switch off digests
#: apart from an otherwise identical block that does not. That is the
#: conservative direction — it splits two configurations that behave alike,
#: rather than pooling two that do not.
_SCHEMA_NESTED_DEFAULTS = {
    'rt': {
        'rt_backend': 'gordon',
        'fit_Bp': False,
        'Bp_value': 0.01,
        'include_CDOM_fl': False,
        'cdom_fraction': 0.8,
    },
}


#: Keys excluded from the digest. ``name``/``label`` identify rather than define;
#: ``noise_model`` was emitted per algorithm before Task 9 and was never a property
#: of one (see :func:`algorithm_block`), so including it would make every old block
#: hash differently from its own re-run; ``digest`` cannot hash itself; and
#: ``schema`` must be excluded or bumping it would change every digest — which is
#: precisely the discontinuity :data:`_SCHEMA_FIELD_DEFAULTS` exists to prevent.
_DIGEST_EXCLUDE = ('name', 'label', 'noise_model', 'digest', 'schema')


def algorithm_digest(spec_or_block):
    """A short stable hash of an algorithm's full parameterization.

    Two rows sharing an algorithm *name* are only the same algorithm if this agrees.
    Computed from :func:`algorithm_block` — i.e. from the spec at **run time**, over
    every field that changes what the fit does — rather than reconstructed later from
    whatever columns happened to survive into a table.

    **Stable across the schema change.** A block written before ``maxfev``/``mcmc``
    were recorded is normalized against :data:`_SCHEMA_FIELD_DEFAULTS` first, and a
    block written before the ``rt`` sub-block grew its five RT-backend keys is
    normalized against :data:`_SCHEMA_NESTED_DEFAULTS` — so an old sweep and its
    re-run agree whenever the configuration really is the same. The
    cost is honest and worth stating: a pre-schema-2 block cannot distinguish "ran at
    the default budget" from "ran at a raised budget nobody wrote down", so its digest
    is a claim about what was *recorded*, not a proof of what ran. ``schema`` on the
    block says which.

    MD5 rather than :func:`hash`, because Python salts string hashing per process and
    a digest that changes between runs is not a digest.
    """
    block = (spec_or_block if isinstance(spec_or_block, dict)
             else algorithm_block(spec_or_block))
    payload = {k: v for k, v in block.items() if k not in _DIGEST_EXCLUDE}
    for key, default in _SCHEMA_FIELD_DEFAULTS.items():
        payload.setdefault(key, default)
    for key, defaults in _SCHEMA_NESTED_DEFAULTS.items():
        sub = payload.get(key)
        if isinstance(sub, dict):
            payload[key] = {k: v for k, v in sub.items()
                            if not (k in defaults and v == defaults[k])}
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.md5(canonical.encode('utf-8')).hexdigest()[:12]


def build(sweep_id, cfg=None, specs=(), *, datasets=None, created=None):
    """Assemble the provenance record (a plain, YAML-serializable dict).

    Parameters
    ----------
    sweep_id : str
        The sweep id (names the output directory).
    cfg : SweepConfig or None
        The sweep config; copied verbatim under ``config`` via ``cfg.to_dict()``.
    specs : iterable of AlgorithmSpec
        The resolved algorithm specs → one ``algorithms`` block each.
    datasets : dict or None
        Per-dataset options/counts (e.g. ``{'L23': {'X': 1, 'Y': 0, 'n_obs': N}}``).
    created : str or None
        ISO timestamp; defaults to now (UTC).

    Notes
    -----
    Two sweep-level keys are hoisted out of the config copy to the top of the
    record (schema 4). ``dataset_opts`` is the verbatim per-dataset adapter
    configuration — "L23" is not one dataset, it is one per ``(X, Y)``, and a
    reader comparing two sweeps needs that without parsing the embedded config.
    ``leaderboard`` is the publish/withhold flag
    :func:`ioptics.report.leaderboard.update` reads, so the exclusion travels
    with the artifacts. Both are also still present inside ``config``; the
    hoisted copies are what the tooling reads.
    """
    blocks = []
    for s in specs:
        block = algorithm_block(s)
        # The digest rides *inside* the block, so a reader comparing two sweeps'
        # provenance files can tell "same algorithm" from "same name" without
        # re-deriving anything; ``schema`` says which fields the block was capable
        # of recording when it was written.
        block['schema'] = PROVENANCE_SCHEMA
        block['digest'] = algorithm_digest(block)
        blocks.append(block)
    dataset_opts = getattr(cfg, 'dataset_opts', None) or {}
    return {
        'sweep_id': sweep_id,
        'created': created or _now(),
        'schema': PROVENANCE_SCHEMA,
        'versions': versions(),
        'config': cfg.to_dict() if cfg is not None else {},
        'dataset_opts': {k: dict(v) for k, v in dataset_opts.items()},
        'leaderboard': bool(getattr(cfg, 'leaderboard', True)),
        'datasets': datasets or {},
        'algorithms': blocks,
    }


def dump(record):
    """Serialize a provenance record to YAML text."""
    return yaml.safe_dump(record, sort_keys=False, default_flow_style=False)


def write(sweep_id, record, *, root=None):
    """Write ``provenance.yaml`` under ``<runs_root>/<sweep_id>/``; return path."""
    from ioptics import io

    path = io.sweep_dir(sweep_id, root=root, create=True) / 'provenance.yaml'
    path.write_text(dump(record))
    return path

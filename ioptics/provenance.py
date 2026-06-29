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

import importlib
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
    """Serializable provenance block for one :class:`AlgorithmSpec`."""
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
        },
        'set_Sdg': spec.set_Sdg,
        'sSdg': spec.sSdg,
        'beta': spec.beta,
        'fit_method': spec.fit_method,
        'noise_model': spec.noise_model,
    }


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
    """
    return {
        'sweep_id': sweep_id,
        'created': created or _now(),
        'versions': versions(),
        'config': cfg.to_dict() if cfg is not None else {},
        'datasets': datasets or {},
        'algorithms': [algorithm_block(s) for s in specs],
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

"""YAML <-> Python sweep-config surface (load / validate / dump).

A sweep is driven by **one YAML config** — the single source of truth for the
sweep id, datasets, algorithms (registry names + per-algorithm overrides), the
sweep-level noise model and fit method, and the MCMC subset (see
``docs/design/IOPtics_implementation.md`` §"Algorithm registry" / §"Driving a
sweep"). This module parses that YAML into plain config objects, **validates**
it, and ``dump()`` writes it back out for the provenance copy.

The objects here are deliberately **neutral**: algorithms resolve to a
``(name, fit_method, overrides)`` carrier rather than to a fully-built
:class:`~ioptics.algorithms.spec.AlgorithmSpec`. The registry/spec resolution is
a Stage 2 concern; Stage 0 only needs the config to round-trip and validate.

Example (the headline sweep YAML)::

    sweep_id: expb_giop_L23_v1
    datasets: [L23]
    noise_model: pace                 # sweep-level, fixed for ALL algorithms
    algorithms:
      - expb_pow                      # registry defaults (sweep fit_method)
      - name: giop
        fit_method: mcmc              # per-algorithm override (allowed)
        mcmc: {nsteps: 40000, nburn: 1000}
    fit_method: chisq                 # sweep default (least-squares first pass)
    mcmc_subset: 200

Validation rules (per the design doc):

- ``sweep_id`` is **required** (non-empty string); it names the output dir.
- ``datasets`` is **required** (non-empty list of dataset names).
- ``algorithms`` is **required**; each entry is either a bare registry name
  (string) or a mapping carrying ``name`` plus optional overrides.
- ``noise_model`` and ``fit_method`` are **sweep-level**.
- ``fit_method`` is **overridable per algorithm**; ``noise_model`` is **not**
  (a per-algorithm ``noise_model`` is a hard error — comparing one algorithm
  under two noise models is, by construction, two sweeps).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

ALLOWED_FIT_METHODS = ('chisq', 'mcmc')


class ConfigError(ValueError):
    """Raised when a sweep config is missing a required field or violates a
    validation rule (e.g. a per-algorithm ``noise_model`` override)."""


@dataclass
class AlgorithmConfig:
    """One algorithm entry from a sweep config (a *neutral* carrier).

    Parameters
    ----------
    name : str
        Registry name of the algorithm (e.g. ``'expb_pow'``). Resolution to an
        :class:`~ioptics.algorithms.spec.AlgorithmSpec` happens in Stage 2.
    fit_method : str or None
        Per-algorithm fit-method override (``'chisq'`` | ``'mcmc'``). ``None``
        means "use the sweep-level default".
    overrides : dict
        Any remaining per-algorithm overrides (e.g. ``mcmc``, ``rt``, priors,
        model names), passed through verbatim for Stage-2 resolution.
    """

    name:       str
    fit_method: str | None = None
    overrides:  dict = field(default_factory=dict)

    def to_entry(self):
        """Canonical YAML entry: a bare string when there are no overrides,
        else a mapping with ``name`` first."""
        if self.fit_method is None and not self.overrides:
            return self.name
        entry = {'name': self.name}
        if self.fit_method is not None:
            entry['fit_method'] = self.fit_method
        entry.update(self.overrides)
        return entry


@dataclass
class SweepConfig:
    """A validated sweep configuration.

    The output of :func:`load`; the input to ``run.run_sweep`` and the source
    of the provenance copy (:func:`dump`). Paths derive from ``$OS_COLOR`` + the
    ``sweep_id`` at run time, so ``results_root`` is optional here.

    Parameters
    ----------
    sweep_id : str
        Author-chosen, legible id; names ``$OS_COLOR/IOPtics/runs/<sweep_id>/``.
    datasets : list of str
        Dataset names to sweep over (e.g. ``['L23']``).
    algorithms : list of AlgorithmConfig
        The algorithms to run, with any per-algorithm overrides.
    noise_model : str
        Sweep-level noise model, fixed for all algorithms (``'pace'`` |
        ``'insitu'`` | ``'pct:X'``). Defaults to ``'pace'``.
    fit_method : str
        Sweep-level default fit method (``'chisq'`` | ``'mcmc'``). Defaults to
        ``'chisq'``.
    mcmc_subset : int or None
        Number of spectra to additionally run with MCMC. ``None`` if unset.
    seed : int or None
        Master RNG seed for reproducible noise draws. ``None`` if unset.
    results_root : str or None
        Output root override; ``None`` defers to ``$OS_COLOR/IOPtics/runs/``.
    extra : dict
        Any additional top-level keys, preserved verbatim for provenance.
    """

    sweep_id:     str
    datasets:     list
    algorithms:   list
    noise_model:  str = 'pace'
    fit_method:   str = 'chisq'
    mcmc_subset:  int | None = None
    seed:         int | None = None
    results_root: str | None = None
    extra:        dict = field(default_factory=dict)
    # Where it was loaded from; not part of identity / round-trip.
    source_path:  str | None = field(default=None, compare=False, repr=False)

    def to_dict(self):
        """Canonical mapping mirroring the input schema (round-trips through
        :func:`from_dict`). Optional fields are emitted only when set."""
        out = {
            'sweep_id':    self.sweep_id,
            'datasets':    list(self.datasets),
            'noise_model': self.noise_model,
            'algorithms':  [a.to_entry() for a in self.algorithms],
            'fit_method':  self.fit_method,
        }
        if self.mcmc_subset is not None:
            out['mcmc_subset'] = self.mcmc_subset
        if self.seed is not None:
            out['seed'] = self.seed
        if self.results_root is not None:
            out['results_root'] = self.results_root
        out.update(self.extra)
        return out

    def dump(self, path=None):
        """Serialize to YAML text for the provenance copy; optionally write it
        to ``path``. Thin wrapper over the module-level :func:`dump`."""
        return dump(self, path)


def _coerce_algorithm(entry, idx):
    """Validate and normalize one ``algorithms`` entry into an
    :class:`AlgorithmConfig`."""
    if isinstance(entry, str):
        if not entry:
            raise ConfigError(f"algorithms[{idx}]: empty algorithm name")
        return AlgorithmConfig(name=entry)

    if isinstance(entry, dict):
        d = dict(entry)
        name = d.pop('name', None)
        if not name or not isinstance(name, str):
            raise ConfigError(
                f"algorithms[{idx}] must carry a non-empty string 'name'")
        if 'noise_model' in d:
            raise ConfigError(
                f"algorithms[{idx}] ('{name}'): 'noise_model' is a sweep-level "
                "setting and cannot be overridden per algorithm — compare two "
                "noise models with two separate sweeps")
        fit_method = d.pop('fit_method', None)
        if fit_method is not None and fit_method not in ALLOWED_FIT_METHODS:
            raise ConfigError(
                f"algorithms[{idx}] ('{name}'): fit_method must be one of "
                f"{ALLOWED_FIT_METHODS}, got {fit_method!r}")
        return AlgorithmConfig(name=name, fit_method=fit_method, overrides=d)

    raise ConfigError(
        f"algorithms[{idx}] must be a name (str) or a mapping with 'name', "
        f"got {type(entry).__name__}")


def from_dict(mapping, *, source_path=None):
    """Validate a parsed mapping and resolve it to a :class:`SweepConfig`.

    This is the shared core of :func:`load`/:func:`loads` and the Python-API
    entry point. Raises :class:`ConfigError` on any validation failure.
    """
    if not isinstance(mapping, dict):
        raise ConfigError(
            "sweep config must be a mapping at the top level, got "
            f"{type(mapping).__name__}")
    d = dict(mapping)

    sweep_id = d.pop('sweep_id', None)
    if not sweep_id or not isinstance(sweep_id, str):
        raise ConfigError("sweep config requires a non-empty string 'sweep_id'")

    datasets = d.pop('datasets', None)
    if (not datasets or not isinstance(datasets, (list, tuple))
            or not all(isinstance(x, str) for x in datasets)):
        raise ConfigError(
            "sweep config requires a non-empty 'datasets' list of names")

    algorithms_raw = d.pop('algorithms', None)
    if not algorithms_raw or not isinstance(algorithms_raw, (list, tuple)):
        raise ConfigError(
            "sweep config requires a non-empty 'algorithms' list")
    algorithms = [_coerce_algorithm(e, i) for i, e in enumerate(algorithms_raw)]

    noise_model = d.pop('noise_model', 'pace')
    if not isinstance(noise_model, str) or not noise_model:
        raise ConfigError("'noise_model' must be a non-empty string")

    fit_method = d.pop('fit_method', 'chisq')
    if fit_method not in ALLOWED_FIT_METHODS:
        raise ConfigError(
            f"'fit_method' must be one of {ALLOWED_FIT_METHODS}, "
            f"got {fit_method!r}")

    mcmc_subset = d.pop('mcmc_subset', None)
    if mcmc_subset is not None and (
            isinstance(mcmc_subset, bool) or not isinstance(mcmc_subset, int)
            or mcmc_subset < 0):
        raise ConfigError("'mcmc_subset' must be a non-negative integer")

    seed = d.pop('seed', None)
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise ConfigError("'seed' must be an integer")

    results_root = d.pop('results_root', None)
    if results_root is not None and not isinstance(results_root, str):
        raise ConfigError("'results_root' must be a string path")

    return SweepConfig(
        sweep_id=sweep_id,
        datasets=list(datasets),
        algorithms=algorithms,
        noise_model=noise_model,
        fit_method=fit_method,
        mcmc_subset=mcmc_subset,
        seed=seed,
        results_root=results_root,
        extra=d,                       # any remaining keys, preserved
        source_path=source_path,
    )


def loads(text, *, source_path=None):
    """Parse + validate a sweep config from a YAML string."""
    mapping = yaml.safe_load(text)
    return from_dict(mapping, source_path=source_path)


def load(path):
    """Read, parse, and validate a sweep config YAML file at ``path``."""
    text = Path(path).read_text()
    return loads(text, source_path=str(path))


def dump(cfg, path=None):
    """Serialize a :class:`SweepConfig` to YAML text (the provenance copy).

    Key order mirrors the canonical schema (``sort_keys=False``). If ``path`` is
    given, the text is also written there. The output round-trips: ``load`` of
    a dumped config reconstructs an equal :class:`SweepConfig`.
    """
    text = yaml.safe_dump(cfg.to_dict(), sort_keys=False, default_flow_style=False)
    if path is not None:
        Path(path).write_text(text)
    return text

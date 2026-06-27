"""Import / smoke test — the cheapest guard against a broken package surface.

Asserts that ``import ioptics`` works, the top-level contracts are re-exported,
and every module in the package tree imports cleanly. This is the check CI runs
to catch breakage in the IOPtics module surface (and, once wired, the BING/ocpy
dependency edge). No data and no heavy compute.
"""

import importlib

import pytest

# Every importable module in the package tree (the `runs/` dir is build scripts,
# not a package, so it is intentionally absent).
ALL_MODULES = [
    'ioptics',
    'ioptics.config',
    'ioptics.records',
    'ioptics.datasets',
    'ioptics.prep',
    'ioptics.noise',
    'ioptics.algorithms',
    'ioptics.algorithms.spec',
    'ioptics.algorithms.registry',
    'ioptics.run',
    'ioptics.evaluate',
    'ioptics.provenance',
    'ioptics.io',
    'ioptics.metrics',
    'ioptics.diagnostics',
    'ioptics.plotting',
    'ioptics.report',
    'ioptics.report.figures',
    'ioptics.report.tables',
    'ioptics.report.leaderboard',
    'ioptics.report.bokeh',
    'ioptics.report.rst',
    'ioptics.report.standard',
]


def test_import_ioptics_and_version():
    import ioptics
    assert isinstance(ioptics.__version__, str)
    assert ioptics.__version__


def test_top_level_contracts_reexported():
    import ioptics
    from ioptics.records import ComponentFit, PreparedRecord, RetrievalResult
    assert ioptics.PreparedRecord is PreparedRecord
    assert ioptics.RetrievalResult is RetrievalResult
    assert ioptics.ComponentFit is ComponentFit


@pytest.mark.parametrize('module', ALL_MODULES)
def test_module_imports_cleanly(module):
    assert importlib.import_module(module) is not None

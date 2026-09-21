=============
API reference
=============

Auto-generated documentation for the ``ioptics`` package: every module documents
its classes and functions in full, grouped below in pipeline order — data
contracts and config, dataset preparation, the algorithm registry, retrieval,
metrics, and the reporting layer.

Two conventions worth knowing before reading any of it. **Thresholds and
conventions are named constants, not literals**, so a number that appears in a
report can be traced to the one place that defines it — for example
:data:`ioptics.records.RED_PEAK_NM` (the turbid Rrs-peak cutoff),
:data:`ioptics.records.CHI2NU_POOR_FIT` (above which a fit is not a solution) and
:data:`ioptics.metrics.PERFECT_VALUE` (what "perfect" means per metric, which
differs between them). And the layers are **strictly separated**:
:mod:`ioptics.metrics` and :mod:`ioptics.diagnostics` import no BING or ocpy and
do no file I/O; :mod:`ioptics.plotting` returns figures and never writes them; the
:mod:`ioptics.report` package is the only layer that touches the docs tree.

Core contracts
==============

The two load-bearing dataclasses (plus :class:`~ioptics.records.ComponentFit`)
that flow through the whole pipeline.

.. automodule:: ioptics.records
   :members:

Sweep configuration
===================

.. automodule:: ioptics.config
   :members:

Data preparation
================

.. automodule:: ioptics.datasets
   :members:

.. automodule:: ioptics.prep
   :members:

.. automodule:: ioptics.noise
   :members:

Algorithm registry
==================

.. automodule:: ioptics.algorithms.spec
   :members:

.. automodule:: ioptics.algorithms.registry
   :members:

Retrieval & run
===============

.. automodule:: ioptics.run
   :members:

.. automodule:: ioptics.evaluate
   :members:

.. automodule:: ioptics.provenance
   :members:

.. automodule:: ioptics.io
   :members:

Metrics & diagnostics
=====================

.. automodule:: ioptics.metrics
   :members:

.. automodule:: ioptics.diagnostics
   :members:

Reporting
=========

.. automodule:: ioptics.style
   :members:

.. automodule:: ioptics.plotting
   :members:

.. automodule:: ioptics.report.figures
   :members:

.. automodule:: ioptics.report.tables
   :members:

.. automodule:: ioptics.report.leaderboard
   :members:

.. automodule:: ioptics.report.bokeh
   :members:

.. automodule:: ioptics.report.rst
   :members:

.. automodule:: ioptics.report.profiles
   :members:

.. automodule:: ioptics.report.standard
   :members:

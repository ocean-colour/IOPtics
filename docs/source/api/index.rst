=============
API reference
=============

Auto-generated documentation for the ``ioptics`` package. Modules still being
built out (Stages 1–6) currently show only their module-level docstring; the
fully implemented Stage-0 modules — :mod:`ioptics.records` and
:mod:`ioptics.config` — document their classes and functions in full.

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

.. automodule:: ioptics.report.standard
   :members:

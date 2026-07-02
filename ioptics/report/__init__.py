"""Reporting subsystem.

The standard figure/table set, persistent leaderboard, standalone/static
BokehJS figures, the accumulating ``.rst`` site, and the on-demand standard
report — all version/provenance-stamped. Consumes the persisted sweep artifacts
(results + metrics + chains + provenance); renders via :mod:`ioptics.plotting`
(matplotlib) and Bokeh. Imports no BING/ocpy directly.

Submodules are eagerly imported so ``report.standard.build`` /
``report.leaderboard.update`` resolve after ``from ioptics import report``.
"""

from __future__ import annotations

from ioptics.report import (bokeh, figures, leaderboard, rst, standard,
                            tables)

__all__ = ['figures', 'tables', 'leaderboard', 'bokeh', 'rst', 'standard']

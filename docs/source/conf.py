"""Configuration file for the IOPtics Sphinx documentation builder.

See https://www.sphinx-doc.org/en/master/usage/configuration.html for the full
list of built-in configuration values.
"""

import os
import sys

# Make the IOPtics package importable for autodoc. conf.py lives at
# docs/source/, so the repository root is two levels up.
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------

project = 'IOPtics'
copyright = '2026, J. Xavier Prochaska et al.'
author = 'J. Xavier Prochaska et al.'

try:                                   # single-source the version from the package
    import ioptics
    release = ioptics.__version__
except Exception:
    release = '0.0.dev0'
version = '.'.join(release.split('.')[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',         # NumPy / Google style docstrings
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
master_doc = 'index'

# -- Autodoc / autosummary ---------------------------------------------------

autosummary_generate = True

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': True,
    'show-inheritance': True,
}
autodoc_typehints = 'description'      # built-in (no sphinx-autodoc-typehints dep)

# Mock the heavy / sibling imports so the docs build without installing the
# whole scientific stack on the RTD runner. IOPtics' implemented modules
# (records, config) only need numpy + PyYAML, but later modules will import
# these — mocking now keeps autodoc green as the package grows.
autodoc_mock_imports = [
    'bing', 'ocpy',
    'emcee', 'corner', 'bokeh',
    'h5netcdf', 'cftime',
]

# Napoleon settings
napoleon_numpy_docstring = True
napoleon_google_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_ivar = True

# -- Intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
}

# -- HTML output -------------------------------------------------------------

# Furo — a clean, modern theme (light/dark) distinct from the classic RTD look.
html_theme = 'furo'
html_static_path = ['_static']
html_title = 'IOPtics'
html_css_files = ['custom.css']       # ocean-colour theme accents

html_theme_options = {
    'sidebar_hide_name': False,
    'navigation_with_keys': True,
    'light_css_variables': {
        'color-brand-primary': '#1a6ea8',
        'color-brand-content': '#1a6ea8',
    },
    'dark_css_variables': {
        'color-brand-primary': '#6cb6e8',
        'color-brand-content': '#6cb6e8',
    },
}

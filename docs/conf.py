# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


master_doc = "index"

project = "boomi-cicd-cli-py"
copyright = "2023, Boomi"
author = "Adam Bedenbaugh"
release = "0.1"

sys.path.insert(0, os.path.abspath("../"))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Used to generate documentation from docstrings
    "sphinx.ext.intersphinx",  # Used to link to other Sphinx documentation
    "sphinx.ext.todo",  # Used to add TODOs to documentationw
    "sphinx.ext.viewcode",  # Used to add links to source code
]

autosummary_generate = True
# numfig = True
# numfig_format = {'figure': 'Figure %s. ', 'table': 'Table %s. ', 'code-block': 'Listing %s. '}
# numfig_secnum_depth = 0
# TODO: Figure out why numfig isn't working after figure 11 in Azure Devops doc
autodoc_mock_imports = ["requests"]
html_favicon = "favicon.ico"
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_css_files = [
    "css/custom.css",
]

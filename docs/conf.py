"""Sphinx configuration file for the qctss_client documentation."""

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# pylint: disable=invalid-name,redefined-builtin

from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

DOCS_DIR = Path(__file__).parent

try:
    release = version("qctss_client")
except PackageNotFoundError:
    release = "0.3.0"

version = ".".join(release.split(".")[:2])

project = "QC-Test Space Client Documentation"
author = "QC-Test Team, RCCI, Academia Sinica, Taiwan"
copyright = f"{datetime.now().year}, {author}"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.mathjax",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinxext.opengraph",
    "myst_nb",  # required for JupyterBook-style notebooks
]

# -- Intersphinx mapping ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#module

intersphinx_mapping = {
    "pydantic": ("https://docs.pydantic.dev/latest", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    # "tqdm": ("https://tqdm.github.io/", None),
    # Well, tqdm is not yet documented for intersphinx
    # See: https://github.com/tqdm/tqdm/issues/705
}


# Execution settings (via myst-nb or jupyter-book)
nb_execution_mode = "off"  # "cache" or "force" or "auto" or "off"
nb_execution_timeout = 1200
nb_execution_cache_path = "_jupyter_cache"

templates_path = ["_templates"] if (DOCS_DIR / "_templates").exists() else []
exclude_patterns = [
    "jupyter_execute",
    "_dist",
    "_generated",
    "README.md",
    "README.rst",
    "README.txt",
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_logo = ""
html_favicon = ""
html_title = f"QC-Test Space Client Documentation {release}"
html_sourcelink_suffix = ""

html_extra_path = []  # You can set this if needed
html_static_path = ["_static"] if (DOCS_DIR / "_static").exists() else []
html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]

html_last_updated_fmt = "%Y-%m-%d %H:%M:%S"  # Format for the last updated time
html_use_edit_page_button = False
html_use_repository_button = False
html_use_issues_button = False
html_use_multitoc_numbering = True
html_extra_footer = ""
html_home_page_in_navbar = True
html_announcement = ""

html_theme_options: dict[str, Any] = {
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/asqum/qctss_client",
            "html": """
                <i class="fa-brands fa-solid fa-github fa-2x"></i>
            """,
            "class": "",
        },
        {
            "name": "RCCI, Academia Sinica",
            "url": "https://rcci.sinica.edu.tw/facility.php?id=7",
            "html": """
                <i class="fa-solid fa-home fa-2x"></i>
            """,
            "class": "",
        },
    ]
}

language = "en"

# -- Options for Pygments (syntax highlighting) -----------------------------

# pygments_style = "sphinx"
# pygments_dark_style = "lightbulb"

"""Configuration file for the Sphinx documentation builder."""

from datetime import datetime
import os

from ansys_sphinx_theme import (
    ansys_favicon,
    ansys_logo_white,
    ansys_logo_white_cropped,
    get_version_match,
    watermark,
)

from ansys.tools.common import __version__

# Project information
project = "ansys-tools-common"
copyright = f"(c) {datetime.now().year} ANSYS, Inc. All rights reserved"
author = "ANSYS, Inc."
release = version = __version__
cname = os.getenv("DOCUMENTATION_CNAME", default="tools.docs.pyansys.com")
switcher_version = get_version_match(__version__)

html_theme = "ansys_sphinx_theme"
html_short_title = html_title = "Ansys tools common"
html_baseurl = f"https://{cname}/version/stable"

# specify the location of your github repo
html_context = {
    "github_user": "ansys",
    "github_repo": "ansys-tools-common",
    "github_version": "main",
    "doc_path": "doc/source",
}
html_theme_options = {
    "logo": "pyansys",
    "switcher": {
        "json_url": f"https://{cname}/versions.json",
        "version_match": switcher_version,
    },
    "check_switcher": False,
    "github_url": "https://github.com/ansys/ansys-tools-common",
    "show_prev_next": False,
    "show_breadcrumbs": True,
    "collapse_navigation": True,
    "use_edit_page_button": True,
    "additional_breadcrumbs": [
        ("PyAnsys", "https://docs.pyansys.com/"),
    ],
    "icon_links": [
        {
            "name": "Support",
            "url": "https://github.com/ansys/ansys-tools-common/discussions",
            "icon": "fa fa-comment fa-fw",
        },
        {
            "name": "Download documentation in PDF",
            "url": f"https://{cname}/version/{switcher_version}/_static/assets/download/ansys-tools-common.pdf",  # noqa: E501
            "icon": "fa fa-file-pdf fa-fw",
        },
    ],
    "ansys_sphinx_theme_autoapi": {
        "project": project,
        "package_depth": 3,
    },
    "static_search": {
        "threshold": 0.5,
        "minMatchCharLength": 2,
        "ignoreLocation": True,
    },
}

linkcheck_ignore = []

if switcher_version != "dev":
    linkcheck_ignore.append(f"https://github.com/ansys/ansys-tools-common/releases/tag/v{__version__}")

# Sphinx extensions
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
    "ansys_sphinx_theme.extension.autoapi",
    "sphinx_click",  # Required by local-product-launcher
    "sphinx_gallery.gen_gallery",
    "sphinx_jinja",
]

# sphinx gallery options
sphinx_gallery_conf = {

    # path to your examples scripts
    "examples_dirs": ["../../examples"],
    # path where to save gallery generated examples
    "gallery_dirs": ["examples"],
    # Pattern to search for example files
    "filename_pattern": r"\.py",
    # Remove the "Download all examples" button from the top level gallery
    "download_all_examples": False,
    # Sort gallery example by file name instead of number of lines (default)
    "within_subsection_order": "FileNameSortKey",
    # directory where function granular galleries are stored
    "backreferences_dir": None,
    # Modules for which function level galleries are created.  In
    "doc_module": "ansys-tools-common",
    "image_scrapers": ("matplotlib",),
    "ignore_pattern": r"__init__\.py",
    "thumbnail_size": (350, 350),
    "copyfile_regex": r".*\.rst",
}


# numpydoc configuration
numpydoc_show_class_members = False
numpydoc_xref_param_type = True

# Consider enabling numpydoc validation. See:
# https://numpydoc.readthedocs.io/en/latest/validation.html#
numpydoc_validate = True
numpydoc_validation_checks = {
    "GL06",  # Found unknown section
    "GL07",  # Sections are in the wrong order.
    # "GL08",  # The object does not have a docstring
    "GL09",  # Deprecation warning should precede extended summary
    "GL10",  # reST directives {directives} must be followed by two colons
    "SS01",  # No summary found
    "SS02",  # Summary does not start with a capital letter
    # "SS03", # Summary does not end with a period
    "SS04",  # Summary contains heading whitespaces
    # "SS05", # Summary must start with infinitive verb, not third person
    "RT02",  # The first line of the Returns section should contain only the
    # type, unless multiple values are being returned"
}

html_favicon = ansys_favicon
# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

typehints_defaults = "comma"
# additional logos for the latex coverpage
latex_additional_files = [watermark, ansys_logo_white, ansys_logo_white_cropped]
suppress_warnings = ["autoapi.python_import_resolution", "ref.python"]

# Ignore files
exclude_patterns = ["changelog/*.md"]


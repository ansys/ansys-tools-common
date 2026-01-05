# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tools to find or cache installed Ansys products.

.. warning::
   This is not concurrent-safe. (Multiple Python processes might race on this data.)
"""

from ansys.tools.common.path.path import (
    LOG,
    SETTINGS_DIR,
    SUPPORTED_ANSYS_VERSIONS,
    change_default_ansys_path,  # deprecated
    change_default_dyna_path,
    change_default_mapdl_path,
    change_default_mechanical_path,
    clear_configuration,
    find_ansys,  # deprecated
    find_dyna,
    find_mapdl,
    find_mechanical,
    get_ansys_path,  # deprecated
    get_available_ansys_installations,
    get_dyna_path,
    get_latest_ansys_installation,
    get_mapdl_path,
    get_mechanical_path,
    get_saved_application_path,
    save_ansys_path,  # deprecated
    save_dyna_path,
    save_mapdl_path,
    save_mechanical_path,
    version_from_path,
)

__all__ = [
    "LOG",
    "SETTINGS_DIR",
    "SUPPORTED_ANSYS_VERSIONS",
    "change_default_mapdl_path",
    "change_default_mechanical_path",
    "change_default_dyna_path",
    "clear_configuration",
    "find_mapdl",
    "find_mechanical",
    "find_dyna",
    "get_available_ansys_installations",
    "get_latest_ansys_installation",
    "get_mapdl_path",
    "get_mechanical_path",
    "get_saved_application_path",
    "get_dyna_path",
    "save_mapdl_path",
    "save_mechanical_path",
    "save_dyna_path",
    "version_from_path",
    "change_default_ansys_path",
    "find_ansys",
    "get_ansys_path",
    "save_ansys_path",
]

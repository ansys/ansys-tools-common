# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
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

"""Miscellaneous functions used by ansys-tools-path."""

import os


def is_float(input_string: str) -> bool:
    r"""Return true when a string can be converted to a float.

    Parameters
    ----------
    input_string : str
        The string to check.

    Returns
    -------
    bool
        ``True`` if the string can be converted to a float, ``False`` otherwise.
    """
    try:
        float(input_string)
        return True
    except ValueError:
        return False


def is_windows() -> bool:
    r"""Check if the host machine is on Windows.

    Returns
    -------
    ``True`` if the host machine is on Windows, ``False`` otherwise.
    """
    return os.name == "nt"


def is_linux() -> bool:
    r"""Check if the host machine is Linux.

    Returns
    -------
    ``True`` if the host machine is Linux, ``False`` otherwise.
    """
    return os.name == "posix"

# Copyright (C) 2025 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

"""Tool discovery functions for licensing utilities.

This module provides functions to find licensing tools (lmutil, ansysli_util)
within Ansys installations.
"""

import logging
import os
from pathlib import Path
from typing import Literal, Union

from ansys.tools.common.path.path import (
    SUPPORTED_ANSYS_VERSIONS,
    SUPPORTED_VERSIONS_TYPE,
    _get_unified_install_base_for_version,
)

logger = logging.getLogger(__name__)


def _find_licensing_tool(
    tool_name: str,
    version: float | int | None = None,
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Union[tuple[str, float], tuple[Literal[""], Literal[""]]]:
    """Find a licensing tool executable within an Ansys installation.

    Parameters
    ----------
    tool_name : str
        Base name of the tool without extension (e.g., ``"lmutil"``,
        ``"ansysli_util"``).
    version : float | int | None, optional
        Ansys version to search for. Can be specified as an integer
        (e.g., ``251`` for 2025 R1) or as a float (e.g., ``25.1``).
        If not specified, the latest installed version is used.
    supported_versions : dict[int, str], optional
        Dictionary mapping version numbers to release strings.
        Defaults to ``SUPPORTED_ANSYS_VERSIONS``.

    Returns
    -------
    tuple[str, float] | tuple[str, str]
        A tuple of ``(path, version)``, where ``path`` is the path to the tool
        executable (empty string if not found) and ``version`` is the version
        as a float (for example, ``25.1``) or an empty string if not found.
    """
    ans_path, ver_str = _get_unified_install_base_for_version(version, supported_versions)
    if not ans_path or not ver_str:
        logger.debug("No Ansys installation found for %s (version=%s)", tool_name, version)
        return "", ""

    base = Path(ans_path)
    if os.name == "nt":
        tool_path = base / "licensingclient" / "winx64" / f"{tool_name}.exe"
    else:
        tool_path = base / "licensingclient" / "linx64" / tool_name

    if tool_path.exists():
        logger.debug("Found %s at %s (version %s)", tool_name, tool_path, int(ver_str) / 10)
        return str(tool_path), int(ver_str) / 10
    logger.debug("%s not found at expected path %s", tool_name, tool_path)
    return "", ""


def find_lmutil(
    version: float | int | None = None,
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Union[tuple[str, float], tuple[Literal[""], Literal[""]]]:
    """Find the lmutil executable within an Ansys installation.

    The lmutil tool is part of FlexLM and is used for license server
    administration tasks such as querying license status.

    Parameters
    ----------
    version : float | int | None, optional
        Ansys version to search for. Can be specified as an integer
        (e.g., ``251`` for 2025 R1) or as a float (e.g., ``25.1``).
        If not specified, the latest installed version is used.
    supported_versions : dict[int, str], optional
        Dictionary mapping version numbers to release strings.
        Defaults to ``SUPPORTED_ANSYS_VERSIONS``.

    Returns
    -------
    tuple[str, float] | tuple[str, str]
        A tuple of ``(path, version)``, where ``path`` is the path to the
        lmutil executable (empty string if not found) and ``version`` is the
        version as a float (for example, ``25.1``) or an empty string if not
        found.

    Examples
    --------
    Find lmutil for the latest installed version:

    >>> from ansys.tools.common.licensing import find_lmutil
    >>> find_lmutil()
    ('C:/Program Files/ANSYS Inc/v251/licensingclient/winx64/lmutil.exe', 25.1)

    Find lmutil for a specific version:

    >>> find_lmutil(version=242)
    ('C:/Program Files/ANSYS Inc/v242/licensingclient/winx64/lmutil.exe', 24.2)

    Using float version format:

    >>> find_lmutil(version=25.1)
    ('C:/Program Files/ANSYS Inc/v251/licensingclient/winx64/lmutil.exe', 25.1)
    """
    return _find_licensing_tool("lmutil", version, supported_versions)


def find_ansysli_util(
    version: float | int | None = None,
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Union[tuple[str, float], tuple[Literal[""], Literal[""]]]:
    """Find the ansysli_util executable within an Ansys installation.

    The ansysli_util tool is used for Ansys Licensing Interconnect
    diagnostics and configuration.

    Parameters
    ----------
    version : float | int | None, optional
        Ansys version to search for. Can be specified as an integer
        (e.g., ``251`` for 2025 R1) or as a float (e.g., ``25.1``).
        If not specified, the latest installed version is used.
    supported_versions : dict[int, str], optional
        Dictionary mapping version numbers to release strings.
        Defaults to ``SUPPORTED_ANSYS_VERSIONS``.

    Returns
    -------
    tuple[str, float] | tuple[str, str]
        A tuple of ``(path, version)``, where ``path`` is the path to the
        ansysli_util executable (empty string if not found) and ``version`` is
        the version as a float (for example, ``25.1``) or an empty string if
        not found.

    Examples
    --------
    Find ansysli_util for the latest installed version:

    >>> from ansys.tools.common.licensing import find_ansysli_util
    >>> find_ansysli_util()
    ('C:/Program Files/ANSYS Inc/v251/licensingclient/winx64/ansysli_util.exe', 25.1)

    Find ansysli_util for a specific version:

    >>> find_ansysli_util(version=242)
    ('C:/Program Files/ANSYS Inc/v242/licensingclient/winx64/ansysli_util.exe', 24.2)
    """
    return _find_licensing_tool("ansysli_util", version, supported_versions)

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
"""Module for installation path retrieval."""

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import re
from typing import Callable, Dict, List, Literal, Optional, Tuple, Union, cast
import warnings

import platformdirs

from ansys.tools.common.path.applications import ApplicationPlugin, dyna, mapdl, mechanical

PLUGINS: Dict[str, ApplicationPlugin] = {"mechanical": mechanical, "dyna": dyna, "mapdl": mapdl}

LOG = logging.getLogger(__name__)

PRODUCT_TYPE = Literal["mapdl", "mechanical", "dyna"]
SUPPORTED_VERSIONS_TYPE = Dict[int, str]

linux_default_dirs = [["/", "usr", "ansys_inc"], ["/", "ansys_inc"], ["/", "install", "ansys_inc"]]
LINUX_DEFAULT_DIRS = [str(Path(*each)) for each in linux_default_dirs]

CONFIG_FILE_NAME = "config.txt"

SUPPORTED_ANSYS_VERSIONS: SUPPORTED_VERSIONS_TYPE = {
    271: "2027R1",
    261: "2026R1",
    252: "2025R2",
    251: "2025R1",
    242: "2024R2",
    241: "2024R1",
    232: "2023R2",
    231: "2023R1",
    222: "2022R2",
    221: "2022R1",
    212: "2021R2",
    211: "2021R1",
    202: "2020R2",
    201: "2020R1",
    195: "19.5",
    194: "19.4",
    193: "19.3",
    192: "19.2",
    191: "19.1",
}

PRODUCT_EXE_INFO = {
    "mapdl": {
        "name": "Ansys MAPDL",
        "pattern": "ansysxxx",
        "patternpath": "vXXX/ansys/bin/ansysXXX",
    },
    "dyna": {
        "name": "Ansys LS-DYNA",  # patternpath and pattern are not used for dyna
    },
    "mechanical": {
        "name": "Ansys Mechanical",
    },
}

if os.name == "nt":  # pragma: no cover
    PRODUCT_EXE_INFO["mechanical"]["patternpath"] = "vXXX/aisol/bin/winx64/AnsysWBU.exe"
    PRODUCT_EXE_INFO["mechanical"]["pattern"] = "AnsysWBU.exe"
    PRODUCT_EXE_INFO["dyna"]["patternpath"] = "vXXX/ansys/bin/winx64/LSDYNAXXX.exe"
    PRODUCT_EXE_INFO["dyna"]["pattern"] = "LSDYNAXXX.exe"
else:
    PRODUCT_EXE_INFO["mechanical"]["patternpath"] = "vXXX/aisol/.workbench"
    PRODUCT_EXE_INFO["mechanical"]["pattern"] = ".workbench"
    PRODUCT_EXE_INFO["dyna"]["patternpath"] = "vXXX/ansys/bin/lsdynaXXX"
    PRODUCT_EXE_INFO["dyna"]["pattern"] = "lsdynaXXX"

# Settings directory
SETTINGS_DIR = Path(platformdirs.user_data_dir(appname="ansys_tools_path", appauthor="Ansys"))

try:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    LOG.debug(f"Settings directory ensured at: {SETTINGS_DIR}")
except OSError:
    warnings.warn(
        f"Unable to create settings directory at {SETTINGS_DIR}.\nWill be unable to cache product executable locations."
    )

# Full path to the configuration file
CONFIG_FILE = SETTINGS_DIR / CONFIG_FILE_NAME

# FileMigrationStrategy: TypeAlias = Callable[[], Dict[PRODUCT_TYPE, str]]


def _get_installed_windows_versions(
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Dict[int, str]:  # pragma: no cover
    """Get the AWP_ROOT environment variable values for supported versions.

    Parameters
    ----------
    supported_versions : SUPPORTED_VERSIONS_TYPE, optional
        A dictionary of supported Ansys versions. Defaults to `SUPPORTED_ANSYS_VERSIONS`.

    Returns
    -------
    Dict[int, str]
        A dictionary mapping Ansys version numbers to their installation paths.
    """
    # The student version overwrites the AWP_ROOT env var
    # (if it is installed later)
    # However the priority should be given to the non-student version.
    awp_roots: list[Tuple[int, str]] = []
    awp_roots_student: list[Tuple[int, str]] = []
    for ver in supported_versions:
        path_str = os.environ.get(f"AWP_ROOT{ver}", "")
        if not path_str:
            continue

        path = Path(path_str)
        if "student" in path_str.lower():
            awp_roots_student.insert(0, (-1 * ver, path_str))
            # Check if non-student version exists by replacing "\\ANSYS Student"
            path_non_student = Path(str(path).replace("\\ANSYS Student", ""))
            if path_non_student.is_dir():
                awp_roots.append((ver, str(path_non_student)))
        else:
            awp_roots.append((ver, path_str))

    awp_roots.extend(awp_roots_student)
    installed_versions: Dict[int, str] = {ver: p for ver, p in awp_roots if p and Path(p).is_dir()}

    if installed_versions:
        LOG.debug(f"Found the following unified Ansys installation versions: {installed_versions}")
    else:
        LOG.debug("No unified Ansys installations found using 'AWP_ROOT' environments.")

    return installed_versions


def _get_default_linux_base_path() -> Optional[str]:
    """Get the default base path of the Ansys unified install on Linux.

    Returns
    -------
    Optional[str]
        Base path to search for Ansys installations.
    """
    for path_str in LINUX_DEFAULT_DIRS:
        path = Path(path_str)
        LOG.debug(f"Checking {path} as a potential ansys directory")
        if path.is_dir():
            return str(path)
    return None


def _get_default_windows_base_path() -> Optional[str]:  # pragma: no cover
    """Get the default base path of the Ansys unified install on Windows.

    Returns
    -------
    Optional[str]
        Base path to search for Ansys installations.
    """
    program_files = Path(os.environ.get("PROGRAMFILES", ""))
    base_path = program_files / "ANSYS Inc"

    if not base_path.exists():
        LOG.debug(f"The supposed 'base_path' {base_path} does not exist. No available ansys found.")
        return None
    return str(base_path)


def _is_float(input_string: str) -> bool:
    """Return true when a string can be converted to a float.

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


def _expand_base_path(base_path: Optional[str]) -> Dict[int, str]:
    """Expand the base path to all possible ansys Unified installations contained within.

    Parameters
    ----------
    base_path: Optional[str]
        Base path to search for Ansys installations.

    Returns
    -------
    Dict[int, str]
        A dictionary mapping Ansys version numbers to their installation paths.
    """
    if base_path is None:
        return {}

    base = Path(base_path)

    ansys_paths: Dict[int, str] = {}

    # Search for versions like /base_path/vXXX
    for path in base.glob("v*"):
        ver_str = path.name[-3:]
        if _is_float(ver_str):
            ansys_paths[int(ver_str)] = str(path)

    # Search for ANSYS STUDENT versions like /base_path/ANSYS*/vXXX
    # student_base_pattern = base / "ANSYS*"
    student_paths = []
    for student_dir in base.glob("ANSYS*"):
        student_paths.extend(student_dir.glob("v*"))

    if not student_paths:
        return ansys_paths

    for path in student_paths:
        ver_str = path.name[-3:]
        if _is_float(ver_str):
            ansys_paths[-int(ver_str)] = str(path)

    return ansys_paths


def _get_available_base_unified(
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Dict[int, str]:
    r"""Get a dictionary of available Ansys Unified Installation versions with their base paths.

    Returns
    -------
        Paths for Unified Installation versions installed.

    Examples
    --------
    On Windows:

    >>> _get_available_base_unified()
    >>> {251: "C:\\Program Files\\ANSYS Inc\\v251"}

    On Linux:

    >>> _get_available_base_unified()
    >>> {251: "/usr/ansys_inc/v251"}
    """
    base_path = None
    if os.name == "nt":  # pragma: no cover
        installed_versions = _get_installed_windows_versions(supported_versions)
        if installed_versions:
            return installed_versions
        else:  # pragma: no cover
            base_path = _get_default_windows_base_path()
    elif os.name == "posix":
        base_path = _get_default_linux_base_path()
    else:  # pragma: no cover
        raise OSError(f"Unsupported OS {os.name}")
    return _expand_base_path(base_path)


def get_available_ansys_installations(
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Dict[int, str]:
    r"""Get a dictionary of available Ansys unified installation versions with their base paths.

    Returns
    -------
    dict[int: str]
        Dictionary of all Ansys unified installations paths in Windows.

    Notes
    -----
    On Windows, It uses the environment variable ``AWP_ROOTXXX``.

    The student versions are returned at the end of the dict and
    with negative value for the version.

    Examples
    --------
    >>> from ansys.tools.common.path import get_available_ansys_installations
    >>> get_available_ansys_installations()
    {251: 'C:\\Program Files\\ANSYS Inc\\v251',
     242: 'C:\\Program Files\\ANSYS Inc\\v242',
     -242: 'C:\\Program Files\\ANSYS Inc\\ANSYS Student\\v242'}

    Return all installed Ansys paths in Linux.

    >>> get_available_ansys_installations()
    {251: '/usr/ansys_inc/v251',
     242: '/usr/ansys_inc/v242',
     241: '/usr/ansys_inc/v241'}
    """
    return _get_available_base_unified(supported_versions)


def _get_unified_install_base_for_version(
    version: Optional[Union[int, float]] = None,
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Tuple[str, str]:
    """Search for the unified install of a given version from the supported versions.

    Returns
    -------
    Tuple[str, str]
        The base unified install path and version
    """
    versions = _get_available_base_unified(supported_versions)
    if not versions:
        return "", ""

    if not version:
        version = max(versions.keys())

    elif isinstance(version, float):
        # Using floats, converting to int.
        version = int(version * 10)

    try:
        ans_path = versions[version]
    except KeyError as e:
        raise ValueError(f"Version {version} not found. Available versions are {list(versions.keys())}") from e

    version = abs(version)
    return ans_path, str(version)


def find_mechanical(
    version: Optional[float] = None,
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Union[Tuple[str, float], Tuple[Literal[""], Literal[""]]]:
    """
    Search for the Ansys Mechanical path in the standard installation location.

    Returns
    -------
    mechanical_path : str
        Full path to the executable file for the latest Mechanical version.
    version : float | str
        Version in the float format. For example, ``25.1`` for 2025 R1.
        If no version has be found, version is set to ""

    Examples
    --------
    On Windows:

    >>> from ansys.tools.common.path import find_mechanical
    >>> find_mechanical()
    ('C:/Program Files/ANSYS Inc/v251/aisol/bin/winx64/AnsysWBU.exe', 25.1)

    On Linux:

    >>> find_mechanical()
    ('/usr/ansys_inc/v251/aisol/.workbench', 25.1)
    """
    ans_path, version = _get_unified_install_base_for_version(version, supported_versions)
    if not ans_path or not version:
        return "", ""

    ans_path = Path(ans_path)
    if os.name == "nt":  # pragma: no cover
        mechanical_bin = ans_path / "aisol" / "bin" / "winx64" / "AnsysWBU.exe"
    else:
        mechanical_bin = ans_path / "aisol" / ".workbench"

    return str(mechanical_bin), int(version) / 10


def find_mapdl(
    version: Optional[Union[int, float]] = None,
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Union[Tuple[str, float], Tuple[Literal[""], Literal[""]]]:
    """Search for the Ansys MAPDL path within the standard install location.

    Returns the path of the latest version.

    Parameters
    ----------
    version : int, float, optional
        Version of Ansys MAPDL to search for.
        If using ``int``, it should follow the convention ``XXY``, where
        ``XX`` is the major version,
        and ``Y`` is the minor.
        If using ``float``, it should follow the convention ``XX.Y``, where
        ``XX`` is the major version,
        and ``Y`` is the minor.
        If ``None``, use latest available version on the machine.

    Returns
    -------
    ansys_path : str
        Full path to ANSYS executable.

    version : float
        Version float.  For example, 25.1 corresponds to 2025R1.

    Examples
    --------
    Within Windows

    >>> from ansys.tools.common.path import find_mapdl
    >>> find_mapdl()
    'C:/Program Files/ANSYS Inc/v251/ANSYS/bin/winx64/ansys251.exe', 25.1

    Within Linux

    >>> find_mapdl()
    (/usr/ansys_inc/v251/ansys/bin/ansys251, 25.1)
    """
    ans_path, version = _get_unified_install_base_for_version(version, supported_versions)
    if not ans_path or not version:
        return "", ""

    ansys_bin_path = Path(ans_path) / "ansys" / "bin"
    if os.name == "nt":
        ansys_bin = ansys_bin_path / "winx64" / f"ansys{version}.exe"
    else:
        ansys_bin = ansys_bin_path / f"ansys{version}"

    return str(ansys_bin), int(version) / 10


def find_dyna(
    version: Optional[Union[int, float]] = None,
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Union[Tuple[str, float], Tuple[Literal[""], Literal[""]]]:
    """Search for the Ansys LS-DYNA path within the standard install location.

    Returns the path of the latest version.

    Parameters
    ----------
    version : int, float, optional
        Version of Ansys LS-Dyna to search for.
        If using ``int``, it should follow the convention ``XXY``, where
        ``XX`` is the major version,
        and ``Y`` is the minor.
        If using ``float``, it should follow the convention ``XX.Y``, where
        ``XX`` is the major version,
        and ``Y`` is the minor.
        If ``None``, use latest available version on the machine.

    Returns
    -------
    ansys_path : str
        Full path to Ansys LS-Dyna executable.

    version : float
        Version float.  For example, 25.1 corresponds to 2025R1.

    Examples
    --------
    Within Windows

    >>> from ansys.tools.common.path import find_dyna
    >>> find_dyna()
    'C:/Program Files/ANSYS Inc/v251/ANSYS/bin/winx64/LSDYNA251.exe', 25.1

    Within Linux

    >>> find_dyna()
    (/usr/ansys_inc/v251/ansys/bin/lsdyna251, 25.1)
    """
    ans_path, version = _get_unified_install_base_for_version(version, supported_versions)
    if not ans_path or not version:
        return "", ""

    ansys_bin_path = Path(ans_path) / "ansys" / "bin"
    if os.name == "nt":
        ansys_bin = ansys_bin_path / "winx64" / f"LSDYNA{version}.exe"
    else:
        ansys_bin = ansys_bin_path / f"lsdyna{version}"

    return str(ansys_bin), int(version) / 10


def _find_installation(
    product: str,
    version: Optional[float] = None,
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Union[Tuple[str, float], Tuple[Literal[""], Literal[""]]]:
    """Find the installation path for a certain product.

    Parameters
    ----------
    product : str
        The product type, either "mapdl", "mechanical", or "dyna".
    version : float, optional
        The version of the product to search for. If not provided, the latest version is used.
    supported_versions : SUPPORTED_VERSIONS_TYPE, optional
        A dictionary of supported versions for the product. Defaults to `SUPPORTED_ANSYS_VERSIONS`.

    Returns
    -------
    Tuple[str, float] | Tuple[Literal[""], Literal[""]]
        A tuple containing the path to the executable and the version number.
    """
    if product == "mapdl":
        return find_mapdl(version, supported_versions)
    elif product == "mechanical":
        return find_mechanical(version, supported_versions)
    elif product == "dyna":
        return find_dyna(version, supported_versions)
    raise Exception("unexpected product")


def find_ansys(
    version: Optional[float] = None,
    supported_versions: SUPPORTED_VERSIONS_TYPE = SUPPORTED_ANSYS_VERSIONS,
) -> Union[Tuple[str, float], Tuple[Literal[""], Literal[""]]]:
    """Obsolete method. Use ``find_mapdl`` instead."""
    warnings.warn(
        "This method is going to be deprecated in future versions. Please use 'find_mapdl'.",
        category=DeprecationWarning,
    )

    return _find_installation("mapdl", version, supported_versions)


def _has_plugin(product: str) -> bool:
    """Check if a product has a plugin defined in PLUGINS.

    Parameters
    ----------
    product : str
        The product type, either "mapdl", "mechanical", or "dyna".

    Returns
    -------
    bool
        True if the product has a plugin defined in PLUGINS, False otherwise.
    """
    return product in PLUGINS


def is_valid_executable_path(product: PRODUCT_TYPE, exe_loc: str) -> bool:
    """Check if the executable path is valid for the product.

    Parameters
    ----------
    product : PRODUCT_TYPE
        The product type, either "mapdl", "mechanical", or "dyna".
    exe_loc : str
        The executable path to check.

    Returns
    -------
    bool
        True if the executable path is valid for the product, False otherwise.
    """
    return PLUGINS[product].is_valid_executable_path(exe_loc)


def _is_common_executable_path(product: PRODUCT_TYPE, exe_loc: str) -> bool:
    """Check if the executable path is a common path for the product.

    Parameters
    ----------
    product : PRODUCT_TYPE
        The product type, either "mapdl", "mechanical", or "dyna".
    exe_loc : str
        The executable path to check.

    Returns
    -------
    bool
        True if the executable path is a common path for the product, False otherwise.
    """
    exe_path = Path(exe_loc)
    exe_str = str(exe_path)

    if product == "mapdl":
        v_version = re.findall(r"v(\d\d\d)", exe_str)
        ansys_version = re.findall(r"ansys(\d\d\d)", exe_str, re.IGNORECASE)

        return (
            len(v_version) != 0
            and len(ansys_version) != 0
            and v_version[-1] == ansys_version[-1]
            and is_valid_executable_path("mapdl", exe_str)
            and "ansys" in exe_path.parts
            and "bin" in exe_path.parts
        )

    elif product == "dyna":
        return "dyna" in exe_str

    elif product == "mechanical":
        is_valid_path = is_valid_executable_path("mechanical", exe_str)

        if os.name == "nt":  # pragma: no cover
            parts = [part.lower() for part in exe_path.parts]
            return (
                is_valid_path
                and re.search(r"v\d\d\d", exe_str) is not None
                and "aisol" in parts
                and "bin" in parts
                and "winx64" in parts
                and "ansyswbu.exe" in parts
            )

        return (
            is_valid_path
            and re.search(r"v\d\d\d", exe_str) is not None
            and "aisol" in exe_path.parts
            and ".workbench" in exe_path.parts
        )

    else:
        raise Exception("unexpected application")


def _change_default_path(application: str, exe_loc: str) -> None:
    exe_path = Path(exe_loc)
    if exe_path.is_file():
        config_data = _read_config_file()
        config_data[application] = str(exe_path)
        _write_config_file(config_data)
    else:
        raise FileNotFoundError(f"File {exe_loc} is invalid or does not exist")


def change_default_mapdl_path(exe_loc: str) -> None:
    """Change your default Ansys MAPDL path.

    Parameters
    ----------
    exe_loc : str
        Ansys MAPDL executable path.  Must be a full path.

    Examples
    --------
    Change default Ansys MAPDL location on Linux

    >>> from ansys.tools.common.path import change_default_mapdl_path, get_mapdl_path
    >>> change_default_mapdl_path("/ansys_inc/v251/ansys/bin/ansys251")
    >>> get_mapdl_path()
    '/ansys_inc/v251/ansys/bin/ansys251'

    Change default Ansys location on Windows

    >>> mapdl_path = "C:/Program Files/ANSYS Inc/v251/ansys/bin/winx64/ANSYS251.exe"
    >>> change_default_mapdl_path(mapdl_path)

    """
    _change_default_path("mapdl", exe_loc)


def change_default_dyna_path(exe_loc: str) -> None:
    """Change your default Ansys LS-DYNA path.

    Parameters
    ----------
    exe_loc : str
        path to LS-Dyna executable. Must be a full path. This need not contain the name of the executable,
        because the name of the LS-Dyna executable depends on the precision.

    Examples
    --------
    Change default Ansys LS-Dyna location on Linux

    >>> from ansys.tools.common.path import change_default_dyna_path, get_dyna_path
    >>> change_default_dyna_path("/ansys_inc/v251/ansys/bin/lsdyna251")
    >>> get_dyna_path()
    '/ansys_inc/v251/ansys/bin/lsdyna251'

    Change default Ansys LS-Dyna location on Windows

    >>> dyna_path = "C:/Program Files/ANSYS Inc/v251/ansys/bin/winx64/LSDYNA251.exe"
    >>> change_default_dyna_path(dyna_path)

    """
    _change_default_path("dyna", exe_loc)


def change_default_mechanical_path(exe_loc: str) -> None:
    """Change your default Mechanical path.

    Parameters
    ----------
    exe_loc : str
        Full path for the Mechanical executable file to use.

    Examples
    --------
    On Windows:

    >>> from ansys.tools.common.path import change_default_mechanical_path, get_mechanical_path
    >>> change_default_mechanical_path("C:/Program Files/ANSYS Inc/v251/aisol/bin/win64/AnsysWBU.exe")
    >>> get_mechanical_path()
    'C:/Program Files/ANSYS Inc/v251/aisol/bin/win64/AnsysWBU.exe'

    On Linux:

    >>> from ansys.tools.common.path import change_default_mechanical_path, get_mechanical_path
    >>> change_default_mechanical_path("/ansys_inc/v251/aisol/.workbench")
    >>> get_mechanical_path()
    '/ansys_inc/v251/aisol/.workbench'

    """
    _change_default_path("mechanical", exe_loc)


def change_default_ansys_path(exe_loc: str) -> None:
    """Deprecated. Use ``change_default_mapdl_path`` instead."""  # noqa: D401
    warnings.warn(
        "This method is going to be deprecated in future versions. Please use 'change_default_mapdl_path'.",
        category=DeprecationWarning,
    )

    _change_default_path("mapdl", exe_loc)


def _save_path(product: str, exe_loc: Optional[str] = None, allow_prompt: bool = True) -> str:
    has_plugin = _has_plugin(product)
    if exe_loc is None and has_plugin:
        exe_loc, _ = _find_installation(product)
    if exe_loc == "" and allow_prompt:
        exe_loc = _prompt_path(product)  # pragma: no cover

    if has_plugin:
        if is_valid_executable_path(product, exe_loc):
            _check_uncommon_executable_path(product, exe_loc)
    _change_default_path(product, exe_loc)
    return exe_loc


def save_mechanical_path(exe_loc: Optional[str] = None, allow_prompt: bool = True) -> str:  # pragma: no cover
    """Find the Mechanical path or query the user.

    Parameters
    ----------
    exe_loc : string, optional
        Path for the Mechanical executable file (``AnsysWBU.exe``).
        The default is ``None``, in which case an attempt is made to
        obtain the path from the following sources in this order:

        - The default Mechanical paths (for example,
          ``C:/Program Files/Ansys Inc/vXXX/aisol/bin/AnsysWBU.exe``)
        - The configuration file
        - User input

        If a path is supplied, this method performs some checks. If the
        checks are successful, it writes this path to the configuration
        file.

    Returns
    -------
    str
        Path for the Mechanical executable file.

    Notes
    -----
    The location of the configuration file ``config.txt`` can be found in
    ``ansys.tools.common.path.SETTINGS_DIR``. For example:

    .. code:: pycon

        >>> from ansys.tools.common.path import SETTINGS_DIR
        >>> import os
        >>> print(os.path.join(SETTINGS_DIR, "config.txt"))
        C:/Users/[username]]/AppData/Local/Ansys/ansys_tools_path/config.txt

    You can change the default for the ``exe_loc`` parameter either by modifying the
    ``config.txt`` file or by running this code:

    .. code:: pycon

       >>> from ansys.tools.common.path import save_mechanical_path
       >>> save_mechanical_path("/new/path/to/executable")

    """
    return _save_path("mechanical", exe_loc, allow_prompt)


def save_dyna_path(exe_loc: Optional[str] = None, allow_prompt: bool = True) -> str:
    """Find Ansys LS-DYNA's path or query the user.

    If no ``exe_loc`` argument is supplied, this function attempts
    to obtain the Ansys LS-DYNA executable from (and in order):

    - The default Ansys paths (such as ``'C:/Program Files/Ansys Inc/vXXX/ansys/bin/winx64/LSDYNAXXX'``)
    - The configuration file
    - User input

    If the ``exe_loc`` argument is supplied, this function performs some checks.
    If successful, it writes the value for the ``exe_loc`` argument into the configuration file.

    Parameters
    ----------
    exe_loc : str, default: None
        Path of the LS-DYNA executable (``'lsdynaXXX'``).

    Returns
    -------
    str
        Path of the LS-DYNA executable.

    Notes
    -----
    The location of the configuration file ``config.txt`` can be found in
    ``ansys.tools.common.path.SETTINGS_DIR``. For example:

    .. code:: pycon

        >>> from ansys.tools.common.path import SETTINGS_DIR
        >>> import os
        >>> print(os.path.join(SETTINGS_DIR, "config.txt"))
        C:/Users/[username]/AppData/Local/Ansys/ansys_tools_path/config.txt

    Examples
    --------
    You can change the default ``exe_loc`` parameter value either by modifying the mentioned
    ``config.txt`` file or by executing this code:

    >>> from ansys.tools.common.path import save_dyna_path
    >>> save_dyna_path("/new/path/to/executable")

    """
    return _save_path("dyna", exe_loc, allow_prompt)


def save_mapdl_path(exe_loc: Optional[str] = None, allow_prompt: bool = True) -> str:
    """Find the Ansys MAPDL's path or query the user.

    If no ``exe_loc`` argument is supplied, this function attempts
    to obtain the Ansys MAPDL executable from (and in order):

    - The default Ansys paths (i.e. ``'C:/Program Files/Ansys Inc/vXXX/ansys/bin/winx64/ansysXXX'``)
    - The configuration file
    - User input

    If the ``exe_loc`` argument is supplied, this function performs some checks.
    If successful, it writes the value for the ``exe_loc`` parameter into the configuration file.

    Parameters
    ----------
    exe_loc : str, default: None
        Path of the MAPDL executable (``ansysXXX``).

    Returns
    -------
    str
        Path of the MAPDL executable.

    Notes
    -----
    The location of the configuration file ``config.txt`` can be found in
    ``ansys.tools.common.path.SETTINGS_DIR``. For example:

    .. code:: pycon

        >>> from ansys.tools.common.path import SETTINGS_DIR
        >>> import os
        >>> print(os.path.join(SETTINGS_DIR, "config.txt"))
        C:/Users/[username]/AppData/Local/Ansys/ansys_tools_path/config.txt

    Examples
    --------
    You can change the default value for the ``exe_loc`` parameter either by modifying the mentioned
    ``config.txt`` file or by executing this code:

    >>> from ansys.tools.common.path import save_mapdl_path
    >>> save_mapdl_path("/new/path/to/executable")

    """
    return _save_path("mapdl", exe_loc, allow_prompt)


def save_ansys_path(exe_loc: Optional[str] = None, allow_prompt: bool = True) -> str:
    """Deprecated. Use ``save_mapdl_path`` instead."""  # noqa: D401
    warnings.warn(
        "This method is going to be deprecated in future versions. Please use 'save_ansys_path'.",
        category=DeprecationWarning,
    )
    return _save_path("mapdl", exe_loc, allow_prompt)


def _check_uncommon_executable_path(product: PRODUCT_TYPE, exe_loc: str):
    """Check if the supplied executable path is not a common one.

    Parameters
    ----------
    product : PRODUCT_TYPE
        Product name, one of "mapdl", "mechanical", or "dyna".
    exe_loc : str
        Path to the executable file.
    """
    if not _is_common_executable_path(product, exe_loc):
        product_pattern_path = PRODUCT_EXE_INFO[product]["patternpath"]
        product_name = PRODUCT_EXE_INFO[product]["name"]
        warnings.warn(
            f"The supplied path ('{exe_loc}') does not match the usual {product_name} executable path style"
            f"('directory/{product_pattern_path}'). "
            "You might have problems at later use."
        )


def _prompt_path(product: PRODUCT_TYPE) -> str:  # pragma: no cover
    """Prompt for the CLI.

    Parameters
    ----------
    product : PRODUCT_TYPE
        Product name, one of "mapdl", "mechanical", or "dyna".

    Returns
    -------
    str
        The path to the executable for the specified product.
    """
    product_info = PRODUCT_EXE_INFO[product]
    product_name = product_info["name"]
    has_pattern = "pattern" in product_info and "patternpath" in product_info
    print(f"Cached {product} executable not found")
    print(f"You are about to enter manually the path of the {product_name} executable\n")
    if has_pattern:
        product_pattern = product_info["pattern"]
        product_pattern_path = product_info["patternpath"]
        print(
            f"({product_pattern}, where XXX is the version\n"
            f"This file is very likely to contained in path ending in '{product_pattern_path}'.\n"
        )
    print(
        "\nIf you experience problems with the input path you can overwrite the configuration\n"
        "file by typing:\n"
        f">>> from ansys.tools.common.path import save_{product}_path\n"
        f">>> save_{product}_path('/new/path/to/executable/')\n"
    )
    while True:
        if has_pattern:
            exe_loc = input(f"Enter the location of {product_name} ({product_pattern}):")
        else:
            exe_loc = input(f"Enter the location of {product_name}:")

        if is_valid_executable_path(product, exe_loc):
            _check_uncommon_executable_path(product, exe_loc)
            config_data = _read_config_file()
            config_data[product] = exe_loc
            _write_config_file(config_data)
            break
        else:
            if has_pattern:
                print(
                    f"The supplied path is either: not a valid file path, or does not match '{product_pattern}' name."
                )
            else:
                print("The supplied path is either: not a valid file path.")
    return exe_loc


def clear_configuration(product: Union[PRODUCT_TYPE, Literal["all"]]) -> None:
    """Clear the entry of the specified product in the configuration file."""
    config = _read_config_file()  # we use read_config_file here because it will do the migration if necessary
    if product == "all":
        _write_config_file({})
        return
    if product in config:
        del config[product]
        _write_config_file(config)


def _read_config_file() -> Dict[PRODUCT_TYPE, str]:
    """Read config file for a given product, migrating if needed."""
    config_path = Path(CONFIG_FILE)

    if not config_path.is_file():
        _migrate_config_file()

    if config_path.is_file():
        content = config_path.read_text()
        if content:
            return json.loads(content)

    return {}


def _write_config_file(config_data: Dict[PRODUCT_TYPE, str]):
    """Warning - this isn't threadsafe."""
    config_path = Path(CONFIG_FILE)
    config_path.write_text(json.dumps(config_data))


def _migrate_config_file() -> None:
    """Migrate configuration if needed."""

    def _migrate_txt_config_file() -> Dict[PRODUCT_TYPE, str]:
        old_mapdl_config_path = Path(platformdirs.user_data_dir("ansys_mapdl_core")) / "config.txt"
        old_mechanical_config_path = Path(platformdirs.user_data_dir("ansys_mechanical_core")) / "config.txt"
        config_file_path = Path(CONFIG_FILE)

        if config_file_path.is_file():
            new_config_data = _read_config_file()
        else:
            new_config_data: Dict[PRODUCT_TYPE, str] = {}

        if "mapdl" not in new_config_data and old_mapdl_config_path.exists():
            new_config_data["mapdl"] = old_mapdl_config_path.read_text()

        if "mechanical" not in new_config_data and old_mechanical_config_path.exists():
            new_config_data["mechanical"] = old_mechanical_config_path.read_text()

        return new_config_data

    def _migrate_json_config_file() -> Dict[PRODUCT_TYPE, str]:  # pragma: no cover
        config_path = Path(platformdirs.user_data_dir("ansys_tools_path")) / "config.txt"
        try:
            old_config_data = config_path.read_text()
            return cast(Dict[PRODUCT_TYPE, str], json.loads(old_config_data))
        except (ValueError, FileNotFoundError):
            # If the config file cannot be parsed or does not exist, return an empty dict
            return {}

    @dataclass
    class FileMigrationStrategy:
        paths: List[Path]
        migration_function: Callable[[], Dict[PRODUCT_TYPE, str]]

        def __call__(self):
            return self.migration_function()

    file_migration_strategy_list: List[FileMigrationStrategy] = [
        FileMigrationStrategy(
            [
                Path(platformdirs.user_data_dir("ansys_mapdl_core")) / "config.txt",
                Path(platformdirs.user_data_dir("ansys_mechanical_core")) / "config.txt",
            ],
            _migrate_txt_config_file,
        ),
        FileMigrationStrategy(
            [Path(platformdirs.user_data_dir("ansys_tools_path")) / "config.txt"],
            _migrate_json_config_file,
        ),
    ]

    # Filter to only keep config files that exist
    file_migration_strategy_list = [
        strategy for strategy in file_migration_strategy_list if any(p.exists() for p in strategy.paths)
    ]

    if not file_migration_strategy_list:
        return

    # Use the migration strategy of the last file
    latest_strategy = file_migration_strategy_list[-1]
    _write_config_file(latest_strategy())

    # Remove all old config files
    for strategy in file_migration_strategy_list:
        for path in strategy.paths:
            if path.exists():
                path.unlink()


def _read_executable_path_from_config_file(product_name: PRODUCT_TYPE) -> Optional[str]:
    """Read the executable path for the product given by `product_name` from config file.

    Parameters
    ----------
    product_name : PRODUCT_TYPE
        Name of the product to get the executable path for. For example, "mapdl", "dyna", or "mechanical".

    Returns
    -------
    Optional[str]
        The path to the executable if it exists in the configuration file, otherwise `None`.
    """
    config_data = _read_config_file()
    return config_data.get(product_name, None)


def get_saved_application_path(application: str) -> Optional[str]:
    """Get the saved path for a specific application from the configuration file.

    Parameters
    ----------
    application : str
        Name of the application to get the path for. For example, "mapdl", "dyna", or "mechanical".

    Returns
    -------
    Optional[str]
        The path to the executable if it exists in the configuration file, otherwise `None`.
    """
    exe_loc = _read_executable_path_from_config_file(application)
    return exe_loc


def _get_application_path(
    product: str,
    allow_input: bool = True,
    version: Optional[float] = None,
    find: bool = True,
) -> Optional[str]:
    _exe_loc = _read_executable_path_from_config_file(product)
    if _exe_loc is not None:
        if version is None:
            return _exe_loc
        else:
            _version = version_from_path(product, _exe_loc)
            if _version == version:
                return _exe_loc
            else:
                LOG.debug(
                    f"Application {product} requested version {version} does not match with {_version} "
                    f"in config file. Trying to find version {version} ..."
                )

    LOG.debug(f"{product} path not found in config file")
    if not _has_plugin(product):
        raise Exception(f"Application {product} not registered.")

    if find:
        try:
            exe_loc, exe_version = _find_installation(product, version)
            if (exe_loc, exe_version) != ("", ""):
                if Path(exe_loc).is_file():
                    return exe_loc
        except ValueError:
            pass  # Continue to allow_input check

    if allow_input:
        exe_loc = _prompt_path(product)
        _change_default_path(product, exe_loc)
        return exe_loc

    warnings.warn(f"No path found for {product} in default locations.")
    return None


def get_mapdl_path(allow_input: bool = True, version: Optional[float] = None, find: bool = True) -> Optional[str]:
    """Acquires the Ansys MAPDL path.

    First, it looks in the configuration file, used by `save_mapdl_path`
    Then, it tries to find it based on conventions for where it usually is.
    Lastly, it takes user input

    Parameters
    ----------
    allow_input : bool, optional
        Allow user input to find Ansys MAPDL path.  The default is ``True``.

    version : float, optional
        Version of Ansys MAPDL to search for. For example ``version=25.1``.
        If ``None``, use latest.

    find: bool, optional
        Allow ansys-tools-path to search for Ansys Mechanical in typical installation locations

    """
    return _get_application_path("mapdl", allow_input, version, find)


def get_dyna_path(allow_input: bool = True, version: Optional[float] = None, find: bool = True) -> Optional[str]:
    """Acquires the Ansys LS-DYNA path from a cached file or user input.

    First, it looks in the configuration file, used by `save_dyna_path`
    Then, it tries to find it based on conventions for where it usually is.
    Lastly, it takes user input

    Parameters
    ----------
    allow_input : bool, optional
        Allow user input to find Ansys LS-Dyna path.  The default is ``True``.

    version : float, optional
        Version of Ansys LS-Dyna to search for. For example ``version=25.1``.
        If ``None``, use latest.

    find: bool, optional
        Allow ansys-tools-path to search for Ansys Mechanical in typical installation locations

    """
    return _get_application_path("dyna", allow_input, version, find)


def get_ansys_path(allow_input: bool = True, version: Optional[float] = None) -> Optional[str]:
    """Deprecated. Use ``get_mapdl_path`` instead."""  # noqa: D401
    warnings.warn(
        "This method is going to be deprecated in future versions. Please use 'get_mapdl_path'.",
        category=DeprecationWarning,
    )
    return _get_application_path("mapdl", allow_input, version, True)


def get_mechanical_path(allow_input: bool = True, version: Optional[float] = None, find: bool = True) -> Optional[str]:
    """Acquires the Ansys Mechanical path.

    First, it looks in the configuration file, used by `save_mechanical_path`
    Then, it tries to find it based on conventions for where it usually is.
    Lastly, it takes user input

    Parameters
    ----------
    allow_input : bool, optional
        Allow user input to find Ansys Mechanical path.  The default is ``True``.

    version : float, optional
        Version of Ansys Mechanical to search for. For example ``version=25.1``.
        If ``None``, use latest.

    find: bool, optional
        Allow ansys-tools-path to search for Ansys Mechanical in typical installation locations

    """
    return _get_application_path("mechanical", allow_input, version, find)


def _version_from_path(path: str, product_name: str, path_version_regex: str) -> int:
    r"""Extract the version from the executable path.

    Parameters
    ----------
    path: str
        The path to the Ansys executable.
    product_name: str
        The name of the product. For example:

        mapdl = "Ansys MAPDL"
        mechanical = "Ansys Mechanical"

    path_version_regex: str
        The regex used to find the Ansys version in the executable path. For example:

        mapdl = r"v(\d\d\d).ansys"
        mechanical = r'v(\d\d\d)'

    Returns
    -------
    int
        The version in the executable path. For example, "251".
    """
    error_message = f"Unable to extract {product_name} version from {path}."
    if path:
        # expect v<ver>/ansys
        # replace \\ with / to account for possible Windows path
        matches = re.findall(rf"{path_version_regex}", path.replace("\\", "/"), re.IGNORECASE)
        if not matches:
            raise RuntimeError(error_message)
        return int(matches[-1])
    else:
        raise RuntimeError(error_message)


def version_from_path(product: PRODUCT_TYPE, path: str) -> int:
    """Extract the product version from a path.

    Parameters
    ----------
    path : str
        The path to the Ansys executable. For example:

        Mechanical:
        - Windows: ``C:/Program Files/ANSYS Inc/v251/aisol/bin/winx64/AnsysWBU.exe``
        - Linux: ``/usr/ansys_inc/v251/aisol/.workbench``

        MAPDL:
        - Windows: ``C:/Program Files/ANSYS Inc/v251/ansys/bin/winx64/ANSYS251.exe``
        - Linux: ``/usr/ansys_inc/v251/ansys/bin/mapdl``

    product: PRODUCT_TYPE
        The product. For example: mapdl, mechanical, or dyna.

    Returns
    -------
    int
        Integer version number (for example, 251).

    """
    product_name = PRODUCT_EXE_INFO[product]["name"]
    if not isinstance(path, str):
        raise ValueError(
            f'The provided path, "{path}", is not a valid string. '
            f"Run the following command to save the path to the {product_name} executable:\n\n"
            f"    save-ansys-path --name {product} /path/to/{product}-executable\n"
        )
    if (product != "dyna") and (product in PRODUCT_EXE_INFO.keys()):
        path_version_regex = r"v(\d\d\d).ansys" if product == "mapdl" else r"v(\d\d\d)"
        return _version_from_path(path, product_name, path_version_regex)
    else:
        raise Exception(f"Unexpected product, {product}")


def get_latest_ansys_installation() -> Tuple[int, str]:
    """Return a tuple with the latest Ansys installation version and its path.

    If there is a student version and a regular installation for the latest release, the regular one is returned

    Returns
    -------
    Tuple[int, str]
        Tuple with the latest version and path of the installation

    Raises
    ------
    ValueError
        No Ansys installation found
    """
    installations = get_available_ansys_installations()
    if not installations:
        raise ValueError("No Ansys installation found")

    def sort_key(version: int) -> float:
        if version < 0:
            return abs(version) - 0.5
        return float(version)

    max_version = max(installations, key=sort_key)
    return (max_version, installations[max_version])

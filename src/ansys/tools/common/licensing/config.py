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

"""License configuration file discovery and parsing utilities.

This module provides functions to find and parse Ansys license configuration
files including ansyslmd.ini and license.preferences.xml.

It also manages the *original-value cache* (a JSON ``config.txt`` file in the
user data directory) that remembers the original license-server settings the
first time they are detected, so they can later be restored via
:func:`restore_env` / :func:`restore_ini`.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET  # nosec B405 - only parses local user-owned config files

import platformdirs

from ansys.tools.common.exceptions import LicenseConfigError, LicenseFileParseError
from ansys.tools.common.licensing.models import AnsyslmdConfig, LicensePreferences
from ansys.tools.common.licensing.vars import (
    get_ansyslic_dir,
    remove_env_unix,
    remove_env_windows,
    set_env_unix,
    set_env_windows,
)
from ansys.tools.common.path import get_available_ansys_installations

logger = logging.getLogger(__name__)


def _get_user_licensing_dir() -> Path | None:
    r"""Return the user-scope licensing config directory.

    Returns
    -------
    Path | None
        ``Path(APPDATA) / ".ansys_licensing"`` on Windows,
        ``Path(HOME) / ".ansys_licensing"`` on Linux/macOS,
        or ``None`` if the required environment variable is not set.
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA", "")
    else:
        base = os.environ.get("HOME", "")
    if not base:
        return None
    return Path(base) / ".ansys_licensing"


def find_ansyslmd_ini(scope: str = "user") -> str | None:
    r"""Find the ansyslmd.ini configuration file.

    Parameters
    ----------
    scope : {"user", "installation"}, optional
        The scope to search for the configuration file. The default is
        ``"user"``.

        - ``"user"``: User-specific config (``~/.ansys_licensing/ansyslmd.ini``
          on Linux, ``%APPDATA%\.ansys_licensing\ansyslmd.ini`` on Windows).
        - ``"installation"``: Installation-wide config
          (``$ANSYSLIC_DIR/ansyslmd.ini``, with fallback to
          ``$AWP_ROOTxxx/../shared_files/licensing/ansyslmd.ini``).

    Returns
    -------
    str | None
        The path to ansyslmd.ini if found, or None if not found.

    Raises
    ------
    ValueError
        If an invalid scope is specified.

    Examples
    --------
    >>> ini_path = find_ansyslmd_ini(scope="user")
    >>> if ini_path:
    ...     print(f"Found config at: {ini_path}")
    """
    if scope not in ("user", "installation"):
        raise ValueError(f"Invalid scope: {scope}. Must be 'user' or 'installation'.")

    if scope == "user":
        # User-specific location
        user_dir = _get_user_licensing_dir()
        if user_dir is None:
            logger.debug("Cannot determine user licensing dir (env var not set)")
            return None
        ini_path = user_dir / "ansyslmd.ini"
        if ini_path.exists():
            logger.debug("Found user ansyslmd.ini: %s", ini_path)
            return str(ini_path)
        logger.debug("User ansyslmd.ini not found at %s", ini_path)
        return None
    else:
        # Installation-wide location
        # Priority 1: $ANSYSLIC_DIR/ansyslmd.ini
        ansyslic_dir = get_ansyslic_dir()
        if ansyslic_dir:
            ini_path = Path(ansyslic_dir) / "ansyslmd.ini"
            if ini_path.exists():
                logger.debug("Found installation ansyslmd.ini via ANSYSLIC_DIR: %s", ini_path)
                return str(ini_path)

        # Priority 2: Derive from AWP_ROOTxxx → <root>/../shared_files/licensing/
        # e.g. AWP_ROOT261=/opt/ansys_inc/v261 → /opt/ansys_inc/shared_files/licensing/
        installations = get_available_ansys_installations()
        # Check highest version first (most likely to be current)
        for _ver in sorted(installations.keys(), reverse=True):
            awp_path = Path(installations[_ver])
            ini_path = awp_path.parent / "shared_files" / "licensing" / "ansyslmd.ini"
            if ini_path.exists():
                logger.debug("Found installation ansyslmd.ini via AWP_ROOT%s: %s", _ver, ini_path)
                return str(ini_path)

        logger.debug("No installation ansyslmd.ini found")
        return None


def parse_ansyslmd_ini(path: str | None = None) -> AnsyslmdConfig:
    """Parse an ansyslmd.ini configuration file.

    Parameters
    ----------
    path : str | None, optional
        Path to the ansyslmd.ini file. If None, attempts to auto-find
        using find_ansyslmd_ini() with user scope first, then installation.

    Returns
    -------
    AnsyslmdConfig
        A dataclass with the parsed configuration. It holds the config file
        ``path``, the ``server`` value (the ``SERVER=`` entry, or ``None`` if
        not defined), and an ``options`` dictionary of the remaining
        key-value pairs. See
        :class:`~ansys.tools.common.licensing.models.AnsyslmdConfig` for
        details.

    Raises
    ------
    LicenseFileParseError
        If the file cannot be found or parsed.

    Examples
    --------
    >>> config = parse_ansyslmd_ini()
    >>> print(config.server)
    '1055@license-server.example.com'
    """
    if path is None:
        # Try to auto-find: user scope first, then installation
        path = find_ansyslmd_ini(scope="user")
        if path is None:
            path = find_ansyslmd_ini(scope="installation")
        if path is None:
            raise LicenseFileParseError("Could not find ansyslmd.ini file")

    ini_path = Path(path)
    if not ini_path.exists():
        raise LicenseFileParseError(f"ansyslmd.ini file not found: {path}")

    try:
        content = ini_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        raise LicenseFileParseError(f"Failed to read ansyslmd.ini: {e}") from e

    server = None
    options: dict[str, str] = {}

    for line in content.splitlines():
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        # Parse key=value pairs
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip().upper()
            value = value.strip()

            if key == "SERVER":
                server = value
            else:
                options[key] = value

    logger.debug("Parsed ansyslmd.ini %s: server=%s, %d options", path, server, len(options))
    return AnsyslmdConfig(path=str(path), server=server, options=options)


def find_license_preferences_xml(version: int | float | None = None) -> str | None:
    """Find the license.preferences.xml file.

    Parameters
    ----------
    version : int | float | None, optional
        Ansys version to find preferences for (e.g., 251 or 25.1).
        If None, uses the latest available installation.

    Returns
    -------
    str | None
        The path to license.preferences.xml if found, or None if not found.

    Examples
    --------
    >>> xml_path = find_license_preferences_xml(version=251)
    >>> if xml_path:
    ...     print(f"Found preferences at: {xml_path}")
    """
    # Determine version string
    if version is None:
        # Get latest installation
        installations = get_available_ansys_installations()
        if not installations:
            return None
        # Get the highest version
        version_code = max(installations.keys())
    else:
        # Convert float version to int code (e.g., 25.1 -> 251)
        if isinstance(version, float):
            version_code = int(version * 10)
        else:
            version_code = int(version)

    # Determine path based on platform
    if os.name == "nt":
        # Windows: %APPDATA%\Ansys\v{VER}\license.preferences.xml
        appdata = os.environ.get("APPDATA", "")
        if not appdata:
            return None
        xml_path = Path(appdata) / "Ansys" / f"v{version_code}" / "license.preferences.xml"
    else:
        # Linux: ~/.ansys/v{VER}/license.preferences.xml
        home = os.environ.get("HOME", "")
        if not home:
            return None
        xml_path = Path(home) / ".ansys" / f"v{version_code}" / "license.preferences.xml"

    if xml_path.exists():
        logger.debug("Found license.preferences.xml: %s", xml_path)
        return str(xml_path)
    logger.debug("license.preferences.xml not found at %s", xml_path)
    return None


def parse_license_preferences_xml(path: str | None = None) -> LicensePreferences:
    """Parse a license.preferences.xml file.

    Parameters
    ----------
    path : str | None, optional
        Path to the license.preferences.xml file. If None, attempts to
        auto-find using find_license_preferences_xml().

    Returns
    -------
    LicensePreferences
        A dataclass with the parsed preferences. It holds the preferences file
        ``path``, the ``preferred_server`` (or ``None``), the ordered
        ``license_order`` list of preferred features, and an ``options``
        dictionary of other preferences. See
        :class:`~ansys.tools.common.licensing.models.LicensePreferences` for
        details.

    Raises
    ------
    LicenseFileParseError
        If the file cannot be found or parsed.

    Examples
    --------
    >>> prefs = parse_license_preferences_xml()
    >>> print(prefs.preferred_server)
    '1055@license-server.example.com'
    """
    if path is None:
        path = find_license_preferences_xml()
        if path is None:
            raise LicenseFileParseError("Could not find license.preferences.xml file")

    xml_path = Path(path)
    if not xml_path.exists():
        raise LicenseFileParseError(f"license.preferences.xml not found: {path}")

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise LicenseFileParseError(f"Invalid XML in license.preferences.xml: {e}") from e
    except OSError as e:
        raise LicenseFileParseError(f"Failed to read license.preferences.xml: {e}") from e

    preferred_server = None
    license_order: list[str] = []
    options: dict[str, Any] = {}

    # Extract preferred server - check various possible element names
    for server_tag in ["LicenseServer", "Server", "PreferredServer"]:
        server_elem = root.find(server_tag)
        if server_elem is not None and server_elem.text:
            preferred_server = server_elem.text.strip()
            break

    # Extract license order - check for LicenseOrder/Feature structure
    license_order_elem = root.find("LicenseOrder")
    if license_order_elem is not None:
        for feature_elem in license_order_elem.findall("Feature"):
            feature_name = feature_elem.get("name")
            if feature_name:
                license_order.append(feature_name)
            elif feature_elem.text:
                license_order.append(feature_elem.text.strip())

    # Collect other options from root element children
    for child in root:
        tag = child.tag
        if tag not in ("LicenseServer", "Server", "PreferredServer", "LicenseOrder"):
            if child.text:
                options[tag] = child.text.strip()
            elif len(child) > 0:
                # Has children - store as dict
                options[tag] = {subchild.tag: subchild.text for subchild in child}

    return LicensePreferences(
        path=str(path),
        preferred_server=preferred_server,
        license_order=license_order,
        options=options,
    )


def get_ansyslmd_ini_path(scope: str = "user") -> str:
    r"""Get the path where ansyslmd.ini should be located (creates directory if needed).

    Unlike ``find_ansyslmd_ini``, this function returns the expected path even if
    the file doesn't exist yet, and creates the parent directory if necessary.

    Parameters
    ----------
    scope : {"user", "installation"}, optional
        The scope for the configuration file. The default is ``"user"``.

        - ``"user"``: User-specific config (``~/.ansys_licensing/ansyslmd.ini``
          on Linux, ``%APPDATA%\.ansys_licensing\ansyslmd.ini`` on Windows).
        - ``"installation"``: Installation-wide config
          (``$ANSYSLIC_DIR/ansyslmd.ini``, with fallback to
          ``$AWP_ROOTxxx/../shared_files/licensing/ansyslmd.ini``).

    Returns
    -------
    str
        The path where ansyslmd.ini should be located.

    Raises
    ------
    ValueError
        If an invalid scope is specified.
    LicenseConfigError
        If the path cannot be determined (e.g., missing environment variables)
        or the directory cannot be created.

    Examples
    --------
    >>> ini_path = get_ansyslmd_ini_path(scope="user")
    >>> print(f"Config path: {ini_path}")
    """
    if scope not in ("user", "installation"):
        raise ValueError(f"Invalid scope: {scope}. Must be 'user' or 'installation'.")

    if scope == "user":
        # User-specific location
        ini_dir = _get_user_licensing_dir()
        if ini_dir is None:
            raise LicenseConfigError(
                "APPDATA environment variable not set" if os.name == "nt" else "HOME environment variable not set"
            )

        # Create directory if it doesn't exist
        try:
            ini_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise LicenseConfigError(f"Failed to create directory {ini_dir}: {e}") from e

        return str(ini_dir / "ansyslmd.ini")
    else:
        # Installation-wide location
        # Priority 1: $ANSYSLIC_DIR/ansyslmd.ini
        ansyslic_dir = get_ansyslic_dir()
        if ansyslic_dir:
            return str(Path(ansyslic_dir) / "ansyslmd.ini")

        # Priority 2: Derive from AWP_ROOTxxx → <root>/../shared_files/licensing/
        installations = get_available_ansys_installations()
        if installations:
            # Use highest version
            highest_ver = max(installations.keys())
            awp_path = Path(installations[highest_ver])
            lic_dir = awp_path.parent / "shared_files" / "licensing"
            return str(lic_dir / "ansyslmd.ini")

        raise LicenseConfigError(
            "Cannot determine installation config path. "
            "Neither ANSYSLIC_DIR is set nor any AWP_ROOTxxx installation found."
        )


def set_ansyslmd_ini(server: str, scope: str = "user") -> str:
    r"""Set the license server in ansyslmd.ini configuration file.

    Creates or updates the ansyslmd.ini file with the specified license server.
    If the file exists, updates the SERVER line while preserving other settings.
    If the file doesn't exist, creates it with the SERVER setting.

    Parameters
    ----------
    server : str
        The license server in port@host format (e.g., "1055@license-server").
    scope : {"user", "installation"}, optional
        The scope for the configuration file. The default is ``"user"``.

        - ``"user"``: User-specific config (``~/.ansys_licensing/ansyslmd.ini``
          on Linux, ``%APPDATA%\.ansys_licensing\ansyslmd.ini`` on Windows).
        - ``"installation"``: Installation-wide config
          (``$ANSYSLIC_DIR/ansyslmd.ini``).

    Returns
    -------
    str
        The path to the updated/created configuration file.

    Raises
    ------
    ValueError
        If an invalid scope is specified.
    LicenseConfigError
        If the file cannot be written due to permission issues or other errors.

    Examples
    --------
    Set the license server in user config:

    >>> path = set_ansyslmd_ini("1055@license-server.example.com", scope="user")
    >>> print(f"Updated config at: {path}")

    Set the license server in installation config (may require admin rights):

    >>> path = set_ansyslmd_ini("1055@license-server.example.com", scope="installation")
    """
    # Capture the pre-change original SERVER value (write-once) before mutating.
    _capture_ini_original(scope)

    ini_path = get_ansyslmd_ini_path(scope=scope)
    path = Path(ini_path)

    # Read existing content if file exists
    lines: list[str] = []
    server_found = False

    if path.exists():
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            for line in content.splitlines():
                stripped = line.strip()
                # Check if this is the SERVER line
                if stripped.upper().startswith("SERVER") and "=" in stripped:
                    key, _, _ = stripped.partition("=")
                    if key.strip().upper() == "SERVER":
                        lines.append(f"SERVER={server}")
                        server_found = True
                        continue
                lines.append(line)
        except OSError as e:
            raise LicenseConfigError(f"Failed to read existing config: {e}") from e

    # Add SERVER line if not found
    if not server_found:
        # Insert at the beginning, after any comments
        insert_pos = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith(";"):
                insert_pos = i
                break
            insert_pos = i + 1
        lines.insert(insert_pos, f"SERVER={server}")

    # Write the file
    try:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except PermissionError as e:
        if scope == "installation":
            raise LicenseConfigError(
                f"Permission denied writing to {ini_path}. "
                "Installation-scope config may require administrator privileges."
            ) from e
        raise LicenseConfigError(f"Permission denied writing to {ini_path}") from e
    except OSError as e:
        raise LicenseConfigError(f"Failed to write config file: {e}") from e

    logger.info("Set SERVER=%s in %s ansyslmd.ini: %s", server, scope, ini_path)
    return ini_path


def _capture_ini_original(scope: str) -> None:
    """Capture the original scoped ansyslmd.ini SERVER value (write-once).

    Thin wrapper around :func:`capture_ini_original`. Capture failures must never
    break the primary operation, so any error is swallowed inside that helper.

    Parameters
    ----------
    scope : {"user", "installation"}
        The ansyslmd.ini scope being changed.
    """
    capture_ini_original(scope)


def remove_ansyslmd_ini_server(scope: str = "user") -> str | None:
    r"""Remove the SERVER line from the scoped ansyslmd.ini configuration file.

    Rewrites the ansyslmd.ini file without its ``SERVER=`` line, preserving all
    other settings and comments. If the file does not exist or has no SERVER
    line, this is a no-op (treated as success).

    Parameters
    ----------
    scope : {"user", "installation"}, optional
        The scope for the configuration file. The default is ``"user"``.

        - ``"user"``: User-specific config (``~/.ansys_licensing/ansyslmd.ini``
          on Linux, ``%APPDATA%\.ansys_licensing\ansyslmd.ini`` on Windows).
        - ``"installation"``: Installation-wide config
          (``$ANSYSLIC_DIR/ansyslmd.ini``).

    Returns
    -------
    str | None
        The path to the configuration file if it exists and was processed, or
        ``None`` if the file does not exist (nothing to remove).

    Raises
    ------
    ValueError
        If an invalid scope is specified.
    LicenseConfigError
        If the file cannot be read or written due to permission issues or other
        errors.

    Examples
    --------
    >>> remove_ansyslmd_ini_server(scope="user")
    '/home/user/.ansys_licensing/ansyslmd.ini'
    """
    if scope not in ("user", "installation"):
        raise ValueError(f"Invalid scope: {scope}. Must be 'user' or 'installation'.")

    # Use find_* (not get_* ) so we never create a directory just to remove.
    ini_path = find_ansyslmd_ini(scope=scope)
    if not ini_path:
        logger.debug("No %s ansyslmd.ini found; nothing to remove", scope)
        return None

    path = Path(ini_path)

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        raise LicenseConfigError(f"Failed to read existing config: {e}") from e

    kept_lines: list[str] = []
    removed_any = False
    for line in content.splitlines():
        stripped = line.strip()
        # Drop active SERVER= lines (preserve commented-out ones and other keys).
        if stripped.upper().startswith("SERVER") and "=" in stripped:
            key, _, _ = stripped.partition("=")
            if key.strip().upper() == "SERVER":
                removed_any = True
                continue
        kept_lines.append(line)

    if not removed_any:
        logger.debug("No active SERVER line in %s ansyslmd.ini; nothing to remove", scope)
        return ini_path

    new_content = "\n".join(kept_lines)
    if new_content:
        new_content += "\n"

    try:
        path.write_text(new_content, encoding="utf-8")
    except PermissionError as e:
        if scope == "installation":
            raise LicenseConfigError(
                f"Permission denied writing to {ini_path}. "
                "Installation-scope config may require administrator privileges."
            ) from e
        raise LicenseConfigError(f"Permission denied writing to {ini_path}") from e
    except OSError as e:
        raise LicenseConfigError(f"Failed to write config file: {e}") from e

    logger.info("Removed SERVER line from %s ansyslmd.ini: %s", scope, ini_path)
    return ini_path


# =============================================================================
# Original-value cache (config.txt) — capture & restore
# =============================================================================
#
# Remembers the *original* license-server settings the first time the licensing
# module observes them, so they can later be restored. The captured state is
# stored as a JSON object in a ``config.txt`` file located in the user data
# directory (``platformdirs.user_data_dir(appname="ansys_tools_licensing",
# appauthor="Ansys")``).
#
# Three items are tracked, each captured **write-once** (recorded the first time
# it is detected and never overwritten afterward):
#
# - ``ANSYSLMD_LICENSE_FILE`` — the environment variable's value at first detection.
# - ``user_ansyslmd_ini_server`` — the ``SERVER=`` value from the user ansyslmd.ini.
# - ``install_ansyslmd_ini_server`` — the ``SERVER=`` value from the installation
#   ansyslmd.ini.
#
# Each stored value is either the original string or JSON ``null`` (``None``),
# which records that the item was *unset / absent* when first detected. A missing
# key means the item has never been captured.

# Settings directory for the licensing module (mirrors the path module pattern,
# only swapping the appname).
SETTINGS_DIR = Path(platformdirs.user_data_dir(appname="ansys_tools_licensing", appauthor="Ansys"))
CONFIG_FILE_NAME = "config.txt"
CONFIG_FILE = SETTINGS_DIR / CONFIG_FILE_NAME

# Optional environment override for the config.txt location (useful for tests and
# non-default deployments), mirroring the launcher's ANSYS_LAUNCHER_CONFIG_PATH.
_CONFIG_PATH_ENV_VAR_NAME = "ANSYS_TOOLS_LICENSING_CONFIG_PATH"

# Stable JSON keys used in config.txt.
KEY_ENV = "ANSYSLMD_LICENSE_FILE"
KEY_USER_INI = "user_ansyslmd_ini_server"
KEY_INSTALL_INI = "install_ansyslmd_ini_server"

# Map config scope -> config.txt key for the ansyslmd.ini values.
_INI_SCOPE_KEYS = {
    "user": KEY_USER_INI,
    "installation": KEY_INSTALL_INI,
}


def _get_config_file() -> Path:
    """Resolve the config.txt path at call time.

    Honors the ``ANSYS_TOOLS_LICENSING_CONFIG_PATH`` environment override when
    set; otherwise falls back to the module-level :data:`CONFIG_FILE` default.
    Resolving lazily (rather than caching the import-time value) keeps the
    location overridable and robust across test environments.
    """
    override = os.environ.get(_CONFIG_PATH_ENV_VAR_NAME)
    if override:
        return Path(override)
    return CONFIG_FILE


def _read_config_file() -> dict[str, str | None]:
    """Read the original-value cache from config.txt.

    Returns
    -------
    dict[str, str | None]
        The parsed JSON object, or an empty dict if the file is missing,
        empty, or cannot be parsed. A corrupt cache must never break a
        licensing operation, so parse/OS errors are logged and treated as
        an empty cache.
    """
    config_file = _get_config_file()
    if not config_file.is_file():
        return {}

    try:
        content = config_file.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Failed to read original-value cache %s: %s", config_file, exc)
        return {}

    if not content.strip():
        return {}

    try:
        data = json.loads(content)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("Original-value cache %s is corrupt, ignoring: %s", config_file, exc)
        return {}

    if not isinstance(data, dict):
        logger.warning("Original-value cache %s has unexpected content, ignoring", config_file)
        return {}

    return data


def _write_config_file(data: dict[str, str | None]) -> None:
    """Write the original-value cache to config.txt.

    Creates the settings directory if needed. This is not threadsafe, matching
    the existing config.txt pattern used elsewhere in the repository.

    Parameters
    ----------
    data : dict[str, str | None]
        The cache contents to serialize as JSON.

    Raises
    ------
    LicenseConfigError
        If the directory cannot be created or the file cannot be written.
    """
    config_file = _get_config_file()
    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise LicenseConfigError(f"Failed to create settings directory {config_file.parent}: {exc}") from exc

    try:
        config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        raise LicenseConfigError(f"Failed to write original-value cache {config_file}: {exc}") from exc


def capture_original(key: str, value: str | None) -> None:
    """Record *value* for *key* in the cache, write-once.

    If *key* is already present in the cache, this is a no-op (the original
    value is never overwritten). Otherwise *value* (which may be ``None`` to
    record "was unset") is stored and the cache is written back to disk.

    Parameters
    ----------
    key : str
        The cache key (one of :data:`KEY_ENV`, :data:`KEY_USER_INI`,
        :data:`KEY_INSTALL_INI`).
    value : str | None
        The original value to record, or ``None`` to record that the item
        was unset / absent when first detected.
    """
    config = _read_config_file()
    if key in config:
        logger.debug("Original value for '%s' already captured, not overwriting", key)
        return

    config[key] = value
    _write_config_file(config)
    logger.debug("Captured original value for '%s': %r", key, value)


def get_original(key: str) -> tuple[bool, str | None]:
    """Look up the captured original value for *key*.

    Parameters
    ----------
    key : str
        The cache key to look up.

    Returns
    -------
    tuple[bool, str | None]
        ``(was_captured, value)``. ``was_captured`` is ``False`` when the key
        has never been captured (``value`` is then ``None``). When
        ``was_captured`` is ``True``, ``value`` is the original string, or
        ``None`` if the item was unset when first detected.
    """
    config = _read_config_file()
    if key not in config:
        return False, None
    return True, config[key]


def capture_env_original() -> None:
    """Capture the original ``ANSYSLMD_LICENSE_FILE`` env var value (write-once)."""
    try:
        capture_original(KEY_ENV, os.environ.get("ANSYSLMD_LICENSE_FILE"))
    except LicenseConfigError as exc:
        # Capture must never break the primary operation.
        logger.warning("Could not capture original ANSYSLMD_LICENSE_FILE: %s", exc)


def _detect_ini_server(scope: str) -> str | None:
    """Return the current ``SERVER=`` value from the scoped ansyslmd.ini, or None.

    Parameters
    ----------
    scope : {"user", "installation"}
        The ansyslmd.ini scope to inspect.

    Returns
    -------
    str | None
        The SERVER value, or ``None`` if the file is absent, has no SERVER
        line, or cannot be parsed.
    """
    ini_path = find_ansyslmd_ini(scope=scope)
    if not ini_path:
        return None
    try:
        return parse_ansyslmd_ini(ini_path).server
    except LicenseFileParseError:
        logger.debug("Could not parse %s ansyslmd.ini while capturing original value", scope)
        return None


def capture_ini_original(scope: str) -> None:
    """Capture the original ``SERVER`` value of the scoped ansyslmd.ini (write-once).

    Parameters
    ----------
    scope : {"user", "installation"}
        The ansyslmd.ini scope to capture.
    """
    key = _INI_SCOPE_KEYS.get(scope)
    if key is None:
        raise ValueError(f"Invalid scope: {scope}. Must be 'user' or 'installation'.")
    try:
        capture_original(key, _detect_ini_server(scope))
    except LicenseConfigError as exc:
        logger.warning("Could not capture original %s ansyslmd.ini SERVER: %s", scope, exc)


def restore_env(scope: str = "user", shell: str = "auto") -> tuple[bool, str | None]:
    """Restore ``ANSYSLMD_LICENSE_FILE`` to its captured original value.

    If the original value was a string, the persistent environment variable is
    set back to it. If the original was unset (``None``), the persistent
    variable is removed so the system returns to its true original state.

    Parameters
    ----------
    scope : {"user", "system"}, optional
        The environment-variable scope (Windows). Default is ``"user"``.
    shell : str, optional
        The shell type for the rc file on Unix. Default is ``"auto"``.

    Returns
    -------
    tuple[bool, str | None]
        ``(removed, value)``. ``removed`` is ``True`` when the persistent
        variable was removed (original was unset); otherwise ``value`` holds
        the restored string.

    Raises
    ------
    LicenseConfigError
        If nothing was ever captured, or if the restore operation fails.
    """
    was_captured, value = get_original(KEY_ENV)
    if not was_captured:
        raise LicenseConfigError("No original ANSYSLMD_LICENSE_FILE captured; nothing to restore.")

    if value is None:
        if os.name == "nt":
            remove_env_windows(scope)
        else:
            remove_env_unix(shell)
        logger.info("Restored ANSYSLMD_LICENSE_FILE by removing it (original was unset)")
        return True, None

    if os.name == "nt":
        set_env_windows(value, scope)
    else:
        set_env_unix(value, shell)
    logger.info("Restored ANSYSLMD_LICENSE_FILE to original value: %s", value)
    return False, value


def restore_ini(scope: str) -> tuple[bool, str | None]:
    """Restore the scoped ansyslmd.ini ``SERVER`` line to its captured original.

    If the original was a string, the SERVER line is set back to it. If the
    original was unset (``None``), the SERVER line is removed.

    Parameters
    ----------
    scope : {"user", "installation"}
        The ansyslmd.ini scope to restore.

    Returns
    -------
    tuple[bool, str | None]
        ``(removed, value)``. ``removed`` is ``True`` when the SERVER line was
        removed (original was unset); otherwise ``value`` holds the restored
        string.

    Raises
    ------
    ValueError
        If an invalid scope is specified.
    LicenseConfigError
        If nothing was ever captured, or if the restore operation fails.
    """
    key = _INI_SCOPE_KEYS.get(scope)
    if key is None:
        raise ValueError(f"Invalid scope: {scope}. Must be 'user' or 'installation'.")

    was_captured, value = get_original(key)
    if not was_captured:
        raise LicenseConfigError(f"No original {scope} ansyslmd.ini SERVER captured; nothing to restore.")

    if value is None:
        remove_ansyslmd_ini_server(scope=scope)
        logger.info("Restored %s ansyslmd.ini by removing SERVER (original was unset)", scope)
        return True, None

    set_ansyslmd_ini(value, scope=scope)
    logger.info("Restored %s ansyslmd.ini SERVER to original value: %s", scope, value)
    return False, value

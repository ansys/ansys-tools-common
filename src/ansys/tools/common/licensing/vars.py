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

"""License environment variable inspection utilities.

This module provides functions to inspect license-related environment variables,
and to set, remove, and restore the persistent ``ANSYSLMD_LICENSE_FILE``
environment variable. Config file fallback logic is NOT here - that is in the
diagnosis module.

For comprehensive license environment information including config files and
effective server resolution, use `get_license_environment()` from the diagnosis module.
"""

import logging
import os
from pathlib import Path
import subprocess  # nosec B404 - used only to invoke setx / reg with fixed argument lists

from ansys.tools.common.exceptions import LicenseConfigError

logger = logging.getLogger(__name__)

# Vendor-specific environment variable priority
# Order matters: first found takes precedence
VENDOR_ENV_VARS = {
    "ansyslmd": ["ANSYSLMD_LICENSE_FILE", "ANSYSLI_SERVERS"],
    "snpslmd": ["SNPSLMD_LICENSE_FILE"],
}

# Additional environment variables to check
ANSYS_ENV_VARS = ["ANSYSLIC_DIR"]


def get_license_vars(vendor: str = "ansyslmd") -> dict[str, str | None]:
    """Get license-related environment variables for a vendor.

    Retrieves all license-related environment variables for the specified
    vendor daemon. This function ONLY inspects environment variables - it
    does NOT include config file information or effective server resolution.

    For comprehensive license environment information including config files,
    use `get_license_environment()` from the diagnosis module.

    Parameters
    ----------
    vendor : str, optional
        The vendor daemon name. Currently supported: "ansyslmd", "snpslmd".
        Default is "ansyslmd".

    Returns
    -------
    dict[str, str | None]
        Dictionary mapping environment variable names to their values
        (None if not set). Includes vendor-specific vars and ANSYSLIC_DIR.

    Examples
    --------
    >>> env_vars = get_license_vars()
    >>> print(env_vars)
    {'ANSYSLMD_LICENSE_FILE': '1055@server.example.com', 'ANSYSLI_SERVERS': None, ...}
    """
    # Get env vars for the specified vendor (default to ansyslmd vars if unknown)
    env_var_names = VENDOR_ENV_VARS.get(vendor, VENDOR_ENV_VARS["ansyslmd"])

    # Collect current values
    env_vars: dict[str, str | None] = {}
    for var_name in env_var_names:
        env_vars[var_name] = os.environ.get(var_name)

    # Add additional Ansys env vars
    for var_name in ANSYS_ENV_VARS:
        env_vars[var_name] = os.environ.get(var_name)

    return env_vars


def get_license_server_from_env(vendor: str = "ansyslmd") -> str | None:
    """Get the license server from environment variables only.

    Checks environment variables in priority order and returns the first
    defined server. This function does NOT fall back to config files.

    The priority order for ansyslmd is:
    1. ANSYSLMD_LICENSE_FILE
    2. ANSYSLI_SERVERS

    Parameters
    ----------
    vendor : str, optional
        The vendor daemon name. Currently supported: "ansyslmd", "snpslmd".
        Default is "ansyslmd".

    Returns
    -------
    str | None
        The license server string (e.g., "1055@host") from the highest
        priority environment variable, or None if no env var is set.

    Examples
    --------
    >>> import os
    >>> os.environ["ANSYSLMD_LICENSE_FILE"] = "1055@server1"
    >>> get_license_server_from_env()
    '1055@server1'
    """
    # Get env vars for the specified vendor (default to ansyslmd vars if unknown)
    env_var_names = VENDOR_ENV_VARS.get(vendor, VENDOR_ENV_VARS["ansyslmd"])

    # Check environment variables in priority order
    for var_name in env_var_names:
        value = os.environ.get(var_name)
        if value:  # Non-empty string
            logger.debug("License server from env var %s: %s", var_name, value)
            return value

    logger.debug("No license server found in environment variables for vendor '%s'", vendor)
    return None


def get_ansyslic_dir() -> str | None:
    """Get the ANSYSLIC_DIR environment variable value.

    ANSYSLIC_DIR points to the Ansys licensing directory which typically
    contains the installation-wide ansyslmd.ini configuration file.

    Returns
    -------
    str | None
        The value of ANSYSLIC_DIR, or None if not set.

    Examples
    --------
    >>> lic_dir = get_ansyslic_dir()
    >>> if lic_dir:
    ...     print(f"Licensing directory: {lic_dir}")
    """
    value = os.environ.get("ANSYSLIC_DIR")
    if value:
        logger.debug("ANSYSLIC_DIR=%s", value)
    else:
        logger.debug("ANSYSLIC_DIR is not set")
    return value


def get_awp_root_versions() -> dict[int, str]:
    r"""Get the AWP_ROOTxxx environment variable values for installed Ansys versions.

    AWP_ROOTxxx environment variables (e.g., AWP_ROOT251, AWP_ROOT242) point to
    the base installation paths for each installed Ansys version.

    This function imports and uses the existing logic from ansys.tools.common.path
    module to avoid code duplication.

    Returns
    -------
    dict[int, str]
        A dictionary mapping Ansys version numbers (e.g., 251) to their
        installation paths. Student versions have negative version numbers.
        Returns an empty dict if no installations are found.

    Examples
    --------
    >>> versions = get_awp_root_versions()
    >>> for ver, path in versions.items():
    ...     print(f"v{ver}: {path}")
    v251: C:\\Program Files\\ANSYS Inc\\v251
    v242: C:\\Program Files\\ANSYS Inc\\v242
    """
    # Import and reuse the existing logic from the path module
    from ansys.tools.common.path import get_available_ansys_installations

    return get_available_ansys_installations()


# =============================================================================
# Persistent ANSYSLMD_LICENSE_FILE environment variable management
# =============================================================================
#
# These helpers set, remove, and support restoring the persistent
# ANSYSLMD_LICENSE_FILE environment variable. They are shared by the CLI
# (``set-server env``) and by the restore logic in the ``config`` module.


def set_env_windows(server: str, scope: str) -> str:
    """Set ANSYSLMD_LICENSE_FILE persistently on Windows using setx.

    Parameters
    ----------
    server : str
        License server in port@host format.
    scope : {"user", "system"}
        Whether to set the variable for the current user or system-wide.
        System scope requires administrator privileges.

    Returns
    -------
    str
        Description of where the variable was set (registry location).

    Raises
    ------
    LicenseConfigError
        If the variable cannot be set (e.g., permission denied, timeout).
    """
    # Use setx command which is available on all modern Windows
    if scope == "system":
        # System-wide requires /M flag and admin privileges
        cmd = ["setx", "ANSYSLMD_LICENSE_FILE", server, "/M"]
        location = "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment"
    else:
        # User scope (default for setx)
        cmd = ["setx", "ANSYSLMD_LICENSE_FILE", server]
        location = "HKEY_CURRENT_USER\\Environment"

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)  # nosec B603
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            if "Access is denied" in error_msg or result.returncode == 1:
                raise LicenseConfigError(
                    f"Permission denied. Setting system-wide environment variables requires "
                    f"running as Administrator. Error: {error_msg}"
                )
            raise LicenseConfigError(f"Failed to set environment variable: {error_msg}")
    except subprocess.TimeoutExpired as e:
        raise LicenseConfigError("Timeout while setting environment variable") from e
    except FileNotFoundError as e:
        raise LicenseConfigError("setx command not found. This should be available on Windows.") from e

    return location


def remove_env_windows(scope: str) -> str:
    """Remove the persistent ANSYSLMD_LICENSE_FILE variable on Windows.

    Deletes the value from the user or system registry environment. A value
    that is already absent is treated as success.

    Parameters
    ----------
    scope : {"user", "system"}
        Whether to remove the variable for the current user or system-wide.
        System scope requires administrator privileges.

    Returns
    -------
    str
        Description of where the variable was removed from (registry location).

    Raises
    ------
    LicenseConfigError
        If the variable cannot be removed (e.g., permission denied, timeout).
    """
    if scope == "system":
        key = "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment"
        location = "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment"
    else:
        key = "HKCU\\Environment"
        location = "HKEY_CURRENT_USER\\Environment"

    cmd = ["reg", "delete", key, "/F", "/V", "ANSYSLMD_LICENSE_FILE"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)  # nosec B603
        if result.returncode != 0:
            error_msg = (result.stderr.strip() or result.stdout.strip()).lower()
            # "unable to find the specified registry key or value" -> already absent, success.
            if "unable to find" in error_msg or "cannot find" in error_msg:
                logger.debug("ANSYSLMD_LICENSE_FILE already absent in %s", location)
                return location
            if "access is denied" in error_msg:
                raise LicenseConfigError(
                    "Permission denied. Removing system-wide environment variables requires "
                    f"running as Administrator. Error: {error_msg}"
                )
            raise LicenseConfigError(f"Failed to remove environment variable: {error_msg}")
    except subprocess.TimeoutExpired as e:
        raise LicenseConfigError("Timeout while removing environment variable") from e
    except FileNotFoundError as e:
        raise LicenseConfigError("reg command not found. This should be available on Windows.") from e

    return location


def detect_shell() -> str:
    """Detect the current user's shell type from the ``SHELL`` environment variable.

    Returns
    -------
    str
        Shell type: 'bash', 'zsh', 'sh', 'csh', 'tcsh', 'fish', or 'bash' as fallback.
    """
    shell_path = os.environ.get("SHELL", "")
    if shell_path:
        shell_name = Path(shell_path).name
        if shell_name in ("bash", "zsh", "sh", "csh", "tcsh", "fish"):
            return shell_name
    # Default to bash if detection fails
    return "bash"


def get_shell_rc_file(shell: str) -> tuple[str, str]:
    """Get the rc file path and export syntax for a given shell.

    Parameters
    ----------
    shell : str
        Shell type: 'bash', 'zsh', 'sh', 'csh', 'tcsh', 'fish', or 'auto'.

    Returns
    -------
    tuple[str, str]
        (rc_file_path, export_template) where export_template uses {server} placeholder.

    Raises
    ------
    LicenseConfigError
        If HOME environment variable is not set.
    """
    home = os.environ.get("HOME", "")
    if not home:
        raise LicenseConfigError("HOME environment variable not set")

    if shell == "auto":
        shell = detect_shell()

    # Map shell to rc file and export syntax
    shell_configs: dict[str, tuple[str, str]] = {
        "bash": (".bashrc", 'export ANSYSLMD_LICENSE_FILE="{server}"'),
        "zsh": (".zshrc", 'export ANSYSLMD_LICENSE_FILE="{server}"'),
        "sh": (".profile", 'export ANSYSLMD_LICENSE_FILE="{server}"'),
        "csh": (".cshrc", 'setenv ANSYSLMD_LICENSE_FILE "{server}"'),
        "tcsh": (".cshrc", 'setenv ANSYSLMD_LICENSE_FILE "{server}"'),
        "fish": (".config/fish/config.fish", 'set -gx ANSYSLMD_LICENSE_FILE "{server}"'),
    }

    rc_file, export_template = shell_configs.get(shell, shell_configs["bash"])
    rc_path = str(Path(home) / rc_file)

    return rc_path, export_template


def set_env_unix(server: str, shell: str = "auto") -> str:
    """Set ANSYSLMD_LICENSE_FILE persistently on Unix by updating the shell rc file.

    Parameters
    ----------
    server : str
        License server in port@host format.
    shell : str, optional
        Shell type or 'auto' for auto-detection. Default is 'auto'.

    Returns
    -------
    str
        Path to the rc file that was updated.

    Raises
    ------
    LicenseConfigError
        If the rc file cannot be written.
    """
    rc_path, export_template = get_shell_rc_file(shell)
    export_line = export_template.format(server=server)
    rc_file = Path(rc_path)

    # Ensure parent directory exists (for fish config)
    rc_file.parent.mkdir(parents=True, exist_ok=True)

    # Determine the pattern to search for existing export.
    # Different shells have different syntax.
    if shell in ("csh", "tcsh") or (shell == "auto" and detect_shell() in ("csh", "tcsh")):
        search_pattern = "ANSYSLMD_LICENSE_FILE"
        line_start = "setenv"
    elif shell == "fish" or (shell == "auto" and detect_shell() == "fish"):
        search_pattern = "ANSYSLMD_LICENSE_FILE"
        line_start = "set"
    else:
        search_pattern = "ANSYSLMD_LICENSE_FILE"
        line_start = "export"

    try:
        if rc_file.exists():
            lines = rc_file.read_text(encoding="utf-8").splitlines(keepends=True)

            # Look for existing ANSYSLMD_LICENSE_FILE export
            found = False
            for i, line in enumerate(lines):
                if search_pattern in line and line.strip().startswith(line_start):
                    lines[i] = export_line + "\n"
                    found = True
                    break

            if found:
                rc_file.write_text("".join(lines), encoding="utf-8")
            else:
                # Append to file
                with rc_file.open("a", encoding="utf-8") as f:
                    f.write(f"\n# Ansys License Server\n{export_line}\n")
        else:
            # Create new rc file with the export
            rc_file.write_text(f"# Ansys License Server\n{export_line}\n", encoding="utf-8")

    except PermissionError as e:
        raise LicenseConfigError(f"Permission denied writing to {rc_path}") from e
    except OSError as e:
        raise LicenseConfigError(f"Failed to update {rc_path}: {e}") from e

    return rc_path


def remove_env_unix(shell: str = "auto") -> str:
    """Remove the persistent ANSYSLMD_LICENSE_FILE export from the shell rc file.

    Strips any ANSYSLMD_LICENSE_FILE export/setenv/set line from the rc file.
    An absent file or absent line is treated as success.

    Parameters
    ----------
    shell : str, optional
        Shell type or 'auto' for auto-detection. Default is 'auto'.

    Returns
    -------
    str
        Path to the rc file that was (or would have been) updated.

    Raises
    ------
    LicenseConfigError
        If the rc file cannot be written.
    """
    rc_path, _ = get_shell_rc_file(shell)
    rc_file = Path(rc_path)

    if not rc_file.exists():
        logger.debug("rc file %s does not exist; nothing to remove", rc_path)
        return rc_path

    try:
        lines = rc_file.read_text(encoding="utf-8").splitlines(keepends=True)
        new_lines = []
        removed_any = False
        for line in lines:
            stripped = line.strip()
            is_export = "ANSYSLMD_LICENSE_FILE" in stripped and stripped.startswith(("export", "setenv", "set"))
            # Also drop the companion "# Ansys License Server" marker comment.
            is_marker = stripped == "# Ansys License Server"
            if is_export or is_marker:
                removed_any = True
                continue
            new_lines.append(line)

        if removed_any:
            rc_file.write_text("".join(new_lines), encoding="utf-8")
            logger.debug("Removed ANSYSLMD_LICENSE_FILE export from %s", rc_path)
        else:
            logger.debug("No ANSYSLMD_LICENSE_FILE export found in %s", rc_path)
    except PermissionError as e:
        raise LicenseConfigError(f"Permission denied writing to {rc_path}") from e
    except OSError as e:
        raise LicenseConfigError(f"Failed to update {rc_path}: {e}") from e

    return rc_path
